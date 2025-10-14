# Force-Directed Testing Flow - ACTUAL IMPLEMENTATION

**Status**: ✅ Implemented  
**Date**: 2025-10-14

---

## Actual Testing Flow

We are using shypn as a **testbed to improve force-directed algorithms** by completely bypassing the SBML import pipeline.

### The Real Flow

```
BIOMD0000000061
    ↓
Fetch (button) ────→ Downloads SBML from BioModels
    ↓
Parse (button) ────→ Creates Petri net with grid layout, loads to canvas
    ↓
Layout (button) ───→ Opens Swiss Palette
    ↓
Force (button) ────→ Applies OUR force-directed algorithm (the one we're testing!)
```

---

## What Happens at Each Step

### 1. **Fetch Button**
- Downloads SBML XML from BioModels
- Stores in memory

### 2. **Parse Button** (Quick Load)
**File**: `src/shypn/helpers/sbml_import_panel.py` line 407

**What it does**:
1. Parse SBML → PathwayData (species, reactions)
2. Use PathwayPostProcessor with grid layout (just to get positions)
3. Convert to Petri net (places, transitions, arcs with weights)
4. Load to canvas

**Result**: Objects on canvas in simple grid arrangement

**Why grid?** Just to get objects on canvas with SOME initial positions. The grid is thrown away immediately.

### 3. **Swiss Palette → Layout → Force Button**
**File**: `src/shypn/edit/graph_layout/force_directed.py`

**What it does**:
1. Build graph from canvas objects (places, transitions, arcs)
2. Add arc weights as edge weights (stoichiometry = spring strength)
3. Call NetworkX `spring_layout()` with our physics parameters
4. Apply new positions to canvas objects

**Result**: Force-directed layout with physics-based positioning

---

## Two SEPARATE Force-Directed Implementations

### ❌ NOT USED: PathwayPostProcessor Force-Directed
**File**: `src/shypn/data/pathway/pathway_postprocessor.py`
- Used by SBML Import button
- Has projection post-processing
- NOT what we're testing

### ✅ TESTING THIS: Swiss Palette Force-Directed  
**File**: `src/shypn/edit/graph_layout/force_directed.py`
- Used by Swiss Palette → Layout → Force
- Pure NetworkX spring_layout
- **THIS is what we modified with arc weights**
- **THIS is what we're testing**

---

## What We Changed (For Testing)

### 1. `src/shypn/edit/graph_layout/engine.py`
**Method**: `build_graph()`

**Change**: Added arc weights when building graph:
```python
# Add springs (arcs) with weight as spring strength
for arc in doc.arcs:
    weight = getattr(arc, 'weight', 1.0)
    graph.add_edge(arc.source, arc.target, weight=weight, obj=arc)
```

### 2. `src/shypn/edit/graph_layout/force_directed.py`
**Method**: `compute()`

**Change**: Detect and use arc weights:
```python
has_weights = any('weight' in graph[u][v] for u, v in graph.edges())

if has_weights:
    layout_params['weight'] = 'weight'
    print(f"🔬 Force-directed: Using arc weights as spring strength")
```

### 3. `src/shypn/helpers/sbml_import_panel.py`
**Method**: `_quick_load_to_canvas()`

**Change**: Auto-load after parse (enable Swiss Palette testing)

---

## Testing Workflow

```bash
# 1. Launch
python3 -m shypn

# 2. In UI: SBML Tab
Click "BioModels" → Search "BIOMD0000000061"
Click "Fetch" (downloads pathway)
Click "Parse" (loads to canvas with grid)

# 3. In UI: Swiss Palette
Click "Swiss Palette" button (toolbar)
Click "Layout" category (bottom)
Click "Force" button
→ Watch console for: "🔬 Force-directed: Using arc weights as spring strength"

# 4. Observe
- Objects rearrange using physics
- Higher stoichiometry arcs pull nodes closer
- All mass nodes repel each other
- System reaches equilibrium
```

---

## Physics Model (What We're Testing)

### Mass Nodes
- **Places** (circles): species in Petri net
- **Transitions** (rectangles): reactions in Petri net
- **Universal repulsion**: ALL mass nodes repel ALL other mass nodes

### Springs
- **Arcs** (arrows): connections in Petri net
- **Spring strength**: arc.weight (stoichiometry from SBML)
- **Selective attraction**: ONLY connected nodes attract

### Example
Reaction: `2A + B → C`

**In Petri net**:
- Place A (mass node)
- Place B (mass node)
- Transition R (mass node)
- Place C (mass node)
- Arc: A → R (spring, weight=2.0)
- Arc: B → R (spring, weight=1.0)
- Arc: R → C (spring, weight=1.0)

**Physics forces**:
- A ↔ B: repel (mass nodes)
- A ↔ R: repel + spring (weight=2.0) → net: strong pull
- B ↔ R: repel + spring (weight=1.0) → net: weak pull
- R ↔ C: repel + spring (weight=1.0) → net: weak pull
- A ↔ C: repel (mass nodes)
- B ↔ C: repel (mass nodes)

**Result**: A ends up CLOSER to R than B (because 2× spring strength)

---

## Why This Testbed Approach?

### Advantages
✅ **Fast iteration**: No SBML import pipeline overhead  
✅ **Pure testing**: Only tests force-directed, nothing else  
✅ **Visual feedback**: See results immediately on canvas  
✅ **Parameter tweaking**: Easy to change k, iterations, scale  
✅ **Real data**: Uses actual biological pathways from BioModels  

### What We're NOT Testing
❌ SBML parsing (already works)  
❌ PathwayPostProcessor (different implementation)  
❌ Projection post-processing (not used)  
❌ Import pipeline (bypassed)  

### What We ARE Testing
✅ Swiss Palette force-directed algorithm  
✅ Arc weight as spring strength  
✅ Mass node repulsion (all-to-all)  
✅ Physics equilibrium convergence  
✅ Visual layout quality  

---

## Next Steps

1. **Test with different pathways**
   - Small (12 nodes)
   - Medium (25 nodes)
   - Large (50+ nodes)

2. **Vary physics parameters**
   - k (optimal distance)
   - iterations (convergence steps)
   - scale (canvas size)

3. **Document findings**
   - What k works best for each size?
   - How many iterations needed?
   - Does stoichiometry effect visible?

4. **Create parameter configuration**
   - Centralized config module
   - Presets (COMPACT, BALANCED, SPACIOUS)
   - UI controls (future)

---

## Summary

**We are NOT testing the SBML import pipeline.**  
**We ARE testing the Swiss Palette force-directed layout algorithm.**  

The testbed workflow is:
1. Load pathway to canvas (any layout)
2. Apply Swiss Palette force-directed
3. Observe and iterate

This is the fastest way to improve the force-directed algorithm!
