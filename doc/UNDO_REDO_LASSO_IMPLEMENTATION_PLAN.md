# Undo/Redo and Lasso Implementation Plan

**Status:** Design Phase  
**Date:** 2025-01-XX  
**Based on:** Legacy `undo.py` and `lasso.py` analysis

---

## Executive Summary

This document outlines the implementation plan for:
1. **Undo/Redo System**: Transaction-based operation recording with grouping
2. **Lasso Selection**: Freeform polygon selection with visual feedback

Both features will be adapted from legacy implementations to fit the current architecture.

---

## Part 1: Undo/Redo System

### Legacy Analysis

**Key Patterns from `legacy/shypnpy/interface/undo.py`:**

```python
@dataclass
class UndoOp:
    kind: str              # 'add', 'move', 'delete-group', 'add-group'
    payload: Dict[str, Any]

class UndoManager:
    _undo: List[UndoOp]    # LIFO stack
    _redo: List[UndoOp]    # LIFO stack
    _limit: int = 300      # Max operations
```

**Operation Types:**

1. **Add (Single Element)**
   - **Payload**: `{'snapshot': {...}}`
   - **Undo**: Remove element by ID
   - **Redo**: Recreate element from snapshot

2. **Move (Single Element)**
   - **Payload**: `{'element_id': int, 'oldx': float, 'oldy': float, 'newx': float, 'newy': float}`
   - **Undo**: Restore old position
   - **Redo**: Apply new position
   - **Optimization**: Dropped if old == new (no-op)

3. **Delete Group**
   - **Payload**: `{'snapshot': {'places': [...], 'transitions': [...], 'arcs': [...]}}`
   - **Undo**: Restore all elements from snapshot
   - **Redo**: Delete all elements again

4. **Add Group** (e.g., Paste)
   - **Payload**: `{'snapshots': [...]}`
   - **Undo**: Remove all elements
   - **Redo**: Recreate all elements
   - **Pattern**: `begin_add_group()` → `collect_add(elem)` → `commit_add_group()`

5. **Move Group** (Multi-element drag)
   - **Payload**: `{'moves': [{'element_id', 'oldx', 'oldy', 'newx', 'newy'}, ...]}`
   - **Undo**: Restore all old positions
   - **Redo**: Apply all new positions

**Snapshot System:**

```python
def _snapshot_element(elem) -> Dict:
    snap = {'id': elem.id, 'type': elem.type}
    if hasattr(elem, 'radius'):  # Place
        snap.update({'kind': 'place', 'x': elem.x, 'y': elem.y, 
                     'radius': elem.radius, 'tokens': elem.tokens,
                     'properties': dict(elem.properties)})
    elif hasattr(elem, 'width'):  # Transition
        snap.update({'kind': 'transition', 'x': elem.x, 'y': elem.y,
                     'width': elem.width, 'height': elem.height,
                     'properties': dict(elem.properties)})
    elif hasattr(elem, 'source_id'):  # Arc
        snap.update({'kind': 'arc', 'source': elem.source_id, 
                     'target': elem.target_id, 'weight': elem.weight,
                     'arc_kind': elem.kind, 'properties': dict(elem.properties)})
    return snap
```

**Key Behaviors:**
- New user operation clears redo stack
- Move operations finalized at drag end (allows dropping no-ops)
- Element recreation preserves original IDs (important for arc connections)
- Model's `next_id` updated to avoid collisions

---

### Adapted Architecture for Current System

#### File Structure

```
src/shypn/edit/
├── undo_manager.py           # NEW: Core undo/redo logic
├── edit_operations.py         # MODIFY: Use UndoManager
└── operations_palette.py      # Already wired for state callbacks
```

#### Class Design

**`src/shypn/edit/undo_manager.py`:**

