# Arc Transformation Refinements

## Issues to Fix

1. **Curved arc endpoint too far inside target** - Need to adjust boundary calculation for curved arcs
2. **Transformed arcs don't respond to context menu** - Need to ensure selection works on new arc types
3. **Hollow circle should reduce target intersection** - Inhibitor arcs should stop before the hollow circle

## Solutions

### Issue 1: Curved Arc Endpoint Position

**Problem:** When transforming to curved arc, the tangent direction at the endpoint causes incorrect boundary calculation.

**Solution:** Override `_get_boundary_point` in CurvedArc to account for the curve's tangent at the endpoint, not the straight-line direction.

**File:** `src/shypn/netobjs/curved_arc.py`

### Issue 2: Transformed Arcs Context Menu

**Problem:** After transformation, the new arc instance might not be properly wired for selection/interaction.

**Solution:** Ensure `on_changed` callback and manager reference are copied during transformation.

**File:** `src/shypn/utils/arc_transform.py` (already fixed)

### Issue 3: Hollow Circle Intersection

**Problem:** Inhibitor arc line goes all the way to target boundary, but should stop before the hollow circle marker.

**Solution:** Adjust the target boundary point calculation for inhibitor arcs to account for marker radius.

**File:** `src/shypn/netobjs/inhibitor_arc.py`

## Implementation

### Fix 1: Inhibitor Arc Boundary Offset
