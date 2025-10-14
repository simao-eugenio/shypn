# Force-Directed Layout: Place-to-Place Repulsion Fix

## Problem

Users reported that places are not repelling other places in force-directed layout. They clump together instead of spreading out with proper spacing.

## Root Cause Analysis

### Issue 1: k Parameter Normalization (FIXED)

**Original Code:**
```python
layout_params = {
    'k': k / scale,  # BUG: Dividing by scale!
    ...
}
```

**Problem:** Dividing k by scale made it extremely small:
- k = 442 (auto-calculated for good spacing)
- scale = 2000
- k passed to NetworkX = 442 / 2000 = **0.221**

This tiny k value caused weak repulsion, making nodes clump together.

**Fix:** Let NetworkX auto-calculate k, use scale for output sizing:
```python
layout_params = {
    'k': None,  # Let NetworkX use default: 1/sqrt(n)
    'scale': scale * k_multiplier,  # Control spacing via scale
    ...
}
```

### Issue 2: DiGraph vs Graph Conversion

**Status:** Already implemented correctly, but needs verification.

**Code:**
```python
if isinstance(graph, nx.DiGraph):
    undirected_graph = graph.to_undirected()
    print("✓ Converted DiGraph → Graph for universal repulsion")
```

**Theory:** 
- DiGraph: Only path-connected nodes repel
- Graph: ALL nodes repel universally

**Reality Check:** NetworkX spring_layout seems to handle repulsion in both cases (based on test), but conversion is still good practice.

## Changes Made

### 1. Fixed k Parameter Calculation (force_directed.py)

**Before:**
```python
# Calculate k
area = scale * scale
k = math.sqrt(area / graph.number_of_nodes()) * k_multiplier

# Pass to NetworkX (WRONG!)
layout_params = {
    'k': k / scale,  # Tiny value!
    ...
}
```

**After:**
```python
# Let user control spacing via k_multiplier
if k is None:
    adjusted_scale = scale * k_multiplier
    print(f"Spacing multiplier = {k_multiplier}x → adjusted_scale = {adjusted_scale:.1f}px")

scale_to_use = adjusted_scale if k is None else k

# Pass to NetworkX (CORRECT!)
layout_params = {
    'k': None,  # Auto: 1/sqrt(n)
    'scale': scale_to_use,  # Controls output size
    ...
}
```

**Effect:**
- k_multiplier = 0.5 → compact layout (scale × 0.5)
- k_multiplier = 1.0 → normal layout (scale × 1.0)
- k_multiplier = 2.0 → spacious layout (scale × 2.0)
- k_multiplier = 3.0 → very spacious layout (scale × 3.0)

### 2. Enhanced Diagnostic Logging

Added verification that conversion is working:
```python
print(f"Output graph type = {type(undirected_graph).__name__}")
print(f"Output is Graph? {isinstance(undirected_graph, nx.Graph)}")
print(f"Output is DiGraph? {isinstance(undirected_graph, nx.DiGraph)}")
```

Expected output:
```
🔬 Force-directed: Input graph type = DiGraph
🔬 Force-directed: ✓ Converted DiGraph → Graph for universal repulsion
🔬 Force-directed: Output graph type = Graph
🔬 Force-directed: Output is Graph? True
🔬 Force-directed: Output is DiGraph? False
```

## Testing

### Test 1: Verify Conversion Happens

Run shypn and apply force-directed layout:
```
1. Fetch BIOMD0000000061
2. Parse
3. Swiss Palette → Layout → Force-Directed
4. Check console for conversion messages
```

Expected console output:
```
🔬 Force-directed: Input graph type = DiGraph
🔬 Force-directed: ✓ Converted DiGraph → Graph for universal repulsion
🔬 Force-directed: Output is Graph? True
```

### Test 2: Verify Spacing Works

**Test A: Compact (k_multiplier=0.5)**
```
1. SBML Tab → Force-Directed params
2. Set: k=0.5, iterations=500, scale=2000
3. Apply layout
4. Result: Nodes closer together
```

**Test B: Spacious (k_multiplier=2.5)**
```
1. SBML Tab → Force-Directed params
2. Set: k=2.5, iterations=500, scale=2000
3. Apply layout
4. Result: Nodes spread out more
```

