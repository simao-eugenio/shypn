# Topology Analysis System

**Version**: 0.1.0  
**Date**: October 19, 2025  
**Status**: Active Development

---

## 📖 Overview

The topology analysis system provides comprehensive structural and behavioral analysis of Petri nets, with a focus on biochemical network applications. It replaces the previous diagnostic system with a unified, extensible topology framework.

### Key Features

- **🔵 Structural Analysis**: P/T-invariants, siphons, traps
- **🔄 Graph Analysis**: Cycles, paths, SCCs, DAG detection
- **⚡ Behavioral Analysis**: Liveness, boundedness, reachability, deadlocks
- **🌐 Network Analysis**: Hubs, centrality, communities, clustering

---

## 🏗️ Architecture

### Directory Structure

```
src/shypn/topology/
    base/                      # Foundation classes
        topology_analyzer.py   # Abstract base class
        analysis_result.py     # Result data structure
        exceptions.py          # Custom exceptions
    
    structural/                # Structural properties
        p_invariants.py        # P-invariant analysis
        t_invariants.py        # T-invariant analysis
        siphons.py             # Siphon detection
        traps.py               # Trap detection
    
    graph/                     # Graph topology
        cycles.py              # Cycle detection ✅ IMPLEMENTED
        paths.py               # Path finding
        sccs.py                # Strongly connected components
        dag.py                 # DAG analysis
    
    behavioral/                # Behavioral properties
        liveness.py            # Liveness analysis
        boundedness.py         # Boundedness checking
        reachability.py        # Reachability analysis
        deadlock.py            # Deadlock detection
    
    network/                   # Network metrics
        hubs.py                # Hub detection
        centrality.py          # Centrality measures
        communities.py         # Community detection
        clustering.py          # Clustering coefficient
```

### Design Principles

1. **OOP Base Classes**: All analyzers inherit from `TopologyAnalyzer`
2. **Separate Modules**: Each analyzer in its own file
3. **Thin Loaders**: UI loaders delegate to analyzers
4. **No Orphaned Widgets**: Proper GTK widget lifecycle
5. **Wayland Compatible**: No X11-specific code

---

## 🚀 Quick Start

### Basic Usage

```python
from shypn.topology.graph import CycleAnalyzer

# Create analyzer
analyzer = CycleAnalyzer(model)

# Perform analysis
result = analyzer.analyze(max_cycles=100)

# Check results
if result.success:
    print(result.summary)
    
    for cycle in result.get('cycles', []):
        print(f"Cycle: {cycle['names']}")
        print(f"  Length: {cycle['length']}")
        print(f"  Type: {cycle['type']}")
else:
    print("Analysis failed:", result.errors)
```

### Property Dialog Integration

```python
# In property dialog loader
from shypn.topology.graph import CycleAnalyzer

def _setup_topology_tab(self):
    """Setup topology tab."""
    # Create analyzer
    cycle_analyzer = CycleAnalyzer(self.model)
    
    # Find cycles containing this place
    place_cycles = cycle_analyzer.find_cycles_containing_node(self.place_obj.id)
    
    # Update UI
    cycles_label = self.builder.get_object('topology_cycles_label')
    if cycles_label:
        if place_cycles:
            text = f"In {len(place_cycles)} cycle(s):\n"
            for i, cycle in enumerate(place_cycles[:5], 1):
                names = ' → '.join(cycle['names'][:10])
                text += f"  {i}. {names}\n"
            cycles_label.set_text(text)
        else:
            cycles_label.set_text("Not in any cycles")
```

---

## 📊 Analysis Results

### AnalysisResult Structure

All analyzers return an `AnalysisResult` object with:

```python
@dataclass
class AnalysisResult:
    success: bool              # Whether analysis succeeded
    data: Dict[str, Any]       # Analysis-specific data
    summary: str               # Human-readable summary
    warnings: List[str]        # Warning messages
    errors: List[str]          # Error messages
    metadata: Dict[str, Any]   # Timing, parameters, etc.
```

### Example Result

```python
result = analyzer.analyze()

# Access data
cycles = result.get('cycles', [])
count = result.get('count', 0)

# Check status
if result.has_warnings():
    for warning in result.warnings:
        print(f"⚠️  {warning}")

# Get metadata
duration = result.metadata.get('analysis_time', 0)
print(f"Analysis took {duration:.3f} seconds")
```

---

## 🔄 Implemented Analyzers

### ✅ Cycle Analyzer

**Module**: `topology.graph.cycles`  
**Class**: `CycleAnalyzer`  
**Status**: ✅ Implemented

Detects all elementary cycles (simple cycles) in the Petri net using Johnson's algorithm.

**Methods**:
- `analyze(max_cycles=100, min_length=2)`: Find all cycles
- `find_cycles_containing_node(node_id)`: Find cycles containing specific node

**Results**:
- `cycles`: List of cycle information dicts
- `count`: Total number of cycles found
- `longest_length`: Length of longest cycle
- `truncated`: Whether results were limited

**Cycle Info**:
- `nodes`: List of node IDs in cycle
- `names`: List of node names
- `length`: Number of nodes
- `place_count`: Number of places
- `transition_count`: Number of transitions
- `type`: Cycle classification (self-loop, balanced, place-heavy, transition-heavy)

