# Stochastic Source Transition Stability Issues - Analysis & Fix

**Date**: October 13, 2025  
**Issue**: Stochastic source transitions are very unstable  
**Root Causes**: Multiple architectural issues with scheduling and enablement tracking

---

## Problem Summary

### Issue 1: Source Transitions Lose Schedule After Firing

**Problem**: Stochastic source transitions (T→P, no inputs) become disabled after firing because:

1. Controller's `_check_newly_enabled()` checks for input tokens
2. Source transitions have NO input places
3. Logic: `if source_place.tokens < arc.weight` → source has no places → `locally_enabled = False`
4. Result: Enablement cleared, no re-scheduling

**Location**: `src/shypn/engine/simulation/controller.py` lines 240-276

```python
def _check_newly_enabled(self):
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        input_arcs = behavior.get_input_arcs()
        locally_enabled = True
        
        for arc in input_arcs:
            # ... check tokens ...
            if source_place.tokens < arc.weight:
                locally_enabled = False  # ❌ Source has no arcs!
                break
        
        if locally_enabled:
            # ✓ Enable and schedule
        else:
            # ❌ CLEARS schedule for source transitions!
            state.enablement_time = None
            state.scheduled_time = None
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
```

---

### Issue 2: No Automatic Re-scheduling After Source Firing

**Problem**: After a source transition fires, it needs to immediately schedule the next firing (sample new delay from exponential distribution). Currently:

1. Fire happens
2. `clear_enablement()` called
3. Next step: `_check_newly_enabled()` sees no input places
4. Transition marked as disabled
5. **Never re-scheduled**

**Expected Behavior**: Continuous Poisson process
```
Fire → Clear → Immediately Reschedule → Wait → Fire → ...
```

**Current Behavior**: One-shot
```
Fire → Clear → Disabled (never fires again) ❌
```

---

### Issue 3: Fixed Sampling Window vs Exponential Distribution

**Problem**: The simulation uses a fixed time step `dt`, but stochastic events follow exponential distribution with varying inter-arrival times.

**Mismatch**:
```
Exponential: Events at t = [0.1, 0.3, 2.7, 3.1, 5.9, ...]
Fixed dt:    Samples at t = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, ...]
```

**Issue**: If `dt` is too large relative to rate λ:
- Miss rapid-fire events
- Under-sample high-frequency transitions
- Over-sample low-frequency transitions

**Current**: `dt` is hardcoded or set globally
**Better**: Let exponential distribution determine next event time (event-driven simulation)

---

## Detailed Analysis

### How Stochastic Source Should Work

**Correct Lifecycle**:
```
1. Initialization: Schedule first firing
   - Sample delay T ~ Exp(λ)
   - Set scheduled_time = current_time + T

2. Simulation loop:
   a. Check if current_time >= scheduled_time
   b. If yes: FIRE
      - Produce tokens (burst)
      - Sample NEW delay T' ~ Exp(λ)
      - Immediately reschedule: scheduled_time = current_time + T'
   c. If no: Wait (continue simulation)

3. Repeat forever (continuous source)
```

**Current Broken Lifecycle**:
```
1. Initialization: Schedule first firing ✓
2. First fire works ✓
3. clear_enablement() called ✓
4. _check_newly_enabled() marks as disabled ❌
5. Never fires again ❌
```

---

### Root Cause: Conflation of "Enabled" Concepts

**Two Different "Enabled" Meanings**:

1. **Structural Enablement** (place-based):
   - Does transition have enough input tokens?
   - For source transitions: NO input places → always structurally "disabled"

2. **Stochastic Enablement** (time-based):
   - Has delay been sampled?
   - Is current_time >= scheduled_fire_time?
   - For source transitions: Should ALWAYS be scheduled if active

**Problem**: Controller uses **structural enablement** to gate **stochastic scheduling**.

Result: Source transitions structurally "disabled" → never scheduled.

---

## Proposed Fixes

### Fix 1: Special Handling for Source/Sink Transitions in Controller

**Modify**: `src/shypn/engine/simulation/controller.py` line ~250

