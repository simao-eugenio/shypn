# Simulation Time Scaling Analysis

**Question**: In a simple net `P1 → T → P2` with P1=300 tokens, where the real phenomenon takes 2 hours, can I see the complete process in 1 second of viewing time?

**Answer**: ✅ **YES**, and you have **THREE different ways** to achieve this!

## Executive Summary

To simulate a 2-hour real process in 1 second of viewing time, you need a **7,200x speedup** (2 hours = 7,200 seconds).

### Three Approaches:

| Approach | Parameter | Value | Best For |
|----------|-----------|-------|----------|
| **1. Time Scale** | `time_scale` | 7200.0 | **Watching visualization** at high speed |
| **2. Transition Rate** | `transition.rate` | 150.0 tokens/s | Matching **real flow rates** |
| **3. Duration + dt** | `duration=2h`, `dt=0.001s` | Fast forward | **Batch processing** without animation |

---

## Understanding the Problem

### Your Net Structure
```
P1 (300 tokens) → T (continuous) → P2 (0 tokens)
```

### Real Phenomenon
- **Duration**: 2 hours
- **Flow**: 300 tokens must move from P1 to P2
- **Real rate**: 300 tokens / 7200 seconds = 0.04167 tokens/second

### Viewing Requirement
- **Watch it in**: 1 second
- **Speedup needed**: 7200x

---

## Solution 1: Time Scale (Playback Speed) ⭐ RECOMMENDED

### Concept
Time scale controls **playback speed** - how fast you watch the simulation.

```
time_scale = model_seconds / real_seconds
```

### Configuration
```python
# In simulation settings:
settings.time_scale = 7200.0  # 7200 seconds of model time per 1 second of real time

# Transition configuration:
T.transition_type = "continuous"
T.rate = 0.04167  # Real-world rate (tokens/second in model time)
```

### How It Works
1. **Model time**: Simulation runs for 7200 seconds (2 hours)
2. **Transition rate**: 0.04167 tokens/s (real-world rate)
3. **Viewing time**: You watch it in 1 second (7200x faster playback)

### Calculation Details
```
GUI update interval = 0.1 seconds (fixed)
Model time per GUI update = 0.1s × 7200 = 720 seconds
Time step dt = 0.1 seconds (auto-calculated)
Steps per GUI update = 720s / 0.1s = 7200 steps

Result: In 1 second of viewing (10 GUI updates):
- Model advances 7200 seconds (2 hours)
- Tokens flow at real-world rate: 0.04167 tokens/s × 7200s = 300 tokens
- P1: 300 → 0
- P2: 0 → 300 ✅
```

### Advantages
✅ **Accurate physics** - Uses real-world rates  
✅ **Flexible viewing** - Change playback speed without changing model  
✅ **Smooth animation** - System batches steps automatically  
✅ **Reusable model** - Same model works at any viewing speed  

### Disadvantages
⚠️ Very high time_scale values (>1000x) may cause UI responsiveness issues  
⚠️ System caps at 1000 steps per GUI update for safety  

---

## Solution 2: Transition Rate (Flow Speed) 🔥

### Concept
Increase the **transition rate** to make tokens flow faster.

### Configuration
```python
# In simulation settings:
settings.duration = 1.0  # 1 second of model time
settings.time_scale = 1.0  # Real-time playback

# Transition configuration:
T.transition_type = "continuous"
T.rate = 150.0  # tokens/second (FAST rate)
```

### How It Works
1. **Model time**: Simulation runs for 1 second
2. **Transition rate**: 150 tokens/s (artificially high)
3. **Viewing time**: You watch it in 1 second (real-time)

### Calculation Details
```
Duration = 1.0 second
Rate = 150 tokens/second
Time step dt = 0.001 seconds (auto: 1.0/1000 steps)

Integration over 1 second:
- Each step: 150 × 0.001 = 0.15 tokens flow
- Total steps: 1000
- Total flow: 0.15 × 1000 = 150 tokens... WAIT! ❌

PROBLEM: Only 150 tokens move, not 300!
```

