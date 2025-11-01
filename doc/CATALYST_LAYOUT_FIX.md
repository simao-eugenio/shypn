# Catalyst Layout Fix - Hierarchical Layout Exclusion

**Date:** 2025-01-20  
**Issue:** Layout flattening when KEGG catalyst visibility enabled  
**Status:** ✅ FIXED  

---

## Problem

When enabling "Show catalysts" in KEGG imports, the hierarchical layout algorithm
flattened the network from a clean multi-layer structure to just 3 layers.

### User Observation

> "too many isolated places that flatten the entire hierarchy"  
> "algorithms tries to put places that seams to inputs to the net on top, but catalysts  
> are not inputs places, they are a kind of decoration"

Visual evidence:
- **WITHOUT catalysts:** Clean hierarchical layout with multiple clear layers
- **WITH catalysts:** Only 3 layers (severely flattened)

---

## Root Cause

Catalyst places (enzyme places with test arcs) have:
- **IN-degree = 0** (no incoming arcs)
- **OUT-degree > 0** (test arcs to reactions)

The hierarchical layout algorithm in `src/shypn/edit/graph_layout/base.py` has this logic:

```python
# Find source nodes (no predecessors)
sources = [n for n in graph.nodes() if graph.in_degree(n) == 0]
```

This treats catalyst places as "source" or "input" nodes and assigns them to **layer 0**.

With many enzyme places at layer 0, the layout algorithm sees the network as having:
- Layer 0: All catalysts + genuine input substrates (TOO MANY NODES)
- Layer 1: First reactions
- Layer 2: Everything else (compressed)

Result: Flattened layout with poor visual hierarchy.

---

## Solution

Exclude catalyst places from hierarchical layout algorithm in two ways:

### 1. Mark Catalyst Places (KEGG Importer)

**File:** `src/shypn/importer/kegg/pathway_converter.py`

When creating enzyme places, mark them with `is_catalyst = True`:

```python
# CRITICAL: Mark as catalyst for layout algorithm exclusion
# Catalysts are NOT input places - they're "decorations" that indicate
# presence/absence of enzymes. Layout algorithms should exclude them
# from dependency graphs to prevent treating them as network inputs.
place.is_catalyst = True  # Direct attribute for fast checking

# Mark as enzyme in metadata
place.metadata['is_enzyme'] = True
place.metadata['is_catalyst'] = True  # Redundant but explicit
```

### 2. Exclude from Layer Assignment (Layout Algorithm)

**File:** `src/shypn/edit/graph_layout/base.py`

Modified `get_layer_assignment()` method:

```python
# Find source nodes (no predecessors)
# CRITICAL: Exclude catalyst places (enzyme places with only test arcs)
# Catalysts are NOT input places - they're decorations showing enzyme presence.
# Including them as sources causes layout flattening (too many layer 0 nodes).
sources = [
    n for n in graph.nodes() 
    if graph.in_degree(n) == 0 and not getattr(n, 'is_catalyst', False)
]
```

And exclude catalysts from influencing transition layer calculation:

```python
# Layer = max(predecessor layers) + 1
# CRITICAL: Exclude catalyst predecessors from layer calculation
# Catalysts shouldn't influence the hierarchical structure
pred_layers = [
    layers.get(pred, 0) 
    for pred in graph.predecessors(successor)
    if not getattr(pred, 'is_catalyst', False)
]
```

Position catalysts AFTER main BFS completes:

```python
# Position catalyst places AFTER main BFS
# Place catalysts at the same layer as the reactions they catalyze
# (or one layer above for visual separation)
for node in graph.nodes():
    if getattr(node, 'is_catalyst', False) and node not in layers:
        # Find the reactions (transitions) this catalyst connects to
        successors = list(graph.successors(node))
        if successors:
            # Position catalyst at same layer as first catalyzed reaction
            # (Test arcs connect catalyst → transition)
            catalyzed_layers = [layers.get(succ, 0) for succ in successors]
            layers[node] = max(catalyzed_layers) if catalyzed_layers else 0
```

---

## Results

### Test Results

