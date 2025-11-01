#!/usr/bin/env python3
"""
Visual test of Biological Category in Topology Panel.

Creates a window showing the complete topology panel with all 4 categories,
including the new BIOLOGICAL ANALYSIS category.

Author: GitHub Copilot
Date: October 31, 2025
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.ui.panels.topology.topology_panel import TopologyPanel


# Simple mock model
class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}
        self.metadata = {'source': 'sbml', 'name': 'Test Biological Model'}
    
    def add_place(self, place):
        self.places[place.id] = place
    
    def add_transition(self, transition):
        self.transitions[transition.id] = transition
    
    def add_arc(self, arc):
        self.arcs[arc.id] = arc


class MockDocument:
    """Mock document (drawing area) for testing."""
    def __init__(self, model):
        self.model = model


class MockModelCanvas:
    """Mock model canvas for testing."""
    def __init__(self, document):
        self.current_document = document
    
    def get_current_document(self):
        return self.current_document


def create_biological_model():
    """Create a biological model with regulatory coupling."""
    model = MockModel()
    
    # Convergent pathway: Two substrates → One product
    # Plus shared enzyme
    substrate1 = Place(id=1, name="Glucose", x=100, y=100, tokens=10)
    substrate2 = Place(id=2, name="Fructose", x=100, y=200, tokens=10)
    enzyme = Place(id=3, name="Hexokinase", x=100, y=300, tokens=5)
    product = Place(id=4, name="G6P", x=300, y=150, tokens=0)
    
    t1 = Transition(id=1, name="Phosphorylation1", x=200, y=100)
    t2 = Transition(id=2, name="Phosphorylation2", x=200, y=200)
    
    model.add_place(substrate1)
    model.add_place(substrate2)
    model.add_place(enzyme)
    model.add_place(product)
    model.add_transition(t1)
    model.add_transition(t2)
    
    # Normal arcs
    model.add_arc(Arc(substrate1, t1, 1, "A1", weight=1))
    model.add_arc(Arc(t1, product, 2, "A2", weight=1))
    model.add_arc(Arc(substrate2, t2, 3, "A3", weight=1))
    model.add_arc(Arc(t2, product, 4, "A4", weight=1))
    
    # Test arcs (catalyst)
    model.add_arc(TestArc(enzyme, t1, 5, "TA1", weight=1))
    model.add_arc(TestArc(enzyme, t2, 6, "TA2", weight=1))
    
    return model


class TopologyPanelTestWindow(Gtk.Window):
    """Test window showing topology panel."""
    
    def __init__(self):
        super().__init__(title="Topology Panel - Biological Category Test")
        self.set_default_size(400, 800)
        self.connect("destroy", Gtk.main_quit)
        
        # Create model
        model = create_biological_model()
        document = MockDocument(model)
        model_canvas = MockModelCanvas(document)
        
        # Create topology panel
        self.topology_panel = TopologyPanel(
            model=model,
            model_canvas=model_canvas
        )
        
        # Add info label at top
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_margin_top(10)
        info_box.set_margin_start(10)
        info_box.set_margin_end(10)
        info_box.set_margin_bottom(10)
        
        title = Gtk.Label()
        title.set_markup("<b>Topology Panel with Biological Analysis</b>")
        title.set_halign(Gtk.Align.START)
        info_box.pack_start(title, False, False, 0)
        
        desc = Gtk.Label()
        desc.set_markup(
            "✅ <b>BIOLOGICAL ANALYSIS</b> category successfully added!\n\n"
            "The panel now contains 4 categories:\n"
            "  1. STRUCTURAL ANALYSIS\n"
            "  2. GRAPH & NETWORK ANALYSIS\n"
            "  3. BEHAVIORAL ANALYSIS\n"
            "  4. BIOLOGICAL ANALYSIS ← NEW!\n\n"
            "<i>Scroll down to see the BIOLOGICAL ANALYSIS category.\n"
            "Expand it to see the Dependency & Coupling analyzer.</i>"
        )
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        info_box.pack_start(desc, False, False, 0)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        info_box.pack_start(separator, False, False, 5)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.pack_start(info_box, False, False, 0)
        main_box.pack_start(self.topology_panel, True, True, 0)
        
        self.add(main_box)
        self.show_all()
        
        print("\n" + "="*70)
        print("VISUAL TEST: Topology Panel with Biological Category")
        print("="*70)
        print("\n✅ Window created successfully!")
        print("\nThe Topology Panel contains 4 categories:")
        for i, category in enumerate(self.topology_panel.categories, 1):
            print(f"  {i}. {category.title}")
        print("\n📋 Instructions:")
        print("  1. Scroll down to see all 4 categories")
        print("  2. Click 'BIOLOGICAL ANALYSIS' to expand")
        print("  3. Click 'Dependency & Coupling' to run analyzer")
        print("  4. View classification results\n")


def main():
    """Main entry point."""
    window = TopologyPanelTestWindow()
    Gtk.main()


if __name__ == "__main__":
    main()
