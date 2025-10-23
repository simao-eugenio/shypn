# Skeleton Test Bed - Architecture Validation

**Date**: October 22, 2025  
**Status**: ⚠️ **PHASE 0 VALIDATION REQUIRED**

---

## 🚨 CRITICAL: Phase 0 Validation FIRST!

**MUST RUN** before implementing Master Palette in production:

### Test 1: GtkStack Principle
```bash
./dev/test_gtkstack_principle.py
```
**Validates**: GtkStack works with Wayland WITHOUT Error 71

### Test 2: Error 71 Diagnosis
```bash
./dev/test_error71_diagnosis.py
```
**Identifies**: Potential issues in panel UI files and loader code

**📖 Complete Instructions**: See `PHASE0_VALIDATION.md`

---

## Overview

This directory contains the findings from testing the **core architectural principle** of the "Hanger" pattern:
- **Main window = Hanger** (empty container)
- **Master Palette = Native widget** (toolbar)
- **Panels = Independent GtkWindows** (can be hanged/revealed/hidden)

**NEW**: Phase 0 validation tests for GtkStack safety and panel code quality.

---

## Documents

### PHASE 0 - Validation (NEW)

**PHASE0_VALIDATION.md** - Complete instructions for validation tests
- Test 1: GtkStack principle validation
- Test 2: Error 71 diagnosis
- GO/NO-GO decision criteria
- Alternative approaches if tests fail

**Validation Files**:
- `dev/test_gtkstack_principle.py` - Interactive + automated GtkStack testing
- `dev/test_error71_diagnosis.py` - Automated panel code analysis

---

### Architecture Documents

### 1. ARCHITECTURE_DECISION.md
**Summary of the validated architecture** with diagrams and recommendations.

**Key Findings**:
- ✅ Main window as "hanger" works perfectly
- ✅ Master Palette as native widget (Mode 2) is recommended
- ✅ Panels as independent windows can be hanged/hidden without Error 71
- ❌ Monolithic GtkStack/GtkRevealer approach FAILED

### 2. HEAVY_PANEL_TESTING.md
**Detailed testing results** with complex widgets and interactions.

**What Was Tested**:
- FileChooserButton widgets
- 5 types of dialogs (Info, Question, File Open/Save, Color)
- Bidirectional panel ↔ hanger communication
- Rapid toggle stress testing (10x cycles)
- State preservation across hang/hide cycles

**Results**: ✅ ALL TESTS PASS - NO Error 71

### 3. TESTING_GUIDE.md
**Quick start guide** for running the skeleton test bed.

**How to Test**:
```bash
./dev/test_architecture_principle.py 2  # Mode 2 (recommended)
```

---

## Test Bed

**Location**: `dev/test_architecture_principle.py`

**Test Modes**:
1. Mode 1: Master Palette as independent window
2. Mode 2: Master Palette as native widget ⭐ **RECOMMENDED**
3. Mode 3: Everything as independent windows

---

## Key Implementation Details

### Master Palette Controls Panel Visibility

```python
# On Files button click:
def on_files_toggled(active):
    if active:
        panel.show()   # REVEAL panel
    else:
        panel.hide()   # HIDE panel
```

### Panel Starts Hidden

```python
# On startup:
panel.hang_on(slot)                    # Attach to main window
panel.content.set_no_show_all(True)   # Prevent show_all from revealing
panel.hide()                           # Start hidden
```

### Panel Show/Hide Implementation

```python
def show(self):
    """Reveal panel (slides to the right)."""
    self.content.set_no_show_all(False)
    self.content.show_all()

def hide(self):
    """Hide panel (still hanged, just invisible)."""
    self.content.set_no_show_all(True)
    self.content.hide()
```

---

## Wayland Compatibility

**ALL OPERATIONS ARE WAYLAND ERROR 71 FREE**:
- ✅ Panel hang/unhang
- ✅ Panel show/hide
- ✅ Dialogs (all types)
- ✅ FileChooser widgets
- ✅ Rapid toggle operations
- ✅ Panel ↔ Hanger communication

---

## Production Implementation Roadmap

### Phase 1: Integrate Master Palette (2-4 hours)
1. Add Master Palette widget to main_window.ui (48px slot)
2. Create MasterPalette class (native Gtk.Box)
3. Wire button signals to existing panel loaders

### Phase 2: Update Panel Loaders (1-2 hours)
1. Add `hide()` and `show()` methods to panel classes
2. Implement `set_no_show_all()` logic
3. Update panel initialization to start hidden

### Phase 3: Connect Everything (1-2 hours)
1. Wire Files button to Files panel show/hide
2. Wire Pathways button to Pathways panel show/hide
3. Wire Analyses button to Analyses panel show/hide
4. Wire Topology button to Topology panel show/hide

### Phase 4: Polish (1-2 hours)
1. Add panel state persistence (remember which panels were visible)
2. Add keyboard shortcuts (F1-F4 for panels)
3. Add visual feedback (button highlights, transitions)

**Total Estimated Time**: 5-10 hours  
**Risk Level**: LOW (built on validated skeleton)  
**Confidence**: HIGH (all tests pass)

---

## Critical Success Factors

1. ✅ **Use `set_no_show_all(True)`** to prevent `window.show_all()` from revealing hidden panels
2. ✅ **Dynamic parent window** for dialogs based on panel state (hanged vs floating)
3. ✅ **Proper show/hide** instead of attach/detach for panel visibility
4. ✅ **Master Palette as native widget** (not independent window)
5. ✅ **Panel starts hanged but hidden** on application startup

---

## Files

- **Test Script**: `dev/test_architecture_principle.py`
- **Documentation**: 
  - `doc/skeleton/ARCHITECTURE_DECISION.md` (summary)
  - `doc/skeleton/HEAVY_PANEL_TESTING.md` (detailed results)
  - `doc/skeleton/TESTING_GUIDE.md` (quick start)
  - `doc/skeleton/README.md` (this file)

---

## Conclusion

**The "Hanger" architecture is production-ready!**

✅ Validated with complex widgets and heavy interactions  
✅ Wayland Error 71 free  
✅ Master Palette button controls (show/hide panels)  
✅ Panels start hidden and reveal on button click  
✅ All dialog types work correctly  
✅ Rapid operations are stable  

**Ready for production implementation with high confidence.**
