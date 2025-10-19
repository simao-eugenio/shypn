# Mass Action Heuristics

Detailed rules for estimating mass action kinetic parameters.

## Overview

Mass action kinetics describe reactions where rate is proportional to reactant concentrations:

$$v = k \prod_{i} [A_i]^{n_i}$$

Where:
- $v$ = reaction rate
- $k$ = rate constant
- $[A_i]$ = concentration of reactant $i$
- $n_i$ = stoichiometric coefficient of reactant $i$

## Parameter Estimation Rules

### Rate Constant (k)

**Formula** (depends on reaction order):

| Reaction Order | k Value | Rationale |
|----------------|---------|-----------|
| **Unimolecular** (1 reactant) | 1.0 | Fast first-order decay |
| **Bimolecular** (2 reactants) | 0.1 | Slower collision-based |
| **Trimolecular** (3+ reactants) | 0.01 | Very rare 3-body collisions |

**Scientific Basis**:
- Unimolecular: Spontaneous processes (e.g., radioactive decay, conformational changes)
- Bimolecular: Two molecules must collide (10× slower)
- Trimolecular: Three molecules must collide simultaneously (100× slower, rare)

**Units** (concentration-dependent):
- Unimolecular: s⁻¹ (time⁻¹)
- Bimolecular: M⁻¹s⁻¹ (concentration⁻¹ time⁻¹)
- Trimolecular: M⁻²s⁻¹ (concentration⁻² time⁻¹)

**Examples**:

| Reaction | Reactants | Order | k |
|----------|-----------|-------|---|
| A → B | 1 | Uni | 1.0 |
| A + B → C | 2 | Bi | 0.1 |
| 2A → A₂ | 1 (×2) | Bi | 0.1 |
| A + B + C → D | 3 | Tri | 0.01 |

## Rate Function Construction

### Unimolecular Reactions

**Format**:
```
mass_action(A, 1.0, k)
```

**Example**:
```python
# Reaction: A → B
# k = 1.0

rate_function = "mass_action(A, 1.0, 1.0)"
```

**Interpretation**:
- Rate = 1.0 × [A]
- Linear dependence on [A]
- Fast process

### Bimolecular Reactions

**Format**:
```
mass_action(A, B, k)
```

**Example**:
```python
# Reaction: A + B → C
# k = 0.1

rate_function = "mass_action(A, B, 0.1)"
```

**Interpretation**:
- Rate = 0.1 × [A] × [B]
- Requires collision between A and B
- 10× slower than unimolecular

### Homodimerization

**Special Case**: 2A → A₂

```python
# Reaction: 2A → A₂
# k = 0.1 (bimolecular)

rate_function = "mass_action(A, A, 0.1)"
# Or equivalently:
rate_function = "mass_action(A, 1.0, 0.1)"  # Squared in implementation
```

**Rate**: $v = k[A]^2$

### Trimolecular Reactions

**Format**:
```
mass_action(A, B, k)  # Still uses first two reactants
```

**Note**: True trimolecular rare in practice
- Often simplified to two-step bimolecular
- k = 0.01 accounts for low probability

**Example**:
```python
# Reaction: A + B + C → D
# k = 0.01

rate_function = "mass_action(A, B, 0.01)"
```

## Reaction Order Analysis

### Zero-Order (No Reactants)

**Not applicable** for mass action - use constant rate

### First-Order (Unimolecular)

```
A → Products
Rate = k[A]
k = 1.0
```

**Examples**:
- Radioactive decay
- Conformational change
- Spontaneous dissociation

### Second-Order (Bimolecular)

```
A + B → Products
Rate = k[A][B]
k = 0.1
```

**Examples**:
- Molecular collision
- Binding reactions
- Association

### Third-Order (Trimolecular)

```
A + B + C → Products
Rate = k[A][B][C]
k = 0.01
```

**Examples** (rare):
- Three-body recombination
- Termolecular gas reactions
- Often actually two-step

## Stoichiometry Awareness

### Simple Stoichiometry

```python
# A → B (1:1)
# k = 1.0
```

### Complex Stoichiometry

Stoichiometry affects **rate**, not **k**:

```python
# 2A + 3B → C
# k = 0.1 (bimolecular)
# Rate = 0.1 × [A]² × [B]³
```

