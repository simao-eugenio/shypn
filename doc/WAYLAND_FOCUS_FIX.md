# Wayland Focus Issue - Orphaned Widgets Analysis and Fix

**Date**: October 18, 2025  
**Issue**: App automatically closes when losing focus on Wayland  
**Root Cause**: Orphaned dialog widgets not properly destroyed

## Problem Analysis

### Symptoms
- Application closes when losing focus
- Happens after UI refactoring (dialogs)
- Wayland-specific issue (orphaned widgets provoke Wayland failures)

### Root Cause
Dialog loaders create GTK dialogs and call `.run()` but **never explicitly call `.destroy()`** after the dialog closes. While `_on_response()` handler calls `dialog.destroy()`, when using `.run()` this may not reliably execute in all code paths, especially if the dialog is closed via window manager (X button) or loses focus.

### Affected Files
1. `src/shypn/helpers/place_prop_dialog_loader.py`
2. `src/shypn/helpers/transition_prop_dialog_loader.py`
3. `src/shypn/helpers/arc_prop_dialog_loader.py`
4. `src/shypn/helpers/model_canvas_loader.py` (dialog caller)

## Current Code Pattern (BROKEN)

```python
# Dialog Loader
class PlacePropDialogLoader:
    def _on_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
            # ... mark dirty, emit signal
        dialog.destroy()  # ❌ Only called if _on_response fires
    
    def run(self):
        return self.dialog.run()  # ❌ No guaranteed cleanup

# Caller
dialog_loader = create_place_prop_dialog(obj, parent_window=self.parent_window)
response = dialog_loader.run()  # ❌ Dialog never destroyed if _on_response fails
```

### Why This Fails
1. `.run()` enters GTK main loop but doesn't guarantee `_on_response` is called
2. Window manager close (X button) may not trigger `response` signal properly
3. Focus loss can interrupt dialog before `_on_response` fires
4. Orphaned dialog widgets remain in memory
5. Wayland detects orphaned widgets and crashes/closes app

## Fix Strategy

### Pattern 1: Explicit Destroy in Caller (RECOMMENDED)
```python
# Caller ensures cleanup
dialog_loader = create_place_prop_dialog(obj, parent_window=self.parent_window)
try:
    response = dialog_loader.run()
    if response == Gtk.ResponseType.OK:
        # Handle OK response
        pass
finally:
    dialog_loader.destroy()  # ✅ Always destroys
```

### Pattern 2: Add destroy() Method to Loaders
```python
# Dialog Loader
class PlacePropDialogLoader:
    def destroy(self):
        """Ensure dialog and all widgets are properly destroyed."""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        # Clean up other widget references
        self.color_picker = None
        self.builder = None
    
    def run(self):
        return self.dialog.run()

# Caller
dialog_loader = create_place_prop_dialog(obj, parent_window=self.parent_window)
try:
    response = dialog_loader.run()
finally:
    dialog_loader.destroy()  # ✅ Explicit cleanup
```

### Pattern 3: Context Manager (BEST PRACTICE)
```python
# Dialog Loader
class PlacePropDialogLoader:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()
        return False

# Caller
with create_place_prop_dialog(obj, parent_window=self.parent_window) as dialog_loader:
    response = dialog_loader.run()
    if response == Gtk.ResponseType.OK:
        # Handle OK
        pass
# ✅ Automatic cleanup via context manager
```

## Recommended Fix

**Use Pattern 2** (add destroy() method) for immediate fix, then migrate to Pattern 3 (context manager) for best practices.

### Immediate Actions

1. **Add `destroy()` method to all three dialog loaders**
   - PlacePropDialogLoader
   - TransitionPropDialogLoader
   - ArcPropDialogLoader

2. **Update model_canvas_loader.py to call destroy()**
   - Wrap `dialog_loader.run()` in try/finally
   - Always call `dialog_loader.destroy()` in finally block

3. **Remove `dialog.destroy()` from `_on_response()`**
   - Let explicit `destroy()` method handle it
   - Prevents double-destroy issues

