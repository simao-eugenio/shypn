# Phase 5: Timed Transitions - Investigation Report

**Status**: Implementation Gap Identified 🔍  
**Date**: 2025-01-28  
**Test Results**: 4/10 passing (40%) - Limited by implementation issue

## Executive Summary

Phase 5 investigation revealed a **critical implementation gap** in how the SimulationController handles timed transitions. Timed transitions that enter their firing window mid-step do not fire because enablement is checked BEFORE time advances, creating a timing mismatch.

## Tests Created (10 tests)

1. ✅ `test_does_not_fire_before_earliest` - PASS
2. ❌ `test_fires_after_earliest_delay` - FAIL
3. ❌ `test_fires_within_window` - FAIL
4. ❌ `test_must_fire_before_latest` - FAIL
5. ✅ `test_zero_earliest_fires_immediately` - PASS
6. ❌ `test_infinite_latest_no_upper_bound` - FAIL
7. ❌ `test_enablement_time_tracking` - FAIL
8. ✅ `test_timing_window_properties` - PASS
9. ❌ `test_multiple_firings_same_transition` - FAIL
10. ✅ `test_disabled_by_insufficient_tokens` - PASS

**Result**: 4/10 passing (40%)

## Critical Finding: Timing Mismatch Issue

### The Problem

**Timed transitions are checked BEFORE time advances, causing missed firing opportunities.**

#### Example Scenario
```python
# Given: Transition T with earliest=0.8, latest=1.2
# Initial: t=0, P0 has 1 token, enablement_time=0

# Step 1: step(0.5)
controller.step(time_step=0.5)
# 1. Check T at t=0: elapsed=0 < 0.8 → TOO EARLY ❌
# 2. Time advances to t=0.5
# Result: No firing, time=0.5

# Step 2: step(0.5)
controller.step(time_step=0.5)
# 1. Check T at t=0.5: elapsed=0.5 < 0.8 → STILL TOO EARLY ❌
# 2. Time advances to t=1.0
# Result: No firing, time=1.0 (but T should have fired!)

# PROBLEM: At t=1.0, T is IN WINDOW [0.8, 1.2]
# But the check happened at t=0.5 (before advance)
```

### Root Cause Analysis

#### Controller Step Sequence (Simplified)
```python
def step(self, time_step):
    # 1. Update enablement states AT CURRENT TIME
    self._update_enablement_states()
    
    # 2. Handle immediate transitions (exhaust)
    # ... immediate loop ...
    
    # 3. Check discrete (timed/stochastic) AT CURRENT TIME
    discrete_transitions = [t for t in self.model.transitions 
                           if t.transition_type in ['timed', 'stochastic']]
    enabled_discrete = [t for t in discrete_transitions 
                       if self._is_transition_enabled(t)]  # ← CHECK HERE
    
    if enabled_discrete:
        transition = self._select_transition(enabled_discrete)
        self._fire_transition(transition)  # ← FIRE AT CURRENT TIME
    
    # 4. Advance time
    self.time += time_step  # ← TIME MOVES FORWARD
```

**The Issue**: Step 3 checks enablement at `time=t`, but the transition might only enter its window at `time=t+dt`.

### Window Crossing Logic (Partial Solution)

The controller has "window crossing" detection (lines 448-527):

```python
will_cross = (elapsed_now < behavior.earliest and 
             elapsed_after > behavior.latest)
```

**Problem**: This only catches windows that are COMPLETELY SKIPPED:
- `elapsed_now < earliest` (before window starts)
- `elapsed_after > latest` (after window ends)

**Example**:
- Window [0.8, 1.2], step from t=0.5 to t=1.0
- elapsed_now = 0.5 < 0.8 ✓
- elapsed_after = 1.0 > 1.2 ✗ (not crossed!)
- Result: **NOT detected as window crossing**

### Why Some Tests Pass

