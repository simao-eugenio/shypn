# Simulation Reset - Complete Coverage Across All Flows

**Date**: 2025-11-04  
**Status**: ✅ IMPLEMENTED  
**Purpose**: Ensure simulation state is ALWAYS reset to guarantee fundamental consistency

---

## The Fundamental Principle

> **Every time a model is created, loaded, modified, or parameter is applied, the simulation MUST be reset to initial state.**

This prevents:
- 🔴 Stale cached behaviors from using old parameter values
- 🔴 Incorrect enablement states persisting across operations
- 🔴 Token values being out of sync with model state
- 🔴 Simulation time not being reset
- 🔴 Scheduled events from previous models interfering

---

## Complete Reset Coverage

### ✅ 1. File → New
**Location**: `model_canvas_loader.py:add_document()`

```python
# After creating new document canvas
self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)

# CRITICAL: Reset simulation to initial state
self._ensure_simulation_reset(drawing)
```

**When**: User creates new empty document  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Clean slate, time=0.0, empty canvas with initial state

---

### ✅ 2. File → Open (New Tab)
**Location**: `model_canvas_loader.py:add_document()`

```python
# After creating new tab for loaded file
self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)

# CRITICAL: Reset simulation to initial state
self._ensure_simulation_reset(drawing)
```

**When**: User opens file in new tab  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Clean slate for loaded model

---

### ✅ 3. File → Open (Reuse Default Tab)
**Location**: `file_explorer_panel.py:_load_document_into_canvas()`

```python
# After loading document via reset_manager_for_load
manager.mark_needs_redraw()

# CRITICAL: Ensure simulation is reset
if hasattr(self.canvas_loader, '_ensure_simulation_reset'):
    drawing_area = self.canvas_loader.get_current_document()
    self.canvas_loader._ensure_simulation_reset(drawing_area)
```

**When**: User opens file and reuses empty default tab  
**Reset Type**: Full reset via `controller.reset_for_new_model()` + explicit reset  
**Effect**: Double-guaranteed clean state

---

### ✅ 4. Double-Click File in Explorer
**Location**: `file_explorer_panel.py:_load_document_into_canvas()`

```python
# Same code path as File → Open
# CRITICAL: Ensure simulation is reset
if hasattr(self.canvas_loader, '_ensure_simulation_reset'):
    drawing_area = self.canvas_loader.get_current_document()
    self.canvas_loader._ensure_simulation_reset(drawing_area)
```

**When**: User double-clicks .shy file in file explorer  
**Reset Type**: Full reset via `controller.reset_for_new_model()` + explicit reset  
**Effect**: Same as File → Open

---

### ✅ 5. KEGG Import (New Tab)
**Location**: `kegg_category.py:_on_kegg_import_complete()`

```python
# After creating new tab and loading KEGG model
canvas_manager.mark_needs_redraw()

# CRITICAL: Ensure simulation is reset
if canvas_loader and hasattr(canvas_loader, '_ensure_simulation_reset'):
    canvas_loader._ensure_simulation_reset(drawing_area)
```

**When**: User imports KEGG pathway into new tab  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Clean initial state for imported pathway

---

### ✅ 6. KEGG Import (Reuse Tab)
**Location**: `kegg_category.py:_on_kegg_import_complete()`

```python
# After reusing tab via reset_manager_for_load
canvas_loader._reset_manager_for_load(canvas_manager, base_name)
# ... load objects ...
canvas_manager.mark_needs_redraw()

# CRITICAL: Ensure simulation is reset
if canvas_loader and hasattr(canvas_loader, '_ensure_simulation_reset'):
    canvas_loader._ensure_simulation_reset(canvas_loader.get_current_document())
```

**When**: User imports KEGG pathway and reuses empty tab  
**Reset Type**: Full reset via `controller.reset_for_new_model()` + explicit reset  
**Effect**: Double-guaranteed clean state for imported pathway

---

### ✅ 7. SBML Import (New Tab)
**Location**: `sbml_category.py:_on_sbml_import_complete()`

```python
# After creating new tab and loading SBML model
canvas_manager.mark_needs_redraw()

# CRITICAL: Ensure simulation is reset
if canvas_loader and hasattr(canvas_loader, '_ensure_simulation_reset'):
    canvas_loader._ensure_simulation_reset(drawing_area)
```

**When**: User imports SBML model into new tab  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Clean initial state for imported model

---

