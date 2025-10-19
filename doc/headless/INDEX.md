# Headless Simulation Testing Documentation

This directory contains documentation for headless simulation testing - testing the simulation engine without GUI dependencies.

## Quick Start

**Command:** `./headless`

```bash
# Test with built-in shortcuts
./headless glycolysis                    # Fresh Glycolysis import
./headless glycolysis-sources            # Glycolysis with source transitions

# Test your own model
./headless path/to/model.shy             # Test any .shy file

# Options
./headless model.shy -s 100              # Run 100 steps
./headless model.shy -v                  # Verbose (show all steps)
./headless model.shy -q                  # Quiet (summary only)
```

## Documentation Files

### [README.md](README.md)
**Main documentation** - Comprehensive guide to headless testing

**Contents:**
- Purpose and benefits of headless tests
- Test file descriptions
- Usage instructions
- Test models and paths
- Historical context (bug discovery Oct 18, 2025)
- CI/CD integration
- Development workflow

### [SIMULATION_HEADLESS_TEST_RESULTS.md](SIMULATION_HEADLESS_TEST_RESULTS.md)
**Bug discovery report** - Documents the critical simulation bug found Oct 18, 2025

**Contents:**
- Initial symptoms (step() returns True but no tokens move)
- Test results showing the failure
- Root cause analysis (3 interconnected bugs)
- Fix validation
- Lessons learned

### [GLYCOLYSIS_SIMULATION_SOURCES.md](GLYCOLYSIS_SIMULATION_SOURCES.md)
**Source transitions guide** - How to add stochastic source transitions

**Contents:**
- What are source transitions
- Automatic detection of input places
- Script usage (`add_source_transitions.py`)
- Glycolysis enhancement (5 sources added)
- Tuning recommendations

### [PATHWAY_FIRING_FIX.md](PATHWAY_FIRING_FIX.md) 🆕
**Critical bug fix** - Pathway transitions had zero rate (Oct 19, 2025)

**Contents:**
- Root cause: Place ID context mapping bug (string IDs → double P prefix)
- Fix: Handle both string IDs (`"P105"`) and numeric IDs properly
- Impact: All imported models (KEGG, SBML) affected
- Verification: All 26 places now active in Glycolysis

## Test Suite Structure

```
tests/validate/headless/
├── __init__.py                   # Package marker
├── test_headless_simulation.py   # Comprehensive test suite (7 tests)
├── test_fresh_glycolysis.py      # Fresh import validation
└── test_any_model.py             # Universal model tester (CLI)

Project root:
├── headless                      # Simple CLI command
└── run_headless_tests.py         # Test runner script
```

## Key Files

### Test Files
- **`test_headless_simulation.py`** - 7 comprehensive tests for simulation engine
- **`test_fresh_glycolysis.py`** - Quick validation of fresh imports
- **`test_any_model.py`** - Universal tester with full CLI support

### Command-Line Tools
- **`headless`** - Simple, user-friendly command with shortcuts
- **`run_headless_tests.py`** - Runs predefined test suites

### Scripts
- **`add_source_transitions.py`** - Adds stochastic sources to models

## Test Shortcuts

The `headless` command includes built-in shortcuts:

| Shortcut | Full Path | Description |
|----------|-----------|-------------|
| `glycolysis`, `gly` | `workspace/projects/Flow_Test/models/Glycolysis_fresh_Gluconeogenesis.shy` | Fresh KEGG import (34 transitions) |
| `glycolysis-sources`, `gly-src` | `workspace/projects/Flow_Test/models/Glycolysis_fresh_WITH_SOURCES.shy` | With 5 source transitions (39 transitions) |

## Historical Context

### Bug Discovery (October 18, 2025)

These tests were created to diagnose a critical simulation bug:

**Symptom:** 
- `controller.step()` returned `True`
- Time advanced correctly
- BUT: No transitions fired, no tokens moved!

