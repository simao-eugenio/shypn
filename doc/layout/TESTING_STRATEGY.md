# Testing Strategy: Pure Force-Directed Layout First

**Date**: October 14, 2025  
**Discovery**: Critical insight from user - test pure physics before adding projection complexity

---

## The Problem: Two-Layer Complexity

Current implementation has **two transformation layers**:

```
SBML → Force-Directed (physics) → 2D Projection (geometry) → Canvas
       └─ k, iterations, weights  └─ layers, spacing, centering
```

**Issue**: Can't tell which parameters affect what!
- Is bad layout from wrong `k` or wrong `layer_spacing`?
- Does `threshold` matter if projection re-arranges everything?
- Are edge weights working if layers flatten the graph?

---

## Solution: Isolate and Test Separately

### Phase 1: Pure Force-Directed (NOW) 🎯

**Goal**: See raw physics output without geometric post-processing

```
SBML → Force-Directed (physics) → Canvas (direct)
       └─ Test: k, iterations, threshold, weights
```

**What to observe**:
- ✅ Spring forces (edge attraction)
- ✅ Repulsion forces (node anti-gravity)
- ✅ Edge weight effects (stoichiometry)
- ✅ Convergence behavior (threshold)
- ✅ Initial conditions (seed)

**Without interference from**:
- ❌ Layer clustering (Y-coordinate grouping)
- ❌ Layer flattening (discrete Y values)
- ❌ X normalization (within-layer redistribution)
- ❌ Canvas fitting (offset/scaling)

### Phase 2: Pure Projection (LATER) 🎯

**Goal**: Test projection transforms on already-good layouts

```
Good Force-Directed → Projection (geometry) → Canvas
                      └─ Test: layers, spacing, spiral
```

---

## Implementation Strategy

### 1. Add Pure Force-Directed Mode

**File**: `pathway_postprocessor.py`

```python
def _calculate_force_directed_layout(self, processed_data, apply_projection=True):
    """
    Args:
        apply_projection: If False, use raw NetworkX output (for testing)
    """
    # ... NetworkX spring_layout ...
    
    if not apply_projection:
        # Direct output - no projection post-processing
        processed_data.positions.update(raw_positions)
        processed_data.metadata['layout_type'] = 'force-directed-raw'
        return
    
    # ... projection code ...
```

### 2. Test via Swiss Layout Palette

**User Workflow**:
1. Import SBML pathway (e.g., BIOMD0000000001)
2. Open **Swiss Layout Palette** (if not already accessible)
3. Select **Force-Directed (Raw)** option
4. Adjust sliders:
   - **k**: 0.5 - 5.0
   - **Iterations**: 20 - 200
   - **Threshold**: 1e-8 to 1e-3
   - **Weight Mode**: Uniform / Stoichiometry / Reversibility
5. Click **Apply** → See immediate raw physics effect

**Advantages**:
- ✅ Real-time parameter experimentation
- ✅ Visual feedback loop
- ✅ No projection interference
- ✅ Easy to compare k=1.0 vs k=2.0

### 3. Document Observations

**Create**: `doc/layout/FORCE_DIRECTED_PARAMETER_EFFECTS.md`

Record for each parameter:
- Visual effect (compact/loose, converged/chaotic)
- Optimal ranges for different pathway sizes
- Interaction effects (k × iterations, etc)
- Edge weight impact (stoich=1 vs stoich=5)

---

## Why This Matters

### Scientific Method:
1. **Isolate variables** - Change one thing at a time
2. **Observe effects** - See pure physics behavior
3. **Control baseline** - Raw force-directed as reference
4. **Add complexity** - Then test projection separately

### Practical Benefits:
- **Faster iteration** - No projection overhead during testing
- **Clear causation** - Know which layer causes issues
- **Better defaults** - Tune physics on raw output first
- **Debugging** - Can disable projection to check physics

### Example Debugging Scenario:
```
Problem: "Layout looks wrong after import"

With projection:
  - Is it k=2.0 too high? Or layer_spacing=200 too small?
  - Is convergence failing? Or projection flattening prematurely?
  - Are weights working? Or X-normalization breaking them?
  → Can't tell!

Without projection (raw):
  - See pure spring forces
  - See convergence directly
  - See weight effects immediately
  → Clear diagnosis!
```

