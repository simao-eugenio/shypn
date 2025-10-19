# Headless Simulation Tests

This directory contains headless tests for the simulation engine - tests that run without GUI dependencies and can validate core simulation functionality.

## Purpose

Headless tests are critical for:
- **CI/CD Integration**: Can run in automated pipelines without display server
- **Rapid Development**: Fast iteration without GUI overhead
- **Regression Detection**: Catch simulation bugs early
- **Core Validation**: Test simulation logic independently of UI

## Test Files

### `test_headless_simulation.py`
**Comprehensive simulation engine test suite**

Tests 7 different scenarios:
1. **Controller Initialization** - Verify SimulationController creates correctly
2. **Transition Enablement** - Test structural enablement detection
3. **Single Step Execution** - Verify tokens move in one step
4. **Multiple Steps** - Test multi-step simulation
5. **Glycolysis Model (no sources)** - Real KEGG pathway simulation
6. **Glycolysis Model (with sources)** - Pathway with continuous input
7. **Stochastic Source Transitions** - Verify source transitions generate tokens

**Usage**:
```bash
cd /home/simao/projetos/shypn
python3 tests/validate/headless/test_headless_simulation.py
```

**Key Features**:
- No GTK/GUI dependencies in test logic
- Creates minimal test nets programmatically
- Validates token movement and time progression
- Tests both simple and complex (Glycolysis) models

### `test_fresh_glycolysis.py`
**Fresh import validation test**

Validates that freshly imported KEGG models have correct properties after serialization fixes.

**What it tests**:
- ✅ All transitions have valid `transition_type` (not corrupted 'transition')
- ✅ Simulation behaviors created correctly
- ✅ Source transitions fire and generate tokens
- ✅ Continuous simulation with token flow

**Usage**:
```bash
cd /home/simao/projetos/shypn
python3 tests/validate/headless/test_fresh_glycolysis.py
```

**Expected Output**:
```
✓ All transitions have valid transition_type!
    continuous: 39
✓ All behaviors created successfully
✓ Simulation step executed successfully
✓ Tokens generated - sources are working!
```

## Test Models

Tests use models from:
- `workspace/Test_flow/model/` - Legacy test models (may have corrupted data)
- `workspace/projects/Flow_Test/models/` - Fresh imports with correct properties

### Recommended Test Models:
- `Glycolysis_fresh_Gluconeogenesis.shy` - Fresh KEGG import (34 transitions)
- `Glycolysis_fresh_WITH_SOURCES.shy` - With 5 stochastic sources (39 transitions)

## Historical Context

### Bug Discovery (Oct 18, 2025)

These tests were created to diagnose a critical simulation bug where:
1. **Symptom**: `step()` returned `True`, time advanced, but NO transitions fired
2. **Root Causes Found**:
   - Serialization confusion: `"type": "transition"` vs `"transition_type": "continuous"`
   - Test code using wrong property: `t.type` instead of `t.transition_type`
   - String ID handling bug in `load_objects()`
   - Old saved models had corrupted data

### Fixes Applied:
1. **Serialization fix**: Renamed `"type"` → `"object_type"` to avoid confusion
2. **Property consistency**: All code uses `transition_type` not `type`
3. **String ID handling**: Fixed `load_objects()` to extract numeric from "P123"
4. **Test updates**: All tests use correct property names

## Quick Command: `headless`

The easiest way to test models is with the `headless` command in the project root:

```bash
# Quick test with shortcut
./headless glycolysis                    # Test fresh Glycolysis import
./headless glycolysis-sources            # Test with source transitions

# Test your own model
./headless path/to/my_model.shy

# Advanced options
./headless glycolysis -s 100             # Run 100 steps
./headless my_model.shy -v               # Verbose (show all steps)
./headless my_model.shy -q               # Quiet (summary only)

# Test multiple models
./headless model1.shy model2.shy model3.shy
```

**Built-in Shortcuts:**
- `glycolysis` or `gly` → Fresh Glycolysis import (34 transitions)
- `glycolysis-sources` or `gly-src` → Glycolysis with 5 sources (39 transitions)

## Running Individual Test Scripts

