# Time Computation During Simulation - Analysis & Test Plan

## Executive Summary

This document provides a comprehensive analysis of how time is computed and advanced during Petri net simulation in the ShyPN system, followed by a complete test plan to verify correct behavior across all transition types and edge cases.

**Date:** October 8, 2025  
**Scope:** Simulation time management, discrete/continuous hybrid execution, event scheduling  
**Components:** SimulationController, TransitionBehaviors, SimulationSettings, Legacy Engine

---

## 1. Time Computation Architecture

### 1.1 Time Representation

**Two Time Systems:**

1. **Logical Time** (`logical_time` in legacy, `time` in controller)
   - Discrete integer steps in legacy system
   - Continuous float in new architecture
   - Represents simulation clock advance
   - Independent of wall-clock time

2. **Wall-Clock Time** (real elapsed time)
   - Used for UI updates and rate limiting
   - Not directly used in simulation logic
   - Managed by GLib.timeout_add for continuous execution

### 1.2 Time Sources

| Component | Time Variable | Type | Purpose |
|-----------|--------------|------|---------|
| **SimulationController** | `self.time` | float | Master simulation clock |
| **ModelAdapter** | `logical_time` property | float | Provides time to behaviors |
| **TransitionBehavior** | `_get_current_time()` | float | Access model's logical_time |
| **SimulationSettings** | duration, dt | float | Time limits and step size |
| **Legacy Engine** | `model.logical_time` | int/float | Legacy time tracking |

### 1.3 Time Flow Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Simulation Step                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Current Time: t = self.time                          │
│                                                          │
│ 2. Update Enablement States (at time t)                 │
│    ├─ Check input tokens                                │
│    ├─ Record enablement_time if newly enabled           │
│    └─ Clear if disabled                                  │
│                                                          │
│ 3. EXHAUST Immediate Transitions (zero time)            │
│    └─ Fire until none enabled (max 1000 iterations)     │
│                                                          │
│ 4. Identify Continuous Transitions (for integration)    │
│    └─ Snapshot: which are enabled at time t             │
│                                                          │
│ 5. Fire ONE Discrete Transition (timed/stochastic)      │
│    ├─ Check timing constraints                          │
│    ├─ Select using conflict policy                      │
│    └─ Update tokens (discrete change)                   │
│                                                          │
│ 6. Integrate ALL Continuous Transitions                 │
│    ├─ Use dt (time_step)                                │
│    ├─ Apply rate functions                              │
│    └─ Update tokens (smooth change)                     │
│                                                          │
│ 7. Advance Time: t = t + dt                            │
│    └─ self.time += time_step                            │
│                                                          │
│ 8. Notify Listeners (UI updates)                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Time Advancement Mechanisms

### 2.1 Discrete Time Steps (Step-by-Step)

**Source:** `SimulationController.step(time_step)`

```python
def step(self, time_step: float = None) -> bool:
    # 1. Use effective dt if not specified
    if time_step is None:
        time_step = self.get_effective_dt()  # From settings
    
    # ... execute transitions ...
    
    # 2. Advance time
    self.time += time_step
    
    # 3. Notify listeners
    self._notify_step_listeners()
```

**Key Points:**
- **Fixed time step** (default or user-specified)
- **Uniform advance** regardless of transition firing
- **Always advances** even if no transitions fire
- **Setting-based:** dt computed from duration/steps or manual

**Time Step Calculation:**
```python
# Auto mode: dt = duration / target_steps
dt = duration_seconds / 1000  # Default: 1000 steps

# Manual mode: dt = user_specified_value
dt = 0.01  # Example: 10ms steps
```

### 2.2 Continuous Integration

**Source:** `ContinuousBehavior.integrate_step(dt, input_arcs, output_arcs)`

```python
def integrate_step(self, dt: float, input_arcs, output_arcs):
    current_time = self._get_current_time()  # Get t
    
    # Evaluate rate function at current time
    rate = self.rate_function(places_dict, current_time)
    
    # Integrate over dt:
    # Δtokens = rate * dt
    
    for arc in output_arcs:
        place = self._get_place(arc.target_id)
        weight = self._get_threshold(arc)
        
        # Apply continuous change
        delta = rate * weight * dt
        place.tokens += delta
```

**Integration Methods:**
- **Forward Euler** (current): `tokens_{t+dt} = tokens_t + rate * dt`
- **Accuracy:** First-order, suitable for small dt
- **Stability:** Depends on dt size relative to system dynamics

**Rate Function Evaluation:**
- Evaluated **at current time** (start of step)
- Uses **current place markings** (before discrete changes)
- Time `t` passed to custom functions: `rate_function(places, t)`

### 2.3 Event Scheduling (Timed Transitions)

**Source:** `TimedBehavior` + `unified_scheduler` (legacy)

**Timed Transition Timing:**

```python
# Enablement tracking
def set_enablement_time(self, time: float):
    """Called when transition becomes enabled."""
    self._enablement_time = time
    # Transition can fire in window: [t + earliest, t + latest]

# Can fire check
def can_fire(self):
    current_time = self._get_current_time()
    elapsed = current_time - self._enablement_time
    
    # Check timing window
    if elapsed < self.earliest:
        return (False, "too-early")
    if elapsed > self.latest:
        return (False, "too-late")
    
    return (True, "ready")
```

**Time Windows:**
```
Enablement     Earliest           Latest
    t             t+e               t+l
    |──────────────|─────────────────|
                   ^                 ^
              Can fire here      Last chance
```