**Note**: Heuristic uses reaction **order** (# reactants), not stoichiometry

## Implementation Details

### Class: MassActionEstimator

**Methods**:

```python
estimate_parameters(reaction, substrates, products) → Dict
    Returns: {'k': float}

build_rate_function(reaction, substrates, products, params) → str
    Returns: "mass_action(...)" string

estimate_and_build(reaction, substrates, products) → (Dict, str)
    Convenience: returns both params and rate function
```

### Algorithm

```python
def _estimate_k(reaction, substrate_places):
    num_reactants = len(reaction.reactants)
    
    if num_reactants == 1:
        return 1.0   # Unimolecular
    elif num_reactants == 2:
        return 0.1   # Bimolecular
    else:
        return 0.01  # Trimolecular
```

## Validation

### Parameter Ranges

| Parameter | Min | Typical | Max |
|-----------|-----|---------|-----|
| k (uni) | 0.1 | 1.0 | 10.0 |
| k (bi) | 0.01 | 0.1 | 1.0 |
| k (tri) | 0.001 | 0.01 | 0.1 |

### Edge Cases Handled

1. **No reactants**: k = 1.0 (fallback)
2. **>3 reactants**: k = 0.01 (same as trimolecular)
3. **Reversible**: Not automatically handled (future enhancement)

## Testing

See `tests/test_heuristic.py`:

```python
# Test unimolecular
def test_estimate_unimolecular()

# Test bimolecular
def test_estimate_bimolecular()

# Test trimolecular
def test_estimate_trimolecular()

# Test rate functions
def test_build_bimolecular()
def test_build_unimolecular()
```

## Examples from Chemistry

### Radioactive Decay (Unimolecular)

```
Reaction: ²³⁸U → ²³⁴Th + α
Type: First-order (spontaneous)
Reactants: U-238 (1)

Estimated:
- k = 1.0 s⁻¹
- Rate: mass_action(U238, 1.0, 1.0)
- Interpretation: Fast spontaneous decay
```

### Simple Binding (Bimolecular)

```
Reaction: A + B → AB
Type: Second-order (collision)
Reactants: A (1), B (1)

Estimated:
- k = 0.1 M⁻¹s⁻¹
- Rate: mass_action(A, B, 0.1)
- Interpretation: Requires A-B collision
```

### Homodimerization (Bimolecular)

```
Reaction: 2P → P₂
Type: Second-order (self-association)
Reactants: P (2)

Estimated:
- k = 0.1 M⁻¹s⁻¹
- Rate: mass_action(P, P, 0.1)
- Interpretation: Two P molecules collide
```

### Complex Formation (Trimolecular)

```
Reaction: A + B + C → ABC
Type: Third-order (rare 3-body)
Reactants: A (1), B (1), C (1)

Estimated:
- k = 0.01 M⁻²s⁻¹
- Rate: mass_action(A, B, 0.01)
- Interpretation: Very slow, unlikely
```

## Comparison with Other Kinetics

| Kinetic Type | Rate Expression | Use Case |
|--------------|-----------------|----------|
| **Mass Action** | $k[A][B]$ | Chemical reactions |
| **Michaelis-Menten** | $\frac{V_{max}[S]}{K_m + [S]}$ | Enzyme-catalyzed |
| **Hill** | $\frac{V_{max}[S]^n}{K^n + [S]^n}$ | Cooperative binding |
| **Stochastic** | $\lambda e^{-\lambda t}$ | Random processes |

**When to use mass action**:
- Simple chemical reactions
- Non-enzymatic processes
- Gas-phase reactions
- No saturation effects

**When NOT to use**:
- Enzyme catalysis (use MM)
- Random events (use stochastic)
- Complex regulation (use custom)

## Reversible Reactions

### Current Status

**Not automatically handled** - forward reaction only

### Future Enhancement

Bidirectional mass action:

$$v_{net} = k_f[A][B] - k_r[C][D]$$

Where:
- $k_f$ = forward rate constant
- $k_r$ = reverse rate constant
- $K_{eq} = k_f / k_r$ (equilibrium constant)

**Example**:
```python
# A + B ⇄ C + D
# k_f = 0.1, k_r = 0.05

rate_forward = "mass_action(A, B, 0.1)"
rate_reverse = "mass_action(C, D, 0.05)"
rate_net = rate_forward - rate_reverse
```

## Relationship to Thermodynamics

### Equilibrium Constant

At equilibrium, forward rate = reverse rate:

$$K_{eq} = \frac{k_f}{k_r} = \frac{[C][D]}{[A][B]}$$

### Free Energy

$$\Delta G = -RT \ln K_{eq}$$

**Interpretation**:
- $K_{eq} > 1$: Favorable forward ($k_f > k_r$)
- $K_{eq} < 1$: Favorable reverse ($k_r > k_f$)
- $K_{eq} = 1$: No preference

## Temperature Dependence (Arrhenius)

$$k = A e^{-E_a/RT}$$

Where:
- $A$ = pre-exponential factor
- $E_a$ = activation energy
- $R$ = gas constant
- $T$ = temperature

**Future enhancement**: Adjust k based on temperature

## References

1. Atkins, P., & de Paula, J. (2014). "Physical Chemistry"
2. Laidler, K. J. (1987). "Chemical Kinetics"
3. Houston, P. L. (2006). "Chemical Kinetics and Reaction Dynamics"

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall design
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [README.md](README.md) - Quick start guide
- [MICHAELIS_MENTEN_HEURISTICS.md](MICHAELIS_MENTEN_HEURISTICS.md) - Enzyme kinetics
- [STOCHASTIC_HEURISTICS.md](STOCHASTIC_HEURISTICS.md) - Stochastic processes
