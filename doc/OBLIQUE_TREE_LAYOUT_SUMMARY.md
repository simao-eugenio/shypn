# Oblique Tree Layout - Implementation Summary

**Date:** October 12, 2025  
**Status:** ✅ Core Implementation Complete - Visual Tuning Phase

## Overview

Successfully implemented oblique tree layout for biochemical pathways with angle-based positioning. The algorithm applies **locality principle**: each parent node independently spreads its children horizontally using moderate oblique angles.

## Key Principles

### 1. Locality-Based Aperture
- **Each node calculates aperture from its own children count** (not global network)
- Parent spreads children within an angular cone
- Angle per child: 20° (low branching) or 18° (higher branching)

### 2. Oblique Tree Structure
- Each parent positions children at oblique angles (not just vertical drop)
- Creates natural hierarchical flow with visible branching
- Maintains clear vertical hierarchy while showing horizontal spread

### 3. Minimum Spacing Safety
- Algorithm enforces minimum horizontal spacing (150px default) to prevent overlaps
- When angle-based position violates minimum spacing, position is adjusted
- This ensures transitions remain visible (width ~44px)

### 4. Angular Inheritance
- Each child inherits an angle from its parent
- Child then spreads its own children relative to that angle
- Creates compound oblique structure through multiple levels

## Current Implementation

### File: `src/shypn/data/pathway/tree_layout.py`

**Aperture Calculation (Lines 245-270):**
```python
def calculate_base_aperture(self, num_children: int) -> float:
    if num_children <= 1:
        return 0.0
    
    # Adaptive angles based on branching
    if num_children <= 3:
        angle_per_child_deg = 20.0  # Good spacing for low branching
    else:
        angle_per_child_deg = 18.0  # Adequate spacing for higher branching
    
    aperture_deg = angle_per_child_deg * (num_children - 1)
    aperture_rad = math.radians(aperture_deg)
    
    # Cap at 170° to avoid tan() domain violation
    MAX_APERTURE_DEG = 170.0
    safe_aperture_deg = min(aperture_deg, MAX_APERTURE_DEG)
    
    return math.radians(safe_aperture_deg)
```

**Expected Angles:**
- 2 children: 20° aperture (±10° from parent)
- 3 children: 40° aperture (±20° from parent)
- 4 children: 54° aperture (±27° from parent)
- 5 children: 72° aperture (±36° from parent)
- 8 children: 126° aperture (±63° from parent)

**Position Calculation:**
```python
x_offset = vertical_distance × tan(angle)
child.x = parent.x + x_offset
```

With 150px vertical distance:
- 20° angle → ~55px horizontal offset
- 10° angle → ~27px horizontal offset

## Evolution History

### V1: Original (BROKEN)
```python
aperture = 45° × num_children × amplification_factor
```
- **Problem:** Exponential amplification → tan() wrap-around
- **Symptom:** Negative offsets, overlapping transitions ("black bar")

### V2: Locality-Based Spacing (TOO WIDE)
```python
angle_step = min_spacing / vertical_distance  # 150/150 = 57.3°
aperture = angle_step × (num_children - 1)
```
- **Problem:** Mathematically correct but visually extreme
- **Symptom:** 8× wider spread, lost vertical hierarchy

### V3: Fixed Angle (CURRENT)
```python
angle_per_child = 18-20°  # Moderate oblique angles
aperture = angle_per_child × (num_children - 1)
```
- **Result:** Moderate angles creating natural oblique tree
- **Status:** ✅ Working, pending visual validation with real pathways

## Known Behavior

### Minimum Spacing Override
When angle-based positioning produces spacing < 150px, the algorithm adjusts positions to meet minimum spacing. This is **correct behavior** to prevent overlaps, but can distort angles.

**Example:** 3 children with 150px vertical spacing
- **Ideal:** 20° angles → 55px spacing between siblings
- **Actual:** 150px minimum enforced → larger effective angles

**Solution Options:**
1. Accept larger effective angles (ensures no overlaps)
2. Increase vertical spacing (allows smaller angles to meet minimum)
3. Reduce minimum spacing (risky for overlap)

### Pipeline Integration
✅ **Complete** - Tree layout enabled by default in SBML import:

```python
# src/shypn/helpers/sbml_import_panel.py (Line 580)
processor = PathwayPostProcessor(
    spacing=self.spacing,
    use_tree_layout=True  # Enabled by default
)
```

## Testing

### Test Files Created
1. **`test_black_bar_fix.py`** - Validates no overlap with high branching (✅ passing)
2. **`test_tree_layout_pipeline.py`** - Verifies pipeline integration (✅ passing)
3. **`test_oblique_tree.py`** - Demonstrates oblique angle-based positioning (✅ working)
4. **`test_visual_scaling.py`** - Shows scaling behavior with branching factors

### Test Results
- ✅ No overlap with 2-20 children
- ✅ Oblique angles visible in output
- ✅ Hierarchical structure maintained
- ✅ Varying spacing confirms angular positioning (not fixed grid)
- ✅ Each parent spreads children independently (locality)

## User Validation

**User Feedback:** "I have edited this image, it was very easily after our rules applied"
- User manually edited pathway to show desired appearance
- Confirms locality approach is correct
- Visual tuning is final step

**Key Requirement:** "Locality: a node spreads horizontal DOWN its children (not the entire net)"
- ✅ Implemented: Each node independently spreads its own children
- ✅ Not global: No network-wide spreading calculation
- ✅ Oblique: Each level applies horizontal spread with moderate angles

## Next Steps

### Visual Tuning
1. Load real SBML pathways (BIOMD0000000001, etc.)
2. Verify oblique appearance matches user's edited image
3. Fine-tune angles if needed:
   - If too narrow: increase to 22-25° per child
   - If too wide: decrease to 12-15° per child

### Future Enhancements
- [ ] UI toggle for tree vs fixed layout
- [ ] Adjustable angle parameter in preferences
- [ ] Visual feedback showing aperture angles during editing
- [ ] Documentation for biochemists explaining tree layout benefits

## Success Metrics

✅ **Algorithm Complete:**
- Locality-based aperture calculation
- Oblique angle-based positioning
- Minimum spacing safety
- Angular inheritance through levels
- Pipeline integration

🔄 **Visual Validation Pending:**
- Test with real SBML pathways
- Compare with user's edited image
- Fine-tune angles for biochemical aesthetic

## References

- **Evolution docs:** See conversation summary for detailed history
- **Four rules:** Angular inheritance, trigonometric spacing, transition paths, sibling coordination
- **Test files:** `test_*.py` in repository root
- **Implementation:** `src/shypn/data/pathway/tree_layout.py`
