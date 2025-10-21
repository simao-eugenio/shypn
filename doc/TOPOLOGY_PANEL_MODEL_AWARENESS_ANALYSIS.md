# Topology Panel Model Awareness Analysis

**Date:** October 20, 2025  
**Topic:** Architecture analysis of how Topology Panel connects to canvas model, signaling, and state management

---

## Executive Summary

The Topology Panel's analysis algorithms connect to the canvas model through a **lazy-loading, on-demand architecture** that retrieves the current model at analysis time rather than maintaining persistent references. This design is clean but **incomplete** - it lacks proper signaling integration for model changes and has no mechanism to invalidate cached results when the model is modified.

**Status:** 🟡 **PARTIALLY IMPLEMENTED**
- ✅ Basic model access works (via `model_canvas_loader`)
- ⚠️ No model change signals/observers
- ⚠️ No cache invalidation
- ⚠️ No state synchronization with canvas

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         shypn.py (Main App)                      │
│                                                                   │
│  topology_panel_loader = TopologyPanelLoader(model=None)        │
│  topology_panel_loader.controller.model_canvas_loader =         │
│      model_canvas_loader  ← WIRES MODEL ACCESS                  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              TopologyPanelLoader (Minimal Wrapper)               │
│                                                                   │
│  • Loads UI (12 expanders)                                       │
│  • Creates controller                                            │
│  • Wires expander signals → controller                          │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│         TopologyPanelController (Business Logic)                 │
│                                                                   │
│  self.model_canvas_loader = None  ← SET EXTERNALLY              │
│  self.results = {}                 ← CACHED RESULTS              │
│  self.analyzing = set()            ← ACTIVE ANALYSES             │
│                                                                   │
│  on_expander_toggled(expander, param, analyzer_name)            │
│    ├─ Check if expanded                                          │
│    ├─ Check cache                                                │
│    └─ _trigger_analysis(analyzer_name) if needed                │
│                                                                   │
│  _trigger_analysis(analyzer_name)                                │
│    ├─ Show spinner                                               │
│    └─ threading.Thread → _run_analysis()                         │
│                                                                   │
│  _run_analysis(analyzer_name) [BACKGROUND THREAD]                │
│    ├─ model = self._get_current_model()  ← FETCH MODEL HERE     │
│    ├─ analyzer = AnalyzerClass(model)                            │
│    └─ result = analyzer.analyze()                                │
│                                                                   │
│  _get_current_model()                                            │
│    └─ return model_canvas_loader.get_current_model() ← MISSING! │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│           ModelCanvasLoader (Canvas Management)                  │
│                                                                   │
│  self.canvas_managers = {}  # {drawing_area: manager}           │
│  self.notebook                                                   │
│                                                                   │
│  get_canvas_manager(drawing_area=None) ✅ EXISTS                │
│    ├─ If drawing_area is None, use current                      │
│    └─ Return canvas_managers.get(drawing_area)                  │
│                                                                   │
│  get_current_document() ✅ EXISTS                                │
│    └─ Return currently active drawing_area                      │
│                                                                   │
│  get_current_model() ❌ MISSING!                                 │
│    └─ Should return: get_canvas_manager().model                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│         ModelCanvasManager (Per-Tab Canvas State)                │
│                                                                   │
│  self.places = []         ← PETRI NET MODEL                      │
│  self.transitions = []                                           │
│  self.arcs = []                                                  │
│  self.filename = None                                            │
│                                                                   │
│  Model Properties (Duck-Typed Interface):                        │
│  • places: List[Place]                                           │
│  • transitions: List[Transition]                                 │
│  • arcs: List[Arc]                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current Implementation

### 1. Model Access Pattern (Lazy Loading)

**File:** `src/shypn/ui/topology_panel_controller.py`

```python
def _get_current_model(self):
    """Get current model from model_canvas_loader.
    
    Returns:
        Current ShypnModel instance or None
    """
    if self.model_canvas_loader and hasattr(self.model_canvas_loader, 'get_current_model'):
        return self.model_canvas_loader.get_current_model()  # ❌ METHOD DOESN'T EXIST!
    return self.model
```

