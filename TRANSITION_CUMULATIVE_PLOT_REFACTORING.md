# Transition Analysis Plot Refactoring: Rate → Cumulative Count

**Date**: October 5, 2025  
**Purpose**: Make transition analysis more intuitive by showing cumulative firing counts instead of rates

---

## Overview

The transition analysis panel has been refactored to display **cumulative firing count evolution** (total firings over time) instead of **firing rate** (firings/second). This change makes the visualization much more meaningful and reveals transition behavior patterns clearly.

---

## Changes Made

### 1. **TransitionRatePanel** (`src/shypn/analyses/transition_rate_panel.py`)

#### Changed: Method `_get_rate_data()`
**Before**: Calculated firing rate using sliding time window
```python
# Old code:
firing_times = [t for t, event_type, _ in raw_events if event_type == 'fired']
rate_series = self.rate_calculator.calculate_firing_rate_series(
    firing_times,
    time_window=self.time_window,
    sample_interval=0.1
)
return rate_series
```

**After**: Converts firing events to cumulative counts
```python
# New code:
firing_times = [t for t, event_type, _ in raw_events if event_type == 'fired']

cumulative_series = []
if firing_times[0] > 0:
    cumulative_series.append((0.0, 0))  # Start at zero

for i, time in enumerate(firing_times):
    count = i + 1  # Cumulative count
    cumulative_series.append((time, count))

return cumulative_series
```

#### Changed: Y-axis Label
- **Before**: `'Firing Rate (firings/s)'`
- **After**: `'Cumulative Firings'`

#### Changed: Plot Title
- **Before**: `'Transition Firing Rate'`
- **After**: `'Transition Firing Count Evolution'`

#### Removed: `set_time_window()` method
- No longer needed since we don't calculate rates
- Cumulative counts are direct sums of firing events

---

## Benefits

### 🎯 **More Intuitive Visualization**
- **Old**: "Rate is 5.2 firings/second at t=10" ← Abstract
- **New**: "Transition has fired 52 times by t=10" ← Concrete!

### 📊 **Clear Transition Type Distinction**

#### Immediate Transitions
- **Old**: Infinite spikes whenever enabled
- **New**: Vertical steps showing instant firing activity

#### Timed Transitions (Deterministic)
- **Old**: Periodic spikes at regular intervals
- **New**: Regular staircase pattern (constant slope = constant rate)

#### Stochastic Transitions (Random)
- **Old**: Random spikes with variable spacing
- **New**: Irregular staircase (variable slope = variable rate)

#### Continuous Transitions
- **Old**: Smooth rate curve (hard to integrate mentally)
- **New**: Smooth increasing curve (direct cumulative integration)

### 🔬 **Activity Analysis**
From the cumulative plot, you can immediately see:

1. **Total Activity**: Final Y value = total firings
2. **Activity Periods**: 
   - Horizontal = idle (transition not firing)
   - Steep slope = high activity
   - Gentle slope = low activity
3. **Comparative Activity**: Compare different transitions' total firings
4. **Time to Milestones**: "When did transition reach 100 firings?"

### ⚡ **Performance Improvement**
- No rate calculation overhead
- No sliding window computation
- Simple cumulative sum = faster plotting

---

## Plot Interpretation Guide

### **Horizontal Segments**
- **Meaning**: Transition not firing (disabled, in conflict, or waiting)
- **Example**: Stochastic transition waiting for next exponential delay

### **Vertical Steps** (Discrete Transitions)
- **Meaning**: Instantaneous firings
- **Step height = 1**: Single firing
- **Step height > 1**: Multiple firings in quick succession
- **Regular steps**: Timed transition (deterministic intervals)
- **Irregular steps**: Stochastic transition (random intervals)

### **Smooth Curves** (Continuous Transitions)
- **Meaning**: Continuous flow/integration
- **Linear**: Constant rate (e.g., rate = 1.0 firings/s)
- **Curve**: Rate depends on place tokens (mass-action kinetics)
- **Slope = instantaneous firing rate**

### **Slope Analysis**
- **Steep slope**: High firing frequency (transition very active)
- **Gentle slope**: Low firing frequency (transition occasionally active)
- **Zero slope**: Transition idle (not enabled or deadlocked)

---

## Example Scenarios

### Scenario 1: Immediate Transition (Loop)
```
P1[1] <--[immediate]--> P2[0]
      |                 |
      +-------[immediate]
```

**What you see**:
- **Both transitions**: Rapid vertical steps forming steep line
- **Total firings**: Both accumulate ~thousands of firings quickly
- **Pattern**: Alternating (when T1 fires, T2 becomes enabled, fires, T1 re-enabled...)

### Scenario 2: Stochastic Producer-Consumer
```
Source --[stochastic, λ=2]--> P1[0] --[stochastic, λ=1]--> Sink
           (T_produce)                     (T_consume)
```

**What you see**:
- **T_produce**: Irregular steps, slope ≈ 2 firings/s (λ=2)
- **T_consume**: Irregular steps, slope ≈ 1 firings/s (λ=1)
- **Comparison**: T_produce fires ~2x more than T_consume
- **Buffer behavior**: P1 accumulates tokens (produce > consume)

