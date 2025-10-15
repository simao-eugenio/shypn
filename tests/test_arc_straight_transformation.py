#!/usr/bin/env python3
"""
Test: Curved Arc -> Straight Arc Transformation
Verify that when a curved arc is transformed back to straight,
it eliminates the offset and returns to the intercepted position
at the place/transition boundary.
"""

import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

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
    
    def clear(self):
        self.selected_objects = []
    
    def select(self, obj):
        if obj not in self.selected_objects:
            self.selected_objects.append(obj)
    
    def deselect(self, obj):
        if obj in self.selected_objects:
            self.selected_objects.remove(obj)
    
    def is_selected(self, obj):
        return obj in self.selected_objects


def print_section(title):
    print("\n" + "="*70)
    print(f"Test: {title}")
    print("="*70)


def test_straight_to_curved_to_straight(arc, arc_name):
    """Test that arc can go straight -> curved -> straight and return to boundary."""
    print_section(f"{arc_name} - Straight -> Curved -> Straight")
    
    # Get source and target positions
    src_x, src_y = arc.source.x, arc.source.y
    tgt_x, tgt_y = arc.target.x, arc.target.y
    
    print(f"\nSource: Place at ({src_x}, {src_y})")
    print(f"Target: Transition at ({tgt_x}, {tgt_y})")
    
    # Check initial state
    is_initially_curved = getattr(arc, 'is_curved', False)
    has_manual_point = hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None
    
    print(f"\nInitial state:")
    print(f"  is_curved: {is_initially_curved}")
    print(f"  manual_control_point: {getattr(arc, 'manual_control_point', 'N/A')}")
    
    # Calculate arc midpoint
    mid_x = (src_x + tgt_x) / 2
    mid_y = (src_y + tgt_y) / 2
    
    # Step 1: Transform to curved (if not already curved)
    selection_manager = MockSelectionManager()
    handler = ArcTransformHandler(selection_manager)
    
    if not is_initially_curved and not has_manual_point:
        print("\nStep 1: Transform straight arc to curved")
        
        # Start transformation at midpoint
        handler.start_transform(arc, 'midpoint', mid_x, mid_y)
        
        # Drag to create curve (30 pixels perpendicular)
        perp_x = mid_x - 30
        perp_y = mid_y
        handler.update_transform(perp_x, perp_y)
        handler.end_transform()
        
        print(f"  After transformation:")
        print(f"    is_curved: {getattr(arc, 'is_curved', False)}")
        print(f"    control_offset_x: {getattr(arc, 'control_offset_x', 'N/A')}")
        print(f"    control_offset_y: {getattr(arc, 'control_offset_y', 'N/A')}")
        print(f"    manual_control_point: {getattr(arc, 'manual_control_point', 'N/A')}")
    else:
        print("\nStep 1: Arc is already curved, skipping transformation")
    
    # Verify arc is now curved
    is_curved_now = getattr(arc, 'is_curved', False) or \
                    (hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None)
    
    if not is_curved_now and not isinstance(arc, (CurvedArc, CurvedInhibitorArc)):
        print("  ✗ FAILED: Arc did not become curved!")
        return False
    
    print("  ✓ Arc is curved")
    
    # Step 2: Transform back to straight
    print("\nStep 2: Transform curved arc back to straight")
    
    handler2 = ArcTransformHandler(selection_manager)
    
    # Click at the handle position (this should toggle straight/curved)
    # For Arc with is_curved, the handle is at the control point
    # For CurvedArc, the handle is at manual_control_point or calculated position
    if isinstance(arc, (CurvedArc, CurvedInhibitorArc)):
        if hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None:
            handle_x, handle_y = arc.manual_control_point
        else:
            # Use automatic calculation
            cp = arc._calculate_curve_control_point()
            if cp:
                handle_x, handle_y = cp
            else:
                handle_x, handle_y = mid_x, mid_y
    else:
        # Arc with is_curved
        offset_x = getattr(arc, 'control_offset_x', 0)
        offset_y = getattr(arc, 'control_offset_y', 0)
        handle_x = mid_x + offset_x
        handle_y = mid_y + offset_y
    
    print(f"  Clicking at handle position: ({handle_x:.1f}, {handle_y:.1f})")
    
    handler2.start_transform(arc, 'midpoint', handle_x, handle_y)
    # Don't drag, just click to toggle
    handler2.end_transform()
    
    print(f"  After transformation back to straight:")
    print(f"    is_curved: {getattr(arc, 'is_curved', False)}")
    print(f"    control_offset_x: {getattr(arc, 'control_offset_x', 'N/A')}")
    print(f"    control_offset_y: {getattr(arc, 'control_offset_y', 'N/A')}")
    print(f"    manual_control_point: {getattr(arc, 'manual_control_point', 'N/A')}")
    
    # Step 3: Verify arc is straight and offsets are eliminated
    is_straight_now = not getattr(arc, 'is_curved', False)
    
    if isinstance(arc, (CurvedArc, CurvedInhibitorArc)):
        # For CurvedArc, check if manual_control_point is None
        manual_point = getattr(arc, 'manual_control_point', None)
        offsets_eliminated = manual_point is None
        print(f"\n  Checking manual_control_point: {manual_point}")
    else:
        # For Arc with is_curved, check if control offsets are zero
        offset_x = getattr(arc, 'control_offset_x', 0)
        offset_y = getattr(arc, 'control_offset_y', 0)
        offsets_eliminated = (abs(offset_x) < 0.01 and abs(offset_y) < 0.01)
        print(f"\n  Checking control offsets: ({offset_x:.2f}, {offset_y:.2f})")
    
    # Final verification
    success = True
    
    if isinstance(arc, (CurvedArc, CurvedInhibitorArc)):
        # CurvedArc should have manual_control_point = None when straight
        if manual_point is not None:
            print("  ✗ FAILED: manual_control_point should be None for straight arc")
            success = False
        else:
            print("  ✓ manual_control_point is None (eliminated)")
    else:
        # Arc should have is_curved = False and zero offsets
        if not is_straight_now:
            print("  ✗ FAILED: is_curved should be False")
            success = False
        elif not offsets_eliminated:
            print("  ✗ FAILED: control offsets should be zero")
            success = False
        else:
            print("  ✓ is_curved = False and offsets eliminated")
    
    if success:
        print(f"\n✓ {arc_name} correctly returns to straight with eliminated offsets!")
    else:
        print(f"\n✗ {arc_name} FAILED to eliminate offsets properly")
    
    return success


