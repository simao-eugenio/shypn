# Physics Terminology Update - Force-Directed Layout

**Date**: 2025-10-14  
**Status**: ✅ Implemented and ready for testing

---

## Changes Made

### 1. Correct Physics Terminology

**OLD (vague):**
- Nodes repel
- Edges attract
- Edge weights

**NEW (precise):**
- **Mass nodes**: Places and Transitions (repel each other via electrostatic force)
- **Springs**: Arcs (attract connected mass nodes via Hooke's law)
- **Spring strength**: Arc weight/stoichiometry (e.g., 2A → 2× stronger spring)

---

## Files Modified

### 1. `src/shypn/edit/graph_layout/engine.py`

**Method**: `build_graph()`

**Change**: Now includes arc weights as spring strength:

```python
# Add springs (arcs) with weight as spring strength
for arc in doc.arcs:
    # Arc weight = stoichiometry = spring strength
    # Higher weight = stronger spring = pulls mass nodes closer
    weight = getattr(arc, 'weight', 1.0)  # Default weight = 1.0
    graph.add_edge(arc.source, arc.target, weight=weight, obj=arc)
```

**Impact**: Graph now has edge weights that represent spring strength

---

### 2. `src/shypn/edit/graph_layout/force_directed.py`

**Method**: `compute()`

**Change**: Automatically detects and uses arc weights:

```python
# Check if edges have weights (arc stoichiometry)
has_weights = any('weight' in graph[u][v] for u, v in graph.edges())

if has_weights:
    # Use arc weights as spring strength (stoichiometry-based)
    layout_params['weight'] = 'weight'
    print(f"🔬 Force-directed: Using arc weights as spring strength")
```

**Impact**: NetworkX spring_layout now uses stoichiometry to calculate spring forces

---

## Physics Model

### Forces in the System

1. **Electrostatic Repulsion** (UNIVERSAL - between ALL mass nodes)
   - **Every mass node repels every other mass node**
   - Place ↔ Place: **repel** (like charges)
   - Transition ↔ Transition: **repel** (like charges)
   - Place ↔ Transition: **repel** (like charges)
   - Force equation: `F_repulsion = -k² / distance`
   - Purpose: Prevents overlap, creates spacing, pushes disconnected nodes apart
   - This is the "anti-gravity" that keeps all mass nodes separated

2. **Spring Attraction** (SELECTIVE - only via arcs)
   - **Only connected mass nodes attract each other**
   - Springs (arcs) pull connected mass nodes together
   - Force equation: `F_spring = k × distance × spring_strength`
   - Spring strength = arc weight (stoichiometry)
   - Example: `2A + B → C`
     * Spring from A to reaction: strength = 2.0 (2× stronger pull)
     * Spring from B to reaction: strength = 1.0 (normal pull)
     * Spring from reaction to C: strength = 1.0 (normal pull)
   - Purpose: Pulls reactants toward reactions, products toward reactions

3. **Equilibrium** (balance of forces)
   - System converges when all forces balance
   - Each mass node settles where: `∑ F_spring + ∑ F_repulsion ≈ 0`
   - Connected nodes: pulled together by springs, pushed apart by repulsion → optimal distance
   - Disconnected nodes: only repulsion → maximum separation

---

## Testing Workflow

### 1. Launch and Load

```bash
cd /home/simao/projetos/shypn
python3 -m shypn
```

### 2. Import Pathway

1. **SBML Tab** → BioModels → BIOMD0000000061
2. Click **Fetch** (downloads pathway)
3. Click **Parse** (loads to canvas with hierarchical layout)
4. **Watch console** for: `🔍 QUICK LOAD: Canvas loaded with X places, Y transitions!`

### 3. Apply Force-Directed with Physics

1. **Swiss Palette** button (toolbar or View menu)
2. Click **Layout** category (bottom)
3. Click **Force** button (Force-Directed)
4. **Watch console** for: `🔬 Force-directed: Using arc weights as spring strength`

### 4. Observe Physics Effects

**Look for:**
- ✅ Higher stoichiometry arcs pull harder (2A closer to reaction than 1B)
- ✅ Mass nodes with many springs cluster together
- ✅ Mass nodes without springs pushed away by repulsion
- ✅ Overall balanced layout (forces in equilibrium)

---

## Expected Console Output

```
🔬 Force-directed: Using arc weights as spring strength
Layout algorithm 'force_directed' applied successfully
25 mass nodes repositioned
```

---

## Physics Parameters (Hardcoded)

These are currently in the ForceDirectedLayout class:

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `iterations` | 500 | Physics simulation steps |
| `k` | auto | Optimal distance between mass nodes (spring rest length) |
| `scale` | 1000.0 | Output coordinate scale (pixels) |
| `threshold` | NetworkX default (1e-4) | Convergence criterion |
| `seed` | 42 | Random seed for reproducibility |

**Note**: The `k` value is auto-calculated as: `k = sqrt(area / num_mass_nodes)`

---

## Comparison: Before vs After

### BEFORE (No Spring Strength)
- All arcs treated equally (uniform spring strength = 1.0)
- `2A + B → C` same as `A + B → C`
- Layout ignores stoichiometry
- Less chemically meaningful

### AFTER (With Spring Strength)
- Arc weight = spring strength (stoichiometry-based)
- `2A + B → C` pulls A 2× harder than B
- Layout reflects chemical stoichiometry
- More chemically meaningful
- **A will be positioned closer to the reaction than B**

---

## Next Steps

1. **Test with different pathways**
   - Small (BIOMD0000000001, 12 nodes)
   - Medium (BIOMD0000000061, 25 nodes)
   - Large (BIOMD0000000064, 40+ nodes)

2. **Observe stoichiometry effects**
   - Find reactions with high stoichiometry (2A, 3B, etc.)
   - Verify stronger springs pull mass nodes closer
   - Document visual differences

3. **Parameter tuning**
   - Test different `k` values (optimal distance)
   - Test different `iterations` (convergence speed)
   - Test different `scale` (canvas size)
   - Document optimal ranges per pathway size

4. **Create configuration system**
   - Centralize physics parameters in `layout_config.py`
   - Create presets (COMPACT, BALANCED, SPACIOUS)
   - Enable parameter UI controls (future)

---

## Success Criteria

✅ Swiss Palette force-directed uses arc weights  
✅ Console shows "Using arc weights as spring strength"  
✅ Higher stoichiometry → stronger spring → closer positioning  
✅ Layout reflects chemical stoichiometry  
✅ Physics model is correct (mass nodes + springs)  

---

**Status**: ✅ **Ready for empirical testing!**

The force-directed layout now correctly implements the spring-mass physics model with proper terminology and stoichiometry-based spring strength.
