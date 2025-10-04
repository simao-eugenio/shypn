# Transition Behaviors Summary - Time/Rate/Locality/Independence Implementation

## Overview

The simulation engine implements **4 transition types** with distinct firing behaviors based on Petri net theory. Each type has its own algorithm for determining **when** and **how** to fire.

---

## 1. Transition Types & Behaviors

### 1.1 **Immediate Behavior** (`immediate_behavior.py`)
**Theory**: Standard Petri Net (PN)

**Time Model**:
- **Zero delay** - fires instantly when enabled
- No timing constraints

**Rate Model**:
- N/A (discrete firing, not rate-based)

**Firing Algorithm**:
```python
def fire():
    1. Check structural enablement (∀p ∈ •t: m(p) ≥ Pre(p,t))
    2. If enabled:
       - Consume: m(p) -= arc_weight for each input p
       - Produce: m(p) += arc_weight for each output p
    3. Time advance: 0 (instant)
```

**Independence**: 
- Transitions are independent (fire one at a time, sequentially)
- No concurrency within immediate transitions

**Properties**:
- `arc_weight`: tokens consumed/produced per firing

---

### 1.2 **Timed Behavior** (`timed_behavior.py`)
**Theory**: Time Petri Net (TPN) - Merlin & Farber 1976

**Time Model**:
- **Timing window**: `[earliest, latest]`
- Enabled at time `t_enable`
- Can fire during interval: `[t_enable + earliest, t_enable + latest]`

**Rate Model**:
- N/A (discrete firing with time constraints)

**Firing Algorithm**:
```python
def can_fire():
    1. Check structural enablement
    2. If enabled since t_enable:
       current_time = model.time
       elapsed = current_time - t_enable
       
       if earliest <= elapsed <= latest:
           return True, "in-timing-window"
       elif elapsed < earliest:
           return False, "too-early"
       else:  # elapsed > latest
           return False, "too-late"
    
def fire():
    1. Same as immediate (discrete token transfer)
    2. Time advance: current_time (already at firing time)
```

**Independence**:
- Transitions have independent timing windows
- Multiple timed transitions can have overlapping windows
- Scheduler chooses which to fire (policy-dependent)

**Properties**:
- `earliest` (α): minimum delay after enablement
- `latest` (β): maximum delay after enablement
- Constraint: `0 ≤ earliest ≤ latest`

---

### 1.3 **Stochastic Behavior** (`stochastic_behavior.py`)
**Theory**: Fluid Stochastic Petri Net (FSPN)

**Time Model**:
- **Exponential delays**: `T ~ Exp(λ)` where `λ = rate`
- Firing delay sampled when transition becomes enabled
- Scheduled firing time: `t_fire = t_enable + T`

**Rate Model**:
- `rate (λ)`: parameter of exponential distribution
- Higher rate → shorter average delay → more frequent firing
- Mean delay = `1/λ`

**Firing Algorithm**:
```python
def set_enablement_time(t_enable):
    # Sample firing delay from exponential distribution
    U = random.uniform(0, 1)
    delay = -ln(U) / rate
    t_fire = t_enable + delay
    
    # Sample burst size (1 to max_burst)
    burst = random.randint(1, max_burst)  # default max_burst = 8

def can_fire():
    if current_time >= t_fire:
        # Check sufficient tokens for burst firing
        if ∀p: m(p) >= arc_weight * burst:
            return True
    return False

def fire():
    # Burst firing: consume/produce burst × arc_weight tokens
    for input_place in •t:
        m(input_place) -= arc_weight * burst
    for output_place in t•:
        m(output_place) += arc_weight * burst
```

**Independence**:
- Each transition has independent exponential clock
- **Race condition**: multiple enabled transitions compete
- First to reach scheduled time fires (others may be disabled)

**Properties**:
- `rate (λ)`: exponential rate parameter
- `max_burst`: maximum burst multiplier (default: 8)
- `burst`: sampled burst size ∈ [1, max_burst]

---

### 1.4 **Continuous Behavior** (`continuous_behavior.py`)
**Theory**: Stochastic Hybrid Petri Net (SHPN)

**Time Model**:
- **Continuous evolution**: no discrete firing events
- Integration over time steps: `dt`

**Rate Model**:
- **Rate function**: `r(t) = f(m(t), params)`
- Defines **continuous flow** of tokens
- Can depend on:
  - Current token counts: `m(p)`
  - Simulation time: `t`
  - External parameters

