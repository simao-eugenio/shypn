# Function Catalog for Transition Rate Expressions

## Overview

The **Function Catalog** provides a comprehensive library of ready-to-use mathematical functions that users can employ in transition rate expressions. This includes activation functions, growth models, kinetic equations, distribution functions, and utility functions.

## Key Features

✅ **30+ Pre-defined Functions**: Sigmoid, exponential, Michaelis-Menten, distributions, and more  
✅ **NumPy Integration**: Full access to numpy's mathematical capabilities  
✅ **Dict Format Support**: Use `{'rate': lambda places, t: ...}` format  
✅ **String Expressions**: Simple expressions like `"sigmoid(time, 10, 0.5)"`  
✅ **Place References**: Access tokens via `P1`, `P2`, etc.  
✅ **Time-Dependent**: Use `time` or `t` variable

## Usage Formats

### 1. **String Expression** (Recommended for Simple Cases)
```python
transition.properties = {
    'rate_function': "sigmoid(time, 10, 0.5)"
}
```

### 2. **Dict Format with Lambda** (Flexible)
```python
transition.properties = {
    'rate': lambda places, t: sigmoid(t, 10, 0.5)
}
```

### 3. **Dict Format in transition.rate** (UI Compatible)
```python
transition.rate = {
    'rate': lambda places, t: michaelis_menten(places[1].tokens, 10, 5)
}
```

### 4. **Direct Callable**
```python
def my_rate_function(places, time):
    return sigmoid(time, 10, 0.5) * places[1].tokens

transition.properties = {
    'rate_function': my_rate_function
}
```

## Available Functions

### 🔄 Activation Functions (S-curves and Transitions)

#### `sigmoid(x, center=0, steepness=1, amplitude=1)`
Logistic sigmoid function (S-curve).

**Formula**: $\sigma(x) = \frac{A}{1 + e^{-k(x - x_0)}}$

**Examples**:
```python
# String format
"sigmoid(time, 20, 0.5, 10)"

# Dict format
{'rate': lambda p, t: sigmoid(t, 20, 0.5, 10)}

# With place tokens
"sigmoid(P1, 50, 0.1, 5)"
```

**Use Cases**:
- Smooth startup/shutdown transitions
- Learning curves
- Market adoption models
- Phase transitions

#### `tanh_activation(x, center=0, steepness=1, amplitude=1)`
Hyperbolic tangent activation (symmetric S-curve).

**Examples**:
```python
"tanh_activation(time, 10, 0.3, 5)"
{'rate': lambda p, t: tanh_activation(t - 10, 0, 0.5, 8)}
```

#### `relu(x, threshold=0)`
Rectified Linear Unit.

**Examples**:
```python
# Activate only when P1 > 10
"relu(P1, 10)"
{'rate': lambda p, t: relu(p[1].tokens, 10)}
```

#### `softplus(x, beta=1)`
Smooth approximation of ReLU.

**Examples**:
```python
"softplus(P1, 0.5)"
```

### 📈 Growth Models

#### `exponential_growth(x, rate)`
Exponential growth/decay.

**Formula**: $\frac{dx}{dt} = rx$

**Examples**:
```python
# 10% growth rate
"exponential_growth(P1, 0.1)"

# Dict format with 5% decay
{'rate': lambda p, t: exponential_growth(p[1].tokens, -0.05)}
```

**Use Cases**:
- Population growth
- Compound interest
- Radioactive decay

#### `logistic_growth(x, carrying_capacity, growth_rate)`
Logistic growth with carrying capacity.

**Formula**: $\frac{dx}{dt} = rx(1 - \frac{x}{K})$

**Examples**:
```python
# Population limited to 100
"logistic_growth(P1, 100, 0.1)"

# Dict format
{'rate': lambda p, t: logistic_growth(p[1].tokens, 100, 0.1)}
```

**Use Cases**:
- Limited resource growth
- Population dynamics
- Market saturation

#### `gompertz_growth(x, carrying_capacity, growth_rate)`
Gompertz growth model (asymmetric S-curve).

**Examples**:
```python
# Tumor growth model
"gompertz_growth(P1, 100, 0.05)"
```

**Use Cases**:
- Tumor growth
- Organism growth
- Technology adoption

### 🧪 Kinetic Models (Enzyme and Reaction Kinetics)

#### `michaelis_menten(substrate, vmax, km)`
Michaelis-Menten enzyme kinetics.

**Formula**: $V = \frac{V_{max}[S]}{K_m + [S]}$

**Examples**:
```python
# Enzyme reaction
"michaelis_menten(P1, 10, 5)"

# Dict format
{'rate': lambda p, t: michaelis_menten(p[1].tokens, 10, 5)}

# Multiple substrates
"michaelis_menten(P1, 10, 5) + michaelis_menten(P2, 8, 3)"
```

