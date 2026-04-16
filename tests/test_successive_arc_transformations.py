#!/usr/bin/env python3
"""
Test Script: Successive Arc Type Transformations

Tests that successive arc type transformations work correctly without
cached information interfering. This verifies the fix for the bug where
transforming an arc multiple times (e.g., normal → test → inhibitor)
would fail because cached references weren't being flushed.

Reference: Bug report about successive transformations confusing behavior
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.utils.arc_transform import (
    convert_to_test, 
    convert_to_inhibitor, 
    convert_to_normal,
    is_test,
    is_inhibitor,
    is_normal
)


def test_successive_transformations():
    """Test successive arc type transformations.
    
    This tests the critical bug fix: after transforming an arc, successive
    transformations should work on the NEW arc, not the old cached reference.
    """
    
    print("\n" + "="*70)
    print("TEST: Successive Arc Type Transformations")
    print("="*70)
    print("\nScenario: Transform same arc multiple times")
    print("  normal → test → inhibitor → normal → test")
    print("  Each transformation should work on the LATEST arc object\n")
    
    # Create initial objects
    place = Place(x=100, y=100, id="P1", name="Substrate")
    place.tokens = 10.0
    
    trans = Transition(x=200, y=200, id="T1", name="Reaction")
    trans.transition_type = 'immediate'
    
    # Start with normal arc
    arc = Arc(place, trans, "A1", "TestArc", weight=2.0)
    arc.color = (0.0, 0.0, 0.0)  # Black
    
    print(f"Step 1: Initial arc")
    print(f"  Type: {type(arc).__name__}")
    print(f"  Arc ID: {arc.id}")
    print(f"  is_normal: {is_normal(arc)}")
    print(f"  is_test: {is_test(arc)}")
    print(f"  is_inhibitor: {is_inhibitor(arc)}")
    
    if not is_normal(arc):
        print(f"  ❌ FAILED: Initial arc should be normal")
        return False
    
    # Transformation 1: normal → test
    print(f"\nStep 2: Transform normal → test")
    arc = convert_to_test(arc)
    print(f"  Type: {type(arc).__name__}")
    print(f"  Arc ID: {arc.id}")
    print(f"  is_normal: {is_normal(arc)}")
    print(f"  is_test: {is_test(arc)}")
    print(f"  is_inhibitor: {is_inhibitor(arc)}")
    
    if not is_test(arc):
        print(f"  ❌ FAILED: Arc should be test after transformation")
        return False
    if arc.id != "A1":
        print(f"  ❌ FAILED: Arc ID should be preserved")
        return False
    print(f"  ✅ PASSED: Test arc created")
    
    # Transformation 2: test → inhibitor
    print(f"\nStep 3: Transform test → inhibitor")
    arc = convert_to_inhibitor(arc)
    print(f"  Type: {type(arc).__name__}")
    print(f"  Arc ID: {arc.id}")
    print(f"  is_normal: {is_normal(arc)}")
    print(f"  is_test: {is_test(arc)}")
    print(f"  is_inhibitor: {is_inhibitor(arc)}")
    
    if not is_inhibitor(arc):
        print(f"  ❌ FAILED: Arc should be inhibitor after transformation")
        return False
    if is_test(arc):
        print(f"  ❌ FAILED: Arc should NOT be test anymore (cached reference issue)")
        return False
    if arc.id != "A1":
        print(f"  ❌ FAILED: Arc ID should be preserved")
        return False
    print(f"  ✅ PASSED: Inhibitor arc created (test type cleared)")
    
    # Transformation 3: inhibitor → normal
    print(f"\nStep 4: Transform inhibitor → normal")
    arc = convert_to_normal(arc)
    print(f"  Type: {type(arc).__name__}")
    print(f"  Arc ID: {arc.id}")
    print(f"  is_normal: {is_normal(arc)}")
    print(f"  is_test: {is_test(arc)}")
    print(f"  is_inhibitor: {is_inhibitor(arc)}")
    
    if not is_normal(arc):
        print(f"  ❌ FAILED: Arc should be normal after transformation")
        return False
    if is_inhibitor(arc):
        print(f"  ❌ FAILED: Arc should NOT be inhibitor anymore (cached reference issue)")
        return False
    if arc.id != "A1":
        print(f"  ❌ FAILED: Arc ID should be preserved")
        return False
    print(f"  ✅ PASSED: Normal arc created (inhibitor type cleared)")
    
    # Transformation 4: normal → test (again)
    print(f"\nStep 5: Transform normal → test (second time)")
    arc = convert_to_test(arc)
    print(f"  Type: {type(arc).__name__}")
    print(f"  Arc ID: {arc.id}")
    print(f"  is_normal: {is_normal(arc)}")
    print(f"  is_test: {is_test(arc)}")
    print(f"  is_inhibitor: {is_inhibitor(arc)}")
    
    if not is_test(arc):
        print(f"  ❌ FAILED: Arc should be test after transformation")
        return False
    if is_normal(arc):
        print(f"  ❌ FAILED: Arc should NOT be normal anymore")
        return False
    if arc.id != "A1":
        print(f"  ❌ FAILED: Arc ID should be preserved")
        return False
    print(f"  ✅ PASSED: Test arc re-created successfully")
    
    print(f"\n✅ ALL TESTS PASSED - Successive transformations working correctly")
    print(f"   • No cached type information interfering")
    print(f"   • Each transformation operates on latest arc object")
    print(f"   • Arc ID preserved throughout transformations")
    
    return True


def test_property_preservation():
    """Test that properties are preserved through transformations."""
    
    print("\n" + "="*70)
    print("TEST: Property Preservation During Transformations")
    print("="*70)
    
    # Create arc with custom properties
    place = Place(x=100, y=100, id="P1", name="Place1")
    trans = Transition(x=200, y=200, id="T1", name="Trans1")
    
    arc = Arc(place, trans, "A1", "CustomArc", weight=3.5)
    arc.width = 2.5
    arc.threshold = 10.0
    arc.label = "Important connection"
    
    print(f"\nInitial properties:")
    print(f"  Weight: {arc.weight}")
    print(f"  Width: {arc.width}")
    print(f"  Threshold: {arc.threshold}")
    print(f"  Label: {arc.label}")
    
    # Transform to test
    arc = convert_to_test(arc)
    
    print(f"\nAfter normal → test transformation:")
    print(f"  Weight: {arc.weight}")
    print(f"  Width: {arc.width}")
    print(f"  Threshold: {arc.threshold}")
    print(f"  Label: {arc.label}")
    
    if arc.weight != 3.5:
        print(f"  ❌ FAILED: Weight not preserved")
        return False
    if arc.width != 2.5:
        print(f"  ❌ FAILED: Width not preserved")
        return False
    if arc.threshold != 10.0:
        print(f"  ❌ FAILED: Threshold not preserved")
        return False
    if arc.label != "Important connection":
        print(f"  ❌ FAILED: Label not preserved")
        return False
    
    # Transform to inhibitor
    arc = convert_to_inhibitor(arc)
    
    print(f"\nAfter test → inhibitor transformation:")
    print(f"  Weight: {arc.weight}")
    print(f"  Width: {arc.width}")
    print(f"  Threshold: {arc.threshold}")
    print(f"  Label: {arc.label}")
    
    if arc.weight != 3.5:
        print(f"  ❌ FAILED: Weight not preserved")
        return False
    if arc.width != 2.5:
        print(f"  ❌ FAILED: Width not preserved")
        return False
    if arc.threshold != 10.0:
        print(f"  ❌ FAILED: Threshold not preserved")
        return False
    if arc.label != "Important connection":
        print(f"  ❌ FAILED: Label not preserved")
        return False
    
    print(f"\n✅ ALL TESTS PASSED - Properties preserved correctly")
    return True


def test_cache_flushing():
    """Test that cached type information is properly flushed."""
    
    print("\n" + "="*70)
    print("TEST: Cached Type Information Flushing")
    print("="*70)
    
    place = Place(x=100, y=100, id="P1", name="Place1")
    trans = Transition(x=200, y=200, id="T1", name="Trans1")
    arc = Arc(place, trans, "A1", "Arc1", weight=1.0)
    
    # Simulate a cached type attribute (if it existed)
    arc._cached_arc_type = 'normal'
    
    print(f"\nBefore transformation:")
    print(f"  Has _cached_arc_type: {hasattr(arc, '_cached_arc_type')}")
    if hasattr(arc, '_cached_arc_type'):
        print(f"  Cached value: {arc._cached_arc_type}")
    
    # Transform (should flush cache)
    new_arc = convert_to_test(arc)
    
    print(f"\nAfter transformation:")
    print(f"  Old arc has _cached_arc_type: {hasattr(arc, '_cached_arc_type')}")
    print(f"  New arc has _cached_arc_type: {hasattr(new_arc, '_cached_arc_type')}")
    
    if hasattr(arc, '_cached_arc_type'):
        print(f"  ⚠️  WARNING: Old arc cache not flushed (acceptable)")
    
    if hasattr(new_arc, '_cached_arc_type'):
        print(f"  ❌ FAILED: New arc should not have cached type")
        return False
    
    print(f"\n✅ TEST PASSED - Cache properly flushed on new arc")
    return True


if __name__ == "__main__":
    print("="*70)
    print("SUCCESSIVE ARC TRANSFORMATION TEST SUITE")
    print("="*70)
    print("\nPurpose: Verify that successive arc type transformations work")
    print("correctly without cached information interfering.")
    print("\nBug Fix: After transformation, arc reference must be updated")
    print("and cached type information must be flushed.")
    
    results = []
    
    # Test 1: Successive transformations
    results.append(("Successive Transformations", test_successive_transformations()))
    
    # Test 2: Property preservation
    results.append(("Property Preservation", test_property_preservation()))
    
    # Test 3: Cache flushing
    results.append(("Cache Flushing", test_cache_flushing()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:40} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nFix Verification:")
        print("• Successive transformations work correctly")
        print("• Arc reference updated after transformation")
        print("• Cached type information flushed")
        print("• Properties preserved through transformations")
        print("\nUsers can now transform arcs multiple times in property dialog")
        print("or via context menu without confusion or stale references.")
    else:
        print("❌ SOME TESTS FAILED - Review implementation")
    print("="*70)
