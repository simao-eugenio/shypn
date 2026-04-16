#!/usr/bin/env python3
"""
Test successive arc transformations with simulation.

This tests the scenario the user reported:
1. Create a normal arc
2. Transform to test arc
3. Verify test arc doesn't consume
4. Transform to inhibitor arc
5. Verify inhibitor arc consumes
6. Transform back to test arc
7. Verify test arc doesn't consume again
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.core.controllers.document_controller import DocumentController
from shypn.data.canvas.id_manager import IDManager
from shypn.utils.arc_transform import convert_to_test, convert_to_inhibitor, convert_to_normal
from shypn.engine.immediate_behavior import ImmediateBehavior


def test_successive_transformations_with_simulation():
    """Test that successive arc transformations work correctly during simulation."""
    print("\n" + "=" * 70)
    print("TEST: Successive Arc Transformations with Simulation")
    print("=" * 70)
    print()
    
    # Create model
    id_manager = IDManager()
    controller = DocumentController(id_manager)
    
    substrate = Place(x=100, y=100, id='substrate', name='Substrate')
    substrate.tokens = 100.0
    
    catalyst = Place(x=100, y=200, id='catalyst', name='Catalyst')
    catalyst.tokens = 10.0
    
    product = Place(x=300, y=100, id='product', name='Product')
    product.tokens = 0.0
    
    reaction = Transition(x=200, y=100, id='reaction', name='Reaction')
    
    controller.places = [substrate, catalyst, product]
    controller.transitions = [reaction]
    
    # Create arcs
    arc_substrate = controller.add_arc(substrate, reaction, weight=1.0)
    arc_catalyst = controller.add_arc(catalyst, reaction, weight=1.0)  # Will transform this
    arc_product = controller.add_arc(reaction, product, weight=1.0)
    
    # Simulation behavior cache
    behavior_cache = {}
    
    def get_behavior(transition):
        """Get or create behavior (simulates controller behavior cache)."""
        if transition.id not in behavior_cache:
            behavior_cache[transition.id] = ImmediateBehavior(transition, controller)
        return behavior_cache[transition.id]
    
    def fire_and_check(step_num, expected_catalyst_tokens, transformation_name):
        """Fire transition and verify catalyst tokens."""
        print(f"STEP {step_num}: After {transformation_name}")
        print("-" * 70)
        
        # Get arcs from controller (fresh query)
        input_arcs = [arc for arc in controller.arcs if arc.target == reaction]
        output_arcs = [arc for arc in controller.arcs if arc.source == reaction]
        
        print(f"  Input arcs:")
        for arc in input_arcs:
            arc_type = getattr(arc, 'arc_type', 'normal')
            consumes = getattr(arc, 'consumes_tokens', lambda: True)()
            print(f"    {arc.source.name}: type={arc_type}, consumes={consumes}, instance={type(arc).__name__}")
        
        print(f"  Before firing: Substrate={substrate.tokens:.1f}, Catalyst={catalyst.tokens:.1f}, Product={product.tokens:.1f}")
        
        # Clear behavior cache to force recreation (simulates UI cache invalidation)
        behavior_cache.clear()
        
        # Fire transition
        behavior = get_behavior(reaction)
        success, details = behavior.fire(input_arcs, output_arcs)
        
        print(f"  After firing:  Substrate={substrate.tokens:.1f}, Catalyst={catalyst.tokens:.1f}, Product={product.tokens:.1f}")
        
        if catalyst.tokens != expected_catalyst_tokens:
            print(f"  ❌ BUG: Expected catalyst={expected_catalyst_tokens}, got {catalyst.tokens}")
            print(f"         {transformation_name} arc behavior is incorrect!")
            return False
        else:
            print(f"  ✓ Correct: Catalyst={catalyst.tokens:.1f} (expected {expected_catalyst_tokens})")
        
        print()
        return True
    
    # STEP 1: Normal arc (both substrate and catalyst consumed)
    success = fire_and_check(1, 9.0, "Normal arc (initial)")
    if not success:
        return 1
    
    # STEP 2: Transform to TEST arc (catalyst should NOT be consumed)
    old_arc = arc_catalyst
    new_arc = convert_to_test(old_arc)
    controller.replace_arc(old_arc, new_arc)
    arc_catalyst = new_arc
    
    success = fire_and_check(2, 9.0, "TEST arc (catalyst not consumed)")
    if not success:
        return 1
    
    # STEP 3: Fire again with test arc (catalyst still not consumed)
    success = fire_and_check(3, 9.0, "TEST arc again")
    if not success:
        return 1
    
    # STEP 4: Transform to INHIBITOR arc (catalyst should be consumed)
    old_arc = arc_catalyst
    new_arc = convert_to_inhibitor(old_arc)
    controller.replace_arc(old_arc, new_arc)
    arc_catalyst = new_arc
    
    success = fire_and_check(4, 8.0, "INHIBITOR arc (catalyst consumed)")
    if not success:
        return 1
    
    # STEP 5: Transform back to TEST arc (catalyst should NOT be consumed)
    old_arc = arc_catalyst
    new_arc = convert_to_test(old_arc)
    controller.replace_arc(old_arc, new_arc)
    arc_catalyst = new_arc
    
    success = fire_and_check(5, 8.0, "TEST arc again (catalyst not consumed)")
    if not success:
        return 1
    
    # STEP 6: Transform back to NORMAL arc (catalyst should be consumed)
    old_arc = arc_catalyst
    new_arc = convert_to_normal(old_arc)
    controller.replace_arc(old_arc, new_arc)
    arc_catalyst = new_arc
    
    success = fire_and_check(6, 7.0, "NORMAL arc (catalyst consumed)")
    if not success:
        return 1
    
    print("=" * 70)
    print("✓ ALL SUCCESSIVE TRANSFORMATIONS WORK CORRECTLY")
    print("=" * 70)
    print()
    print("Summary:")
    print("  ✓ Normal arc → Test arc → works correctly")
    print("  ✓ Test arc → Inhibitor arc → works correctly")
    print("  ✓ Inhibitor arc → Test arc → works correctly")
    print("  ✓ Test arc → Normal arc → works correctly")
    print("  ✓ Behavior cache cleared between transformations")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(test_successive_transformations_with_simulation())
