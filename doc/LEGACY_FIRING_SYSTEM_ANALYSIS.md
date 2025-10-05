# Legacy Firing System Analysis - Time Control & Transition Logic

**Date**: October 5, 2025  
**Purpose**: Comprehensive analysis of legacy firing system architecture for all transition types

---

## Executive Summary

The legacy system implements a **three-phase firing architecture** with separate schedulers for each transition type. Current implementation uses a **simplified single-phase approach** that may be missing critical timing and scheduling logic.

### Key Findings

1. **Legacy uses SEPARATE schedulers per transition type** (timed, stochastic, continuous)
2. **Current implementation lacks scheduler infrastructure** - all timing handled in behaviors
3. **Legacy has proper time advancement** via `unified_scheduler.advance_to_next_event()`
4. **Current implementation may deadlock** when waiting for scheduled events

---

## 1. Legacy Architecture Overview

### 1.1 Controller Structure (`simulation/controller.py`)

```python
class SimulationController:
    def __init__(self, model):
        self.model = model
        self._on_step = []  # Step listeners
        self._verbose_firing = False
        self._force_method = None  # 'locality' or 'global'
```

**Key Methods**:
- `step(time_step=0.1)` - Main simulation step
- `add_step_listener(callback)` - Register UI update callbacks
- `set_firing_method(method)` - Force locality vs global firing
- `enable_verbose_firing()` - Debug output toggle

### 1.2 Three-Phase Firing Process

Legacy `controller.step()` implements:

```python
def step(self, time_step=0.1):
    # PHASE 1: IMMEDIATE TRANSITIONS (loop until exhausted)
    immediate_iterations = 0
    while immediate_iterations < 1000:
        immediate_enabled = [t for t in transitions if t.is_immediate() 
                            and model.is_transition_enabled(t)]
        if not immediate_enabled:
            break
        fire_enabled_transitions(model)  # Fires ALL enabled immediate
        immediate_iterations += 1
    
    # PHASE 2: TIMED TRANSITIONS (time advancement)
    timed_result = fire_enabled_transitions(model)
    
    # PHASE 3: CONTINUOUS TRANSITIONS (integration)
    unified_scheduler = model.unified_scheduler
    if unified_scheduler and unified_scheduler.continuous_scheduler:
        # Schedule continuous transitions
        # Integrate step
        # Update place markings
```

**Critical Differences from Current**:
- ✅ **Legacy**: Loops until ALL immediate transitions exhausted
- ❌ **Current**: Fires ONE immediate per step
- ✅ **Legacy**: Uses unified scheduler for time advancement
- ❌ **Current**: No scheduler - waits in loop until time passes

---

## 2. Scheduler Infrastructure

### 2.1 Unified Scheduler (`simulation/unified_scheduler.py`)

**Purpose**: Coordinates all time-based events across transition types

```python
class UnifiedScheduler:
    def __init__(self):
        self.timed_scheduler = TimedScheduler()
        self.stochastic_scheduler = StochasticScheduler()
        self.continuous_scheduler = ContinuousScheduler()
        self.current_time = 0.0
    
    def get_next_event(self) -> Event:
        """Get earliest event across all schedulers"""
        
    def advance_to_next_event(self) -> (float, list):
        """Advance time to next scheduled event, return new_time and ready_transitions"""
```

**Current Implementation**: ❌ **MISSING** - No unified scheduler exists

### 2.2 Timed Scheduler (`simulation/timed_scheduler.py`)

**Scientific Basis**: Time Petri Nets (Merlin & Farber 1976)

```python
class TimedEvent:
    fire_time: float        # When transition can fire
    transition_id: str
    enabled_time: float     # When transition became enabled
    min_delay: float        # [earliest, latest] window
    max_delay: float
    priority: int           # Conflict resolution

class EnhancedTimedScheduler:
    def __init__(self):
        self.event_queue = []  # Min-heap ordered by fire_time
        self.current_time = 0.0
        self.transition_schedules = {}
    
    def schedule_transition(self, transition_id, min_delay, max_delay):
        """Schedule transition at current_time + min_delay"""
        fire_time = self.current_time + min_delay
        event = TimedEvent(fire_time, transition_id, ...)
        heapq.heappush(self.event_queue, event)
    
    def get_next_event_time(self) -> float:
        """Return time of next scheduled event"""
    
    def get_ready_transitions(self, current_time) -> list:
        """Return all transitions ready to fire at current_time"""
```

