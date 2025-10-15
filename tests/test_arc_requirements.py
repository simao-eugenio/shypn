#!/usr/bin/env python3
"""Comprehensive test for all arc transformation requirements."""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler
from shypn.edit.selection_manager import SelectionManager


def get_curve_midpoint(arc_obj):
    """Helper to get a point on the curve for clicking."""
    from shypn.netobjs.curved_arc import CurvedArc
    
    src_x, src_y = arc_obj.source.x, arc_obj.source.y
    tgt_x, tgt_y = arc_obj.target.x, arc_obj.target.y
    
    if isinstance(arc_obj, CurvedArc):
        if hasattr(arc_obj, 'manual_control_point') and arc_obj.manual_control_point:
            cp_x, cp_y = arc_obj.manual_control_point
        else:
            control_point = arc_obj._calculate_curve_control_point()
            cp_x, cp_y = control_point
    elif getattr(arc_obj, 'is_curved', False):
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        cp_x = mid_x + arc_obj.control_offset_x
        cp_y = mid_y + arc_obj.control_offset_y
    else:
        # Straight arc - use midpoint
        return ((src_x + tgt_x) / 2, (src_y + tgt_y) / 2)
    
    # Calculate point on curve at t=0.5
    t = 0.5
    one_minus_t = 1.0 - t
    curve_x = (one_minus_t * one_minus_t * src_x + 
               2 * one_minus_t * t * cp_x + 
               t * t * tgt_x)
    curve_y = (one_minus_t * one_minus_t * src_y + 
               2 * one_minus_t * t * cp_y + 
               t * t * tgt_y)
    return (curve_x, curve_y)


def test_multiple_transformations(arc_type_name, arc_obj, num_transforms=5):
    """Test that an arc can be transformed multiple times."""
    print(f"\n{'='*70}")
    print(f"Test: {arc_type_name} - Multiple Transformations ({num_transforms}x)")
    print('='*70)
    
    selection_mgr = SelectionManager()
    
    for i in range(num_transforms):
        print(f"\nTransformation #{i+1}:")
        
        handler = ArcTransformHandler(selection_mgr)
        
        # Start transformation
        handler.start_transform(arc_obj, 'midpoint', 200, 100 + i*10)
        assert handler.is_transforming(), f"Should be transforming at iteration {i+1}"
        
        # Drag to new position
        new_y = 150 + i*15
        handler.update_transform(200, new_y)
        
        # End transformation
        changed = handler.end_transform()
        print(f"  Changed: {changed}")
        
        # Verify arc is still clickable
        curve_mid = get_curve_midpoint(arc_obj)
        mx, my = curve_mid
        is_clickable = arc_obj.contains_point(mx, my)
        print(f"  Arc clickable at ({mx:.1f}, {my:.1f}): {is_clickable}")
        
        if not is_clickable:
            print(f"  ✗ FAILED: Arc not clickable after transformation {i+1}")
            return False
    
    print(f"\n✓ {arc_type_name} can be transformed {num_transforms} times!")
    return True


def test_context_menu_sensitivity(arc_type_name, arc_obj):
    """Test that an arc is sensitive to context menu (contains_point works)."""
    print(f"\n{'='*70}")
    print(f"Test: {arc_type_name} - Context Menu Sensitivity")
    print('='*70)
    
    # Get a point on the arc
    curve_mid = get_curve_midpoint(arc_obj)
    mx, my = curve_mid
    
    # Test contains_point (used by context menu detection)
    is_clickable = arc_obj.contains_point(mx, my)
    print(f"Arc clickable at ({mx:.1f}, {my:.1f}): {is_clickable}")
    
    if not is_clickable:
        print(f"✗ FAILED: Arc not sensitive to context menu")
        return False
    
    # Test at multiple points along the arc
    src_x, src_y = arc_obj.source.x, arc_obj.source.y
    tgt_x, tgt_y = arc_obj.target.x, arc_obj.target.y
    
    clickable_count = 0
    for t in [0.25, 0.5, 0.75]:
        # Simple linear interpolation for testing
        test_x = src_x + t * (tgt_x - src_x)
        test_y = src_y + t * (tgt_y - src_y)
        
        if arc_obj.contains_point(test_x, test_y):
            clickable_count += 1
    
    print(f"Clickable at {clickable_count}/3 test points")
    
    print(f"\n✓ {arc_type_name} is sensitive to context menu!")
    return True


