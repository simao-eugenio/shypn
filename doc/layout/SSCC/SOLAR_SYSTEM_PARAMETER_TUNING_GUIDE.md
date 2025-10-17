# Solar System Layout - Parameter Tuning Guide

**Date**: 2025-01-20  
**Purpose**: Fine-tune unified physics algorithm for optimal layout quality  
**Current Status**: ✅ Paradigm correct, needs spacing adjustments

## Current Parameter Values

### Force Constants (unified_physics_simulator.py)

```python
# Oscillatory forces (arc-based)
GRAVITY_CONSTANT = 0.1          # Attraction strength
SPRING_CONSTANT = 800.0         # Repulsion strength when too close
EQUILIBRIUM_SCALE = 400.0       # Base equilibrium distance
MASS_EXPONENT = 0.35            # Mass influence on equilibrium

# Proximity repulsion (non-arc pairs)
PROXIMITY_CONSTANT = 200000.0   # Hub-hub extra repulsion
PROXIMITY_THRESHOLD = 500.0     # Mass threshold for "hub"
AMBIENT_CONSTANT = 1000.0       # Base for universal repulsion
UNIVERSAL_REPULSION_MULTIPLIER = 100.0  # 100x ambient = 100k base

# Satellite repulsion (low-mass pairs)
SATELLITE_REPULSION_MULTIPLIER = 10.0   # 10x universal = 1M for satellites
```

### Simulation Parameters (unified_physics_simulator.py)

```python
NUM_ITERATIONS = 500            # Total iterations
DAMPING_FACTOR = 0.85           # Velocity damping (0.85 = 15% energy loss)
MAX_VELOCITY = 20.0             # Speed limit per iteration
TIME_STEP = 0.1                 # Physics time step
```

## Tuning Scenarios

### Scenario 1: Wider Hub Separation (RECOMMENDED)

**Goal**: Push the 3 transition hubs further apart (current: 105-132 units → target: 300-500 units)

**Adjustment**: Increase hub-hub repulsion

```python
# In unified_physics_simulator.py, line ~15
PROXIMITY_CONSTANT = 400000.0   # CHANGE: from 200,000 → 400,000 (2x)
```

**Effect**:
- Hub-hub repulsion: 2×10⁸ → 4×10⁸ (doubles force)
- Expected hub separation: ~300-400 units (3x current)
- Place orbits: Unaffected (orbital spreading remains good)

**When to use**: If transition hubs are too clustered (current canvas shows this)

---

### Scenario 2: Even Wider Hub Separation

**Goal**: Maximum hub separation for large canvas (target: 500-700 units)

**Adjustment**: Triple hub-hub repulsion

```python
PROXIMITY_CONSTANT = 600000.0   # CHANGE: from 200,000 → 600,000 (3x)
```

**Effect**:
- Hub-hub repulsion: 2×10⁸ → 6×10⁸ (3x force)
- Expected hub separation: ~500-700 units
- Risk: May push hubs too far for small canvas

**When to use**: Large models on large canvas, want maximum spread

---

### Scenario 3: Tighter Place Orbits

**Goal**: Pull places closer to their transition hub (current: 58-570 units → target: 100-300 units)

**Adjustment**: Increase equilibrium distance scaling

```python
EQUILIBRIUM_SCALE = 300.0       # CHANGE: from 400 → 300 (smaller orbits)
```

**Effect**:
- Equilibrium distance decreases by 25%
- Places orbit closer to transition
- More compact orbital systems

**When to use**: If places drift too far from hubs, want tighter clustering per hub

---

### Scenario 4: Wider Place Orbits

**Goal**: Spread places further from their transition hub (target: 300-800 units)

**Adjustment**: Decrease equilibrium distance scaling

```python
EQUILIBRIUM_SCALE = 500.0       # CHANGE: from 400 → 500 (larger orbits)
```

**Effect**:
- Equilibrium distance increases by 25%
- Places orbit further from transition
- More spacious orbital systems

**When to use**: Large canvas, want dramatic orbital spread

---

### Scenario 5: More Place-Place Separation (within orbit)

**Goal**: Increase spacing between places orbiting same transition (current: 92-476 units → target: 150-500 units)

