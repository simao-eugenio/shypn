#!/usr/bin/env python3
"""
Test arc hit detection for straight and curved arcs.
"""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.netobjs import Place, Transition, Arc


def test_straight_arc_hit_detection():
    """Test hit detection on a straight arc."""
    print("\n" + "="*60)
    print("Testing Straight Arc Hit Detection")
    print("="*60)
    
    # Create arc from (100, 100) to (300, 100)
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    arc = Arc(source=place, target=transition, id=1, name="A1")
    
    assert not arc.is_curved, "Arc should start straight"
    
    # Test points on the line
    mid_x = 200
    mid_y = 100
    
    print(f"\nArc from ({place.x}, {place.y}) to ({transition.x}, {transition.y})")
    print(f"Testing point on line: ({mid_x}, {mid_y})")
    assert arc.contains_point(mid_x, mid_y), "Point on line should be contained"
    print("  ✓ Point on line detected")
    
    # Test point near the line (within tolerance)
    print(f"Testing point near line: ({mid_x}, {mid_y + 5})")
    assert arc.contains_point(mid_x, mid_y + 5), "Point near line should be contained"
    print("  ✓ Point near line detected")
    
    # Test point far from line (outside tolerance)
    print(f"Testing point far from line: ({mid_x}, {mid_y + 20})")
    assert not arc.contains_point(mid_x, mid_y + 20), "Point far from line should not be contained"
    print("  ✓ Point far from line correctly rejected")
    
    print("\n✓ Straight arc hit detection tests passed!")


def test_curved_arc_hit_detection():
    """Test hit detection on a curved arc."""
    print("\n" + "="*60)
    print("Testing Curved Arc Hit Detection")
    print("="*60)
    
    # Create arc from (100, 100) to (300, 100)
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    arc = Arc(source=place, target=transition, id=1, name="A1")
    
    # Make it curved with offset upward
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -50.0  # Curve upward
    
    print(f"\nCurved arc from ({place.x}, {place.y}) to ({transition.x}, {transition.y})")
    print(f"Control offset: ({arc.control_offset_x}, {arc.control_offset_y})")
    
    # The midpoint of the straight line should NOT be on the curve
    mid_x = 200
    mid_y = 100
    print(f"\nTesting straight midpoint: ({mid_x}, {mid_y})")
    # This might or might not be within tolerance depending on curve
    result = arc.contains_point(mid_x, mid_y)
    print(f"  Result: {result} (depends on curve strength)")
    
    # Point on the curve (approximately at the apex)
    # For a quadratic Bezier at t=0.5:
    # curve_y = 0.25 * src_y + 0.5 * control_y + 0.25 * tgt_y
    # = 0.25 * 100 + 0.5 * 50 + 0.25 * 100 = 25 + 25 + 25 = 75
    curve_mid_x = 200
    curve_mid_y = 75  # Approximate apex of curve
    
    print(f"Testing point on curve apex: ({curve_mid_x}, {curve_mid_y})")
    assert arc.contains_point(curve_mid_x, curve_mid_y), "Point on curve should be contained"
    print("  ✓ Point on curved arc detected")
    
    # Point far from curve
    print(f"Testing point far from curve: ({curve_mid_x}, {curve_mid_y - 30})")
    assert not arc.contains_point(curve_mid_x, curve_mid_y - 30), "Point far from curve should not be contained"
    print("  ✓ Point far from curve correctly rejected")
    
    # Test point along the curve (at t=0.25)
    t = 0.25
    one_minus_t = 0.75
    control_x = 200  # mid_x + control_offset_x
    control_y = 50   # mid_y + control_offset_y
    curve_x = one_minus_t * one_minus_t * 100 + 2 * one_minus_t * t * control_x + t * t * 300
    curve_y = one_minus_t * one_minus_t * 100 + 2 * one_minus_t * t * control_y + t * t * 100
    
    print(f"Testing point at t=0.25 on curve: ({curve_x:.1f}, {curve_y:.1f})")
    assert arc.contains_point(curve_x, curve_y), "Point on curve at t=0.25 should be contained"
    print("  ✓ Point on curve detected")
    
    print("\n✓ Curved arc hit detection tests passed!")


def test_toggle_and_click():
    """Test that arc remains clickable after toggling curved/straight."""
    print("\n" + "="*60)
    print("Testing Arc Clickability After Transform")
    print("="*60)
    
    # Create arc
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    arc = Arc(source=place, target=transition, id=1, name="A1")
    
    # Test straight arc clickability
    print("\nTesting straight arc...")
    assert arc.contains_point(200, 100), "Straight arc should be clickable"
    print("  ✓ Straight arc is clickable")
    
    # Toggle to curved
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -50.0
    
    print("\nTesting after toggle to curved...")
    # Should still be clickable somewhere on the curve
    assert arc.contains_point(200, 75), "Curved arc should be clickable"
    print("  ✓ Curved arc is clickable")
    
    # Toggle back to straight
    arc.is_curved = False
    
    print("\nTesting after toggle back to straight...")
    assert arc.contains_point(200, 100), "Arc should be clickable after toggle back"
    print("  ✓ Arc remains clickable after toggle")
    
    print("\n✓ Arc clickability after transform tests passed!")


if __name__ == '__main__':
    try:
        test_straight_arc_hit_detection()
        test_curved_arc_hit_detection()
        test_toggle_and_click()
        
        print("\n" + "="*60)
        print("ALL ARC HIT DETECTION TESTS PASSED!")
        print("="*60)
        print("\nCurved arcs are now clickable and editable!")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
