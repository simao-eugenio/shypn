# Thermodynamic Validation Quick Reference

## Import

```python
from shypn.thermodynamics import ThermodynamicSimulationValidator
```

## Initialization

```python
# Default settings (recommended)
validator = ThermodynamicSimulationValidator()

# Custom settings
validator = ThermodynamicSimulationValidator(
    tolerance=0.5,         # ±50% tolerance (default)
    enable_web=False,      # Offline mode (default)
    emit_warnings=True     # Emit warnings (default)
)
```

## Basic Validation

```python
result = validator.validate_reversible_reaction(
    reaction_id="R_example",
    k_forward=1e6,         # Forward rate constant
    k_reverse=1e3,         # Reverse rate constant  
    reactants={"C00002": 1},      # {compound_id: stoichiometry}
    products={"C00008": 1},
    ph=7.0,                # Optional: default 7.0
    temperature=298.15     # Optional: default 298.15 K
)

if result.is_valid:
    print(f"✓ Valid (K_eq = {result.k_eq:.2e})")
else:
    print(f"✗ Invalid: {result.message}")
```

## Batch Validation

```python
# SBML reactions
results = validator.validate_sbml_reactions(
    reactions=sbml_model.reactions,
    species_to_compound={"ATP": "C00002", ...}
)

# Petri net transitions
results = validator.validate_model_transitions(
    transitions=model.get_transitions(),
    compound_mapping={"p_ATP": "C00002", ...}
)

# Summary
summary = validator.get_validation_summary(results)
print(f"Valid: {summary['valid']}/{summary['total']}")
```

## Result Fields

```python
result.is_valid          # bool: validation passed
result.message           # str: explanation
result.k_eq              # float: thermodynamic K_eq
result.delta_g_reaction  # float: ΔG° (kJ/mol)
result.details           # dict: kinetic_ratio, etc.
```

## Tolerance Levels

| Tolerance | Meaning | Use Case |
|-----------|---------|----------|
| 0.1 | ±26% | Strict: curated models |
| 0.5 | ±1 order | Default: typical models |
| 0.9 | ±8 orders | Lenient: exploratory |

## Common Compounds

| ID | Name | ΔG°_f (kJ/mol) |
|----|------|----------------|
| C00002 | ATP | -2292.5 |
| C00008 | ADP | -1425.6 |
| C00009 | Phosphate | -1073.3 |
| C00001 | H₂O | -237.2 |
| C00003 | NAD+ | -11.3 |
| C00004 | NADH | 23.1 |
| C00006 | NADP+ | -14.6 |
| C00005 | NADPH | 41.7 |

## Error Handling

```python
try:
    result = validator.validate_reversible_reaction(...)
except ValueError as e:
    print(f"Invalid input: {e}")
    
# Missing data (handled internally)
result = validator.validate_reversible_reaction(
    ...,
    reactants={"C99999": 1}  # Unknown compound
)
# result.is_valid = False
# result.message = "Cannot validate: Compound data not found..."
```

## Integration Points

### 1. SBML Import (sbml_kinetics_service.py)

```python
# After marking reversible reactions
if reaction.reversible:
    transition.properties['is_reversible'] = True
    
    # ADD VALIDATION
    validation = validator.validate_reversible_reaction(...)
    transition.properties['thermodynamic_validation'] = {
        'is_valid': validation.is_valid,
        'message': validation.message
    }
```

### 2. Simulation Init (controller.py)

```python
class SimulationController:
    def __init__(self, model):
        self.model = model
        self.validate_thermodynamics()  # ADD THIS
    
    def validate_thermodynamics(self):
        validator = ThermodynamicSimulationValidator()
        results = validator.validate_model_transitions(
            self.model.get_transitions()
        )
        # Log violations
```

### 3. Runtime Check (tau_leaping_engine.py)

```python
# Optional: periodic validation during simulation
if self.step % 1000 == 0:
    self.check_thermodynamics()
```

## Configuration

### Enable Web API (eQuilibrator)

```python
validator = ThermodynamicSimulationValidator(enable_web=True)
```

**Note**: Requires internet connection. ~50-100ms per compound query.

### Suppress Warnings

```python
# Globally
validator = ThermodynamicSimulationValidator(emit_warnings=False)

# Per call
result = validator.validate_reversible_reaction(
    ...,
    suppress_warnings=True
)
```

## Testing

```bash
# Integration tests
pytest tests/thermodynamics/test_simulation_integration.py -v

# All thermodynamics tests
pytest tests/thermodynamics/ -v

# With coverage
pytest tests/thermodynamics/ --cov=shypn.thermodynamics
```

## Debugging

### Check Available Compounds

```python
from shypn.thermodynamics import MultiSourceProvider

provider = MultiSourceProvider()
compounds = provider.get_available_compounds()
print(f"Available: {len(compounds)} compounds")
```

### Inspect Validation Details

```python
result = validator.validate_reversible_reaction(...)
print(f"K_eq: {result.k_eq:.2e}")
print(f"k_f/k_r: {result.details['kinetic_ratio']:.2e}")
print(f"ΔG°: {result.delta_g_reaction:.1f} kJ/mol")
```

### Manual K_eq Calculation

```python
from shypn.thermodynamics import GibbsCalculator, MultiSourceProvider

provider = MultiSourceProvider()
calc = GibbsCalculator(provider)

thermo = calc.calculate_delta_g_reaction(
    reactants={"C00002": 1},
    products={"C00008": 1, "C00009": 1},
    ph=7.0,
    temperature=298.15
)

print(f"ΔG° = {thermo.delta_g_standard:.1f} kJ/mol")
print(f"K_eq = {thermo.k_eq:.2e}")
```

## Best Practices

1. ✅ Validate during import, not runtime
2. ✅ Log violations, don't silently ignore
3. ✅ Use pH 7.0, T 298.15 K for physiological conditions
4. ✅ Check summary statistics after batch validation
5. ✅ Enable web API only when needed (slower)
6. ✅ Use appropriate tolerance for your model
7. ❌ Don't validate non-reversible reactions
8. ❌ Don't ignore missing data warnings

## Performance Tips

- Cache compound data (done automatically)
- Validate at import, not every simulation step
- Use `enable_web=False` for offline/fast mode
- Batch validations are faster than individual calls

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Compound not found" | Enable web API or add to static data |
| Warning overload | Set `emit_warnings=False` |
| Slow validation | Use `enable_web=False` |
| K_eq overflow | Expected for reactions with large ΔG |
| All reactions invalid | Check compound IDs (KEGG C-numbers) |

## References

- Full documentation: `doc/thermodynamics_simulation_integration.md`
- Tests: `tests/thermodynamics/test_simulation_integration.py`
- Source: `src/shypn/thermodynamics/simulation_integration.py`

---

**Version**: 0.3.0  
**Module**: shypn.thermodynamics  
**Status**: Production-ready
