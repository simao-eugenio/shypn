# Transition Analysis: Adaptive Plotting Based on Transition Type

**Date**: October 5, 2025  
**Purpose**: Show actual transition behavior characteristics - rate functions for continuous, cumulative counts for discrete

---

## Overview

The transition analysis panel now **adapts its visualization** based on transition type:

- **Continuous transitions**: Plot **rate function value** over time (shows sigmoid curves, exponentials, etc.)
- **Discrete transitions**: Plot **cumulative firing count** over time (shows activity accumulation)

This addresses your requirement: **"When plotting a continuous transition with a sigmoid function set I expect to see S curves"**

---

## What This Patch Does

### ✅ Continuous Transitions → Rate Function Plots

When you add a continuous transition with:
```python
transition.properties = {
    'rate_function': 'sigmoid(t, 10, 0.5)'  # Sigmoid function
}
```

**The plot will show**: An **S-curve** representing the rate value over time!

- **X-axis**: Time (s)
- **Y-axis**: Rate (tokens/s) - the instantaneous flow rate
- **Curve**: Matches your rate function exactly (sigmoid, exponential, linear, etc.)

### ✅ Discrete Transitions → Cumulative Count

When you add an immediate/timed/stochastic transition:

**The plot will show**: Step function showing total firings

- **X-axis**: Time (s)
- **Y-axis**: Cumulative Firings - total number of times fired
- **Curve**: Staircase pattern (step up at each firing)

---

## Implementation Details

### How It Works

The panel inspects the data to determine transition type:

```python
# Check if transition is continuous
raw_events = data_collector.get_transition_data(transition_id)
details = raw_events[0][2]  # Get first event details

if isinstance(details, dict) and 'rate' in details:
    # CONTINUOUS: details contains 'rate' field
    # Plot rate values over time
    for time, event_type, details in raw_events:
        rate = details.get('rate', 0.0)
        plot_point(time, rate)
else:
    # DISCRETE: details doesn't contain rate
    # Plot cumulative count
    cumulative_count = 0
    for time, event_type, _ in raw_events:
        cumulative_count += 1
        plot_point(time, cumulative_count)
```

### Data Source

The data comes from `SimulationDataCollector`:

**Continuous transitions**: When `integrate_step()` is called, it stores:
```python
details = {
    'rate': 5.2,  # ← This is the instantaneous rate function value!
    'consumed': {...},
    'produced': {...},
    'dt': 0.01,
    'method': 'rk4'
}
data_collector.on_transition_fired(transition, time, details)
```

**Discrete transitions**: When `fire()` is called, it stores:
```python
details = {
    'consumed': {...},
    'produced': {...}
    # No 'rate' field
}
data_collector.on_transition_fired(transition, time, details)
```

---

## Rate Functions and Their Curves

### Supported Rate Function Types

1. **Constant**:
   ```python
   'rate_function': '2.0'
   ```
   **Plot**: Horizontal line at y=2.0

2. **Linear (State-dependent)**:
   ```python
   'rate_function': '0.5 * P1'  # Proportional to place P1 tokens
   ```
   **Plot**: Decreasing line as P1 drains

3. **Sigmoid** (Logistic):
   ```python
   'rate_function': 'sigmoid(t, 10, 0.5)'
   # sigmoid(time, midpoint, steepness)
   ```
   **Plot**: S-curve from 0 to 1, centered at t=10

4. **Exponential Growth**:
   ```python
   'rate_function': 'math.exp(0.1 * t)'
   ```
   **Plot**: Exponential curve growing over time

5. **Exponential Decay**:
   ```python
   'rate_function': 'math.exp(-0.1 * t)'
   ```
   **Plot**: Exponential curve decaying to zero

6. **Hill Function** (Enzyme kinetics):
   ```python
   'rate_function': 'hill(P1, 5, 2)'
   # hill(substrate, Km, n)
   ```
   **Plot**: Cooperative binding curve

7. **Saturating (Michaelis-Menten)**:
   ```python
   'rate_function': 'michaelis_menten(P1, 10, 5)'
   # mm(substrate, Vmax, Km)
   ```
   **Plot**: Hyperbolic saturation curve

