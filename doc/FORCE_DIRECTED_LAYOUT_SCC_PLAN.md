# Force-Directed Layout with SCC-Based Post-Processing: Solar System Architecture

## Executive Summary

This document outlines a comprehensive plan to implement an **auto-layout system** for Petri net models using **force-directed graph algorithms** with a **strongly-connected components (SCC) post-processing step**. The system creates a "solar system" metaphor where:

- **Strong components** act as **gravitational centers** (stars/planets)
- **Peripheral nodes** **orbit** around these centers
- **Hierarchical structure** emerges naturally from component relationships

## 1. Conceptual Foundation

### 1.1 Graph Theory Background

**Strongly Connected Component (SCC):**
- A maximal subgraph where every node can reach every other node
- In Petri nets: cyclical structures (feedback loops, resource cycles)
- Represents **core functional units** of the model

**Force-Directed Layout:**
- Nodes repel each other (coulombic repulsion)
- Edges act as springs (attract connected nodes)
- Iterative simulation until equilibrium
- Results in aesthetically pleasing, symmetric layouts

### 1.2 Solar System Metaphor

```
           Satellite            Satellite
              ↓                    ↓
           Planet ← → Moon      Planet
              ↓                    ↓
    ═════════════════════════════════════
              ⭐ Star (SCC Core) ⭐
    ═════════════════════════════════════
              ↑                    ↑
           Planet              Planet → Moon
              ↑                    ↑
           Satellite            Satellite
```

**Components:**
1. **Stars (SCC cores)**: Largest/most connected SCCs → center of gravity
2. **Planets**: Medium SCCs → orbit stars at fixed radius
3. **Moons**: Small SCCs/single nodes → orbit planets
4. **Satellites**: Peripheral nodes → furthest from center

### 1.3 Why This Approach?

**Benefits:**
- ✅ **Natural Hierarchy**: Important structures naturally gravitate to center
- ✅ **Visual Clarity**: Related components cluster together
- ✅ **Scalability**: Large models decompose into manageable regions
- ✅ **Semantic Meaning**: Layout reflects actual system structure
- ✅ **Aesthetic**: Symmetric, balanced, professional appearance

**Use Cases:**
- Large industrial models (100+ nodes)
- Complex biological pathways
- Multi-level workflows
- System architecture diagrams
- Resource allocation networks

## 2. System Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────┐
│           AutoLayoutManager                      │
│  (Orchestrates entire layout process)            │
└───────┬─────────────────────────────┬───────────┘
        │                             │
        ↓                             ↓
┌─────────────────┐          ┌──────────────────┐
│  GraphAnalyzer  │          │  LayoutEngine    │
│  - Build graph  │          │  - Force-direct  │
│  - Find SCCs    │          │  - Post-process  │
│  - Compute rank │          │  - Apply coords  │
└─────────────────┘          └──────────────────┘
        │                             │
        ↓                             ↓
┌─────────────────┐          ┌──────────────────┐
│  SCCDetector    │          │ ForceSimulator   │
│  (Tarjan/Kosaraju)         │ (Fruchterman-   │
│                 │          │  Reingold)       │
└─────────────────┘          └──────────────────┘
        │                             │
        ↓                             ↓
┌─────────────────┐          ┌──────────────────┐
│ ComponentRanker │          │ OrbitPostProcess │
│ (Assign levels) │          │ (Solar system)   │
└─────────────────┘          └──────────────────┘
```

### 2.2 Class Structure

```python
# Core orchestrator
class AutoLayoutManager:
    """Orchestrates the entire auto-layout process."""
    def __init__(self, document_model: DocumentModel):
        self.document = document_model
        self.graph_analyzer = GraphAnalyzer()
        self.layout_engine = LayoutEngine()
    
    def apply_layout(self) -> None:
        """Main entry point: compute and apply layout."""
        pass

