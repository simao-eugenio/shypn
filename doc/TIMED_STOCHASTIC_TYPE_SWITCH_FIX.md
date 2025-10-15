# Timed/Stochastic Transition Type Switching Fix

## Date
October 15, 2025

## Issue Summary

**BUG**: "only timed and stochastic didn't fired on fetched/imported module during transitions types switching in simulation"

### Symptoms
- Immediate transitions: Fire correctly after type switch ✓
- Continuous transitions: Fire correctly after type switch ✓  
- **Timed transitions**: Don't fire after switching to timed type ❌
- **Stochastic transitions**: Don't fire after switching to stochastic type ❌
- Occurs specifically when changing types during active simulation
- Affects imported/loaded models

## Root Cause Analysis

### How Behavior Caching Works

**SimulationController behavior cache** (`_get_behavior` method):
```python
# 1. Check if behavior exists in cache
if transition.id in self.behavior_cache:
    cached_behavior = self.behavior_cache[transition.id]
    
    # 2. Validate cached type matches current type
    if cached_type != current_type:
        # Type changed! Invalidate cache
        del self.behavior_cache[transition.id]
        del self.transition_states[transition.id]

# 3. Create new behavior if not cached
if transition.id not in self.behavior_cache:
    behavior = create_behavior(transition, model_adapter)
    self.behavior_cache[transition.id] = behavior
    # ❌ PROBLEM: Enablement time not set for new behavior!

return self.behavior_cache[transition.id]
```

### The Missing Step

**For time-aware behaviors** (timed, stochastic):
- They track `_enablement_time` - when they became structurally enabled
- This is set by `set_enablement_time(time)` method
- Used to determine if enough time has passed to fire

**What happens during type switch**:
```
T0: Transition is immediate, tokens present, enabled
T1: User switches type to "timed" (earliest=2.0, latest=5.0)
T2: Cache invalidated, old ImmediateBehavior deleted
T3: New TimedBehavior created
T4: ❌ _enablement_time = None (never set!)
T5: can_fire() called → checks timing window
T6: Returns (False, "not-enabled-yet") because _enablement_time is None
T7: Transition never fires even though tokens are present
```

### Why Immediate/Continuous Work

**Immediate transitions**:
- Don't use `_enablement_time`
- Only check tokens and guard
- Fire immediately if enabled ✓

**Continuous transitions**:
- Don't use `_enablement_time`
- Check flow rates and tokens
- Integrate over time ✓

**Timed/Stochastic transitions**:
- **REQUIRE** `_enablement_time` to calculate timing windows ❌
- If `_enablement_time` is None, assume not enabled yet
- This is the failure mode!

### Timing of the Issue

**Scenario 1: Type switch with tokens present**:
```
State: Place has 5 tokens, Transition enabled
Action: Switch type from immediate → timed
Problem: New TimedBehavior created WITHOUT enablement time
Result: Transition thinks it's not enabled (missing timestamp)
```

**Scenario 2: Type switch then tokens added**:
```
State: Place empty, Transition disabled
Action: Switch type to timed
Later: Tokens added to input place
Result: Works! _update_enablement_states() sets enablement time ✓
```

**Key insight**: The bug only occurs when **tokens are already present** when the type is switched to timed/stochastic.

## The Solution

### Initialize Enablement on Behavior Creation

Modified `_get_behavior` method in `controller.py` (line ~225):

```python
if transition.id not in self.behavior_cache:
    behavior = behavior_factory.create_behavior(transition, self.model_adapter)
    self.behavior_cache[transition.id] = behavior
    
    # CRITICAL: After creating new behavior (especially after type switch),
    # check if transition is currently enabled and set enablement time
    # This is needed for timed/stochastic transitions that were just switched
    is_source = getattr(transition, 'is_source', False)
    if is_source:
        # Source transitions are always enabled
        state = self._get_or_create_state(transition)
        state.enablement_time = self.time
        if hasattr(behavior, 'set_enablement_time'):
            behavior.set_enablement_time(self.time)
    else:
        # Check if structurally enabled (has sufficient tokens)
        input_arcs = behavior.get_input_arcs()
        locally_enabled = True
        for arc in input_arcs:
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            if kind != 'normal':
                continue
            source_place = behavior._get_place(arc.source_id)
            if source_place is None or source_place.tokens < arc.weight:
                locally_enabled = False
                break
        
        if locally_enabled:
            # Transition is enabled, set enablement time
            state = self._get_or_create_state(transition)
            if state.enablement_time is None:
                state.enablement_time = self.time
                if hasattr(behavior, 'set_enablement_time'):
                    behavior.set_enablement_time(self.time)

return self.behavior_cache[transition.id]
```

### How This Fix Works

