```markdown
````markdown
```markdown
# SHYpn Test Suite

This directory contains all test scripts and test modules for the SHYpn project. **130+ test files** covering various aspects of the application.

## Test Status (November 2025)

**Property Dialog Tests**: ✅ 34/34 passing (100%)
- Place dialogs: 9/9 passing
- Arc dialogs: 13/13 passing  
- Transition dialogs: 12/12 passing

**Hybrid Petri Net Validation**: ✅ New test suite added
- Continuous chain equilibrium tests
- Michaelis-Menten kinetics validation
- Deadlock scenario verification
- Mathematical equilibrium proofs

**Catalyst/TestArc Tests**: ✅ All passing
- TestArc enablement validation
- Non-consuming arc behavior verified
- KEGG model catalyst simulation confirmed

**Firing Policy Tests**: ✅ All 7 policies tested and passing
- Random, Earliest, Latest, Priority, Race, Age, Preemptive-Priority

**SBML Import Tests**: ✅ All passing
- Duplicate ID bug fixes validated
- Stochastic transition scheduling verified
- Source/sink transition compatibility confirmed

**Overall Coverage**: High coverage across all major components

**Repository Organization**: Complete reorganization (November 5, 2025)
- 90 test/diagnostic files moved to `tests/diagnostic/`
- All test files properly organized by category
- Clean separation of validation and diagnostic tests

## Organization

Tests are organized by functionality:
- **Validation tests**: Organized by transition type (validation/)
  - `continuous/`: Continuous transition tests including chain equilibrium analysis
  - `stochastic/`: Stochastic transition tests
  - `immediate/`: Immediate transition tests
  - `timed/`: Timed transition tests
  - `ui/`: UI validation tests
- **Diagnostic tests**: Test and diagnostic scripts (diagnostic/)
  - `test_*.py`: Unit and integration tests
  - `diagnose_*.py`: Diagnostic scripts for debugging
  - `debug_*.py`: Debug scripts for specific issues
  - `check_*.py`: Validation and verification scripts
  - `analyze_*.py`: Analysis scripts
- **Property dialog tests**: Complete integration tests (prop_dialogs/)
- **Benchmark tests**: Performance benchmarks (benchmark/)

## Recent Changes

### November 2025 Updates

#### Repository Reorganization (November 5, 2025)
Major cleanup and organization of test structure:
- ✅ **90 test/diagnostic files** moved from root to `tests/diagnostic/`
- ✅ Files categorized by purpose (test, diagnose, debug, check, analyze, etc.)
- ✅ Clean separation between validation tests and diagnostic tools
- ✅ All files maintain 100% functionality
- ✅ Professional project structure achieved

**New test additions** (November 5, 2025):
- `validation/continuous/test_continuous_chain_deadlock.py` - Hybrid Petri net validation
- `validation/continuous/test_chain_equilibrium_simple.py` - Mathematical equilibrium proof
- Complete test suite for continuous → immediate deadlock scenarios
- Stochastic → immediate working pattern validation
- Michaelis-Menten equilibrium analysis

