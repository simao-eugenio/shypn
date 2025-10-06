#!/usr/bin/env python3
"""
Test arc transformation handlers.

Tests the arc curve/straight transformation functionality.
"""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs import Place, Transition, Arc
from shypn.edit.transformation.handle_detector import HandleDetector
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler
from shypn.edit.selection_manager import SelectionManager


def test_arc_handle_detection():
    """Test that HandleDetector calculates arc handle positions correctly."""
    print("\n" + "="*60)
    print("Testing Arc Handle Detection")
    print("="*60)
    
    # Create test objects (Place → Transition for bipartite property)
    place1 = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=200, id=2, name="T1", width=40, height=20)
    arc = Arc(source=place1, target=transition, id=1, name="A1")
    
    detector = HandleDetector()
    
    # Test straight arc handle positions
    positions = detector.get_handle_positions(arc, zoom=1.0)
    print(f"\nStraight arc (P1→T1):")
    print(f"  Source: ({place1.x}, {place1.y})")
    print(f"  Target: ({transition.x}, {transition.y})")
    print(f"  Handle positions: {positions}")
    
    assert 'midpoint' in positions, "Should have midpoint handle"
    
    # Check handle is near midpoint
    hx, hy = positions['midpoint']
    mid_x = (place1.x + transition.x) / 2
    mid_y = (place1.y + transition.y) / 2
    print(f"  Expected midpoint: ({mid_x}, {mid_y})")
    print(f"  Handle at: ({hx:.1f}, {hy:.1f})")
    
    # Test curved arc handle positions
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -30.0
    
    positions = detector.get_handle_positions(arc, zoom=1.0)
    print(f"\nCurved arc:")
    print(f"  Control offset: ({arc.control_offset_x}, {arc.control_offset_y})")
    print(f"  Handle positions: {positions}")
    
    hx, hy = positions['midpoint']
    print(f"  Handle at: ({hx:.1f}, {hy:.1f})")
    print(f"  Expected: ({mid_x}, {mid_y - 30})")
    
    # Test handle detection
    print("\nTesting handle detection:")
    detected = detector.detect_handle_at_position(arc, hx, hy, zoom=1.0)
    print(f"  Click at handle position: detected '{detected}'")
    assert detected == 'midpoint', f"Expected 'midpoint', got '{detected}'"
    
    print("\n✓ Arc handle detection tests passed!")


def test_arc_transform_handler():
    """Test ArcTransformHandler."""
    print("\n" + "=" * 60)
    print("Testing Arc Transform Handler")
    print("=" * 60)
    
    selection_manager = SelectionManager()
    handler = ArcTransformHandler(selection_manager)
    
    # Create arc (Place → Transition for bipartite property)
    place = Place(id=1, x=100, y=100, name="P1")
    transition = Transition(id=2, x=200, y=100, name="T1", width=40, height=20)
    arc = Arc(source=place, target=transition, id=1, name="A1")
    
    assert not arc.is_curved, "Arc should start straight"
    
    print(f"\nTest 1: Toggle straight to curved")
    print(f"  Initial state: is_curved = {arc.is_curved}")
    
    assert handler.can_transform(arc), "Handler should support Arc"
    
    # Start transformation (click on handle)
    handler.start_transform(arc, 'midpoint', 150, 100)
    assert handler.is_transforming(), "Should be transforming"
    
    # End without dragging (toggle)
    result = handler.end_transform()
    print(f"  After toggle: is_curved = {arc.is_curved}")
    assert arc.is_curved, "Arc should be curved after toggle"
    assert result, "Transformation should succeed"
    
    print(f"\nTest 2: Toggle curved to straight")
    print(f"  Initial state: is_curved = {arc.is_curved}")
    
    handler.start_transform(arc, 'midpoint', 150, 100)
    result = handler.end_transform()
    print(f"  After toggle: is_curved = {arc.is_curved}")
    assert not arc.is_curved, "Arc should be straight after toggle"
    
    print(f"\nTest 3: Drag to adjust curve")
    arc.is_curved = False
    print(f"  Initial state: is_curved = {arc.is_curved}")
    
    handler.start_transform(arc, 'midpoint', 150, 100)
    
    # Simulate drag
    handler.update_transform(150, 80)  # Drag 20 units up
    print(f"  After drag: is_curved = {arc.is_curved}")
    print(f"  Control offset: ({arc.control_offset_x:.1f}, {arc.control_offset_y:.1f})")
    
    assert arc.is_curved, "Arc should become curved when dragged"
    assert arc.control_offset_y < 0, "Should have negative Y offset (dragged up)"
    
    handler.end_transform()
    
    print(f"\nTest 4: Cancel transformation")
    original_curved = arc.is_curved
    print(f"  Initial state: is_curved = {original_curved}")
    
    handler.start_transform(arc, 'midpoint', 150, 100)
    handler.update_transform(150, 150)  # Drag down
    print(f"  During drag: is_curved = {arc.is_curved}")
    
    handler.cancel_transform()
    print(f"  After cancel: is_curved = {arc.is_curved}")
    assert arc.is_curved == original_curved, "Should restore original state"
    
    print("\n✓ Arc transform handler tests passed!")


if __name__ == '__main__':
    try:
        test_arc_handle_detection()
        test_arc_transform_handler()
        
        print("\n" + "=" * 60)
        print("ALL ARC TESTS PASSED!")
        print("=" * 60)
        print("\nArc transformation system is ready.")
        print("Try in the application:")
        print("  1. Create an arc between two objects")
        print("  2. Double-click the arc to enter edit mode")
        print("  3. Click the handle to toggle straight/curved")
        print("  4. Drag the handle to adjust curve")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