```python
from dataclasses import dataclass
from typing import Any, Dict, List
from abc import ABC, abstractmethod

@dataclass
class UndoOperation:
    """Base class for undo operations."""
    kind: str              # 'add', 'move', 'delete', 'property_change', 'group'
    payload: Dict[str, Any]
    
    @abstractmethod
    def undo(self, canvas_manager):
        """Reverse the operation."""
        pass
    
    @abstractmethod
    def redo(self, canvas_manager):
        """Reapply the operation."""
        pass

class AddOperation(UndoOperation):
    """Single element addition."""
    def __init__(self, element_snapshot: Dict):
        super().__init__('add', {'snapshot': element_snapshot})
    
    def undo(self, canvas_manager):
        elem_id = self.payload['snapshot']['id']
        canvas_manager.remove_element(elem_id)
    
    def redo(self, canvas_manager):
        snap = self.payload['snapshot']
        canvas_manager.recreate_element_from_snapshot(snap)

class MoveOperation(UndoOperation):
    """Single element move."""
    def __init__(self, element_id: int, old_pos: tuple, new_pos: tuple):
        super().__init__('move', {
            'element_id': element_id,
            'oldx': old_pos[0], 'oldy': old_pos[1],
            'newx': new_pos[0], 'newy': new_pos[1]
        })
    
    def undo(self, canvas_manager):
        elem = canvas_manager.get_element_by_id(self.payload['element_id'])
        if elem:
            elem.set_position(self.payload['oldx'], self.payload['oldy'])
    
    def redo(self, canvas_manager):
        elem = canvas_manager.get_element_by_id(self.payload['element_id'])
        if elem:
            elem.set_position(self.payload['newx'], self.payload['newy'])

class DeleteOperation(UndoOperation):
    """Single or group delete."""
    def __init__(self, elements_snapshot: List[Dict]):
        super().__init__('delete', {'snapshots': elements_snapshot})
    
    def undo(self, canvas_manager):
        for snap in self.payload['snapshots']:
            canvas_manager.recreate_element_from_snapshot(snap)
    
    def redo(self, canvas_manager):
        for snap in self.payload['snapshots']:
            canvas_manager.remove_element(snap['id'])

class UndoManager:
    """Manages undo/redo stacks with operation recording."""
    
    def __init__(self, limit: int = 300):
        self._undo_stack: List[UndoOperation] = []
        self._redo_stack: List[UndoOperation] = []
        self._limit = limit
        self._group_mode = False
        self._group_operations: List[UndoOperation] = []
    
    def push_operation(self, operation: UndoOperation):
        """Add operation to undo stack."""
        if self._group_mode:
            self._group_operations.append(operation)
        else:
            self._undo_stack.append(operation)
            self._redo_stack.clear()  # New operation invalidates redo
            self._trim_stack()
    
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
    
    def undo(self, canvas_manager):
        if not self._undo_stack:
            return False
        op = self._undo_stack.pop()
        op.undo(canvas_manager)
        self._redo_stack.append(op)
        return True
    
    def redo(self, canvas_manager):
        if not self._redo_stack:
            return False
        op = self._redo_stack.pop()
        op.redo(canvas_manager)
        self._undo_stack.append(op)
        return True
    
    def begin_group(self):
        """Start collecting operations into a group."""
        self._group_mode = True
        self._group_operations.clear()
    
    def end_group(self):
        """Commit grouped operations as single undo unit."""
        if not self._group_mode:
            return
        if self._group_operations:
            # TODO: Create GroupOperation that wraps multiple operations
            for op in self._group_operations:
                self._undo_stack.append(op)
            self._redo_stack.clear()
        self._group_mode = False
        self._group_operations.clear()
    
    def _trim_stack(self):
        if len(self._undo_stack) > self._limit:
            self._undo_stack = self._undo_stack[-self._limit:]
```

#### Integration with EditOperations

**Modify `src/shypn/edit/edit_operations.py`:**

