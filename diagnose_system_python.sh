#!/bin/bash
# System Python Diagnostics
# Verifies that all GTK3 + Cairo dependencies are properly installed

echo "======================================"
echo "  SHYpn - System Python Diagnostics"
echo "======================================"
echo ""

# Check Python
echo "1. Checking Python..."
if /usr/bin/python3 --version > /dev/null 2>&1; then
    PYTHON_VERSION=$(/usr/bin/python3 --version 2>&1)
    echo "   ✓ $PYTHON_VERSION"
else
    echo "   ✗ Python not found at /usr/bin/python3"
    exit 1
fi
echo ""

# Check PyGObject (gi)
echo "2. Checking PyGObject (gi module)..."
if /usr/bin/python3 -c "import gi; print('   ✓ PyGObject version:', gi.__version__)" 2>/dev/null; then
    :
else
    echo "   ✗ PyGObject not found"
    echo "   Install with: sudo apt-get install python3-gi"
    exit 1
fi
echo ""

# Check GTK3
echo "3. Checking GTK3..."
if /usr/bin/python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print(f'   ✓ GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}')" 2>/dev/null; then
    :
else
    echo "   ✗ GTK3 not found"
    echo "   Install with: sudo apt-get install gir1.2-gtk-3.0 libgtk-3-0"
    exit 1
fi
echo ""

# Check Cairo
echo "4. Checking Cairo integration..."
if /usr/bin/python3 -c "import gi; gi.require_version('Gtk', '3.0'); gi.require_version('cairo', '1.0'); from gi.repository import Gtk, cairo; print('   ✓ Cairo integration available')" 2>/dev/null; then
    :
else
    echo "   ✗ Cairo integration not available"
    echo "   Install with: sudo apt-get install python3-gi-cairo"
    exit 1
fi
echo ""

# Test drawing
echo "5. Testing Cairo drawing..."
DRAW_TEST=$(/usr/bin/python3 << 'EOF' 2>&1
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

success = False

def on_draw(widget, cr):
    global success
    try:
        cr.set_source_rgb(1, 0, 0)
        cr.paint()
        success = True
    except Exception as e:
        print(f"   ✗ Drawing failed: {e}")
    return False

window = Gtk.Window()
drawing_area = Gtk.DrawingArea()
drawing_area.connect("draw", on_draw)
window.add(drawing_area)
window.show_all()

# Trigger draw and quit immediately
GLib.timeout_add(100, Gtk.main_quit)
Gtk.main()

if success:
    print("   ✓ Cairo drawing works!")
else:
    print("   ✗ Cairo drawing failed!")
EOF
)

echo "$DRAW_TEST"

if echo "$DRAW_TEST" | grep -q "✓ Cairo drawing works!"; then
    :
else
    echo ""
    echo "   Cairo drawing test failed!"
    echo "   This may indicate missing python3-gi-cairo package."
    exit 1
fi
echo ""

# Check if shypn.py exists
echo "6. Checking application files..."
if [ -f "src/shypn.py" ]; then
    echo "   ✓ src/shypn.py found"
else
    echo "   ✗ src/shypn.py not found"
    echo "   Run this script from the shypn project root directory"
    exit 1
fi
echo ""

# Final summary
echo "======================================"
echo "  ✓ ALL CHECKS PASSED!"
echo "======================================"
echo ""
echo "Your system is ready to run SHYpn."
echo ""
echo "Run the application:"
echo "  ./run.sh"
echo ""
echo "Or directly:"
echo "  /usr/bin/python3 src/shypn.py"
echo ""
