# GTK Parent Window Audit - Dialog Attachment Issues

## Problem Summary

The "New Project" button was causing application crashes with:
```
Gdk-Message: Error 71 (Protocol error) dispatching to Wayland display.
```

This is a Wayland display protocol error caused by dialogs being attached to invalid or non-realized parent windows.

## Root Cause Analysis

### The Bug Chain

1. **LeftPanelLoader initialization** (left_panel_loader.py:136)
   ```python
   self.project_controller = ProjectActionsController(self.builder, parent_window=self.window)
   ```
   - Passes `self.window` (the detached left panel window) as parent

2. **ProjectActionsController initialization** (project_actions_controller.py:57)
   ```python
   self.dialog_manager = ProjectDialogManager(parent_window=parent_window)
   ```
   - Stores the left panel window as parent for all project dialogs

3. **Main app attaches left panel** (shypn.py:251)
   ```python
   left_panel_loader.attach_to(left_dock_area, parent_window=window)
   ```
   - Left panel content moved to main window
   - Left panel window is **hidden** (left_panel_loader.py:265)
   - Main window reference stored in `left_panel_loader.parent_window`
   - **BUT**: ProjectActionsController still has reference to hidden window!

4. **User clicks "New Project"** → Dialog tries to attach to hidden window → **Wayland Error 71**

### Why Standalone Test Worked

The standalone test (test_dialog_standalone.py) worked because:
```python
window = Gtk.Window(title="Test Window")
window.show_all()  # Window is visible and realized
dialog_manager = ProjectDialogManager(parent_window=window)
```
The parent window was properly shown/realized before dialog creation.

### Why Main App Failed

In the main app:
1. Left panel window created but never shown (stays hidden)
2. ProjectActionsController references this hidden window
3. When panel attaches to main window, controller's parent reference not updated
4. Dialog tries to show with hidden parent → Wayland protocol violation

## The Fix

### Primary Fix: Update Parent Window on Attach

**File**: `src/shypn/helpers/left_panel_loader.py`  
**Lines**: 246-261 (in `attach_to()` method)

```python
def attach_to(self, container, parent_window=None):
    """Attach panel to container (embed content in extreme left, hide window).
    
    Args:
        container: Gtk.Box or other container to embed content into.
        parent_window: Optional parent window (stored for float button).
    """
    if self.window is None:
        self.load()
    
    # Store parent window and container for float button callback
    if parent_window:
        self.parent_window = parent_window
        # CRITICAL: Update project controller's parent window so dialogs attach to main window
        if self.project_controller:
            self.project_controller.set_parent_window(parent_window)  # ← ADDED THIS
    self.parent_container = container
    # ... rest of method
```

This ensures when the left panel attaches to main window, the ProjectActionsController (and its ProjectDialogManager) get updated with the correct parent window reference.

### Why This Works

The `ProjectActionsController.set_parent_window()` method (project_actions_controller.py:185-192) propagates the update:
```python
def set_parent_window(self, window):
    """Update parent window reference.
    
    Args:
        window: New parent window for dialogs
    """
    self.parent_window = window
    if self.dialog_manager:
        self.dialog_manager.parent_window = window  # ← Updates dialog manager too
```

Now when "New Project" is clicked:
1. Dialog manager has reference to main window (visible, realized)
2. Dialog attaches properly with `set_transient_for(main_window)`
3. No Wayland protocol error!

## Comprehensive Audit Results

### Files With Dialog Operations (50+ instances found)

#### 1. **project_dialog_manager.py** (24 matches - FIXED)
- **Status**: ✅ Fixed by parent window update
- Lines with `set_transient_for()`: 76, 176, 355
- Lines with `dialog.run()`: 106, 153, 225, 259, 273, 382, 412, 449
- **Nested dialogs**: Error dialogs use `transient_for=dialog` (lines 146-153, 249-259, etc.)
  - This is CORRECT - error dialogs should be children of main dialog
- **Parent validation**: Now receives correct parent from ProjectActionsController

