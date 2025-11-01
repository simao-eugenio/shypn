#!/usr/bin/env python3
"""Test that transitions with multiple test arcs (catalysts) work correctly.

This verifies that:
1. A transition with multiple test arcs requires ALL catalysts to have tokens
2. Firing does NOT consume tokens from any of the test arcs
3. The transition can fire multiple times with the same catalysts

Test Model Structure:
    P1 (tokens=1) --test--> T1
    P2 (tokens=1) --test--> T1
    P3 (tokens=1) --normal--> T1
    T1 --normal--> P4 (tokens=0)

Expected Behavior:
- T1 requires: P1>=1 (catalyst), P2>=1 (catalyst), P3>=1 (substrate)
- Firing consumes from P3 only, produces to P4
- After 1 firing: P1=1, P2=1, P3=0, P4=1
- After reset: P1=1, P2=1, P3=1, P4=0
- Can fire again with same catalysts
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.engine.simulation.model_adapter import ModelAdapter
from shypn.engine.simulation.controller import SimulationController


def test_multiple_test_arcs():
    """Test transition with multiple test arcs (2 catalysts + 1 substrate)."""
    print("\n" + "="*70)
    print("TEST: Multiple Test Arcs (Catalysts)")
    print("="*70)
    
    # Create places
    p1 = Place(x=100, y=100, id="P1", name="P1", label="Catalyst 1")
    p1.tokens = 1
    p1.initial_marking = 1
    
    p2 = Place(x=200, y=100, id="P2", name="P2", label="Catalyst 2")
    p2.tokens = 1
    p2.initial_marking = 1
    
    p3 = Place(x=300, y=100, id="P3", name="P3", label="Substrate")
    p3.tokens = 1
    p3.initial_marking = 1
    
    p4 = Place(x=400, y=100, id="P4", name="P4", label="Product")
    p4.tokens = 0
    p4.initial_marking = 0
    
    # Create transition
    t1 = Transition(x=250, y=200, id="T1", name="T1", label="Reaction", 
                    horizontal=False, transition_type='immediate')
    
    # Create arcs
    # Two test arcs (catalysts) - should NOT consume tokens
    arc1 = TestArc(source=p1, target=t1, id="A1", name="A1", weight=1)
    arc2 = TestArc(source=p2, target=t1, id="A2", name="A2", weight=1)
    
    # One normal arc (substrate) - SHOULD consume tokens
    arc3 = Arc(source=p3, target=t1, id="A3", name="A3", weight=1)
    
    # One output arc (product)
    arc4 = Arc(source=t1, target=p4, id="A4", name="A4", weight=1)
    
    print("\n1. Initial State:")
    print(f"   P1 (Catalyst 1): {p1.tokens} tokens")
    print(f"   P2 (Catalyst 2): {p2.tokens} tokens")
    print(f"   P3 (Substrate):  {p3.tokens} tokens")
    print(f"   P4 (Product):    {p4.tokens} tokens")
    
    # Create model adapter
    places_dict = {"P1": p1, "P2": p2, "P3": p3, "P4": p4}
    transitions_dict = {"T1": t1}
    arcs_dict = {"A1": arc1, "A2": arc2, "A3": arc3, "A4": arc4}
    
    model = ModelAdapter(places_dict, transitions_dict, arcs_dict)
    
    # Create controller
    controller = SimulationController(model)
    controller.reset()
    
    # Test Case 1: All catalysts present - should be enabled
    print("\n2. Enablement Check (all catalysts + substrate present):")
    controller.update_enablement()
    enabled = controller.is_enabled(t1)
    print(f"   T1 enabled: {enabled}")
    
    if not enabled:
        print("   ❌ FAIL: T1 should be enabled when all catalysts and substrate present")
        return False
    print("   ✅ PASS: T1 correctly enabled")
    
    # Fire transition
    print("\n3. Fire T1 (first firing):")
    result = controller.fire_transition(t1)
    if result:
        print("   ✅ Firing succeeded")
    else:
        print("   ❌ Firing failed")
        return False
    
    print(f"   After firing:")
    print(f"   P1 (Catalyst 1): {p1.tokens} tokens (should be 1 - NOT consumed)")
    print(f"   P2 (Catalyst 2): {p2.tokens} tokens (should be 1 - NOT consumed)")
    print(f"   P3 (Substrate):  {p3.tokens} tokens (should be 0 - consumed)")
    print(f"   P4 (Product):    {p4.tokens} tokens (should be 1 - produced)")
    
    # Verify catalysts NOT consumed
    if p1.tokens != 1:
        print(f"   ❌ FAIL: Catalyst 1 was consumed (expected 1, got {p1.tokens})")
        return False
    if p2.tokens != 1:
        print(f"   ❌ FAIL: Catalyst 2 was consumed (expected 1, got {p2.tokens})")
        return False
    print("   ✅ PASS: Both catalysts NOT consumed")
    
    # Verify substrate consumed
    if p3.tokens != 0:
        print(f"   ❌ FAIL: Substrate not consumed (expected 0, got {p3.tokens})")
        return False
    print("   ✅ PASS: Substrate correctly consumed")
    
    # Verify product produced
    if p4.tokens != 1:
        print(f"   ❌ FAIL: Product not produced (expected 1, got {p4.tokens})")
        return False
    print("   ✅ PASS: Product correctly produced")
    
    # Test Case 2: Remove one catalyst - should be disabled
    print("\n4. Remove Catalyst 1 - check disablement:")
    p1.tokens = 0
    controller.update_enablement()
    enabled = controller.is_enabled(t1)
    print(f"   T1 enabled: {enabled}")
    
    if enabled:
        print("   ❌ FAIL: T1 should be disabled when catalyst 1 missing")
        return False
    print("   ✅ PASS: T1 correctly disabled without catalyst 1")
    
    # Test Case 3: Restore catalysts, refill substrate - can fire again
    print("\n5. Restore all - check multiple firings possible:")
    p1.tokens = 1
    p3.tokens = 1
    controller.update_enablement()
    enabled = controller.is_enabled(t1)
    print(f"   T1 enabled: {enabled}")
    
    if not enabled:
        print("   ❌ FAIL: T1 should be enabled again with catalysts + substrate")
        return False
    print("   ✅ PASS: T1 can be enabled multiple times with same catalysts")
    
    # Fire again
    result = controller.fire_transition(t1)
    if not result:
        print("   ❌ FAIL: Second firing failed")
        return False
    
    print(f"   After second firing:")
    print(f"   P1 (Catalyst 1): {p1.tokens} tokens (should still be 1)")
    print(f"   P2 (Catalyst 2): {p2.tokens} tokens (should still be 1)")
    print(f"   P3 (Substrate):  {p3.tokens} tokens (should be 0 again)")
    print(f"   P4 (Product):    {p4.tokens} tokens (should be 2 now)")
    
    if p1.tokens != 1 or p2.tokens != 1:
        print("   ❌ FAIL: Catalysts consumed on second firing")
        return False
    if p4.tokens != 2:
        print(f"   ❌ FAIL: Product count wrong (expected 2, got {p4.tokens})")
        return False
    
    print("   ✅ PASS: Multiple firings work correctly with same catalysts")
    
    return True


def test_missing_one_catalyst():
    """Test that transition is disabled if ANY catalyst is missing."""
    print("\n" + "="*70)
    print("TEST: Transition Disabled When ONE Catalyst Missing")
    print("="*70)
    
    # Create places
    p1 = Place(x=100, y=100, id="P1", name="P1", label="Catalyst 1")
    p1.tokens = 1
    p1.initial_marking = 1
    
    p2 = Place(x=200, y=100, id="P2", name="P2", label="Catalyst 2")
    p2.tokens = 0  # MISSING!
    p2.initial_marking = 1
    
    p3 = Place(x=300, y=100, id="P3", name="P3", label="Substrate")
    p3.tokens = 1
    p3.initial_marking = 1
    
    # Create transition
    t1 = Transition(x=250, y=200, id="T1", name="T1", label="Reaction",
                    horizontal=False, transition_type='immediate')
    
    # Create arcs
    arc1 = TestArc(source=p1, target=t1, id="A1", name="A1", weight=1)
    arc2 = TestArc(source=p2, target=t1, id="A2", name="A2", weight=1)
    arc3 = Arc(source=p3, target=t1, id="A3", name="A3", weight=1)
    
    print("\n1. Initial State:")
    print(f"   P1 (Catalyst 1): {p1.tokens} tokens ✓")
    print(f"   P2 (Catalyst 2): {p2.tokens} tokens ✗ MISSING")
    print(f"   P3 (Substrate):  {p3.tokens} tokens ✓")
    
    # Create model
    places_dict = {"P1": p1, "P2": p2, "P3": p3}
    transitions_dict = {"T1": t1}
    arcs_dict = {"A1": arc1, "A2": arc2, "A3": arc3}
    
    model = ModelAdapter(places_dict, transitions_dict, arcs_dict)
    controller = SimulationController(model)
    controller.reset()
    
    # Check enablement
    print("\n2. Enablement Check:")
    controller.update_enablement()
    enabled = controller.is_enabled(t1)
    print(f"   T1 enabled: {enabled}")
    
    if enabled:
        print("   ❌ FAIL: T1 should be disabled when Catalyst 2 is missing")
        return False
    
    print("   ✅ PASS: T1 correctly disabled when one catalyst missing")
    return True


if __name__ == '__main__':
    results = []
    
    try:
        results.append(("Multiple Test Arcs", test_multiple_test_arcs()))
        results.append(("Missing One Catalyst", test_missing_one_catalyst()))
        
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status}: {test_name}")
            if not passed:
                all_passed = False
        
        print("="*70)
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Multiple test arcs work correctly")
            print("✅ ALL catalysts must be present for enablement")
            print("✅ NO catalysts are consumed during firing")
            print("✅ Same catalysts can be reused for multiple firings")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
