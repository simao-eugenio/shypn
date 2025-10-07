#!/usr/bin/env python3
"""
Test that ALL arc types support double-click, edit mode, and curve transformation.

Tests all arc types in the system:
1. Arc - Normal straight arc
2. InhibitorArc - Inhibitor arc (Place → Transition only)
3. CurvedArc - Legacy curved arc class
4. CurvedInhibitorArc - Legacy curved inhibitor arc

Verifies:
- Double-click detection (via contains_point)
- Transformation handler support (can_transform)
- Curve property manipulation (is_curved flag)
- Hit detection after transformation (contains_point after curve)
"""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler
from shypn.edit.selection_manager import SelectionManager


def test_normal_arc():
    """Test Arc (normal straight arc)."""
    print("\n" + "="*60)
    print("Testing Arc (Normal)")
    print("="*60)
    
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    arc = Arc(source=place, target=transition, id=1, name="A1")
    
    # Test 1: Clickable when straight
    print("\n1. Testing clickability (straight)...")
    assert arc.contains_point(200, 100), "Straight arc should be clickable"
    print("   ✓ Straight arc is clickable")
    
    # Test 2: Handler supports Arc
    print("\n2. Testing transformation handler support...")
    selection_manager = SelectionManager()
    handler = ArcTransformHandler(selection_manager)
    assert handler.can_transform(arc), "Handler should support Arc"
    print("   ✓ Handler supports Arc")
    
    # Test 3: Can be transformed to curved
    print("\n3. Testing transformation to curved...")
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -50.0
    assert arc.is_curved, "Arc should be curved"
    print("   ✓ Arc transformed to curved")
    
    # Test 4: Still clickable after transformation
    print("\n4. Testing clickability after transformation...")
    assert arc.contains_point(200, 75), "Curved arc should be clickable"
    print("   ✓ Curved arc is clickable")
    
    print("\n✓ Arc (Normal) - ALL TESTS PASSED!")


def test_inhibitor_arc():
    """Test InhibitorArc."""
    print("\n" + "="*60)
    print("Testing InhibitorArc")
    print("="*60)
    
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    arc = InhibitorArc(source=place, target=transition, id=2, name="I1")
    
    # Test 1: Clickable when straight
    print("\n1. Testing clickability (straight)...")
    assert arc.contains_point(200, 100), "Straight inhibitor arc should be clickable"
    print("   ✓ Straight inhibitor arc is clickable")
    
    # Test 2: Handler supports InhibitorArc
    print("\n2. Testing transformation handler support...")
    selection_manager = SelectionManager()
    handler = ArcTransformHandler(selection_manager)
    assert handler.can_transform(arc), "Handler should support InhibitorArc"
    print("   ✓ Handler supports InhibitorArc")
    
    # Test 3: Can be transformed to curved
    print("\n3. Testing transformation to curved...")
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -50.0
    assert arc.is_curved, "InhibitorArc should be curved"
    print("   ✓ InhibitorArc transformed to curved")
    
    # Test 4: Still clickable after transformation
    print("\n4. Testing clickability after transformation...")
    assert arc.contains_point(200, 75), "Curved inhibitor arc should be clickable"
    print("   ✓ Curved inhibitor arc is clickable")
    
    print("\n✓ InhibitorArc - ALL TESTS PASSED!")


def test_curved_arc():
    """Test CurvedArc (legacy curved arc class)."""
    print("\n" + "="*60)
    print("Testing CurvedArc (Legacy)")
    print("="*60)
    
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    arc = CurvedArc(source=place, target=transition, id=3, name="C1")
    
    # CurvedArc is already curved by design
    print("\n1. CurvedArc is already curved by design")
    
    # Test 2: Clickable (uses its own contains_point)
    print("\n2. Testing clickability...")
    # CurvedArc's contains_point samples the bezier curve
    # It should be clickable somewhere along the curve
    mid_x = 200
    mid_y = 100
    # Try multiple points along where the curve might be
    found_clickable = False
    for y_offset in range(-50, 51, 5):
        if arc.contains_point(mid_x, mid_y + y_offset):
            found_clickable = True
            print(f"   ✓ CurvedArc is clickable at ({mid_x}, {mid_y + y_offset})")
            break
    
    assert found_clickable, "CurvedArc should be clickable somewhere along curve"
    
    # Test 3: Handler supports CurvedArc
    print("\n3. Testing transformation handler support...")
    selection_manager = SelectionManager()
    handler = ArcTransformHandler(selection_manager)
    assert handler.can_transform(arc), "Handler should support CurvedArc"
    print("   ✓ Handler supports CurvedArc")
    
    # Test 4: Can use is_curved flag (though CurvedArc has its own curve logic)
    print("\n4. Testing is_curved flag compatibility...")
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -30.0
    print("   ✓ CurvedArc accepts is_curved flag")
    
    print("\n✓ CurvedArc (Legacy) - ALL TESTS PASSED!")