```python
from shypn.edit.undo_manager import UndoManager, AddOperation, MoveOperation, DeleteOperation

class EditOperations:
    def __init__(self, canvas_manager):
        self.canvas_manager = canvas_manager
        
        # Replace simple lists with UndoManager
        self.undo_manager = UndoManager(limit=50)
        
        # ... rest of existing code ...
    
    def undo(self):
        """Undo the last operation."""
        success = self.undo_manager.undo(self.canvas_manager)
        if success:
            print("[EditOps] Undo successful")
            self.canvas_manager.queue_draw()  # Refresh display
        else:
            print("[EditOps] Nothing to undo")
        self._notify_state_changed()
    
    def redo(self):
        """Redo the last undone operation."""
        success = self.undo_manager.redo(self.canvas_manager)
        if success:
            print("[EditOps] Redo successful")
            self.canvas_manager.queue_draw()
        else:
            print("[EditOps] Nothing to redo")
        self._notify_state_changed()
    
    def can_undo(self):
        return self.undo_manager.can_undo()
    
    def can_redo(self):
        return self.undo_manager.can_redo()
    
    def record_add(self, element):
        """Record element addition for undo."""
        snapshot = self._snapshot_element(element)
        operation = AddOperation(snapshot)
        self.undo_manager.push_operation(operation)
        self._notify_state_changed()
    
    def record_move(self, element, old_pos, new_pos):
        """Record element move for undo."""
        if old_pos == new_pos:
            return  # No-op, don't record
        operation = MoveOperation(element.id, old_pos, new_pos)
        self.undo_manager.push_operation(operation)
        self._notify_state_changed()
    
    def record_delete(self, elements):
        """Record element deletion for undo."""
        snapshots = [self._snapshot_element(elem) for elem in elements]
        operation = DeleteOperation(snapshots)
        self.undo_manager.push_operation(operation)
        self._notify_state_changed()
    
    def _snapshot_element(self, elem):
        """Create snapshot of element for undo/redo."""
        snap = {
            'id': elem.id,
            'type': type(elem).__name__
        }
        # Add type-specific data
        if hasattr(elem, 'radius'):  # Place
            snap.update({
                'kind': 'place',
                'x': elem.x, 'y': elem.y,
                'radius': elem.radius,
                'tokens': getattr(elem, 'tokens', 0),
                'properties': dict(getattr(elem, 'properties', {}))
            })
        elif hasattr(elem, 'width') and hasattr(elem, 'height'):  # Transition
            snap.update({
                'kind': 'transition',
                'x': elem.x, 'y': elem.y,
                'width': elem.width,
                'height': elem.height,
                'properties': dict(getattr(elem, 'properties', {}))
            })
        elif hasattr(elem, 'source_id'):  # Arc
            snap.update({
                'kind': 'arc',
                'source': elem.source_id,
                'target': elem.target_id,
                'weight': getattr(elem, 'weight', 1),
                'arc_kind': getattr(elem, 'kind', 'normal'),
                'properties': dict(getattr(elem, 'properties', {}))
            })
        return snap
```

#### Canvas Manager Integration

**Required methods in `canvas_manager`:**

```python
def recreate_element_from_snapshot(self, snapshot):
    """Recreate element from snapshot dict."""
    kind = snapshot.get('kind')
    if kind == 'place':
        elem = self.model.add_place(
            snapshot['x'], snapshot['y'],
            radius=snapshot.get('radius', 20),
            tokens=snapshot.get('tokens', 0)
        )
        # Force original ID
        if elem.id != snapshot['id']:
            self.model.places.pop(elem.id)
            elem.id = snapshot['id']
            self.model.places[elem.id] = elem
    # Similar for transitions and arcs...
    return elem

def get_element_by_id(self, elem_id):
    """Get element by ID from model."""
    # Check places
    if elem_id in self.model.places:
        return self.model.places[elem_id]
    # Check transitions
    if elem_id in self.model.transitions:
        return self.model.transitions[elem_id]
    # Check arcs
    if elem_id in self.model.arcs:
        return self.model.arcs[elem_id]
    return None
```

