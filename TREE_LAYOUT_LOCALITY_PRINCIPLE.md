# Tree Layout - Locality-Based Aperture Calculation

## The Locality Principle

**Key Insight:** Each node only needs to know about its **immediate children** (locality). The aperture angle should naturally ensure proper spacing for those children, and the effect propagates downstream through angular inheritance.

## Current Problem: Over-Amplification

**Current formula:**
```python
aperture = base_angle × num_children × scaling_factor
```

**Issues:**
- Amplification causes aperture to grow unbounded (5 children → 225°)
- Exceeds tan() domain (±90°)
- Creates "black bar" overlap

## Natural Solution: Spacing-Driven Aperture

**Principle:** Calculate the aperture angle needed to achieve **minimum spacing** between immediate children.

### Geometric Relationship

For `n` children distributed within aperture angle `θ`:

```
        Parent
          |
    ╱─────┼─────╲
   ╱      |      ╲
  ╱       |       ╲
 C1      C2       C3

Angles: -θ/2, 0, +θ/2 (for 3 children)
```

**Spacing between adjacent children:**
```
spacing = vertical_distance × [tan(angle₂) - tan(angle₁)]
```

For equal distribution:
```
angle_step = θ / (n - 1)
angle₁ = -θ/2
angle₂ = -θ/2 + angle_step

spacing = vertical_distance × [tan(-θ/2 + angle_step) - tan(-θ/2)]
```

**Required:** `spacing >= min_spacing`

### Simplified Approach

For small to moderate apertures (< 90°), we can approximate:

**Given:**
- `n` children
- `min_spacing` required (e.g., 150px)
- `vertical_distance` between layers (e.g., 150px)

**Calculate aperture to achieve spacing:**

For uniform distribution, the angle step is:
```python
angle_step = aperture / (n - 1)
```

The spacing between first two children (at angles -aperture/2 and -aperture/2 + angle_step):
```python
spacing ≈ vertical_distance × angle_step  # For small angles, tan(x) ≈ x
```

**Solving for aperture:**
```python
aperture = (n - 1) × (min_spacing / vertical_distance)
```

This is naturally bounded because:
- More children → larger aperture (needed for spacing)
- But the relationship is **linear**, not quadratic
- For n=10, min_spacing=150, vertical_distance=150:
  - aperture = 9 × (150/150) = 9 radians = 515°... still too large!

## Better Approach: Arc-Length Based

The issue is that tangent spacing grows non-linearly. For high branching, we should think in terms of **arc length** on a circle.

**Idea:** Children arranged on an arc at fixed radius:

```
        Parent
          ●
          |
         / \
        /   \
       /     \
     C1  C2  C3  (on arc)
```

**Arc length between siblings:**
```
arc_length = radius × angle_step
```

**For horizontal spacing:**
```
horizontal_spacing ≈ arc_length  # For shallow arcs
```

**This gives:**
```python
radius × angle_step = min_spacing
angle_step = min_spacing / radius
aperture = angle_step × (n - 1)
```

Using `radius = vertical_distance`:
```python
aperture = (n - 1) × (min_spacing / vertical_distance)
```

Same formula, but the interpretation is clearer: we're spacing children on an arc.

## Practical Solution: Natural Angle Formula

**Principle:** The aperture should be **just enough** to fit all children with minimum spacing.

```python
def calculate_natural_aperture(num_children: int, 
                               min_spacing: float = 150.0,
                               vertical_distance: float = 150.0) -> float:
    """Calculate aperture based on spacing requirements (locality).
    
    Each node determines its aperture based on:
    1. Number of immediate children (locality)
    2. Minimum spacing requirement
    3. Vertical distance (geometric constraint)
    
    The aperture naturally scales with num_children, but is bounded
    by geometric constraints (tan domain).
    """
    if num_children <= 1:
        return 0.0
    
    # Calculate angle step needed for minimum spacing
    # Using small-angle approximation: spacing ≈ vertical_distance × angle
    angle_step_rad = min_spacing / vertical_distance
    
    # Total aperture for n children with (n-1) gaps
    aperture_rad = angle_step_rad * (num_children - 1)
    
    # Cap at safe maximum (170° = 2.967 rad) to avoid tan() wrap
    MAX_APERTURE_RAD = math.radians(170.0)
    safe_aperture = min(aperture_rad, MAX_APERTURE_RAD)
    
    return safe_aperture
```

## Example Calculations

### 2 children:
```
aperture = 1 × (150/150) = 1 radian ≈ 57°
angles: ±28.5°
spacing: 150 × [tan(28.5°) - tan(-28.5°)] ≈ 163px ✓
```

### 5 children:
```
aperture = 4 × (150/150) = 4 radians ≈ 229°  → CAPPED at 170°
angles: ±85° (at cap)
spacing: varies, but guaranteed > 0 (no wrap)
```

### 10 children:
```
aperture = 9 × (150/150) = 9 radians → CAPPED at 170°
angles: ±85° (at cap)
Children distributed uniformly within safe range
Spacing determined by cap, not infinite growth
```

## Why This Works

1. **Locality:** Each node only considers its immediate children
2. **Natural scaling:** Aperture grows linearly with num_children
3. **Bounded:** Cap prevents tan() domain violation
4. **Propagation:** Angular constraints inherited by descendants (Rule 1)
5. **Simplicity:** No arbitrary amplification factors

## Implementation

Replace the current `calculate_base_aperture()` function with the natural formula:

```python
def calculate_base_aperture(num_children: int) -> float:
    """Calculate aperture angle based on spacing requirements (locality).
    
    Each node determines its aperture from:
    - Number of immediate children (local information)
    - Minimum spacing requirement (layout parameter)
    - Vertical distance (geometric constraint)
    
    The aperture grows naturally with num_children but is capped
    to keep all angles within tan()'s monotonic domain (±85°).
    """
    if num_children <= 1:
        return 0.0
    
    # Natural angle step for minimum spacing
    # This is the angle between adjacent children needed to achieve min_spacing
    angle_step = self.min_horizontal_spacing / self.base_vertical_spacing
    
    # Total aperture = angle_step × number of gaps
    aperture = angle_step * (num_children - 1)
    
    # Cap at 170° (2.967 rad) to keep child angles within ±85°
    MAX_APERTURE = math.radians(170.0)
    
    return min(aperture, MAX_APERTURE)
```

**Benefits:**
- ✅ Linear growth (not exponential)
- ✅ Based on actual spacing needs
- ✅ Naturally bounded
- ✅ Respects locality
- ✅ No arbitrary amplification

**Result:**
- 2 children: aperture ≈ 57° (spacing 163px)
- 3 children: aperture ≈ 114° (spacing preserved)
- 5 children: aperture ≈ 170° (capped, spacing still adequate)
- 10 children: aperture = 170° (capped, uniform distribution)

No "black bar" overlap, natural spacing throughout.
