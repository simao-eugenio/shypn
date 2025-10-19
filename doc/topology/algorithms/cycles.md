# Cycle Detection Algorithm

**Algorithm**: Johnson's Algorithm (1975)  
**Complexity**: O((n + e)(c + 1)) where n=nodes, e=edges, c=cycles  
**Implementation**: `src/shypn/topology/graph/cycles.py`

---

## Overview

Cycle detection finds all **elementary cycles** (simple cycles) in a directed graph. An elementary cycle is a closed path where no node appears more than once (except the start/end node).

For Petri nets, cycles represent:
- **Metabolic loops**: TCA cycle, Calvin cycle, urea cycle
- **Feedback regulation**: Product inhibition, allosteric control
- **Substrate recycling**: NAD+/NADH, ATP/ADP cycling
- **Conservation cycles**: Mass/charge conservation loops

---

## Algorithm: Johnson's Algorithm

### Pseudocode

```
JOHNSON(G):
    cycles = []
    
    for each strongly connected component SCC in G:
        blocked = set()
        B = {v: set() for v in SCC}  # Blocked neighbors
        stack = []
        
        for s in SCC:
            CIRCUIT(s, s, SCC, blocked, B, stack, cycles)
            blocked.clear()
            for v in SCC:
                B[v].clear()
    
    return cycles

CIRCUIT(v, s, SCC, blocked, B, stack, cycles):
    found = False
    stack.push(v)
    blocked.add(v)
    
    for w in neighbors(v) ∩ SCC:
        if w == s:
            # Found cycle
            cycles.append(stack.copy())
            found = True
        elif w not in blocked:
            if CIRCUIT(w, s, SCC, blocked, B, stack, cycles):
                found = True
    
    if found:
        UNBLOCK(v, blocked, B)
    else:
        for w in neighbors(v) ∩ SCC:
            B[w].add(v)
    
    stack.pop()
    return found

UNBLOCK(v, blocked, B):
    blocked.remove(v)
    for w in B[v]:
        if w in blocked:
            UNBLOCK(w, blocked, B)
    B[v].clear()
```

### Key Ideas

1. **SCC Decomposition**: Only search within strongly connected components
2. **Backtracking**: Explore all paths from start node
3. **Blocking**: Avoid redundant searches using blocked set
4. **Smart Unblocking**: Unblock nodes when cycle found

---

## Implementation Details

### Graph Construction

```python
def _build_graph(self) -> nx.DiGraph:
    """Build NetworkX graph from Petri net."""
    graph = nx.DiGraph()
    
    # Add nodes (places and transitions)
    for place in self.model.places:
        graph.add_node(place.id, type='place', obj=place)
    
    for transition in self.model.transitions:
        graph.add_node(transition.id, type='transition', obj=transition)
    
    # Add edges (arcs)
    for arc in self.model.arcs:
        graph.add_edge(arc.source_id, arc.target_id, obj=arc)
    
    return graph
```

### Cycle Analysis

```python
def _analyze_cycle(self, cycle_nodes: List[int]) -> Dict[str, Any]:
    """Analyze cycle structure."""
    # Count places vs transitions
    objects = [self._get_object_by_id(id) for id in cycle_nodes]
    places = [o for o in objects if hasattr(o, 'tokens')]
    transitions = [o for o in objects if hasattr(o, 'transition_type')]
    
    # Classify type
    if len(transitions) == 1:
        cycle_type = 'self-loop'
    elif len(places) == len(transitions):
        cycle_type = 'balanced'  # Typical metabolic cycle
    elif len(places) > len(transitions):
        cycle_type = 'place-heavy'
    else:
        cycle_type = 'transition-heavy'
    
    return {
        'nodes': cycle_nodes,
        'length': len(cycle_nodes),
        'names': [get_name(o) for o in objects],
        'place_count': len(places),
        'transition_count': len(transitions),
        'type': cycle_type,
    }
```

---

## Cycle Types

### 1. Self-Loop
```
T1 ──→ P1 ──→ T1
```
- Single transition, single place
- Represents immediate feedback

### 2. Balanced Cycle
```
P1 ──→ T1 ──→ P2 ──→ T2 ──→ P3 ──→ T3 ──→ P1
```
- Equal places and transitions
- **Most common in metabolic pathways**
- Example: TCA cycle (8 metabolites, 8 reactions)

### 3. Place-Heavy Cycle
```
P1 ──→ T1 ──→ P2 ──→ P3 ──→ T2 ──→ P1
```
- More places than transitions
- Represents substrate accumulation points

### 4. Transition-Heavy Cycle
```
P1 ──→ T1 ──→ T2 ──→ T3 ──→ P2 ──→ P1
```
- More transitions than places
- Represents complex reaction sequences

---

## Biochemical Examples

### Example 1: TCA Cycle (Krebs Cycle)

```
Acetyl-CoA ──→ Citrate ──→ Isocitrate ──→ α-Ketoglutarate 
     ↑                                          ↓
     └──── Oxaloacetate ←──── Malate ←──── Succinate
```

**Cycle Properties**:
- Length: 8 (balanced)
- Type: Metabolic loop
- Function: Energy production (NADH/FADH2)

### Example 2: Calvin Cycle

```
RuBP ──→ 3-PGA ──→ G3P ──→ Glucose
  ↑                    ↓
  └──── (regeneration) ─┘
```