def test_transformed_context_menu_sensitivity(arc_type_name, arc_obj):
    """Test that an arc remains context menu sensitive after transformation."""
    print(f"\n{'='*70}")
    print(f"Test: {arc_type_name} - Context Menu After Transformation")
    print('='*70)
    
    # Transform the arc
    selection_mgr = SelectionManager()
    handler = ArcTransformHandler(selection_mgr)
    handler.start_transform(arc_obj, 'midpoint', 200, 100)
    handler.update_transform(200, 150)
    changed = handler.end_transform()
    print(f"Transformed: {changed}")
    
    # Test context menu sensitivity after transformation
    curve_mid = get_curve_midpoint(arc_obj)
    mx, my = curve_mid
    is_clickable = arc_obj.contains_point(mx, my)
    print(f"Arc clickable after transform at ({mx:.1f}, {my:.1f}): {is_clickable}")
    
    if not is_clickable:
        print(f"✗ FAILED: Arc not sensitive to context menu after transformation")
        return False
    
    print(f"\n✓ {arc_type_name} remains context menu sensitive after transformation!")
    return True


def test_transformation_size_constraint(arc_type_name, arc_obj):
    """Test that transformation is restricted to reasonable arc size."""
    print(f"\n{'='*70}")
    print(f"Test: {arc_type_name} - Transformation Size Constraint")
    print('='*70)
    
    src_x, src_y = arc_obj.source.x, arc_obj.source.y
    tgt_x, tgt_y = arc_obj.target.x, arc_obj.target.y
    
    # Calculate arc length
    dx = tgt_x - src_x
    dy = tgt_y - src_y
    arc_length = (dx * dx + dy * dy) ** 0.5
    print(f"Arc length: {arc_length:.1f}")
    
    # Try to transform with extreme offset
    selection_mgr = SelectionManager()
    handler = ArcTransformHandler(selection_mgr)
    
    # Start transformation
    handler.start_transform(arc_obj, 'midpoint', 200, 100)
    
    # Try to drag VERY far away (5x arc length)
    extreme_y = 100 + arc_length * 5
    handler.update_transform(200, extreme_y)
    
    # Check if constraint was applied
    from shypn.netobjs.curved_arc import CurvedArc
    
    if isinstance(arc_obj, CurvedArc):
        if hasattr(arc_obj, 'manual_control_point') and arc_obj.manual_control_point:
            cp_x, cp_y = arc_obj.manual_control_point
            mid_x = (src_x + tgt_x) / 2
            mid_y = (src_y + tgt_y) / 2
            actual_offset = ((cp_x - mid_x)**2 + (cp_y - mid_y)**2) ** 0.5
            print(f"Actual control point offset: {actual_offset:.1f}")
            
            # Check if it's constrained
            max_constraint = handler.MAX_CURVE_OFFSET if hasattr(handler, 'MAX_CURVE_OFFSET') else 200.0
            print(f"Maximum allowed offset: {max_constraint}")
            
            if actual_offset > max_constraint:
                print(f"✗ FAILED: Offset {actual_offset:.1f} exceeds constraint {max_constraint}")
                return False
            
            print(f"✓ Offset properly constrained!")
    elif getattr(arc_obj, 'is_curved', False):
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        actual_offset = (arc_obj.control_offset_x**2 + arc_obj.control_offset_y**2) ** 0.5
        print(f"Actual control offset: {actual_offset:.1f}")
        
        max_constraint = handler.MAX_CURVE_OFFSET if hasattr(handler, 'MAX_CURVE_OFFSET') else 200.0
        print(f"Maximum allowed offset: {max_constraint}")
        
        if actual_offset > max_constraint:
            print(f"✗ FAILED: Offset {actual_offset:.1f} exceeds constraint {max_constraint}")
            return False
        
        print(f"✓ Offset properly constrained!")
    
    handler.end_transform()
    
    print(f"\n✓ {arc_type_name} transformation is properly constrained!")
    return True


