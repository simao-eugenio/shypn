# New Project Button Fix - Summary

## Problem
"New Project" button was causing app crash with Wayland Error 71 (Protocol error).

## Root Cause
The **left panel** passes its own hidden window as parent to `ProjectActionsController`, which then passes it to `ProjectDialogManager`. When the panel is **attached** to the main window, the panel window is hidden but the dialog manager still tries to use it as parent → **Wayland protocol violation**.

## The Fix

**File**: `src/shypn/helpers/left_panel_loader.py`  
**Method**: `attach_to()`  
**Line**: ~260

### Change Made
```python
def attach_to(self, container, parent_window=None):
    # ...
    if parent_window:
        self.parent_window = parent_window
        # ADDED: Update project controller so dialogs use main window, not hidden panel window
        if self.project_controller:
            self.project_controller.set_parent_window(parent_window)
    # ...
```

## Why This Works

When the left panel attaches to the main window:
1. Main window reference passed as `parent_window` parameter
2. Now we call `project_controller.set_parent_window(parent_window)`
3. This propagates to `ProjectDialogManager.parent_window`
4. Dialog now correctly attaches to **visible main window** instead of **hidden panel window**

## Test Results

### Before Fix ❌
```
[Click "New Project"]
Gdk-Message: Error 71 (Protocol error) dispatching to Wayland display.
[CRASH]
```

### After Fix ✅
```
[ProjectActions] New Project button clicked
[ProjectDialogManager] Loading new project dialog...
[ProjectDialogManager] Set transient for: <GtkApplicationWindow>  ← CORRECT!
[ProjectDialogManager] Running dialog...
[ProjectDialogManager] Dialog returned response: -6  ← WORKS!
```

## Verified Working
- ✅ New Project button shows dialog
- ✅ Dialog displays correctly
- ✅ Can cancel dialog
- ✅ Can create projects
- ✅ No Wayland errors
- ✅ App remains stable

## Documentation
See `GTK_PARENT_WINDOW_AUDIT.md` for comprehensive analysis of all dialog parent window issues in the codebase.

---
**Status**: ✅ **FIXED AND VERIFIED**  
**Date**: 2025-01-06
