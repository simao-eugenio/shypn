# Biological Petri Net Testing Documentation

This directory contains comprehensive documentation for testing biological Petri net features in SHYpn.

## Main Documentation

### [TESTING_BIOLOGICAL_PETRI_NETS.md](TESTING_BIOLOGICAL_PETRI_NETS.md)
**Comprehensive testing framework guide** covering:
- Testing philosophy and principles
- Test categories (unit, integration, property, E2E)
- Biological Petri net semantics testing
- SBML and KEGG import validation
- Simulation testing (stochastic and continuous)
- Topology testing (P/T-invariants, siphons)
- Property dialog testing (102 tests)
- CI/CD integration

## Testing Results

### [PROPERTY_DIALOG_TESTS_100_PERCENT.md](PROPERTY_DIALOG_TESTS_100_PERCENT.md)
Complete results for property dialog test suite:
- **102 tests total** (34 for Place, 34 for Transition, 34 for Arc)
- **100% passing** - all tests successful
- Topology tab integration validated
- UI consistency verified

### [PROPERTY_DIALOG_TESTS_FINAL_RESULTS.md](PROPERTY_DIALOG_TESTS_FINAL_RESULTS.md)
Final validation and results summary for the complete property dialog testing effort.

## Import Architecture Analysis

### [KEGG_VS_SBML_ARC_ANALYSIS.md](KEGG_VS_SBML_ARC_ANALYSIS.md)
**Comparative analysis** of KEGG and SBML import architectures:
- Arc duplication vulnerabilities
- Catalyst-only transition detection
- Mixed-role species validation
- Entry-based vs species-based approaches
- Architectural recommendations

### [SBML_MODELING_ERROR_CATALYST_ONLY.md](SBML_MODELING_ERROR_CATALYST_ONLY.md)
**Detailed analysis** of catalyst modeling errors in SBML:
- Catalyst-only transitions (blocked transitions)
- Catalyst depletion (mixed-role species)
- Biochemical interpretation
- Detection algorithms
- Solutions and recommendations

## Test Organization

All test files are located in `tests/testing_BIOpn/`:

```
tests/testing_BIOpn/
├── README.md
├── prop_dialogs/           # Property dialog tests (102 tests)
│   ├── test_place_model_integration.py
│   ├── test_transition_model_integration.py
│   └── test_arc_model_integration.py
│
├── test_sbml_*.py         # SBML import tests
├── test_kegg_*.py         # KEGG import tests
├── test_test_arc_*.py     # Test arc (catalyst) tests
└── test_catalyst_*.py     # Catalyst functionality tests
```

## Key Concepts

### Biological Petri Net Semantics

1. **Normal Arcs** (Substrate/Product)
   - Consume tokens when transition fires
   - Represent substrates and products
   - Weight = stoichiometric coefficient

2. **Test Arcs** (Catalyst/Modifier)
   - Do NOT consume tokens
   - Represent enzymes, catalysts, modulators
   - Enable biological regulation

3. **Transition Types**
   - Immediate: Fire instantly when enabled
   - Stochastic: Exponentially distributed delays
   - Continuous: Fire continuously with rate functions

### Import Validation

1. **Arc Duplication Prevention**
   - Aggregate stoichiometry before creating arcs
   - Handle species appearing multiple times in reactions

2. **Catalyst-Only Detection**
   - Warn about transitions with only test arcs
   - Identify potentially blocked transitions

3. **Mixed-Role Validation**
   - Detect species acting as both substrate and catalyst
   - Warn about potential catalyst depletion

## Test Execution

### Run All BIOpn Tests
```bash
cd /home/simao/projetos/shypn
python3 -m pytest tests/testing_BIOpn/
```

### Run with Coverage
```bash
python3 -m pytest tests/testing_BIOpn/ --cov=src/shypn --cov-report=html
```

### Run Specific Categories
```bash
# Property dialogs
python3 -m pytest tests/testing_BIOpn/prop_dialogs/

# SBML import
python3 -m pytest tests/testing_BIOpn/test_sbml*.py

# KEGG import
python3 -m pytest tests/testing_BIOpn/test_kegg*.py

# Test arcs
python3 -m pytest tests/testing_BIOpn/test_test_arc*.py
```

## Related Documentation

- [../../README.md](../../README.md) - Main project README
- [../FIRING_POLICIES.md](../FIRING_POLICIES.md) - 7 firing policy implementations
- [../DUPLICATE_ID_BUG_FIX.md](../DUPLICATE_ID_BUG_FIX.md) - ID generation fixes
- [../SBML_COMPLETE_FLOW_ANALYSIS.md](../SBML_COMPLETE_FLOW_ANALYSIS.md) - SBML import pipeline

## Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Property Dialogs | 100% | ✅ 100% |
| SBML Import | 95% | ✅ 95% |
| KEGG Import | 90% | ✅ 92% |
| Test Arc Semantics | 90% | ✅ 90% |
| **Overall BIOpn** | **90%** | ✅ **93%** |

## Contributing

When adding new biological Petri net tests:

1. Place test files in `tests/testing_BIOpn/`
2. Follow naming convention: `test_<feature>_<aspect>.py`
3. Add test documentation to this directory
4. Update coverage metrics
5. Ensure tests verify biological semantics

## Maintainers

- **Test Framework**: SHYpn Development Team
- **Last Updated**: November 1, 2025
- **Status**: Production Ready

---

For questions or issues, refer to the main [TESTING_BIOLOGICAL_PETRI_NETS.md](TESTING_BIOLOGICAL_PETRI_NETS.md) document.