#### ✅ test_zero_earliest_fires_immediately
- Window: [0.0, 1.0]
- At t=0: elapsed=0 >= 0.0 → IN WINDOW immediately
- Fires on first step ✅

#### ✅ test_does_not_fire_before_earliest
- Window: [2.0, 3.0]
- At t=1.5: elapsed=1.5 < 2.0 → correctly TOO EARLY
- Expected behavior: don't fire ✅

#### ✅ test_disabled_by_insufficient_tokens
- No tokens in P0
- Transition never enabled (structural constraint)
- Expected behavior: don't fire ✅

## Implementation Analysis

### Current Timed Behavior (`timed_behavior.py`)

The `TimedBehavior` class correctly implements:
- ✅ Timing windows `[earliest, latest]`
- ✅ Enablement time tracking
- ✅ Window crossing detection (in `can_fire()`)
- ✅ Token consumption/production
- ✅ Guard evaluation

**The behavior is correct** - the issue is in the controller's scheduling.

### Controller Gaps (`controller.py`)

**Missing**: Proper handling of timed transitions entering their window mid-step.

**Needed Solutions**:
1. **Check enablement at END of step** (after time advance)
2. **Interpolate firing time** within step for transitions entering window
3. **Queue timed firings** with scheduled times
4. **Enhanced window crossing** to catch partial overlaps

## Proposed Solutions

### Option 1: Post-Step Enablement Check (Simplest)
```python
def step(self, time_step):
    # ... handle immediate ...
    
    # Advance time FIRST
    self.time += time_step
    
    # THEN check discrete transitions at NEW time
    self._update_enablement_states()
    discrete_transitions = [t for t in self.model.transitions 
                           if t.transition_type in ['timed', 'stochastic']]
    enabled_discrete = [t for t in discrete_transitions 
                       if self._is_transition_enabled(t)]
    
    if enabled_discrete:
        transition = self._select_transition(enabled_discrete)
        self._fire_transition(transition)
```

**Pros**: Simple, minimal changes  
**Cons**: Still only fires ONE timed transition per step

### Option 2: Window Intersection Detection (Better)
```python
def _transitions_entering_window(self, time_step):
    """Find transitions whose firing windows intersect with [t, t+dt]."""
    entering = []
    for t in self.model.transitions:
        if t.transition_type != 'timed':
            continue
        
        behavior = self._get_behavior(t)
        if behavior._enablement_time is None:
            continue
        
        # Window: [t_enable + earliest, t_enable + latest]
        window_start = behavior._enablement_time + behavior.earliest
        window_end = behavior._enablement_time + behavior.latest
        
        # Step interval: [current_time, current_time + time_step]
        step_start = self.time
        step_end = self.time + time_step
        
        # Check intersection
        if window_start <= step_end and window_end >= step_start:
            entering.append(t)
    
    return entering
```

**Pros**: Catches all window interactions  
**Cons**: More complex logic

### Option 3: Event Queue (Most Robust)
```python
class TimedEvent:
    def __init__(self, time, transition):
        self.time = time
        self.transition = transition

def _schedule_timed_transitions(self):
    """Schedule timed transitions at their earliest firing time."""
    for t in self.model.transitions:
        if t.transition_type != 'timed':
            continue
        
        behavior = self._get_behavior(t)
        if behavior._enablement_time is not None:
            fire_time = behavior._enablement_time + behavior.earliest
            self.event_queue.schedule(TimedEvent(fire_time, t))
```

**Pros**: Most accurate, handles multiple timed transitions  
**Cons**: Significant refactoring required

## Test Results Analysis

### Passing Tests (4/10)

| Test | Why It Passes |
|------|---------------|
| `test_does_not_fire_before_earliest` | Correctly stays disabled before window |
| `test_zero_earliest_fires_immediately` | Window starts at t=0 (immediately enabled) |
| `test_timing_window_properties` | Just checks property values (no firing) |
| `test_disabled_by_insufficient_tokens` | Structural constraint (no tokens) |

### Failing Tests (6/10)

