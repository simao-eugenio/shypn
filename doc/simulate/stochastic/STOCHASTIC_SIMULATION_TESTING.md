# Stochastic Simulation Testing and Token Sampling

**Purpose**: Testing stochastic (FSPN) transitions and understanding the token sampling window parameter.

**Date**: October 12, 2025  
**Status**: Ready for Testing

---

## Overview

Stochastic transitions in Shypn implement **Fluid Stochastic Petri Nets (FSPN)** with:
- Exponential distribution for firing delays: `T ~ Exp(λ)`
- Burst firing: 1x to 8x token consumption/production
- Rate-dependent behavior (higher rate = more frequent firing)

**Key Question**: How do we measure token counts over time in stochastic simulations?

**Answer**: The **time step (dt)** parameter defines the **sampling window** for token measurements.

---

## Token Sampling Window: The `dt` Parameter

### What Is It?

The `dt` (delta time, time step) parameter controls:

1. **Simulation granularity**: How finely time is discretized
2. **Token sampling frequency**: How often we record place markings
3. **Stochastic event detection**: How accurately we capture rapid changes

```
Simulation Timeline:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
t=0      t=dt    t=2dt   t=3dt   t=4dt ...
│        │       │       │       │
└────────┴───────┴───────┴───────┴───────→ time
   step1   step2   step3   step4

At each step, we:
1. Check which stochastic transitions can fire
2. Fire enabled transitions
3. Record current token counts (sampling!)
4. Advance time by dt
```

### Why Is It Important for Stochastic Simulation?

**Problem**: Stochastic events happen at random times between sampling points.

```
True stochastic behavior:
                Firing!
                   ↓
Tokens: 10─────────3─────────3────────5───...
        │          │         │        │
Time:   0         1.3       2.7      4.1

With dt=1.0 sampling:
Tokens: 10─────────3─────────5───...
        │          │         │
Time:   0          1         2        (missed detail at t=1.3!)

With dt=0.1 sampling:
Tokens: 10─10─10─10─3─3─3─3─3─5─...
        │  │  │  │  │ │ │ │ │ │
Time:   0 .1 .2 .3 .4.5.6.7.8.9  (captures more detail!)
```

**Trade-off**:
- **Smaller dt**: Better resolution, more accurate, but slower simulation
- **Larger dt**: Faster simulation, but may miss rapid token changes

---

## Where Is `dt` Configured?

### UI Location

**Simulation Settings Dialog** (`ui/dialogs/simulation_settings.ui`):

```
Simulation Settings Dialog
┌──────────────────────────────────────┐
│  Time Step Configuration             │
│                                      │
│  ○ Automatic (Recommended)           │
│     dt = duration / 1000             │
│                                      │
│  ○ Manual: [ 0.01 ] seconds         │← User can set explicit dt
│                                      │
│  Estimated steps: 1,000              │
└──────────────────────────────────────┘
```

### Code Location

**SimulationSettings class** (`src/shypn/engine/simulation/settings.py`):

```python
class SimulationSettings:
    """Manages simulation timing configuration."""
    
    def get_effective_dt(self) -> float:
        """Calculate effective time step.
        
        Returns:
            float: Time step in seconds (the sampling window!)
        """
        if self._dt_auto:
            # Auto mode: duration / 1000 steps
            duration_seconds = self.get_duration_seconds()
            if duration_seconds is not None:
                return duration_seconds / 1000  # Default target
            return self._dt_manual  # Fallback
        else:
            # Manual mode: user-specified
            return self._dt_manual
```

**SimulationController** (`src/shypn/engine/simulation/controller.py`):

```python
def step(self, time_step: float = None) -> bool:
    """Execute one simulation step.
    
    Args:
        time_step: Sampling interval (dt). If None, uses settings.
    
    Process:
        1. Check stochastic transitions (are they scheduled to fire?)
        2. Fire enabled transitions
        3. Record token counts (sampling!)
        4. Advance time: self.time += time_step
    """
    if time_step is None:
        time_step = self.get_effective_dt()  # Get from settings
    
    # ... simulation logic ...
    
    self.time += time_step  # Advance clock
```