**Event Scheduling (Legacy):**
```python
# unified_scheduler.advance_to_next_event()
# Jumps time forward to next scheduled event
new_time = min(all_scheduled_events)
model.logical_time = new_time
```

### 2.4 Stochastic Scheduling

**Source:** `StochasticBehavior`

**Exponential Distribution Sampling:**

```python
def schedule_next_firing(self):
    """Sample delay from exponential distribution."""
    import random
    
    # λ = rate parameter
    # Delay ~ Exp(λ)
    # Mean delay = 1/λ
    
    delay = random.expovariate(self.rate)
    self.scheduled_time = self._enablement_time + delay
```

**Firing Decision:**
```python
def can_fire(self):
    current_time = self._get_current_time()
    
    # Fire when scheduled time reached
    if current_time >= self.scheduled_time:
        return (True, "scheduled-time-reached")
    else:
        return (False, "waiting-for-scheduled-time")
```

---

## 3. Time-Critical Components

### 3.1 SimulationSettings

**Responsibilities:**
- Define simulation duration
- Calculate time step (dt)
- Track progress
- Completion detection

**Time Configuration:**

```python
class SimulationSettings:
    def __init__(self):
        self.duration_value = 10.0      # Simulation duration
        self.duration_unit = 'seconds'  # Time unit
        self.dt_mode = 'auto'           # 'auto' or 'manual'
        self.dt_value = 0.01            # Manual dt (if mode='manual')
        self.target_steps = 1000        # For auto mode
    
    def get_effective_dt(self) -> float:
        """Calculate time step."""
        duration_seconds = self._get_duration_seconds()
        
        if self.dt_mode == 'auto':
            # dt = duration / target_steps
            return duration_seconds / self.target_steps
        else:
            # Use manual value
            return self._convert_to_seconds(self.dt_value, self.dt_unit)
    
    def calculate_progress(self, current_time: float) -> float:
        """Progress as fraction [0.0, 1.0]."""
        duration = self._get_duration_seconds()
        return min(current_time / duration, 1.0) if duration > 0 else 0.0
    
    def is_complete(self, current_time: float) -> bool:
        """Check if duration reached."""
        duration = self._get_duration_seconds()
        return current_time >= duration
```

### 3.2 TransitionBehavior Time Access

**Base Class Method:**

```python
class TransitionBehavior:
    def _get_current_time(self) -> float:
        """Get current simulation time from model.
        
        Returns:
            float: Current logical time (0.0 if not set)
        """
        return getattr(self.model, 'logical_time', 0.0)
```

**Usage Across Behaviors:**

| Behavior Type | Time Usage | Purpose |
|---------------|------------|---------|
| **Immediate** | Read time for logging | Debug/trace information |
| **Timed** | `current_time - enablement_time` | Elapsed time check |
| **Stochastic** | `current_time >= scheduled_time` | Firing decision |
| **Continuous** | Passed to `rate_function(places, t)` | Time-dependent rates |

### 3.3 Enablement Time Tracking

**TransitionState Class:**

```python
class TransitionState:
    """Per-transition state for time-aware behaviors."""
    
    def __init__(self):
        self.enablement_time = None  # When became enabled (None if disabled)
        self.scheduled_time = None   # Scheduled firing time (stochastic only)
```

**State Management:**

```python
# In SimulationController._update_enablement_states():

for transition in self.model.transitions:
    behavior = self._get_behavior(transition)
    state = self._get_or_create_state(transition)
    
    # Check local enablement (input tokens)
    locally_enabled = self._is_locally_enabled(transition)
    
    if locally_enabled:
        # Just became enabled
        if state.enablement_time is None:
            state.enablement_time = self.time
            
            # Notify behavior
            if hasattr(behavior, 'set_enablement_time'):
                behavior.set_enablement_time(self.time)
    else:
        # Just became disabled
        if state.enablement_time is not None:
            state.enablement_time = None
            state.scheduled_time = None
            
            # Clear behavior state
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
```

---

## 4. Critical Time Scenarios

### 4.1 Zero-Time Firing (Immediate Transitions)

**Behavior:**
- Fire **immediately** when enabled
- **No time advance** during firing
- **Multiple firings** in single step (exhaust loop)

**Implementation:**
```python
# Phase 1: Exhaust immediate transitions
immediate_fired_total = 0
max_iterations = 1000

for iteration in range(max_iterations):
    immediate_transitions = [t for t in model.transitions 
                            if t.transition_type == 'immediate']
    enabled = [t for t in immediate_transitions 
               if self._is_transition_enabled(t)]
    
    if not enabled:
        break  # No more immediate transitions can fire
    
    # Select and fire one
    transition = self._select_transition(enabled)
    self._fire_transition(transition)
    immediate_fired_total += 1
    
    # Re-check enablement (tokens changed)
    self._update_enablement_states()

# Time has NOT advanced yet (still at t)
```

**Time Characteristics:**
- ✅ Multiple firings at **same time point**
- ✅ **Zero duration** per firing
- ❌ Risk: **Infinite loop** if improper model
- ✅ Safety: **Max iteration limit** (1000)

### 4.2 Fixed Delay (Timed Transitions)