**Firing Algorithm** (Integration):
```python
def integrate_step(dt):
    # Runge-Kutta 4th order (RK4) integration
    
    # Compute rate at current state
    r0 = rate_function(places, t)
    
    # RK4 intermediate steps
    k1 = r0 * dt
    k2 = rate_function(places + k1/2, t + dt/2) * dt
    k3 = rate_function(places + k2/2, t + dt/2) * dt
    k4 = rate_function(places + k3, t + dt) * dt
    
    # Update token counts
    Δm = (k1 + 2*k2 + 2*k3 + k4) / 6
    
    for input_place in •t:
        m(input_place) -= Δm * arc_weight
    for output_place in t•:
        m(output_place) += Δm * arc_weight
```

**Independence**:
- **Concurrent evolution**: multiple continuous transitions evolve simultaneously
- All enabled continuous transitions integrate in parallel
- No race conditions (continuous state space)

**Properties**:
- `rate_function`: expression or callable
  - Example: `"5.0"` (constant rate)
  - Example: `"2.0 * P1"` (proportional to tokens)
  - Example: `"min(10, P1)"` (saturated rate)
- `max_rate`, `min_rate`: bounds on rate
- `integration_method`: "rk4" (Runge-Kutta 4th order)

---

## 2. Locality Concept

### 2.1 **Definition**
**Locality** refers to the **neighborhood** of a transition:
- **Input places** (`•t`): places with arcs TO the transition
- **Output places** (`t•`): places with arcs FROM the transition

### 2.2 **Locality-Based Enablement**
A transition is **enabled** based on its **local neighborhood**:

```python
def is_enabled(transition):
    # Check only INPUT places (locality)
    for place in •transition:
        if place.tokens < arc_weight:
            return False  # Insufficient tokens in input place
    return True
```

**Key Insight**: 
- A transition's enablement depends **only on its input places**
- Does not depend on global network state
- Enables **local reasoning** about transition behavior

### 2.3 **Locality in Simulation**
The simulation controller uses locality for efficiency:

```python
def get_enabled_transitions():
    enabled = []
    for transition in model.transitions:
        # Locality: check only transition's input places
        if is_locally_enabled(transition):
            enabled.append(transition)
    return enabled
```

---

## 3. Independence Concept

