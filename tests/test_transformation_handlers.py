#!/usr/bin/env python3
"""
Test script for transformation handlers.

Tests the basic functionality of the transformation system:
- HandleDetector position calculations
- ResizeHandler transformation logic
"""

import sys
import math
sys.path.insert(0, 'src')

from shypn.netobjs import Place, Transition
from shypn.edit.transformation.handle_detector import HandleDetector
from shypn.edit.transformation.resize_handler import ResizeHandler
from shypn.edit.selection_manager import SelectionManager


def test_handle_detector():
    """Test HandleDetector calculations."""
    print("=" * 60)
    print("Testing HandleDetector")
    print("=" * 60)
    
    detector = HandleDetector()
    
    # Test Place handle positions
    place = Place(id=1, x=100, y=100, name="P1")
    place.radius = 20
    
    positions = detector.get_handle_positions(place, zoom=1.0)
    print(f"\nPlace at (100, 100) with radius 20:")
    print(f"  Handle positions: {len(positions)} handles")
    
    # Verify handle positions are at radius distance
    for handle_name, (hx, hy) in positions.items():
        dist = math.sqrt((hx - place.x)**2 + (hy - place.y)**2)
        print(f"  {handle_name}: ({hx:.1f}, {hy:.1f}) - distance: {dist:.1f}")
        assert abs(dist - place.radius) < 0.1, f"Handle {handle_name} not at correct distance"
    
    # Test Transition handle positions
    transition = Transition(id=2, x=200, y=200, name="T1", horizontal=True)
    transition.width = 60
    transition.height = 30
    
    positions = detector.get_handle_positions(transition, zoom=1.0)
    print(f"\nTransition at (200, 200) with width=60, height=30:")
    print(f"  Handle positions: {len(positions)} handles")
    
    for handle_name, (hx, hy) in positions.items():
        print(f"  {handle_name}: ({hx:.1f}, {hy:.1f})")
    
    # Verify corner positions
    assert positions['nw'] == (200 - 30, 200 - 15), "NW corner incorrect"
    assert positions['se'] == (200 + 30, 200 + 15), "SE corner incorrect"
    
    # Test handle detection
    print("\nTesting handle detection:")
    
    # Click near north handle of place
    north_pos = positions_place = detector.get_handle_positions(place, zoom=1.0)
    north_x, north_y = positions_place['n']
    detected = detector.detect_handle_at_position(place, north_x, north_y, zoom=1.0)
    print(f"  Click at north handle: detected '{detected}'")
    assert detected == 'n', f"Expected 'n', got '{detected}'"
    
    # Click away from handles
    detected = detector.detect_handle_at_position(place, 50, 50, zoom=1.0)
    print(f"  Click away from handles: detected '{detected}'")
    assert detected is None, f"Expected None, got '{detected}'"
    
    print("\n✓ HandleDetector tests passed!")


def test_resize_handler():
    """Test ResizeHandler transformations."""
    print("\n" + "=" * 60)
    print("Testing ResizeHandler")
    print("=" * 60)
    
    selection_manager = SelectionManager()
    handler = ResizeHandler(selection_manager)
    
    # Test Place resize
    place = Place(id=1, x=100, y=100, name="P1")
    place.radius = 20
    original_radius = place.radius
    
    print(f"\nTest 1: Resize Place")
    print(f"  Original radius: {original_radius}")
    
    assert handler.can_transform(place), "Handler should support Place"
    
    # Start resize from east handle
    handler.start_transform(place, 'e', 120, 100)
    assert handler.is_transforming(), "Should be transforming"
    
    # Drag to the right (increase radius)
    handler.update_transform(130, 100)  # 10 units to the right
    print(f"  After dragging right 10 units: radius = {place.radius:.1f}")
    assert place.radius > original_radius, "Radius should increase"
    
    # End transformation
    result = handler.end_transform()
    assert result, "Transformation should succeed"
    assert not handler.is_transforming(), "Should not be transforming anymore"
    
    # Test Transition resize
    transition = Transition(id=2, x=200, y=200, name="T1", horizontal=True)
    transition.width = 60
    transition.height = 30
    original_width = transition.width
    original_height = transition.height
    
    print(f"\nTest 2: Resize Transition (horizontal)")
    print(f"  Original dimensions: {original_width} x {original_height}")
    
    assert handler.can_transform(transition), "Handler should support Transition"
    
    # Start resize from east handle (should only affect width)
    handler.start_transform(transition, 'e', 230, 200)
    
    # Drag to the right
    handler.update_transform(250, 200)  # 20 units to the right
    print(f"  After dragging east handle right 20 units:")
    print(f"    Width: {transition.width:.1f} (original: {original_width})")
    print(f"    Height: {transition.height:.1f} (original: {original_height})")
    
    assert transition.width > original_width, "Width should increase"
    assert abs(transition.height - original_height) < 0.1, "Height should not change"
    
    handler.end_transform()
    
    # Test corner resize (both dimensions)
    transition.width = original_width
    transition.height = original_height
    
    print(f"\nTest 3: Resize Transition corner (both dimensions)")
    handler.start_transform(transition, 'se', 230, 215)
    handler.update_transform(250, 230)  # 20 units right, 15 units down
    print(f"  After dragging SE corner:")
    print(f"    Width: {transition.width:.1f}")
    print(f"    Height: {transition.height:.1f}")
    
    assert transition.width > original_width, "Width should increase"
    assert transition.height > original_height, "Height should increase"
    
    handler.end_transform()
    
    # Test cancel
    print(f"\nTest 4: Cancel transformation")
    original_w = transition.width
    handler.start_transform(transition, 'e', 230, 200)
    handler.update_transform(300, 200)  # Big change
    print(f"  Before cancel: width = {transition.width:.1f}")
    
    handler.cancel_transform()
    print(f"  After cancel: width = {transition.width:.1f}")
    assert abs(transition.width - original_w) < 0.1, "Width should be restored"
    
    print("\n✓ ResizeHandler tests passed!")


def test_constraints():
    """Test size constraints."""
    print("\n" + "=" * 60)
    print("Testing Size Constraints")
    print("=" * 60)
    
    selection_manager = SelectionManager()
    handler = ResizeHandler(selection_manager)
    
    # Test minimum Place radius
    place = Place(id=1, x=100, y=100, name="P1")
    place.radius = 15  # Close to minimum
    
    handler.start_transform(place, 'e', 115, 100)
    handler.update_transform(80, 100)  # Try to make it very small
    
    print(f"\nPlace radius after trying to shrink below minimum: {place.radius:.1f}")
    assert place.radius >= ResizeHandler.MIN_PLACE_RADIUS, \
        f"Radius should not go below {ResizeHandler.MIN_PLACE_RADIUS}"
    
    handler.end_transform()
    
    # Test maximum Place radius
    place.radius = 95  # Close to maximum
    
    handler.start_transform(place, 'e', 195, 100)
    handler.update_transform(250, 100)  # Try to make it very large
    
    print(f"Place radius after trying to exceed maximum: {place.radius:.1f}")
    assert place.radius <= ResizeHandler.MAX_PLACE_RADIUS, \
        f"Radius should not exceed {ResizeHandler.MAX_PLACE_RADIUS}"
    
    handler.end_transform()
    
    print("\n✓ Constraint tests passed!")


if __name__ == '__main__':
    try:
        test_handle_detector()
        test_resize_handler()
        test_constraints()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nTransformation system is ready for manual testing.")
        print("Launch the application and try:")
        print("  1. Double-click a Place or Transition to enter edit mode")
        print("  2. Drag the handles to resize")
        print("  3. Press ESC to cancel a resize operation")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
