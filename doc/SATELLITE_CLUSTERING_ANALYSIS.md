# Satellite Clustering Problem - Analysis and Solutions

**Date:** October 16, 2025  
**Issue:** Satellites clustering in narrow angular range instead of distributing around hubs  
**Status:** DIAGNOSED, SOLUTIONS PROPOSED  

## Problem Description

### Observed Behavior (from canvas):
- ✅ Hubs well-separated (448-571 units)
- ❌ Satellites clustering in small angular range (all on one side of hub)
- ❌ Satellites too close to each other (24-38 units, should be > 50)
- ❌ No circular distribution around hubs

### Detailed Analysis Results:

**Hub 1 satellites:**
- Angular range: 18.7° to 87.1° (**68° range**, should be ~360°)
- Min satellite-to-satellite distance: **24.1 units** (too close!)
- Distance from hub: 102-242 units (uneven)

**Hub 2 satellites:**
- Angular range: -43.0° to -23.0° (**20° range!**, very clustered)
- Min satellite-to-satellite distance: **37.9 units** (too close!)
- Distance from hub: 397-584 units (uneven)

**Hub 3 satellites:**
- Angular range: 19.7° to 34.7° (**15° range!**, extremely clustered)
- Min satellite-to-satellite distance: **28.6 units** (too close!)
- Distance from hub: 410-543 units (uneven)

## Root Cause Analysis

### Why Satellites Cluster:

1. **Identical Force Interactions**
   - All satellites from same hub have identical:
     - Arc weight (1.0)
     - Source mass (hub mass = 1000 for hubs, or varies by degree)
     - Target mass (transition mass = 50)
   - Result: All satellites want same equilibrium distance
   - No differentiation → they cluster at that distance

2. **No Angular Distribution Force**
   - Current forces:
     - Oscillatory (radial): hub ← → satellite
     - Proximity repulsion: satellite ←/→ satellite
     - Ambient tension: weak global repulsion
   - **Missing**: Tangential force to spread satellites around orbit
   - Satellites repel radially but not tangentially

3. **Weak Satellite-to-Satellite Repulsion**
   - Universal repulsion: `(AMBIENT_CONSTANT * 200) / r²`
   - For transitions (mass=50): `(1000 * 200 * 50 * 50) / r²`
   - At 30 units: Force ≈ 555,000
   - **But** oscillatory attraction to hub is stronger!
   - Result: Satellites pushed together in clump

4. **Convergence to Stable (but bad) Equilibrium**
   - Algorithm converges quickly (< 1000 iterations)
   - Satellites find stable position as a cluster
   - Increasing iterations doesn't help (already at equilibrium)
   - Need different force model, not more iterations

## Proposed Solutions

### Solution 1: Angular Distribution Force (RECOMMENDED)

Add a new force type that distributes satellites evenly around their hub:

```python
def _calculate_angular_distribution(self, positions, arcs, masses):
    """Distribute satellites evenly around their hub (angular spacing)."""
    
    # Group satellites by their hub
    hub_satellites = {}  # hub_id → list of satellite_ids
    for arc in arcs:
        hub_id = arc.source.id
        sat_id = arc.target.id
        if hub_id not in hub_satellites:
            hub_satellites[hub_id] = []
        hub_satellites[hub_id].append(sat_id)
    
    # For each hub, distribute its satellites evenly
    for hub_id, sat_ids in hub_satellites.items():
        if len(sat_ids) < 2:
            continue
        
        hub_pos = positions[hub_id]
        
        # Calculate current angles of satellites
        sat_angles = []
        for sat_id in sat_ids:
            sat_pos = positions[sat_id]
            dx = sat_pos[0] - hub_pos[0]
            dy = sat_pos[1] - hub_pos[1]
            angle = math.atan2(dy, dx)
            sat_angles.append((sat_id, angle))
        
        # Sort by angle
        sat_angles.sort(key=lambda x: x[1])
        
        # Calculate ideal angular spacing
        ideal_spacing = 2 * math.pi / len(sat_ids)
        
        # Apply tangential forces to even out spacing
        for i, (sat_id, angle) in enumerate(sat_angles):
            prev_angle = sat_angles[i-1][1]
            next_angle = sat_angles[(i+1) % len(sat_angles)][1]
            
            # Calculate angular gaps
            gap_before = angle - prev_angle
            gap_after = next_angle - angle
            
            # Apply force to even out gaps
            # If gap_before < ideal: push forward (increase angle)
            # If gap_after < ideal: push backward (decrease angle)
            force_factor = (ideal_spacing - gap_before) - (ideal_spacing - gap_after)
            
            # Convert to tangential force (perpendicular to radial)
            sat_pos = positions[sat_id]
            dx = sat_pos[0] - hub_pos[0]
            dy = sat_pos[1] - hub_pos[1]
            r = math.sqrt(dx*dx + dy*dy)
            
            # Tangential direction (perpendicular to radial)
            tx = -dy / r
            ty = dx / r
            
            # Apply force
            force_magnitude = ANGULAR_DISTRIBUTION_CONSTANT * force_factor
            fx = tx * force_magnitude
            fy = ty * force_magnitude
            
            self.forces[sat_id] = (
                self.forces[sat_id][0] + fx,
                self.forces[sat_id][1] + fy
            )
```

