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

## Development Tools

These scripts are designed for:
- **Development**: Quick model inspection and manipulation
- **Testing**: Headless test execution and model preparation
- **Analysis**: KEGG pathway analysis and topology comparison
- **Debugging**: Transition type validation and model inspection
- **CI/CD**: Automated testing without GUI requirements

## Related Directories

- `tests/`: Complete test suite (110+ test files)
- `archive/`: Legacy analysis scripts (deprecated)
- `src/shypn/dev/`: Development utilities integrated into the application
- `src/shypn/diagnostic/`: Diagnostic tools for runtime debugging

## Notes

- All scripts assume they are run from the repository root
- Some scripts require specific data files or model files as arguments
- Scripts use the same Python environment as the main application
- For KEGG-related scripts, ensure KEGG data is available in `data/` directory

## Migration from Root

These scripts were moved from the repository root to `scripts/` in December 2024 as part of project organization improvements. They maintain 100% functionality with the same command-line interfaces.

Previous locations:
- `add_source_transitions.py` → `scripts/add_source_transitions.py`
- `compare_topology.py` → `scripts/compare_topology.py`
- `inspect_kegg_ec_numbers.py` → `scripts/inspect_kegg_ec_numbers.py`
- `inspect_kegg_reactions.py` → `scripts/inspect_kegg_reactions.py`
- `inspect_transition_types.py` → `scripts/inspect_transition_types.py`
- `run_headless_tests.py` → `scripts/run_headless_tests.py`
