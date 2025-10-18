# Kinetic Parameter Heuristics - Implementation Summary

**Created**: October 18, 2025  
**Status**: 📋 READY FOR IMPLEMENTATION  
**Architecture**: Clean OOP with Base Class + Specialized Estimators

---

## Executive Summary

**Redesigned** the kinetic parameter estimation system following **professional OOP patterns**:

- ✅ **Abstract base class** (`KineticEstimator`)
- ✅ **Separate modules** for each estimator type
- ✅ **Minimal loader code** (~20 lines in PathwayConverter)
- ✅ **Dedicated package** (`src/shypn/heuristic/`)
- ✅ **Comprehensive documentation** (`doc/heuristic/`)

---

## Architecture At-a-Glance

### Class Hierarchy

```
KineticEstimator (ABC)                    # base.py
│
├── MichaelisMentenEstimator             # michaelis_menten.py
│   ├── Vmax from stoichiometry
│   ├── Km from concentrations
│   └── Sequential MM for multi-substrate
│
├── StochasticEstimator                  # stochastic.py (NEW)
│   ├── Lambda from reaction order
│   ├── Exponential distribution
│   └── Adjusts for availability
│
└── MassActionEstimator                  # mass_action.py
    ├── k varies by reaction order
    └── Unimolecular, bimolecular, trimolecular
```

### Factory Pattern

```python
EstimatorFactory.create('michaelis_menten') → MichaelisMentenEstimator()
EstimatorFactory.create('stochastic')       → StochasticEstimator()
EstimatorFactory.create('mass_action')      → MassActionEstimator()
```

---

## Module Structure

### Source Code

```
src/shypn/heuristic/
├── __init__.py                  # 15 lines   - Package exports
├── base.py                      # 120 lines  - Abstract KineticEstimator
├── michaelis_menten.py          # 150 lines  - MM estimator
├── stochastic.py                # 120 lines  - Stochastic/exponential (NEW)
├── mass_action.py               # 100 lines  - Mass action estimator
└── factory.py                   # 40 lines   - EstimatorFactory

Total: ~545 lines (clean, testable, modular)
```

### Documentation

```
doc/heuristic/
├── README.md                          # Overview & quick start
├── ARCHITECTURE.md                    # Complete design (17KB)
├── MICHAELIS_MENTEN_HEURISTICS.md    # MM estimation rules
├── STOCHASTIC_HEURISTICS.md          # Exponential distribution (NEW)
└── MASS_ACTION_HEURISTICS.md         # Mass action kinetics
```

---

## Estimator Specifications

### 1. MichaelisMentenEstimator

**Purpose**: Enzyme kinetics (continuous transitions)

**Parameters Estimated**:
- `Vmax` = 10.0 × max(product_stoichiometry)
- `Km` = mean(substrate_concentrations) / 2

**Rate Function**:
- Single substrate: `michaelis_menten(P1, 10.0, 5.0)`
- Multiple substrates: `michaelis_menten(P1, 10.0, 5.0) * (P2 / (5.0 + P2))`

**Adjustments**:
- Reversible reactions: Vmax × 0.8
- Low concentrations: Km ≥ 0.5

---

### 2. StochasticEstimator (NEW)

**Purpose**: Random events (stochastic transitions)

**Parameters Estimated**:
- `lambda` = base_rate × total_reactant_stoichiometry
- `distribution` = 'exponential'

**Rate Function**:
- `exponential(lambda_rate)`

**Adjustments**:
- Low substrate concentration: lambda × 0.5
- Base lambda = 1.0

**Dialog Pre-fill**:
- Transition type: "stochastic"
- Rate field: lambda value
- Distribution: "exponential"

---

### 3. MassActionEstimator

**Purpose**: Chemical reactions (stochastic or continuous)

**Parameters Estimated**:
- `k` (rate constant)
  - Unimolecular: k = 1.0
  - Bimolecular: k = 0.1
  - Trimolecular: k = 0.01

**Rate Function**:
- Two substrates: `mass_action(P1, P2, 0.1)`
- One substrate: `mass_action(P1, 1.0, 1.0)`

---

## Base Class Interface

### Abstract Methods

```python
class KineticEstimator(ABC):
    @abstractmethod
    def estimate_parameters(
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place]
    ) -> Dict[str, Any]:
        """Return {'param1': value1, 'param2': value2}"""
    
    @abstractmethod
    def build_rate_function(
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place],
        parameters: Dict[str, Any]
    ) -> str:
        """Return 'function_name(args...)'"""
```

### Convenience Method

```python
def estimate_and_build(
    reaction, substrate_places, product_places
) -> Tuple[Dict, str]:
    """
    One-call convenience method.
    
    Returns:
        (parameters_dict, rate_function_string)
    """
```

---

## Integration with PathwayConverter

### Minimal Loader Code (~20 lines)

