#!/usr/bin/env python3
"""Quick visual test for Dynamic Analyses Panel with title."""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.ui.panels.dynamic_analyses import DynamicAnalysesPanel

window = Gtk.Window(title="Dynamic Analyses Panel - Visual Test")
window.set_default_size(400, 600)
window.connect("destroy", Gtk.main_quit)

panel = DynamicAnalysesPanel()
window.add(panel)
window.show_all()

print("✓ Panel displayed with 'DYNAMIC ANALYSES' title")
print("  - 3 categories: Transitions, Places, Diagnostics")
print("  - Close window to exit")

Gtk.main()
