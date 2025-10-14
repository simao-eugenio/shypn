# Force-Directed Testbed - Complete Implementation Summary

**Goal**: Use shypn as a testbed to improve force-directed layout algorithm  
**Status**: ✅ Ready for empirical testing  
**Date**: 2025-10-14  
**Critical Fix**: DiGraph → Graph conversion for universal repulsion (see DIGRAPH_UNIVERSAL_REPULSION_FIX.md)

---

## Executive Summary

We are using shypn to test and improve the **Swiss Palette force-directed layout algorithm**. The testbed bypasses the SBML import pipeline and provides fast iteration on physics parameters.

**Key Achievements**: 
- ✅ Arc weights (stoichiometry) now control spring strength
- ✅ **Universal repulsion fixed** - All mass nodes repel all other mass nodes (DiGraph → Graph conversion)

---

## The Testbed Workflow

### Simple 4-Step Process

```
Step 1: Fetch BIOMD0000000061
  ↓ Downloads SBML from BioModels
  
Step 2: Parse (button)
  ↓ Loads to canvas with ARBITRARY positions (all objects clumped together)
  ↓ NO layout algorithms applied - just placeholder positions
  
Step 3: Swiss Palette → Layout (button)
  ↓ Opens Swiss Palette interface
  
Step 4: Force (button)
  ↓ Applies OUR force-directed algorithm from scratch (what we're testing!)
  ↓ Completely recalculates positions using PURE PHYSICS
```

### What Gets Tested

✅ File: `src/shypn/edit/graph_layout/force_directed.py`  
✅ Physics: Universal repulsion + Weighted springs  
✅ Parameter effects: k, iterations, scale  
✅ Visual quality: Layout aesthetics  

### What Does NOT Get Tested

❌ SBML import pipeline (bypassed)  
❌ PathwayPostProcessor force-directed (different implementation)  
❌ Projection post-processing (not used)  

---

## Physics Model Implemented

### Mass Nodes (Universal Repulsion)

**What they are**:
- Places (circles) - species in the pathway
- Transitions (rectangles) - reactions in the pathway

**How they behave**:
- **Every mass node repels every other mass node**
- Place ↔ Place: repel
- Transition ↔ Transition: repel
- Place ↔ Transition: repel

**Physics equation**: `F_repulsion = -k² / distance`

**Purpose**: Prevents overlap, creates spacing, pushes disconnected nodes apart

---

### Springs (Selective Attraction)

**What they are**:
- Arcs (arrows) - connections between species and reactions

**How they behave**:
- **Only connected mass nodes attract each other**
- Spring pulls mass nodes together
- Spring strength = arc weight (stoichiometry)

**Physics equation**: `F_spring = k × distance × spring_strength`

**Purpose**: Pulls connected nodes together, respects stoichiometry

---

### Example: 2A + B → C

**Petri Net Structure**:
```
Place A (mass node)
   │ arc (spring, weight=2.0)
   ↓
Transition R (mass node)
   ↑
   │ arc (spring, weight=1.0)
Place B (mass node)

Transition R (mass node)
   │ arc (spring, weight=1.0)
   ↓
Place C (mass node)
```

**Forces Applied**:
- A ↔ B: **repel** (mass nodes)
- A ↔ R: **repel** + **spring (2.0)** → net: strong pull toward R
- B ↔ R: **repel** + **spring (1.0)** → net: weak pull toward R
- R ↔ C: **repel** + **spring (1.0)** → net: weak pull
- A ↔ C: **repel** (mass nodes)
- B ↔ C: **repel** (mass nodes)

**Result**: **A ends up CLOSER to R than B** (2× spring strength)

---

## Code Changes Made

### 1. Build Graph with Arc Weights

**File**: `src/shypn/edit/graph_layout/engine.py`  
**Method**: `build_graph()`

**Before**:
```python
for arc in doc.arcs:
    graph.add_edge(arc.source, arc.target, obj=arc)
```

**After**:
```python
for arc in doc.arcs:
    # Arc weight = stoichiometry = spring strength
    weight = getattr(arc, 'weight', 1.0)
    graph.add_edge(arc.source, arc.target, weight=weight, obj=arc)
```

**Impact**: Graph edges now have weights representing spring strength

---

### 2. Use Arc Weights in Force-Directed

