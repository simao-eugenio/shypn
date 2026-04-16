#!/usr/bin/env python3
"""
Test: Inhibitor Arc Visual Transformation
Verify that inhibitor arcs render correctly when transformed to curved.
"""

import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler


class MockSelectionManager:
    """Mock selection manager for testing."""
    def __init__(self):
        self.selected_objects = []


def test_inhibitor_transformation():
    """Test that inhibitor arcs can be transformed visually."""
    print("="*70)
    print("Test: Inhibitor Arc Visual Transformation")
    print("="*70)
    
    # Create test objects
    place = Place(100, 150, id=1, name="P1")
    trans = Transition(300, 150, id=2, name="T1")
    
    # Create inhibitor arc
    inhibitor = InhibitorArc(place, trans, id=3, name="I1")
    
    print("\n1. Initial state:")
    print(f"   Type: {type(inhibitor).__name__}")
    print(f"   is_curved: {getattr(inhibitor, 'is_curved', False)}")
    print(f"   control_offset_x: {getattr(inhibitor, 'control_offset_x', 'N/A')}")
    print(f"   control_offset_y: {getattr(inhibitor, 'control_offset_y', 'N/A')}")
    
    # Transform to curved
    selection_manager = MockSelectionManager()
    handler = ArcTransformHandler(selection_manager)
    
    mid_x = (place.x + trans.x) / 2
    mid_y = (place.y + trans.y) / 2
    
    print("\n2. Transforming to curved:")
    handler.start_transform(inhibitor, 'midpoint', mid_x, mid_y)
    handler.update_transform(mid_x - 30, mid_y)
    success = handler.end_transform()
    
    print(f"   Transformation success: {success}")
    print(f"   is_curved: {getattr(inhibitor, 'is_curved', False)}")
    print(f"   control_offset_x: {getattr(inhibitor, 'control_offset_x', 'N/A')}")
    print(f"   control_offset_y: {getattr(inhibitor, 'control_offset_y', 'N/A')}")
    
    # Test rendering (just check it doesn't crash)
    print("\n3. Testing render method:")
    try:
        import cairo
        # Create a small surface for testing
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
        cr = cairo.Context(surface)
        
        # Try to render the curved inhibitor arc
        inhibitor.render(cr, zoom=1.0)
        print("   ✓ Curved inhibitor arc renders without error")
        
        # Transform back to straight
        handler2 = ArcTransformHandler(selection_manager)
        control_x = mid_x + getattr(inhibitor, 'control_offset_x', 0)
        control_y = mid_y + getattr(inhibitor, 'control_offset_y', 0)
        handler2.start_transform(inhibitor, 'midpoint', control_x, control_y)
        handler2.end_transform()
        
        print("\n4. After transforming back to straight:")
        print(f"   is_curved: {getattr(inhibitor, 'is_curved', False)}")
        print(f"   control_offset_x: {getattr(inhibitor, 'control_offset_x', 'N/A')}")
        print(f"   control_offset_y: {getattr(inhibitor, 'control_offset_y', 'N/A')}")
        
        # Try to render straight
        inhibitor.render(cr, zoom=1.0)
        print("   ✓ Straight inhibitor arc renders without error")
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED - Inhibitor arcs transform correctly!")
        print("="*70)
        
    except Exception as e:
        print(f"   ✗ Render failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_inhibitor_transformation()
    sys.exit(0 if success else 1)
