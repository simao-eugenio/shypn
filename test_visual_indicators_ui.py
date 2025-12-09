#!/usr/bin/env python3
"""Interactive test to verify visual indicators in the UI."""

import sys
sys.path.insert(0, 'src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.panels.viability.viability_panel import ViabilityPanel

class TestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Visual Indicators Test")
        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)
        
        # Create main box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        self.add(vbox)
        
        # Add viability panel
        self.viability_panel = ViabilityPanel()
        vbox.pack_start(self.viability_panel, True, True, 0)
        
        # Add test buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Button to add test data
        add_data_btn = Gtk.Button(label="1. Add Test Data")
        add_data_btn.connect("clicked", self.on_add_test_data)
        button_box.pack_start(add_data_btn, False, False, 0)
        
        # Button to highlight place
        highlight_place_btn = Gtk.Button(label="2. Highlight P2 (Place)")
        highlight_place_btn.connect("clicked", lambda w: self.viability_panel.update_sweep_indicators('place', 'P2'))
        button_box.pack_start(highlight_place_btn, False, False, 0)
        
        # Button to highlight transition
        highlight_trans_btn = Gtk.Button(label="3. Highlight T1 (Transition)")
        highlight_trans_btn.connect("clicked", lambda w: self.viability_panel.update_sweep_indicators('transition', 'T1'))
        button_box.pack_start(highlight_trans_btn, False, False, 0)
        
        # Button to clear indicators
        clear_btn = Gtk.Button(label="4. Clear All")
        clear_btn.connect("clicked", lambda w: self.viability_panel._clear_sweep_indicators())
        button_box.pack_start(clear_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Add status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<b>Instructions:</b> Click buttons in order. Check the parameter tables for light blue highlighting.")
        vbox.pack_start(self.status_label, False, False, 0)
        
    def on_add_test_data(self, button):
        """Add test data to stores."""
        # Clear existing
        self.viability_panel.places_store.clear()
        self.viability_panel.transitions_store.clear()
        self.viability_panel.arcs_store.clear()
        
        # Add test places
        self.viability_panel.places_store.append(['P1', 'Substrate', 100, 'Normal', 'Test substrate', '#FFFFFF'])
        self.viability_panel.places_store.append(['P2', 'Product', 0, 'Normal', 'Test product', '#FFFFFF'])
        self.viability_panel.places_store.append(['P3', 'Enzyme', 10, 'Normal', 'Catalyst', '#FFFFFF'])
        
        # Add test transitions
        self.viability_panel.transitions_store.append(['T1', 'Reaction', 1.5, '0.5 * Substrate', 'continuous', 'Test reaction', '#FFFFFF'])
        self.viability_panel.transitions_store.append(['T2', 'Transport', 0.8, '', 'continuous', 'Transport', '#FFFFFF'])
        
        # Add test arcs
        self.viability_panel.arcs_store.append(['A1', 'P1', 'T1', 1, 'Place→Transition', '#FFFFFF'])
        self.viability_panel.arcs_store.append(['A2', 'T1', 'P2', 1, 'Transition→Place', '#FFFFFF'])
        
        self.status_label.set_markup("<span foreground='green'>✓ Test data added! Now try highlighting buttons.</span>")

def main():
    win = TestWindow()
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
