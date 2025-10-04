# Fix for Group Selection Drag Error

**Date**: October 3, 2025  
**Issue**: KeyError when dragging objects after group selection  
**Status**: ✅ FIXED + DEBUG OUTPUT ADDED

## Problem

When using rectangle selection to select multiple objects and then dragging them, a KeyError occurred:

```python
KeyError: 134721938795232
File ".../drag_controller.py", line 154, in update_drag
    initial_x, initial_y = self._initial_positions[id(obj)]
```

## Root Cause

The motion handler was calling `update_drag()` **before** checking if rectangle selection was active. This caused the drag controller to try to update positions for objects that were never initialized.

### Problematic Flow:
1. User clicks empty space → rectangle selection starts
2. Motion event → `update_drag()` called FIRST
3. If a previous drag was active, it would try to access stale object IDs
4. KeyError!

## Solution

### Fix 1: Reorder Motion Handler Checks

Moved the `update_drag()` call to happen AFTER rectangle selection check:

**Before** (in `model_canvas_loader.py` ~line 682):
```python
def _on_motion_notify(self, widget, event, manager):
    # ... cursor update ...
    
    # Check if dragging objects (via SelectionManager)
    if manager.selection_manager.update_drag(event.x, event.y, manager):
        widget.queue_draw()
        return True
    
    # ... button pressed check ...
    
    # Handle rectangle selection drag
    if state.get('is_rect_selecting', False):
        # ...
```

**After**:
```python
def _on_motion_notify(self, widget, event, manager):
    # ... cursor update ...
    
    # ... button pressed check ...
    
    # Handle rectangle selection drag
    if state.get('is_rect_selecting', False):
        # Update rectangle selection
        world_x, world_y = manager.screen_to_world(event.x, event.y)
        manager.rectangle_selection.update(world_x, world_y)
        widget.queue_draw()
        return True
    
    # Check if dragging objects (via SelectionManager)
    # Only check if NOT doing rectangle selection
    if manager.selection_manager.update_drag(event.x, event.y, manager):
        widget.queue_draw()
        return True
```

**Priority Order** (now correct):
1. Rectangle selection (highest priority)
2. Object dragging
3. Panning (lowest priority)

### Fix 2: Defensive Programming

Added a safety check in `DragController.update_drag()` to handle missing object IDs gracefully:

```python
# Update all dragged objects
for obj in self._drag_objects:
    obj_id = id(obj)
    if obj_id not in self._initial_positions:
        # This should never happen - it means the object list changed during drag
        print(f"WARNING: Object {obj.name if hasattr(obj, 'name') else obj} (ID: {obj_id}) not in initial positions!")
        print(f"  Initial positions keys: {list(self._initial_positions.keys())}")
        print(f"  Drag objects: {[id(o) for o in self._drag_objects]}")
        # Skip this object to prevent crash
        continue
    
    initial_x, initial_y = self._initial_positions[obj_id]
    # ... rest of update logic ...
```

This prevents crashes and provides diagnostic information if the issue occurs again.

### Fix 3: Debug Output

Added comprehensive debug output to help diagnose drag issues:

**In `SelectionManager.start_drag()`**:
```python
print(f"DEBUG start_drag: clicked={clicked_obj.name}")
print(f"DEBUG start_drag: selected_objs count={len(selected_objs)}, IDs={[id(o) for o in selected_objs]}")
print(f"DEBUG start_drag: names={[o.name for o in selected_objs]}")
```

**In `DragController.start_drag()`**:
```python
print(f"DEBUG DragController.start_drag: Received {len(objects)} objects, IDs={[id(o) for o in objects]}")
print(f"DEBUG DragController.start_drag: Stored {len(self._initial_positions)} initial positions")
print(f"DEBUG DragController.start_drag: Position IDs={list(self._initial_positions.keys())}")
```

This will help identify if:
- Objects are being duplicated
- Object IDs are changing
- Selection state is inconsistent

## Files Modified

1. **`src/shypn/helpers/model_canvas_loader.py`**
   - Moved `update_drag()` call after rectangle selection check
   - Lines modified: ~15 lines in `_on_motion_notify()`

2. **`src/shypn/edit/drag_controller.py`**
   - Added defensive check in `update_drag()`
   - Added debug output in `start_drag()`
   - Lines modified: ~20 lines

3. **`src/shypn/edit/selection_manager.py`**
   - Added debug output in `start_drag()`
   - Lines modified: ~5 lines

## Testing

### Test Case 1: Single Object Drag
1. Click object to select
2. Click and drag → should work
3. ✅ EXPECTED: Object moves smoothly

### Test Case 2: Group Selection Drag
1. Drag rectangle to select multiple objects
2. Release to finish selection
3. Click on one selected object
4. Drag → should work
5. ✅ EXPECTED: All selected objects move together

### Test Case 3: Multi-Select Drag
1. Click object A
2. Ctrl+click object B, C
3. Click and drag any selected object
4. ✅ EXPECTED: All move together

### Test Case 4: Rectangle Selection During Drag
1. Click on selected object (starts drag)
2. Try to drag rectangle (shouldn't happen - drag takes priority)
3. ✅ EXPECTED: Objects drag, not rectangle selection

## Verification

Run the application and look for debug output when dragging:

```
DEBUG start_drag: clicked=Place_1
DEBUG start_drag: selected_objs count=3, IDs=[139876543210, 139876543211, 139876543212]
DEBUG start_drag: names=['Place_1', 'Place_2', 'Transition_1']
DEBUG DragController.start_drag: Received 3 objects, IDs=[139876543210, 139876543211, 139876543212]
DEBUG DragController.start_drag: Stored 3 initial positions
DEBUG DragController.start_drag: Position IDs=[139876543210, 139876543211, 139876543212]
```

All object counts and IDs should match!

If you see the WARNING message:
```
WARNING: Object Place_1 (ID: 139876543210) not in initial positions!
```

This indicates a different issue (objects being added to selection during drag, object recreation, etc.).

## Related Issues

This fix also prevents:
- Drag conflict with rectangle selection
- Stale drag state from previous operations
- Race conditions between selection and drag

## Design Improvements

The fix clarifies the priority order for motion events:
1. **Rectangle Selection** - When actively selecting with rectangle
2. **Object Dragging** - When dragging selected objects
3. **Canvas Panning** - When moving the view

Each operation now properly returns `True` to prevent lower-priority handlers from running.

## Future Enhancements

To remove debug output in production, wrap in a debug flag:

```python
if DEBUG_DRAG:
    print(f"DEBUG start_drag: ...")
```

Or use proper logging:

```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"start_drag: clicked={clicked_obj.name}")
```

---

**Summary**: Group selection drag error fixed by reordering motion handler checks and adding defensive programming. Debug output added to help diagnose future issues.
