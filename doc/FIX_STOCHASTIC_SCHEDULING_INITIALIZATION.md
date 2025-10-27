# Fix: Time-Dependent Transition Scheduling on Controller Creation

## Problem
When loading SBML models from .shy files, stochastic and timed transitions did not fire, while immediate and continuous transitions worked correctly.

## Root Cause
The SimulationController only called `_update_enablement_states()` inside the `step()` method, meaning:
- When controller was first created (e.g., loading a file), transitions were NOT scheduled
- Stochastic transitions require `behavior.set_enablement_time()` to be called to:
  * Sample exponential delay from rate parameter
  * Set `_scheduled_fire_time` for the transition
- Without scheduling, `behavior.can_fire()` returns `False, "not-scheduled"`

## Solution
Added `_update_enablement_states()` calls in two places:

### 1. SimulationController.__init__() (line 157-160)
```python
# Initialize enablement states for time-dependent transitions (timed/stochastic)
# This ensures transitions are properly scheduled when controller is first created
self._update_enablement_states()
```

**Effect**: When loading a model, any transitions with sufficient tokens are immediately scheduled

### 2. SimulationController.reset() (line 1656-1657)
```python
# Schedule time-dependent transitions (timed/stochastic) after reset
self._update_enablement_states()
```

**Effect**: When resetting simulation, transitions are rescheduled based on initial markings

## Why This Was Missed
- Interactive model creation: Users typically start simulation immediately after creating transitions
- First `step()` call would schedule transitions, so issue wasn't noticeable
- Loaded models: Controller created when file opens, but user might not run simulation immediately
- Without scheduling, transitions appear "broken" when simulation starts

## Testing
To verify the fix works:
1. Load BIOMD0000000001.shy (17 stochastic transitions)
2. Mark one transition as source (to provide tokens)
3. Run simulation
4. Stochastic transitions should now fire correctly

## Files Changed
- `src/shypn/engine/simulation/controller.py`: Added 2 `_update_enablement_states()` calls

## Commit
- Hash: 35ffcd7
- Message: "Fix: Initialize time-dependent transition scheduling on controller creation"
