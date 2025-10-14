# Hierarchical Layout Fix - Coordinate Bounds

**Date:** October 14, 2025
**Issue:** Stretched and negative coordinates in hierarchical layout
**Status:** ✅ Fixed

## Problem Description

### Symptoms
When importing pathways with many species in a single layer, coordinates became stretched to extreme values:

```
✅ Normal:  P1 at (188.91, 400.0)           - BIOMD0000000001
⚠️  Stretched: P1 at (253.02, 250.0)       - BIOMD0000000002  
❌ BROKEN: P1 at (-2988.74, 4705.52)        - BIOMD0000000061
```

**Result:** Species positioned at negative coordinates or thousands of pixels away, making them invisible or requiring extreme zoom.

### Root Cause

**File:** `src/shypn/data/pathway/hierarchical_layout.py`
**Method:** `_position_layers()`

The algorithm calculated positions using unlimited spacing:

```python
# OLD CODE - NO BOUNDS CHECKING
total_width = (num_species - 1) * self.horizontal_spacing
start_x = canvas_center_x - total_width / 2

for i, species_id in enumerate(layer_species):
    x = start_x + i * self.horizontal_spacing  # Can be negative!
    positions[species_id] = (x, y)
```

**Problem:**
- If a layer has **50 species** with **100px spacing**:
  - `total_width = 49 * 100 = 4900px`
  - `start_x = 400 - 2450 = -2050px` ⚠️ **NEGATIVE!**
  - Species positioned from `-2050px` to `+2850px`

## Solution

### Fix 1: Maximum Width Constraint

Added `max_canvas_width` limit to prevent unbounded spreading:

```python
# NEW CODE - BOUNDED LAYOUT
canvas_center_x = 400.0
max_canvas_width = 1200.0  # Maximum usable width

# Calculate ideal spacing, but limit to prevent stretching
ideal_spacing = self.horizontal_spacing
total_width = (num_species - 1) * ideal_spacing

# If layer is too wide, scale down spacing to fit
if total_width > max_canvas_width:
    actual_spacing = max_canvas_width / (num_species - 1)
    total_width = max_canvas_width
    self.logger.debug(f"Layer {layer_index} has {num_species} species, "
                    f"reducing spacing to {actual_spacing:.1f}px to fit")
else:
    actual_spacing = ideal_spacing

start_x = canvas_center_x - total_width / 2
```

**Benefits:**
- Large layers automatically compress to fit within 1200px width
- Spacing scales down gracefully (e.g., 100px → 25px for 50 species)
- All coordinates remain within reasonable canvas bounds

### Fix 2: Coordinate Normalization

Added `_normalize_coordinates()` to guarantee positive coordinates:

```python
def _normalize_coordinates(self, positions: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
    """Ensure all coordinates are positive by shifting if needed."""
    if not positions:
        return positions
    
    # Find minimum coordinates
    min_x = min(x for x, y in positions.values())
    min_y = min(y for x, y in positions.values())
    
    # If any coordinate is negative, shift everything
    offset_x = max(0, 50 - min_x)  # At least 50px margin
    offset_y = max(0, 50 - min_y)
    
    if offset_x > 0 or offset_y > 0:
        self.logger.info(f"Normalizing coordinates: offset=({offset_x:.1f}, {offset_y:.1f})")
        positions = {
            element_id: (x + offset_x, y + offset_y)
            for element_id, (x, y) in positions.items()
        }
    
    return positions
```

**Benefits:**
- **Safety net:** Even if bounds checking fails, normalization fixes it
- **Consistent margins:** Always leaves 50px minimum margin
- **Logged:** Shows when normalization occurs for debugging

## Changes Summary

### Modified File
**`src/shypn/data/pathway/hierarchical_layout.py`**

1. **`_position_layers()` method** (+10 lines)
   - Added `max_canvas_width = 1200.0` constraint
   - Calculate `actual_spacing` based on layer width
   - Scale down spacing when layer exceeds max width
   - Added debug logging for spacing adjustments

