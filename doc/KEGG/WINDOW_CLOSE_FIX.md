# Pathway Panel Window Close Fix

## Issue

**Problem**: Clicking the X button on the floating pathway panel window caused a **Segmentation Fault (core dumped)**.

**Exit Code**: 139 (SIGSEGV - segmentation violation)

## Root Cause

When a GTK window's close button (X) is clicked, GTK sends a `delete-event` signal. If this signal is not handled, GTK's default behavior is to **destroy the window object**.

In our case:
1. The pathway panel window object (`self.window`) is created once and reused
2. The window is referenced by multiple parts of the code (loader, builder, parent window)
3. When GTK destroyed the window, these references became invalid
4. Accessing invalid memory references → **Segmentation Fault**

## Solution

### Code Changes

**File**: `src/shypn/helpers/pathway_panel_loader.py`

#### 1. Connected delete-event Handler (Line ~93)

```python
# Connect delete-event to prevent window destruction
# When X button is clicked, just hide the window instead of destroying it
self.window.connect('delete-event', self._on_delete_event)
```

#### 2. Implemented Handler Method (Lines ~148-175)

```python
def _on_delete_event(self, window, event):
    """Handle window close button (X) - hide instead of destroy.
    
    When user clicks X on floating window, we don't want to destroy
    the window (which causes segfault), just hide it and dock it back.
    
    Args:
        window: The window being closed
        event: The delete event
        
    Returns:
        bool: True to prevent default destroy behavior
    """
    # Hide the window
    self.hide()
    
    # Update float button to inactive state
    if self.float_button and self.float_button.get_active():
        self._updating_button = True
        self.float_button.set_active(False)
        self._updating_button = False
    
    # Dock back if we have a container
    if self.parent_container:
        self.attach_to(self.parent_container, self.parent_window)
    
    # Return True to prevent window destruction
    return True
```

## How It Works

### Before Fix:
```
User clicks X → GTK sends delete-event → No handler exists
                ↓
GTK default behavior: destroy window → Invalid memory references
                ↓
Segmentation Fault (Exit Code 139)
```

### After Fix:
```
User clicks X → GTK sends delete-event → _on_delete_event() called
                ↓
Handler hides window (doesn't destroy)
                ↓
Updates float button state
                ↓
Docks panel back to main window
                ↓
Returns True (prevents GTK default destroy)
                ↓
✅ Clean closure, no crash
```

## Behavior After Fix

When user clicks X on floating pathway panel:
1. ✅ Window hides smoothly
2. ✅ Float button (⇲) updates to inactive state
3. ✅ Panel docks back to right_dock_area
4. ✅ No segmentation fault
5. ✅ Window object preserved for reuse
6. ✅ Can be shown again by clicking "Pathways" toggle button

## Testing

### Test Script Created
`test_pathway_panel_close.py` - Isolated test for close behavior

### Manual Testing Steps
1. Launch application: `python3 src/shypn.py`
2. Click "Pathways" button → Panel docks on right
3. Click float button (⇲) → Panel becomes floating window
4. Click X button on floating window
5. ✅ Window closes cleanly without crash
6. ✅ Panel is hidden
7. Click "Pathways" button again → Panel reappears docked

### Expected Results
- No "Segmentation fault (core dumped)" message
- No Exit Code 139
- Clean window closure
- Panel can be reshown multiple times
- Float/dock cycle works repeatedly

## Similar Patterns in Codebase

This fix follows standard GTK window management patterns:
- Windows should be **hidden**, not **destroyed**, when they need to be reused
- The `delete-event` handler should return `True` to prevent default destroy
- Window lifecycle should be managed by the application, not GTK defaults

**Note**: The left and right panels likely don't have this issue because they may not be using floating windows in the same way, or they may already have proper handlers implemented.

## Related Documentation

- **PANEL_INTEGRATION_GUIDE.md** - Updated to reflect safe close behavior
- **MUTUAL_EXCLUSIVITY_SUMMARY.md** - Documents panel lifecycle
- **ARCHITECTURE_STATUS.md** - Notes panel loader implementation

## Verification

✅ **Issue**: Segmentation fault on window close  
✅ **Fix**: Added delete-event handler to hide instead of destroy  
✅ **Testing**: Test script created for isolated testing  
✅ **Documentation**: Updated panel behavior documentation  
✅ **Status**: Ready for end-to-end testing  

## Summary

The segmentation fault was caused by GTK destroying a window object that was still being referenced by the application. The fix intercepts the `delete-event` signal and hides the window instead of allowing GTK to destroy it. This preserves the window object for reuse and prevents memory access violations.

**Key Insight**: In GTK applications with reusable windows, always handle `delete-event` and return `True` to prevent default destruction behavior when you want to preserve the window object.