**Timing Window:**
```
t = 10.0: Transition becomes enabled
    ├─ earliest = 2.0
    ├─ latest = 5.0
    └─ Window: [12.0, 15.0]

t = 12.0: Can fire (earliest passed)
t = 13.0: Can fire (within window)
t = 15.0: Can fire (last chance)
t = 15.1: Cannot fire (too late)
```

**Critical Timing Issues:**

**Issue 1: Missed Windows**
```python
# Scenario:
# - Window: [12.0, 15.0]
# - dt = 5.0 (large step)
# - Steps: 10.0 -> 15.0 -> 20.0

# Problem: Step jumps over entire window!
# Transition never fires because we skip from 10.0 to 15.0 to 20.0
```

**Issue 2: Window Boundary**
```python
# Scenario:
# - Window: [12.0, 15.0]
# - t = 15.0 exactly

# Question: Can fire at t=15.0?
# Answer: Yes (current implementation uses <=)

if elapsed <= self.latest:  # Inclusive
    return (True, "ready")
```

**Issue 3: Re-enablement**
```python
# Scenario:
# 1. T1 enabled at t=10.0 (window [12.0, 15.0])
# 2. T1 disabled at t=11.0 (tokens consumed)
# 3. T1 re-enabled at t=14.0
# 4. When can T1 fire now?

# Answer: New window from t=14.0!
# Window: [16.0, 19.0]
# NOT the original [12.0, 15.0]
```

### 4.3 Hybrid Execution (Discrete + Continuous)

**Critical Ordering:**

```python
def step(self, time_step):
    # TIME = t (start of step)
    
    # 1. EXHAUST immediate (at time t)
    fire_immediate_transitions()
    
    # 2. SNAPSHOT continuous (which are enabled at time t)
    continuous_to_integrate = identify_enabled_continuous()
    
    # 3. FIRE ONE discrete (at time t)
    fire_discrete_transition()
    
    # 4. INTEGRATE continuous (over [t, t+dt])
    for cont in continuous_to_integrate:
        integrate(cont, dt)  # Uses state from BEFORE discrete firing
    
    # 5. ADVANCE time
    self.time += time_step
    # TIME = t + dt (end of step)
```

**Critical Design Decisions:**

**Q: Why snapshot continuous BEFORE discrete firing?**
```
A: To avoid order-dependence artifacts.

Example WITHOUT snapshot:
- Discrete transition fires → changes tokens
- Continuous checked → sees CHANGED tokens
- Result: Continuous integration depends on which discrete fired!

Example WITH snapshot:
- Continuous checked → sees ORIGINAL tokens
- Discrete transition fires → changes tokens
- Continuous integrates → uses ORIGINAL state
- Result: Consistent, order-independent
```

**Q: Should continuous see discrete changes immediately?**
```
Current answer: NO (snapshot before discrete)
Alternative: YES (check after discrete)

Trade-offs:
- Current: More predictable, order-independent
- Alternative: More "reactive" but order-dependent

Decision: Keep snapshot approach for consistency.
```

### 4.4 Event Scheduling vs. Fixed Steps

**Two Approaches:**

**1. Fixed Time Steps (Current)**
```python
# Always advance by dt
t = 0.0
while t < duration:
    step(dt)
    t += dt  # Fixed increment

# Advantages:
# + Simple, predictable
# + Works for continuous transitions
# + Uniform sampling for data collection

# Disadvantages:
# - May miss timed windows
# - Inefficient for sparse events
# - dt must be small enough
```

**2. Event-Driven (Next-Event Scheduling)**
```python
# Jump to next scheduled event
t = 0.0
while t < duration:
    next_event = min(all_scheduled_times)
    
    if next_event < duration:
        t = next_event
        fire_scheduled_transitions(t)
    else:
        break

# Advantages:
# + Never misses events
# + Efficient for sparse models
# + Exact timing

# Disadvantages:
# - Complex implementation
# - Harder with continuous transitions
# - Variable time steps
```

**Hybrid Approach (Recommended for Future):**
```python
# Combine both methods
def step():
    # 1. Check if any events before next regular step
    next_event = scheduler.get_next_event_time()
    next_regular = self.time + dt
    
    if next_event is not None and next_event < next_regular:
        # Jump to event
        time_step = next_event - self.time
        self.time = next_event
        fire_scheduled_transitions()
    else:
        # Regular fixed step
        time_step = dt
        self.time += dt
    
    # 2. Integrate continuous with actual time_step
    integrate_continuous(time_step)
```

---

## 5. Edge Cases and Corner Cases

### 5.1 Zero Duration Simulation

```python
# Settings:
duration = 0.0
dt = 0.01

# Behavior:
is_complete(0.0) -> True  # Immediately complete
step() returns False      # No execution
```

**Test:** Verify no time advance, no errors

### 5.2 Very Small dt

```python
# Settings:
duration = 10.0
dt = 1e-10  # Extremely small

# Issues:
# - Millions of steps required
# - Floating-point precision loss
# - Performance degradation
# - Cumulative rounding errors
```

**Test:** Verify warning, performance limits

### 5.3 Very Large dt

```python
# Settings:
duration = 10.0
dt = 100.0  # Larger than duration

# Issues:
# - Single step exceeds duration
# - Timing windows missed
# - Overshoot completion
```

**Test:** Verify correct handling, no overshoot

### 5.4 Exact Window Boundaries

```python
# Timed transition:
earliest = 5.0
latest = 10.0
enablement_time = 0.0

# Test cases:
t = 4.999999 -> can_fire? (should be False)
t = 5.0      -> can_fire? (should be True - inclusive)
t = 10.0     -> can_fire? (should be True - inclusive)
t = 10.000001 -> can_fire? (should be False)
```