**Cycle Properties**:
- Length: 5-13 (depending on detail)
- Type: Carbon fixation cycle
- Function: CO2 → Glucose conversion

### Example 3: Substrate Cycling (ATP/ADP)

```
        Kinase
ATP ─────────→ ADP
 ↑               ↓
 └─── Synthase ──┘
```

**Cycle Properties**:
- Length: 2 (self-loop)
- Type: Energy currency
- Function: Energy transfer

---

## Performance Considerations

### Complexity Analysis

- **Time**: O((n + e)(c + 1))
  - n = number of nodes
  - e = number of edges
  - c = number of cycles
- **Space**: O(n + e)

### Typical Performance

**Small Networks** (< 100 nodes):
- Analysis time: < 1 second
- Memory: < 10 MB

**Medium Networks** (100-1000 nodes):
- Analysis time: 1-10 seconds
- Memory: 10-100 MB

**Large Networks** (> 1000 nodes):
- Analysis time: 10+ seconds
- Memory: > 100 MB
- **Recommendation**: Use `max_cycles` limit

### Optimization Strategies

1. **SCC Decomposition**: Only search within strongly connected components
2. **Early Termination**: Use `max_cycles` parameter
3. **Caching**: Cache results until model changes
4. **Length Filter**: Use `min_length` to skip trivial cycles

---

## Usage Examples

### Example 1: Find All Cycles

```python
from shypn.topology.graph import CycleAnalyzer

analyzer = CycleAnalyzer(model)
result = analyzer.analyze()

print(f"Found {result.get('count')} cycles")

for cycle in result.get('cycles', []):
    print(f"  {' → '.join(cycle['names'])}")
    print(f"    Type: {cycle['type']}")
    print(f"    Length: {cycle['length']}")
```

### Example 2: Find Cycles Containing Specific Node

```python
# Find cycles containing glucose-6-phosphate (place ID 42)
analyzer = CycleAnalyzer(model)
g6p_cycles = analyzer.find_cycles_containing_node(42)

print(f"G6P is in {len(g6p_cycles)} cycle(s):")
for cycle in g6p_cycles:
    print(f"  {' → '.join(cycle['names'])}")
```

### Example 3: Find Long Cycles (Complex Pathways)

```python
analyzer = CycleAnalyzer(model)
result = analyzer.analyze(min_length=10)  # Only cycles with 10+ nodes

long_cycles = [c for c in result.get('cycles', []) if c['length'] >= 10]
print(f"Found {len(long_cycles)} long cycles")
```

### Example 4: Performance-Limited Search

```python
# Large network: limit to 50 cycles
analyzer = CycleAnalyzer(model)
result = analyzer.analyze(max_cycles=50)

if result.get('truncated'):
    print(f"⚠️  Results truncated (found {result.get('count')} total)")
```

---

## Integration with Property Dialogs

### Place Property Dialog

```python
def _setup_topology_tab(self):
    """Add topology info to place dialog."""
    from shypn.topology.graph import CycleAnalyzer
    
    analyzer = CycleAnalyzer(self.model)
    place_cycles = analyzer.find_cycles_containing_node(self.place_obj.id)
    
    # Update UI
    label = self.builder.get_object('topology_cycles_label')
    if place_cycles:
        text = f"Part of {len(place_cycles)} cycle(s):\n\n"
        for i, cycle in enumerate(place_cycles[:5], 1):
            names = ' → '.join(cycle['names'][:10])
            if len(cycle['names']) > 10:
                names += ' ...'
            text += f"{i}. {names}\n"
            text += f"   Length: {cycle['length']}, Type: {cycle['type']}\n\n"
        label.set_text(text)
    else:
        label.set_text("Not part of any cycles")
```

---

## References

### Papers

1. **Johnson, D. B. (1975)**  
   "Finding all the elementary circuits of a directed graph"  
   *SIAM Journal on Computing*, 4(1), 77-84.  
   [DOI: 10.1137/0204007](https://doi.org/10.1137/0204007)

2. **Tarjan, R. (1972)**  
   "Depth-first search and linear graph algorithms"  
   *SIAM Journal on Computing*, 1(2), 146-160.

### Implementations

- **NetworkX**: `nx.simple_cycles()` - Python implementation
- **Boost Graph Library**: `hawick_circuits()` - C++ implementation
- **igraph**: `graph.simple_cycles()` - C/Python implementation

### Biochemical Context

- **KEGG**: Pathway database with cycle annotations
- **MetaCyc**: Metabolic pathway database
- **Reactome**: Pathway knowledge base

---

## Future Enhancements

### Planned Features

1. **Cycle Filtering**:
   - Filter by biochemical relevance
   - Filter by token flow direction
   - Filter by cycle length range

2. **Cycle Visualization**:
   - Highlight cycles in GUI
   - Export cycle graphs
   - Animate token flow in cycles

3. **Cycle Analysis**:
   - Flux balance analysis
   - Stoichiometric analysis
   - Thermodynamic feasibility

4. **Performance**:
   - Incremental cycle detection
   - Parallel cycle enumeration
   - GPU-accelerated search

---

**Status**: ✅ **IMPLEMENTED**  
**Version**: 0.1.0  
**Last Updated**: October 19, 2025