2. **`calculate_hierarchical_layout()` method** (+2 lines)
   - Added Step 5: Call `_normalize_coordinates()`
   - Enhanced completion logging

3. **New method: `_normalize_coordinates()`** (+24 lines)
   - Find minimum X and Y coordinates
   - Calculate offsets to ensure 50px margins
   - Apply offsets to all positions
   - Log normalization when applied

### Total Changes
- **Lines added:** ~36
- **Lines modified:** ~12
- **New methods:** 1 (`_normalize_coordinates`)

## Testing

### Test Cases

| Model ID | Species | Before | After | Status |
|----------|---------|--------|-------|--------|
| BIOMD0000000001 | 12 | ✅ Good | ✅ Good | No change needed |
| BIOMD0000000002 | 13 | ⚠️ Stretched | ✅ Fixed | Bounded layout |
| BIOMD0000000061 | 25 | ❌ Negative | ✅ Fixed | Normalized |
| BIOMD0000000064 | 26 | ⚠️ Stretched | ✅ Fixed | Bounded + normalized |
| BIOMD0000000428 | 31 | ⚠️ Stretched | ✅ Fixed | Bounded + normalized |

### Expected Results

**Small pathways (< 10 species per layer):**
- No change - spacing remains 100px as configured
- Centered around 400px canvas center

**Medium pathways (10-20 species per layer):**
- Spacing may reduce slightly to fit within 1200px
- All species visible and well-distributed

**Large pathways (20+ species per layer):**
- Spacing scales down proportionally (e.g., 100px → 40px)
- Layer compressed to fit within 1200px width
- Normalization ensures 50px minimum margins

## Coordinate Guarantees

After these fixes, hierarchical layout guarantees:

1. ✅ **All coordinates positive:** Minimum 50px margins
2. ✅ **Bounded width:** Maximum 1200px spread per layer
3. ✅ **Adaptive spacing:** Scales down for large layers
4. ✅ **Centered layout:** Balanced around canvas center
5. ✅ **No infinite stretch:** Hard limits prevent extreme values

## Related Changes

### CrossFetch Removal
This fix is part of the larger effort to:
- ✅ Remove CrossFetch coordinate enrichment (intractable)
- ✅ Make hierarchical layout the default for ALL imports
- ✅ Ensure consistent, beautiful layouts across all pathways

**See:** `doc/CROSSFETCH_REMOVAL_DECISION.md`

### Hierarchical Layout Priority
Changed layout strategy priority in `pathway_postprocessor.py`:

```
OLD:
1. Cross-reference (KEGG/Reactome) - BEST
2. Hierarchical (top-to-bottom) - GOOD
3. Force-directed (networkx) - OK
4. Grid - BASIC

NEW:
1. Hierarchical (top-to-bottom) - ALWAYS ✓
2. Force-directed (networkx) - Fallback
3. Grid - Last resort
```

## Performance Impact

- **Negligible:** Normalization adds O(n) scan (milliseconds)
- **Better:** Prevents extreme coordinates that slow rendering
- **Cleaner:** Consistent bounds improve canvas performance

## Future Enhancements

Possible improvements for very large pathways:

1. **Multi-column layout:** Split wide layers into multiple columns
2. **Smart grouping:** Group related species within layers
3. **Hierarchical clustering:** Use pathway annotations to organize layout
4. **Interactive folding:** Collapse/expand pathway sections

## Conclusion

The hierarchical layout now produces **bounded, positive coordinates** for all pathway sizes. This ensures:

✅ All pathways import correctly without stretching  
✅ Consistent visual appearance across different models  
✅ Better user experience with predictable layouts  
✅ No more negative coordinates or invisible species  

**Status:** Ready for production use with all pathway sources (SBML, KEGG, etc.)
