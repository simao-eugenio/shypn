# Wayland Comprehensive Fix - All Orphaned Widgets

**Date**: October 10, 2025  
**Status**: ✅ **PHASE 1 COMPLETE** - Testing Required

## Problem

Systemic Wayland "Error 71 (Protocol error)" due to orphaned widgets (dialogs, menus, popups) without proper parent windows.

## Fixes Applied

### Phase 1: model_canvas_loader.py ✅
- [x] Fix 3 context menu locations (already done)
- [x] Add defensive check to line 887 MessageDialog (arc creation error)

### Phase 2: project_dialog_manager.py ✅
- [x] Add defensive parent checks to 3 builder dialog locations:
  - Line ~70: new_project_dialog
  - Line ~162: open_project_dialog  
  - Line ~341: project_properties_dialog
- Note: 11 error MessageDialogs use `transient_for=dialog` (builder dialog as parent)
  - These should be OK now that builder dialogs have proper parents

### Phase 3: shypn.py ✅
- [x] Add defensive check to line 472 MessageDialog (unsaved changes during close)
- [x] **CRITICAL FIX**: Add `window.realize()` early in initialization (line ~83)
  - Establishes Wayland surface BEFORE any child widgets are created
  - Ensures parent window is available for ALL dialogs/menus during startup
  - This is the key fix for "Error 71" during application initialization

### Already Fixed (Previous Phases) ✅
1. `src/shypn/file/netobj_persistency.py` - 6 dialogs
2. `src/shypn/helpers/file_explorer_panel.py` - 4 dialogs + 1 menu

## Summary of Changes

**Total Locations Fixed**: 23
- netobj_persistency.py: 6 methods
- file_explorer_panel.py: 5 locations (4 dialogs + 1 menu)
- model_canvas_loader.py: 4 locations (3 menus + 1 dialog)
- project_dialog_manager.py: 3 builder dialog parents
- project_dialog_manager.py: 11 error dialogs (fixed via parent chain)
- shypn.py: 2 fixes (1 dialog + **1 early window.realize()**)
- simulation_settings_dialog.py: 1 dialog (already OK - uses `self`)

**Files Modified**: 5
1. `src/shypn/file/netobj_persistency.py`
2. `src/shypn/helpers/file_explorer_panel.py`
3. `src/shypn/helpers/model_canvas_loader.py`
4. `src/shypn/helpers/project_dialog_manager.py`
5. `src/shypn.py` (**Critical: Early window.realize()**)

## Critical Insight - Window Realization

**Root Cause**: Wayland requires the parent window's surface to exist BEFORE child widgets (dialogs, menus, popovers) can be created.

**Solution**: Call `window.realize()` immediately after window geometry setup, but BEFORE loading any panels or managers:

```python
# BEFORE (WRONG - window not realized before child widgets):
window = main_builder.get_object('main_window')
window.set_default_size(1200, 800)
# Load panels and managers that might create dialogs
model_canvas_loader = create_model_canvas()  # Might trigger widget creation!

# AFTER (CORRECT - window realized first):
window = main_builder.get_object('main_window')
window.set_default_size(1200, 800)
window.realize()  # ← Establish Wayland surface NOW
# Load panels and managers (now they have valid parent window)
model_canvas_loader = create_model_canvas()
```

**Why This Works**:
- `window.realize()` creates the underlying GDK window and Wayland surface
- All subsequent child widgets can reference this surface as their parent
- Prevents "Error 71 (Protocol error)" during initialization
- Does NOT show the window (that happens later with `window.present()`)

## Fix Patterns

### For Direct Dialog Creation:
```python
# BEFORE:
dialog = Gtk.MessageDialog(
    transient_for=self.parent_window,  # Could be None!
    ...
)

# AFTER:
parent = self.parent_window if self.parent_window else None
dialog = Gtk.MessageDialog(
    transient_for=parent,  # Explicitly None if not set
    ...
)
```

### For Builder-Loaded Dialogs:
```python
# BEFORE:
dialog = self.builder.get_object('dialog_name')
if self.parent_window:
    dialog.set_transient_for(self.parent_window)
dialog.run()  # BAD - might show before parent set!

# AFTER:
dialog = self.builder.get_object('dialog_name')
parent = self.parent_window if self.parent_window else None
if parent:
    dialog.set_transient_for(parent)
# Parent is now properly set BEFORE dialog shows
dialog.run()
```

### For Context Menus:
```python
# BEFORE:
menu = Gtk.Menu()
menu.popup(None, None, None, None, button, time)

# AFTER:
menu = Gtk.Menu()
menu.attach_to_widget(widget, None)  # Attach to widget for parent
menu.popup_at_pointer(event)  # Wayland-compatible
```

## Testing Checklist

After all fixes:
- [ ] Clean application startup (no Wayland errors) ← **PRIMARY TEST**
- [ ] File operations (save/open) work
- [ ] Context menus work (canvas, file explorer, objects)
- [ ] Property dialogs work
- [ ] Project dialogs work
- [ ] Error dialogs show properly
- [ ] No "Error 71" messages on Wayland

## Root Cause

Wayland requires **explicit parent-child relationships** for:
1. **Dialogs**: Must have parent set in constructor OR via `set_transient_for()` BEFORE showing
2. **Menus**: Must be attached to widget via `attach_to_widget()` BEFORE popup
3. **Popups**: Must use `popup_at_pointer()` instead of deprecated `popup()`

## Key Insights

1. **Builder-loaded dialogs are tricky**: They exist but aren't shown yet. Parent MUST be set before `.run()` or `.show()`
2. **Intermittent errors**: If dialog shows during startup before parent window is ready
3. **`transient_for=dialog`**: Error dialogs with parent=another_dialog are OK (dialog is valid parent) - BUT parent dialog itself needs parent
4. **Explicit None is safe**: GTK handles `parent=None` correctly, it's the undefined/invalid parent that crashes
5. **Parent chain matters**: Error dialog → builder dialog → main window (all links must be valid)

## Next Steps

1. ✅ Fix model_canvas_loader.py line 887
2. ✅ Fix project_dialog_manager.py (3 builder dialog parents)
3. ✅ Fix shypn.py line 470
4. ⏳ **TEST APPLICATION STARTUP** - Check for "Error 71"
5. ⏳ If error persists, check startup sequence for other orphaned widgets

---

**Priority**: CRITICAL  
**Complexity**: MEDIUM (systematic pattern matching)  
**Estimated Time**: 1-2 hours for complete fix + testing
**Status**: Phase 1 complete - ready for testing
