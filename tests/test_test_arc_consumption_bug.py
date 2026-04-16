#!/usr/bin/env python3
"""
Test to verify test arcs don't consume tokens.

Test arcs are READ ARCS - they should check token presence WITHOUT consuming.
This is critical for modeling catalysts, enzymes, and regulatory molecules.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.engine.immediate_behavior import ImmediateBehavior
from shypn.engine.timed_behavior import TimedBehavior
from shypn.engine.continuous_behavior import ContinuousBehavior
from shypn.engine.stochastic_behavior import StochasticBehavior


def test_test_arc_no_consumption_immediate():
    """Test that test arcs don't consume in immediate mode."""
    print("=" * 70)
    print("TEST: Test Arc Non-Consumption (Immediate Behavior)")
    print("=" * 70)
    
    # Create enzyme-catalyzed reaction:
    # Substrate + Enzyme -> Product
    # Enzyme modeled as test arc (not consumed)
    
    substrate = Place(x=100, y=100, id='p_substrate', name='Substrate')
    substrate.tokens = 10.0
    
    enzyme = Place(x=100, y=200, id='p_enzyme', name='Enzyme')
    enzyme.tokens = 5.0
    
    product = Place(x=300, y=100, id='p_product', name='Product')
    product.tokens = 0.0
    
    reaction = Transition(id='t_reaction', name='Catalyzed_Reaction', x=200, y=100)
    reaction_behavior = ImmediateBehavior(reaction, None)
    
    # Normal arc: substrate consumed
    arc_substrate = Arc(substrate, reaction, id='a1', name='A1', weight=2.0)
    
    # TEST ARC: enzyme NOT consumed (catalyst)
    arc_enzyme = TestArc(enzyme, reaction, id='a2', name='A2', weight=1.0)
    
    # Output arc: product produced
    arc_product = Arc(reaction, product, id='a3', name='A3', weight=1.0)
    
    print(f"Initial state:")
    print(f"  Substrate: {substrate.tokens} tokens")
    print(f"  Enzyme: {enzyme.tokens} tokens (CATALYST - should not be consumed)")
    print(f"  Product: {product.tokens} tokens")
    print()
    
    # Check that test arc is correctly identified
    print(f"Arc types:")
    print(f"  arc_substrate.arc_type = {arc_substrate.arc_type}")
    print(f"  arc_enzyme.arc_type = {arc_enzyme.arc_type}")
    print(f"  arc_enzyme consumes_tokens() = {arc_enzyme.consumes_tokens()}")
    print()
    
    # Fire transition
    input_arcs = [arc_substrate, arc_enzyme]
    output_arcs = [arc_product]
    
    success, details = reaction_behavior.fire(input_arcs, output_arcs)
    
    print(f"Firing result: {success}")
    print(f"Details: {details}")
    print()
    
    print(f"After firing:")
    print(f"  Substrate: {substrate.tokens} tokens (should be 10 - 2 = 8)")
    print(f"  Enzyme: {enzyme.tokens} tokens (should STILL be 5 - NOT consumed!)")
    print(f"  Product: {product.tokens} tokens (should be 0 + 1 = 1)")
    print()
    
    # Verify
    assert substrate.tokens == 8.0, f"Substrate should be consumed (10-2=8), got {substrate.tokens}"
    assert enzyme.tokens == 5.0, f"❌ BUG: Enzyme should NOT be consumed (5), got {enzyme.tokens}"
    assert product.tokens == 1.0, f"Product should be produced (0+1=1), got {product.tokens}"
    
    print("✓ Test arc correctly NOT consumed (catalyst behavior)")
    print()


