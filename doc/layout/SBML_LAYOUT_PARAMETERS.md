# SBML Import Layout Parameters

## Overview

The SBML Import tab in the Pathway panel now provides full control over layout algorithms and their parameters. Users can choose between automatic selection, hierarchical layout, or force-directed layout, with algorithm-specific parameters exposed in the UI.

## Location

**Pathway Panel → SBML Tab → Import Options → Layout Algorithm**

## Layout Algorithm Options

### 1. Auto (Automatic Selection)

**Description:** The system automatically selects the best layout algorithm based on the pathway structure.

**Decision Logic:**
- **DAG (Directed Acyclic Graph):** → Hierarchical Layout
- **Large cycle (>50% nodes):** → Circular Layout (future)
- **Highly connected (avg degree > 4):** → Force-Directed Layout
- **Default:** → Hierarchical Layout

**Parameters:** None (system chooses optimal parameters)

**Best for:** Most users who want good results without tweaking

---

### 2. Hierarchical (Layered)

**Description:** Top-to-bottom layered layout using the Sugiyama framework. Creates clear directional flow with nodes arranged in horizontal layers.

**Parameters:**

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| **Layer spacing** | Integer | 50-500px | 150px | Vertical distance between layers |
| **Node spacing** | Integer | 50-300px | 100px | Horizontal distance between nodes in same layer |

**Algorithm:** Sugiyama framework
- Phase 1: Layer assignment (longest path method)
- Phase 2: Crossing reduction (barycentric heuristic)
- Phase 3: Coordinate assignment (minimize edge length)

**Best for:**
- Linear pathways (e.g., glycolysis)
- Metabolic flows
- DAGs with clear direction
- Pathways from KEGG/BioModels with hierarchical structure

**Example Settings:**
- **Compact:** layer_spacing=100, node_spacing=80
- **Normal:** layer_spacing=150, node_spacing=100
- **Spacious:** layer_spacing=200, node_spacing=150

---

### 3. Force-Directed (Physics-based)

**Description:** Physics-based simulation using Fruchterman-Reingold algorithm. Treats nodes as charged particles that repel each other, and edges as springs that pull connected nodes together.

**Parameters:**

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| **Iterations** | Integer | 50-1000 | 500 | Number of physics simulation steps (more = better convergence) |
| **Optimal distance (k)** | Float | 0.5-3.0 | 1.5 | Multiplier for target distance between connected nodes (higher = more spread) |
| **Canvas scale** | Integer | 500-5000px | 2000px | Overall size/scale of the layout |

**Physics Model:**

1. **Universal Repulsion (all nodes):**
   - Force: F_repulsion = -k² / distance
   - Every place repels every other place
   - Every transition repels every other transition
   - Cross-repulsion between places and transitions
   - Prevents overlap, creates spacing

2. **Selective Attraction (via edges):**
   - Force: F_spring = k × distance × weight
   - Weight = arc stoichiometry (e.g., 2A → 2× stronger spring)
   - Pulls connected nodes together

3. **Equilibrium:**
   - System converges when forces balance
   - Connected nodes: balance of spring attraction + repulsion
   - Disconnected nodes: only repulsion → maximum separation

**Best for:**
- Complex networks without clear hierarchy
- Highly interconnected pathways
- Circular/cyclic pathways
- Pathways where relationships matter more than flow direction

**Parameter Effects:**

**Iterations:**
- **50-100:** Fast but may not converge (nodes still moving)
- **200-500:** Good balance (recommended)
- **500-1000:** Best convergence but slower

**Optimal distance (k):**
- **0.5-1.0:** Compact layout (nodes closer)
- **1.5:** Balanced (default)
- **2.0-3.0:** Spacious layout (more spread)

**Canvas scale:**
- **500-1000:** Small pathways (<10 nodes)
- **1000-2000:** Medium pathways (10-30 nodes)
- **2000-5000:** Large pathways (>30 nodes)

**Example Settings:**

Small pathway (5-10 nodes):
- iterations=200, k=1.0, scale=1000

Medium pathway (10-30 nodes):
- iterations=500, k=1.5, scale=2000

Large pathway (>30 nodes):
- iterations=800, k=2.0, scale=3000

Dense/hairball layout:
- iterations=1000, k=2.5, scale=4000

---

## Implementation Details

### UI Components

**File:** `ui/panels/pathway_panel.ui`

- `sbml_layout_algorithm_combo`: ComboBoxText with 3 options
- `sbml_auto_params_box`: Information box for Auto mode
- `sbml_hierarchical_params_box`: Parameters for Hierarchical (visible when selected)
- `sbml_force_params_box`: Parameters for Force-Directed (visible when selected)