# Graph analysis
class GraphAnalyzer:
    """Analyzes Petri net graph structure."""
    def build_adjacency_list(self, places, transitions, arcs) -> Dict:
        """Convert Petri net to directed graph."""
        pass
    
    def find_strongly_connected_components(self) -> List[SCC]:
        """Detect SCCs using Tarjan's algorithm."""
        pass
    
    def compute_component_hierarchy(self, sccs: List[SCC]) -> ComponentHierarchy:
        """Rank SCCs by importance/connectivity."""
        pass

# SCC representation
class StronglyConnectedComponent:
    """Represents a single SCC."""
    def __init__(self, nodes: List[PetriNetObject]):
        self.nodes = nodes
        self.size = len(nodes)
        self.rank = 0  # Hierarchical level
        self.mass = 0.0  # Gravitational influence
    
    def compute_centroid(self) -> Tuple[float, float]:
        """Calculate geometric center of component."""
        pass

# Layout execution
class LayoutEngine:
    """Executes force-directed layout with SCC post-processing."""
    def __init__(self):
        self.force_simulator = ForceSimulator()
        self.orbit_processor = OrbitPostProcessor()
    
    def compute_layout(self, graph, sccs) -> Dict[int, Tuple[float, float]]:
        """Phase 1: Force-directed layout."""
        pass
    
    def apply_orbital_constraints(self, positions, sccs) -> Dict[int, Tuple[float, float]]:
        """Phase 2: SCC-based orbital refinement."""
        pass

# Force simulation
class ForceSimulator:
    """Implements Fruchterman-Reingold algorithm."""
    def __init__(self):
        self.k = 50.0  # Optimal distance
        self.iterations = 1000
        self.temperature = 100.0
    
    def simulate(self, graph) -> Dict[int, Tuple[float, float]]:
        """Run force-directed simulation."""
        pass

# Orbital post-processing
class OrbitPostProcessor:
    """Applies solar system constraints to layout."""
    def __init__(self):
        self.orbit_spacing = 200.0  # Distance between orbital levels
    
    def assign_orbits(self, positions, sccs) -> Dict[int, Tuple[float, float]]:
        """Reposition nodes in orbital structure."""
        pass
```

## 3. Algorithm Details

### 3.1 Phase 1: Graph Construction

**Input:** Places, Transitions, Arcs (Petri net)
**Output:** Directed graph adjacency list

**Process:**
```python
def build_graph(places, transitions, arcs):
    graph = {}
    
    # All nodes (places + transitions)
    for place in places:
        graph[place.id] = []
    for transition in transitions:
        graph[transition.id] = []
    
    # Edges (arcs)
    for arc in arcs:
        graph[arc.source_id].append(arc.target_id)
    
    return graph
```

**Complexity:** O(V + E) where V = nodes, E = arcs

### 3.2 Phase 2: SCC Detection (Tarjan's Algorithm)

**Algorithm:** Tarjan's strongly connected components
**Complexity:** O(V + E)

**Key Concepts:**
- DFS traversal with discovery/low-link values
- Stack to track current path
- Detect back-edges to identify cycles

**Implementation:**
```python
def tarjan_scc(graph):
    index = 0
    stack = []
    indices = {}
    lowlinks = {}
    on_stack = set()
    sccs = []
    
    def strongconnect(node):
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])
        
        if lowlinks[node] == indices[node]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == node:
                    break
            sccs.append(scc)
    
    for node in graph:
        if node not in indices:
            strongconnect(node)
    
    return sccs
```

### 3.3 Phase 3: Component Ranking

**Objective:** Determine hierarchical importance of each SCC

**Ranking Criteria:**
1. **Size**: Number of nodes in SCC
2. **Connectivity**: Number of edges within SCC
3. **Centrality**: Number of connections to other SCCs
4. **Depth**: Distance from root SCCs (source components)

**Formula:**
```
rank_score = (size_weight * size) + 
             (connectivity_weight * internal_edges) +
             (centrality_weight * external_edges) +
             (depth_penalty * depth_level)