---

## Recommended Settings for Stochastic Simulation

### General Guidelines

| Simulation Type | Duration | Recommended dt | Steps | Reason |
|----------------|----------|----------------|-------|---------|
| **Fast dynamics** | 10s | 0.01s | 1,000 | Capture rapid token changes |
| **Medium dynamics** | 60s | 0.05s | 1,200 | Balance speed and accuracy |
| **Slow dynamics** | 300s | 0.1s | 3,000 | Adequate for slow processes |
| **Very slow** | 1000s | 0.5s | 2,000 | Performance priority |

### Based on Stochastic Rate (λ)

The rate parameter determines how frequently transitions fire:
```
Mean firing interval = 1 / λ
```

**Rule of Thumb**: Set `dt ≤ (1/λ) / 10` to capture at least 10 samples per firing event.

| Rate (λ) | Mean Interval | Recommended dt | Samples/Event |
|----------|---------------|----------------|---------------|
| 0.1 | 10s | 1.0s | 10 |
| 1.0 | 1s | 0.1s | 10 |
| 10.0 | 0.1s | 0.01s | 10 |
| 100.0 | 0.01s | 0.001s | 10 |

**Example**:
```
Stochastic transition with λ = 5.0:
- Mean interval: 1/5 = 0.2s
- Recommended dt: 0.2/10 = 0.02s
- This gives ~10 samples between firings
```

### Based on Token Count Dynamics

Consider how quickly token counts change:

```python
# Fast-changing tokens (birth-death process)
# Tokens: 100 → 50 → 120 → 30 in 1 second
dt = 0.01s  # Need fine sampling

# Slow-changing tokens (enzyme kinetics)
# Tokens: 100 → 98 → 96 → 94 in 10 seconds  
dt = 0.5s   # Coarse sampling okay
```

---

## Testing Plan: Simple Stochastic Nets

### Test 1: Single Source Transition (Token Generation)

**Model Structure**:
```
     [T1]
      ↓
    ┌───┐
    │ P1│  (Tokens accumulate)
    └───┘
```

**Properties**:
- T1: Stochastic, λ = 1.0, burst = 1-8
- P1: Initially 0 tokens

**Test Procedure**:
```python
# Test with different dt values
dt_values = [0.001, 0.01, 0.1, 1.0]

for dt in dt_values:
    model = create_source_model()
    sim = SimulationController(model)
    
    sim.settings.set_duration(10.0, TimeUnits.SECONDS)
    sim.settings.dt_manual = dt
    sim.settings.dt_auto = False
    
    sim.run()
    
    # Analyze results
    tokens = sim.get_place_history(P1)
    print(f"dt={dt}: Final tokens={tokens[-1]}, samples={len(tokens)}")
```

**Expected Results**:

| dt | Steps | Samples | Avg Burst | Approx Final Tokens |
|----|-------|---------|-----------|---------------------|
| 0.001 | 10,000 | 10,000 | 4.5 | 45-50 |
| 0.01 | 1,000 | 1,000 | 4.5 | 45-50 |
| 0.1 | 100 | 100 | 4.5 | 45-50 |
| 1.0 | 10 | 10 | 4.5 | 45-50 |

**Key Observation**: Final token count should be similar (stochastic variance), but sampling resolution differs dramatically.

---

### Test 2: Source-Sink Pair (Token Flow)

**Model Structure**:
```
     [T1]        [T2]
      ↓           ↑
    ┌───┐       (Tokens consumed)
    │ P1│
    └───┘
```

**Properties**:
- T1: Stochastic source, λ₁ = 2.0, burst = 1-8
- T2: Stochastic sink, λ₂ = 1.0, burst = 1-8  
- P1: Initially 0 tokens

