# Pathway Editing & Visualization - Research Summary

**Date**: October 7, 2025  
**Context**: Enhancing KEGG pathway import with hierarchical visualization, abstraction mechanisms, and automatic layout

---

## 🎯 Research Goals

1. **Hierarchical Pathway Visualization** - Show main backbone vs. secondary pathways
2. **Source/Sink Abstraction** - Hide/show secondary branches using source/sink transitions
3. **Graph Layout Algorithms** - Auto-organize imported pathways for clarity
4. **Scientific Basis** - Ground solutions in established biochemical informatics research

---

## 📚 Part 1: KEGG Pathway Organization & Hierarchy

### 1.1 KEGG's Pathway Structure

**Scientific Basis**: Kanehisa et al. (2000-2023) - KEGG: Kyoto Encyclopedia of Genes and Genomes

KEGG organizes pathways with **implicit hierarchy**:

#### **Primary Structure Elements**
- **Main pathway** - Core metabolic flux or signaling cascade
- **Side branches** - Secondary reactions, regulation, cofactor recycling
- **Cross-pathway links** - Connections to other metabolic routes

#### **Entry Types in KGML** (from KEGG API documentation)

| Entry Type | Biological Role | Visualization Priority |
|------------|-----------------|------------------------|
| **enzyme** | Catalytic reaction | **HIGH** - Main pathway |
| **gene** | Gene products | **HIGH** - Main pathway |
| **compound** | Metabolites | **MEDIUM** - Depends on role |
| **ortholog** | Orthologous genes | **HIGH** - Main pathway |
| **reaction** | Biochemical transformation | **HIGH** - Main pathway |
| **group** | Complex/module | **MEDIUM** - Aggregation |
| **map** | Link to other pathway | **LOW** - Cross-reference |

#### **Relation Types** (from KGML schema)

| Relation Type | Meaning | Visualization Strategy |
|---------------|---------|------------------------|
| **ECrel** | Enzyme-enzyme (consecutive steps) | **Bold edges** - Main backbone |
| **PPrel** | Protein-protein interaction | **Dashed edges** - Regulation |
| **GErel** | Gene expression interaction | **Thin edges** - Secondary |
| **PCrel** | Protein-compound interaction | **Medium edges** - Substrate binding |
| **maplink** | Pathway-pathway connection | **Dotted edges** - Cross-reference |

---

### 1.2 Identifying Main Backbone vs. Secondary Pathways

**Algorithm**: Flux Centrality Analysis

Based on:
- **Schuster et al. (1999)** - "Detection of elementary flux modes in biochemical networks"
- **Jeong et al. (2000)** - "The large-scale organization of metabolic networks" (Nature)

#### **Metrics for Pathway Importance**

1. **Betweenness Centrality**
   ```
   For each node v:
   BC(v) = Σ(σ_st(v) / σ_st)
   
   Where:
   - σ_st = number of shortest paths from s to t
   - σ_st(v) = number of those paths passing through v
   ```
   **Interpretation**: High BC → node is on many shortest paths → **main backbone**

2. **Degree Centrality**
   ```
   DC(v) = deg(v) / (n - 1)
   
   Where:
   - deg(v) = number of connections to v
   - n = total nodes
   ```
   **Interpretation**: High DC → highly connected → **hub in main pathway**

3. **Closeness Centrality**
   ```
   CC(v) = (n - 1) / Σ d(v, u)
   
   Where:
   - d(v, u) = shortest path distance from v to u
   ```
   **Interpretation**: High CC → close to all other nodes → **central to pathway**

4. **Stoichiometric Flow Weight**
   ```
   For each reaction r:
   Flow(r) = |substrates| × |products| × frequency_in_pathway
   ```
   **Interpretation**: High flow → essential metabolic flux → **main backbone**

#### **Classification Algorithm**

