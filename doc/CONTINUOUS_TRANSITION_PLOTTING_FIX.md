# Continuous Transition Plotting Fix

## Problem Statement

Continuous type transitions were not appearing in the transition rate analysis plots. When users added continuous transitions to the analysis panel and ran the simulation, no data was plotted.

## Root Cause Analysis

### Simulation Architecture

The `SimulationController.step()` method uses a hybrid execution model with two phases:

**Phase 2: Discrete Transitions (immediate, timed, stochastic)**
```python
if enabled_discrete:
    transition = self._select_transition(enabled_discrete)
    self._fire_transition(transition)  # ← Data collector notified here
    discrete_fired = True
```

**Phase 3: Continuous Transitions**
```python
for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
    success, details = behavior.integrate_step(dt, input_arcs, output_arcs)
    if success:
        continuous_active += 1
    # ← Data collector was NOT notified here!
```

### The Issue

- **Discrete transitions** call `_fire_transition()` which contains:
  ```python
  if self.data_collector is not None:
      self.data_collector.on_transition_fired(transition, self.time)
  ```

- **Continuous transitions** call `integrate_step()` directly and never triggered data collector notification

- **Result**: `SimulationDataCollector.transition_data` never received events for continuous transitions, so `RateCalculator` had no firing times to work with

## Solution

Added data collector notification for continuous transitions after successful integration:

**File**: `src/shypn/engine/simulation/controller.py`

```python
# === PHASE 3: CONTINUOUS TRANSITIONS (integrate all pre-identified) ===
continuous_active = 0
for transition, behavior, input_arcs, output_arcs in continuous_to_integrate:
    success, details = behavior.integrate_step(
        dt=time_step,
        input_arcs=input_arcs,
        output_arcs=output_arcs
    )
    
    if success:
        continuous_active += 1
        
        # NEW: Notify data collector about continuous transition activity
        if self.data_collector is not None:
            self.data_collector.on_transition_fired(transition, self.time, details)
```

## Technic al Details

### Why Pass `details`?

Continuous transitions return integration details including:
```python
{
    'consumed': {place_id: amount, ...},
    'produced': {place_id: amount, ...},
    'continuous_mode': True,
    'rate': float,
    'dt': float,
    'method': 'rk4'
}
```

Passing `details` to `on_transition_fired()` allows the data collector to potentially track:
- Continuous flow rates
- Integration method
- Consumed/produced amounts per step

Currently, `on_transition_fired()` uses `details` as the optional third parameter, which is stored in the transition data tuple: `(time, 'fired', details)`.

### Data Flow After Fix

```
SimulationController.step()
    ↓
Phase 3: Continuous Integration
    ↓
behavior.integrate_step(dt, ...) → success=True
    ↓
data_collector.on_transition_fired(transition, time, details)
    ↓
transition_data[transition_id].append((time, 'fired', details))
    ↓
TransitionRatePanel → RateCalculator
    ↓
calculate_firing_rate(event_times, current_time, window)
    ↓
Plot shows continuous transition activity! ✓
```

## Testing

### Test Scenario: Continuous Transition Plotting

1. Create a Petri net with a continuous transition
2. Set transition type to 'continuous'
3. Set rate function (e.g., `2.0` or `1.5 * P1`)
4. Add transition to analysis panel via "Add to Analysis"
5. Run simulation
6. **Expected Result**: Plot shows continuous transition firing events over time

### Before Fix
- Continuous transitions: **No data in plot** (empty)
- Console: No errors, but `transition_data[continuous_id]` was empty

### After Fix
- Continuous transitions: **Data appears in plot** showing activity
- `transition_data[continuous_id]` contains integration events
- Rate calculations work correctly

## Implementation Notes

### Why Every Integration Step?

Continuous transitions integrate at every simulation step (`time_step` interval). Each successful integration represents a "firing event" in the sense that tokens are flowing. By recording every integration, we get:

- **Fine-grained rate data**: Integration happens every `dt` (e.g., 0.1s)
- **Accurate flow tracking**: Each integration event represents actual token movement
- **Consistent with discrete**: Discrete transitions record each firing, continuous records each integration

### Performance Considerations

- Integration typically happens at the simulation time step rate (10 Hz @ 0.1s steps)
- Data collector has automatic downsampling (threshold: 8000 points)
- Continuous transitions generate more data than discrete (every step vs. sporadic)
- Memory usage: Acceptable for typical simulations (< 10,000 steps)

### Alternative Approaches Considered

1. **Separate method** (`on_continuous_integration`): More explicit but adds API complexity
2. **Aggregate events**: Only record periodically (e.g., every 10 steps) - loses granularity
3. **Use existing `on_transition_fired()`**: ✅ Chosen - reuses existing infrastructure

## Behavioral Differences

### Discrete vs. Continuous Events

**Discrete Transitions** (immediate, timed, stochastic):
- Fire sporadically based on enablement
- Each firing is a discrete event in time
- Event times: `[0.1, 0.3, 0.8, 1.2, ...]` (irregular intervals)

**Continuous Transitions**:
- Integrate at every simulation step
- Events occur regularly at `time_step` intervals
- Event times: `[0.1, 0.2, 0.3, 0.4, ...]` (regular intervals)

**Rate Calculation**:
Both use the same `RateCalculator.calculate_firing_rate()`:
```python
rate = count_of_events_in_window / time_window
```

For continuous transitions with regular integration:
- Time window = 1.0s, step = 0.1s → rate ≈ 10 events/s (constant)
- Rate represents **integration frequency**, not token flow rate
- For token flow rate, use the place rate analysis instead

## Related Files

- `src/shypn/engine/simulation/controller.py` - Added continuous data collection
- `src/shypn/analyses/data_collector.py` - Receives transition events
- `src/shypn/analyses/rate_calculator.py` - Calculates firing rates from events
- `src/shypn/analyses/transition_rate_panel.py` - Displays transition rates

## Future Enhancements

1. **Separate Continuous Rate Tracking**: Track actual flow rate from integration details
2. **Event Type Differentiation**: Use different event types ('integrated' vs 'fired')
3. **Continuous-Specific Plots**: Show flow rate instead of integration frequency
4. **Adaptive Sampling**: Downsample continuous events more aggressively

## Commit

**Title:** Fix continuous transition plotting by adding data collector notification

**Description:**
- Add data_collector.on_transition_fired() call after successful continuous integration
- Continuous transitions now tracked in transition_data for rate calculations
- Fixes issue where continuous type transitions showed no data in analysis plots
- Pass integration details to data collector for potential future use
- Maintains consistent event tracking across all transition types

**Files Changed:**
- `src/shypn/engine/simulation/controller.py`
- `doc/CONTINUOUS_TRANSITION_PLOTTING_FIX.md` (new)

**Date:** 2025-10-04
