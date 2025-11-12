# Adding Wiener Noise to Complex Rate Functions

## Problem

Heuristics insert complex rate functions like:
```python
rate = "michaelis_menten(P17, vmax=70.0, km=0.1)"
```

How to add stochastic noise (wiener) to these?

## Solutions

### Strategy 1: Multiplicative Noise (RECOMMENDED)

Multiply the entire rate function by a noise factor:

```python
# Original
rate = "michaelis_menten(P17, vmax=70.0, km=0.1)"

# With ±10% stochastic noise
rate = "michaelis_menten(P17, vmax=70.0, km=0.1) * (1 + 0.1 * wiener(time))"
```

**Advantages:**
- ✅ Preserves rate function shape
- ✅ Simple to implement
- ✅ Noise scales with rate magnitude
- ✅ Never produces negative rates (if base rate > 0)

**Example values:**
```
Base rate = 50.0
With noise: 45.0 to 55.0 (±10%)

Base rate = 5.0  
With noise: 4.5 to 5.5 (±10%)
```

### Strategy 2: Additive Noise to Parameters

Add noise to kinetic parameters (vmax, km):

```python
# Add noise to vmax
rate = "michaelis_menten(P17, vmax=70.0 * (1 + 0.1 * wiener(time)), km=0.1)"

# Add noise to km
rate = "michaelis_menten(P17, vmax=70.0, km=0.1 * (1 + 0.05 * wiener(time)))"

# Add noise to both
rate = "michaelis_menten(P17, vmax=70.0 * (1 + 0.1 * wiener(time)), km=0.1 * (1 + 0.05 * wiener(time)))"
```

**Advantages:**
- ✅ Biologically interpretable (enzyme concentration varies, affinity varies)
- ✅ Can represent different noise sources

**Disadvantages:**
- ⚠️ More complex
- ⚠️ May need different wiener processes for each parameter

### Strategy 3: Additive Noise to Result

Add absolute noise after computing rate:

```python
# Original
rate = "michaelis_menten(P17, vmax=70.0, km=0.1)"

# With additive noise
rate = "michaelis_menten(P17, vmax=70.0, km=0.1) + 5.0 * wiener(time)"
```

**Disadvantages:**
- ❌ Can produce negative rates (needs max(0, ...))
- ❌ Noise doesn't scale with rate
- ❌ Not recommended

## Recommended Pattern for Viability Engine

### For Heuristic-Generated Rates

When viability engine suggests escaping steady state, wrap the **entire** rate function:

```python
def add_stochastic_noise_to_rate(original_rate: str, amplitude: float = 0.1) -> str:
    """Add multiplicative Wiener noise to any rate expression.
    
    Args:
        original_rate: Original rate expression (can be complex)
        amplitude: Noise amplitude (default 0.1 = ±10%)
    
    Returns:
        Modified rate expression with stochastic noise
    """
    # Wrap entire expression with multiplicative noise
    return f"({original_rate}) * (1 + {amplitude} * wiener(time))"
```

**Usage:**
```python
# Original heuristic rate
rate = "michaelis_menten(P17, vmax=70.0, km=0.1)"

# Add noise
noisy_rate = add_stochastic_noise_to_rate(rate, amplitude=0.1)
# Result: "(michaelis_menten(P17, vmax=70.0, km=0.1)) * (1 + 0.1 * wiener(time))"
```

## Examples with Different Rate Functions

### Example 1: Michaelis-Menten
```python
# Deterministic
"michaelis_menten(P17, vmax=70.0, km=0.1)"

# Stochastic (±10% noise)
"michaelis_menten(P17, vmax=70.0, km=0.1) * (1 + 0.1 * wiener(time))"
```

### Example 2: Hill Equation
```python
# Deterministic
"hill_equation(P5, vmax=100.0, k=0.5, n=2.0)"

# Stochastic (±15% noise)
"hill_equation(P5, vmax=100.0, k=0.5, n=2.0) * (1 + 0.15 * wiener(time))"
```

### Example 3: Mass Action
```python
# Deterministic
"mass_action(P1, P2, k=0.01)"

# Stochastic (±20% noise for small molecules)
"mass_action(P1, P2, k=0.01) * (1 + 0.2 * wiener(time))"
```

### Example 4: Complex SBML Formula
```python
# Deterministic (from SBML import)
"kf_0 * P1 * P2 - kr_0 * P3"

# Stochastic (±10% noise on forward reaction)
"(kf_0 * P1 * P2) * (1 + 0.1 * wiener(time)) - kr_0 * P3"

# Or on both directions
"(kf_0 * P1 * P2) * (1 + 0.1 * wiener(time)) - (kr_0 * P3) * (1 + 0.1 * wiener(time))"
```

### Example 5: Conditional Rates
```python
# Deterministic
"if(P1 > 10, vmax * P1 / (km + P1), 0)"

# Stochastic (noise only when active)
"if(P1 > 10, vmax * P1 / (km + P1) * (1 + 0.1 * wiener(time)), 0)"
```