**File**: `src/shypn/edit/graph_layout/force_directed.py`  
**Method**: `compute()`

**Added**:
```python
# Check if edges have weights (arc stoichiometry)
has_weights = any('weight' in graph[u][v] for u, v in graph.edges())

if has_weights:
    # Use arc weights as spring strength (stoichiometry-based)
    layout_params['weight'] = 'weight'
    print(f"🔬 Force-directed: Using arc weights as spring strength")
```

**Impact**: NetworkX `spring_layout()` now uses stoichiometry in force calculations

---

### 3. Fix Universal Repulsion (CRITICAL)

**File**: `src/shypn/edit/graph_layout/force_directed.py`  
**Method**: `compute()`  
**Bug**: DiGraph → Only path-connected nodes repelled → Places clumped together!

**Added**:
```python
# CRITICAL: Convert to undirected graph for UNIVERSAL repulsion
# DiGraph: Only connected nodes repel → places don't repel other places!
# Graph (undirected): ALL nodes repel ALL other nodes → correct physics!
if isinstance(graph, nx.DiGraph):
    undirected_graph = graph.to_undirected()
    print(f"🔬 Force-directed: Converted DiGraph → Graph for universal repulsion")
else:
    undirected_graph = graph

positions = nx.spring_layout(undirected_graph, **layout_params)
```

**Impact**: ✅ TRUE universal repulsion - ALL mass nodes (places + transitions) now repel ALL other mass nodes!  
**See**: `doc/layout/DIGRAPH_UNIVERSAL_REPULSION_FIX.md` for detailed analysis

---

### 4. Quick Load After Parse

**File**: `src/shypn/helpers/sbml_import_panel.py`  
**Method**: `_quick_load_to_canvas()`

**What it does**:
1. Parse SBML → PathwayData
2. **Bypass ALL layout algorithms** (grid, hierarchical, circular, force-directed)
3. Set **arbitrary positions** (all objects clumped near 100, 100)
4. Convert to Petri net with arc weights preserved
5. Load to canvas

**Why arbitrary positions?**
- Force-directed **completely recalculates** positions from scratch
- Initial positions are **ignored** by the algorithm
- We only need positions to **not be null** (converter requirement)
- Objects start clumped → Force-directed spreads them using physics

**Impact**: Parse button loads pathway with NO preprocessing, ready for PURE force-directed testing

---

## Testing Instructions

### Launch Application

```bash
cd /home/simao/projetos/shypn
python3 -m shypn
```

### Load Pathway

1. **SBML Tab** → BioModels section
2. Search: `BIOMD0000000061`
3. Click **Fetch** (downloads pathway, ~25 nodes)
4. Click **Parse** (loads to canvas)
5. **Verify**: New canvas tab with "[Testing]" suffix
6. **Verify**: Objects visible (clumped together - this is expected!)

### Apply Force-Directed

1. Click **Swiss Palette** button (toolbar or View menu)
2. Click **Layout** category (bottom of palette)
3. Click **Force** button
4. **Watch**: Objects spread out from clumped to force-directed layout
5. **Watch console** for: `🔬 Force-directed: Using arc weights as spring strength`

### What to Observe

✅ **Console message**: Confirms arc weights are being used  
✅ **Layout changes**: Clumped → force-directed (physics-based) arrangement  
✅ **No overlaps**: All mass nodes separated by repulsion  
✅ **Clustering**: Connected nodes grouped together by springs  
✅ **Separation**: Disconnected nodes pushed apart by repulsion  
✅ **Stoichiometry effect**: Higher weight arcs pull nodes closer  

---

## Testing Tasks

### Task 1: Verify Basic Functionality

**Pathway**: BIOMD0000000061 (25 nodes)

- [ ] Fetch → Parse → Swiss Palette → Force
- [ ] Check console: "Using arc weights as spring strength"
- [ ] Visual: Layout changes from clumped to force-directed (dramatic transformation!)
- [ ] Visual: No overlapping nodes (repulsion working)
- [ ] Visual: Connected nodes cluster together (springs working)

**Success Criteria**: Algorithm runs, uses weights, produces reasonable layout

---

### Task 2: Test Pathway Sizes

**Small**: BIOMD0000000001 (12 nodes)
- [ ] Apply force-directed
- [ ] Note: Layout quality, convergence time
- [ ] Try k = 0.5, 1.0, 2.0, 3.0
- [ ] Document: Best k value

