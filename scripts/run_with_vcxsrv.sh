#!/bin/bash
# Launch SHYpn with VcXsrv on display :99
# Use this to test if VcXsrv has better popover behavior than WSLg

echo "========================================="
echo "SHYpn Launcher - VcXsrv Backend"
echo "========================================="
echo ""

# Check if VcXsrv is accessible
export DISPLAY=:99
if ! xset q &>/dev/null; then
    echo "❌ ERROR: VcXsrv on :99 is not accessible"
    echo ""
    echo "📝 Please start VcXsrv on Windows first:"
    echo "   1. Open XLaunch or VcXsrv"
    echo "   2. Choose 'Multiple windows'"
    echo "   3. Set display number to: 99"
    echo "   4. Check 'Disable access control'"
    echo "   5. Start"
    echo ""
    echo "   Or use command line:"
    echo "   vcxsrv.exe :99 -multiwindow -clipboard -wgl -ac"
    echo ""
    exit 1
fi

echo "✅ VcXsrv on :99 is accessible"
echo ""

# Set environment for X11 backend
export DISPLAY=:99
export GDK_BACKEND=x11
unset WAYLAND_DISPLAY

echo "🔧 Environment Settings:"
echo "   DISPLAY: $DISPLAY"
echo "   GDK_BACKEND: $GDK_BACKEND"
echo "   WAYLAND_DISPLAY: (unset)"
echo ""

# Get GTK4 display info
echo "🔍 GTK4 Display Detection:"
/usr/bin/python3 << 'PYTHON_CHECK'
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

display = Gdk.Display.get_default()
if display:
    print(f"   Display Type: {type(display).__name__}")
    print(f"   Display Name: {display.get_name()}")
    print(f"   GTK Version: {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}")
else:
    print("   ❌ Could not get display")
PYTHON_CHECK

echo ""
echo "========================================="
echo "Starting SHYpn with VcXsrv..."
echo "========================================="
echo ""

# Launch the application
cd "$(dirname "$0")/.."
exec /usr/bin/python3 src/shypn.py