#### 2. **file_explorer_panel.py** (10 matches - SAFE)
- **Status**: ✅ Safe - uses `get_toplevel()`
- Lines: 725, 764, 801, 828
- Pattern: `window = self.tree_view.get_toplevel()`
  - When left panel attached: Returns main window ✓
  - When left panel floating: Returns left panel window ✓
- **Dynamic parent lookup** ensures correct window in all configurations

#### 3. **model_canvas_loader.py** (6 matches - SAFE)
- **Status**: ✅ Safe - uses parent_window from main app
- Line 75: `self.parent_window = None` (initialized)
- Line 103 (shypn.py): Set to main window: `model_canvas_loader.parent_window = window`
- Line 1575: Arc dialog: `create_arc_prop_dialog(obj, parent_window=self.parent_window, ...)`
- **All property dialogs** (place, transition, arc) use `self.parent_window` which is main window

#### 4. **shypn.py** (4 matches - SAFE)
- **Status**: ✅ Safe - uses main window directly
- Line 470: MessageDialog for unsaved changes
- Pattern: `dialog = Gtk.MessageDialog(parent=window, ...)`
- **Direct reference to main window** - always correct

#### 5. **project_actions_controller.py** (references - FIXED)
- **Status**: ✅ Fixed by parent window propagation
- Line 51: Stores parent_window
- Line 57: Passes to ProjectDialogManager
- Line 185-192: `set_parent_window()` method that fixes the issue
- Line 190: Updates dialog_manager.parent_window too

#### 6. **pathway_panel_loader.py** & **left_panel_loader.py** (panel windows - SAFE)
- **Status**: ✅ Safe - panel floating windows, not dialogs
- Use `set_transient_for()` for float button popups
- These are for panel detachment, not modal dialogs

#### 7. **place_prop_dialog_loader.py** (2 matches - SAFE)
- **Status**: ✅ Safe - receives parent from model_canvas_loader
- Parent passed from model_canvas_loader.parent_window (main window)

### Pattern Analysis

#### Safe Patterns ✅
```python
# 1. Direct main window reference
dialog = Gtk.MessageDialog(parent=main_window, ...)

# 2. Dynamic lookup via widget hierarchy
window = widget.get_toplevel()
dialog.set_transient_for(window)

# 3. Parent passed from correctly initialized component
# (as long as that component has valid parent)
dialog_loader = create_dialog(parent_window=self.parent_window)
```

#### Problematic Patterns ❌
```python
# 1. Hidden/non-realized window as parent
dialog.set_transient_for(hidden_window)  # ← Wayland Error 71

# 2. Panel window as parent when panel is attached
# (panel window hidden, should use main window instead)
dialog_manager = DialogManager(parent_window=self.panel_window)  # ← WRONG

# 3. No parent validation
dialog.set_transient_for(parent)  # What if parent is None?
```

## Testing Verification

### Before Fix
```bash
$ python3 src/shypn.py
[Click "New Project" button]
Gdk-Message: 15:38:56.958: Error 71 (Protocol error) dispatching to Wayland display.
[APP CRASHES]
```

### After Fix
```bash
$ python3 src/shypn.py
[Click "New Project" button]
[Dialog appears successfully]
[Can create project]
```

### Test Coverage

1. **Backend test** (test_new_project.py) - ✅ PASSES
   - ProjectManager creates projects correctly
   - Directory structure correct (workspace/projects/)

2. **Standalone dialog test** (test_dialog_standalone.py) - ✅ PASSES
   - Dialog code is correct
   - Works with simple parent window

3. **Main application** - ✅ NOW WORKS
   - Fix applied to left_panel_loader.py
   - Parent window correctly propagated

## Wayland vs X11 Considerations

### Wayland Protocol Requirements
- Parent windows MUST be realized before child dialogs
- Modal dialogs require valid transient-for relationship
- Hidden windows cannot be dialog parents
- Protocol errors are non-recoverable (crash)

### X11 Differences
- More permissive about parent window state
- Can sometimes recover from invalid parent
- May show warnings but not crash

### Best Practices for Both
1. **Always validate parent window**
   ```python
   if parent_window and parent_window.get_realized():
       dialog.set_transient_for(parent_window)
   ```

2. **Update parent references when widget hierarchy changes**
   ```python
   # When panel attaches/detaches
   if self.dialog_manager:
       self.dialog_manager.parent_window = new_parent
   ```