### 3.1 **Definition**
**Independence** describes how transitions **interact** (or don't interact) during firing:

**Types of Independence**:
1. **Structural Independence**: Transitions have disjoint localities
   - `•t1 ∩ •t2 = ∅` (no shared input places)
   - Can fire concurrently without conflict

2. **Temporal Independence**: Transitions have separate timing
   - Immediate/Timed: sequential (one fires per step)
   - Stochastic: race condition (first to fire wins)
   - Continuous: parallel (all integrate simultaneously)

### 3.2 **Independence Algorithms**

#### **Immediate & Timed**: Sequential (No Concurrency)
```python
def simulation_step():
    enabled = get_enabled_transitions()
    if enabled:
        # Choose ONE transition to fire (policy: random, priority, etc.)
        selected = choose_one(enabled)
        selected.fire()
    # Only one transition fires per step
```

#### **Stochastic**: Race Condition
```python
def simulation_step():
    enabled = get_enabled_transitions()
    
    # Each transition has scheduled fire time
    earliest_time = min(t.scheduled_time for t in enabled)
    
    # Advance time to earliest fire time
    model.time = earliest_time
    
    # Fire transition that reached fire time first
    winner = [t for t in enabled if t.scheduled_time == earliest_time][0]
    winner.fire()
    
    # Other transitions may now be disabled (tokens consumed)
```

#### **Continuous**: Parallel Evolution
```python
def simulation_step(dt):
    enabled_continuous = [t for t in transitions if t.type == 'continuous' and t.is_enabled()]
    
    # ALL continuous transitions integrate in parallel
    for transition in enabled_continuous:
        transition.integrate_step(dt)
    
    # Tokens evolve smoothly, all transitions active simultaneously
```

---

## 4. Implementation Architecture

### 4.1 **Strategy Pattern**
Each behavior is a separate class implementing `TransitionBehavior` interface:

```
TransitionBehavior (ABC)
    ├── ImmediateBehavior    # Zero-delay discrete
    ├── TimedBehavior         # Time windows [earliest, latest]
    ├── StochasticBehavior    # Exponential delays + bursts
    └── ContinuousBehavior    # Rate functions + integration
```

### 4.2 **Factory Pattern**
Behaviors are created via factory:

```python
behavior = create_behavior(transition, model)
# Returns appropriate behavior based on transition.type
```

### 4.3 **Simulation Controller Integration**
The `SimulationController` uses behaviors:

```python
def step(time_step):
    1. Get enabled transitions (locality-based)
    2. For each enabled transition:
       behavior = create_behavior(transition, model)
       can_fire, reason = behavior.can_fire()
    3. Choose transition(s) to fire (independence algorithm)
    4. Execute firing:
       behavior.fire(input_arcs, output_arcs)
    5. Advance time
    6. Emit step-executed signal
```

---

## 5. Key Properties Summary

| Property | Immediate | Timed | Stochastic | Continuous |
|----------|-----------|-------|------------|------------|
| **Time Model** | Zero delay | `[earliest, latest]` | `T ~ Exp(λ)` | Continuous |
| **Rate Model** | N/A | N/A | `λ` (exponential) | `r(t)` (function) |
| **Token Mode** | Discrete | Discrete | Discrete (burst) | Continuous |
| **Firing** | Instant | Within window | Scheduled | Integration |
| **Independence** | Sequential | Sequential | Race | Parallel |
| **Locality** | Input places | Input places | Input places | Input places |

---

## 6. References

### Legacy Code
- **immediate_behavior.py**: Lines extracted from `legacy/shypnpy/core/petri.py:1908-1970`
- **timed_behavior.py**: Lines extracted from `legacy/shypnpy/core/petri.py:1971-2050+`
- **stochastic_behavior.py**: Lines extracted from `legacy/shypnpy/core/petri.py:1562-1690`
- **continuous_behavior.py**: Lines extracted from `legacy/shypnpy/core/petri.py:1691-1900`

### Theory
- **Time Petri Nets**: Merlin & Farber (1976)
- **Fluid Stochastic Petri Nets**: FSPN theory
- **Stochastic Hybrid Petri Nets**: SHPN theory

---

## 7. Current Implementation Status

✅ **Fully Implemented**:
- All 4 behavior classes with complete algorithms
- Factory pattern for behavior creation
- Locality-based enablement checking
- Independence algorithms (sequential, race, parallel)

✅ **Integrated**:
- SimulationController uses behaviors
- Signals for UI update (step-executed)
- Time tracking and advancement

🔨 **Future Work**:
- Formula evaluation for rate functions (guard/rate expressions)
- Advanced scheduling policies
- Conflict resolution strategies
- Performance optimizations (locality caching)

---

## 8. Usage Examples

### Example 1: Immediate Transition
```python
# Create immediate transition
t1 = Transition(id=1, name="T1")
t1.type = 'immediate'

# Create behavior
behavior = create_behavior(t1, model)

# Check and fire
if behavior.can_fire()[0]:
    success, details = behavior.fire(
        behavior.get_input_arcs(),
        behavior.get_output_arcs()
    )
    print(f"Consumed: {details['consumed']}")
    print(f"Produced: {details['produced']}")
```

### Example 2: Timed Transition
```python
# Create timed transition with window [2.0, 5.0]
t2 = Transition(id=2, name="T2")
t2.type = 'timed'
t2.properties = {'earliest': 2.0, 'latest': 5.0}

# Create behavior
behavior = create_behavior(t2, model)

# Set enablement time
behavior.set_enablement_time(model.time)

# Later, check if can fire
can_fire, reason = behavior.can_fire()
print(f"Can fire: {can_fire}, Reason: {reason}")
```

### Example 3: Stochastic Transition
```python
# Create stochastic transition with rate λ=0.5
t3 = Transition(id=3, name="T3")
t3.type = 'stochastic'
t3.properties = {'rate': 0.5, 'max_burst': 8}

# Create behavior
behavior = create_behavior(t3, model)

# Set enablement (samples delay and burst)
behavior.set_enablement_time(model.time)

# Check scheduled fire time
fire_time = behavior.get_scheduled_fire_time()
print(f"Scheduled to fire at: {fire_time}")
```

### Example 4: Continuous Transition
```python
# Create continuous transition with rate function
t4 = Transition(id=4, name="T4")
t4.type = 'continuous'
t4.properties = {'rate_function': '2.0 * P1'}

# Create behavior
behavior = create_behavior(t4, model)

# Integrate over time step
success, details = behavior.integrate_step(
    dt=0.01,
    input_arcs=behavior.get_input_arcs(),
    output_arcs=behavior.get_output_arcs()
)
print(f"Integrated flow: {details}")
```

---

**Document Created**: October 4, 2025  
**Status**: Complete implementation summary based on legacy code analysis