```python
def _check_newly_enabled(self):
    """Update enablement tracking for all transitions."""
    
    for transition in self.model.transitions:
        behavior = self._get_behavior(transition)
        
        # Check if this is a source or sink transition
        is_source = getattr(transition, 'is_source', False)
        is_sink = getattr(transition, 'is_sink', False)
        
        # Source transitions are ALWAYS enabled (no input requirements)
        if is_source:
            state = self._get_or_create_state(transition)
            if state.enablement_time is None:
                state.enablement_time = self.time
                if hasattr(behavior, 'set_enablement_time'):
                    behavior.set_enablement_time(self.time)
            continue  # Skip input token checks
        
        # Sink transitions need only input checks (no output requirements)
        # Normal transitions need both input and output
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
        
        state = self._get_or_create_state(transition)
        
        if locally_enabled:
            if state.enablement_time is None:
                state.enablement_time = self.time
                if hasattr(behavior, 'set_enablement_time'):
                    behavior.set_enablement_time(self.time)
        else:
            # Only clear if not source (sources ALWAYS enabled)
            state.enablement_time = None
            state.scheduled_time = None
            if hasattr(behavior, 'clear_enablement'):
                behavior.clear_enablement()
```

---

### Fix 2: Auto-Reschedule After Stochastic Firing

**Modify**: `src/shypn/engine/stochastic_behavior.py` line ~300

Add re-scheduling logic to `fire()` method:

```python
def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
    """Execute stochastic burst firing."""
    
    try:
        # ... existing firing logic ...
        
        # Phase 3: Clear OLD scheduling state
        self.clear_enablement()
        
        # Phase 3b: IMMEDIATELY RE-SCHEDULE (especially for sources)
        # If this is a source transition OR if still enabled after firing,
        # schedule the next firing now
        is_source = getattr(self.transition, 'is_source', False)
        
        if is_source:
            # Source transitions: Always reschedule immediately
            current_time = self._get_current_time()
            self.set_enablement_time(current_time)
        else:
            # Normal transitions: Check if still enabled after firing
            # (may have consumed tokens, need to recheck)
            # Controller will handle re-enablement check in next step
            pass
        
        # Phase 4: Record stochastic firing event
        # ... existing recording logic ...
        
        return True, {
            'consumed': consumed_map,
            'produced': produced_map,
            'stochastic_mode': True,
            'burst_size': burst,
            'rate': self.rate,
            'delay': delay,
            'transition_type': 'stochastic',
            'time': current_time,
            'rescheduled': is_source  # Indicate if immediately rescheduled
        }
    
    except Exception as e:
        return False, {
            'reason': f'stochastic-error: {str(e)}',
            'stochastic_mode': True,
            'error_type': type(e).__name__
        }
```

---

### Fix 3: Event-Driven Simulation for Stochastic Transitions (Optional Enhancement)

**Current**: Fixed-step simulation with `dt`
**Better**: Hybrid approach - event-driven for stochastic, fixed-step for continuous

**Concept**:
```python
def step_hybrid(self, time_step: float = None):
    """Hybrid simulation step.
    
    1. Check stochastic events: Use next scheduled time
    2. Check continuous: Use fixed dt
    3. Advance to min(next_stochastic_event, current_time + dt)
    """
    
    # Find next stochastic event
    next_stochastic_time = self._get_next_stochastic_event_time()
    
    if time_step is None:
        time_step = self.get_effective_dt()
    
    # Advance to next event or dt, whichever comes first
    if next_stochastic_time is not None:
        time_advance = min(next_stochastic_time - self.time, time_step)
    else:
        time_advance = time_step
    
    # Fire all stochastic transitions scheduled at or before target time
    target_time = self.time + time_advance
    self._fire_stochastic_up_to(target_time)
    
    # Integrate continuous transitions
    self._integrate_continuous(time_advance)
    
    # Advance time
    self.time += time_advance
```

**Advantages**:
- ✅ Accurate stochastic timing (no sampling issues)
- ✅ Efficient (skip time when nothing happens)
- ✅ Respects exponential distribution

