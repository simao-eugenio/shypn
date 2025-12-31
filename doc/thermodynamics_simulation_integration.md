# Thermodynamic Simulation Integration

This document describes how to integrate thermodynamic validation with the simulation framework in shypn.

## Overview

The `ThermodynamicSimulationValidator` provides validation that kinetic rate constants (k_forward/k_reverse) are consistent with thermodynamic equilibrium constants (K_eq) derived from Gibbs free energy calculations.

This is critical for ensuring that reversible reactions in stochastic simulations (e.g., τ-leaping with Skellam distribution) maintain thermodynamic consistency.

## Key Features

- **Automatic validation** of reversible reactions during SBML import
- **Runtime checks** for equilibrium consistency
- **Warning system** for thermodynamically inconsistent reactions
- **Integration points**:
  - SBML/KEGG model import
  - Simulation initialization
  - τ-leaping reversible reaction handling

## Basic Usage

### 1. Initialize the Validator

```python
from shypn.thermodynamics import ThermodynamicSimulationValidator

# Create validator with default settings
validator = ThermodynamicSimulationValidator(
    tolerance=0.5,         # ±50% tolerance in log space (≈±1 order of magnitude)
    enable_web=False,      # Offline mode (use cached data only)
    emit_warnings=True     # Emit Python warnings for violations
)
```

### 2. Validate Individual Reactions

```python
# Example: ATP hydrolysis
result = validator.validate_reversible_reaction(
    reaction_id="R_ATP_hydrolysis",
    k_forward=1e8,         # Forward rate constant
    k_reverse=1e3,         # Reverse rate constant
    reactants={"C00002": 1},       # ATP
    products={"C00008": 1, "C00009": 1},  # ADP + Pi
    ph=7.0,
    temperature=298.15
)

if result.is_valid:
    print(f"✓ Reaction is thermodynamically consistent")
    print(f"  K_eq (thermodynamic) = {result.k_eq:.2e}")
    print(f"  k_f/k_r (kinetic) = {result.details['kinetic_ratio']:.2e}")
else:
    print(f"✗ Thermodynamic inconsistency detected:")
    print(f"  {result.message}")
```

### 3. Validate SBML Reactions

```python
# During SBML import
sbml_reactions = load_sbml_model("model.xml").reactions

# Map SBML species to KEGG compound IDs
species_map = {
    "ATP": "C00002",
    "ADP": "C00008",
    "Pi": "C00009"
}

# Validate all reversible reactions
results = validator.validate_sbml_reactions(
    reactions=sbml_reactions,
    species_to_compound=species_map
)

# Generate summary
summary = validator.get_validation_summary(results)
print(f"Validated {summary['total']} reactions:")
print(f"  ✓ Valid: {summary['valid']}")
print(f"  ✗ Invalid: {summary['invalid']}")
print(f"  ? Missing data: {summary['missing_data']}")
```

### 4. Validate Petri Net Transitions

```python
# For Petri net transitions (shypn's internal format)
transitions = model.get_all_transitions()

results = validator.validate_model_transitions(
    transitions=transitions,
    compound_mapping=place_to_compound_map
)

# Check for violations
for name, result in results.items():
    if not result.is_valid:
        print(f"Warning: {name} - {result.message}")
```

## Integration Points

### A. SBML Kinetics Service Integration

Add validation during SBML import in `sbml_kinetics_service.py`:

```python
# In integrate_kinetics() method, after marking reversible reactions:

if reaction.reversible:
    transition.properties['is_reversible'] = True
    
    # ADD THERMODYNAMIC VALIDATION
    from shypn.thermodynamics import ThermodynamicSimulationValidator
    
    validator = ThermodynamicSimulationValidator(
        tolerance=0.5,
        enable_web=False,
        emit_warnings=True
    )
    
    # Validate the reaction
    validation = validator.validate_reversible_reaction(
        reaction_id=reaction.id,
        k_forward=transition.rate_forward,
        k_reverse=transition.rate_reverse,
        reactants=...,  # Extract from reaction
        products=...
    )
    
    # Store validation result
    transition.properties['thermodynamic_validation'] = {
        'is_valid': validation.is_valid,
        'message': validation.message,
        'k_eq': validation.k_eq,
        'k_ratio': validation.details.get('kinetic_ratio')
    }
```

