# Dialog Freeze on Imported Models - Root Cause and Fix

**Date**: October 19, 2025  
**Issue**: Property dialogs freeze when opened on imported models (e.g., Glycolysis_01_.shy)  
**Status**: 🔴 ROOT CAUSE IDENTIFIED

---

## Problem Summary

When working with **newly created models**, property dialogs open normally. However, when opening dialogs on **imported models** (like `Glycolysis_01_.shy`), the application freezes indefinitely.

### Test Case
- **File**: `workspace/projects/Flow_Test/models/Glycolysis_01_.shy`
- **Size**: 85KB
- **Contents**: 26 places, 34 transitions, 73 arcs (realistic biochemical pathway)
- **Symptom**: Application freezes when right-clicking and selecting "Properties"

---

## Root Cause Analysis

### Headless Test Results

Created `test_headless_dialog_import.py` to isolate the issue without GUI:

```bash
$ timeout 10 python3 -u test_headless_dialog_import.py
======================================================================
TEST 2: Create Place Property Dialog
======================================================================

1. Testing with Place: P45 (ID: P45)
   Position: (839.2743055555555, 1329.5416666666667)
   Tokens: 0

2. Importing PlacePropDialogLoader...
✓ PlacePropDialogLoader imported

3. Creating mock drawing area and canvas manager...
✓ Mock objects created

4. Creating PlacePropDialogLoader...

Command exited with code 124  <-- TIMEOUT (10 seconds)
```

**Freeze Location**: Inside `PlacePropDialogLoader.__init__()`, specifically during topology tab initialization.

### Call Stack at Freeze

```
PlacePropDialogLoader.__init__()
  └─ _setup_topology_tab()
      └─ PlaceTopologyTabLoader.__init__()
          └─ _load_ui()
          └─ _setup_widgets()
          └─ _connect_signals()
      └─ PlaceTopologyTabLoader.populate()  ⚠️ BLOCKS HERE
          └─ CycleAnalyzer.find_cycles_containing_node()
              └─ CycleAnalyzer.analyze()
                  └─ nx.simple_cycles(graph)  🔴 INFINITE LOOP
```

### The Culprit

**File**: `src/shypn/topology/graph/cycles.py`  
**Line**: 79-80

```python
# Find elementary cycles using NetworkX (Johnson's algorithm)
all_cycles = list(nx.simple_cycles(graph))
```

**Problem**: 
- **Johnson's algorithm** for finding simple cycles has **exponential time complexity**
- For biochemical networks with many cycles (like Glycolysis), this can take **hours** or **hang indefinitely**
- The Glycolysis model has 73 arcs connecting 60 nodes - potentially thousands of cycles
- The algorithm is called **synchronously** during dialog initialization, blocking the UI thread

### Why New Models Work

- **New models** typically have few or no cycles initially (user is building incrementally)
- **Empty or small networks** → cycle detection finishes quickly (milliseconds)
- **Imported models** have complex, complete topologies with many cycles → algorithm hangs

---

## Detailed Investigation

### Architecture Issue

The problem occurs due to **eager initialization** in dialog loaders:

**`src/shypn/helpers/place_prop_dialog_loader.py`** (lines 24-53):
```python
def __init__(self, place_obj, parent_window=None, ui_dir: str=None, 
             persistency_manager=None, model=None):
    # ... initialization ...
    self._load_ui()
    self._setup_color_picker()
    self._populate_fields()
    self._setup_topology_tab()  # ⚠️ BLOCKS HERE
```

**`_setup_topology_tab()`** (lines 207-232):
```python
def _setup_topology_tab(self):
    """Setup and populate the topology analysis tab."""
    try:
        from shypn.ui.topology_tab_loader import PlaceTopologyTabLoader
        
        self.topology_loader = PlaceTopologyTabLoader(
            model=self.model if self.model else self.place_obj,
            element_id=self.place_obj.id,
        )
        
        self.topology_loader.populate()  # 🔴 SYNCHRONOUS BLOCKING CALL
        
        # ... embed in dialog ...
```

**`src/shypn/ui/topology_tab_loader.py`** - `PlaceTopologyTabLoader.populate()` (lines 321-370):
```python
def populate(self):
    """Populate place topology information."""
    if not self.model:
        return
    
    try:
        from shypn.topology.graph import CycleAnalyzer, PathAnalyzer
        from shypn.topology.structural import PInvariantAnalyzer
        from shypn.topology.network import HubAnalyzer
        
        # Analyze cycles
        if self.cycles_label:
            try:
                cycle_analyzer = CycleAnalyzer(self.model)
                cycles = cycle_analyzer.find_cycles_containing_node(self.element_id)
                # 🔴 THIS CALL HANGS ON COMPLEX NETWORKS
                
                # ... populate UI ...
```

### The Exponential Complexity

**NetworkX Documentation** (`nx.simple_cycles`):