mass = rank_score  // Gravitational influence
```

**Implementation:**
```python
def rank_components(sccs, graph):
    ranked_sccs = []
    
    for scc in sccs:
        size = len(scc.nodes)
        internal_edges = count_internal_edges(scc, graph)
        external_edges = count_external_edges(scc, graph)
        depth = compute_depth(scc, sccs, graph)
        
        rank_score = (
            1.0 * size +
            0.5 * internal_edges +
            0.3 * external_edges -
            0.2 * depth
        )
        
        scc.rank = rank_score
        scc.mass = rank_score  # Gravitational influence
        ranked_sccs.append(scc)
    
    # Sort by rank (highest first)
    ranked_sccs.sort(key=lambda s: s.rank, reverse=True)
    
    return ranked_sccs
```

### 3.4 Phase 4: Force-Directed Layout (Fruchterman-Reingold)

**Algorithm:** Classic force-directed graph drawing
**Complexity:** O(iterations × V²) → can be optimized with spatial indexing

**Forces:**
1. **Repulsive force** (all pairs): F_rep = k² / distance
2. **Attractive force** (connected pairs): F_attr = distance² / k
3. **Temperature cooling**: Gradually reduce movement

**Implementation:**
```python
def fruchterman_reingold(graph, width=2000, height=2000, iterations=1000):
    import math
    import random
    
    # Initialize positions randomly
    positions = {}
    for node in graph:
        positions[node] = (
            random.uniform(0, width),
            random.uniform(0, height)
        )
    
    # Optimal distance
    area = width * height
    k = math.sqrt(area / len(graph))
    
    # Temperature schedule
    t = width / 10.0
    dt = t / (iterations + 1)
    
    for iteration in range(iterations):
        # Calculate repulsive forces
        displacement = {node: (0.0, 0.0) for node in graph}
        
        for v in graph:
            for u in graph:
                if u != v:
                    delta_x = positions[v][0] - positions[u][0]
                    delta_y = positions[v][1] - positions[u][1]
                    distance = math.sqrt(delta_x**2 + delta_y**2) + 0.01
                    
                    # Repulsive force
                    force = k * k / distance
                    displacement[v] = (
                        displacement[v][0] + (delta_x / distance) * force,
                        displacement[v][1] + (delta_y / distance) * force
                    )
        
        # Calculate attractive forces
        for v in graph:
            for u in graph[v]:
                delta_x = positions[v][0] - positions[u][0]
                delta_y = positions[v][1] - positions[u][1]
                distance = math.sqrt(delta_x**2 + delta_y**2) + 0.01
                
                # Attractive force
                force = distance * distance / k
                displacement[v] = (
                    displacement[v][0] - (delta_x / distance) * force,
                    displacement[v][1] - (delta_y / distance) * force
                )
                displacement[u] = (
                    displacement[u][0] + (delta_x / distance) * force,
                    displacement[u][1] + (delta_y / distance) * force
                )
        
        # Limit displacement by temperature and update positions
        for v in graph:
            dx, dy = displacement[v]
            disp_length = math.sqrt(dx**2 + dy**2) + 0.01
            positions[v] = (
                positions[v][0] + (dx / disp_length) * min(disp_length, t),
                positions[v][1] + (dy / disp_length) * min(disp_length, t)
            )
        
        # Cool temperature
        t -= dt
    
    return positions
