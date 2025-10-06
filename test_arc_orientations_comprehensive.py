#!/usr/bin/env python3
"""
Test: Arc Context Menu Sensitivity with Multiple Orientations
Verify that arcs work correctly regardless of their visual orientation:
- Horizontal (left-right, right-left)
- Vertical (top-bottom, bottom-top)
- Diagonal (various angles)
- With parallel arcs
- With transformations (curved)
"""

import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.data.model_canvas_manager import ModelCanvasManager


def get_arc_test_point(arc, manager, offset_applied=True):
    """Calculate a point that should be on the arc for testing."""
    src_x, src_y = arc.source.x, arc.source.y
    tgt_x, tgt_y = arc.target.x, arc.target.y
    
    # Check for parallel offset
    offset_distance = 0.0
    if offset_applied and hasattr(arc, '_manager') and arc._manager:
        try:
            parallels = manager.detect_parallel_arcs(arc)
            if parallels:
                offset_distance = manager.calculate_arc_offset(arc, parallels)
        except:
            pass
    
    # Apply offset if needed
    if abs(offset_distance) > 1e-6:
        dx = tgt_x - src_x
        dy = tgt_y - src_y
        length = math.sqrt(dx*dx + dy*dy)
        if length > 1e-6:
            perp_x = -dy / length
            perp_y = dx / length
            src_x += perp_x * offset_distance
            src_y += perp_y * offset_distance
            tgt_x += perp_x * offset_distance
            tgt_y += perp_y * offset_distance
    
    # Check if curved
    if getattr(arc, 'is_curved', False):
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        control_x = mid_x + getattr(arc, 'control_offset_x', 0)
        control_y = mid_y + getattr(arc, 'control_offset_y', 0)
        
        # Point at t=0.5 on bezier curve
        t = 0.5
        b0 = (1 - t) * (1 - t)
        b1 = 2 * (1 - t) * t
        b2 = t * t
        x = b0 * src_x + b1 * control_x + b2 * tgt_x
        y = b0 * src_y + b1 * control_y + b2 * tgt_y
        return (x, y)
    else:
        # Straight line midpoint
        return ((src_x + tgt_x) / 2, (src_y + tgt_y) / 2)


def test_orientation(name, place_pos, trans_pos, test_both_directions=True):
    """Test arcs in a specific orientation."""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    
    # Create manager and objects
    manager = ModelCanvasManager(None)
    place = Place(place_pos[0], place_pos[1], id=1, name="P1")
    trans = Transition(trans_pos[0], trans_pos[1], id=2, name="T1")
    manager.places.append(place)
    manager.transitions.append(trans)
    
    results = {}
    
    # Test Place → Transition
    print(f"\n1. Place ({place_pos[0]:.0f},{place_pos[1]:.0f}) → Transition ({trans_pos[0]:.0f},{trans_pos[1]:.0f})")
    
    arc1 = Arc(place, trans, id=3, name="A1")
    arc1._manager = manager
    manager.arcs.append(arc1)
    
    # Test straight
    test_x, test_y = get_arc_test_point(arc1, manager, offset_applied=False)
    clickable = arc1.contains_point(test_x, test_y)
    print(f"   Straight arc at ({test_x:.1f}, {test_y:.1f}): {clickable}")
    results[f"{name} - P→T straight"] = clickable
    
    # Test curved
    arc1.is_curved = True
    arc1.control_offset_x = -20
    arc1.control_offset_y = -20
    test_x, test_y = get_arc_test_point(arc1, manager, offset_applied=False)
    clickable = arc1.contains_point(test_x, test_y)
    print(f"   Curved arc at ({test_x:.1f}, {test_y:.1f}): {clickable}")
    results[f"{name} - P→T curved"] = clickable
    
    if test_both_directions:
        # Test Transition → Place (opposite direction)
        # Create a fresh manager to test arc2 in isolation
        print(f"\n2. Transition ({trans_pos[0]:.0f},{trans_pos[1]:.0f}) → Place ({place_pos[0]:.0f},{place_pos[1]:.0f})")
        
        manager2 = ModelCanvasManager(None)
        place2 = Place(place_pos[0], place_pos[1], id=1, name="P1")
        trans2 = Transition(trans_pos[0], trans_pos[1], id=2, name="T1")
        manager2.places.append(place2)
        manager2.transitions.append(trans2)
        
        arc2 = Arc(trans2, place2, id=4, name="A2")
        arc2._manager = manager2
        manager2.arcs.append(arc2)
        
        # Test straight
        test_x, test_y = get_arc_test_point(arc2, manager2, offset_applied=False)
        clickable = arc2.contains_point(test_x, test_y)
        print(f"   Straight arc at ({test_x:.1f}, {test_y:.1f}): {clickable}")
        results[f"{name} - T→P straight"] = clickable
        
        # Test curved
        arc2.is_curved = True
        arc2.control_offset_x = 20
        arc2.control_offset_y = 20
        test_x, test_y = get_arc_test_point(arc2, manager2, offset_applied=False)
        clickable = arc2.contains_point(test_x, test_y)
        print(f"   Curved arc at ({test_x:.1f}, {test_y:.1f}): {clickable}")
        results[f"{name} - T→P curved"] = clickable
        
        # Test with parallel arcs (both directions present)
        # Use the original manager with both arcs
        print(f"\n3. Parallel arcs (both directions):")
        
        # Reset arc1 to straight and add arc2 to original manager
        arc1.is_curved = False
        arc1.control_offset_x = 0
        arc1.control_offset_y = 0
        
        arc2_parallel = Arc(trans, place, id=5, name="A2")
        arc2_parallel._manager = manager
        manager.arcs.append(arc2_parallel)
        
        arc2_parallel = Arc(trans, place, id=5, name="A2")
        arc2_parallel._manager = manager
        manager.arcs.append(arc2_parallel)
        
        # Test with offset
        test_x1, test_y1 = get_arc_test_point(arc1, manager, offset_applied=True)
        clickable1 = arc1.contains_point(test_x1, test_y1)
        print(f"   Arc1 (P→T) with offset at ({test_x1:.1f}, {test_y1:.1f}): {clickable1}")
        results[f"{name} - parallel A1"] = clickable1
        
        test_x2, test_y2 = get_arc_test_point(arc2_parallel, manager, offset_applied=True)
        clickable2 = arc2_parallel.contains_point(test_x2, test_y2)
        print(f"   Arc2 (T→P) with offset at ({test_x2:.1f}, {test_y2:.1f}): {clickable2}")
        results[f"{name} - parallel A2"] = clickable2
    
    return results


