#!/usr/bin/env python3
"""Quick GUI demo showing subnet parameters tables populating."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.panels.viability.viability_panel import ViabilityPanel
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.ui.panels.viability.investigation import Locality


def create_test_model():
    """Create simple test model: P3→T5→P4→T6→P5"""
    model = DocumentModel()
    
    # Places
    p3 = Place(100, 100, 'P3', 'P3')
    p3.tokens = 5
    p4 = Place(200, 100, 'P4', 'P4')
    p4.tokens = 2
    p5 = Place(300, 100, 'P5', 'P5')
    p5.tokens = 0
    
    # Transitions
    t5 = Transition(150, 150, 'T5', 'T5')
    t5.rate = 1.0
    t6 = Transition(250, 150, 'T6', 'T6')
    t6.rate = 0.8
    
    # Arcs
    a1 = Arc(p3, t5, 'A1', 'A1', 1)
    a2 = Arc(t5, p4, 'A2', 'A2', 1)
    a3 = Arc(p4, t6, 'A3', 'A3', 1)
    a4 = Arc(t6, p5, 'A4', 'A4', 1)
    
    model.places = [p3, p4, p5]
    model.transitions = [t5, t6]
    model.arcs = [a1, a2, a3, a4]
    
    return model


class DemoWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Viability Panel - Subnet Parameters Demo")
        self.set_default_size(900, 700)
        self.connect('destroy', Gtk.main_quit)
        
        # Create viability panel
        self.panel = ViabilityPanel()
        
        # Create and set model
        self.model = create_test_model()
        self.panel.model = self.model
        
        # Wrap in scrolled window
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.panel)
        self.add(scroll)
        
        # Auto-add transitions after window shows
        GLib.timeout_add(500, self.auto_populate)
    
    def auto_populate(self):
        """Auto-populate the viability panel to demonstrate tables."""
        print("\n" + "="*60)
        print("AUTO-POPULATING VIABILITY PANEL")
        print("="*60)
        
        # Create localities for T5 and T6
        locality_t5 = Locality(
            transition_id='T5',
            input_places=['P3'],
            output_places=['P4'],
            input_arcs=['A1'],
            output_arcs=['A2']
        )
        
        locality_t6 = Locality(
            transition_id='T6',
            input_places=['P4'],
            output_places=['P5'],
            input_arcs=['A3'],
            output_arcs=['A4']
        )
        
        # Mock transition knowledge
        class MockTransition:
            def __init__(self, tid):
                self.transition_id = tid
                self.label = ""
        
        # Add T5
        print("\n1. Adding T5 to analysis...")
        self.panel.selected_localities['T5'] = {
            'row': None,
            'checkbox': None,
            'transition': MockTransition('T5'),
            'locality': locality_t5
        }
        self.panel._refresh_subnet_parameters()
        print(f"   ✓ Places: {len(self.panel.places_store)}")
        print(f"   ✓ Transitions: {len(self.panel.transitions_store)}")
        print(f"   ✓ Arcs: {len(self.panel.arcs_store)}")
        
        # Add T6 after 1 second
        GLib.timeout_add(1000, self.add_t6, locality_t6)
        
        return False  # Don't repeat
    
    def add_t6(self, locality_t6):
        """Add T6 to show table expansion."""
        print("\n2. Adding T6 to analysis...")
        
        class MockTransition:
            def __init__(self, tid):
                self.transition_id = tid
                self.label = ""
        
        self.panel.selected_localities['T6'] = {
            'row': None,
            'checkbox': None,
            'transition': MockTransition('T6'),
            'locality': locality_t6
        }
        self.panel._refresh_subnet_parameters()
        print(f"   ✓ Places: {len(self.panel.places_store)} (P3, P4, P5)")
        print(f"   ✓ Transitions: {len(self.panel.transitions_store)} (T5, T6)")
        print(f"   ✓ Arcs: {len(self.panel.arcs_store)} (A1-A4)")
        
        print("\n" + "="*60)
        print("TABLES POPULATED!")
        print("="*60)
        print("\nNow you can:")
        print("  • Edit markings in Places tab")
        print("  • Edit rates in Transitions tab")
        print("  • Edit weights in Arcs tab")
        print("  • Click '⏭ Step' to execute single firings")
        print("  • Click '▶ Run' for full simulation")
        print("="*60 + "\n")
        
        return False


if __name__ == '__main__':
    win = DemoWindow()
    win.show_all()
    Gtk.main()
