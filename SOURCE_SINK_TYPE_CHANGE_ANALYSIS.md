# Source/Sink Behavior During Transition Type Changes - Analysis

## Question
Is source/sink behavior properly maintained when transition types are switched during simulation?

## Answer: ✅ YES - Properly Wired

---

## Architecture Analysis

### 1. Behavior Creation and Caching

**Factory Pattern** (`behavior_factory.py`):
```python
def create_behavior(transition, model) -> TransitionBehavior:
    transition_type = getattr(transition, 'transition_type', 'immediate')
    type_map = {
        'immediate': ImmediateBehavior,
        'timed': TimedBehavior,
        'stochastic': StochasticBehavior,
        'continuous': ContinuousBehavior,
    }
    behavior_class = type_map[transition_type]
    return behavior_class(transition, model)  # Passes transition object reference
```

**Key Point**: Behavior classes store `self.transition = transition` (reference, not copy)

### 2. Source/Sink Property Access

All behavior classes use **runtime dynamic lookup**:

```python
# In can_fire() and fire() methods:
is_source = getattr(self.transition, 'is_source', False)
is_sink = getattr(self.transition, 'is_sink', False)
```

**Key Point**: Properties are read from the transition object at runtime, not cached in the behavior

### 3. Type Change Mechanism

**UI Handler** (`model_canvas_loader.py:_on_transition_type_change()`):
```python
def _on_transition_type_change(self, transition, new_type, manager, drawing_area):
    old_type = getattr(transition, 'transition_type', 'immediate')
    if old_type == new_type:
        return
    
    # 1. Update transition object
    transition.transition_type = new_type
    
    # 2. Mark file as dirty
    if self.persistency:
        self.persistency.mark_dirty()
    
    # 3. Invalidate behavior cache
    if drawing_area in self.simulate_tools_palettes:
        simulate_tools = self.simulate_tools_palettes[drawing_area]
        if simulate_tools.simulation:
            if transition.id in simulate_tools.simulation.behavior_cache:
                del simulate_tools.simulation.behavior_cache[transition.id]
    
    # 4. Update UI panels
    # ... trigger panel updates ...
    
    # 5. Redraw
    drawing_area.queue_draw()
```

### 4. Simulation Controller Cache Management

**Automatic Cache Validation** (`controller.py:_get_behavior()`):
```python
def _get_behavior(self, transition):
    # Check if cached behavior type matches current transition type
    if transition.id in self.behavior_cache:
        cached_behavior = self.behavior_cache[transition.id]
        cached_type = cached_behavior.get_type_name()
        current_type = getattr(transition, 'transition_type', 'immediate')
        
        # Type name normalization
        type_name_map = {
            'Immediate': 'immediate',
            'Timed (TPN)': 'timed',
            'Stochastic (FSPN)': 'stochastic',
            'Continuous (SHPN)': 'continuous'
        }
        cached_type_normalized = type_name_map.get(cached_type, cached_type.lower())
        
        # Invalidate if type changed
        if cached_type_normalized != current_type:
            if hasattr(cached_behavior, 'clear_enablement'):
                cached_behavior.clear_enablement()
            del self.behavior_cache[transition.id]
            if transition.id in self.transition_states:
                del self.transition_states[transition.id]
    
    # Create new behavior if not cached
    if transition.id not in self.behavior_cache:
        behavior = behavior_factory.create_behavior(transition, self.model_adapter)
        self.behavior_cache[transition.id] = behavior
    
    return self.behavior_cache[transition.id]
```

**Key Points**:
- Controller validates cache on every access
- Type mismatch triggers automatic cache invalidation
- New behavior instance created from same transition object
- Enablement state cleared when type changes

---

## Source/Sink Preservation Flow

### Scenario: User Changes Transition Type During Simulation

**Initial State**:
```
Transition T1:
  - transition_type = 'immediate'
  - is_source = True
  - is_sink = False

Behavior Cache:
  - T1.id → ImmediateBehavior(T1, model)
```

**User Action**: Right-click → Change Type → Timed

**Step-by-Step Flow**:

1. **UI Handler Invoked**:
   ```python
   _on_transition_type_change(T1, 'timed', ...)
   ```

2. **Transition Object Modified**:
   ```python
   T1.transition_type = 'timed'  # Changed
   T1.is_source = True            # Preserved (unchanged)
   T1.is_sink = False             # Preserved (unchanged)
   ```

3. **Behavior Cache Invalidated**:
   ```python
   del behavior_cache[T1.id]  # Old ImmediateBehavior removed
   ```

4. **Next Simulation Step**:
   ```python
   behavior = controller._get_behavior(T1)
   # Cache miss → creates new TimedBehavior(T1, model)
   ```

5. **New Behavior Reads Properties**:
   ```python
   # In TimedBehavior.can_fire():
   is_source = getattr(self.transition, 'is_source', False)
   # → Reads T1.is_source → True ✅
   
   if is_source:
       return True, "enabled-source"  # Source semantics preserved!
   ```

6. **New Behavior Fires**:
   ```python
   # In TimedBehavior.fire():
   is_source = getattr(self.transition, 'is_source', False)  # True
   is_sink = getattr(self.transition, 'is_sink', False)      # False
   
   if not is_source:  # False (is_source=True)
       # Skip this block ✅
       for arc in input_arcs:
           # ... token consumption ...
   
   if not is_sink:    # True (is_sink=False)
       # Execute this block ✅
       for arc in output_arcs:
           # ... token production ...
   ```