4. **Add widget cleanup to destroy() method**
   - Set all widget references to None
   - Prevent memory leaks

## Implementation Plan

### Step 1: Add destroy() to PlacePropDialogLoader
```python
def destroy(self):
    """Destroy dialog and clean up widget references."""
    if self.dialog:
        self.dialog.destroy()
        self.dialog = None
    self.color_picker = None
    self.builder = None
    self.place_obj = None

def _on_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
        self._apply_changes()
        if self.persistency_manager:
            self.persistency_manager.mark_dirty()
        self.emit('properties-changed')
    # Don't destroy here - let explicit destroy() handle it
```

### Step 2: Add destroy() to TransitionPropDialogLoader
```python
def destroy(self):
    """Destroy dialog and clean up widget references."""
    if self.dialog:
        self.dialog.destroy()
        self.dialog = None
    self.color_picker = None
    self.locality_widget = None
    self.builder = None
    self.transition_obj = None

def _on_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
        # Validate before applying
        if not self._validate_fields():
            return  # Keep dialog open
        self._apply_changes()
        if self.persistency_manager:
            self.persistency_manager.mark_dirty()
        self.emit('properties-changed')
    # Don't destroy here
```

### Step 3: Add destroy() to ArcPropDialogLoader
```python
def destroy(self):
    """Destroy dialog and clean up widget references."""
    if self.dialog:
        self.dialog.destroy()
        self.dialog = None
    self.color_picker = None
    self.builder = None
    self.arc_obj = None

def _on_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
        self._apply_changes()
        if self.persistency_manager:
            self.persistency_manager.mark_dirty()
        self.emit('properties-changed')
    # Don't destroy here
```

### Step 4: Update model_canvas_loader.py
```python
# Around line 2754
dialog_loader.connect('properties-changed', on_properties_changed)

try:
    response = dialog_loader.run()
finally:
    # Always destroy dialog to prevent orphaned widgets
    dialog_loader.destroy()

# Restore original tool if we switched it
if original_tool == 'arc':
    manager.set_tool('arc')

# ... rest of cleanup code
```

## Testing Checklist

After fix:
- [ ] Open place properties dialog, click OK → dialog closes cleanly
- [ ] Open place properties dialog, click Cancel → dialog closes cleanly
- [ ] Open place properties dialog, click X (window close) → dialog closes cleanly
- [ ] Open dialog, switch to another app, come back → app still running
- [ ] Open dialog, click outside dialog (lose focus) → app still running
- [ ] Repeat all above for transition properties dialog
- [ ] Repeat all above for arc properties dialog
- [ ] Run app for extended period, open/close dialogs many times → no memory leaks

## Additional Orphaned Widget Checks

### Other Potential Sources

1. **Color Picker Widget**
   - Check if properly destroyed with parent dialog
   - May need explicit cleanup in destroy()

2. **Locality Widget** (TransitionPropDialogLoader)
   - Custom widget, may not auto-destroy
   - Add explicit cleanup in destroy()

3. **Builder Objects**
   - GTK.Builder holds references to all widgets
   - Set to None in destroy() to release

4. **Signal Connections**
   - Dialog signal handlers auto-disconnect on destroy
   - Custom widgets may need manual disconnection

5. **Error Dialogs**
   - Check that error dialogs in validation are destroyed
   - Use transient_for properly

## Long-Term Best Practices

1. **Always use context managers for dialogs**
2. **Never rely on implicit cleanup**
3. **Test on Wayland explicitly**
4. **Use weak references for circular refs**
5. **Implement `__del__` with warnings for un-destroyed widgets**
6. **Add unit tests for dialog lifecycle**

## References

- GTK3 Dialog Documentation: https://docs.gtk.org/gtk3/class.Dialog.html
- Wayland Protocol: https://wayland.freedesktop.org/
- Python GTK Memory Management: https://pygobject.readthedocs.io/

---

**Status**: Ready to implement  
**Priority**: HIGH (causes app crashes)  
**Estimated Time**: 1 hour
