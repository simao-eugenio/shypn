# pytest Quick Installation Guide

## 🚀 Quick Start (3 Methods)

### Method 1: Run Installation Script (Easiest)
```bash
cd /home/simao/projetos/shypn
./install_test_tools.sh
```

### Method 2: Install from requirements file
```bash
cd /home/simao/projetos/shypn
pip3 install -r requirements-test.txt
```

### Method 3: Manual installation
```bash
pip3 install pytest pytest-cov pytest-benchmark pytest-html pytest-timeout
```

---

## 📦 What Gets Installed

| Package | Purpose | Command to Test |
|---------|---------|----------------|
| **pytest** | Core testing framework | `pytest --version` |
| **pytest-cov** | Code coverage analysis | `pytest --cov=shypn` |
| **pytest-benchmark** | Performance testing | `pytest --benchmark-only` |
| **pytest-html** | HTML test reports | `pytest --html=report.html` |
| **pytest-timeout** | Prevent hanging tests | `pytest --timeout=10` |

---

## ✅ Verify Installation

```bash
# Quick check - run this command:
python3 -c "import pytest, pytest_cov, pytest_benchmark, pytest_html, pytest_timeout; print('✅ All packages installed!')"
```

**Expected output**: `✅ All packages installed!`

---

## 🧪 Test Your Installation

### 1. Run existing tests
```bash
cd /home/simao/projetos/shypn/tests/validation/immediate
pytest test_basic_firing.py -v
```

**Expected**: 6 tests passing ✅

### 2. Try with coverage
```bash
pytest test_basic_firing.py --cov=shypn.engine --cov-report=term-missing
```

**Expected**: Coverage report showing tested lines

### 3. Try HTML report
```bash
pytest test_basic_firing.py --html=report.html --self-contained-html
firefox report.html  # or xdg-open report.html
```

**Expected**: Beautiful HTML report opens in browser

---

## 📚 Common Commands

```bash
# Run all tests in directory
pytest tests/validation/immediate/

# Run specific test
pytest tests/validation/immediate/test_basic_firing.py::test_fires_when_enabled

# Run with verbose output
pytest -v

# Stop at first failure
pytest -x

# Show what tests would run (don't execute)
pytest --collect-only

# Run only fast tests (skip slow ones)
pytest -m "not slow"

# Run with coverage + HTML report
pytest --cov=shypn --cov-report=html --html=test_report.html
```

---

## 🐛 Troubleshooting

### Problem: "pip3: command not found"
**Solution**:
```bash
sudo apt-get install python3-pip
```

### Problem: "Permission denied"
**Solution**: Install for user only:
```bash
pip3 install --user pytest pytest-cov pytest-benchmark
```

### Problem: "Package conflicts"
**Solution**: Use virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements-test.txt
```

### Problem: "pytest-benchmark not found"
**Check installation**:
```bash
python3 -c "import pytest_benchmark; print('OK')"
```
**If fails**: Reinstall:
```bash
pip3 install --upgrade pytest-benchmark
```

---

## 📖 Full Documentation

For complete details, see: `/doc/validation/PYTEST_INSTALLATION_GUIDE.md`

---

## 🎯 Next Steps

1. ✅ Install packages (you are here)
2. Run tests: `cd tests/validation/immediate && pytest -v`
3. Check coverage: `pytest --cov=shypn`
4. Write more tests!

**Happy testing!** 🧪
