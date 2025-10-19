# Michaelis-Menten Heuristics

Detailed rules for estimating Michaelis-Menten parameters from stoichiometry.

## Overview

The Michaelis-Menten equation describes enzyme-catalyzed reactions:

$$v = \frac{V_{max} \cdot [S]}{K_m + [S]}$$

Where:
- $v$ = reaction velocity
- $V_{max}$ = maximum velocity
- $[S]$ = substrate concentration
- $K_m$ = Michaelis constant (substrate concentration at half $V_{max}$)

## Parameter Estimation Rules

### Vmax (Maximum Velocity)

**Base Formula**:
$$V_{max} = 10.0 \times \max(\text{product stoichiometry})$$

**Rationale**:
- Default base rate of 10.0 (biochemical timescale)
- Scales with product production (higher stoich = more products)
- Represents enzyme's maximum catalytic capacity

**Adjustments**:

1. **Reversible Reactions** (×0.8):
   ```
   Vmax = 10.0 × max(product_stoich) × 0.8
   ```
   Reversible reactions are typically slower due to product inhibition

2. **Future**: Could adjust for:
   - Enzyme concentration (if available)
   - Temperature effects
   - pH effects

**Examples**:

| Reaction | Product Stoich | Reversible | Vmax |
|----------|----------------|------------|------|
| E + S → P | 1 | No | 10.0 |
| E + S → 2P | 2 | No | 20.0 |
| E + S ⇄ P | 1 | Yes | 8.0 |

### Km (Michaelis Constant)

**Base Formula**:
$$K_m = \frac{\text{mean}([S_1], [S_2], ...)}{2}$$

**Rationale**:
- Km typically half the substrate concentration at steady state
- Uses mean when multiple substrates present
- Represents enzyme-substrate affinity

**Minimum Value**: 0.5 (avoid division by zero, numerical stability)

**Examples**:

| Substrates | Concentrations | Mean | Km |
|------------|----------------|------|----|
| S1 | [10] | 10 | 5.0 |
| S1, S2 | [20, 10] | 15 | 7.5 |
| S1, S2, S3 | [30, 20, 10] | 20 | 10.0 |

**Edge Cases**:
- **No substrate concentrations available**: Use default Km = 5.0
- **Zero concentrations**: Ignore in mean calculation
- **Very low concentrations**: Apply minimum of 0.5

## Rate Function Construction

### Single Substrate

**Format**:
```
michaelis_menten(S, Vmax, Km)
```

**Example**:
```python
# Reaction: Glucose → G6P
# S = Glucose (concentration = 10)
# Vmax = 10.0
# Km = 5.0

rate_function = "michaelis_menten(Glucose, 10.0, 5.0)"
```

### Multiple Substrates (Sequential Binding)

**Format**:
```
michaelis_menten(S1, Vmax, Km) × (S2 / (Km + S2)) × (S3 / (Km + S3))
```

**Rationale**:
- First substrate uses full MM equation
- Additional substrates use binding fraction
- Models sequential enzyme-substrate binding
- Each substrate must bind for reaction to proceed

**Example**:
```python
# Reaction: ATP + Glucose → ADP + G6P
# S1 = ATP (concentration = 20)
# S2 = Glucose (concentration = 10)
# Mean = 15, Km = 7.5
# Vmax = 10.0

rate_function = "michaelis_menten(ATP, 10.0, 7.5) * (Glucose / (7.5 + Glucose))"
```

**Biochemical Interpretation**:
- Primary substrate (ATP) determines base rate
- Secondary substrate (Glucose) modulates rate
- Both must be present for reaction
- Saturation of either substrate increases rate

## Context-Aware Features

### Place Name Usage

Rate functions use **actual place names** from the model:

```python
# NOT generic: michaelis_menten(S1, 10.0, 5.0)
# BUT specific: michaelis_menten(Glucose, 10.0, 5.0)
```

**Benefits**:
1. More readable rate functions
2. Easier debugging
3. Better user understanding
4. Direct mapping to model

### Stoichiometry Awareness

Parameters automatically adjust to reaction complexity:

```python
# Simple: E + S → P
# Vmax = 10.0 (1 product)

# Complex: E + 2S → 3P
# Vmax = 30.0 (3 products)
```

## Implementation Details

### Class: MichaelisMentenEstimator

**Methods**:

```python
estimate_parameters(reaction, substrates, products) → Dict
    Returns: {'vmax': float, 'km': float}

build_rate_function(reaction, substrates, products, params) → str
    Returns: "michaelis_menten(...)" string

estimate_and_build(reaction, substrates, products) → (Dict, str)
    Convenience: returns both params and rate function
```

### Caching

Parameters are cached by reaction signature:
- Key: `reaction.name + reactants + products`
- Improves performance for repeated estimates
- Cache invalidates if reaction changes

## Validation

### Parameter Ranges

| Parameter | Min | Typical | Max |
|-----------|-----|---------|-----|
| Vmax | 1.0 | 10.0 | 100.0 |
| Km | 0.5 | 5.0 | 50.0 |

### Edge Cases Handled

1. **No products**: Use default Vmax = 10.0
2. **No substrates**: Use default Km = 5.0
3. **Zero concentrations**: Exclude from mean
4. **Single substrate**: Standard MM
5. **Multiple substrates**: Sequential MM

## Testing

See `tests/test_heuristic.py`:

```python
# Test Vmax scaling
def test_vmax_scales_with_stoichiometry()

# Test Km estimation
def test_km_from_multiple_substrates()

# Test reversibility
def test_reversible_reduces_vmax()

# Test rate functions
def test_build_single_substrate()
def test_build_multiple_substrates()
```

## Examples from Biochemistry

### Hexokinase (Glucose Phosphorylation)

```
Reaction: ATP + Glucose → ADP + Glucose-6-phosphate
Substrates: ATP (5 mM), Glucose (5 mM)
Products: ADP (1), G6P (1)

Estimated:
- Vmax = 10.0 (1 product)
- Km = 2.5 ((5+5)/2 / 2)
- Rate: michaelis_menten(ATP, 10.0, 2.5) * (Glucose / (2.5 + Glucose))
```

### Pyruvate Kinase

```
Reaction: PEP + ADP → Pyruvate + ATP
Substrates: PEP (2 mM), ADP (1 mM)
Products: Pyruvate (1), ATP (1)

Estimated:
- Vmax = 10.0
- Km = 0.75 ((2+1)/2 / 2)
- Rate: michaelis_menten(PEP, 10.0, 0.75) * (ADP / (0.75 + ADP))
```

## Future Enhancements

### Cooperative Binding (Hill Equation)

For enzymes with multiple binding sites:
$$v = \frac{V_{max} \cdot [S]^n}{K_m^n + [S]^n}$$

### Product Inhibition

For reversible reactions:
$$v = \frac{V_{max} \cdot [S]}{K_m + [S] + [P]/K_i}$$

### Competitive Inhibition

When inhibitors present:
$$v = \frac{V_{max} \cdot [S]}{K_m(1 + [I]/K_i) + [S]}$$

## References

1. Michaelis, L., & Menten, M. L. (1913). "Die Kinetik der Invertinwirkung"
2. Cornish-Bowden, A. (2012). "Fundamentals of Enzyme Kinetics"
3. Berg, J. M., et al. (2002). "Biochemistry"

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall design
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [README.md](README.md) - Quick start guide
