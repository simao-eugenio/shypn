# Background Topology Analysis Architecture

**Date**: October 19, 2025  
**Status**: 🎯 DESIGN PROPOSAL  
**Priority**: HIGH

---

## 🎯 Strategic Vision

**Current Problem**: Topology analysis is **triggered by dialogs** → blocks UI  
**New Strategy**: Topology analysis runs **in background after model load** → results cached → dialogs just display

### Key Principles

1. **Analyze Once, Display Many**: Run expensive analysis once when model loads
2. **Non-Blocking**: All analysis in background threads/processes
3. **Progressive Loading**: Show partial results as they complete
4. **Cache Results**: Store in memory, invalidate on model changes
5. **User Awareness**: Show analysis progress in status bar

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         MODEL LOADED                            │
│                    (DocumentModel.from_dict)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TOPOLOGY ANALYSIS MANAGER                      │
│  - Detects model load event                                     │
│  - Spawns background workers                                    │
│  - Manages result cache                                         │
│  - Emits progress signals                                       │
└────────┬────────────────┬────────────────┬──────────────────────┘
         │                │                │
         ▼                ▼                ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │ Worker │      │ Worker │      │ Worker │
    │   1    │      │   2    │      │   3    │
    │ Cycles │      │  Paths │      │P-Invs  │
    └────┬───┘      └────┬───┘      └────┬───┘
         │                │                │
         │ (completes)    │                │
         ▼                ▼                ▼
    ┌──────────────────────────────────────────┐
    │        TOPOLOGY RESULTS CACHE            │
    │  {                                       │
    │    "cycles": {...},                      │
    │    "paths": {...},                       │
    │    "p_invariants": {...},                │
    │    "status": "in_progress/complete"      │
    │  }                                       │
    └────────────────┬─────────────────────────┘
                     │
                     │ (user opens dialog)
                     ▼
    ┌──────────────────────────────────────────┐
    │       PROPERTY DIALOG                    │
    │  - Checks cache for results              │
    │  - Displays immediately if available     │
    │  - Shows "Computing..." if in progress   │
    │  - Shows "Error" if failed               │
    └──────────────────────────────────────────┘
```

---

## 📋 Component Design

### 1. TopologyAnalysisManager (NEW)

**Location**: `src/shypn/topology/analysis_manager.py`

**Responsibilities**:
- Monitor model load events
- Spawn background analysis workers
- Manage result cache (in-memory)
- Emit GLib signals for progress updates
- Handle analysis cancellation
- Invalidate cache on model changes

**API**:
```python
class TopologyAnalysisManager:
    """Manager for background topology analysis.
    
    Runs topology analyzers in background threads/processes when
    model is loaded, caches results, and provides them to dialogs.
    """
    
    def __init__(self):
        self.cache = {}  # model_id -> analysis_results
        self.workers = {}  # model_id -> worker_threads
        self.status = {}  # model_id -> analysis_status
    
    def analyze_model(self, model, model_id=None):
        """Start background analysis for a model.
        
        Args:
            model: DocumentModel instance
            model_id: Unique identifier (defaults to model hash)
        """
        pass
    
    def get_results(self, model_id, analyzer_name=None):
        """Get cached results for a model.
        
        Args:
            model_id: Model identifier
            analyzer_name: Specific analyzer (None = all)
            
        Returns:
            dict: Cached results or None if not ready
        """
        pass
    
    def get_status(self, model_id):
        """Get analysis status for a model.
        
        Returns:
            dict: {
                'status': 'idle|running|complete|error',
                'progress': 0.0-1.0,
                'completed': ['cycles', 'paths'],
                'pending': ['p_invariants', 'hubs'],
                'errors': []
            }
        """
        pass
    
    def cancel_analysis(self, model_id):
        """Cancel ongoing analysis."""
        pass
    
    def invalidate_cache(self, model_id):
        """Invalidate cached results (model changed)."""
        pass
