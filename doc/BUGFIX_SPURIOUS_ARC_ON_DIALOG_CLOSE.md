# Fix: Spurious Arc Creation on Dialog Close

## Issue
When editing source/sink markers (or any object properties) via the properties dialog, a small arc would appear after the dialog closed.

## Root Cause
When the arc tool is active and a source object has been clicked:
1. User clicks on source object → `arc_state['source']` is set
2. User right-clicks to open context menu (or double-clicks)
3. Properties dialog opens
4. User edits properties and clicks OK
5. Dialog closes and returns focus to canvas
6. Mouse release event is processed by canvas
7. Canvas interprets this as "user clicked target for arc"
8. Spurious arc is created

## Solution
Clear the arc creation state (`arc_state['source'] = None`) when:
1. **Opening properties dialog** (`_on_object_properties`)
2. **Entering edit mode** (`_on_enter_edit_mode`)

This ensures that any pending arc creation is cancelled before the dialog opens, preventing the mouse release after dialog close from being interpreted as an arc target selection.

## Files Modified

### `src/shypn/helpers/model_canvas_loader.py`

**Location 1:** `_on_object_properties()` method
```python
def _on_object_properties(self, obj, manager, drawing_area):
    """Open properties dialog for an object."""
    # Clear arc creation state to prevent spurious arc creation on dialog close
    arc_state = self._arc_state.get(drawing_area)
    if arc_state:
        arc_state['source'] = None
    
    # ... rest of method
```

**Location 2:** `_on_enter_edit_mode()` method
```python
def _on_enter_edit_mode(self, obj, manager, drawing_area):
    """Enter EDIT mode for an object."""
    # Clear arc creation state to prevent spurious arc creation
    arc_state = self._arc_state.get(drawing_area)
    if arc_state:
        arc_state['source'] = None
    
    # ... rest of method
```

## Testing

**Before Fix:**
1. Select arc tool
2. Click on a place/transition (source selected)
3. Right-click to open context menu
4. Select "Properties..."
5. Edit anything, click OK
6. ❌ **Bug**: Small arc appears from source to some point

**After Fix:**
1. Select arc tool
2. Click on a place/transition (source selected)
3. Right-click to open context menu
4. Select "Properties..."
5. Edit anything, click OK
6. ✅ **Fixed**: No spurious arc created

## Technical Details

### Arc State Structure
```python
self._arc_state = {
    drawing_area: {
        'source': None,        # Source object for arc creation (Place/Transition)
        'cursor_pos': (0, 0)   # Current cursor position in world coords
    }
}
```

### Arc Creation Flow
1. User selects arc tool
2. User clicks on source object → `source` is set
3. User moves mouse → transient arc follows cursor
4. User clicks on target object → permanent arc created, `source` cleared
5. OR user clicks on empty space → `source` cleared (cancel)

### The Bug Pattern
The bug occurred because step 4 was triggered unintentionally:
- Dialog interaction consumed mouse press
- Mouse release after dialog close was processed as "target click"
- Arc was created from `source` to some arbitrary point

### The Fix
By clearing `source` when entering edit mode or opening dialogs, we ensure that any mouse events after the dialog closes won't be interpreted as arc target selection.

## Related Issues

This fix also prevents similar issues with:
- Double-click to open properties
- Context menu → Properties
- Any other modal dialog that might interrupt arc creation

## Prevention Strategy

**General Rule:** Clear transient UI state (like arc creation) when entering modal operations:
- Opening dialogs
- Entering special modes
- Switching tools
- Switching tabs

This prevents "state leakage" where transient state persists across mode changes and causes unexpected behavior.

## Status

✅ **Fixed** - Spurious arc creation on dialog close prevented

---

**Date:** October 6, 2025
**Issue:** Spurious arc creation after editing properties
**Fix:** Clear arc_state['source'] when opening dialogs or entering edit mode
