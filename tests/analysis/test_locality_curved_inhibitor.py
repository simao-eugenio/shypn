#!/usr/bin/env python3
"""Test that curved inhibitor arcs are included in localities."""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.diagnostic.locality_detector import LocalityDetector


class SimpleModel:
    """Simple model container for testing."""
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []


def test_locality_with_curved_inhibitor():
    """Test that curved inhibitor arcs are included in locality detection."""
    print("=" * 70)
    print("TESTING: Curved Inhibitor Arcs in Locality Detection")
    print("=" * 70)
    
    # Create a simple model
    model = SimpleModel()
    
    # Create places
    p1 = Place(100, 100, "1", "P1")
    p1.tokens = 5
    p2 = Place(300, 100, "2", "P2")
    p2.tokens = 10
    p3 = Place(200, 300, "3", "P3")
    p3.tokens = 15
    
    model.places = [p1, p2, p3]
    
    # Create transition
    t1 = Transition(200, 150, "1", "T1")
    model.transitions = [t1]
    
    # Create arcs of different types
    arc1 = Arc(p1, t1, 1, "A1", weight=1.0)  # Normal arc: P1 → T1
    arc2 = CurvedArc(p2, t1, 2, "A2", weight=2.0)  # Curved arc: P2 → T1
    arc3 = InhibitorArc(p3, t1, 3, "I1", weight=5.0)  # Inhibitor arc: P3 ⊣ T1
    arc4 = CurvedInhibitorArc(p3, t1, 4, "CI1", weight=10.0)  # Curved inhibitor: P3 ⊣ T1
    
    model.arcs = [arc1, arc2, arc3, arc4]
    
    print("\nModel Created:")
    print(f"  Places: {len(model.places)}")
    print(f"  Transitions: {len(model.transitions)}")
    print(f"  Arcs: {len(model.arcs)}")
    print("\nArc Types:")
    for arc in model.arcs:
        print(f"  {arc.name}: {arc.__class__.__name__} - {arc.source.name} → {arc.target.name}")
    
    # Create locality detector
    detector = LocalityDetector(model)
    print("\nLocality Detector Created")
    
    # Get locality for T1
    locality = detector.get_locality_for_transition(t1)
    
    print(f"\nLocality for T1:")
    print(f"  Valid: {locality.is_valid}")
    print(f"  Input places: {[p.name for p in locality.input_places]}")
    print(f"  Output places: {[p.name for p in locality.output_places]}")
    print(f"  Input arcs: {len(locality.input_arcs)}")
    print(f"  Output arcs: {len(locality.output_arcs)}")
    
    print("\nDetailed Input Arcs:")
    for arc in locality.input_arcs:
        print(f"  {arc.name}: {arc.__class__.__name__} - {arc.source.name} → {arc.target.name}")
    
    # Check if all arc types are present
    print("\nArc Type Coverage:")
    arc_types = {arc.__class__.__name__ for arc in locality.input_arcs}
    
    expected_types = ['Arc', 'CurvedArc', 'InhibitorArc', 'CurvedInhibitorArc']
    for expected in expected_types:
        if expected in arc_types:
            print(f"  ✓ {expected} - FOUND")
        else:
            print(f"  ✗ {expected} - MISSING")
    
    # Verify curved inhibitor arc is included
    curved_inhibitor_found = any(
        isinstance(arc, CurvedInhibitorArc) for arc in locality.input_arcs
    )
    
    print("\n" + "=" * 70)
    if curved_inhibitor_found:
        print("✓ SUCCESS: CurvedInhibitorArc IS included in locality!")
        print("=" * 70)
        return 0
    else:
        print("✗ FAILURE: CurvedInhibitorArc NOT included in locality!")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(test_locality_with_curved_inhibitor())