```

### 2. BackgroundAnalysisWorker (NEW)

**Location**: `src/shypn/topology/workers/background_worker.py`

**Responsibilities**:
- Run single analyzer in background thread
- Report progress via callbacks
- Handle timeouts gracefully
- Catch and report errors

**API**:
```python
class BackgroundAnalysisWorker(threading.Thread):
    """Worker thread for running topology analysis.
    
    Runs a single analyzer (e.g., CycleAnalyzer) in background,
    with timeout and progress reporting.
    """
    
    def __init__(self, analyzer_class, model, 
                 timeout=30.0, 
                 on_progress=None,
                 on_complete=None,
                 on_error=None):
        """Initialize worker.
        
        Args:
            analyzer_class: Analyzer class to instantiate
            model: Model to analyze
            timeout: Maximum time in seconds
            on_progress: Callback(progress: float)
            on_complete: Callback(results: dict)
            on_error: Callback(error: Exception)
        """
        pass
    
    def run(self):
        """Run analysis in background."""
        pass
    
    def cancel(self):
        """Cancel analysis."""
        pass
```

### 3. TopologyResultCache (NEW)

**Location**: `src/shypn/topology/cache.py`

**Responsibilities**:
- Store analysis results in memory
- LRU eviction for memory management
- Serialize to disk for persistence (optional)
- Thread-safe access

**API**:
```python
class TopologyResultCache:
    """Cache for topology analysis results.
    
    Stores results in memory with LRU eviction.
    Optionally persists to disk.
    """
    
    def __init__(self, max_size=10, persist_dir=None):
        """Initialize cache.
        
        Args:
            max_size: Max models to cache
            persist_dir: Directory for disk persistence
        """
        pass
    
    def set(self, model_id, analyzer_name, results):
        """Store results."""
        pass
    
    def get(self, model_id, analyzer_name=None):
        """Get results."""
        pass
    
    def invalidate(self, model_id):
        """Invalidate cached results."""
        pass
    
    def clear(self):
        """Clear all cache."""
        pass
```

### 4. Model Change Detector (NEW)

**Location**: `src/shypn/topology/change_detector.py`

**Responsibilities**:
- Monitor model for structural changes
- Emit invalidation events
- Track dirty state

**API**:
```python
class ModelChangeDetector:
    """Detects structural changes in Petri net models.
    
    Monitors add/remove/modify operations on places, transitions, arcs.
    Emits signals when topology analysis needs to be re-run.
    """
    
    def __init__(self, model):
        self.model = model
        self._attach_listeners()
    
    def _attach_listeners(self):
        """Attach to model change events."""
        pass
    
    def on_model_changed(self, callback):
        """Register callback for model changes."""
        pass
```

---

## 🔄 Workflow

### Scenario 1: User Opens Imported Model

```python
# 1. User opens Glycolysis_01_.shy
document = DocumentModel.load_from_file('Glycolysis_01_.shy')

# 2. Main app triggers background analysis
topology_manager.analyze_model(document, model_id='glycolysis_01')

# 3. Manager spawns background workers (non-blocking)
workers = [
    BackgroundAnalysisWorker(CycleAnalyzer, document, timeout=10),
    BackgroundAnalysisWorker(PathAnalyzer, document, timeout=10),
    BackgroundAnalysisWorker(PInvariantAnalyzer, document, timeout=20),
    BackgroundAnalysisWorker(HubAnalyzer, document, timeout=5),
]

# 4. Status bar shows: "Analyzing topology... (1/4 complete)"
# User can work normally - analysis happens in background

# 5. User right-clicks place → Properties (while analysis running)
dialog = PlacePropDialogLoader(place, model=document)

# 6. Dialog checks cache
results = topology_manager.get_results('glycolysis_01', 'cycles')

if results is None:
    # Analysis not complete yet
    status = topology_manager.get_status('glycolysis_01')
    if status['status'] == 'running':
        label.set_text("Computing cycles... (please wait)")
    else:
        label.set_text("Cycles analysis pending...")
        