### Scenario 3: Continuous Flow System
```
P1[100] --[continuous, rate=5.0]--> P2[0] --[continuous, rate=2.0]--> P3[0]
             (T1)                              (T2)
```

**What you see**:
- **T1**: Smooth curve, fires 5 times/second = slope of 5
- **T2**: Smooth curve, fires 2 times/second = slope of 2
- **After 10s**: T1 ≈ 50 firings, T2 ≈ 20 firings
- **Relationship**: T1 fires 2.5x more than T2

### Scenario 4: Timed Periodic Task
```
Timer[1] --[timed, delay=0.5s]--> Task[0]
   ^                                  |
   |                                  |
   +--------[immediate]---------------+
```

**What you see**:
- **Timed transition**: Perfect staircase with 0.5s steps
- **Linear growth**: Exactly 2 firings per second
- **Predictable**: Count = 2 × time

---

## Curve Shape Dictionary

| Transition Type | Curve Shape | Slope Behavior | Example |
|----------------|-------------|----------------|---------|
| **Immediate** | Sharp vertical steps | Variable (depends on enabling) | Firing cascade |
| **Timed** | Regular staircase | Constant (deterministic) | Clock, periodic tasks |
| **Stochastic** | Irregular staircase | Average matches λ | Random arrivals |
| **Continuous** | Smooth curve | Depends on enabling | Fluid flow, chemicals |

---

## Advanced Analysis

### Derivative = Rate
The **slope of the cumulative curve** at any point equals the **firing rate** at that time:
- Steep slope = high rate (frequent firings)
- Gentle slope = low rate (occasional firings)
- Zero slope = zero rate (idle)

So you still get rate information visually, but with cumulative context!

### Integration = Total Activity
The **Y-value** at any time directly shows **total firings up to that point**:
- No need to integrate rate mentally
- Direct reading of activity metric

### Comparison = Relative Activity
Comparing curves shows relative activity:
- Higher curve = more total firings
- Steeper slope = higher current rate
- Parallel curves = same rate, different start times

### Throughput Analysis
For producer-consumer systems:
- **Producer cumulative count** = total items produced
- **Consumer cumulative count** = total items consumed
- **Difference** = items in buffer (conservation)

---

## Backward Compatibility

### Class Name Preserved
- Class still named `TransitionRatePanel` for compatibility
- No changes needed in UI loaders or other modules
- Future: Consider renaming to `TransitionActivityPanel` or `TransitionCountPanel`

### Method Name Preserved
- `_get_rate_data()` still exists (called by base class)
- Now returns cumulative counts instead of rates
- Base class `update_plot()` unchanged - works with any (time, value) data

---

## Testing Checklist

- [x] Refactoring complete
- [ ] Test with immediate transitions (vertical steps expected)
- [ ] Test with timed transitions (regular staircase expected)
- [ ] Test with stochastic transitions (irregular staircase expected)
- [ ] Test with continuous transitions (smooth curves expected)
- [ ] Test with multiple transitions (different colors, comparison)
- [ ] Verify performance (no hang, smooth updates)

---

## Comparison with Place Plots

| Aspect | Place Plot | Transition Plot |
|--------|-----------|-----------------|
| **Y-axis** | Token count (state) | Cumulative firings (activity) |
| **Meaning** | System state (marking) | System activity (events) |
| **Decreasing?** | Yes (token consumption) | No (monotonic increase) |
| **Horizontal** | Steady state | Idle (not firing) |
| **Steep slope** | Fast token change | Frequent firings |

Both are now **cumulative measures** rather than derivatives!

---

## Future Enhancements

### Optional Rate View Toggle
Could add a button to switch between:
- **Cumulative view** (current): Shows total firings
- **Rate view** (optional): Shows firings/second for analysis

### Inter-Event Time Histogram
Could add panel showing:
- Distribution of time between consecutive firings
- Helps validate stochastic transition distributions

### Firing Density Heatmap
Could show:
- Time axis divided into bins
- Color intensity = firing frequency in that bin
- Good for long simulations

### Statistics Overlay
Could add optional statistics:
- Total firings (final count)
- Average firing rate
- Maximum burst rate
- Idle time percentage

---

## Related Files

- `src/shypn/analyses/transition_rate_panel.py` - Main changes
- `src/shypn/analyses/data_collector.py` - No changes (still collects firing events)
- `src/shypn/analyses/rate_calculator.py` - No longer used by transition panel
- `src/shypn/analyses/plot_panel.py` - No changes needed

---

## Notes

- **Place panel also refactored** - now shows token counts (marking evolution)
- **Both panels now show cumulative measures** - more intuitive than derivatives
- **Data collection unchanged** - still records all firing events
- **RateCalculator utility preserved** - available if needed for custom analysis
- **Performance improved** - no expensive rate calculations during plotting

---

## Mathematical Note

**Old approach** (derivative):
```
rate(t) = d(count)/dt
```
Required numerical differentiation with sliding window, introduced noise and lag.

**New approach** (integral):
```
count(t) = ∫₀ᵗ rate(τ) dτ
```
Direct measurement, no calculation needed, numerically stable!

The relationship is preserved: **slope of cumulative plot = rate at that time**.