**Test Procedure**:
```python
model = create_source_sink_model()
sim = SimulationController(model)

# Test with medium dt
sim.settings.set_duration(100.0, TimeUnits.SECONDS)
sim.settings.dt_manual = 0.05
sim.settings.dt_auto = False

sim.run()

# Analyze equilibrium
tokens = sim.get_place_history(P1)
plot_tokens_over_time(tokens)  # Should oscillate around equilibrium
```

**Expected Behavior**:
- **Early phase**: Tokens accumulate (T1 > T2)
- **Equilibrium**: Oscillates around mean (T1 ≈ T2)
- **Mean tokens**: Approximately (λ₁ - λ₂) × mean_burst × τ

```
Tokens
  │
  │    ╱╲  ╱╲  ╱╲
  │   ╱  ╲╱  ╲╱  ╲
  │──────────────────  ← Equilibrium ~10 tokens
  │╱
  │
  └────────────────────→ Time
```

---

### Test 3: Two-Place Oscillator

**Model Structure**:
```
    ┌───┐  T1  ┌───┐
    │ P1│────→│ P2│
    └───┘     └───┘
       ↑       │
       │       │ T2
       └───────┘
```

**Properties**:
- P1: Initially 50 tokens
- P2: Initially 50 tokens
- T1: Stochastic, λ = 1.0, weight = 1
- T2: Stochastic, λ = 1.0, weight = 1

**Test Procedure**:
```python
model = create_oscillator_model()
sim = SimulationController(model)

# Fine sampling to capture oscillations
sim.settings.set_duration(50.0, TimeUnits.SECONDS)
sim.settings.dt_manual = 0.01  # Fine resolution
sim.settings.dt_auto = False

sim.run()

# Analyze oscillation
p1_tokens = sim.get_place_history(P1)
p2_tokens = sim.get_place_history(P2)

# Should show anti-phase oscillations
plot_dual_time_series(p1_tokens, p2_tokens)
```

**Expected Behavior**:
```
Tokens
  │
  │ P1: ─╲  ╱─╲  ╱─
  │      ╲╱   ╲╱
  │       ╱╲   ╱╲
  │ P2: ─╱  ╲─╱  ╲─
  │
  └─────────────────→ Time
```

---

## Analysis: Effect of `dt` on Results

### Test Setup
```python
def analyze_dt_effect():
    """Compare simulation with different dt values."""
    
    dt_values = [0.001, 0.01, 0.1, 0.5]
    results = {}
    
    for dt in dt_values:
        model = create_source_sink_model()
        sim = SimulationController(model)
        
        sim.settings.set_duration(10.0, TimeUnits.SECONDS)
        sim.settings.dt_manual = dt
        sim.settings.dt_auto = False
        
        start_time = time.time()
        sim.run()
        elapsed = time.time() - start_time
        
        tokens = sim.get_place_history(P1)
        
        results[dt] = {
            'steps': len(tokens),
            'final_tokens': tokens[-1],
            'mean_tokens': np.mean(tokens),
            'std_tokens': np.std(tokens),
            'elapsed_time': elapsed
        }
    
    return results
```

### Expected Output

```
┌────────┬───────┬──────────┬────────┬───────┬──────────┐
│   dt   │ Steps │  Final   │  Mean  │  Std  │ Time(s)  │
├────────┼───────┼──────────┼────────┼───────┼──────────┤
│ 0.001  │10,000 │   47     │  23.5  │  8.2  │   2.34   │
│ 0.01   │ 1,000 │   45     │  22.8  │  8.1  │   0.24   │
│ 0.1    │   100 │   48     │  24.1  │  7.9  │   0.03   │
│ 0.5    │    20 │   46     │  23.2  │  8.3  │   0.01   │
└────────┴───────┴──────────┴────────┴───────┴──────────┘

Observations:
1. Final tokens: Similar (stochastic variance)
2. Mean/Std: Consistent (sampling doesn't affect underlying dynamics)
3. Computation time: Scales linearly with steps
4. Sampling resolution: More samples = smoother plots
```

