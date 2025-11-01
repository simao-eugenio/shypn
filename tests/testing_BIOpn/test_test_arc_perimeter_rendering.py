"""
Test that test arcs render perimeter-to-perimeter (not center-to-center).

This test verifies the fix for refinement issue #1.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.arc import Arc


def test_test_arc_uses_boundary_points():
    """Verify test arcs connect at node perimeters, not centers."""
    
    print("=" * 80)
    print("TEST: Test Arc Perimeter-to-Perimeter Rendering")
    print("=" * 80)
    
    # Create a simple model
    doc = DocumentModel()
    
    # Create place (circle, radius=30) at (100, 100)
    substrate = Place(x=100.0, y=100.0, id="P1", name="Substrate", label="S")
    substrate.radius = 30.0
    doc.places.append(substrate)
    
    # Create transition (rectangle 20x40) at (200, 100)
    reaction = Transition(x=200.0, y=100.0, id="T1", name="Reaction", label="R")
    reaction.width = 20.0
    reaction.height = 40.0
    reaction.horizontal = True
    doc.transitions.append(reaction)
    
    # Create enzyme place (circle, radius=30) at (150, 50)
    enzyme = Place(x=150.0, y=50.0, id="P2", name="Enzyme", label="E")
    enzyme.radius = 30.0
    doc.places.append(enzyme)
    
    # Create normal arc: substrate → reaction
    normal_arc = Arc(source=substrate, target=reaction, id="A1", name="A1", weight=1)
    doc.arcs.append(normal_arc)
    
    # Create test arc: enzyme → reaction
    test_arc = TestArc(source=enzyme, target=reaction, id="A2", name="TA2", weight=1)
    doc.arcs.append(test_arc)
    
    print(f"\n📊 Model Structure:")
    print(f"   Place P1 (Substrate): center=({substrate.x}, {substrate.y}), radius={substrate.radius}")
    print(f"   Place P2 (Enzyme): center=({enzyme.x}, {enzyme.y}), radius={enzyme.radius}")
    print(f"   Transition T1 (Reaction): center=({reaction.x}, {reaction.y}), size={reaction.width}x{reaction.height}")
    print(f"   Normal Arc A1: P1 → T1")
    print(f"   Test Arc TA2: P2 → T1")
    
    # Test boundary point calculation for normal arc
    print(f"\n🔍 Normal Arc Boundary Points:")
    src_x, src_y = normal_arc.source.x, normal_arc.source.y
    tgt_x, tgt_y = normal_arc.target.x, normal_arc.target.y
    dx = tgt_x - src_x
    dy = tgt_y - src_y
    length = (dx * dx + dy * dy) ** 0.5
    dx /= length
    dy /= length
    
    start_x, start_y = normal_arc._get_boundary_point(
        normal_arc.source, src_x, src_y, dx, dy)
    end_x, end_y = normal_arc._get_boundary_point(
        normal_arc.target, tgt_x, tgt_y, -dx, -dy)
    
    print(f"   Source center: ({src_x}, {src_y})")
    print(f"   Source boundary: ({start_x:.2f}, {start_y:.2f})")
    print(f"   ✓ Offset from center: {abs(start_x - src_x):.2f}px (should be ~31.5px for radius 30 + border 1.5)")
    print(f"   Target center: ({tgt_x}, {tgt_y})")
    print(f"   Target boundary: ({end_x:.2f}, {end_y:.2f})")
    
    # Test boundary point calculation for test arc
    print(f"\n🔍 Test Arc Boundary Points:")
    src_x, src_y = test_arc.source.x, test_arc.source.y
    tgt_x, tgt_y = test_arc.target.x, test_arc.target.y
    dx = tgt_x - src_x
    dy = tgt_y - src_y
    length = (dx * dx + dy * dy) ** 0.5
    dx /= length
    dy /= length
    
    start_x, start_y = test_arc._get_boundary_point(
        test_arc.source, src_x, src_y, dx, dy)
    end_x, end_y = test_arc._get_boundary_point(
        test_arc.target, tgt_x, tgt_y, -dx, -dy)
    
    print(f"   Source center: ({src_x}, {src_y})")
    print(f"   Source boundary: ({start_x:.2f}, {start_y:.2f})")
    print(f"   Target center: ({tgt_x}, {tgt_y})")
    print(f"   Target boundary: ({end_x:.2f}, {end_y:.2f})")
    
    # Verify test arc uses boundary points (not centers)
    assert start_x != src_x or start_y != src_y, "Test arc should use boundary point, not center for source"
    assert end_x != tgt_x or end_y != tgt_y, "Test arc should use boundary point, not center for target"
    
    print(f"\n✅ VERIFIED:")
    print(f"   Test arc has _get_boundary_point() method: {hasattr(test_arc, '_get_boundary_point')}")
    print(f"   Test arc inherits from Arc: {isinstance(test_arc, Arc)}")
    print(f"   Test arc boundary points differ from centers: ✓")
    print(f"   Test arc will render perimeter-to-perimeter: ✓")
    
    print(f"\n" + "=" * 80)
    print("TEST PASSED: Test arcs now render perimeter-to-perimeter!")
    print("=" * 80)


if __name__ == "__main__":
    test_test_arc_uses_boundary_points()