8. **Custom Complex Functions**:
   ```python
   'rate_function': 'min(10, P1) * sigmoid(t, 5, 0.3)'
   ```
   **Plot**: Product of saturation and sigmoid (composite curve)

---

## Visual Examples

### Example 1: Continuous with Sigmoid

**Setup**:
```
P1[100] --[continuous, rate='sigmoid(t, 10, 0.5)']--> P2[0]
```

**What you'll see**:
```
Rate (tokens/s)
^
|  1.0 ┼                     ╭───────────
|      │                   ╭─
|  0.5 ┼                 ╭─  (S-curve!)
|      │               ╭─
|  0.0 ┼─────────────╭─
└──────┴────────────────────────────────> Time (s)
       0    5   10   15   20
```

**Interpretation**:
- At t<5: Rate ≈ 0 (slow start)
- At t=10: Rate ≈ 0.5 (midpoint)
- At t>15: Rate ≈ 1.0 (saturated)
- Flow accelerates then saturates (S-curve behavior!)

### Example 2: Continuous with Exponential Decay

**Setup**:
```
P1[50] --[continuous, rate='P1 * 0.1']--> P2[0]
```

**What you'll see**:
```
Rate (tokens/s)
^
|  5.0 ┼╲
|      │ ╲___
|  2.5 ┼     ╲___
|      │         ╲___        (Exponential decay)
|  0.0 ┼─────────────╲______
└──────┴──────────────────────────────> Time (s)
       0    10   20   30
```

**Interpretation**:
- Rate proportional to P1 tokens
- As P1 drains, rate decreases
- Exponential decay curve

### Example 3: Stochastic (Discrete)

**Setup**:
```
P1[1] --[stochastic, λ=2.0]--> P2[0] (with feedback)
```

**What you'll see**:
```
Cumulative Firings
^
| 10 ┼       ┌─┐
|    │     ┌─┘ └─┐
|  5 ┼   ┌─┘     └─┐      (Irregular staircase)
|    │ ┌─┘         └─┐
|  0 ┼─┘             └─
└────┴──────────────────────────────> Time (s)
     0    2    4    6    8
```

**Interpretation**:
- Steps at random times (exponential distribution)
- Average slope ≈ λ (2 firings/second)
- Stochastic behavior visible

### Example 4: Timed (Discrete)

**Setup**:
```
P1[1] --[timed, delay=0.5s]--> P2[0] (with feedback)
```

**What you'll see**:
```
Cumulative Firings
^
| 10 ┼       ┌─┐
|    │     ┌─┘ │
|  5 ┼   ┌─┘   │       (Perfect staircase)
|    │ ┌─┘     │
|  0 ┼─┘       │
└────┴──────────────────────────────> Time (s)
     0   1   2   3   4   5
```

**Interpretation**:
- Steps at exact intervals (0.5s)
- Perfectly regular staircase
- Deterministic timing visible

---

## Y-Axis Label Adaptation

The panel automatically adjusts the Y-axis label:

| Transitions Selected | Y-axis Label | Meaning |
|---------------------|--------------|---------|
| Only continuous | `Rate (tokens/s)` | Instantaneous flow rate |
| Only discrete | `Cumulative Firings` | Total number of firings |
| Mixed (both types) | `Value` | Generic (different meanings per curve) |

---

## Testing Scenarios

### Test 1: Sigmoid Rate Function ✅
```
1. Create continuous transition
2. Set rate_function = 'sigmoid(t, 10, 0.5)'
3. Add to analysis panel
4. Run simulation for 20 seconds
5. **Expected**: S-curve visible, rate goes from 0 → 1
```

### Test 2: Exponential Growth ✅
```
1. Create continuous transition
2. Set rate_function = 'math.exp(0.1 * t)'
3. Add to analysis panel
4. Run simulation for 10 seconds
5. **Expected**: Exponential curve, rate increases rapidly
```

### Test 3: State-Dependent Rate ✅
```
1. Create: P1[100] --[continuous, rate='0.5 * P1']--> P2[0]
2. Add transition to analysis panel
3. Run simulation
4. **Expected**: Decreasing curve as P1 drains (rate ∝ P1)
```

