# Force-Directed Layout Physics Parameters

**Date**: October 14, 2025  
**Algorithm**: Fruchterman-Reingold (via NetworkX `spring_layout`)

## Overview

The force-directed layout uses **physics simulation** to position nodes:
- **Attractive forces** (springs): Edges pull connected nodes together
- **Repulsive forces** (anti-gravity): All nodes push each other apart
- **Energy minimization**: Iteratively moves nodes until equilibrium

## Physics Model

### Fruchterman-Reingold Algorithm

```
Attractive force (spring):  f_attr(d) = d² / k
Repulsive force (charge):   f_rep(d)  = -k² / d

where:
  d = distance between nodes
  k = optimal distance (spring rest length)
```

**Simulation process:**
1. Start with random or fixed positions
2. Calculate all forces on each node
3. Move nodes based on net force
4. Apply "cooling" (reduce movement over time)
5. Repeat until convergence or max iterations

---

## Available Parameters

### 1. **Optimal Distance (`k`)** - Spring Rest Length

**What it does**: Controls how far apart nodes should be at equilibrium.

**Current implementation**:
```python
if num_nodes > 20:
    k = 2.0      # Large pathways: more spread
elif num_nodes > 10:
    k = 1.5      # Medium pathways
else:
    k = 1.0      # Small pathways: compact
```

**Default (if None)**: `k = 1/√n` where n = number of nodes

**Effects**:
- Higher k → nodes farther apart (loose layout)
- Lower k → nodes closer together (dense layout)

---

### 2. **Edge Weights** - Spring Strength ✨ **NEW!**

**What it does**: Controls how strongly edges pull nodes together.

**Current implementation** (stoichiometry-based):
```python
# For reaction: 2A + B → C
# Edge A→reaction has weight=2.0 (stronger pull)
# Edge B→reaction has weight=1.0 (normal pull)
# Edge reaction→C has weight=1.0 (normal pull)

for species_id, stoich in reaction.reactants:
    edge_weight = max(1.0, float(stoich))
    graph.add_edge(species_id, reaction.id, weight=edge_weight)
```

**Effects**:
- Higher weight → stronger attraction (nodes pulled closer)
- Weight=1.0 → standard spring
- Weight=5.0 → 5× stronger spring

**Biochemical interpretation**:
- Stoichiometry 2: Requires twice as much substrate → pull closer
- Stoichiometry 1: Standard participation
- Could also use: reversibility, catalysis, regulation

---

### 3. **Iterations** - Simulation Steps

**What it does**: Number of physics simulation cycles.

**Current value**: `iterations=100`  
**NetworkX default**: `iterations=50`

**Effects**:
- More iterations → better convergence (slower)
- Fewer iterations → faster but may not reach equilibrium
- Useful range: 50-200

---

### 4. **Convergence Threshold** - Stop Condition

**What it does**: Stops simulation when node movement drops below threshold.

**Current value**: `threshold=1e-6` ✨ **NEW!**  
**NetworkX default**: `threshold=1e-4`

**Effects**:
- Smaller threshold → tighter convergence (more accurate)
- Larger threshold → stops earlier (faster)
- Our value is 100× tighter than default

---

### 5. **Scale Factor** - Output Coordinate Range

**What it does**: Multiplies final coordinates by this factor.

**Current implementation**:
```python
if num_nodes > 20:
    scale = 600.0    # Large: 600px range
elif num_nodes > 10:
    scale = 400.0    # Medium: 400px range
else:
    scale = 300.0    # Small: 300px range
```

**Effects**:
- Higher scale → larger canvas space
- Does NOT affect physics, only final output
- Applied AFTER simulation completes

---

### 6. **Seed** - Reproducibility

**What it does**: Controls random number generator for initial positions.

**Current value**: `seed=42`

**Effects**:
- Same seed → same layout every time
- `None` → random layout each run
- Useful for testing and debugging

---

### 7. **Initial Positions (`pos`)** - Starting Configuration

