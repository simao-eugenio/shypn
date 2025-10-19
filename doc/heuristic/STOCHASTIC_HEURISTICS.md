# Stochastic Heuristics (Exponential Distribution)

Detailed rules for estimating stochastic transition parameters.

## Overview

Stochastic transitions model random, memory-less processes using exponential distributions:

$$P(t) = \lambda e^{-\lambda t}$$

Where:
- $P(t)$ = probability density at time $t$
- $\lambda$ = rate parameter (events per time unit)
- $t$ = time

**Mean firing time**: $\frac{1}{\lambda}$

**Interpretation**: Higher $\lambda$ = faster firing, lower $\lambda$ = slower firing

## Parameter Estimation Rules

### Lambda (Rate Parameter)

**Base Formula**:
$$\lambda = \text{base\_rate} \times \sum \text{reactant stoichiometry}$$

**Default base rate**: 1.0

**Rationale**:
- Lambda scales with total reactant consumption
- More reactants = more complex reaction = proportional rate
- Base rate of 1.0 gives reasonable stochastic timescale

**Adjustments**:

1. **Low Substrate Concentration** (×0.5):
   ```
   if min(substrate_tokens) < 10:
       lambda = lambda × 0.5
   ```
   
   Low substrate availability slows reaction

2. **Future enhancements**:
   - Scale with temperature
   - Adjust for reaction complexity
   - Consider competitive reactions

**Examples**:

| Reaction | Reactant Stoich | Substrate Conc | Lambda |
|----------|----------------|----------------|--------|
| A → B | 1 | 20 | 1.0 |
| A → B | 1 | 5 | 0.5 (low conc) |
| A + B → C | 1 + 1 = 2 | 20, 20 | 2.0 |
| 2A + B → C | 2 + 1 = 3 | 20, 20 | 3.0 |

## Rate Function Construction

### Format

**Simple**:
```
exponential(lambda)
```

**Example**:
```python
# Reaction: mRNA → mRNA + Protein (translation)
# Reactant stoich: 1 (mRNA consumed temporarily)
# Lambda: 1.0

rate_function = "exponential(1.0)"
```

### Common Use Cases

#### 1. Gene Expression (Transcription)
```
Gene → Gene + mRNA
Lambda = 1.0 (single reactant, base rate)
exponential(1.0)
```

#### 2. Translation
```
mRNA → mRNA + Protein
Lambda = 1.0
exponential(1.0)
```

#### 3. Degradation
```
Protein → ∅
Lambda = 0.5 (slow degradation)
exponential(0.5)
```

#### 4. Complex Formation
```
A + B → AB
Lambda = 2.0 (two reactants)
Adjusted to 1.0 if low concentration
exponential(1.0)
```

## Stoichiometry Awareness

### Simple Reactions

```python
# A → B
# Reactant stoich: 1
# Lambda: 1.0 × 1 = 1.0

rate = "exponential(1.0)"
```

### Complex Reactions

```python
# 2A + B → C
# Reactant stoich: 2 + 1 = 3
# Lambda: 1.0 × 3 = 3.0

rate = "exponential(3.0)"
```

### Catalytic Reactions

```python
# E + S → E + P (enzyme not consumed)
# Effective stoich: 1 (only S consumed)
# Lambda: 1.0

rate = "exponential(1.0)"
```

## Concentration Effects

### High Concentration (≥10 tokens)

No adjustment - use base lambda:
```python
# Substrate: 50 tokens
# Lambda: 1.0 (no adjustment)
```

### Low Concentration (<10 tokens)

Apply 0.5 multiplier:
```python
# Substrate: 5 tokens
# Lambda: 1.0 × 0.5 = 0.5
# Slower due to limited substrate
```

### Zero Concentration