**Example**:
```python
analyzer = CycleAnalyzer(model)
result = analyzer.analyze()

for cycle in result.get('cycles', []):
    print(f"{cycle['type']} cycle: {' → '.join(cycle['names'])}")
```

---

## 🔜 Planned Analyzers

### Priority Order (Tier 1)

1. ✅ **Cycles** - COMPLETED
2. **P-Invariants** - Next (Week 2)
3. **Hubs** - Week 2 (wrap existing)
4. **Paths** - Week 3

### Tier 2 (Important)

- Boundedness
- T-Invariants
- Communities

### Tier 3 (Useful)

- Centrality
- Liveness
- Deadlocks

### Tier 4 (Advanced)

- SCCs, Siphons, Traps, Reachability, DAG, Clustering

---

## 🎨 UI Integration

### Property Dialogs

Topology information is integrated into property dialogs via a "Topology" tab:

**Place Properties**:
- Cycles containing this place
- P-Invariants including this place
- Siphons/Traps containing this place
- Degree (in/out connections)
- Centrality scores
- Community membership

**Transition Properties**:
- Cycles including this transition
- T-Invariants including this transition
- Locality information
- Liveness classification
- Conflicts with other transitions
- Centrality scores

**Arc Properties**:
- Connection information
- Cycles using this arc
- Critical path membership
- Token flow statistics

### Wayland Compatibility

All UI code follows Wayland-safe practices:
- ✅ Proper widget hierarchy (no orphans)
- ✅ GTK3 standard widgets only
- ✅ No X11-specific calls
- ✅ Proper cleanup in destructors

---

## 🧪 Testing

### Unit Tests

Location: `tests/topology/`

```python
def test_cycle_analyzer_simple():
    """Test cycle detection on simple network."""
    model = create_simple_cycle_model()
    
    analyzer = CycleAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count') == 1
    assert len(result.get('cycles')[0]['nodes']) == 4

def test_cycle_analyzer_dag():
    """Test on DAG (no cycles)."""
    model = create_dag_model()
    
    analyzer = CycleAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count') == 0
    assert 'DAG' in result.summary
```

---

## 📈 Performance

### Caching

All analyzers support caching for expensive computations:

```python
analyzer = CycleAnalyzer(model)

# First call: full analysis
result1 = analyzer.analyze()

# Modify model
model.add_place(...)

# Invalidate cache
analyzer.invalidate()

# Next call: recomputes
result2 = analyzer.analyze()
```

### Timing

Analysis timing is automatically recorded:

```python
result = analyzer.analyze()
duration = result.metadata.get('analysis_time', 0)
print(f"Analysis took {duration:.3f} seconds")
```

---

## 🔧 Extending

### Creating New Analyzers

1. **Inherit from TopologyAnalyzer**:
```python
from shypn.topology.base import TopologyAnalyzer, AnalysisResult

class MyAnalyzer(TopologyAnalyzer):
    def analyze(self, **kwargs) -> AnalysisResult:
        # Your implementation
        return AnalysisResult(success=True, data={...})
```

2. **Add to appropriate submodule**:
   - `structural/` - Conservation, structural properties
   - `graph/` - Graph-theoretic properties
   - `behavioral/` - Dynamic/simulation properties
   - `network/` - Network metrics

3. **Export in `__init__.py`**:
```python
from .my_analyzer import MyAnalyzer
__all__ = ['MyAnalyzer']
```

4. **Write tests**:
```python
def test_my_analyzer():
    analyzer = MyAnalyzer(model)
    result = analyzer.analyze()
    assert result.success
```

---

## 📚 References

### Algorithms

- **Cycles**: Johnson's algorithm (1975)
- **P-Invariants**: Integer linear algebra
- **Siphons/Traps**: Graph search algorithms
- **Centrality**: Betweenness, closeness, PageRank

### Documentation

- `doc/topology/algorithms/` - Detailed algorithm descriptions
- `doc/topology/examples/` - Usage examples
- `doc/TOPOLOGY_TOOLS_PALETTE_PLAN.md` - Original plan
- `doc/TOPOLOGY_DIAGNOSTIC_FLOW_ANALYSIS.md` - Comparison with diagnostics

---

## 🚀 Roadmap

### Week 1 (Current)
- ✅ Directory structure
- ✅ Base classes
- ✅ Cycles analyzer
- ✅ Documentation
- ⬜ Tests for cycles

### Week 2
- ⬜ P-Invariants analyzer
- ⬜ Hubs analyzer (wrap existing)
- ⬜ Property dialog integration
- ⬜ Tests

### Week 3
- ⬜ Paths analyzer
- ⬜ T-Invariants analyzer
- ⬜ Complete property dialog tabs
- ⬜ Tests

### Week 4
- ⬜ Migrate locality from diagnostic/
- ⬜ Delete old diagnostic code
- ⬜ Unified topology system
- ⬜ Final documentation

---

**Status**: Phase 1 Foundation ✅ COMPLETE  
**Next**: Tests and P-Invariants analyzer