---

## Part 2: Lasso Selection

### Legacy Analysis

**Key Patterns from `legacy/shypnpy/interface/lasso.py`:**

1. **Point Collection**
   - Left-click starts polygon
   - Subsequent clicks add points
   - Freehand drag mode: collect points during motion with button held
   - Minimum distance threshold (3-5px) to avoid point spam

2. **Polygon Closure**
   - Double-click finalizes
   - Click near first point (within 12px threshold) finalizes
   - Escape cancels

3. **Selection Logic**
   - Ray-casting algorithm for point-in-polygon
   - Modifiers:
     - Plain: Replace selection
     - Shift: Additive selection (add to existing)
     - Ctrl: Toggle selection (invert for nodes inside)

4. **Visual Feedback**
   - Semi-transparent blue path (rgba: 0.1, 0.5, 0.9, 0.35)
   - Dashed line style (2px width)
   - Points drawn as small circles

5. **Event Handling**
   - `button-press-event`: Start lasso / add point / finalize
   - `motion-notify-event`: Freehand point collection
   - `button-release-event`: End freehand drag
   - `key-press-event`: Escape to cancel

### Current Implementation Status

**`src/shypn/edit/lasso_selector.py` (INCOMPLETE):**

✅ **Has:**
- Basic structure with `start_lasso()`, `add_point()`, `finish_lasso()`
- Point-in-polygon algorithm (`_is_point_in_polygon()`)
- Render method for visual feedback
- Minimum distance threshold (5px)

❌ **Missing:**
- Freehand dragging (points added during motion)
- Canvas event wiring (button press/motion/release)
- Escape key cancellation
- Integration with canvas overlay for rendering
- Modifier key support (Shift/Ctrl)

### Implementation Plan

#### 1. Complete LassoSelector Class

**Enhance `src/shypn/edit/lasso_selector.py`:**

```python
class LassoSelector:
    def __init__(self, canvas_manager):
        self.canvas_manager = canvas_manager
        self.points = []
        self.is_active = False
        self.is_dragging = False  # NEW: Track freehand drag
        self.last_click_time = 0.0  # NEW: For double-click detection
    
    def on_button_press(self, widget, event):
        """Handle mouse button press."""
        import time
        if event.button != 1 or not self.is_active:
            return False
        
        lx, ly = self._widget_to_logical(event.x, event.y)
        now = time.time()
        
        # Double-click detection
        if self.points and (now - self.last_click_time) < 0.4:
            self.finish_lasso(event)
            return True
        
        self.last_click_time = now
        
        # Check proximity to first point (close polygon)
        if len(self.points) >= 3:
            fx, fy = self.points[0]
            if self._distance(lx, ly, fx, fy) < 12 / self._get_zoom():
                self.finish_lasso(event)
                return True
        
        # Add point
        self.add_point(lx, ly)
        self.is_dragging = True
        self._queue_draw()
        return True
    
    def on_motion(self, widget, event):
        """Handle mouse motion (freehand dragging)."""
        if not self.is_active or not self.is_dragging:
            return False
        
        # Check if button1 is held
        from gi.repository import Gdk
        if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
            return False
        
        lx, ly = self._widget_to_logical(event.x, event.y)
        self.add_point(lx, ly)  # Uses distance threshold internally
        self._queue_draw()
        return False
    
    def on_button_release(self, widget, event):
        """Handle mouse button release."""
        if event.button != 1 or not self.is_active:
            return False
        
        self.is_dragging = False
        
        # If we have enough points, finalize
        if len(self.points) >= 3:
            self.finish_lasso(event)
        
        return True
    
    def on_key_press(self, widget, event):
        """Handle key press (Escape to cancel)."""
        if event.keyval == 65307:  # Escape
            if self.is_active:
                self.cancel_lasso()
                self._queue_draw()
                return True
        return False
    
    def finish_lasso(self, event):
        """Finish lasso and select objects."""
        # ... existing code ...
        
        # NEW: Handle modifiers
        from gi.repository import Gdk
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        
        if not (shift or ctrl):
            self.canvas_manager.selection_manager.clear_selection()
        
        for obj in selected:
            if ctrl:
                # Toggle selection
                if obj.selected:
                    self.canvas_manager.selection_manager.deselect(obj)
                else:
                    self.canvas_manager.selection_manager.select(obj, multi=True)
            else:
                # Add to selection
                self.canvas_manager.selection_manager.select(obj, multi=True)
    
    def _distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def _widget_to_logical(self, px, py):
        """Convert widget coordinates to logical (world) coordinates."""
        zoom = self._get_zoom()
        pan_x, pan_y = self._get_pan()
        return (px / zoom - pan_x, py / zoom - pan_y)
    
    def _get_zoom(self):
        return getattr(self.canvas_manager, 'zoom_scale', 1.0) or 1.0
    
    def _get_pan(self):
        return (
            getattr(self.canvas_manager, 'pan_x', 0.0),
            getattr(self.canvas_manager, 'pan_y', 0.0)
        )
    
    def _queue_draw(self):
        # Get drawing area and trigger redraw
        if hasattr(self.canvas_manager, 'drawing_area'):
            self.canvas_manager.drawing_area.queue_draw()
```