Use base lambda (reaction won't fire anyway):
```python
# Substrate: 0 tokens
# Lambda: 1.0 (default)
# Note: Transition won't fire until tokens available
```

## Implementation Details

### Class: StochasticEstimator

**Methods**:

```python
estimate_parameters(reaction, substrates, products) → Dict
    Returns: {'lambda': float, 'distribution': 'exponential'}

build_rate_function(reaction, substrates, products, params) → str
    Returns: "exponential(lambda)" string

estimate_and_build(reaction, substrates, products) → (Dict, str)
    Convenience: returns both params and rate function
```

### Algorithm

```python
def _estimate_lambda(reaction, substrate_places):
    # Sum reactant stoichiometry
    total_stoich = sum(stoich for _, stoich in reaction.reactants)
    
    # Base lambda
    lambda_rate = 1.0 * total_stoich
    
    # Check concentrations
    if substrate_places:
        available = [p.tokens for p in substrate_places if p.tokens > 0]
        if available and min(available) < 10:
            lambda_rate *= 0.5  # Low concentration
    
    return lambda_rate
```

## Validation

### Parameter Ranges

| Parameter | Min | Typical | Max |
|-----------|-----|---------|-----|
| Lambda | 0.1 | 1.0 | 10.0 |

### Edge Cases Handled

1. **No reactants**: Lambda = 1.0 (default)
2. **Zero concentrations**: Use default lambda
3. **Very high stoichiometry**: Lambda scales proportionally
4. **Mixed concentrations**: Use minimum for adjustment

## Testing

See `tests/test_heuristic.py`:

```python
# Test basic lambda
def test_estimate_simple_reaction()

# Test stoichiometry scaling
def test_lambda_scales_with_stoichiometry()

# Test low concentration
def test_low_concentration_reduces_lambda()

# Test rate function
def test_build_rate_function()
```

## Examples from Molecular Biology

### Transcription

```
Reaction: DNA → DNA + mRNA
Type: Stochastic (random promoter firing)
Reactants: DNA (1, tokens=1)
Products: mRNA (1)

Estimated:
- Lambda = 1.0 (single reactant)
- Rate: exponential(1.0)
- Mean time: 1.0 time unit

Interpretation: On average, one mRNA produced per time unit
```

### Translation

```
Reaction: mRNA → mRNA + Protein
Type: Stochastic (random ribosome binding)
Reactants: mRNA (1, tokens=10)
Products: Protein (1)

Estimated:
- Lambda = 1.0 (high concentration)
- Rate: exponential(1.0)
- Mean time: 1.0 time unit
```

### Degradation (Low Concentration)

```
Reaction: Protein → ∅
Type: Stochastic (random degradation)
Reactants: Protein (1, tokens=5)
Products: None

Estimated:
- Lambda = 0.5 (1.0 × 0.5 due to low concentration)
- Rate: exponential(0.5)
- Mean time: 2.0 time units

Interpretation: Protein degrades slowly when scarce
```

### Dimerization

```
Reaction: 2P → P2
Type: Stochastic (random collision)
Reactants: P (2, tokens=20)
Products: P2 (1)

Estimated:
- Lambda = 2.0 (stoichiometry = 2)
- Rate: exponential(2.0)
- Mean time: 0.5 time units

Interpretation: Fast dimerization due to high stoichiometry
```

## Comparison with Other Distributions

### Exponential vs Deterministic

| Property | Exponential | Deterministic |
|----------|-------------|---------------|
| Memory | Memoryless | Has memory |
| Variation | High (CV=1) | None (CV=0) |
| Use case | Random events | Timed events |

**When to use exponential**:
- Gene expression
- Molecular collisions
- Random degradation
- Stochastic processes

**When NOT to use**:
- Fixed timing (use deterministic)
- Oscillations (use deterministic)
- Known delays (use deterministic)

## Future Enhancements

### Gamma Distribution

For processes with stages:
$$P(t) = \frac{\lambda^k t^{k-1} e^{-\lambda t}}{(k-1)!}$$

Useful for:
- Multi-step transcription
- Sequential processing
- Delayed responses

### Weibull Distribution

For time-dependent rates:
$$P(t) = \frac{k}{\lambda}\left(\frac{t}{\lambda}\right)^{k-1}e^{-(t/\lambda)^k}$$

Useful for:
- Aging effects
- Failure rates
- Non-constant hazards

## Stochastic Simulation

### Gillespie Algorithm

When simulating:
1. Calculate propensity: $a = \lambda \times \text{tokens}$
2. Sample time: $\tau \sim \text{Exp}(a)$
3. Fire transition at time $t + \tau$

**Example**:
```python
# Lambda = 2.0, tokens = 5
propensity = 2.0 * 5 = 10.0
tau = random.exponential(1.0/10.0)  # Mean = 0.1
```

## References

1. Gillespie, D. T. (1977). "Exact stochastic simulation of coupled chemical reactions"
2. Van Kampen, N. G. (2007). "Stochastic Processes in Physics and Chemistry"
3. McQuarrie, D. A. (1967). "Stochastic approach to chemical kinetics"

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall design
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [README.md](README.md) - Quick start guide
- [MICHAELIS_MENTEN_HEURISTICS.md](MICHAELIS_MENTEN_HEURISTICS.md) - Enzyme kinetics