### Visual Comparison

```
dt = 0.001 (10,000 samples):
Tokens │ ───╱╲─╱╲╱╲───╱╲─╱
       │       smooth, detailed

dt = 0.1 (100 samples):
Tokens │ ──╱─╲╱──╲─╱─╲──
       │    coarser, still captures trend

dt = 0.5 (20 samples):
Tokens │ ─╱──╲───╲─╱──
       │   very coarse, may miss peaks
```

---

## UI Parameter Recommendations

### Automatic Mode (Recommended)

**Formula**: `dt = duration / 1000`

```
Duration = 10s  → dt = 0.01s  (1,000 steps)
Duration = 60s  → dt = 0.06s  (1,000 steps)  
Duration = 300s → dt = 0.3s   (1,000 steps)
```

**Advantages**:
- ✅ Consistent ~1,000 samples regardless of duration
- ✅ Good balance for most cases
- ✅ No user calculation needed

**Disadvantages**:
- ❌ May be too coarse for fast stochastic (high λ)
- ❌ May be too fine for slow stochastic (low λ)

---

### Manual Mode (Advanced)

**When to Use**:
- Fast stochastic transitions (λ > 10)
- Need to capture specific dynamics
- Performance tuning (trade speed vs accuracy)

**Setting Guidelines**:

1. **Based on fastest transition rate**:
   ```
   λ_max = maximum rate among all stochastic transitions
   dt_recommended = 1 / (10 * λ_max)
   ```

2. **Based on desired samples**:
   ```
   dt = duration / desired_samples
   
   Smooth plots: 2,000-10,000 samples
   Acceptable: 500-2,000 samples
   Coarse: 100-500 samples
   ```

3. **Performance constraint**:
   ```
   If simulation too slow: increase dt (fewer samples)
   If missing dynamics: decrease dt (more samples)
   ```

---

## UI Enhancement Proposal

### Add "Samples" Display

Current UI:
```
Duration: [100.0] seconds
Time step: ○ Auto  ○ Manual [0.1]
```

Proposed UI:
```
Duration: [100.0] seconds
Time step: ○ Auto  ○ Manual [0.1]

Estimated samples: 1,000  ← Add this!
Sampling interval: 0.1s   ← Add this!

For stochastic rates:
  λ=1.0 → ~10 samples/event
  λ=10.0 → ~1 samples/event ⚠ Consider dt=0.01s
```

### Add Warnings

```python
def validate_dt_for_stochastic(model, dt):
    """Warn user if dt too large for stochastic transitions."""
    
    stochastic_transitions = [t for t in model.transitions 
                             if t.transition_type == 'stochastic']
    
    if not stochastic_transitions:
        return None  # No stochastic, no problem
    
    max_rate = max(t.rate for t in stochastic_transitions)
    mean_interval = 1.0 / max_rate
    
    if dt > mean_interval / 2:
        return (f"⚠ Time step ({dt}s) may be too large for fastest "
                f"stochastic transition (λ={max_rate}, interval={mean_interval:.3f}s). "
                f"Consider dt ≤ {mean_interval/10:.3f}s for better sampling.")
    
    return None
```

---

## Testing Checklist

### Phase 1: Simple Source (Token Generation)
- [ ] Create single source transition model
- [ ] Test with dt = [0.001, 0.01, 0.1, 1.0]
- [ ] Verify tokens accumulate linearly (on average)
- [ ] Check burst sizes recorded correctly
- [ ] Plot token history (should be stepwise increasing)

### Phase 2: Source-Sink (Equilibrium)
- [ ] Create source-sink pair model
- [ ] Test with medium dt = 0.05s
- [ ] Verify equilibrium reached
- [ ] Check oscillations around mean
- [ ] Measure time to equilibrium