elif results.success:
    # Analysis complete - show results
    label.set_text(f"Found {results.get('count')} cycles")
    
else:
    # Analysis failed
    label.set_text(f"Analysis error: {results.errors[0]}")

# 7. When analysis completes, emit signal to update any open dialogs
topology_manager.connect('analysis-complete', on_analysis_complete)
```

### Scenario 2: User Modifies Model

```python
# User adds a new place
document.add_place(new_place)

# Change detector triggers
change_detector.emit('model-changed')

# Manager invalidates cache
topology_manager.invalidate_cache('glycolysis_01')

# Manager re-runs analysis in background
topology_manager.analyze_model(document, model_id='glycolysis_01')

# Open dialogs update to show "Re-analyzing..."
```

---

## 🎛️ UI Integration

### Status Bar Integration

```python
# In main app (shypn.py)
class MainWindow:
    def __init__(self):
        self.status_bar = self.builder.get_object('status_bar')
        self.topology_manager = TopologyAnalysisManager()
        
        # Connect to analysis events
        self.topology_manager.connect('analysis-started', self._on_analysis_started)
        self.topology_manager.connect('analysis-progress', self._on_analysis_progress)
        self.topology_manager.connect('analysis-complete', self._on_analysis_complete)
    
    def _on_analysis_started(self, manager, model_id):
        self.status_bar.push(0, f"🔄 Analyzing topology...")
    
    def _on_analysis_progress(self, manager, model_id, progress):
        percent = int(progress * 100)
        self.status_bar.push(0, f"🔄 Analyzing topology... {percent}%")
    
    def _on_analysis_complete(self, manager, model_id, results):
        self.status_bar.push(0, f"✓ Topology analysis complete")
        # Auto-hide after 3 seconds
        GLib.timeout_add_seconds(3, lambda: self.status_bar.pop(0))
```

### Dialog Integration

**BEFORE (blocks UI)**:
```python
# Old approach - runs synchronously
def _setup_topology_tab(self):
    self.topology_loader = PlaceTopologyTabLoader(...)
    self.topology_loader.populate()  # ❌ BLOCKS FOR MINUTES
```

**AFTER (shows cached results)**:
```python
# New approach - instant display
def _setup_topology_tab(self):
    self.topology_loader = PlaceTopologyTabLoader(...)
    
    # Check if results already available
    model_id = self._get_model_id()
    results = topology_manager.get_results(model_id, 'cycles')
    
    if results:
        # Results ready - display immediately
        self.topology_loader.display_results(results)
    else:
        # Results not ready - show status
        status = topology_manager.get_status(model_id)
        self.topology_loader.display_status(status)
        
        # Listen for completion
        topology_manager.connect('analysis-complete', 
                                self._on_topology_ready)
