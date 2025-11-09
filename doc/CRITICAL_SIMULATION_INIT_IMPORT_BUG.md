# CRITICAL: Simulation Controller Not Reset on Model Import

**Date:** 2025-11-08  
**Severity:** HIGH - Breaks simulation for all imported models  
**Reporter:** User observation: "imported a model from kegg, added 5 stochastics source transition, run, nothing runs"  
**Root Cause:** `load_objects()` resets place markings but NOT simulation controller state

---

## Problem Description

### User's Discovery

The user reported a critical clue:
1. **Imported KEGG model** → Added 5 stochastic source transitions → **Run → NOTHING RUNS**
2. **Created new transition-place on canvas** → Run → **EVERYTHING RUNS**

This is a **state initialization problem**: The simulation controller is created when a canvas tab is first created, but **never reset** when a new model is loaded into that same tab.

---

## Root Cause Analysis

### Lifecycle Flow

```
1. Application starts
   └─> Canvas tab created (File → New or default tab)
       └─> SimulationController created for this tab
           ├─> controller.time = 0.0
           ├─> controller._running = False
           ├─> controller.transition_states = {}
           ├─> controller.behavior_cache = {}
           └─> controller.data_collector initialized

2. User imports KEGG model (File → Open or KEGG Import)
   └─> File → Open flow
       ├─> DocumentModel.load_from_file(filepath)
       ├─> _load_document_into_canvas(document, filepath)
       ├─> manager.load_objects(places, transitions, arcs)
       │   ├─> Adds places to manager.places ✓
       │   ├─> Adds transitions to manager.transitions ✓
       │   ├─> Adds arcs to manager.arcs ✓
       │   ├─> Resets place.tokens = place.initial_marking ✓
       │   └─> ❌ DOES NOT RESET SIMULATION CONTROLLER
       └─> Canvas displays imported model

3. User clicks "Run" simulation
   └─> SimulationController still has OLD STATE from previous model
       ├─> Old behavior_cache with stale transition IDs
       ├─> Old transition_states with removed transitions
       ├─> Old data_collector with wrong model reference
       └─> Result: Simulation fails silently or behaves incorrectly
```

### The Bug

**File:** `src/shypn/data/model_canvas_manager.py`  
**Method:** `load_objects()` (lines 542-638)

```python
def load_objects(self, places=None, transitions=None, arcs=None):
    """Load objects into the model in bulk."""
    
    # ... add places, transitions, arcs ...
    
    # CRITICAL: Reset all places to their initial marking
    for place in places:
        if hasattr(place, 'initial_marking'):
            place.tokens = place.initial_marking  # ✓ RESETS PLACES
    
    # ❌ MISSING: Reset simulation controller!
    # The controller still has:
    # - Old behavior cache with invalid transition references
    # - Old transition_states dict with deleted transitions
    # - Old data_collector tracking wrong model
    # - Potentially _running=True if previous simulation didn't complete
    
    self.mark_dirty()
    self.mark_needs_redraw()
```

**Result:** The simulation controller is in an **inconsistent state** - it has references to old transitions, stale behavior cache, and wrong data collector model.

---

## Why Creating a New Transition Fixed It

When the user manually created a new transition-place pair:
1. The new objects were added via `add_transition()` and `add_place()`
2. These methods trigger observer notifications: `'created'` events
3. The simulation controller observes these events via `_on_model_changed()`
4. **Critical:** The new arc creation **invalidates the model adapter caches**
5. This forces the simulation to rebuild its internal state on next run
6. **Side effect:** The cache invalidation "accidentally" fixed the stale state

This is why creating new objects made everything work - it forced a cache rebuild that shouldn't have been necessary in the first place.

---

## Evidence from Code

### 1. SimulationController.__init__() (controller.py:133-178)

```python
def __init__(self, model):
    """Initialize the simulation controller."""
    self.model = model
    self.time = 0.0  # ← Simulation time state
    self.model_adapter = ModelAdapter(model, controller=self)
    self.step_listeners = []
    self._running = False  # ← Running state
    self._stop_requested = False
    self._timeout_id = None
    self.behavior_cache = {}  # ← Behavior cache with transition IDs
    self.transition_states = {}  # ← Transition state tracking
    self.conflict_policy = DEFAULT_POLICY
    self._round_robin_index = 0
    
    # Data collection for simulation results
    from shypn.engine.simulation.data_collector import DataCollector
    self.data_collector = DataCollector(model)  # ← Model reference
```

**Problem:** All these state variables are **never reset** when `load_objects()` is called.

### 2. _reset_manager_for_load() (model_canvas_loader.py:761-940)