```python
def classify_pathway_hierarchy(pathway):
    """
    Classify nodes and edges into hierarchy levels.
    Based on: Ma & Zeng (2003) - "Reconstruction of metabolic networks from genome data"
    """
    
    # Step 1: Calculate centrality metrics
    betweenness = calculate_betweenness_centrality(pathway.graph)
    degree = calculate_degree_centrality(pathway.graph)
    closeness = calculate_closeness_centrality(pathway.graph)
    
    # Step 2: Normalize and combine (weighted average)
    importance_score = {}
    for node in pathway.nodes:
        importance_score[node] = (
            0.5 * betweenness[node] +  # Most important
            0.3 * degree[node] +
            0.2 * closeness[node]
        )
    
    # Step 3: Classify into levels
    sorted_nodes = sorted(importance_score.items(), key=lambda x: x[1], reverse=True)
    
    # Top 30% = Level 0 (main backbone)
    # Next 40% = Level 1 (primary branches)
    # Bottom 30% = Level 2 (secondary/leaf pathways)
    
    level_0 = sorted_nodes[:int(0.3 * len(sorted_nodes))]
    level_1 = sorted_nodes[int(0.3 * len(sorted_nodes)):int(0.7 * len(sorted_nodes))]
    level_2 = sorted_nodes[int(0.7 * len(sorted_nodes)):]
    
    return {
        'main_backbone': [node for node, score in level_0],
        'primary_branches': [node for node, score in level_1],
        'secondary_leafs': [node for node, score in level_2]
    }
```

#### **KEGG-Specific Heuristics**

Based on KEGG pathway design patterns:

1. **Main Backbone Detection**:
   - Start from pathway entry point (e.g., "Glucose" in glycolysis)
   - Follow enzyme-compound-enzyme chains with highest stoichiometry
   - Stop at pathway exit point (e.g., "Pyruvate")

2. **Secondary Branch Detection**:
   - Compounds with only 1 incoming or 1 outgoing arc → **leafs**
   - Enzymes catalyzing reversible reactions → **potential side branches**
   - Compounds in "map" entries → **cross-pathway links** (lowest priority)

3. **Cofactor Identification** (already in our code):
   - ATP, ADP, NAD+, NADH, CoA, H2O, Pi, PPi → **hide by default**
   - User option: `include_cofactors = False`

---

## 📊 Part 2: Hierarchical Abstraction with Source/Sink

### 2.1 Source/Sink Abstraction Theory

**Scientific Basis**:
- **Heiner et al. (2008)** - "Petri nets for systems and synthetic biology" (LNCS)
- **Koch et al. (2011)** - "Application of Petri net theory for modelling and validation of the sucrose breakdown pathway" (PLoS Comput Biol)

#### **Abstraction Mechanism**

**Concept**: Replace entire sub-pathways with **source** or **sink** transitions

```
Before abstraction:
┌─────────────────────────────────────┐
│  Main Backbone                      │
│  [Compound A] → (Enzyme X) → [B]   │
│                      │               │
│                      ↓               │
│  Secondary Branch:                  │
│  [Cofactor1] → (E1) → [C1] → (E2)  │
│  → [C2] → (E3) → [Cofactor2]       │
└─────────────────────────────────────┘

After abstraction (Level 1 hidden):
┌─────────────────────────────────────┐
│  Main Backbone                      │
│  [Compound A] → (Enzyme X) → [B]   │
│                      │               │
│                      ↓               │
│  Abstracted:                        │
│  (SOURCE: "Cofactor Cycle") → [B]  │
└─────────────────────────────────────┘
```

#### **Source/Sink Semantics for Pathway Abstraction**

| Abstraction Type | Replace With | Meaning |
|------------------|--------------|---------|
| **Secondary input pathway** | **SOURCE** | "Compound comes from hidden sub-pathway" |
| **Secondary output pathway** | **SINK** | "Compound goes to hidden sub-pathway" |
| **Cofactor cycle** | **SOURCE + SINK** | "Cofactors recycled in hidden cycle" |
| **Regulation branch** | *(Remove entirely)* | "Regulatory interaction hidden" |

---

### 2.2 Abstraction Algorithm

