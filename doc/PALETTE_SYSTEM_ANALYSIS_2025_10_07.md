# Palette System Analysis - October 7, 2025

## Executive Summary

Complete analysis of edit/simulation mode system, palette architecture (old vs new), canvas tab lifecycle, and identified conflicts between old UI-based palettes and new OOP palettes.

---

## 1. Mode System Architecture

### 1.1 Mode Palette (Edit/Sim Toggle)
**Location**: `src/ui/palettes/mode/mode_palette_loader.py`

**Initialization**:
```python
self.current_mode = 'edit'  # Line 19 - DEFAULT IS EDIT MODE
```

**Buttons**:
- `edit_mode_button` - [Edit] button (bottom-left, 24px margins)
- `sim_mode_button` - [Sim] button

**Signal**: `'mode-changed'` with mode parameter ('edit' or 'sim')

### 1.2 Mode Change Flow

```
ModePaletteLoader (init)
    └─> current_mode = 'edit'
    └─> update_button_states()

CanvasOverlayManager._setup_mode_palette()
    └─> Creates ModePaletteLoader
    └─> add_overlay(mode_widget)
    └─> update_palette_visibility('edit')  # Line 206

ModelCanvasLoader.connect_mode_changed_signal()
    └─> mode_palette.connect('mode-changed', _on_mode_changed, ...)
    
User clicks [Edit] or [Sim]
    └─> ModePaletteLoader.on_edit_clicked() or on_sim_clicked()
    └─> emit('mode-changed', mode)
    └─> _on_mode_changed() handler called
            ├─> overlay_manager.update_palette_visibility(mode)  # OLD system
            └─> palette_manager.show_all() or hide_all()        # NEW system
```

---

## 2. Palette Ecosystem Map (Old vs New)

### 2.1 OLD UI-Based Palette System

#### Created by `CanvasOverlayManager`:

1. **ZoomPalette** ✅ ACTIVE
   - File: `src/shypn/helpers/predefined_zoom.py`
   - UI: `ui/palettes/zoom.ui`
   - Position: Top-left, packed in overlay_box
   - Status: **WORKING** (not being replaced)

2. **EditPalette** ⚠️ PARTIALLY ACTIVE
   - File: `src/shypn/helpers/edit_palette_loader.py`
   - UI: `ui/palettes/edit_palette.ui`
   - Purpose: Single [E] button to toggle tools/operations palettes
   - Status: **STILL CREATED** but expects old palettes that no longer exist
   - **CONFLICT**: Lines 157-160 try to wire to `self.tools_palette` and `self.operations_palette` which are None

3. **ToolsPalette** (OLD) ❌ COMMENTED OUT
   - Method: `_setup_edit_palettes()` (lines 127-151)
   - Status: **COMMENTED OUT** (line 108)
   - Purpose: [P][T][A] tool buttons
   - **REPLACED BY**: New OOP `ToolsPalette`

4. **OperationsPalette** (OLD) ❌ COMMENTED OUT
   - Method: `_setup_edit_palettes()` (lines 127-151)
   - Status: **COMMENTED OUT** (line 108)
   - Purpose: [S][L][U][R] operation buttons
   - **REPLACED BY**: New OOP `OperationsPalette`

5. **SimulatePalette** ✅ ACTIVE
   - Method: `_setup_simulate_palettes()`
   - Purpose: Simulation controls
   - Status: **ACTIVE** (for simulation mode)

6. **SimulateToolsPalette** ✅ ACTIVE
   - Method: `_setup_simulate_palettes()`
   - Purpose: Simulation tools
   - Status: **ACTIVE** (for simulation mode)

### 2.2 NEW OOP Palette System

#### Created by `ModelCanvasLoader._setup_edit_palettes()`:

1. **PaletteManager**
   - File: `src/shypn/edit/palette_manager.py`
   - Purpose: Central coordinator for NEW OOP palettes
   - Manages: Registration, show/hide, CSS application
   - Storage: `self.palette_managers[drawing_area]`