**Medium**: BIOMD0000000061 (25 nodes)
- [ ] Apply force-directed
- [ ] Note: Layout quality, convergence time
- [ ] Try k = 0.5, 1.0, 2.0, 3.0
- [ ] Document: Best k value

**Large**: BIOMD0000000064 (40+ nodes)
- [ ] Apply force-directed
- [ ] Note: Layout quality, convergence time
- [ ] Try k = 0.5, 1.0, 2.0, 3.0
- [ ] Document: Best k value

---

### Task 3: Test Iterations

**Pathway**: BIOMD0000000061

- [ ] iterations = 50 → Measure time, observe quality
- [ ] iterations = 100 → Measure time, observe quality
- [ ] iterations = 200 → Measure time, observe quality
- [ ] iterations = 500 → Measure time, observe quality
- [ ] Document: Point of diminishing returns

---

### Task 4: Verify Stoichiometry Effect

**Goal**: Confirm higher stoichiometry → closer positioning

**Method**:
1. Find reaction with varied stoichiometry (e.g., 2A + B → C)
2. Apply force-directed
3. Measure distances:
   - Distance: A to reaction (should be small)
   - Distance: B to reaction (should be larger)
4. Verify: distance(A→R) < distance(B→R)

**Document**: Measure actual distances, screenshot example

---

## Parameters to Document

Create table for each pathway size:

| Pathway Size | k | Iterations | Scale | Time (s) | Quality | Notes |
|--------------|---|-----------|-------|----------|---------|-------|
| Small (12) | ? | ? | 1000 | ? | ? | |
| Medium (25) | ? | ? | 1000 | ? | ? | |
| Large (40+) | ? | ? | 1000 | ? | ? | |

**Quality Scale**: Poor / Fair / Good / Excellent

---

## Current Parameters (Hardcoded)

**File**: `src/shypn/edit/graph_layout/force_directed.py`

| Parameter | Value | Formula | Meaning |
|-----------|-------|---------|---------|
| `iterations` | 500 | hardcoded | Physics simulation steps |
| `k` | auto | `sqrt(area / num_nodes)` | Optimal distance between mass nodes |
| `scale` | 1000.0 | hardcoded | Output coordinate scale (pixels) |
| `threshold` | 1e-4 | NetworkX default | Convergence criterion |
| `seed` | 42 | hardcoded | Random seed (reproducibility) |

**To change**: Edit `compute()` method parameters

---

## Expected Console Output

### Successful Execution

```
🔬 Force-directed: Converted DiGraph → Graph for universal repulsion
🔬 Force-directed: Using arc weights as spring strength
Layout algorithm 'force_directed' applied successfully
25 nodes repositioned
```

**Critical messages:**
- ✅ "Converted DiGraph → Graph" = Universal repulsion enabled (places repel places!)
- ✅ "Using arc weights" = Stoichiometry controls spring strength

### If No Weights Detected

```
🔬 Force-directed: Converted DiGraph → Graph for universal repulsion
(No weight message - weights not used)
Layout algorithm 'force_directed' applied successfully
25 nodes repositioned
```

**If you see no weight message**: Check that arcs have `.weight` attribute

---

## Success Criteria