```

### 3.5 Phase 5: Orbital Post-Processing (Solar System)

**Objective:** Refine layout to create hierarchical orbital structure

**Steps:**
1. Identify the **central SCC** (highest rank)
2. Place central SCC at origin (0, 0)
3. For each SCC level (by rank):
   - Calculate **orbital radius** based on rank
   - Position SCC nodes on orbit at angle θ
   - Preserve internal SCC structure (scale + translate)
4. Adjust peripheral nodes to orbit their parent SCC

**Implementation:**
```python
def apply_orbital_constraints(positions, ranked_sccs):
    import math
    
    # Configuration
    BASE_ORBIT_RADIUS = 300.0
    ORBIT_SPACING = 200.0
    
    # Step 1: Identify central SCC (star)
    central_scc = ranked_sccs[0]  # Highest rank
    
    # Step 2: Place central SCC at origin
    centroid = compute_centroid(central_scc, positions)
    for node in central_scc.nodes:
        positions[node.id] = (
            positions[node.id][0] - centroid[0],
            positions[node.id][1] - centroid[1]
        )
    
    # Step 3: Position other SCCs in orbits
    for i, scc in enumerate(ranked_sccs[1:], start=1):
        # Calculate orbit radius (level 1, 2, 3, ...)
        orbit_radius = BASE_ORBIT_RADIUS + (i * ORBIT_SPACING)
        
        # Calculate angle for this SCC
        num_sccs_in_level = count_sccs_at_level(ranked_sccs, i)
        angle_index = get_angle_index_for_scc(scc, ranked_sccs, i)
        angle = (2 * math.pi * angle_index) / num_sccs_in_level
        
        # Calculate target position on orbit
        target_x = orbit_radius * math.cos(angle)
        target_y = orbit_radius * math.sin(angle)
        
        # Move SCC to orbit (preserve internal structure)
        scc_centroid = compute_centroid(scc, positions)
        for node in scc.nodes:
            positions[node.id] = (
                positions[node.id][0] - scc_centroid[0] + target_x,
                positions[node.id][1] - scc_centroid[1] + target_y
            )
    
    return positions
```

**Visual Example:**
```
Level 0 (Star):     ⭐ (rank 100)
                    
Level 1 (Planets):  🌍 (rank 50)  🌍 (rank 45)  🌍 (rank 40)
                    r=300px       r=300px       r=300px
                    
Level 2 (Moons):    🌙 (rank 20)  🌙 (rank 15)  🌙 (rank 10)
                    r=500px       r=500px       r=500px
                    
Level 3 (Satellites): • (rank 5)  • (rank 3)   • (rank 1)
                      r=700px     r=700px      r=700px
```

## 4. Integration with Shypn

### 4.1 File Structure

```
src/shypn/
├── layout/                          # NEW: Auto-layout subsystem
│   ├── __init__.py
│   ├── auto_layout_manager.py      # Orchestrator
│   ├── graph_analyzer.py           # Graph construction + SCC
│   ├── scc_detector.py             # Tarjan's algorithm
│   ├── component_ranker.py         # SCC ranking
│   ├── layout_engine.py            # Layout computation
│   ├── force_simulator.py          # Fruchterman-Reingold
│   └── orbit_post_processor.py     # Solar system refinement
│
├── helpers/
│   └── model_canvas_loader.py      # Add auto-layout menu item
│
└── data/
    └── model_canvas_manager.py     # Apply computed positions