**Advantages:**
- ✅ Directly addresses angular clustering
- ✅ Maintains radial distances (doesn't interfere with oscillatory forces)
- ✅ Natural even distribution emerges
- ✅ Works for any number of satellites

**Implementation:**
- Add constant: `ANGULAR_DISTRIBUTION_CONSTANT = 10000.0`
- Call in `_calculate_forces()` after oscillatory forces
- Enable/disable via flag

### Solution 2: Increase Satellite-to-Satellite Repulsion

Dramatically increase the universal repulsion multiplier specifically for low-mass nodes:

```python
# In _calculate_proximity_repulsion():
# Scale repulsion by inverse of mass (lighter = stronger repulsion)
mass_factor = 1000.0 / min(m1, m2)  # Lighter nodes repel more
base_force = (self.AMBIENT_CONSTANT * self.UNIVERSAL_REPULSION_MULTIPLIER * mass_factor) / (distance * distance)
```

**Advantages:**
- ✅ Simple modification to existing code
- ✅ No new force type needed
- ✅ Makes transitions repel each other strongly

**Disadvantages:**
- ❌ May cause instability (very strong forces)
- ❌ Doesn't guarantee angular distribution
- ❌ May push satellites too far from hub

### Solution 3: Randomize Arc Weights

Give each satellite a slightly different arc weight to break symmetry:

```python
# In generate_test_models.py:
import random
for sat_idx in range(6):
    weight = 1.0 + random.uniform(-0.2, 0.2)  # 0.8 to 1.2
    arcs.append(Arc(hub, satellite, arc_id, weight=weight))
```

**Advantages:**
- ✅ Very simple
- ✅ Breaks perfect symmetry
- ✅ Different equilibrium distances

**Disadvantages:**
- ❌ Doesn't solve angular clustering (still cluster, just at different radii)
- ❌ Feels like a hack
- ❌ Unpredictable results

### Solution 4: Use Initial Positions as Constraint

Preserve the initial angular distribution by adding a "memory" force:

```python
def _calculate_position_memory(self, positions, initial_positions, masses):
    """Pull nodes toward their initial angular position."""
    for node_id in positions:
        initial_pos = initial_positions[node_id]
        current_pos = positions[node_id]
        
        # Calculate angular deviation from initial
        # Apply weak force to maintain initial angle
        ...
```

**Advantages:**
- ✅ Preserves designer intent
- ✅ Guaranteed angular distribution

**Disadvantages:**
- ❌ Rigid (can't adapt to network structure)
- ❌ Defeats purpose of automatic layout
- ❌ Not generalizable to real networks

## Recommendation

**Implement Solution 1: Angular Distribution Force**

This is the most principled approach because:
1. It directly addresses the problem (angular clustering)
2. It's physically intuitive (satellites push each other apart tangentially)
3. It generalizes to any network structure
4. It can be enabled/disabled like other forces
5. It creates natural, aesthetic results

**Implementation Plan:**
1. Add `_calculate_angular_distribution_forces()` method to `UnifiedPhysicsSimulator`
2. Add constant: `ANGULAR_DISTRIBUTION_CONSTANT = 10000.0`
3. Call in `_calculate_forces()` after proximity repulsion
4. Test on hub_constellation model
5. Tune constant for best visual results

**Expected Result:**
- Satellites evenly distributed around hub (60° spacing for 6 satellites)
- No clustering (> 100 units between satellites)
- Clean circular/orbital pattern
- Maintains hub separation

## Alternative Quick Fix

If angular distribution is too complex, combine Solutions 2 and 3:

1. **Increase repulsion for transitions:** Mass 50 → 100
2. **Randomize arc weights:** weight = 0.8-1.2
3. **Increase universal repulsion multiplier:** 200 → 500

This won't guarantee perfect distribution but should reduce clustering significantly.

## Testing Strategy

1. **Implement angular distribution force**
2. **Test on hub_constellation.shy:**
   - Check angular spread (should be ~60° spacing)
   - Check satellite-to-satellite distances (should be > 100 units)
   - Check radial distances (should be ~300-400 units)
3. **Test on scc_with_hubs.shy:**
   - Verify doesn't break SCC layout
   - Check hub satellite distribution
4. **Test on real biomodels:**
   - BIOMD0000000061
   - Verify no negative side effects

## Summary

**Problem:** Satellites cluster in narrow angular range due to identical force interactions and lack of tangential distribution forces.

**Root Cause:** Current force model only has radial forces (hub ← → satellite), no tangential forces (satellite ← → satellite around orbit).

**Solution:** Add angular distribution force that spreads satellites evenly around their hub's orbit.

**Impact:** Clean, circular satellite orbits with even spacing, maintaining the hub constellation pattern.

---

**Status:** Analysis complete, solution proposed  
**Next Step:** Implement angular distribution force  
**Priority:** HIGH (blocks visual quality of constellation pattern)  