**Parameters**:
- `substrate`: Substrate concentration (tokens in place)
- `vmax`: Maximum reaction velocity
- `km`: Michaelis constant (concentration at half-maximum velocity)

**Use Cases**:
- Enzyme catalysis
- Drug metabolism
- Receptor binding

#### `hill_equation(substrate, vmax, kd, n=1)`
Hill equation (cooperative binding).

**Formula**: $V = \frac{V_{max}[S]^n}{K_d^n + [S]^n}$

**Examples**:
```python
# Cooperative binding with n=2.5
"hill_equation(P1, 10, 5, 2.5)"

# Dict format
{'rate': lambda p, t: hill_equation(p[1].tokens, 10, 5, 2.5)}
```

**Parameters**:
- `n`: Hill coefficient (cooperativity)
  - n = 1: No cooperativity (same as Michaelis-Menten)
  - n > 1: Positive cooperativity (sharper response)
  - n < 1: Negative cooperativity

**Use Cases**:
- Hemoglobin oxygen binding
- Transcription factor binding
- Allosteric enzymes

#### `competitive_inhibition(substrate, inhibitor, vmax, km, ki)`
Competitive enzyme inhibition.

**Examples**:
```python
# Substrate in P1, inhibitor in P2
"competitive_inhibition(P1, P2, 10, 5, 2)"

# Dict format
{'rate': lambda p, t: competitive_inhibition(p[1].tokens, p[2].tokens, 10, 5, 2)}
```

#### `mass_action(reactant1, reactant2=1, rate_constant=1)`
Mass action kinetics.

**Formula**: $\text{rate} = k[A][B]$

**Examples**:
```python
# Bimolecular reaction
"mass_action(P1, P2, 0.1)"

# Unimolecular reaction
"mass_action(P1, 1, 0.5)"
```

### 📊 Distribution Functions (Probability Densities)

#### `normal_pdf(x, mean=0, std=1)`
Normal (Gaussian) probability density function.

**Examples**:
```python
# Bell curve centered at t=10
"10 * normal_pdf(time, 10, 2)"

# Dict format with place-dependent mean
{'rate': lambda p, t: 5 * normal_pdf(t, p[1].tokens, 3)}
```

**Use Cases**:
- Transient bursts of activity
- Measurement noise
- Natural variation

#### `exponential_pdf(x, rate=1)`
Exponential probability density function.

**Examples**:
```python
"exponential_pdf(time, 0.5)"
```

#### `gamma_pdf(x, shape, scale=1)`
Gamma probability density function.

**Examples**:
```python
"gamma_pdf(time, 2, 3)"
```

#### `uniform(x, low=0, high=1)`
Uniform distribution (constant within range).

**Examples**:
```python
# Constant rate between t=5 and t=15
"10 * uniform(time, 5, 15)"
```

### 🎛️ Utility Functions (Control and Timing)

#### `step(x, threshold, low=0, high=1)`
Step function (Heaviside function).

**Examples**:
```python
# Jump from 0 to 10 at t=15
"step(time, 15, 0, 10)"

# Conditional based on tokens
"step(P1, 50, 1, 10)"
```

#### `ramp(x, start, end, low=0, high=1)`
Linear ramp function.

**Examples**:
```python
# Linear increase from 0 to 10 between t=5 and t=15
"ramp(time, 5, 15, 0, 10)"

# Dict format
{'rate': lambda p, t: ramp(t, 5, 15, 0, 10)}
```

#### `pulse(x, start, end, amplitude=1)`
Rectangular pulse function.

**Examples**:
```python
# Pulse of rate 10 from t=5 to t=15
"pulse(time, 5, 15, 10)"

# Multiple pulses
"pulse(time, 5, 10, 5) + pulse(time, 20, 25, 8)"
```

#### `periodic_pulse(x, period, duty_cycle=0.5, amplitude=1)`
Periodic pulse train (square wave).

**Examples**:
```python
# Square wave: period 10, 50% duty cycle, amplitude 5
"periodic_pulse(time, 10, 0.5, 5)"

# 30% duty cycle
"periodic_pulse(time, 20, 0.3, 8)"
```

#### `triangle_wave(x, period, amplitude=1)`
Triangle wave function.

**Examples**:
```python
"triangle_wave(time, 20, 10)"
```

#### `sawtooth_wave(x, period, amplitude=1)`
Sawtooth wave function.

**Examples**:
```python
"sawtooth_wave(time, 15, 8)"
```

### 🔗 Combined/Complex Functions

#### `double_sigmoid(x, center1, center2, steepness1=1, steepness2=1, amplitude=1)`
Double sigmoid (two-phase activation).

**Examples**:
```python
# Two-phase activation
"double_sigmoid(time, 10, 30, 0.5, 0.5, 10)"
```