def test_inhibitor_orientation(name, place_pos, trans_pos):
    """Test inhibitor arcs in a specific orientation (only Place→Transition)."""
    print(f"\n{'='*70}")
    print(f"Testing Inhibitor: {name}")
    print(f"{'='*70}")
    
    # Create manager and objects
    manager = ModelCanvasManager(None)
    place = Place(place_pos[0], place_pos[1], id=1, name="P1")
    trans = Transition(trans_pos[0], trans_pos[1], id=2, name="T1")
    manager.places.append(place)
    manager.transitions.append(trans)
    
    results = {}
    
    print(f"\n1. InhibitorArc: Place ({place_pos[0]:.0f},{place_pos[1]:.0f}) → Transition ({trans_pos[0]:.0f},{trans_pos[1]:.0f})")
    
    arc = InhibitorArc(place, trans, id=3, name="I1")
    arc._manager = manager
    manager.arcs.append(arc)
    
    # Test straight
    test_x, test_y = get_arc_test_point(arc, manager, offset_applied=False)
    clickable = arc.contains_point(test_x, test_y)
    print(f"   Straight inhibitor at ({test_x:.1f}, {test_y:.1f}): {clickable}")
    results[f"{name} - Inhibitor straight"] = clickable
    
    # Test curved
    arc.is_curved = True
    arc.control_offset_x = -20
    arc.control_offset_y = -20
    test_x, test_y = get_arc_test_point(arc, manager, offset_applied=False)
    clickable = arc.contains_point(test_x, test_y)
    print(f"   Curved inhibitor at ({test_x:.1f}, {test_y:.1f}): {clickable}")
    results[f"{name} - Inhibitor curved"] = clickable
    
    return results


def run_all_orientation_tests():
    """Test all different arc orientations."""
    print("\n" + "#"*70)
    print("# COMPREHENSIVE ARC ORIENTATION TEST")
    print("# Testing arcs at different angles and directions")
    print("#"*70)
    
    all_results = {}
    
    # 1. Horizontal arcs (left-right)
    all_results.update(test_orientation(
        "Horizontal (→)",
        place_pos=(100, 150),
        trans_pos=(300, 150)
    ))
    
    # 2. Vertical arcs (top-bottom)
    all_results.update(test_orientation(
        "Vertical (↓)",
        place_pos=(200, 100),
        trans_pos=(200, 300)
    ))
    
    # 3. Diagonal arcs (top-left to bottom-right)
    all_results.update(test_orientation(
        "Diagonal (↘)",
        place_pos=(100, 100),
        trans_pos=(300, 300)
    ))
    
    # 4. Diagonal arcs (bottom-left to top-right)
    all_results.update(test_orientation(
        "Diagonal (↗)",
        place_pos=(100, 300),
        trans_pos=(300, 100)
    ))
    
    # 5. Diagonal arcs (45° angle)
    all_results.update(test_orientation(
        "Diagonal 45° (↗)",
        place_pos=(150, 250),
        trans_pos=(250, 150)
    ))
    
    # 6. Steep angle
    all_results.update(test_orientation(
        "Steep angle",
        place_pos=(150, 100),
        trans_pos=(200, 300)
    ))
    
    # 7. Wide angle
    all_results.update(test_orientation(
        "Wide angle",
        place_pos=(100, 180),
        trans_pos=(300, 220)
    ))
    
    # Test inhibitor arcs with different orientations
    print("\n\n" + "#"*70)
    print("# INHIBITOR ARC ORIENTATIONS")
    print("#"*70)
    
    all_results.update(test_inhibitor_orientation(
        "Horizontal (→)",
        place_pos=(100, 150),
        trans_pos=(300, 150)
    ))
    
    all_results.update(test_inhibitor_orientation(
        "Vertical (↓)",
        place_pos=(200, 100),
        trans_pos=(200, 300)
    ))
    
    all_results.update(test_inhibitor_orientation(
        "Diagonal (↘)",
        place_pos=(100, 100),
        trans_pos=(300, 300)
    ))
    
    # Print summary
    print("\n\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in all_results.values() if v)
    total = len(all_results)
    
    print(f"\nTotal tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    print("\nDetailed results:")
    for test_name, result in all_results.items():
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")
    
    print("\n" + "="*70)
    if passed == total:
        print(f"✓ ALL {total} ORIENTATION TESTS PASSED! 🎉")
    else:
        print(f"✗ {total - passed} TESTS FAILED")
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_orientation_tests()
    sys.exit(0 if success else 1)