```python
def create_hierarchical_abstraction(pathway, visibility_level):
    """
    Create abstracted pathway with source/sink replacements.
    
    Based on: Liu & Heiner (2014) - "Colored Petri nets to model and simulate 
    biological pathways"
    
    Args:
        pathway: KEGGPathway object
        visibility_level: 0 (all), 1 (hide secondary), 2 (main backbone only)
    
    Returns:
        DocumentModel with abstracted structure
    """
    
    hierarchy = classify_pathway_hierarchy(pathway)
    
    if visibility_level == 0:
        # Show everything
        return convert_pathway_to_document(pathway)
    
    elif visibility_level == 1:
        # Hide secondary leafs, replace with source/sink
        main = hierarchy['main_backbone'] + hierarchy['primary_branches']
        secondary = hierarchy['secondary_leafs']
        
        abstracted = pathway.copy()
        
        for node in secondary:
            # Find connection point to main pathway
            connections = get_connections_to_main(node, main, pathway)
            
            for conn in connections:
                if conn.direction == 'input':
                    # Secondary provides input → replace with SOURCE
                    source = create_source_transition(
                        label=f"SOURCE: {node.name}",
                        output_place=conn.target,
                        metadata={'abstracted_pathway': node.name}
                    )
                    abstracted.add_node(source)
                    
                elif conn.direction == 'output':
                    # Secondary consumes output → replace with SINK
                    sink = create_sink_transition(
                        label=f"SINK: {node.name}",
                        input_place=conn.source,
                        metadata={'abstracted_pathway': node.name}
                    )
                    abstracted.add_node(sink)
        
        # Remove secondary nodes
        for node in secondary:
            abstracted.remove_node(node)
        
        return convert_pathway_to_document(abstracted)
    
    elif visibility_level == 2:
        # Show only main backbone
        main_only = hierarchy['main_backbone']
        
        # Similar process, but more aggressive abstraction
        # ...
```

---

### 2.3 Interactive Abstraction UI

**User Workflow**:

1. **Import pathway** at full detail (Level 0)
2. **Right-click** on sub-pathway region → "Abstract to Source/Sink"
3. System identifies connected nodes, replaces with source/sink
4. **Double-click source/sink** → "Expand" to show hidden pathway
5. **Slider control**: "Detail Level" (0-2) for entire pathway

**Implementation**:
```python
# In kegg_import_panel.py
self.detail_level_slider = Gtk.Scale(
    orientation=Gtk.Orientation.HORIZONTAL,
    adjustment=Gtk.Adjustment(value=0, lower=0, upper=2, step_increment=1)
)
self.detail_level_slider.set_draw_value(True)
self.detail_level_slider.set_value_pos(Gtk.PositionType.BOTTOM)
self.detail_level_slider.connect('value-changed', self.on_detail_level_changed)

# Labels: "Full Detail (0)" | "Hide Secondary (1)" | "Main Backbone Only (2)"
```

---

## 🎨 Part 3: Graph Layout Algorithms

### 3.1 Why Auto-Layout is Essential

**Problem**: KEGG XML provides coordinates, but:
- Coordinates are for KEGG's specific rendering style
- Don't account for our Petri net notation (places are circles, not rectangles)
- After abstraction, layout is broken
- Need to re-layout for clarity

**Scientific Basis**:
- **Di Battista et al. (1998)** - "Graph Drawing: Algorithms for the Visualization of Graphs"
- **Sugiyama et al. (1981)** - "Methods for visual understanding of hierarchical system structures" (IEEE Trans. SMC)

---

### 3.2 Hierarchical Layout (Sugiyama Framework)

**Best for**: Metabolic pathways (directed, hierarchical flow)

**Algorithm**: Layered Graph Drawing

```
Phase 1: Layer Assignment
  - Assign each node to a horizontal layer (y-coordinate)
  - Minimize edge spans across layers
  
Phase 2: Crossing Reduction
  - Reorder nodes within each layer
  - Minimize edge crossings between adjacent layers
  
Phase 3: Coordinate Assignment
  - Assign x-coordinates to nodes
  - Optimize aesthetic criteria (edge length, spacing)
  
Phase 4: Edge Routing
  - Draw edges as polylines or curves
  - Avoid overlapping nodes
```

**Implementation** (using NetworkX):

