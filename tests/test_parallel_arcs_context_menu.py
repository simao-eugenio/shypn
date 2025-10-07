#!/usr/bin/env python3
"""
Test: Parallel Arc Context Menu Sensitivity
Verify that parallel arcs (opposite directions) are clickable with offset.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.data.model_canvas_manager import ModelCanvasManager


def test_parallel_arcs_context_menu():
    """Test that parallel arcs can be clicked for context menu."""
    print("="*70)
    print("Test: Parallel Arc Context Menu Sensitivity")
    print("="*70)
    
    # Create a simple manager to handle parallel arc detection
    manager = ModelCanvasManager(None)
    
    # Create place and transition
    place = Place(100, 150, id=1, name="P1")
    trans = Transition(300, 150, id=2, name="T1")
    
    # Add them to manager
    manager.places.append(place)
    manager.transitions.append(trans)
    
    # Create parallel arcs
    arc1 = Arc(place, trans, id=3, name="A1")  # Place -> Transition
    arc2 = Arc(trans, place, id=4, name="A2")  # Transition -> Place
    
    # Set manager reference
    arc1._manager = manager
    arc2._manager = manager
    
    # Add arcs to manager
    manager.arcs.append(arc1)
    manager.arcs.append(arc2)
    
    print("\n1. Setup:")
    print(f"   Arc1: {arc1.source.name} → {arc1.target.name}")
    print(f"   Arc2: {arc2.source.name} → {arc2.target.name}")
    
    # Detect parallel arcs
    parallels1 = manager.detect_parallel_arcs(arc1)
    parallels2 = manager.detect_parallel_arcs(arc2)
    
    print(f"\n2. Parallel arc detection:")
    print(f"   Arc1 has {len(parallels1)} parallel arc(s): {[p.name for p in parallels1]}")
    print(f"   Arc2 has {len(parallels2)} parallel arc(s): {[p.name for p in parallels2]}")
    
    # Calculate offsets
    offset1 = manager.calculate_arc_offset(arc1, parallels1)
    offset2 = manager.calculate_arc_offset(arc2, parallels2)
    
    print(f"\n3. Offsets:")
    print(f"   Arc1 offset: {offset1:.1f}")
    print(f"   Arc2 offset: {offset2:.1f}")
    
    # Test points near the rendered arcs (with offset)
    # Midpoint of line
    mid_x = (place.x + trans.x) / 2  # 200
    mid_y = (place.y + trans.y) / 2  # 150
    
    # Both arcs should be on the SAME side due to how perpendicular is calculated!
    # Arc1: (100→300), perp=(0,1), offset=+50 → (0,1)*50 = UP 50
    # Arc2: (300→100), perp=(0,-1), offset=-50 → (0,-1)*(-50) = UP 50
    # So both should be at y=200!
    
    test_x1 = mid_x
    test_y1 = mid_y + 50  # Arc1 should be here
    
    test_x2 = mid_x  
    test_y2 = mid_y + 50  # Arc2 should also be here!
    
    print(f"\n4. Hit testing (straight arcs with parallel offset):")
    print(f"   Testing Arc1 at ({test_x1:.1f}, {test_y1:.1f}):")
    clickable1 = arc1.contains_point(test_x1, test_y1)
    print(f"     Arc1 clickable: {clickable1}")
    
    print(f"   Testing Arc2 at ({test_x2:.1f}, {test_y2:.1f}):")
    clickable2 = arc2.contains_point(test_x2, test_y2)
    print(f"     Arc2 clickable: {clickable2}")
    
    # Test at midpoint (should click one of them)
    print(f"\n5. Hit testing at exact midpoint ({mid_x:.1f}, {mid_y:.1f}):")
    clickable1_mid = arc1.contains_point(mid_x, mid_y)
    clickable2_mid = arc2.contains_point(mid_x, mid_y)
    print(f"   Arc1 clickable at midpoint: {clickable1_mid}")
    print(f"   Arc2 clickable at midpoint: {clickable2_mid}")
    
    # Test with curved arcs
    print("\n" + "="*70)
    print("6. Testing with curved parallel arcs:")
    print("="*70)
    
    # Transform arc1 to curved
    arc1.is_curved = True
    arc1.control_offset_x = -30
    arc1.control_offset_y = 0
    
    # Calculate curve midpoint for arc1
    # At t=0.5 on bezier curve
    src_x1 = place.x
    src_y1 = place.y
    tgt_x1 = trans.x
    tgt_y1 = trans.y
    
    # Apply parallel offset
    if abs(offset1) > 1e-6:
        dx = tgt_x1 - src_x1
        dy = tgt_y1 - src_y1
        length = (dx * dx + dy * dy) ** 0.5
        perp_x = -dy / length
        perp_y = dx / length
        src_x1 += perp_x * offset1
        src_y1 += perp_y * offset1
        tgt_x1 += perp_x * offset1
        tgt_y1 += perp_y * offset1
    
    # Control point
    mid_x1 = (src_x1 + tgt_x1) / 2
    mid_y1 = (src_y1 + tgt_y1) / 2
    control_x1 = mid_x1 + arc1.control_offset_x
    control_y1 = mid_y1 + arc1.control_offset_y
    
    # Point at t=0.5
    t = 0.5
    b0 = (1 - t) * (1 - t)
    b1 = 2 * (1 - t) * t
    b2 = t * t
    curve_x1 = b0 * src_x1 + b1 * control_x1 + b2 * tgt_x1
    curve_y1 = b0 * src_y1 + b1 * control_y1 + b2 * tgt_y1
    
    print(f"   Arc1 is now curved")
    print(f"   Testing at curve point ({curve_x1:.1f}, {curve_y1:.1f}):")
    clickable1_curved = arc1.contains_point(curve_x1, curve_y1)
    print(f"     Arc1 clickable: {clickable1_curved}")
    
    # Summary
    print("\n" + "="*70)
    print("RESULTS:")
    print("="*70)
    
    results = {
        "Arc1 (straight, with offset)": clickable1,
        "Arc2 (straight, with offset)": clickable2,
        "Arc1 (curved, with offset)": clickable1_curved,
    }
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"{status} {test_name}: {'PASS' if passed else 'FAIL'}")
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL PARALLEL ARCS ARE CLICKABLE! 🎉")
    else:
        print("✗ SOME PARALLEL ARCS FAILED")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = test_parallel_arcs_context_menu()
    sys.exit(0 if success else 1)