**Problem:** `model_canvas_loader.get_current_model()` method **does not exist**!

**What Actually Works:**
```python
# Working approach (used by other panels):
drawing_area = model_canvas_loader.get_current_document()
canvas_manager = model_canvas_loader.get_canvas_manager(drawing_area)
# canvas_manager IS the model (has places, transitions, arcs)
```

### 2. Analyzer Interface

**File:** `src/shypn/topology/base/topology_analyzer.py`

All analyzers inherit from `TopologyAnalyzer` and expect:

```python
class TopologyAnalyzer(ABC):
    def __init__(self, model: Any):
        """
        Args:
            model: PetriNetModel instance with:
                - places: List[Place]
                - transitions: List[Transition]
                - arcs: List[Arc]
        """
        if model is None:
            raise InvalidModelError("Model cannot be None")
        self.model = model
        self._validate_model()
    
    def _validate_model(self):
        """Validate model structure."""
        if not hasattr(self.model, 'places'):
            raise InvalidModelError("Model missing 'places' attribute")
        if not hasattr(self.model, 'transitions'):
            raise InvalidModelError("Model missing 'transitions' attribute")
        if not hasattr(self.model, 'arcs'):
            raise InvalidModelError("Model missing 'arcs' attribute")
    
    @abstractmethod
    def analyze(self, **kwargs) -> AnalysisResult:
        """Perform topology analysis."""
        pass
```

**Key Insight:** Analyzers use **duck-typing** - they don't care about the exact model class, only that it has `places`, `transitions`, and `arcs` attributes.

**✅ `ModelCanvasManager` already satisfies this interface!**

### 3. Example: P-Invariants Analyzer

**File:** `src/shypn/topology/structural/p_invariants.py`

```python
class PInvariantAnalyzer(TopologyAnalyzer):
    def analyze(self, min_support=1, max_invariants=100, normalize=True):
        # 1. Build incidence matrix from model.places, model.transitions, model.arcs
        incidence_matrix, place_map, transition_map = self._build_incidence_matrix()
        
        # 2. Compute kernel (null space of C^T)
        invariant_vectors = self._compute_invariants(incidence_matrix.T)
        
        # 3. Analyze each invariant
        for inv_vector in invariant_vectors:
            inv_info = self._analyze_invariant(inv_vector, place_map)
            # Accesses: place.id, place.name, place.tokens
        
        # 4. Return AnalysisResult
        return AnalysisResult(
            success=True,
            data={'p_invariants': p_invariants, ...},
            summary="...",
            metadata={...}
        )
    
    def _build_incidence_matrix(self):
        """Build C matrix from model.places, model.transitions, model.arcs."""
        place_map = {p.id: i for i, p in enumerate(self.model.places)}
        transition_map = {t.id: i for i, t in enumerate(self.model.transitions)}
        
        # Parse arcs to fill matrix
        for arc in self.model.arcs:
            weight = getattr(arc, 'weight', 1)
            # Check arc type and update matrix...
```

**Model Access Points:**
- `self.model.places` - List of Place objects with `.id`, `.name`, `.tokens`
- `self.model.transitions` - List of Transition objects with `.id`
- `self.model.arcs` - List of Arc objects with `.source_id`, `.target_id`, `.weight`

---

## Missing Pieces

### 1. ❌ `get_current_model()` Method

**Problem:** Controller calls a non-existent method.

**Solution:** Add to `ModelCanvasLoader`:

```python
def get_current_model(self):
    """Get the current canvas manager (which IS the model).
    
    Returns:
        ModelCanvasManager: The active canvas manager (has places, transitions, arcs),
                           or None if no document is open.
    """
    drawing_area = self.get_current_document()
    if drawing_area is None:
        return None
    return self.get_canvas_manager(drawing_area)
```

