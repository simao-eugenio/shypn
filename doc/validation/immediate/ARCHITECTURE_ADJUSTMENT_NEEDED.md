# Test Infrastructure - Architecture Adjustment Required

**Date**: 2025-01-XX  
**Status**: ⚠️ NEEDS ADJUSTMENT - Wrong Model Type Used

---

## Problem Identified

The test infrastructure was built using `DocumentModel`, but the `SimulationController` expects `ModelCanvasManager`.

### What Was Built
```python
# In conftest.py (CURRENT - INCORRECT)
from shypn.data.canvas.document_model import DocumentModel

model = DocumentModel()
P1 = model.create_place(...)
controller = SimulationController(model)  # ❌ Won't work
```

### What's Actually Needed
```python
# What SimulationController expects
from shypn.data.model_canvas_manager import ModelCanvasManager

manager = ModelCanvasManager()
# manager.places - list of Place objects
# manager.transitions - list of Transition objects  
# manager.arcs - list of Arc objects
controller = SimulationController(manager)  # ✅ Correct
```

---

## Architecture Analysis

### SimulationController API (Verified)
**Location**: `src/shypn/engine/simulation/controller.py`

```python
class SimulationController:
    """Controller for Petri net simulation execution."""
    
    def __init__(self, model):
        """
        Args:
            model: ModelCanvasManager instance (has places, transitions, arcs lists)
        """
        self.model = model  # Expects ModelCanvasManager
        self.time = 0.0
        # ...
    
    def step(self, time_step: float = None) -> bool:
        """Execute one simulation step."""
    
    def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
        """Start continuous simulation execution (uses GLib)."""
    
    def reset(self):
        """Reset simulation to initial state."""
```

**Key Findings**:
1. ✅ Controller exists at `shypn.engine.simulation.controller`
2. ⚠️ Expects `ModelCanvasManager`, not `DocumentModel`
3. ✅ Has `run()` method, but signature is different than assumed
4. ⚠️ Uses GLib for continuous simulation (requires GTK environment)
5. ✅ Has `step()` method for single-step execution (better for testing)

---

## Model Canvas Manager Structure

**Location**: `src/shypn/data/model_canvas_manager.py`

```python
class ModelCanvasManager:
    """Manages canvas properties, transformations, and rendering."""
    
    def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
        # ...
        self.document_controller = DocumentController(filename=filename)
        # ...
    
    # Object collections (delegated to document_controller)
    @property
    def places(self) -> List[Place]:
        """List of all places."""
        return self.document_controller.places
    
    @property
    def transitions(self) -> List[Transition]:
        """List of all transitions."""
        return self.document_controller.transitions
    
    @property
    def arcs(self) -> List[Arc]:
        """List of all arcs."""
        return self.document_controller.arcs
```

**Complexity**: ModelCanvasManager is a large facade handling:
- Viewport (zoom, pan)
- Grid rendering
- Selection management
- Transformation management
- Document metadata
- **Object collections** (places, transitions, arcs)

---

## Required Adjustments

### Option 1: Use ModelCanvasManager (Recommended)
**Pros**:
- Matches actual architecture
- Tests run against real simulation controller
- More realistic integration testing

**Cons**:
- Brings in unnecessary complexity (viewport, rendering, etc.)
- Heavier weight for unit tests

```python
# Updated conftest.py
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.netobjs import Place, Transition, Arc

@pytest.fixture
def ptp_model():
    # Create manager
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    
    # Access document_controller to create objects
    doc_ctrl = manager.document_controller
    P1 = doc_ctrl.create_place(x=100, y=100, label="P1")
    P1.tokens = 0
    # ...
    
    return manager, P1, T1, P2, A1, A2
```

### Option 2: Create Minimal Test Adapter
**Pros**:
- Lightweight for unit testing
- Only includes what's needed for simulation
- Faster test execution

**Cons**:
- Doesn't test against real architecture
- Need to maintain adapter compatibility

```python
# New test_adapter.py in tests/validation/immediate/
class MinimalModelAdapter:
    """Minimal adapter for testing SimulationController."""
    
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []
    
    def add_place(self, place):
        self.places.append(place)
    
    def add_transition(self, transition):
        self.transitions.append(transition)
    
    def add_arc(self, arc):
        self.arcs.append(arc)
```