**Root Causes Found:**
1. **Serialization confusion**: `"type": "transition"` vs `"transition_type": "continuous"`
2. **Property name mismatch**: Code used `t.type` instead of `t.transition_type`
3. **String ID handling bug**: `load_objects()` couldn't handle "P123" format

**Resolution:**
- Renamed serialization field: `"type"` → `"object_type"` (avoids confusion)
- Fixed all code to use `transition_type` property
- Fixed `load_objects()` to extract numeric from string IDs
- Created fresh imports with correct data
- Validated with comprehensive test suite

### Test Results

**Before fixes:**
```
✗ FAIL: step() returns True but tokens don't move
✗ FAIL: Simulation not firing transitions
✗ FAIL: Source transitions not generating tokens
```

**After fixes:**
```
✓ PASS: All transitions have valid transition_type
✓ PASS: Behaviors created successfully
✓ PASS: Simulation step executed
✓ PASS: Tokens generated - sources working!
```

## Usage Examples

### Quick Model Validation
```bash
# After importing a model from KEGG
./headless workspace/projects/MyProject/models/my_pathway.shy

# Should see:
# ✓ Model loaded successfully
# ✓ All transitions have valid transition_type
# ✓ Simulation step executed successfully
```

### Debugging Simulation Issues
```bash
# Verbose mode shows every step
./headless my_model.shy -v -s 50

# Look for:
# - Which transitions are firing
# - How tokens are moving
# - Time progression
# - Enablement states
```

### CI/CD Integration
```bash
# In GitHub Actions or similar
./headless glycolysis glycolysis-sources -q

# Returns exit code 0 if all tests pass
# Returns exit code 1 if any test fails
```

### Testing Multiple Models
```bash
# Test all models in a directory
./headless models/*.shy

# Shows summary for each model
# Reports which ones passed/failed
```

## Development Workflow

### When to Run Headless Tests

1. **Before committing** - Verify simulation still works
2. **After import changes** - Check models load correctly  
3. **After behavior changes** - Validate firing logic
4. **After serialization changes** - Ensure save/load works

### Debugging Failed Tests

1. Check error messages for property issues
2. Verify model file path exists
3. Check if using old corrupted models
4. Use `-v` flag to see detailed execution
5. Compare with working models (glycolysis shortcuts)

## Best Practices

### Model Creation
- ✅ Use fresh imports from KEGG
- ✅ Verify transition_type is set correctly
- ✅ Test immediately after import
- ❌ Don't rely on old saved models (may have corruption)

### Test Writing
- ✅ No GUI dependencies
- ✅ Clear test names describing what's tested
- ✅ Comprehensive output showing progress
- ✅ Document expected behavior

### CI/CD
- ✅ Use `--quiet` mode for cleaner logs
- ✅ Test multiple models in one run
- ✅ Check exit codes for pass/fail
- ✅ Run on every commit to main branch

## Future Enhancements

### Planned Features
- [ ] Pytest integration for better reporting
- [ ] Parametrized tests for different transition types
- [ ] Performance benchmarks
- [ ] Coverage reports
- [ ] Property-based tests (hypothesis)

### Potential Tests
- [ ] Timed transition behavior validation
- [ ] Stochastic distribution tests
- [ ] Immediate transition priority tests
- [ ] Hybrid simulation tests
- [ ] Large-scale pathway tests (100+ transitions)

## Related Documentation

- [Simulation Integration](../SIMULATION_INTEGRATION_PLAN.md)
- [Observer Pattern Fix](../OBSERVER_PATTERN_SIMULATION_FIX.md)
- [Source/Sink Implementation](../SOURCE_SINK_SIMULATION_IMPLEMENTATION.md)
- [Validation Architecture](../validation/README.md)

---

**Created:** October 18-19, 2025  
**Purpose:** Document headless simulation testing infrastructure  
**Status:** Active - Core validation tool for development and CI/CD