def test_test_arc_no_consumption_continuous():
    """Test that test arcs don't consume in continuous mode."""
    print("=" * 70)
    print("TEST: Test Arc Non-Consumption (Continuous Behavior)")
    print("=" * 70)
    
    # Create enzyme-catalyzed reaction in continuous mode
    substrate = Place(x=100, y=100, id='p_substrate', name='Substrate')
    substrate.tokens = 100.0
    
    enzyme = Place(x=100, y=200, id='p_enzyme', name='Enzyme')
    enzyme.tokens = 50.0
    
    product = Place(x=300, y=100, id='p_product', name='Product')
    product.tokens = 0.0
    
    reaction = Transition(id='t_reaction', name='Catalyzed_Reaction', x=200, y=100)
    reaction.rate_constant = 0.5  # Continuous rate
    reaction_behavior = ContinuousBehavior(reaction, None)
    
    # Normal arc: substrate consumed
    arc_substrate = Arc(substrate, reaction, id='a1', name='A1', weight=10.0)
    
    # TEST ARC: enzyme NOT consumed (catalyst)
    arc_enzyme = TestArc(enzyme, reaction, id='a2', name='A2', weight=1.0)
    
    # Output arc: product produced
    arc_product = Arc(reaction, product, id='a3', name='A3', weight=5.0)
    
    print(f"Initial state:")
    print(f"  Substrate: {substrate.tokens} tokens")
    print(f"  Enzyme: {enzyme.tokens} tokens (CATALYST - should not be consumed)")
    print(f"  Product: {product.tokens} tokens")
    print()
    
    print(f"Arc types:")
    print(f"  arc_substrate.arc_type = {arc_substrate.arc_type}")
    print(f"  arc_enzyme.arc_type = {arc_enzyme.arc_type}")
    print(f"  arc_enzyme.consumes_tokens() = {arc_enzyme.consumes_tokens()}")
    print()
    
    # Integrate over time step
    input_arcs = [arc_substrate, arc_enzyme]
    output_arcs = [arc_product]
    dt = 0.1  # Small time step
    
    success, details = reaction_behavior.integrate_step(dt, input_arcs, output_arcs)
    
    print(f"Integration result: {success}")
    print(f"Details: {details}")
    print()
    
    print(f"After integration (dt={dt}):")
    print(f"  Substrate: {substrate.tokens} tokens (should decrease)")
    print(f"  Enzyme: {enzyme.tokens} tokens (should STILL be 50 - NOT consumed!)")
    print(f"  Product: {product.tokens} tokens (should increase)")
    print()
    
    # Verify enzyme not consumed
    assert enzyme.tokens == 50.0, f"❌ BUG: Enzyme should NOT be consumed (50), got {enzyme.tokens}"
    assert substrate.tokens < 100.0, f"Substrate should be consumed, got {substrate.tokens}"
    assert product.tokens > 0.0, f"Product should be produced, got {product.tokens}"
    
    print("✓ Test arc correctly NOT consumed in continuous mode")
    print()


def test_multiple_firings_test_arc():
    """Test that enzyme remains unchanged over multiple firings."""
    print("=" * 70)
    print("TEST: Test Arc Over Multiple Firings")
    print("=" * 70)
    
    # Create reaction that fires 5 times
    substrate = Place(x=100, y=100, id='p_substrate', name='Substrate')
    substrate.tokens = 100.0
    
    enzyme = Place(x=100, y=200, id='p_enzyme', name='Enzyme')
    enzyme.tokens = 10.0
    
    product = Place(x=300, y=100, id='p_product', name='Product')
    product.tokens = 0.0
    
    reaction = Transition(id='t_reaction', name='Catalyzed_Reaction', x=200, y=100)
    reaction_behavior = ImmediateBehavior(reaction, None)
    
    arc_substrate = Arc(substrate, reaction, id='a1', name='A1', weight=5.0)
    arc_enzyme = TestArc(enzyme, reaction, id='a2', name='A2', weight=1.0)
    arc_product = Arc(reaction, product, id='a3', name='A3', weight=2.0)
    
    print(f"Initial state:")
    print(f"  Substrate: {substrate.tokens}")
    print(f"  Enzyme: {enzyme.tokens} (should remain constant)")
    print(f"  Product: {product.tokens}")
    print()
    
    input_arcs = [arc_substrate, arc_enzyme]
    output_arcs = [arc_product]
    
    # Fire 5 times
    for i in range(5):
        success, details = reaction_behavior.fire(input_arcs, output_arcs)
        print(f"Firing {i+1}: Substrate={substrate.tokens}, Enzyme={enzyme.tokens}, Product={product.tokens}")
        
        # Check enzyme unchanged
        assert enzyme.tokens == 10.0, f"❌ BUG: Enzyme consumed in firing {i+1}! Got {enzyme.tokens}"
    
    print()
    print(f"Final state:")
    print(f"  Substrate: {substrate.tokens} (100 - 5*5 = 75)")
    print(f"  Enzyme: {enzyme.tokens} (should STILL be 10)")
    print(f"  Product: {product.tokens} (0 + 5*2 = 10)")
    print()
    
    assert substrate.tokens == 75.0, f"Substrate should be 75, got {substrate.tokens}"
    assert enzyme.tokens == 10.0, f"❌ BUG: Enzyme should be 10, got {enzyme.tokens}"
    assert product.tokens == 10.0, f"Product should be 10, got {product.tokens}"
    
    print("✓ Enzyme correctly unchanged over 5 firings")
    print()