**Result**: Source behavior maintained across type change!

---

## Critical Design Decisions

### ✅ Why It Works

1. **Reference Semantics**: Behaviors store reference to transition object, not properties
   - `self.transition` points to same object before and after type change
   - Properties are read dynamically on each method call

2. **Runtime Property Lookup**: Using `getattr()` instead of caching
   - `is_source` read from transition object during `can_fire()` and `fire()`
   - Not stored in behavior instance variables
   - Always reflects current state of transition

3. **Cache Invalidation**: Automatic on type mismatch
   - Controller validates cache on every `_get_behavior()` call
   - UI handler explicitly invalidates on type change
   - Prevents stale behavior instances

4. **State Clearing**: Enablement state cleared on invalidation
   - Timing information reset
   - Scheduled fire times cleared
   - Prevents temporal state corruption

### ⚠️ Potential Issues (None Found)

**Checked for**:
- ❌ Behavior caching `is_source`/`is_sink` in `__init__` → Not happening ✅
- ❌ Type change not invalidating cache → Handled in two places ✅
- ❌ New behavior reading old transition object → Same object reference ✅
- ❌ Properties not preserved during type change → Only `transition_type` changes ✅

---

## Test Scenarios

### Test 1: Immediate → Timed (Source Preserved)
```python
# Setup
T1 = Transition(type='immediate', is_source=True)
behavior1 = ImmediateBehavior(T1, model)
assert behavior1.can_fire() == (True, "enabled-source")

# Type change
T1.transition_type = 'timed'
controller.invalidate_behavior_cache(T1.id)

# New behavior
behavior2 = TimedBehavior(T1, model)
behavior2.set_enablement_time(0.0)
model.time = 5.0
assert behavior2.can_fire() == (True, "enabled-source (elapsed=5.0)")

# Source semantics preserved ✅
```

### Test 2: Stochastic → Continuous (Sink Preserved)
```python
# Setup
T2 = Transition(type='stochastic', is_sink=True)
behavior1 = StochasticBehavior(T2, model)
# Sink requires tokens to enable
assert behavior1.can_fire()[0] == depends_on_tokens

# Type change
T2.transition_type = 'continuous'
controller.invalidate_behavior_cache(T2.id)

# New behavior
behavior2 = ContinuousBehavior(T2, model)
# Sink semantics preserved: still needs tokens
result = behavior2.fire(input_arcs, output_arcs)
# Should consume tokens but not produce ✅
```

### Test 3: Source+Sink → Different Type
```python
# Setup
T3 = Transition(type='immediate', is_source=True, is_sink=True)

# Change type
T3.transition_type = 'timed'
controller.invalidate_behavior_cache(T3.id)

# New behavior should preserve both flags
behavior = TimedBehavior(T3, model)
assert getattr(behavior.transition, 'is_source', False) == True
assert getattr(behavior.transition, 'is_sink', False) == True
# Both semantics preserved ✅
```

---

## Verification Checklist

### Property Persistence
- [x] `is_source` property preserved on transition object during type change
- [x] `is_sink` property preserved on transition object during type change
- [x] Only `transition_type` modified by type change handler

### Behavior Creation
- [x] New behavior receives reference to same transition object
- [x] Behavior reads `is_source`/`is_sink` dynamically via `getattr()`
- [x] Properties not cached in behavior instance variables

### Cache Management
- [x] UI handler invalidates cache on explicit type change
- [x] Controller validates cache on every access
- [x] Type mismatch triggers automatic cache invalidation
- [x] Enablement state cleared on cache invalidation

### Simulation Correctness
- [x] Source enablement logic preserved across type changes
- [x] Sink enablement logic preserved across type changes
- [x] Token consumption skipped for sources (all types)
- [x] Token production skipped for sinks (all types)

---

## Conclusion

### ✅ Properly Wired: Source/Sink Behavior IS Maintained

The architecture correctly preserves source/sink semantics during transition type changes through:

1. **Reference-based design**: Behaviors hold reference to transition object
2. **Runtime property lookup**: `getattr()` reads current values
3. **Automatic cache invalidation**: Type changes trigger behavior recreation
4. **State clearing**: Temporal state reset on type change

### No Changes Required

The current implementation is **correct and robust**. Source and sink properties:
- Are stored on the transition object (not behavior instances)
- Are read dynamically during simulation
- Persist across type changes
- Work correctly with all four transition types

### Recommendation: Add Integration Test

While the architecture is sound, add an integration test to verify:

```python
def test_source_sink_preserved_on_type_change():
    """Verify source/sink behavior maintained when switching transition types."""
    model = create_test_model()
    T = Transition(x=0, y=0, transition_type='immediate', is_source=True)
    
    # Test all type transitions
    types = ['immediate', 'timed', 'stochastic', 'continuous']
    for new_type in types:
        T.transition_type = new_type
        controller.invalidate_behavior_cache(T.id)
        behavior = controller._get_behavior(T)
        
        # Verify source semantics preserved
        assert behavior.can_fire()[0] == True, f"Source not enabled for {new_type}"
        
        # Verify firing behavior
        success, result = behavior.fire([], output_arcs)
        assert len(result['consumed']) == 0, f"Source consumed tokens for {new_type}"
```

### Status
**✅ VERIFIED**: Source/sink behavior properly wired during transition type commutation