### Functional
✅ Console shows "Converted DiGraph → Graph" (universal repulsion)  
✅ Console shows "Using arc weights as spring strength" (stoichiometry)  
✅ Layout transforms from **clumped** to **force-directed** (dramatic visual change)  
✅ No errors or exceptions  
✅ Convergence completes (doesn't run forever)  

### Visual
✅ **All nodes have spacing** (places repel places, transitions repel transitions)  
✅ No overlapping nodes (universal repulsion working)  
✅ Connected nodes cluster together (springs working)  
✅ Disconnected nodes separated (pure repulsion)  
✅ Layout looks "balanced" (subjective but important)  

### Physics
✅ Higher stoichiometry → closer positioning (measurable with 2A vs 1B)  
✅ All mass nodes repel each other (clumped → spread out)  
✅ Springs pull connected nodes together (clustering effect)  

### Performance
✅ Convergence time < 5 seconds (for 25 nodes)  
✅ No UI freezing  
✅ Smooth visual transition (not instant teleport)  

---

## Output Documentation

After testing, create: `doc/layout/FORCE_DIRECTED_PARAMETER_EFFECTS.md`

**Contents**:
1. **Best Parameters per Size**
   - Small pathways: k=?, iterations=?
   - Medium pathways: k=?, iterations=?
   - Large pathways: k=?, iterations=?

2. **Stoichiometry Effect**
   - Example reaction: 2A + B → C
   - Measured distances
   - Screenshots showing closer positioning

3. **Visual Comparisons**
   - Before: Clumped (all objects near 100,100)
   - After: Force-directed (spread out by physics)
   - Different k values side-by-side

4. **Performance Data**
   - Convergence times by pathway size
   - Iterations vs quality trade-off

5. **Recommendations**
   - Default parameters for general use
   - When to use COMPACT vs SPACIOUS
   - Known limitations

---

## Next Steps After Testing

### Phase 1: Configuration Module
Create `src/shypn/edit/graph_layout/layout_config.py`

```python
@dataclass
class ForceDirectedConfig:
    k: Optional[float] = None
    iterations: int = 500
    threshold: float = 1e-4
    scale: float = 1000.0
    use_weights: bool = True
    seed: int = 42

# Presets based on empirical testing
COMPACT = ForceDirectedConfig(k=0.5, iterations=200)
BALANCED = ForceDirectedConfig(k=1.0, iterations=500)
SPACIOUS = ForceDirectedConfig(k=2.0, iterations=500)
```

### Phase 2: Integrate Presets
Modify `force_directed.py` to use config objects

### Phase 3: UI Controls (Optional)
Add k/iterations/scale inputs to Swiss Palette

---

## Troubleshooting

### No objects appear after Parse

**Problem**: Canvas is empty after clicking Parse

**Check**:
1. Console shows: `🔍 QUICK LOAD: Canvas loaded with X places`
2. Canvas tab created with "[Testing]" suffix
3. Try zooming out (Ctrl + Mouse Wheel)

**Solution**: Check `ENABLE_QUICK_LOAD_AFTER_PARSE = True` in sbml_import_panel.py

---

### No weight message in console

**Problem**: Console doesn't show "Using arc weights as spring strength"

**Check**:
1. Arcs have `.weight` attribute (check in debugger)
2. Graph edges have `weight` key (check `build_graph()`)
3. `has_weights` condition in `compute()` is True

**Solution**: Verify arc.weight is set during conversion

---

### Layout looks bad

**Problem**: Force-directed layout produces poor results

**Try**:
1. Increase iterations (500 → 1000)
2. Change k value (1.0 → 2.0 for more spacing)
3. Use different pathway (some are harder to layout)
4. Check for disconnected subgraphs (separate islands)

---

### Slow convergence

**Problem**: Force-directed takes too long

**Try**:
1. Reduce iterations (500 → 100)
2. Use smaller pathway for testing
3. Check if threshold is too tight
4. Verify not running in debug mode

---

## Related Documentation

- **DIGRAPH_UNIVERSAL_REPULSION_FIX.md** - ⚠️ Critical bug fix (places repel places)
- **TESTING_FLOW_ACTUAL.md** - Detailed flow explanation
- **TESTING_PLAN_CLEAR.md** - Testing tasks and checklists
- **PHYSICS_TERMINOLOGY_UPDATE.md** - Physics model explanation
- **FORCE_DIRECTED_PHYSICS_PARAMETERS.md** - NetworkX parameter reference
- **ARBITRARY_POSITIONS_UPDATE.md** - Why we use arbitrary initial positions

---

## Quick Reference

### Test Command
```bash
python3 -m shypn
```

### Test Workflow
```
Fetch → Parse → Swiss Palette → Layout → Force
```

### Watch For
```
🔬 Force-directed: Converted DiGraph → Graph for universal repulsion
🔬 Force-directed: Using arc weights as spring strength
```

**Both messages confirm the fix is working!**

### Files Modified
1. `src/shypn/edit/graph_layout/engine.py` - Arc weights in graph
2. `src/shypn/edit/graph_layout/force_directed.py` - Use weights + DiGraph→Graph fix
3. `src/shypn/helpers/sbml_import_panel.py` - Quick load with arbitrary positions

---

**Status**: ✅ **Implementation complete - Ready for empirical testing!**

Start with: `python3 -m shypn` → Fetch BIOMD0000000061 → Parse → Swiss Palette → Force