```python
from shypn.heuristic import EstimatorFactory

class ReactionConverter:
    def _setup_estimated_kinetics(self, transition, reaction):
        """Estimate kinetics using heuristic package."""
        
        # Get places
        substrate_places = [...]
        product_places = [...]
        
        # Create estimator (default: Michaelis-Menten)
        estimator = EstimatorFactory.create('michaelis_menten')
        
        # Estimate and apply
        params, rate_func = estimator.estimate_and_build(
            reaction, substrate_places, product_places
        )
        
        transition.transition_type = "continuous"
        transition.rate = params.get('vmax', 1.0)
        transition.properties['rate_function'] = rate_func
```

**Key Point**: Loader delegates all logic to heuristic package!

---

## Usage Examples

### Example 1: Michaelis-Menten

```python
from shypn.heuristic import EstimatorFactory

# Create estimator
estimator = EstimatorFactory.create('michaelis_menten')

# Estimate parameters
params, rate_func = estimator.estimate_and_build(
    reaction, substrate_places, product_places
)

# Result:
# params = {'vmax': 10.0, 'km': 5.0}
# rate_func = "michaelis_menten(P_Glucose, 10.0, 5.0)"

# Apply to transition
transition.properties['rate_function'] = rate_func
```

### Example 2: Stochastic (NEW)

```python
# Create stochastic estimator
estimator = EstimatorFactory.create('stochastic')

# Estimate parameters
params, rate_func = estimator.estimate_and_build(
    reaction, substrate_places, product_places
)

# Result:
# params = {'lambda': 2.0, 'distribution': 'exponential'}
# rate_func = "exponential(2.0)"

# Apply to transition
transition.transition_type = "stochastic"
transition.rate = params['lambda']
transition.properties['rate_function'] = rate_func
```

### Example 3: Mass Action

```python
# Create mass action estimator
estimator = EstimatorFactory.create('mass_action')

# Estimate parameters
params, rate_func = estimator.estimate_and_build(
    reaction, substrate_places, product_places
)

# Result:
# params = {'k': 0.1}  # Bimolecular
# rate_func = "mass_action(P1, P2, 0.1)"

# Apply to transition
transition.transition_type = "stochastic"
transition.rate = params['k']
transition.properties['rate_function'] = rate_func
```

---

## Stochastic Transitions - Pre-fill Details

### Exponential Distribution

**When**: Reaction times are memoryless (Poisson process)

**Parameters**:
- `lambda` (rate): Events per time unit

**Heuristic Rules**:
```python
# Base lambda
lambda_rate = 1.0

# Scale by stoichiometry
lambda_rate *= sum(reactant_stoichiometries)

# Adjust for low concentrations
if min(substrate_tokens) < 10:
    lambda_rate *= 0.5
```

**Dialog Pre-fill**:
```python
# Transition properties dialog
transition_type: "stochastic"
rate: 2.0  # lambda value
rate_function: "exponential(2.0)"
```

**Function Catalog**:
```python
def exponential(lambda_rate: float) -> float:
    """Exponential distribution (memoryless)."""
    return np.random.exponential(1.0 / lambda_rate)
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Day 1)

- [ ] Create `src/shypn/heuristic/` package
- [ ] Implement `base.py` (KineticEstimator ABC)
- [ ] Implement `factory.py` (EstimatorFactory)
- [ ] Create `__init__.py` with exports
- [ ] Add basic tests

### Phase 2: Estimators (Day 2)

- [ ] Implement `michaelis_menten.py`
- [ ] Implement `stochastic.py` (NEW)
- [ ] Implement `mass_action.py`
- [ ] Add estimator-specific tests

### Phase 3: Integration (Day 3)

- [ ] Modify `PathwayConverter` (~20 lines)
- [ ] Test SBML import with estimation
- [ ] Verify dialog pre-filling
- [ ] Integration tests

### Phase 4: Documentation (Day 4)

- [ ] Create `doc/heuristic/README.md`
- [ ] Create `MICHAELIS_MENTEN_HEURISTICS.md`
- [ ] Create `STOCHASTIC_HEURISTICS.md` (NEW)
- [ ] Create `MASS_ACTION_HEURISTICS.md`
- [ ] User guide with examples

---

## Testing Strategy

### Unit Tests

**Per Estimator** (~30 tests total):

```python
# Michaelis-Menten
test_mm_estimate_vmax_from_stoichiometry()
test_mm_estimate_km_from_concentrations()
test_mm_single_substrate_rate_function()
test_mm_multiple_substrate_sequential()
test_mm_reversible_adjustment()

# Stochastic
test_stochastic_estimate_lambda_from_stoich()
test_stochastic_low_concentration_adjustment()
test_stochastic_exponential_rate_function()
test_stochastic_cache_parameters()

