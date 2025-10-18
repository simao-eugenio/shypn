# Test Infrastructure Quick Start Guide

This guide provides quick commands for running the validation test suite.

## Prerequisites

```bash
# Ensure you're in the project root
cd /home/simao/projetos/shypn

# Activate virtual environment
source venv/bin/activate

# Install package in editable mode (if not done)
pip install -e .

# Install test dependencies
pip install pytest pytest-cov pytest-html pytest-benchmark
```

## Quick Test Commands

### Run All Immediate Tests (Recommended)
```bash
# All 47 immediate transition tests
pytest tests/validation/immediate/ -v

# With coverage report
pytest tests/validation/immediate/ --cov=src/shypn/engine --cov-report=term -v

# With HTML coverage report
pytest tests/validation/immediate/ --cov=src/shypn/engine --cov-report=html -v
# View report: open htmlcov/index.html
```

### Run Specific Test Modules
```bash
# Basic firing tests (6 tests)
pytest tests/validation/immediate/test_basic_firing.py -v

# Arc weight tests (9 tests)
pytest tests/validation/immediate/test_arc_weights.py -v

# Guard tests (17 tests)
pytest tests/validation/immediate/test_guards.py -v

# Priority tests (15 tests)
pytest tests/validation/immediate/test_priorities.py -v
```

### Run Specific Tests
```bash
# Single test by name
pytest tests/validation/immediate/test_guards.py::test_guard_with_token_condition -v

# Multiple tests by pattern
pytest tests/validation/immediate/ -k "guard" -v

# Tests matching multiple patterns
pytest tests/validation/immediate/ -k "guard or priority" -v
```

### Run with Different Verbosity
```bash
# Minimal output
pytest tests/validation/immediate/ -q

# Standard output
pytest tests/validation/immediate/

# Verbose output
pytest tests/validation/immediate/ -v

# Very verbose (show all details)
pytest tests/validation/immediate/ -vv

# Show print statements
pytest tests/validation/immediate/ -s
```

### Run with Coverage Options
```bash
# Terminal report only
pytest tests/validation/immediate/ --cov=src/shypn/engine --cov-report=term

# HTML report (best for detailed analysis)
pytest tests/validation/immediate/ --cov=src/shypn/engine --cov-report=html

# XML report (for CI/CD)
pytest tests/validation/immediate/ --cov=src/shypn/engine --cov-report=xml

# Multiple report formats
pytest tests/validation/immediate/ \
  --cov=src/shypn/engine \
  --cov-report=term \
  --cov-report=html \
  --cov-report=xml

# Fail if coverage below threshold
pytest tests/validation/immediate/ \
  --cov=src/shypn/engine \
  --cov-fail-under=30
```

### Run with HTML Test Report
```bash
# Generate HTML test report
pytest tests/validation/immediate/ --html=report.html --self-contained-html

# With coverage and HTML report
pytest tests/validation/immediate/ \
  --cov=src/shypn/engine \
  --cov-report=html \
  --html=test_report.html \
  --self-contained-html
```

### Debugging Options
```bash
# Stop at first failure
pytest tests/validation/immediate/ -x

# Stop after N failures
pytest tests/validation/immediate/ --maxfail=3

# Show local variables in tracebacks
pytest tests/validation/immediate/ -l

# Full traceback (not abbreviated)
pytest tests/validation/immediate/ --tb=long

# Short traceback
pytest tests/validation/immediate/ --tb=short

# Line-only traceback
pytest tests/validation/immediate/ --tb=line

# Drop into debugger on failure
pytest tests/validation/immediate/ --pdb

# Drop into debugger at start of each test
pytest tests/validation/immediate/ --trace
```

### Performance and Timing
```bash
# Show slowest 10 tests
pytest tests/validation/immediate/ --durations=10

# Show all test durations
pytest tests/validation/immediate/ --durations=0

# Benchmark tests (if pytest-benchmark installed)
pytest tests/validation/immediate/ --benchmark-only
```

### Timed Transition Tests (Currently Blocked)
```bash
# Run timed tests (4/10 passing due to controller issue)
pytest tests/validation/timed/ -v

# Skip known failing tests
pytest tests/validation/timed/ -v --ignore=test_basic_timing.py::test_fires_after_earliest_delay
```

