#!/usr/bin/env python3
"""Test that compound mapper uses place.name only (not place.label).

Labels are inconsistent display text and should not be used for compound mapping.
Only place.name (the object identifier) is reliable.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.thermodynamics.mappers import LabelBasedMapper


class MockPlace:
    """Mock place object for testing."""
    def __init__(self, id, name, label=""):
        self.id = id
        self.name = name
        self.label = label


def test_name_only():
    """Test that only name is used, label is ignored."""
    mapper = LabelBasedMapper()
    
    # Label says "glucose" but name says "ATP" - should use name
    place = MockPlace(id="P1", name="ATP", label="glucose")
    mappings = mapper.map_places([place])
    
    assert "P1" in mappings, "Should map place by name"
    assert mappings["P1"] == "C00002", f"Expected C00002 (ATP from name), got {mappings['P1']}"
    print("✅ PASS: Name is used, label is ignored")


def test_name_mapping():
    """Test that name-based mapping works."""
    mapper = LabelBasedMapper()
    
    places = [
        MockPlace(id="P1", name="ATP", label="whatever"),
        MockPlace(id="P2", name="ADP", label=""),
        MockPlace(id="P3", name="H2O", label="display text"),
    ]
    
    mappings = mapper.map_places(places)
    
    assert len(mappings) == 3, f"Expected 3 mappings, got {len(mappings)}"
    assert mappings["P1"] == "C00002", "ATP"
    assert mappings["P2"] == "C00008", "ADP"
    assert mappings["P3"] == "C00001", "H2O"
    
    print("✅ PASS: Name-based mapping works correctly")


def test_atp_hydrolysis_model():
    """Test the actual ATP_hydrolysis.shy scenario."""
    mapper = LabelBasedMapper()
    
    places = [
        MockPlace(id="P1", name="ATP", label=""),
        MockPlace(id="P3", name="H2O", label=""),
        MockPlace(id="P4", name="ADP", label=""),
        MockPlace(id="P5", name="Pi", label=""),
    ]
    
    mappings = mapper.map_places(places)
    
    expected = {
        "P1": "C00002",  # ATP
        "P3": "C00001",  # H2O
        "P4": "C00008",  # ADP
        "P5": "C00009",  # Pi
    }
    
    assert len(mappings) == 4, f"Expected 4 mappings, got {len(mappings)}"
    
    for place_id, expected_compound in expected.items():
        assert place_id in mappings, f"Missing mapping for {place_id}"
        assert mappings[place_id] == expected_compound, \
            f"{place_id}: expected {expected_compound}, got {mappings[place_id]}"
    
    print("✅ PASS: ATP hydrolysis model scenario works")
    print(f"   Mapped: {mappings}")
    print(f"   Confidences: {[mapper.get_confidence(pid) for pid in mappings.keys()]}")


def main():
    """Run all tests."""
    print("Testing compound mapper uses place.name only...\n")
    
    try:
        test_name_only()
        test_name_mapping()
        test_atp_hydrolysis_model()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nThe fix ensures:")
        print("- Mapper uses place.name only (object identifier)")
        print("- place.label is ignored (inconsistent display text)")
        print("- ATP_hydrolysis.shy model will auto-map correctly")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