# Mass Action
test_ma_unimolecular_rate_constant()
test_ma_bimolecular_rate_constant()
test_ma_rate_function_two_substrates()
```

### Integration Tests

```python
test_sbml_import_without_kinetics_uses_mm()
test_dialog_shows_estimated_rate_function()
test_stochastic_transition_prefilled()
test_parameters_cached_for_performance()
```

---

## Key Benefits

### 1. Clean Architecture ✅
- Abstract base class defines interface
- Each estimator in separate module
- Factory for simple creation

### 2. Minimal Coupling ✅
- Loader has ~20 lines of integration code
- All logic in heuristic package
- Easy to mock for testing

### 3. Extensibility ✅
```python
# Add new estimator
class MyNewEstimator(KineticEstimator):
    def estimate_parameters(...):
        # Custom logic
    
    def build_rate_function(...):
        # Custom formula

# Register in factory
EstimatorFactory._estimators['my_new_type'] = MyNewEstimator
```

### 4. Testability ✅
- Each estimator independently testable
- No UI dependencies
- Mock reaction data easily

### 5. Performance ✅
- Parameter caching built into base class
- Lazy evaluation
- Minimal overhead

---

## File Structure Summary

### Source Code (545 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 15 | Package exports |
| `base.py` | 120 | Abstract base class |
| `michaelis_menten.py` | 150 | Enzyme kinetics |
| `stochastic.py` | 120 | Exponential distribution (NEW) |
| `mass_action.py` | 100 | Chemical reactions |
| `factory.py` | 40 | Estimator creation |

### Documentation (5 files)

| File | Purpose |
|------|---------|
| `README.md` | Quick start guide |
| `ARCHITECTURE.md` | Complete design (17KB) |
| `MICHAELIS_MENTEN_HEURISTICS.md` | MM rules & examples |
| `STOCHASTIC_HEURISTICS.md` | Exponential rules (NEW) |
| `MASS_ACTION_HEURISTICS.md` | MA kinetics |

### Tests (~30 tests)

| Test Suite | Tests |
|------------|-------|
| `test_michaelis_menten_estimator.py` | 10 |
| `test_stochastic_estimator.py` | 8 |
| `test_mass_action_estimator.py` | 6 |
| `test_estimator_factory.py` | 3 |
| `test_pathway_converter_integration.py` | 3 |

---

## Comparison: Before vs After

### Before (Initial Plan)

```
❌ All logic in pathway_converter.py
❌ ~200 lines of estimation code mixed with conversion
❌ Hard to test (coupled to converter)
❌ Hard to extend (modify large file)
```

### After (OOP Architecture)

```
✅ Dedicated heuristic package (545 lines, 6 files)
✅ Each estimator in separate module
✅ ~20 lines in pathway_converter.py
✅ Easy to test (independent estimators)
✅ Easy to extend (add new estimator class)
```

---

## Next Steps

### Ready to Implement

**Order of Implementation**:

1. **Day 1**: Core infrastructure
   ```bash
   mkdir -p src/shypn/heuristic
   touch src/shypn/heuristic/{__init__,base,factory}.py
   # Implement base class + factory
   ```

2. **Day 2**: Estimators
   ```bash
   touch src/shypn/heuristic/{michaelis_menten,stochastic,mass_action}.py
   # Implement each estimator
   ```

3. **Day 3**: Integration
   ```python
   # Modify pathway_converter.py (~20 lines)
   # Test SBML import
   # Verify dialog pre-filling
   ```

4. **Day 4**: Documentation
   ```bash
   mkdir -p doc/heuristic
   # Create all MD files
   # Add examples and guides
   ```

---

## Success Criteria

✅ **Architecture Complete** when:
- All 6 modules implemented and tested
- Factory creates correct estimators
- Base class interface enforced
- Cache working correctly

✅ **Integration Complete** when:
- PathwayConverter uses factory (~20 lines)
- SBML import estimates parameters
- Dialog shows rate functions
- Tests pass

✅ **Documentation Complete** when:
- All 5 MD files created
- Examples for each estimator
- Integration guide
- API reference

---

## Estimated Effort

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Infrastructure | 1 day | Base class + factory |
| Phase 2: Estimators | 1 day | 3 estimator classes |
| Phase 3: Integration | 1 day | PathwayConverter + tests |
| Phase 4: Documentation | 1 day | 5 MD files |
| **Total** | **4 days** | **Complete system** |

---

## Conclusion

Created **professional OOP architecture** for kinetic parameter estimation:

- ✅ Clean separation of concerns
- ✅ Each estimator in separate module
- ✅ Minimal loader code (~20 lines)
- ✅ Easy to test and extend
- ✅ Comprehensive documentation
- ✅ Factory pattern for simplicity
- ✅ **NEW**: Stochastic/exponential support

**Status**: 📋 Architecture complete, ready for implementation  
**Quality**: Production-grade OOP design  
**Maintainability**: Excellent (modular, testable)

---

**Document Version**: 1.0  
**Last Updated**: October 18, 2025  
**Ready**: FOR IMPLEMENTATION
