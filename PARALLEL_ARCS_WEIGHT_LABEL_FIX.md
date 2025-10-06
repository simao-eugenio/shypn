# Parallel Arcs Weight Label Positioning - Fixed

## Problem

When rendering weight labels on parallel curved arcs (opposite directions between same nodes), the text appeared **in the void between the two arcs** instead of on the outer side of each curve.

### Visual Problem

**Before (Wrong):**
```
           [3]        [5]
            ↓          ↓
P1 ───╮          ╭─── T1
       ╰────────╯
        Both texts in the middle gap!
```

**Why This Happened:**
1. Both arcs calculated perpendicular direction from their tangent
2. Both used 90° counterclockwise rotation
3. For mirror-symmetric curves, this put text on **inner sides**
4. Result: Both labels ended up in the space between curves

## Solution

Added **curve direction detection** to ensure text goes on the **outer side** of each curve.

### Algorithm

1. **Calculate tangent perpendicular** (as before)
2. **Determine control point side** relative to straight line
3. **If curve bends "inward", flip perpendicular** direction
4. **Result**: Text always on outer side

### Mathematical Details

#### Step 1: Calculate where control point is

```python
# Straight line midpoint
mid_line_x = (x1 + x2) / 2
mid_line_y = (y1 + y2) / 2

# Control point offset from midpoint
cp_offset_x = cp_x - mid_line_x
cp_offset_y = cp_y - mid_line_y
```

#### Step 2: Calculate perpendicular to straight line

```python
dx = x2 - x1
dy = y2 - y1
line_length = sqrt(dx² + dy²)

# Perpendicular to line (normalized)
line_perp_x = -dy / line_length
line_perp_y = dx / line_length
```

#### Step 3: Determine which side (dot product)

```python
# Dot product tells us which side control point is on
side = cp_offset_x * line_perp_x + cp_offset_y * line_perp_y

if side > 0:
    # Control point on positive side (curve bends outward)
    # Use perpendicular as calculated
elif side < 0:
    # Control point on negative side (curve bends inward)
    # Flip perpendicular to point outward
    perp_x = -perp_x
    perp_y = -perp_y
```

### Code Implementation

```python
def _render_weight_curved(self, cr, x1, y1, x2, y2, cp_x, cp_y, 
                         curve_offset, zoom):
    # ... calculate mid_x, mid_y on bezier curve ...
    # ... calculate tangent_x, tangent_y at midpoint ...
    
    # Initial perpendicular (rotate tangent 90° CCW)
    perp_x = -tangent_y
    perp_y = tangent_x
    
    # Determine which side to place text based on curve direction
    if curve_offset is not None:
        dx = x2 - x1
        dy = y2 - y1
        line_length = sqrt(dx*dx + dy*dy)
        
        if line_length > 1e-6:
            # Perpendicular to straight line
            line_perp_x = -dy / line_length
            line_perp_y = dx / line_length
            
            # Check which side control point is on
            mid_line_x = (x1 + x2) / 2
            mid_line_y = (y1 + y2) / 2
            cp_offset_x = cp_x - mid_line_x
            cp_offset_y = cp_y - mid_line_y
            
            # Dot product determines side
            side = cp_offset_x * line_perp_x + cp_offset_y * line_perp_y
            
            # If curve bends inward (negative side), flip perpendicular
            if side < 0:
                perp_x = -perp_x
                perp_y = -perp_y
    
    # Position text using corrected perpendicular
    text_x = mid_x + perp_x * offset - extents.width / 2
    text_y = mid_y + perp_y * offset + extents.height / 2
```

## Visual Result

### After (Correct)

```
P1 ───╮ [3]      [5] ╭─── T1
       ╰────────────╯
    Each text on outer side!
```

### Detailed Example

