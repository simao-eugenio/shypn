# Behavior Cache Bug Fix - Transitions Not Firing After Model Reload

## Issue

**Symptom**: Transitions (T3, T4) that should fire don't fire after loading a model, but work correctly after deleting and recreating them.

**Root Cause**: The `SimulationController` caches `TransitionBehavior` instances by transition ID for performance. When a model is reloaded (or a different model with the same transition IDs is loaded), the cached behaviors from the previous model persist, carrying stale state such as:
- Old scheduled fire times
- Old enablement states  
- Stale token requirements

## Discovery Process

User reported that hsa00010.shy model with catalysts had transitions T3 and T4 that wouldn't fire despite:
- ✅ All input arcs enabled (sufficient tokens)
- ✅ Correct transition types (T3: stochastic, T4: continuous)
- ✅ Valid rate formulas
- ✅ Proper test arcs for enzymes

When the user **deleted and recreated** T3 and T4, they fired correctly. This indicated the transitions themselves were configured correctly, but something about the existing transitions was broken.

## Analysis

### Behavior Cache Mechanism

```python
class SimulationController:
    def __init__(self, model):
        self.behavior_cache = {}  # {transition_id: TransitionBehavior}
        
    def _get_behavior(self, transition):
        if transition.id not in self.behavior_cache:
            behavior = behavior_factory.create_behavior(transition, self.model_adapter)
            self.behavior_cache[transition.id] = behavior
        return self.behavior_cache[transition.id]
```

The cache improves performance by reusing behavior objects across simulation steps. However, it persists across:
- Simulation reset
- Model reload
- Switching between models

### Why Delete/Recreate Fixed It

When deleting and recreating transitions:
1. Old transitions T3, T4 are deleted
2. New transitions are created with **new IDs** (e.g., T40, T41)
3. Cache lookup fails for T40/T41 (no cached entry)
4. Fresh behaviors are created
5. Everything works!

### The Actual Bug

When reloading the same model (or loading a different model with same IDs):
1. Load model with T3, T4
2. Behaviors cached as `{"T3": behavior_t3, "T4": behavior_t4}`
3. Simulation runs, behaviors may have scheduled fire times set
4. Reload model (same T3, T4 IDs)
5. **Cached behaviors are reused** with stale state
6. Stochastic transitions may think they're "not-scheduled" or "too-early"
7. Transitions don't fire!

## Solution

**Clear the behavior cache in `reset()` method:**

```python
def reset(self):
    """Reset simulation to initial marking.
    
    Also clears behavior cache to prevent stale state across model reloads.
    """
    self.time = 0.0
    self.transition_states.clear()
    
    # Clear behavior cache (NEW)
    for behavior in self.behavior_cache.values():
        if hasattr(behavior, 'clear_enablement'):
            behavior.clear_enablement()
    self.behavior_cache.clear()  # <-- FIX
    
    # Reset places to initial marking
    for place in self.model.places:
        place.tokens = place.initial_marking
    
    # Re-initialize enablement
    self._update_enablement_states()
```

### Why This Works

1. `reset()` is called when:
   - User clicks reset button
   - Model is loaded (presumably via application code)
   - Simulation is stopped and restarted
   
2. Clearing the cache forces all behaviors to be recreated on next access
3. New behaviors have fresh state (no stale fire times, enablement, etc.)
4. Transitions fire correctly

### Alternative Approaches Considered

**Option 2: Clear only on model replacement**
- Requires detecting "model replaced" events
- More complex to implement
- Benefits: More targeted, preserves cache during simple reset

**Option 3: Object identity checking**
- Use weakref to transition object in cache key
- Automatic invalidation when transition object changes
- Benefits: Most precise
- Drawbacks: More complex, potential memory issues

**Chosen: Option 1** (clear on reset) because:
- Simple and robust
- Covers all reload scenarios
- Minimal performance impact (behaviors recreated only on reset)
- Reset is infrequent compared to simulation steps

## Cache Invalidation Strategy

The complete strategy now includes:

1. **Type change**: `_get_behavior()` checks if cached type matches current type, invalidates if mismatch
2. **Reset**: `reset()` clears entire cache (prevents stale state)
3. **Object deletion**: `_on_model_changed()` removes deleted transition from cache
4. **Arc changes**: `_on_model_changed()` invalidates affected transition behaviors

## Testing

To verify the fix:
1. Load hsa00010.shy model
2. Set P101 initial tokens = 5.0
3. Start simulation
4. Verify T3 and T4 fire (P105 gets tokens)
5. Stop and reset simulation
6. Start again - should still work (cache cleared on reset)
7. Load model again - should still work

## Related Files

- `src/shypn/engine/simulation/controller.py` - SimulationController with behavior cache
- `src/shypn/engine/behavior_factory.py` - Creates behavior instances
- `src/shypn/engine/stochastic_behavior.py` - Stochastic transition logic with scheduling
- `src/shypn/engine/continuous_behavior.py` - Continuous transition logic

## Prevention

Future improvements to prevent similar issues:
1. Add cache diagnostics (log cache hits/misses, age of cached behaviors)
2. Add validation that cached behavior's transition object matches current
3. Consider time-to-live (TTL) for cache entries
4. Add unit tests for cache invalidation scenarios