def run_all_tests():
    print("\n" + "#"*70)
    print("# TESTING: Curved -> Straight Transformation")
    print("# Requirement: Offsets must be eliminated and arc returns to boundary")
    print("#"*70)
    
    # Create test objects
    place = Place(100, 150, id=1, name="P1")
    trans = Transition(300, 150, id=2, name="T1")
    
    # Create all arc types
    arc_types = [
        ("Arc (straight)", Arc(place, trans, id=1, name="A1")),
        ("InhibitorArc (straight)", InhibitorArc(place, trans, id=2, name="I1")),
        ("CurvedArc", CurvedArc(place, trans, id=3, name="C1")),
        ("CurvedInhibitorArc", CurvedInhibitorArc(place, trans, id=4, name="CI1")),
    ]
    
    # Also test Arc that starts curved
    arc_curved = Arc(place, trans, id=5, name="A2")
    arc_curved.is_curved = True
    arc_curved.control_offset_x = 0
    arc_curved.control_offset_y = -30
    arc_types.append(("Arc (initially curved)", arc_curved))
    
    inhibitor_curved = InhibitorArc(place, trans, id=6, name="I2")
    inhibitor_curved.is_curved = True
    inhibitor_curved.control_offset_x = 0
    inhibitor_curved.control_offset_y = -30
    arc_types.append(("InhibitorArc (initially curved)", inhibitor_curved))
    
    # Run tests
    results = {}
    for name, arc in arc_types:
        try:
            results[name] = test_straight_to_curved_to_straight(arc, name)
        except Exception as e:
            print(f"\n✗ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print()
    
    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}:")
        print(f"  {status} - Straight transformation eliminates offsets")
        if not passed:
            all_passed = False
    
    print()
    print("="*70)
    if all_passed:
        print("ALL ARCS CORRECTLY ELIMINATE OFFSETS! 🎉")
    else:
        print("SOME ARCS FAILED TO ELIMINATE OFFSETS")
    print("="*70)


if __name__ == "__main__":
    run_all_tests()