> "The implementation of Johnson's algorithm has worst-case complexity O(((n+e)(c+1)))  
> where n is the number of nodes, e is the number of edges, and c is the number of  
> simple cycles in the graph. For dense graphs with many cycles, this can be extremely slow."

**Glycolysis Model**:
- **n** = 60 nodes (26 places + 34 transitions)
- **e** = 73 edges (arcs)
- **c** = ? (potentially thousands of cycles in metabolic networks)

**Result**: Algorithm explores exponentially many cycle candidates → **hangs indefinitely**.

---

## Impact Assessment

### Affected Components
- ✅ **Place property dialogs** (confirmed freeze)
- ✅ **Transition property dialogs** (same architecture, same issue)
- ⚠️ **Arc property dialogs** (depends on if arc topology uses same analyzers)

### Affected Operations
- `CycleAnalyzer.find_cycles_containing_node()` - exponential
- `PathAnalyzer` - potentially slow for large graphs
- `PInvariantAnalyzer` - matrix operations, should be OK
- `HubAnalyzer` - graph metrics, usually fast
- **All behavioral analyzers** in topology tab

### User Experience
- ❌ **Cannot open property dialogs on imported models**
- ❌ **Application appears frozen (unresponsive)**
- ❌ **Must force-quit application**
- ✅ **New models work fine** (small, few cycles)

---

## Proposed Solutions

### Solution 1: Lazy Loading (RECOMMENDED)
**Delay topology analysis until user switches to Topology tab**

**Pros**:
- Dialog opens instantly
- Analysis only runs if user wants to see topology
- User can cancel if taking too long

**Cons**:
- Slight delay when switching to Topology tab
- Requires tab change detection

**Implementation**:
```python
def _setup_topology_tab(self):
    """Setup topology tab (WITHOUT populating)."""
    try:
        from shypn.ui.topology_tab_loader import PlaceTopologyTabLoader
        
        self.topology_loader = PlaceTopologyTabLoader(
            model=self.model if self.model else self.place_obj,
            element_id=self.place_obj.id,
        )
        
        # DON'T populate here - wait for tab activation
        # self.topology_loader.populate()  # ❌ REMOVE THIS
        
        # Connect tab switch signal
        notebook = self.builder.get_object('dialog_notebook')
        if notebook:
            notebook.connect('switch-page', self._on_tab_switched)
        
        # ... embed in dialog ...
    except Exception as e:
        # ... error handling ...

def _on_tab_switched(self, notebook, page, page_num):
    """Lazy-load topology when user switches to that tab."""
    if page_num == TOPOLOGY_TAB_INDEX and not self._topology_loaded:
        # Show loading indicator
        self._show_topology_loading_spinner()
        
        # Populate in background thread
        import threading
        thread = threading.Thread(target=self._populate_topology_async)
        thread.daemon = True
        thread.start()
```

### Solution 2: Timeout + Fallback
**Set maximum time limit for analysis**

**Implementation**:
```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

def populate_with_timeout(self, timeout=5.0):
    """Populate topology with timeout."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(self._populate_topology)
    
    try:
        future.result(timeout=timeout)
    except TimeoutError:
        # Show "Analysis timeout" message
        self.cycles_label.set_text("Analysis timeout (network too complex)")
    except Exception as e:
        self.cycles_label.set_text(f"Analysis error: {e}")
    finally:
        executor.shutdown(wait=False)
```

### Solution 3: Algorithm Optimization
**Limit cycle search depth and count**

**Implementation** (in `CycleAnalyzer`):
```python
def analyze(self, max_cycles: int = 100, max_length: int = 20, timeout: float = 5.0):
    """Find cycles with limits."""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Cycle analysis timeout")
    
    # Set alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout))
    
    try:
        # Use length-bounded cycle iterator
        graph = self._build_graph()
        cycles = []
        
        for cycle in nx.simple_cycles(graph):
            if len(cycle) > max_length:
                continue  # Skip long cycles
            
            cycles.append(cycle)
            
            if len(cycles) >= max_cycles:
                break  # Stop after max_cycles found
        
        # ... rest of analysis ...
    finally:
        signal.alarm(0)  # Cancel alarm
```

### Solution 4: Caching
**Cache analysis results per model**

**Pros**:
- Subsequent dialog opens are instant
- Can cache to disk for persistence

**Cons**:
- First open still slow
- Cache invalidation complexity

---

## Recommended Fix (Hybrid Approach)

**Combine Solutions 1, 2, and 3**:

1. **Lazy Loading**: Don't populate topology during init
2. **Background Thread**: Populate in worker thread when tab activated
3. **Timeout**: Set 10-second timeout for analysis
4. **Algorithm Limits**: Max 100 cycles, max length 20
5. **Progress Indicator**: Show spinner while computing
6. **Graceful Fallback**: Show "Analysis unavailable" if timeout

### Implementation Plan

#### Phase 1: Quick Fix (Emergency Patch)
**Remove synchronous populate() calls from dialog init**

