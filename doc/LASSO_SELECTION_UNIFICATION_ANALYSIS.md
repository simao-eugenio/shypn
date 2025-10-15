# Lasso Selection Behavior Unification Analysis

## Date
October 15, 2025

## Problem Statement

**User Request**: "Unify lasso selection behavior throughout the code, select group, for drag, delete, copy, paste at pointer position, delete on DEL, verify all flows, plan and fix, please"

Need to ensure that lasso selection (and rectangle selection) provide consistent group operations:
- ✅ Group selection (select multiple objects)
- ❓ Group drag (drag all selected objects together)
- ❓ Group delete (DELETE key)
- ❓ Group copy (Ctrl+C)
- ❓ Group cut (Ctrl+X)
- ❓ Group paste at pointer position (Ctrl+V)
- ❓ All operations work consistently regardless of selection method

## Current Architecture

### Selection Components

1. **SelectionManager** (`src/shypn/edit/selection_manager.py`)
   - Manages selection state (set of object IDs)
   - Handles select/deselect operations
   - Supports multi-select (Ctrl+Click)
   - Integrates with DragController
   - Selection modes: NORMAL and EDIT

2. **RectangleSelection** (`src/shypn/edit/rectangle_selection.py`)
   - Rubber-band rectangle selection
   - Drag to create selection box
   - Selects objects within bounds
   - Visual rendering (blue dashed border)

3. **LassoSelector** (`src/shypn/edit/lasso_selector.py`)
   - Freeform polygon selection
   - Click-and-drag creates path
   - Point-in-polygon detection
   - Visual rendering (blue dashed path)

4. **DragController** (`src/shypn/edit/drag_controller.py`)
   - Handles drag operations for objects
   - Multi-object dragging support
   - Position tracking for undo
   - Snap-to-grid support
   - Axis constraints (horizontal/vertical)

### Key Event Handlers

Located in `src/shypn/helpers/model_canvas_loader.py`:

- `_on_button_press_event()` - Mouse down (line ~1062)
- `_on_button_release_event()` - Mouse up (line ~1188)
- `_on_motion_notify_event()` - Mouse move (line ~1266)
- `_on_key_press_event()` - Keyboard (line ~1375)

### Current Operations

**DELETE Key** (Line ~1390):
```python
if event.keyval == Gdk.KEY_Delete or event.keyval == Gdk.KEY_KP_Delete:
    selected = manager.selection_manager.get_selected_objects()
    if selected:
        # Delete all selected objects
        for obj in selected:
            manager.delete_object(obj)
        # Push to undo stack
        manager.undo_manager.push(DeleteOperation(delete_data, manager))
```

**Copy (Ctrl+C)** (Line ~1406):
```python
if is_ctrl and not is_shift and event.keyval == Gdk.KEY_c:
    selected = manager.selection_manager.get_selected_objects()
    if selected:
        self._copy_selection(manager)
```

**Cut (Ctrl+X)** (Line ~1399):
```python
if is_ctrl and not is_shift and event.keyval == Gdk.KEY_x:
    selected = manager.selection_manager.get_selected_objects()
    if selected:
        self._cut_selection(manager, widget)
```

**Paste (Ctrl+V)** (Line ~1413):
```python
if is_ctrl and not is_shift and event.keyval == Gdk.KEY_v:
    if hasattr(self, '_clipboard') and self._clipboard:
        self._paste_selection(manager, widget)
```

## Issues Identified

### 1. Paste Position - NOT at Pointer ❌

**Current Behavior** (Line ~2639):
```python
def _paste_selection(self, manager, widget):
    # Paste with offset to avoid exact overlap
    offset_x, offset_y = 30, 30  # FIXED OFFSET!
    
    for item in self._clipboard:
        if item['type'] == 'place':
            place = manager.add_place(
                item['x'] + offset_x,  # Original position + fixed offset
                item['y'] + offset_y
            )
```

**Problem**: Pastes at `original_position + (30, 30)`, NOT at pointer position!

**Expected**: Paste should be relative to current mouse/pointer position.

### 2. Missing get_move_data_for_undo() Method ❌

**Used in code** (Line ~1239):
```python
if manager.selection_manager.is_dragging():
    move_data = manager.selection_manager.get_move_data_for_undo()
```