```bash
# Run comprehensive simulation tests (7 test scenarios)
cd /home/simao/projetos/shypn
python3 tests/validate/headless/test_headless_simulation.py

# Run fresh import validation (quick test)
python3 tests/validate/headless/test_fresh_glycolysis.py

# Test any model with CLI args
python3 tests/validate/headless/test_any_model.py --model my_model.shy --steps 50
```

## Using the Test Runner Script

```bash
# Run all tests
python3 run_headless_tests.py

# Run only quick test
python3 run_headless_tests.py --quick

# Run only comprehensive test
python3 run_headless_tests.py --full
```

## Test Results Interpretation

### Success Indicators:
- ✅ All transitions have valid `transition_type`
- ✅ Behaviors created without errors
- ✅ `step()` returns `True` and tokens move
- ✅ Time advances correctly
- ✅ Token conservation (unless sources/sinks present)

### Failure Indicators:
- ✗ `AttributeError: 'Transition' object has no attribute 'type'` - Using wrong property
- ✗ `Unknown transition type: 'transition'` - Corrupted saved model
- ✗ `step()` returns `True` but tokens don't move - Simulation not firing
- ✗ Tokens don't change over multiple steps - No enabled transitions

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
test_simulation:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
    - name: Run headless simulation tests
      run: |
        python3 tests/validate/headless/test_headless_simulation.py
        python3 tests/validate/headless/test_fresh_glycolysis.py
```

## Development Workflow

### When to Run:
- **Before commit**: Verify simulation still works
- **After import changes**: Check models load correctly
- **After behavior changes**: Validate firing logic
- **After serialization changes**: Ensure save/load works

### Debugging Failed Tests:
1. Check error messages for property name issues (`type` vs `transition_type`)
2. Verify model file path exists
3. Check if using old corrupted models vs fresh imports
4. Enable verbose output to see token movements
5. Use debugger to trace behavior creation

## Test Architecture

```
tests/validate/headless/
├── README.md                         # This file
├── test_headless_simulation.py       # Comprehensive test suite (7 tests)
├── test_fresh_glycolysis.py          # Fresh import validation
└── [future tests]                    # More headless tests as needed
```

## Related Files

### Core Simulation:
- `src/shypn/engine/simulation/controller.py` - Main simulation controller
- `src/shypn/engine/behavior_factory.py` - Creates behaviors from transition types
- `src/shypn/engine/behaviors/` - Behavior implementations

### Data Model:
- `src/shypn/netobjs/transition.py` - Transition with `transition_type` property
- `src/shypn/data/model_canvas_manager.py` - Object manager with observers

### Serialization:
- `src/shypn/netobjs/transition.py::to_dict()` - Uses `"object_type"` not `"type"`
- `src/shypn/data/canvas/document_model.py` - Save/load documents

## Future Enhancements

### Planned Tests:
- [ ] Timed transition behavior validation
- [ ] Stochastic transition distribution tests
- [ ] Immediate transition priority tests
- [ ] Hybrid simulation (continuous + discrete)
- [ ] Large-scale pathway tests (100+ transitions)
- [ ] Performance benchmarks

### Test Framework:
- [ ] Convert to pytest for better reporting
- [ ] Add parametrized tests for different transition types
- [ ] Generate coverage reports
- [ ] Add property-based tests (hypothesis)

## Contributing

When adding new headless tests:
1. **No GUI dependencies** - Tests must run without GTK/display
2. **Clear test names** - Describe what is being tested
3. **Comprehensive output** - Show what's happening at each step
4. **Document expectations** - Explain what success looks like
5. **Use fresh models** - Prefer fresh imports over legacy files

## Lessons Learned

### Key Insights from Bug Hunt:

1. **Property naming matters**: `type` vs `transition_type` - clear naming prevents confusion
2. **Serialization must match**: What you save must match what you load
3. **Test early and often**: Headless tests catch issues before GUI testing
4. **Fresh imports are clean**: Old saved files can accumulate corruption
5. **Observer pattern works**: But only if objects go through proper initialization

---

**Created**: October 18, 2025  
**Purpose**: Validate simulation engine without GUI dependencies  
**Status**: Active - Critical for CI/CD and development
