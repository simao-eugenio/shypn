#!/usr/bin/env python3
"""Comprehensive test for all arc types: transformation and context menu sensitivity."""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.edit.transformation.handle_detector import HandleDetector
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler
from shypn.edit.selection_manager import SelectionManager


def get_curve_midpoint(arc_obj):
    """Helper to calculate point on curve at t=0.5."""
    from shypn.netobjs.curved_arc import CurvedArc
    
    if isinstance(arc_obj, CurvedArc):
        # CurvedArc: check manual first, then automatic
        if hasattr(arc_obj, 'manual_control_point') and arc_obj.manual_control_point:
            cp_x, cp_y = arc_obj.manual_control_point
        else:
            control_point = arc_obj._calculate_curve_control_point()
            cp_x, cp_y = control_point
    elif getattr(arc_obj, 'is_curved', False):
        # Arc with is_curved flag
        src_x, src_y = arc_obj.source.x, arc_obj.source.y
        tgt_x, tgt_y = arc_obj.target.x, arc_obj.target.y
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        cp_x = mid_x + arc_obj.control_offset_x
        cp_y = mid_y + arc_obj.control_offset_y
    else:
        # Straight arc - use midpoint
        src_x, src_y = arc_obj.source.x, arc_obj.source.y
        tgt_x, tgt_y = arc_obj.target.x, arc_obj.target.y
        return ((src_x + tgt_x) / 2, (src_y + tgt_y) / 2)
    
    # Calculate curve midpoint at t=0.5
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


def test_arc_type_transformation(arc_type_name, arc_obj):
    """Test transformation handler for a specific arc type."""
    print(f"\n{'='*60}")
    print(f"Testing: {arc_type_name}")
    print('='*60)
    
    # Test 1: Can transform
    print("\n[Test 1] Can handler transform this arc type?")
    selection_mgr = SelectionManager()
    handler = ArcTransformHandler(selection_mgr)
    can_transform = handler.can_transform(arc_obj)
    print(f"  Result: {can_transform}")
    assert can_transform, f"{arc_type_name} should be transformable"
    
    # Test 2: Handle detection
    print("\n[Test 2] Can detect handle position?")
    detector = HandleDetector()
    handles = detector.get_handle_positions(arc_obj, zoom=1.0)
    has_handle = 'midpoint' in handles
    print(f"  Has midpoint handle: {has_handle}")
    assert has_handle, f"{arc_type_name} should have a midpoint handle"
    handle_pos = handles['midpoint']
    print(f"  Handle position: {handle_pos}")
    
    # Test 3: First transformation
    print("\n[Test 3] First transformation (drag handle)")
    handler1 = ArcTransformHandler(selection_mgr)
    handler1.start_transform(arc_obj, 'midpoint', 200, 100)
    handler1.update_transform(200, 150)  # Drag
    changed1 = handler1.end_transform()
    print(f"  Transformation changed arc: {changed1}")
    assert changed1, f"{arc_type_name} transformation should report changes"
    
    # Test 4: Arc is clickable after transformation
    print("\n[Test 4] Arc clickable after transformation?")
    curve_mid = get_curve_midpoint(arc_obj)
    mx, my = curve_mid
    print(f"  Testing clickability at ({mx:.1f}, {my:.1f})")
    is_clickable = arc_obj.contains_point(mx, my)
    print(f"  Is clickable: {is_clickable}")
    assert is_clickable, f"{arc_type_name} should be clickable after transformation"
    
    # Test 5: Handle position after transformation
    print("\n[Test 5] Handle position after transformation?")
    handles2 = detector.get_handle_positions(arc_obj, zoom=1.0)
    handle_pos2 = handles2.get('midpoint')
    print(f"  New handle position: {handle_pos2}")
    assert handle_pos2 is not None, f"{arc_type_name} should still have handle"
    # Handle should have moved (unless it's a straight arc that didn't curve)
    
    # Test 6: Second transformation (double-click again)
    print("\n[Test 6] Second transformation (double-click sensitivity)")
    handler2 = ArcTransformHandler(selection_mgr)
    handler2.start_transform(arc_obj, 'midpoint', mx, my)
    handler2.update_transform(200, 180)  # Drag further
    changed2 = handler2.end_transform()
    print(f"  Second transformation changed arc: {changed2}")
    # For straight arcs that toggle, this might not change if toggled back
    # For CurvedArc, this should change
    
    # Test 7: Still clickable after second transformation
    print("\n[Test 7] Arc still clickable after second transformation?")
    curve_mid2 = get_curve_midpoint(arc_obj)
    mx2, my2 = curve_mid2
    print(f"  Testing clickability at ({mx2:.1f}, {my2:.1f})")
    is_clickable2 = arc_obj.contains_point(mx2, my2)
    print(f"  Is clickable: {is_clickable2}")
    assert is_clickable2, f"{arc_type_name} should be clickable after second transformation"
    
    print(f"\n✓ {arc_type_name} PASSED all transformation tests!")
    return True


