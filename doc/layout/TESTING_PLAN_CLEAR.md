# Testing Plan - Swiss Palette Force-Directed Algorithm

**Goal**: Use shypn as a testbed to improve force-directed layout algorithm  
**Status**: ✅ Ready for testing  
**Date**: 2025-10-14

---

## Clear Separation

### What We're NOT Testing
❌ SBML import pipeline  
❌ PathwayPostProcessor force-directed  
❌ Projection post-processing  

### What We ARE Testing
✅ **Swiss Palette force-directed algorithm**  
✅ File: `src/shypn/edit/graph_layout/force_directed.py`  
✅ Physics: Arc weights → Spring strength  
✅ Universal repulsion: All mass nodes repel  

---

## Testbed Workflow

```
Step 1: Fetch BIOMD0000000061
  → Downloads SBML from BioModels

Step 2: Parse
  → Loads to canvas with grid layout
  → Just to get objects on canvas

Step 3: Swiss Palette → Layout → Force
  → Applies OUR force-directed algorithm
  → THIS is what we're testing!

Step 4: Observe & Iterate
  → Change parameters
  → Re-apply
  → Document results
```

---

## What We Changed

### 1. Arc Weights as Spring Strength
**File**: `src/shypn/edit/graph_layout/engine.py`
- `build_graph()` now includes `weight=arc.weight` when adding edges
- Stoichiometry becomes spring strength

### 2. Auto-Detect and Use Weights
**File**: `src/shypn/edit/graph_layout/force_directed.py`
- `compute()` checks for edge weights
- If found, passes `weight='weight'` to NetworkX
- Logs: "🔬 Force-directed: Using arc weights as spring strength"

### 3. Quick Load After Parse
**File**: `src/shypn/helpers/sbml_import_panel.py`
- Parse button auto-loads to canvas
- Uses grid layout (just for initial positions)
- Enables Swiss Palette testing

---

## Testing Tasks

### Task 1: Verify It Works
- [ ] Fetch BIOMD0000000061
- [ ] Parse (loads to canvas)
- [ ] Swiss Palette → Force
- [ ] Check console: "Using arc weights as spring strength"
- [ ] Observe: Layout changes from grid to force-directed

### Task 2: Test Small Pathway (12 nodes)
- [ ] Use BIOMD0000000001
- [ ] Apply force-directed
- [ ] Try k = 0.5, 1.0, 2.0, 3.0
- [ ] Document best k value

### Task 3: Test Medium Pathway (25 nodes)
- [ ] Use BIOMD0000000061
- [ ] Apply force-directed
- [ ] Try k = 0.5, 1.0, 2.0, 3.0
- [ ] Document best k value

### Task 4: Test Large Pathway (50+ nodes)
- [ ] Use BIOMD0000000064
- [ ] Apply force-directed
- [ ] Try k = 0.5, 1.0, 2.0, 3.0
- [ ] Document best k value

### Task 5: Test Iterations
- [ ] Same pathway
- [ ] Try iterations = 50, 100, 200, 500
- [ ] Measure convergence time
- [ ] Document diminishing returns point

### Task 6: Verify Stoichiometry Effect
- [ ] Find reaction with 2A or 3B (high stoichiometry)
- [ ] Apply force-directed
- [ ] Measure distance: A to reaction vs B to reaction
- [ ] Verify: Higher stoichiometry → closer distance

---

## Parameters to Document

For each pathway size, document:

| Parameter | Test Values | Best Value | Notes |
|-----------|-------------|------------|-------|
| k | 0.5, 1.0, 2.0, 3.0 | ? | Optimal distance |
| iterations | 50, 100, 200, 500 | ? | Convergence steps |
| scale | 500, 1000, 2000 | ? | Canvas size |

---

## Success Criteria

✅ Console shows "Using arc weights as spring strength"  
✅ Higher stoichiometry → closer positioning (measurable)  
✅ All mass nodes repel (no overlaps)  
✅ Connected nodes cluster together  
✅ Disconnected nodes pushed apart  
✅ Layout looks "good" (subjective)  
✅ Convergence time acceptable (< 5 seconds)  

---

## Output

Create: `doc/layout/FORCE_DIRECTED_PARAMETER_EFFECTS.md`

Document:
- Best k per pathway size
- Best iterations per pathway size
- Visual comparison screenshots
- Stoichiometry effect measurements
- Recommendations for default parameters

---

## Next Phase

After empirical testing:

1. Create `layout_config.py` with parameter presets
2. Define COMPACT, BALANCED, SPACIOUS configs
3. (Optional) Add UI controls for parameters
4. Document final recommendations

---

**Current Status**: ✅ Code ready, waiting for empirical testing

**Test Command**:
```bash
python3 -m shypn
# Then: Fetch → Parse → Swiss Palette → Force
```
