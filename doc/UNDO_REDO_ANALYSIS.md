# Undo/Redo System Implementation Analysis

**Date**: October 7, 2025  
**Status**: Partially Implemented - Infrastructure Exists, Core Logic Missing  
**Priority**: High

---

## Executive Summary

The undo/redo system has **partial infrastructure** but is **not functional**. The application has:

1. ✅ **UI Buttons**: [U] and [R] buttons exist in operations palette
2. ✅ **Signal Handlers**: Button clicks trigger signals
3. ✅ **Placeholder Logic**: `EditOperations` class has undo/redo stubs
4. ❌ **No Operation Recording**: Objects are created/modified without recording
5. ❌ **No UndoManager**: Core undo/redo manager class doesn't exist
6. ❌ **No Integration**: Canvas operations don't push to undo stack

**Implementation Status**: ~30% Complete

---

## Current Implementation Status

### ✅ Complete Components

#### 1. **Operations Palette Buttons** (`src/shypn/edit/operations_palette_new.py`)

**Buttons Exist**:
- `[U]` - Undo button (initially disabled)
- `[R]` - Redo button (initially disabled)

**Tooltips**:
- Undo: "Undo (Ctrl+Z)\n\nUndo the last operation"
- Redo: "Redo (Ctrl+Shift+Z)\n\nRedo the previously undone operation"

**Signal Emission**:
```python
self.buttons['undo'].connect('clicked', self._on_undo_clicked)
self.buttons['redo'].connect('clicked', self._on_redo_clicked)

def _on_undo_clicked(self, button):
    self.emit('operation-triggered', 'undo')
    
def _on_redo_clicked(self, button):
    self.emit('operation-triggered', 'redo')
```

**Button State Management**:
```python
def set_undo_enabled(self, enabled: bool):
    self.set_button_sensitive('undo', enabled)
    
def set_redo_enabled(self, enabled: bool):
    self.set_button_sensitive('redo', enabled)
    
def update_undo_redo_state(self, can_undo: bool, can_redo: bool):
    self.set_undo_enabled(can_undo)
    self.set_redo_enabled(can_redo)
```

---

#### 2. **Signal Handler** (`src/shypn/helpers/model_canvas_loader.py`)

**Location**: Lines 503-510

**Current Code**:
```python
elif operation == 'undo':
    if canvas_manager.undo_manager and canvas_manager.undo_manager.can_undo():
        canvas_manager.undo_manager.undo()
        drawing_area.queue_draw()
elif operation == 'redo':
    if canvas_manager.undo_manager and canvas_manager.undo_manager.can_redo():
        canvas_manager.undo_manager.redo()
        drawing_area.queue_draw()
```

**Problem**: `canvas_manager.undo_manager` doesn't exist, so this code never executes.

---

#### 3. **EditOperations Stub** (`src/shypn/edit/edit_operations.py`)

**Methods Exist**:
```python
class EditOperations:
    def __init__(self, canvas_manager):
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_levels = 50
    
    def undo(self):
        """Undo the last operation."""
        if not self.undo_stack:
            print("[EditOps] Nothing to undo")
            return
        
        operation = self.undo_stack.pop()
        self.redo_stack.append(operation)
        
        # Apply reverse operation
        operation.undo()  # <-- operation class doesn't exist
        
        print(f"[EditOps] Undone: {operation}")
        self._notify_state_changed()
    
    def redo(self):
        """Redo the last undone operation."""
        if not self.redo_stack:
            print("[EditOps] Nothing to redo")
            return
        
        operation = self.redo_stack.pop()
        self.undo_stack.append(operation)
        
        # Apply forward operation
        operation.redo()  # <-- operation class doesn't exist
        
        print(f"[EditOps] Redone: {operation}")
        self._notify_state_changed()
    
    def push_operation(self, operation):
        """Add an operation to the undo stack."""
        self.undo_stack.append(operation)
        self.redo_stack.clear()
        
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)
        
        self._notify_state_changed()
    
    def can_undo(self):
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        return len(self.redo_stack) > 0
```

**Problems**:
1. Operation classes don't exist (no `operation.undo()` / `operation.redo()` methods)
2. No integration with `ModelCanvasManager`
3. No recording of actual operations (add/move/delete)

---

### ❌ Missing Components

#### 1. **UndoManager Class** (Does Not Exist)

**Required File**: `src/shypn/edit/undo_manager.py`

**Purpose**: Core undo/redo logic with operation classes

