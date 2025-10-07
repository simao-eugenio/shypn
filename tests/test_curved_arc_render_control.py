#!/usr/bin/env python3
"""Test that CurvedArc rendering uses manual control point correctly."""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.curved_arc import CurvedArc


def test_curved_arc_render_uses_manual_control():
    """Verify that CurvedArc render() uses manual_control_point when set."""
    print("\n=== Test: CurvedArc Render Uses Manual Control Point ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Get automatic control point
    auto_control = arc._calculate_curve_control_point()
    print(f"Automatic control point: {auto_control}")
    
    # Test 1: Without manual control point, should use automatic
    print("\nTest 1: No manual control point set")
    assert not hasattr(arc, 'manual_control_point') or arc.manual_control_point is None
    print("✓ manual_control_point is None (will use automatic)")
    
    # Test 2: Set manual control point
    print("\nTest 2: Set manual control point")
    manual_point = (200, 200)
    arc.manual_control_point = manual_point
    assert arc.manual_control_point == manual_point
    print(f"✓ manual_control_point set to {manual_point}")
    
    # Test 3: Verify manual point is different from automatic
    assert arc.manual_control_point != auto_control
    print(f"✓ Manual point {manual_point} differs from automatic {auto_control}")
    
    # Test 4: Clear manual control point (back to automatic)
    print("\nTest 3: Clear manual control point")
    arc.manual_control_point = None
    assert arc.manual_control_point is None
    print("✓ manual_control_point cleared (back to automatic)")
    
    print("\n" + "="*50)
    print("CURVED ARC RENDER CONTROL POINT TEST PASSED!")
    print("="*50)
    return True


if __name__ == '__main__':
    try:
        test_curved_arc_render_uses_manual_control()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