def test_mixed_arc_types():
    """Test normal arc vs test arc consumption in same transition."""
    print("=" * 70)
    print("TEST: Mixed Arc Types (Normal + Test)")
    print("=" * 70)
    
    # Reaction: Substrate1 + Substrate2 + Enzyme -> Product
    # Substrate1, Substrate2: normal arcs (consumed)
    # Enzyme: test arc (NOT consumed)
    
    substrate1 = Place(x=100, y=100, id='p_sub1', name='Substrate1')
    substrate1.tokens = 20.0
    
    substrate2 = Place(x=100, y=150, id='p_sub2', name='Substrate2')
    substrate2.tokens = 15.0
    
    enzyme = Place(x=100, y=200, id='p_enzyme', name='Enzyme')
    enzyme.tokens = 5.0
    
    product = Place(x=300, y=100, id='p_product', name='Product')
    product.tokens = 0.0
    
    reaction = Transition(id='t_reaction', name='Multi_Substrate_Reaction', x=200, y=150)
    reaction_behavior = ImmediateBehavior(reaction, None)
    
    # Normal arcs (consuming)
    arc_sub1 = Arc(substrate1, reaction, id='a1', name='A1', weight=3.0)
    arc_sub2 = Arc(substrate2, reaction, id='a2', name='A2', weight=2.0)
    
    # Test arc (non-consuming)
    arc_enzyme = TestArc(enzyme, reaction, id='a3', name='A3', weight=1.0)
    
    # Output
    arc_product = Arc(reaction, product, id='a4', name='A4', weight=1.0)
    
    print(f"Initial state:")
    print(f"  Substrate1: {substrate1.tokens} (NORMAL arc - will be consumed)")
    print(f"  Substrate2: {substrate2.tokens} (NORMAL arc - will be consumed)")
    print(f"  Enzyme: {enzyme.tokens} (TEST arc - should NOT be consumed)")
    print(f"  Product: {product.tokens}")
    print()
    
    input_arcs = [arc_sub1, arc_sub2, arc_enzyme]
    output_arcs = [arc_product]
    
    success, details = reaction_behavior.fire(input_arcs, output_arcs)
    
    print(f"After firing:")
    print(f"  Substrate1: {substrate1.tokens} (should be 20 - 3 = 17)")
    print(f"  Substrate2: {substrate2.tokens} (should be 15 - 2 = 13)")
    print(f"  Enzyme: {enzyme.tokens} (should STILL be 5)")
    print(f"  Product: {product.tokens} (should be 0 + 1 = 1)")
    print()
    
    assert substrate1.tokens == 17.0, f"Substrate1 should be consumed, got {substrate1.tokens}"
    assert substrate2.tokens == 13.0, f"Substrate2 should be consumed, got {substrate2.tokens}"
    assert enzyme.tokens == 5.0, f"❌ BUG: Enzyme should NOT be consumed, got {enzyme.tokens}"
    assert product.tokens == 1.0, f"Product should be produced, got {product.tokens}"
    
    print("✓ Normal arcs consumed, test arc NOT consumed")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("TEST ARC CONSUMPTION BUG VERIFICATION")
    print("=" * 70)
    print()
    
    try:
        test_test_arc_no_consumption_immediate()
        test_multiple_firings_test_arc()
        test_mixed_arc_types()
        test_test_arc_no_consumption_continuous()
        
        print("=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        print()
        print("Test arcs correctly implement READ semantics:")
        print("  ✓ Test arcs check token presence")
        print("  ✓ Test arcs do NOT consume tokens")
        print("  ✓ Test arcs model catalysts/enzymes correctly")
        print("  ✓ Behavior consistent across immediate and continuous modes")
        print()
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 70)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 70)
        print()
        print("BUG CONFIRMED: Test arcs are consuming tokens!")
        print("Test arcs should be READ ARCS - check without consuming.")
        print()
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
