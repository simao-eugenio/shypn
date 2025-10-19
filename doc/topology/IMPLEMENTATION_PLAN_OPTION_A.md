# Topology Implementation Plan - Option A (Property Dialogs)

**Date**: October 19, 2025  
**Architecture**: OOP with base classes, separate modules, thin loaders  
**Goal**: Replace diagnostics with comprehensive topology system

---

## 🏗️ Architecture Principles

### **1. Code Organization**
```
src/shypn/topology/          # Business logic (OOP)
    base/                    # Base classes
    structural/              # P/T-invariants, siphons, traps
    graph/                   # Cycles, paths, SCCs
    behavioral/              # Liveness, boundedness, deadlocks
    network/                 # Hubs, centrality, communities
    
doc/topology/                # Documentation
    algorithms/              # Algorithm descriptions
    examples/                # Usage examples
    benchmarks/              # Performance tests
```

### **2. OOP Design**
- **Base class**: `TopologyAnalyzer` (abstract)
- **Separate modules**: Each analyzer in own file
- **Thin loaders**: UI loaders delegate to analyzers
- **No orphaned widgets**: Proper cleanup
- **Wayland-safe**: No X11-specific code

### **3. Diagnostics Replacement**
- Merge `diagnostic/` into `topology/`
- Keep locality analysis (useful)
- Extend with topology properties
- Single unified system

---

## 📁 Directory Structure

```
src/shypn/topology/
    __init__.py
    
    base/
        __init__.py
        topology_analyzer.py        # Abstract base class
        analysis_result.py          # Result data class
        exceptions.py               # Custom exceptions
    
    structural/
        __init__.py
        p_invariants.py             # P-invariant analyzer
        t_invariants.py             # T-invariant analyzer
        siphons.py                  # Siphon detector
        traps.py                    # Trap detector
    
    graph/
        __init__.py
        cycles.py                   # Cycle detector
        paths.py                    # Path finder
        sccs.py                     # SCC analyzer (wrap existing)
        dag.py                      # DAG analyzer
    
    behavioral/
        __init__.py
        liveness.py                 # Liveness analyzer
        boundedness.py              # Boundedness checker
        reachability.py             # Reachability analyzer
        deadlock.py                 # Deadlock detector
    
    network/
        __init__.py
        hubs.py                     # Hub detector (wrap existing)
        centrality.py               # Centrality measures
        communities.py              # Community detection
        clustering.py               # Clustering coefficient
    
    locality/                       # Migrated from diagnostic/
        __init__.py
        locality.py                 # Locality data class
        locality_detector.py        # Detector
        locality_analyzer.py        # Analyzer
        locality_runtime.py         # Runtime analyzer

doc/topology/
    README.md                       # Overview
    ARCHITECTURE.md                 # Architecture details
    ALGORITHMS.md                   # Algorithm descriptions
    
    algorithms/
        p_invariants.md
        cycles.md
        paths.md
        hubs.md
    
    examples/
        basic_usage.md
        property_dialog.md
        panel_integration.md
```

---

## 🎯 Phase 1: Foundation (Week 1)

### **Step 1.1: Create Base Classes**

**File**: `src/shypn/topology/base/topology_analyzer.py`
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .analysis_result import AnalysisResult

class TopologyAnalyzer(ABC):
    """Abstract base class for topology analyzers.
    
    All topology analyzers inherit from this base class and implement
    the analyze() method to perform specific analysis.
    
    Attributes:
        model: PetriNetModel instance
        cache: Optional cache for expensive computations
    """
    
    def __init__(self, model: Any):
        self.model = model
        self._cache = {}
        self._dirty = True
    
    @abstractmethod
    def analyze(self, **kwargs) -> AnalysisResult:
        """Perform topology analysis.
        
        Returns:
            AnalysisResult: Analysis results
        """
        pass
    
    def clear_cache(self):
        """Clear cached results."""
        self._cache.clear()
        self._dirty = True
    
    def invalidate(self):
        """Mark cache as dirty."""
        self._dirty = True
```

**File**: `src/shypn/topology/base/analysis_result.py`
```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class AnalysisResult:
    """Result of topology analysis.
    
    Attributes:
        success: Whether analysis succeeded
        data: Analysis data
        summary: Human-readable summary
        warnings: List of warnings
        errors: List of errors
        metadata: Additional metadata
    """
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default=None):
        """Get data value."""
        return self.data.get(key, default)
    
    def has_warnings(self) -> bool:
        """Check if result has warnings."""
        return len(self.warnings) > 0
    
    def has_errors(self) -> bool:
        """Check if result has errors."""
        return len(self.errors) > 0
```

---

### **Step 1.2: Implement Cycles Analyzer (First Tool)**

**File**: `src/shypn/topology/graph/cycles.py`
```python
from typing import List, Dict, Any
import networkx as nx
from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult

class CycleAnalyzer(TopologyAnalyzer):
    """Analyzer for detecting cycles in Petri nets.
    
    Finds all elementary cycles (simple cycles) in the Petri net graph.
    Uses Johnson's algorithm for efficient cycle enumeration.
    
    Example:
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze()
        
        for cycle in result.get('cycles', []):
            print(f"Cycle: {cycle['nodes']}")
    """
    
    def analyze(self, max_cycles: int = 100) -> AnalysisResult:
        """Find all cycles in the Petri net.
        
        Args:
            max_cycles: Maximum number of cycles to find
            
        Returns:
            AnalysisResult with:
                - cycles: List of cycle dicts
                - count: Total number of cycles
                - longest: Longest cycle
                - summary: Human-readable summary
        """
        try:
            # Build directed graph
            graph = self._build_graph()
            
            # Find cycles using NetworkX
            cycles = list(nx.simple_cycles(graph))
            
            # Limit results
            if len(cycles) > max_cycles:
                cycles = cycles[:max_cycles]
                truncated = True
            else:
                truncated = False
            
            # Analyze cycles
            cycle_data = []
            for cycle in cycles:
                cycle_info = self._analyze_cycle(cycle)
                cycle_data.append(cycle_info)
            
            # Find longest cycle
            longest = max(cycles, key=len) if cycles else []
            
            # Create summary
            summary = self._create_summary(len(cycles), longest, truncated)
            
            return AnalysisResult(
                success=True,
                data={
                    'cycles': cycle_data,
                    'count': len(cycles),
                    'longest_length': len(longest),
                    'longest_cycle': longest,
                    'truncated': truncated
                },
                summary=summary,
                warnings=['Results truncated'] if truncated else []
            )
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Cycle analysis failed: {str(e)}"]
            )
    
    def _build_graph(self) -> nx.DiGraph:
        """Build NetworkX graph from Petri net."""
        graph = nx.DiGraph()
        
        # Add nodes
        for place in self.model.places:
            graph.add_node(place.id, type='place', obj=place)
        
        for transition in self.model.transitions:
            graph.add_node(transition.id, type='transition', obj=transition)
        
        # Add edges
        for arc in self.model.arcs:
            graph.add_edge(arc.source_id, arc.target_id, obj=arc)
        
        return graph
    
    def _analyze_cycle(self, cycle: List[int]) -> Dict[str, Any]:
        """Analyze single cycle."""
        # Get objects
        objects = []
        for node_id in cycle:
            obj = self._get_object_by_id(node_id)
            objects.append(obj)
        
        # Classify nodes
        places = [obj for obj in objects if hasattr(obj, 'tokens')]
        transitions = [obj for obj in objects if hasattr(obj, 'transition_type')]
        
        # Get names
        names = [getattr(obj, 'name', f'ID{obj.id}') for obj in objects]
        
        return {
            'nodes': cycle,
            'length': len(cycle),
            'names': names,
            'place_count': len(places),
            'transition_count': len(transitions),
            'type': self._classify_cycle_type(places, transitions)
        }
    
    def _classify_cycle_type(self, places, transitions) -> str:
        """Classify cycle type."""
        if len(transitions) == 1:
            return 'self-loop'
        elif len(places) == len(transitions):
            return 'balanced'
        elif len(places) > len(transitions):
            return 'place-heavy'
        else:
            return 'transition-heavy'
    
    def _create_summary(self, count: int, longest: List, truncated: bool) -> str:
        """Create human-readable summary."""
        if count == 0:
            return "No cycles found (DAG)"
        
        summary = f"Found {count} cycle(s)"
        if truncated:
            summary += " (truncated)"
        
        if longest:
            summary += f"\nLongest cycle: {len(longest)} nodes"
        
        return summary
    
    def _get_object_by_id(self, obj_id: int) -> Any:
        """Get Petri net object by ID."""
        # Try places
        for place in self.model.places:
            if place.id == obj_id:
                return place
        
        # Try transitions
        for transition in self.model.transitions:
            if transition.id == obj_id:
                return transition
        
        return None
```

---

### **Step 1.3: Property Dialog Integration**

**File**: `src/shypn/helpers/place_prop_dialog_loader.py` (MODIFY)

Add topology tab to existing dialog:
```python
def _setup_topology_tab(self):
    """Setup topology tab (NEW)."""
    # Get topology analyzers
    from shypn.topology.graph.cycles import CycleAnalyzer
    
    # Create analyzer
    cycle_analyzer = CycleAnalyzer(self.model)
    
    # Analyze cycles for this place
    result = cycle_analyzer.analyze()
    
    # Find cycles containing this place
    place_cycles = self._find_cycles_containing_place(
        result.get('cycles', []),
        self.place_obj.id
    )
    
    # Update UI
    cycles_label = self.builder.get_object('topology_cycles_label')
    if cycles_label:
        if place_cycles:
            text = f"In {len(place_cycles)} cycle(s):\n"
            for i, cycle in enumerate(place_cycles[:5], 1):
                text += f"  {i}. {' → '.join(cycle['names'][:10])}\n"
            cycles_label.set_text(text)
        else:
            cycles_label.set_text("Not in any cycles")

def _find_cycles_containing_place(self, cycles, place_id):
    """Find cycles that contain this place."""
    return [c for c in cycles if place_id in c['nodes']]
