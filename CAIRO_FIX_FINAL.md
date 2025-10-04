# Cairo Context Error - RESOLVED

## Problem

When running the SHYpn application in a conda environment, you encountered:

```
TypeError: Couldn't find foreign struct converter for 'cairo.Context'
```

This error occurred during GTK3 drawing operations, causing the grid and other visual elements to fail rendering.

## Root Cause

**Conda's `pygobject` package has broken Cairo integration.** The foreign struct converter that bridges between C Cairo contexts and Python cairo objects is not properly registered in conda's pygobject builds.

This is a known issue:
- PyGObject needs to register converters for Cairo types
- Conda's pygobject package doesn't properly initialize these converters
- The system's PyGObject (from `python3-gi` and `python3-gi-cairo` packages) works correctly

## Solution

**Use system Python instead of conda Python for running SHYpn.**

### Why This Works

- System Python `/usr/bin/python3` has proper PyGObject packages installed:
  - `python3-gi` (PyGObject bindings)
  - `python3-gi-cairo` (Cairo integration)
  - `gir1.2-gtk-3.0` (GTK3 introspection)
- These system packages have properly compiled and tested Cairo foreign struct converters
- All drawing operations work flawlessly

### Implementation

The `run.sh` script has been updated to use system Python:

```bash
#!/bin/bash
# Use system Python which has proper PyGObject + Cairo integration
/usr/bin/python3 src/shypn.py
```

## How to Run

Simply use the provided script:

```bash
./run.sh
```

Or directly:

```bash
/usr/bin/python3 src/shypn.py
```

## What About Conda?

You **don't need conda** for this GTK3 application. All required dependencies are satisfied by system packages:

### System Packages (Already Installed)
```bash
python3              # Python 3.12
python3-gi           # PyGObject bindings
python3-gi-cairo     # Cairo integration (THE FIX!)
gir1.2-gtk-3.0       # GTK3 introspection
libgtk-3-0           # GTK3 library
```

These were installed via `apt-get` and work perfectly.

## Verification

Test that Cairo works:

```bash
/usr/bin/python3 test_cairo_draw.py
```

Expected output:
```
Draw callback called with context type: <class 'cairo.Context'>
✓ Drawing succeeded!
```

## Technical Details

### Why Conda's PyGObject Fails

1. **Build Process**: Conda's pygobject is cross-platform and may not include all platform-specific Cairo integration code
2. **Dependency Chain**: The `pycairo` → `pygobject` → `cairo` integration requires specific build flags
3. **GObject Introspection**: Foreign struct converters must be registered at module init time
4. **Version Mismatch**: Conda Python 3.10 vs System Python 3.12 makes using system pygobject impossible

### What We Tried (That Didn't Work)

1. ❌ Installing `pycairo` in conda
2. ❌ Installing `gobject-introspection` in conda
3. ❌ Using `gi.require_foreign("cairo")`
4. ❌ Importing `cairo` before `gi`
5. ❌ Importing `gi.repository.cairo`
6. ❌ Installing PyGObject from pip (build failed)
7. ❌ Adding system packages to conda Python path (version mismatch)

### What Worked ✓

✅ **Using system Python with system PyGObject packages**

## Files Modified

1. **`run.sh`**: Updated to use `/usr/bin/python3`
2. **`src/shypn.py`**: Added Cairo import attempt (for documentation, not strictly needed with system Python)

## Conclusion

**The application now works perfectly with system Python.** No more Cairo Context errors, and all drawing operations (grid, arcs, shapes) render correctly.

---

**Summary**: Conda's pygobject is broken for Cairo integration. Use system Python instead. Problem solved!