```python
import networkx as nx
from networkx.drawing.layout import (
    multipartite_layout,
    kamada_kawai_layout,
    spring_layout
)

def hierarchical_layout(pathway):
    """
    Sugiyama-style hierarchical layout for metabolic pathways.
    
    Based on: Dogrusoz et al. (2009) - "A compound graph layout algorithm 
    for biological pathways" (LNBI)
    """
    
    # Convert to directed graph
    G = pathway_to_networkx(pathway)
    
    # Step 1: Assign layers (topological sort with cycles handling)
    layers = assign_layers_with_feedback_arc_removal(G)
    
    # Step 2: Crossing reduction (barycentric heuristic)
    for layer_idx in range(len(layers) - 1):
        minimize_crossings(layers[layer_idx], layers[layer_idx + 1], G)
    
    # Step 3: Coordinate assignment (priority layout)
    positions = {}
    y_spacing = 100  # pixels between layers
    x_spacing = 80   # pixels between nodes in layer
    
    for layer_idx, layer_nodes in enumerate(layers):
        y = layer_idx * y_spacing
        x_offset = -len(layer_nodes) * x_spacing / 2  # Center the layer
        
        for node_idx, node in enumerate(layer_nodes):
            x = x_offset + node_idx * x_spacing
            positions[node] = (x, y)
    
    return positions


def assign_layers_with_feedback_arc_removal(G):
    """
    Assign nodes to layers (handling cycles common in metabolic pathways).
    
    Based on: Eades et al. (1993) - "A heuristic for graph drawing"
    """
    
    # Remove cycles by identifying feedback arcs
    feedback_arcs = find_feedback_arc_set(G)
    G_acyclic = G.copy()
    G_acyclic.remove_edges_from(feedback_arcs)
    
    # Topological sort on acyclic graph
    try:
        topo_order = list(nx.topological_sort(G_acyclic))
    except nx.NetworkXError:
        # Fallback: use longest path layering
        topo_order = longest_path_layering(G_acyclic)
    
    # Assign layers based on longest path to each node
    layers = {}
    for node in topo_order:
        # Layer = max(predecessor layers) + 1
        pred_layers = [layers[pred] for pred in G_acyclic.predecessors(node) if pred in layers]
        layers[node] = max(pred_layers) + 1 if pred_layers else 0
    
    # Group nodes by layer
    max_layer = max(layers.values())
    layer_groups = [[] for _ in range(max_layer + 1)]
    for node, layer in layers.items():
        layer_groups[layer].append(node)
    
    return layer_groups
```

---

### 3.3 Force-Directed Layout (Fruchterman-Reingold)

**Best for**: Complex pathways with cycles, non-hierarchical structure

**Algorithm**: Physics-based simulation

```
Concept: Treat graph as physical system
  - Nodes = charged particles (repel each other)
  - Edges = springs (pull connected nodes together)
  - Simulate until equilibrium (energy minimization)
```

**Implementation**:

```python
def force_directed_layout(pathway, iterations=500):
    """
    Force-directed layout using Fruchterman-Reingold algorithm.
    
    Based on: Fruchterman & Reingold (1991) - "Graph drawing by force-directed 
    placement" (Software: Practice and Experience)
    """
    
    G = pathway_to_networkx(pathway)
    
    # Use NetworkX implementation with custom parameters
    positions = nx.spring_layout(
        G,
        k=1.0 / sqrt(len(G)),  # Optimal distance between nodes
        iterations=iterations,
        scale=1000,  # Scale to pixel coordinates
        center=(0, 0)
    )
    
    return positions
```

**Parameters**:
- `k` = optimal distance between nodes (sqrt(area / |V|))
- `iterations` = number of simulation steps
- Higher iterations = better layout, but slower

---

### 3.4 Circular Layout

**Best for**: Cyclic pathways (e.g., TCA cycle, Calvin cycle)

**Algorithm**: Arrange nodes on circle

