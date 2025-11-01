#!/usr/bin/env python3
"""
Simplified test suite for TestArc simulation behavior.

Verifies that test arcs (read arcs):
1. Check enablement (require tokens >= weight)
2. Do NOT consume tokens during firing
3. Work correctly with immediate and continuous transitions

Author: GitHub Copilot
Date: October 31, 2025
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.engine.immediate_behavior import ImmediateBehavior
from shypn.engine.continuous_behavior import ContinuousBehavior


# Simple mock model with dictionary structure (as expected by behaviors)
class MockModel:
    """Mock model with dict-based structure for testing."""
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}
        self.logical_time = 0.0
    
    def add_place(self, place):
        self.places[place.id] = place
    
    def add_transition(self, transition):
        self.transitions[transition.id] = transition
    
    def add_arc(self, arc):
        self.arcs[arc.id] = arc


def test_immediate_with_test_arc():
    """Test immediate transition with test arc (catalyst)."""
    print("\n" + "="*70)
    print("TEST 1: Immediate Transition with Test Arc")
    print("="*70)
    
    # Create model
    model = MockModel()
    
    # Places
    substrate = Place(id=1, name="Substrate", x=100, y=100)
    substrate.tokens = 10
    enzyme = Place(id=2, name="Enzyme", x=100, y=200)
    enzyme.tokens = 5  # CATALYST
    product = Place(id=3, name="Product", x=300, y=150)
    product.tokens = 0
    
    model.add_place(substrate)
    model.add_place(enzyme)
    model.add_place(product)
    
    # Transition
    reaction = Transition(id=1, name="Reaction", x=200, y=150)
    reaction.transition_type = "immediate"
    model.add_transition(reaction)
    
    # Arcs
    arc1 = Arc(substrate, reaction, 1, "SubstrateArc", weight=2)  # Consumed
    arc2 = TestArc(enzyme, reaction, 2, "EnzymeArc", weight=1)    # NOT consumed
    arc3 = Arc(reaction, product, 3, "ProductArc", weight=1)       # Produced
    
    model.add_arc(arc1)
    model.add_arc(arc2)
    model.add_arc(arc3)
    
    print(f"Initial state:")
    print(f"  Substrate (P1): {substrate.tokens} tokens")
    print(f"  Enzyme (P2):    {enzyme.tokens} tokens (CATALYST)")
    print(f"  Product (P3):   {product.tokens} tokens")
    
    # Create behavior
    behavior = ImmediateBehavior(reaction, model)
    
    # Check enablement
    can_fire, reason = behavior.can_fire()
    print(f"\nEnablement check: {can_fire} ({reason})")
    assert can_fire, f"Should be enabled but got: {reason}"
    
    # Fire transition
    input_arcs = [arc1, arc2]
    output_arcs = [arc3]
    success, details = behavior.fire(input_arcs, output_arcs)
    
    print(f"\nFiring result: {success}")
    print(f"Consumed: {details.get('consumed', {})}")
    print(f"Produced: {details.get('produced', {})}")
    
    print(f"\nFinal state:")
    print(f"  Substrate (P1): {substrate.tokens} tokens (consumed 2)")
    print(f"  Enzyme (P2):    {enzyme.tokens} tokens (should be UNCHANGED)")
    print(f"  Product (P3):   {product.tokens} tokens (produced 1)")
    
    # Verify results
    assert success, "Firing should succeed"
    assert substrate.tokens == 8, f"Substrate should be 8, got {substrate.tokens}"
    assert enzyme.tokens == 5, f"Enzyme should remain 5, got {enzyme.tokens} (TEST ARC BUG!)"
    assert product.tokens == 1, f"Product should be 1, got {product.tokens}"
    
    # Verify enzyme NOT in consumed map
    assert 2 not in details.get('consumed', {}), "Enzyme (ID=2) should NOT be in consumed map"
    
    print("\n✓ TEST PASSED: Enzyme tokens NOT consumed (catalyst behavior)")


def test_continuous_with_test_arc():
    """Test continuous transition with test arc (catalyst)."""
    print("\n" + "="*70)
    print("TEST 2: Continuous Transition with Test Arc")
    print("="*70)
    
    # Create model
    model = MockModel()
    
    # Places
    substrate = Place(id=1, name="Substrate", x=100, y=100)
    substrate.tokens = 100.0
    catalyst = Place(id=2, name="Catalyst", x=100, y=200)
    catalyst.tokens = 10.0  # CATALYST
    product = Place(id=3, name="Product", x=300, y=150)
    product.tokens = 0.0
    
    model.add_place(substrate)
    model.add_place(catalyst)
    model.add_place(product)
    
    # Transition with rate function
    reaction = Transition(id=1, name="CatalyticReaction", x=200, y=150)
    reaction.transition_type = "continuous"
    if not hasattr(reaction, 'properties'):
        reaction.properties = {}
    reaction.properties['rate_function'] = "10.0"  # Constant rate for simplicity
    model.add_transition(reaction)
    
    # Arcs
    arc1 = Arc(substrate, reaction, 1, "SubstrateArc", weight=1)   # Consumed
    arc2 = TestArc(catalyst, reaction, 2, "CatalystArc", weight=1)  # NOT consumed
    arc3 = Arc(reaction, product, 3, "ProductArc", weight=1)        # Produced
    
    model.add_arc(arc1)
    model.add_arc(arc2)
    model.add_arc(arc3)
    
    print(f"Initial state:")
    print(f"  Substrate (P1): {substrate.tokens} tokens")
    print(f"  Catalyst (P2):  {catalyst.tokens} tokens (CATALYST)")
    print(f"  Product (P3):   {product.tokens} tokens")
    print(f"  Rate function:  10.0 (constant rate)")
    
    # Create behavior
    behavior = ContinuousBehavior(reaction, model)
    
    # Check enablement
    can_fire, reason = behavior.can_fire()
    print(f"\nEnablement check: {can_fire} ({reason})")
    assert can_fire, f"Should be enabled but got: {reason}"
    
    # Integrate over time step
    dt = 0.1
    input_arcs = [arc1, arc2]
    output_arcs = [arc3]
    success, details = behavior.integrate_step(dt, input_arcs, output_arcs)
    
    print(f"\nIntegration result: {success}")
    print(f"Time step: {dt}")
    print(f"Rate: {details.get('rate', 'N/A')}")
    print(f"Consumed: {details.get('consumed', {})}")
    print(f"Produced: {details.get('produced', {})}")
    
    print(f"\nFinal state:")
    print(f"  Substrate (P1): {substrate.tokens:.2f} tokens")
    print(f"  Catalyst (P2):  {catalyst.tokens:.2f} tokens (should be UNCHANGED)")
    print(f"  Product (P3):   {product.tokens:.2f} tokens")
    
    # Verify results
    assert success, "Integration should succeed"
    assert catalyst.tokens == 10.0, f"Catalyst should remain 10.0, got {catalyst.tokens} (TEST ARC BUG!)"
    assert substrate.tokens < 100.0, f"Substrate should decrease, got {substrate.tokens}"
    assert product.tokens > 0.0, f"Product should increase, got {product.tokens}"
    
    # Verify catalyst NOT in consumed map
    assert 2 not in details.get('consumed', {}), "Catalyst (ID=2) should NOT be in consumed map"
    
    print("\n✓ TEST PASSED: Catalyst tokens NOT consumed in continuous flow")


def test_multiple_firings():
    """Test multiple firings with constant catalyst."""
    print("\n" + "="*70)
    print("TEST 3: Multiple Firings with Constant Catalyst")
    print("="*70)
    
    # Create model
    model = MockModel()
    
    # Places
    substrate = Place(id=1, name="Substrate", x=100, y=100)
    substrate.tokens = 20
    enzyme = Place(id=2, name="Enzyme", x=100, y=200)
    enzyme.tokens = 3  # Limited catalyst
    product = Place(id=3, name="Product", x=300, y=150)
    product.tokens = 0
    
    model.add_place(substrate)
    model.add_place(enzyme)
    model.add_place(product)
    
    # Transition
    reaction = Transition(id=1, name="Reaction", x=200, y=150)
    reaction.transition_type = "immediate"
    model.add_transition(reaction)
    
    # Arcs
    arc1 = Arc(substrate, reaction, 1, "SubstrateArc", weight=2)
    arc2 = TestArc(enzyme, reaction, 2, "EnzymeArc", weight=1)
    arc3 = Arc(reaction, product, 3, "ProductArc", weight=1)
    
    model.add_arc(arc1)
    model.add_arc(arc2)
    model.add_arc(arc3)
    
    print(f"Initial state:")
    print(f"  Substrate: {substrate.tokens}, Enzyme: {enzyme.tokens}, Product: {product.tokens}")
    
    # Create behavior
    behavior = ImmediateBehavior(reaction, model)
    
    # Fire multiple times
    firings = 0
    input_arcs = [arc1, arc2]
    output_arcs = [arc3]
    
    while behavior.can_fire()[0] and firings < 20:  # Safety limit
        success, details = behavior.fire(input_arcs, output_arcs)
        if not success:
            break
        firings += 1
        print(f"  After firing {firings}: Substrate={substrate.tokens}, Enzyme={enzyme.tokens}, Product={product.tokens}")
        
        # Verify enzyme NEVER changes
        assert enzyme.tokens == 3, f"Enzyme should always be 3, got {enzyme.tokens} after firing {firings}"
    
    print(f"\nTotal firings: {firings}")
    print(f"Final state:")
    print(f"  Substrate: {substrate.tokens}")
    print(f"  Enzyme: {enzyme.tokens} (CONSTANT!)")
    print(f"  Product: {product.tokens}")
    
    # Should fire until substrate exhausted (10 times: 20 / 2 = 10)
    assert firings == 10, f"Should fire 10 times, got {firings}"
    assert substrate.tokens == 0, f"Substrate should be 0, got {substrate.tokens}"
    assert enzyme.tokens == 3, f"Enzyme should remain 3, got {enzyme.tokens}"
    assert product.tokens == 10, f"Product should be 10, got {product.tokens}"
    
    print("\n✓ TEST PASSED: Catalyst enables unlimited reactions!")


def run_all_tests():
    """Run all test arc simulation tests."""
    print("\n" + "="*70)
    print("TEST ARC SIMULATION BEHAVIOR TEST SUITE")
    print("="*70)
    print("\nVerifying that test arcs (read arcs) properly model catalysts:")
    print("  1. Check enablement (require tokens >= weight)")
    print("  2. Do NOT consume tokens during firing")
    print("  3. Enable unlimited reactions (catalyst never depleted)")
    
    try:
        test_immediate_with_test_arc()
        test_continuous_with_test_arc()
        test_multiple_firings()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED! ✅")
        print("="*70)
        print("\nTest arc simulation behavior is CORRECT:")
        print("  ✓ Immediate transitions: catalyst NOT consumed")
        print("  ✓ Continuous transitions: catalyst NOT consumed")
        print("  ✓ Multiple firings: catalyst enables unlimited reactions")
        print("\nBiological interpretation:")
        print("  Enzymes act as TRUE catalysts - they enable reactions")
        print("  without being consumed. This is the correct biological")
        print("  behavior for Biological Petri Nets!")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
