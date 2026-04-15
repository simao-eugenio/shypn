#!/usr/bin/env python3
"""
Test Manual Arc Creation Type Inheritance

Validates that manually created arcs inherit the type from the most recent
arc transformation, instead of always defaulting to normal arcs.

Author: SHPN Development Team
Date: 2025
"""

import os
import sys

# Ensure shypn package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shypn.core.controllers.document_controller import DocumentController
from shypn.data.canvas.id_manager import IDManager
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.utils.arc_transform import convert_to_test, convert_to_inhibitor


def test_default_arc_creation():
    """Test that first arc defaults to normal type."""
    print("=" * 70)
    print("TEST 1: Default arc creation (should be normal)")
    print("=" * 70)
    
    id_manager = IDManager()
    controller = DocumentController(id_manager)
    
    # Create places and transition
    p1 = Place(id='p1', name='Source Place', x=100, y=100)
    t1 = Transition(id='t1', name='Test Transition', x=200, y=100)
    
    controller.places.append(p1)
    controller.transitions.append(t1)
    
    # Create first arc (should default to normal)
    arc1 = controller.add_arc(p1, t1)
    
    # Verify
    assert isinstance(arc1, Arc), f"Expected Arc, got {type(arc1).__name__}"
    assert not isinstance(arc1, TestArc), "Arc should not be TestArc"
    assert not isinstance(arc1, InhibitorArc), "Arc should not be InhibitorArc"
    assert arc1.arc_type == 'normal', f"Expected normal, got {arc1.arc_type}"
    
    print(f"✓ First arc type: {arc1.arc_type}")
    print(f"✓ First arc class: {type(arc1).__name__}")
    print(f"✓ Session preference: {controller._last_arc_type}")
    print()
    
    return controller


def test_arc_creation_after_test_transformation(controller):
    """Test that new arcs inherit test type after test transformation."""
    print("=" * 70)
    print("TEST 2: Arc creation after test transformation")
    print("=" * 70)
    
    # Create places and transition
    p2 = Place(id='p2', name='Source Place 2', x=100, y=200)
    t2 = Transition(id='t2', name='Test Transition 2', x=200, y=200)
    
    controller.places.append(p2)
    controller.transitions.append(t2)
    
    # Create arc and transform to test
    arc1 = controller.add_arc(p2, t2)
    print(f"Created arc: {arc1.arc_type} ({type(arc1).__name__})")
    
    # Transform to test arc
    new_arc = convert_to_test(arc1)
    controller.replace_arc(arc1, new_arc)
    print(f"Transformed to: {new_arc.arc_type} ({type(new_arc).__name__})")
    print(f"Session preference updated to: {controller._last_arc_type}")
    
    # Create new arc (should inherit test type)
    p3 = Place(id='p3', name='Source Place 3', x=100, y=300)
    t3 = Transition(id='t3', name='Test Transition 3', x=200, y=300)
    controller.places.append(p3)
    controller.transitions.append(t3)
    
    arc2 = controller.add_arc(p3, t3)
    
    # Verify
    assert isinstance(arc2, TestArc), f"Expected TestArc, got {type(arc2).__name__}"
    assert arc2.arc_type == 'test', f"Expected test, got {arc2.arc_type}"
    
    print(f"✓ New arc inherits type: {arc2.arc_type}")
    print(f"✓ New arc class: {type(arc2).__name__}")
    print(f"✓ Session preference: {controller._last_arc_type}")
    print()
    
    return controller


def test_arc_creation_after_inhibitor_transformation(controller):
    """Test that new arcs inherit inhibitor type after inhibitor transformation."""
    print("=" * 70)
    print("TEST 3: Arc creation after inhibitor transformation")
    print("=" * 70)
    
    # Create places and transition
    p4 = Place(id='p4', name='Source Place 4', x=100, y=400)
    t4 = Transition(id='t4', name='Test Transition 4', x=200, y=400)
    
    controller.places.append(p4)
    controller.transitions.append(t4)
    
    # Current preference should be 'test' from previous test
    print(f"Current session preference: {controller._last_arc_type}")
    
    # Create arc (should be test type from previous transformation)
    arc1 = controller.add_arc(p4, t4)
    print(f"Created arc: {arc1.arc_type} ({type(arc1).__name__})")
    assert arc1.arc_type == 'test', "Should inherit test type from session"
    
    # Transform to inhibitor arc
    new_arc = convert_to_inhibitor(arc1)
    controller.replace_arc(arc1, new_arc)
    print(f"Transformed to: {new_arc.arc_type} ({type(new_arc).__name__})")
    print(f"Session preference updated to: {controller._last_arc_type}")
    
    # Create new arc (should inherit inhibitor type)
    p5 = Place(id='p5', name='Source Place 5', x=100, y=500)
    t5 = Transition(id='t5', name='Test Transition 5', x=200, y=500)
    controller.places.append(p5)
    controller.transitions.append(t5)
    
    arc2 = controller.add_arc(p5, t5)
    
    # Verify
    assert isinstance(arc2, InhibitorArc), f"Expected InhibitorArc, got {type(arc2).__name__}"
    assert arc2.arc_type == 'inhibitor', f"Expected inhibitor, got {arc2.arc_type}"
    
    print(f"✓ New arc inherits type: {arc2.arc_type}")
    print(f"✓ New arc class: {type(arc2).__name__}")
    print(f"✓ Session preference: {controller._last_arc_type}")
    print()
    
    return controller


