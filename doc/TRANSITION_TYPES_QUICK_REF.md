# Transition Types Quick Reference

## Type Comparison Matrix

| Aspect | Immediate | Timed (TPN) | Stochastic (FSPN) | Continuous (SHPN) |
|--------|-----------|-------------|-------------------|-------------------|
| **Time Delay** | Zero | [earliest, latest] | Exponential λ | dt integration |
| **Token Mode** | Discrete | Discrete | Burst (1x-8x) | Continuous flow |
| **Firing Unit** | arc_weight | arc_weight | arc_weight × N | dm/dt = R(m,t) |
| **Enablement** | Standard | Standard + timing | Standard | Standard + rate>0 |
| **Math Model** | Boolean logic | TPN intervals | Exponential dist. | ODE integration |
| **Complexity** | Simple | Medium | Medium-High | High |
| **Implementation** | ~60 lines | ~100 lines | ~120 lines | ~200 lines |

---

## Code Extraction Map

### Immediate Behavior
**Source**: `legacy/shypnpy/core/petri.py:1908-1970` (62 lines)

**Key Logic:**
```python
# Check tokens
for arc in input_arcs:
    if source_place.tokens < arc.weight:
        return False

# Consume
for arc in input_arcs:
    source_place.tokens -= arc.weight

# Produce
for arc in output_arcs:
    target_place.tokens += arc.weight
```

**Attributes Used:**
- `arc.weight`
- `place.tokens`

---

### Timed Behavior
**Source**: `legacy/shypnpy/core/petri.py:1971-2050+` (~80 lines)

**Key Logic:**
```python
# Update enablement tracking
trans.update_tpn_enablement_status(is_enabled, current_time)

# Check timing window
can_fire = (enablement_time + earliest <= current_time <= 
            enablement_time + latest)

# Fire same as immediate
consume_and_produce()
```

**Attributes Used:**
- `transition.earliest_time`
- `transition.latest_time`
- `transition.enablement_time`
- `transition.timed_enabled`

---

### Stochastic Behavior
**Source**: `legacy/shypnpy/core/petri.py:1562-1690` (~128 lines)

**Key Logic:**
```python
# Sample holding time
holding_time = -log(1 - uniform()) / rate_parameter

# Calculate burst size from holding time
if holding_time <= 0.2: burst = 1
elif holding_time <= 0.5: burst = random.choice([1,2])
elif holding_time <= 1.0: burst = random.choice([2,3,4])
# ... etc

# Fire in bursts
for i in range(burst_size):
    consume_arc_weight()
    produce_arc_weight()
```

**Attributes Used:**
- `transition.rate_parameter` (λ)
- `transition.stochastic_enabled`

---

### Continuous Behavior
**Source**: `legacy/shypnpy/core/petri.py:1691-1900` (~210 lines)

**Key Logic:**
```python
# Setup safe eval environment
eval_context = {
    'math': math, 'np': np,
    't': current_time,
    'P1': place1.tokens,
    'P2': place2.tokens,
    # ...
}

# RK4 integration
k1 = rate * dt
k2 = evaluate_rate(t + dt/2) * dt
k3 = evaluate_rate(t + dt/2) * dt
k4 = evaluate_rate(t + dt) * dt
delta = (k1 + 2*k2 + 2*k3 + k4) / 6

# Update tokens
for place in places:
    place.tokens += delta * proportion
```

**Attributes Used:**
- `transition.rate_function` (str: "1.0", "P1*0.5", etc.)
- `transition.time_step` (dt)
- `transition.max_flow_time`
- `transition.continuous_enabled`

---

## Class Method Signatures

### Base Class: TransitionBehavior
```python
__init__(transition, model)
can_fire() -> (bool, str)
fire(input_arcs, output_arcs) -> (bool, dict)
get_type_name() -> str
is_enabled() -> bool
get_input_arcs() -> List[Arc]
get_output_arcs() -> List[Arc]
```

### ImmediateBehavior
```python
can_fire() -> (bool, str)
    # Check sufficient tokens
    
fire(input_arcs, output_arcs) -> (bool, dict)
    # Consume arc_weight, produce arc_weight
    
get_type_name() -> str
    # Return "Immediate"
```

### TimedBehavior
```python
can_fire() -> (bool, str)
    # Check enabled + timing window
    
fire(input_arcs, output_arcs) -> (bool, dict)
    # Update enablement, fire discrete
    
is_within_timing_window() -> (bool, bool, str)
    # Check [earliest, latest]
    
update_enablement_tracking()
    # Track when enabled/disabled
    
get_type_name() -> str
    # Return "Timed (TPN)"
```

