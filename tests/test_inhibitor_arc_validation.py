#!/usr/bin/env python3
"""Test inhibitor arc connection validation.

Verifies that:
1. Inhibitor arcs can only connect Place → Transition
2. Transition → Place is forbidden for inhibitor arcs
3. Transformation to inhibitor arc validates direction
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs import Place, Transition, Arc, InhibitorArc, CurvedInhibitorArc
from shypn.utils.arc_transform import convert_to_inhibitor, transform_arc


def test_inhibitor_arc_place_to_transition():
    """Test that Place → Transition is allowed for inhibitor arcs."""
    print("Testing Place → Transition (should succeed)...")
    
    place = Place(id=1, name="P1", x=100, y=100)
    transition = Transition(id=2, name="T1", x=200, y=100)
    
    try:
        arc = InhibitorArc(source=place, target=transition, id=10, name="I1")
        print(f"  ✓ Created {type(arc).__name__}: {arc.source.name} → {arc.target.name}")
        return True
    except ValueError as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_inhibitor_arc_transition_to_place():
    """Test that Transition → Place is forbidden for inhibitor arcs."""
    print("\nTesting Transition → Place (should fail)...")
    
    transition = Transition(id=1, name="T1", x=100, y=100)
    place = Place(id=2, name="P1", x=200, y=100)
    
    try:
        arc = InhibitorArc(source=transition, target=place, id=10, name="I1")
        print(f"  ✗ FAILED: Should have raised ValueError")
        print(f"     Created: {type(arc).__name__}: {arc.source.name} → {arc.target.name}")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly rejected: {e}")
        return True


def test_curved_inhibitor_arc_transition_to_place():
    """Test that Transition → Place is forbidden for curved inhibitor arcs."""
    print("\nTesting Curved Transition → Place (should fail)...")
    
    transition = Transition(id=1, name="T1", x=100, y=100)
    place = Place(id=2, name="P1", x=200, y=100)
    
    try:
        arc = CurvedInhibitorArc(source=transition, target=place, id=10, name="CI1")
        print(f"  ✗ FAILED: Should have raised ValueError")
        print(f"     Created: {type(arc).__name__}: {arc.source.name} → {arc.target.name}")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly rejected: {e}")
        return True


def test_normal_arc_transition_to_place():
    """Test that normal Arc allows Transition → Place."""
    print("\nTesting Normal Arc Transition → Place (should succeed)...")
    
    transition = Transition(id=1, name="T1", x=100, y=100)
    place = Place(id=2, name="P1", x=200, y=100)
    
    try:
        arc = Arc(source=transition, target=place, id=10, name="A1")
        print(f"  ✓ Created {type(arc).__name__}: {arc.source.name} → {arc.target.name}")
        return True
    except ValueError as e:
        print(f"  ✗ FAILED: Normal arcs should allow this: {e}")
        return False


def test_transform_transition_to_place_to_inhibitor():
    """Test that transforming Transition → Place arc to inhibitor fails."""
    print("\nTesting transformation Transition → Place to Inhibitor (should fail)...")
    
    transition = Transition(id=1, name="T1", x=100, y=100)
    place = Place(id=2, name="P1", x=200, y=100)
    arc = Arc(source=transition, target=place, id=10, name="A1")
    
    print(f"  Created normal arc: {arc.source.name} → {arc.target.name}")
    
    try:
        inhibitor_arc = convert_to_inhibitor(arc)
        print(f"  ✗ FAILED: Should have raised ValueError")
        print(f"     Converted to: {type(inhibitor_arc).__name__}")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly rejected transformation: {e}")
        return True


def test_transform_place_to_transition_to_inhibitor():
    """Test that transforming Place → Transition arc to inhibitor succeeds."""
    print("\nTesting transformation Place → Transition to Inhibitor (should succeed)...")
    
    place = Place(id=1, name="P1", x=100, y=100)
    transition = Transition(id=2, name="T1", x=200, y=100)
    arc = Arc(source=place, target=transition, id=10, name="A1")
    
    print(f"  Created normal arc: {arc.source.name} → {arc.target.name}")
    
    try:
        inhibitor_arc = convert_to_inhibitor(arc)
        print(f"  ✓ Converted to {type(inhibitor_arc).__name__}: {inhibitor_arc.source.name} → {inhibitor_arc.target.name}")
        return True
    except ValueError as e:
        print(f"  ✗ FAILED: This transformation should succeed: {e}")
        return False


def main():
    print("=== Testing Inhibitor Arc Connection Validation ===\n")
    
    tests = [
        test_inhibitor_arc_place_to_transition,
        test_inhibitor_arc_transition_to_place,
        test_curved_inhibitor_arc_transition_to_place,
        test_normal_arc_transition_to_place,
        test_transform_transition_to_place_to_inhibitor,
        test_transform_place_to_transition_to_inhibitor,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} of {total} tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
