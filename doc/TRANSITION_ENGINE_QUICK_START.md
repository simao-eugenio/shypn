# Transition Engine - Quick Start Guide

**Status**: ✅ Complete (Phases 1-6)  
**Location**: `src/shypn/engine/`  
**Total**: 1,663 lines, 7 files

---

## Quick Import

```python
# Import everything you need
from shypn.engine import (
    # Factory (recommended)
    create_behavior,
    get_available_types,
    
    # Or import specific behaviors
    ImmediateBehavior,
    TimedBehavior,
    StochasticBehavior,
    ContinuousBehavior,
    
    # Base class (for type checking)
    TransitionBehavior
)
```

---

## Quick Usage

### Option 1: Use Factory (Recommended)

```python
# Factory automatically selects the right behavior
behavior = create_behavior(transition, model)

# Standard interface for all types
can_fire, reason = behavior.can_fire()
if can_fire:
    success, details = behavior.fire(
        behavior.get_input_arcs(),
        behavior.get_output_arcs()
    )
```

### Option 2: Direct Instantiation

```python
# For immediate control over behavior type
behavior = ImmediateBehavior(transition, model)
behavior = TimedBehavior(transition, model)
behavior = StochasticBehavior(transition, model)
behavior = ContinuousBehavior(transition, model)
```

---

## Behavior Types Cheat Sheet

| Type | Class | Delay | Tokens | Key Feature |
|------|-------|-------|--------|-------------|
| **Immediate** | `ImmediateBehavior` | Zero | Discrete | Instant firing |
| **Timed** | `TimedBehavior` | [earliest, latest] | Discrete | Timing windows |
| **Stochastic** | `StochasticBehavior` | Exponential | Burst (1x-8x) | Random + bursts |
| **Continuous** | `ContinuousBehavior` | Continuous | Continuous flow | Rate functions |

---

## Type-Specific APIs

### Immediate Transitions

```python
behavior = ImmediateBehavior(transition, model)

# Check enablement
can_fire, reason = behavior.can_fire()
# Returns: (True, "enabled") or (False, "insufficient-tokens-P5")

# Fire
success, details = behavior.fire(input_arcs, output_arcs)
# Returns: (True, {'consumed': {1: 5}, 'produced': {2: 3}, ...})

# Debug
info = behavior.get_enablement_info()
# Returns: {'is_enabled': True, 'input_places': [...]}
```

### Timed Transitions (TPN)

```python
behavior = TimedBehavior(transition, model)
# transition.properties = {'earliest': 2.0, 'latest': 5.0}

# Set when enabled
behavior.set_enablement_time(current_time)

# Check timing window
can_fire, reason = behavior.can_fire()
# Returns: (True, "enabled-in-window (elapsed=3.5)")
#       or (False, "too-early (elapsed=1.2, earliest=2.0)")

# Get timing info
timing = behavior.get_timing_info()
# Returns: {
#   'elapsed': 3.5,
#   'in_window': True,
#   'must_fire_before': 15.0,
#   'time_remaining': 1.5
# }

# Check urgency
if behavior.is_urgent():
    # Fire ASAP!
    success, details = behavior.fire(input_arcs, output_arcs)

# Clear when disabled
behavior.clear_enablement()
```

### Stochastic Transitions (FSPN)

```python
behavior = StochasticBehavior(transition, model)
# transition.properties = {'rate': 2.5, 'max_burst': 8}

# Enable (automatically samples delay and burst)
behavior.set_enablement_time(current_time)

# Get scheduled info
fire_time = behavior.get_scheduled_fire_time()
burst = behavior.get_sampled_burst()
print(f"Will fire at {fire_time} with burst {burst}x")

# Check if ready
can_fire, reason = behavior.can_fire()
# Returns: (True, "enabled-stochastic (burst=5)")
#       or (False, "too-early (remaining=0.345)")

# Fire when ready
if current_time >= fire_time:
    success, details = behavior.fire(input_arcs, output_arcs)
    print(f"Burst size: {details['burst_size']}")

# Get info
info = behavior.get_stochastic_info()
# Returns: {
#   'rate': 2.5,
#   'max_burst': 8,
#   'mean_delay': 0.4,
#   'scheduled_fire_time': 12.345,
#   'sampled_burst': 5
# }

# Resample burst (if needed)
behavior.resample_burst()
```

### Continuous Transitions (SHPN)

