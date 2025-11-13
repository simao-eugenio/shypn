#!/usr/bin/env python3
"""Test viability panel subnet parameter population.

Tests that Places, Transitions, and Arcs tables are populated
when transitions are added to the viability analysis.
"""

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
    """Create simple test model with T5, T6 and their localities."""
    model = DocumentModel()
    
    # Create places
    p3 = Place(100, 100, 'P3', 'P3')
    p3.tokens = 5
    p4 = Place(200, 100, 'P4', 'P4')
    p4.tokens = 2
    p5 = Place(300, 100, 'P5', 'P5')
    p5.tokens = 0
    
    # Create transitions
    t5 = Transition(150, 150, 'T5', 'T5')
    t5.rate = 1.0
    t6 = Transition(250, 150, 'T6', 'T6')
    t6.rate = 0.8
    
    # Create arcs
    a1 = Arc(p3, t5, 'A1', 'A1', 1)
    a2 = Arc(t5, p4, 'A2', 'A2', 1)
    a3 = Arc(p4, t6, 'A3', 'A3', 1)
    a4 = Arc(t6, p5, 'A4', 'A4', 1)
    
    # Add to model
    model.places = [p3, p4, p5]
    model.transitions = [t5, t6]
    model.arcs = [a1, a2, a3, a4]
    
    return model


def test_subnet_parameters_population():
    """Test that subnet parameters tables populate correctly."""
    print("=" * 60)
    print("VIABILITY PANEL - SUBNET PARAMETERS POPULATION TEST")
    print("=" * 60)
    
    # Create panel
    print("\n1. Creating viability panel...")
    panel = ViabilityPanel()
    print("   ✓ Panel created")
    
    # Create test model
    print("\n2. Creating test model (P3, P4, P5, T5, T6)...")
    model = create_test_model()
    panel.model = model
    print(f"   ✓ Model created with {len(model.places)} places, {len(model.transitions)} transitions")
    
    # Check initial state
    print("\n3. Checking initial table state...")
    assert len(panel.places_store) == 0, "Places table should be empty initially"
    assert len(panel.transitions_store) == 0, "Transitions table should be empty initially"
    assert len(panel.arcs_store) == 0, "Arcs table should be empty initially"
    print("   ✓ All tables empty initially")
    
    # Manually populate selected_localities (simulating right-click add)
    print("\n4. Adding T5 to analysis (simulating right-click)...")
    from shypn.ui.panels.viability.investigation import Locality
    
    locality_t5 = Locality(
        transition_id='T5',
        input_places=['P3'],
        output_places=['P4'],
        input_arcs=['A1'],
        output_arcs=['A2']
    )
    
    # Create mock transition knowledge
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
    
    # Trigger refresh
    panel._refresh_subnet_parameters()
    print("   ✓ T5 added, refresh triggered")
    
    # Check tables populated
    print("\n5. Checking Places table...")
    places_count = len(panel.places_store)
    print(f"   Places count: {places_count}")
    for row in panel.places_store:
        place_id, name, marking, ptype, label = row
        print(f"   - {place_id}: {name}, marking={marking}, type={ptype}")
    assert places_count == 2, f"Expected 2 places (P3, P4), got {places_count}"
    print("   ✓ Places table populated correctly")
    
    print("\n6. Checking Transitions table...")
    trans_count = len(panel.transitions_store)
    print(f"   Transitions count: {trans_count}")
    for row in panel.transitions_store:
        trans_id, name, rate, formula, ttype, label = row
        print(f"   - {trans_id}: {name}, rate={rate}, type={ttype}")
    assert trans_count == 1, f"Expected 1 transition (T5), got {trans_count}"
    print("   ✓ Transitions table populated correctly")
    
    print("\n7. Checking Arcs table...")
    arcs_count = len(panel.arcs_store)
    print(f"   Arcs count: {arcs_count}")
    for row in panel.arcs_store:
        arc_id, from_id, to_id, weight, atype = row
        print(f"   - {arc_id}: {from_id}→{to_id}, weight={weight}, type={atype}")
    assert arcs_count == 2, f"Expected 2 arcs (A1, A2), got {arcs_count}"
    print("   ✓ Arcs table populated correctly")
    
    # Add T6
    print("\n8. Adding T6 to analysis...")
    locality_t6 = Locality(
        transition_id='T6',
        input_places=['P4'],
        output_places=['P5'],
        input_arcs=['A3'],
        output_arcs=['A4']
    )
    
    panel.selected_localities['T6'] = {
        'row': None,
        'checkbox': None,
        'transition': MockTransition('T6'),
        'locality': locality_t6
    }
    
    panel._refresh_subnet_parameters()
    print("   ✓ T6 added, refresh triggered")
    
    # Check expanded tables
    print("\n9. Checking expanded tables (T5 + T6)...")
    places_count = len(panel.places_store)
    trans_count = len(panel.transitions_store)
    arcs_count = len(panel.arcs_store)
    
    print(f"   Places: {places_count} (expected 3: P3, P4, P5)")
    print(f"   Transitions: {trans_count} (expected 2: T5, T6)")
    print(f"   Arcs: {arcs_count} (expected 4: A1-A4)")
    
    assert places_count == 3, f"Expected 3 places, got {places_count}"
    assert trans_count == 2, f"Expected 2 transitions, got {trans_count}"
    assert arcs_count == 4, f"Expected 4 arcs, got {arcs_count}"
    print("   ✓ All tables expanded correctly")
    
    # Test clear all
    print("\n10. Testing Clear All...")
    panel._on_clear_all_clicked(None)
    
    assert len(panel.places_store) == 0, "Places table should be empty after clear"
    assert len(panel.transitions_store) == 0, "Transitions table should be empty after clear"
    assert len(panel.arcs_store) == 0, "Arcs table should be empty after clear"
    assert len(panel.selected_localities) == 0, "Selected localities should be empty"
    print("   ✓ Clear All works correctly")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nSubnet Parameters tables populate correctly:")
    print("  ✓ Places table shows locality input/output places")
    print("  ✓ Transitions table shows selected transitions")
    print("  ✓ Arcs table shows locality arcs")
    print("  ✓ Tables update when transitions added")
    print("  ✓ Clear All resets everything")
    print("\nReady for simulation testing!")


if __name__ == '__main__':
    test_subnet_parameters_population()
