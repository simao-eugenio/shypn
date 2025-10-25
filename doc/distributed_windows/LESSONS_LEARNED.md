# Autonomous Panel Windows - Lessons Learned

## Experiment: Independent Window-Based Panel Architecture
**Branch:** `feature/autonomous-panel-windows`  
**Status:** ❌ ABANDONED - Reverted to stack-based architecture  
**Date:** October 24, 2025

## What We Tried

Created an autonomous panel architecture where each panel is an independent `Gtk.Window`:

- **Base Class:** `AutonomousPanelWindow` (436 lines)
- **Docking Modes:** `FLOATING`, `DOCKED`, `HIDDEN`
- **Approach:** Position independent windows next to main window
- **Goal:** Avoid widget reparenting to prevent Wayland Error 71

## Why It Failed

### 1. **Not True Docking**
- Panels were just "positioned windows" near main window
- No integration with desktop window management
- Didn't share space properly
- All panels could be visible simultaneously (chaos)

### 2. **Content Rendering Issues**
- Some panels showed empty windows
- Content didn't load properly in independent windows
- FileExplorerPanel needed complex re-wiring

### 3. **Position Management Problems**
- Initial negative X coordinates (panels off-screen left)
- 100ms timer spam for position tracking
- Windows didn't stay docked when main window moved
- Positioning logic was fragile

### 4. **Architectural Mismatch**
- GTK expects panels in containers (Stack, Box, Paned)
- Independent windows fight GTK's widget hierarchy
- Lost benefits of GTK layout management
- More code, more complexity, less functionality

## What Worked

✅ Base class design was clean  
✅ Factory pattern for panel creation  
✅ Converted ToggleButton to Button (good UX improvement)  
✅ Master Palette callbacks triggered correctly  
✅ No Wayland Error 71 (but at what cost?)

## Key Insight

**The original Error 71 was NOT caused by widget reparenting itself.**  
It was caused by:
1. Premature `window.realize()` calls
2. Using `show_all()` instead of `show()`
3. Gtk.main_iteration() loops during initialization

**We were solving the wrong problem.**

## Correct Solution

**Stick with stack-based architecture (v0.9.0-multi-panel-float):**
- Panels load content directly into GtkStack
- No window creation/destruction
- Proper GTK integration
- Simple, proven, works

**Future Enhancement (If Needed):**
- Add float capability by moving content to temporary window
- Use careful widget reparenting with proper show/realize order
- Keep docked mode as primary, floating as bonus feature

## Files Created (Preserved in feature branch for reference)

```
src/shypn/ui/autonomous_panel_window.py (436 lines)
src/shypn/panels/
├── __init__.py
├── file_panel.py
├── pathway_panel.py
├── analyses_panel.py
└── topology_panel.py

doc/distributed_windows/
├── ARCHITECTURE.md
├── IMPLEMENTATION_SESSION.md
├── PHASE1_COMPLETE.md
└── LESSONS_LEARNED.md (this file)
```

## Conclusion

**Sometimes the simple solution is the right solution.**

The stack-based architecture in v0.9.0-multi-panel-float:
- ✅ Works reliably
- ✅ No Wayland errors
- ✅ Proper GTK integration
- ✅ Simple codebase
- ✅ Standard desktop behavior

**Recommendation:** Stay with stack-based architecture. If floating panels are truly needed, implement as a bonus feature on top of solid stack foundation.

---

**Effort:** ~8 hours of development  
**LOC Added:** ~1200 lines  
**LOC Removed:** ~1200 lines (reverted)  
**Net Result:** Better understanding of GTK limitations  
**Lesson:** Don't fight the framework
