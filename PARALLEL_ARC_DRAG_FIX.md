# Parallel Arc Drag Fix

## Problem

Transformed parallel arcs did not maintain their curve shape correctly when the connected place or transition was dragged. The control point would drift to the wrong position.

## Root Cause

The issue was in how `control_offset_x/y` was calculated and stored during arc transformation.

### The Mismatch

**When dragging the transformation handle** (`arc_transform_handler.py`):
- Midpoint was calculated as simple average: `mid_x = (source.x + target.x) / 2`
- Did NOT account for parallel arc offset

**When rendering** (`arc.py`):
- Midpoint was calculated AFTER applying parallel arc offset
- Source/target positions were offset perpendicular to arc direction
- Then midpoint was calculated from these offset positions

### The Result

For parallel arcs:
1. User drags handle to position (200, 70)
2. Handler calculates midpoint without parallel offset
3. Stores `control_offset_x/y` relative to non-offset midpoint
4. When rendering, midpoint is calculated WITH parallel offset
5. Control point ends up in wrong position
6. When place/transition moves, the mismatch becomes visible

## Solution

Updated `arc_transform_handler.py` to calculate the midpoint using the same parallel arc offset logic that rendering uses.

### Changes Made

**File: `src/shypn/edit/transformation/arc_transform_handler.py`**

#### 1. `_update_control_point()` method (lines ~173-227)

Added parallel arc offset calculation before computing midpoint:

```python
# Calculate direction and length
dx = tgt_x - src_x
dy = tgt_y - src_y
length = (dx * dx + dy * dy) ** 0.5

# Check for parallel arcs and apply offset (same as rendering)
offset_distance = 0.0
if hasattr(arc, '_manager') and arc._manager:
    parallels = arc._manager.detect_parallel_arcs(arc)
    if parallels:
        offset_distance = arc._manager.calculate_arc_offset(arc, parallels)

# Apply parallel arc offset to endpoints if needed
if abs(offset_distance) > 1e-6 and length > 1e-6:
    # Normalize direction
    dx_norm = dx / length
    dy_norm = dy / length
    
    # Perpendicular vector (90° counterclockwise rotation)
    perp_x = -dy_norm
    perp_y = dx_norm
    
    # Offset the endpoints
    src_x += perp_x * offset_distance
    src_y += perp_y * offset_distance
    tgt_x += perp_x * offset_distance
    tgt_y += perp_y * offset_distance

# Calculate midpoint (after parallel offset, matching rendering)
mid_x = (src_x + tgt_x) / 2
mid_y = (src_y + tgt_y) / 2
```

#### 2. `_update_curved_arc_control_point()` method (lines ~139-193)

Applied the same fix for CurvedArc (legacy) class.

## How It Works Now

### 1. **Transformation**
- User drags handle to desired position
- Handler detects parallel arcs
- Calculates parallel arc offset (perpendicular displacement)
- Applies offset to source/target positions
- Calculates midpoint from offset positions
- Stores `control_offset_x/y` relative to offset midpoint

### 2. **Rendering**
- Detects parallel arcs
- Calculates parallel arc offset (same logic)
- Applies offset to source/target positions
- Calculates midpoint from offset positions
- Adds `control_offset_x/y` to offset midpoint
- Control point is in correct position!

### 3. **Dragging Place/Transition**
- Place/transition moves to new position
- Arc source/target positions change
- Parallel offset recalculates (perpendicular to new direction)
- Midpoint recalculates with new offset
- `control_offset_x/y` remains constant (as it should)
- Control point maintains correct relative position

## Testing

**Test file:** `test_parallel_arc_drag.py`

### Test Scenario
1. Create Place (100, 100) → Transition (300, 100)
2. Create parallel arcs in both directions
3. Transform arc1 to curved (drag handle to 200, 70)
4. Move Place to (150, 150)
5. Verify control point moves with the arc

### Results
```
Arc1 after transformation:
  is_curved: True
  control_offset_x: 0.00
  control_offset_y: -20.00
  Expected control point (with offset): (200.00, 70.00)

--- Moving Place1 to (150, 150) ---
  New control point (with offset): (221.84, 95.51)

✓ Control point moved with the arc
  Delta: (21.84, 25.51)

✓ Offsets remain constant (as expected)
```

## Impact

- ✅ **Parallel arcs**: Control points stay correctly positioned when place/transition moves
- ✅ **Non-parallel arcs**: No change in behavior (offset_distance = 0)
- ✅ **Straight arcs**: No change (is_curved = False)
- ✅ **Legacy CurvedArc**: Also fixed with same logic

## Related Files

**Modified:**
- `src/shypn/edit/transformation/arc_transform_handler.py`

**Test:**
- `test_parallel_arc_drag.py`

**Related (not modified):**
- `src/shypn/netobjs/arc.py` - Rendering logic (reference for parallel offset)
- `src/shypn/data/model_canvas_manager.py` - Parallel arc detection

## Conclusion

The fix ensures that `control_offset_x/y` is stored relative to the **same midpoint** that rendering uses, which accounts for parallel arc offsets. This makes curved parallel arcs behave correctly when their connected objects are dragged. ✅