**Test:** Boundary inclusivity/exclusivity

### 5.5 Floating-Point Precision

```python
# Accumulation error:
t = 0.0
dt = 0.1

for i in range(100):
    t += dt

# Expected: t = 10.0
# Actual: t = 9.999999999999998 (floating-point error)

# Impact on timing checks:
if t >= 10.0:  # May fail due to precision!
    ...
```

**Solution:**
```python
# Use epsilon comparison
EPSILON = 1e-9

if abs(t - target) < EPSILON:  # Close enough
    ...

# Or for completion:
if t >= target - EPSILON:
    ...
```

### 5.6 Re-enablement Timing

```python
# Scenario:
t=0: Transition T enabled (window [5, 10])
t=3: T disabled (consumed by another transition)
t=7: T re-enabled

# Question: What's the new window?
# Answer: [7+5=12, 7+10=17] (resets from re-enablement time!)

# Implementation check:
def set_enablement_time(self, time):
    self._enablement_time = time  # Records NEW enablement
    # Window is relative to THIS time
```

**Test:** Verify window resets on re-enablement

### 5.7 Simultaneous Events

```python
# Two timed transitions:
T1: enabled at t=0, earliest=5, latest=10
T2: enabled at t=0, earliest=5, latest=10

# At t=5, both can fire
# Question: Which fires?
# Answer: Conflict resolution policy

# Policies:
# - Random: random.choice([T1, T2])
# - Priority: max(priority) among enabled
# - Round-robin: cycle through in order
# - FCFS: first enabled fires first (needs queue)
```

**Test:** Verify policy applied correctly

### 5.8 Continuous Rate = 0

```python
# Continuous transition:
rate_function = lambda places, t: 0.0

# Integration:
delta = rate * weight * dt = 0.0 * 1.0 * 0.01 = 0.0

# Behavior: No token change
# Question: Is transition "fired" or not?
# Current: Reported as "active" but no effect
```

**Test:** Verify zero-rate handling

### 5.9 Negative Time Step

```python
# Attempt:
step(time_step=-0.01)

# Expected: Error or clamp to 0
# Current: No explicit check!

# Impact:
self.time += (-0.01)  # Time goes backwards!
```

**Test:** Validate time_step >= 0

### 5.10 Infinite Loop Detection

```python
# Immediate transitions:
P1 --(T1)--> P2
P2 --(T2)--> P1

# Both immediate, sufficient tokens
# Result: T1 fires, T2 fires, T1 fires, ... (infinite)

# Protection:
max_immediate_iterations = 1000
if iteration >= max_iterations:
    # Log warning, break loop
```

**Test:** Verify loop detection and limit

---

## 6. Test Plan

### 6.1 Test Categories

| Category | Priority | Coverage |
|----------|----------|----------|
| **Basic Time Advance** | HIGH | Fixed steps, dt calculation |
| **Transition Timing** | HIGH | All 4 types, firing windows |
| **Hybrid Execution** | HIGH | Discrete + continuous interaction |
| **Edge Cases** | MEDIUM | Boundaries, precision, errors |
| **Performance** | MEDIUM | Large dt, many steps, efficiency |
| **Conflict Resolution** | MEDIUM | Multiple enabled, policies |
| **Event Scheduling** | LOW | Next-event, exact timing |

### 6.2 Test Structure

```python
# Test file organization:
tests/
    test_time_basic.py           # Basic time advance
    test_time_immediate.py       # Zero-time firing
    test_time_timed.py          # Timing windows
    test_time_stochastic.py     # Exponential scheduling
    test_time_continuous.py     # Integration timing
    test_time_hybrid.py         # Mixed transition types
    test_time_edge_cases.py     # Corner cases
    test_time_precision.py      # Floating-point issues
    test_time_settings.py       # SimulationSettings
    test_time_conflict.py       # Simultaneous events
```

### 6.3 Core Test Cases

#### Test Suite 1: Basic Time Advance

```python
def test_time_starts_at_zero():
    """Verify simulation starts at t=0."""
    controller = SimulationController(model)
    assert controller.time == 0.0

def test_time_advances_by_dt():
    """Verify time advances by dt on each step."""
    controller = SimulationController(model)
    controller.settings.dt_value = 0.5
    controller.settings.dt_mode = 'manual'
    
    controller.step()
    assert controller.time == 0.5
    
    controller.step()
    assert controller.time == 1.0

def test_time_advances_even_if_no_firing():
    """Time advances even when no transitions fire."""
    # Model with no enabled transitions
    controller = SimulationController(empty_model)
    controller.step()
    assert controller.time > 0.0

def test_auto_dt_calculation():
    """Auto mode calculates dt from duration and steps."""
    controller = SimulationController(model)
    controller.settings.duration_value = 10.0
    controller.settings.duration_unit = 'seconds'
    controller.settings.dt_mode = 'auto'
    controller.settings.target_steps = 1000
    
    dt = controller.get_effective_dt()
    assert dt == 10.0 / 1000
    assert dt == 0.01

def test_manual_dt_respected():
    """Manual dt overrides auto calculation."""
    controller = SimulationController(model)
    controller.settings.dt_mode = 'manual'
    controller.settings.dt_value = 0.123
    
    dt = controller.get_effective_dt()
    assert dt == 0.123

def test_simulation_completes_at_duration():
    """Simulation stops when time reaches duration."""
    controller = SimulationController(model)
    controller.settings.duration_value = 1.0
    controller.settings.dt_value = 0.1
    controller.settings.dt_mode = 'manual'
    
    # Run 10 steps (1.0 seconds)
    for _ in range(10):
        result = controller.step()
    
    # 11th step should return False (complete)
    result = controller.step()
    assert result == False
    assert controller.is_simulation_complete()
```