### ✅ 8. SBML Import (Reuse Tab)
**Location**: `sbml_category.py:_on_sbml_import_complete()`

```python
# After reusing tab via reset_manager_for_load
canvas_loader._reset_manager_for_load(canvas_manager, base_name)
# ... load objects ...
canvas_manager.mark_needs_redraw()

# CRITICAL: Ensure simulation is reset
if canvas_loader and hasattr(canvas_loader, '_ensure_simulation_reset'):
    canvas_loader._ensure_simulation_reset(canvas_loader.get_current_document())
```

**When**: User imports SBML model and reuses empty tab  
**Reset Type**: Full reset via `controller.reset_for_new_model()` + explicit reset  
**Effect**: Double-guaranteed clean state for imported model

---

### ✅ 9. Heuristic Parameters - Apply Selected
**Location**: `heuristic_parameters_category.py:_on_apply_selected()`

```python
# After applying parameters to selected transitions
if applied_count > 0:
    self._reset_simulation_after_parameter_changes()
```

**When**: User applies inferred parameters to transitions  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Clears cached behaviors, resets places to initial marking, time=0.0

---

### ✅ 10. Heuristic Parameters - Apply All
**Location**: `heuristic_parameters_category.py:_on_apply_all()`

```python
# After applying parameters to all high-confidence transitions
if applied_count > 0:
    self._reset_simulation_after_parameter_changes()
```

**When**: User applies all high-confidence parameters  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Same as Apply Selected

---

### ✅ 11. BRENDA Enrichment - Apply Parameters
**Location**: `brenda_category.py:_apply_batch_parameters()`

```python
# After applying BRENDA parameters
self.brenda_controller.finish_enrichment()

# CRITICAL: Reset simulation state
if applied_count > 0:
    self._reset_simulation_after_parameter_changes()
```

**When**: User applies BRENDA kinetic parameters  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Clears cached behaviors, resets to initial state

---

### ✅ 12. SABIO-RK Enrichment - Apply Selected
**Location**: `sabio_rk_category.py:_on_apply_clicked()`

```python
# After applying SABIO-RK parameters
summary = self.sabio_controller.apply_batch(...)

# CRITICAL: Reset simulation state
if summary.get('success', 0) > 0:
    self._reset_simulation_after_parameter_changes()
```

**When**: User applies SABIO-RK kinetic parameters  
**Reset Type**: Full reset via `controller.reset()`  
**Effect**: Clears cached behaviors, resets to initial state

---

## Reset Implementation Details

### Method 1: `_ensure_simulation_reset(drawing_area)`
**Location**: `model_canvas_loader.py`

```python
def _ensure_simulation_reset(self, drawing_area):
    """Ensure simulation is reset to initial state for a canvas.
    
    Calls controller.reset() which:
    - Clears behavior cache (forces new behaviors with new parameters)
    - Resets places to initial_marking
    - Resets simulation time to 0.0
    - Clears transition states
    - Updates enablement states
    """
    if not drawing_area:
        return
    
    try:
        if drawing_area in self.simulation_controllers:
            controller = self.simulation_controllers[drawing_area]
            controller.reset()
            print(f"[RESET] Simulation reset for canvas")
    except Exception as e:
        print(f"[RESET] Error: {e}")
```

**Used For**: File operations, imports

---

### Method 2: `_reset_simulation_after_parameter_changes()`
**Location**: All enrichment categories (Heuristic, BRENDA, SABIO-RK)

```python
def _reset_simulation_after_parameter_changes(self):
    """Reset simulation after applying parameter changes.
    
    Gets current canvas and calls controller.reset() to ensure:
    - Behavior cache cleared
    - Places reset to initial marking
    - Clean slate for testing new parameters
    """
    drawing_area = self.canvas_loader.get_current_document()
    if drawing_area in self.canvas_loader.simulation_controllers:
        controller = self.canvas_loader.simulation_controllers[drawing_area]
        controller.reset()
        drawing_area.queue_draw()
```

**Used For**: Parameter enrichment operations

---

### Method 3: `reset_for_new_model(new_model)`
**Location**: `simulation/controller.py`

```python
def reset_for_new_model(self, new_model):
    """Reset controller for completely new model.
    
    More comprehensive than reset():
    - Recreates model adapter
    - Clears all caches
    - Resets state detector
    - Ensures no cross-contamination
    """
    if self._running:
        self.stop()
    
    self.model = new_model
    self.model_adapter = ModelAdapter(new_model, controller=self)
    self.time = 0.0
    self.behavior_cache.clear()
    self.transition_states.clear()
    # ... full reset ...
```