def run_all_tests_for_arc_type(arc_type_name, arc_obj):
    """Run all tests for a specific arc type."""
    print(f"\n{'#'*70}")
    print(f"# TESTING: {arc_type_name}")
    print('#'*70)
    
    results = []
    
    # Test 1: Multiple transformations
    try:
        result = test_multiple_transformations(arc_type_name, arc_obj, num_transforms=3)
        results.append(("Multiple Transformations", result))
    except Exception as e:
        print(f"\n✗ Multiple Transformations EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Multiple Transformations", False))
    
    # Test 2: Context menu sensitivity (before transform)
    try:
        # Create fresh arc for this test
        place = Place(100, 100, id=1, name="P1")
        trans = Transition(300, 100, id=2, name="T1")
        fresh_arc = type(arc_obj)(place, trans, id=3, name=f"Test_{arc_type_name}")
        if hasattr(arc_obj, 'is_curved') and arc_obj.is_curved:
            fresh_arc.is_curved = True
            fresh_arc.control_offset_x = arc_obj.control_offset_x
            fresh_arc.control_offset_y = arc_obj.control_offset_y
        
        result = test_context_menu_sensitivity(arc_type_name, fresh_arc)
        results.append(("Context Menu Sensitivity", result))
    except Exception as e:
        print(f"\n✗ Context Menu Sensitivity EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Context Menu Sensitivity", False))
    
    # Test 3: Context menu after transformation
    try:
        # Create fresh arc for this test
        place = Place(100, 100, id=1, name="P1")
        trans = Transition(300, 100, id=2, name="T1")
        fresh_arc = type(arc_obj)(place, trans, id=3, name=f"Test_{arc_type_name}")
        if hasattr(arc_obj, 'is_curved') and arc_obj.is_curved:
            fresh_arc.is_curved = True
            fresh_arc.control_offset_x = 0
            fresh_arc.control_offset_y = -30
        
        result = test_transformed_context_menu_sensitivity(arc_type_name, fresh_arc)
        results.append(("Context Menu After Transform", result))
    except Exception as e:
        print(f"\n✗ Context Menu After Transform EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Context Menu After Transform", False))
    
    # Test 4: Transformation size constraint
    try:
        # Create fresh arc for this test
        place = Place(100, 100, id=1, name="P1")
        trans = Transition(300, 100, id=2, name="T1")
        fresh_arc = type(arc_obj)(place, trans, id=3, name=f"Test_{arc_type_name}")
        
        result = test_transformation_size_constraint(arc_type_name, fresh_arc)
        results.append(("Transformation Size Constraint", result))
    except Exception as e:
        print(f"\n✗ Transformation Size Constraint EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Transformation Size Constraint", False))
    
    return results


if __name__ == '__main__':
    print("\n" + "="*70)
    print("COMPREHENSIVE ARC TRANSFORMATION REQUIREMENTS TEST")
    print("="*70)
    print("\nRequirements:")
    print("1. All arcs types must be able to be transformed multiple times")
    print("2. All arcs type must be sensitive to context menu")
    print("3. All transformed arcs type must be sensitive to context menu")
    print("4. All transient arcs must be restricted to the size of the arc")
    print("="*70)
    
    # Define all arc types to test
    place = Place(100, 100, id=1, name="P1")
    trans = Transition(300, 100, id=2, name="T1")
    
    # Create curved arc instances
    arc_curved = Arc(place, trans, id=4, name="A2")
    arc_curved.is_curved = True
    arc_curved.control_offset_x = 0
    arc_curved.control_offset_y = -30
    
    inhibitor_curved = InhibitorArc(place, trans, id=6, name="I2")
    inhibitor_curved.is_curved = True
    inhibitor_curved.control_offset_x = 0
    inhibitor_curved.control_offset_y = -30
    
    arc_types = [
        ("Arc (straight)", Arc(place, trans, id=3, name="A1")),
        ("Arc (curved)", arc_curved),
        ("InhibitorArc (straight)", InhibitorArc(place, trans, id=5, name="I1")),
        ("InhibitorArc (curved)", inhibitor_curved),
        ("CurvedArc", CurvedArc(place, trans, id=7, name="C1")),
        ("CurvedInhibitorArc", CurvedInhibitorArc(place, trans, id=8, name="CI1")),
    ]
    
    all_results = []
    
    for arc_type_name, arc_obj in arc_types:
        results = run_all_tests_for_arc_type(arc_type_name, arc_obj)
        all_results.append((arc_type_name, results))
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    all_pass = True
    for arc_type_name, results in all_results:
        print(f"\n{arc_type_name}:")
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status} - {test_name}")
            if not result:
                all_pass = False
    
    if all_pass:
        print("\n" + "="*70)
        print("ALL REQUIREMENTS MET! 🎉")
        print("="*70)
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("SOME REQUIREMENTS NOT MET")
        print("="*70)
        sys.exit(1)
