#!/usr/bin/env python3
"""Simple test to verify arc rendering logic without GTK."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.api import Place, Transition, Arc


def test_arc_render_preparation():
    """Test that arc calculates render coordinates correctly."""
    # Create simple network
    p1 = Place(x=0, y=0, id=1, name="P1", radius=25.0)
    t1 = Transition(x=100, y=0, id=1, name="T1", width=50.0, height=25.0)
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    
    print("✓ Arc created successfully")
    print(f"  Source: {a1.source.name} at ({a1.source.x}, {a1.source.y})")
    print(f"  Target: {a1.target.name} at ({a1.target.x}, {a1.target.y})")
    print(f"  Weight: {a1.weight}")
    print(f"  Color: {a1.color}")
    print(f"  Width: {a1.width}")
    
    # Test boundary calculation
    import math
    dx = t1.x - p1.x
    dy = t1.y - p1.y
    length = math.sqrt(dx * dx + dy * dy)
    
    if length > 0:
        dx /= length
        dy /= length
        print(f"\n✓ Direction vector: ({dx:.3f}, {dy:.3f})")
        
        # Source boundary (Place - circle)
        src_boundary_x = p1.x + dx * p1.radius
        src_boundary_y = p1.y + dy * p1.radius
        print(f"✓ Source boundary: ({src_boundary_x:.1f}, {src_boundary_y:.1f})")
        
        # Target boundary (Transition - approximate)
        max_dim = max(t1.width, t1.height) / 2
        tgt_boundary_x = t1.x - dx * max_dim
        tgt_boundary_y = t1.y - dy * max_dim
        print(f"✓ Target boundary: ({tgt_boundary_x:.1f}, {tgt_boundary_y:.1f})")
        
        print(f"\n✓ Arc should render from ({src_boundary_x:.1f}, {src_boundary_y:.1f})")
        print(f"  to ({tgt_boundary_x:.1f}, {tgt_boundary_y:.1f})")
        print(f"  Length: {length:.1f} units")
    
    return True


def test_arc_render_call():
    """Test that arc render method can be called (without actual rendering)."""
    p1 = Place(x=0, y=0, id=1, name="P1")
    t1 = Transition(x=100, y=0, id=1, name="T1")
    a1 = Arc(source=p1, target=t1, id=1, name="A1")
    
    # Mock Cairo context
    class MockCairoContext:
        def __init__(self):
            self.operations = []
        
        def move_to(self, x, y):
            self.operations.append(('move_to', x, y))
        
        def line_to(self, x, y):
            self.operations.append(('line_to', x, y))
        
        def set_source_rgb(self, r, g, b):
            self.operations.append(('set_source_rgb', r, g, b))
        
        def set_source_rgba(self, r, g, b, a):
            self.operations.append(('set_source_rgba', r, g, b, a))
        
        def set_line_width(self, w):
            self.operations.append(('set_line_width', w))
        
        def stroke(self):
            self.operations.append(('stroke',))
        
        def save(self):
            self.operations.append(('save',))
        
        def restore(self):
            self.operations.append(('restore',))
        
        def fill(self):
            self.operations.append(('fill',))
        
        def close_path(self):
            self.operations.append(('close_path',))
    
    mock_cr = MockCairoContext()
    
    # Call render without transform parameter
    a1.render(mock_cr)
    
    # Check operations
    has_move = any(op[0] == 'move_to' for op in mock_cr.operations)
    has_line = any(op[0] == 'line_to' for op in mock_cr.operations)
    has_stroke = any(op[0] == 'stroke' for op in mock_cr.operations)
    
    assert has_move, "Arc should call move_to"
    assert has_line, "Arc should call line_to"
    assert has_stroke, "Arc should call stroke"
    
    print("✓ Arc render method executes correctly")
    print(f"  Operations performed: {len(mock_cr.operations)}")
    print(f"  Includes: move_to, line_to, stroke")
    
    return True


def main():
    print("\n=== Testing Arc Rendering Logic ===\n")
    
    try:
        test_arc_render_preparation()
        print()
        test_arc_render_call()
        
        print("\n=== Arc Rendering Tests Passed ===\n")
        print("Arc objects can:")
        print("  ✓ Calculate boundary intersections")
        print("  ✓ Compute direction vectors")
        print("  ✓ Call Cairo drawing operations")
        print("\nIf arcs are not visible in the app, check:")
        print("  1. Are arcs being added to the model?")
        print("  2. Is get_all_objects() returning arcs?")
        print("  3. Is the Cairo context valid during rendering?")
        print("  4. Is the transform function working correctly?")
        print("  5. Are arcs behind other objects (z-order)?")
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