2. **ToolsPalette (NEW)** ✅ ACTIVE
   - File: `src/shypn/edit/tools_palette_new.py`
   - Base: `BasePalette` (abstract base class)
   - Buttons: [P] Place, [T] Transition, [A] Arc
   - Signal: `'tool-selected'` with tool_name
   - Position: **Bottom-left, 82px from bottom, 24px from left** (centered above [Edit] button)
   - Visibility: **Hidden by default, shows only in edit mode**

3. **OperationsPalette (NEW)** ✅ ACTIVE
   - File: `src/shypn/edit/operations_palette_new.py`
   - Base: `BasePalette` (abstract base class)
   - Buttons: [S] Select, [L] Lasso, [U] Undo, [R] Redo
   - Signal: `'operation-triggered'` with operation
   - Position: **Bottom-left + 160px, 82px from bottom** (right of tools palette)
   - Visibility: **Hidden by default, shows only in edit mode**

### 2.3 Palette Positioning Summary

```
Canvas Layout (Bottom-Left Corner):
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                                     │
│  [P][T][A]  [S][L][U][R]  ← 82px   │ NEW OOP palettes (edit mode only)
│      ↑           ↑                  │
│      └─ 24px     └─ 184px          │
│                                     │
│  [Edit] [Sim]  ← 24px from bottom  │ Mode palette (always visible)
│   ↑                                 │
│   └─ 24px from left                │
└─────────────────────────────────────┘
```

---

## 3. Canvas Tab Lifecycle

### 3.1 Tab Creation Flow

```
MainWindow: New tab or load file
    └─> ModelCanvasLoader.create_canvas_tab()
        ├─> Create GtkDrawingArea
        ├─> Create ModelCanvasManager
        ├─> Create CanvasOverlayManager
        │   └─> setup_overlays()
        │       ├─> _setup_zoom_palette()           # Zoom (top-left)
        │       ├─> _setup_edit_palette()           # [E] button (OLD, broken)
        │       ├─> _setup_simulate_palettes()      # Sim palettes
        │       └─> _setup_mode_palette()           # [Edit][Sim] buttons
        │           └─> update_palette_visibility('edit')  # Set initial mode
        │
        └─> _setup_edit_palettes()                  # NEW OOP palettes
            ├─> Create PaletteManager
            ├─> Create ToolsPalette (hidden)
            ├─> Create OperationsPalette (hidden)
            ├─> Register with PaletteManager
            └─> Wire to mode-changed signal
```

### 3.2 Mode Change Per Tab

Each canvas tab has:
- **Independent `CanvasOverlayManager`** (stores OLD palettes)
- **Independent `PaletteManager`** (stores NEW palettes)  
- **Shared `ModePaletteLoader`** visual widget (but separate instance per tab)

Mode persists per-tab:
- Stored in: `ModePaletteLoader.current_mode`
- Each tab has its own `ModePaletteLoader` instance
- Switching tabs does NOT change mode
- You can have tab 1 in 'edit' mode, tab 2 in 'sim' mode

---

## 4. Old/New Code Conflicts

### 4.1 CONFLICT #1: EditPalette [E] Button Wiring

**Location**: `canvas_overlay_manager.py` lines 152-165

**Issue**:
```python
def _setup_edit_palette(self):
    self.edit_palette = create_edit_palette()
    edit_widget = self.edit_palette.get_widget()
    
    # Wire edit palette to both palettes
    if self.tools_palette and self.operations_palette:  # ← BOTH ARE NONE!
        self.edit_palette.set_edit_palettes(self.tools_palette, self.operations_palette)
```

**Problem**: 
- `_setup_edit_palettes()` is commented out (line 108)
- `self.tools_palette` and `self.operations_palette` are never created (OLD system)
- `self.edit_palette` is created but has no palettes to control
- NEW palettes are managed by `PaletteManager`, not `EditPaletteLoader`

**Impact**: [E] button is created but does nothing (no palettes wired)

### 4.2 CONFLICT #2: Duplicate Mode Change Handling

**Location**: `model_canvas_loader.py` `_on_mode_changed()` lines 463-482

