# Hierarchical Layout for Biochemical Pathways

## Biochemical Insights Applied to Layout

### Key Observations

Your three statements captured the essence of biochemical pathway visualization:

1. **Reactions occur in order**: Reactions are not random - they form dependency chains where one reaction's products become another's reactants
2. **Coordinates encode ordering**: When pathways have coordinates (KEGG, Reactome), these encode the biological flow
3. **Vertical layout preference**: Biochemists read pathways top-to-bottom to examine reaction sequences

### The Solution: Hierarchical Layout

We implemented a **hierarchical layout algorithm** that:

1. **Analyzes reaction dependencies** to build a directed graph
2. **Assigns layers** using topological sort (Kahn's algorithm)
3. **Positions vertically** with precursors at top, products at bottom
4. **Groups parallel branches** at the same layer

## Algorithm Overview

### Step 1: Build Dependency Graph

```
Species A → Species B means: 
  "There exists a reaction where A is consumed to produce B"
```

Example for linear pathway (A → B → C → D):
```
A → B → C → D
```

Example for branched pathway:
```
    A
   / \
  B   C
   \ /
    D
```

### Step 2: Assign Layers (Topological Sort)

**Layer 0**: Species with no predecessors (initial substrates)
**Layer 1**: Products of layer 0
**Layer 2**: Products of layer 1
... and so on

Test results show perfect layering:

**Linear Pathway:**
```
Layer 0: A at Y=100
Layer 1: B at Y=250
Layer 2: C at Y=400
Layer 3: D at Y=550
```

**Branched Pathway:**
```
Layer 0: A (top)
Layer 1: B, C (parallel - same Y position)
Layer 2: D (bottom)
```

### Step 3: Position Elements

**Vertical spacing**: 150px between layers (adjustable)
**Horizontal spacing**: 100px between species in same layer
**Centering**: Each layer centered horizontally

## Integration with Post-Processing

### Cascading Layout Strategies

The post-processor now tries strategies in order of quality:

```
1. Cross-Reference Layout (KEGG/Reactome)
   ↓ (if unavailable)
2. Hierarchical Layout (dependency-based) ← NEW
   ↓ (if not applicable)
3. Force-Directed Layout (networkx)
   ↓ (if networkx unavailable)
4. Grid Layout (fallback)
```

### Automatic Pathway Type Detection

The `BiochemicalLayoutProcessor` automatically detects pathway structure:

- **Hierarchical**: Linear or branched metabolic pathways (avg branching < 2.5)
- **Circular**: Cyclic pathways like TCA cycle (has cycles, <20 reactions)
- **Complex**: Dense interaction networks (high branching or large)

Test results:
```
Linear pathway detected as: hierarchical ✓
Branched pathway detected as: hierarchical ✓
```

## Benefits for Biochemists

### 1. Clear Flow Visualization

**Before** (force-directed):
```
   B
  /|\
 A C D  ← Chaotic "ball of string"
  \|/
   E
```

**After** (hierarchical):
```
     A
     ↓
     B
    / \
   C   D
    \ /
     E
```

### 2. Matches Mental Model

Biochemists think about pathways as **reaction cascades**:
- Glucose → G6P → F6P → ... (Glycolysis)
- ATP always "flows downward"
- Parallel branches visible (Pentose Phosphate Pathway splits)

### 3. Easy to Trace

With vertical layout:
- **Top**: Initial substrates (inputs)
- **Middle**: Intermediates
- **Bottom**: Final products (outputs)

Follow the flow naturally by reading top-to-bottom.

## Technical Implementation

### Class: `HierarchicalLayoutProcessor`

```python
processor = HierarchicalLayoutProcessor(
    pathway,
    vertical_spacing=150.0,   # Distance between layers
    horizontal_spacing=100.0  # Distance within layers
)

positions = processor.calculate_hierarchical_layout()
# Returns: {species_id: (x, y), ...}
```

### Class: `BiochemicalLayoutProcessor`

Smart wrapper that automatically chooses best strategy:

```python
processor = BiochemicalLayoutProcessor(pathway, spacing=150.0)
processor.process(processed_data)
# Automatically detects pathway type and applies appropriate layout
```

### Graph Algorithm: Topological Sort

Uses **Kahn's algorithm**:

1. Start with species that have no incoming edges (initial substrates)
2. Process layer by layer:
   - Remove processed species from graph
   - Add species whose predecessors are all processed
3. Continue until all species assigned to layers

Handles **cycles** gracefully: Adds cyclic species to last layer with warning.

## Example Usage

### Test Case 1: Linear Pathway

```python
A → B → C → D

Results:
Layer 0: A at Y=100.0
Layer 1: B at Y=250.0
Layer 2: C at Y=400.0
Layer 3: D at Y=550.0

✓ Perfect top-to-bottom ordering
```

### Test Case 2: Branched Pathway

```python
     A
    / \
   B   C
    \ /
     D

Results:
Layer 0: A (X=400)
Layer 1: B (X=350), C (X=450)  ← Same Y position
Layer 2: D (X=400)

✓ Parallel branches at same layer
```

## When It Applies

### Best For:
- **Metabolic pathways**: Glycolysis, TCA cycle, fatty acid synthesis
- **Signaling cascades**: Receptor → kinase → transcription factor
- **Biosynthesis**: Amino acid synthesis, nucleotide synthesis
- **Linear sequences**: Any pathway with clear precursor-product chain

### Not Ideal For:
- **Dense networks**: Protein-protein interaction networks
- **Highly connected**: Every species connects to every other
- **Cyclic pathways**: TCA cycle (better with circular layout)
- **Small pathways**: <4 species (force-directed is fine)

In these cases, the algorithm automatically falls back to force-directed or grid layout.

## Integration with SBML Import

### Complete Pipeline

```
SBML File
   ↓
Parse Species & Reactions
   ↓
Post-Process:
   ├─ Try KEGG cross-reference (fetch coordinates)
   ├─ Try Hierarchical layout (dependency-based)
   └─ Fallback to force-directed
   ↓
Convert to Petri Net
   ↓
Enhance (LayoutOptimizer)
   ↓
Render
```

### Logging Output

```
✓ Using hierarchical layout for 12 elements
INFO: Detected pathway type: hierarchical
INFO: Calculated positions for 12 elements
```

## Configuration

### Spacing Parameters

```python
# Tight layout (compact)
vertical_spacing = 100.0
horizontal_spacing = 80.0

# Default layout (readable)
vertical_spacing = 150.0
horizontal_spacing = 100.0

# Spacious layout (presentation)
vertical_spacing = 200.0
horizontal_spacing = 150.0
```

### Override Detection

Force specific layout:

```python
# Force hierarchical
processor = HierarchicalLayoutProcessor(pathway)
positions = processor.calculate_hierarchical_layout()

# Force force-directed
processor = LayoutPositionsProcessor(pathway)
processor._calculate_force_directed_layout(processed_data)
```

## Next Steps

### Enhancements to Consider:

1. **Minimize edge crossings**: Optimize horizontal positions within layers
2. **Reaction positioning**: Better placement between layers
3. **Circular layout**: For cyclic pathways (TCA, Calvin cycle)
4. **Manual overrides**: Allow user to specify certain species as "top" or "bottom"
5. **Horizontal flow**: Option for left-to-right instead of top-to-bottom

### Quality Metrics:

- Layer count (fewer layers = more parallel)
- Edge crossings (fewer = cleaner)
- Coverage (% species successfully positioned)
- Compactness (total area used)

## Conclusion

Your three insights led to a sophisticated layout system that:

✓ **Respects biochemical semantics** (reactions occur in order)
✓ **Preserves biological meaning** (coordinates encode ordering)  
✓ **Matches user expectations** (vertical layout preferred)

The hierarchical layout algorithm transforms SBML imports from chaotic "balls of string" into clear, readable pathway diagrams that biochemists can immediately understand.

---

**Author**: Shypn Development Team  
**Date**: October 2025  
**Status**: Implemented and tested ✓