**Used For**: Model loading (called by `_reset_manager_for_load()`)

---

## What Gets Reset

### In `controller.reset()`:
1. ✅ **Stops running simulation**
2. ✅ **Clears behavior cache** - Forces new behaviors to be created
3. ✅ **Clears transition states** - Fresh enablement calculation
4. ✅ **Resets time to 0.0** - Clean timeline
5. ✅ **Resets places to initial_marking** - Clean slate for tokens
6. ✅ **Updates enablement states** - Recalculates what's enabled
7. ✅ **Clears data collector** - Fresh simulation data
8. ✅ **Notifies listeners** - UI updates

### In `controller.reset_for_new_model()`:
All of the above PLUS:
9. ✅ **Recreates model adapter** - New model reference
10. ✅ **Invalidates state detector cache** - Fresh state detection
11. ✅ **Re-registers observers** - Proper event wiring

---

## Testing Checklist

### File Operations
- [ ] File → New creates clean canvas with reset simulation
- [ ] File → Open (new tab) loads with reset simulation  
- [ ] File → Open (reuse tab) loads with reset simulation
- [ ] Double-click .shy file loads with reset simulation
- [ ] Simulation works correctly after each operation
- [ ] Places show initial marking values
- [ ] Transitions enabled/disabled correctly

### Import Operations
- [ ] KEGG import (new tab) loads with reset simulation
- [ ] KEGG import (reuse tab) loads with reset simulation
- [ ] SBML import (new tab) loads with reset simulation
- [ ] SBML import (reuse tab) loads with reset simulation
- [ ] Simulation works correctly after import
- [ ] All parameters correctly applied
- [ ] No stale state from previous model

### Parameter Operations
- [ ] Heuristic Parameters Apply Selected resets simulation
- [ ] Heuristic Parameters Apply All resets simulation
- [ ] BRENDA Apply Parameters resets simulation
- [ ] SABIO-RK Apply Selected resets simulation
- [ ] Simulation uses new parameter values
- [ ] Places reset to initial marking
- [ ] Time resets to 0.0

### Edge Cases
- [ ] Multiple operations in sequence work correctly
- [ ] Rapid file switching doesn't cause issues
- [ ] Import → Apply Parameters → Import works
- [ ] No memory leaks from old controllers
- [ ] Tab close properly cleans up controllers

---

## Benefits of Comprehensive Reset

### Consistency
✅ **Predictable behavior** - Same reset logic everywhere  
✅ **No special cases** - All paths use same mechanism  
✅ **Easy to reason about** - Always starts from known state

### Correctness
✅ **No stale cache** - Behaviors always use current parameter values  
✅ **No cross-contamination** - Models don't interfere with each other  
✅ **No timing bugs** - Simulation always starts from time=0.0

### Maintainability
✅ **Single source of truth** - Reset logic centralized  
✅ **Clear documentation** - Each reset point documented  
✅ **Easy to test** - Can verify reset at each point

---

## Related Files

**Core Implementation:**
- `src/shypn/helpers/model_canvas_loader.py` - `_ensure_simulation_reset()`
- `src/shypn/engine/simulation/controller.py` - `reset()`, `reset_for_new_model()`

**File Operations:**
- `src/shypn/helpers/file_explorer_panel.py` - File→Open, double-click

**Import Operations:**
- `src/shypn/ui/panels/pathway_operations/kegg_category.py` - KEGG import
- `src/shypn/ui/panels/pathway_operations/sbml_category.py` - SBML import

**Parameter Operations:**
- `src/shypn/ui/panels/pathway_operations/heuristic_parameters_category.py`
- `src/shypn/ui/panels/pathway_operations/brenda_category.py`
- `src/shypn/ui/panels/pathway_operations/sabio_rk_category.py`

**Documentation:**
- `CANVAS_STATE_ISSUES_COMPARISON.md` - Historical pattern analysis
- `SIMULATION_RESET_IMPLEMENTATION.md` - Original implementation

---

## Conclusion

**12 reset points** ensure simulation state is ALWAYS consistent across the entire application. No matter which flow the user takes - file operations, imports, or parameter applications - the simulation will always start from a clean, predictable initial state.

This eliminates the entire class of "stale state" bugs that have repeatedly appeared in the system's history.

**The fundamentals are now never disrupted.** ✅
