#!/usr/bin/env python3
"""Test script to verify updated Petri net object dimensions and InhibitorArc."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.api import Place, Transition, Arc, InhibitorArc


def test_place_dimensions():
    """Test that Place keeps its current radius."""
    place = Place(x=100, y=100, id=1, name="P1")
    assert place.radius == 25.0, f"Expected radius 25.0, got {place.radius}"
    print("✓ Place radius: 25.0 (unchanged)")


def test_transition_dimensions():
    """Test that Transition has updated dimensions."""
    trans = Transition(x=200, y=200, id=1, name="T1")
    assert trans.width == 50.0, f"Expected width 50.0, got {trans.width}"
    assert trans.height == 25.0, f"Expected height 25.0 (updated from 8.0), got {trans.height}"
    print(f"✓ Transition dimensions: {trans.width}×{trans.height} (height updated to place radius)")


def test_arc_parameters():
    """Test that Arc has updated visual parameters."""
    place = Place(x=100, y=100, id=1, name="P1")
    trans = Transition(x=200, y=200, id=1, name="T1")
    arc = Arc(source=place, target=trans, id=1, name="A1")
    
    assert arc.width == 3.0, f"Expected width 3.0 (updated from 2.0), got {arc.width}"
    assert arc.ARROW_SIZE == 15.0, f"Expected arrow size 15.0 (updated from 10.0), got {arc.ARROW_SIZE}"
    print(f"✓ Arc parameters: width={arc.width}, arrow_size={arc.ARROW_SIZE} (improved visibility)")


def test_inhibitor_arc():
    """Test that InhibitorArc class exists and inherits from Arc."""
    place = Place(x=100, y=100, id=1, name="P1")
    trans = Transition(x=200, y=200, id=2, name="T1")
    
    # Create inhibitor arc
    inhibitor = InhibitorArc(source=place, target=trans, id=1, name="I1", weight=1)
    
    assert isinstance(inhibitor, Arc), "InhibitorArc should inherit from Arc"
    assert inhibitor.MARKER_RADIUS == 8.0, f"Expected marker radius 8.0, got {inhibitor.MARKER_RADIUS}"
    assert inhibitor.weight == 1, f"Expected weight 1, got {inhibitor.weight}"
    print(f"✓ InhibitorArc created: inherits from Arc, marker_radius={inhibitor.MARKER_RADIUS}")


def test_object_creation():
    """Test basic object creation and relationships."""
    # Create objects
    p1 = Place(x=100, y=100, id=1, name="P1")
    t1 = Transition(x=200, y=200, id=1, name="T1")
    a1 = Arc(source=p1, target=t1, id=1, name="A1")
    i1 = InhibitorArc(source=p1, target=t1, id=2, name="I1", weight=1)
    
    # Verify relationships
    assert a1.source == p1, "Arc source should be P1"
    assert a1.target == t1, "Arc target should be T1"
    assert i1.source == p1, "InhibitorArc source should be P1"
    assert i1.target == t1, "InhibitorArc target should be T1"
    
    print("✓ Object creation and relationships work correctly")


def main():
    """Run all tests."""
    print("\n=== Testing Petri Net Object Updates ===\n")
    
    try:
        test_place_dimensions()
        test_transition_dimensions()
        test_arc_parameters()
        test_inhibitor_arc()
        test_object_creation()
        
        print("\n=== All Tests Passed! ===\n")
        print("Summary of changes:")
        print("  • Place radius: 25.0 (unchanged)")
        print("  • Transition: 50.0×25.0 (height updated from 8.0 to place radius)")
        print("  • Arc width: 3.0 (updated from 2.0)")
        print("  • Arc arrow size: 15.0 (updated from 10.0)")
        print("  • InhibitorArc class: Created (inherits from Arc)")
        print("  • InhibitorArc marker: 8.0 radius circular marker\n")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
