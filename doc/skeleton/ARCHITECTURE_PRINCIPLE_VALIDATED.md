# Architecture Principle Test Results

**Date**: October 22, 2025  
**Test**: Core "Hanger" Architecture Validation  
**Objective**: Determine which widgets can be safely "hanged" on main window without Wayland Error 71

---

## Test Concept

**PRINCIPLE**: Main window = HANGER (empty GtkApplicationWindow)

```
Main Window (HANGER)
├── Left Slot      → For Master Palette (hanged)
├── Content Area   → For Panels (hanged)
│   ├── Panel Slot 1
│   ├── Canvas (drawing area)
│   └── Panel Slot 2
└── Right Slot     → Reserved
```

**QUESTION**: What widget types can be "hanged" safely?
- Independent GtkWindow instances?
- Native Gtk widgets?
- Mixed approach?

---

## Test Modes

### Mode 1: Master Palette as Independent Window
**Design**: 
- Master Palette = GtkWindow (independent)
- Panels = GtkWindow (independent)
- Both can be "hanged" on main window

**Implementation**:
```python
class MasterPaletteOption1:
    def __init__(self):
        self.window = Gtk.Window()  # Independent window
        self.content = Gtk.Box()    # Content to hang
    
    def hang_on(self, container):
        self.window.hide()
        self.window.remove(self.content)
        container.pack_start(self.content, ...)
```

**Test Results**: ✅ **NO Error 71**
- Master Palette hangs successfully
- Panels attach/detach cleanly
- Rapid toggle test (10x cycles): PASS
- Wayland compatibility: CONFIRMED

**Pros**:
- Maximum flexibility (everything can be window or hanged)
- Consistent pattern (everything follows same rules)
- Master Palette can float independently if needed

**Cons**:
- Slightly more complex (Master Palette needs window management)
- Extra window object (even if always hanged)

---

### Mode 2: Master Palette as Native Widget ⭐ **RECOMMENDED**
**Design**:
- Master Palette = Native Gtk.Box (no window)
- Panels = GtkWindow (independent)
- Only panels can be "hanged"

**Implementation**:
```python
class MasterPaletteOption2:
    def __init__(self):
        self.content = Gtk.Box()  # Just a widget, no window
    
    def get_widget(self):
        return self.content  # Pack directly
```

**Test Results**: ✅ **NO Error 71**
- Master Palette integrates seamlessly
- Panels attach/detach cleanly
- Rapid toggle test (10x cycles): PASS
- Wayland compatibility: CONFIRMED

**Pros**:
- Simpler architecture (Master Palette is just a widget)
- No unnecessary window management
- Master Palette always visible (logical for main toolbar)
- Fewer moving parts = fewer bugs

**Cons**:
- Master Palette cannot float independently
- Less flexible (but do we need floating palette?)

---

### Mode 3: Everything as Independent Windows
**Design**:
- Master Palette = GtkWindow (independent)
- Panels = GtkWindow (independent)
- Everything can float independently OR hang on main window

**Implementation**:
- Both Master Palette and panels start as floating windows
- Can be hanged on demand
- Can return to floating window state

**Test Results**: ✅ **NO Error 71**
- All windows float independently: WORKS
- All windows hanged on main: WORKS
- Mixed state (some hanged, some floating): WORKS
- Rapid toggle test: PASS
- Wayland compatibility: CONFIRMED

**Pros**:
- Ultimate flexibility
- User can arrange workspace however they want
- Supports multi-monitor workflows

**Cons**:
- Most complex state management
- More potential for user confusion
- May be overkill for typical use case

---

## Critical Findings

### ✅ The "Hanger" Architecture is Wayland-Safe

**ALL THREE MODES WORK WITHOUT Error 71!**

The core principle is sound:
1. Main window is just a container (hanger)
2. Independent GtkWindows can be "hanged" (content reparented to main window)
3. Native widgets can be packed directly
4. Rapid attach/detach cycles are stable
5. No Wayland protocol violations

### ❌ The Monolithic GtkStack/GtkRevealer is NOT Wayland-Safe

Comparison:
```
✅ WORKS: window.remove(content) → container.pack_start(content)
❌ FAILS: GtkRevealer + GtkStack with embedded panels
```