```

### 4.2 UI Integration

**Menu Item:**
```
Context Menu (right-click on canvas)
├── ...
├── Auto Layout
│   ├── Force-Directed (Classic)    # Standard force-directed
│   ├── Solar System (SCC-based) ✨  # NEW: Orbital layout
│   ├── Hierarchical (Top-down)     # Future: Tree layout
│   └── Circular                     # Future: Circular layout
├── ...
```

**Dialog:**
```
┌─────────────────────────────────────────┐
│  Auto Layout Settings                    │
├─────────────────────────────────────────┤
│  Layout Type: [Solar System (SCC) ▼]    │
│                                          │
│  ⚙️ Force Parameters:                    │
│    Iterations:    [1000    ]            │
│    Optimal Distance: [50.0    ] px      │
│    Repulsion:     [1.0     ]            │
│    Attraction:    [0.1     ]            │
│                                          │
│  🌍 Orbital Parameters:                  │
│    Base Radius:   [300.0   ] px         │
│    Orbit Spacing: [200.0   ] px         │
│    Center Mass:   [✓] Use largest SCC   │
│                                          │
│  [ Preview ] [ Apply ] [ Cancel ]       │
└─────────────────────────────────────────┘
```

### 4.3 Usage Workflow

```python
# User workflow
1. User creates/imports Petri net model
2. User right-clicks canvas
3. User selects "Auto Layout → Solar System (SCC-based)"
4. System analyzes graph structure
5. System shows progress dialog
6. System computes layout
7. System animates transition to new positions
8. User can undo if unsatisfied
```

## 5. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- ✅ Create layout package structure
- ✅ Implement GraphAnalyzer (adjacency list)
- ✅ Implement SCCDetector (Tarjan's algorithm)
- ✅ Unit tests for SCC detection
- **Deliverable:** SCC detection working on test graphs

### Phase 2: Ranking & Force Simulation (Week 3-4)
- ✅ Implement ComponentRanker
- ✅ Implement ForceSimulator (Fruchterman-Reingold)
- ✅ Integration tests with real Petri nets
- **Deliverable:** Basic force-directed layout working

### Phase 3: Orbital Post-Processing (Week 5-6)
- ✅ Implement OrbitPostProcessor
- ✅ Implement orbital constraint solver
- ✅ Visual testing with various net topologies
- **Deliverable:** Solar system layout working

### Phase 4: UI Integration (Week 7)
- ✅ Add context menu items
- ✅ Create settings dialog
- ✅ Wire to ModelCanvasManager
- ✅ Add undo/redo support
- **Deliverable:** Feature complete and usable

### Phase 5: Polish & Optimization (Week 8)
- ✅ Add animation/transitions
- ✅ Optimize for large graphs (spatial indexing)
- ✅ Add progress indicators
- ✅ Performance testing
- **Deliverable:** Production-ready feature

## 6. Technical Considerations

### 6.1 Performance Optimization

**Problem:** Force-directed is O(n²) per iteration
**Solutions:**
1. **Barnes-Hut Approximation**: O(n log n) using quad-tree
2. **Spatial Hashing**: Group nodes by grid cells
3. **Multi-threading**: Parallelize force calculations
4. **Progressive Refinement**: Show intermediate results

### 6.2 Edge Cases

**Disconnected Components:**
- Treat each as separate solar system
- Arrange systems in grid pattern

**Single-Node SCCs:**
- Treat as satellites
- Attach to nearest larger SCC

**Bipartite Structure (Petri nets):**
- Places and transitions naturally alternate
- Preserve this property in layout

**Large SCCs:**
- May need sub-layout within SCC
- Use recursive force-directed on SCC internals

### 6.3 Undo/Redo Support

```python
class LayoutCommand:
    """Command pattern for undo/redo."""
    def __init__(self, old_positions, new_positions):
        self.old_positions = old_positions
        self.new_positions = new_positions
    
    def execute(self):
        apply_positions(self.new_positions)
    
    def undo(self):
        apply_positions(self.old_positions)
```

## 7. Testing Strategy

### 7.1 Unit Tests

```python
def test_scc_detection_simple_cycle():
    """Test: Detect single SCC in cycle."""
    graph = {1: [2], 2: [3], 3: [1]}
    sccs = tarjan_scc(graph)
    assert len(sccs) == 1
    assert set(sccs[0]) == {1, 2, 3}

def test_scc_detection_disconnected():
    """Test: Detect multiple SCCs."""
    graph = {1: [2], 2: [1], 3: [4], 4: [3]}
    sccs = tarjan_scc(graph)
    assert len(sccs) == 2

def test_force_simulation_convergence():
    """Test: Force simulation converges."""
    graph = {1: [2], 2: [3], 3: [4]}
    positions = fruchterman_reingold(graph, iterations=100)
    assert all(node in positions for node in graph)