**Problem**: Method doesn't exist in SelectionManager!

**Location**: Should be in `src/shypn/edit/selection_manager.py`

### 3. Rectangle Selection Multi-Select Inconsistency ⚠️

**Current** (`rectangle_selection.py`, line ~179):
```python
def select_objects(self, manager, multi: bool = False):
    # Clear existing selection if not multi-select
    if not multi:
        manager.clear_all_selections()
```

**Issue**: Rectangle selection has `multi` parameter but:
- Not passed from event handlers
- No way to do Ctrl+Rectangle (add to selection)

### 4. Lasso Selection Behavior

**Current** (`lasso_selector.py`, line ~60):
```python
def finish_lasso(self):
    # Find objects inside polygon
    selected = []
    for obj in self.canvas_manager.get_all_objects():
        if self._is_point_in_polygon(obj.x, obj.y, self.points):
            selected.append(obj)
    
    # ALWAYS clears selection first
    self.canvas_manager.selection_manager.clear_selection()
```

**Issue**: Lasso ALWAYS clears selection - no multi-select support!

### 5. Inconsistent Selection Clearing

Different methods used:
- `manager.selection_manager.clear_selection()` 
- `manager.clear_all_selections()`

Need to verify these are equivalent.

### 6. Drag Behavior Differences

**Single-click drag** (Line ~1136):
```python
manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
```

**Rectangle/Lasso**: Objects selected, but drag not automatically initiated

**Question**: Should selected group be draggable immediately?

## Desired Unified Behavior

### Selection Methods Should Be Equivalent

All selection methods (click, Ctrl+Click, rectangle, lasso) should:
1. Support single-select mode (clear others)
2. Support multi-select mode (add to selection with Ctrl)
3. Result in same selected state
4. Enable same group operations

### Group Operations Should Work Consistently

Once objects are selected (by ANY method):
1. **Drag**: All selected objects move together
2. **Delete** (DEL): Delete all selected objects
3. **Copy** (Ctrl+C): Copy all selected to clipboard
4. **Cut** (Ctrl+X): Copy and delete all selected
5. **Paste** (Ctrl+V): Paste relative to pointer position

### Expected Flow

```
User selects objects (any method):
  - Click → select single object
  - Ctrl+Click → toggle object in/out of selection
  - Rectangle drag → select all in rectangle
  - Ctrl+Rectangle drag → ADD all in rectangle to selection
  - Lasso drag → select all in polygon
  - Ctrl+Lasso drag → ADD all in polygon to selection

Selected objects shown with blue highlight

User performs operation:
  - Click-and-drag selected → all move together (DragController)
  - DELETE key → all deleted with undo support
  - Ctrl+C → all copied to clipboard
  - Ctrl+X → all cut to clipboard
  - Ctrl+V → all pasted at mouse pointer position (not fixed offset!)
  - ESC → clear selection / cancel drag
```

## Implementation Plan

### Phase 1: Fix Missing Method (CRITICAL)

**File**: `src/shypn/edit/selection_manager.py`

**Add method**:
```python
def get_move_data_for_undo(self):
    """Get move data for undo operation.
    
    Returns:
        Dictionary with initial positions of dragged objects
    """
    if hasattr(self, '_drag_controller') and self._drag_controller.is_dragging():
        return self._drag_controller.get_initial_positions()
    return {}
```

### Phase 2: Fix Paste Position

**File**: `src/shypn/helpers/model_canvas_loader.py`

**Current** (Line ~2639):
```python
def _paste_selection(self, manager, widget):
    offset_x, offset_y = 30, 30  # WRONG!
```

