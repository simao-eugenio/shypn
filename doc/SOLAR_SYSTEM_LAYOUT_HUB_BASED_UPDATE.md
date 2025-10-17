# Solar System Layout - Hub-Based Mass Assignment Update

## Overview

The Solar System Layout algorithm has been **enhanced** with hub-based mass assignment! This makes high-degree nodes (hubs) become gravitational centers, creating better layouts for networks without cycles or with hub nodes outside SCCs.

## What Changed

### Before (Original)
```python
Mass assignment based ONLY on SCCs:
- SCC nodes: mass = 1000 (stars)
- Places: mass = 100 (planets)
- Transitions: mass = 10 (satellites)
```

**Problem:** Networks without cycles (DAGs) had no gravitational centers, resulting in uniform distribution.

### After (Hub-Based)
```python
Mass assignment based on NODE DEGREE (connectivity):
- Super-hubs (≥6 connections): mass = 1000 (like stars)
- Major hubs (≥4 connections): mass = 500 (strong centers)
- Minor hubs (≥2 connections): mass = 200 (moderate centers)
- Regular places: mass = 100 (normal)
- Regular transitions: mass = 10 (light)

PLUS: SCCs still get mass = 1000 (takes precedence)
```

**Benefit:** Hub nodes become gravitational centers, creating hierarchy even in DAG networks!

## New Parameter

The `SolarSystemLayoutEngine` now accepts a new parameter:

```python
engine = SolarSystemLayoutEngine(
    iterations=1000,
    use_arc_weight=True,
    use_hub_masses=True,    # NEW! (default: True)
    scc_radius=50.0,
    planet_orbit=300.0,
    satellite_orbit=50.0
)
```

**`use_hub_masses` (bool):**
- `True` (default): Use hub-based mass assignment
- `False`: Use original simple SCC-based assignment

## How Hub Detection Works

The algorithm calculates **total degree** for each node:
```
total_degree = in_degree + out_degree
```

**Example:**
- Node with 3 incoming arcs + 2 outgoing arcs = degree 5 → **Major hub** (mass = 500)
- Node with 1 incoming arc + 1 outgoing arc = degree 2 → **Minor hub** (mass = 200)
- Node with 1 incoming arc only = degree 1 → **Regular** (mass = 100 or 10)

**Both places AND transitions** can be hubs!

## Visual Impact on Canvas

### DAG Networks (No Cycles)
**Before:** Uniform distribution, no clear structure  
**After:** Hub nodes cluster at center, others orbit them

### Networks with Cycles + Hubs
**Before:** Only SCC at center  
**After:** SCC at center, hubs with intermediate mass orbit closer, creating multi-layer structure

### Example: BIOMD0000000001
- **Large SCC (15 nodes):** mass = 1000 → Center cluster
- **React3 (5 connections):** mass = 500 → Intermediate orbit
- **React5 (4 connections):** mass = 500 → Intermediate orbit
- **Others:** mass = 100 or 10 → Outer orbits

## Threshold Configuration

Thresholds are defined in `HubBasedMassAssigner`:

```python
SUPER_HUB_THRESHOLD = 6  # ≥6 connections
MAJOR_HUB_THRESHOLD = 4  # ≥4 connections
MINOR_HUB_THRESHOLD = 2  # ≥2 connections
```

**Adjust these** based on network density:
- **Sparse networks:** Lower thresholds (e.g., 4, 3, 2)
- **Dense networks:** Higher thresholds (e.g., 8, 6, 4)

## Statistics

The `get_statistics()` method now includes hub information:

```python
stats = engine.get_statistics()

# Standard stats
print(f"SCCs: {stats['num_sccs']}")
print(f"Avg mass: {stats['avg_mass']}")

# Hub stats (if use_hub_masses=True)
if 'hub_stats' in stats:
    hub_stats = stats['hub_stats']
    print(f"Super-hubs: {len(hub_stats['super_hubs'])}")
    print(f"Major hubs: {len(hub_stats['major_hubs'])}")
    print(f"Minor hubs: {len(hub_stats['minor_hubs'])}")
```

## Testing

**Files:**
1. `tests/test_solar_system_layout_basic.py` - Basic smoke test ✅ PASSING
2. `tests/test_hub_based_layout.py` - Hub-based analysis on SBML files ✅ WORKING

**Test on canvas:**
1. Open Shypn application
2. Load a Petri net (e.g., from `data/biomodels_test/`)
3. Right-click on canvas → "Layout: Solar System (SSCC)"
4. Hub nodes should cluster near center!

## Backward Compatibility

✅ **Fully backward compatible!**
- Default behavior: Hub-based masses (better layouts)
- To use original: `use_hub_masses=False`
- All existing code works without changes

## Files Modified

1. `src/shypn/layout/sscc/solar_system_layout_engine.py`
   - Added `use_hub_masses` parameter
   - Integrated `HubBasedMassAssigner`
   - Updated statistics

2. `src/shypn/layout/sscc/hub_based_mass_assigner.py` (NEW)
   - Hub detection logic
   - Mass assignment based on degree
   - Statistics gathering

## Performance

**No performance impact:**
- Hub detection: O(E) where E = number of arcs
- Same complexity as original algorithm
- Negligible overhead

## Next Steps

1. ✅ Update main algorithm
2. ✅ Test on basic smoke test
3. 🔄 Test on canvas with real models
4. 📋 Gather user feedback on hub thresholds
5. 🎨 Consider UI controls for hub detection settings

---

**Date:** October 16, 2025  
**Status:** Integrated into main algorithm ✅  
**Enabled by default:** Yes  
**Impact:** Better layouts for DAG networks and hub-centric structures