**Why This Works:**
- `ModelCanvasManager` has `places`, `transitions`, `arcs` attributes
- Satisfies analyzer's duck-typed interface
- No extra wrapper needed!

### 2. ❌ No Model Change Signals

**Problem:** When user modifies model (add/remove place, change arc weight), topology panel doesn't know to invalidate cache.

**Current Behavior:**
```
1. User expands P-Invariants → Analysis runs → Result cached
2. User adds a new place on canvas
3. User collapses/re-expands P-Invariants → Shows OLD cached result ❌
```

**What's Missing:**
- No signal from `ModelCanvasManager` when model changes
- No observer pattern between canvas and topology panel
- No cache invalidation mechanism

**Proposed Solution:**

#### Option A: Signal-Based (Clean)

Add signals to `ModelCanvasManager`:

```python
class ModelCanvasManager:
    def __init__(self, ...):
        self.model_changed_callbacks = []  # List of callbacks
    
    def register_model_change_observer(self, callback):
        """Register callback to be called when model changes."""
        self.model_changed_callbacks.append(callback)
    
    def _notify_model_changed(self):
        """Call all registered observers."""
        for callback in self.model_changed_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in model change callback: {e}")
    
    def add_place(self, x, y):
        place = Place(...)
        self.places.append(place)
        self._notify_model_changed()  # ← NOTIFY
        return place
    
    def remove_place(self, place):
        self.places.remove(place)
        self._notify_model_changed()  # ← NOTIFY
    
    # ... same for transitions, arcs, weight changes, etc.
```

Wire topology panel controller:

```python
# In shypn.py:
if hasattr(topology_panel_loader, 'controller'):
    topology_panel_loader.controller.model_canvas_loader = model_canvas_loader
    
    # Register for model changes
    def on_model_changed():
        topology_panel_loader.controller.invalidate_all_caches()
    
    # Need to register per-canvas (when tabs switch)
    model_canvas_loader.register_topology_observer(on_model_changed)
```

#### Option B: Polling-Based (Simple but inefficient)

```python
def _run_analysis(self, analyzer_name):
    """Run analysis (always fresh - ignore cache)."""
    # Always fetch fresh model
    model = self._get_current_model()
    
    # Check if result is stale by comparing model state
    if analyzer_name in self.results:
        cached_model_hash = self.results[analyzer_name].get('_model_hash')
        current_model_hash = self._compute_model_hash(model)
        if cached_model_hash == current_model_hash:
            return self.results[analyzer_name]  # Use cache
    
    # Fresh analysis
    analyzer = self.analyzers[analyzer_name](model)
    result = analyzer.analyze()
    result['_model_hash'] = self._compute_model_hash(model)
    return result

def _compute_model_hash(self, model):
    """Compute hash of model state."""
    return (
        len(model.places),
        len(model.transitions),
        len(model.arcs),
        # Could include more: place tokens, arc weights, etc.
    )
```

### 3. ❌ No Multi-Tab Awareness

**Problem:** Cache is global across all tabs, but each tab has its own model.

**Scenario:**
```
Tab 1 (ModelA.shy): Expand P-Invariants → Result cached
Switch to Tab 2 (ModelB.shy)
Tab 2: Expand P-Invariants → Shows cached result from ModelA! ❌
```

**Solution:** Key cache by drawing_area:

```python
class TopologyPanelController:
    def __init__(self, ...):
        self.results = {}  # {drawing_area: {analyzer_name: result}}
        self.analyzing = {}  # {drawing_area: set(analyzer_names)}
    
    def _trigger_analysis(self, analyzer_name):
        # Get current canvas
        drawing_area = self.model_canvas_loader.get_current_document()
        
        # Initialize cache for this canvas if needed
        if drawing_area not in self.results:
            self.results[drawing_area] = {}
            self.analyzing[drawing_area] = set()
        
        # Check cache for THIS canvas
        if analyzer_name in self.results[drawing_area]:
            return  # Already cached for this canvas
        
        # Mark as analyzing
        self.analyzing[drawing_area].add(analyzer_name)
        
        # Run analysis...
```

