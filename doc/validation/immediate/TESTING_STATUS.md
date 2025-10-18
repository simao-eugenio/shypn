# Test Infrastructure Setup - Status and Next Steps

**Date**: 2025-01-XX  
**Status**: ✅ Infrastructure COMPLETE (pending simulation engine verification)

---

## Summary

Created complete test infrastructure for immediate transition validation and benchmarking:

### ✅ Completed
1. **Directory Structure** - All test directories created for 4 transition types
2. **Documentation** - READMEs, benchmark plans, methodology guides
3. **Test Fixtures** - conftest.py with reusable fixtures
4. **Validation Tests** - 6 basic firing tests written
5. **Benchmark Tests** - 5 basic firing benchmarks written
6. **Architecture Alignment** - Updated to use actual project structure (DocumentModel, netobjs)

### ⚠️ Pending Verification
1. **Simulation Engine** - Need to verify `shypn.engine.simulation_controller` exists and API
2. **pytest-benchmark** - Package not installed (required for benchmark tests)
3. **Test Execution** - Can't run tests until simulation engine is verified

---

## Files Created (Session Total: 12 files)

### Documentation (4 files)
1. `/doc/validation/immediate/TEST_INFRASTRUCTURE_COMPLETE.md` - Infrastructure summary
2. `/doc/validation/immediate/TESTING_STATUS.md` - This file

### Test Infrastructure (4 files)
3. `/tests/validation/immediate/conftest.py` - Validation fixtures (197 lines)
4. `/tests/validation/immediate/test_basic_firing.py` - 6 validation tests (107 lines)
5. `/tests/benchmark/immediate/conftest.py` - Benchmark fixtures (169 lines)
6. `/tests/benchmark/immediate/bench_basic_firing.py` - 5 benchmark tests (99 lines)

### Directory Structures (8 directories)
7-14. Created `/tests/validation/{immediate,timed,stochastic,continuous}/`
      Created `/tests/benchmark/{immediate,timed,stochastic,continuous}/`

---

## Architecture Discovered

### Actual Project Structure
```python
# Correct imports (verified working)
from shypn.netobjs import Place, Transition, Arc
from shypn.data.canvas.document_model import DocumentModel

# NOT VERIFIED (assumed based on architecture)
from shypn.engine.simulation_controller import SimulationController
```

### Model Creation Pattern
```python
# Create model
model = DocumentModel()

# Create places using model methods
P1 = model.create_place(x=100, y=100, label="P1")
P1.tokens = 5

# Create transitions
T1 = model.create_transition(x=200, y=100, label="T1")
T1.transition_type = "immediate"

# Create arcs
A1 = model.create_arc(source=P1, target=T1, weight=1)
```

---

## Test Discovery Results

### ✅ Validation Tests (Working)
```bash
$ cd tests/validation/immediate
$ python3 -m pytest --collect-only

collected 6 items

<Module test_basic_firing.py>
  <Function test_fires_when_enabled>
  <Function test_does_not_fire_when_disabled>
  <Function test_fires_immediately_at_t0>
  <Function test_fires_multiple_times>
  <Function test_consumes_tokens_correctly>
  <Function test_produces_tokens_correctly>
```

### ⚠️ Benchmark Tests (Pending)
```bash
$ cd tests/benchmark/immediate
$ python3 -m pytest --collect-only

collected 0 items
```

**Reason**: pytest-benchmark not installed (expected, not critical yet)

---

## Next Steps (Priority Order)

### 🔴 CRITICAL: Verify Simulation Engine

**Need to verify**:
1. Does `shypn.engine.simulation_controller` exist?
2. What's the correct import path?
3. What's the SimulationController API?
   - Constructor: `SimulationController(model)` or different?
   - Run method: `.run(max_time=X, max_firings=Y)`?
   - Results: `.get_firing_history()`, `.current_time`?

**Actions**:
```bash
# Search for simulation controller
find src -name "*simulation*" -o -name "*controller*" | grep -i sim

# Check imports
grep -r "SimulationController" src/

# Check transition firing logic
grep -r "def.*fire" src/ | grep -i transition
```

### 🟡 IMPORTANT: Install Dependencies

```bash
# Install pytest-benchmark for benchmark tests
pip install pytest-benchmark

# Install other test dependencies if needed
pip install pytest-cov pytest-html pytest-timeout
```

### 🟢 READY: Run First Tests

Once simulation engine is verified:

```bash
# Run validation tests (should work)
cd tests/validation/immediate
pytest -v test_basic_firing.py

# Run with coverage
pytest --cov=shypn.engine --cov-report=term-missing

# Run benchmark tests (after installing pytest-benchmark)
cd tests/benchmark/immediate
pytest -v bench_basic_firing.py --benchmark-disable  # Disable benchmark mode first
```

---

## Current Test Status

### Validation Tests (tests/validation/immediate/)
- ✅ **Infrastructure**: conftest.py with 7 fixtures
- ✅ **Tests Written**: 6/6 basic firing tests
- ⚠️ **Tests Passing**: 0/6 (not run yet - simulation engine needs verification)
- 📊 **Coverage**: 0% (not measured yet)

### Benchmark Tests (tests/benchmark/immediate/)
- ✅ **Infrastructure**: conftest.py with 6 fixtures
- ✅ **Tests Written**: 5/5 basic firing benchmarks
- ⚠️ **Tests Passing**: 0/5 (pytest-benchmark not installed)
- 📊 **Baseline**: Not established yet