```
TEST: Catalyst Exclusion from Layer 0
================================================================================
Layer Assignments:
   Layer 0: Substrate
   Layer 1: Reaction
   Layer 1: Enzyme (CATALYST)  ← Positioned at reaction layer, NOT layer 0
   Layer 2: Product

✓ Catalyst properly excluded from layer 0
✓ Catalyst positioned at same layer as catalyzed reaction
✓ Hierarchical structure preserved

TEST: Multiple Catalysts (No Flattening)
================================================================================
Number of layers: 5 (clean hierarchy)
Without fix would be: 3 layers (flattened due to catalysts at layer 0)

✓ Hierarchical structure preserved (5 layers)
✓ Catalysts positioned at reaction layers
✓ No layout flattening!
```

### Visual Impact

**BEFORE (with catalysts, old code):**
```
Layer 0: S1, E1, E2, E3, E4, E5, ... (many enzyme places!)
Layer 1: R1, I1
Layer 2: R2, R3, R4, P1, P2, P3, ... (everything else compressed)
```
Result: Only 3 layers, poor visual hierarchy

**AFTER (with catalysts, fixed code):**
```
Layer 0: S1
Layer 1: R1, E1
Layer 2: I1
Layer 3: R2, E2
Layer 4: I2
Layer 5: R3, E3
Layer 6: P1
```
Result: Clean hierarchical layout with clear flow, catalysts positioned near reactions

---

## User Guidance

### For KEGG Imports

1. Enable "Show catalysts" checkbox in KEGG Options
2. Import pathway (e.g., hsa00010 - Glycolysis)
3. Apply **Swiss Palette → Layout → Hierarchical**
4. Result: Clean hierarchical layout with enzyme places visible

### For Other Importers

If creating Biological Petri Nets with test arcs, mark catalyst places:

```python
enzyme_place = Place(x, y, id, name)
enzyme_place.is_catalyst = True  # ← Mark for layout exclusion
enzyme_place.metadata['is_enzyme'] = True

# Create test arc (enzyme → reaction)
test_arc = TestArc(enzyme_place, reaction_transition, id, name)
```

---

## Technical Details

### Why Catalysts Are "Decorations"

User insight:
> "catalysts are not inputs places, they are a kind of decoration that states  
> a presence/not presence of catalyses, they must treating differently from  
> input places to the net"

In Biological Petri Nets:
- **Input places:** Network sources, consumed by reactions (e.g., glucose, ATP)
- **Catalyst places:** Enable reactions WITHOUT being consumed (e.g., hexokinase enzyme)

Test arcs (Σ component) model this:
- Check enablement: `enzyme.tokens >= arc.weight`
- Do NOT consume tokens during firing
- Catalyst concentration affects RATE but is NOT depleted

### Layout Algorithm Perspective

Hierarchical layout uses topological sorting to assign layers:
1. Find sources (in-degree = 0) → Layer 0
2. BFS: assign successors to layer = max(predecessor layers) + 1
3. Result: Clean flow from top to bottom

Problem: Catalysts have in-degree = 0 (like sources) but they're NOT sources!

Solution: Explicitly exclude catalysts from source detection, position them
at the same layer as the reactions they catalyze.

---

## Commits

- **64a2c6d:** `fix: Exclude catalyst places from hierarchical layout layer assignment`

---

## Testing

Test file: `test_catalyst_layout_fix.py`

Run: `python3 test_catalyst_layout_fix.py`

Expected output:
```
ALL TESTS PASSED! ✅

Fix verified:
  ✓ Catalyst places excluded from layer 0
  ✓ Catalysts positioned at same layer as catalyzed reactions
  ✓ Hierarchical layout preserved (no flattening)
```

---

## Related Documentation

- `doc/ENZYME_LAYOUT_ISSUE.md` - Original issue analysis
- `doc/CATALYST_VISIBILITY_GUIDE.md` - User guide for catalyst visibility
- `doc/foundation/BIOLOGICAL_PETRI_NET_FORMALIZATION.md` - Test arc formalization

---

## Future Work

1. Add UI option: "Position catalysts above reactions" (offset in Y)
2. Add visual styling: dim enzyme places to emphasize they're decorations
3. Consider other layout algorithms (force-directed, circular) catalyst exclusion
4. Document in user manual: "Understanding Catalyst Visualization"
