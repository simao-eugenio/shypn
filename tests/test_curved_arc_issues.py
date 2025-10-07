#!/usr/bin/env python3
"""Test fixes for CurvedArc transformation issues."""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.curved_arc import CurvedArc
from shypn.edit.transformation.handle_detector import HandleDetector
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler
from shypn.edit.selection_manager import SelectionManager


def test_handle_position_after_transform():
    """Test that handle appears at the manual control point after transformation."""
    print("\n=== Test: Handle Position After Transform ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Get automatic control point
    auto_control = arc._calculate_curve_control_point()
    print(f"Automatic control point: {auto_control}")
    
    # Get handle position before transformation
    detector = HandleDetector()
    handles_before = detector.get_handle_positions(arc, zoom=1.0)
    handle_pos_before = handles_before.get('midpoint')
    print(f"Handle position before transform: {handle_pos_before}")
    
    # Verify handle is at automatic control point
    assert handle_pos_before == auto_control, f"Expected {auto_control}, got {handle_pos_before}"
    
    # Set manual control point (simulating user drag)
    manual_point = (200, 150)
    arc.manual_control_point = manual_point
    print(f"Set manual control point to: {manual_point}")
    
    # Get handle position after transformation
    handles_after = detector.get_handle_positions(arc, zoom=1.0)
    handle_pos_after = handles_after.get('midpoint')
    print(f"Handle position after transform: {handle_pos_after}")
    
    # Verify handle is now at manual control point
    assert handle_pos_after == manual_point, f"Expected {manual_point}, got {handle_pos_after}"
    
    print("✓ Handle position correctly follows manual control point!")
    return True


def test_contains_point_after_transform():
    """Test that transformed arc is still clickable at the new position."""
    print("\n=== Test: Contains Point After Transform ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Get automatic control point
    auto_control = arc._calculate_curve_control_point()
    auto_cp_x, auto_cp_y = auto_control
    print(f"Automatic control point: {auto_control}")
    
    # Calculate point ON the curve at t=0.5 (midpoint of curve)
    src_x, src_y = place.x, place.y
    tgt_x, tgt_y = trans.x, trans.y
    t = 0.5
    one_minus_t = 1.0 - t
    auto_curve_x = (one_minus_t * one_minus_t * src_x + 
                    2 * one_minus_t * t * auto_cp_x + 
                    t * t * tgt_x)
    auto_curve_y = (one_minus_t * one_minus_t * src_y + 
                    2 * one_minus_t * t * auto_cp_y + 
                    t * t * tgt_y)
    print(f"Point on automatic curve at t=0.5: ({auto_curve_x:.1f}, {auto_curve_y:.1f})")
    
    # Test that arc is clickable near automatic curve midpoint
    is_clickable_before = arc.contains_point(auto_curve_x, auto_curve_y)
    print(f"Arc clickable at automatic curve midpoint: {is_clickable_before}")
    assert is_clickable_before, "Arc should be clickable at automatic curve midpoint"
    
    # Set manual control point (simulating user drag)
    manual_point = (200, 150)
    arc.manual_control_point = manual_point
    manual_cp_x, manual_cp_y = manual_point
    print(f"Set manual control point to: {manual_point}")
    
    # Calculate point ON the manual curve at t=0.5
    manual_curve_x = (one_minus_t * one_minus_t * src_x + 
                      2 * one_minus_t * t * manual_cp_x + 
                      t * t * tgt_x)
    manual_curve_y = (one_minus_t * one_minus_t * src_y + 
                      2 * one_minus_t * t * manual_cp_y + 
                      t * t * tgt_y)
    print(f"Point on manual curve at t=0.5: ({manual_curve_x:.1f}, {manual_curve_y:.1f})")
    
    # Test that arc is now clickable near manual curve midpoint
    is_clickable_after = arc.contains_point(manual_curve_x, manual_curve_y)
    print(f"Arc clickable at manual curve midpoint: {is_clickable_after}")
    assert is_clickable_after, "Arc should be clickable at manual curve midpoint"
    
    print("✓ Transformed arc is clickable at new position!")
    return True


def test_double_click_after_transform():
    """Test that double-clicking a transformed arc enters edit mode again."""
    print("\n=== Test: Double-Click After Transform ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Helper function to calculate point on curve at t=0.5
    def get_curve_midpoint(arc_obj):
        if hasattr(arc_obj, 'manual_control_point') and arc_obj.manual_control_point:
            cp_x, cp_y = arc_obj.manual_control_point
        else:
            control_point = arc_obj._calculate_curve_control_point()
            cp_x, cp_y = control_point
        
        src_x, src_y = arc_obj.source.x, arc_obj.source.y
        tgt_x, tgt_y = arc_obj.target.x, arc_obj.target.y
        t = 0.5
        one_minus_t = 1.0 - t
        curve_x = (one_minus_t * one_minus_t * src_x + 
                   2 * one_minus_t * t * cp_x + 
                   t * t * tgt_x)
        curve_y = (one_minus_t * one_minus_t * src_y + 
                   2 * one_minus_t * t * cp_y + 
                   t * t * tgt_y)
        return (curve_x, curve_y)
    
    # First transformation
    print("\nFirst transformation:")
    selection_mgr = SelectionManager()
    handler1 = ArcTransformHandler(selection_mgr)
    
    # Start first transform
    handler1.start_transform(arc, 'midpoint', 200, 100)
    handler1.update_transform(200, 150)  # Drag to new position
    handler1.end_transform()
    
    first_manual_point = arc.manual_control_point
    print(f"After first transform, manual control point: {first_manual_point}")
    assert first_manual_point is not None
    
    # Get curve midpoint after first transformation
    curve_mid_1 = get_curve_midpoint(arc)
    mx1, my1 = curve_mid_1
    print(f"Curve midpoint after first transform: ({mx1:.1f}, {my1:.1f})")
    
    # Verify arc is clickable at the curve midpoint
    is_clickable = arc.contains_point(mx1, my1)
    print(f"Arc clickable at curve midpoint: {is_clickable}")
    assert is_clickable, "Arc should be clickable after transformation"
    
    # Second transformation (simulating double-click again)
    print("\nSecond transformation (double-click again):")
    handler2 = ArcTransformHandler(selection_mgr)
    
    # Start second transform (user clicks on the curve)
    handler2.start_transform(arc, 'midpoint', mx1, my1)
    handler2.update_transform(200, 180)  # Drag to another position
    handler2.end_transform()
    
    second_manual_point = arc.manual_control_point
    print(f"After second transform, manual control point: {second_manual_point}")
    assert second_manual_point is not None
    assert second_manual_point != first_manual_point, "Manual point should have changed"
    
    # Get curve midpoint after second transformation
    curve_mid_2 = get_curve_midpoint(arc)
    mx2, my2 = curve_mid_2
    print(f"Curve midpoint after second transform: ({mx2:.1f}, {my2:.1f})")
    
    # Verify arc is clickable at the newest curve midpoint
    is_clickable2 = arc.contains_point(mx2, my2)
    print(f"Arc clickable at new curve midpoint: {is_clickable2}")
    assert is_clickable2, "Arc should be clickable after second transformation"
    
    print("✓ Arc remains editable after transformation!")
    return True


def test_handle_at_curve_extent():
    """Test that handle appears along the curve, not the straight line."""
    print("\n=== Test: Handle at Curve Extent ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Get source and target positions
    src_x, src_y = place.x, place.y
    tgt_x, tgt_y = trans.x, trans.y
    
    # Midpoint between source and target (straight line)
    straight_mid_x = (src_x + tgt_x) / 2
    straight_mid_y = (src_y + tgt_y) / 2
    print(f"Straight line midpoint: ({straight_mid_x}, {straight_mid_y})")
    
    # Get handle position (should be at curve)
    detector = HandleDetector()
    handles = detector.get_handle_positions(arc, zoom=1.0)
    handle_pos = handles.get('midpoint')
    handle_x, handle_y = handle_pos
    print(f"Handle position: ({handle_x}, {handle_y})")
    
    # Handle should NOT be at straight line midpoint (unless degenerate case)
    # For a curved arc, it should be offset perpendicular to the line
    is_at_straight = (abs(handle_x - straight_mid_x) < 0.1 and 
                      abs(handle_y - straight_mid_y) < 0.1)
    
    if not is_at_straight:
        print("✓ Handle is offset from straight line (on the curve)")
    else:
        print("⚠ Handle is at straight line midpoint (might be okay for short arcs)")
    
    # Calculate expected offset for CurvedArc (20% perpendicular)
    dx = tgt_x - src_x
    dy = tgt_y - src_y
    length = (dx * dx + dy * dy) ** 0.5
    expected_offset = length * 0.20  # CURVE_OFFSET_RATIO
    
    # Distance from straight midpoint to handle
    actual_offset = ((handle_x - straight_mid_x) ** 2 + 
                     (handle_y - straight_mid_y) ** 2) ** 0.5
    
    print(f"Expected offset: {expected_offset:.2f}")
    print(f"Actual offset: {actual_offset:.2f}")
    
    # Should be close to expected offset
    assert abs(actual_offset - expected_offset) < 5.0, \
        f"Handle offset {actual_offset:.2f} should be near {expected_offset:.2f}"
    
    print("✓ Handle appears at curve extent, not straight line!")
    return True


if __name__ == '__main__':
    all_pass = True
    
    tests = [
        test_handle_position_after_transform,
        test_contains_point_after_transform,
        test_double_click_after_transform,
        test_handle_at_curve_extent,
    ]
    
    for test_func in tests:
        try:
            all_pass &= test_func()
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            all_pass = False
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            all_pass = False
    
    if all_pass:
        print("\n" + "="*60)
        print("ALL CURVED ARC ISSUE TESTS PASSED!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("SOME TESTS FAILED")
        print("="*60)
        sys.exit(1)