**What it does**: Pre-set starting positions for some or all nodes.

**Current implementation**: Not used (random initialization)

**Potential use**:
```python
# Pin substrate nodes at top
entry_nodes = find_entry_points()
initial_pos = {node: (500, 800) for node in entry_nodes}

raw_pos = nx.spring_layout(
    graph,
    pos=initial_pos,
    k=k_factor,
    iterations=100
)
```

**Effects**:
- Biases layout toward initial configuration
- Good for maintaining semantic structure
- Can fix nodes with `fixed` parameter

---

### 8. **Fixed Nodes** - Anchored Positions

**What it does**: Prevents certain nodes from moving during simulation.

**Current implementation**: Not used

**Potential use**:
```python
# Keep entry substrates at top, fixed
entry_nodes = find_entry_points()
initial_pos = {node: (500, 800) for node in entry_nodes}

raw_pos = nx.spring_layout(
    graph,
    pos=initial_pos,
    fixed=entry_nodes,  # Don't move these
    k=k_factor,
    iterations=100
)
```

**Effects**:
- Fixed nodes act as anchors
- Other nodes arrange around them
- Useful for hierarchical constraint

---

## Current Parameter Summary

| Parameter | Value | NetworkX Default | Status |
|-----------|-------|------------------|--------|
| **k** | 1.0-2.0 (adaptive) | 1/√n | ✅ Using |
| **weight** | Stoichiometry-based | 1.0 (uniform) | ✅ **NEW!** |
| **iterations** | 100 | 50 | ✅ Using |
| **threshold** | 1e-6 | 1e-4 | ✅ **NEW!** |
| **scale** | 300-600px (adaptive) | 1.0 | ✅ Using |
| **seed** | 42 | None (random) | ✅ Using |
| **pos** | None (random) | None | ❌ Not using |
| **fixed** | None | None | ❌ Not using |

---

## Future Enhancements

### Potential Physics Extensions:

1. **Node Mass** (requires custom implementation):
   ```python
   # Heavier nodes (high concentration) resist movement more
   mass = {species.id: species.initial_concentration or 1.0}
   ```

2. **Edge Directionality**:
   ```python
   # Use directed graph for one-way attraction
   graph = nx.DiGraph()
   ```

3. **Reversible Reaction Weights**:
   ```python
   if reaction.reversible:
       weight = 0.5  # Weaker springs for equilibrium
   else:
       weight = stoich  # Strong springs for irreversible
   ```

4. **Regulation-Based Repulsion**:
   ```python
   # Inhibitors create repulsive forces
   if regulation_type == 'inhibition':
       graph.add_edge(regulator, target, weight=-1.0)
   ```

5. **Compartment Clustering**:
   ```python
   # Add extra attraction for same-compartment nodes
   for species1 in compartment:
       for species2 in compartment:
           if species1 != species2:
               graph.add_edge(species1, species2, weight=0.1)
   ```

---

## Testing Physics Parameters

Use the test script to experiment:

```bash
# Test with different parameters
python scripts/test_spiral_layout.py BIOMD0000000001

# Modify pathway_postprocessor.py to try:
k = 3.0              # Very loose layout
iterations = 200     # High accuracy
threshold = 1e-8     # Ultra-tight convergence
```

---

## References

- **Fruchterman-Reingold Algorithm**: 
  *Graph Drawing by Force-directed Placement* (1991)
  
- **NetworkX Documentation**:
  https://networkx.org/documentation/stable/reference/generated/networkx.drawing.layout.spring_layout.html

- **Physics Simulation**:
  - Hooke's Law (springs): F = -k·x
  - Coulomb's Law (repulsion): F = k·q₁·q₂/r²

---

**Summary**: YES, we use physics! Springs (edges) pull nodes together with stoichiometry-based strength, while nodes repel like charged particles. The simulation runs for 100 iterations until convergence (threshold 1e-6), producing physically stable layouts. 🔬