**Required Classes**:
```python
# Base operation class
class UndoOperation(ABC):
    @abstractmethod
    def undo(self, canvas_manager):
        pass
    
    @abstractmethod
    def redo(self, canvas_manager):
        pass

# Concrete operation classes
class AddPlaceOperation(UndoOperation):
    """Undo/redo place addition."""
    pass

class AddTransitionOperation(UndoOperation):
    """Undo/redo transition addition."""
    pass

class AddArcOperation(UndoOperation):
    """Undo/redo arc addition."""
    pass

class MoveOperation(UndoOperation):
    """Undo/redo object movement."""
    pass

class DeleteOperation(UndoOperation):
    """Undo/redo object deletion."""
    pass

class PropertyChangeOperation(UndoOperation):
    """Undo/redo property changes (name, tokens, weight, etc.)."""
    pass

class GroupOperation(UndoOperation):
    """Undo/redo multiple operations as a group."""
    pass

# Manager class
class UndoManager:
    def __init__(self, limit=50):
        self.undo_stack = []
        self.redo_stack = []
        self.limit = limit
    
    def push(self, operation):
        """Add operation to undo stack and clear redo."""
        self.undo_stack.append(operation)
        self.redo_stack.clear()
        
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)
    
    def undo(self, canvas_manager):
        """Undo last operation."""
        if not self.undo_stack:
            return False
        
        op = self.undo_stack.pop()
        self.redo_stack.append(op)
        op.undo(canvas_manager)
        return True
    
    def redo(self, canvas_manager):
        """Redo last undone operation."""
        if not self.redo_stack:
            return False
        
        op = self.redo_stack.pop()
        self.undo_stack.append(op)
        op.redo(canvas_manager)
        return True
    
    def can_undo(self):
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        return len(self.redo_stack) > 0
    
    def clear(self):
        """Clear both stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()
```

---

#### 2. **ModelCanvasManager Integration** (Missing)

**File**: `src/shypn/data/model_canvas_manager.py`

**Required Changes**:

```python
class ModelCanvasManager:
    def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
        # ... existing code ...
        
        # NEW: Add undo manager
        from shypn.edit.undo_manager import UndoManager
        self.undo_manager = UndoManager(limit=50)
```

**Problem**: Currently `undo_manager` is not initialized, so:
```python
canvas_manager.undo_manager  # AttributeError
```

---

#### 3. **Operation Recording** (Completely Missing)

**Current Behavior**: Operations are performed but not recorded.

**Example - Add Place** (`src/shypn/data/model_canvas_manager.py`):

```python
# CURRENT CODE (No undo recording)
def add_place(self, x, y, radius=20.0, tokens=0.0):
    place = Place(
        place_id=self._next_place_id,
        x=x, y=y,
        radius=radius,
        tokens=tokens
    )
    self.places.append(place)
    self._next_place_id += 1
    self.mark_modified()
    return place
```

**REQUIRED CODE (With undo recording)**:
```python
def add_place(self, x, y, radius=20.0, tokens=0.0):
    place = Place(
        place_id=self._next_place_id,
        x=x, y=y,
        radius=radius,
        tokens=tokens
    )
    self.places.append(place)
    self._next_place_id += 1
    self.mark_modified()
    
    # NEW: Record operation for undo
    if hasattr(self, 'undo_manager') and self.undo_manager:
        from shypn.edit.undo_manager import AddPlaceOperation
        operation = AddPlaceOperation(place)
        self.undo_manager.push(operation)
    
    return place
```

**Required for All Operations**:
- `add_place()` → Record AddPlaceOperation
- `add_transition()` → Record AddTransitionOperation
- `add_arc()` → Record AddArcOperation
- `delete_object()` → Record DeleteOperation
- Move operations (drag end) → Record MoveOperation
- Property changes (dialogs) → Record PropertyChangeOperation

---

#### 4. **Snapshot System** (Missing)

**Purpose**: Capture object state for undo/redo

**Required Methods**:

```python
def _snapshot_place(place):
    """Capture place state for undo/redo."""
    return {
        'type': 'place',
        'id': place.place_id,
        'name': place.name,
        'x': place.x,
        'y': place.y,
        'radius': place.radius,
        'tokens': place.tokens,
        'marking': place.marking,
        'capacity': place.capacity,
        'properties': dict(place.properties) if hasattr(place, 'properties') else {}
    }

def _snapshot_transition(transition):
    """Capture transition state for undo/redo."""
    return {
        'type': 'transition',
        'id': transition.transition_id,
        'name': transition.name,
        'x': transition.x,
        'y': transition.y,
        'width': transition.width,
        'height': transition.height,
        'horizontal': transition.horizontal,
        'transition_type': transition.transition_type,
        'rate': transition.rate if hasattr(transition, 'rate') else None,
        'delay': transition.delay if hasattr(transition, 'delay') else None,
        'properties': dict(transition.properties) if hasattr(transition, 'properties') else {}
    }

def _snapshot_arc(arc):
    """Capture arc state for undo/redo."""
    return {
        'type': 'arc',
        'id': arc.arc_id,
        'name': arc.name,
        'source_id': arc.source.place_id if hasattr(arc.source, 'place_id') else arc.source.transition_id,
        'target_id': arc.target.transition_id if hasattr(arc.target, 'transition_id') else arc.target.place_id,
        'source_type': 'place' if hasattr(arc.source, 'place_id') else 'transition',
        'target_type': 'transition' if hasattr(arc.target, 'transition_id') else 'place',
        'weight': arc.weight,
        'arc_kind': arc.arc_kind,
        'properties': dict(arc.properties) if hasattr(arc, 'properties') else {}
    }

def recreate_from_snapshot(canvas_manager, snapshot):
    """Recreate object from snapshot."""
    obj_type = snapshot['type']
    
    if obj_type == 'place':
        place = Place(
            place_id=snapshot['id'],
            x=snapshot['x'],
            y=snapshot['y'],
            radius=snapshot['radius'],
            tokens=snapshot['tokens']
        )
        place.name = snapshot['name']
        place.marking = snapshot.get('marking', snapshot['tokens'])
        place.capacity = snapshot.get('capacity', float('inf'))
        canvas_manager.places.append(place)
        return place
    
    elif obj_type == 'transition':
        transition = Transition(
            transition_id=snapshot['id'],
            x=snapshot['x'],
            y=snapshot['y'],
            width=snapshot['width'],
            height=snapshot['height'],
            horizontal=snapshot['horizontal']
        )
        transition.name = snapshot['name']
        transition.transition_type = snapshot.get('transition_type', 'immediate')
        if 'rate' in snapshot:
            transition.rate = snapshot['rate']
        if 'delay' in snapshot:
            transition.delay = snapshot['delay']
        canvas_manager.transitions.append(transition)
        return transition
    
    elif obj_type == 'arc':
        # Find source and target objects
        if snapshot['source_type'] == 'place':
            source = next((p for p in canvas_manager.places if p.place_id == snapshot['source_id']), None)
        else:
            source = next((t for t in canvas_manager.transitions if t.transition_id == snapshot['source_id']), None)
        
        if snapshot['target_type'] == 'place':
            target = next((p for p in canvas_manager.places if p.place_id == snapshot['target_id']), None)
        else:
            target = next((t for t in canvas_manager.transitions if t.transition_id == snapshot['target_id']), None)
        
        if source and target:
            arc = Arc(
                arc_id=snapshot['id'],
                source=source,
                target=target,
                weight=snapshot['weight']
            )
            arc.name = snapshot['name']
            arc.arc_kind = snapshot.get('arc_kind', 'normal')
            canvas_manager.arcs.append(arc)
            return arc
```

---

#### 5. **Move Operation Tracking** (Missing)

**Problem**: Object movement during drag doesn't record undo operation.

**Current Code** (`src/shypn/helpers/model_canvas_loader.py`):

```python
def _on_button_press(self, widget, event, manager):
    # ... start drag ...
    if clicked_obj.selected:
        manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)

def _on_button_release(self, widget, event, manager):
    if manager.selection_manager.end_drag():
        widget.queue_draw()
    # NO UNDO RECORDING HERE!
```

**Required Code**:
```python
def _on_button_release(self, widget, event, manager):
    # Get drag info before ending
    drag_data = manager.selection_manager.get_drag_data()  # NEW method
    
    if manager.selection_manager.end_drag():
        # Record move operation for undo
        if drag_data and hasattr(manager, 'undo_manager') and manager.undo_manager:
            from shypn.edit.undo_manager import MoveOperation
            operation = MoveOperation(
                objects=drag_data['objects'],
                old_positions=drag_data['old_positions'],
                new_positions=drag_data['new_positions']
            )
            manager.undo_manager.push(operation)
        
        widget.queue_draw()
```

---

#### 6. **Property Change Recording** (Missing)

**Problem**: Property dialog changes don't record undo operations.

**Example - Place Properties**:

Currently, when place properties are changed via dialog, no undo operation is created.