#### `bell_curve(x, center, width, amplitude=1)`
Bell-shaped curve (Gaussian envelope).

**Examples**:
```python
# Transient burst centered at t=20
"bell_curve(time, 20, 5, 10)"
```

#### `bounded_linear(x, slope, intercept=0, min_val=0, max_val=inf)`
Linear function with bounds.

**Examples**:
```python
# Linear growth capped at 10
"bounded_linear(P1, 0.5, 1, 0, 10)"
```

### 🛠️ Helper Utilities

#### `interpolate(x, x_points, y_points)`
Linear interpolation between points.

**Examples**:
```python
# Custom curve through points
"interpolate(time, [0, 10, 20, 30], [0, 5, 8, 10])"
```

#### `smooth_threshold(x, threshold, width)`
Smooth threshold function (soft step).

**Examples**:
```python
# Smooth activation around 10 tokens
"10 * smooth_threshold(P1, 10, 2)"
```

## Complete Examples

### Example 1: Enzyme Reaction with Sigmoid Activation

```python
transition.properties = {
    'rate_function': "sigmoid(time, 10, 0.5, 1) * michaelis_menten(P1, 10, 5)"
}
```
**Behavior**: Enzyme reaction that starts slowly (sigmoid), then follows Michaelis-Menten kinetics.

### Example 2: Dict Format with Complex Logic

```python
transition.rate = {
    'rate': lambda places, t: (
        sigmoid(t, 20, 0.5, 10) *  # Smooth startup
        michaelis_menten(places[1].tokens, 15, 8) *  # Enzyme kinetics
        (1.0 if places[2].tokens > 5 else 0.5)  # Conditional factor
    )
}
```

### Example 3: Population Growth with Logistic Limit

```python
transition.properties = {
    'rate_function': "logistic_growth(P1, 100, 0.1)"
}
```
**Behavior**: Population grows exponentially initially, then saturates at carrying capacity of 100.

### Example 4: Periodic Production with Bell Curve Envelope

```python
transition.properties = {
    'rate_function': "periodic_pulse(time, 10, 0.5, 5) * bell_curve(time, 50, 20, 1)"
}
```
**Behavior**: Square wave production that peaks at t=50 and fades away.

### Example 5: Cooperative Binding with Hill Equation

```python
transition.properties = {
    'rate_function': "hill_equation(P1, 10, 20, 2.5)"
}
```
**Behavior**: Cooperative binding (n=2.5) creates sharp threshold around 20 tokens.

### Example 6: Two-Substrate Reaction

```python
transition.rate = {
    'rate': lambda p, t: mass_action(p[1].tokens, p[2].tokens, 0.1)
}
```
**Behavior**: Reaction rate proportional to product of two substrate concentrations.

### Example 7: Time-Varying Activation

```python
transition.properties = {
    'rate_function': "ramp(time, 0, 10, 0, 5) + 3 * normal_pdf(time, 20, 3)"
}
```
**Behavior**: Linear ramp-up from 0-10, then transient burst at t=20.

### Example 8: Competitive Inhibition Model

```python
transition.rate = {
    'rate': lambda p, t: competitive_inhibition(
        p[1].tokens,  # Substrate
        p[2].tokens,  # Inhibitor
        vmax=15,
        km=10,
        ki=5
    )
}
```
**Behavior**: Enzyme reaction slowed by competitive inhibitor in P2.

## Advanced Usage

### Combining Multiple Functions

```python
# String format
"sigmoid(time, 10, 0.5, 1) * michaelis_menten(P1, 10, 5) * step(P2, 20, 0, 1)"

# Dict format
{'rate': lambda p, t: (
    sigmoid(t, 10, 0.5, 1) *
    michaelis_menten(p[1].tokens, 10, 5) *
    step(p[2].tokens, 20, 0, 1)
)}
```

### Using NumPy Functions

```python
# String format (np is available)
"10 * np.exp(-0.1 * time)"
"5 + 3 * np.sin(0.5 * time)"
"np.sqrt(P1) * 2"

# Dict format
{'rate': lambda p, t: 10 * np.exp(-0.1 * t)}
```

### Custom Conditional Logic

```python
# Dict format allows full Python logic
transition.rate = {
    'rate': lambda p, t: (
        10 if p[1].tokens > 50 else
        5 if p[1].tokens > 20 else
        1
    )
}
```

### Accessing Multiple Places

```python
# String format
"0.5 * P1 * P2 / (P1 + P2 + 1)"

# Dict format
{'rate': lambda p, t: 0.5 * p[1].tokens * p[2].tokens / (p[1].tokens + p[2].tokens + 1)}
```

## Available Variables and Modules

When evaluating rate functions, the following are available:

### Variables
- `time` or `t`: Current simulation time
- `P1`, `P2`, `P3`, ...: Tokens in places (by ID)

