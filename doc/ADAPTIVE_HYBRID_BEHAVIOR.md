# Adaptive Hybrid Behavior - Runtime ODE/Stochastic Switching

## Overview

**AdaptiveHybridBehavior** automatically selects between continuous (ODE) and stochastic (τ-leaping/SSA) execution based on **molecular population size** (tokens × compartment_volume) **at runtime**.

## Biological Motivation

Real biological systems operate across different regimes:
- **Few molecules (< 100)**: Stochastic noise dominates → Use discrete SSA/τ-leaping
- **Many molecules (> 1000)**: Deterministic approximation valid → Use continuous ODE

This matches how advanced hybrid simulation algorithms work in computational systems biology.

## How It Works

### Mode Selection (Runtime)

```python
# Creates BOTH continuous and stochastic behavior delegates
behavior = AdaptiveHybridBehavior(transition, model)

# Every simulation step:
places = behavior._get_connected_places()

# Calculate molecule count for each place
molecule_counts = [p.tokens * p.compartment_volume for p in places]
min_molecules = min(molecule_counts)

if min_molecules < 100:  # molecule threshold
    mode = 'stochastic'  # → Delegates to StochasticBehavior
else:
    mode = 'continuous'  # → Delegates to ContinuousBehavior
```

### Integration with Existing Engines

**Stochastic mode**: Uses existing τ-leaping engine
```python
# Scheduler calls:
behavior.fire(...)
# ↓ Delegates to:
stochastic_behavior.fire(...)  # Discrete burst firing
```

**Continuous mode**: Uses existing RK4 integrator
```python
# Scheduler calls:
behavior.integrate_step(dt, ...)
# ↓ Delegates to:
continuous_behavior.integrate_step(dt, ...)  # Smooth ODE integration
```

### Mode Switching

When mode changes at runtime:
1. Detects molecule count change (as tokens change)
2. Logs mode transition
3. Clears stochastic scheduling state if switching away
4. Seamlessly continues with new method

```python
# Simulation running with 50 molecules (10 mM × 5 fL)
# → Uses stochastic (discrete events)

# ... reaction produces more molecules ...
place.tokens = 500  # 500 mM concentration
# molecule_count = 500 × 5 fL = 2500 molecules

# Next step automatically switches
# → Uses continuous (smooth ODE)
```

## Usage

### Creating Adaptive Transitions

```python
transition = Transition(..., transition_type='adaptive')
transition.properties = {
    'volume_threshold': 100,  # Molecule count threshold (not fL!)
    'prefer_continuous': True,
    'rate_function': '5.0 * P1',
    'max_burst': 8  # For stochastic mode
}
```

### Querying Current Mode

```python
info = behavior.get_adaptive_info()
# {
#   'molecule_threshold': 100,
#   'current_mode': 'stochastic',  # or 'continuous'
#   'last_molecule_check': {...},
#   'continuous_info': {...},
#   'stochastic_info': {...}
# }
```

## Implementation Details

### Class Structure

```python
class AdaptiveHybridBehavior(TransitionBehavior):
    def __init__(self, transition, model):
        self.continuous_behavior = ContinuousBehavior(...)
        self.stochastic_behavior = StochasticBehavior(...)
        self.volume_selector = VolumeAdaptiveSelector(threshold_fL=1.0)
    
    def can_fire(self):
        mode = self._select_mode()  # Check volumes
        if mode == 'stochastic':
            return self.stochastic_behavior.can_fire()
        else:
            return self.continuous_behavior.can_fire()
    
    def fire(self, ...):
        mode = self._select_mode()
        if mode == 'stochastic':
            return self.stochastic_behavior.fire(...)
        else:
            return False  # Use integrate_step for continuous
    
    def integrate_step(self, dt, ...):
        mode = self._select_mode()
        if mode == 'continuous':
            return self.continuous_behavior.integrate_step(dt, ...)
        else:
            # Check if stochastic fires within dt
            return self._handle_stochastic_within_interval(dt, ...)
```

### State Management

- **Continuous mode**: No scheduling state needed
- **Stochastic mode**: Tracks `enablement_time`, `scheduled_fire_time`, `sampled_burst`
- **Mode switches**: Preserves token state, resets scheduling

### Integration with Simulation Controller

The controller already handles hybrid models (continuous + stochastic):
- Calls `integrate_step()` for continuous phase
- Calls τ-leaping engine for stochastic phase

Adaptive transitions work in BOTH phases:
- Continuous phase: Behavior delegates to continuous or handles stochastic events within dt
- Stochastic phase: τ-leaping engine treats adaptive as stochastic

## Comparison with Fixed Types

| Feature | Fixed Type | Adaptive Type |
|---------|-----------|---------------|
| Mode selection | Design time | Runtime |
| Volume changes | Ignored | Detected automatically |
| Method switch | Never | Dynamic |
| Biological realism | Assumes constant regime | Matches molecular dynamics |
| Computational efficiency | Fixed (may be inefficient) | Optimal for current state |

## Testing

```bash
python dev/test_adaptive_hybrid.py
```

**Test results**:
- ✓ Runtime mode selection based on volume
- ✓ Dynamic switching during simulation
- ✓ Integration with continuous and stochastic behaviors
- ✓ State consistency across mode changes

## Example: Ca²⁺ Signaling

```python
# Cytoplasmic Ca²⁺ (small volume → stochastic)
ca_cyto = Place(...)
ca_cyto.compartment_volume = 0.8  # fL
ca_cyto.tokens = 50  # Few molecules

# ER Ca²⁺ store (large volume → continuous)
ca_er = Place(...)
ca_er.compartment_volume = 100.0  # fL
ca_er.tokens = 50000  # Many molecules

# Release transition (adaptive)
release = Transition(..., transition_type='adaptive')

# Simulation:
# - Initial: Few Ca²⁺ → Uses stochastic (burst events)
# - After release: Many Ca²⁺ → Switches to continuous (smooth wave)
```

This matches real biology: Calcium sparks (discrete) → Calcium waves (continuous).

## Future Enhancements

1. **Token-based threshold**: Switch based on molecular counts instead of volume
2. **Hybrid propensity**: Weighted selection based on multiple criteria
3. **Adaptive τ-leaping**: Adjust epsilon based on molecular counts
4. **Performance monitoring**: Track efficiency gains from adaptivity

## Related Features

- **Spatial signal properties** (Layer 1): Provide `compartment_volume` for mode selection
- **τ-leaping engine**: Handles stochastic mode execution
- **RK4 integrator**: Handles continuous mode execution
- **VolumeAdaptiveSelector**: Utility class for volume-based decisions

---

**Status**: ✅ Implemented and tested (2026-02-03)
**Commit**: `2f29bf3` - feat: Implement adaptive hybrid behavior
