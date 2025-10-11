# Parallel Arc Fix - Boundary-to-Boundary Anchoring

**Date**: 2025-10-10  
**Status**: ✅ COMPLETE

## Problem Statement

Parallel arcs (arcs connecting the same two nodes in same or opposite directions) were being rendered with **offset anchor points** instead of anchoring at actual object boundaries. This caused visual inconsistencies where arcs appeared to float away from objects.

### Root Cause

The parallel arc offset was being applied to the **center coordinates** before calculating boundary points:

```python
# OLD (WRONG):
src_x += perp_x * offset_distance  # Offset the centers
tgt_x += perp_x * offset_distance
# Then calculate boundary points from offset centers
start_x, start_y = _get_boundary_point(source, src_x, src_y, ...)
```

This caused the boundary calculation to use **offset centers** instead of actual centers, resulting in arcs that didn't touch the objects at their true boundaries.

## Solution

**Apply parallel arc offset to the CONTROL POINT, not the endpoints:**

1. Calculate boundary points from **ACTUAL** object centers
2. Calculate midpoint from boundary points
3. Apply parallel arc offset **perpendicular** to the midpoint (for curved arcs only)
4. Add user control offsets on top of the offset midpoint

```python
# NEW (CORRECT):
# 1. Get boundary points from ACTUAL centers
start_x, start_y = _get_boundary_point(source, src_x, src_y, dx, dy)
end_x, end_y = _get_boundary_point(target, tgt_x, tgt_y, -dx, -dy)

# 2. Calculate midpoint
mid_x = (start_x + end_x) / 2
mid_y = (start_y + end_y) / 2

# 3. Apply parallel offset perpendicular to arc direction
if abs(parallel_offset) > 1e-6:
    perp_x = -dy_norm
    perp_y = dx_norm
    mid_x += perp_x * parallel_offset
    mid_y += perp_y * parallel_offset

# 4. Add user control offsets
control_x = mid_x + control_offset_x
control_y = mid_y + control_offset_y
```

## Files Modified

### 1. **`src/shypn/netobjs/arc.py`**
- **render() method** (lines 185-217):
  - Removed offset application to centers
  - Calculate boundary points from actual centers
  - Apply parallel offset to midpoint before adding control offsets
  
- **contains_point() method** (lines 470-516):
  - Updated hit detection to use same logic
  - Apply parallel offset to control point calculation only

### 2. **`src/shypn/edit/transformation/arc_transform_handler.py`**
- **_update_control_point() method** (lines 218-252):
  - Removed offset application to centers
  - Calculate boundary points from actual centers
  - Apply parallel offset to midpoint before calculating control offsets

### 3. **`src/shypn/edit/object_editing_transforms.py`**
- **_render_edit_mode_visual() method** (lines 354-378):
  - Added parallel arc offset detection
  - Apply offset to midpoint for blue preview rendering
  - Ensures preview matches actual arc

### 4. **`src/shypn/edit/transformation/handle_detector.py`**
- **get_handle_positions() method** (lines 155-212):
  - Calculate handle position from boundary midpoint
  - Apply parallel arc offset to midpoint
  - Ensures handle is at correct position

## Benefits

✅ **All arcs anchor at actual object boundaries** - perpendicular to object edge, touching at radius + border_width/2  
✅ **Parallel arcs separate visually** - through control point offset, not endpoint offset  
✅ **Consistent across all systems** - render, hit detection, transformation, preview  
✅ **Maintains user control** - manual control offsets still work correctly  
✅ **Handles legacy CurvedArc** - compatible with both Arc.is_curved and CurvedArc class  

## Visual Result

**Before**:
```
┌──────┐          ╱─────────────╲
│      │        ╱                 ╲
│  A   │───────                    ────┐
│      │        ╲                 ╱    │ B │
└──────┘          ╲─────────────╱      └───┘
         ↑ Arcs don't touch A properly
```

**After**:
```
┌──────┐╱─────────────╲
│      ◯                ╲
│  A   │                 ◯───┐
│      ◯                ╱    │ B │
└──────┘╲─────────────╱      └───┘
         ↑ All arcs touch boundaries correctly
```

## Testing

To test parallel arcs:
1. Create two nodes (Place and Transition)
2. Create an arc A → B
3. Create a second arc A → B (same direction)
4. Create a third arc B → A (opposite direction)
5. Verify all arcs:
   - Touch object boundaries (not floating)
   - Curve in different directions
   - Context menu works on all arcs
   - Transformation handles at correct positions
   - Blue preview matches real arc

## Integration with Existing Features

- **Boundary calculation**: Uses existing `_get_boundary_point()` method ✅
- **Border width accounting**: Correctly uses radius + border_width/2 ✅  
- **Arc transformation**: User can still drag handles to adjust curves ✅
- **Hit detection**: Works on all parts of curved parallel arcs ✅
- **Blue preview**: Matches actual arc rendering ✅

## Related Issues Fixed

This fix also resolved:
- Blue preview not matching actual arc during transformation
- Hit detection failing on middle of curved arcs
- Transformation handles at wrong positions for parallel arcs

## Notes

- Parallel arc offset is only applied to **curved** arcs (for visual separation)
- Straight parallel arcs remain at same position (will overlap visually)
- System auto-converts parallel arcs to curved when detected (via `_auto_convert_parallel_arcs_to_curved`)
- Offset calculation uses stable arc ID ordering to ensure consistent offsets
- Default offset: ±50px for opposite direction, ±15px for same direction

## Backward Compatibility

✅ Compatible with existing Petri net files  
✅ Works with both `Arc.is_curved` flag and legacy `CurvedArc` class  
✅ No changes to file format or arc properties  
✅ Existing arcs will render correctly with new logic  