### B. Simulation Controller Integration

Add initialization check in `controller.py`:

```python
class SimulationController:
    def __init__(self, model, verbose=False, recording_interval=10):
        self.model = model
        # ... existing initialization ...
        
        # Validate thermodynamics
        self.validate_thermodynamics()
    
    def validate_thermodynamics(self):
        """Check all reversible reactions for thermodynamic consistency."""
        from shypn.thermodynamics import ThermodynamicSimulationValidator
        
        validator = ThermodynamicSimulationValidator(
            tolerance=0.5,
            enable_web=False,
            emit_warnings=False  # Handle warnings manually
        )
        
        # Get all transitions
        transitions = self.model.get_transitions()
        
        # Validate
        results = validator.validate_model_transitions(transitions)
        
        # Log summary
        summary = validator.get_validation_summary(results)
        if summary['invalid'] > 0:
            self.logger.warning(
                f"Thermodynamic validation: {summary['invalid']} of "
                f"{summary['total']} reversible reactions are inconsistent"
            )
            
            # Log details for each violation
            for name, result in results.items():
                if not result.is_valid:
                    self.logger.warning(f"  {name}: {result.message}")
```

### C. τ-Leaping Engine Integration (Optional)

For runtime monitoring in `tau_leaping_engine.py`:

```python
class TauLeapingEngine:
    def __init__(self, model):
        self.model = model
        # ... existing initialization ...
        
        # Initialize validator for runtime checks
        self.thermodynamic_validator = ThermodynamicSimulationValidator(
            tolerance=0.5,
            enable_web=False,
            emit_warnings=False
        )
    
    def step(self, dt):
        # ... existing step logic ...
        
        # Periodically check reversible reactions
        if self.iteration % 1000 == 0:
            self.check_reversible_reactions()
    
    def check_reversible_reactions(self):
        """Runtime check for thermodynamic consistency."""
        # Get current rate constants from propensities
        # Validate against K_eq
        # Log drift warnings
        pass
```

## Validation Algorithm

The validator uses the following criterion:

```
K_eq (thermodynamic) ≈ k_forward / k_reverse (kinetic)
```

Specifically:

1. **Calculate K_eq** from Gibbs free energy:
   - ΔG° = Σ(ν · ΔG°_f) for reactants and products
   - K_eq = exp(-ΔG° / RT)

2. **Calculate kinetic ratio**:
   - k_ratio = k_forward / k_reverse

3. **Compare in log space**:
   - δlog = |log₁₀(k_ratio) - log₁₀(K_eq)|
   - Valid if δlog < tolerance_orders

4. **Interpret tolerance**:
   - 0.5 (default) ≈ ±1 order of magnitude
   - 0.1 (strict) ≈ ±26%
   - 0.9 (lenient) ≈ ±8 orders

## Configuration

### Tolerance Levels

- **Strict** (0.1): For highly curated models with precise rate constants
- **Default** (0.5): Balanced for typical biochemical models
- **Lenient** (0.9): For exploratory models or uncertain data

### Data Sources

The validator uses three data sources (in order):

1. **Cache**: Previously queried compounds (JSON file)
2. **Static**: Built-in data for ~17 common compounds
3. **eQuilibrator** (optional): Web API for ~10,000 compounds

To enable web access:

```python
validator = ThermodynamicSimulationValidator(
    tolerance=0.5,
    enable_web=True,  # Enable eQuilibrator API
    emit_warnings=True
)
```

## Examples