```

---

## 🎯 Phase 2: Core Tools (Week 2-3)

### **Priority Order**:
1. ✅ Cycles (Week 1) - DONE ABOVE
2. **P-Invariants** (Week 2)
3. **Hubs** (Week 2) - Wrap existing
4. **Paths** (Week 3)

### **Implementation Pattern** (same for all):
```python
# 1. Create analyzer class
class XxxAnalyzer(TopologyAnalyzer):
    def analyze(self, **kwargs) -> AnalysisResult:
        # Implementation
        pass

# 2. Add to property dialog
def _setup_topology_tab(self):
    xxx_analyzer = XxxAnalyzer(self.model)
    result = xxx_analyzer.analyze()
    # Update UI

# 3. Add tests
def test_xxx_analyzer():
    analyzer = XxxAnalyzer(model)
    result = analyzer.analyze()
    assert result.success
```

---

## 🎯 Phase 3: UI Files (Parallel with Phase 2)

### **Update Glade Files** (No Orphaned Widgets)

**File**: `ui/dialogs/place_prop_dialog.ui`

Add topology tab:
```xml
<object class="GtkNotebook" id="notebook">
  <!-- Existing tabs -->
  <child>
    <object class="GtkBox" id="topology_tab">
      <property name="orientation">vertical</property>
      <property name="spacing">10</property>
      <property name="margin">10</property>
      
      <!-- Cycles section -->
      <child>
        <object class="GtkFrame">
          <property name="label">Cycles</property>
          <child>
            <object class="GtkLabel" id="topology_cycles_label">
              <property name="xalign">0</property>
              <property name="wrap">True</property>
              <property name="selectable">True</property>
            </object>
          </child>
        </object>
      </child>
      
      <!-- P-Invariants section -->
      <child>
        <object class="GtkFrame">
          <property name="label">P-Invariants</property>
          <child>
            <object class="GtkLabel" id="topology_p_invariants_label">
              <property name="xalign">0</property>
              <property name="wrap">True</property>
              <property name="selectable">True</property>
            </object>
          </child>
        </object>
      </child>
      
      <!-- More sections... -->
    </object>
  </child>
  <child type="tab">
    <object class="GtkLabel">
      <property name="label">Topology</property>
    </object>
  </child>
</object>
```

**Wayland Safety**:
- ✅ Use GtkLabel (not orphaned TextViews)
- ✅ Proper parent-child hierarchy
- ✅ No X11-specific properties
- ✅ Clean widget lifecycle

---

## 🎯 Phase 4: Diagnostics Replacement (Week 4)

### **Migration Plan**:

1. **Keep**:
   - Locality detection/analysis (useful!)
   - Runtime analysis (throughput, events)
   
2. **Move to topology/**:
   - `diagnostic/locality_*.py` → `topology/locality/`
   
3. **Delete**:
   - `diagnostic/README.md` (replace)
   - Old diagnostic panel (if exists)

4. **Create unified system**:
   ```
   topology/
       locality/          # Local structure
       structural/        # Invariants, siphons, traps
       graph/            # Cycles, paths
       behavioral/       # Liveness, boundedness
       network/          # Hubs, centrality
   ```

---

## 📝 Testing Strategy

### **Unit Tests**:
```python
tests/topology/
    test_cycles.py
    test_p_invariants.py
    test_hubs.py
    test_paths.py
```

### **Test Pattern**:
```python
def test_cycle_analyzer_simple():
    """Test cycle detection on simple net."""
    # Create simple cycle: P1 → T1 → P2 → T2 → P1
    model = create_simple_cycle_model()
    
    analyzer = CycleAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count') == 1
    assert len(result.get('cycles')[0]['nodes']) == 4

def test_cycle_analyzer_no_cycles():
    """Test on DAG (no cycles)."""
    model = create_dag_model()
    
    analyzer = CycleAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count') == 0
    assert 'DAG' in result.summary
```

---

## 🚀 Implementation Timeline

### **Week 1: Foundation**
- ✅ Create directory structure
- ✅ Base classes (TopologyAnalyzer, AnalysisResult)
- ✅ Cycles analyzer
- ✅ Property dialog integration
- ✅ Tests

### **Week 2: Core Tools**
- P-Invariants analyzer
- Hubs analyzer (wrap existing)
- Property dialog updates
- Tests

### **Week 3: Essential Tools**
- Paths analyzer
- T-Invariants analyzer
- Property dialog completion
- Tests

### **Week 4: Consolidation**
- Migrate locality from diagnostic/
- Delete old diagnostic code
- Unified topology system
- Documentation

---

## ✅ Success Criteria

1. **Architecture**:
   - ✅ OOP base classes
   - ✅ Separate modules
   - ✅ Thin loaders
   - ✅ No orphaned widgets

2. **Functionality**:
   - ✅ 4 core tools working (Cycles, P-Inv, Hubs, Paths)
   - ✅ Property dialog integration
   - ✅ Wayland-compatible UI

3. **Code Quality**:
   - ✅ Tests passing
   - ✅ Documentation complete
   - ✅ No diagnostic/ remains

---

**Status**: ✅ **PLAN COMPLETE**  
**Next**: Create directory structure and implement base classes
