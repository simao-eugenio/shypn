# Parallel Arcs: Legacy vs Current Implementation

## Legacy Approach (shypnpy)

### Core Algorithm: `compute_parallel_arc()`
**Location:** `legacy/shypnpy/utils/layout.py`

**Strategy:**
1. **Detection**: Find "opposite" arcs (same endpoints reversed: A→B and B→A)
2. **Offset Calculation**: 
   - Calculate perpendicular offset (`W/2`) from centerline
   - Offset distance adaptive: `min(30, max(8, base_dist * 0.15))`
3. **Bezier Curves**: Generate TWO bezier specs (one for each arc)
   - Start/end points: Intersect offset line with shape boundaries
   - Control point: Midpoint + perpendicular offset * curve factor (0.25)
4. **Mapping**: Assign each curve to correct arc using cross product (determines which side)
5. **Caching**: Store computed curves with key `(src_id, tgt_id, positions, offset_w)`

### Key Features:
- **Perimeter-accurate**: Start/end calculated by ray-circle/ray-rect intersection with offset
- **Symmetric curves**: Both arcs curve away from centerline by equal amounts
- **Renders as bezier**: Uses `ctx.curve_to(ctrl_x, ctrl_y, ctrl_x, ctrl_y, end_x, end_y)` (quadratic as cubic)
- **Cache invalidation**: On arc deletion, weight change, or position change

### Code Snippet (Legacy):
```python
def compute_parallel_arc(src_center, src_shape, dst_center, dst_shape, W, curve=0.2):
    """Returns TWO bezier curves for parallel arcs.
    
    W = total separation width
    curve = curvature factor (default 0.2)
    
    Returns: [
        {'start': (x,y), 'end': (x,y), 'ctrl': (x,y)},  # First arc
        {'start': (x,y), 'end': (x,y), 'ctrl': (x,y)}   # Second arc
    ]
    """
    # 1. Calculate direction vector u and perpendicular v
    # 2. For each offset (+W/2, -W/2):
    #    - Find start: intersect(source_shape, direction=u, offset=±W/2*v)
    #    - Find end: intersect(target_shape, direction=-u, offset=±W/2*v)
    #    - Control: midpoint + curve * distance * v
```

### Renderer Integration:
```python
# In renderer.py draw_arc():
if opposite_arc and compute_parallel_arc is not None:
    arcs = compute_parallel_arc(src_center, src_shape, dst_center, dst_shape, offset_w, curve=0.25)
    
    # Map curves to arcs using cross product
    for spec, mapped_obj in zip(arcs, [arc, opposite_arc]):
        if mapped_obj == arc:  # Only render current arc's curve
            ctx.move_to(spec['start'][0], spec['start'][1])
            ctrl = spec['ctrl']
            ctx.curve_to(ctrl[0], ctrl[1], ctrl[0], ctrl[1], 
                        spec['end'][0], spec['end'][1])
            ctx.stroke()
```

---

## Current Approach (Feature Branch)

### Core Algorithm: Manager-based Detection
**Location:** `src/shypn/data/model_canvas_manager.py`

**Strategy:**
1. **Detection**: `detect_parallel_arcs()` finds arcs with same source/target (any direction)
2. **Offset Calculation**: 
   - Fixed offsets: ±15px for 2 arcs, ±10/±30px for 3+ arcs
   - Stored in arc property during transformation
3. **Curved Arc Class**: `CurvedArc` calculates own control point
   - `_calculate_curve_control_point(offset=distance)`
   - Control point = midpoint + perpendicular * offset
4. **Individual Rendering**: Each arc renders independently
5. **Transformation-based**: Context menu converts Arc ↔ CurvedArc

### Key Features:
- **Class-based**: `Arc`, `CurvedArc`, `InhibitorArc`, `CurvedInhibitorArc`
- **Manager reference**: Arcs store `_manager` for parallel detection
- **Transform utilities**: `arc_transform.py` handles conversions
- **Simplified**: No complex geometric calculations, target crops curve naturally