---

## State Management Issues

### Current State Flow

```
User Action (Canvas)                    Topology Panel
─────────────────────                   ──────────────
Add Place                               [No notification]
  ↓
ModelCanvasManager.places.append()      [Cache still valid]
  ↓
Canvas redraws                          [Shows old result if expanded]
  ↓
[No signal sent]
```

**Problems:**
1. **No notification** when model changes
2. **Stale cache** shows incorrect results
3. **No visual feedback** that results are outdated

### Desired State Flow

```
User Action (Canvas)                    Topology Panel
─────────────────────                   ──────────────
Add Place                               [Listening...]
  ↓
ModelCanvasManager.add_place()
  ↓
_notify_model_changed()  ────────────→  on_model_changed()
  ↓                                       ↓
Canvas redraws                          invalidate_cache(drawing_area)
                                          ↓
                                        Show "⚠ Model changed. Re-expand to update."
```

---

## Recommendations

### Priority 1: Fix `get_current_model()` (CRITICAL)

**Impact:** Analysis currently **cannot run** without this fix.

**Implementation:** Add method to `ModelCanvasLoader`:

```python
def get_current_model(self):
    """Get current canvas manager (which is the model)."""
    drawing_area = self.get_current_document()
    if drawing_area is None:
        return None
    return self.get_canvas_manager(drawing_area)
```

**Estimated Time:** 5 minutes

---

### Priority 2: Add Per-Tab Cache Keying (HIGH)

**Impact:** Prevents showing wrong results when switching tabs.

**Implementation:** Key cache by `drawing_area`:

```python
self.results = {}  # {drawing_area: {analyzer_name: result}}
```

**Estimated Time:** 30 minutes

---

### Priority 3: Implement Model Change Signals (MEDIUM)

**Impact:** Prevents stale results after model edits.

**Implementation:**
1. Add `model_changed_callbacks` to `ModelCanvasManager`
2. Call `_notify_model_changed()` in all mutating methods
3. Register topology panel as observer
4. Invalidate cache on notification

**Estimated Time:** 2-3 hours

---

### Priority 4: Add Staleness Indicators (LOW)

**Impact:** User experience improvement.

**Implementation:**
- Show "⚠ Model changed since last analysis" in cached results
- Add timestamp to results
- Show "Analysis from 2 minutes ago" in report

**Estimated Time:** 1 hour

---

## Testing Strategy

### Unit Tests Needed

1. **Test `get_current_model()` returns correct canvas manager**
   ```python
   loader = ModelCanvasLoader()
   loader.add_document("test.shy")
   model = loader.get_current_model()
   assert model is not None
   assert hasattr(model, 'places')
   ```

2. **Test per-tab cache isolation**
   ```python
   # Add two tabs
   loader.add_document("model1.shy")
   loader.add_document("model2.shy")
   
   # Analyze on tab 1
   controller.on_expander_toggled(..., 'p_invariants')
   result1 = controller.results[drawing_area1]['p_invariants']
   
   # Switch to tab 2
   loader.notebook.set_current_page(1)
   
   # Analyze on tab 2
   controller.on_expander_toggled(..., 'p_invariants')
   result2 = controller.results[drawing_area2]['p_invariants']
   
   assert result1 != result2  # Different results for different models
   ```

3. **Test cache invalidation on model change**
   ```python
   # Analyze
   controller.on_expander_toggled(..., 'p_invariants')
   assert 'p_invariants' in controller.results[drawing_area]
   
   # Modify model
   manager.add_place(100, 100)
   
   # Cache should be invalidated
   assert 'p_invariants' not in controller.results[drawing_area]
   ```

### Integration Tests Needed

1. **Test end-to-end analysis with real model**
   - Load SBML model
   - Expand P-Invariants
   - Verify result format
   - Add place
   - Re-expand
   - Verify new result

2. **Test multi-tab switching**
   - Open two different models
   - Run same analysis on both
   - Switch tabs
   - Verify correct results displayed

---