#### Test Suite 2: Immediate Transitions (Zero-Time)

```python
def test_immediate_fires_in_zero_time():
    """Immediate transition fires without time advance."""
    # P1(5) --T1(immediate)--> P2(0)
    model = create_simple_immediate_model()
    controller = SimulationController(model)
    
    # Before step
    t_before = controller.time
    
    # Execute step
    controller.step()
    
    # After step
    t_after = controller.time
    
    # Time advanced by dt (not zero!)
    assert t_after > t_before
    
    # But transition fired at t_before time
    # (firing happens before time advance)
    assert model.places[1].tokens == 4  # P1 decreased
    assert model.places[2].tokens == 1  # P2 increased

def test_multiple_immediate_fire_same_step():
    """Multiple immediate transitions fire in one step."""
    # P1 --T1(imm)--> P2 --T2(imm)--> P3
    model = create_chain_immediate_model()
    controller = SimulationController(model)
    
    # Initial: P1=1, P2=0, P3=0
    # After step: P1=0, P2=0, P3=1 (both fired)
    
    controller.step()
    
    assert model.places[1].tokens == 0
    assert model.places[2].tokens == 0
    assert model.places[3].tokens == 1

def test_immediate_exhaust_loop():
    """Immediate transitions exhaust until none enabled."""
    # Cycle: P1 <--> P2 with immediate transitions
    # Should hit max iteration limit
    model = create_immediate_cycle()
    controller = SimulationController(model)
    
    # Should not hang (max 1000 iterations)
    controller.step()
    
    # Check it stopped (even if still enabled)
    assert True  # Didn't hang

def test_immediate_fires_before_discrete():
    """Immediate transitions fire before discrete."""
    # P1 --T1(immediate)--> P2 --T2(timed)--> P3
    model = create_immediate_then_timed()
    controller = SimulationController(model)
    
    # Step 1: T1 fires (immediate), T2 becomes enabled
    controller.step()
    assert model.places[2].tokens == 1  # P2 has token from T1
    assert model.places[3].tokens == 0  # T2 hasn't fired yet
    
    # Step 2: T2 can fire (if timing allows)
    # ...continue test based on timing...
```

#### Test Suite 3: Timed Transitions

```python
def test_timed_window_earliest():
    """Timed transition cannot fire before earliest."""
    # T1: earliest=5.0, latest=10.0
    model = create_timed_model(earliest=5.0, latest=10.0)
    controller = SimulationController(model)
    controller.settings.dt_value = 1.0
    controller.settings.dt_mode = 'manual'
    
    # Enable transition at t=0
    # Advance to t=4.99 (before earliest)
    for _ in range(5):  # t=0 -> 4.0
        controller.step()
    
    controller.step()  # t=5.0
    # Now can fire (earliest reached)
    # (Actual firing depends on conflict resolution)

def test_timed_window_latest():
    """Timed transition cannot fire after latest."""
    model = create_timed_model(earliest=5.0, latest=10.0)
    controller = SimulationController(model)
    controller.settings.dt_value = 1.0
    
    # Advance past latest
    for _ in range(11):  # t=0 -> 11.0
        controller.step()
    
    # Transition missed its window
    behavior = controller._get_behavior(model.transitions[0])
    can_fire, reason = behavior.can_fire()
    
    assert not can_fire
    assert "too-late" in reason

def test_timed_window_boundaries_inclusive():
    """Window boundaries are inclusive."""
    model = create_timed_model(earliest=5.0, latest=10.0)
    controller = SimulationController(model)
    
    # Set time exactly to earliest
    controller.time = 5.0
    behavior = controller._get_behavior(model.transitions[0])
    behavior.set_enablement_time(0.0)
    
    can_fire, _ = behavior.can_fire()
    assert can_fire  # Exactly at earliest is OK
    
    # Set time exactly to latest
    controller.time = 10.0
    can_fire, _ = behavior.can_fire()
    assert can_fire  # Exactly at latest is OK

def test_timed_reenablement_resets_window():
    """Re-enabling resets timing window."""
    model = create_timed_model(earliest=5.0, latest=10.0)
    controller = SimulationController(model)
    
    # First enablement at t=0
    behavior = controller._get_behavior(model.transitions[0])
    behavior.set_enablement_time(0.0)
    
    # Window: [5.0, 10.0]
    controller.time = 7.0
    can_fire_1, _ = behavior.can_fire()
    assert can_fire_1  # Within first window
    
    # Disable and re-enable at t=7.0
    behavior.clear_enablement()
    behavior.set_enablement_time(7.0)
    
    # New window: [12.0, 17.0]
    can_fire_2, _ = behavior.can_fire()
    assert not can_fire_2  # Too early for new window
    
    # Advance to new window
    controller.time = 13.0
    can_fire_3, _ = behavior.can_fire()
    assert can_fire_3  # Within new window

def test_timed_large_dt_misses_window():
    """Large dt can cause window to be missed."""
    model = create_timed_model(earliest=5.0, latest=10.0)
    controller = SimulationController(model)
    controller.settings.dt_value = 20.0  # Large step
    
    # Enabled at t=0, window [5.0, 10.0]
    behavior = controller._get_behavior(model.transitions[0])
    behavior.set_enablement_time(0.0)
    
    # Step: t=0 -> t=20 (jumps over window!)
    controller.step()
    
    # Check transition missed window
    can_fire, reason = behavior.can_fire()
    assert not can_fire
    assert "too-late" in reason
```