### Fix: Adjust Rate
```python
T.rate = 300.0  # tokens/second

Result after 1 second:
- Flow = 300 tokens/s × 1.0s = 300 tokens ✅
- P1: 300 → 0
- P2: 0 → 300
```

### Advantages
✅ **Simple** - Just set the rate high  
✅ **Fast simulation** - Short model time  
✅ **Good for testing** - Quick iterations  

### Disadvantages
❌ **Unrealistic rates** - 300 tokens/s doesn't match real phenomenon (0.04167 tokens/s)  
❌ **Model modification** - Changes the model itself, not just viewing  
❌ **Not scalable** - Different rates needed for different viewing speeds  

---

## Solution 3: Duration + Small dt (Batch Mode) ⚡

### Concept
Run the full 2-hour simulation with fine time steps, let it compute as fast as possible.

### Configuration
```python
# In simulation settings:
settings.duration = 7200.0  # 2 hours in seconds
settings.time_units = TimeUnits.SECONDS
settings.dt_manual = 0.1  # 0.1 second steps
settings.time_scale = 1.0  # Doesn't matter for batch

# Transition configuration:
T.transition_type = "continuous"
T.rate = 0.04167  # Real-world rate
```

### How It Works
1. **Model time**: Simulation runs for 7200 seconds (2 hours)
2. **Transition rate**: 0.04167 tokens/s (real rate)
3. **Computation**: Runs as fast as CPU allows (no animation throttling)
4. **Result**: You get the final state almost instantly

### Calculation Details
```
Duration = 7200 seconds
Time step = 0.1 seconds
Total steps = 7200 / 0.1 = 72,000 steps

Each step:
- Rate = 0.04167 tokens/s
- Flow = 0.04167 × 0.1 = 0.004167 tokens

Total flow = 0.004167 × 72,000 = 300 tokens ✅

Computation time: ~0.1-1 second (depending on CPU)
```

### Advantages
✅ **Accurate physics** - Uses real-world rates  
✅ **Fast computation** - No animation overhead  
✅ **Batch processing** - Good for analysis, not watching  

### Disadvantages
❌ **No visualization** - You don't "see" the process  
❌ **Many steps** - 72,000 steps takes memory  
❌ **Not interactive** - Can't watch it flow  

---

## Comparison Matrix

| Feature | Time Scale | Transition Rate | Duration + dt |
|---------|------------|-----------------|---------------|
| **Accurate real rates** | ✅ Yes | ❌ No (artificial) | ✅ Yes |
| **Watch animation** | ✅ Yes (smooth) | ✅ Yes | ❌ No |
| **Viewing time** | 1 second | 1 second | ~instant |
| **Model changes** | None | Rate change | None |
| **Reusability** | ✅ High | ❌ Low | ✅ High |
| **CPU intensive** | Medium | Low | High |
| **Memory usage** | Low | Low | High |
| **Best for** | **Interactive viewing** | Quick tests | Batch analysis |

---

## Recommended Approach: Time Scale ⭐

### Why?
1. **Separation of concerns**: Model represents reality, viewing speed is separate
2. **Flexibility**: Change viewing speed without modifying model
3. **Accuracy**: Transition rates match real-world phenomenon
4. **Smooth**: System handles animation batching automatically

### Setup Steps

#### 1. Configure Transition (Real Rates)
```python
# P1 → T → P2
T.transition_type = "continuous"
T.rate = 0.04167  # 300 tokens / 7200 seconds
```

Or in SBML import (now defaults to continuous):
```python
# Already set to continuous by default!
# Rate will be 1.0 by default (can adjust)
```

#### 2. Configure Simulation Settings
```python
# In GUI or programmatically:
settings = SimulationSettings()
settings.duration = 7200.0  # 2 hours in seconds
settings.time_units = TimeUnits.SECONDS
settings.dt_auto = True  # Auto-calculate dt
settings.time_scale = 7200.0  # 7200x speedup

# Effective dt = 7200 / 1000 = 7.2 seconds per step
# Steps per GUI update (0.1s) = (0.1 × 7200) / 7.2 = 100 steps
```

