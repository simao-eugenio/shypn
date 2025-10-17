"""Solar System Layout - Testing Guide

This document provides a guide for testing the Solar System Layout algorithm.

## Quick Start

Run the basic smoke test:

```bash
cd /home/simao/projetos/shypn
python3 tests/test_solar_system_layout_basic.py
```

## Test Results (October 16, 2025)

### Basic Smoke Test: ✅ PASSED

**Test Network:**
- 4 places (P1, P2, P3, P4)
- 3 transitions (T1, T2, T3)
- 6 arcs forming:
  - Cycle: P1 → T1 → P2 → T2 → P1
  - Branch: P3 → T3 → P4

**Results:**
- ✅ All 7 objects positioned successfully
- ✅ SCC detection: Found 1 SCC with 4 nodes (P1, P2, T1, T2 cycle)
- ✅ Classification: 2 free places, 1 transition outside cycle
- ✅ No runtime errors

## Using the Layout in the UI

1. **Open a Petri net** in the canvas
2. **Right-click** on empty canvas area
3. **Select:** "Layout: Solar System (SSCC)"
4. **View statistics** in console output

## Creating Test Networks

### Simple Cycle Test

```python
from shypn.netobjs import Place, Transition, Arc

# Create cycle: P1 → T1 → P2 → T2 → P1
p1 = Place(x=0, y=0, id=1, name="P1", label="")
p2 = Place(x=100, y=0, id=2, name="P2", label="")
t1 = Transition(x=50, y=0, id=3, name="T1", label="")
t2 = Transition(x=50, y=50, id=4, name="T2", label="")

arcs = [
    Arc(source=p1, target=t1, id=5, name="A1", weight=1),
    Arc(source=t1, target=p2, id=6, name="A2", weight=1),
    Arc(source=p2, target=t2, id=7, name="A3", weight=1),
    Arc(source=t2, target=p1, id=8, name="A4", weight=1),
]

from shypn.layout.sscc import SolarSystemLayoutEngine
engine = SolarSystemLayoutEngine(iterations=100)
positions = engine.apply_layout([p1, p2], [t1, t2], arcs)
```

### Multiple SCCs Test

```python
# Create two separate cycles
# Cycle 1: P1 → T1 → P2 → T2 → P1
# Cycle 2: P3 → T3 → P4 → T4 → P3

p1 = Place(x=0, y=0, id=1, name="P1", label="")
p2 = Place(x=100, y=0, id=2, name="P2", label="")
p3 = Place(x=0, y=100, id=3, name="P3", label="")
p4 = Place(x=100, y=100, id=4, name="P4", label="")

t1 = Transition(x=50, y=0, id=5, name="T1", label="")
t2 = Transition(x=50, y=50, id=6, name="T2", label="")
t3 = Transition(x=50, y=100, id=7, name="T3", label="")
t4 = Transition(x=50, y=150, id=8, name="T4", label="")

# First cycle
arcs = [
    Arc(source=p1, target=t1, id=9, name="A1", weight=1),
    Arc(source=t1, target=p2, id=10, name="A2", weight=1),
    Arc(source=p2, target=t2, id=11, name="A3", weight=1),
    Arc(source=t2, target=p1, id=12, name="A4", weight=1),
]

# Second cycle
arcs += [
    Arc(source=p3, target=t3, id=13, name="A5", weight=1),
    Arc(source=t3, target=p4, id=14, name="A6", weight=1),
    Arc(source=p4, target=t4, id=15, name="A7", weight=1),
    Arc(source=t4, target=p3, id=16, name="A8", weight=1),
]

engine = SolarSystemLayoutEngine(iterations=200)
positions = engine.apply_layout([p1, p2, p3, p4], [t1, t2, t3, t4], arcs)

stats = engine.get_statistics()
print(f"Found {stats['num_sccs']} SCCs")  # Should be 2
```

## Expected Behavior

### SCC Detection
- **Single node:** Not counted as SCC (filtered out)
- **2+ nodes in cycle:** Detected as SCC
- **Complex cycles:** All nodes in cycle grouped into one SCC

### Layout Structure
- **SCCs:** Positioned at origin (0, 0), nodes arranged in circle
- **Free places:** Orbiting at distance ~300 units
- **Transitions:** Orbiting near their connected places at ~50 units

### Physics Simulation
- **Force calculation:** Arc-weighted gravitational forces
- **Integration:** Velocity Verlet (stable)
- **Convergence:** 1000 iterations (configurable)
- **Final refinement:** Orbital stabilization applied

## Known Issues / Limitations

### 1. Multiple SCCs (Current Implementation)
**Status:** Only largest SCC pinned at origin
**Future:** Position multiple SCCs at different angles

### 2. Transition Positioning
**Status:** Uses simple nearest-place heuristic
**Future:** Use arc connections to determine orbital placement

### 3. Large Networks
**Performance:** O(E × iterations) for physics
**Recommendation:** For >200 nodes, consider reducing iterations

## Parameter Tuning

### For Small Networks (<20 nodes)
```python
engine = SolarSystemLayoutEngine(
    iterations=500,       # Fewer iterations needed
    scc_radius=30.0,      # Smaller SCC radius
    planet_orbit=200.0,   # Tighter orbits
    satellite_orbit=40.0  # Closer satellites
)
```

### For Large Networks (>100 nodes)
```python
engine = SolarSystemLayoutEngine(
    iterations=1500,      # More iterations for convergence
    scc_radius=100.0,     # Larger SCC radius
    planet_orbit=500.0,   # Wider orbits to reduce overlap
    satellite_orbit=75.0  # More spacing
)
```

### For Dense Networks (many arcs)
```python
engine = SolarSystemLayoutEngine(
    iterations=2000,      # More iterations for complex forces
    use_arc_weight=True,  # Use arc weights (default)
    planet_orbit=600.0,   # Very wide orbits
)
```

## Visual Testing Checklist

After applying layout, verify:

- [ ] **SCCs at center:** Cycle nodes should cluster at origin
- [ ] **Circular arrangement:** SCC nodes in circular pattern
- [ ] **Clear orbits:** Places arranged in orbital rings
- [ ] **Satellite positioning:** Transitions near their places
- [ ] **No overlaps:** Minimum spacing maintained
- [ ] **Arc visualization:** Arcs clearly visible and not tangled

## Debugging

### Enable Debug Output

```python
def progress_callback(stage, progress):
    print(f"[{stage}] {progress * 100:.0f}%")

engine = SolarSystemLayoutEngine(progress_callback=progress_callback)
```

### Inspect Engine State

```python
positions = engine.apply_layout(places, transitions, arcs)

# Check detected SCCs
print(f"SCCs: {len(engine.sccs)}")
for i, scc in enumerate(engine.sccs):
    print(f"  SCC {i}: {scc.size} nodes, IDs: {scc.node_ids}")

# Check mass assignments
print(f"Masses: {engine.masses}")

# Check final positions
print(f"Positions: {engine.positions}")
```

### Compare with Other Layouts

```python
# Apply force-directed first
from shypn.edit.graph_layout import LayoutEngine
engine_fd = LayoutEngine(manager)
result_fd = engine_fd.apply_layout('force_directed')

# Apply solar system
from shypn.layout.sscc import SolarSystemLayoutEngine
engine_ss = SolarSystemLayoutEngine()
positions_ss = engine_ss.apply_layout(places, transitions, arcs)

# Compare visually
```

## Performance Benchmarks

**Hardware:** Standard development machine
**Test:** Simple cycle (4 nodes, 4 arcs)

| Iterations | Time (ms) | Notes |
|-----------|-----------|-------|
| 100       | <50       | Quick test |
| 500       | ~100      | Small networks |
| 1000      | ~200      | Default (good quality) |
| 2000      | ~400      | Large networks |

**Scaling:** Approximately O(E × iterations) where E = number of arcs

## Unit Tests (Future)

### Priority Tests to Implement

1. **test_scc_detection.py**
   - Single cycle detection
   - Multiple cycles detection
   - No cycles (DAG)
   - Self-loops

2. **test_mass_assignment.py**
   - SCC nodes get MASS_SCC
   - Free places get MASS_PLACE
   - Transitions get MASS_TRANSITION

3. **test_gravitational_forces.py**
   - Force calculation accuracy
   - Arc weight multiplier
   - Newton's 3rd law (action-reaction)

4. **test_orbit_stabilization.py**
   - SCC pinning at origin
   - Circular arrangement
   - Collision resolution

5. **test_integration.py**
   - End-to-end layout on sample networks
   - Statistics validation
   - Position bounds checking

## Next Steps

### Phase 2: UI Enhancement
- [ ] Settings dialog for parameters
- [ ] Progress bar during simulation
- [ ] Real-time visualization (optional)
- [ ] Save/load parameter presets

### Phase 3: Algorithm Improvements
- [ ] Multiple SCC positioning
- [ ] Smart transition placement using arc analysis
- [ ] Convergence detection (early stopping)
- [ ] Adaptive time step

### Phase 4: Documentation
- [ ] User guide with screenshots
- [ ] Algorithm paper/technical documentation
- [ ] Video tutorial
- [ ] Example gallery

---

**Last Updated:** October 16, 2025
**Status:** Phase 1 Complete ✅
**Test Status:** Basic smoke test passing ✅
"""