### Example 1: Detect Inconsistent Reaction

```python
validator = ThermodynamicSimulationValidator(tolerance=0.5)

# ATP → ADP + Pi with WRONG rate ratio
result = validator.validate_reversible_reaction(
    reaction_id="R_ATP_wrong",
    k_forward=1e4,      # Too small
    k_reverse=1e4,      # Too large
    reactants={"C00002": 1},
    products={"C00008": 1, "C00009": 1}
)

# Output:
# result.is_valid = False
# result.message = "Invalid: k_f/k_r = 1.00e+00 vs K_eq = 8.83e+117 
#                   (exceeds 50% tolerance, δlog = 117.95 > 1.00 orders)"
```

### Example 2: Batch Validation with Summary

```python
reactions = [
    {"id": "R1", "k_f": 1e8, "k_r": 1e3, ...},
    {"id": "R2", "k_f": 1e6, "k_r": 1e2, ...},
    {"id": "R3", "k_f": 1e5, "k_r": 1e5, ...},
]

results = {}
for rxn in reactions:
    result = validator.validate_reversible_reaction(**rxn)
    results[rxn["id"]] = result

summary = validator.get_validation_summary(results)
print(f"Validation complete: {summary['valid']}/{summary['total']} valid")
```

## Best Practices

1. **Validate during import**: Catch issues early in the workflow
2. **Log violations**: Don't silently ignore thermodynamic inconsistencies
3. **Use appropriate tolerance**: Balance precision vs. flexibility
4. **Check data availability**: Not all compounds have thermodynamic data
5. **Consider pH/temperature**: Use physiological conditions (pH 7.0, 298 K)
6. **Document assumptions**: Record tolerance and conditions used

## Troubleshooting

### Missing Compound Data

```python
# Error: "Compound data not found: C99999"

# Solutions:
# 1. Enable web access for eQuilibrator
validator = ThermodynamicSimulationValidator(enable_web=True)

# 2. Add compound to static database
# Edit: src/shypn/data/static_compounds.json

# 3. Use compound resolver to map names to IDs
from shypn.thermodynamics import CompoundResolver
resolver = CompoundResolver()
result = resolver.resolve("ATP")  # → C00002
```

### Warning Overload

```python
# Suppress warnings for specific calls
result = validator.validate_reversible_reaction(
    ...,
    suppress_warnings=True  # No warning for this reaction
)

# Or disable warnings globally
validator = ThermodynamicSimulationValidator(emit_warnings=False)
```

### Extreme K_eq Values

```python
# K_eq can be very large (10^100+) or very small (10^-100)
# Validator handles overflow/underflow automatically

if result.k_eq is None:
    # Thermodynamic data unavailable or overflow
    print("Cannot validate: insufficient data")
elif not math.isfinite(result.k_eq):
    # Overflow (ΔG too negative) or underflow (ΔG too positive)
    print("Cannot validate: K_eq overflow")
```

## Testing

Run simulation integration tests:

```bash
pytest tests/thermodynamics/test_simulation_integration.py -v
```

All tests (110 total):

```bash
pytest tests/thermodynamics/ -v
```

## References

- Alberty, R. A. (2003). *Thermodynamics of Biochemical Reactions*
- Flamholz, A. et al. (2012). eQuilibrator – the biochemical thermodynamics calculator
- Gillespie, D. T. (2001). Approximate accelerated stochastic simulation of chemically reacting systems

## Version History

- **v0.3.0** (2024): Added simulation integration validator
  - Support for SBML, Petri net transitions
  - Batch validation and summary statistics
  - Integration examples for simulation framework

- **v0.2.0** (2024): Added equilibrium validator and corrector
  - pH, temperature, ionic strength corrections
  - Configurable tolerance levels

- **v0.1.0** (2024): Initial Gibbs calculator and database integration
  - Cache, static, eQuilibrator providers
  - Compound resolver for ID mapping
