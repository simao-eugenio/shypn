# Tree Layout "Black Bar" Issue - Root Cause Analysis

## Issue Description

**Reported Problem:** "transition siblings at 100% looks like a black bar"

**User's Concern:** "our four rules are not applied on rendering, visually"

## Root Cause: Tangent Function Wrap-Around

### Mathematical Problem

The tree layout uses **trigonometric positioning** (Rule 2):
```python
x_offset = vertical_distance × tan(angle)
```

**But tan() has singularities at ±90°:**
- tan(±90°) = ±∞ (undefined/infinity)
- tan(angles > 90°) wraps around and becomes negative
- tan(angles < -90°) wraps around and becomes positive

### Current Aperture Calculation

```python
def calculate_base_aperture(num_children: int) -> float:
    base_aperture_deg = 45.0  # Base angle
    scaling_factor = num_children * 1.0  # Direct proportionality
    aperture_angle = math.radians(base_aperture_deg * scaling_factor)
    return aperture_angle
```

**Problem Cases:**
- **5 children**: 45° × 5 = 225° aperture → angles from -112.5° to +112.5°
  - tan(-112.5°) ≈ +2.41 (wraps around!)
  - tan(+112.5°) ≈ -2.41 (wraps around!)
  - Result: **negative spacing** between siblings → overlap
  
- **10 children**: 45° × 10 = 450° aperture → complete chaos
  - Angles exceed ±180°
  - Multiple wraps, positions scrambled
  - Result: **random overlapping** positions

### Evidence from Testing

```
5-way branching (aperture 225.0°):
  Angles: ['-112.5°', '-56.2°', '0.0°', '56.2°', '112.5°']
  Positions: ['362.1px', '-224.5px', '0.0px', '224.5px', '-362.1px']
  Minimum spacing: -586.6px  ← NEGATIVE SPACING!
  ❌ OVERLAP! (min spacing -586.6px < width 44.0px)
```

The positions are **out of order** (362, -224, 0, 224, -362) because tan() wrapped around.

## Why This Wasn't Caught in Testing

### Test Files Used Small Branching Factors

All test files used **2-3 way branching**, which stays within safe range:
- 2-way: 45° × 2 = 90° aperture → angles -45° to +45° ✅
- 3-way: 45° × 3 = 135° aperture → angles -67.5° to +67.5° ✅

Both are within tan()'s safe range (±90°).

### Real Pathways Have More Children

SBML pathways from BioModels can have:
- Complex reaction networks
- Hub metabolites (e.g., ATP, ADP) with 10+ connections
- Branching factors of 5-20+ children per node

This is where the wrap-around manifests as the "black bar" effect.

## Visual Manifestation

### Normal Case (3 siblings, 135° aperture):
```
    [S1]         [S2]         [S3]
     |            |            |
     ↓            ↓            ↓
  [R1: 44px]  [R2: 44px]  [R3: 44px]
  
  Spacing: 362px between each
  Result: ✅ Clean, separated transitions
```

### Bug Case (5 siblings, 225° aperture with wrap):
```
  [S2]  [S4]                    [S1]    [S3]    [S5]
   |     |                       |       |       |
   ↓     ↓                       ↓       ↓       ↓
[R2][R4]                    [R1][R3][R5]
^^^^^^^^^                   ^^^^^^^^^^^^^
CLUMP                       CLUMP

Positions scrambled due to tan() wrap
Result: ❌ Overlapping "black bars" of transitions
```

The transitions appear as **solid black bars** because:
1. Multiple 44px-wide rectangles overlap
2. All filled with black (transition default color)
3. No gaps between them due to negative/wrong spacing
4. Human eye sees continuous black bar, not individual rectangles

## The Four Rules ARE Calculated Correctly

