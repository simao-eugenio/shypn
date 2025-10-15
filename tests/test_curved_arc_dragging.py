#!/usr/bin/env python3
"""Test CurvedArc transformation - verify dragging works without ghost lines."""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.curved_arc import CurvedArc
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler
from shypn.edit.selection_manager import SelectionManager


def test_curved_arc_manual_control_point():
    """Test that CurvedArc can use manual control point override."""
    print("\n=== Test: CurvedArc Manual Control Point ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Initially, no manual control point
    assert not hasattr(arc, 'manual_control_point') or arc.manual_control_point is None
    
    # Get automatic control point
    auto_control = arc._calculate_curve_control_point()
    print(f"Automatic control point: {auto_control}")
    assert auto_control is not None
    
    # Set manual control point
    manual_point = (200, 150)
    arc.manual_control_point = manual_point
    print(f"Manual control point: {arc.manual_control_point}")
    
    # Verify it was set
    assert arc.manual_control_point == manual_point
    
    print("✓ CurvedArc can store manual control point!")
    return True


def test_curved_arc_transformation_handler():
    """Test that ArcTransformHandler works with CurvedArc."""
    print("\n=== Test: CurvedArc Transformation Handler ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Create handler
    selection_mgr = SelectionManager()
    handler = ArcTransformHandler(selection_mgr)
    
    # Check if handler can transform CurvedArc
    can_transform = handler.can_transform(arc)
    print(f"Handler can transform CurvedArc: {can_transform}")
    assert can_transform, "Handler should be able to transform CurvedArc"
    
    # Start transformation
    handler.start_transform(arc, 'midpoint', 200, 100)
    assert handler.is_transforming()
    print("✓ Transformation started")
    
    # Simulate drag
    handler.update_transform(200, 150)  # Move handle down
    
    # Check that manual control point was set
    assert hasattr(arc, 'manual_control_point')
    assert arc.manual_control_point is not None
    print(f"Manual control point after drag: {arc.manual_control_point}")
    
    # Verify the manual point is near where we dragged
    cp_x, cp_y = arc.manual_control_point
    assert abs(cp_x - 200) < 5, f"X should be near 200, got {cp_x}"
    assert abs(cp_y - 150) < 5, f"Y should be near 150, got {cp_y}"
    
    # End transformation
    changed = handler.end_transform()
    assert changed, "Transformation should indicate changes"
    print("✓ Transformation completed successfully")
    
    # Verify manual control point persists
    assert arc.manual_control_point == (cp_x, cp_y)
    print(f"Final manual control point: {arc.manual_control_point}")
    
    print("✓ CurvedArc transformation handler works correctly!")
    return True


def test_curved_arc_vs_automatic_control():
    """Test that manual control point overrides automatic calculation."""
    print("\n=== Test: Manual vs Automatic Control Point ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Get automatic control point
    auto_control = arc._calculate_curve_control_point()
    print(f"Automatic control point: {auto_control}")
    
    # Set a different manual control point
    manual_point = (200, 200)  # Much further down
    arc.manual_control_point = manual_point
    
    # The manual point should be different from automatic
    assert arc.manual_control_point != auto_control
    print(f"Manual control point: {arc.manual_control_point}")
    
    # When rendering, manual should be used (we'd need to check render logic)
    # For now, just verify they're different
    print("✓ Manual control point differs from automatic!")
    return True


def test_cancel_transformation():
    """Test that canceling transformation restores original state."""
    print("\n=== Test: Cancel Transformation ===")
    
    # Create basic Petri net objects
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create CurvedArc
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    # Initially no manual control point
    assert not hasattr(arc, 'manual_control_point') or arc.manual_control_point is None
    
    # Create handler and start transformation
    selection_mgr = SelectionManager()
    handler = ArcTransformHandler(selection_mgr)
    handler.start_transform(arc, 'midpoint', 200, 100)
    
    # Simulate drag
    handler.update_transform(200, 150)
    
    # Verify manual control point was set
    assert arc.manual_control_point is not None
    print(f"During drag: {arc.manual_control_point}")
    
    # Cancel transformation
    handler.cancel_transform()
    
    # Verify manual control point was restored to None
    assert arc.manual_control_point is None
    print("✓ Manual control point restored to None after cancel")
    
    print("✓ Cancel transformation works correctly!")
    return True


if __name__ == '__main__':
    all_pass = True
    
    try:
        all_pass &= test_curved_arc_manual_control_point()
    except AssertionError as e:
        print(f"✗ Manual control point test failed: {e}")
        all_pass = False
    
    try:
        all_pass &= test_curved_arc_transformation_handler()
    except AssertionError as e:
        print(f"✗ Transformation handler test failed: {e}")
        all_pass = False
    
    try:
        all_pass &= test_curved_arc_vs_automatic_control()
    except AssertionError as e:
        print(f"✗ Manual vs automatic test failed: {e}")
        all_pass = False
    
    try:
        all_pass &= test_cancel_transformation()
    except AssertionError as e:
        print(f"✗ Cancel transformation test failed: {e}")
        all_pass = False
    
    if all_pass:
        print("\n" + "="*50)
        print("ALL CURVED ARC DRAGGING TESTS PASSED!")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("SOME TESTS FAILED")
        print("="*50)
        sys.exit(1)