### Option 3: Use DocumentController Directly
**Pros**:
- Middle ground - lighter than ModelCanvasManager
- Still part of actual architecture
- Has object management methods

**Cons**:
- SimulationController expects ModelCanvasManager, not DocumentController
- Would need wrapper or modification

```python
# Might need wrapper
class SimulationTestWrapper:
    def __init__(self):
        self.document_controller = DocumentController()
    
    @property
    def places(self):
        return self.document_controller.places
    
    @property
    def transitions(self):
        return self.document_controller.transitions
    
    @property  
    def arcs(self):
        return self.document_controller.arcs
```

---

## Recommendation: Option 1 (Use ModelCanvasManager)

**Rationale**:
1. Tests actual integration with simulation controller
2. Verifies compatibility with real architecture
3. Discovers issues early
4. ModelCanvasManager provides clean facade despite complexity

**Implementation Steps**:
1. Update both `conftest.py` files to use `ModelCanvasManager`
2. Use `manager.document_controller` to create objects
3. Update `run_simulation` fixture to use `step()` instead of `run()`
4. Remove GLib dependency by using step-based execution

---

## Updated Fixture Pattern

```python
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

@pytest.fixture
def ptp_model():
    """Create P-T-P model using actual architecture."""
    manager = ModelCanvasManager()
    doc_ctrl = manager.document_controller
    
    # Create objects through document controller
    P1 = doc_ctrl.create_place(x=100, y=100, label="P1")
    P1.tokens = 0
    
    T1 = doc_ctrl.create_transition(x=200, y=100, label="T1")
    T1.ttype = "immediate"  # Check actual attribute name!
    
    P2 = doc_ctrl.create_place(x=300, y=100, label="P2")
    P2.tokens = 0
    
    # Create arcs
    A1 = doc_ctrl.create_arc(source=P1, target=T1, weight=1)
    A2 = doc_ctrl.create_arc(source=T1, target=P2, weight=1)
    
    return manager, P1, T1, P2, A1, A2


@pytest.fixture
def run_simulation():
    """Run simulation using step-based execution."""
    def _run(manager, max_time=10.0, max_firings=None):
        controller = SimulationController(manager)
        
        firings = []
        steps = 0
        max_steps = max_firings if max_firings else 10000
        
        # Step-based execution (no GLib dependency)
        while controller.time < max_time and steps < max_steps:
            fired = controller.step(time_step=0.001)
            if fired:
                firings.append({'time': controller.time})
            steps += 1
            
            # Safety: break if no progress
            if steps > max_steps:
                break
        
        return {
            'firings': firings,
            'final_time': controller.time,
            'places': {p.name: p.tokens for p in manager.places}
        }
    
    return _run
```

---

## Next Actions

### 1. Investigate Transition Type Attribute
```bash
# Find correct attribute name
grep -A 10 "class Transition" src/shypn/netobjs/transition.py
grep "immediate" src/shypn/netobjs/transition.py
```

### 2. Test DocumentController API
```bash
# Find create_place, create_transition methods
grep "def create_place\|def create_transition" src/shypn/core/controllers/document_controller.py
```

### 3. Understand Step Execution
```bash
# Check how step() works
grep -A 30 "def step" src/shypn/engine/simulation/controller.py
```

### 4. Update Test Files
- Fix `/tests/validation/immediate/conftest.py`
- Fix `/tests/benchmark/immediate/conftest.py`
- Update imports and fixture implementations
- Run test discovery to verify

---

## Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Directory Structure | ✅ Complete | All directories created |
| Documentation | ✅ Complete | READMEs, plans, methodology |
| Test Files | ✅ Written | 6 validation + 5 benchmark tests |
| Imports | ⚠️ Wrong Model | Using DocumentModel instead of ModelCanvasManager |
| SimulationController | ✅ Found | At `shypn.engine.simulation.controller` |
| API Understanding | ⚠️ Partial | Know structure, need details |
| Test Execution | ❌ Blocked | Can't run until model type fixed |

---

**Next Step**: Update conftest.py files to use ModelCanvasManager and verify DocumentController API.
