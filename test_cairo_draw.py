#!/usr/bin/env python3
"""Test if Cairo drawing context works with GTK"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('cairo', '1.0')
from gi.repository import Gtk, GLib, cairo as _gi_cairo  # Import gi.repository.cairo to register converters
import cairo

def on_draw(widget, cr):
    """Test drawing callback"""
    print(f"Draw callback called with context type: {type(cr)}")
    try:
        # Try to use the cairo context
        cr.set_source_rgb(1, 0, 0)
        cr.paint()
        print("✓ Drawing succeeded!")
        return True
    except Exception as e:
        print(f"✗ Drawing failed: {e}")
        return False

# Create a simple window
window = Gtk.Window(title="Cairo Test")
window.set_default_size(200, 200)
window.connect("destroy", Gtk.main_quit)

# Create drawing area
drawing_area = Gtk.DrawingArea()
drawing_area.connect("draw", on_draw)
window.add(drawing_area)

window.show_all()

# Force a redraw and then quit
GLib.timeout_add(100, Gtk.main_quit)
Gtk.main()

print("\nTest completed")