**Files now in diagnostic/** (November 5, 2025):
- All `test_*.py` files from root (except validation suite)
- All `diagnose_*.py` diagnostic scripts
- All `debug_*.py` debug scripts
- All `check_*.py` validation scripts
- All `analyze_*.py` analysis scripts
- All `investigate_*.py` investigation scripts
- All `show_*.py` display/reporting scripts
- All `compare_*.py` comparison scripts
- All `fix_*.py` fix/migration scripts
- All `reimport_*.py` re-import scripts
- All `bulk_*.py` batch operation scripts

### October 2025 Updates

#### Test Consolidation (October 27, 2025)
All test files consolidated from repository root into this directory:
- ✅ **10 additional test files** moved from root (test scripts and shell scripts)
- ✅ **29 test log files** removed from root
- ✅ Files organized into logical categories
- ✅ All tests maintain 100% functionality
- ✅ Clean repository structure achieved

**Recently moved files** (October 27, 2025):
- `test_duplicate_canvas.sh` - Duplicate canvas testing
- `test_duplicate_id_fix.py` - Duplicate ID bug verification tests
- `test_import_property_dialogs.sh` - Property dialog import tests
- `test_panel_creation.sh` - Panel creation testing
- `test_sbml_biomodels_headless.py` - Headless SBML BioModels tests
- `test_sbml_flow.sh` - SBML import flow testing
- `test_sbml_import_flow.py` - SBML import flow Python tests
- `test_sbml_stochastic_source.py` - SBML stochastic source tests
- `test_stochastic_source.py` - Stochastic source transition tests
- `test_transition_dialog_stochastic.py` - Stochastic transition dialog tests

**Previously moved files** (October 22, 2025):
- `test_dialog_speed.py` - Dialog performance testing
- `test_dialogs.py` - Dialog functionality tests
- `test_exclusive_master_palette.py` - Master Palette exclusive button logic
- `test_file_chooser.py` - File chooser tests
- `test_file_chooser_app.py` - File chooser application tests
- `test_float_button.py` - Panel float button functionality
- `test_gtk_toggle_behavior.py` - GTK toggle button behavior
- `test_headless_dialog_import.py` - Headless dialog import tests
- `test_master_palette_integration.py` - Master Palette integration
- `test_master_palette_logic.py` - Master Palette logic tests
- `test_master_palette_visual.py` - Master Palette visual tests
- `test_phase6_master_palette.py` - Phase 6 Master Palette tests
- `test_real_model.py` - Real model testing

### December 2024 Updates

#### Property Dialog Tests
- ✅ **34/34 tests passing (100%)** - Complete property dialog integration
- Place dialog tests: Dialog loading, topology integration, persistence
- Arc dialog tests: Endpoint display, weight updates, canvas integration
- Transition dialog tests: Behavior configuration, analysis signaling, state management
- See **[prop_dialogs/README.md](prop_dialogs/README.md)** for details

#### Performance Validation
- ✅ Analysis panel optimization verified (95% improvement)
- ✅ Update frequency validation (250ms confirmed)
- ✅ CPU usage reduction verified (75% improvement)

### Test Categories

#### Arc System Tests
- `test_arc_types.py` - All arc type transformations
- `test_arc_transformation.py` - Arc geometry transformations
- `test_arc_hit_detection.py` - Arc selection and hit detection
- `test_long_arc_hit_detection.py` - Long arc click detection
- `test_curved_arc_handle_position.py` - Curved arc control points
- `test_all_arc_types_transformation.py` - Comprehensive arc testing
- `check_arc_endpoints.py` - Arc endpoint validation

#### KEGG Import Tests
- `test_real_kegg_pathways.py` - Real KEGG pathway import
- `test_phase0_relations_analysis.py` - Relation analysis
- `test_phase0_rendering_search.py` - Rendering verification
- `check_kegg_relations.py` - Relations validation
- `check_kegg_relations_rendering.py` - Relations rendering check
- `check_relation_conversion.py` - Conversion validation
- `check_pathway_structure.py` - Pathway structure check
- `check_specific_chain.py` - Chain validation
- `check_specific_compounds.py` - Compound validation

#### Feature Tests
- `test_enhanced_filtering.py` - Enhanced filtering features
- `test_filtering_option.py` - Filter options
- `test_isolated_compounds.py` - Isolated compound handling
- `test_isolated_filtering.py` - Isolated node filtering
- `test_with_enhancements.py` - Enhancement pipeline

#### Source/Sink Tests
- `test_source_sink.py` - Source/sink place types
- `test_timed_source.py` - Timed source places
- `test_timed_sink.py` - Timed sink places
- `test_stochastic_source.py` - Stochastic source transitions (moved Oct 27, 2025)

#### SBML Import Tests
- `test_sbml_biomodels_headless.py` - Headless SBML BioModels tests (moved Oct 27, 2025)
- `test_sbml_import_flow.py` - SBML import flow tests (moved Oct 27, 2025)
- `test_sbml_stochastic_source.py` - SBML stochastic source tests (moved Oct 27, 2025)
- `test_sbml_flow.sh` - SBML flow shell tests (moved Oct 27, 2025)

#### Firing Policy Tests
- `test_firing_policy_persistence.py` - Firing policy persistence and all 7 policies

#### Duplicate ID Tests
- `test_duplicate_id_fix.py` - Duplicate ID bug verification (moved Oct 27, 2025)
- `test_duplicate_canvas.sh` - Duplicate canvas testing (moved Oct 27, 2025)

#### Transformation Handler Tests
- `test_transformation_handlers.py` - Arc transformation handlers

#### Workspace Tests
- `test_workspace_isolation.sh` - Workspace isolation validation

#### Check Scripts
- `check_old_converter.py` - Legacy converter validation
- `check_transition_sizes.py` - Transition size validation

### Test Structure
```
tests/
├── README.md (this file)
├── prop_dialogs/     # Property dialog integration tests (34 tests - 100% passing)
│   ├── README.md
│   ├── test_place_dialog_integration.py (9 tests)
│   ├── test_arc_dialog_integration.py (13 tests)
│   ├── test_transition_dialog_integration.py (12 tests)
│   └── run_all_tests.sh
├── test_*_model_integration.py  # Model integration tests
├── test_*.py         # Individual test modules (120+)
│   ├── test_dialog_*.py          # Dialog tests (moved from root Oct 2025)
│   ├── test_master_palette_*.py  # Master Palette tests (moved from root Oct 2025)
│   ├── test_file_chooser*.py     # File chooser tests (moved from root Oct 2025)
│   ├── test_float_button.py      # Float button tests (moved from root Oct 2025)
│   ├── test_exclusive_master_palette.py  # Exclusive button logic (moved from root Oct 2025)
│   └── ...
├── check_*.py        # Validation scripts
└── *.sh              # Shell test scripts
```

## Running Tests

### Property Dialog Tests (Recommended)
```bash
# All property dialog tests
cd tests/prop_dialogs
./run_all_tests.sh

# Individual dialog tests
python3 tests/prop_dialogs/test_place_dialog_integration.py
python3 tests/prop_dialogs/test_arc_dialog_integration.py
python3 tests/prop_dialogs/test_transition_dialog_integration.py
```

### All Tests
```bash
# Using pytest
python3 -m pytest tests/

# Using headless script (no GUI required)
python3 scripts/run_headless_tests.py
```

### Specific Test File
```bash
python3 -m pytest tests/test_file_explorer.py
```

### With Coverage
```bash
python3 -m pytest --cov=src/shypn --cov-report=html tests/
```

### Verbose Output
```bash
python3 -m pytest -v tests/
```

## Writing Tests

### Guidelines
1. **Naming**: Test files must start with `test_`
2. **Structure**: Mirror the source code structure
3. **Coverage**: Aim for high code coverage
4. **Isolation**: Tests should be independent
5. **Clean Code**: No debug prints, use assertions

### Example Test Structure
```python
import pytest
from shypn.api.file.explorer import FileExplorer

class TestFileExplorer:
    def setup_method(self):
        """Set up test fixtures."""
        self.explorer = FileExplorer()
    
    def test_navigation(self):
        """Test directory navigation."""
        result = self.explorer.navigate_to("/tmp")
        assert result == True
    
    def teardown_method(self):
        """Clean up after tests."""
        pass
```

### GTK Testing
For GTK-related tests:
- Use GTK test utilities
- Mock UI interactions when possible
- Test business logic separately from UI
- Ensure X server or Wayland is available

## Test Requirements

### Dependencies
```bash
pip install pytest pytest-cov pytest-gtk
```

### System Requirements
- Python 3.8+
- GTK 3.22+
- PyGObject
- Display server (for UI tests)

## CI/CD Integration

Tests are run automatically on:
- Pull requests
- Commits to main branches
- Tagged releases

Ensure all tests pass before submitting pull requests.

## Troubleshooting

### No Display Server
If running tests in headless environment:
```bash
xvfb-run python3 -m pytest tests/
```

### Import Errors
Ensure the project root is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### GTK Warnings
Some GTK warnings are normal during testing. Focus on test failures and errors.

```