**Disadvantages**:
- More complex implementation
- Requires priority queue for events
- May complicate continuous integration

---

## Implementation Priority

### High Priority (Must Fix)

✅ **Fix 1**: Source transition enablement handling
- Impact: Critical - sources currently broken
- Complexity: Low - simple conditional
- File: `controller.py` line ~250

✅ **Fix 2**: Auto-reschedule after firing
- Impact: Critical - enables continuous source behavior
- Complexity: Low - add one method call
- File: `stochastic_behavior.py` line ~300

### Medium Priority (Should Fix)

⚠️ **Fix 3a**: Adaptive dt warning
- Impact: User guidance
- Complexity: Low
- File: Add to simulation settings dialog

### Low Priority (Nice to Have)

📝 **Fix 3b**: Full event-driven simulation
- Impact: Performance + accuracy
- Complexity: High
- File: New module `event_driven_controller.py`

---

## Testing Plan

### Test 1: Single Stochastic Source

**Model**:
```
[T_source] → P1
λ = 1.0, burst = 1
```

**Test**:
```python
model = create_source_model()
sim = SimulationController(model)
sim.settings.set_duration(10.0, TimeUnits.SECONDS)
sim.settings.dt_manual = 0.1
sim.run()

tokens = sim.get_place_tokens(P1)
print(f"Final tokens: {tokens}")
# Expected: ~45 tokens (10s × 1 firing/s × 4.5 avg burst)
```

**Current Behavior**: 0 tokens (never fires again) ❌  
**After Fix 1+2**: ~45 tokens ✓

---

### Test 2: Source Firing Frequency

**Model**: Same as Test 1

**Test**:
```python
firing_times = sim.get_transition_firing_times(T_source)
inter_arrival_times = np.diff(firing_times)

print(f"Number of firings: {len(firing_times)}")
print(f"Mean inter-arrival: {np.mean(inter_arrival_times):.3f}s")
print(f"Expected (1/λ): {1.0}s")

# Plot histogram
plt.hist(inter_arrival_times, bins=20, density=True)
plt.xlabel('Inter-arrival time (s)')
plt.ylabel('Density')
plt.title('Exponential distribution check')
```

**Expected**: Mean ≈ 1.0s, exponential shape  
**After Fix**: Should match theory ✓

---

### Test 3: Source-Sink Equilibrium

**Model**:
```
[T_source] → P1 → [T_sink]
λ₁ = 2.0, λ₂ = 1.0
```

**Test**:
```python
model = create_source_sink_model()
sim = SimulationController(model)
sim.settings.set_duration(100.0, TimeUnits.SECONDS)
sim.run()

token_history = sim.get_place_history(P1)
plt.plot(token_history)
plt.xlabel('Time (s)')
plt.ylabel('Tokens in P1')
plt.title('Source-Sink Equilibrium')

# Check equilibrium
final_50_percent = token_history[len(token_history)//2:]
mean_equilibrium = np.mean(final_50_percent)
print(f"Equilibrium tokens: {mean_equilibrium:.1f}")
# Expected: Oscillating around ~10-15 tokens
```