---

## Current State Analysis

### What Works:
✅ Force-directed with projection (but coupled)
✅ Edge weights (stoichiometry-based)
✅ Adaptive k/scale/iterations

### What's Missing:
❌ Pure force-directed option (no projection)
❌ Swiss palette for imported SBML
❌ Real-time parameter adjustment UI
❌ Documentation of parameter effects

---

## Testing Protocol

### Test Pathway: BIOMD0000000001 (Repressilator)

**Properties**:
- Small (12 nodes: 6 species + 6 reactions)
- Simple topology (circular regulation)
- Well-studied (known "good" layout exists)

### Test Matrix:

| Test | k | Iterations | Weights | Expected Outcome |
|------|---|------------|---------|------------------|
| Baseline | 1.0 | 50 | Uniform | Circular, compact |
| High k | 3.0 | 50 | Uniform | Loose, spread out |
| Low k | 0.3 | 50 | Uniform | Dense, overlapping |
| More iter | 1.0 | 200 | Uniform | Better convergence |
| Stoich weights | 1.0 | 50 | Stoich | Stronger clustering |
| Low threshold | 1.0 | 50 | Uniform (1e-8) | Tighter positions |

### Success Criteria:
- ✅ Can visually distinguish k=0.5 from k=3.0
- ✅ More iterations → smoother layout
- ✅ Stoichiometry weights → visible clustering
- ✅ Threshold affects final positions
- ✅ No jitter/instability

---

## Implementation Steps

### Step 1: Add Pure Mode Flag ✅
```python
class PathwayPostProcessor:
    def __init__(self, ..., use_raw_force_directed=False):
        self.use_raw_force_directed = use_raw_force_directed
```

### Step 2: Bypass Projection When Flag Set ✅
```python
if self.use_raw_force_directed:
    # Skip projection, use raw NetworkX output
    processed_data.positions.update(positions)
    return
```

### Step 3: Wire Up Swiss Palette (if needed) 🔄
Check if Swiss palette already accessible for imported nets.

### Step 4: Test and Document 📝
- Run tests with different parameters
- Record observations
- Document optimal ranges

---

## After Pure Testing Complete

Once we understand pure force-directed effects:

1. **Return to Projection** with informed parameters
2. **Test projection transforms** separately
3. **Combine optimally** - Good physics + Good geometry
4. **Create presets** based on empirical results

---

## Key Insight

> **"Before you can optimize a pipeline, you must understand each stage independently."**

Current pipeline:
```
[Physics] → [Geometry] → Output
   ↑           ↑
   ?           ?
```

Testing strategy:
```
[Physics] → Output          ← Test first (isolate physics)
              ↓
         [Geometry] → Output ← Test second (isolate geometry)
              ↓
    [Physics + Geometry]    ← Combine with understanding
```

---

## Expected Outcomes

### After Pure Force-Directed Testing:
- 📊 **Parameter sensitivity curves** documented
- 🎯 **Optimal k ranges** for small/medium/large
- 🔢 **Iteration sweet spot** (convergence vs speed)
- ⚖️ **Weight effects** quantified (stoich impact)
- 📏 **Threshold impact** on final precision

### Then Apply to Projection:
- Use **optimal force-directed params** as input
- Test **projection transforms** on good layouts
- Create **combined presets** with both tuned
- Enable **Swiss palette** for live adjustment

---

## Timeline

1. **Add pure mode flag**: 30 min ✅
2. **Test with BIOMD0000000001**: 1 hour 🔄
3. **Document findings**: 30 min 📝
4. **Enable Swiss palette** (if needed): 1 hour 🔄
5. **Return to projection**: After pure testing complete

**Total**: ~3 hours for pure force-directed characterization

---

## Success Definition

We'll know we're ready for projection when we can say:

✅ "k=1.5 with 100 iterations produces optimal spacing for 15-node pathways"  
✅ "Stoichiometry weights improve clustering by 30% visually"  
✅ "Threshold below 1e-6 has no noticeable effect"  
✅ "Edge weights working correctly - 2A shows 2× stronger attraction"

Then we confidently add projection layer knowing physics baseline is solid! 🚀

---

**Next Action**: Implement pure force-directed mode and test with Swiss palette.
