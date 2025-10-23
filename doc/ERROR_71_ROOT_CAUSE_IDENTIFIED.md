# Error 71 Root Cause Identified

**Date**: 2025-10-22  
**Status**: ✅ Root cause identified through swap test

## Summary

Error 71 (Wayland protocol error) was isolated to the **production file panel's complexity**, not the GtkStack architecture or Master Palette.

## Test Methodology

Created a swap test that replaces the production file panel with a simplified test panel while keeping all other architecture (GtkStack, Master Palette, dialog handling) identical.

### Simple Test Panel Features:
- Basic file operations (New, Open, Save buttons)
- FileChooserDialog using `dialog.run()` (same as fixed persistency)
- GtkStack integration (add_to_stack, show_in_stack, hide_in_stack)
- Proper parent window handling

### Test Results:

| Configuration | Error 71? | Conclusion |
|--------------|-----------|------------|
| Production file panel | ✅ YES | Panel is cause |
| Simple test panel | ❌ NO | Architecture is OK |

## Evidence

```bash
# With simple panel (SHYPN_USE_SIMPLE_PANEL=1):
[INIT] All panels pre-docked successfully (no Error 71!)
[PHASE5] files button toggled: True
[SIMPLE] show_in_stack()
# NO ERROR 71 - Panel opens successfully!

# With production panel (normal mode):
[PHASE5] files button toggled: True
[STACK] LeftPanel show_in_stack() called
Gdk-Message: Error 71 (Protocol error) dispatching to Wayland display.
```

## Root Cause Analysis

The production file panel (`src/shypn/helpers/left_panel_loader.py` + `file_explorer_panel.py`) has:

1. **Complex widget hierarchy**: TreeView, ScrolledWindow, multiple toolbars, context menus
2. **Heavy signal handling**: File system events, selection changes, edit mode toggles  
3. **Nested controllers**: FileExplorerPanel + ProjectActionsController with their own signals
4. **Multiple dialog types**: FileChooser, confirmation dialogs, rename dialogs, properties dialogs

The **combination** of these elements creates a race condition or improper widget realization on Wayland when the panel becomes visible in the GtkStack.

## Fixes Implemented

### ✅ Already Fixed:
1. **FileChooserDialog pattern**: Changed from nested `Gtk.main()` to `dialog.run()` 
   - File: `src/shypn/file/netobj_persistency.py`
   - Lines: 403-418 (Save), 547-562 (Open)

2. **Parent window timing**: Set parent_window AFTER `window.show_all()` to ensure window is realized
   - File: `src/shypn.py`  
   - Lines: 570-590

3. **FileExplorerPanel parent propagation**: Updated `set_parent_window()` to also update persistency
   - File: `src/shypn/helpers/file_explorer_panel.py`
   - Lines: 1027-1042

### ⚠️ Still Problematic:

The Error 71 persists even after these fixes, suggesting the issue is in the **file_explorer_panel.py internal structure**, not just the dialogs.

## Next Steps

### Option A: Incremental Simplification (Recommended)
1. Temporarily disable file explorer TreeView (`set_visible(False)`)
2. Test if panel opens without Error 71
3. If yes → TreeView is cause
4. If no → Check toolbar signal handlers

### Option B: Redesign File Panel
1. Create new simplified file panel from scratch
2. Add features incrementally:
   - Basic layout ✓
   - File operations toolbar ✓
   - TreeView (carefully)
   - Context menus (carefully)
   - Project actions
3. Test at each step for Error 71

### Option C: Use Simple Panel Temporarily
1. Ship with simple panel enabled (`SHYPN_USE_SIMPLE_PANEL=1`)
2. Redesign production panel in parallel
3. Swap back when fixed

## Validation Command

```bash
# Test with simple panel (should work):
cd /home/simao/projetos/shypn
SHYPN_USE_SIMPLE_PANEL=1 python3 src/shypn.py

# Test with production panel (Error 71):
cd /home/simao/projetos/shypn  
python3 src/shypn.py
```

## Conclusion

**The GtkStack + Master Palette architecture is validated and working correctly.**  
**The production file panel needs refactoring or incremental debugging to isolate the specific widget/signal causing Error 71.**