#### Test Suite 4: Continuous Transitions

```python
def test_continuous_integration_linear():
    """Continuous transition integrates linearly."""
    # P1 --T1(continuous, rate=2.0)--> P2
    model = create_continuous_model(rate=2.0)
    controller = SimulationController(model)
    controller.settings.dt_value = 0.1
    
    # Initial: P1=10, P2=0
    # Rate = 2.0 tokens/second
    # dt = 0.1 seconds
    # Expected Δ = 2.0 * 0.1 = 0.2 tokens
    
    initial_p1 = model.places[1].tokens
    initial_p2 = model.places[2].tokens
    
    controller.step()
    
    # Verify integration
    assert abs(model.places[1].tokens - (initial_p1 - 0.2)) < 1e-6
    assert abs(model.places[2].tokens - (initial_p2 + 0.2)) < 1e-6

def test_continuous_time_dependent_rate():
    """Rate function depends on time."""
    # rate = 2.0 * t
    def rate_func(places, t):
        return 2.0 * t
    
    model = create_continuous_model_with_func(rate_func)
    controller = SimulationController(model)
    controller.settings.dt_value = 0.1
    
    # t=0: rate = 0, Δ = 0
    controller.step()
    assert model.places[2].tokens == 0.0  # No change
    
    # t=0.1: rate = 0.2, Δ = 0.2 * 0.1 = 0.02
    controller.step()
    assert abs(model.places[2].tokens - 0.02) < 1e-6

def test_continuous_multiple_outputs():
    """Continuous with multiple outputs."""
    # P1 --T1--> P2 (weight=1)
    #        \-> P3 (weight=2)
    # Rate = 1.0, dt = 0.1
    # P2 += 1.0 * 1 * 0.1 = 0.1
    # P3 += 1.0 * 2 * 0.1 = 0.2
    
    model = create_continuous_multi_output()
    controller = SimulationController(model)
    controller.settings.dt_value = 0.1
    
    controller.step()
    
    assert abs(model.places[2].tokens - 0.1) < 1e-6
    assert abs(model.places[3].tokens - 0.2) < 1e-6

def test_continuous_snapshot_before_discrete():
    """Continuous uses state before discrete firing."""
    # Setup: P1 --T1(discrete)--> P2 --T2(continuous)--> P3
    # T2 rate depends on P2
    model = create_hybrid_model()
    controller = SimulationController(model)
    
    # Initial: P1=1, P2=0, P3=0
    # Step:
    #   1. Snapshot continuous (T2 not enabled, P2=0)
    #   2. Fire T1 (discrete): P1=0, P2=1
    #   3. Integrate T2: uses snapshot (P2=0), so no flow
    #   4. Result: P2=1, P3=0 (T2 didn't see P2's new token)
    
    controller.step()
    
    assert model.places[2].tokens == 1
    assert model.places[3].tokens == 0  # Didn't integrate
```

#### Test Suite 5: Hybrid Execution

```python
def test_hybrid_immediate_then_timed():
    """Immediate fires, then timed waits."""
    model = create_immediate_timed_chain()
    controller = SimulationController(model)
    
    # Chain: P0(1) --T1(imm)--> P1 --T2(timed,5s)--> P2
    
    # Step 1: T1 fires (immediate)
    controller.step()
    assert model.places[1].tokens == 1
    assert model.places[2].tokens == 0
    
    # Steps 2-5: Wait for T2 window
    for _ in range(5):
        controller.step()
    
    # Step 6: T2 can fire
    # (Check if it actually fired)
    assert model.places[2].tokens > 0

def test_hybrid_discrete_doesnt_affect_continuous():
    """Discrete firing doesn't immediately affect continuous."""
    # Already tested in continuous suite
    pass

def test_hybrid_all_four_types():
    """Model with all 4 transition types."""
    model = create_full_hybrid_model()
    controller = SimulationController(model)
    
    # Verify all types can coexist
    controller.step()
    # (More specific assertions based on model)
```

#### Test Suite 6: Edge Cases