The monolithic refactor was using the WRONG widget hierarchy. The "hanger" pattern works perfectly.

---

## Recommendations

### Primary Recommendation: **Mode 2** ⭐

**Use Master Palette as native widget, panels as independent windows.**

**Rationale**:
1. **Simplest correct solution** (Occam's Razor)
2. Master Palette is logically a permanent toolbar (doesn't need to float)
3. Panels need flexibility (attach/detach/float) → keep as windows
4. Proven Wayland-safe in tests
5. Matches existing working architecture (just adds Master Palette widget)

**Implementation**:
```python
# In main window initialization:
self.master_palette = MasterPalette()  # Just a Gtk.Box
main_layout.pack_start(self.master_palette.get_widget(), False, False, 0)

# Panels remain as GtkWindows (existing code works!)
self.left_panel = create_left_panel()  # Returns window-based panel
self.left_panel.attach_to(left_dock_stack)  # Existing mechanism
```

### Alternative: **Mode 3** (Future Enhancement)

If we want maximum flexibility later:
- Allow Master Palette to be detached (becomes floating window)
- Support docking of panels to screen edges
- Multi-monitor workspace management

But start with Mode 2 for simplicity.

---

## Implementation Path Forward

### What to Keep from Monolithic Refactor

✅ **Keep these**:
- Master Palette widget design (buttons, signals, visual design)
- Panel controller classes (clean architecture)
- OOP structure (BasePanel, panel subclasses)

❌ **Abandon these**:
- GtkRevealer + GtkStack hierarchy in main_window.ui
- Embedded panel containers in main window
- Phase 1-2 UI files (monolithic structure)

### Implementation Steps (Mode 2)

1. **Add Master Palette to main_window.ui** (as native widget)
   ```xml
   <object class="GtkBox" id="master_palette_container">
     <!-- Master Palette buttons will be added here via code -->
   </object>
   ```

2. **Revert main_window.ui to original structure**
   ```bash
   cp archive/refactor_main/main_window.ui.backup ui/main/main_window.ui
   ```

3. **Insert Master Palette widget slot in UI**
   - Add a 48px-wide left box for Master Palette
   - Keep existing left_dock_stack for panels (WORKS!)

4. **Wire Master Palette signals to existing panel loaders**
   ```python
   master_palette.connect('files', lambda active: 
       left_panel.attach_to(left_dock_stack) if active else left_panel.hide()
   )
   ```

5. **Test incrementally**
   - Test with Files panel only
   - Add Pathways panel
   - Add Analyses panel
   - Add Topology panel

**Estimated time**: 2-4 hours (reusing proven working code)

---

## Validation Metrics

| Test | Mode 1 | Mode 2 | Mode 3 | Monolithic |
|------|--------|--------|--------|------------|
| **No Error 71** | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL |
| **Attach/Detach** | ✅ PASS | ✅ PASS | ✅ PASS | ❌ N/A |
| **Rapid Toggle (10x)** | ✅ PASS | ✅ PASS | ✅ PASS | ❌ N/A |
| **Wayland Stable** | ✅ YES | ✅ YES | ✅ YES | ❌ NO |
| **Simplicity** | ⚠️ Medium | ✅ Simple | ⚠️ Complex | N/A |
| **Flexibility** | ✅ High | ⚠️ Medium | ✅ Very High | N/A |

---

## Conclusion

**The architectural principle is VALIDATED:**
- ✅ Main window as "hanger" works perfectly
- ✅ Independent GtkWindows can be "hanged" safely
- ✅ Wayland Error 71 is NOT caused by window reparenting
- ✅ Wayland Error 71 IS caused by monolithic GtkStack/GtkRevealer structure

**Recommended path forward:**
1. Use **Mode 2** (Master Palette as native widget)
2. Keep existing panel window architecture (already works!)
3. Wire Master Palette signals to existing panel loaders
4. Implementation time: 2-4 hours
5. High confidence: Built on proven working code

**The original architecture was correct all along!**

---

## Test Files

- Test script: `dev/test_architecture_principle.py`
- Run Mode 1: `./dev/test_architecture_principle.py 1`
- Run Mode 2: `./dev/test_architecture_principle.py 2`
- Run Mode 3: `./dev/test_architecture_principle.py 3`

All modes tested successfully without Wayland errors.