### Modules
- `math`: Python math module (exp, log, sin, cos, sqrt, etc.)
- `np` or `numpy`: NumPy module (full functionality)
- `min`, `max`, `abs`: Built-in functions

### Catalog Functions
All 30+ functions from the catalog are directly available:
- `sigmoid`, `tanh`, `relu`, `softplus`
- `exponential_growth`, `logistic_growth`, `gompertz_growth`
- `michaelis_menten`, `hill_equation`, `mass_action`
- `normal_pdf`, `exponential_pdf`, `gamma_pdf`
- `step`, `ramp`, `pulse`, `bell_curve`
- And many more...

## Function Catalog Reference

### Quick Reference Table

| Category | Functions |
|----------|-----------|
| **Activation** | sigmoid, tanh_activation, relu, leaky_relu, softplus |
| **Growth** | exponential_growth, exponential_decay, logistic_growth, gompertz_growth |
| **Kinetics** | michaelis_menten, hill_equation, competitive_inhibition, mass_action |
| **Distributions** | normal_pdf, exponential_pdf, gamma_pdf, uniform |
| **Utility** | step, ramp, pulse, periodic_pulse, triangle_wave, sawtooth_wave |
| **Combined** | double_sigmoid, bell_curve, bounded_linear |
| **Helpers** | interpolate, smooth_threshold |

### Getting Function Documentation

```python
from shypn.engine.function_catalog import get_function_info, list_functions

# List all available functions
functions = list_functions()
print(functions)

# Get documentation for specific function
info = get_function_info('sigmoid')
print(info)
```

## Best Practices

### 1. **Start Simple**
Begin with constant or simple linear rates, then add complexity:
```python
"5.0"  # Constant
"2 * P1"  # Linear
"sigmoid(time, 10, 0.5, 1) * michaelis_menten(P1, 10, 5)"  # Complex
```

### 2. **Use Dict Format for Complex Logic**
When you need conditionals or multi-step calculations, dict format is clearer:
```python
{'rate': lambda p, t: (
    michaelis_menten(p[1].tokens, 10, 5)
    if t > 10 else 0
)}
```

### 3. **Test Functions Independently**
Test individual components before combining:
```python
# Test sigmoid alone
"sigmoid(time, 10, 0.5, 10)"

# Then combine
"sigmoid(time, 10, 0.5, 1) * P1"
```

### 4. **Use Catalog Functions**
Prefer catalog functions over manual implementations:
```python
# Good
"michaelis_menten(P1, 10, 5)"

# Avoid (error-prone)
"10 * P1 / (5 + P1)"
```

### 5. **Handle Edge Cases**
Be aware of division by zero and negative values:
```python
# Safe
"michaelis_menten(P1, 10, 5)"  # Built-in safety

# Potentially unsafe
"P1 / P2"  # What if P2 is 0?

# Better
"P1 / (P2 + 0.001)"  # Add small epsilon
```

## Troubleshooting

### Error: "Rate function evaluation error"

**Cause**: Expression contains syntax errors or undefined variables

**Solutions**:
- Check spelling of function names
- Verify place IDs (P1, P2, etc. must match actual places)
- Test expression in Python console first
- Check for balanced parentheses

### Rate Always Returns 0

**Cause**: Exception in evaluation, falling back to 0

**Solutions**:
- Check console logs for error messages
- Verify all referenced places exist
- Ensure math operations are valid (no division by zero)

### Function Not Found

**Cause**: Using non-existent catalog function

**Solutions**:
- Use `list_functions()` to see available functions
- Check spelling and capitalization
- Import function catalog if using dict format

## Performance Considerations

### Evaluation Frequency
Rate functions are evaluated **every time step** during continuous integration (typically 10-100 times per second).

### Optimization Tips

1. **Avoid expensive operations**: Use catalog functions instead of complex manual calculations
2. **Cache constant values**: Use dict format to cache unchanging values
3. **Simplify expressions**: Combine constants before simulation

```python
# Less efficient
"sigmoid(time, 10, 0.5, 1) * 2 * 5"

# More efficient
"sigmoid(time, 10, 0.5, 10)"  # Pre-multiply 2*5=10
```

## Summary

The Function Catalog provides:

✅ **30+ Ready-to-Use Functions**: Comprehensive library of common patterns  
✅ **Multiple Input Formats**: String expressions, dict format, callables  
✅ **NumPy Integration**: Full scientific computing capabilities  
✅ **Biological Models**: Enzyme kinetics, growth models, binding equations  
✅ **Control Functions**: Steps, ramps, pulses, waves  
✅ **Distribution Functions**: Normal, exponential, gamma, uniform  
✅ **Easy Composition**: Combine functions to create complex behaviors  

Use the catalog to express sophisticated rate functions without manual implementation, ensuring correctness and readability in your Petri net models!