```

### 7.2 Integration Tests

```python
def test_full_layout_pipeline():
    """Test: End-to-end layout on real Petri net."""
    # Create test net
    places = [Place(0, 0, i, f"P{i}") for i in range(5)]
    transitions = [Transition(0, 0, i, f"T{i}") for i in range(5)]
    arcs = [Arc(places[i], transitions[i], i, f"A{i}") for i in range(5)]
    
    # Run layout
    manager = AutoLayoutManager(document)
    manager.apply_layout()
    
    # Verify: All objects have new positions
    for obj in places + transitions:
        assert obj.x != 0 or obj.y != 0
```

### 7.3 Visual Tests

- Small net (10 nodes): Verify orbital structure
- Medium net (50 nodes): Verify performance
- Large net (200+ nodes): Verify scalability
- Cyclic net: Verify SCC detection
- Linear net: Verify hierarchical layout

## 8. Future Enhancements

### 8.1 Advanced Features

1. **Interactive Orbit Adjustment**
   - Drag SCCs to different orbital levels
   - Real-time re-layout

2. **Custom Gravitational Centers**
   - User pins specific nodes as "stars"
   - Manual override of SCC ranking

3. **3D Solar System**
   - Vertical layering (Z-axis)
   - Orbital planes at different angles

4. **Animation Effects**
   - Smooth interpolation between layouts
   - Particle trails showing movement
   - Zoom-to-fit after layout

### 8.2 Alternative Algorithms

1. **Hierarchical Layout** (Sugiyama)
   - Top-down layering
   - Good for workflows

2. **Circular Layout**
   - Nodes on circle perimeter
   - Minimizes edge crossings

3. **Orthogonal Layout**
   - Right-angle edges only
   - Good for circuit diagrams

## 9. Documentation Deliverables

1. ✅ **This document** (FORCE_DIRECTED_LAYOUT_SCC_PLAN.md)
2. **API Documentation** (docstrings in code)
3. **User Guide** (how to use auto-layout)
4. **Algorithm Analysis** (performance characteristics)
5. **Visual Examples** (before/after screenshots)

## 10. Success Metrics

**Quantitative:**
- Layout time: < 5 seconds for 100-node graph
- Visual quality: < 5% edge crossings (vs random)
- User satisfaction: > 80% prefer vs manual layout

**Qualitative:**
- Intuitive hierarchy visible
- Related components clustered
- Professional, aesthetic appearance
- Stable results (reproducible)

---

## Summary: Key Concepts

### The Solar System Analogy

```
             BEFORE (Random)              AFTER (Solar System)

    T1    P1       P2                         P2
                                              / \
    P3  T2    P4   T3                       T1   T2 (Orbit 2)
                                               \ /
    T4    P5       P6              P1 ← → ⭐ SCC ⭐ → P3 (Orbit 1)
                                               / \
    P7  T5    P8   T6                       T3   T4 (Orbit 2)
                                              \ /
                                               P4

    (Chaotic, unclear)              (Structured, clear hierarchy)
```

### Algorithm Pipeline

```
1. BUILD GRAPH
   Input: Petri net (Places, Transitions, Arcs)
   Output: Adjacency list
   
2. DETECT SCCs
   Algorithm: Tarjan's DFS
   Output: List of strongly connected components
   
3. RANK SCCs
   Criteria: Size, connectivity, centrality
   Output: Hierarchical levels (star, planets, moons, satellites)
   
4. FORCE-DIRECTED LAYOUT
   Algorithm: Fruchterman-Reingold
   Output: Initial positions (aesthetic but not structured)
   
5. ORBITAL POST-PROCESSING ✨
   Algorithm: Constrained optimization
   Output: Final positions (structured solar system)
   
6. APPLY TO CANVAS
   Update node coordinates
   Trigger redraw
```

### Core Innovation

**Traditional force-directed:** Aesthetic but chaotic
**Our approach:** Aesthetic + structured hierarchy through SCC analysis

The post-processing step transforms a "cloud of stars" into a "solar system" - same nodes, but organized by semantic importance derived from graph structure.

---

**Document Status:** ✅ Complete - Ready for Implementation
**Author:** AI Assistant + User Collaboration
**Date:** October 16, 2025
**Version:** 1.0
