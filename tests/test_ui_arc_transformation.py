#!/usr/bin/env python3
"""
Test arc type transformation through UI simulation.

This tests the specific scenario the user reported:
1. Create a normal arc
2. Transform to test arc via UI (property dialog or context menu)
3. Verify the arc is actually a TestArc instance
4. Verify the arc does NOT consume tokens
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.core.controllers.document_controller import DocumentController
from shypn.data.canvas.id_manager import IDManager
from shypn.utils.arc_transform import convert_to_test, is_test
from shypn.engine.immediate_behavior import ImmediateBehavior


def test_ui_arc_transformation():
    """Simulate UI arc transformation workflow."""
    print("\n" + "=" * 70)
    print("TEST: UI Arc Type Transformation (Normal → Test)")
    print("=" * 70)
    print()
    
    # Create model with DocumentController (simulates UI)
    id_manager = IDManager()
    controller = DocumentController(id_manager)
    
    # Create places and transition
    substrate = Place(x=100, y=100, id='substrate', name='Substrate')
    substrate.tokens = 10.0
    
    enzyme = Place(x=100, y=200, id='enzyme', name='Enzyme')
    enzyme.tokens = 5.0
    
    product = Place(x=300, y=100, id='product', name='Product')
    product.tokens = 0.0
    
    reaction = Transition(x=200, y=100, id='reaction', name='Reaction')
    
    controller.places = [substrate, enzyme, product]
    controller.transitions = [reaction]
    
    # Create arcs using controller (simulates UI arc creation)
    arc_substrate = controller.add_arc(substrate, reaction, weight=1.0)
    arc_enzyme = controller.add_arc(enzyme, reaction, weight=1.0)  # Normal arc initially
    arc_product = controller.add_arc(reaction, product, weight=1.0)
    
    print("Initial Arc Configuration:")
    print(f"  arc_substrate: {type(arc_substrate).__name__}, arc_type={arc_substrate.arc_type}")
    print(f"  arc_enzyme: {type(arc_enzyme).__name__}, arc_type={arc_enzyme.arc_type}")
    print(f"  arc_product: {type(arc_product).__name__}, arc_type={arc_product.arc_type}")
    print()
    
    # Store reference to enzyme arc (this is what UI dialogs do)
    ui_arc_reference = arc_enzyme
    
    print("Step 1: User opens arc property dialog for enzyme arc")
    print(f"  Dialog arc reference: {type(ui_arc_reference).__name__}")
    print(f"  Arc type: {ui_arc_reference.arc_type}")
    print()
    
    # Transform to test arc (simulates user selecting "Test Arc" in dropdown)
    print("Step 2: User changes arc type to 'Test' and clicks Apply")
    new_arc = convert_to_test(ui_arc_reference)
    
    # Replace in model (this is what the property dialog does)
    controller.replace_arc(ui_arc_reference, new_arc)
    
    print(f"  Transformation complete")
    print(f"  Old arc: {type(ui_arc_reference).__name__}, arc_type={ui_arc_reference.arc_type}")
    print(f"  New arc: {type(new_arc).__name__}, arc_type={new_arc.arc_type}")
    print(f"  New arc is TestArc: {isinstance(new_arc, TestArc)}")
    print(f"  New arc consumes: {new_arc.consumes_tokens()}")
    print()
    
    # Verify arc is in controller's arc list
    print("Step 3: Verify arc is properly stored in model")
    enzyme_arcs = [arc for arc in controller.arcs if arc.source == enzyme]
    
    if len(enzyme_arcs) != 1:
        print(f"  ❌ Expected 1 arc from enzyme, found {len(enzyme_arcs)}")
        return 1
    
    stored_arc = enzyme_arcs[0]
    print(f"  Arc stored in model: {type(stored_arc).__name__}")
    print(f"  Arc type: {stored_arc.arc_type}")
    print(f"  Is TestArc instance: {isinstance(stored_arc, TestArc)}")
    print(f"  Consumes tokens: {stored_arc.consumes_tokens()}")
    print()
    
    if not isinstance(stored_arc, TestArc):
        print("❌ BUG: Arc stored in model is not TestArc instance!")
        print(f"   Type: {type(stored_arc).__name__}")
        return 1
    
    # Verify firing behavior
    print("Step 4: Fire transition and verify enzyme not consumed")
    
    # Get arcs for firing
    input_arcs = [arc for arc in controller.arcs if arc.target == reaction]
    output_arcs = [arc for arc in controller.arcs if arc.source == reaction]
    
    print(f"  Input arcs: {len(input_arcs)}")
    for arc in input_arcs:
        print(f"    {type(arc).__name__}: {arc.source.name} → {arc.target.name}")
        print(f"      arc_type={arc.arc_type}, consumes={arc.consumes_tokens()}")
    
    print()
    print(f"  Before firing: Substrate={substrate.tokens}, Enzyme={enzyme.tokens}, Product={product.tokens}")
    
    # Fire using behavior
    behavior = ImmediateBehavior(reaction, None)
    success, details = behavior.fire(input_arcs, output_arcs)
    
    print(f"  After firing: Substrate={substrate.tokens}, Enzyme={enzyme.tokens}, Product={product.tokens}")
    print()
    
    # Verify
    if substrate.tokens != 9.0:
        print(f"❌ Substrate should be 9.0, got {substrate.tokens}")
        return 1
    
    if enzyme.tokens != 5.0:
        print(f"❌ BUG: Enzyme should still be 5.0 (not consumed), got {enzyme.tokens}")
        print("   Test arc is consuming tokens!")
        return 1
    
    if product.tokens != 1.0:
        print(f"❌ Product should be 1.0, got {product.tokens}")
        return 1
    
    print("=" * 70)
    print("✓ UI ARC TRANSFORMATION WORKING CORRECTLY")
    print("=" * 70)
    print()
    print("Summary:")
    print("  ✓ Arc transformed from Arc to TestArc")
    print("  ✓ Arc properly stored in model as TestArc instance")
    print("  ✓ Test arc does NOT consume tokens during firing")
    print("  ✓ UI workflow simulated successfully")
    print()
    
    return 0


def test_multiple_transformations():
    """Test successive transformations (normal → test → inhibitor → test)."""
    print("\n" + "=" * 70)
    print("TEST: Multiple Successive Transformations")
    print("=" * 70)
    print()
    
    from shypn.utils.arc_transform import convert_to_inhibitor, convert_to_normal
    
    # Create simple model
    id_manager = IDManager()
    controller = DocumentController(id_manager)
    
    p1 = Place(x=100, y=100, id='p1', name='P1')
    p1.tokens = 10.0
    
    t1 = Transition(x=200, y=100, id='t1', name='T1')
    
    controller.places = [p1]
    controller.transitions = [t1]
    
    # Create normal arc
    arc = controller.add_arc(p1, t1, weight=1.0)
    
    print(f"Initial: {type(arc).__name__}, arc_type={arc.arc_type}")
    
    # Transform: normal → test
    arc = convert_to_test(arc)
    controller.replace_arc(controller.arcs[0], arc)
    print(f"After → test: {type(arc).__name__}, arc_type={arc.arc_type}, consumes={arc.consumes_tokens()}")
    
    if not isinstance(arc, TestArc):
        print("❌ Arc should be TestArc instance!")
        return 1
    
    # Transform: test → inhibitor
    arc = convert_to_inhibitor(arc)
    controller.replace_arc(controller.arcs[0], arc)
    print(f"After → inhibitor: {type(arc).__name__}, arc_type={arc.arc_type}")
    
    # Transform: inhibitor → test
    arc = convert_to_test(controller.arcs[0])
    controller.replace_arc(controller.arcs[0], arc)
    print(f"After → test: {type(arc).__name__}, arc_type={arc.arc_type}, consumes={arc.consumes_tokens()}")
    
    if not isinstance(arc, TestArc):
        print("❌ Arc should be TestArc instance after re-transformation!")
        return 1
    
    if arc.consumes_tokens():
        print("❌ Test arc should NOT consume tokens!")
        return 1
    
    print()
    print("✓ Multiple transformations work correctly")
    print()
    
    return 0


def main():
    """Run all tests."""
    try:
        result = test_ui_arc_transformation()
        if result != 0:
            return result
        
        result = test_multiple_transformations()
        if result != 0:
            return result
        
        print("=" * 70)
        print("ALL UI TRANSFORMATION TESTS PASSED ✓")
        print("=" * 70)
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