**Required**:
```python
def _on_place_properties_ok(self, dialog, place, canvas_manager):
    # Capture old state
    old_snapshot = _snapshot_place(place)
    
    # Apply changes
    place.name = dialog.get_name()
    place.marking = dialog.get_marking()
    place.capacity = dialog.get_capacity()
    
    # Capture new state
    new_snapshot = _snapshot_place(place)
    
    # Record undo operation
    if hasattr(canvas_manager, 'undo_manager') and canvas_manager.undo_manager:
        from shypn.edit.undo_manager import PropertyChangeOperation
        operation = PropertyChangeOperation(old_snapshot, new_snapshot)
        canvas_manager.undo_manager.push(operation)
```

---

## Legacy Implementation Analysis

### Legacy UndoManager (`legacy/shypnpy/interface/undo.py`)

**Features**:
- ✅ Transaction-based operation recording
- ✅ Grouping support (add-group, delete-group, move-group)
- ✅ Full snapshot system for object recreation
- ✅ Move operation finalization (drops no-op moves)
- ✅ ID preservation during recreation
- ✅ Redo stack management
- ✅ Stack size limiting (300 operations)

**Operation Types**:
1. `add` - Single object addition
2. `move` - Single object movement
3. `move-group` - Multi-object movement
4. `delete-group` - Multi-object deletion
5. `add-group` - Multi-object addition (paste)

**Key Methods**:
```python
def undo_record_add(elem):
    """Record element addition."""
    
def undo_record_move(elem, oldx, oldy):
    """Record move start."""
    
def undo_finalize_move(elem):
    """Finalize move (compute delta, drop if no-op)."""
    
def undo_record_move_group(moves):
    """Record multi-element move."""
    
def undo_record_delete_group(snapshot):
    """Record group deletion."""
    
def undo_begin_add_group():
    """Start collecting added elements."""
    
def undo_collect_add(elem):
    """Add element to group."""
    
def undo_commit_add_group():
    """Finalize group addition."""
```

---

## Architecture Requirements

### Proposed Class Structure

```
src/shypn/edit/
├── undo_manager.py
│   ├── UndoOperation (ABC)
│   ├── AddPlaceOperation
│   ├── AddTransitionOperation
│   ├── AddArcOperation
│   ├── DeleteOperation
│   ├── MoveOperation
│   ├── PropertyChangeOperation
│   ├── GroupOperation
│   └── UndoManager
│
└── edit_operations.py (MODIFY)
    └── Use UndoManager instead of raw stacks
```

### Integration Points

```
ModelCanvasManager
├── __init__()
│   └── self.undo_manager = UndoManager()
├── add_place()
│   └── Record AddPlaceOperation
├── add_transition()
│   └── Record AddTransitionOperation
├── add_arc()
│   └── Record AddArcOperation
├── delete_object()
│   └── Record DeleteOperation
└── Property dialogs
    └── Record PropertyChangeOperation

SelectionManager
└── end_drag()
    └── Record MoveOperation

model_canvas_loader.py
└── _on_palette_operation_triggered()
    ├── 'undo' → canvas_manager.undo_manager.undo()
    └── 'redo' → canvas_manager.undo_manager.redo()
```

---

## Implementation Priority

### Phase 1: Core Infrastructure (High Priority)
1. ❌ Create `undo_manager.py` with base classes
2. ❌ Add `undo_manager` to `ModelCanvasManager.__init__()`
3. ❌ Implement snapshot functions
4. ❌ Implement recreation functions

### Phase 2: Basic Operations (High Priority)
5. ❌ Record AddPlaceOperation in `add_place()`
6. ❌ Record AddTransitionOperation in `add_transition()`
7. ❌ Record AddArcOperation in `add_arc()`
8. ❌ Record DeleteOperation in `delete_object()`
9. ❌ Test basic add/delete undo/redo

### Phase 3: Move Operations (Medium Priority)
10. ❌ Capture drag start positions
11. ❌ Record MoveOperation in `end_drag()`
12. ❌ Test move undo/redo

### Phase 4: Property Changes (Medium Priority)
13. ❌ Record property changes in place dialog
14. ❌ Record property changes in transition dialog
15. ❌ Record property changes in arc dialog
16. ❌ Test property undo/redo

### Phase 5: Advanced Features (Low Priority)
17. ❌ Group operations (paste, multi-delete)
18. ❌ Move operation optimization (drop no-ops)
19. ❌ Keyboard shortcuts (Ctrl+Z, Ctrl+Shift+Z)
20. ❌ Button state updates based on can_undo/can_redo

---

## Estimated Implementation Time

