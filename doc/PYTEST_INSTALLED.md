# ✅ pytest Installation Complete!

## 🎉 SUCCESS - All Packages Installed

The following packages are now installed in the virtual environment:

- ✅ **pytest 8.4.2** - Core testing framework
- ✅ **pytest-cov 7.0.0** - Code coverage analysis
- ✅ **pytest-benchmark 5.1.0** - Performance testing
- ✅ **pytest-html 4.1.1** - HTML test reports
- ✅ **pytest-timeout 2.4.0** - Test timeout handling

---

## 🚀 How to Use

### Step 1: Activate Virtual Environment

**EVERY TIME** you want to run tests, activate the virtual environment first:

```bash
cd /home/simao/projetos/shypn
source venv/bin/activate
```

You'll see `(venv)` in your prompt: `(venv) simao@Antares:~/projetos/shypn$`

### Step 2: Run Tests

```bash
# Basic test run
cd tests/validation/immediate
pytest test_basic_firing.py -v

# With coverage
pytest test_basic_firing.py --cov=shypn --cov-report=term-missing

# HTML report
pytest test_basic_firing.py --html=report.html --self-contained-html

# All tests in directory
pytest -v
```

### Step 3: Deactivate When Done

```bash
deactivate
```

---

## 📋 Quick Commands Reference

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Go to test directory
cd tests/validation/immediate

# 3. Run tests
pytest test_basic_firing.py -v

# 4. Deactivate when done
deactivate
```

---

## ⚠️ Known Issue: GTK Dependencies

The tests require GTK (PyGObject) which isn't in the virtual environment. You have two options:

### Option A: Install PyGObject system-wide (Recommended)
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0
```

### Option B: Use system Python packages in venv
```bash
# Recreate venv with system packages
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements-test.txt
```

---

## 🧪 Test Your Setup

### Quick Test (No GTK needed)
```bash
source venv/bin/activate
python -c "import pytest; print(f'pytest {pytest.__version__} installed ✅')"
```

### Full Test (Needs GTK)
```bash
source venv/bin/activate
cd tests/validation/immediate
pytest test_basic_firing.py -v
```

---

## 📊 Example Usage Session

```bash
$ cd /home/simao/projetos/shypn
$ source venv/bin/activate
(venv) $ cd tests/validation/immediate
(venv) $ pytest test_basic_firing.py -v

============================== test session starts ==============================
collected 6 items

test_basic_firing.py::test_fires_when_enabled PASSED                      [ 16%]
test_basic_firing.py::test_does_not_fire_when_disabled PASSED             [ 33%]
test_basic_firing.py::test_fires_immediately_at_t0 PASSED                 [ 50%]
test_basic_firing.py::test_fires_multiple_times PASSED                    [ 66%]
test_basic_firing.py::test_consumes_tokens_correctly PASSED               [ 83%]
test_basic_firing.py::test_produces_tokens_correctly PASSED               [100%]

============================== 6 passed in 0.04s ================================

(venv) $ deactivate
$
```

---

## 🐛 Troubleshooting

### Problem: "No module named 'gi'"
**Solution**: Install GTK system packages:
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0
```

Then recreate venv with system packages:
```bash
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements-test.txt
```

### Problem: "venv/bin/activate: No such file"
**Solution**: Make sure you're in the project root:
```bash
cd /home/simao/projetos/shypn
source venv/bin/activate
```

### Problem: Tests still don't run
**Solution**: Check you're in venv and GTK is available:
```bash
source venv/bin/activate
python -c "from gi.repository import Gtk; print('GTK OK')"
```

---

## 📚 More Information

- **Quick Start**: See `PYTEST_QUICK_START.md`
- **Full Guide**: See `doc/validation/PYTEST_INSTALLATION_GUIDE.md`
- **Test Status**: See `doc/validation/immediate/COMPLETE_SUCCESS.md`

---

## ✨ Summary

**Installed**: ✅ All pytest packages  
**Location**: `/home/simao/projetos/shypn/venv`  
**Activate**: `source venv/bin/activate`  
**Test**: `cd tests/validation/immediate && pytest -v`  

**Happy testing!** 🧪