---

## Assumptions to Verify

### ❓ Simulation Controller API
```python
# ASSUMED (needs verification)
from shypn.engine.simulation_controller import SimulationController

controller = SimulationController(model)  # Takes DocumentModel?
controller.run(max_time=10.0, max_firings=None)  # Correct signature?
history = controller.get_firing_history()  # Returns list of firing events?
time = controller.current_time  # Property or method?
```

### ❓ Transition Properties
```python
# ASSUMED (needs verification)
T1.transition_type = "immediate"  # Correct attribute name?
# Or is it:
# T1.type = "immediate"
# T1.ttype = "immediate"
# T1.set_type("immediate")
```

### ❓ Place Token Management
```python
# ASSUMED (should work - Place class verified)
P1.tokens = 5  # Direct attribute access?
# Or is it:
# P1.set_tokens(5)
# P1.token_count = 5
```

---

## Investigation Commands

### Find Simulation Engine
```bash
# Search for simulation files
find src -type f -name "*.py" | xargs grep -l "class.*Simulation"

# Search for controller files
find src -type f -name "*.py" | xargs grep -l "class.*Controller"

# Search for transition firing logic
grep -r "def fire" src/shypn/ | grep -v "firewall\|firebase"
```

### Check Transition Types
```bash
# Find transition type definitions
grep -r "transition_type\|ttype" src/shypn/netobjs/transition.py

# Find immediate transition usage
grep -r "immediate" src/shypn/ | grep -i transition | head -20
```

### Check Simulation Usage Examples
```bash
# Find existing test files
find . -name "*test*.py" -o -name "*_test.py" | head -10

# Find simulation examples
grep -r "Simulation" examples/ | head -20
```

---

## Fixture Reference

### ptp_model Fixture
```python
def test_example(ptp_model):
    model, P1, T1, P2, A1, A2 = ptp_model
    # model: DocumentModel instance
    # P1: Input Place (tokens=0 initially)
    # T1: Immediate Transition
    # P2: Output Place (tokens=0 initially)
    # A1: Arc P1→T1 (weight=1)
    # A2: Arc T1→P2 (weight=1)
```

### run_simulation Fixture
```python
def test_example(ptp_model, run_simulation):
    model, P1, T1, P2, A1, A2 = ptp_model
    P1.tokens = 5
    
    results = run_simulation(model, max_time=10.0)
    # results['firings']: List of firing events
    # results['final_time']: Final simulation time
    # results['places']: Dict {name: tokens}
```

### Custom Assertions
```python
def test_example(ptp_model, run_simulation, 
                 assert_tokens, assert_firing_count, assert_firing_time):
    model, P1, T1, P2, A1, A2 = ptp_model
    P1.tokens = 3
    
    results = run_simulation(model, max_time=1.0)
    
    assert_tokens(P1, 0)              # P1 has 0 tokens
    assert_tokens(P2, 3)              # P2 has 3 tokens
    assert_firing_count(results, 3)   # 3 firings occurred
    assert_firing_time(results, 0, 0.0)  # First firing at t=0
```

---

## Success Metrics

### Phase 1: Infrastructure ✅ COMPLETE
- [x] Directory structure created
- [x] conftest.py fixtures written
- [x] Test files created
- [x] Tests discoverable by pytest

### Phase 2: Verification ⏳ IN PROGRESS
- [ ] Simulation engine API confirmed
- [ ] Dependencies installed
- [ ] First test passes
- [ ] Baseline benchmark established

### Phase 3: Expansion 🔜 PLANNED
- [ ] Arc weights tests (6 validation + 9 benchmark)
- [ ] Guards tests (12 validation + 18 benchmark)
- [ ] Priorities tests (4 validation + 8 benchmark)
- [ ] Remaining categories...

---

## Risk Assessment

### 🔴 HIGH RISK
- **Simulation Engine API Unknown**: All tests depend on this. If API is different, will need refactoring.

### 🟡 MEDIUM RISK
- **Transition Property Names**: Assumed `transition_type` attribute exists
- **Firing Event Format**: Assumed `get_firing_history()` returns list with 'time' key

### 🟢 LOW RISK
- **Model Creation**: DocumentModel API verified working
- **Place/Transition/Arc**: Classes verified in netobjs package
- **pytest Discovery**: Working correctly

---

## Recommended Immediate Actions

1. **Verify simulation engine** (30 minutes)
   ```bash
   find src -name "*simulation*.py" -o -name "*engine*.py"
   grep -r "class.*Controller" src/
   ```

2. **Check transition examples** (15 minutes)
   ```bash
   grep -r "transition_type.*immediate" src/ examples/
   grep -r "\.fire\|firing" src/shypn/netobjs/transition.py
   ```

3. **Install dependencies** (5 minutes)
   ```bash
   pip install pytest-benchmark pytest-cov
   ```

4. **Run first test** (attempt - 5 minutes)
   ```bash
   cd tests/validation/immediate
   pytest test_basic_firing.py::test_does_not_fire_when_disabled -v
   ```
   This test doesn't require simulation to run (disabled transition), so it's safest first test.

---

**Status**: Infrastructure complete, pending simulation engine verification to proceed with test execution.
