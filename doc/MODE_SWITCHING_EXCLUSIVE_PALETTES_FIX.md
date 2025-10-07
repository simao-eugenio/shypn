# Mode Switching Exclusive Palette Management - Complete ✅

**Date**: October 7, 2025
**Status**: Fixed
**Issue**: Simulation palettes overlapping with edit palettes when switching modes
**Solution**: Ensure all mode palettes and their tools are mutually exclusive with proper state reset

---

## Problem Description

### Original Issue
When switching between Edit mode and Simulation mode, palettes were overlapping at bottom-center:
- Switching to Edit mode: [S] button hidden, but simulation tools palette remained visible
- Switching to Simulation mode: [E] button hidden, but edit tools palettes could remain visible
- Toggle buttons not being reset to OFF state when modes switched
- Result: Visual clutter with overlapping palettes

**Visual Problem**:
```
Bottom-center (BROKEN):
┌─────────────────────────────┐
│   [ ] [E] [ ]               │  ← Edit palette
└─────────────────────────────┘
     [R] [P] [S] [T]           ← Simulation tools OVERLAPPING!
┌─────────────────────────────┐
│   [ ] [S] [ ]               │  ← Simulation palette HIDDEN
└─────────────────────────────┘
```

---

## Solution

### Core Principle: Mutual Exclusivity

**Edit Mode** and **Simulation Mode** must be completely exclusive:
- Only ONE mode visible at a time
- Only ONE set of mode buttons visible
- Only ONE set of tools palettes accessible
- Toggle buttons reset to OFF when switching modes

---

## Implementation

### Mode Switching Handler: `_on_mode_changed()`

Located in: `src/shypn/helpers/model_canvas_loader.py` (lines 525-590)

#### Edit Mode Activation (mode == 'edit')

**What happens when switching TO Edit mode**:

```python
if mode == 'edit':
    # 1. Show [E] button, hide [S] button
    if overlay_manager.edit_palette:
        edit_widget = overlay_manager.edit_palette.get_widget()
        if edit_widget:
            edit_widget.show()
            # Reset [E] button to OFF state (edit tools hidden)
            if overlay_manager.edit_palette.edit_toggle_button:
                if overlay_manager.edit_palette.edit_toggle_button.get_active():
                    overlay_manager.edit_palette.edit_toggle_button.set_active(False)
    
    if overlay_manager.simulate_palette:
        sim_widget = overlay_manager.simulate_palette.get_widget()
        if sim_widget:
            sim_widget.hide()
            # Reset [S] button to OFF state when hiding it
            sim_button = overlay_manager.simulate_palette.get_toggle_button()
            if sim_button and sim_button.get_active():
                sim_button.set_active(False)
    
    # 2. Hide any open simulation tools palette
    if overlay_manager.simulate_tools_palette:
        overlay_manager.simulate_tools_palette.hide()
    
    # 3. Hide any open edit tools palettes (ensure clean state)
    if drawing_area in self.palette_managers:
        palette_manager = self.palette_managers[drawing_area]
        palette_manager.hide_all()
```

**Actions**:
1. ✅ Show [E] button
2. ✅ Reset [E] toggle to OFF (edit tools hidden)
3. ✅ Hide [S] button
4. ✅ Reset [S] toggle to OFF (sim tools hidden)
5. ✅ Hide simulation tools palette (revealer)
6. ✅ Hide edit tools palettes ([P][T][A] and [S][L][U][R])

**Result**: Clean edit mode - only [E] button visible, all tools hidden

---

#### Simulation Mode Activation (mode == 'sim')

**What happens when switching TO Simulation mode**:

```python
elif mode == 'sim':
    # 1. Hide [E] button, show [S] button
    if overlay_manager.edit_palette:
        edit_widget = overlay_manager.edit_palette.get_widget()
        if edit_widget:
            edit_widget.hide()
    
    if overlay_manager.simulate_palette:
        sim_widget = overlay_manager.simulate_palette.get_widget()
        if sim_widget:
            sim_widget.show()
            # Reset [S] button to OFF state (simulation tools hidden)
            sim_button = overlay_manager.simulate_palette.get_toggle_button()
            if sim_button and sim_button.get_active():
                sim_button.set_active(False)
    
    # 2. Hide any open edit palettes
    if drawing_area in self.palette_managers:
        palette_manager = self.palette_managers[drawing_area]
        palette_manager.hide_all()
```

**Actions**:
1. ✅ Hide [E] button
2. ✅ Show [S] button
3. ✅ Reset [S] toggle to OFF (sim tools hidden)
4. ✅ Hide edit tools palettes ([P][T][A] and [S][L][U][R])

**Result**: Clean simulation mode - only [S] button visible, all tools hidden

---

## Key Fixes Applied

### Fix 1: Reset [S] Button When Hiding in Edit Mode

**Before** (incomplete):
```python
if overlay_manager.simulate_palette:
    sim_widget = overlay_manager.simulate_palette.get_widget()
    if sim_widget:
        sim_widget.hide()
        # Missing: Reset button state!
```

**After** (complete):
```python
if overlay_manager.simulate_palette:
    sim_widget = overlay_manager.simulate_palette.get_widget()
    if sim_widget:
        sim_widget.hide()
        # Reset [S] button to OFF state when hiding it
        sim_button = overlay_manager.simulate_palette.get_toggle_button()
        if sim_button and sim_button.get_active():
            sim_button.set_active(False)
```

**Why important**: If [S] button stays checked while hidden, clicking it after mode switch might not trigger the toggle event (already checked → no change → no signal).

---

### Fix 2: Fixed [E] Button Access Method

**Before** (incorrect API):
```python
edit_button = overlay_manager.edit_palette.get_toggle_button()  # Method doesn't exist!
if edit_button and edit_button.get_active():
    edit_button.set_active(False)
```

**After** (correct API):
```python
if overlay_manager.edit_palette.edit_toggle_button:
    if overlay_manager.edit_palette.edit_toggle_button.get_active():
        overlay_manager.edit_palette.edit_toggle_button.set_active(False)
```

**Why**: `EditPaletteLoader` exposes `edit_toggle_button` as a direct property, not through a getter method. `SimulatePaletteLoader` has `get_toggle_button()` method.

---

### Fix 3: Hide Edit Tools When Switching TO Edit Mode

**Before** (missing):
```python
# When switching to edit mode, only simulation tools were hidden
# Edit tools palettes could still be visible from previous session
```

**After** (complete):
```python
# 3. Hide any open edit tools palettes (ensure clean state)
if drawing_area in self.palette_managers:
    palette_manager = self.palette_managers[drawing_area]
    palette_manager.hide_all()
```

**Why**: User might have had edit tools open before switching to sim mode. When returning to edit mode, those palettes should start hidden (user must click [E] to show them again).

---

## Mode State Flow

### Starting Application
```
Initial State:
- Mode: Edit (default)
- [E] button: Visible, OFF
- [S] button: Hidden
- Edit tools: Hidden
- Sim tools: Hidden
```

### User Clicks [S] in Mode Palette
```
1. Mode changed to 'sim'
2. _on_mode_changed() called with mode='sim'
3. [E] button: Hidden
4. [S] button: Visible, OFF (reset)
5. Edit tools: Hidden (closed)
6. Sim tools: Hidden (user must click [S] to show)
```

### User Clicks [S] Toggle Button
```
1. [S] button becomes checked (ON)
2. SimulatePaletteLoader._on_simulate_toggle() called
3. Simulation tools palette revealed (slide-up animation)
4. Tools visible: [R] [P] [S] [T]
```

### User Clicks [E] in Mode Palette (returning to edit)
```
1. Mode changed to 'edit'
2. _on_mode_changed() called with mode='edit'
3. [S] button: Hidden, reset to OFF ✅ (NEW FIX)
4. [E] button: Visible, OFF (reset)
5. Sim tools: Hidden (revealer closed) ✅
6. Edit tools: Hidden (user must click [E] to show)
```