Console should show:
```
🔬 Force-directed: Spacing multiplier = 2.5x → adjusted_scale = 5000.0px
🔬 Force-directed: NetworkX params: iterations=500, scale=5000.0, k=auto
```

### Test 3: Visual Verification

After applying force-directed layout with k=2.0:

**Expected behavior:**
- Places spread out from each other
- Transitions spread out from each other
- No overlapping nodes
- Connected nodes pulled together by springs
- Disconnected nodes pushed apart by repulsion

**Problem indicators:**
- Multiple places clumped in same location
- Places overlapping each other
- All places in center, transitions on outside (or vice versa)

## NetworkX spring_layout Behavior

### Parameters

- **k**: Optimal distance between nodes in normalized [0,1] space
  - If None: k = 1/sqrt(n) (automatic)
  - Controls repulsion strength
  
- **scale**: Output coordinate scale
  - Scales the final [0,1] layout to [-scale, scale]
  - Does NOT affect physics, only output size
  
- **iterations**: Number of force-calculation steps
  - More iterations = better convergence
  - 50-100: Fast but may not settle
  - 200-500: Good balance
  - 500-1000: Slow but thorough

- **weight**: Edge attribute for spring strength
  - Uses arc.weight (stoichiometry) for variable spring force
  
### Force Model

NetworkX spring_layout implements Fruchterman-Reingold:

1. **Repulsive force** between ALL node pairs:
   ```
   F_repel = -k² / distance
   ```

2. **Attractive force** between connected nodes:
   ```
   F_attract = distance² / k
   ```

3. **With weights:**
   ```
   F_attract = distance² / k × weight
   ```

**Key insight:** Repulsion happens between ALL nodes, regardless of graph type (DiGraph vs Graph), in NetworkX's implementation. However, conversion to Graph is still recommended for clarity and potential future changes.

## Expected Results

### Before Fix

**Symptom:** Places clump together
**Console:** `k = 0.221` (extremely small)
**Cause:** k divided by scale, causing weak repulsion

### After Fix

**Symptom:** Places spread out properly
**Console:** `scale = 5000.0` (k_multiplier=2.5 × scale=2000)
**Cause:** Proper use of scale parameter for spacing control

## Troubleshooting Guide

### Problem: Nodes still clumping

**Possible causes:**

1. **k_multiplier too small**
   - Solution: Increase to 2.0 or 3.0
   - Check console: "Spacing multiplier = X"

2. **Iterations too low**
   - Solution: Increase to 500-1000
   - Low iterations = not enough time to spread

3. **Scale too small**
   - Solution: Increase base scale to 3000-5000
   - Check console: "adjusted_scale = X"

4. **Too many nodes**
   - Large pathways (>50 nodes) need more space
   - Solution: scale=5000, k_multiplier=3.0

### Problem: Nodes too spread out

**Cause:** k_multiplier or scale too large

**Solution:**
- Reduce k_multiplier to 0.5-1.0
- Or reduce base scale to 1000-1500

### Problem: Nodes overlapping

**Causes:**
1. Iterations too low (hasn't converged)
2. Canvas rendering issue (not layout issue)
3. Node sizes too large relative to spacing

**Solutions:**
1. Increase iterations to 800-1000
2. Check node rendering sizes
3. Increase scale

## Files Modified

1. **src/shypn/edit/graph_layout/force_directed.py**
   - Fixed k parameter calculation
   - Use scale × k_multiplier for spacing control
   - Enhanced diagnostic logging
   - Let NetworkX auto-calculate k

2. **scripts/test_place_repulsion.py** (NEW)
   - Test script verifying DiGraph vs Graph behavior
   - Measures actual distances between nodes

## Documentation

- `doc/SWISS_PALETTE_SBML_PARAMETER_INTEGRATION.md` - Parameter flow
- `doc/SBML_LAYOUT_PARAMETERS.md` - UI parameter details
- `doc/layout/FORCE_DIRECTED_LAYOUT.md` - Algorithm details (if exists)

## Summary

The main fix was **removing the k/scale division** that was making k extremely small. Now we:
1. Let NetworkX calculate k automatically (k = 1/sqrt(n))
2. Control spacing via `scale × k_multiplier`
3. Verify DiGraph → Graph conversion happens
4. Log all parameters for debugging

This ensures proper universal repulsion where all nodes repel each other, with user-controllable spacing.