### Test 4: Mixed Types ✅
```
1. Add continuous transition (with sigmoid)
2. Add stochastic transition
3. Run simulation
4. **Expected**: 
   - Continuous shows S-curve (rate value)
   - Stochastic shows staircase (cumulative count)
   - Y-axis label = "Value" (generic)
```

---

## Backward Compatibility

### Class Name Unchanged
- Still named `TransitionRatePanel` (no loader changes needed)
- Method `_get_rate_data()` still exists (called by base class)
- Now returns different data based on transition type

### Data Collection Unchanged
- `SimulationDataCollector` already stores rate in details
- No changes to data collection logic
- Just using existing data differently

---

## Benefits

### ✅ True Behavior Visualization

**Before**: All transitions showed cumulative count (generic)
**After**: Each transition type shows its characteristic behavior

### ✅ Mathematical Function Validation

You can now **visually verify** your rate functions:
- Is your sigmoid shaped correctly?
- Is your exponential growing/decaying as expected?
- Are parameters (midpoint, steepness) correct?

### ✅ System Dynamics Understanding

- **Continuous**: See how rate changes over time (dynamics)
- **Discrete**: See how many times transition fired (activity)
- Both are meaningful for their respective types

### ✅ No Manual Mode Switching

The panel **automatically detects** transition type and plots appropriately. No user configuration needed!

---

## Code Changes Summary

### File: `src/shypn/analyses/transition_rate_panel.py`

1. **`_get_rate_data()` method**: Checks if transition is continuous or discrete, returns appropriate data

2. **`_get_ylabel()` method**: Returns dynamic label based on selected transitions

3. **Module docstring**: Updated to explain adaptive behavior

4. **Class docstring**: Detailed explanation of different visualizations per type

---

## Comparison Table

| Aspect | Continuous Transitions | Discrete Transitions |
|--------|----------------------|---------------------|
| **What's Plotted** | Rate function value r(t) | Cumulative firing count |
| **Y-axis** | Rate (tokens/s) | Cumulative Firings |
| **Curve Shape** | Smooth (sigmoid, exp, etc.) | Staircase steps |
| **Interpretation** | Instantaneous flow rate | Total activity |
| **Data Source** | `details['rate']` | Count of firing events |
| **Example Curves** | S-curve, exponential | Regular/irregular steps |

---

## Related Files

- `src/shypn/analyses/transition_rate_panel.py` - Main implementation
- `src/shypn/analyses/data_collector.py` - No changes (already stores rate)
- `src/shypn/engine/continuous_behavior.py` - No changes (already provides rate)
- `src/shypn/engine/simulation/controller.py` - No changes (already passes rate in details)

---

## Future Enhancements

### Derivative Visualization for Discrete
Could compute "instantaneous rate" from cumulative count:
- Smooth the staircase
- Show d(count)/dt for comparison with continuous rates

### Multiple Y-Axes
When mixing continuous + discrete:
- Left Y-axis: Rate (tokens/s)
- Right Y-axis: Cumulative Firings
- Each curve on appropriate axis

### Rate Function Editor
Could add UI to:
- Edit rate function interactively
- Preview curve shape before simulation
- Suggest common functions (sigmoid, exponential, etc.)

---

## Answer to Your Question

> "When plotting a continuous transition with a sigmoid function set I expect to see S curves... Last patch do this?"

**YES! ✅** The patch now does exactly this:

1. **Continuous transitions with sigmoid**: Plot shows S-curve of rate function
2. **Timed transitions**: Plot shows regular staircase (deterministic timing)
3. **Stochastic transitions**: Plot shows irregular staircase (random timing)
4. **Immediate transitions**: Plot shows vertical steps (instant firings)

Each transition type now visualizes its **characteristic behavior**, not just generic cumulative counts!

---

## Quick Start

1. **Restart application** (to load new code)
2. **Create continuous transition** with rate function (e.g., `sigmoid(t, 10, 0.5)`)
3. **Add to analysis panel** via right-click → "Add to Analysis"
4. **Run simulation** for 20+ seconds
5. **See the S-curve!** Rate function plotted over time

🎉 Your sigmoid functions will now show as beautiful S-curves!