**Parallel Arc Pair:**
```
Arc 1: P1 → T1 (curves upward)
Arc 2: T1 → P1 (curves downward, mirror of Arc 1)

Arc 1:
- Control point ABOVE straight line (positive side)
- Perpendicular points up ✓
- Text appears ABOVE curve [3]

Arc 2:
- Control point BELOW straight line (negative side)
- Perpendicular initially points up (wrong!)
- FLIP IT! Now points down ✓
- Text appears BELOW curve [5]

Result:
  [3] ← Arc 1 text
P1 ╭─╮ T1
   ╰─╯
  [5] ← Arc 2 text
```

## Files Modified

1. **`src/shypn/netobjs/curved_arc.py`**
   - Updated `render()` to pass `curve_offset` to weight rendering
   - Modified `_render_weight_curved()` signature to accept `curve_offset`
   - Added curve direction detection logic

2. **`src/shypn/netobjs/curved_inhibitor_arc.py`**
   - Same modifications as `curved_arc.py`

## Key Changes

### Signature Change

**Before:**
```python
def _render_weight_curved(self, cr, x1, y1, x2, y2, cp_x, cp_y, zoom):
```

**After:**
```python
def _render_weight_curved(self, cr, x1, y1, x2, y2, cp_x, cp_y, 
                         curve_offset, zoom):
```

### Render Call Change

**Before:**
```python
if self.weight > 1:
    self._render_weight_curved(cr, start_x, start_y, end_x, end_y, 
                              cp_x, cp_y, zoom)
```

**After:**
```python
if self.weight > 1:
    # Calculate offset for parallel arcs
    offset_distance = None
    if hasattr(self, '_manager') and self._manager:
        parallels = self._manager.detect_parallel_arcs(self)
        if parallels:
            offset_distance = self._manager.calculate_arc_offset(self, parallels)
    
    self._render_weight_curved(cr, start_x, start_y, end_x, end_y, 
                              cp_x, cp_y, offset_distance, zoom)
```

## Edge Cases Handled

1. **Single curved arc** (no parallel):
   - `curve_offset = None`
   - Uses default perpendicular direction
   - Text positioned naturally

2. **Degenerate curve** (control point on line):
   - Falls back to straight line rendering
   - No divide-by-zero errors

3. **Nearly parallel lines** (small angle):
   - Robust dot product calculation
   - Handles numerical precision gracefully

## Testing Scenarios

### Test 1: Horizontal Parallel Arcs
```
P1 (left) ⟷ T1 (right)

Expected:
  [3] ← Above
P1 ═══ T1
  [5] ← Below
```

### Test 2: Vertical Parallel Arcs
```
P1 (top)
  ↕
T1 (bottom)

Expected:
P1 ║[3]    [5]║ T1
   ════════════
```

### Test 3: Diagonal Parallel Arcs
```
P1 (top-left) ⟷ T1 (bottom-right)

Expected:
P1 [3]          T1
    ╲          ╱
     ╲        ╱ [5]
      ╲      ╱
```

## Benefits

✅ **Readability**: Each arc's weight clearly associated with its curve  
✅ **No Overlap**: Labels don't collide in middle space  
✅ **Visual Clarity**: Text follows natural outer edge of curves  
✅ **Consistent**: Works for any arc orientation  
✅ **Robust**: Handles edge cases gracefully

## Technical Quality

- **Mathematical Correctness**: Uses dot product for side detection
- **Performance**: Efficient calculation (no iteration)
- **Maintainability**: Clear logic with comments
- **Robustness**: Handles degenerate cases
- **Consistency**: Same fix applied to both arc types

## Related Issues Fixed

This completes the curved arc refinement trilogy:

1. ✅ **Context menu hit detection** - Fixed `contains_point()`
2. ✅ **Weight label positioning** - Fixed `_render_weight_curved()` basic
3. ✅ **Parallel arcs labels** - Fixed outer side detection (this fix)

All three use consistent bezier mathematics.

## Summary

Weight labels on parallel curved arcs now appear on the **outer side** of each curve, preventing labels from clustering in the empty space between arcs. This is achieved by detecting which side the control point is on relative to the straight line, and flipping the perpendicular direction if needed to ensure outward placement.

**Status**: ✅ **FIXED - Ready for testing**
