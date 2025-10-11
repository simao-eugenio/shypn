# Arc Boundary Precision Fix

**Date**: October 10, 2025  
**Status**: ✅ Complete

## Problem

Arc endpoints were not touching object boundaries correctly:
1. Initially: ~3px gap between arc and object perimeter
2. After first fix: ~3px invasion into objects
3. Final issue: Inhibitor arc hollow circles not touching perimeter on curved parallel arcs

## Root Cause

The border stroke calculation was incorrect. Objects have a border that is **centered** on the mathematical perimeter:
- Inner edge: `perimeter - border_width/2` (e.g., radius - 1.5px for 3px border)
- Outer edge: `perimeter + border_width/2` (e.g., radius + 1.5px for 3px border)

Arcs should touch at the **outer edge** for natural appearance.

## Solution

### 1. Arc Boundary Point Calculation (`src/shypn/netobjs/arc.py`)

Fixed `_get_boundary_point()` to properly account for border width:

**For Places (circles)**:
```python
border_width = getattr(obj, 'border_width', 3.0)
border_offset = border_width / 2.0  # +1.5px for 3px border
effective_radius = obj.radius + border_offset
```

**For Transitions (rectangles)**:
```python
border_offset = border_width / 2.0
half_w = w / 2 + border_offset
half_h = h / 2 + border_offset
```

This ensures arcs touch at the **outer edge** of the border (+1.5px from mathematical perimeter).

### 2. Inhibitor Arc Hollow Circle Position (`src/shypn/netobjs/inhibitor_arc.py`)

Fixed curved inhibitor arcs to position hollow circle using **straight-line direction** instead of curve tangent:

**Before** (incorrect):
```python
# Used curve tangent direction (dx_end, dy_end)
boundary_x, boundary_y = self._get_boundary_point(
    self.target, tgt_world_x, tgt_world_y, -dx_end, -dy_end)
marker_x = boundary_x - dx_end * marker_radius
marker_y = boundary_y - dy_end * marker_radius
```

**After** (correct):
```python
# Calculate straight-line direction from source to target
dx_straight = tgt_world_x - src_world_x
dy_straight = tgt_world_y - src_world_y
length_straight = math.sqrt(dx_straight*dx_straight + dy_straight*dy_straight)
dx_straight /= length_straight
dy_straight /= length_straight

# Use straight-line direction for boundary and marker positioning
boundary_x, boundary_y = self._get_boundary_point(
    self.target, tgt_world_x, tgt_world_y, -dx_straight, -dy_straight)
marker_x = boundary_x - dx_straight * marker_radius
marker_y = boundary_y - dy_straight * marker_radius
```

**Why this matters**: For curved parallel arcs with control point offset, the curve tangent at the target can be significantly different from the straight-line direction. The hollow circle should be positioned radially (straight line to target), not tangentially (along curve direction).

## Files Modified

1. **`src/shypn/netobjs/arc.py`**
   - Lines 285-330: `_get_boundary_point()` - Added border_offset calculation
   - Removed obsolete code that tried to extend rectangle intersection by non-existent border_offset

2. **`src/shypn/netobjs/inhibitor_arc.py`**
   - Lines 270-290: `_render_curved()` - Use straight-line direction for hollow circle positioning

## Verification

### Test Cases
✅ Straight arcs touch object boundaries precisely  
✅ Curved arcs touch object boundaries precisely  
✅ Parallel curved arcs touch boundaries on both sides  
✅ Inhibitor arc hollow circles touch boundaries (straight arcs)  
✅ Inhibitor arc hollow circles touch boundaries (curved arcs)  
✅ Inhibitor arc hollow circles touch boundaries (curved parallel arcs)  

### Visual Characteristics
- Arc endpoints touch at the **outer edge** of the 3px border
- This is at `radius + 1.5px` for circles
- This is at `(width/2 + 1.5px, height/2 + 1.5px)` for rectangles
- Hollow circles positioned radially, ensuring edge-to-edge contact with target

## Technical Details

### Border Width Accounting
```
Object Geometry:
├── Mathematical perimeter (radius for circles, width/height for rectangles)
├── Border stroke (3px wide, centered on perimeter)
│   ├── Inner edge: perimeter - 1.5px
│   └── Outer edge: perimeter + 1.5px (visible boundary)
└── Arc touch point: Outer edge (perimeter + 1.5px)
```

### Curved Arc Geometry
For curved arcs with parallel offset:
- **Control point**: Offset perpendicular to straight-line direction
- **Curve tangent at target**: Direction from control point to target
- **Hollow circle direction**: Straight line from source to target (NOT tangent)

This ensures the hollow circle is positioned radially, maintaining proper edge-to-edge contact even when the curve approaches from an angle.

## Related Issues

- Parallel arc separation (already fixed - arcs curve to opposite sides)
- Inhibitor arc hollow circle rendering (already fixed - curve stops before circle)
- Arc hit detection (already fixed - 26.5px tolerance for curved arcs)

## Conclusion

All arc boundary precision issues are now resolved:
1. ✅ Arcs touch at outer edge of border (+1.5px)
2. ✅ No gaps or invasions at boundaries
3. ✅ Inhibitor hollow circles positioned correctly on curved parallel arcs