**Important:** The four rules are implemented correctly:
- ✅ Rule 1: Angular inheritance (children within parent's cone)
- ✅ Rule 2: Trigonometric spacing (x = distance × tan(angle))
- ✅ Rule 3: Transition angular paths (midpoints)
- ✅ Rule 4: Sibling coordination (max branching)

**The problem is NOT the rules, but the APERTURE LIMITS:**
- Rules calculate angles correctly
- **But angles exceed tan()'s domain (±90°)**
- This causes wrap-around, breaking positions

**Analogy:** Having a perfect map (the rules) but trying to navigate beyond the map's edge (tan() domain).

## Solution: Cap Maximum Aperture Angle

### Mathematical Constraint

**Safe aperture range:** aperture ∈ [0°, 170°]

This ensures:
- All child angles stay within (-85°, +85°)
- tan() stays well-defined and monotonic
- No wrap-around issues

### Proposed Fix

```python
def calculate_base_aperture(num_children: int, min_spacing: float = 150.0) -> float:
    """Calculate aperture angle for a node with children.
    
    Args:
        num_children: Number of children nodes
        min_spacing: Minimum horizontal spacing between siblings (default: 150px)
        
    Returns:
        Aperture angle in radians (capped at 170° to avoid tan() wrap)
    """
    base_aperture_deg = 45.0
    scaling_factor = num_children * 1.0
    
    # Calculate desired aperture
    desired_aperture_deg = base_aperture_deg * scaling_factor
    
    # Cap at 170° to keep all angles within tan() domain
    # This ensures angles stay within (-85°, +85°)
    MAX_APERTURE_DEG = 170.0
    capped_aperture_deg = min(desired_aperture_deg, MAX_APERTURE_DEG)
    
    aperture_angle = math.radians(capped_aperture_deg)
    return aperture_angle
```

### Alternative: Use Minimum Spacing Enforcement

For very high branching (>8 children), we could switch to **linear spacing**:

```python
def calculate_base_aperture(num_children: int, min_spacing: float = 150.0, 
                           vertical_distance: float = 150.0) -> float:
    """Calculate aperture angle with spacing guarantees."""
    
    # Calculate aperture from branching
    base_aperture_deg = 45.0
    scaling_factor = num_children * 1.0
    desired_aperture_deg = base_aperture_deg * scaling_factor
    
    # Cap at 170° for tan() domain safety
    MAX_APERTURE_DEG = 170.0
    capped_aperture_deg = min(desired_aperture_deg, MAX_APERTURE_DEG)
    
    # For high branching, ensure minimum spacing
    if num_children > 8:
        # Calculate required aperture for minimum spacing
        # spacing = vertical_distance × tan(half_aperture / (n-1))
        # Solve for aperture given minimum spacing
        required_angle_step = math.atan(min_spacing / vertical_distance)
        required_aperture_rad = required_angle_step * (num_children - 1)
        required_aperture_deg = math.degrees(required_aperture_rad)
        
        # Use larger of scaled or spacing-required aperture
        final_aperture_deg = max(capped_aperture_deg, required_aperture_deg)
        
        # Still cap at max safe angle
        final_aperture_deg = min(final_aperture_deg, MAX_APERTURE_DEG)
    else:
        final_aperture_deg = capped_aperture_deg
    
    return math.radians(final_aperture_deg)
```

## Implementation Plan

### Priority 1: Quick Fix (Cap Aperture)
- Modify `calculate_base_aperture()` in `tree_layout.py`
- Add `MAX_APERTURE_DEG = 170.0` constant
- Cap calculated aperture: `min(calculated, MAX_APERTURE_DEG)`
- Add comment explaining tan() domain constraint

### Priority 2: Enhanced Testing
- Add test for high branching (5, 10, 20 children)
- Verify no negative spacings
- Verify minimum spacing maintained
- Test with real SBML pathways with hub metabolites

### Priority 3: Hybrid Approach (Future)
- For num_children ≤ 8: Use angular spreading (dramatic visual effect)
- For num_children > 8: Switch to fixed spacing (guaranteed no overlap)
- Document the transition threshold in user guide

## Verification Steps

After applying fix:
1. Run `test_scaling_effect.py` with 2-10 way branching
2. Verify all spacings > 44px (no overlap)
3. Verify positions in ascending order (no wrap)
4. Load BIOMD0000000001 with tree layout
5. Visually inspect for black bars
6. Verify all transitions clearly separated

## Conclusion

**The four rules are mathematically correct and implemented correctly.**

The "black bar" issue is caused by:
- ❌ **Unbounded aperture amplification** (45° × num_children)
- ❌ **tan() domain violation** (angles > 90°)
- ❌ **Insufficient testing** with high branching factors

Not by rendering pipeline errors or rule violations.

**Fix:** Cap maximum aperture at 170° to stay within tan() domain.

---

**Date:** 2025-10-12  
**Status:** Root cause identified, fix ready to implement  
**Impact:** High (affects all pathways with >4 children per node)
