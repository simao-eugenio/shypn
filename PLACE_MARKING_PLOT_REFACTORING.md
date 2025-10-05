# Place Analysis Plot Refactoring: Rate → Marking

**Date**: October 5, 2025  
**Purpose**: Make place analysis more intuitive by showing actual token counts instead of rates

---

## Overview

The place analysis panel has been refactored to display **marking evolution** (token counts over time) instead of **token rate** (d(tokens)/dt). This change makes the visualization much more meaningful and intuitive for understanding Petri net behavior.

---

## Changes Made

### 1. **PlaceRatePanel** (`src/shypn/analyses/place_rate_panel.py`)

#### Changed: Method `_get_rate_data()`
**Before**: Calculated rate using sliding time window
```python
# Old code:
rate_series = self.rate_calculator.calculate_token_rate_series(
    raw_data,
    time_window=self.time_window,
    sample_interval=0.01
)
return rate_series
```

**After**: Returns raw token counts directly
```python
# New code:
raw_data = self.data_collector.get_place_data(place_id)
return raw_data  # Direct return - no rate calculation!
```

#### Changed: Y-axis Label
- **Before**: `'Token Rate (tokens/s)'`
- **After**: `'Token Count'`

#### Changed: Plot Title
- **Before**: `'Place Token Consumption/Production Rate'`
- **After**: `'Place Marking Evolution'`

#### Removed: `set_time_window()` method
- No longer needed since we don't calculate rates
- Rate calculation required time window parameter
- Token counts are direct measurements

### 2. **AnalysisPlotPanel** (`src/shypn/analyses/plot_panel.py`)

#### Removed: Zero Reference Line
**Before**:
```python
# Add zero line for place panels (consumption vs production)
if self.object_type == 'place':
    self.axes.axhline(y=0, color='gray', linestyle='-', 
                    linewidth=0.8, alpha=0.5)
```

**After**: Line removed - zero reference only meaningful for rates, not token counts

---

## Benefits

### 🎯 **More Intuitive Visualization**
- **Old**: "Rate is +2.5 tokens/second at t=10" ← Hard to interpret
- **New**: "Place has 15 tokens at t=10" ← Immediately clear!

### 📊 **Better for All Transition Types**

#### Discrete Transitions (Immediate/Timed/Stochastic)
- **Old**: Showed spiky rates (infinite rate at firing instant, zero between)
- **New**: Shows step functions (clear instantaneous jumps)

#### Continuous Transitions
- **Old**: Showed rate as horizontal line (constant d(tokens)/dt)
- **New**: Shows smooth curves (actual token growth/decay)

### 🔬 **Direct State Visualization**
- Token count = actual Petri net state (marking)
- Can directly see when places become empty or full
- Easier to understand buffer behavior, resource availability, etc.

### ⚡ **Performance Improvement**
- No rate calculation overhead
- No sliding window computation
- Direct data display = faster plotting

---

## Plot Interpretation Guide

### **Horizontal Lines**
- **Meaning**: Steady state - no tokens added or removed
- **Example**: Place has 5 tokens constantly

### **Increasing Lines**
- **Meaning**: Tokens being added (production exceeds consumption)
- **Discrete**: Step function (jumps at transition firings)
- **Continuous**: Smooth curve (continuous flow)

### **Decreasing Lines**
- **Meaning**: Tokens being consumed (consumption exceeds production)
- **Discrete**: Step function (drops at transition firings)
- **Continuous**: Smooth curve (continuous drain)

### **Curves** (Continuous Transitions)
- **Linear**: Constant rate (e.g., rate = 1.0 tokens/s)
- **Exponential decay**: Draining toward zero
- **Exponential growth**: Unbounded accumulation
- **S-curves**: Limited by arc weights or enabling conditions

---

## Example Scenarios

### Scenario 1: Producer-Buffer-Consumer (Continuous)
```
P1[25] --[continuous, rate=1.0]--> P2[0] --[continuous, rate=0.5]--> P3[0]
```

**What you see**:
- **P1**: Linear decrease from 25 → 0 (draining at 1.0 tokens/s)
- **P2**: Linear increase then decrease (fills up, then drains slower)
- **P3**: Linear increase from 0 → 12.5 (accumulating at 0.5 tokens/s)

### Scenario 2: Discrete Event System
```
P1[10] --[immediate]--> P2[0] --[stochastic, rate=λ]--> P3[0]
```

**What you see**:
- **P1**: Step down by 1 each firing (10 → 9 → 8 → ...)
- **P2**: Spiky (jumps up instantly, waits, drops randomly)
- **P3**: Step up at random intervals (exponential distribution)

---

## Backward Compatibility

### Class Name Preserved
- Class still named `PlaceRatePanel` for compatibility
- No changes needed in UI loaders or other modules
- Future: Consider renaming to `PlaceMarkingPanel`

### Method Name Preserved
- `_get_rate_data()` still exists (called by base class)
- Now returns token counts instead of rates
- Base class `update_plot()` unchanged - works with any (time, value) data

---

## Testing Checklist

- [x] Refactoring complete
- [ ] Test with continuous transitions (smooth curves expected)
- [ ] Test with discrete transitions (step functions expected)
- [ ] Test with multiple places (different colors, legend works)
- [ ] Verify no hang after simulation stops
- [ ] Check matplotlib auto-scaling works correctly
- [ ] Confirm performance improvement (no rate calculation overhead)

---

## Future Enhancements

### Optional Rate View Toggle
Could add a button to switch between:
- **Marking view** (current): Shows token counts
- **Rate view** (optional): Shows d(tokens)/dt for analysis

### Derivative Visualization
Could show both on same plot:
- Primary Y-axis: Token count (solid lines)
- Secondary Y-axis: Rate (dashed lines, semi-transparent)

### Statistics Overlay
Could add optional statistics:
- Min/max token count
- Average occupancy
- Time spent empty/full

---

## Related Files

- `src/shypn/analyses/place_rate_panel.py` - Main changes
- `src/shypn/analyses/plot_panel.py` - Zero line removed
- `src/shypn/analyses/data_collector.py` - No changes (still collects raw data)
- `src/shypn/analyses/rate_calculator.py` - No longer used by place panel

---

## Notes

- **Transition rate panel unchanged** - still shows firing rates (meaningful for transitions)
- **Data collection unchanged** - still records all place token counts
- **RateCalculator utility preserved** - available if needed for custom analysis