**Result**: Clean mode switch with no overlapping palettes! ✅

---

## Toggle Button State Management

### Why Reset Buttons to OFF?

**Reason 1: Visual Consistency**
- When mode palette shows [E] or [S] button, it should always start in OFF state
- User expectation: Click to reveal tools, click again to hide

**Reason 2: Signal Reliability**
- GTK toggle buttons only emit 'toggled' signal when state CHANGES
- If button is already ON when shown, clicking it OFF doesn't trigger tools to hide
- If button is already OFF when shown, clicking it ON doesn't trigger tools to show

**Reason 3: Clean State**
- Each mode switch is a "fresh start"
- No lingering state from previous mode
- Predictable behavior

### Button Reset Locations

**Edit Palette** ([E] button):
- Reset when switching TO edit mode (line 543-545)
- Direct property access: `edit_palette.edit_toggle_button.set_active(False)`

**Simulate Palette** ([S] button):
- Reset when switching TO edit mode (line 551-554) - hides button and resets
- Reset when switching TO sim mode (line 576-579) - shows button but resets
- Getter method access: `simulate_palette.get_toggle_button().set_active(False)`

---

## Tools Palette Visibility Control

### Edit Tools Palettes

**Components**:
- Tools palette: [P] [T] [A] - Place, Transition, Arc
- Operations palette: [S] [L] [U] [R] - Select, Lasso, Undo, Redo

**Controller**: `PaletteManager` (in `self.palette_managers[drawing_area]`)

**Show/Hide Methods**:
```python
# Show both palettes
palette_manager.show_all()

# Hide both palettes
palette_manager.hide_all()
```

**Visibility Rules**:
- Only visible in Edit mode
- Hidden when switching to Simulation mode
- Hidden when switching TO Edit mode (clean start)
- User must click [E] button to reveal

---

### Simulation Tools Palette

**Components**:
- Simulation tools: [R] [P] [S] [T] - Run, steP, Stop, reset (T)

**Controller**: `SimulateToolsPaletteLoader` (in `overlay_manager.simulate_tools_palette`)

**Show/Hide Methods**:
```python
# Show palette (revealer animation)
simulate_tools_palette.show()

# Hide palette (revealer animation)
simulate_tools_palette.hide()
```

**Visibility Rules**:
- Only visible in Simulation mode
- Hidden when switching to Edit mode
- Hidden when switching TO Simulation mode (clean start)
- User must click [S] button to reveal

---

## Testing Results

### ✅ Test 1: Edit to Sim Mode Switch
**Steps**:
1. Start in Edit mode
2. Click [E] to show edit tools
3. Click [E][S] mode button to switch to Simulation mode

**Expected**:
- [E] button hidden
- [S] button shown (OFF state)
- Edit tools hidden ([P][T][A] and [S][L][U][R] palettes gone)
- Simulation tools hidden (not shown yet)

**Result**: ✅ Pass - Clean switch, no overlapping palettes

---

### ✅ Test 2: Sim to Edit Mode Switch
**Steps**:
1. Start in Simulation mode
2. Click [S] to show simulation tools
3. Click [S][E] mode button to switch to Edit mode

**Expected**:
- [S] button hidden and reset to OFF
- [E] button shown (OFF state)
- Simulation tools hidden (revealer closed)
- Edit tools hidden (not shown yet)

**Result**: ✅ Pass - Clean switch, simulation tools properly hidden

---

### ✅ Test 3: Toggle Button State After Mode Switch
**Steps**:
1. Edit mode, click [E] to show tools
2. Switch to Sim mode (tools hidden)
3. Switch back to Edit mode
4. Click [E] again

**Expected**:
- [E] button starts in OFF state (not checked)
- Clicking [E] turns it ON and shows tools
- Tools appear correctly

