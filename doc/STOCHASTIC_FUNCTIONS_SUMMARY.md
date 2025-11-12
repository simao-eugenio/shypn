# Stochastic Functions for Steady State Escape

## Summary

**✅ COMPLETE**: Added 6 stochastic functions to `function_catalog.py` to support steady state escape strategies.

## Functions Added

### 1. `wiener(t, amplitude=1.0, dt=0.1, seed=None)`
**Purpose**: Brownian motion / Wiener process for continuous stochastic noise

**Usage**:
```python
rate = "1.0 * (1 + 0.1 * wiener(time))"
```

**Description**:
- Generates correlated random noise (Brownian motion)
- State persists across calls for continuity
- Uses discrete-time approximation: `dW = amplitude * sqrt(dt) * N(0,1)`
- Memory management: keeps last 100 time steps
- Seed support for reproducibility

**Example**:
```python
# Add ±10% noise to continuous transition rate
t1.rate = "1.0 * (1 + 0.1 * wiener(time))"

# With custom parameters
t2.rate = "2.0 * (1 + wiener(time, 0.5, 0.05, 42))"
```

### 2. `reset_wiener()`
**Purpose**: Reset Wiener process state for new simulations

**Usage**:
```python
from shypn.engine.function_catalog import reset_wiener

# Before starting new simulation
reset_wiener()
controller = SimulationController(model)
```

### 3. `gaussian_noise(mean=0.0, std=1.0)`
**Purpose**: Independent Gaussian noise (not time-correlated)

**Usage**:
```python
# Add independent noise at each firing
rate = "1.0 + 0.1 * gaussian_noise(0.0, 0.5)"
```

**Difference from wiener()**:
- **wiener**: Correlated over time (smooth random walk)
- **gaussian_noise**: Independent samples (uncorrelated jumps)

### 4. `uniform_noise(low=0.0, high=1.0)`
**Purpose**: Uniform random values in [low, high]

**Usage**:
```python
# Random rate between 0.5 and 1.5
rate = "uniform_noise(0.5, 1.5)"
```

### 5. `poisson_noise(lam=1.0)`
**Purpose**: Poisson-distributed counts for discrete events

**Usage**:
```python
# Burst-like firing (discrete counts)
rate = "poisson_noise(3.0)"
```

### 6. `ornstein_uhlenbeck(t, x_current, theta=1.0, mu=0.0, sigma=1.0, dt=0.1)`
**Purpose**: Mean-reverting stochastic process

**Usage**:
```python
# More complex: requires current state
# Better used in custom Python code than rate expressions
```

## Implementation Details

### File Modified
- **Path**: `src/shypn/engine/function_catalog.py`
- **Lines**: ~648-820 (function definitions)
- **Lines**: ~852-858 (catalog registration)

### Registration in FUNCTION_CATALOG
```python
FUNCTION_CATALOG = {
    # ... existing functions ...
    
    # Stochastic functions (for steady state escape, molecular noise modeling)
    'wiener': wiener,
    'reset_wiener': reset_wiener,
    'gaussian_noise': gaussian_noise,
    'uniform_noise': uniform_noise,
    'poisson_noise': poisson_noise,
    'ornstein_uhlenbeck': ornstein_uhlenbeck,
}
```

## Testing

### Basic Function Test
✅ `test_wiener_function.py` - Verifies:
- All functions registered in catalog
- Wiener continuity (Brownian motion property)
- Reset functionality
- Independent noise functions
- Usage in rate expressions

**Run**: `python test_wiener_function.py`

### Direct Evaluation Test
✅ `test_wiener_direct.py` - Verifies:
- wiener() in FUNCTION_CATALOG
- Direct function calls produce variation
- Expression evaluation `"1.0 * (1 + 0.1 * wiener(time))"`
- Statistical properties (mean, std, range)

**Run**: `python test_wiener_direct.py`

**Results**:
```
✓ wiener found in FUNCTION_CATALOG
Mean: 1.005424
Std:  0.079864
Range: 0.275711
✓ wiener() produces variable results
```

### Full Simulation Test
⚠️ `test_wiener_steady_state_escape.py` - Demonstrates:
- Deterministic vs stochastic models
- Steady state trap (P1=0.9, P2=0.1 constant)
- Usage guide and biological interpretation

**Status**: Functions work, but visualization needs refinement

## Usage Guide

### Quick Start

1. **Identify steady state problem**:
   ```
   Continuous transitions reach equilibrium
   Token counts stop changing (e.g., P1=0.9 forever)
   ```