**Issue**:
```python
def _on_mode_changed(self, mode_palette, mode, drawing_area, *args):
    # Handle old overlay manager palette visibility
    if drawing_area in self.overlay_managers:
        overlay_manager = self.overlay_managers[drawing_area]
        overlay_manager.update_palette_visibility(mode)  # ← OLD system
    
    # Handle NEW OOP palettes visibility
    if drawing_area in self.palette_managers:
        palette_manager = self.palette_managers[drawing_area]
        if mode == 'edit':
            palette_manager.show_all()  # ← NEW system
        else:
            palette_manager.hide_all()
```

**Problem**:
- TWO separate systems handling mode changes
- OLD system (`update_palette_visibility`) tries to show/hide OLD palettes that don't exist
- NEW system (`palette_manager`) correctly shows/hide NEW palettes
- Code duplication and confusion

### 4.3 CONFLICT #3: Incorrect Initial Mode in Logs

**Log Output**:
```
[PaletteManager] Hiding all 2 palettes
[ModelCanvasLoader] Hiding edit palettes (simulation mode)
[BasePalette] Showing palette: tools (was False, now True)
[BasePalette] Showing palette: operations (was False, now True)
[PaletteManager] Showing all 2 palettes
[ModelCanvasLoader] Showing edit palettes (edit mode)
```

**Issue**:
- "Hiding edit palettes (simulation mode)" appears FIRST
- Then "Showing edit palettes (edit mode)" appears
- Suggests mode-changed signal is fired TWICE during initialization
- Or `update_button_states()` triggers signal emission

**Root Cause**: Unknown - needs signal emission tracing

### 4.4 CONFLICT #4: EditPaletteLoader Has Dead Code

**Location**: `edit_palette_loader.py` lines 45-60

**Issue**:
```python
# Palette loaders to control
self.tools_palette_loader = None              # OLD: Deprecated
self.editing_operations_palette_loader = None # OLD: Deprecated
self.combined_tools_palette_loader = None     # OLD: Unified combined
self.floating_buttons_manager = None          # OLD: Individual floating buttons

# NEW: Two separate palette instances (transparent containers)
self.tools_palette = None                     # ToolsPalette instance [P][T][A]
self.operations_palette = None                # OperationsPalette instance [S][L][U][R]
```

