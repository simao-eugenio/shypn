# Timed/Stochastic Interference Investigation

## Issue Report
"somehow timed and stochastic are interfering in each other on an automatic created canvas"

## Hypothesis Testing

### Hypothesis 1: Shared State in TransitionState
**Status**: ❌ Unlikely
- Each transition has its own `TransitionState` keyed by `transition.id`
- No evidence of state sharing between different transitions

### Hypothesis 2: Cache Invalidation (Already Fixed)
**Status**: ✅ FIXED
- ModelAdapter cache now properly invalidates for all object types
- This was causing ALL types to fail, not specifically timed/stochastic

### Hypothesis 3: Properties Dictionary Mutation
**Status**: ❌ Not the issue
- `getattr(transition, 'properties', {})` returns a NEW dict if properties doesn't exist
- Imported transitions DO have `properties = {}` initialized (line 202 in pathway_converter.py)

### Hypothesis 4: Rate Parameter Ambiguity
**Status**: ⚠️ POSSIBLE
- Timed transitions: Use `rate` as delay (single value for both earliest and latest)
- Stochastic transitions: Use `rate` as lambda parameter (exponential distribution)
- When switching types, the `rate` value is reinterpreted

**Example**:
```
T1 as timed: rate=2.0 → earliest=2.0, latest=2.0
User switches to stochastic
T1 as stochastic: rate=2.0 → lambda=2.0 (mean delay = 1/2.0 = 0.5)
```

This is correct behavior, but might be confusing.

### Hypothesis 5: Enablement Time Initialization Order
**Status**: ⚠️ INVESTIGATING

**Scenario A - Manually Created**:
```
1. User creates transition T1 (type: continuous, no behavior yet)
2. User runs simulation
3. _update_enablement_states() called
4. Behavior created for T1
5. If enabled, set_enablement_time(current_time) called
6. Works correctly ✓
```

**Scenario B - Imported Model**:
```
1. SBML imported: transitions T1 (timed), T2 (stochastic) created
2. add_document() → _setup_canvas_manager() → _setup_edit_palettes()
3. SwissKnifePalette → SimulateToolsPaletteLoader → SimulationController created
4. ModelAdapter created
5. manager._notify_observers('created', T1)
6. controller._on_model_changed('created', T1)
7. Cache invalidated ✓
8. First simulation step:
   a. _update_enablement_states() called
   b. For T1 (timed): behavior created, set_enablement_time() called ✓
   c. For T2 (stochastic): behavior created, set_enablement_time() called ✓
9. Should work? But user reports interference...
```

### Hypothesis 6: Behavior Creation During Import
**Status**: 🔍 KEY ISSUE FOUND!

Looking at `_get_behavior` (lines 225-258 in controller.py):
```python
if transition.id not in self.behavior_cache:
    behavior = behavior_factory.create_behavior(transition, self.model_adapter)
    self.behavior_cache[transition.id] = behavior
    
    # Check if structurally enabled
    is_source = getattr(transition, 'is_source', False)
    if is_source:
        state.enablement_time = self.time
        if hasattr(behavior, 'set_enablement_time'):
            behavior.set_enablement_time(self.time)  # ← Called during import!
    else:
        # Check tokens...
        if locally_enabled:
            if hasattr(behavior, 'set_enablement_time'):
                behavior.set_enablement_time(self.time)  # ← Called during import!
```

**Problem**: When behaviors are created during import notification handling, `set_enablement_time()` is called with `self.time`, which is likely **time=0.0** (simulation hasn't started yet).

For StochasticBehavior, this means:
- `_enablement_time = 0.0`
- `_scheduled_fire_time = 0.0 + random_delay`
- If simulation starts later, the scheduled time might have already passed!

For TimedBehavior, this is less of an issue because it just stores the enablement time and checks the window each step.

## Testing Required

### Test 1: Check enablement time at import
Add logging:
```python
def set_enablement_time(self, time: float):
    print(f"[StochasticBehavior] {self.transition.name} enablement_time={time}")
    self._enablement_time = time
    delay = -math.log(random.random()) / self.rate
    self._scheduled_fire_time = time + delay
    print(f"[StochasticBehavior] {self.transition.name} scheduled_fire_time={self._scheduled_fire_time}")
```

### Test 2: Import model with mixed types
1. Import SBML with multiple transitions
2. Manually set some to timed, some to stochastic
3. Run simulation
4. Check if both types fire correctly

## Recommended Fix

**Issue**: Behaviors are initialized during import with `time=0.0`, but simulation might start at a different time.

**Solution**: Don't call `set_enablement_time()` during behavior creation in `_get_behavior()`. Let `_update_enablement_states()` handle it on the first simulation step.

**Change in controller.py `_get_behavior()` method**:
```python
# REMOVE this block (lines 231-258):
# if is_source:
#     state = self._get_or_create_state(transition)
#     state.enablement_time = self.time
#     if hasattr(behavior, 'set_enablement_time'):
#         behavior.set_enablement_time(self.time)
# else:
#     ... check tokens and set enablement ...

# Let _update_enablement_states() handle enablement on first step
```

**Rationale**:
- Behavior creation shouldn't trigger state initialization
- `_update_enablement_states()` is called at the START of each `step()`
- It will properly set enablement times when simulation actually begins
- Avoids timing issues with import-time initialization