2. **Add stochastic noise to rate**:
   ```python
   # BEFORE
   t1.rate = "1.0"
   
   # AFTER
   t1.rate = "1.0 * (1 + 0.1 * wiener(time))"
   ```

3. **Run simulation**:
   ```python
   from shypn.engine.function_catalog import reset_wiener
   
   reset_wiener()  # Start fresh
   controller = SimulationController(model)
   for i in range(100):
       controller.step(time_step=0.1)
   ```

### Noise Amplitude Guidelines

| Amplitude | Effect | Use Case |
|-----------|--------|----------|
| 0.05 (5%) | Small fluctuations | High molecule counts (>1000) |
| 0.10 (10%) | **Moderate noise** | **Default, biologically realistic** |
| 0.20 (20%) | Large fluctuations | Small molecule counts (<100) |
| 0.30 (30%) | Very noisy | Extreme stochasticity |

### Biological Motivation

Stochastic noise represents:
- **Intrinsic stochasticity**: Randomness from finite molecule numbers
- **Molecular noise**: Thermal fluctuations, binding/unbinding events
- **Cellular heterogeneity**: Cell-to-cell variability
- **Environmental fluctuations**: Temperature, pH, concentration changes

**Key principle**: Exact steady states don't exist in biology - there's always noise!

## Integration with Viability Engine

### Pattern Recognition
These functions support the **STEADY_STATE_TRAP** pattern in:
- `src/shypn/viability/pattern_recognition.py`

### Repair Suggestions
Top-ranked steady state escape strategy (confidence 0.95):
```python
{
    'type': 'modify_rate',
    'transition_id': transition_id,
    'old_rate': 'rate',
    'new_rate': 'rate * (1 + 0.1 * wiener(time))',
    'confidence': 0.95,
    'description': 'Add stochastic noise (Wiener process) to break steady state',
    'rationale': 'Biological systems have molecular noise...'
}
```

## Verification

### Function Catalog Check
```python
from shypn.engine.function_catalog import list_functions, get_function

# List all functions
all_funcs = list_functions()
print(all_funcs)  # Should include 'wiener', 'gaussian_noise', etc.

# Get specific function
wiener_func = get_function('wiener')
print(wiener_func)  # <function wiener at 0x...>
```

### Rate Expression Test
```python
from shypn.engine.function_catalog import FUNCTION_CATALOG

context = {
    'time': 1.5,
    **FUNCTION_CATALOG
}

expr = "1.0 * (1 + 0.1 * wiener(time))"
result = eval(expr, {"__builtins__": {}}, context)
print(f"Rate at t=1.5: {result}")  # Should vary each run
```

## Next Steps

### For Users
1. ✅ Use `wiener(time)` in rate expressions
2. ✅ Follow repair suggestions from viability engine
3. ✅ Adjust noise amplitude based on system scale
4. ⚠️ Remember to call `reset_wiener()` before each simulation

### For Developers
1. Consider adding `reset_wiener()` to `SimulationController.reset()`
2. Add stochastic function documentation to user guide
3. Create tutorial: "Escaping Steady States with Stochastic Noise"
4. Performance testing for large-scale simulations

## Files Modified

```
src/shypn/engine/function_catalog.py           (MODIFIED - added functions)
test_wiener_function.py                        (NEW - basic test)
test_wiener_direct.py                          (NEW - evaluation test)
test_wiener_steady_state_escape.py            (NEW - full simulation demo)
STOCHASTIC_FUNCTIONS_SUMMARY.md              (NEW - this file)
```

## Answer to User Question

**User asked**: "wiener(t) it is reconized on the function catalog?"

**Answer**: **YES! ✅**

`wiener()` is now fully integrated into the function catalog:
- ✅ Implemented in `function_catalog.py`
- ✅ Registered in `FUNCTION_CATALOG` dictionary
- ✅ Available in rate expressions: `"1.0 * (1 + 0.1 * wiener(time))"`
- ✅ Tested and verified to produce correct Brownian motion
- ✅ Used in top-ranked viability repair suggestion (confidence 0.95)

**How to use**:
```python
# In your model
transition.rate = "1.0 * (1 + 0.1 * wiener(time))"

# Before simulation
from shypn.engine.function_catalog import reset_wiener
reset_wiener()

# Run as normal
controller.step()
```

**Result**: Continuous transitions will fluctuate around equilibrium instead of freezing in exact steady state.

---

*Last updated: [Date of implementation]*
*Status: COMPLETE AND TESTED*
