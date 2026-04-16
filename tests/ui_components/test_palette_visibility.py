#!/usr/bin/env python3
"""Quick test to verify palette visibility."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# Simple test window
win = Gtk.Window(title="Palette Visibility Test")
win.set_default_size(800, 600)
win.connect("destroy", Gtk.main_quit)

overlay = Gtk.Overlay()
win.add(overlay)

# Add a colored background so we can see the canvas
canvas = Gtk.DrawingArea()
canvas.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.2, 0.2, 0.2, 1.0))
overlay.add(canvas)

# Import and create palettes
import sys
sys.path.insert(0, '/home/simao/projetos/shypn')
from src.shypn.edit.palette_manager import PaletteManager
from src.shypn.edit.tools_palette_new import ToolsPalette
from src.shypn.edit.operations_palette_new import OperationsPalette

# Create palette manager
pm = PaletteManager(overlay)

# Create tools palette (bottom-left)
tools = ToolsPalette()
tools_revealer = tools.get_widget()
tools_revealer.set_margin_start(10)
tools_revealer.set_margin_bottom(10)
pm.register_palette(tools, (Gtk.Align.START, Gtk.Align.END))

# Create operations palette (bottom-right)
ops = OperationsPalette()
ops_revealer = ops.get_widget()
ops_revealer.set_margin_end(10)
ops_revealer.set_margin_bottom(10)
pm.register_palette(ops, (Gtk.Align.END, Gtk.Align.END))

# Show everything
win.show_all()

# Show palettes after window is realized
def show_palettes():
    pm.show_all()
    print("Palettes shown")
    return False

GLib.timeout_add(500, show_palettes)

print("Starting test window...")
Gtk.main()
