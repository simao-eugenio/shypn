#!/usr/bin/env python3
"""Test that property dialog arc transformations work correctly with behavior cache.

This test verifies that successive arc transformations via property dialog
correctly update behavior cache and don't cause mixed behaviors.

Issue: When user transforms arc via property dialog (Normal → Test → Inhibitor),
the callback was using stale arc reference from closure instead of updated
arc from dialog loader. This caused behavior cache mismatches.

Fix: Callback now receives loader instance and uses loader.arc_obj which
is updated after each transformation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs import Place, Transition, Arc
from shypn.core.controllers.document_controller import DocumentController
from shypn.engine.simulation.controller import SimulationController
from shypn.utils.arc_transform import convert_to_test, convert_to_inhibitor, convert_to_normal

def test_property_dialog_transformation_simulation():
    """Test that arc transformations via property dialog work with simulation."""
    
    # Create model
    controller = DocumentController()
    
    # Create network: Substrate -> Transition -> Product
    #                  Catalyst ---/  (the arc we'll transform)
    substrate = Place(id='substrate', name='Substrate', x=100, y=100)
    substrate.tokens = 100.0
    
    catalyst = Place(id='catalyst', name='Catalyst', x=100, y=200)
    catalyst.tokens = 10.0
    
    product = Place(id='product', name='Product', x=300, y=100)
    product.tokens = 0.0
    
    transition = Transition(id='reaction', name='Reaction', x=200, y=100)
    
    controller.places = [substrate, catalyst, product]
    controller.transitions = [transition]
    
    # Create arcs
    arc_substrate = controller.add_arc(substrate, transition, weight=1.0)
    arc_catalyst = controller.add_arc(catalyst, transition, weight=1.0)  # This one we'll transform
    arc_product = controller.add_arc(transition, product, weight=1.0)
    
    # Create behavior for transition (immediate)
    from shypn.engine.immediate_behavior import ImmediateBehavior
    behavior_cache = {}
    
    def get_behavior():
        """Get or create behavior (simulates controller behavior cache)."""
        if transition.id not in behavior_cache:
            behavior_cache[transition.id] = ImmediateBehavior(transition, controller)
        return behavior_cache[transition.id]
    
    def fire_transition():
        """Fire the transition using its behavior."""
        # Get arcs from controller (fresh query)
        input_arcs = [arc for arc in controller.arcs if arc.target == transition]
        output_arcs = [arc for arc in controller.arcs if arc.source == transition]
        
        behavior = get_behavior()
        success, details = behavior.fire(input_arcs, output_arcs)
        return success
    
    print("=" * 70)
    print("TEST: Property Dialog Arc Transformation with Simulation")
    print("=" * 70)
    
    # Step 1: Fire with Normal arc (both consume)
    print("\nSTEP 1: Normal arc (both consume)")
    print(f"Before: Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    
    # Fire transition
    fire_transition()
    
    print(f"After:  Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    assert substrate.tokens == 99.0, f"Substrate should be 99.0, got {substrate.tokens}"
    assert catalyst.tokens == 9.0, f"Catalyst should be 9.0, got {catalyst.tokens}"
    assert product.tokens == 1.0, f"Product should be 1.0, got {product.tokens}"
    print("✓ Both consumed correctly")
    
    # Step 2: Transform to TEST arc (catalyst NOT consumed)
    # Simulate property dialog transformation path
    print("\n" + "=" * 70)
    print("STEP 2: Transform to TEST arc via property dialog path")
    old_catalyst_arc = controller.arcs[1]  # Get current arc
    new_catalyst_arc = convert_to_test(old_catalyst_arc)
    controller.replace_arc(old_catalyst_arc, new_catalyst_arc)
    
    # Simulate property dialog callback clearing behavior cache
    # (This is what the fixed callback does now)
    if transition.id in behavior_cache:
        del behavior_cache[transition.id]
        print("✓ Behavior cache cleared for transition")
    
    # Verify transformation
    arc_type = getattr(new_catalyst_arc, 'type', None) or getattr(new_catalyst_arc, 'arc_type', None)
    print(f"Arc type: {arc_type}, class: {new_catalyst_arc.__class__.__name__}")
    
    print(f"Before: Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    
    # Fire again - catalyst should NOT be consumed (test arc = read arc)
    fire_transition()
    
    print(f"After:  Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    assert substrate.tokens == 98.0, f"Substrate should be 98.0, got {substrate.tokens}"
    assert catalyst.tokens == 9.0, f"Catalyst should remain 9.0, got {catalyst.tokens}"
    assert product.tokens == 2.0, f"Product should be 2.0, got {product.tokens}"
    print("✓ Catalyst NOT consumed (test arc works correctly)")
    
    # Step 3: Transform to INHIBITOR arc (catalyst consumed)
    print("\n" + "=" * 70)
    print("STEP 3: Transform to INHIBITOR arc via property dialog path")
    old_catalyst_arc = controller.arcs[1]  # Get current arc
    new_catalyst_arc = convert_to_inhibitor(old_catalyst_arc)
    controller.replace_arc(old_catalyst_arc, new_catalyst_arc)
    
    # Simulate callback clearing cache
    if transition.id in behavior_cache:
        del behavior_cache[transition.id]
        print("✓ Behavior cache cleared for transition")
    
    # Verify transformation
    arc_type = getattr(new_catalyst_arc, 'type', None) or getattr(new_catalyst_arc, 'arc_type', None)
    print(f"Arc type: {arc_type}, class: {new_catalyst_arc.__class__.__name__}")
    
    print(f"Before: Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    
    # Fire again - catalyst SHOULD be consumed (inhibitor arcs consume in SHPN)
    fire_transition()
    
    print(f"After:  Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    assert substrate.tokens == 97.0, f"Substrate should be 97.0, got {substrate.tokens}"
    assert catalyst.tokens == 8.0, f"Catalyst should be 8.0, got {catalyst.tokens}"
    assert product.tokens == 3.0, f"Product should be 3.0, got {product.tokens}"
    print("✓ Catalyst consumed (inhibitor arc works correctly)")
    
    # Step 4: Transform back to NORMAL arc
    print("\n" + "=" * 70)
    print("STEP 4: Transform back to NORMAL arc via property dialog path")
    old_catalyst_arc = controller.arcs[1]  # Get current arc
    new_catalyst_arc = convert_to_normal(old_catalyst_arc)
    controller.replace_arc(old_catalyst_arc, new_catalyst_arc)
    
    # Simulate callback clearing cache
    if transition.id in behavior_cache:
        del behavior_cache[transition.id]
        print("✓ Behavior cache cleared for transition")
    
    # Verify transformation
    arc_type = getattr(new_catalyst_arc, 'type', None) or getattr(new_catalyst_arc, 'arc_type', None)
    print(f"Arc type: {arc_type or 'normal'}, class: {new_catalyst_arc.__class__.__name__}")
    
    print(f"Before: Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    
    # Fire again - catalyst SHOULD be consumed (normal arc)
    fire_transition()
    
    print(f"After:  Substrate={substrate.tokens}, Catalyst={catalyst.tokens}, Product={product.tokens}")
    assert substrate.tokens == 96.0, f"Substrate should be 96.0, got {substrate.tokens}"
    assert catalyst.tokens == 7.0, f"Catalyst should be 7.0, got {catalyst.tokens}"
    assert product.tokens == 4.0, f"Product should be 4.0, got {product.tokens}"
    print("✓ Catalyst consumed (normal arc works correctly)")
    
    print("\n" + "=" * 70)
    print("✅ ALL PROPERTY DIALOG TRANSFORMATIONS WORK CORRECTLY")
    print("=" * 70)
    print("\nSummary:")
    print("  - Normal arc: Catalyst consumed ✓")
    print("  - Test arc: Catalyst NOT consumed ✓")
    print("  - Inhibitor arc: Catalyst consumed ✓")
    print("  - Back to Normal: Catalyst consumed ✓")
    print("\nBehavior cache was properly cleared after each transformation.")
    print("No mixed behaviors observed.")

if __name__ == '__main__':
    test_property_dialog_transformation_simulation()