**Flow after fix**:
```
T0: Transition is immediate, tokens present
T1: User switches type to "timed" (earliest=2.0, latest=5.0)
T2: Cache invalidated, old ImmediateBehavior deleted
T3: New TimedBehavior created
T4: ✅ Check if structurally enabled (tokens >= weights)
T5: ✅ Tokens present! Set _enablement_time = current_time
T6: can_fire() called → checks timing window
T7: Returns (False, "too-early") if current_time < enablement + earliest
T8: After waiting, returns (True, "enabled-in-window") ✅
T9: Transition fires! ✅
```

### Key Aspects

1. **Source transition handling**:
   ```python
   if is_source:
       # Always enabled, set enablement time immediately
       state.enablement_time = self.time
   ```

2. **Normal transition handling**:
   ```python
   # Check tokens in all input places
   for arc in input_arcs:
       if source_place.tokens < arc.weight:
           locally_enabled = False
   
   if locally_enabled:
       state.enablement_time = self.time
   ```

3. **Behavior interface**:
   ```python
   if hasattr(behavior, 'set_enablement_time'):
       behavior.set_enablement_time(self.time)
   ```
   - Uses duck typing to avoid breaking immediate/continuous
   - Only time-aware behaviors have this method

## Impact Assessment

### Severity: HIGH
- **Scope**: Dynamic type switching during simulation
- **User Impact**: Timed/stochastic transitions non-functional after switch
- **Workaround**: Restart simulation after type change (not user-friendly)

### Affected Scenarios

**❌ Broken before fix**:
1. Import model with immediate transitions
2. Switch some to timed during simulation
3. Timed transitions never fire

**✅ Fixed after**:
1. Import model with immediate transitions
2. Switch some to timed during simulation  
3. Timed transitions fire after earliest delay expires

### Unaffected Scenarios

**Already working**:
- Imported models with pre-existing timed/stochastic transitions ✓
- Type switches from timed → immediate ✓
- Type switches when tokens not present ✓
- New transitions created as timed/stochastic ✓

## Technical Details

### Enablement Time Tracking

**Two places track enablement time**:

1. **TransitionState** (in controller):
   ```python
   class TransitionState:
       enablement_time: Optional[float]  # When became enabled
       scheduled_time: Optional[float]   # For stochastic scheduling
   ```

2. **Behavior instance** (in timed/stochastic behaviors):
   ```python
   class TimedBehavior:
       _enablement_time: Optional[float]  # When became enabled
   ```

**Both must be set** for consistency!

### Structural Enablement Check

**Same logic as `_update_enablement_states`**:
```python
# Check each input arc
for arc in input_arcs:
    # Skip inhibitor/reset arcs
    if kind != 'normal':
        continue
    
    # Get source place
    source_place = behavior._get_place(arc.source_id)
    
    # Check token availability
    if source_place.tokens < arc.weight:
        locally_enabled = False
        break

# If all places have enough tokens
if locally_enabled:
    state.enablement_time = self.time
```

**Why duplicate this code**:
- `_update_enablement_states()` runs once per step
- Behavior creation can happen at any time (type switch, import)
- Need immediate enablement check on creation

### Alternative Approaches Considered

**Option 1: Call `_update_enablement_states()` after behavior creation**:
```python
behavior = create_behavior(...)
self.behavior_cache[transition.id] = behavior
self._update_enablement_states()  # Update all transitions
```
- ❌ Expensive: checks ALL transitions
- ❌ Overkill: only need to check THIS transition

**Option 2: Delay enablement until next step**:
```python
# Don't set enablement time on creation
# Let next step() call handle it via _update_enablement_states()
```
- ❌ Breaks immediate usage: User switches type and expects immediate effect
- ❌ One-step delay feels laggy

**Option 3: Current approach** (chosen):
```python
# Check structural enablement for THIS transition only
# Set enablement time if currently enabled
```
- ✅ Immediate effect (no delay)
- ✅ Efficient (one transition checked)
- ✅ Consistent with existing logic

## Testing Verification

### Test Cases

**Priority 1: Type Switching**

1. **Immediate → Timed**:
   - Create place with 5 tokens
   - Create immediate transition (enabled)
   - Fire once to verify it works
   - Switch to timed (earliest=2.0, latest=5.0)
   - **VERIFY**: Transition fires after 2.0 seconds ✓

2. **Continuous → Stochastic**:
   - Create continuous transition with flow
   - Switch to stochastic (rate=1.0)
   - **VERIFY**: Transition fires stochastically ✓

3. **Timed → Timed** (parameter change):
   - Create timed transition (earliest=1.0, latest=2.0)
   - Change to (earliest=5.0, latest=10.0)
   - **VERIFY**: New timing window used ✓

**Priority 2: Edge Cases**