```python
def _reset_manager_for_load(self, manager, filename):
    """Reset manager state before loading objects from file.
    
    MUST be called BEFORE load_objects() when reusing a tab for File→Open or Import.
    
    This is the CANONICAL state reset for document loading, ensuring:
    - All state flags are reset
    - Callbacks are enabled
    - Objects are cleared
    - ID counters are reset
    - Canvas interaction states are reset (drag, arc, lasso, etc.)
    - Simulation controllers are reset to initial state  # ← CLAIM
    - Swiss palettes are reset to default tool/mode
    """
    
    # ... resets many things ...
    
    # ❌ NO SIMULATION CONTROLLER RESET CODE EXISTS!
```

**Problem:** The docstring **claims** it resets simulation controllers, but **no such code exists**.

### 3. _load_document_into_canvas() (file_explorer_panel.py:1795-1889)

```python
def _load_document_into_canvas(self, document, filepath):
    """Load a document model into the canvas."""
    
    # Either reuse current empty tab or create new one
    if can_reuse_tab:
        # CRITICAL: Reset manager state before loading
        self.canvas_loader._reset_manager_for_load(manager, base_name)
    else:
        # Create a new tab for this document
        page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
    
    if manager:
        # ===== UNIFIED OBJECT LOADING =====
        manager.load_objects(
            places=document.places,
            transitions=document.transitions,
            arcs=document.arcs
        )  # ← Loads objects but doesn't reset controller
```

**Problem:** Even when reusing a tab, `_reset_manager_for_load()` doesn't reset the simulation controller.

---

## Impact Assessment

### Affected Workflows

1. **KEGG Import** → File saved → File → Open → Simulation fails ❌
2. **SBML Import** → Simulation fails ❌
3. **File → Open existing model** → Simulation may fail if tab was reused ❌
4. **File → Open model A → File → Open model B in same tab** → Model B simulation has Model A's state ❌

### Symptoms

- Transitions don't fire even though enabled
- Stochastic source transitions never produce tokens
- Simulation appears to run but nothing happens
- Canvas shows transitions highlighting (enabled) but no token movement
- Data collector shows no/wrong data
- **Workaround:** Creating ANY new object triggers cache invalidation, "fixing" it

### Why It's Hard to Notice

- Creating a new model (File → New) creates a **new tab with fresh controller** ✓
- Most testing uses **new tabs**, not reused tabs
- **Creating new objects** (transition, place, arc) **triggers cache invalidation**, masking the bug
- Bug only appears when:
  - Reusing a tab (File → Open into existing empty tab)
  - Imported model has no manual edits (no cache invalidation trigger)

---

## Solution

### Fix 1: Reset Controller in _reset_manager_for_load()

**File:** `src/shypn/helpers/model_canvas_loader.py`  
**Method:** `_reset_manager_for_load()` (around line 940)

```python
def _reset_manager_for_load(self, manager, filename):
    """Reset manager state before loading objects from file."""
    
    # ... existing reset code ...
    
    # CRITICAL FIX: Reset simulation controller for this canvas
    drawing_area = None
    for da, mgr in self.canvas_managers.items():
        if mgr == manager:
            drawing_area = da
            break
    
    if drawing_area and drawing_area in self.simulation_controllers:
        controller = self.simulation_controllers[drawing_area]
        
        # Reset controller state to initial conditions
        controller.time = 0.0
        controller._running = False
        controller._stop_requested = False
        controller._timeout_id = None
        controller.behavior_cache.clear()
        controller.transition_states.clear()
        controller._round_robin_index = 0
        
        # Reinitialize model adapter with new model
        from shypn.engine.simulation.model_adapter import ModelAdapter
        controller.model_adapter = ModelAdapter(manager, controller=controller)
        
        # Reinitialize data collector with new model
        from shypn.engine.simulation.data_collector import DataCollector
        controller.data_collector = DataCollector(manager)
        
        # Reset settings to defaults (keep buffered settings wrapper)
        if hasattr(controller, 'buffered_settings'):
            controller.buffered_settings.rollback()  # Discard any uncommitted changes
```

### Fix 2: Add reset() Method to SimulationController

**File:** `src/shypn/engine/simulation/controller.py`  
**Add method:**

```python
def reset(self):
    """Reset controller to initial state.
    
    Called when loading a new model into an existing canvas tab.
    Clears all cached state and reinitializes adapters.
    """
    self.time = 0.0
    self._running = False
    self._stop_requested = False
    self._timeout_id = None
    self.behavior_cache.clear()
    self.transition_states.clear()
    self._round_robin_index = 0
    
    # Reinitialize model adapter
    from shypn.engine.simulation.model_adapter import ModelAdapter
    self.model_adapter = ModelAdapter(self.model, controller=self)
    
    # Reinitialize data collector
    from shypn.engine.simulation.data_collector import DataCollector
    self.data_collector = DataCollector(self.model)
    
    # Reset buffered settings (discard uncommitted changes)
    if hasattr(self, 'buffered_settings'):
        self.buffered_settings.rollback()
```