```python
behavior = ContinuousBehavior(transition, model)
# transition.properties = {
#   'rate_function': '2.0 * P1',  # or constant, or callable
#   'max_rate': 10.0
# }

# Main method: integrate over time step
dt = 0.01  # 10ms
success, details = behavior.integrate_step(dt, input_arcs, output_arcs)
# Returns: (True, {
#   'consumed': {1: 0.05},  # Continuous amounts
#   'produced': {2: 0.03},
#   'rate': 5.2,
#   'dt': 0.01,
#   'method': 'rk4'
# })

# Preview without applying
prediction = behavior.predict_flow(dt)
# Returns: {
#   'rate': 5.2,
#   'dt': 0.01,
#   'consumed': {1: 0.05},
#   'produced': {2: 0.03}
# }

# Evaluate current rate
rate = behavior.evaluate_current_rate()
print(f"Current rate: {rate}")

# Get info
info = behavior.get_continuous_info()
# Returns: {
#   'max_rate': 10.0,
#   'min_rate': 0.0,
#   'integration_method': 'rk4'
# }
```

---

## Common Patterns

### Pattern 1: Check and Fire

```python
behavior = create_behavior(transition, model)

can_fire, reason = behavior.can_fire()
if can_fire:
    success, details = behavior.fire(
        behavior.get_input_arcs(),
        behavior.get_output_arcs()
    )
    if success:
        print(f"Fired! Consumed: {details['consumed']}")
    else:
        print(f"Failed: {details['reason']}")
else:
    print(f"Cannot fire: {reason}")
```

### Pattern 2: Continuous Integration Loop

```python
behavior = ContinuousBehavior(transition, model)

dt = 0.01  # Time step
for step in range(1000):
    success, details = behavior.integrate_step(
        dt,
        behavior.get_input_arcs(),
        behavior.get_output_arcs()
    )
    
    if not success:
        print(f"Integration stopped: {details['reason']}")
        break
    
    current_time += dt
```

### Pattern 3: Scheduled Firing (Timed/Stochastic)

```python
# For timed or stochastic transitions
behavior.set_enablement_time(current_time)

# Later, check if ready
if behavior.can_fire()[0]:
    behavior.fire(input_arcs, output_arcs)
```

### Pattern 4: Type Checking

```python
behavior = create_behavior(transition, model)

# Check specific type
if isinstance(behavior, ContinuousBehavior):
    # Use integrate_step instead of fire
    behavior.integrate_step(dt, arcs_in, arcs_out)
else:
    # Standard discrete firing
    behavior.fire(arcs_in, arcs_out)

# Or check by name
if behavior.get_type_name() == "Continuous (SHPN)":
    # Special handling
```

---

## Return Value Structures

### `can_fire()` Return

```python
(bool, str)
```

**Examples**:
- `(True, "enabled")` - Immediate, ready to fire
- `(True, "enabled-in-window (elapsed=3.5)")` - Timed, within window
- `(False, "insufficient-tokens-P5")` - Not enough tokens
- `(False, "too-early (remaining=0.5)")` - Stochastic, not ready yet

### `fire()` Return (Success)

```python
(True, {
    'consumed': {place_id: amount, ...},
    'produced': {place_id: amount, ...},
    'transition_type': 'immediate',  # or 'timed', 'stochastic', 'continuous'
    'time': float,
    # Type-specific fields:
    'immediate_mode': True,          # Immediate
    'elapsed_time': float,           # Timed
    'burst_size': int,               # Stochastic
    'rate': float,                   # Continuous
})
```

### `fire()` Return (Failure)

```python
(False, {
    'reason': 'error-description',
    'error_type': 'ValueError',  # Optional
    # Context fields
})
```

---

## Configuration Requirements

### Immediate
```python
transition.transition_type = 'immediate'
# No additional properties needed
```

### Timed
```python
transition.transition_type = 'timed'
transition.properties = {
    'earliest': 2.0,    # Required
    'latest': 5.0       # Required
}
```

### Stochastic
```python
transition.transition_type = 'stochastic'
transition.properties = {
    'rate': 2.5,        # Required (λ > 0)
    'max_burst': 8      # Optional (default: 8)
}
```

### Continuous
```python
transition.transition_type = 'continuous'
transition.properties = {
    'rate_function': '2.0 * P1',  # Required (string or callable)
    'max_rate': 10.0,             # Optional (default: inf)
    'min_rate': 0.0               # Optional (default: 0)
}
```

---

## Troubleshooting

