# Diagnostic and Test Scripts

**Purpose:** Collection of diagnostic scripts, debug tools, and integration tests organized from the repository root.

**Organization Date:** November 5, 2025

## Overview

This directory contains 90 files moved from the project root for better organization. These scripts were used during development for debugging, diagnosing issues, and verifying fixes.

## File Categories

### Test Scripts (`test_*.py`)
Unit and integration tests for specific features:
- `test_autoload_diagnosis.py` - Autoload feature diagnosis
- `test_biological_category_ui.py` - Biological category UI tests
- `test_brenda_*.py` - BRENDA database integration tests
- `test_catalyst_*.py` - Catalyst feature tests
- `test_compound_*.py` - Compound handling tests
- `test_kegg_*.py` - KEGG import tests
- `test_sabio_*.py` - SABIO-RK database tests
- And many more...

### Diagnostic Scripts (`diagnose_*.py`)
Scripts for diagnosing specific issues:
- `diagnose_catalyst_tokens.py` - Catalyst token investigation
- `diagnose_firing_issue.py` - Transition firing diagnosis
- `diagnose_hsa00010_catalysts.py` - KEGG pathway catalyst analysis
- `diagnose_kegg_model_loading.py` - KEGG model loading verification
- `diagnose_runtime_arcs.py` - Runtime arc state diagnosis
- `diagnose_t3_t4_firing.py` - Specific transition firing diagnosis

### Debug Scripts (`debug_*.py`)
Debugging tools for specific problems:
- `debug_arc_references.py` - Arc reference debugging
- `debug_p5_consumption.py` - Place consumption debugging
- `debug_parameter_matching.py` - Parameter matching debugging
- `debug_sabio_count.py` - SABIO-RK count debugging

### Check Scripts (`check_*.py`)
Validation and verification scripts:
- `check_arc_types.py` - Arc type validation
- `check_stochastic_sources.py` - Stochastic source verification

### Analysis Scripts (`analyze_*.py`)
Analysis and inspection tools:
- `analyze_simulation_idmanager.py` - ID manager analysis

### Investigation Scripts (`investigate_*.py`)
Deep investigation tools:
- `investigate_catalyst_interference.py` - Catalyst interference investigation

### Show/Display Scripts (`show_*.py`)
Display and reporting tools:
- `show_kegg_matching_potential.py` - KEGG matching potential display
- `show_kegg_simulation_instructions.py` - KEGG simulation instructions

### Comparison Scripts (`compare_*.py`)
Comparison and diff tools:
- `compare_old_vs_fixed_models.py` - Model version comparison

### Fix/Migration Scripts (`fix_*.py`)
Scripts for fixing or migrating data:
- `fix_id_naming_conventions.py` - ID naming convention fixes

### Reimport Scripts (`reimport_*.py`)
Data reimport utilities:
- `reimport_hsa00010_with_catalysts.py` - KEGG pathway reimport

### Bulk Operation Scripts (`bulk_*.py`)
Batch processing tools:
- `bulk_import_biomodels.py` - Bulk BioModels import

## Usage

Most of these scripts are standalone and can be run directly:

```bash
# Run a diagnostic script
python tests/diagnostic/diagnose_kegg_model_loading.py

# Run a test script
python tests/diagnostic/test_catalyst_visibility.py

# Run a check script
python tests/diagnostic/check_arc_types.py
```

**Note:** Some scripts may require specific model files or database configurations to run successfully. They were typically used during active development of specific features.

## Historical Context

These scripts were created during various development phases:
- **KEGG Import Development** - KEGG-related tests and diagnostics
- **Catalyst Implementation** - TestArc and catalyst feature development
- **Database Integration** - BRENDA and SABIO-RK integration
- **Bug Fixes** - Specific bug investigation and verification
- **Feature Development** - New feature testing and validation

## Relationship to Validation Tests

This directory contains **development-time diagnostics**, while the `validation/` directory contains **production validation tests**:

- **diagnostic/** - Ad-hoc scripts for debugging specific issues
- **validation/** - Systematic test suites for ongoing validation

Both serve important purposes but have different goals and maintenance levels.

## Maintenance

These scripts are kept for:
1. **Historical reference** - Understanding how issues were diagnosed
2. **Reusability** - May be useful for future similar issues
3. **Documentation** - Show the debugging process
4. **Quick checks** - Fast verification of specific behaviors

Not all scripts are guaranteed to work with the current codebase, as they may have been created for specific development contexts that have since evolved.

## Related Directories

- `../validation/` - Systematic validation test suites
- `../../scripts/` - Production utility scripts
- `../../doc/` - Documentation including validation docs