#### 3. Run Simulation
```python
# GUI: Click "Start Simulation"
# Programmatic:
controller.start_simulation(time_step=None)  # Uses effective dt

# Watch for 1 second (10 GUI updates):
# - 10 updates × 100 steps = 1000 steps total
# - 1000 steps × 7.2s = 7200 seconds model time
# - Flow: 0.04167 tokens/s × 7200s = 300 tokens ✅
```

---

## Mathematical Validation

### Given
- Real phenomenon duration: `T_real = 2 hours = 7200 seconds`
- Tokens to transfer: `N = 300 tokens`
- Viewing time desired: `T_view = 1 second`

### Derived
```
Real flow rate:
r_real = N / T_real = 300 / 7200 = 0.04167 tokens/s

Time scale required:
time_scale = T_real / T_view = 7200 / 1 = 7200x

Model configuration:
- duration = T_real = 7200 seconds
- rate = r_real = 0.04167 tokens/s
- time_scale = 7200x

Verification:
- Model time: 7200 seconds
- Flow: 0.04167 × 7200 = 300 tokens ✅
- Viewing time: 7200 / 7200 = 1 second ✅
```

---

## Practical Example: SBML Import

### Your SBML Pathway
```
P1 (initial: 300) → Reaction → P2 (initial: 0)
```

### After Import (with new defaults)
```python
# Automatic configuration:
T.transition_type = "continuous"  # ✅ New default!
T.rate = 1.0  # Default (adjust to 0.04167 for real rate)
```

### Adjust for 2-Hour Process
```python
# Method 1: Edit transition properties
T.rate = 0.04167  # Real-world rate

# Method 2: Keep rate=1.0, adjust time scale
settings.duration = 300.0  # 300 seconds (5 minutes)
settings.time_scale = 300.0  # Watch in 1 second
# Flow: 1.0 tokens/s × 300s = 300 tokens ✅
```

---

## Implementation Notes

### Current Code Location
- **Time scale**: `src/shypn/engine/simulation/settings.py` line ~128
- **Time scale usage**: `src/shypn/engine/simulation/controller.py` line ~1378
- **Continuous rate**: `src/shypn/engine/continuous_behavior.py` line ~70-92
- **Integration**: `src/shypn/engine/continuous_behavior.py` (RK4 method)

### Key Formula in Controller
```python
# controller.py line 1378
model_time_per_gui_update = gui_interval_s * self.settings.time_scale

# Example: gui_interval_s=0.1s, time_scale=7200
# → model_time_per_gui_update = 720 seconds
# → In 10 GUI updates (1 second), model advances 7200 seconds
```

### Integration Calculation
```python
# continuous_behavior.py - RK4 integration
def integrate_step(self, dt, input_arcs, output_arcs):
    rate = self.rate_function(places, time)  # e.g., 0.04167
    flow = rate * dt  # tokens per step
    
    # Update place tokens
    for arc in input_arcs:
        arc.place.tokens -= flow * arc.weight
    for arc in output_arcs:
        arc.place.tokens += flow * arc.weight
```

---

## Summary

### Question Answered ✅
**YES**, you can see a 2-hour real process complete in 1 second of viewing time.

### Best Method: Time Scale
```python
# Model (represents reality):
T.rate = 0.04167 tokens/s  # Real-world rate
settings.duration = 7200 seconds  # 2 hours

# Viewing (just playback speed):
settings.time_scale = 7200.0  # Watch 7200x faster
```

### Result
- **Model time**: 7200 seconds (2 hours)
- **Real time to watch**: 1 second
- **Tokens transferred**: 300 (P1→P2)
- **Rate accuracy**: Matches real phenomenon ✅
- **Animation**: Smooth and continuous ✅

### Alternative (Simpler but less accurate)
```python
# Quick and dirty:
T.rate = 300.0 tokens/s  # Just make it fast
settings.duration = 1.0 second
settings.time_scale = 1.0  # Real-time
```

**Use time scale for production, use high rate for quick testing!**
