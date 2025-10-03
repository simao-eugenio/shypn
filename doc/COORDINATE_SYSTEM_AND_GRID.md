# Coordinate System and Grid Implementation

**Date:** October 3, 2025  
**Version:** 1.0  
**Status:** Implemented and Verified

## Overview

This document describes the coordinate transformation system, infinite canvas implementation, and DPI-aware grid rendering for the Shypn Petri Net editor.

---

## Coordinate System

### Core Formulas

The coordinate system uses two spaces:

1. **Screen Space** - Device pixels on the display
2. **World Space** - Logical model coordinates

**Transformations:**
```python
# Screen to World (device to logical)
world_x = screen_x / zoom - pan_x
world_y = screen_y / zoom - pan_y

# World to Screen (logical to device)
screen_x = (world_x + pan_x) * zoom
screen_y = (world_y + pan_y) * zoom
```

### Parameters

- **zoom**: Scale factor (1.0 = 100%, range: 0.3 to 3.0)
- **pan_x, pan_y**: World coordinates at screen origin
- **screen coordinates**: Pixels from top-left (0, 0)
- **world coordinates**: Logical units in model space

### Legacy Compatibility

These formulas match the legacy implementation exactly:
- `legacy/shypnpy/interface/coords.py` - `device_to_logical()` and `logical_to_device()`
- Ensures backward compatibility with existing models

---

## Pan System

### Implementation

**Approach:** Total-delta from start (legacy-compatible)

```python
# On button press: store initial state
state['start_x'] = event.x
state['start_y'] = event.y
state['start_pan_x'] = manager.pan_x
state['start_pan_y'] = manager.pan_y

# On motion: calculate total delta and set pan directly
dx = event.x - state['start_x']
dy = event.y - state['start_y']
manager.pan_x = state['start_pan_x'] + dx / manager.zoom
manager.pan_y = state['start_pan_y'] + dy / manager.zoom
```

**Key Points:**
1. Pan increases when dragging right/down (+= not -=)
2. Delta is total distance from original start, not incremental
3. Matches legacy `validate_ui.py` lines 7056-7062 exactly

### Pan Clamping

Prevents blank space while maintaining infinite canvas feeling:

```python
# Calculate extent (ensures viewport always covered)
extent_x = max(CANVAS_EXTENT, viewport_width / (2 * zoom))
extent_y = max(CANVAS_EXTENT, viewport_height / (2 * zoom))

# Clamp pan values
min_pan_x = (viewport_width / zoom) - extent_x
max_pan_x = extent_x
pan_x = clamp(pan_x, min_pan_x, max_pan_x)
```

**Result:** Canvas bounds of ±10,000 logical units with dynamic adjustment based on viewport size and zoom.

---

## Zoom System

### Pointer-Centered Zoom

Zoom is centered at the cursor position, keeping the world coordinate under the pointer stationary:

```python
# Get world coordinate under pointer before zoom
world_x = (pointer_x / zoom) - pan_x
world_y = (pointer_y / zoom) - pan_y

# Apply new zoom
zoom = new_zoom

# Adjust pan to keep world coordinate at same screen position
pan_x = (pointer_x / new_zoom) - world_x
pan_y = (pointer_y / new_zoom) - world_y
```

**Properties:**
- Zoom range: 30% to 300% (MIN_ZOOM=0.3, MAX_ZOOM=3.0)
- Zoom step: 1.1 (10% per scroll)
- Smooth zoom on trackpad, discrete on mouse wheel

---

## Infinite Canvas Grid

### Critical Design Principle

**The grid does NOT move - it is REGENERATED each frame.**

This is the key to the infinite canvas illusion. The grid appears stationary because we:
1. Calculate visible world bounds using coordinate transforms
2. Regenerate grid lines for that visible region
3. Never store or pan grid positions

### Visible Bounds Calculation

```python
def get_visible_bounds(self):
    """Calculate visible area in world coordinates."""
    # Top-left corner of viewport (screen origin)
    min_x, min_y = self.screen_to_world(0, 0)
    # Bottom-right corner of viewport
    max_x, max_y = self.screen_to_world(self.viewport_width, self.viewport_height)
    return min_x, min_y, max_x, max_y
```

**Critical Fix:** Previously used `min_x = pan_x` which was incorrect. The proper transform is:
```
min_x = 0 / zoom - pan_x = -pan_x
max_x = viewport_width / zoom - pan_x
```