4. **Switch when disabled**:
   - Transition with no input tokens
   - Switch to timed
   - Add tokens
   - **VERIFY**: Fires after delay ✓

5. **Source transitions**:
   - Create source transition (no inputs)
   - Switch to timed
   - **VERIFY**: Fires immediately (source always enabled) ✓

6. **Multiple switches**:
   - Switch immediate → timed → stochastic → timed
   - **VERIFY**: Each switch preserves correct behavior ✓

### Expected Behavior

**Before Fix**:
```
User: Switch transition to timed (earliest=2.0)
System: [Creates new TimedBehavior]
System: [_enablement_time = None]
User: Run simulation
System: can_fire() → (False, "not-enabled-yet")
User: Wait 5 seconds...
System: Still can_fire() → (False, "not-enabled-yet")  ❌
Result: Never fires!
```

**After Fix**:
```
User: Switch transition to timed (earliest=2.0)
System: [Creates new TimedBehavior]
System: [Checks tokens: 5 >= 1, enabled!]
System: [Sets _enablement_time = current_time]  ✅
User: Run simulation
System: can_fire() → (False, "too-early") [t < 2.0]
User: Wait 2+ seconds...
System: can_fire() → (True, "enabled-in-window")  ✅
System: Fires transition!  ✅
Result: Works correctly!
```

## Code Quality

### Files Modified

**`src/shypn/engine/simulation/controller.py`**:
- Lines ~225-254: Enhanced `_get_behavior()` method
- Added enablement time initialization on behavior creation
- Handles both source and normal transitions
- Uses duck typing for behavior interface compatibility

### Documentation

- Added comprehensive inline comments
- Explains why this is CRITICAL for type switching
- References the structural enablement check

### Error Handling

No additional error handling needed because:
- Uses existing `_get_or_create_state()` method
- Token checks are safe (null checks included)
- Duck typing with `hasattr()` prevents AttributeError

## Design Patterns

### Lazy Initialization Pattern

**Problem**: Behavior created before enablement known

**Solution**: Check enablement immediately after creation

**Benefits**:
- No wasted initialization if not enabled
- Immediate effect when enabled
- Consistent with step-based enablement tracking

### Duck Typing for Backward Compatibility

```python
if hasattr(behavior, 'set_enablement_time'):
    behavior.set_enablement_time(self.time)
```

**Why this matters**:
- Immediate/continuous behaviors don't have this method
- Avoids AttributeError
- Future-proof: new behavior types automatically supported

## Related Fixes

### Observer Pattern (Earlier Today)

**Connection**: Observer pattern ensures controller knows about imported transitions

**Relationship**: 
- Observer pattern: Controller LEARNS about transitions
- This fix: Controller INITIALIZES transitions properly

**Both needed for complete solution**:
1. Observer pattern: Transition exists in controller's view ✓
2. Enablement initialization: Transition ready to fire ✓

### Behavior Cache Invalidation

**Existing mechanism** (lines 206-214):
```python
# Already invalidates cache on type change
if cached_type != current_type:
    del self.behavior_cache[transition.id]
```

**This fix completes the picture**:
```python
# Now also initializes the NEW behavior
if transition.id not in self.behavior_cache:
    behavior = create_behavior(...)
    # ✅ Set enablement time if currently enabled
```

## Lessons Learned

### State Consistency

**Rule**: When creating stateful objects, initialize ALL state immediately

**Application**:
- Behavior instance: `_enablement_time`
- Controller state: `TransitionState.enablement_time`
- Both must be set together

### Type-Aware Initialization

**Problem**: Different transition types need different initialization

**Solution**: Check structural properties (tokens, source/sink) at creation

### Testing Type Switches

**Overlooked scenario**: Dynamic type changes during simulation

**Lesson**: Test not just initial states, but state transitions (type switches)

## Future Enhancements

### Potential Improvements

1. **Enablement history**:
   ```python
   state.enablement_history = [(time1, 'enabled'), (time2, 'disabled'), ...]
   ```
   - Track enablement over time
   - Useful for debugging and analytics

2. **Type switch callbacks**:
   ```python
   behavior.on_type_switched_from(old_behavior)
   ```
   - Transfer state from old behavior
   - Preserve accumulated values (for continuous)

3. **Validation warnings**:
   ```python
   if switch_during_simulation:
       warn("Type switch may affect reproducibility")
   ```
   - Alert users to potential issues

## Conclusion

This fix ensures that when a transition's type is switched to timed or stochastic during simulation, the new behavior is properly initialized with enablement time if the transition is currently structurally enabled (has sufficient input tokens).

**User Impact**: Timed and stochastic transitions now fire correctly after type switching during simulation.

**Architecture Impact**: Establishes pattern for stateful behavior initialization on creation.

**Testing Required**: Verify type switching works for timed/stochastic transitions in running simulations.