```python
def test_zero_duration():
    """Zero duration simulation."""
    controller = SimulationController(model)
    controller.settings.duration_value = 0.0
    
    assert controller.is_simulation_complete()
    result = controller.step()
    assert result == False  # Already complete

def test_very_small_dt():
    """Very small dt."""
    controller = SimulationController(model)
    controller.settings.dt_value = 1e-10
    controller.settings.dt_mode = 'manual'
    
    dt = controller.get_effective_dt()
    assert dt == 1e-10
    
    # Should warn about performance
    # (Check for warning log)

def test_very_large_dt():
    """dt larger than duration."""
    controller = SimulationController(model)
    controller.settings.duration_value = 10.0
    controller.settings.dt_value = 100.0
    
    controller.step()
    
    # Should not overshoot
    assert controller.time <= controller.settings._get_duration_seconds()

def test_negative_dt_rejected():
    """Negative dt should be rejected."""
    controller = SimulationController(model)
    
    with pytest.raises(ValueError):
        controller.step(time_step=-0.01)

def test_floating_point_precision():
    """Handle floating-point accumulation errors."""
    controller = SimulationController(model)
    controller.settings.dt_value = 0.1
    controller.settings.duration_value = 1.0
    
    # 10 steps should reach exactly 1.0
    for _ in range(10):
        controller.step()
    
    # Check with epsilon
    assert abs(controller.time - 1.0) < 1e-9

def test_simultaneous_timed_conflict():
    """Two timed transitions ready at same time."""
    model = create_two_timed_model()
    controller = SimulationController(model)
    
    # Both enabled at t=0, both windows [5,10]
    # At t=5, both can fire
    controller.time = 5.0
    
    # Only ONE should fire per step
    controller.step()
    
    # Count how many fired
    # (Depends on conflict policy)
```

#### Test Suite 7: Stochastic Timing

```python
def test_stochastic_exponential_delay():
    """Stochastic samples from exponential distribution."""
    import random
    random.seed(42)  # Reproducible
    
    model = create_stochastic_model(rate=0.5)
    controller = SimulationController(model)
    
    behavior = controller._get_behavior(model.transitions[0])
    behavior.set_enablement_time(0.0)
    
    # Get scheduled time
    scheduled = behavior.scheduled_time
    
    # Should be > 0 (some delay)
    assert scheduled > 0.0
    
    # Mean delay should be 1/rate = 2.0
    # (Run multiple times to verify mean)

def test_stochastic_fires_at_scheduled_time():
    """Stochastic fires when scheduled time reached."""
    model = create_stochastic_model(rate=1.0)
    controller = SimulationController(model)
    
    behavior = controller._get_behavior(model.transitions[0])
    behavior.set_enablement_time(0.0)
    scheduled = behavior.scheduled_time
    
    # Before scheduled time
    controller.time = scheduled - 0.01
    can_fire, _ = behavior.can_fire()
    assert not can_fire
    
    # At scheduled time
    controller.time = scheduled
    can_fire, _ = behavior.can_fire()
    assert can_fire

def test_stochastic_reschedules_on_reenablement():
    """Re-enabling samples new delay."""
    import random
    random.seed(42)
    
    model = create_stochastic_model(rate=1.0)
    controller = SimulationController(model)
    
    behavior = controller._get_behavior(model.transitions[0])
    
    # First enablement
    behavior.set_enablement_time(0.0)
    scheduled_1 = behavior.scheduled_time
    
    # Clear and re-enable
    behavior.clear_enablement()
    behavior.set_enablement_time(10.0)
    scheduled_2 = behavior.scheduled_time
    
    # Should be different (new sample)
    assert scheduled_2 != scheduled_1
    assert scheduled_2 > 10.0  # Relative to new enablement
```

### 6.4 Performance Tests

```python
def test_performance_many_steps():
    """Simulation with many steps completes in reasonable time."""
    import time
    
    model = create_simple_model()
    controller = SimulationController(model)
    controller.settings.duration_value = 1000.0
    controller.settings.target_steps = 100000  # 100k steps
    
    start = time.time()
    controller.run()
    elapsed = time.time() - start
    
    # Should complete in < 10 seconds (adjust as needed)
    assert elapsed < 10.0

def test_performance_many_transitions():
    """Model with many transitions."""
    model = create_large_model(num_transitions=1000)
    controller = SimulationController(model)
    
    # Should complete step without hanging
    start = time.time()
    controller.step()
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # Single step < 1 second
```

### 6.5 Integration Tests

```python
def test_full_simulation_run():
    """Complete simulation from start to finish."""
    model = load_example_model("manufacturing.shy")
    controller = SimulationController(model)
    controller.settings.duration_value = 60.0  # 1 minute
    controller.settings.dt_mode = 'auto'
    
    # Run to completion
    result = controller.run()
    
    # Verify completed
    assert controller.is_simulation_complete()
    assert controller.time >= 60.0
    
    # Verify model state changed
    # (Check specific place markings)

def test_pause_resume():
    """Simulation can be paused and resumed."""
    model = load_example_model("simple.shy")
    controller = SimulationController(model)
    
    # Run for 5 steps
    for _ in range(5):
        controller.step()
    
    time_paused = controller.time
    
    # Pause (just stop calling step)
    # ... (UI would show paused state)
    
    # Resume
    for _ in range(5):
        controller.step()
    
    # Time continued from pause point
    assert controller.time > time_paused

def test_reset():
    """Simulation can be reset to initial state."""
    model = load_example_model("simple.shy")
    controller = SimulationController(model)
    
    # Run for several steps
    controller.run(max_steps=10)
    
    # Reset
    controller.reset()
    
    # Verify back to initial state
    assert controller.time == 0.0
    # (Check place markings reset)
```

---

## 7. Test Implementation Priority

### Phase 1: Critical Tests (Implement First)

1. ✅ **Basic Time Advance**
   - `test_time_starts_at_zero`
   - `test_time_advances_by_dt`
   - `test_auto_dt_calculation`
   - `test_simulation_completes_at_duration`

2. ✅ **Timed Transitions**
   - `test_timed_window_earliest`
   - `test_timed_window_latest`
   - `test_timed_window_boundaries_inclusive`

3. ✅ **Continuous Integration**
   - `test_continuous_integration_linear`
   - `test_continuous_time_dependent_rate`

