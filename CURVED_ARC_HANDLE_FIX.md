# Curved Arc Handle Positioning Fix

## Issue

When double-clicking on `CurvedArc` instances (legacy curved arc class), the transformation handle was appearing at the straight-line midpoint with a perpendicular offset, rather than at the actual curve control point where the curve is rendered.

## Root Cause

The `HandleDetector._get_arc_handle_positions()` method only checked the `is_curved` flag (new curve system) but didn't account for `CurvedArc` class instances which use their own `_calculate_curve_control_point()` method.

## Solution

Updated `HandleDetector._get_arc_handle_positions()` to:

1. **Check if arc is `CurvedArc` instance first**
   - Use `isinstance(arc, CurvedArc)`
   - Call arc's own `_calculate_curve_control_point()` method
   - Account for parallel arc detection and offset (via `_manager`)

2. **Then check `is_curved` flag**
   - For arcs using the new curve system
   - Use `control_offset_x` and `control_offset_y` properties

3. **Finally fallback to straight arc logic**
   - Perpendicular offset for visibility

## Code Changes

**File**: `src/shypn/edit/transformation/handle_detector.py`

### Before
```python
def _get_arc_handle_positions(self, arc, zoom: float) -> dict:
    # ...
    
    # If curved, offset by control point
    if arc.is_curved:
        control_offset_x = getattr(arc, 'control_offset_x', 0.0)
        control_offset_y = getattr(arc, 'control_offset_y', 0.0)
        handle_x = mid_x + control_offset_x
        handle_y = mid_y + control_offset_y
    else:
        # Straight arc: handle at midpoint, but offset perpendicular
        # ...
```

### After
```python
def _get_arc_handle_positions(self, arc, zoom: float) -> dict:
    from shypn.netobjs.curved_arc import CurvedArc
    
    # ...
    
    # Check if this is a CurvedArc instance (legacy curved arc class)
    if isinstance(arc, CurvedArc):
        # Use CurvedArc's own control point calculation
        # This accounts for parallel arc detection and offset
        offset_distance = None
        if hasattr(arc, '_manager') and arc._manager:
            try:
                parallels = arc._manager.detect_parallel_arcs(arc)
                if parallels:
                    offset_distance = arc._manager.calculate_arc_offset(arc, parallels)
            except (AttributeError, Exception):
                pass
        
        control_point = arc._calculate_curve_control_point(offset=offset_distance)
        if control_point:
            handle_x, handle_y = control_point
        else:
            handle_x = mid_x
            handle_y = mid_y
    # Check if arc uses the is_curved flag (new curve system)
    elif getattr(arc, 'is_curved', False):
        control_offset_x = getattr(arc, 'control_offset_x', 0.0)
        control_offset_y = getattr(arc, 'control_offset_y', 0.0)
        handle_x = mid_x + control_offset_x
        handle_y = mid_y + control_offset_y
    else:
        # Straight arc: handle at midpoint, but offset perpendicular
        # ...
```

## Test Results

All tests in `test_curved_arc_handle_position.py` pass:

```
✓ CurvedArc handle is at the correct position!
✓ Opposite curved arcs have correctly positioned handles!
✓ CurvedInhibitorArc handle is at the correct position!
✓ Straight and curved arcs have different handle positions!
```

## Affected Arc Types

✅ **CurvedArc** - Handle now appears at curve control point (20% offset)

✅ **CurvedInhibitorArc** - Inherits fix from CurvedArc

✅ **Arc** with `is_curved=True` - Still works (new system)

✅ **InhibitorArc** with `is_curved=True` - Still works

## Behavior Details

### CurvedArc Control Point Logic

`CurvedArc` uses a **canonical direction** for control point calculation:
- For arcs A→B and B→A, both use the same control point
- The curves differ by which end is source vs. target
- This creates **mirror-symmetric** opposite curves
- Handle appears at the shared control point

### With Manager (Parallel Arc Detection)

When arcs have a `_manager` reference:
- System detects parallel/opposite arcs
- Applies different offsets to separate the curves
- Handles appear at their respective adjusted control points

### Without Manager

- Default 20% offset from midpoint perpendicular to line
- Opposite arcs share the same control point
- Still correct - curves differ by source/target direction

## Visual Improvement

**Before**: Handle appeared offset from the straight line between endpoints

**After**: Handle appears exactly on the curve, making it intuitive to grab and adjust

## Examples

### Single CurvedArc
```
Place(100,100) → Transition(300,100)
Control Point: (200, 140)  ← 40 units above midpoint
Handle: (200, 140)          ← Now correctly positioned!
```

### Straight vs. Curved
```
Straight Arc Handle: (200, 115)  ← Small perpendicular offset
Curved Arc Handle:   (200, 140)  ← At actual curve control point
Separation: 25 pixels            ← Clearly distinguishable
```

## Integration

The fix is **transparent** to users:
- No API changes
- No configuration needed
- Works automatically for all `CurvedArc` instances
- Backward compatible with `is_curved` flag system

## Related Files

- `src/shypn/edit/transformation/handle_detector.py` - Fix implemented here
- `src/shypn/netobjs/curved_arc.py` - Control point calculation
- `src/shypn/netobjs/curved_inhibitor_arc.py` - Inherits behavior
- `test_curved_arc_handle_position.py` - Comprehensive tests

## Summary

✅ **Fixed**: Curved arc handles now appear at the actual curve control point

✅ **Tested**: All arc types and scenarios verified

✅ **Backward Compatible**: Both curve systems supported

✅ **Intuitive**: Handle position matches visual curve location