| Phase | Task | Complexity | Time Estimate |
|-------|------|-----------|---------------|
| 1 | UndoManager core | High | 2-3 hours |
| 1 | Snapshot system | Medium | 1-2 hours |
| 1 | Recreation system | Medium | 1-2 hours |
| 2 | Add operations recording | Low | 1 hour |
| 2 | Delete operation recording | Low | 30 minutes |
| 2 | Testing | Medium | 1 hour |
| 3 | Move operation tracking | Medium | 1-2 hours |
| 3 | Testing | Medium | 1 hour |
| 4 | Property change recording | Medium | 2-3 hours |
| 4 | Testing | Medium | 1 hour |
| 5 | Group operations | High | 3-4 hours |
| 5 | Polish & optimization | Medium | 2 hours |
| **Total** | | | **16-24 hours** |

---

## Known Challenges

### 1. **ID Management During Recreation**
**Problem**: When undoing a delete, objects must be recreated with original IDs to maintain arc connections.

**Solution**: Store original IDs in snapshots, temporarily override ID counters during recreation.

### 2. **Arc Connection Dependencies**
**Problem**: Arcs reference places/transitions by object reference, not ID.

**Solution**: Store source/target IDs in snapshots, reconnect during recreation.

### 3. **Selection State During Undo/Redo**
**Problem**: Selected objects might be deleted/recreated, breaking selection.

**Solution**: Clear selection before undo/redo operations.

### 4. **Move Operation No-ops**
**Problem**: Small accidental drags create useless undo operations.

**Solution**: Compare old/new positions, drop operation if delta < threshold (1 pixel).

### 5. **Button State Updates**
**Problem**: [U] and [R] buttons should be enabled/disabled based on stack state.

**Solution**: Emit state change signal after each operation, update button sensitivity.

---

## Testing Strategy

### Unit Tests
1. Test UndoOperation classes (undo/redo logic)
2. Test UndoManager (stack operations)
3. Test snapshot/recreation functions

### Integration Tests
1. Add place → Undo → Verify removed
2. Add place → Undo → Redo → Verify recreated
3. Move object → Undo → Verify position restored
4. Delete object → Undo → Verify recreated
5. Change property → Undo → Verify original value
6. Multi-step operations → Undo all → Redo all

### Edge Cases
1. Undo when stack empty (should do nothing)
2. Redo when stack empty (should do nothing)
3. New operation clears redo stack
4. Stack size limit (oldest operation dropped)
5. Undo/redo with complex arc connections

---

## Related Files

### Files to Create
- `src/shypn/edit/undo_manager.py` - Core undo/redo logic (NEW)

### Files to Modify
- `src/shypn/data/model_canvas_manager.py` - Add undo_manager initialization
- `src/shypn/data/model_canvas_manager.py` - Record operations in add/delete methods
- `src/shypn/helpers/model_canvas_loader.py` - Already has handlers (working)
- `src/shypn/edit/edit_operations.py` - Use UndoManager instead of stubs

### Legacy Reference
- `legacy/shypnpy/interface/undo.py` - Complete working implementation
- `legacy/shypnpy/tests/test_undo_*.py` - Test cases

### Documentation
- `doc/UNDO_REDO_LASSO_IMPLEMENTATION_PLAN.md` - Original design document
- `doc/UNDO_REDO_ANALYSIS.md` - This file

---

## Recommendations

### Immediate Actions
1. **Create `undo_manager.py`** with operation classes
2. **Add `self.undo_manager = UndoManager()`** to ModelCanvasManager
3. **Record AddPlace/Transition/Arc operations** in respective methods
4. **Test basic undo/redo** with simple add/delete

### Short-term Goals
5. Implement move operation recording
6. Implement property change recording
7. Update button states based on can_undo/can_redo
8. Add keyboard shortcuts (Ctrl+Z, Ctrl+Shift+Z)

### Long-term Goals
9. Group operations for paste/multi-delete
10. Move operation optimization (drop no-ops)
11. Comprehensive test suite
12. User documentation

---

## Conclusion

The undo/redo system has **good UI infrastructure** (buttons, signals, handlers) but **lacks core implementation**. The main missing piece is the `UndoManager` class and operation recording throughout the codebase.

**Priority Recommendation**: High - Undo/redo is a fundamental editing feature that users expect.

**Estimated Effort**: 16-24 hours of focused development

**Next Step**: Create `src/shypn/edit/undo_manager.py` with basic operation classes, then integrate into ModelCanvasManager.

---

**Status**: Analysis Complete - Ready for Implementation  
**Date**: October 7, 2025
