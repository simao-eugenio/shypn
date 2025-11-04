# Canvas State Issues - Historical Analysis & Comparison

**Date**: 2025-11-04  
**Context**: Recurring simulation issues after applying heuristic parameters

## Executive Summary

The symptoms you're seeing (transitions not firing after applying parameters) are **NOT new** - they are part of a **recurring pattern** of canvas state management issues that have been documented and partially fixed multiple times:

1. **Behavior Cache Bug** (Nov 1, 2025) - Transitions not firing after model reload
2. **Canvas Freeze Bug** (Nov 1, 2025) - Pan/zoom/edit broken after save/reload
3. **Comprehensive Canvas Reset** (Nov 2, 2025) - Full state reset for model loading

## Common Root Cause: State Persistence Across Operations

All these issues share the same fundamental problem:

> **State persists across document operations when it should be reset**

### The Pattern

```
Operation Flow:
1. User performs action (load file, apply parameters, import pathway)
2. Canvas objects are modified
3. Simulation state is NOT properly reset
4. Old state (cached behaviors, scheduled times, enablement flags) persists
5. Simulation behaves incorrectly (transitions don't fire, etc.)
```

---

## Issue #1: Behavior Cache Bug (Commit 864ae92)

### Symptom
- Transitions T3, T4 wouldn't fire after loading model
- **Exact same as your current issue**: "some transitions never fired"
- Delete + recreate transitions → fixed temporarily

### Root Cause
```python
# SimulationController maintains behavior cache by transition ID
self.behavior_cache = {}  # {transition_id: TransitionBehavior}

# When loading model with same transition IDs:
# 1. Old behaviors persist with stale state
# 2. Stochastic transitions think they're "not scheduled"
# 3. Transitions don't fire!
```

### Fix Applied
```python
def reset(self):
    """Reset simulation to initial marking."""
    self.time = 0.0
    self.transition_states.clear()
    
    # NEW: Clear behavior cache to prevent stale state
    for behavior in self.behavior_cache.values():
        if hasattr(behavior, 'clear_enablement'):
            behavior.clear_enablement()
    self.behavior_cache.clear()  # <-- FIX
    
    # Reset places to initial marking
    for place in self.model.places:
        place.tokens = place.initial_marking
```

### When This Gets Called
- User clicks reset button
- Model is loaded
- Simulation is stopped

---

## Issue #2: Canvas Freeze Bug (Commit df037a6)

### Symptom
- Pan/zoom/edit not working after save/reload
- Canvas appears frozen
- Right-click context menu broken

### Root Cause
```python
# When reusing existing tab for File→Open:
# 1. _setup_canvas_manager() NOT called
# 2. _suppress_callbacks stays True
# 3. Event handlers exist but manager state is stale
# 4. No reset of drag_state, arc_state, click_state
```

### Fix Applied
```python
def _reset_manager_for_load(self, manager, filename):
    """Reset manager state before loading objects from file.
    
    MUST be called BEFORE load_objects() when reusing a tab.
    """
    # Reset document metadata
    manager.filename = filename
    manager.modified = False
    
    # CRITICAL: Ensure callbacks are enabled
    manager._suppress_callbacks = False
    
    # Clear objects
    manager.places.clear()
    manager.transitions.clear()
    manager.arcs.clear()
    
    # Reset ID counters
    manager.document_controller._next_place_id = 1
    
    # Reset canvas interaction states
    self._drag_state[drawing_area] = {'active': False, ...}
    self._arc_state[drawing_area] = {'source': None, ...}
    self._click_state[drawing_area] = {'last_click_time': 0.0, ...}
    self._lasso_state[drawing_area] = {'active': False, ...}
```

### When This Gets Called
- File→Open (tab reuse)
- Import KEGG/SBML (tab reuse)

---

## Issue #3: Comprehensive Canvas Reset (Commit be02ff5)

### Symptom
- Old schedulers persisted across model loads
- Stale interaction guards blocked operations
- Palette tool state leaked between models

### Root Cause
```python
# SimulationController has many cached components:
# - behavior_cache (transition behaviors)
# - transition_states (enablement tracking)
# - schedulers (for timed/stochastic transitions)
# - interaction guards (for UI permissions)

# These persisted even after _reset_manager_for_load()
```