### Code Snippet (Current):
```python
# In CurvedArc.render():
def render(self, cr, transform=None, zoom=1.0):
    # Detect parallels via manager
    offset_distance = None
    if hasattr(self, '_manager') and self._manager:
        parallels = self._manager.detect_parallel_arcs(self)
        if parallels:
            offset_distance = self._manager.calculate_arc_offset(self, parallels)
    
    # Calculate control point with offset
    control_point = self._calculate_curve_control_point(offset=offset_distance)
    cp_x, cp_y = control_point
    
    # Draw curve to target center (let target crop naturally)
    cr.move_to(start_world_x, start_world_y)
    cr.curve_to(cp_x, cp_y, cp_x, cp_y, tgt_world_x, tgt_world_y)
    cr.stroke()
```

---

## Comparison

| Aspect | Legacy | Current |
|--------|--------|---------|
| **Detection** | Per-render scan | Manager-based query |
| **Offset** | Dynamic (8-30px) | Fixed (±15px, ±10/±30px) |
| **Endpoint Calc** | Ray-shape intersection | Simple boundary point |
| **Curve Calc** | `compute_parallel_arc()` | `_calculate_curve_control_point()` |
| **Rendering** | Bezier to exact boundary | Bezier to center (cropped) |
| **Caching** | Geometry cache | No cache |
| **Arc Types** | Property-based | Class-based inheritance |
| **Transformation** | N/A | Context menu system |

---

## Issues in Current Implementation

### Problem: "Parallel opposite arcs lose references and are not transformable"

**Root Cause Analysis:**
1. ✅ **Manager Reference**: Fixed - `ensure_arc_references()` added
2. ✅ **Transform Callback**: Fixed - `on_changed` copied in `replace_arc()`
3. ⚠️ **Parallel Detection**: Current approach may not match legacy behavior

### Legacy Detection Logic:
```python
# Finds OPPOSITE arc (reversed endpoints)
for other_arc in model.arcs:
    if other_arc.source_id == arc.target_id and other_arc.target_id == arc.source_id:
        opposite_arc = other_arc  # Found opposite
```

### Current Detection Logic:
```python
# Finds ALL parallel arcs (same source/target pair, any direction)
def detect_parallel_arcs(self, arc):
    parallels = []
    for other in self.arcs:
        if other == arc:
            continue
        same_direction = (other.source == arc.source and other.target == arc.target)
        opposite_direction = (other.source == arc.target and other.target == arc.source)
        if same_direction or opposite_direction:
            parallels.append(other)
    return parallels
```

**Key Difference:**
- Legacy: Only considers ONE opposite arc
- Current: Considers ALL arcs between same objects (handles 3+ arcs)

---

## Recommendations

### 1. Adopt Legacy's Perimeter-Accurate Endpoints ✅ PARTIALLY DONE
- **Status**: Simplified approach - draw to center, let target crop
- **Issue**: Works but less precise than legacy
- **Solution**: Keep current approach (simpler, works well enough)

### 2. Improve Parallel Detection ✅ DONE
- **Status**: Manager-based detection working
- **Issue**: References lost after transformation
- **Solution**: Added `ensure_arc_references()` and fixed `replace_arc()`

### 3. Cache Geometry Calculations ⏳ TODO (Optional)
- **Status**: No caching currently
- **Impact**: Recalculates control points every frame
- **Solution**: Add cache similar to legacy (if performance issue)

### 4. Inhibitor Arc Positioning ✅ DONE
- **Status**: Fixed - hollow circle entirely outside, edge touches boundary
- **Legacy**: Same approach
- **Current**: Matches legacy behavior

### 5. Context Menu Validation ✅ DONE
- **Status**: Added direction validation for inhibitor arcs
- **Rule**: Inhibitor arcs only Place → Transition
- **Error**: Shows dialog if invalid transformation attempted

---

## Summary

The **legacy approach** was more geometrically precise with ray-shape intersection calculations and explicit caching. The **current approach** is simpler and more object-oriented with class-based arc types and transformation system.

**Key insight from legacy**: The `compute_parallel_arc()` function **returns two curves** - one for each arc in an opposite pair. The renderer then selects which curve to draw based on which arc is being rendered.

**Current implementation simplification**: Each curved arc calculates its own control point with an offset, and relies on the target object to naturally crop the curve. This works well but is less precise than the legacy geometric calculations.

**Fix applied**: Added `ensure_arc_references()` to maintain `_manager` and `on_changed` callbacks, ensuring all arcs remain transformable even in parallel/opposite configurations.
