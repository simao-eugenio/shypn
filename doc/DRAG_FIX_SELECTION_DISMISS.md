# Fix for Selection Dismissed When Dragging After Rectangle Selection

**Date**: October 3, 2025  
**Issue**: Rectangle selection dismissed when trying to drag selected objects  
**Status**: ✅ FIXED

## Problem

After selecting multiple objects with rectangle selection, clicking on one of them to start dragging would cause all other objects to be deselected after 300ms.

### Scenario:
1. User drags rectangle to select objects A, B, C ✓
2. User clicks on object A to start dragging all selected objects
3. User starts moving mouse (dragging)
4. After 300ms, objects B and C get deselected ✗
5. Only object A remains selected and moves

### Root Cause:

The delayed single-click mechanism was processing the click on object A after 300ms, calling `toggle_selection(obj, multi=False)` which cleared all other selections since Ctrl was not held.

**Flow**:
```
Click on selected object A
  ↓
start_drag() called ✓
  ↓
Delayed single-click scheduled (300ms) 
  ↓
User moves mouse → drag starts ✓
  ↓
[300ms passes]
  ↓
process_single_click() fires
  ↓
toggle_selection(A, multi=False) → deselects B, C ✗
```

## Solution

### Fix 1: Cancel Pending Click When Drag Starts

In the motion handler, when `update_drag()` returns True (drag is active), cancel any pending single-click:

```python
# Check if dragging objects (via SelectionManager)
if manager.selection_manager.update_drag(event.x, event.y, manager):
    # Cancel any pending single-click processing
    # This prevents selection change when dragging starts
    click_state = self._click_state.get(widget)
    if click_state and click_state.get('pending_timeout'):
        from gi.repository import GLib
        GLib.source_remove(click_state['pending_timeout'])
        click_state['pending_timeout'] = None
        click_state['pending_click_data'] = None
    
    widget.queue_draw()
    return True
```

**Location**: `model_canvas_loader.py`, `_on_motion_notify()` method (~line 710)

### Fix 2: Check Drag State in Delayed Callback

In `process_single_click()`, check if dragging started before processing the click:

```python
def process_single_click():
    data = click_state['pending_click_data']
    if data is None:
        return False
    
    # ... get obj, ctrl, etc ...
    
    # Check if drag started (if so, don't process single-click)
    if mgr.selection_manager.is_dragging():
        click_state['pending_timeout'] = None
        click_state['pending_click_data'] = None
        return False
    
    # ... rest of single-click processing ...
```

**Location**: `model_canvas_loader.py`, `_on_button_press()` method, inside `process_single_click()` (~line 540)

### Fix 3: Set Drag State When Clicking Selected Object

When clicking on an already-selected object, set the drag state so motion handler can work:

```python
# Check if clicking on already-selected object (potential drag start)
if clicked_obj.selected and not is_double_click:
    # Start potential drag
    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
    
    # IMPORTANT: Set drag state so motion handler can update drag
    state['active'] = True
    state['button'] = event.button
    state['start_x'] = event.x
    state['start_y'] = event.y
    state['is_panning'] = False
    state['is_rect_selecting'] = False
```

**Location**: `model_canvas_loader.py`, `_on_button_press()` method (~line 498)

## Files Modified

1. **`src/shypn/helpers/model_canvas_loader.py`**
   - Added drag state initialization when clicking selected object (~line 498)
   - Added pending click cancellation in motion handler (~line 710)
   - Added drag check in `process_single_click()` callback (~line 540)
   - Lines modified: ~20 lines

## Testing

### Test Case 1: Rectangle Selection → Drag
1. Drag rectangle to select multiple objects (A, B, C)
2. Release to complete selection
3. Click on object A
4. Immediately start dragging
5. ✅ EXPECTED: All three objects (A, B, C) move together
6. ✅ EXPECTED: Selection remains intact

### Test Case 2: Ctrl+Click Selection → Drag
1. Click object A
2. Ctrl+Click object B
3. Ctrl+Click object C
4. Click on any selected object
5. Start dragging
6. ✅ EXPECTED: All three move together
7. ✅ EXPECTED: Selection remains intact

### Test Case 3: Single Object Drag
1. Click object A (selects it)
2. Click and drag object A
3. ✅ EXPECTED: Object A moves
4. ✅ EXPECTED: No other selections affected

### Test Case 4: Click Without Drag
1. Select multiple objects (rectangle or Ctrl+click)
2. Click on one selected object
3. DON'T move mouse (no drag)
4. Wait 300ms
5. ✅ EXPECTED: After 300ms, single-click processes normally
6. ✅ EXPECTED: Without Ctrl, only clicked object remains selected (normal behavior)

## Design

### Click Handling Priority:
1. **Immediate Actions** (no delay):
   - Double-click → EDIT mode
   - Arc tool clicks
   - Empty space → rectangle selection
   - Selected object → drag preparation

2. **Delayed Actions** (300ms):
   - Single-click → selection toggle
   - ONLY if drag didn't start

### Drag vs Click Detection:
- Click + hold on selected object → **drag prepared**
- If mouse moves → **drag activated**, pending click cancelled
- If mouse doesn't move → **single-click processed** after 300ms

This ensures:
- ✅ Smooth drag initiation
- ✅ No selection changes during drag
- ✅ Normal click behavior when not dragging
- ✅ Double-click still works for EDIT mode

## Related Fixes

This fix complements:
- **DRAG_FIX_GROUP_SELECTION.md** - Rectangle selection priority in motion handler
- **DRAG_INTEGRATION_COMPLETE.md** - Original drag integration

## Debug Output

When dragging after rectangle selection, you should see:

```
# Rectangle selection
[user drags rectangle]

# Release → selection complete
P1 selected (multi) [NORMAL mode]
P2 selected (multi) [NORMAL mode]
T1 selected (multi) [NORMAL mode]

# Click on P1 to drag
DEBUG start_drag: clicked=P1
DEBUG start_drag: selected_objs count=3, IDs=[...]
DEBUG DragController.start_drag: Received 3 objects, IDs=[...]

# Start moving → drag activates
[user moves mouse]
# Pending single-click CANCELLED (no selection change!)

# All 3 objects move together
[objects dragging...]

# Release → drag complete
[all 3 objects in new positions, all still selected]
```

## Timing Details

**Delayed Single-Click**: 300ms (`double_click_threshold`)

**Why the delay?**
- To detect double-clicks (for EDIT mode)
- If second click comes within 300ms → it's a double-click
- If no second click → process as single-click

**Drag vs Click**:
- Mouse moves during 300ms → Cancel pending click, activate drag
- Mouse stays still for 300ms → Process single-click, no drag

This gives a natural feel where:
- Quick click → selection toggle
- Click + drag → move objects
- Double-click → EDIT mode

---

**Summary**: Fixed rectangle selection being dismissed when dragging by cancelling pending single-click when drag starts. Multi-object selection now preserved during drag operations.