```

---

## ⚙️ Implementation Plan

### Phase 1: Core Infrastructure (4 hours)

**Goal**: Basic background analysis framework

1. **Create TopologyAnalysisManager** (1.5h)
   - Basic manager class
   - Model registration
   - Simple in-memory cache
   
2. **Create BackgroundAnalysisWorker** (1.5h)
   - Threading wrapper
   - Timeout handling
   - Error capture
   
3. **Create TopologyResultCache** (1h)
   - Dictionary-based cache
   - Get/set/invalidate methods

**Deliverable**: Can run analysis in background, store results

---

### Phase 2: Main App Integration (3 hours)

**Goal**: Auto-analyze on model load

4. **Wire to Model Loading** (1h)
   - Hook into `load_document()` in shypn.py
   - Trigger analysis on model open
   - Generate model IDs
   
5. **Status Bar Integration** (1h)
   - Show "Analyzing..." message
   - Progress indicator
   - Auto-hide on complete
   
6. **Model Change Detection** (1h)
   - Monitor add/remove operations
   - Invalidate cache on changes
   - Re-trigger analysis

**Deliverable**: Models auto-analyze on load, status visible

---

### Phase 3: Dialog Integration (3 hours)

**Goal**: Dialogs display cached results

7. **Update Dialog Loaders** (1.5h)
   - Check cache before populate
   - Display cached results
   - Show "Computing..." if pending
   
8. **Live Updates** (1h)
   - Listen for analysis-complete signal
   - Auto-update open dialogs
   - Smooth transitions
   
9. **Error Handling** (0.5h)
   - Display timeout messages
   - Show analysis errors
   - Retry mechanism

**Deliverable**: Dialogs instant, show cached or "pending"

---

### Phase 4: Optimization (2 hours)

**Goal**: Performance and UX polish

10. **Algorithm Improvements** (1h)
    - Add max_cycles limits
    - Add max_length limits
    - Early termination
    
11. **Progress Reporting** (0.5h)
    - Detailed progress from analyzers
    - Better UI feedback
    
12. **Disk Persistence** (0.5h)
    - Save cache to disk
    - Load on startup
    - Faster re-opens

**Deliverable**: Fast, polished, production-ready

---

## 📊 Performance Expectations

### Current (Synchronous)
- **Small models** (10 nodes): 50ms
- **Medium models** (30 nodes): 500ms
- **Large models** (60 nodes): **INFINITE HANG** ❌

### After Phase 1-3 (Background)
- **All model sizes**: Dialog opens in **<50ms** ✓
- **Analysis happens in background**
- **User can work immediately**

### After Phase 4 (Optimized)
- **Small models**: Analysis completes in 100ms
- **Medium models**: Analysis completes in 1-2s
- **Large models**: Analysis completes in 5-10s (with limits)
- **Very large models**: Timeout after 30s, show partial results

---

## 🎯 Success Criteria

### User Experience
- ✅ Dialogs open **instantly** (<100ms) regardless of model size
- ✅ User can work while analysis runs in background
- ✅ Status bar shows analysis progress
- ✅ Results appear automatically when ready
- ✅ No freezes or hangs

### Technical
- ✅ All analysis in background threads
- ✅ No blocking of GTK main loop
- ✅ Results cached and reused
- ✅ Cache invalidated on model changes
- ✅ Graceful timeout handling
- ✅ Thread-safe cache access

### Performance
- ✅ Dialog open time: <100ms (all models)
- ✅ Small model analysis: <500ms
- ✅ Large model analysis: <30s (with timeout)
- ✅ Memory usage: <100MB cache overhead
- ✅ No memory leaks

---

## 🔧 Technical Considerations

### Threading Strategy

**Option 1: Threading (RECOMMENDED)**
```python
import threading
worker = threading.Thread(target=analyze_cycles, args=(model,))
worker.daemon = True  # Don't block app exit
worker.start()
```

**Pros**: 
- ✅ Simple, built-in
- ✅ Shared memory (easy cache access)
- ✅ GLib.idle_add() for UI updates

**Cons**:
- ⚠️ GIL limitations (but analysis is I/O-bound, not CPU-bound)

**Option 2: Multiprocessing**
```python
from multiprocessing import Process, Queue
worker = Process(target=analyze_cycles, args=(model, queue))
worker.start()
```

**Pros**:
- ✅ True parallelism (no GIL)
- ✅ Better for CPU-heavy work

**Cons**:
- ⚠️ More complex IPC
- ⚠️ Serialization overhead
- ⚠️ Harder debugging

**Decision**: Use **threading** for simplicity, switch to multiprocessing if needed.

---

### Cache Invalidation Strategy

**When to invalidate**:
- ✅ Place added/removed
- ✅ Transition added/removed
- ✅ Arc added/removed/modified (weight change)
- ❌ Visual property changes (position, color) - don't affect topology
- ❌ Name/label changes - don't affect topology

**Granular invalidation**:
```python
# Only invalidate affected analyses
if arc_weight_changed:
    cache.invalidate(model_id, 'p_invariants')  # Affected
    # Don't invalidate 'cycles' - still valid