## Noise Amplitude Guidelines by System

| System Type | Molecules | Amplitude | Rationale |
|-------------|-----------|-----------|-----------|
| High concentration | >10,000 | 0.01-0.05 | Law of large numbers, low variance |
| Medium concentration | 100-10,000 | 0.05-0.15 | **Default biological range** |
| Low concentration | 10-100 | 0.15-0.30 | Significant molecular fluctuations |
| Very low concentration | <10 | 0.30-0.50 | Dominated by stochasticity |

**Rule of thumb**: Noise amplitude ≈ 1/√N where N is typical molecule count

## Implementation for Viability Engine

### In `pattern_recognition.py`

Update the steady state escape repair suggestion:

```python
def _suggest_steady_state_escape_repairs(self, pattern_data: Dict) -> List[Dict]:
    """Generate repair suggestions for steady state traps."""
    
    repairs = []
    transition_id = pattern_data.get('transition_id')
    current_rate = pattern_data.get('current_rate', 'rate')
    
    # Strategy #1: Add stochastic noise (WORKS WITH ANY RATE FUNCTION)
    repairs.append({
        'type': 'modify_rate',
        'transition_id': transition_id,
        'old_rate': current_rate,
        'new_rate': f"({current_rate}) * (1 + 0.1 * wiener(time))",
        'confidence': 0.95,
        'description': 'Add stochastic noise (Wiener process) to break steady state',
        'rationale': (
            'Multiplies entire rate function by (1 + 0.1 * wiener(time)), '
            'adding ±10% Brownian motion noise. Works with any rate function: '
            'simple constants, Michaelis-Menten, Hill equations, SBML formulas, etc. '
            'Biologically represents intrinsic molecular noise from finite populations.'
        ),
        'biological_basis': 'Molecular stochasticity prevents exact equilibria',
        'implementation': 'Wrap existing rate with multiplicative noise factor',
    })
    
    return repairs
```

### In `repair_engine.py`

Apply the repair automatically:

```python
def apply_stochastic_noise_repair(self, transition, amplitude: float = 0.1) -> bool:
    """Apply stochastic noise to transition rate.
    
    Args:
        transition: Transition object to modify
        amplitude: Noise amplitude (default 0.1 = ±10%)
    
    Returns:
        True if repair applied successfully
    """
    try:
        current_rate = transition.rate
        
        # Handle numeric rates
        if isinstance(current_rate, (int, float)):
            current_rate = str(float(current_rate))
        
        # Wrap with multiplicative noise
        new_rate = f"({current_rate}) * (1 + {amplitude} * wiener(time))"
        
        transition.rate = new_rate
        
        logger.info(
            f"Added stochastic noise to {transition.id}: "
            f"{current_rate} → {new_rate}"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply stochastic noise: {e}")
        return False
```

## Testing Strategy

### Test 1: Simple Rate
```python
original = "1.0"
noisy = "(1.0) * (1 + 0.1 * wiener(time))"

# Should produce values around 0.9 to 1.1
```

### Test 2: Michaelis-Menten
```python
original = "michaelis_menten(P17, vmax=70.0, km=0.1)"
noisy = "(michaelis_menten(P17, vmax=70.0, km=0.1)) * (1 + 0.1 * wiener(time))"

# At P17=0.5, base rate ≈ 58.3
# With noise: 52.5 to 64.2 (±10%)
```

### Test 3: Complex SBML
```python
original = "kf_0 * P1 * P2 - kr_0 * P3"
noisy = "(kf_0 * P1 * P2 - kr_0 * P3) * (1 + 0.1 * wiener(time))"

# Entire net rate gets noise
```

## Best Practices

### ✅ DO:
1. **Wrap entire rate function** with multiplicative noise
2. **Use parentheses** around original expression
3. **Start with 0.1** (±10%) amplitude
4. **Call `reset_wiener()`** before each simulation
5. **Document** the noise amplitude used

### ❌ DON'T:
1. **Don't use additive noise** (can go negative)
2. **Don't modify** parameters individually (unless needed)
3. **Don't use amplitude > 0.5** (too noisy)
4. **Don't forget** to import reset_wiener
5. **Don't assume** steady state will persist (that's the point!)

## Summary

**For ANY rate function** (simple or complex), use this pattern:

```python
# Generic formula
stochastic_rate = f"({original_rate}) * (1 + {amplitude} * wiener(time))"

# Specific example
original = "michaelis_menten(P17, vmax=70.0, km=0.1)"
stochastic = "(michaelis_menten(P17, vmax=70.0, km=0.1)) * (1 + 0.1 * wiener(time))"
```

**This works because:**
- Multiplicative noise preserves sign (no negative rates)
- Noise scales with rate magnitude (relative noise)
- Simple to implement and understand
- Works with ANY expression type
- Biologically realistic

---

**Key Insight**: You don't need to understand the internal structure of the rate function. Just wrap it with `(rate) * (1 + noise)` and you're done!
