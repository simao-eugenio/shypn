#!/usr/bin/env python3
"""
Test Biological Category UI Integration.

Verifies the Biological Analysis category appears in Topology Panel.

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


# Simple mock model with dictionary structure
class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}
    
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
    """Create a simple biological model with test arcs."""
    model = MockModel()
    
    # Two reactions sharing enzyme
    substrate1 = Place(id=1, name="Substrate1", x=100, y=100)
    substrate2 = Place(id=2, name="Substrate2", x=100, y=200)
    enzyme = Place(id=3, name="Enzyme", x=100, y=300)
    product1 = Place(id=4, name="Product1", x=300, y=100)
    product2 = Place(id=5, name="Product2", x=300, y=200)
    
    t1 = Transition(id=1, name="Reaction1", x=200, y=100)
    t2 = Transition(id=2, name="Reaction2", x=200, y=200)
    
    model.add_place(substrate1)
    model.add_place(substrate2)
    model.add_place(enzyme)
    model.add_place(product1)
    model.add_place(product2)
    model.add_transition(t1)
    model.add_transition(t2)
    
    # Normal arcs
    model.add_arc(Arc(substrate1, t1, 1, "A1", weight=1))
    model.add_arc(Arc(t1, product1, 2, "A2", weight=1))
    model.add_arc(Arc(substrate2, t2, 3, "A3", weight=1))
    model.add_arc(Arc(t2, product2, 4, "A4", weight=1))
    
    # Test arcs (catalysts)
    model.add_arc(TestArc(enzyme, t1, 5, "TA1", weight=1))
    model.add_arc(TestArc(enzyme, t2, 6, "TA2", weight=1))
    
    return model


def test_biological_category_exists():
    """Test that biological category is added to topology panel."""
    print("\n" + "="*70)
    print("TEST: Biological Category UI Integration")
    print("="*70)
    
    # Create model
    model = create_biological_model()
    document = MockDocument(model)
    model_canvas = MockModelCanvas(document)
    
    # Create topology panel
    topology_panel = TopologyPanel(
        model=model,
        model_canvas=model_canvas
    )
    
    # Verify 4 categories exist
    assert len(topology_panel.categories) == 4, \
        f"Expected 4 categories, got {len(topology_panel.categories)}"
    
    # Verify biological category is present
    assert hasattr(topology_panel, 'biological_category'), \
        "TopologyPanel should have biological_category attribute"
    
    # Verify biological category is in list
    assert topology_panel.biological_category in topology_panel.categories, \
        "Biological category should be in categories list"
    
    # Verify category has correct title
    bio_category = topology_panel.biological_category
    assert bio_category.title == "BIOLOGICAL ANALYSIS", \
        f"Expected 'BIOLOGICAL ANALYSIS', got '{bio_category.title}'"
    
    # Verify category has dependency_coupling analyzer
    analyzers = bio_category._get_analyzers()
    assert 'dependency_coupling' in analyzers, \
        "Biological category should have dependency_coupling analyzer"
    
    print("\n✓ Topology Panel has 4 categories")
    print("✓ Biological Analysis category exists")
    print("✓ Dependency & Coupling analyzer registered")
    
    # Verify category order
    category_titles = [cat.title for cat in topology_panel.categories]
    print(f"\nCategory order:")
    for i, title in enumerate(category_titles, 1):
        print(f"  {i}. {title}")
    
    expected_order = [
        "STRUCTURAL ANALYSIS",
        "GRAPH & NETWORK ANALYSIS",
        "BEHAVIORAL ANALYSIS",
        "BIOLOGICAL ANALYSIS"
    ]
    
    assert category_titles == expected_order, \
        f"Category order mismatch: {category_titles} vs {expected_order}"
    
    print("\n✓ TEST PASSED: Biological category integrated correctly!")
    print("\nThe BIOLOGICAL expander will appear in the Topology Panel with:")
    print("  - Dependency & Coupling analyzer")
    print("  - (Regulatory Structure analyzer - TODO)")
    
    return True


def run_all_tests():
    """Run all UI integration tests."""
    print("\n" + "="*70)
    print("BIOLOGICAL CATEGORY UI INTEGRATION TEST SUITE")
    print("="*70)
    
    try:
        test_biological_category_exists()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED! ✅")
        print("="*70)
        print("\nBiological Analysis category is ready for use!")
        print("\nTo use in SHYPN:")
        print("  1. Open a biological model (or create one with test arcs)")
        print("  2. Open Topology Panel")
        print("  3. Expand 'BIOLOGICAL ANALYSIS' category")
        print("  4. Click 'Dependency & Coupling' to run analysis")
        print("\nThe analyzer will classify transition dependencies and show")
        print("the ratio of valid couplings vs true conflicts.")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