### Fix Applied
```python
def reset_for_new_model(self, new_model):
    """Reset controller for completely new model.
    
    More comprehensive than reset() - recreates all internal
    components with new model reference.
    """
    # Stop simulation
    if self._running:
        self.stop()
    
    # Update model reference
    self.model = new_model
    
    # Recreate model adapter
    self.model_adapter = ModelAdapter(new_model, controller=self)
    
    # Clear ALL state and caches
    self.time = 0.0
    self.behavior_cache.clear()
    self.transition_states.clear()
    self._round_robin_index = 0
    
    # Reset data collector
    if self.data_collector:
        self.data_collector.clear()
    
    # Invalidate state detector caches
    if hasattr(self.state_detector, '_cached_states'):
        self.state_detector._cached_states = {}
```

### Integration Point
```python
# Added to _reset_manager_for_load():
if drawing_area in self.simulation_controllers:
    controller = self.simulation_controllers[drawing_area]
    controller.reset_for_new_model(manager)  # <-- NEW
```

---

## Your Current Issue: Parameters Not Working Correctly

### Symptom (from your description)
> "all worked, but with the parameters inferred the simulation becomes very different, some transitions never fired"

### Why This Is The Same Pattern

When you apply heuristic parameters:

1. **Parameter application modifies transitions**
   ```python
   # heuristic_parameters_controller.py:apply_parameters()
   transition.properties['vmax'] = params.vmax
   transition.properties['km'] = params.km
   # ... etc
   ```

2. **Simulation state is NOT reset after modification**
   - Behavior cache still has old behaviors with old parameters
   - Cached behaviors calculated enablement/fire times with old values
   - New parameters exist on transition objects but cached behaviors ignore them

3. **Result: Stale cached behaviors use old parameter values**
   - Some transitions fire with wrong rates
   - Some transitions never fire (cached as "not enabled" with old params)
   - Simulation behavior is inconsistent

### The Missing Reset

Currently, `apply_parameters()` does:
```python
# Apply parameters to transitions
for row in self.model:
    if row[0]:  # If selected
        transition = row[10]
        # ... apply params ...

# Mark canvas dirty
canvas_manager.mark_dirty()
```

**But it does NOT reset simulation state!**

It should do:
```python
# After applying parameters, reset simulation
if drawing_area in canvas_loader.simulation_controllers:
    controller = canvas_loader.simulation_controllers[drawing_area]
    controller.reset()  # Clear behavior cache, reset enablement
```

---

## Comparison Table: All Three Issues

| Aspect | Behavior Cache Bug | Canvas Freeze Bug | Comprehensive Reset | **Your Current Issue** |
|--------|-------------------|-------------------|---------------------|----------------------|
| **Symptom** | Transitions don't fire | Canvas frozen | Stale state across models | Transitions don't fire correctly |
| **Operation** | Model reload | File→Open (reuse tab) | Import pathway | Apply parameters |
| **Root Cause** | Cached behaviors persist | _suppress_callbacks=True | Schedulers/guards persist | **Cached behaviors persist** |
| **Stale State** | behavior_cache | Manager flags | All controller state | **behavior_cache** |
| **Fix Location** | controller.reset() | _reset_manager_for_load() | reset_for_new_model() | **apply_parameters()** |
| **Fix Type** | Clear cache | Reset flags | Recreate components | **Need to add reset** |

---

## The Solution for Your Issue

### Option 1: Reset Simulation After Applying Parameters (Recommended)

Add to `heuristic_parameters_controller.py:apply_parameters()`:

```python
def apply_parameters(self):
    """Apply selected parameters to canvas transitions."""
    # ... existing code to apply parameters ...
    
    # CRITICAL: Reset simulation to clear cached behaviors
    # This ensures new parameters are used by recreating behaviors
    if hasattr(self.canvas_loader, 'simulation_controllers'):
        # Find drawing_area for this canvas_manager
        for drawing_area, manager in self.canvas_loader.managers.items():
            if manager == canvas_manager:
                if drawing_area in self.canvas_loader.simulation_controllers:
                    controller = self.canvas_loader.simulation_controllers[drawing_area]
                    # Clear behavior cache so new behaviors use new parameters
                    controller.reset()
                break
    
    self.canvas_manager.mark_dirty()
```

### Option 2: Auto-Reset on Property Change

Modify `ModelCanvasManager._on_object_changed()` to detect parameter changes:

```python
def _on_object_changed(self, obj, property_name, old_value, new_value):
    """Handle object property changes."""
    # ... existing dirty marking ...
    
    # If parameter changed, invalidate cached behavior for this transition
    if isinstance(obj, Transition) and property_name in ['vmax', 'km', 'kcat', 'lambda', 'delay']:
        # Notify simulation controller to invalidate behavior cache for this transition
        if hasattr(self, '_simulation_controller'):
            if obj.id in self._simulation_controller.behavior_cache:
                del self._simulation_controller.behavior_cache[obj.id]
```

### Option 3: Invalidate Specific Behaviors Only (Most Efficient)

Instead of clearing entire cache, invalidate only affected transitions:

```python
def apply_parameters(self):
    """Apply selected parameters to canvas transitions."""
    affected_transition_ids = []
    
    # Apply parameters and track affected transitions
    for row in self.model:
        if row[0]:  # Selected
            transition = row[10]
            # ... apply params ...
            affected_transition_ids.append(transition.id)
    
    # Invalidate behaviors for affected transitions only
    if hasattr(self.canvas_loader, 'simulation_controllers'):
        for drawing_area, manager in self.canvas_loader.managers.items():
            if manager == canvas_manager:
                if drawing_area in self.canvas_loader.simulation_controllers:
                    controller = self.canvas_loader.simulation_controllers[drawing_area]
                    # Remove only affected transitions from cache
                    for tid in affected_transition_ids:
                        if tid in controller.behavior_cache:
                            del controller.behavior_cache[tid]
                break
```

---

## Architectural Recommendation

This recurring pattern suggests we need a **unified state management strategy**:

### Proposal: Event-Driven State Invalidation

```python
class ModelCanvasManager:
    def __init__(self):
        self.state_invalidation_listeners = []
    
    def register_state_invalidation_listener(self, callback):
        """Register listener for state invalidation events."""
        self.state_invalidation_listeners.append(callback)
    
    def _invalidate_simulation_state(self, reason, affected_objects=None):
        """Notify all listeners that simulation state should be reset."""
        for callback in self.state_invalidation_listeners:
            callback(reason, affected_objects)

# SimulationController registers as listener
controller.model.register_state_invalidation_listener(
    lambda reason, objs: controller._handle_invalidation(reason, objs)
)

# Any code that modifies model triggers invalidation
canvas_manager._invalidate_simulation_state(
    reason='parameters_applied',
    affected_objects=[t1, t2, t3]
)
```

This would provide:
- **Single source of truth** for when state should reset
- **Automatic propagation** to all affected components
- **Granular control** (full reset vs. partial invalidation)
- **Audit trail** of what caused invalidation

---

## Immediate Next Steps

1. **Quick Fix** (5 minutes): Add `controller.reset()` to `apply_parameters()`
2. **Test** (10 minutes): Verify transitions fire correctly after parameter application
3. **Verify** (5 minutes): Check that parameter values are used (inspect cached behaviors)
4. **Document** (10 minutes): Add comments explaining why reset is needed

5. **Long-term** (future sprint):
   - Implement event-driven invalidation system
   - Add unit tests for state invalidation scenarios
   - Create invalidation audit log for debugging

---

## Lessons Learned

### The Real Problem Is NOT:
- ❌ Bad parameter values (though they may need refinement)
- ❌ Wrong inference heuristics
- ❌ UI bugs

### The Real Problem IS:
- ✅ **Cached state persisting across operations**
- ✅ **Missing state invalidation after model modifications**
- ✅ **Lack of unified state management strategy**

### Why This Keeps Happening:
1. **Complex stateful system** - Multiple caches, multiple components
2. **Many entry points** - File load, import, parameter apply, etc.
3. **No centralized invalidation** - Each component manages own state
4. **Implicit assumptions** - Code assumes state is fresh when it's not

### The Pattern Recognition:
```
IF: Model is modified (objects added/removed/changed)
THEN: Simulation state MUST be invalidated
BECAUSE: Cached behaviors/schedulers/guards reference old state
```

This should be **enforced architecturally**, not remembered procedurally.

---

## Conclusion

Your current issue is **not about parameter values** - it's about **stale cached state** after applying those parameters. The same bug pattern has appeared three times before:

1. Nov 1: Behavior cache persists after model reload → fixed with `reset()`
2. Nov 1: Manager flags persist after tab reuse → fixed with `_reset_manager_for_load()`
3. Nov 2: All controller state persists → fixed with `reset_for_new_model()`
4. **Nov 4: Behavior cache persists after parameter changes → needs same fix**

The solution is simple: **Reset simulation state after applying parameters**.

The deeper issue is: We need **architectural changes** to prevent this pattern from recurring.
