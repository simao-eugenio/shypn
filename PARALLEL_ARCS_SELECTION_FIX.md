# Parallel Curved Arcs Selection Fix

## Issue

When selecting one of the parallel curved arcs, the transformation handle (little square) appeared correctly at the curve's control point, but the blue selection arc (the thick blue line showing which arc is selected) was "mirrored" and invaded the centers of Place/Transition objects. The blue arc should appear on the same side as the transformation handle.

## Root Cause

The selection rendering code in `ObjectEditingTransforms` was calculating the control point for curved arcs WITHOUT considering parallel arc offsets.

### How Parallel Arcs Work

When two arcs connect the same pair of nodes in opposite directions (e.g., Place→Transition and Transition→Place), they are called **parallel arcs** or **opposite arcs**.

For `CurvedArc` instances:
1. By default, both arcs would use the same control point (canonical direction design)
2. This causes them to overlap visually
3. The `ModelCanvasManager.detect_parallel_arcs()` detects this situation
4. The `ModelCanvasManager.calculate_arc_offset()` calculates different offsets for each arc
5. One arc curves above the straight line, the other curves below

### The Problem

**Arc Rendering** (`CurvedArc.render()`):
```python
# Check for parallel arcs and calculate offset
offset_distance = None
if hasattr(self, '_manager') and self._manager:
    parallels = self._manager.detect_parallel_arcs(self)
    if parallels:
        offset_distance = self._manager.calculate_arc_offset(self, parallels)

# Calculate control point WITH offset
control_point = self._calculate_curve_control_point(offset=offset_distance)
```

**Selection Rendering** (BEFORE fix):
```python
# Get control point
if isinstance(obj, CurvedArc):
    if hasattr(obj, 'manual_control_point') and obj.manual_control_point is not None:
        control_x, control_y = obj.manual_control_point
    else:
        # Use automatic calculation WITHOUT parallel arc offset
        control_point = obj._calculate_curve_control_point()  # ❌ Missing offset!
```

Result: The arc renders curved upward, but the selection renders curved downward (or vice versa), appearing "mirrored".

## Solution

Updated both selection rendering methods in `object_editing_transforms.py` to include parallel arc offset detection:

### File: `src/shypn/edit/object_editing_transforms.py`

**Two methods updated:**

1. **`_render_object_selection()`** - Renders the thick blue selection highlight
2. **`_render_edit_mode_visual()`** - Renders the dashed blue edit mode outline

**Changes Applied (both methods):**

```python
# Get control point
if isinstance(obj, CurvedArc):
    # CurvedArc: check for manual control point first
    if hasattr(obj, 'manual_control_point') and obj.manual_control_point is not None:
        control_x, control_y = obj.manual_control_point
    else:
        # Use automatic calculation with parallel arc offset ✅ ADDED
        offset_distance = None
        if hasattr(obj, '_manager') and obj._manager:
            try:
                parallels = obj._manager.detect_parallel_arcs(obj)
                if parallels:
                    offset_distance = obj._manager.calculate_arc_offset(obj, parallels)
            except (AttributeError, Exception):
                pass
        
        control_point = obj._calculate_curve_control_point(offset=offset_distance)  # ✅ WITH OFFSET
        if control_point:
            control_x, control_y = control_point
        else:
            control_x, control_y = mid_x, mid_y
else:
    # Arc with is_curved flag: use control offsets
    control_x = mid_x + getattr(obj, 'control_offset_x', 0.0)
    control_y = mid_y + getattr(obj, 'control_offset_y', 0.0)
```

## Result

Now the selection rendering:
1. ✅ Detects if the arc has parallel arcs via `_manager.detect_parallel_arcs()`
2. ✅ Calculates the appropriate offset via `_manager.calculate_arc_offset()`
3. ✅ Uses the offset when calculating the control point
4. ✅ Renders the blue selection arc on the **same side** as the actual arc
5. ✅ Transformation handle and selection outline are **aligned**

## Visual Comparison

### Before Fix

```
Place ----arc1 (rendered above)----> Transition
      <---arc2 (rendered below)------

When selecting arc1:
  - Actual arc: curves ABOVE straight line
  - Blue selection: curves BELOW straight line ❌ WRONG SIDE
  - Handle: appears above ✓
  - Selection and handle on OPPOSITE sides
```

### After Fix

```
Place ----arc1 (rendered above)----> Transition
      <---arc2 (rendered below)------

When selecting arc1:
  - Actual arc: curves ABOVE straight line
  - Blue selection: curves ABOVE straight line ✅ CORRECT SIDE
  - Handle: appears above ✓
  - Selection and handle on SAME side ✓
```

## Technical Details

### Parallel Arc Offset Calculation

The `ModelCanvasManager` uses this logic:
- Arc with lower ID or "forward" direction gets positive offset (curves one way)
- Arc with higher ID or "backward" direction gets negative offset (curves opposite way)
- Offsets are perpendicular to the straight line connecting the nodes
- Typical offset distance: 20-40 pixels depending on line length

### Control Point Calculation

For `CurvedArc`:
```python
def _calculate_curve_control_point(self, offset=None):
    # Calculate midpoint
    mx = (source.x + target.x) / 2
    my = (source.y + target.y) / 2
    
    # Calculate perpendicular direction
    perpendicular = rotate_90_degrees(direction)
    
    # Apply offset (or default 20% of line length)
    if offset is None:
        offset = length * 0.20
    
    # Control point = midpoint + perpendicular * offset
    control_x = mx + perp_x * offset
    control_y = my + perp_y * offset
    
    return (control_x, control_y)
```

When `offset` is positive, curve goes one way; when negative, it goes the opposite way.

## Files Modified

**`src/shypn/edit/object_editing_transforms.py`** (2 locations):
- Line ~215-238: Updated `_render_object_selection()` for CurvedArc parallel arc offset
- Line ~345-368: Updated `_render_edit_mode_visual()` for CurvedArc parallel arc offset

## Testing

The fix ensures that for parallel/opposite curved arcs:
1. Each arc renders with its own offset
2. Selection rendering uses the **same** offset as arc rendering
3. Edit mode outline uses the **same** offset as arc rendering
4. Transformation handle uses the **same** offset (already working)
5. All visual elements (arc, selection, outline, handle) are **aligned** and on the **same side**

## Benefits

✅ **Visual Consistency**: Selection outline matches actual arc path

✅ **Intuitive Interaction**: Handle appears where user expects (on the curve)

✅ **No Visual Clutter**: No crossing or overlapping selection artifacts

✅ **Parallel Arc Support**: Correctly handles opposite arcs without confusion

## Notes

- This fix applies to **`CurvedArc`** class instances (legacy curve system)
- For `Arc` with `is_curved` flag (new system), parallel arc support is separate
- The fix includes try-except to handle cases where manager is not available
- Manual control points (after user transformation) take precedence over automatic calculation