## CI/CD Command

Recommended command for continuous integration:

```bash
pytest tests/validation/immediate/ \
  --cov=src/shypn/engine \
  --cov-report=term \
  --cov-report=xml \
  --cov-fail-under=30 \
  --tb=short \
  -v \
  || echo "Tests failed with exit code $?"
```

## Quick Status Check

```bash
# Quick pass/fail status
pytest tests/validation/immediate/ -q

# Count tests
pytest tests/validation/immediate/ --collect-only | grep "test session starts" -A 1

# List all tests
pytest tests/validation/immediate/ --collect-only

# Show test structure
pytest tests/validation/immediate/ --collect-only -q
```

## Coverage Analysis

```bash
# Generate coverage report
pytest tests/validation/immediate/ \
  --cov=src/shypn/engine \
  --cov-report=html

# View coverage report in browser
firefox htmlcov/index.html  # or: chromium, google-chrome, open (macOS)

# Show missing lines
pytest tests/validation/immediate/ \
  --cov=src/shypn/engine \
  --cov-report=term-missing

# Coverage for specific module
pytest tests/validation/immediate/ \
  --cov=src/shypn/engine/immediate_behavior \
  --cov-report=term
```

## Watch Mode (Continuous Testing)

```bash
# Install pytest-watch
pip install pytest-watch

# Watch for changes and re-run tests
ptw tests/validation/immediate/ -- -v

# Watch with coverage
ptw tests/validation/immediate/ -- --cov=src/shypn/engine --cov-report=term
```

## Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/validation/immediate/ -n 4

# Auto-detect number of CPUs
pytest tests/validation/immediate/ -n auto
```

## Test Markers (Future Enhancement)

```python
# In test files, you can add markers:
@pytest.mark.slow
def test_something_slow():
    ...

@pytest.mark.smoke
def test_critical_path():
    ...
```

```bash
# Run only smoke tests
pytest tests/validation/immediate/ -m smoke

# Run everything except slow tests
pytest tests/validation/immediate/ -m "not slow"

# Run smoke OR critical tests
pytest tests/validation/immediate/ -m "smoke or critical"
```

## Expected Results

### Current Status (2025-01-28)

```
✅ Immediate Transitions: 47/47 passing (100%)
   • test_basic_firing.py:    6/6   ✅
   • test_arc_weights.py:     9/9   ✅
   • test_guards.py:         17/17  ✅
   • test_priorities.py:     15/15  ✅

🔍 Timed Transitions: 4/10 passing (40%)
   • Blocked by controller scheduling issue
   • See: doc/validation/timed/TIMED_PHASE5_INVESTIGATION.md

📊 Coverage: 31% (+10% from baseline)
   • immediate_behavior.py: 65%
   • conflict_policy.py: 88%
   • transition_behavior.py: 50%
```

## Troubleshooting

### Import Errors
```bash
# If you get "ModuleNotFoundError: No module named 'shypn'"
pip install -e .
```

### Coverage Not Working
```bash
# Reinstall pytest-cov
pip install --upgrade pytest-cov
```

### Tests Running Slow
```bash
# Use parallel execution
pip install pytest-xdist
pytest tests/validation/immediate/ -n auto
```

### Fixture Errors
```bash
# Check conftest.py is in place
ls tests/validation/immediate/conftest.py

# Re-run with verbose output
pytest tests/validation/immediate/ -vv
```

## Documentation

For detailed information about test results and findings:

- **Phase Reports**: `doc/validation/immediate/`
- **Investigation Reports**: `doc/validation/timed/`
- **Session Summary**: `doc/validation/VALIDATION_SESSION_SUMMARY.md`
- **Execution Report**: `doc/validation/TEST_EXECUTION_REPORT.md`

## Support

For issues or questions:
1. Check documentation in `doc/validation/`
2. Review test output with `-vv` flag
3. Check coverage report for missing areas
4. Review conftest.py for fixture definitions

---

**Last Updated**: 2025-01-28  
**Test Suite Version**: 1.0  
**Status**: Immediate tests complete, Timed tests blocked
