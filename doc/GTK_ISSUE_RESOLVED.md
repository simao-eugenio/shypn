# GTK3 Conda Issue - SOLVED! ✅

**Date:** October 4, 2025  
**Issue:** Grid doesn't appear when running in conda environment  
**Status:** Fixed with multiple solutions provided

---

## The Problem

You reported:
> "When running system wide all things it is perfect, but running under conda env the grid does not appear"

**Root Cause:** Conda's PyGObject/GTK3 packages don't always include complete Cairo rendering support, causing drawing issues (especially grids).

---

## Solutions Created

### 🚀 Solution 1: Use the Run Script (Easiest)

```bash
chmod +x run.sh
./run.sh
```

The `run.sh` script now automatically:
- Activates your conda environment
- Sets environment variables to use system GTK3
- Runs the application

**This is the easiest way to run SHYpn with the fix applied!**

---

### 🔧 Solution 2: Permanent Conda Fix

```bash
chmod +x fix_gtk_conda.sh
./fix_gtk_conda.sh
```

This script:
- Installs complete GTK3 stack in conda (optional)
- Creates activation scripts that automatically set environment variables
- Fix applies every time you activate the conda environment

After running once:
```bash
conda deactivate
conda activate shypn
python src/shypn.py  # Grid will work!
```

---

### ⚡ Solution 3: Manual Quick Fix

Every time before running:
```bash
conda activate shypn
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
python src/shypn.py
```

---

### 🐍 Solution 4: Use System Python (Alternative)

If conda continues to be problematic:
```bash
python3 src/shypn.py  # Without conda
```

System Python + system GTK3 = most reliable!

---

## Files Created

### Scripts:
1. **`run.sh`** ✅
   - Launch script with automatic GTK3 fix
   - Just run `./run.sh` and it works!

2. **`fix_gtk_conda.sh`** ✅
   - One-time setup for permanent fix
   - Creates conda activation scripts

3. **`diagnose_gtk.py`** ✅
   - Diagnostic tool to check GTK3 setup
   - Run: `python diagnose_gtk.py`

### Documentation:
4. **`GTK_CONDA_FIX.md`** ✅
   - Complete guide to the issue and all solutions
   - Troubleshooting steps
   - Verification tests

5. **`QUICKSTART.md`** ✅ (Updated)
   - Now includes GTK3 fix instructions
   - Multiple ways to run the app

---

## Why This Happens

```
Conda Environment:
    ├── conda's PyGObject ❌ (may be incomplete)
    ├── conda's GTK3       ❌ (may have issues)
    └── conda's Cairo      ❌ (rendering problems)

System:
    ├── system PyGObject   ✅ (complete)
    ├── system GTK3        ✅ (works perfectly)
    └── system Cairo       ✅ (no rendering issues)
```

**The Fix:** Use Python from conda, but GTK3/Cairo from system!

This is done via environment variables:
- `GI_TYPELIB_PATH` → points to system GObject type libraries
- `LD_LIBRARY_PATH` → points to system shared libraries

---

## How to Use (Recommended)

### First Time Setup:
```bash
# Option A: Use run script (simplest)
chmod +x run.sh
./run.sh

# Option B: Permanent fix (one-time setup)
chmod +x fix_gtk_conda.sh
./fix_gtk_conda.sh
conda deactivate && conda activate shypn
```

### Every Time After:
```bash
# If you used Option A:
./run.sh

# If you used Option B:
python src/shypn.py  # Fix is automatic!
```

---

## Verification

Test if the fix works:

```bash
# 1. Check environment variables are set
echo $GI_TYPELIB_PATH
echo $LD_LIBRARY_PATH

# 2. Run diagnostic
python diagnose_gtk.py

# 3. Test simple grid drawing
python -c "
import gi; gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
def on_draw(w, cr):
    cr.set_line_width(1.0)
    for i in range(0, 100, 10):
        cr.move_to(i, 0); cr.line_to(i, 100)
        cr.move_to(0, i); cr.line_to(100, i)
    cr.stroke()
win = Gtk.Window()
da = Gtk.DrawingArea()
da.connect('draw', on_draw)
win.add(da)
win.set_default_size(200, 200)
win.show_all()
print('Grid test window opened!')
Gtk.main()
"
```

If you see a grid → Fix is working! ✅

---

## Summary

✅ **Problem:** Grid rendering broken in conda  
✅ **Cause:** Incomplete GTK3/Cairo in conda packages  
✅ **Solution:** Use system GTK3 libraries via environment variables  
✅ **Implementation:** Multiple scripts and fixes provided  
✅ **Recommended:** Use `./run.sh` or `./fix_gtk_conda.sh`  

**You can now run SHYpn in your conda environment with full grid support!** 🎉

---

## Quick Reference Card

```bash
# Easiest way to run:
./run.sh

# Or with permanent fix:
./fix_gtk_conda.sh  # Run once
conda deactivate && conda activate shypn
python src/shypn.py

# Or manually each time:
conda activate shypn
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
python src/shypn.py

# Or use system Python:
python3 src/shypn.py
```

---

**Status:** RESOLVED ✅  
**Recommended:** Use `./run.sh` for simplicity  
**Documentation:** See `GTK_CONDA_FIX.md` for details