**Adjustment**: Increase satellite-satellite repulsion

```python
# In unified_physics_simulator.py, line ~347
# Find this section:
if m1 < PROXIMITY_THRESHOLD and m2 < PROXIMITY_THRESHOLD:
    satellite_repulsion = (AMBIENT_CONSTANT * UNIVERSAL_REPULSION_MULTIPLIER * 10.0) / (distance * distance)

# CHANGE the multiplier from 10.0 to 20.0:
    satellite_repulsion = (AMBIENT_CONSTANT * UNIVERSAL_REPULSION_MULTIPLIER * 20.0) / (distance * distance)
```

**Effect**:
- Place-place repulsion: 1M → 2M (doubles)
- Minimum place-place spacing increases
- Better 360° spread around transition

**When to use**: If places still cluster within orbit (not current issue)

---

### Scenario 6: Longer Simulation (smoother convergence)

**Goal**: Allow more iterations for system to settle

**Adjustment**: Increase iterations

```python
NUM_ITERATIONS = 1000           # CHANGE: from 500 → 1000 (2x)
```

**Effect**:
- More time for forces to balance
- Smoother, more stable final positions
- Slower computation (2x time)

**When to use**: If layout looks "unfinished" or jittery

---

### Scenario 7: Faster Convergence

**Goal**: Reach equilibrium faster (for large models)

**Adjustment**: Reduce damping, increase velocity limit

```python
DAMPING_FACTOR = 0.90           # CHANGE: from 0.85 → 0.90 (less energy loss)
MAX_VELOCITY = 30.0             # CHANGE: from 20.0 → 30.0 (faster movement)
```

**Effect**:
- Nodes move faster per iteration
- Converges in fewer iterations
- Risk: May overshoot and oscillate

**When to use**: Large models where 500 iterations isn't enough

---

## Recommended Fix for Current Canvas

Based on the image showing **tight hub clustering** (3 transitions almost touching), I recommend:

### **Option A: Double Hub Repulsion** (Quick fix)

```python
# File: src/shypn/layout/sscc/unified_physics_simulator.py
# Line: ~15

PROXIMITY_CONSTANT = 400000.0   # CHANGE from 200000.0
```

**Expected Result**:
- Hub separation: 105-132 → 300-400 units
- Places keep good orbital spreading
- **1 line change, big improvement**

### **Option B: Triple Hub Repulsion** (Dramatic spread)

```python
PROXIMITY_CONSTANT = 600000.0   # CHANGE from 200000.0
```

**Expected Result**:
- Hub separation: 105-132 → 500-700 units
- Maximum constellation spread
- Best for large canvas

---

## Testing Workflow

### 1. Modify Parameters

```bash
# Edit the file
nano src/shypn/layout/sscc/unified_physics_simulator.py

# Change desired constant (see scenarios above)
```

### 2. Test with Script

```bash
cd /home/simao/projetos/shypn
python3 scripts/verify_paradigm_shift.py | grep -A5 "Hub Separation"
```

**Look for**:
```
Hub Separation (Transition-to-Transition):
  Hub Transition 1 ↔ Hub Transition 2: XXX units
```

### 3. Test in Canvas

```bash
python3 src/shypn.py
```

1. File → Open → `workspace/Test_flow/model/hub_constellation.shy`
2. Right-click canvas → "Layout: Solar System (SSCC)"
3. **Observe**: Are hubs better separated?

### 4. Compare Results

Take screenshot, compare with previous layout:
- Hub spacing improved?
- Orbital spreading maintained?
- Overall aesthetic better?

---

## Parameter Interaction Matrix

| Increase... | Effect on Hubs | Effect on Orbits | Effect on Places |
|-------------|---------------|------------------|------------------|
| `PROXIMITY_CONSTANT` | ⬆️ Separate more | ➡️ No change | ➡️ No change |
| `EQUILIBRIUM_SCALE` | ➡️ No change | ⬆️ Wider orbits | ⬆️ Further from hub |
| `SATELLITE_REPULSION` | ➡️ No change | ➡️ No change | ⬆️ More separation |
| `GRAVITY_CONSTANT` | ⬇️ Cluster more | ⬇️ Tighter orbits | ⬇️ Closer to hub |
| `NUM_ITERATIONS` | ➡️ Smoother | ➡️ Smoother | ➡️ Smoother |
| `MAX_VELOCITY` | ⚡ Faster converge | ⚡ Faster converge | ⚡ Faster converge |

