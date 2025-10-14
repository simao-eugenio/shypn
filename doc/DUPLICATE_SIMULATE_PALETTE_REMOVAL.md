# Duplicate Simulate Palette Removal

## Date: October 11, 2025

## Problem

After integrating the SwissKnife palette, an extra simulate palette appeared at the bottom center of the screen. This was a duplicate of the simulation controls that are now embedded inside the SwissKnife palette's Simulate category.

---

## Root Cause

The `canvas_overlay_manager.py` file was still creating and adding a separate `SimulateToolsPaletteLoader` instance to the overlay, even though the SwissKnife palette now creates its own instance internally.

### Architecture Before Fix:

```
Canvas Overlay
├── SwissKnifePalette (bottom-center)
│   └── Simulate Category
│        └── SimulateToolsPaletteLoader (INTERNAL)
│             └── [R][P][S][T][⚙] controls
└── SimulateToolsPaletteLoader (DUPLICATE - also bottom-center)
     └── [R][P][S][T][⚙] controls (EXTRA/UNWANTED)
```

**Result**: Two sets of simulation controls visible!

---

## Solution

### File 1: `canvas_overlay_manager.py`

**Location**: Lines 171-199 in `_setup_simulate_palettes()` method

**Changes Made**:
1. Removed creation of separate `SimulateToolsPaletteLoader`
2. Removed adding it to overlay
3. Set both `simulate_tools_palette` and `simulate_palette` to `None`

**Old Code** (REMOVED):
```python
self.simulate_tools_palette = create_simulate_tools_palette(model=self.canvas_manager)
simulate_tools_widget = self.simulate_tools_palette.get_widget()

if simulate_tools_widget:
    self.overlay_widget.add_overlay(simulate_tools_widget)
    self.register_palette('simulate_tools', self.simulate_tools_palette)
    self.simulate_tools_palette.hide()
```

**New Code**:
```python
# Set to None - SwissKnifePalette manages simulation controls internally
self.simulate_tools_palette = None
self.simulate_palette = None
```

**Rationale**: 
The SwissKnife palette creates its own `SimulateToolsPaletteLoader` instance when it detects the 'simulate' category is configured as a widget palette. We don't need to create or manage it separately in the overlay manager.

---

### File 2: `model_canvas_loader.py`

**Location**: Line 682 in `_on_simulation_reset()` method

**Changes Made**:
Fixed signal handler signature to accept `drawing_area` parameter.

**Old Signature**:
```python
def _on_simulation_reset(self, palette):
```

**New Signature**:
```python
def _on_simulation_reset(self, palette, drawing_area):
```

**Rationale**:
The signal was being connected with `drawing_area` as user data:
```python
swissknife_palette.connect('simulation-reset-executed', self._on_simulation_reset, drawing_area)
```

The handler must accept this parameter to avoid `TypeError`.

---

## Architecture After Fix

```
Canvas Overlay
└── SwissKnifePalette (bottom-center)
     └── Simulate Category
          └── SimulateToolsPaletteLoader (SINGLE INSTANCE)
               └── [R][P][S][T][⚙] controls ✅
```

**Result**: Only ONE set of simulation controls, properly integrated in SwissKnife!

---

## Key Design Principles

### Widget Palette Pattern

The SwissKnife palette supports two types of sub-palettes:

1. **Simple Tool Buttons**: Edit, Layout categories
   - Simple buttons created directly in SwissKnife
   - Managed entirely by SwissKnife

2. **Widget Palettes**: Simulate category
   - Complex UI loaded from external component (`SimulateToolsPaletteLoader`)
   - SwissKnife creates the instance internally
   - No external creation needed

### Separation of Concerns

- **CanvasOverlayManager**: Manages zoom, mode, and SwissKnife palette
- **SwissKnifePalette**: Manages categories and their sub-palettes (including widget palettes)
- **SimulateToolsPaletteLoader**: Manages simulation controls and settings

The overlay manager should NOT create widget palettes that belong inside SwissKnife.

---

## Testing Results

### ✅ Verified Behavior

1. **Single Simulate Palette**: Only one set of simulation controls visible
2. **Proper Integration**: Controls appear inside SwissKnife's Simulate category
3. **No Errors**: Application launches without TypeError
4. **Signal Handling**: All simulation signals work correctly
5. **Settings Panel**: Inline settings panel works (⚙ button)

### ✅ No Side Effects

- Edit palette works
- Layout palette works
- Mode switching works
- Canvas drawing works
- All other functionality preserved

---

## Summary

The duplicate simulate palette has been successfully removed by:

1. ✅ Preventing separate creation of `SimulateToolsPaletteLoader` in overlay manager
2. ✅ Fixing signal handler signature for `_on_simulation_reset()`
3. ✅ Maintaining proper widget palette pattern in SwissKnife

The application now has a clean, unified interface with simulation controls properly integrated into the SwissKnife palette.

---

**Document Version**: 1.0  
**Date**: October 11, 2025  
**Status**: ✅ DUPLICATE REMOVED, ALL WORKING