### Phase 3: Two-Place Oscillator
- [ ] Create circular transfer model
- [ ] Test with fine dt = 0.01s
- [ ] Verify anti-phase oscillations
- [ ] Check token conservation (sum constant)
- [ ] Measure oscillation period

### Phase 4: dt Effect Analysis
- [ ] Run same model with multiple dt values
- [ ] Compare final tokens (should be similar)
- [ ] Compare computation time (should scale with 1/dt)
- [ ] Compare plot quality (finer dt = smoother)
- [ ] Document optimal dt range

### Phase 5: UI Testing
- [ ] Test automatic dt calculation
- [ ] Test manual dt input
- [ ] Verify validation warnings
- [ ] Check estimated samples display
- [ ] Test with very small/large dt

---

## Expected Issues and Solutions

### Issue 1: Simulation Too Slow

**Symptom**: Long wait for completion, high step count

**Cause**: dt too small (too many steps)

**Solution**:
```python
# Increase dt (coarser sampling)
sim.settings.dt_manual = 0.1  # Instead of 0.01
```

---

### Issue 2: Missing Rapid Token Changes

**Symptom**: Plot looks blocky, missing oscillations

**Cause**: dt too large (under-sampling)

**Solution**:
```python
# Decrease dt (finer sampling)
sim.settings.dt_manual = 0.01  # Instead of 0.1
```

---

### Issue 3: Stochastic Transitions Not Firing

**Symptom**: Expected firings not occurring

**Possible Causes**:
1. Insufficient tokens for burst
2. Not scheduled (enablement issue)
3. dt larger than firing interval

**Debugging**:
```python
# Check transition state
behavior = sim._get_behavior(transition)
info = behavior.get_stochastic_info()

print(f"Rate: {info['rate']}")
print(f"Mean delay: {info['mean_delay']}")
print(f"Scheduled: {info['scheduled_fire_time']}")
print(f"Can fire: {behavior.can_fire()}")
```

---

### Issue 4: Unrealistic Token Accumulation

**Symptom**: Tokens grow without bound

**Cause**: Source without sink, or imbalanced rates

**Solution**:
```python
# Add sink transition or balance rates
T_source.rate = 1.0
T_sink.rate = 1.0  # Match for equilibrium
```

---

## Summary

### Key Concepts

1. **dt (time step)** = **Token sampling window**
   - How often we record place markings
   - Simulation resolution

2. **Smaller dt** = More accurate, but slower
3. **Larger dt** = Faster, but may miss dynamics

4. **Automatic mode**: `dt = duration / 1000` (good default)
5. **Manual mode**: Set based on transition rates

### Recommended Workflow

```
1. Start with automatic dt
2. Run simulation, observe results
3. If plots too coarse → decrease dt manually
4. If simulation too slow → increase dt manually
5. For stochastic: dt ≤ (1/λ_max) / 10
```

### Testing Priority

✅ **MUST TEST**:
1. Simple source transition (token generation)
2. Different dt values (0.01, 0.1, 1.0)
3. Verify token histories recorded correctly

📝 **SHOULD TEST**:
4. Source-sink equilibrium
5. Oscillator model
6. dt effect on computation time

🔬 **NICE TO HAVE**:
7. Multiple stochastic transitions
8. Complex BioModels pathways
9. Performance benchmarking

---

**Next Steps**:
1. Create simple test nets (source, source-sink, oscillator)
2. Test with various dt settings
3. Document observations
4. Consider UI enhancements for dt guidance

---

**References**:
- `src/shypn/engine/stochastic_behavior.py` - Stochastic firing logic
- `src/shypn/engine/simulation/settings.py` - dt configuration
- `src/shypn/engine/simulation/controller.py` - Simulation loop
- `ui/dialogs/simulation_settings.ui` - UI for dt parameter
