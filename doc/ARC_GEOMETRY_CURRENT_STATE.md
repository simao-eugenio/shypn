# Arc Geometry Current State Analysis

**Date**: 2025-10-10  
**Phase**: 1.1 - Architecture Analysis  
**Status**: ✅ COMPLETE

---

## Executive Summary

**GOOD NEWS**: The arc geometry system already implements perimeter-to-perimeter calculations! The current implementation is more advanced than initially expected.

**Current State**: 
- ✅ Boundary intersection implemented for Place (circle) and Transition (rectangle)
- ✅ Hit detection for both straight and curved arcs
- ✅ Parallel arc offset support
- ⚠️ Some edge cases and optimizations needed

---

## Current Architecture

### File Structure

```
src/shypn/netobjs/
├── arc.py              # Base Arc class (straight arcs)
├── curved_arc.py       # CurvedArc class (Bezier curves)
├── inhibitor_arc.py    # InhibitorArc subclass
├── place.py            # Place class (circles)
├── transition.py       # Transition class (rectangles)
└── petri_net_object.py # Base class
```

### Arc Class Hierarchy

```
PetriNetObject (base)
    └── Arc
        ├── CurvedArc
        └── InhibitorArc
```

---

## Geometry Implementation Analysis

### 1. Perimeter Intersection (`_get_boundary_point`)

**Location**: `src/shypn/netobjs/arc.py` lines 270-335

**Current Implementation**: ✅ **CORRECT**

```python
def _get_boundary_point(self, obj, cx, cy, dx, dy):
    """Calculate where arc intersects object boundary."""
    
    if isinstance(obj, Place):
        # Circle: Point on circle = center + radius * direction
        return (cx + dx * obj.radius, cy + dy * obj.radius)
    
    elif isinstance(obj, Transition):
        # Rectangle: Ray-rectangle intersection
        # Calculate t values for each edge
        t_right = half_w / dx if dx > 0 else float('inf')
        t_left = -half_w / dx if dx < 0 else float('inf')
        t_bottom = half_h / dy if dy > 0 else float('inf')
        t_top = -half_h / dy if dy < 0 else float('inf')
        
        # Find minimum positive t (closest intersection)
        t = min(t_right, t_left, t_bottom, t_top)
        intersect_x = cx + t * dx
        intersect_y = cy + t * dy
        
        # Clamp to bounds
        return (intersect_x, intersect_y)
```

**Assessment**:
- ✅ Mathematically correct ray-intersection
- ✅ Handles both circles and rectangles
- ✅ Uses normalized direction vectors
- ⚠️ Assumes axis-aligned rectangles (transition orientation handled via width/height swap)

---

### 2. Arc Rendering (`render`)

**Location**: `src/shypn/netobjs/arc.py` lines 153-267

**Current Implementation**: ✅ **GOOD**

**Flow**:
1. Get source/target positions (centers)
2. Calculate direction vector
3. Check for parallel arcs, apply offset if needed
4. **Call `_get_boundary_point()` for both ends** ← Uses perimeter intersection!
5. For curved arcs: calculate control point from midpoint + offsets
6. Draw line (straight or Bezier curve)
7. Draw arrowhead at target
8. Draw weight label if > 1

**Key Features**:
- ✅ Uses perimeter intersections (already implemented!)
- ✅ Supports curved arcs with control points
- ✅ Handles parallel arc offsets
- ✅ Zoom-compensated line width
- ✅ Color and glow effects

**Rendering Formula for Curved Arcs**:
```python
# Quadratic Bezier
mid_x = (start_x + end_x) / 2
mid_y = (start_y + end_y) / 2
control_x = mid_x + self.control_offset_x
control_y = mid_y + self.control_offset_y

# Cairo curve_to draws from start to end via control point
cr.curve_to(control_x, control_y, control_x, control_y, end_x, end_y)
```

---

### 3. Hit Detection (`contains_point`)

**Location**: `src/shypn/netobjs/arc.py` lines 440-543

**Current Implementation**: ⚠️ **MOSTLY GOOD, NEEDS IMPROVEMENT**

**For Straight Arcs**:
```python
# Line segment distance formula
dx = tgt_x - src_x
dy = tgt_y - src_y
length_sq = dx * dx + dy * dy

# Project point onto line segment
t = ((x - src_x) * dx + (y - src_y) * dy) / length_sq
t = max(0.0, min(1.0, t))  # Clamp to [0, 1]

# Closest point on segment
closest_x = src_x + t * dx
closest_y = src_y + t * dy

# Distance from point to segment
dist_sq = (x - closest_x) ** 2 + (y - closest_y) ** 2
return dist_sq <= (tolerance * tolerance)
```

**Assessment**:
- ✅ Mathematically correct point-to-segment distance
- ✅ Handles parallel arc offsets
- ✅ Generous tolerance (10px) for easier clicking

**For Curved Arcs**:
```python
# Sample 20 points along Bezier curve
for i in range(21):
    t = i / 20
    # Quadratic Bezier formula
    curve_x = (1-t)^2 * src_x + 2(1-t)t * control_x + t^2 * tgt_x
    curve_y = (1-t)^2 * src_y + 2(1-t)t * control_y + t^2 * tgt_y
    
    # Find minimum distance
    dist_sq = (x - curve_x)^2 + (y - curve_y)^2
    min_dist_sq = min(min_dist_sq, dist_sq)

return min_dist_sq <= tolerance^2
```

**Assessment**:
- ✅ Works correctly via sampling
- ⚠️ Sampling approach (20 points) may miss narrow curves
- ⚠️ Could be optimized with analytic Bezier distance

---

### 4. Parallel Arc Handling

**Detection**: Manager detects arcs with same source/target (or reversed)

**Offset Calculation**:
```python
# Perpendicular offset distance based on arc index
offset_distance = arc_index * PARALLEL_ARC_SPACING

# Apply offset perpendicular to arc direction
perp_x = -dy / length  # 90° rotation
perp_y = dx / length

src_x += perp_x * offset_distance
tgt_x += perp_x * offset_distance
```

**Assessment**:
- ✅ Prevents arc overlap
- ✅ Applied consistently in render and hit detection
- ⚠️ Offset applied to centers, not to boundary points

---

## Curved Arc Implementation

**Location**: `src/shypn/netobjs/curved_arc.py`

Let me check this file...
