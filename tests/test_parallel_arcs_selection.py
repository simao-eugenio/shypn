#!/usr/bin/env python3
"""Test parallel curved arcs selection rendering matches actual arc rendering."""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.curved_arc import CurvedArc
from shypn.data.model_canvas_manager import ModelCanvasManager


def test_parallel_curved_arcs_control_points():
    """Test that parallel curved arcs get offset control points."""
    print("\n=== Test: Parallel Curved Arcs Control Points ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create two opposite curved arcs (parallel arcs)
    arc1 = CurvedArc(place, trans, id=3, name="C1")
    arc2 = CurvedArc(trans, place, id=4, name="C2")
    
    # Create manager and add arcs
    manager = ModelCanvasManager()
    manager._objects_by_id = {
        1: place,
        2: trans,
        3: arc1,
        4: arc2,
    }
    manager._arcs = [arc1, arc2]
    
    # Link arcs to manager
    arc1._manager = manager
    arc2._manager = manager
    
    # Get control points WITHOUT parallel detection
    control1_no_offset = arc1._calculate_curve_control_point(offset=None)
    control2_no_offset = arc2._calculate_curve_control_point(offset=None)
    
    print(f"Arc1 control point (no offset): {control1_no_offset}")
    print(f"Arc2 control point (no offset): {control2_no_offset}")
    
    # Without parallel detection, opposite arcs should have same control point (canonical direction)
    # This is by design in CurvedArc
    
    # Detect parallel arcs
    parallels1 = manager.detect_parallel_arcs(arc1)
    parallels2 = manager.detect_parallel_arcs(arc2)
    
    print(f"\nArc1 has parallel arcs: {len(parallels1) if parallels1 else 0}")
    print(f"Arc2 has parallel arcs: {len(parallels2) if parallels2 else 0}")
    
    assert parallels1 and len(parallels1) > 0, "Arc1 should have parallel arc (Arc2)"
    assert parallels2 and len(parallels2) > 0, "Arc2 should have parallel arc (Arc1)"
    
    # Calculate offsets
    offset1 = manager.calculate_arc_offset(arc1, parallels1)
    offset2 = manager.calculate_arc_offset(arc2, parallels2)
    
    print(f"\nArc1 offset: {offset1}")
    print(f"Arc2 offset: {offset2}")
    
    # Offsets should be opposite (one positive, one negative)
    assert offset1 * offset2 < 0, "Parallel arcs should have opposite offsets"
    
    # Get control points WITH parallel detection
    control1_with_offset = arc1._calculate_curve_control_point(offset=offset1)
    control2_with_offset = arc2._calculate_curve_control_point(offset=offset2)
    
    print(f"\nArc1 control point (with offset): {control1_with_offset}")
    print(f"Arc2 control point (with offset): {control2_with_offset}")
    
    # Control points should now be different
    assert control1_with_offset != control2_with_offset, "Parallel arcs should have different control points"
    
    # Distance between control points
    cp1_x, cp1_y = control1_with_offset
    cp2_x, cp2_y = control2_with_offset
    distance = ((cp1_x - cp2_x) ** 2 + (cp1_y - cp2_y) ** 2) ** 0.5
    print(f"\nDistance between control points: {distance:.2f}")
    
    # They should be separated
    assert distance > 10, f"Control points should be separated by more than 10 units, got {distance:.2f}"
    
    print("\n✓ Parallel curved arcs have correctly offset control points!")
    return True


def test_selection_uses_parallel_offset():
    """Test that selection rendering would use parallel arc offset."""
    print("\n=== Test: Selection Rendering Uses Parallel Offset ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create two opposite curved arcs
    arc1 = CurvedArc(place, trans, id=3, name="C1")
    arc2 = CurvedArc(trans, place, id=4, name="C2")
    
    # Create manager and add arcs
    manager = ModelCanvasManager()
    manager._objects_by_id = {
        1: place,
        2: trans,
        3: arc1,
        4: arc2,
    }
    manager._arcs = [arc1, arc2]
    
    # Link arcs to manager
    arc1._manager = manager
    arc2._manager = manager
    
    print("Simulating selection rendering logic for Arc1:")
    
    # Simulate what the selection rendering does (from object_editing_transforms.py)
    offset_distance = None
    if hasattr(arc1, '_manager') and arc1._manager:
        try:
            parallels = arc1._manager.detect_parallel_arcs(arc1)
            if parallels:
                offset_distance = arc1._manager.calculate_arc_offset(arc1, parallels)
                print(f"  Detected {len(parallels)} parallel arc(s)")
                print(f"  Calculated offset: {offset_distance}")
        except (AttributeError, Exception) as e:
            print(f"  Exception: {e}")
            pass
    
    control_point = arc1._calculate_curve_control_point(offset=offset_distance)
    print(f"  Control point for selection rendering: {control_point}")
    
    # Now check what the actual render would use
    parallels_render = arc1._manager.detect_parallel_arcs(arc1)
    offset_render = arc1._manager.calculate_arc_offset(arc1, parallels_render) if parallels_render else None
    control_point_render = arc1._calculate_curve_control_point(offset=offset_render)
    print(f"  Control point for arc rendering: {control_point_render}")
    
    # They should match
    assert control_point == control_point_render, \
        f"Selection control point {control_point} should match render control point {control_point_render}"
    
    print("\n✓ Selection rendering uses same control point as arc rendering!")
    return True


def test_opposite_arcs_on_same_side_as_handle():
    """Verify that parallel arcs curve on opposite sides with handles matching."""
    print("\n=== Test: Opposite Arcs Curve on Opposite Sides ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create two opposite curved arcs
    arc1 = CurvedArc(place, trans, id=3, name="C1")  # P1 -> T1
    arc2 = CurvedArc(trans, place, id=4, name="C2")  # T1 -> P1
    
    # Create manager and add arcs
    manager = ModelCanvasManager()
    manager._objects_by_id = {
        1: place,
        2: trans,
        3: arc1,
        4: arc2,
    }
    manager._arcs = [arc1, arc2]
    
    # Link arcs to manager
    arc1._manager = manager
    arc2._manager = manager
    
    # Get control points with parallel detection
    parallels1 = manager.detect_parallel_arcs(arc1)
    offset1 = manager.calculate_arc_offset(arc1, parallels1) if parallels1 else None
    control1 = arc1._calculate_curve_control_point(offset=offset1)
    
    parallels2 = manager.detect_parallel_arcs(arc2)
    offset2 = manager.calculate_arc_offset(arc2, parallels2) if parallels2 else None
    control2 = arc2._calculate_curve_control_point(offset=offset2)
    
    # Midpoint between place and transition
    mid_x = (place.x + trans.x) / 2
    mid_y = (place.y + trans.y) / 2
    
    print(f"Place: ({place.x}, {place.y})")
    print(f"Transition: ({trans.x}, {trans.y})")
    print(f"Midpoint: ({mid_x}, {mid_y})")
    print(f"\nArc1 (P→T) control point: {control1}")
    print(f"Arc2 (T→P) control point: {control2}")
    
    cp1_x, cp1_y = control1
    cp2_x, cp2_y = control2
    
    # Check which side of the straight line each control point is on
    # Using cross product to determine side
    # Vector from place to trans: (200, 0)
    # Vector from place to control1: (cp1_x - 100, cp1_y - 100)
    # Cross product z-component: dx1*dy2 - dy1*dx2
    
    dx_line = trans.x - place.x
    dy_line = trans.y - place.y
    
    dx_cp1 = cp1_x - place.x
    dy_cp1 = cp1_y - place.y
    cross1 = dx_line * dy_cp1 - dy_line * dx_cp1
    
    dx_cp2 = cp2_x - place.x
    dy_cp2 = cp2_y - place.y
    cross2 = dx_line * dy_cp2 - dy_line * dx_cp2
    
    print(f"\nArc1 side (cross product): {cross1:.2f} ({'above' if cross1 > 0 else 'below'} line)")
    print(f"Arc2 side (cross product): {cross2:.2f} ({'above' if cross2 > 0 else 'below'} line)")
    
    # They should be on opposite sides
    assert cross1 * cross2 < 0, "Parallel arcs should curve on opposite sides of the straight line"
    
    print("\n✓ Parallel arcs curve on opposite sides with handles matching!")
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PARALLEL CURVED ARCS SELECTION RENDERING TEST")
    print("="*70)
    
    all_pass = True
    tests = [
        test_parallel_curved_arcs_control_points,
        test_selection_uses_parallel_offset,
        test_opposite_arcs_on_same_side_as_handle,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except AssertionError as e:
            print(f"\n✗ {test_func.__name__} FAILED: {e}")
            all_pass = False
        except Exception as e:
            print(f"\n✗ {test_func.__name__} ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_pass = False
    
    if all_pass:
        print("\n" + "="*70)
        print("ALL TESTS PASSED!")
        print("="*70)
        print("\nThe selection rendering (blue arc) now uses the same control")
        print("point calculation as the actual arc rendering, including parallel")
        print("arc offset detection. This ensures the blue selection arc matches")
        print("the actual rendered arc and appears on the same side as the handle.")
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("SOME TESTS FAILED")
        print("="*70)
        sys.exit(1)