def test_inhibitor_arc_straight():
    """Test straight InhibitorArc transformation."""
    print("\n" + "="*70)
    print("TEST: Straight InhibitorArc")
    print("="*70)
    
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    arc = InhibitorArc(place, trans, id=3, name="I1")
    
    return test_arc_type_transformation("InhibitorArc (straight)", arc)


def test_inhibitor_arc_curved():
    """Test curved InhibitorArc transformation."""
    print("\n" + "="*70)
    print("TEST: Curved InhibitorArc (with is_curved flag)")
    print("="*70)
    
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    arc = InhibitorArc(place, trans, id=3, name="I1")
    
    # Make it curved first
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -30.0
    
    return test_arc_type_transformation("InhibitorArc (curved)", arc)


def test_arc_straight():
    """Test straight Arc transformation."""
    print("\n" + "="*70)
    print("TEST: Straight Arc")
    print("="*70)
    
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    arc = Arc(place, trans, id=3, name="A1")
    
    return test_arc_type_transformation("Arc (straight)", arc)


def test_arc_curved():
    """Test curved Arc transformation."""
    print("\n" + "="*70)
    print("TEST: Curved Arc (with is_curved flag)")
    print("="*70)
    
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    arc = Arc(place, trans, id=3, name="A1")
    
    # Make it curved first
    arc.is_curved = True
    arc.control_offset_x = 0.0
    arc.control_offset_y = -30.0
    
    return test_arc_type_transformation("Arc (curved)", arc)


def test_curved_arc_class():
    """Test CurvedArc class transformation."""
    print("\n" + "="*70)
    print("TEST: CurvedArc (class)")
    print("="*70)
    
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    arc = CurvedArc(place, trans, id=3, name="C1")
    
    return test_arc_type_transformation("CurvedArc (class)", arc)


def test_curved_inhibitor_arc_class():
    """Test CurvedInhibitorArc class transformation."""
    print("\n" + "="*70)
    print("TEST: CurvedInhibitorArc (class)")
    print("="*70)
    
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    arc = CurvedInhibitorArc(place, trans, id=3, name="CI1")
    
    return test_arc_type_transformation("CurvedInhibitorArc (class)", arc)


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("# COMPREHENSIVE ARC TRANSFORMATION TEST SUITE")
    print("#"*70)
    
    all_pass = True
    tests = [
        ("Straight Arc", test_arc_straight),
        ("Curved Arc (is_curved flag)", test_arc_curved),
        ("Straight InhibitorArc", test_inhibitor_arc_straight),
        ("Curved InhibitorArc (is_curved flag)", test_inhibitor_arc_curved),
        ("CurvedArc (class)", test_curved_arc_class),
        ("CurvedInhibitorArc (class)", test_curved_inhibitor_arc_class),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "✓ PASS", None))
        except AssertionError as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            results.append((test_name, "✗ FAIL", str(e)))
            all_pass = False
        except Exception as e:
            print(f"\n✗ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "✗ ERROR", str(e)))
            all_pass = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, status, error in results:
        print(f"{status} {test_name}")
        if error:
            print(f"    {error}")
    
    if all_pass:
        print("\n" + "="*70)
        print("ALL TESTS PASSED! 🎉")
        print("="*70)
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("SOME TESTS FAILED")
        print("="*70)
        sys.exit(1)