**Result**: ✅ Pass - Button state properly reset, tools show/hide correctly

---

### ✅ Test 4: Overlapping Prevention
**Steps**:
1. Simulation mode with simulation tools showing
2. Switch to Edit mode

**Expected**:
- Only [E] button visible at bottom-center
- No simulation tools visible
- No overlapping palettes

**Result**: ✅ Pass - Perfect separation, no visual conflicts

---

## Code Architecture

### Widget Hierarchy

```
GtkOverlay (overlay_widget)
  ├─ GtkScrolledWindow
  │    └─ GtkDrawingArea (canvas)
  │
  ├─ Edit Palette (bottom-center)
  │    └─ GtkBox (edit_palette_container)
  │         └─ GtkBox (edit_control) - purple container
  │              └─ GtkToggleButton [E]
  │
  ├─ Simulate Palette (center-bottom)
  │    └─ GtkBox (simulate_palette_container)
  │         └─ GtkBox (simulate_control) - purple container
  │              └─ GtkToggleButton [S]
  │
  ├─ Simulation Tools Palette (above [S])
  │    └─ GtkRevealer (simulate_tools_revealer)
  │         └─ GtkBox (simulate_tools_container)
  │              ├─ GtkButton [R]
  │              ├─ GtkButton [P]
  │              ├─ GtkButton [S]
  │              └─ GtkButton [T]
  │
  ├─ Tools Palette (above [E], left)
  │    └─ GtkRevealer
  │         └─ GtkBox
  │              ├─ GtkToggleButton [P]
  │              ├─ GtkToggleButton [T]
  │              └─ GtkToggleButton [A]
  │
  └─ Operations Palette (above [E], right)
       └─ GtkRevealer
            └─ GtkBox
                 ├─ GtkButton [S]
                 ├─ GtkButton [L]
                 ├─ GtkButton [U]
                 └─ GtkButton [R]
```

### Signal Flow

**Mode Change**:
```
User clicks [E] or [S] in mode palette
    ↓
ModePaletteLoader emits 'mode-changed' signal
    ↓
ModelCanvasLoader._on_mode_changed() handler
    ↓
Hide old mode button + tools
Show new mode button (reset to OFF)
    ↓
Clean mode switch complete
```

**Tools Toggle**:
```
User clicks [E] or [S] toggle button
    ↓
'toggled' signal emitted (only on state change)
    ↓
EditPaletteLoader._on_edit_toggled() or
SimulatePaletteLoader._on_simulate_toggle()
    ↓
Show/hide respective tools palettes
    ↓
Tools visibility updated
```

---

## Files Modified

**File**: `src/shypn/helpers/model_canvas_loader.py`

**Lines Changed**: ~540-590 (mode switching handler)

**Changes**:
1. Added [S] button state reset when hiding in edit mode (lines 551-554)
2. Fixed [E] button access to use direct property instead of getter (lines 543-545)
3. Added edit tools hiding when switching TO edit mode (lines 557-560)
4. Updated comments for clarity

**No other files modified** - All fixes in mode switching logic only.

---

## Summary

### Problem
- Palettes overlapping when switching between Edit and Simulation modes
- Toggle buttons not being reset, causing unreliable behavior
- Simulation tools staying visible when returning to Edit mode

### Solution
- Implemented strict mutual exclusivity between modes
- All toggle buttons reset to OFF state when modes switch
- All tools palettes hidden when switching modes
- User must explicitly click toggle buttons to reveal tools

### Result
- ✅ Clean mode switching with no overlapping palettes
- ✅ Predictable toggle button behavior
- ✅ Professional appearance with proper state management
- ✅ All edit and simulation components mutually exclusive

**Mode switching now works perfectly with complete palette isolation!** 🎯✨

---

**Lines changed**: ~15 lines
**Files modified**: 1 file (model_canvas_loader.py)
**Testing**: All mode switching scenarios verified
**Result**: Perfect mutual exclusivity! 🚀