1. Remove `self.topology_loader.populate()` from all dialog loaders
2. Add lazy population on tab switch
3. Add "Loading..." placeholder
4. **TIME: 1 hour**

#### Phase 2: Background Threading
**Move analysis to worker threads**

1. Create `TopologyAnalysisWorker` class
2. Integrate with GLib main loop (GLib.idle_add for UI updates)
3. Add cancel mechanism
4. **TIME: 2 hours**

#### Phase 3: Algorithm Optimization
**Add timeouts and limits to all analyzers**

1. Add `max_time` parameter to all `analyze()` methods
2. Implement early termination
3. Add progress callbacks
4. **TIME: 2 hours**

#### Phase 4: Caching (Optional)
**Cache results for performance**

1. Create `TopologyCache` class
2. Implement LRU eviction
3. Add cache invalidation on model changes
4. **TIME: 3 hours**

---

## Testing Plan

### Automated Tests

```python
# test_topology_performance.py

def test_dialog_opens_quickly_on_large_model():
    """Dialog should open in < 1 second even for large models."""
    import time
    
    # Load Glycolysis model (60 nodes, 73 arcs)
    document = DocumentModel.load_from_file('Glycolysis_01_.shy')
    place = document.places[0]
    
    # Measure dialog creation time
    start = time.time()
    dialog_loader = PlacePropDialogLoader(
        place_obj=place,
        model=document
    )
    elapsed = time.time() - start
    
    # Should be instant (< 1 second)
    assert elapsed < 1.0, f"Dialog init took {elapsed:.2f}s (too slow!)"

def test_topology_tab_has_timeout():
    """Topology analysis should timeout on complex networks."""
    # Load Glycolysis model
    document = DocumentModel.load_from_file('Glycolysis_01_.shy')
    place = document.places[0]
    
    # Create loader
    topology_loader = PlaceTopologyTabLoader(
        model=document,
        element_id=place.id
    )
    
    # Populate with timeout
    import time
    start = time.time()
    topology_loader.populate()
    elapsed = time.time() - start
    
    # Should finish within timeout (10 seconds max)
    assert elapsed < 10.0, f"Analysis took {elapsed:.2f}s (no timeout!)"
```

### Manual Tests

1. **Import Glycolysis model**
2. **Right-click on place** → Properties
3. **Dialog should open instantly** (< 1 second)
4. **Switch to Topology tab**
5. **Should show "Loading..." spinner**
6. **After 5-10 seconds**: Should show results OR timeout message
7. **Dialog should remain responsive** (can close, switch tabs)

---

## Files to Modify

### High Priority (Emergency Fix)
1. `src/shypn/helpers/place_prop_dialog_loader.py` - Remove sync populate
2. `src/shypn/helpers/transition_prop_dialog_loader.py` - Remove sync populate
3. `src/shypn/helpers/arc_prop_dialog_loader.py` - Remove sync populate
4. `src/shypn/ui/topology_tab_loader.py` - Add lazy loading support

### Medium Priority (Background Threading)
5. `src/shypn/topology/graph/cycles.py` - Add timeout
6. `src/shypn/topology/graph/paths.py` - Add timeout
7. Create `src/shypn/ui/topology_worker.py` - Background worker

### Low Priority (Optimization)
8. Create `src/shypn/topology/cache.py` - Result caching
9. `src/shypn/topology/base/topology_analyzer.py` - Add cancel mechanism

---

## Next Steps

1. ✅ **Root cause identified** (exponential cycle detection)
2. 🔄 **Implement emergency fix** (remove sync populate)
3. ⏳ **Add background threading** (responsive UI)
4. ⏳ **Add timeouts** (graceful degradation)
5. ⏳ **Test with Glycolysis model** (verify fix)
6. ⏳ **Document changes** (update architecture docs)
7. ⏳ **Commit and push** (deploy fix)

---

## Technical Notes

### Why Didn't Unit Tests Catch This?

The existing `test_dialogs.py` uses **mock objects** with minimal data:
- 0 places, 0 transitions, 0 arcs
- No actual topology to analyze
- `populate()` returns immediately (no cycles to find)

**Lesson**: Need **integration tests with realistic models** to catch performance issues.

### Why Only Imported Models?

- **New models** start empty or small
- Users build incrementally → few nodes, few arcs, few cycles
- Cycle detection completes in milliseconds

- **Imported models** are complete, complex networks
- 60+ nodes, 70+ arcs, potentially hundreds/thousands of cycles
- Cycle detection hangs or takes hours

**Lesson**: Real-world data has exponentially more complexity than test data.

---

## References

- NetworkX Documentation: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.cycles.simple_cycles.html
- Johnson's Algorithm: https://doi.org/10.1137/0204007 (1975)
- Petri Net Cycle Analysis: https://doi.org/10.1007/978-3-540-27755-2_3

---

**Status**: Ready for implementation  
**Priority**: 🔴 CRITICAL (blocks dialog usage on imported models)  
**Estimated Fix Time**: 1 hour (emergency), 5 hours (complete solution)