**Fixed**:
```python
def _paste_selection(self, manager, widget, pointer_x=None, pointer_y=None):
    """Paste objects from clipboard at pointer position.
    
    Args:
        manager: ModelCanvasManager
        widget: GtkDrawingArea
        pointer_x: World X coordinate of pointer (None = use last known)
        pointer_y: World Y coordinate of pointer (None = use last known)
    """
    if not self._clipboard:
        return
    
    # Get clipboard center
    clipboard_min_x = min(item['x'] for item in self._clipboard if 'x' in item)
    clipboard_min_y = min(item['y'] for item in self._clipboard if 'y' in item)
    clipboard_max_x = max(item['x'] for item in self._clipboard if 'x' in item)
    clipboard_max_y = max(item['y'] for item in self._clipboard if 'y' in item)
    clipboard_center_x = (clipboard_min_x + clipboard_max_x) / 2
    clipboard_center_y = (clipboard_min_y + clipboard_max_y) / 2
    
    # Get paste position
    if pointer_x is None or pointer_y is None:
        # Use canvas center if no pointer position
        pointer_x, pointer_y = manager.viewport_width / 2, manager.viewport_height / 2
        pointer_x, pointer_y = manager.screen_to_world(pointer_x, pointer_y)
    
    # Calculate offset to center clipboard at pointer
    offset_x = pointer_x - clipboard_center_x
    offset_y = pointer_y - clipboard_center_y
    
    # ... rest of paste logic
```

**Update caller** (Line ~1413):
```python
if is_ctrl and not is_shift and event.keyval == Gdk.KEY_v:
    if hasattr(self, '_clipboard') and self._clipboard:
        # Get current pointer position
        pointer = widget.get_pointer()
        world_x, world_y = manager.screen_to_world(pointer.x, pointer.y)
        self._paste_selection(manager, widget, world_x, world_y)
        return True
```

### Phase 3: Add Multi-Select to Rectangle Selection

**File**: `src/shypn/helpers/model_canvas_loader.py`

**Button release handler** (Line ~1188):
```python
def _on_button_release_event(self, widget, event, manager):
    # ... existing code ...
    
    # Rectangle selection finish
    if manager.rectangle_selection.active:
        is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        bounds = manager.rectangle_selection.finish()
        if bounds:
            manager.rectangle_selection.select_objects(
                manager, 
                multi=is_ctrl  # ADD THIS - support Ctrl+Rectangle
            )
        widget.queue_draw()
        return True
```

### Phase 4: Add Multi-Select to Lasso Selection

**File**: `src/shypn/edit/lasso_selector.py`

**Modify finish_lasso**:
```python
def finish_lasso(self, multi=False):
    """Finish lasso and select objects inside.
    
    Args:
        multi: If True, add to selection. If False, replace selection.
    """
    if not self.is_active or len(self.points) < 3:
        self.cancel_lasso()
        return
    
    # Close the polygon
    if self.points[0] != self.points[-1]:
        self.points.append(self.points[0])
    
    # Find objects inside polygon
    selected = []
    for obj in self.canvas_manager.get_all_objects():
        if self._is_point_in_polygon(obj.x, obj.y, self.points):
            selected.append(obj)
    
    # Update selection
    if not multi:  # NEW: Only clear if not multi-select
        self.canvas_manager.selection_manager.clear_selection()
    
    for obj in selected:
        self.canvas_manager.selection_manager.select(
            obj, 
            multi=True,  # Always add to selection (already cleared if needed)
            manager=self.canvas_manager
        )
    
    # Reset
    self.is_active = False
    self.points = []
```

**Update callers** (in model_canvas_loader.py):
```python
def _on_button_release_event(self, widget, event, manager):
    # ... lasso finish ...
    if lasso_state.get('active', False):
        is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        lasso_state['selector'].finish_lasso(multi=is_ctrl)  # ADD multi parameter
        lasso_state['active'] = False
        widget.queue_draw()
        return True
```

### Phase 5: Store Pointer Position

**File**: `src/shypn/helpers/model_canvas_loader.py`

**Add instance variable** (in __init__):
```python
self._last_pointer_world_x = 0.0
self._last_pointer_world_y = 0.0
```

**Update in motion handler** (Line ~1266):
```python
def _on_motion_notify_event(self, widget, event, manager):
    # Store pointer position for paste operation
    self._last_pointer_world_x, self._last_pointer_world_y = \
        manager.screen_to_world(event.x, event.y)
    
    # ... existing motion code ...
```

**Use in paste** (Line ~1413):
```python
if is_ctrl and not is_shift and event.keyval == Gdk.KEY_v:
    if hasattr(self, '_clipboard') and self._clipboard:
        self._paste_selection(
            manager, 
            widget, 
            self._last_pointer_world_x, 
            self._last_pointer_world_y
        )
        return True
```