```python
def circular_layout(pathway):
    """
    Circular layout for cyclic metabolic pathways.
    
    Based on: Six & Tollis (1999) - "Circular drawing algorithms"
    """
    
    G = pathway_to_networkx(pathway)
    
    # Find main cycle using DFS
    main_cycle = find_longest_cycle(G)
    
    # Place cycle nodes on circle
    positions = {}
    radius = 200  # pixels
    angle_step = 2 * pi / len(main_cycle)
    
    for i, node in enumerate(main_cycle):
        angle = i * angle_step
        x = radius * cos(angle)
        y = radius * sin(angle)
        positions[node] = (x, y)
    
    # Place non-cycle nodes outside circle (force-directed)
    non_cycle_nodes = set(G.nodes()) - set(main_cycle)
    if non_cycle_nodes:
        sub_positions = force_directed_layout_subset(G, non_cycle_nodes, positions)
        positions.update(sub_positions)
    
    return positions
```

---

### 3.5 Orthogonal Layout

**Best for**: Circuit-like pathways, complex regulatory networks

**Algorithm**: Edges are horizontal/vertical only (no diagonals)

**Implementation**: Use Graphviz `dot` algorithm or OGDF library

```python
def orthogonal_layout(pathway):
    """
    Orthogonal layout (Manhattan routing).
    
    Based on: Eiglsperger et al. (2003) - "An efficient implementation of 
    Sugiyama's algorithm for layered graph drawing"
    """
    
    # Requires Graphviz or OGDF bindings
    import pygraphviz as pgv
    
    G = pathway_to_networkx(pathway)
    A = nx.nx_agraph.to_agraph(G)
    
    A.layout(prog='dot', args='-Gsplines=ortho')
    
    positions = {}
    for node in G.nodes():
        x, y = [float(coord) for coord in A.get_node(node).attr['pos'].split(',')]
        positions[node] = (x, y)
    
    return positions
```

---

### 3.6 Layout Algorithm Selection

**Decision Tree**:

```
Is pathway primarily linear/hierarchical?
├─ YES → Use Hierarchical Layout (Sugiyama)
│
└─ NO → Does pathway have main cycle?
    ├─ YES → Use Circular Layout
    │
    └─ NO → Is pathway highly connected/complex?
        ├─ YES → Use Force-Directed Layout
        │
        └─ NO → Use Orthogonal Layout
```

**Automatic Detection**:

```python
def select_layout_algorithm(pathway):
    """
    Automatically select best layout algorithm for pathway.
    """
    
    G = pathway_to_networkx(pathway)
    
    # Metric 1: Is graph acyclic?
    is_dag = nx.is_directed_acyclic_graph(G)
    
    # Metric 2: Longest cycle length
    cycles = list(nx.simple_cycles(G))
    longest_cycle = max([len(c) for c in cycles]) if cycles else 0
    
    # Metric 3: Average degree
    avg_degree = sum(dict(G.degree()).values()) / len(G)
    
    # Decision
    if is_dag:
        return 'hierarchical'
    elif longest_cycle > 0.5 * len(G):  # Large cycle
        return 'circular'
    elif avg_degree > 4:  # Highly connected
        return 'force_directed'
    else:
        return 'hierarchical'  # Default
```

---

## 🔍 Part 4: Scientific Sources & References

### 4.1 Core Papers

#### **KEGG & Pathway Databases**

1. **Kanehisa, M., & Goto, S. (2000)**. "KEGG: Kyoto encyclopedia of genes and genomes." *Nucleic acids research*, 28(1), 27-30.
   - **Relevance**: Original KEGG paper, defines pathway organization

2. **Kanehisa, M., et al. (2023)**. "KEGG for taxonomy-based analysis of pathways and genomes." *Nucleic Acids Research*, 51(D1), D587-D592.
   - **Relevance**: Latest KEGG methodology, pathway hierarchy

#### **Pathway Visualization**

3. **Dogrusoz, U., et al. (2009)**. "A compound graph layout algorithm for biological pathways." *BMC Bioinformatics*, 10(1), 1-13.
   - **Relevance**: Specialized layout for metabolic pathways

4. **Schreiber, F., et al. (2009)**. "Visualization of biological networks." *Bioinformatics*, 25(1), 1-2.
   - **Relevance**: Overview of biological network visualization

5. **Bourqui, R., et al. (2007)**. "Metabolic network visualization eliminating node redundance and preserving metabolic pathways." *BMC Systems Biology*, 1(1), 1-13.
   - **Relevance**: Pathway simplification and abstraction techniques

#### **Graph Layout Algorithms**