**Key Features**:
- ✅ **Heap-based priority queue** for efficient scheduling
- ✅ **[min_delay, max_delay] interval** support (TPN semantics)
- ✅ **Conflict resolution** via priority
- ✅ **Dynamic rescheduling** when transitions disabled

**Current Implementation**: 
- ❌ **No event queue** - timing checked inline in `can_fire()`
- ❌ **No heap structure** - linear search each step
- ⚠️ **Timing checked but not scheduled** - wastes CPU cycles

### 2.3 Stochastic Scheduler (`simulation/stochastic_scheduler.py`)

**Scientific Basis**: Stochastic Petri Nets (Marsan et al. 1984)

```python
class StochasticEvent:
    fire_time: float
    transition_id: str
    enabled_time: float
    rate_parameter: float      # λ for exponential distribution
    sampled_delay: float       # Actual delay sampled

class StochasticScheduler:
    def __init__(self, random_seed=None):
        self.random_generator = random.Random(random_seed)
        self.event_queue = []  # Min-heap
        self.firing_history = []  # Statistical tracking
    
    def sample_exponential_delay(self, rate: float) -> float:
        """Sample from Exp(λ) using inverse transform:
        T = -ln(U) / λ, where U ~ Uniform(0,1)
        """
        u = self.random_generator.random()
        return -math.log(u) / rate
    
    def schedule_transition(self, transition_id, rate):
        """Sample delay, schedule at current_time + delay"""
        delay = self.sample_exponential_delay(rate)
        fire_time = self.current_time + delay
        event = StochasticEvent(fire_time, transition_id, ...)
        heapq.heappush(self.event_queue, event)
```

**Key Features**:
- ✅ **Exponential distribution** via inverse transform
- ✅ **Reproducible randomness** with seed support
- ✅ **Burst size sampling** (1 to max_burst)
- ✅ **Race condition resolution** (earliest event wins)

**Current Implementation**:
- ✅ **Exponential sampling exists** in `StochasticBehavior`
- ❌ **No event queue** - checked every step
- ⚠️ **Sampled delay stored but not scheduled** - works but inefficient

### 2.4 Continuous Scheduler (`simulation/continuous_scheduler.py`)

**Scientific Basis**: Hybrid Petri Nets, Continuous Petri Nets

```python
class ContinuousScheduler:
    def __init__(self, integration_step=0.01):
        self.integration_step = 0.01  # Small dt for numerical integration
        self.continuous_transitions = {}
        self.current_time = 0.0
    
    def schedule_continuous_transition(self, tid, transition, marking):
        """Add transition to continuous integration set"""
    
    def integrate_step(self, dt, marking, transitions, arcs) -> dict:
        """Perform numerical integration (Euler method):
        
        dm(p)/dt = Σ rate(t) * weight(t,p) - Σ rate(t) * weight(p,t)
        
        Returns new marking after integration
        """
```

**Key Features**:
- ✅ **Euler integration** with configurable step size
- ✅ **Rate function evaluation** per transition
- ✅ **Continuous token updates** (float values)
- ✅ **Boundary detection** (prevent negative tokens)

**Current Implementation**:
- ✅ **Integration exists** in `ContinuousBehavior.integrate_step()`
- ✅ **Rate functions work** (sigmoid, linear, etc.)
- ⚠️ **No separate scheduler** - integrated directly in controller

---

## 3. Time Advancement Logic

### 3.1 Legacy Time Advancement

```python
# In controller.step():
unified_scheduler = model.unified_scheduler

# Check for next scheduled event
next_event_time = unified_scheduler.get_next_event_time()

if next_event_time is not None and next_event_time > current_time:
    # ADVANCE TIME to next event
    new_time, ready_transitions = unified_scheduler.advance_to_next_event()
    model.logical_time = new_time  # Jump forward in time
    
    # Fire ready transitions
    for transition in ready_transitions:
        fire_transition(transition)
```

**Key Point**: Legacy **JUMPS TIME FORWARD** to next event, not incremental 0.1s steps!

### 3.2 Current Time Advancement

```python
# In controller.step():
# ... fire transitions ...

# Advance time ALWAYS by fixed increment
self.time += time_step  # e.g., 0.1 seconds

# No scheduler, no time jumping
```

**Key Point**: Current **ALWAYS increments by time_step**, even if nothing happens!

### 3.3 Comparison

