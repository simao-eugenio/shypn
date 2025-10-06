#!/usr/bin/env python3
"""Debug: Find clickable points on curved arc."""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.curved_arc import CurvedArc


def find_clickable_region():
    """Find where the curved arc is actually clickable."""
    print("\n=== Debug: Find Clickable Region on Curve ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Get control point
    control_point = arc._calculate_curve_control_point()
    cp_x, cp_y = control_point
    print(f"Control point: ({cp_x}, {cp_y})")
    
    # Source and target
    src_x, src_y = place.x, place.y
    tgt_x, tgt_y = trans.x, trans.y
    print(f"Source: ({src_x}, {src_y})")
    print(f"Target: ({tgt_x}, {tgt_y})")
    
    # Sample points along the Bezier curve
    print("\nSampling curve to find clickable points:")
    clickable_points = []
    
    for i in range(21):
        t = i / 20.0
        # Quadratic Bezier formula
        one_minus_t = 1.0 - t
        curve_x = (one_minus_t * one_minus_t * src_x + 
                  2 * one_minus_t * t * cp_x + 
                  t * t * tgt_x)
        curve_y = (one_minus_t * one_minus_t * src_y + 
                  2 * one_minus_t * t * cp_y + 
                  t * t * tgt_y)
        
        # Test if this point is clickable
        is_clickable = arc.contains_point(curve_x, curve_y)
        
        if is_clickable:
            clickable_points.append((curve_x, curve_y))
            print(f"  t={t:.2f}: ({curve_x:.1f}, {curve_y:.1f}) ✓ CLICKABLE")
        else:
            print(f"  t={t:.2f}: ({curve_x:.1f}, {curve_y:.1f}) ✗ not clickable")
    
    if clickable_points:
        print(f"\n✓ Found {len(clickable_points)} clickable points on curve")
        # Find midpoint of clickable region
        mid_idx = len(clickable_points) // 2
        mid_x, mid_y = clickable_points[mid_idx]
        print(f"Mid-clickable point: ({mid_x:.1f}, {mid_y:.1f})")
        return (mid_x, mid_y)
    else:
        print("\n✗ No clickable points found on curve!")
        return None


def test_with_better_point():
    """Test clicking at a point that's actually on the curve."""
    print("\n=== Test: Click at Point ON Curve ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Get control point
    control_point = arc._calculate_curve_control_point()
    cp_x, cp_y = control_point
    src_x, src_y = place.x, place.y
    tgt_x, tgt_y = trans.x, trans.y
    
    # Calculate point ON the curve at t=0.5 (midpoint of curve)
    t = 0.5
    one_minus_t = 1.0 - t
    curve_mid_x = (one_minus_t * one_minus_t * src_x + 
                   2 * one_minus_t * t * cp_x + 
                   t * t * tgt_x)
    curve_mid_y = (one_minus_t * one_minus_t * src_y + 
                   2 * one_minus_t * t * cp_y + 
                   t * t * tgt_y)
    
    print(f"Control point: ({cp_x}, {cp_y})")
    print(f"Point on curve at t=0.5: ({curve_mid_x:.1f}, {curve_mid_y:.1f})")
    
    # Test if control point is clickable
    cp_clickable = arc.contains_point(cp_x, cp_y)
    print(f"Control point clickable: {cp_clickable}")
    
    # Test if curve midpoint is clickable
    curve_clickable = arc.contains_point(curve_mid_x, curve_mid_y)
    print(f"Curve midpoint clickable: {curve_clickable}")
    
    if curve_clickable:
        print("✓ Curve midpoint is clickable!")
        return (curve_mid_x, curve_mid_y)
    else:
        print("✗ Even curve midpoint is not clickable!")
        return None


if __name__ == '__main__':
    clickable_mid = find_clickable_region()
    test_with_better_point()