## API Contract Summary

### What Analyzers Expect from Model

```python
model.places: List[Place]
    - place.id: int
    - place.name: str
    - place.tokens: int (or float)
    - place.x, place.y: float (optional, for layout)

model.transitions: List[Transition]
    - transition.id: int
    - transition.name: str
    - transition.x, transition.y: float (optional)

model.arcs: List[Arc]
    - arc.source_id: int (place or transition ID)
    - arc.target_id: int (place or transition ID)
    - arc.weight: int (default 1)
    - arc.type: str (optional: 'normal', 'inhibitor', 'test')
```

### What `ModelCanvasManager` Provides

```python
✅ manager.places: List[Place]
✅ manager.transitions: List[Transition]
✅ manager.arcs: List[Arc]
✅ All required attributes present
✅ Duck-typing compatible with TopologyAnalyzer interface
```

**Compatibility:** ✅ **PERFECT MATCH** - No adapter layer needed!

---

## Conclusion

The Topology Panel's model awareness architecture is **well-designed** at its core but **incomplete** in execution:

**Strengths:**
- ✅ Clean separation: analyzers don't depend on GTK
- ✅ Duck-typed interface allows flexibility
- ✅ Background threading keeps UI responsive
- ✅ Caching prevents redundant computation

**Critical Missing Pieces:**
- ❌ `get_current_model()` method doesn't exist (BLOCKER)
- ❌ No per-tab cache keying (INCORRECT RESULTS)
- ❌ No model change signals (STALE DATA)
- ❌ No cache invalidation strategy

**Recommended Path Forward:**
1. **Immediate:** Add `get_current_model()` method (5 min)
2. **Short-term:** Key cache by drawing_area (30 min)
3. **Medium-term:** Implement model change observers (2-3 hours)
4. **Long-term:** Add staleness indicators and timestamps (1 hour)

**Total Estimated Time to Complete:** ~4 hours

Once these pieces are in place, the topology panel will have **full model awareness** with proper signaling and state synchronization. 🎯

---

## Appendix: Code Examples

### Example: Complete Model Access Pattern

```python
# In TopologyPanelController._run_analysis()

def _run_analysis(self, analyzer_name):
    """Run analysis with proper model access."""
    # Get current drawing area
    if not self.model_canvas_loader:
        raise Exception("No canvas loader available")
    
    drawing_area = self.model_canvas_loader.get_current_document()
    if not drawing_area:
        raise Exception("No document open")
    
    # Get canvas manager (which IS the model)
    canvas_manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
    if not canvas_manager:
        raise Exception("No canvas manager found")
    
    # Validate model structure
    if not hasattr(canvas_manager, 'places'):
        raise Exception("Canvas manager missing 'places' attribute")
    if not hasattr(canvas_manager, 'transitions'):
        raise Exception("Canvas manager missing 'transitions' attribute")
    if not hasattr(canvas_manager, 'arcs'):
        raise Exception("Canvas manager missing 'arcs' attribute")
    
    # Create analyzer with canvas_manager as model
    analyzer_class = self.analyzers.get(analyzer_name)
    analyzer = analyzer_class(canvas_manager)  # ← CANVAS MANAGER IS THE MODEL!
    
    # Run analysis
    result = analyzer.analyze()
    
    return result
```

### Example: Observer Registration

```python
# In shypn.py main application

def on_activate(a):
    # ... create topology panel ...
    
    if topology_panel_loader and topology_panel_loader.controller:
        # Wire model access
        topology_panel_loader.controller.model_canvas_loader = model_canvas_loader
        
        # Register for model changes (when implemented)
        def on_any_model_changed(drawing_area):
            """Called when any canvas model changes."""
            topology_panel_loader.controller.invalidate_cache(drawing_area)
        
        # This would require adding to ModelCanvasLoader:
        # model_canvas_loader.register_model_observer(on_any_model_changed)
```

---

**Document Status:** ✅ Complete  
**Next Action:** Implement Priority 1 fix (`get_current_model()` method)
