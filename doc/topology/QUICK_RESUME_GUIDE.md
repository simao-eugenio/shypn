# Topology Integration - Quick Resume Guide

**Date**: December 2024  
**Purpose**: Quick reference for resuming topology integration work

---

## 🎯 Where We Are

**80% Complete** - 4 of 16 core analyzers implemented and integrated into property dialogs.

### ✅ What's Working
- Cycles detection in all property dialogs
- Paths analysis
- P-Invariants computation
- Hub detection
- Topology tab appears in Place/Transition/Arc dialogs

### 🔜 What's Next
Implement remaining 12 analyzers (T-Invariants is Priority #1)

---

## 🚀 Quick Start - Resume in 5 Minutes

### 1. Verify Current State (2 min)

```bash
cd /home/simao/projetos/shypn

# Test analyzers are importable
python3 << 'EOF'
try:
    from shypn.topology.graph.cycles import CycleAnalyzer
    from shypn.topology.graph.paths import PathAnalyzer
    from shypn.topology.structural.p_invariants import PInvariantAnalyzer
    from shypn.topology.network.hubs import HubAnalyzer
    print("✅ All 4 analyzers load successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
EOF
```

### 2. Test in Application (2 min)

```bash
# Run the application
python3 src/shypn.py

# Then:
# 1. Open or create a Petri net model
# 2. Double-click any place/transition
# 3. Click on "Topology" tab
# 4. Should see cycle analysis results
```

### 3. Review Code Pattern (1 min)

```bash
# Look at existing analyzer as template
cat src/shypn/topology/graph/cycles.py | head -100
```

---

## 📝 Implementing Next Analyzer (T-Invariants)

### Step 1: Create File (1 min)

```bash
cd src/shypn/topology/structural
cp p_invariants.py t_invariants.py
```

### Step 2: Modify Class (30 min)

```python
# In t_invariants.py
from shypn.topology.base import TopologyAnalyzer, AnalysisResult
import numpy as np
from scipy.linalg import null_space

class TInvariantAnalyzer(TopologyAnalyzer):
    """Analyzer for T-Invariants (Transition Invariants).
    
    T-invariants are firing sequences that return the net to its
    initial marking. They represent reproducible behaviors.
    
    Mathematical: Find vectors x where C·x = 0
    (C is the incidence matrix)
    """
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Find T-invariants in the Petri net.
        
        Returns:
            AnalysisResult with:
                - invariants: List of T-invariant vectors
                - count: Number of invariants
                - summary: Human-readable description
        """
        try:
            # Get incidence matrix
            C = self._get_incidence_matrix()
            
            # Find null space of C (not C^T like P-invariants)
            null = null_space(C)
            
            # Convert to non-negative integer vectors
            invariants = self._convert_to_nonneg_int(null)
            
            # Analyze each invariant
            invariant_data = []
            for inv_vector in invariants:
                info = self._analyze_invariant(inv_vector)
                invariant_data.append(info)
            
            summary = self._create_summary(len(invariants))
            
            return AnalysisResult(
                success=True,
                data={
                    'invariants': invariant_data,
                    'count': len(invariants),
                },
                summary=summary
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"T-Invariant analysis failed: {str(e)}"]
            )
    
    def _get_incidence_matrix(self):
        """Get incidence matrix from model."""
        # Use existing matrix module
        from shypn.matrix.dense import DenseMatrixBuilder
        builder = DenseMatrixBuilder(self.model)
        return builder.build_incidence_matrix()
    
    def _analyze_invariant(self, vector):
        """Analyze a single T-invariant."""
        # Get transitions with non-zero coefficients
        transitions = []
        for i, coeff in enumerate(vector):
            if coeff > 0:
                trans = self.model.transitions[i]
                transitions.append({
                    'id': trans.id,
                    'name': trans.name,
                    'coefficient': int(coeff)
                })
        
        return {
            'transitions': transitions,
            'size': len(transitions),
            'type': self._classify_invariant(transitions)
        }
```

### Step 3: Export (1 min)

```python
# In structural/__init__.py
from .p_invariants import PInvariantAnalyzer
from .t_invariants import TInvariantAnalyzer  # ADD THIS

__all__ = ['PInvariantAnalyzer', 'TInvariantAnalyzer']  # ADD TInvariantAnalyzer
```

### Step 4: Test (30 min)

```python
# Create tests/topology/test_t_invariants.py
import pytest
from shypn.topology.structural.t_invariants import TInvariantAnalyzer

def test_t_invariant_simple_cycle():
    """Test T-invariant on simple cycle."""
    # Create model with P1→T1→P2→T2→P1
    model = create_simple_cycle_model()
    
    analyzer = TInvariantAnalyzer(model)
    result = analyzer.analyze()
    
    assert result.success
    assert result.get('count') > 0
    
    # Verify invariant structure
    invariants = result.get('invariants', [])
    assert len(invariants) > 0
    assert 'transitions' in invariants[0]
```

### Step 5: Integration (5 min)

The topology tab loaders will automatically pick up the new analyzer! Just ensure it's exported in `__init__.py`.

**Test it**:
```bash
python3 src/shypn.py
# Open model → Open transition dialog → Check Topology tab
# Should now show T-Invariant info!
```

---

## 📚 Key Files Reference

### Implementation Files
```
src/shypn/topology/
├── base/
│   ├── topology_analyzer.py    # Base class - inherit from this
│   └── analysis_result.py      # Return this from analyze()
│
├── structural/
│   ├── p_invariants.py         # REFERENCE: Copy this pattern
│   └── t_invariants.py         # NEXT: Create this
│
├── graph/
│   └── cycles.py               # REFERENCE: Good example of graph analysis
│
└── network/
    └── hubs.py                 # REFERENCE: Wrapping existing code
```

### Integration Files (Don't modify - already done!)
```
src/shypn/helpers/
├── place_prop_dialog_loader.py      # Has _setup_topology_tab()
├── transition_prop_dialog_loader.py # Has _setup_topology_tab()
└── arc_prop_dialog_loader.py        # Has _setup_topology_tab()

src/shypn/ui/
└── topology_tab_loader.py           # Auto-loads all analyzers
```

### Documentation
```
doc/topology/
├── README.md                        # Start here
├── CURRENT_STATUS.md                # Detailed progress
├── TOPOLOGY_INTEGRATION_RECOVERY_PLAN.md  # Full context
└── IMPLEMENTATION_PLAN_OPTION_A.md  # Complete technical plan

doc/
└── TOPOLOGY_TOOLS_PALETTE_PLAN.md   # Full specification (16 tools)
```

---

## 🎯 Priority Order

Implement in this order for maximum value:

1. **T-Invariants** (4-6h) - Completes structural pair with P-Invariants
2. **SCCs** (4-5h) - Wrap existing code, high value
3. **Liveness** (8-10h) - Critical for Petri net analysis
4. **Deadlock** (6-8h) - Pairs with Liveness
5. **Boundedness** (8-10h) - Safety property
6. **Siphons & Traps** (10-14h) - Structural properties
7. **Reachability** (10-12h) - Foundation for behavioral
8. **Centrality** (6-8h) - Network importance
9. **DAG** (3-4h) - Quick win, useful for hierarchies
10. **Communities** (6-8h) - Modularity
11. **Clustering** (3-4h) - Quick win, network property

Total: ~80-100 hours (~2-3 weeks full-time)

---

## 💡 Pro Tips

### Reuse Existing Code
```python
# For SCCs
from shypn.layout.sscc.scc_detector import SCCDetector

class SCCAnalyzer(TopologyAnalyzer):
    def analyze(self):
        detector = SCCDetector(self.model)
        sccs = detector.detect()  # Wrap existing!
        return AnalysisResult(success=True, data={'sccs': sccs})
```

### Use NetworkX
```python
import networkx as nx

def analyze(self):
    # Build graph
    G = nx.DiGraph()
    for place in self.model.places:
        G.add_node(place.id, type='place')
    # ... add edges ...
    
    # Use NetworkX algorithms
    cycles = list(nx.simple_cycles(G))
    paths = nx.shortest_path(G, source, target)
    centrality = nx.betweenness_centrality(G)
```

### Error Handling Pattern
```python
def analyze(self):
    try:
        # Main logic
        result_data = self._do_analysis()
        
        return AnalysisResult(
            success=True,
            data=result_data,
            summary=self._create_summary(result_data)
        )
    
    except ValueError as e:
        return AnalysisResult(
            success=False,
            errors=[f"Invalid input: {str(e)}"]
        )
    
    except Exception as e:
        return AnalysisResult(
            success=False,
            errors=[f"Analysis failed: {str(e)}"],
            warnings=["Unexpected error - please report"]
        )
```

---

## 🧪 Testing Commands

```bash
# Run all topology tests
python3 -m pytest tests/topology/ -v

# Run specific test
python3 -m pytest tests/topology/test_t_invariants.py -v

# Run with coverage
python3 -m pytest tests/topology/ --cov=src/shypn/topology --cov-report=html

# Quick integration test
python3 << 'EOF'
from shypn.topology.structural.t_invariants import TInvariantAnalyzer
# Create test model...
analyzer = TInvariantAnalyzer(model)
result = analyzer.analyze()
print(result.summary)
EOF
```

---

## 📞 Need Help?

### Key Algorithms
- **T-Invariants**: Null space of C (not C^T)
- **Liveness**: Reachability graph analysis (Murata 1989)
- **Boundedness**: Coverability tree
- **Siphons**: ∀p∈S: •p ⊆ S•
- **Traps**: ∀p∈S: S• ⊆ •p

### Reference Code
- P-Invariants: `src/shypn/topology/structural/p_invariants.py`
- Cycles: `src/shypn/topology/graph/cycles.py`
- Matrix operations: `src/shypn/matrix/dense.py`

### Documentation
- Full spec: `doc/TOPOLOGY_TOOLS_PALETTE_PLAN.md`
- Each tool has detailed description, algorithm, output format

---

**TL;DR**: Copy `p_invariants.py` → rename to `t_invariants.py` → change algorithm from `null_space(C.T)` to `null_space(C)` → export in `__init__.py` → test → done! The topology tab will automatically show results.

**Estimated time**: 4-6 hours for T-Invariants, then repeat pattern for other analyzers.

---

**Last Updated**: December 2024  
**Quick Links**:
- Status: `doc/topology/CURRENT_STATUS.md`
- Plan: `doc/topology/IMPLEMENTATION_PLAN_OPTION_A.md`
- Spec: `doc/TOPOLOGY_TOOLS_PALETTE_PLAN.md`
