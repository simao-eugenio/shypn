# Kinetic Parameter Heuristics

Intelligent estimation of kinetic parameters from stoichiometry for SBML import.

## Quick Start

```python
from shypn.heuristic import EstimatorFactory

# Create estimator
estimator = EstimatorFactory.create('michaelis_menten')

# Estimate parameters and build rate function
params, rate_func = estimator.estimate_and_build(
    reaction, 
    substrate_places, 
    product_places
)

# Use in transition
transition.properties['rate_function'] = rate_func
```

## Available Estimators

| Type | Use Case | Parameters | Rate Function |
|------|----------|------------|---------------|
| **michaelis_menten** | Enzyme kinetics | Vmax, Km | `michaelis_menten(S, Vmax, Km)` |
| **stochastic** | Stochastic processes | lambda | `exponential(lambda)` |
| **mass_action** | Chemical reactions | k | `mass_action(A, B, k)` |

## Architecture

```
src/shypn/heuristic/
├── __init__.py              # Package exports
├── base.py                  # KineticEstimator ABC
├── michaelis_menten.py      # Enzyme kinetics
├── stochastic.py            # Exponential distribution
├── mass_action.py           # Chemical kinetics
└── factory.py               # EstimatorFactory

doc/heuristic/
├── README.md                        # This file
├── ARCHITECTURE.md                  # Complete design
├── IMPLEMENTATION_SUMMARY.md        # Implementation guide
├── MICHAELIS_MENTEN_HEURISTICS.md  # MM rules
├── STOCHASTIC_HEURISTICS.md        # Stochastic rules
└── MASS_ACTION_HEURISTICS.md       # MA rules
```

## Usage Examples

### Michaelis-Menten (Enzyme Kinetics)

```python
estimator = EstimatorFactory.create('michaelis_menten')
params, rate_func = estimator.estimate_and_build(reaction, substrates, products)

# Single substrate
# params = {'vmax': 10.0, 'km': 5.0}
# rate_func = "michaelis_menten(Glucose, 10.0, 5.0)"

# Multiple substrates (sequential MM)
# rate_func = "michaelis_menten(S1, 10.0, 5.0) * (S2 / (5.0 + S2))"
```

### Stochastic (Exponential Distribution)

```python
estimator = EstimatorFactory.create('stochastic')
params, rate_func = estimator.estimate_and_build(reaction, substrates, products)

# params = {'lambda': 2.0, 'distribution': 'exponential'}
# rate_func = "exponential(2.0)"
```

### Mass Action (Chemical Kinetics)

```python
estimator = EstimatorFactory.create('mass_action')
params, rate_func = estimator.estimate_and_build(reaction, substrates, products)

# Bimolecular
# params = {'k': 0.1}
# rate_func = "mass_action(A, B, 0.1)"
```

## Integration with SBML Import

### In PathwayConverter

```python
from shypn.heuristic import EstimatorFactory

class PathwayConverter:
    def _create_transition(self, reaction):
        # ... existing code ...
        
        # Estimate kinetic parameters
        estimator = EstimatorFactory.create('michaelis_menten')
        params, rate_func = estimator.estimate_and_build(
            reaction,
            substrate_places,
            product_places
        )
        
        # Set rate function
        transition.properties['rate_function'] = rate_func
        
        return transition
```

### In Transition Dialog

Dialog pre-fills with estimated rate function:
- User opens imported transition
- Rate function field shows: `michaelis_menten(Glucose, 10.0, 5.0)`
- User can modify or accept

## Heuristic Rules Summary

### Michaelis-Menten
- **Vmax**: 10.0 × max(product_stoichiometry)
- **Km**: mean(substrate_concentrations) / 2
- **Adjustments**: Reversible reactions × 0.8

### Stochastic
- **Lambda**: base_rate × total_reactant_stoichiometry
- **Adjustments**: Low concentrations (<10) × 0.5

### Mass Action
- **Unimolecular**: k = 1.0
- **Bimolecular**: k = 0.1
- **Trimolecular**: k = 0.01

## Testing

Run unit tests:
```bash
python3 -m pytest tests/test_heuristic.py -v
```

Test coverage:
- 26 tests total
- Factory pattern
- All 3 estimators
- Integration scenarios
- 100% pass rate

## Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Complete OOP design |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Implementation guide |
| [MICHAELIS_MENTEN_HEURISTICS.md](MICHAELIS_MENTEN_HEURISTICS.md) | MM rules detail |
| [STOCHASTIC_HEURISTICS.md](STOCHASTIC_HEURISTICS.md) | Stochastic rules |
| [MASS_ACTION_HEURISTICS.md](MASS_ACTION_HEURISTICS.md) | MA rules |

## Key Benefits

1. **Context-Aware**: Uses actual place names in rate functions
2. **Intelligent**: Estimates from stoichiometry and concentrations
3. **Extensible**: Easy to add new estimator types
4. **Testable**: Clean OOP with comprehensive tests
5. **Minimal Coupling**: ~20 lines of integration code

## Next Steps

1. Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for usage details
2. See [ARCHITECTURE.md](ARCHITECTURE.md) for design rationale
3. Check specific heuristic documentation for parameter rules
4. Run tests to verify installation

## Status

- ✅ Core infrastructure implemented
- ✅ All 3 estimators working
- ✅ 26 unit tests passing
- ✅ Ready for loader integration
- ⏳ Loader integration pending
- ⏳ End-to-end testing pending
