# Timed Transition Floating-Point Precision Fix

## Issue Summary
Timed transitions were not firing at their expected timing windows due to floating-point precision errors in time comparisons.

## Problem Description

### Symptoms
- Timed transition with `earliest=1.0, latest=1.0` would not fire
- Debug output showed: `elapsed=0.9999999999999999, earliest=1.0`
- Transition was blocked as "too-early" even though time appeared to be exactly 1.0
- Simulation would detect deadlock immediately after the transition should have fired

### Root Cause
The simulation uses discrete time steps of `0.1` seconds. When the simulation advances time:
```python
self.time += 0.1  # repeated 10 times
```

Due to binary floating-point representation, adding `0.1` ten times does **not** equal exactly `1.0`:
```
0.1 + 0.1 + 0.1 + 0.1 + 0.1 + 0.1 + 0.1 + 0.1 + 0.1 + 0.1 = 0.9999999999999999
```

This caused the timing check `elapsed < earliest` to incorrectly evaluate to `True` when it should have been `False`.

### Code Location
File: `src/shypn/engine/timed_behavior.py`
Method: `can_fire()`

Original problematic code:
```python
if elapsed < self.earliest:
    return False, "too-early"
```

## Solution

### Floating-Point Tolerance
Introduced an epsilon value for floating-point comparisons:

```python
EPSILON = 1e-9  # Tolerance for floating-point comparisons

# Check earliest constraint with tolerance
if elapsed + EPSILON < self.earliest:
    return False, f"too-early (elapsed={elapsed:.3f}, earliest={self.earliest})"

# Check latest constraint with tolerance  
if elapsed > self.latest + EPSILON:
    return False, f"too-late (elapsed={elapsed:.3f}, latest={self.latest})"
```

### How It Works
- **Earliest check**: `elapsed + EPSILON < earliest`
  - When `elapsed = 0.9999999999999999` and `earliest = 1.0`
  - `0.9999999999999999 + 0.000000001 = 1.000000001` which is NOT `< 1.0`
  - Transition can fire ✓

- **Latest check**: `elapsed > latest + EPSILON`
  - When `elapsed = 1.0000000000000001` and `latest = 1.0`
  - `1.0000000000000001 > 1.000000001` is `False`
  - Transition still within window ✓

### Epsilon Value Selection
`EPSILON = 1e-9` (one nanosecond) was chosen because:
- Small enough to be negligible for simulation purposes
- Large enough to handle typical floating-point precision errors
- Much smaller than the simulation time step (0.1 seconds)

## Related Fixes

### 1. Simulation Deadlock Detection (controller.py)
Fixed premature deadlock detection when timed transitions are waiting:
```python
# Check if any timed/stochastic transitions are waiting
for transition in discrete_transitions:
    behavior = self._get_behavior(transition)
    can_fire, reason = behavior.can_fire()
    
    if not can_fire and reason and 'too-early' in str(reason):
        return True  # Keep simulation running, transition is waiting
```

### 2. Matplotlib Legend Warnings (plot_panel.py)
Fixed "No artists with labels" warnings when plotting before data is available:
```python
if self.show_legend and self.selected_objects:
    handles, labels = self.axes.get_legend_handles_labels()
    if handles:  # Only show legend if there are labeled artists
        self.axes.legend(loc='best', fontsize=9)
```

## Testing

### Test Case
1. Create a simple Petri net with one timed transition (delay = 1.0 seconds)
2. Add initial tokens to input place
3. Run simulation with time step = 0.1 seconds
4. **Expected**: Transition fires at t ≈ 1.0 seconds (10th step)
5. **Actual**: Transition now fires correctly at the 10th step ✓

### Verification
Console output shows:
```
[TimedBehavior] T1: current_time=1.000, enablement_time=0.000, elapsed=1.000, earliest=1.0, latest=1.0
[Controller] Step at t=1.000:
  - T1 (type=timed): CAN FIRE
  >>> FIRED: T1
```

## Best Practices for Future Development

### 1. Always Use Tolerance for Floating-Point Time Comparisons
```python
# Bad
if time == target_time:
    ...

# Good
EPSILON = 1e-9
if abs(time - target_time) < EPSILON:
    ...
```

### 2. Consider Integer Time Steps
For more precise timing, consider using integer time steps internally:
```python
# Store time as integer milliseconds
self.time_ms = 0
self.time_ms += 100  # 0.1 second = 100 milliseconds

# Convert to float for display
display_time = self.time_ms / 1000.0
```

### 3. Document Precision Assumptions
When defining timing properties, document the expected precision:
```python
# Timing windows support precision down to ~1 nanosecond (1e-9 seconds)
# Values closer than EPSILON (1e-9) are considered equal
```

## Performance Impact
- **Negligible**: Adding epsilon to comparisons has no measurable performance impact
- **Correctness**: Critical for proper timed transition behavior
- **Stability**: Prevents simulation from incorrectly detecting deadlock

## Conclusion
This fix resolves the floating-point precision issue that prevented timed transitions from firing at their specified times. The epsilon-based comparison ensures that timing windows work correctly even with cumulative floating-point errors from discrete time steps.

---

**Date**: 2025-10-05  
**Status**: ✅ Resolved  
**Files Modified**:
- `src/shypn/engine/timed_behavior.py` (timing comparisons)
- `src/shypn/engine/simulation/controller.py` (deadlock detection)
- `src/shypn/analyses/plot_panel.py` (legend warnings)