4. ✅ **Immediate Exhaustion**
   - `test_immediate_fires_in_zero_time`
   - `test_immediate_exhaust_loop`

### Phase 2: Integration Tests

5. ✅ **Hybrid Execution**
   - `test_hybrid_discrete_doesnt_affect_continuous`
   - `test_hybrid_all_four_types`

6. ✅ **Full Simulation**
   - `test_full_simulation_run`
   - `test_pause_resume`
   - `test_reset`

### Phase 3: Edge Cases

7. ⚠️ **Edge Cases**
   - `test_zero_duration`
   - `test_very_small_dt`
   - `test_very_large_dt`
   - `test_negative_dt_rejected`
   - `test_floating_point_precision`

8. ⚠️ **Conflict Resolution**
   - `test_simultaneous_timed_conflict`
   - (Test each policy)

### Phase 4: Performance & Stress

9. 🔧 **Performance**
   - `test_performance_many_steps`
   - `test_performance_many_transitions`

---

## 8. Known Issues & Recommendations

### 8.1 Current Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| **Large dt misses timed windows** | HIGH | Transitions never fire |
| **No negative dt validation** | MEDIUM | Time can go backwards |
| **Floating-point accumulation** | MEDIUM | Precision loss over time |
| **No warning for small/large dt** | LOW | Performance degradation |
| **Immediate loop only logs warning** | LOW | May appear as hang |

### 8.2 Recommendations

#### Short-Term (Next Sprint)

1. **Add dt validation**
   ```python
   def step(self, time_step=None):
       if time_step is not None and time_step < 0:
           raise ValueError("time_step must be non-negative")
       # ... rest of implementation
   ```

2. **Warn about large dt**
   ```python
   if time_step > 1.0:  # Arbitrary threshold
       logger.warning(f"Large time step ({time_step}s) may miss timed transition windows")
   ```

3. **Use epsilon for comparisons**
   ```python
   EPSILON = 1e-9
   
   if abs(elapsed - self.earliest) < EPSILON or elapsed >= self.earliest:
       # Within window (handle floating-point precision)
   ```

#### Medium-Term (Future Release)

4. **Implement adaptive dt**
   ```python
   def get_adaptive_dt(self):
       """Adjust dt based on scheduled events."""
       next_event = self._get_next_scheduled_event()
       regular_dt = self.get_effective_dt()
       
       if next_event and next_event < self.time + regular_dt:
           # Use smaller dt to hit event exactly
           return next_event - self.time
       else:
           return regular_dt
   ```

5. **Add next-event scheduling**
   ```python
   def step_to_next_event(self):
       """Advance directly to next scheduled event."""
       next_event = min(all_scheduled_times)
       
       if next_event > self.time:
           time_step = next_event - self.time
           self.time = next_event
           # Fire scheduled transitions
   ```

6. **Improve immediate loop detection**
   ```python
   if immediate_fired_total >= max_immediate_iterations:
       raise SimulationError(
           f"Immediate transition loop detected "
           f"({max_immediate_iterations} iterations). "
           f"Check for cycles in immediate transitions."
       )
   ```

#### Long-Term (Research)

7. **Higher-order integration**
   - Replace Forward Euler with RK4 or adaptive methods
   - Better accuracy for continuous transitions
   - Requires more complex implementation

8. **Hybrid time-stepping**
   - Combine fixed steps (continuous) with event scheduling (discrete)
   - Best of both worlds
   - Significant architectural change

---

## 9. Documentation Needs

### 9.1 User Documentation

- **Time Settings Guide:** How to choose dt and duration
- **Transition Timing Guide:** Understanding windows and delays
- **Performance Tuning:** Optimizing dt for model complexity
- **Troubleshooting:** Why transitions don't fire

### 9.2 Developer Documentation

- **Time Architecture:** Complete system overview (this document)
- **API Reference:** Time-related methods and properties
- **Integration Guide:** Adding new transition types
- **Testing Guide:** Writing time-sensitive tests

---

## 10. Conclusion

### Summary

Time computation in ShyPN simulation involves:

1. **Fixed time steps** with configurable dt
2. **Zero-time immediate** transitions (exhaustive firing)
3. **Windowed timed** transitions (earliest/latest constraints)
4. **Scheduled stochastic** transitions (exponential delays)
5. **Integrated continuous** transitions (rate-based flow)
6. **Hybrid execution** (discrete + continuous in one step)

### Critical Success Factors

✅ **Correct time advance** (self.time += dt)  
✅ **Proper enablement tracking** (record when transitions enable)  
✅ **Timing constraint enforcement** (windows, schedules)  
✅ **Consistent execution order** (immediate → discrete → continuous)  
✅ **Snapshot approach** (continuous uses pre-discrete state)  

### Test Coverage Goals

- ✅ 100% of basic time advance scenarios
- ✅ 100% of transition timing constraints
- ✅ 90% of edge cases
- ✅ 80% of performance scenarios

### Next Steps

1. **Implement Phase 1 tests** (critical functionality)
2. **Fix identified issues** (validation, warnings)
3. **Run test suite** and achieve 90%+ pass rate
4. **Document findings** and update user guides
5. **Plan medium-term improvements** (adaptive dt, event scheduling)

---

**Document Status:** ✅ Complete  
**Last Updated:** October 8, 2025  
**Maintainer:** Development Team  
**Review Status:** Ready for implementation