Then call it from `_reset_manager_for_load()`:

```python
if drawing_area and drawing_area in self.simulation_controllers:
    controller = self.simulation_controllers[drawing_area]
    controller.reset()  # Single method call
```

---

## Testing Plan

### Test Case 1: KEGG Import Then Run

1. Start application
2. Import KEGG hsa00010 (glycolysis)
3. **Before fix:** Add stochastic source transitions → Run → Nothing runs ❌
4. **After fix:** Add stochastic source transitions → Run → Should run ✓

### Test Case 2: Open Model A, Then Open Model B

1. File → New (or use default tab)
2. Create simple model: Place P1 → Transition T1 → Place P2, P1.tokens=10
3. Run simulation → Should work
4. File → Open different model (hsa00010)
5. **Before fix:** Run simulation → Model A's controller state interferes ❌
6. **After fix:** Run simulation → Clean state, works correctly ✓

### Test Case 3: Tab Reuse

1. File → New (creates "default" tab)
2. Don't add anything (keep it empty)
3. File → Open model → Reuses default tab
4. **Before fix:** Controller not reset, may have stale state ❌
5. **After fix:** Controller reset, simulation works ✓

### Test Case 4: Multiple Sequential Opens

1. Open model A in tab 1
2. Open model B in tab 2
3. Switch to tab 1, modify, run
4. Switch to tab 2, run
5. **Verify:** Each tab has independent controller state ✓

---

## Related Issues

### Similar Bugs in History

From `doc/CRITICAL_FIX_IMPORTED_TRANSITIONS_NOT_FIRING.md`:
- Problem: Imported transitions had stale behavior cache
- Fix: Added cache invalidation on arc transformation
- **This current bug is the same pattern** - state not reset on import

### Design Debt

The current design has **implicit assumptions**:
- Assumes each tab is used for ONE model for its entire lifetime
- Assumes tab reuse is rare (but File → Open DOES reuse tabs!)
- Assumes object creation will trigger cache invalidation (but imports don't create, they load!)

**Root cause:** **Lifecycle management is incomplete** - we create resources but don't clean them up properly when switching models.

---

## Proposed Long-Term Solution

### Unified Lifecycle Adapter (Already Exists!)

From `model_canvas_loader.py` line 1236:

```python
# ============================================================
# GLOBAL-SYNC: Integrate with canvas lifecycle system
# ============================================================
if self.lifecycle_adapter:
    try:
        # Register canvas with adapter
        self.lifecycle_adapter.register_canvas(
            drawing_area,
            canvas_manager,
            simulation_controller,
            swissknife_palette
        )
```

**Enhancement:** Add lifecycle methods:
- `lifecycle_adapter.reset_canvas(drawing_area)` - Reset all components for model load
- `lifecycle_adapter.cleanup_canvas(drawing_area)` - Full cleanup on tab close
- `lifecycle_adapter.switch_model(drawing_area, old_model, new_model)` - Model swap

This centralizes lifecycle management instead of scattered reset logic.

---

## Acceptance Criteria

- [ ] `SimulationController.reset()` method implemented
- [ ] `_reset_manager_for_load()` calls `controller.reset()`
- [ ] Test Case 1 passes: KEGG import → run works without manual edits
- [ ] Test Case 2 passes: Open Model A → Open Model B works
- [ ] Test Case 3 passes: Tab reuse works correctly
- [ ] Test Case 4 passes: Multi-tab independence maintained
- [ ] No regression: Existing workflows (File → New, Create objects) still work

---

## Priority

**CRITICAL** - This affects ALL model import workflows:
- KEGG imports
- SBML imports
- File → Open
- Any workflow that reuses tabs

**Impact:** Users cannot simulate imported models without first manually creating/editing objects (which accidentally fixes the bug via cache invalidation).

---

## Implementation Notes

### Where to Add reset() Call

`_reset_manager_for_load()` already has code to find the drawing_area:

```python
# Reset canvas interaction states (CRITICAL for fixing corrupted context menu/drag)
drawing_area = None
if hasattr(self, 'canvas_managers'):
    for da, mgr in self.canvas_managers.items():
        if mgr == manager:
            drawing_area = da
            break
```

Add after this block:

```python
if drawing_area and drawing_area in self.simulation_controllers:
    self.simulation_controllers[drawing_area].reset()
```

### Testing the Fix

Run the validation script I created earlier, but with imported model:

```bash
cd /home/simao/projetos/shypn
python dev/validate_heuristic_fixes.py
```

This should work WITHOUT any manual edits after the fix.
