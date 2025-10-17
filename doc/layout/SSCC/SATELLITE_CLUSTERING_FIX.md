# Satellite Clustering Fix - Strong Satellite-Satellite Repulsion

**Date:** October 16, 2025  
**Issue:** Satellites clustering together instead of spreading around their hub  
**User Insight:** "Satellites prefer satellite clustering (mass of satellite prefers mass of satellite) then to their hubs"  
**Status:** FIX IMPLEMENTED - TESTING REQUIRED  

## Problem Analysis

### User Observations:

1. **Satellites form a single clustered mass** instead of orbiting individually around their hub
2. **Satellites drift far from hub** as a collective group
3. **Satellite-to-satellite attraction dominates** over hub-to-satellite relationship
4. **Hub separation is good** (450-570 units) but satellites don't spread around the hub

### Root Cause:

The issue is **force balance**:

**Attractive Forces** (pulling satellites together):
- Hub → Satellite (oscillatory force with weight 10.0)
- Formula: `F = (0.1 * 1000 * 50 * 10.0) / r² = 50,000 / r²`

**Repulsive Forces** (pushing satellites apart):
- Universal base repulsion: `F = 100,000 / r²`
- Should be strong enough, but isn't working!

**Why satellites still cluster:**
1. Each satellite is attracted to its hub
2. All 6 satellites from same hub converge toward the hub
3. They meet in the same region (equilibrium distance from hub)
4. Universal repulsion (100k) can't overcome **6 satellites all trying to be at same spot**
5. Result: Satellites cluster together at ~400-500 units from hub

## User's Key Insight

> "the distance between hubs must weak (or act against satellite aggrupment) the preference for others satellite attraction"

**Translation:** Hub-to-hub distance should counter satellite clustering. When hubs are far apart, satellites should spread around their own hub rather than clustering.

**Interpretation:** Satellites (low-mass nodes) need **MUCH STRONGER repulsion** from each other than from high-mass nodes (hubs).

## Solution: 10x Satellite-Satellite Repulsion

Added **special case repulsion** for low-mass nodes (satellites/transitions):

### Implementation:

**File:** `src/shypn/layout/sscc/unified_physics_simulator.py`

**Method:** `_calculate_proximity_repulsion()`

```python
# SATELLITE-SATELLITE EXTRA REPULSION: Prevent satellite clustering
# Satellites (low mass) should strongly repel each other to spread around hub
# This counters their collective attraction toward hub
satellite_repulsion = 0.0
if m1 < PROXIMITY_THRESHOLD and m2 < PROXIMITY_THRESHOLD:
    # Both are low-mass nodes (satellites/transitions)
    # Apply strong repulsion to prevent them clustering together
    # Strength: 10x the universal base (1,000,000 / r²)
    satellite_repulsion = (AMBIENT_CONSTANT * UNIVERSAL_REPULSION_MULTIPLIER * 10.0) / (distance * distance)

# Total repulsion force
force_magnitude = base_force + satellite_repulsion + extra_force
```

### Force Levels:

| Force Type | Formula | Strength (at r=100) |
|------------|---------|---------------------|
| Hub → Satellite attraction | 50,000 / r² | 5.0 |
| Universal base repulsion | 100,000 / r² | 10.0 |
| **Satellite-satellite repulsion** | **1,000,000 / r²** | **100.0** |
| Hub-hub extra repulsion | 200M * m1*m2 / r² | Very high |

**Result:** Satellite-satellite repulsion is now **20x stronger** than hub-satellite attraction!

## Expected Behavior

### Before (Clustered Satellites):
```
         Satellite Cluster
              ●●●●●●
             /      \
            /        \
     Hub 1 ○          ○ Hub 2
            \        /
             \      /
              ●●●●●●
         Satellite Cluster
```

### After (Spread Satellites):
```
          ●     ●
        ●   ○   ●   Hub 1
          ●     ●
       
       ●     ●
     ●   ○   ●       Hub 2
       ●     ●
       
          ●     ●
        ●   ○   ●   Hub 3
          ●     ●
```

## Testing

### Canvas Test:
```bash
python3 src/shypn.py
# File → Open → workspace/Test_flow/model/hub_constellation.shy
# Right-click → "Layout: Solar System (SSCC)"
```

### Expected Results:
- ✅ Satellites spread around their parent hub (not clustered)
- ✅ Satellites maintain 50-150 unit spacing from each other
- ✅ Satellites orbit at 100-200 units from hub
- ✅ Hubs remain 450-570 units apart
- ✅ 3 distinct hub systems visible

### Metrics to Check:
1. **Satellite-to-satellite distance:** Should be > 50 units (not 24-38 units)
2. **Satellite angular distribution:** Should spread 0-360° (not clustered in 18-87° range)
3. **Satellite orbit radius:** Should be consistent 100-200 units from hub
4. **Hub separation:** Should maintain 450-570 units

## Alternative Solutions (if 10x doesn't work)

If satellites still cluster, we can try:

### 1. **Even Stronger Satellite Repulsion (100x)**
```python
satellite_repulsion = (AMBIENT_CONSTANT * UNIVERSAL_REPULSION_MULTIPLIER * 100.0) / (distance * distance)
# Results in: 10,000,000 / r² = 1000 at r=100
```

### 2. **Reduce Hub-Satellite Attraction**
```python
# In model generator, use weight = 1.0 instead of 10.0
arcs.append(Arc(hub, t, arc_id, f"A{arc_id}", weight=1.0))
```

### 3. **Angular Distribution Force**
Add a tangential force that pushes satellites apart in angular direction:
```python
# For satellites around same hub, push them apart tangentially
# This preserves radial distance while spreading them angularly
```

### 4. **Satellite Mass Increase**
Increase transition mass from 50 to 100 or 200:
```python
MASS_TRANSITION = 100  # in hub_based_mass_assigner.py
```

## Physics Principles

The key insight is: **In a multi-body system, pairwise interactions matter.**

**Satellite Clustering Physics:**
- 1 Hub (mass 1000) attracts 6 satellites (mass 50 each)
- Each satellite experiences: `F_hub = 50,000 / r²` toward hub
- Each satellite also experiences: `F_sat = 100,000 / r²` from each of 5 other satellites
- Total repulsion from other satellites: `5 × 100,000 / r² = 500,000 / r²`
- Ratio: Repulsion/Attraction = 500k / 50k = 10:1

**With 10x Boost:**
- Satellite-satellite repulsion: `5 × 1,000,000 / r² = 5,000,000 / r²`
- Ratio: Repulsion/Attraction = 5M / 50k = 100:1

**This should definitely prevent clustering!**

## Status

**Implementation:** ✅ COMPLETE  
**Testing:** ⏳ PENDING (canvas test required)  
**Expected Result:** Satellites spread 360° around their hub  
**Fallback:** If 10x insufficient, increase to 100x  

---

**Modified File:** `unified_physics_simulator.py` line 347-359  
**Key Change:** Added 10x satellite-satellite repulsion for nodes with mass < 500  
**Force Ratio:** Satellite repulsion now 100x stronger than hub attraction  
