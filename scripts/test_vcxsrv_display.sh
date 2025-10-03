#!/bin/bash
# Test VcXsrv connection on display :99
# This script tests GTK4 app behavior with different display backends

echo "================================="
echo "VcXsrv Display Test - Port :99"
echo "================================="
echo ""

# Save current display settings
ORIGINAL_DISPLAY=$DISPLAY
ORIGINAL_WAYLAND=$WAYLAND_DISPLAY
ORIGINAL_GDK_BACKEND=$GDK_BACKEND

echo "📊 Current Environment:"
echo "  DISPLAY: $DISPLAY"
echo "  WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "  GDK_BACKEND: ${GDK_BACKEND:-'(auto)'}"
echo ""

# Test 1: Check if VcXsrv is accessible on :99
echo "🔍 Test 1: Check VcXsrv accessibility on :99"
export DISPLAY=:99
if xset q &>/dev/null; then
    echo "  ✅ VcXsrv on :99 is ACCESSIBLE"
    VCXSRV_AVAILABLE=true
else
    echo "  ❌ VcXsrv on :99 is NOT accessible"
    echo "  💡 Make sure VcXsrv is running on Windows with display number 99"
    echo "  💡 In VcXsrv config: -multiwindow -clipboard -wgl -ac -display 99"
    VCXSRV_AVAILABLE=false
fi
echo ""

if [ "$VCXSRV_AVAILABLE" = true ]; then
    # Test 2: Check GTK4 with X11 backend on :99
    echo "🔍 Test 2: GTK4 Detection on VcXsrv :99"
    export DISPLAY=:99
    export GDK_BACKEND=x11
    unset WAYLAND_DISPLAY
    
    /usr/bin/python3 << 'PYTHON_TEST'
import os
import sys
try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk
    
    print("  ✅ GTK4 imports successful")
    
    # Try to get default display
    display = Gdk.Display.get_default()
    if display:
        print(f"  ✅ Display connected: {type(display).__name__}")
        print(f"  📍 Display name: {display.get_name()}")
    else:
        print("  ❌ Could not get default display")
        sys.exit(1)
        
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)
PYTHON_TEST
    
    if [ $? -eq 0 ]; then
        echo "  ✅ GTK4 can connect to VcXsrv :99"
    else
        echo "  ❌ GTK4 cannot connect to VcXsrv :99"
    fi
    echo ""
    
    # Test 3: Run simple GTK4 window test
    echo "🔍 Test 3: Create test window on VcXsrv :99"
    export DISPLAY=:99
    export GDK_BACKEND=x11
    unset WAYLAND_DISPLAY
    
    timeout 3 /usr/bin/python3 << 'PYTHON_WINDOW_TEST' &
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

def on_activate(app):
    window = Gtk.ApplicationWindow(application=app)
    window.set_title("VcXsrv Test")
    window.set_default_size(300, 200)
    
    label = Gtk.Label(label="VcXsrv :99 Connection Test\nIf you see this, it works!")
    window.set_child(label)
    
    window.present()
    print("  ✅ Test window created on :99")
    
    # Close after 2 seconds
    GLib.timeout_add(2000, lambda: app.quit())

app = Gtk.Application(application_id='com.shypn.vcxsrv_test')
app.connect('activate', on_activate)
try:
    app.run(None)
    print("  ✅ Window displayed successfully")
except Exception as e:
    print(f"  ❌ Window error: {e}")
PYTHON_WINDOW_TEST
    
    WINDOW_PID=$!
    wait $WINDOW_PID
    echo ""
    
    # Test 4: Test Popover on VcXsrv
    echo "🔍 Test 4: Test Popover rendering on VcXsrv :99"
    export DISPLAY=:99
    export GDK_BACKEND=x11
    unset WAYLAND_DISPLAY
    
    timeout 5 /usr/bin/python3 << 'PYTHON_POPOVER_TEST' &
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib

def on_activate(app):
    window = Gtk.ApplicationWindow(application=app)
    window.set_title("Popover Test on VcXsrv")
    window.set_default_size(400, 300)
    
    # Create main box
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.set_margin_top(20)
    box.set_margin_bottom(20)
    box.set_margin_start(20)
    box.set_margin_end(20)
    
    # Create button to trigger popover
    button = Gtk.Button(label="Click to Test Popover")
    box.append(button)
    
    # Create simple popover
    popover = Gtk.Popover()
    popover.set_parent(button)
    
    # Popover content
    popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    popover_box.set_margin_top(10)
    popover_box.set_margin_bottom(10)
    popover_box.set_margin_start(10)
    popover_box.set_margin_end(10)
    
    popover_box.append(Gtk.Label(label="Popover Item 1"))
    popover_box.append(Gtk.Label(label="Popover Item 2"))
    popover_box.append(Gtk.Label(label="Popover Item 3"))
    
    popover.set_child(popover_box)
    popover.set_autohide(True)
    
    # Button click handler
    def on_button_clicked(btn):
        print("  🖱️  Button clicked, showing popover...")
        popover.popup()
        print("  ✅ Popover.popup() called successfully")
        # Check if visible after a moment
        GLib.timeout_add(100, lambda: print(f"  📊 Popover visible: {popover.get_visible()}"))
    
    button.connect('clicked', on_button_clicked)
    
    # Status label
    status = Gtk.Label(label="VcXsrv :99 Popover Test\nClick button above")
    box.append(status)
    
    window.set_child(box)
    window.present()
    print("  ✅ Test window with popover ready")
    print("  💡 Click the button to test popover rendering")
    
    # Auto-trigger popover after 1 second
    GLib.timeout_add(1000, lambda: on_button_clicked(button))
    
    # Close after 4 seconds
    GLib.timeout_add(4000, lambda: app.quit())

app = Gtk.Application(application_id='com.shypn.popover_test')
app.connect('activate', on_activate)
try:
    app.run(None)
except Exception as e:
    print(f"  ❌ Popover test error: {e}")
PYTHON_POPOVER_TEST
    
    wait
    echo ""
    
fi

# Test 5: Compare display backends
echo "🔍 Test 5: Backend Comparison"
echo ""
echo "  📊 Wayland (WSLg) - Current Default:"
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
unset GDK_BACKEND
/usr/bin/python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gdk; d = Gdk.Display.get_default(); print(f'    Type: {type(d).__name__}'); print(f'    Name: {d.get_name()}')" 2>/dev/null || echo "    ❌ Failed"
echo ""

if [ "$VCXSRV_AVAILABLE" = true ]; then
    echo "  📊 X11 (VcXsrv :99):"
    export DISPLAY=:99
    unset WAYLAND_DISPLAY
    export GDK_BACKEND=x11
    /usr/bin/python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gdk; d = Gdk.Display.get_default(); print(f'    Type: {type(d).__name__}'); print(f'    Name: {d.get_name()}')" 2>/dev/null || echo "    ❌ Failed"
fi
echo ""

# Restore original settings
export DISPLAY=$ORIGINAL_DISPLAY
export WAYLAND_DISPLAY=$ORIGINAL_WAYLAND
if [ -n "$ORIGINAL_GDK_BACKEND" ]; then
    export GDK_BACKEND=$ORIGINAL_GDK_BACKEND
else
    unset GDK_BACKEND
fi

echo "================================="
echo "Summary and Recommendations"
echo "================================="
echo ""

if [ "$VCXSRV_AVAILABLE" = true ]; then
    echo "✅ VcXsrv on :99 is available and working"
    echo ""
    echo "📝 To run SHYpn with VcXsrv instead of WSLg:"
    echo "   DISPLAY=:99 GDK_BACKEND=x11 python3 src/shypn.py"
    echo ""
    echo "⚠️  Note: VcXsrv (X11) may have different popover behavior than WSLg (Wayland)"
    echo "   - WSLg (Wayland): Native, modern, recommended"
    echo "   - VcXsrv (X11): Older protocol, may have rendering differences"
else
    echo "❌ VcXsrv on :99 is not available"
    echo ""
    echo "📝 To start VcXsrv on Windows:"
    echo "   1. Launch VcXsrv with these settings:"
    echo "      - Multiple windows mode"
    echo "      - Display number: 99"
    echo "      - Start no client"
    echo "      - Disable access control"
    echo ""
    echo "   2. Or use command line:"
    echo "      vcxsrv.exe :99 -multiwindow -clipboard -wgl -ac"
    echo ""
    echo "   3. Then run this test again"
fi
echo ""
echo "✅ Current setup (WSLg/Wayland) is optimal for GTK4"
echo "   Only test VcXsrv if experiencing issues with WSLg"
echo ""
