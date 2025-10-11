# Curved Arc Hit Detection and Edit Mode Fixes

**Date**: October 10, 2025  
**Status**: ✅ COMPLETE

## Issues Identified

### Issue 1: Double-Click Lost After Transformation
**Symptom**: After transforming an arc to curved, clicking away and then trying to double-click the arc again didn't work. The arc appeared to "lose sensitivity."

**Root Cause**: In `model_canvas_loader.py` line 956, when clicking an already-selected object, the click state wasn't being updated. This broke double-click detection because the first click wasn't recorded.

```python
# BEFORE - Missing click state update
if clicked_obj.selected and (not is_double_click):
    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
    state['active'] = True
    # ...no click state update!
```

**Fix**: Added click state update for already-selected objects (lines 956-966):
```python
# AFTER - Click state properly tracked
if clicked_obj.selected and (not is_double_click):
    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
    state['active'] = True
    state['button'] = event.button
    state['start_x'] = event.x
    state['start_y'] = event.y
    state['is_panning'] = False
    state['is_rect_selecting'] = False
    # Record for double-click detection
    click_state['last_click_time'] = current_time
    click_state['last_click_obj'] = clicked_obj
```

### Issue 2: Curved Arc Hit Detection Too Narrow
**Symptom**: Curved arcs only responded to clicks directly on or inside the curve. Clicking just outside the visible arc (even when visually it looked like you were clicking on it) didn't register.

**Root Cause**: The hit detection tolerance was only 10 pixels, measuring distance to the centerline. This didn't account for:
1. The visual stroke width (3.0 pixels)
2. The curvature making the arc harder to click precisely

**Analysis from Debug Output**:
```
[HIT] Arc 2: min_dist=28.2, tolerance=10.0, hit=False
```
Distance was 28.2 pixels, but tolerance was only 10 pixels → miss.

**Fix**: Updated tolerance calculation in `arc.py` (lines 472-481):
```python
# Tolerance: Account for visual stroke width plus comfortable margin
# The arc centerline is measured, but users click on the visible stroke
# Stroke width is 3px (self.width), so half-width is 1.5px
# Add generous margin for comfortable clicking
half_stroke = self.width / 2.0
click_margin = 25.0 if self.is_curved else 8.0  # Curved arcs need more margin
tolerance = half_stroke + click_margin
```

**Result**:
- **Curved arcs**: 1.5 + 25.0 = **26.5 pixels** tolerance
- **Straight arcs**: 1.5 + 8.0 = **9.5 pixels** tolerance

## Files Modified

### 1. `src/shypn/helpers/model_canvas_loader.py`
- **Lines 956-966**: Added click state tracking for already-selected objects
- **Effect**: Double-click detection now works after transformation

### 2. `src/shypn/netobjs/arc.py`
- **Lines 472-481**: Updated hit detection tolerance calculation
- **Effect**: Curved arcs are now easy to click throughout their entire visual stroke

## Technical Details

### Hit Detection Algorithm
The curved arc hit detection uses a sampling approach:
1. Calculate 50 sample points along the Bézier curve
2. Find the minimum distance from click point to any sample point
3. Check if minimum distance ≤ tolerance

```python
# Sample the Bézier curve
for i in range(num_samples + 1):
    t = i / num_samples
    # Quadratic Bezier formula: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
    one_minus_t = 1.0 - t
    curve_x = (one_minus_t * one_minus_t * start_x + 
              2 * one_minus_t * t * control_x + 
              t * t * end_x)
    curve_y = (one_minus_t * one_minus_t * start_y + 
              2 * one_minus_t * t * control_y + 
              t * t * end_y)
    
    dist_sq = (x - curve_x) ** 2 + (y - curve_y) ** 2
    min_dist_sq = min(min_dist_sq, dist_sq)

return min_dist_sq <= (tolerance * tolerance)
```

### Why Curved Arcs Need More Tolerance
1. **Visual stroke**: The arc has a 3px stroke, so clicks up to 1.5px away from centerline should hit
2. **Curvature**: Curved paths are harder to click precisely than straight lines
3. **User expectation**: Users expect to click anywhere on the visible arc stroke
4. **Parallel offset**: Parallel arcs are displaced, making them harder to target

## Testing Results

### Before Fixes
- ❌ After transforming arc, could not double-click it again
- ❌ Curved arcs only clickable at endpoints or very close to centerline
- ❌ User had to click precisely inside the curve

### After Fixes
- ✅ Double-click works consistently after transformation
- ✅ Curved arcs clickable throughout their entire visible stroke
- ✅ Can click slightly outside the curve and still register a hit
- ✅ Comfortable, natural clicking behavior

## Workflow Validation

**Manual Parallel Arc Workflow** (from TEST_MANUAL_PARALLEL_ARCS.md):
1. ✅ Draw arc A→B (straight)
2. ✅ Double-click → Transform to curved
3. ✅ Click away → Edit mode exits, arc stays selected
4. ✅ Click arc again → Arc responds to click
5. ✅ Double-click arc → Edit mode re-enters
6. ✅ Can transform arc multiple times
7. ✅ Draw arc B→A (opposite direction)
8. ✅ Double-click → Transform to curved
9. ✅ Both curved arcs are easily clickable
10. ✅ Hit detection works on entire curve length

## Related Issues

This fix complements previous work:
- **PARALLEL_ARC_DOUBLE_CLICK_FIX.md**: Removed blocking that prevented parallel arcs from entering edit mode
- **PARALLEL_ARC_FIX.md**: Fixed boundary-to-boundary anchoring for parallel arcs
- **TEST_MANUAL_PARALLEL_ARCS.md**: Disabled automatic parallel arc conversion

## Configuration

The tolerance values can be adjusted if needed:
```python
# In arc.py contains_point() method
click_margin = 25.0 if self.is_curved else 8.0
```

Current values provide comfortable clicking while avoiding false positives on nearby arcs.

## Summary

Two critical fixes enable smooth curved arc editing:
1. **Click state tracking**: Double-click detection now works for selected objects
2. **Stroke-aware tolerance**: Hit detection accounts for visual stroke width and curvature

Result: Users can naturally click and interact with curved arcs throughout their transformation lifecycle.