#### 2. Wire Events in EditOperations

**Modify `src/shypn/edit/edit_operations.py`:**

```python
def activate_lasso_mode(self):
    """Activate lasso selection mode."""
    from shypn.edit.lasso_selector import LassoSelector
    
    self.selection_mode = 'lasso'
    
    if not self.lasso_selector:
        self.lasso_selector = LassoSelector(self.canvas_manager)
        # Wire events
        da = self.canvas_manager.drawing_area
        da.connect('button-press-event', self.lasso_selector.on_button_press)
        da.connect('motion-notify-event', self.lasso_selector.on_motion)
        da.connect('button-release-event', self.lasso_selector.on_button_release)
        
        # Wire key events to window
        window = da.get_toplevel()
        window.connect('key-press-event', self.lasso_selector.on_key_press)
    
    # Start lasso
    self.lasso_selector.is_active = True
    print("[EditOps] Lasso selection activated (click and drag to draw)")

def deactivate_lasso_mode(self):
    """Deactivate lasso selection."""
    if self.lasso_selector:
        self.lasso_selector.is_active = False
        self.lasso_selector.cancel_lasso()
    self.selection_mode = 'rectangle'
```

#### 3. Rendering Integration

**Canvas must call lasso renderer:**

In canvas drawing code (wherever the main `draw` signal is connected):

```python
def on_draw(widget, cr):
    # ... existing drawing code ...
    
    # Draw lasso overlay if active
    if edit_operations and edit_operations.lasso_selector:
        edit_operations.lasso_selector.render_lasso(cr, zoom_scale)
```

---

## Implementation Phases

### Phase 1: Core UndoManager (Priority: HIGH)
1. ✅ Create `undo_manager.py` with operation classes
2. ✅ Implement dual-stack logic
3. ✅ Add snapshot system

### Phase 2: EditOperations Integration (Priority: HIGH)
4. ✅ Replace list-based undo with UndoManager
5. ✅ Implement state callbacks
6. ✅ Wire to operations palette

### Phase 3: Canvas Recording (Priority: HIGH)
7. ✅ Intercept `add_element()` → `record_add()`
8. ✅ Intercept `move_element()` → `record_move()`
9. ✅ Intercept `delete_element()` → `record_delete()`

### Phase 4: Lasso Completion (Priority: MEDIUM)
10. ✅ Add freehand dragging to `lasso_selector.py`
11. ✅ Wire events in `activate_lasso_mode()`
12. ✅ Add rendering to canvas draw cycle

