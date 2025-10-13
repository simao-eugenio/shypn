# Tree Layout - Angular vs Linear Distribution

## The Issue with High Branching

When aperture is capped at 170° (to avoid tan() wrap), children are distributed **uniformly by angle**, which creates **non-uniform horizontal spacing** due to tan()'s non-linearity.

### Example: 5 Children at 170° Aperture

**Angular distribution** (equal angle steps):
```
Angles: -85°, -42.5°, 0°, +42.5°, +85°
Positions: -1715px, -137px, 0px, +137px, +1715px
Spacings: 1578px, 137px, 137px, 1578px
```

**The edges are 11× wider than the center!**

This happens because:
- `tan(85°) ≈ 11.4` (very large)
- `tan(42.5°) ≈ 0.92` (moderate)
- `tan(0°) = 0`

The tangent function grows exponentially near ±90°.

## Two Valid Approaches

### Approach 1: Angular Distribution (Current - Mathematically Pure)

**Principle:** Distribute children uniformly by angle

**Formula:**
```python
angle_step = aperture / (num_children - 1)
angle[i] = -aperture/2 + i × angle_step
position[i] = vertical_distance × tan(angle[i])
```

**Advantages:**
- ✅ Mathematically pure angular distribution
- ✅ Respects angular inheritance (Rule 1)
- ✅ Natural geometric relationship
- ✅ Consistent with tree structure (angular cones)

**Disadvantages:**
- ❌ Non-uniform horizontal spacing (edges much wider)
- ❌ Can look unbalanced for high branching
- ❌ Center nodes crowded, edge nodes spread out

**When to use:**
- Low-medium branching (2-8 children)
- When angular relationships are more important than visual balance
- Scientific/mathematical visualizations

### Approach 2: Linear Distribution (Alternative - Visually Balanced)

**Principle:** Distribute children uniformly by horizontal spacing

**Formula:**
```python
# Calculate positions to achieve uniform spacing
total_width = (num_children - 1) × min_spacing
position[i] = -total_width/2 + i × min_spacing

# Then calculate angles (for compatibility with Rule 1)
angle[i] = atan(position[i] / vertical_distance)
```

**Advantages:**
- ✅ Uniform visual spacing
- ✅ Balanced appearance for high branching
- ✅ Predictable layout
- ✅ Better for UI/visualization

**Disadvantages:**
- ❌ Angles no longer uniformly distributed
- ❌ Breaks pure angular inheritance
- ❌ Less mathematically "pure"

**When to use:**
- High branching (9+ children)
- User interfaces and visualizations
- When visual balance is prioritized

## Hybrid Approach (Recommended)

**Strategy:** Use angular distribution for low branching, switch to linear for high branching

```python
def calculate_positions(num_children, aperture, vertical_distance, min_spacing):
    \"\"\"Calculate child positions using hybrid approach.\"\"\"
    
    # Threshold: switch at 8 children (aperture ~315° → capped at 170°)
    HYBRID_THRESHOLD = 8
    
    if num_children <= HYBRID_THRESHOLD:
        # ANGULAR DISTRIBUTION (natural, pure)
        angle_step = aperture / (num_children - 1)
        positions = []
        for i in range(num_children):
            angle = -aperture/2 + i × angle_step
            pos = vertical_distance × tan(angle)
            positions.append(pos)
        return positions
    else:
        # LINEAR DISTRIBUTION (balanced, practical)
        total_width = (num_children - 1) × min_spacing
        positions = []
        for i in range(num_children):
            pos = -total_width/2 + i × min_spacing
            positions.append(pos)
        return positions
```

**Benefits:**
- ✅ Best of both worlds
- ✅ Angular purity for normal cases
- ✅ Visual balance for extreme cases
- ✅ Smooth transition at threshold

## Current Status

**Implementation:** Approach 1 (Angular Distribution)

**Result for high branching:**
- 5 children: spacing varies 11× (1578px edges, 137px center)
- 10 children: spacing varies 28× (1376px edges, 50px center)
- 20 children: spacing varies 47× (1111px edges, 24px center)

**This is mathematically correct but visually unbalanced.**

## Recommendation

For production use, implement **Hybrid Approach**:

1. **Low branching (≤8 children):** Angular distribution (current)
   - Respects locality principle
   - Natural angular inheritance
   - Dramatic scaling effect visible
   
2. **High branching (>8 children):** Linear distribution
   - Uniform spacing
   - Visual balance
   - No "crowded center, sparse edges" effect

**Implementation in `_position_subtree()`:**
```python
if len(children) <= 8:
    # Angular distribution (natural)
    angle_step = parent.aperture_angle / (len(children) - 1)
    for i, child in enumerate(children):
        child.my_angle = parent.my_angle + (-parent.aperture_angle/2 + i * angle_step)
        child.x = parent.x + self.base_vertical_spacing * math.tan(child.my_angle)
else:
    # Linear distribution (balanced)
    total_width = (len(children) - 1) * self.min_horizontal_spacing
    for i, child in enumerate(children):
        child.x = parent.x + (-total_width/2 + i * self.min_horizontal_spacing)
        # Calculate angle for consistency
        child.my_angle = math.atan((child.x - parent.x) / self.base_vertical_spacing)
```

This preserves the locality principle while ensuring visual quality for all branching factors.