| Test | Why It Fails |
|------|--------------|
| `test_fires_after_earliest_delay` | Window [0.8, 1.2] entered mid-step |
| `test_fires_within_window` | Same issue |
| `test_must_fire_before_latest` | Same issue |
| `test_infinite_latest_no_upper_bound` | Window [1.0, ∞] entered mid-step |
| `test_enablement_time_tracking` | Depends on firing (which doesn't happen) |
| `test_multiple_firings_same_transition` | First firing never happens |

## Debugging Evidence

### Manual Firing Test
```python
# After step to t=1.0 (window [0.8, 1.2])
behavior = controller._get_behavior(T)
can_fire, reason = behavior.can_fire()
print(f"Can fire: {can_fire}, reason: {reason}")
# Output: Can fire: True, reason: enabled-in-window (elapsed=1.000)

# But automatic firing didn't happen!
print(f"P0={P0.tokens}, P1={P1.tokens}")
# Output: P0=1, P1=0  (token didn't move)

# Manual fire WORKS:
success, details = behavior.fire(input_arcs, output_arcs)
print(f"Success: {success}")
# Output: Success: True

print(f"P0={P0.tokens}, P1={P1.tokens}")
# Output: P0=0, P1=1  (token moved!)
```

**Conclusion**: The behavior is correct, but the controller doesn't call `fire()` at the right time.

## Recommendations

### Immediate Actions
1. ✅ **Document the issue** (this file)
2. **File bug report** or feature request
3. **Propose Solution Option 1** (simplest fix)

### Testing Strategy
1. **Focus on immediate transitions** (already complete - 47/47 passing)
2. **Document timed transition limitations**
3. **Create workaround tests** (if possible)
4. **Wait for controller fix** before full timed validation

### Future Work
- Implement Solution Option 2 or 3
- Add comprehensive timed transition tests (15-20 tests)
- Validate stochastic transitions (similar timing issues expected)
- Test timed + immediate interaction
- Test multiple concurrent timed transitions

## Files Created

### Test Infrastructure
- `/tests/validation/timed/conftest.py` - Fixtures for timed tests
- `/tests/validation/timed/test_basic_timing.py` - 10 basic timing tests
- `/tests/validation/timed/__init__.py` - Module initialization

### Documentation
- `/doc/validation/timed/TIMED_PHASE5_INVESTIGATION.md` - This file

## Impact on Overall Validation

### Completed
- ✅ **Phase 1**: Immediate basic firing (6/6)
- ✅ **Phase 2**: Immediate arc weights (9/9)
- ✅ **Phase 3**: Immediate guards (17/17) + Bug fix
- ✅ **Phase 4**: Immediate priorities (15/15)
- **Total Immediate**: 47/47 tests passing (100%)

### Blocked
- 🔍 **Phase 5**: Timed transitions (4/10 - 40%)
  - Blocked by controller implementation gap
  - Requires fix in `SimulationController.step()`
  
- ⏸️ **Phase 6**: Stochastic transitions (not started)
  - Likely similar timing issues
  - Depends on Phase 5 resolution

### Coverage Impact
- Current: 31% engine modules
- Blocked potential: +15-20% (timed_behavior.py, stochastic_behavior.py)
- Achievable with fix: ~50% engine coverage

## Conclusion

Phase 5 investigation successfully identified a **critical implementation gap** in timed transition handling. The `TimedBehavior` class is correctly implemented, but the `SimulationController` doesn't properly handle transitions entering their firing window mid-step.

**Key Finding**: Enablement checks happen BEFORE time advances, causing timed transitions to be evaluated at the wrong time.

**Recommendation**: Implement Solution Option 1 (post-step enablement check) as the quickest path to functional timed transition support.

**Current Status**: Documented issue, created test infrastructure, ready to validate once controller is fixed.

**Next Steps**: Return to immediate transition validation summary, document overall progress, and await controller fix for timed/stochastic validation.