### Phase 5: Testing (Priority: HIGH)
13. ✅ Test undo single operation
14. ✅ Test undo/redo sequence
15. ✅ Test lasso selection
16. ✅ Test modifier keys (Shift/Ctrl)

### Phase 6: Polish (Priority: LOW)
17. ✅ Add keyboard shortcuts (Ctrl+Z, Ctrl+Shift+Z)
18. ✅ Improve visual feedback
19. ✅ Add tooltips to buttons

---

## Testing Checklist

### Undo/Redo Tests

- [ ] **Single Add**: Create element → Undo → Element removed → Redo → Element back
- [ ] **Single Move**: Move element → Undo → Restored to old position → Redo → At new position
- [ ] **Single Delete**: Delete element → Undo → Element restored → Redo → Deleted again
- [ ] **Multiple Operations**: Add 3 elements → Undo 3 times → All removed → Redo 3 times → All back
- [ ] **Redo Clear**: Add element → Undo → Add another element → Redo stack cleared (can't redo first)
- [ ] **Button States**: Undo/Redo buttons enabled/disabled correctly
- [ ] **Group Operations**: Paste 5 elements → Undo → All 5 removed as one operation

### Lasso Tests

- [ ] **Click Mode**: Click 4 points → Close polygon → Objects inside selected
- [ ] **Freehand Mode**: Press and drag → Release → Polygon formed → Selection applied
- [ ] **Close Detection**: Click near first point → Polygon closes automatically
- [ ] **Double-Click**: Draw lasso → Double-click → Selection applied
- [ ] **Escape Cancel**: Start lasso → Press Escape → Lasso cancelled, no selection
- [ ] **Replace Selection**: Lasso select → Previous selection cleared
- [ ] **Additive Selection (Shift)**: Select obj1 → Shift+Lasso obj2 → Both selected
- [ ] **Toggle Selection (Ctrl)**: Ctrl+Lasso over selected obj → Deselected
- [ ] **Visual Feedback**: Lasso path visible as blue dashed line while drawing
- [ ] **Point Markers**: Small circles visible at each lasso point

---

## Dependencies

### Required Methods in `canvas_manager`:
- ✅ `get_all_objects()` - Already exists
- ✅ `get_element_by_id(elem_id)` - Need to implement
- ✅ `remove_element(elem_id)` - Need to implement
- ✅ `recreate_element_from_snapshot(snap)` - Need to implement
- ✅ `queue_draw()` - Already exists

### Required Attributes in Elements:
- ✅ `elem.id` - Already exists
- ✅ `elem.x, elem.y` - Already exists
- ✅ `elem.selected` - Already exists
- ✅ `elem.set_position(x, y)` - Already exists

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| ID collision on recreate | MEDIUM | Force original ID, update `next_id` |
| Arc reconstruction without endpoints | HIGH | Snapshot dependent elements first |
| Memory leak from large undo stack | LOW | Implement 300 operation limit |
| Event handler conflicts | MEDIUM | Careful event connection order |
| Coordinate system mismatch (widget vs logical) | HIGH | Use consistent transformation helpers |

---

## Success Criteria

✅ **Undo/Redo:**
- Single operation undo/redo works
- Multiple operations work in sequence
- Button states reflect availability
- No crashes or data loss

✅ **Lasso:**
- Freehand drawing creates smooth polygon
- Point-in-polygon selection accurate
- Visual feedback clear and responsive
- Modifier keys work as expected

---

## Future Enhancements

1. **Property Change Undo**: Record changes to element properties (color, weight, etc.)
2. **Group Operations**: Implement `GroupOperation` for multi-element transactions
3. **Undo History View**: Show list of undoable operations
4. **Selective Undo**: Undo specific operation from history (non-linear)
5. **Lasso Smoothing**: Apply Bezier smoothing to freehand paths
6. **Lasso Inversion**: Select everything *outside* polygon (Ctrl+Alt modifier)

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Next Review:** After Phase 1 implementation