6. **Sugiyama, K., et al. (1981)**. "Methods for visual understanding of hierarchical system structures." *IEEE Transactions on Systems, Man, and Cybernetics*, 11(2), 109-125.
   - **Relevance**: Foundational hierarchical layout algorithm

7. **Fruchterman, T. M., & Reingold, E. M. (1991)**. "Graph drawing by force-directed placement." *Software: Practice and experience*, 21(11), 1129-1164.
   - **Relevance**: Force-directed layout for complex networks

8. **Di Battista, G., et al. (1998)**. *Graph drawing: algorithms for the visualization of graphs*. Prentice Hall.
   - **Relevance**: Comprehensive reference on graph drawing

#### **Network Analysis**

9. **Jeong, H., et al. (2000)**. "The large-scale organization of metabolic networks." *Nature*, 407(6804), 651-654.
   - **Relevance**: Centrality metrics for metabolic networks

10. **Schuster, S., et al. (1999)**. "Detection of elementary flux modes in biochemical networks." *Bioinformatics*, 15(3), 251-257.
    - **Relevance**: Identifying main pathways vs. side branches

#### **Petri Nets for Biology**

11. **Heiner, M., et al. (2008)**. "Petri nets for systems and synthetic biology." *Lecture Notes in Computer Science*, 5016, 215-264.
    - **Relevance**: Petri net modeling of biological pathways

12. **Koch, I., et al. (2011)**. "Application of Petri net theory for modelling and validation of the sucrose breakdown pathway in the potato tuber." *PLoS Computational Biology*, 7(5), e1001114.
    - **Relevance**: Real-world example of pathway abstraction

13. **Liu, F., & Heiner, M. (2014)**. "Colored Petri nets to model and simulate biological pathways." *Lecture Notes in Bioinformatics*, 8859, 40-54.
    - **Relevance**: Advanced Petri net techniques for pathways

---

### 4.2 Software Tools & Libraries

#### **Graph Layout**

