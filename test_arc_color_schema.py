#!/usr/bin/env python3
"""Test Arc Creation and Transformation Color Schema Compliance.

Verifies that:
1. Arc creation applies correct ColorSchemaManager colors
2. Arc transformation preserves semantic colors
3. Arc types maintain proper colors after operations
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.utils.color_schema_manager import ColorSchemaManager
from shypn.utils.arc_transform import (
    convert_to_test, convert_to_signal_flow, convert_to_inhibitor,
    convert_to_normal, make_curved, make_straight, transform_arc
)


def color_to_str(color):
    """Convert color tuple to readable string."""
    if color == (0.0, 0.0, 0.0):
        return "Black"
    elif color == (0.0, 0.0, 1.0):
        return "Blue"
    elif color == (0.7, 0.7, 0.7):
        return "LightGray"
    elif color == (0.5, 0.5, 0.5):
        return "Gray"
    else:
        return f"RGB{color}"


def test_arc_creation_colors():
    """Test that newly created arcs have proper ColorSchemaManager colors."""
    print("=" * 80)
    print("TEST 1: Arc Creation Colors")
    print("=" * 80)
    
    # Create test objects
    p1 = Place(x=0, y=0, id="P1", name="P1")
    p2 = Place(x=100, y=0, id="P2", name="P2")
    p2.is_signal_place = True  # Make P2 a signal place
    t1 = Transition(x=50, y=50, id="T1", name="T1")
    
    # Test normal arc
    arc1 = Arc(source=p1, target=t1, id="A1", name="A1", weight=1)
    expected_color = ColorSchemaManager.ARC_DEFAULT
    status = "✓ PASS" if arc1.color == expected_color else "✗ FAIL"
    print(f"Normal Arc (P→T):        {color_to_str(arc1.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Test inhibitor arc
    arc2 = InhibitorArc(source=p1, target=t1, id="A2", name="A2", weight=1)
    expected_color = ColorSchemaManager.ARC_INHIBITOR
    status = "✓ PASS" if arc2.color == expected_color else "✗ FAIL"
    print(f"Inhibitor Arc (P→T):     {color_to_str(arc2.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Test test arc
    arc3 = TestArc(source=p1, target=t1, id="A3", name="A3", weight=1)
    expected_color = ColorSchemaManager.ARC_TEST
    status = "✓ PASS" if arc3.color == expected_color else "✗ FAIL"
    print(f"Test Arc (P→T):          {color_to_str(arc3.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Test signal flow arc
    arc4 = SignalFlowArc(source=p2, target=t1, id="A4", name="A4", weight=1)
    expected_color = ColorSchemaManager.ARC_SIGNAL_FLOW
    status = "✓ PASS" if arc4.color == expected_color else "✗ FAIL"
    print(f"SignalFlow Arc (Ψ→T):    {color_to_str(arc4.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    print()


def test_arc_transformation_colors():
    """Test that arc transformations apply proper ColorSchemaManager colors."""
    print("=" * 80)
    print("TEST 2: Arc Transformation Colors")
    print("=" * 80)
    
    # Create test objects
    p1 = Place(x=0, y=0, id="P1", name="P1")
    p2 = Place(x=100, y=0, id="P2", name="P2")
    p2.is_signal_place = True  # Make P2 a signal place
    t1 = Transition(x=50, y=50, id="T1", name="T1")
    
    # Transform normal → test
    arc_normal = Arc(source=p1, target=t1, id="A1", name="A1", weight=1)
    arc_test = convert_to_test(arc_normal)
    expected_color = ColorSchemaManager.ARC_TEST
    status = "✓ PASS" if arc_test.color == expected_color else "✗ FAIL"
    print(f"Normal → Test:           {color_to_str(arc_test.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Transform normal → inhibitor
    arc_normal2 = Arc(source=p1, target=t1, id="A2", name="A2", weight=1)
    arc_inhib = convert_to_inhibitor(arc_normal2)
    expected_color = ColorSchemaManager.ARC_INHIBITOR
    status = "✓ PASS" if arc_inhib.color == expected_color else "✗ FAIL"
    print(f"Normal → Inhibitor:      {color_to_str(arc_inhib.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Transform normal → signal_flow
    arc_normal3 = Arc(source=p2, target=t1, id="A3", name="A3", weight=1)
    arc_signal = convert_to_signal_flow(arc_normal3)
    expected_color = ColorSchemaManager.ARC_SIGNAL_FLOW
    status = "✓ PASS" if arc_signal.color == expected_color else "✗ FAIL"
    print(f"Normal → SignalFlow:     {color_to_str(arc_signal.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Transform test → normal
    arc_test2 = TestArc(source=p1, target=t1, id="A4", name="A4", weight=1)
    arc_back_normal = convert_to_normal(arc_test2)
    expected_color = ColorSchemaManager.ARC_DEFAULT
    status = "✓ PASS" if arc_back_normal.color == expected_color else "✗ FAIL"
    print(f"Test → Normal:           {color_to_str(arc_back_normal.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Transform inhibitor → normal (should preserve black)
    arc_inhib2 = InhibitorArc(source=p1, target=t1, id="A5", name="A5", weight=1)
    arc_back_normal2 = convert_to_normal(arc_inhib2)
    expected_color = ColorSchemaManager.ARC_DEFAULT
    status = "✓ PASS" if arc_back_normal2.color == expected_color else "✗ FAIL"
    print(f"Inhibitor → Normal:      {color_to_str(arc_back_normal2.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    print()


def test_curved_arc_transformation_colors():
    """Test that curved/straight transformations preserve semantic colors."""
    print("=" * 80)
    print("TEST 3: Curved/Straight Transformation Colors")
    print("=" * 80)
    
    # Create test objects
    p1 = Place(x=0, y=0, id="P1", name="P1")
    p2 = Place(x=100, y=0, id="P2", name="P2")
    p2.is_signal_place = True
    t1 = Transition(x=50, y=50, id="T1", name="T1")
    
    # Test arc → curved (should preserve color)
    test_arc_obj = TestArc(source=p1, target=t1, id="A1", name="A1", weight=1)
    curved_test = make_curved(test_arc_obj)
    expected_color = ColorSchemaManager.ARC_TEST
    status = "✓ PASS" if curved_test.color == expected_color else "✗ FAIL"
    print(f"Test → Curved Test:      {color_to_str(curved_test.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Signal arc → curved (should preserve color)
    signal_arc = SignalFlowArc(source=p2, target=t1, id="A2", name="A2", weight=1)
    curved_signal = make_curved(signal_arc)
    expected_color = ColorSchemaManager.ARC_SIGNAL_FLOW
    status = "✓ PASS" if curved_signal.color == expected_color else "✗ FAIL"
    print(f"Signal → Curved Signal:  {color_to_str(curved_signal.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Curved test → straight (should preserve color)
    from shypn.netobjs.curved_arc import CurvedArc
    curved_test2 = CurvedArc(source=p1, target=t1, id="A3", name="A3", weight=1)
    # Manually convert to test type first
    curved_test_typed = TestArc(source=p1, target=t1, id="A3", name="A3", weight=1)
    curved_test_typed.control_points = [(25, 25)]
    straight_test = make_straight(curved_test_typed)
    expected_color = ColorSchemaManager.ARC_TEST
    status = "✓ PASS" if straight_test.color == expected_color else "✗ FAIL"
    print(f"Curved Test → Straight:  {color_to_str(straight_test.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    print()


def test_transform_arc_function():
    """Test the generic transform_arc function with make_curved/make_inhibitor."""
    print("=" * 80)
    print("TEST 4: Generic transform_arc() Function")
    print("=" * 80)
    
    # Create test objects
    p1 = Place(x=0, y=0, id="P1", name="P1")
    p2 = Place(x=100, y=0, id="P2", name="P2")
    p2.is_signal_place = True
    t1 = Transition(x=50, y=50, id="T1", name="T1")
    
    # Test normal → curved (should preserve black)
    arc1 = Arc(source=p1, target=t1, id="A1", name="A1", weight=1)
    arc1_curved = transform_arc(arc1, make_curved=True)
    expected_color = ColorSchemaManager.ARC_DEFAULT
    status = "✓ PASS" if arc1_curved.color == expected_color else "✗ FAIL"
    print(f"transform_arc(curved):   {color_to_str(arc1_curved.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Test normal → inhibitor (should get black)
    arc2 = Arc(source=p1, target=t1, id="A2", name="A2", weight=1)
    arc2_inhib = transform_arc(arc2, make_inhibitor=True)
    expected_color = ColorSchemaManager.ARC_INHIBITOR
    status = "✓ PASS" if arc2_inhib.color == expected_color else "✗ FAIL"
    print(f"transform_arc(inhibit):  {color_to_str(arc2_inhib.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    # Test signal → curved (should preserve gray)
    arc3 = SignalFlowArc(source=p2, target=t1, id="A3", name="A3", weight=1)
    arc3_curved = transform_arc(arc3, make_curved=True)
    expected_color = ColorSchemaManager.ARC_SIGNAL_FLOW
    status = "✓ PASS" if arc3_curved.color == expected_color else "✗ FAIL"
    print(f"transform_arc(sig→curv): {color_to_str(arc3_curved.color):15} Expected: {color_to_str(expected_color):15} {status}")
    
    print()


def run_all_tests():
    """Run all arc color schema tests."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "ARC COLOR SCHEMA COMPLIANCE TEST" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    test_arc_creation_colors()
    test_arc_transformation_colors()
    test_curved_arc_transformation_colors()
    test_transform_arc_function()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("All arc creation and transformation operations should apply proper")
    print("ColorSchemaManager colors:")
    print("  • Normal arcs:      Black (0.0, 0.0, 0.0)")
    print("  • Inhibitor arcs:   Black (0.0, 0.0, 0.0)")
    print("  • Test arcs:        Blue (0.0, 0.0, 1.0)")
    print("  • SignalFlow arcs:  LightGray (0.7, 0.7, 0.7)")
    print()
    print("Semantic arc types (Test, SignalFlow) MUST preserve their colors during:")
    print("  • Creation from constructors")
    print("  • Transformation between types")
    print("  • Curved/straight conversions")
    print("  • Copy/paste operations")
    print("=" * 80)
    print()


if __name__ == '__main__':
    run_all_tests()
