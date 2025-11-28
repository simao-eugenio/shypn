# Utility Scripts

This directory contains utility scripts for development, testing, and analysis.

## Scripts

### add_source_transitions.py
Adds source transitions to Petri net models for testing purposes.
- Creates transitions that generate tokens (source behavior)
- Useful for setting up test scenarios with token generation
- Can be used to prepare models for simulation testing

**Usage**:
```bash
python3 scripts/add_source_transitions.py [model_file.shy]
```

### analyze_biomd61_parameters.py
Analyzes parameters in the BIOMD61 model.
- Inspects parameter values and distributions
- Validates parameter assignments
- Reports parameter statistics
- Useful for SBML model analysis

**Usage**:
```bash
python3 scripts/analyze_biomd61_parameters.py
```

### check_arc_types.py
Checks and validates arc types in Petri net models.
- Identifies normal, inhibitor, and test arcs
- Validates arc configurations
- Reports arc type distribution
- Useful for model verification

**Usage**:
```bash
python3 scripts/check_arc_types.py [model_file.shy]
```

### check_stochastic_sources.py
Checks stochastic source configurations in models.
- Identifies stochastic transitions with source behavior
- Validates source/sink configurations
- Reports stochastic source statistics
- Useful for simulation setup validation

**Usage**:
```bash
python3 scripts/check_stochastic_sources.py [model_file.shy]
```

### compare_topology.py
Compares topology between different Petri net models or versions.
- Analyzes structural differences
- Reports changes in places, transitions, and arcs
- Useful for validating model transformations
- Helps track model evolution

**Usage**:
```bash
python3 scripts/compare_topology.py model1.shy model2.shy
```

### diagnose_firing_issue.py
Diagnoses issues with transition firing in models.
- Analyzes why transitions are not firing
- Checks enablement conditions
- Reports missing tokens or inhibitor conflicts
- Useful for debugging simulation problems

**Usage**:
```bash
python3 scripts/diagnose_firing_issue.py [model_file.shy]
```

### diagnose_runtime_arcs.py
Diagnoses arc-related issues during runtime.
- Analyzes arc connections and weights
- Validates arc endpoints
- Reports arc rendering issues
- Useful for debugging visual artifacts

**Usage**:
```bash
python3 scripts/diagnose_runtime_arcs.py [model_file.shy]
```

### diagnose_transition_firing.py
Comprehensive transition firing diagnostics.
- Detailed analysis of firing conditions
- Token availability checks
- Rate function validation
- Enablement state tracking

**Usage**:
```bash
python3 scripts/diagnose_transition_firing.py [model_file.shy]
```

### diagnosis_sigmoid_issue.py
Diagnoses issues with sigmoid rate functions.
- Analyzes sigmoid function parameters
- Validates curve shapes
- Reports parameter sensitivity
- Useful for continuous transition debugging

**Usage**:
```bash
python3 scripts/diagnosis_sigmoid_issue.py [model_file.shy]
```

### fix_stochastic_to_continuous.py
Converts stochastic transitions to continuous transitions.
- Batch conversion utility
- Preserves rate function structure
- Updates transition types
- Useful for model transformation

**Usage**:
```bash
python3 scripts/fix_stochastic_to_continuous.py [model_file.shy]
```

### inspect_kegg_ec_numbers.py
Inspects EC (Enzyme Commission) numbers in KEGG pathway data.
- Analyzes enzyme classifications in imported pathways
- Validates EC number assignments
- Reports enzyme distribution statistics
- Useful for biochemical pathway analysis

**Usage**:
```bash
python3 scripts/inspect_kegg_ec_numbers.py [kegg_data_file]
```

### inspect_kegg_reactions.py
Inspects reaction data in KEGG pathway imports.
- Analyzes reaction structures and participants
- Reports compound connections
- Validates reaction stoichiometry
- Useful for pathway import debugging

**Usage**:
```bash
python3 scripts/inspect_kegg_reactions.py [kegg_data_file]
```

### inspect_transition_types.py
Inspects and analyzes transition types in Petri net models.
- Reports distribution of transition types (immediate, timed, stochastic, continuous)
- Analyzes behavior configurations
- Validates transition parameters
- Useful for model verification

**Usage**:
```bash
python3 scripts/inspect_transition_types.py [model_file.shy]
```

### run_headless_tests.py
Runs test suite in headless mode without GUI.
- Executes tests without X server requirement
- Suitable for CI/CD pipelines
- Reports test results to console
- Can run specific test suites or all tests

**Usage**:
```bash
# Run all tests
python3 scripts/run_headless_tests.py

# Run specific test suite
python3 scripts/run_headless_tests.py --suite property_dialogs
```

### verify_biomd61_fix.py
Verifies fixes applied to the BIOMD61 model.
- Validates model integrity after fixes
- Checks transition types
- Verifies parameter values
- Confirms simulation readiness

**Usage**:
```bash
python3 scripts/verify_biomd61_fix.py
```

## Development Tools

These scripts are designed for:
- **Development**: Quick model inspection and manipulation
- **Testing**: Headless test execution and model preparation
- **Analysis**: KEGG pathway analysis and topology comparison
- **Debugging**: Transition type validation and model inspection
- **CI/CD**: Automated testing without GUI requirements

## Related Directories

- `tests/`: Complete test suite (130+ test files, organized November 2025)
- `archive/`: Legacy analysis scripts (deprecated)
- `src/shypn/dev/`: Development utilities integrated into the application
- `src/shypn/diagnostic/`: Diagnostic tools for runtime debugging

## Notes

- All scripts assume they are run from the repository root
- Some scripts require specific data files or model files as arguments
- Scripts use the same Python environment as the main application
- For KEGG-related scripts, ensure KEGG data is available in `data/` directory

## Migration from Root (November 2025)

These scripts were moved from the repository root to `scripts/` in November 2025 as part of comprehensive project organization improvements. A total of **54 Python scripts** were moved to this directory, maintaining 100% functionality with the same command-line interfaces.

**Organization highlights (November 5, 2025)**:
- 54 utility scripts moved from root to `scripts/`
- 90 test/diagnostic files moved to `tests/diagnostic/`
- 673 documentation files organized in `doc/`
- Clean project root achieved
- All scripts maintain backward compatibility

**Key scripts in this directory**:
- Model inspection tools (inspect_*.py)
- Model modification utilities (add_*, fix_*)
- Comparison and analysis tools (compare_*, analyze_*)
- Diagnostic scripts (diagnose_*, diagnosis_*)
- Verification scripts (verify_*, check_*)
- Testing utilities (run_headless_tests.py)
