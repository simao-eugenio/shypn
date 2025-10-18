# Installing pytest and Testing Tools

This guide shows you how to install pytest and related testing packages for the SHYpn project.

---

## Quick Installation

### Option 1: Install All Test Dependencies at Once

```bash
cd /home/simao/projetos/shypn
pip install pytest pytest-cov pytest-benchmark pytest-html pytest-timeout
```

### Option 2: Install from requirements-test.txt (Recommended)

```bash
cd /home/simao/projetos/shypn
pip install -r requirements-test.txt
```

---

## Detailed Installation Guide

### 1. Core Testing Package

**pytest** - The main testing framework

```bash
pip install pytest
```

**What it does**: Discovers and runs tests, provides fixtures, assertions
**Current version**: 7.4.4 (you already have this!)
**Verify**: `pytest --version`

```bash
$ pytest --version
pytest 7.4.4
```

---

### 2. Coverage Analysis

**pytest-cov** - Measures code coverage

```bash
pip install pytest-cov
```

**What it does**: Shows which lines of code are executed by tests
**Usage**:
```bash
# Basic coverage
pytest --cov=shypn

# With HTML report
pytest --cov=shypn --cov-report=html

# Show missing lines
pytest --cov=shypn --cov-report=term-missing
```

**Example output**:
```
---------- coverage: platform linux, python 3.12.3 -----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/shypn/engine/simulation.py           120     15    87%   45-52, 89
src/shypn/netobjs/transition.py           85      8    91%   102-105
---------------------------------------------------------------------
TOTAL                                     205     23    89%
```

---

### 3. Performance Benchmarking

**pytest-benchmark** - Measures and compares performance

```bash
pip install pytest-benchmark
```

**What it does**: Times test execution, tracks performance over time
**Usage**:
```bash
# Run benchmark tests
pytest tests/benchmark/immediate/ --benchmark-only

# Save baseline
pytest --benchmark-save=baseline

# Compare with baseline
pytest --benchmark-compare=baseline
```

**Example output**:
```
----------------------- benchmark: 5 tests -----------------------
Name                           Min      Mean    StdDev    Rounds
------------------------------------------------------------------
test_single_firing          1.23ms   1.45ms    0.12ms       100
test_multiple_firings      10.45ms  11.23ms    0.89ms        50
------------------------------------------------------------------
```

---

### 4. HTML Test Reports

**pytest-html** - Generates beautiful HTML reports

```bash
pip install pytest-html
```

**What it does**: Creates detailed HTML test reports with screenshots, logs
**Usage**:
```bash
# Generate HTML report
pytest --html=report.html --self-contained-html

# Open report
firefox report.html  # or your browser
```

**Features**:
- Summary statistics
- Pass/fail details
- Test duration
- Error tracebacks
- Screenshots (if configured)

---

### 5. Test Timeouts

**pytest-timeout** - Prevents tests from hanging

```bash
pip install pytest-timeout
```

**What it does**: Kills tests that take too long
**Usage**:
```bash
# Set global timeout (10 seconds)
pytest --timeout=10

# Or in test:
@pytest.mark.timeout(5)
def test_something():
    pass
```

---

## Complete Installation Script

Save this as `install_test_tools.sh`:

```bash
#!/bin/bash
# Install all pytest testing tools for SHYpn

echo "Installing pytest testing tools..."

# Core testing
pip install pytest

# Coverage analysis
pip install pytest-cov

# Performance benchmarking
pip install pytest-benchmark

# HTML reports
pip install pytest-html

# Timeout handling
pip install pytest-timeout

echo ""
echo "✅ Installation complete!"
echo ""
echo "Verify installation:"
pytest --version
python3 -c "import pytest_cov; print('pytest-cov: OK')"
python3 -c "import pytest_benchmark; print('pytest-benchmark: OK')"
python3 -c "import pytest_html; print('pytest-html: OK')"
python3 -c "import pytest_timeout; print('pytest-timeout: OK')"
```

Run it:
```bash
chmod +x install_test_tools.sh
./install_test_tools.sh
```

---

## Verification Commands

After installation, verify each package:

```bash
# Check pytest
pytest --version

# Check pytest-cov
python3 -c "import pytest_cov; print('pytest-cov installed')"

# Check pytest-benchmark
python3 -c "import pytest_benchmark; print('pytest-benchmark installed')"

# Check pytest-html
python3 -c "import pytest_html; print('pytest-html installed')"

# Check pytest-timeout
python3 -c "import pytest_timeout; print('pytest-timeout installed')"
```

---

## Testing Your Installation

### Run Your First Test

```bash
cd /home/simao/projetos/shypn/tests/validation/immediate
pytest test_basic_firing.py -v
```

**Expected output**:
```
============================== test session starts ==============================
collected 6 items

test_basic_firing.py::test_fires_when_enabled PASSED                      [ 16%]
test_basic_firing.py::test_does_not_fire_when_disabled PASSED             [ 33%]
test_basic_firing.py::test_fires_immediately_at_t0 PASSED                 [ 50%]
test_basic_firing.py::test_fires_multiple_times PASSED                    [ 66%]
test_basic_firing.py::test_consumes_tokens_correctly PASSED               [ 83%]
test_basic_firing.py::test_produces_tokens_correctly PASSED               [100%]

============================== 6 passed in 0.04s ================================
```

### Try Coverage

```bash
pytest test_basic_firing.py --cov=shypn.engine --cov-report=term-missing
```

### Try HTML Report

```bash
pytest test_basic_firing.py --html=report.html --self-contained-html
firefox report.html
```

---

## Package Versions (Recommended)

Create `requirements-test.txt`:

```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-benchmark>=4.0.0
pytest-html>=3.2.0
pytest-timeout>=2.1.0
```

Install from file:
```bash
pip install -r requirements-test.txt
```

---

## Common Installation Issues

### Issue 1: pip not found
```bash
# Install pip
sudo apt-get install python3-pip  # Ubuntu/Debian
```

### Issue 2: Permission denied
```bash
# Use --user flag
pip install --user pytest pytest-cov pytest-benchmark
```

### Issue 3: Package conflicts
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install pytest pytest-cov pytest-benchmark
```

---

## Using Virtual Environment (Recommended)

Virtual environments keep packages isolated:

```bash
# Create virtual environment
cd /home/simao/projetos/shypn
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install pytest pytest-cov pytest-benchmark pytest-html pytest-timeout

# Verify
pytest --version

# Deactivate when done
deactivate
```

**Benefits**:
- No system-wide installation
- No permission issues
- Easy to reset (delete venv folder)
- Project-specific versions

---

## Configuration Files

### pytest.ini

Create `/home/simao/projetos/shypn/pytest.ini`:

```ini
[tool:pytest]
# Test discovery patterns
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# Minimum version
minversion = 7.0

# Test paths
testpaths = tests

# Output options
addopts = 
    -v
    --strict-markers
    --tb=short

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    stress: marks tests as stress tests
    ui: marks tests that require UI/GTK
    integration: marks integration tests

# Coverage options
[coverage:run]
source = src/shypn
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

---

## Quick Reference Card

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/validation/immediate/test_basic_firing.py

# Run specific test
pytest tests/validation/immediate/test_basic_firing.py::test_fires_when_enabled

# Run with coverage
pytest --cov=shypn --cov-report=html

# Run with verbose output
pytest -v

# Run only fast tests (skip slow)
pytest -m "not slow"

# Run with HTML report
pytest --html=report.html --self-contained-html

# Run benchmarks
pytest tests/benchmark/ --benchmark-only

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Parallel execution (needs pytest-xdist)
pytest -n auto
```

---

## Summary

**Minimum install** (for basic testing):
```bash
pip install pytest
```

**Recommended install** (for full features):
```bash
pip install pytest pytest-cov pytest-benchmark pytest-html pytest-timeout
```

**Best practice** (with virtual environment):
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt
```

---

## Next Steps

1. ✅ Install packages
2. ✅ Verify installation
3. ✅ Run existing tests
4. 🔄 Write more tests
5. 📊 Generate coverage reports
6. ⚡ Run benchmarks

**Happy testing!** 🎉
