#!/usr/bin/env python3
"""Test script to verify Petri net connection rules and validation."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.api import Place, Transition, Arc, InhibitorArc


def test_valid_place_to_transition():
    """Test valid connection: Place → Transition."""
    place = Place(x=100, y=100, id=1, name="P1")
    trans = Transition(x=200, y=200, id=1, name="T1")
    
    try:
        arc = Arc(source=place, target=trans, id=1, name="A1", weight=1)
        assert arc.source == place
        assert arc.target == trans
        print("✓ Valid connection: Place → Transition")
        return True
    except ValueError as e:
        print(f"✗ Unexpected error for Place→Transition: {e}")
        return False


def test_valid_transition_to_place():
    """Test valid connection: Transition → Place."""
    trans = Transition(x=100, y=100, id=1, name="T1")
    place = Place(x=200, y=200, id=1, name="P1")
    
    try:
        arc = Arc(source=trans, target=place, id=1, name="A1", weight=1)
        assert arc.source == trans
        assert arc.target == place
        print("✓ Valid connection: Transition → Place")
        return True
    except ValueError as e:
        print(f"✗ Unexpected error for Transition→Place: {e}")
        return False


def test_invalid_place_to_place():
    """Test invalid connection: Place → Place (should raise ValueError)."""
    place1 = Place(x=100, y=100, id=1, name="P1")
    place2 = Place(x=200, y=200, id=2, name="P2")
    
    try:
        arc = Arc(source=place1, target=place2, id=1, name="A1", weight=1)
        print(f"✗ FAILED: Place→Place should raise ValueError but succeeded!")
        return False
    except ValueError as e:
        if "bipartite" in str(e).lower():
            print(f"✓ Invalid connection blocked: Place → Place")
            print(f"  Error message: {e}")
            return True
        else:
            print(f"✗ Wrong error message for Place→Place: {e}")
            return False


def test_invalid_transition_to_transition():
    """Test invalid connection: Transition → Transition (should raise ValueError)."""
    trans1 = Transition(x=100, y=100, id=1, name="T1")
    trans2 = Transition(x=200, y=200, id=2, name="T2")
    
    try:
        arc = Arc(source=trans1, target=trans2, id=1, name="A1", weight=1)
        print(f"✗ FAILED: Transition→Transition should raise ValueError but succeeded!")
        return False
    except ValueError as e:
        if "bipartite" in str(e).lower():
            print(f"✓ Invalid connection blocked: Transition → Transition")
            print(f"  Error message: {e}")
            return True
        else:
            print(f"✗ Wrong error message for Transition→Transition: {e}")
            return False


def test_inhibitor_arc_validation():
    """Test that InhibitorArc also validates connections (inherits from Arc)."""
    place = Place(x=100, y=100, id=1, name="P1")
    trans = Transition(x=200, y=200, id=1, name="T1")
    place2 = Place(x=300, y=300, id=2, name="P2")
    
    # Valid: Place → Transition
    try:
        inhibitor = InhibitorArc(source=place, target=trans, id=1, name="I1", weight=1)
        print("✓ InhibitorArc valid: Place → Transition")
    except ValueError as e:
        print(f"✗ InhibitorArc failed on valid connection: {e}")
        return False
    
    # Invalid: Place → Place
    try:
        inhibitor2 = InhibitorArc(source=place, target=place2, id=2, name="I2", weight=1)
        print(f"✗ FAILED: InhibitorArc Place→Place should raise ValueError!")
        return False
    except ValueError:
        print("✓ InhibitorArc blocks invalid Place → Place")
        return True


def test_default_colors():
    """Verify all objects use black as default color."""
    place = Place(x=100, y=100, id=1, name="P1")
    trans = Transition(x=200, y=200, id=1, name="T1")
    arc = Arc(source=place, target=trans, id=1, name="A1")
    inhibitor = InhibitorArc(source=place, target=trans, id=2, name="I1")
    
    # Place: white fill, black border
    assert place.fill_color == (1.0, 1.0, 1.0), f"Place fill should be white, got {place.fill_color}"
    assert place.border_color == (0.0, 0.0, 0.0), f"Place border should be black, got {place.border_color}"
    
    # Transition: black fill, black border
    assert trans.fill_color == (0.0, 0.0, 0.0), f"Transition fill should be black, got {trans.fill_color}"
    assert trans.border_color == (0.0, 0.0, 0.0), f"Transition border should be black, got {trans.border_color}"
    
    # Arc: black line
    assert arc.color == (0.0, 0.0, 0.0), f"Arc color should be black, got {arc.color}"
    
    # InhibitorArc: black line (inherits from Arc)
    assert inhibitor.color == (0.0, 0.0, 0.0), f"InhibitorArc color should be black, got {inhibitor.color}"
    
    print("✓ All objects use black as default color")
    print("  Place: white fill (1,1,1), black border (0,0,0)")
    print("  Transition: black fill (0,0,0), black border (0,0,0)")
    print("  Arc: black line (0,0,0)")
    print("  InhibitorArc: black line (0,0,0)")
    return True


def main():
    """Run all connection validation tests."""
    print("\n=== Testing Petri Net Connection Rules ===\n")
    
    tests = [
        ("Valid: Place → Transition", test_valid_place_to_transition),
        ("Valid: Transition → Place", test_valid_transition_to_place),
        ("Invalid: Place → Place", test_invalid_place_to_place),
        ("Invalid: Transition → Transition", test_invalid_transition_to_transition),
        ("InhibitorArc Validation", test_inhibitor_arc_validation),
        ("Default Colors", test_default_colors),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
            print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("\n✓ All connection rules validated successfully!\n")
        print("Summary:")
        print("  ✓ Place → Transition (valid)")
        print("  ✓ Transition → Place (valid)")
        print("  ✗ Place → Place (blocked)")
        print("  ✗ Transition → Transition (blocked)")
        print("  ✓ InhibitorArc follows same rules")
        print("  ✓ All objects use black default color\n")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
