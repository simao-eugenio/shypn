# GTK3 Grid Rendering Issue in Conda - Solutions

**Problem:** Grid doesn't appear when running SHYpn in conda environment, but works fine system-wide.

**Cause:** Conda's GTK3 packages may be incomplete or conflict with system GTK3 libraries, causing Cairo rendering issues.

---

## Quick Fix (Try This First)

```bash
# While in your shypn conda environment:
conda activate shypn

# Set environment variables to use system GTK3:
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Run the app:
python src/shypn.py
```

If this works, the grid should now appear! ✓

---

## Permanent Solutions

### Solution 1: Use the Fixed Run Script (Easiest)

```bash
# Make script executable
chmod +x run.sh

# Run the app (automatically applies the fix)
./run.sh
```

The `run.sh` script now includes the environment variables fix.

---

### Solution 2: Auto-Fix on Conda Activation (Recommended)

Run the fix script to automatically apply the solution every time you activate the conda environment:

```bash
# Make script executable
chmod +x fix_gtk_conda.sh

# Run the fix (only need to do once)
./fix_gtk_conda.sh

# Deactivate and reactivate to apply
conda deactivate
conda activate shypn

# Now run the app normally
python src/shypn.py
```

This creates activation/deactivation scripts in your conda environment that automatically set the correct environment variables.

---

### Solution 3: Install Complete GTK3 Stack in Conda

```bash
conda activate shypn
conda install -c conda-forge gtk3 pygobject cairo gdk-pixbuf gobject-introspection -y
```

This installs a complete GTK3 stack in your conda environment. May or may not work depending on your system.

---

### Solution 4: Use System Python (Alternative)

If conda continues to have issues, you can use system Python instead:

```bash
# Install system dependencies (if not already installed)
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Run with system Python
python3 src/shypn.py
```

System Python + system GTK3 is usually the most reliable combination.

---

## Diagnosis

To check your GTK3 setup and see what's wrong:

```bash
python3 diagnose_gtk.py
```

This will:
- Check if GTK3 is properly installed
- Test basic GTK functionality
- Show your environment variables
- Provide specific recommendations

---

## Understanding the Issue

### Why Does This Happen?

1. **Conda's GTK3:** When you install PyGObject via conda, it may bring its own GTK3 libraries
2. **System GTK3:** Your system has its own GTK3 libraries (which work fine)
3. **Conflict:** Conda's GTK3 may be incomplete or have version mismatches
4. **Result:** Cairo (the drawing library) doesn't work properly, grids don't render

### The Fix Explained

The environment variables force Python to use the system's GTK3 libraries instead of conda's:

- **`GI_TYPELIB_PATH`**: Where to find GObject introspection type libraries
- **`LD_LIBRARY_PATH`**: Where to find shared libraries (.so files)

By pointing these to the system directories (`/usr/lib/x86_64-linux-gnu`), we use the system's complete, working GTK3 stack.

---

## Verification

After applying a fix, verify it works:

```bash
conda activate shypn

# Test simple grid drawing
python3 -c "
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import cairo

def on_draw(widget, cr):
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(1.0)
    for i in range(0, 100, 10):
        cr.move_to(i, 0)
        cr.line_to(i, 100)
        cr.move_to(0, i)
        cr.line_to(100, i)
    cr.stroke()
    return False

win = Gtk.Window()
da = Gtk.DrawingArea()
da.connect('draw', on_draw)
win.add(da)
win.set_default_size(200, 200)
win.connect('destroy', Gtk.main_quit)
win.show_all()
print('If you see a grid in the window, the fix works!')
Gtk.main()
"
```

If you see a grid, the fix is working! ✓

---

## Scripts Created

1. **`run.sh`** - Launch script with automatic GTK3 fix
2. **`fix_gtk_conda.sh`** - One-time setup for automatic conda activation fix
3. **`diagnose_gtk.py`** - Diagnostic tool to check your GTK3 setup

All scripts are ready to use!

---

## Quick Reference

### Run with automatic fix:
```bash
./run.sh
```

### Run with manual fix:
```bash
conda activate shypn
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
python src/shypn.py
```

### Run with system Python (no conda):
```bash
python3 src/shypn.py
```

---

## Troubleshooting

### Still no grid?

1. **Check if Cairo is working:**
   ```bash
   python -c "import cairo; print('Cairo OK:', cairo.version)"
   ```

2. **Verify GTK3 version:**
   ```bash
   python -c "from gi.repository import Gtk; print(f'GTK: {Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}')"
   ```

3. **Check library paths:**
   ```bash
   echo $GI_TYPELIB_PATH
   echo $LD_LIBRARY_PATH
   ```

4. **Try system Python:**
   ```bash
   python3 src/shypn.py  # Without conda
   ```

---

## Summary

✅ **Problem Identified:** Conda GTK3 packages incomplete/conflicting  
✅ **Solution Created:** Use system GTK3 libraries via environment variables  
✅ **Scripts Provided:** Automatic fix on run or conda activation  
✅ **Fallback:** Use system Python if needed  

**Recommended:** Use `./run.sh` or run `./fix_gtk_conda.sh` once for permanent fix.

---

**Related Files:**
- `run.sh` - Launch with fix
- `fix_gtk_conda.sh` - Permanent conda fix
- `diagnose_gtk.py` - Diagnostic tool
- `QUICKSTART.md` - Updated with GTK3 fix info
