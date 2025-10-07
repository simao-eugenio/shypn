#!/usr/bin/env python3
"""
Test: Comprehensive Context Menu Sensitivity for All Arc Types
Verify that all arc types are sensitive to context menu (contains_point)
in all states: straight, curved, transformed, and both orientations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.edit.transformation.arc_transform_handler import ArcTransformHandler


class MockSelectionManager:
    """Mock selection manager for testing."""
    def __init__(self):
        self.selected_objects = []


def get_curve_midpoint(arc):
    """Get a point on the arc that should be clickable."""
    src_x, src_y = arc.source.x, arc.source.y
    tgt_x, tgt_y = arc.target.x, arc.target.y
    
    # Check if curved
    is_curved = False
    control_x, control_y = None, None
    
    if isinstance(arc, (CurvedArc, CurvedInhibitorArc)):
        is_curved = True
        if hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None:
            control_x, control_y = arc.manual_control_point
        else:
            cp = arc._calculate_curve_control_point()
            if cp:
                control_x, control_y = cp
    elif getattr(arc, 'is_curved', False):
        is_curved = True
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        control_x = mid_x + getattr(arc, 'control_offset_x', 0)
        control_y = mid_y + getattr(arc, 'control_offset_y', 0)
    
    if is_curved and control_x is not None:
        # Point at t=0.5 on bezier curve
        t = 0.5
        b0 = (1 - t) * (1 - t)
        b1 = 2 * (1 - t) * t
        b2 = t * t
        
        x = b0 * src_x + b1 * control_x + b2 * tgt_x
        y = b0 * src_y + b1 * control_y + b2 * tgt_y
        return (x, y)
    else:
        # Straight line midpoint
        return ((src_x + tgt_x) / 2, (src_y + tgt_y) / 2)


def test_arc_context_menu(arc, arc_name, orientation):
    """Test context menu sensitivity for one arc in different states."""
    print(f"\n{'='*70}")
    print(f"Testing: {arc_name} ({orientation})")
    print(f"{'='*70}")
    
    results = {
        'initial_straight': False,
        'after_curved': False,
        'after_straight_again': False,
    }
    
    # Test 1: Initial state (should be straight)
    print("\n1. Initial state (straight):")
    test_x, test_y = get_curve_midpoint(arc)
    clickable = arc.contains_point(test_x, test_y)
    print(f"   Clickable at ({test_x:.1f}, {test_y:.1f}): {clickable}")
    results['initial_straight'] = clickable
    
    if not clickable:
        print(f"   ✗ FAILED: Arc not clickable in initial state")
    else:
        print(f"   ✓ Arc is clickable in initial state")
    
    # Test 2: Transform to curved
    print("\n2. Transform to curved:")
    selection_manager = MockSelectionManager()
    handler = ArcTransformHandler(selection_manager)
    
    mid_x = (arc.source.x + arc.target.x) / 2
    mid_y = (arc.source.y + arc.target.y) / 2
    
    handler.start_transform(arc, 'midpoint', mid_x, mid_y)
    handler.update_transform(mid_x - 30, mid_y - 20)  # Drag to create curve
    handler.end_transform()
    
    is_curved = getattr(arc, 'is_curved', False) or \
                (hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None)
    print(f"   Arc is now curved: {is_curved}")
    
    # Test after transformation
    test_x, test_y = get_curve_midpoint(arc)
    clickable = arc.contains_point(test_x, test_y)
    print(f"   Clickable at ({test_x:.1f}, {test_y:.1f}): {clickable}")
    results['after_curved'] = clickable
    
    if not clickable:
        print(f"   ✗ FAILED: Arc not clickable after transformation to curved")
    else:
        print(f"   ✓ Arc is clickable after transformation to curved")
    
    # Test 3: Transform back to straight
    print("\n3. Transform back to straight:")
    handler2 = ArcTransformHandler(selection_manager)
    
    # Get handle position
    if isinstance(arc, (CurvedArc, CurvedInhibitorArc)):
        if hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None:
            handle_x, handle_y = arc.manual_control_point
        else:
            cp = arc._calculate_curve_control_point()
            if cp:
                handle_x, handle_y = cp
            else:
                handle_x, handle_y = mid_x, mid_y
    else:
        offset_x = getattr(arc, 'control_offset_x', 0)
        offset_y = getattr(arc, 'control_offset_y', 0)
        handle_x = mid_x + offset_x
        handle_y = mid_y + offset_y
    
    handler2.start_transform(arc, 'midpoint', handle_x, handle_y)
    handler2.end_transform()  # Click without drag to toggle
    
    is_curved = getattr(arc, 'is_curved', False) or \
                (hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None)
    print(f"   Arc is now straight: {not is_curved}")
    
    # Test after transformation back
    test_x, test_y = get_curve_midpoint(arc)
    clickable = arc.contains_point(test_x, test_y)
    print(f"   Clickable at ({test_x:.1f}, {test_y:.1f}): {clickable}")
    results['after_straight_again'] = clickable
    
    if not clickable:
        print(f"   ✗ FAILED: Arc not clickable after transformation back to straight")
    else:
        print(f"   ✓ Arc is clickable after transformation back to straight")
    
    # Summary for this arc
    all_passed = all(results.values())
    if all_passed:
        print(f"\n✓ {arc_name} ({orientation}) - ALL TESTS PASSED")
    else:
        print(f"\n✗ {arc_name} ({orientation}) - SOME TESTS FAILED")
        for state, passed in results.items():
            print(f"     {state}: {'PASS' if passed else 'FAIL'}")
    
    return all_passed


def run_all_tests():
    print("\n" + "#"*70)
    print("# COMPREHENSIVE CONTEXT MENU SENSITIVITY TEST")
    print("# All arc types, all states, both orientations")
    print("#"*70)
    
    test_results = {}
    
    # Test both orientations
    for orientation in ['Place → Transition', 'Transition → Place']:
        print(f"\n\n{'#'*70}")
        print(f"# ORIENTATION: {orientation}")
        print(f"{'#'*70}")
        
        if orientation == 'Place → Transition':
            source = Place(100, 150, id=1, name="P1")
            target = Transition(300, 150, id=2, name="T1")
        else:
            source = Transition(100, 150, id=1, name="T1")
            target = Place(300, 150, id=2, name="P1")
        
        # Create all arc types
        arc_types = [
            ("Arc", Arc(source, target, id=3, name="A1")),
            ("InhibitorArc", InhibitorArc(source, target, id=4, name="I1") if orientation == 'Place → Transition' else None),
            ("CurvedArc", CurvedArc(source, target, id=5, name="C1")),
            ("CurvedInhibitorArc", CurvedInhibitorArc(source, target, id=6, name="CI1") if orientation == 'Place → Transition' else None),
        ]
        
        for arc_name, arc in arc_types:
            if arc is None:
                print(f"\n{arc_name} - Skipped (only valid for Place → Transition)")
                continue
            
            key = f"{arc_name} ({orientation})"
            try:
                test_results[key] = test_arc_context_menu(arc, arc_name, orientation)
            except Exception as e:
                print(f"\n✗ EXCEPTION in {arc_name}: {e}")
                import traceback
                traceback.print_exc()
                test_results[key] = False
    
    # Print final summary
    print("\n\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    all_passed = True
    for key, passed in test_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {key}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL ARCS ARE CONTEXT MENU SENSITIVE IN ALL STATES! 🎉")
    else:
        print("✗ SOME ARCS FAILED CONTEXT MENU SENSITIVITY TEST")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
