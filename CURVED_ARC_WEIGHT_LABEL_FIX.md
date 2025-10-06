# Curved Arc Weight Label Positioning - Fixed

## Problem

When rendering weight labels (numbers) on curved arcs with `weight > 1`, the text position was calculated using straight-line midpoint logic, which doesn't work for bezier curves.

**Before:**
- Weight label positioned at midpoint between start and end points
- Perpendicular offset calculated from straight line
- Result: Text not aligned with curved arc path

## Solution

Implemented `_render_weight_curved()` method in both `CurvedArc` and `CurvedInhibitorArc` that:

1. **Calculates true midpoint on bezier curve** at t=0.5
2. **Computes tangent vector** at that point  
3. **Positions text perpendicular** to the actual curve

## Mathematical Details

### Bezier Curve Midpoint (t=0.5)

Quadratic bezier formula:
```
B(t) = (1-t)²*P₀ + 2(1-t)t*P₁ + t²*P₂

At t=0.5:
mid_x = 0.25*x₁ + 0.5*cp_x + 0.25*x₂
mid_y = 0.25*y₁ + 0.5*cp_y + 0.25*y₂
```

### Tangent Vector at Midpoint

Derivative of bezier:
```
B'(t) = 2(1-t)(P₁-P₀) + 2t(P₂-P₁)

At t=0.5:
tangent_x = (cp_x - x₁) + (x₂ - cp_x) = x₂ - x₁ + 2(cp_x - mid_x)
tangent_y = (cp_y - y₁) + (y₂ - cp_y) = y₂ - y₁ + 2(cp_y - mid_y)
```

### Perpendicular Direction

Rotate tangent 90° counterclockwise:
```
perp_x = -tangent_y
perp_y = tangent_x
```

## Implementation

### CurvedArc._render_weight_curved()

```python
def _render_weight_curved(self, cr, x1, y1, x2, y2, cp_x, cp_y, zoom):
    # Calculate midpoint on bezier curve at t=0.5
    t = 0.5
    b0 = (1 - t) * (1 - t)      # 0.25
    b1 = 2 * (1 - t) * t        # 0.5
    b2 = t * t                  # 0.25
    
    mid_x = b0 * x1 + b1 * cp_x + b2 * x2
    mid_y = b0 * y1 + b1 * cp_y + b2 * y2
    
    # Calculate tangent at midpoint
    tangent_x = 2 * (1 - t) * (cp_x - x1) + 2 * t * (x2 - cp_x)
    tangent_y = 2 * (1 - t) * (cp_y - y1) + 2 * t * (y2 - cp_y)
    
    # Normalize tangent
    tangent_length = sqrt(tangent_x² + tangent_y²)
    tangent_x /= tangent_length
    tangent_y /= tangent_length
    
    # Perpendicular direction (rotate 90° CCW)
    perp_x = -tangent_y
    perp_y = tangent_x
    
    # Position text perpendicular to curve
    offset = 11 / zoom
    text_x = mid_x + perp_x * offset - text_width / 2
    text_y = mid_y + perp_y * offset + text_height / 2
    
    # Draw background + text
    ...
```

### Modified Render Call

**Before:**
```python
if self.weight > 1:
    self._render_weight(cr, start_x, start_y, end_x, end_y, zoom)
```

**After:**
```python
if self.weight > 1:
    self._render_weight_curved(cr, start_x, start_y, end_x, end_y, 
                              cp_x, cp_y, zoom)
```

## Visual Comparison

### Straight Arc (Original - Correct)
```
P1 ----[5]----> T1
       ↑
   Midpoint of line
```

### Curved Arc (Before - Wrong)
```
P1 ╭─────╮ T1
    [5]     ← Text at straight-line midpoint (off curve!)
      ↑
   Not on curve
```

### Curved Arc (After - Fixed)
```
P1 ╭──[5]─╮ T1
      ↑
   Text on curve, perpendicular to tangent
```

## Files Modified

1. **`src/shypn/netobjs/curved_arc.py`**
   - Added `_render_weight_curved()` method
   - Updated render() to call new method when weight > 1

2. **`src/shypn/netobjs/curved_inhibitor_arc.py`**
   - Added `_render_weight_curved()` method (same implementation)
   - Updated render() to call new method when weight > 1

## Testing

### Manual Test
1. Create model with curved arc
2. Set weight > 1 (e.g., weight=5)
3. Verify text appears:
   - On the curve (not off to the side)
   - Perpendicular to curve direction
   - At midpoint of arc

### Test Cases

**Case 1: Horizontal Curved Arc**
```
P1 (left) ╭─[5]─╮ T1 (right)
```
Text should be above or below the curve peak.

**Case 2: Vertical Curved Arc**
```
P1 (top)
  │╲
  │ [5]
  │  ╲
T1 (bottom)
```
Text should be to the left or right of curve peak.

**Case 3: Diagonal Curved Arc**
```
P1 (top-left)
    ╲
     [5]
      ╲
    T1 (bottom-right)
```
Text perpendicular to curve tangent at midpoint.

## Edge Cases Handled

1. **Degenerate curve** (control point on line):
   - Falls back to straight line weight rendering
   - Check: `tangent_length < 1e-6`

2. **Zoom compensation**:
   - Font size: `12 / zoom`
   - Offset: `11 / zoom`
   - Padding: `2 / zoom`
   - Ensures consistent screen-space appearance

3. **Legacy styling preserved**:
   - Bold Arial 12pt
   - White semi-transparent background (0.8 alpha)
   - Black text
   - 2px padding

## Benefits

✅ **Visual Accuracy**: Text follows curve path  
✅ **Readability**: Perpendicular to tangent (natural reading angle)  
✅ **Consistency**: Same style as straight arcs  
✅ **Robustness**: Handles edge cases gracefully  
✅ **Zoom-Invariant**: Text maintains size and position at any zoom level

## Related Issues

- Fixed context menu hit detection for curved arcs (previous issue)
- Both issues required accurate bezier curve calculations
- Now rendering and hit detection are mathematically consistent

## Summary

Curved arcs with `weight > 1` now correctly position the weight label on the actual bezier curve path, perpendicular to the curve's tangent at the midpoint. This provides natural, readable text placement that follows the visual arc path.