| Aspect | Legacy | Current |
|--------|--------|---------|
| Time model | Event-driven (variable Δt) | Fixed time-step (constant Δt) |
| Idle periods | Skips ahead to next event | Iterates through empty steps |
| Efficiency | O(log n) per event | O(n) steps regardless |
| Timed transitions | Fires exactly at scheduled time | Fires when elapsed ≥ delay |
| Precision | Exact event times | Depends on time_step granularity |

---

## 4. Firing Logic Per Transition Type

### 4.1 Immediate Transitions

**Legacy**:
```python
# Fire ALL enabled immediate transitions in priority order
while True:
    immediate_enabled = find_all_immediate_enabled()
    if not immediate_enabled:
        break
    
    # Sort by priority
    immediate_enabled.sort(key=lambda t: t.priority, reverse=True)
    
    # Fire highest priority
    fire_transition(immediate_enabled[0])
```

**Current**:
```python
# Fire ONE enabled transition per step
enabled = find_enabled_transitions()
if enabled:
    transition = select_transition(enabled)  # Conflict resolution
    fire_transition(transition)
```

**Impact**: Current may take multiple steps to fire all immediate transitions!

### 4.2 Timed Transitions (TPN)

**Legacy**:
```python
# Schedule when enabled
timed_scheduler.schedule_transition(
    transition_id, 
    min_delay=earliest, 
    max_delay=latest
)

# Later: advance to scheduled time
new_time, ready = scheduler.advance_to_next_event()
for t in ready:
    fire_transition(t)
```

**Current**:
```python
# Check every step
elapsed = current_time - enablement_time
if earliest <= elapsed <= latest:
    fire_transition()  # Fires on first step where condition true
```

**Impact**: Current works but checks EVERY step (inefficient)

### 4.3 Stochastic Transitions (SPN)

**Legacy**:
```python
# Sample delay when enabled
delay = -math.log(random()) / rate
stochastic_scheduler.schedule_transition(transition_id, delay)

# Later: advance to scheduled time
new_time, ready = scheduler.advance_to_next_event()
for t in ready:
    fire_transition(t, burst=sampled_burst)
```

**Current**:
```python
# Sample delay when enabled
delay = -math.log(random()) / rate
scheduled_time = current_time + delay

# Check every step
if current_time >= scheduled_time:
    fire_transition(burst=sampled_burst)
```

**Impact**: Current works but checks EVERY step (inefficient)

### 4.4 Continuous Transitions (HPN)

**Legacy**:
```python
# Schedule for continuous integration
continuous_scheduler.schedule_continuous_transition(tid, transition, marking)

# Integrate at small time steps
dt = 0.01  # Small integration step
new_marking = continuous_scheduler.integrate_step(dt, marking, transitions, arcs)

# Update marking
for place_id, new_tokens in new_marking.items():
    place.tokens = new_tokens
```

**Current**:
```python
# Integrate directly in controller
for transition in continuous_transitions:
    if can_fire:
        behavior.integrate_step(dt=time_step, input_arcs, output_arcs)
```

**Impact**: Current works, no scheduler needed for continuous

---

## 5. Critical Issues in Current Implementation

### 5.1 Stop/Resume Bug (Fixed)

**Problem**: Enablement times not cleared on Stop → stale times on Resume

**Root Cause**:
```python
# Old stop():
def stop(self):
    self._stop_requested = True
    # BUG: Enablement times NOT cleared!
```

**Fix Applied**:
```python
def stop(self):
    self._stop_requested = True
    # Clear enablement states
    for state in self.transition_states.values():
        state.enablement_time = None
        state.scheduled_time = None
```

**Status**: ✅ **FIXED** - Enablement times now cleared on Stop

### 5.2 Missing Initial Enablement (Fixed)

**Problem**: First Run doesn't set enablement times until first step

**Root Cause**:
```python
# Old run():
def run(self, time_step=0.1):
    self._running = True
    GLib.timeout_add(100, self._simulation_loop)
    # BUG: No initial enablement update!
```

**Fix Applied**:
```python
def run(self, time_step=0.1):
    self._running = True
    self._update_enablement_states()  # Initialize before loop
    GLib.timeout_add(100, self._simulation_loop)
```

**Status**: ✅ **FIXED** - Enablement times set before simulation starts

### 5.3 Inefficient Time Checking (Not Fixed)

**Problem**: Every transition checked every step (100ms interval)

**Example**: Timed transition with delay=10.0 seconds
- Legacy: Schedule once, check once at t=10.0 → **1 check total**
- Current: Check every step for 10 seconds → **100 checks total**