3. **Use widget.get_toplevel() for dynamic lookup**
   ```python
   # Gets correct window whether widget is in main window or floating panel
   window = widget.get_toplevel()
   ```

4. **Prefer non-blocking dialogs on Wayland**
   ```python
   # Instead of blocking run():
   dialog.connect("response", callback)
   dialog.present()
   ```

## Related Files Modified

### Core Fix
- ✅ `src/shypn/helpers/left_panel_loader.py` (line 258-261)

### Previously Fixed (Earlier in Debug Session)
- ✅ `src/shypn/helpers/left_panel_loader.py` (line 161, 171) - Changed `set_base_path()` to `navigate_to()`
- ✅ `ui/dialogs/project_dialogs.ui` (line 86) - Updated path hint to workspace/projects/
- ✅ `ui/panels/left_panel.ui` (line 253) - Updated placeholder to workspace/examples/

### No Changes Required (Already Safe)
- ✅ `src/shypn/helpers/file_explorer_panel.py` - Uses get_toplevel()
- ✅ `src/shypn/helpers/model_canvas_loader.py` - Uses main window
- ✅ `src/shypn.py` - Uses main window directly
- ✅ `src/shypn/helpers/project_dialog_manager.py` - Now receives correct parent

## Lessons Learned

### For Future Development

1. **Panel Architecture Pattern**
   - When panels can attach/detach, dialog parents must update
   - Store parent window reference, update on state change
   - Always propagate parent changes to sub-controllers

2. **GTK Dialog Parent Requirements**
   - Parent must be realized (shown) before dialog
   - Hidden windows cause Wayland protocol errors
   - Test on both X11 and Wayland

3. **Debugging Strategy**
   - Isolate components (backend, standalone UI, full app)
   - Compare working vs failing configurations
   - Check widget hierarchy with get_toplevel()
   - Add parent window validation logging

4. **Code Review Checklist**
   - [ ] Dialog parent window validated?
   - [ ] Parent window realized before dialog?
   - [ ] Parent updates when widget hierarchy changes?
   - [ ] Tested on Wayland?
   - [ ] Nested dialogs use correct parent?

## Success Criteria

- [x] "New Project" button shows dialog without crash
- [x] Can create project successfully
- [x] Project appears in workspace/projects/
- [x] File explorer navigates to new project
- [x] No Wayland protocol errors
- [x] All existing dialogs still work (arc properties, file operations, etc.)

## Additional Notes

### Why The Bug Was Hard to Find

1. **Error was environmental, not code logic**
   - Backend code worked perfectly
   - Dialog UI code was correct
   - Issue was in window hierarchy state

2. **Worked in isolation**
   - Standalone test succeeded
   - Made us think dialog code was fine (it was!)
   - Problem was in how main app wired everything together

3. **Multiple layers of indirection**
   - LeftPanelLoader → ProjectActionsController → ProjectDialogManager
   - Parent window passed through 3 layers
   - Easy to miss where reference became stale

4. **Attach/detach complexity**
   - Panel can be in two states (attached/floating)
   - Parent window different in each state
   - Update logic was incomplete

### Prevention Strategy

Add to CI/automated testing:
```python
# Test dialog parent window validity
def test_dialog_parents_are_valid():
    """Ensure all dialogs have valid, realized parent windows."""
    app = create_app()
    for dialog_manager in find_all_dialog_managers(app):
        parent = dialog_manager.parent_window
        assert parent is not None, "Dialog manager has None parent"
        assert isinstance(parent, Gtk.Window), "Parent is not a GtkWindow"
        # In real app context, parent should be realized
        # (In test context, may not be shown yet)
```

## References

- GTK3 Documentation: https://docs.gtk.org/gtk3/class.Dialog.html
- Wayland Protocol: https://wayland.freedesktop.org/docs/html/
- GDK Error 71: Protocol error - usually indicates window hierarchy violation
- Related Issue: "New Project button causing app abortion"

---

**Date**: 2025-01-06  
**Fixed By**: Parent window propagation in attach_to() method  
**Status**: ✅ RESOLVED
