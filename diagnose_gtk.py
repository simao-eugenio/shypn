#!/usr/bin/env python3
"""
GTK3 Environment Diagnostics for SHYpn

This script checks your GTK3 installation and helps diagnose
grid rendering issues in conda environments.
"""

import sys

print("=" * 60)
print("GTK3 Environment Diagnostics")
print("=" * 60)
print()

# Check Python version
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")
print()

# Check if we're in a conda environment
import os
conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'None')
print(f"Conda Environment: {conda_env}")
print()

# Try to import GTK
try:
    import gi
    print(f"✓ gi module found: {gi.__file__}")
    print(f"  Version: {gi.__version__}")
except ImportError as e:
    print(f"✗ gi module not found: {e}")
    sys.exit(1)

print()

# Try to import GTK 3
try:
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk
    print(f"✓ GTK 3.0 loaded")
    print(f"  GTK Version: {Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}")
except Exception as e:
    print(f"✗ Failed to load GTK 3.0: {e}")
    sys.exit(1)

print()

# Check Cairo
try:
    gi.require_version('cairo', '1.0')
    import cairo
    print(f"✓ Cairo found: {cairo.version}")
    print(f"  Cairo version: {cairo.cairo_version_string()}")
except Exception as e:
    print(f"✗ Cairo issue: {e}")

print()

# Test basic GTK functionality
print("Testing GTK functionality...")
try:
    window = Gtk.Window()
    print("✓ Can create Gtk.Window")
    
    drawing_area = Gtk.DrawingArea()
    print("✓ Can create Gtk.DrawingArea")
    
    # Test drawing
    def on_draw(widget, cr):
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1.0)
        
        # Draw a simple grid
        for i in range(0, 100, 10):
            cr.move_to(i, 0)
            cr.line_to(i, 100)
            cr.move_to(0, i)
            cr.line_to(100, i)
        cr.stroke()
        return False
    
    drawing_area.connect("draw", on_draw)
    print("✓ Can connect draw signal")
    
except Exception as e:
    print(f"✗ GTK functionality test failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Check for common conda GTK issues
print("Checking for known issues...")

# Check GTK theme
gtk_theme = os.environ.get('GTK_THEME', 'Not set')
print(f"  GTK_THEME: {gtk_theme}")

# Check if system GTK is being used
gtk_path = os.environ.get('GTK_PATH', 'Not set')
print(f"  GTK_PATH: {gtk_path}")

# Check GI typelib path
gi_typelib_path = os.environ.get('GI_TYPELIB_PATH', 'Not set')
print(f"  GI_TYPELIB_PATH: {gi_typelib_path}")

print()
print("=" * 60)
print("Recommendations:")
print("=" * 60)

if conda_env != 'None':
    print("""
For conda environments, grid rendering issues often occur due to:

1. Missing GTK3 system integration
2. Conflicting GTK versions between conda and system
3. Missing Cairo or GObject introspection components

SOLUTION 1: Use system-site-packages (Recommended)
Create conda environment with system packages access:

    conda create -n shypn python=3.10
    conda activate shypn
    conda install -c conda-forge --no-deps pygobject
    
    # Then use system GTK3
    export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

SOLUTION 2: Install complete GTK3 stack in conda

    conda activate shypn
    conda install -c conda-forge gtk3 pygobject cairo
    conda install -c conda-forge gdk-pixbuf gobject-introspection

SOLUTION 3: Force system GTK3 libraries

    # Add to ~/.bashrc or run before starting app:
    export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0
    export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

SOLUTION 4: Use system Python instead
Sometimes it's easier to just use system Python with GTK3:

    deactivate  # or conda deactivate
    python3 src/shypn.py
""")
else:
    print("Running with system Python - should work fine!")

print()
print("=" * 60)