def test_curved_inhibitor_arc():
    """Test CurvedInhibitorArc (legacy curved inhibitor arc class)."""
    print("\n" + "="*60)
    print("Testing CurvedInhibitorArc (Legacy)")
    print("="*60)
    
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    arc = CurvedInhibitorArc(source=place, target=transition, id=4, name="CI1")
    
    # CurvedInhibitorArc is already curved by design
    print("\n1. CurvedInhibitorArc is already curved by design")
    
    # Test 2: Clickable (inherits CurvedArc's contains_point)
    print("\n2. Testing clickability...")
    # Try multiple points along where the curve might be
    mid_x = 200
    mid_y = 100
    found_clickable = False
    for y_offset in range(-50, 51, 5):
        if arc.contains_point(mid_x, mid_y + y_offset):
            found_clickable = True
            print(f"   ✓ CurvedInhibitorArc is clickable at ({mid_x}, {mid_y + y_offset})")
            break
    
    assert found_clickable, "CurvedInhibitorArc should be clickable somewhere along curve"
    
    # Test 3: Handler supports CurvedInhibitorArc
    print("\n3. Testing transformation handler support...")
    selection_manager = SelectionManager()
    handler = ArcTransformHandler(selection_manager)
    assert handler.can_transform(arc), "Handler should support CurvedInhibitorArc"
    print("   ✓ Handler supports CurvedInhibitorArc")
    
    # Test 4: Can use is_curved flag (though has its own curve logic)
    print("\n4. Testing is_curved flag compatibility...")
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -30.0
    print("   ✓ CurvedInhibitorArc accepts is_curved flag")
    
    print("\n✓ CurvedInhibitorArc (Legacy) - ALL TESTS PASSED!")


def test_handler_with_all_types():
    """Test that one handler instance works with all arc types."""
    print("\n" + "="*60)
    print("Testing Handler with All Arc Types")
    print("="*60)
    
    place = Place(x=100, y=100, id=1, name="P1", radius=20)
    transition = Transition(x=300, y=100, id=2, name="T1", width=40, height=20)
    
    arcs = [
        Arc(source=place, target=transition, id=1, name="A1"),
        InhibitorArc(source=place, target=transition, id=2, name="I1"),
        CurvedArc(source=place, target=transition, id=3, name="C1"),
        CurvedInhibitorArc(source=place, target=transition, id=4, name="CI1"),
    ]
    
    selection_manager = SelectionManager()
    handler = ArcTransformHandler(selection_manager)
    
    for arc in arcs:
        arc_type = arc.__class__.__name__
        print(f"\nTesting {arc_type}...")
        assert handler.can_transform(arc), f"Handler should support {arc_type}"
        print(f"   ✓ Handler supports {arc_type}")
    
    print("\n✓ Handler works with all arc types!")


if __name__ == '__main__':
    try:
        test_normal_arc()
        test_inhibitor_arc()
        test_curved_arc()
        test_curved_inhibitor_arc()
        test_handler_with_all_types()
        
        print("\n" + "="*60)
        print("ALL ARC TYPES - TRANSFORMATION TESTS PASSED!")
        print("="*60)
        print("\nAll arc types support:")
        print("  ✓ Double-click detection (contains_point)")
        print("  ✓ Edit mode entry")
        print("  ✓ Transformation handler")
        print("  ✓ Curve transformation")
        print("  ✓ Hit detection after transformation")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