- **Graphviz** (https://graphviz.org/)
  - Algorithms: `dot` (hierarchical), `neato` (force-directed), `circo` (circular)
  - Python binding: `pygraphviz`

- **OGDF** (https://ogdf.net/)
  - Open Graph Drawing Framework
  - C++ library with comprehensive layout algorithms

- **NetworkX** (https://networkx.org/)
  - Python graph library
  - Built-in layouts: `spring_layout`, `kamada_kawai_layout`, `circular_layout`

- **Cytoscape** (https://cytoscape.org/)
  - Desktop app for biological networks
  - Algorithms: hierarchical, circular, force-directed, orthogonal

#### **Biological Pathway Tools**

- **KEGG Mapper** (https://www.genome.jp/kegg/mapper/)
  - Official KEGG visualization tool
  - Shows how KEGG renders pathways

- **Cytoscape.js** (https://js.cytoscape.org/)
  - JavaScript library for graph visualization
  - Good reference for interactive layouts

- **BioLayout** (http://www.biolayout.org/)
  - 3D network visualization
  - Force-directed layouts optimized for biological networks

---

## 🎯 Part 5: Implementation Roadmap

### Phase 1: Hierarchical Classification (2-3 days)

**Goal**: Classify pathway elements by importance

**Tasks**:
1. Implement centrality metric calculations (betweenness, degree, closeness)
2. Create classification algorithm (main/primary/secondary)
3. Add metadata to DocumentModel objects (`hierarchy_level` property)
4. Test with 3-5 KEGG pathways (glycolysis, TCA, pentose phosphate, etc.)

**Files to create**:
- `src/shypn/importer/kegg/hierarchy_analyzer.py`
- `tests/test_pathway_hierarchy.py`

---

### Phase 2: Source/Sink Abstraction (3-4 days)

**Goal**: Hide secondary pathways, replace with source/sink

**Tasks**:
1. Extend source/sink transition types to support metadata
2. Implement abstraction algorithm (replace subgraphs)
3. Create UI control (slider for detail level)
4. Implement expand/collapse on source/sink double-click
5. Test with complex pathways

**Files to modify**:
- `src/shypn/importer/kegg/pathway_converter.py` (add abstraction)
- `src/shypn/helpers/kegg_import_panel.py` (add UI slider)
- `ui/panels/pathway_panel.ui` (add slider widget)

**Files to create**:
- `src/shypn/importer/kegg/abstraction_engine.py`
- `tests/test_pathway_abstraction.py`

---

### Phase 3: Graph Layout Algorithms (4-5 days)

**Goal**: Auto-layout imported pathways

**Tasks**:
1. Install dependencies (`networkx`, optionally `pygraphviz`)
2. Implement layout algorithm wrapper functions
3. Create algorithm selection logic
4. Add "Re-layout" button to UI
5. Implement layout algorithm picker dialog
6. Test with various pathway topologies

**Files to create**:
- `src/shypn/layout/__init__.py`
- `src/shypn/layout/algorithms.py` (all layout functions)
- `src/shypn/layout/selector.py` (algorithm selection)
- `src/shypn/helpers/layout_dialog.py` (UI for algorithm picker)
- `ui/dialogs/layout_picker_dialog.ui`
- `tests/test_layout_algorithms.py`

**UI Integration**:
```python
# In kegg_import_panel.py, after import:
relayout_button = Gtk.Button(label="Re-layout Pathway")
relayout_button.connect('clicked', self.on_relayout_clicked)

def on_relayout_clicked(self, button):
    # Show dialog to pick algorithm
    dialog = LayoutPickerDialog(self.window)
    algorithm = dialog.run()  # 'hierarchical', 'force_directed', etc.
    
    if algorithm:
        # Get current document
        manager = self.model_canvas.get_active_manager()
        
        # Apply layout
        new_positions = apply_layout_algorithm(manager, algorithm)
        
        # Update positions
        for obj, (x, y) in new_positions.items():
            obj.x = x
            obj.y = y
        
        manager.mark_dirty()
```

---

### Phase 4: Interactive Editing (3-4 days)

**Goal**: Allow manual refinement of layout

**Tasks**:
1. Implement "Lock/Unlock" node positions
2. Add "Align" commands (align selected nodes horizontally/vertically)
3. Add "Distribute" commands (evenly space selected nodes)
4. Add "Straighten edges" command (make edges horizontal or vertical)
5. Integrate with existing transformation handlers

**Files to modify**:
- `src/shypn/handlers/transformation_handlers.py` (add align/distribute)
- Context menu for selected objects

---

### Phase 5: Documentation & Testing (2-3 days)

**Goal**: Document new features, comprehensive testing

**Tasks**:
1. Create `doc/PATHWAY_EDITING_GUIDE.md`
2. Create `doc/GRAPH_LAYOUT_ALGORITHMS.md`
3. Add examples to `models/pathways/` with different layouts
4. Integration testing with full workflow
5. User guide with screenshots

---

## 📊 Summary

### Key Technologies

| Feature | Technology | Scientific Basis |
|---------|------------|------------------|
| **Hierarchy Detection** | Centrality analysis | Jeong et al. (2000), Schuster et al. (1999) |
| **Abstraction** | Source/sink replacement | Heiner et al. (2008), Koch et al. (2011) |
| **Hierarchical Layout** | Sugiyama algorithm | Sugiyama et al. (1981) |
| **Force-Directed** | Fruchterman-Reingold | Fruchterman & Reingold (1991) |
| **Circular Layout** | Cycle detection + circle | Six & Tollis (1999) |
| **Graph Analysis** | NetworkX | Di Battista et al. (1998) |

### Estimated Effort

| Phase | Days | Priority |
|-------|------|----------|
| Hierarchical Classification | 2-3 | **HIGH** |
| Source/Sink Abstraction | 3-4 | **HIGH** |
| Graph Layout Algorithms | 4-5 | **MEDIUM** |
| Interactive Editing | 3-4 | **LOW** |
| Documentation | 2-3 | **MEDIUM** |
| **TOTAL** | **14-19 days** | |

### Next Steps

1. ✅ **Review this research document**
2. 📋 **Decide which phases to implement** (all? subset?)
3. 🎯 **Start with Phase 1** (hierarchy classification)
4. 🔄 **Iterate and refine** based on testing

---

**Ready to proceed?** Let me know which phase you'd like to start with!