### Phase 6: Verify Group Drag

**Check**: Does DragController properly handle all selected objects?

**File**: `src/shypn/edit/selection_manager.py` (Line ~246)

```python
def start_drag(self, clicked_obj, screen_x: float, screen_y: float, manager):
    """Start dragging selected objects if clicking on a selected object."""
    if clicked_obj and clicked_obj.selected:
        self.__init_drag_controller()
        selected_objs = self.get_selected_objects(manager)
        
        # Filter to only draggable objects
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        draggable_objs = [obj for obj in selected_objs 
                        if isinstance(obj, (Place, Transition))]
        
        if draggable_objs:
            self._drag_controller.start_drag(draggable_objs, screen_x, screen_y)
            return True
    return False
```

**Status**: ✅ Looks correct - drags ALL selected objects

### Phase 7: Unified Testing

Test all combinations:

1. **Single Click Selection**
   - Select object → can drag, delete, copy, cut, paste

2. **Multi-Click Selection**
   - Ctrl+Click multiple → can drag all, delete all, copy all

3. **Rectangle Selection**
   - Drag rectangle → can drag all, delete all, copy all
   - Ctrl+Drag rectangle → adds to selection

4. **Lasso Selection**
   - Drag lasso → can drag all, delete all, copy all
   - Ctrl+Drag lasso → adds to selection

5. **Mixed Selection**
   - Click + Ctrl+Rectangle → combined selection
   - All operations work on combined set

6. **Paste Position**
   - Copy objects → Move pointer → Paste → Objects appear at pointer!

## Files to Modify

1. **`src/shypn/edit/selection_manager.py`**
   - Add `get_move_data_for_undo()` method

2. **`src/shypn/edit/lasso_selector.py`**
   - Add `multi` parameter to `finish_lasso()`

3. **`src/shypn/helpers/model_canvas_loader.py`**
   - Add `_last_pointer_world_x/y` tracking
   - Fix `_paste_selection()` to use pointer position
   - Pass `multi` to rectangle selection
   - Pass `multi` to lasso selection
   - Update paste caller to pass pointer position

## Benefits of Unification

### ✅ Consistency
- All selection methods behave the same
- Same group operations available regardless of selection method
- Predictable user experience

### ✅ Functionality
- Paste at pointer (not fixed offset!)
- Multi-select with any selection method
- Complete undo support

### ✅ Maintainability
- Single code path for group operations
- Easy to test and verify
- Clear separation of concerns

## Testing Strategy

### Manual Testing Checklist

- [ ] Single-click select → drag works
- [ ] Single-click select → DELETE works
- [ ] Single-click select → Ctrl+C → Ctrl+V at pointer works
- [ ] Ctrl+Click multi-select → drag all works
- [ ] Ctrl+Click multi-select → DELETE all works
- [ ] Ctrl+Click multi-select → Ctrl+C → Ctrl+V at pointer works
- [ ] Rectangle select → all operations work
- [ ] Ctrl+Rectangle adds to selection
- [ ] Lasso select → all operations work
- [ ] Ctrl+Lasso adds to selection
- [ ] Mixed selection (click + rectangle) → all operations work
- [ ] Paste position matches pointer location
- [ ] ESC cancels drag
- [ ] ESC clears selection

### Automated Testing

Create test suite:
- Selection state management
- Multi-select combinations
- Group operations on selected sets
- Paste position calculation
- Undo/redo for group operations

## Implementation Priority

1. **HIGH**: Add `get_move_data_for_undo()` - Fixes crash/error
2. **HIGH**: Fix paste position - Major usability issue
3. **MEDIUM**: Add multi-select to rectangle/lasso - Feature completion
4. **MEDIUM**: Track pointer position - Enables proper paste
5. **LOW**: Comprehensive testing - Validation

## Conclusion

The selection system has good architecture but needs:
1. Missing method implementation
2. Paste position fix (critical usability)
3. Multi-select support for area selection methods
4. Pointer tracking for paste

All group operations (drag, delete, copy, cut, paste) already work on selected sets - just need to unify selection behavior across all selection methods.

**Goal**: Make selection method irrelevant - once objects are selected, all operations work the same way.
