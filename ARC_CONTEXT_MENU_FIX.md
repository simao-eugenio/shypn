# Arc Context Menu Fix - Auto-Converted Curved Arcs

## Problem

Auto-converted curved arcs (created when opposite direction arcs are detected) were not responding to right-click context menu. The context menu would not appear when clicking on the curved portions of the arcs.

## Root Cause

The `contains_point()` method in `CurvedArc` was calculating the bezier curve **without the offset parameter**, while the `render()` method was drawing the curve **with the offset** (±50px for opposite arcs).

This mismatch meant:
- The arc was drawn with offset (curved to one side)
- Hit detection checked against the non-offset curve (center)
- Clicking on the visible curve didn't register as a hit

## Solution

Modified `CurvedArc.contains_point()` to match the rendering logic exactly:

1. **Detect parallel arcs** (same as `render()`)
2. **Calculate offset** using `calculate_arc_offset()` (+50 or -50px)
3. **Pass offset to control point calculation**
4. **Use same curve for hit detection** as is rendered

### Code Changes

**File: `src/shypn/netobjs/curved_arc.py`**

```python
def contains_point(self, x: float, y: float) -> bool:
    try:
        # Calculate offset for parallel arcs (same as rendering)
        offset_distance = None
        if hasattr(self, '_manager') and self._manager:
            parallels = self._manager.detect_parallel_arcs(self)
            if parallels:
                offset_distance = self._manager.calculate_arc_offset(self, parallels)
        
        # Calculate control point with offset (same as rendering)
        control_point = self._calculate_curve_control_point(offset=offset_distance)
        
        # ... rest of bezier distance calculation
```

### Key Points

1. **Offset calculation**: Must match render() exactly
2. **Boundary points**: Uses `_get_boundary_point()` to match rendered endpoints
3. **Bezier sampling**: 20 samples along the curve for accurate hit detection
4. **Tolerance**: 15px in world space (generous for clicking)

## Testing

**Test Case:**
1. Create P1 and T1
2. Create arc P1→T1 (straight)
3. Create arc T1→P1 (triggers auto-conversion of both to curved)
4. Right-click on curved arc
5. Context menu should appear with transformation options

**Expected Behavior:**
- ✅ Context menu appears on curved arcs
- ✅ Can transform curved → straight
- ✅ Can convert to inhibitor (with validation)
- ✅ All transformations work correctly

## Related Features

- **Automatic parallel detection**: `model_canvas_manager.detect_parallel_arcs()`
- **Auto-conversion**: `_auto_convert_parallel_arcs_to_curved()`
- **Mirror symmetry**: Opposite arcs curve on opposite sides (ellipse shape)
- **Context menu**: Full arc transformation support maintained

## Commit Message

```
fix: Curved arc context menu hit detection

Auto-converted curved arcs were not responding to right-click because
contains_point() was checking against non-offset curve while render()
drew offset curve.

Now contains_point() calculates same offset and control point as
render(), ensuring hit detection matches visible curve exactly.

Fixes context menu access for automatically-curved opposite arcs.
```

## Files Modified

- `src/shypn/netobjs/curved_arc.py` - Fixed `contains_point()` to use offset
- Removed debug output from all files after verification

## Impact

All auto-converted curved arcs now properly respond to context menu, enabling:
- Transformation back to straight arcs
- Conversion to/from inhibitor arcs
- Full editing workflow for parallel arc pairs