### Grid Regeneration

Each frame:
1. Get visible bounds in world coordinates
2. Calculate grid line positions using `floor(min / spacing) * spacing`
3. Draw lines within visible bounds
4. Grid appears infinite and stationary

---

## DPI-Aware Grid

### Physical Spacing

Grid spacing is defined in physical millimeters, converted to pixels based on screen DPI:

```python
# Base configuration
BASE_GRID_SPACING = 1.0  # 1mm physical

# DPI conversion
px_per_mm = screen_dpi / 25.4
base_px = BASE_GRID_SPACING * px_per_mm
```

**At 96 DPI:**
- 1mm = 96 / 25.4 = 3.7795 pixels

### Adaptive Grid Spacing

Grid spacing adapts based on zoom level to maintain usability:

| Zoom Range | Minor Cell | Major Cell | Use Case |
|------------|------------|------------|----------|
| ≥ 5.0× (500%+) | 0.2 mm | 1 mm | Very fine detail |
| ≥ 2.0× (200-500%) | 0.5 mm | 2.5 mm | Fine detail |
| **≥ 0.5× (50-200%)** | **1 mm** | **5 mm** | **Normal work** |
| ≥ 0.2× (20-50%) | 2 mm | 10 mm | Coarse overview |
| < 0.2× (<20%) | 5 mm | 25 mm | Very coarse overview |

**Design Target at 100% Zoom:**
- Minor grid cell: **1 mm** (3.78 pixels @ 96 DPI)
- Major grid cell: **5 mm** (18.90 pixels @ 96 DPI)
- Major lines: Every 5th line (`GRID_MAJOR_EVERY = 5`)

### Visual Styling

**Minor Lines:**
- Color: RGB(0.85, 0.85, 0.88) with alpha 0.6
- Width: 0.5 / zoom (constant screen size)

**Major Lines:**
- Color: RGB(0.65, 0.65, 0.68) with alpha 0.8
- Width: 1.0 / zoom (constant screen size)

**Line Width Compensation:**
```python
cr.set_line_width(width / zoom)
```
This ensures grid lines maintain constant pixel width on screen regardless of zoom level.

---

## Object Metrics at 100% Zoom

### Proportional Design

All objects are sized proportionally with Place radius as the base unit:

| Object | Size (pixels) | Physical Size | Grid Relationship |
|--------|---------------|---------------|-------------------|
| **Place radius** | 25 px | ~6.6 mm | 1.3 major cells |
| **Place diameter** | 50 px | ~13.2 mm | 2.6 major cells |
| **Transition width** | 50 px | ~13.2 mm | 2.6 major cells |
| **Transition height** | 25 px | ~6.6 mm | 1.3 major cells |
| **Border width** | 3 px | ~0.8 mm | Constant visual size |

**Proportional Relationship:**
- Transition width = Place diameter
- Transition height = Place radius
- All sizes scale with zoom

### Border Width Compensation

```python
cr.set_line_width(3.0 / zoom)
```
Ensures borders maintain constant 3-pixel visual width regardless of zoom.

---

## Implementation Files

### Core Manager
- `src/shypn/data/model_canvas_manager.py`
  - Coordinate transformations (lines 125-150)
  - Pan operations (lines 490-530)
  - Zoom operations (lines 390-450)
  - Pan clamping (lines 451-488)
  - Grid spacing calculation (lines 538-563)
  - Visible bounds calculation (lines 567-580)
  - Grid rendering (lines 582-720)

### Event Handling
- `src/shypn/helpers/model_canvas_loader.py`
  - Pan drag implementation (lines 460-530)
  - Zoom scroll handling (lines 532-580)
  - DPI detection (lines 241-254)

### Object Definitions
- `src/shypn/api/place.py` - Place with DEFAULT_RADIUS = 25.0
- `src/shypn/api/transition.py` - Transition with DEFAULT_WIDTH = 50.0, DEFAULT_HEIGHT = 25.0

---

## Testing and Validation

### Coordinate Transform Tests

```python
# Round-trip accuracy
world_x, world_y = 100.0, 200.0
screen_x, screen_y = world_to_screen(world_x, world_y)
result_x, result_y = screen_to_world(screen_x, screen_y)
assert result_x == world_x and result_y == world_y
```

### Pan Behavior Tests