**Dynamic Visibility:** Parameter boxes show/hide based on selected algorithm.

### Backend Processing

**File:** `src/shypn/data/pathway/pathway_postprocessor.py`

**Classes Modified:**
- `PathwayPostProcessor.__init__`: Added `layout_type` and `layout_params` parameters
- `LayoutProcessor.__init__`: Added `layout_type` and `layout_params` parameters
- `LayoutProcessor.process()`: Respects user-selected algorithm and parameters

**Flow:**
1. User selects algorithm in UI
2. `SBMLImportPanel._import_pathway_background()` reads values from spin buttons
3. Creates `layout_params` dictionary with algorithm-specific parameters
4. Passes to `PathwayPostProcessor(layout_type='...', layout_params={...})`
5. `LayoutProcessor` uses parameters to configure algorithm

**Force-Directed Parameters:**
```python
layout_params = {
    'iterations': 500,        # From sbml_iterations_spin
    'k_multiplier': 1.5,      # From sbml_k_factor_spin
    'scale': 2000.0          # From sbml_canvas_scale_spin
}
```

**Hierarchical Parameters:**
```python
layout_params = {
    'layer_spacing': 150.0,   # From sbml_layer_spacing_spin
    'node_spacing': 100.0     # From sbml_node_spacing_spin
}
```

### NetworkX Integration

Force-Directed layout uses NetworkX's `spring_layout`:

```python
import math
import networkx as nx

# Calculate k from scale and node count
area = scale * scale
k = math.sqrt(area / num_nodes) * k_multiplier

# Run simulation
positions = nx.spring_layout(
    graph,
    k=k,                    # Optimal distance
    iterations=iterations,  # Simulation steps
    scale=scale,           # Canvas size
    weight='weight',       # Use arc stoichiometry
    seed=42                # Reproducible
)
```

## Testing Workflow

### Test Hierarchical Layout

1. Open Pathway Panel → SBML tab
2. Fetch BIOMD0000000061 (glycolysis pathway)
3. Set Layout Algorithm = "Hierarchical (Layered)"
4. Try different spacings:
   - layer_spacing=100, node_spacing=80 (compact)
   - layer_spacing=200, node_spacing=150 (spacious)
5. Parse → Import to Canvas
6. Observe: Linear top-to-bottom flow, clear layers

### Test Force-Directed Layout

1. Fetch BIOMD0000000061
2. Set Layout Algorithm = "Force-Directed (Physics-based)"
3. Try different parameters:
   - iterations=200, k=1.0, scale=1000 (compact, fast)
   - iterations=500, k=1.5, scale=2000 (balanced)
   - iterations=800, k=2.5, scale=3000 (spacious, slow)
4. Parse → Import to Canvas
5. Observe: Natural clustering, balanced spacing

### Test Auto Selection

1. Fetch different pathways
2. Set Layout Algorithm = "Auto (Automatic Selection)"
3. Import and observe which algorithm was chosen
4. Check console for: "Using hierarchical layout" or "Using force-directed layout"

## Known Issues & Limitations

1. **NetworkX Required:** Force-directed layout requires NetworkX. If not installed, falls back to hierarchical.

2. **Large Pathways:** Force-directed with >50 nodes can be slow with high iterations. Consider:
   - Reduce iterations to 200-300
   - Use hierarchical instead

3. **Parameter Ranges:** Hardcoded min/max values in UI:
   - If you need values outside ranges, edit `pathway_panel.ui` adjustments

4. **No Real-time Preview:** Parameters apply on import, not live preview. To test different parameters, re-import the pathway.

## Future Enhancements

1. **Circular Layout:** Add as 4th option for cyclic pathways
2. **Parameter Presets:** Add "Compact/Balanced/Spacious" preset buttons
3. **Live Preview:** Show layout preview before importing
4. **Algorithm Recommendations:** Show "Recommended" badge on best algorithm for current pathway
5. **Parameter Tooltips:** Add more detailed tooltips with examples

## Related Documentation

- `doc/layout/FORCE_DIRECTED_LAYOUT.md` - Force-directed algorithm details
- `doc/layout/HIERARCHICAL_LAYOUT.md` - Hierarchical algorithm details
- `src/shypn/edit/graph_layout/` - Swiss Palette layout algorithms (for post-import adjustments)

## Change Log

**October 14, 2025:**
- Added layout algorithm selector to SBML import panel
- Exposed algorithm-specific parameters (spacing, iterations, k, scale)
- Updated `PathwayPostProcessor` to respect user-selected algorithms
- Dynamic UI: parameter boxes show/hide based on selection
- Backward compatible: defaults to Auto mode (existing behavior)