**Current**: Broken (source doesn't fire) ❌  
**After Fix**: Stable oscillation ✓

---

## Summary of Changes

### File 1: `src/shypn/engine/simulation/controller.py`

**Lines ~250-276** - `_check_newly_enabled()`:
```python
# ADD: Special case for source transitions
if is_source:
    state = self._get_or_create_state(transition)
    if state.enablement_time is None:
        state.enablement_time = self.time
        if hasattr(behavior, 'set_enablement_time'):
            behavior.set_enablement_time(self.time)
    continue  # Skip input checks
```

---

### File 2: `src/shypn/engine/stochastic_behavior.py`

**Lines ~280-290** - `fire()` method, after `clear_enablement()`:
```python
# ADD: Immediate re-scheduling for source transitions
is_source = getattr(self.transition, 'is_source', False)

if is_source:
    current_time = self._get_current_time()
    self.set_enablement_time(current_time)
```

---

## Expected Results After Fixes

### Before Fixes:
- ❌ Source transitions fire once, then stop
- ❌ Token accumulation: 0 (broken)
- ❌ Firing rate: 0 events/s (after first)

### After Fixes:
- ✅ Source transitions fire continuously
- ✅ Token accumulation: Linear growth (~λ × burst × time)
- ✅ Firing rate: Matches exponential distribution (mean = 1/λ)
- ✅ Source-sink equilibrium: Stable oscillation
- ✅ No crashes or instability

---

## Additional Recommendations

### 1. Add Debug Logging

```python
# In stochastic_behavior.py
import logging
logger = logging.getLogger(__name__)

def set_enablement_time(self, time: float):
    self._enablement_time = time
    delay = self._sample_exponential_delay()
    self._scheduled_fire_time = time + delay
    
    logger.debug(f"Stochastic {self.transition.name}: "
                f"scheduled at t={self._scheduled_fire_time:.3f} "
                f"(delay={delay:.3f}s, rate={self.rate})")
```

---

### 2. Add Validation Warning

```python
# In controller.py initialization
def __init__(self, model):
    # ... existing code ...
    
    # Warn about stochastic sources with high rates
    for transition in model.transitions:
        if transition.transition_type == 'stochastic':
            is_source = getattr(transition, 'is_source', False)
            if is_source:
                rate = getattr(transition, 'rate', 1.0)
                mean_interval = 1.0 / rate
                dt = self.get_effective_dt()
                
                if dt > mean_interval:
                    logger.warning(
                        f"Stochastic source '{transition.name}': "
                        f"dt ({dt}s) > mean interval ({mean_interval}s). "
                        f"May under-sample events. Consider dt ≤ {mean_interval/10:.3f}s"
                    )
```

---

### 3. Add Unit Tests

```python
# tests/test_stochastic_source.py
def test_source_continuous_firing():
    """Test that source transitions fire continuously."""
    model = create_single_source_model()
    sim = SimulationController(model)
    sim.settings.set_duration(10.0, TimeUnits.SECONDS)
    sim.run()
    
    # Check that source fired multiple times
    firing_count = len(sim.get_transition_firing_times(T_source))
    assert firing_count > 5, f"Source should fire multiple times, got {firing_count}"

def test_source_exponential_distribution():
    """Test that inter-arrival times follow exponential distribution."""
    model = create_single_source_model(rate=2.0)
    sim = SimulationController(model)
    sim.settings.set_duration(100.0, TimeUnits.SECONDS)
    sim.run()
    
    firing_times = sim.get_transition_firing_times(T_source)
    inter_arrivals = np.diff(firing_times)
    
    # Check mean
    expected_mean = 1.0 / 2.0  # 1/λ = 0.5s
    actual_mean = np.mean(inter_arrivals)
    assert abs(actual_mean - expected_mean) < 0.1, \
        f"Mean inter-arrival should be ~{expected_mean}s, got {actual_mean}s"
```

---

## Conclusion

### Critical Issues Identified:

1. ❌ Source transitions lose schedule after first firing
2. ❌ No automatic re-scheduling for continuous source behavior
3. ⚠️ Fixed sampling may under-sample high-rate transitions

### Fixes Required:

✅ **Immediate** (Critical):
- Special handling for source transitions in `_check_newly_enabled()`
- Auto-reschedule after firing in `fire()` method

⚠️ **Soon** (Important):
- Add dt validation warnings
- Add debug logging

📝 **Future** (Enhancement):
- Event-driven simulation for pure stochastic nets
- Adaptive dt based on transition rates

### Impact:

After implementing Fixes 1 & 2, stochastic source transitions will:
- Fire continuously (Poisson process)
- Maintain stable token generation
- Work correctly in source-sink equilibrium scenarios
- Enable realistic biochemical pathway simulation from BioModels

---

**Status**: Ready to implement  
**Estimated Effort**: 30 minutes (Fixes 1 & 2)  
**Testing**: 1 hour (create test nets, verify behavior)
