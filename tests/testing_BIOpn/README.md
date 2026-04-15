# Testing Biological Petri Nets

This directory contains tests and documentation specifically for biological Petri net features.

## Test Categories

### SBML Import Tests
- `test_sbml_modifier_import.py` - Modifier/catalyst import validation
- `test_sbml_arc_id_fix.py` - Arc ID duplication prevention
- `test_sbml_transition_type_validation.py` - Transition type assignment
- `test_biomd61_reimport_validation.py` - BIOMD61 model validation

### KEGG Import Tests
- `test_kegg_catalyst_import.py` - KEGG enzyme/catalyst import
- `test_kegg_import_autoload.py` - KEGG pathway auto-loading

### Test Arc (Catalyst) Tests
- `test_test_arc.py` - Basic test arc functionality
- `test_test_arc_simulation.py` - Test arc in simulation
- `test_test_arc_simulation_simple.py` - Simplified simulation tests
- `test_test_arc_loading.py` - Test arc persistence
- `test_test_arc_perimeter_rendering.py` - Visual rendering tests
- `test_multiple_test_arcs.py` - Multiple test arcs per transition

### Catalyst/Enzyme Tests
- `test_catalyst_visibility.py` - Catalyst visualization
- `test_hierarchical_layout_with_catalysts.py` - Layout with catalysts

### Property Dialog Tests
Directory: `prop_dialogs/`
- `test_place_model_integration.py` - 34 tests for Place dialog
- `test_transition_model_integration.py` - 34 tests for Transition dialog
- `test_arc_model_integration.py` - 34 tests for Arc dialog
- **Total**: 102 tests, 100% passing

## Running Tests

### All Biological Petri Net Tests
```bash
python3 -m pytest tests/testing_BIOpn/
```

### Specific Test Categories
```bash
# SBML tests
python3 -m pytest tests/testing_BIOpn/test_sbml*.py

# KEGG tests
python3 -m pytest tests/testing_BIOpn/test_kegg*.py

# Test arc tests
python3 -m pytest tests/testing_BIOpn/test_test_arc*.py

# Property dialog tests
python3 -m pytest tests/testing_BIOpn/prop_dialogs/
```

### Individual Tests
```bash
# Run specific test file
python3 tests/testing_BIOpn/test_sbml_arc_id_fix.py

# Run with verbose output
python3 -m pytest tests/testing_BIOpn/test_biomd61_reimport_validation.py -v
```

## Documentation

See `doc/testing_BIOpn/` for comprehensive documentation:
- `TESTING_BIOLOGICAL_PETRI_NETS.md` - Complete testing guide
- `PROPERTY_DIALOG_TESTS_100_PERCENT.md` - Property dialog test results
- `KEGG_VS_SBML_ARC_ANALYSIS.md` - Import architecture comparison
- `SBML_MODELING_ERROR_CATALYST_ONLY.md` - Catalyst modeling issues

## Test Coverage

- **Property Dialogs**: 100% (102/102)
- **SBML Import**: 95%
- **KEGG Import**: 92%
- **Test Arc Semantics**: 90%
- **Overall BIOpn Tests**: 93%

## Related Documentation

- [../doc/testing_BIOpn/TESTING_BIOLOGICAL_PETRI_NETS.md](../../doc/testing_BIOpn/TESTING_BIOLOGICAL_PETRI_NETS.md)
- [FIRING_POLICIES.md](../../doc/FIRING_POLICIES.md)
- [DUPLICATE_ID_BUG_FIX.md](../../doc/DUPLICATE_ID_BUG_FIX.md)