def test_multiple_arc_creation_same_type(controller):
    """Test creating multiple arcs of the same type in succession."""
    print("=" * 70)
    print("TEST 4: Multiple arc creation with same type")
    print("=" * 70)
    
    # Current preference should be 'inhibitor' from previous test
    print(f"Current session preference: {controller._last_arc_type}")
    
    # Create multiple arcs (all should be inhibitor type)
    created_arcs = []
    for i in range(3):
        p = Place(id=f'p_multi_{i}', name=f'Place {i}', x=100, y=600 + i*100)
        t = Transition(id=f't_multi_{i}', name=f'Trans {i}', x=200, y=600 + i*100)
        controller.places.append(p)
        controller.transitions.append(t)
        
        arc = controller.add_arc(p, t)
        created_arcs.append(arc)
        print(f"  Arc {i+1}: {arc.arc_type} ({type(arc).__name__})")
    
    # Verify all are inhibitor type
    for i, arc in enumerate(created_arcs):
        assert isinstance(arc, InhibitorArc), f"Arc {i+1} should be InhibitorArc"
        assert arc.arc_type == 'inhibitor', f"Arc {i+1} should be inhibitor type"
    
    print(f"✓ All {len(created_arcs)} arcs inherit inhibitor type")
    print(f"✓ Session preference remains: {controller._last_arc_type}")
    print()
    
    return controller


def test_explicit_arc_type_override():
    """Test that explicit arc_type parameter overrides session preference."""
    print("=" * 70)
    print("TEST 5: Explicit arc type override")
    print("=" * 70)
    
    id_manager = IDManager()
    controller = DocumentController(id_manager)
    
    # Set session preference to test
    controller._last_arc_type = 'test'
    print(f"Session preference set to: {controller._last_arc_type}")
    
    # Create places and transition
    p1 = Place(id='p_override_1', name='Place Override 1', x=100, y=100)
    t1 = Transition(id='t_override_1', name='Trans Override 1', x=200, y=100)
    controller.places.append(p1)
    controller.transitions.append(t1)
    
    # Create arc with explicit inhibitor type (should override session preference)
    arc1 = controller.add_arc(p1, t1, arc_type='inhibitor')
    
    # Verify
    assert isinstance(arc1, InhibitorArc), f"Expected InhibitorArc, got {type(arc1).__name__}"
    assert arc1.arc_type == 'inhibitor', f"Expected inhibitor, got {arc1.arc_type}"
    
    print(f"✓ Explicit arc_type='inhibitor' overrides session preference")
    print(f"✓ Created arc type: {arc1.arc_type}")
    print(f"✓ Session preference unchanged: {controller._last_arc_type}")
    print()
    
    # Create another arc without explicit type (should use session preference = test)
    p2 = Place(id='p_override_2', name='Place Override 2', x=100, y=200)
    t2 = Transition(id='t_override_2', name='Trans Override 2', x=200, y=200)
    controller.places.append(p2)
    controller.transitions.append(t2)
    
    arc2 = controller.add_arc(p2, t2)
    
    # Verify
    assert isinstance(arc2, TestArc), f"Expected TestArc, got {type(arc2).__name__}"
    assert arc2.arc_type == 'test', f"Expected test, got {arc2.arc_type}"
    
    print(f"✓ Next arc uses session preference: {arc2.arc_type}")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MANUAL ARC CREATION TYPE INHERITANCE TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        # Test 1: Default behavior
        controller = test_default_arc_creation()
        
        # Test 2: Test arc transformation
        controller = test_arc_creation_after_test_transformation(controller)
        
        # Test 3: Inhibitor arc transformation
        controller = test_arc_creation_after_inhibitor_transformation(controller)
        
        # Test 4: Multiple arcs of same type
        controller = test_multiple_arc_creation_same_type(controller)
        
        # Test 5: Explicit type override
        test_explicit_arc_type_override()
        
        print("=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ Default arc creation uses 'normal' type")
        print("  ✓ New arcs inherit type from last transformation")
        print("  ✓ Test arc transformations update session preference")
        print("  ✓ Inhibitor arc transformations update session preference")
        print("  ✓ Multiple arcs can be created with same type")
        print("  ✓ Explicit arc_type parameter overrides session preference")
        print()
        
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 70)
        print(f"TEST FAILED: {e}")
        print("=" * 70)
        return 1
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