```

---

### Timeout Strategy

**Per-analyzer timeouts**:
- CycleAnalyzer: 10s (most expensive)
- PathAnalyzer: 10s
- PInvariantAnalyzer: 20s (matrix operations)
- HubAnalyzer: 5s (simple metrics)
- LivenessAnalyzer: 15s
- BoundednessAnalyzer: 10s

**Timeout behavior**:
1. Start timer when worker begins
2. If timeout, cancel worker gracefully
3. Return partial results if available
4. Show "Analysis timeout" in UI
5. Allow user to retry with stricter limits

---

## 📝 Code Examples

### Example 1: Manager Usage in Main App

```python
# In shypn.py - after model load

class MainApp:
    def __init__(self):
        # Initialize topology manager (singleton)
        from shypn.topology.analysis_manager import get_topology_manager
        self.topology_manager = get_topology_manager()
        
        # Connect to signals
        self.topology_manager.connect('analysis-complete', 
                                     self._on_topology_complete)
    
    def on_file_loaded(self, filepath):
        """Called when user opens a model."""
        # Load model
        document = DocumentModel.load_from_file(filepath)
        
        # Generate model ID (hash of filepath + modification time)
        import hashlib
        model_id = hashlib.md5(
            f"{filepath}:{os.path.getmtime(filepath)}".encode()
        ).hexdigest()
        
        # Start background analysis
        self.topology_manager.analyze_model(document, model_id)
        
        # Show in status bar
        self.status_bar.push(0, "🔄 Analyzing topology in background...")
    
    def _on_topology_complete(self, manager, model_id, results):
        """Called when background analysis completes."""
        # Update status bar
        self.status_bar.push(0, "✓ Topology analysis complete")
        
        # Update any open dialogs
        for dialog in self.open_dialogs:
            if dialog.model_id == model_id:
                dialog.refresh_topology_tab()
```

### Example 2: Dialog Using Cached Results

```python
# In place_prop_dialog_loader.py

def _setup_topology_tab(self):
    """Setup topology tab with cached results."""
    try:
        from shypn.ui.topology_tab_loader import PlaceTopologyTabLoader
        from shypn.topology.analysis_manager import get_topology_manager
        
        self.topology_loader = PlaceTopologyTabLoader(
            model=self.model,
            element_id=self.place_obj.id
        )
        
        # Get topology manager
        manager = get_topology_manager()
        model_id = self._get_model_id()
        
        # Check cache for results
        status = manager.get_status(model_id)
        
        if status['status'] == 'complete':
            # Results ready - display immediately
            results = manager.get_results(model_id)
            self.topology_loader.display_cached_results(results)
            
        elif status['status'] == 'running':
            # Analysis in progress
            progress = status.get('progress', 0) * 100
            self.topology_loader.show_computing_message(
                f"Analyzing topology... {progress:.0f}%"
            )
            
            # Listen for completion
            manager.connect('analysis-complete', 
                          self._on_analysis_complete)
            
        elif status['status'] == 'error':
            # Analysis failed
            errors = status.get('errors', [])
            self.topology_loader.show_error_message(
                f"Analysis failed: {errors[0] if errors else 'Unknown error'}"
            )
            
        else:
            # Not started yet (shouldn't happen)
            self.topology_loader.show_pending_message()
        
        # Embed in dialog
        topology_widget = self.topology_loader.get_root_widget()
        container = self.builder.get_object('topology_tab_container')
        if container and topology_widget:
            container.pack_start(topology_widget, True, True, 0)
            topology_widget.show_all()
    
    except Exception as e:
        print(f"Error setting up topology tab: {e}")
        import traceback
        traceback.print_exc()

def _on_analysis_complete(self, manager, model_id, results):
    """Called when background analysis completes."""
    if model_id == self._get_model_id():
        # Our model's analysis is done - update display
        self.topology_loader.display_cached_results(results)