**Impact**: 
- ⚠️ **Performance**: O(n) checks per step vs O(1) scheduler lookup
- ⚠️ **CPU Usage**: Higher but probably acceptable for typical models
- ✅ **Correctness**: Works correctly, just not optimal

**Recommendation**: Consider adding scheduler for large models (100+ transitions)

### 5.4 Immediate Transition Exhaustion (Not Fixed)

**Problem**: Only fires ONE immediate transition per step

**Example**: Chain of 5 immediate transitions
- Legacy: All 5 fire in one step (< 1ms) → **instant propagation**
- Current: Takes 5 steps (5 × 100ms = 500ms) → **visible delay**

**Impact**:
- ⚠️ **User Experience**: Slow token propagation through immediate chains
- ⚠️ **Semantics**: Violates "instantaneous" property of immediate transitions
- 🔧 **Fix**: Loop until no immediate transitions enabled (like legacy)

**Recommendation**: **HIGH PRIORITY** - Add immediate exhaustion loop

---

## 6. Recommended Improvements

### 6.1 Immediate Priority: Add Immediate Exhaustion Loop

```python
def step(self, time_step=0.1):
    # PHASE 1: Fire ALL immediate transitions
    max_iterations = 1000
    for i in range(max_iterations):
        immediate_enabled = [t for t in self.model.transitions 
                            if t.transition_type == 'immediate' 
                            and self._is_transition_enabled(t)]
        
        if not immediate_enabled:
            break  # No more immediate transitions
        
        # Fire highest priority immediate
        transition = self._select_transition(immediate_enabled)
        self._fire_transition(transition)
    
    # PHASE 2: Continue with timed/stochastic/continuous
    # ... existing code ...
```

**Benefit**: Proper immediate transition semantics, instant token propagation

### 6.2 Medium Priority: Add Event Scheduler (Optional)

```python
class SimulationController:
    def __init__(self, model):
        # ... existing ...
        self.event_scheduler = EventScheduler()  # NEW
    
    def _update_enablement_states(self):
        for transition in self.model.transitions:
            if newly_enabled:
                if transition.transition_type == 'timed':
                    # Schedule event instead of just tracking time
                    self.event_scheduler.schedule(
                        transition.id, 
                        current_time + earliest
                    )
    
    def step(self, time_step=0.1):
        # Check if should jump to next event
        next_event_time = self.event_scheduler.get_next_time()
        
        if next_event_time and next_event_time <= self.time + time_step:
            # Jump to event time
            self.time = next_event_time
            ready = self.event_scheduler.get_ready_events(self.time)
            for t_id in ready:
                fire_transition(t_id)
        else:
            # Normal step
            # ... existing code ...
```

**Benefit**: Better performance for large models, exact event timing

### 6.3 Low Priority: Unified Scheduler (Future)

Full legacy-style unified scheduler with timed/stochastic/continuous coordination.

**Benefit**: Maximum efficiency, but complex to implement

---

## 7. Summary & Recommendations

### Current State

✅ **Working**:
- All transition types fire correctly
- Timing constraints respected
- Stop/Resume bug fixed
- Initial enablement bug fixed

⚠️ **Suboptimal**:
- Immediate transitions not exhausted instantly
- No event scheduler (checks every step)
- Higher CPU usage than necessary

### Immediate Actions

1. **HIGH**: Implement immediate exhaustion loop (30 minutes)
2. **MEDIUM**: Consider event scheduler for large models (2-4 hours)
3. **LOW**: Full unified scheduler migration (1-2 days)

### Performance Profile

| Model Size | Current | With Scheduler |
|------------|---------|----------------|
| Small (<20 trans) | Excellent | No difference |
| Medium (20-100) | Good | Better |
| Large (100+) | Acceptable | Much better |
| Very Large (1000+) | May lag | Smooth |

### Conclusion

Current implementation is **functionally correct** but **architecturally simplified** compared to legacy. The **immediate exhaustion loop** is the only critical missing piece for proper Petri net semantics. The event scheduler is an optimization, not a requirement.

**Recommended next step**: Add immediate exhaustion loop (highest semantic impact, lowest implementation cost).

---

## References

- **Legacy Code**: `legacy/shypnpy/simulation/`
- **Current Code**: `src/shypn/engine/simulation/controller.py`
- **Merlin & Farber (1976)**: Time Petri Nets
- **Marsan et al. (1984)**: Stochastic Petri Nets