**Problem**:
- Comments indicate multiple deprecated palette systems
- NEW palette references are never set (they're managed by `PaletteManager` now)
- EditPaletteLoader is orphaned - it doesn't control anything

---

## 5. Default Mode Verification

### 5.1 Confirmed: Edit Mode IS Default

**Evidence**:
1. `ModePaletteLoader.__init__()` line 19: `self.current_mode = 'edit'`
2. `CanvasOverlayManager._setup_mode_palette()` line 206: `self.update_palette_visibility('edit')`
3. Mode palette UI buttons: Edit button starts insensitive (active state)

### 5.2 Why "Sim Mode" Appears First in Logs?

**Investigation Needed**:
1. Check if `update_button_states()` emits signals during initialization
2. Check if signal connection happens BEFORE mode palette init completes
3. Trace exact order of:
   - ModePaletteLoader.__init__()
   - connect_mode_changed_signal()
   - First mode-changed emission

**Hypothesis**: Signal handler is connected AFTER mode palette creation, and during connection, handler gets called with stale/default value

---

## 6. Architecture Summary

### Current State:
```
┌──────────────────────────────────────────────────────────────┐
│                    Canvas Tab (GtkOverlay)                   │
├──────────────────────────────────────────────────────────────┤
│  OLD SYSTEM (CanvasOverlayManager)                          │
│  ├─ ZoomPalette (working)                                    │
│  ├─ EditPalette [E] button (orphaned, broken)               │
│  ├─ tools_palette = None (commented out)                     │
│  ├─ operations_palette = None (commented out)                │
│  ├─ SimulatePalette (working)                                │
│  ├─ SimulateToolsPalette (working)                           │
│  └─ ModePalette [Edit][Sim] (working)                        │
│      └─> emits 'mode-changed'                                │
│          ├─> overlay_manager.update_palette_visibility()     │
│          │   (tries to show/hide non-existent OLD palettes)  │
│          └─> palette_manager.show_all() / hide_all()         │
│              (correctly shows/hides NEW palettes)            │
├──────────────────────────────────────────────────────────────┤
│  NEW SYSTEM (PaletteManager)                                 │
│  ├─ ToolsPalette [P][T][A] (working, OOP)                   │
│  └─ OperationsPalette [S][L][U][R] (working, OOP)           │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Action Plan

### PHASE 1: Remove Orphaned [E] Button ✅ HIGH PRIORITY
**Goal**: Remove or repurpose EditPaletteLoader since it no longer controls anything

**Options**:
A. **Remove entirely** - Mode palette [Edit]/[Sim] buttons now control palette visibility
B. **Repurpose** - Use [E] button as quick toggle within edit mode (floating tools toggle)
C. **Keep as placeholder** - For future floating button manager

**Recommendation**: **Option A** - Remove EditPaletteLoader and `_setup_edit_palette()`
- NEW palettes auto-show when mode = 'edit'
- No need for separate [E] button
- Simplifies architecture

### PHASE 2: Clean Up Mode Change Handler ✅ MEDIUM PRIORITY
**Goal**: Remove OLD palette handling from `_on_mode_changed()`

**Changes**:
```python
def _on_mode_changed(self, mode_palette, mode, drawing_area, *args):
    # Handle NEW OOP palettes visibility ONLY
    if drawing_area in self.palette_managers:
        palette_manager = self.palette_managers[drawing_area]
        if mode == 'edit':
            palette_manager.show_all()
        else:
            palette_manager.hide_all()
    
    # OLD system removed - simulate palettes handled by overlay_manager directly
```

### PHASE 3: Fix Initial Mode Signal Issue ⚠️ LOW PRIORITY
**Goal**: Understand why "sim mode" appears first in logs

**Tasks**:
1. Add debug output to `ModePaletteLoader.__init__()`
2. Add debug output to `update_button_states()`
3. Trace signal connection timing
4. Verify no signals emitted during initialization

### PHASE 4: Rename Files ✅ LOW PRIORITY
**Goal**: Remove `_new.py` suffix from final palette files

**Changes**:
- `tools_palette_new.py` → `tools_palette.py` (after old one fully removed)
- `operations_palette_new.py` → `operations_palette.py`
- Update imports in `palette_manager.py` and `model_canvas_loader.py`

### PHASE 5: Documentation Update ✅ LOW PRIORITY
**Goal**: Update all docs to reflect NEW palette system only

**Files to Update**:
- `doc/PALETTE_ARCHITECTURE_ANALYSIS.md`
- `doc/mode_palette_quickref.md`
- `doc/OOP_REFACTORING_COMPLETE.md`
- README.md

---

## 8. Recommendations

### Immediate Actions (Today):
1. ✅ **Comment out `_setup_edit_palette()` call** in `canvas_overlay_manager.py` line 109
2. ✅ **Remove OLD palette handling** from `_on_mode_changed()` in `model_canvas_loader.py`
3. ✅ **Test** that NEW palettes show/hide correctly with [Edit]/[Sim] buttons

### Short-Term (This Week):
4. **Investigate initial mode signal** to eliminate confusing log messages
5. **Rename `*_new.py` files** to final names
6. **Remove EditPaletteLoader** entirely (delete file + UI file)

### Long-Term (Next Sprint):
7. **Update all documentation** to reflect NEW architecture
8. **Add unit tests** for PaletteManager and concrete palettes
9. **Consider** abstracting simulate palettes to same OOP pattern

---

## 9. Conclusion

The palette system is in a **transition state** with OLD UI-based palettes partially removed and NEW OOP palettes fully functional. The main issues are:

1. **Orphaned [E] button** - Created but controls nothing
2. **Duplicate mode handling** - Both OLD and NEW systems respond to mode changes
3. **Confusing logs** - Initial mode signal behavior unclear

**System IS functional** - NEW OOP palettes work correctly when mode = 'edit'. The issues are cleanup and polish, not core functionality.

**Priority**: Remove OLD palette remnants (EditPaletteLoader, dead code in mode handler) to clarify architecture.