### StochasticBehavior
```python
can_fire() -> (bool, str)
    # Check if any tokens available
    
fire(input_arcs, output_arcs) -> (bool, dict)
    # Execute burst firing
    
sample_holding_time() -> float
    # Exponential distribution
    
calculate_burst_size(holding_time) -> int
    # Convert time to burst multiplier
    
get_max_burst_size(input_arcs) -> int
    # Check available tokens
    
get_type_name() -> str
    # Return "Stochastic (FSPN)"
```

### ContinuousBehavior
```python
can_fire() -> (bool, str)
    # Check enabled + rate > 0
    
fire(input_arcs, output_arcs) -> (bool, dict)
    # Execute RK4 integration
    
evaluate_rate_function(marking, time) -> float
    # Safe eval of R(m,t)
    
rk4_step(marking, time, dt) -> float
    # Single RK4 integration step
    
build_eval_context(marking, time) -> dict
    # Create P1, P2, ..., t variables
    
get_type_name() -> str
    # Return "Continuous (SHPN)"
```

---

## Factory Usage

```python
from shypn.engine import create_behavior

# Automatic type detection
behavior = create_behavior(transition, model)

# Or manual instantiation
from shypn.engine import ImmediateBehavior
behavior = ImmediateBehavior(transition, model)
```

---

## Return Value Formats

### can_fire() Returns
```python
(True, "enabled")                    # Can fire
(False, "insufficient-tokens")       # Cannot fire
(False, "not-in-timing-window")     # Timed only
(False, "rate-zero")                # Continuous only
```

### fire() Returns
```python
# Success
(True, {
    'consumed': {place_id: amount, ...},
    'produced': {place_id: amount, ...},
    'type_specific_key': value,
    ...
})

# Failure
(False, {
    'reason': 'error-description',
    'details': '...'
})
```

#### Type-Specific Details

**Immediate:**
```python
{
    'consumed': {...},
    'produced': {...},
    'immediate_mode': True,
    'discrete_firing': True
}
```

**Timed:**
```python
{
    'consumed': {...},
    'produced': {...},
    'tpn_mode': True,
    'fired_at_time': 5.2,
    'was_urgent': False
}
```

**Stochastic:**
```python
{
    'consumed': {...},
    'produced': {...},
    'burst_size': 3,
    'holding_time': 1.5,
    'rate_parameter': 2.0
}
```

**Continuous:**
```python
{
    'consumed': {...},
    'produced': {...},
    'flow_duration': 2.5,
    'integration_steps': 25,
    'final_rate': 0.8
}
```

---

## Testing Checklist

### Per-Type Tests
- ✅ Fire when enabled
- ✅ Don't fire when disabled
- ✅ Correct token consumption
- ✅ Correct token production
- ✅ Handle edge cases (zero tokens, etc.)
- ✅ Return correct status/details

### Type-Specific Tests

**Immediate:**
- ✅ Zero time delay
- ✅ Exact arc_weight transfer

**Timed:**
- ✅ Respect earliest time
- ✅ Respect latest time (urgency)
- ✅ Enablement tracking
- ✅ Timing window violations

**Stochastic:**
- ✅ Exponential distribution
- ✅ Burst size calculation
- ✅ Maximum burst constraints
- ✅ Token balance (consumed = produced × burst)

**Continuous:**
- ✅ Rate function evaluation
- ✅ RK4 accuracy
- ✅ Safe math environment
- ✅ Integration termination
- ✅ Variable mapping (P1, P2, t)

---

## Performance Notes

| Type | Complexity | Typical Time |
|------|-----------|--------------|
| Immediate | O(n_arcs) | < 1ms |
| Timed | O(n_arcs) | < 1ms |
| Stochastic | O(n_arcs × burst) | 1-5ms |
| Continuous | O(n_arcs × steps) | 5-50ms |

---

## Common Pitfalls

1. **Forgetting type-specific flags**
   - Check `timed_enabled`, `stochastic_enabled`, `continuous_enabled`

2. **Not updating enablement tracking**
   - Timed transitions need enablement time updates

3. **Unsafe rate function evaluation**
   - Always use restricted eval environment

4. **Burst size overflow**
   - Check available tokens before bursting

5. **RK4 instability**
   - Validate time step size (dt too large → unstable)

---

**Last Updated**: October 3, 2025
