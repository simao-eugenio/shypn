#!/usr/bin/env python3
"""Test viability panel coloring of transitions, places, and arcs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.viability.viability_panel import ViabilityPanel
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc


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


def color_to_hex(rgb):
    """Convert RGB tuple to hex string."""
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb[0] * 255),
        int(rgb[1] * 255),
        int(rgb[2] * 255)
    )


def test_viability_coloring():
    """Test that transitions, places, and arcs are colored correctly."""
    print("=" * 60)
    print("VIABILITY PANEL - COLORING TEST")
    print("=" * 60)
    
    # Create panel and model
    print("\n1. Creating viability panel and test model...")
    panel = ViabilityPanel()
    model = create_test_model()
    panel.model = model
    print("   ✓ Panel and model created")
    
    # Get default colors
    from shypn.netobjs import Place, Transition, Arc
    default_place_border = Place.DEFAULT_BORDER_COLOR
    default_transition_border = Transition.DEFAULT_BORDER_COLOR
    default_transition_fill = Transition.DEFAULT_COLOR
    default_arc_color = Arc.DEFAULT_COLOR
    
    print("\n2. Verifying default colors...")
    print(f"   Default place border: {color_to_hex(default_place_border)}")
    print(f"   Default transition border: {color_to_hex(default_transition_border)}")
    print(f"   Default transition fill: {color_to_hex(default_transition_fill)}")
    print(f"   Default arc color: {color_to_hex(default_arc_color)}")
    
    # Get viability color
    viability_color = panel._get_viability_color()
    viability_hex = color_to_hex(viability_color)
    print(f"\n3. Viability color: {viability_hex} (expected: #9b59b6)")
    assert viability_hex == '#9b59b6', f"Expected #9b59b6, got {viability_hex}"
    print("   ✓ Viability color correct")
    
    # Check initial colors (should be defaults)
    print("\n4. Checking initial object colors (should be defaults)...")
    t5 = model.transitions[0]
    p3 = model.places[0]
    p4 = model.places[1]
    a1 = model.arcs[0]
    a2 = model.arcs[1]
    
    assert t5.border_color == default_transition_border, "T5 border should be default"
    assert t5.fill_color == default_transition_fill, "T5 fill should be default"
    assert p3.border_color == default_place_border, "P3 border should be default"
    assert p4.border_color == default_place_border, "P4 border should be default"
    assert a1.color == default_arc_color, "A1 color should be default"
    assert a2.color == default_arc_color, "A2 color should be default"
    print("   ✓ All objects have default colors")
    
    # Mock model_canvas for _get_current_model to work
    class MockModelCanvas:
        def get_current_document(self):
            return MockDrawingArea()
    
    class MockDrawingArea:
        def __init__(self):
            self.document_model = model
    
    panel.model_canvas = MockModelCanvas()
    
    # Add T5 to viability analysis
    print("\n5. Adding T5 to viability analysis...")
    from shypn.ui.panels.viability.investigation import Locality
    
    locality_t5 = Locality(
        transition_id='T5',
        input_places=['P3'],
        output_places=['P4'],
        input_arcs=['A1'],
        output_arcs=['A2']
    )
    
    class MockTransition:
        def __init__(self, tid):
            self.transition_id = tid
            self.label = ""
    
    panel.selected_localities['T5'] = {
        'row': None,
        'checkbox': None,
        'transition': MockTransition('T5'),
        'locality': locality_t5
    }
    
    # Manually color objects (simulating _add_transition_to_list)
    panel._color_transition(t5)
    panel._color_locality_place(p3)
    panel._color_locality_place(p4)
    panel._color_arc(a1)
    panel._color_arc(a2)
    
    print("   ✓ T5 locality colored")
    
    # Verify colors changed to viability purple
    print("\n6. Checking colors after adding to viability...")
    print(f"   T5 border: {color_to_hex(t5.border_color)}")
    print(f"   T5 fill: {color_to_hex(t5.fill_color)}")
    print(f"   P3 border: {color_to_hex(p3.border_color)}")
    print(f"   P4 border: {color_to_hex(p4.border_color)}")
    print(f"   A1 color: {color_to_hex(a1.color)}")
    print(f"   A2 color: {color_to_hex(a2.color)}")
    
    assert t5.border_color == viability_color, "T5 border should be viability purple"
    assert t5.fill_color == viability_color, "T5 fill should be viability purple"
    assert p3.border_color == viability_color, "P3 border should be viability purple"
    assert p4.border_color == viability_color, "P4 border should be viability purple"
    assert a1.color == viability_color, "A1 should be viability purple"
    assert a2.color == viability_color, "A2 should be viability purple"
    print("   ✓ All objects colored with viability purple")
    
    # Test clear all resets colors
    print("\n7. Testing Clear All resets colors...")
    panel._on_clear_all_clicked(None)
    
    print("   Checking colors after clear...")
    print(f"   T5 border: {color_to_hex(t5.border_color)}")
    print(f"   T5 fill: {color_to_hex(t5.fill_color)}")
    print(f"   P3 border: {color_to_hex(p3.border_color)}")
    print(f"   P4 border: {color_to_hex(p4.border_color)}")
    print(f"   A1 color: {color_to_hex(a1.color)}")
    print(f"   A2 color: {color_to_hex(a2.color)}")
    
    assert t5.border_color == default_transition_border, "T5 border should be reset to default"
    assert t5.fill_color == default_transition_fill, "T5 fill should be reset to default"
    assert p3.border_color == default_place_border, "P3 border should be reset to default"
    assert p4.border_color == default_place_border, "P4 border should be reset to default"
    assert a1.color == default_arc_color, "A1 should be reset to default"
    assert a2.color == default_arc_color, "A2 should be reset to default"
    print("   ✓ All colors reset to defaults")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nViability coloring verified:")
    print("  ✓ Viability purple color is #9b59b6")
    print("  ✓ Transitions get purple border + fill")
    print("  ✓ Places get purple border")
    print("  ✓ Arcs get purple color")
    print("  ✓ Clear All resets all colors to defaults")
    print("\nReady for real app testing!")


if __name__ == '__main__':
    test_viability_coloring()