1. **Drag right:** Objects move right (pan increases)
2. **Drag down:** Objects move down (pan increases)
3. **Release:** Pan stops at current position
4. **Multi-drag:** Each drag starts from previous position

### Zoom Behavior Tests

1. **Pointer-centered:** World coordinate under cursor stays fixed
2. **Zoom in:** Grid spacing decreases, objects grow
3. **Zoom out:** Grid spacing increases, objects shrink
4. **Limits:** Clamped to 30%-300% range

### Grid Tests

1. **Infinite illusion:** Grid appears stationary during pan
2. **No drift:** Grid lines align consistently
3. **DPI awareness:** Physical spacing consistent across displays
4. **Major/minor pattern:** Every 5th line is darker/thicker

---

## Performance Considerations

### Grid Rendering Optimization

1. **Visible bounds only:** Grid lines drawn only within viewport
2. **Efficient spacing:** Adaptive grid prevents over-cluttering
3. **Line width compensation:** Simple division, no complex calculations

### Redraw Triggering

Grid is redrawn on:
- Pan operation (`_needs_redraw = True`)
- Zoom operation (`_needs_redraw = True`)
- Viewport resize (automatic)

---

## Troubleshooting

### Issue: Grid appears to drift during zoom

**Cause:** Incorrect visible bounds calculation  
**Solution:** Use `screen_to_world()` transform, not direct pan access

### Issue: Pan direction inverted

**Cause:** Using `-=` instead of `+=` in pan calculation  
**Solution:** Pan should increase when dragging right/down

### Issue: Grid too fine or too coarse

**Cause:** Adaptive threshold misconfiguration  
**Solution:** Adjust thresholds in `get_grid_spacing()` for desired density

### Issue: Objects drift during zoom

**Cause:** Pan adjustment formula incorrect  
**Solution:** Use `pan = screen/new_zoom - world` formula after zoom change

---

## Future Enhancements

### Possible Improvements

1. **Zoom percentage display** - Show current zoom level in UI
2. **Grid style toggle** - Switch between line/dot/cross styles
3. **Snap to grid** - Align objects to grid intersections
4. **Custom grid spacing** - User-defined base spacing
5. **Grid color themes** - Different color schemes for visual comfort

### Compatibility Notes

All coordinate transformations maintain legacy compatibility:
- Existing models load correctly
- Object positions preserved
- Export/import format unchanged

---

## References

### Legacy Code Analysis

- `legacy/shypnpy/interface/coords.py` - Coordinate formulas
- `legacy/shypnpy/interface/validate_ui.py` - Pan implementation (lines 7056-7062)
- `legacy/shypnpy/interface/zoom_infinite.py` - Zoom and clamp algorithms
- `legacy/shypnpy/core/petri.py` - Original object sizes

### Documentation

- `doc/INFINITE_CANVAS_SCALING_ANALYSIS.md` - Comprehensive legacy analysis
- `doc/IMPLEMENTATION_PLAN_1_TO_1_SCALE.md` - Implementation planning

---

## Change Log

### October 3, 2025 - Initial Implementation

**Coordinate System:**
- ✅ Implemented correct screen ↔ world transforms
- ✅ Verified formulas match legacy exactly

**Pan System:**
- ✅ Fixed pan direction (changed -= to +=)
- ✅ Implemented total-delta approach (store initial pan)
- ✅ Added pan clamping for infinite canvas (±10,000 extent)

**Grid System:**
- ✅ Fixed visible bounds calculation (use screen_to_world)
- ✅ Grid regenerates each frame (infinite illusion)
- ✅ Implemented DPI-aware spacing (1mm physical base)
- ✅ Configured adaptive thresholds (1mm at 100% zoom)
- ✅ Target achieved: 5mm major cells at 100% zoom

**Object Metrics:**
- ✅ Proportional design: radius=25px base
- ✅ Transition sized relative to Place circle
- ✅ Border width compensation (constant 3px visual)

**Testing:**
- ✅ Application runs without errors
- ✅ DPI detection working (96.0)
- ✅ Pan follows cursor correctly
- ✅ Grid appears stationary
- ✅ Zoom stays pointer-centered

---

**Document Version:** 1.0  
**Last Updated:** October 3, 2025  
**Author:** GitHub Copilot + Simão Eugénio  
**Status:** Complete and Verified ✅