### "Unknown or unimplemented transition type"
```python
# Check available types
from shypn.engine import get_available_types
print(get_available_types())
# ['immediate', 'timed', 'stochastic', 'continuous']

# Ensure transition has correct type
transition.transition_type = 'immediate'  # Must be one of the above
```

### "Use integrate_step for continuous"
```python
# Continuous transitions use integrate_step(), not fire()
if isinstance(behavior, ContinuousBehavior):
    behavior.integrate_step(dt, input_arcs, output_arcs)
else:
    behavior.fire(input_arcs, output_arcs)
```

### Timed transition never fires
```python
# Ensure enablement time is set
behavior.set_enablement_time(current_time)

# Check timing info
timing = behavior.get_timing_info()
print(f"Elapsed: {timing['elapsed']}")
print(f"Window: [{behavior.earliest}, {behavior.latest}]")
print(f"In window: {timing['in_window']}")
```

### Stochastic transition not scheduled
```python
# Ensure enablement time is set (samples delay + burst)
behavior.set_enablement_time(current_time)

# Check schedule
fire_time = behavior.get_scheduled_fire_time()
if fire_time is None:
    print("Not scheduled! Call set_enablement_time() first")
else:
    print(f"Scheduled for: {fire_time}")
```

---

## Testing Checklist

### Unit Test Each Behavior
```python
# Test enablement
assert behavior.can_fire()[0] == expected

# Test firing
success, details = behavior.fire(arcs_in, arcs_out)
assert success == expected_success
assert details['consumed'] == expected_consumed

# Test type-specific features
# - Timed: test timing windows, urgency
# - Stochastic: test delay sampling, burst
# - Continuous: test integration, rate evaluation
```

### Integration Test
```python
# Create full model with places, arcs, transitions
model = create_test_model()

# Test each transition type
for transition in model.transitions:
    behavior = create_behavior(transition, model)
    # Exercise behavior...
```

---

## Performance Tips

### 1. Reuse Behavior Instances
```python
# Don't create new behavior every time
# SLOW:
for step in range(1000):
    behavior = create_behavior(transition, model)  # ❌
    behavior.fire(...)

# FAST:
behavior = create_behavior(transition, model)  # ✅
for step in range(1000):
    behavior.fire(...)
```

### 2. Cache Arc Lists
```python
# Avoid repeated arc fetching
input_arcs = behavior.get_input_arcs()   # Cache
output_arcs = behavior.get_output_arcs()

for step in range(1000):
    behavior.fire(input_arcs, output_arcs)  # Use cached
```

### 3. Batch Continuous Integration
```python
# Use larger time steps when possible
# SLOW: dt = 0.001 (1000 steps per second)
# FAST: dt = 0.01  (100 steps per second)

# Adjust based on accuracy requirements
```

---

## What's Next?

### For Users
- **Wait for Phase 7-9**: Integration, testing, documentation
- **Current limitation**: No connection to simulation engine yet
- **Try it out**: Can test individual behaviors with mock objects

### For Developers
- **Phase 7 (Integration)**: Connect to model classes, build scheduler
- **Phase 8 (Testing)**: Write unit tests, integration tests
- **Phase 9 (Documentation)**: API docs, user guide, migration guide

---

## Files to Read

1. **Start here**: `TRANSITION_ENGINE_IMPLEMENTATION_COMPLETE.md` - Full report
2. **Architecture**: `TRANSITION_ENGINE_VISUAL.md` - Diagrams
3. **Quick ref**: `TRANSITION_TYPES_QUICK_REF.md` - Type comparison
4. **Planning**: `TRANSITION_ENGINE_PLAN.md` - Original plan
5. **This file**: Quick start guide

---

## Questions?

**Q: Which behavior should I use?**  
A: Use the factory: `create_behavior(transition, model)` - it chooses automatically based on `transition.transition_type`.

**Q: Can I add custom behavior types?**  
A: Yes! Subclass `TransitionBehavior`, implement the 3 abstract methods, add to factory's type_map.

**Q: Why separate `fire()` and `integrate_step()`?**  
A: Continuous transitions need different semantics (flow over time vs. discrete jumps). Both satisfy the abstract interface.

**Q: How do I test this?**  
A: Wait for Phase 8 (testing), or create mock Place/Arc/Transition objects for isolated testing.

**Q: Is this production-ready?**  
A: Not yet - needs Phase 7-9 (integration, testing, documentation) before production use.

---

**Quick Start Guide - End**