```

---

## 🎨 UI Mockups

### Status Bar States

```
┌────────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help               🔄 Analyzing... │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help       🔄 Analyzing... 45%     │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help       ✓ Topology complete    │
└────────────────────────────────────────────────────────────┘
```

### Topology Tab States

**State 1: Computing**
```
┌─────────────────────────────────────────────┐
│ Basic │ Visual │ Topology                   │
├─────────────────────────────────────────────┤
│                                             │
│  🔄 Computing topology analysis...          │
│                                             │
│  Cycles: Computing...                       │
│  Paths: Complete ✓                          │
│  P-Invariants: Computing... (45%)           │
│  Hubs: Pending...                           │
│                                             │
│  This may take up to 30 seconds for        │
│  large models.                              │
│                                             │
└─────────────────────────────────────────────┘
```

**State 2: Complete**
```
┌─────────────────────────────────────────────┐
│ Basic │ Visual │ Topology                   │
├─────────────────────────────────────────────┤
│                                             │
│  Cycles                                     │
│  Found 12 cycles containing this place      │
│  Longest: 8 nodes                           │
│  [View Details]                             │
│                                             │
│  Conservation Laws                          │
│  2 P-invariants involve this place          │
│  [View Details]                             │
│                                             │
│  Paths                                      │
│  45 paths pass through this place           │
│  [View Details]                             │
│                                             │
└─────────────────────────────────────────────┘
```

**State 3: Timeout**
```
┌─────────────────────────────────────────────┐
│ Basic │ Visual │ Topology                   │
├─────────────────────────────────────────────┤
│                                             │
│  ⚠️ Analysis Timeout                        │
│                                             │
│  Topology analysis took too long for this   │
│  large model (>30 seconds).                 │
│                                             │
│  Partial results:                           │
│  • Paths: 45 found ✓                        │
│  • Hubs: Degree 8 ✓                         │
│  • Cycles: Timeout ⏱                        │
│  • P-Invariants: Timeout ⏱                  │
│                                             │
│  [Retry with Limits] [Cancel]               │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 📦 File Structure

```
src/shypn/topology/
├── __init__.py
├── analysis_manager.py          # NEW - Main manager
├── cache.py                      # NEW - Result cache
├── change_detector.py            # NEW - Model change monitoring
├── workers/                      # NEW - Background workers
│   ├── __init__.py
│   ├── background_worker.py     # NEW - Base worker
│   ├── cycle_worker.py          # NEW - Cycle analysis worker
│   ├── path_worker.py           # NEW - Path analysis worker
│   └── invariant_worker.py      # NEW - Invariant worker
├── base/
│   ├── topology_analyzer.py     # EXISTING - Base class
│   └── analysis_result.py       # EXISTING - Result class
├── graph/
│   ├── cycles.py                # EXISTING - Modify for cancellation
│   └── paths.py                 # EXISTING - Modify for cancellation
├── structural/
│   └── p_invariants.py          # EXISTING - Modify for timeout
└── behavioral/                   # EXISTING - All behavioral analyzers
```

---

## 🚀 Migration Path

### Step 1: Keep Old Code Working
- New system runs in parallel
- Old populate() still works
- Feature flag to switch between modes

### Step 2: Gradual Rollout
- Enable background analysis by default
- Dialogs try cache first, fall back to old populate()
- Monitor performance

### Step 3: Remove Old Code
- Once stable, remove synchronous populate()
- Full background mode only

---

## ✅ Summary

### What This Solves
- ✅ **No more dialog freezes** - analysis is background
- ✅ **Instant dialog opening** - just displays cache
- ✅ **Better UX** - progress visible in status bar
- ✅ **Scalable** - handles any model size
- ✅ **Responsive** - user can work during analysis

### Implementation Effort
- **Phase 1-3**: 10 hours (core functionality)
- **Phase 4**: 2 hours (polish)
- **Total**: ~12 hours for complete solution

### Next Steps
1. Review and approve architecture
2. Implement Phase 1 (core infrastructure)
3. Test with Glycolysis model
4. Iterate based on feedback

---

**Ready to implement?** Let me know if you want me to start with Phase 1! 🚀