⬆️ = Increases  
⬇️ = Decreases  
➡️ = No effect  
⚡ = Speeds up

---

## Quick Reference: Force Magnitudes

### Current Force Balance (at typical distances)

**Hub-Hub Repulsion** (r=100 units):
```
F = 200,000 * 1000 * 1000 / 100²
  = 2,000,000 (2M)
```

**Place-Place Repulsion** (r=100 units):
```
F = 1,000,000 / 100²
  = 100,000 (100k)
```

**Place-Hub Attraction** (r=200 units):
```
F = 0.1 * 100 * 1000 * 1.0 / 200²
  = 250
```

### Ratio Analysis

```
Hub-Hub : Place-Place : Place-Hub
  2M     :    100k     :    250
  8000   :     400     :     1       (normalized to attraction)
```

**Insight**: Hub-hub repulsion is **8000x stronger** than place-hub attraction!  
This is why hubs spread apart. But at current settings, still too weak (hubs only 105 units apart).

### After Doubling PROXIMITY_CONSTANT

```
Hub-Hub : Place-Place : Place-Hub
  4M     :    100k     :    250
  16000  :     400     :     1       (normalized)
```

**Expected**: Hub separation improves to ~300-400 units.

---

## Advanced: Multi-Parameter Tuning

For **optimal layout quality**, tune multiple parameters together:

### **Preset 1: Compact Constellation** (small canvas)
```python
PROXIMITY_CONSTANT = 300000.0       # Moderate hub spacing
EQUILIBRIUM_SCALE = 300.0           # Tight orbits
UNIVERSAL_REPULSION_MULTIPLIER = 80.0  # Less overall spread
NUM_ITERATIONS = 500
```

### **Preset 2: Wide Constellation** (large canvas) - RECOMMENDED
```python
PROXIMITY_CONSTANT = 500000.0       # Wide hub spacing
EQUILIBRIUM_SCALE = 400.0           # Standard orbits
UNIVERSAL_REPULSION_MULTIPLIER = 100.0  # Current setting
NUM_ITERATIONS = 500
```

### **Preset 3: Dramatic Spread** (presentation mode)
```python
PROXIMITY_CONSTANT = 800000.0       # Maximum hub spacing
EQUILIBRIUM_SCALE = 500.0           # Wide orbits
UNIVERSAL_REPULSION_MULTIPLIER = 120.0  # Extra spacing
NUM_ITERATIONS = 750                # More time to settle
```

---

## Troubleshooting

### Problem: Hubs still too close

**Solution**: Increase `PROXIMITY_CONSTANT` (try 400k → 600k → 800k)

### Problem: Hubs too far apart (off canvas)

**Solution**: Decrease `PROXIMITY_CONSTANT` (try 200k → 150k → 100k)

### Problem: Places cluster within orbit

**Solution**: Increase satellite repulsion multiplier (10.0 → 20.0 → 30.0)

### Problem: Places too far from hub

**Solution**: Decrease `EQUILIBRIUM_SCALE` (400 → 300 → 250)

### Problem: Layout looks chaotic

**Solution**: 
- Increase `NUM_ITERATIONS` (500 → 1000)
- Decrease `MAX_VELOCITY` (20.0 → 15.0)
- Increase `DAMPING_FACTOR` (0.85 → 0.90)

### Problem: Simulation too slow

**Solution**:
- Decrease `NUM_ITERATIONS` (500 → 300)
- Keep other parameters for quality

---

## Conclusion

**For your current canvas** (tight hub clustering), I recommend starting with:

```python
PROXIMITY_CONSTANT = 400000.0  # Double from 200k
```

This single change should give you **3x better hub separation** (105-132 → 300-400 units) while maintaining the excellent orbital spreading you're already seeing.

**Test, observe, iterate!** 🚀
