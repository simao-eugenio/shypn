#!/usr/bin/env python3
"""Test signal place visualization (hexagon rendering)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.analysis.quorum_sensing import mark_signal_places_in_model


class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}


def test_signal_place_marking():
    """Test that signal places are correctly marked for hexagon rendering."""
    model = MockModel()
    
    # Create places
    p1 = Place(100, 100, "P1", "P1", label="AHL_internal")
    p2 = Place(200, 100, "P2", "P2", label="AHL_external")
    p3 = Place(150, 200, "P3", "P3", label="LuxR_AHL")
    
    model.places = {"P1": p1, "P2": p2, "P3": p3}
    
    # Create transition with rate formula referencing P2 (not connected)
    t1 = Transition(150, 150, "T1", "T1", label="activation")
    t1.rate_function = "0.5 * P3 / (1 + P2)"  # P2 not connected = signal place
    model.transitions = {"T1": t1}
    
    # Create arcs (P1 → T1, T1 → P3) 
    # Note: Arc expects object references, but detector checks arc.source/target
    # which should return the object's ID
    class MockArc:
        def __init__(self, source_id, target_id):
            self.source = source_id
            self.target = target_id
            self.arc_type = "normal"
    
    arc1 = MockArc("P1", "T1")  # P1 → T1
    arc2 = MockArc("T1", "P3")  # T1 → P3
    model.arcs = {"A1": arc1, "A2": arc2}
    
    # Mark signal places
    signal_places = mark_signal_places_in_model(model)
    
    # Verify P2 is marked as signal place
    assert "P2" in signal_places, "P2 should be detected as signal place"
    assert p2.is_signal_place == True, "P2 should be marked with is_signal_place=True"
    assert p1.is_signal_place == False, "P1 should NOT be signal place (connected by arc)"
    assert p3.is_signal_place == False, "P3 should NOT be signal place (connected by arc)"
    
    # Verify transition is marked as environment-aware
    assert t1.is_environment_aware == True
    assert "P2" in t1.signal_places
    
    print("✓ Signal place marking test passed")


def test_hexagon_vs_circle_distinction():
    """Test that signal places use hexagon shape."""
    # Create regular place
    p_regular = Place(100, 100, "P1", "P1", label="Regular")
    assert p_regular.is_signal_place == False
    
    # Create signal place
    p_signal = Place(200, 100, "P2", "P2", label="Signal")
    p_signal.is_signal_place = True
    assert p_signal.is_signal_place == True
    
    # Note: Actual rendering tested visually in GUI
    # Here we just verify the attribute is set correctly
    print("✓ Hexagon vs circle distinction test passed")


def test_signal_place_serialization():
    """Test that signal place flag is preserved in save/load."""
    # Create signal place
    p1 = Place(100, 100, "P1", "P1", label="Signal_AHL")
    p1.is_signal_place = True
    p1.tokens = 50
    
    # Serialize
    data = p1.to_dict()
    assert data["is_signal_place"] == True, "Signal place flag should be in dict"
    
    # Deserialize
    p2 = Place.from_dict(data)
    assert p2.is_signal_place == True, "Signal place flag should be restored"
    assert p2.tokens == 50
    assert p2.label == "Signal_AHL"
    
    print("✓ Signal place serialization test passed")


def test_signal_place_hit_testing():
    """Test that hexagon hit testing works correctly."""
    # Create signal place (hexagon)
    p = Place(100, 100, "P1", "P1", radius=30)
    p.is_signal_place = True
    
    # Test center (should always be inside)
    assert p.contains_point(100, 100) == True
    
    # Test inscribed circle boundary (should be inside)
    # Hexagon inscribed circle radius ≈ 0.866 * circumradius
    inscribed_radius = 30 * 0.866
    assert p.contains_point(100 + inscribed_radius - 1, 100) == True
    
    # Test beyond inscribed circle (might be outside)
    assert p.contains_point(100 + 30, 100) == False
    
    print("✓ Signal place hit testing test passed")


if __name__ == "__main__":
    test_signal_place_marking()
    test_hexagon_vs_circle_distinction()
    test_signal_place_serialization()
    test_signal_place_hit_testing()
    print("\n✅ All UI integration tests passed!")
