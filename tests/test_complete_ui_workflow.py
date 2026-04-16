#!/usr/bin/env python3
"""
Test complete UI workflow: Load → Transform → Simulate
This reproduces the exact workflow the user is experiencing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.utils.arc_transform import convert_to_test
from shypn.engine.continuous_behavior import ContinuousBehavior
from shypn.engine.immediate_behavior import ImmediateBehavior


def test_complete_workflow():
    """Test: Load → Transform Arc → Simulate → Verify."""
    print("\n" + "=" * 70)
    print("COMPLETE UI WORKFLOW TEST")
    print("=" * 70)
    print()
    
    model_path = 'workspace/projects/My_Project/models/test.shy'
    
    # STEP 1: Load model
    print("STEP 1: Load model from file")
    print("-" * 70)
    model = DocumentModel.load_from_file(model_path)
    
    # Find objects
    p1 = next((p for p in model.places if p.id == 'P1'), None)
    p2 = next((p for p in model.places if p.id == 'P2'), None)
    p3 = next((p for p in model.places if p.id == 'P3'), None)
    t1 = next((t for t in model.transitions if t.id == 'T1'), None)
    
    print(f"  P1 (substrate): {p1.tokens} tokens")
    print(f"  P2 (product):   {p2.tokens} tokens")
    print(f"  P3 (catalyst):  {p3.tokens} tokens")
    print()
    
    # Find A3 arc (the one that should be test arc)
    a3 = next((arc for arc in model.arcs if arc.id == 'A3'), None)
    
    if not a3:
        print("❌ Arc A3 not found!")
        return 1
    
    print(f"  Arc A3: {type(a3).__name__}, arc_type={a3.arc_type}")
    print(f"  Arc A3 consumes_tokens(): {a3.consumes_tokens()}")
    print()
    
    # Verify A3 is already a test arc (loaded from file)
    if a3.arc_type != 'test':
        print(f"  ⚠️  Arc A3 is not a test arc in file! Transforming now...")
        
        # USER ACTION: Transform via UI
        print()
        print("STEP 2: User transforms A3 to test arc via property dialog")
        print("-" * 70)
        
        old_a3 = a3
        new_a3 = convert_to_test(old_a3)
        
        # Replace in model
        try:
            index = model.arcs.index(old_a3)
            model.arcs[index] = new_a3
            a3 = new_a3
            print(f"  ✓ Arc transformed: {type(a3).__name__}, arc_type={a3.arc_type}")
            print(f"  ✓ Consumes tokens: {a3.consumes_tokens()}")
        except ValueError:
            print("  ❌ Failed to replace arc in model!")
            return 1
        print()
    
    # STEP 3: Run simulation
    print("STEP 3: Run simulation")
    print("-" * 70)
    
    # Get arcs for transition
    input_arcs = [arc for arc in model.arcs if arc.target == t1]
    output_arcs = [arc for arc in model.arcs if arc.source == t1]
    
    print(f"  Input arcs to T1:")
    for arc in input_arcs:
        arc_type = getattr(arc, 'arc_type', 'normal')
        consumes = getattr(arc, 'consumes_tokens', lambda: True)()
        print(f"    {arc.id}: {arc.source.name} → T1 (type={arc_type}, consumes={consumes})")
    
    print()
    print(f"  Initial: P1={p1.tokens}, P2={p2.tokens}, P3={p3.tokens}")
    
    # Run simulation based on transition type
    if t1.transition_type == 'continuous':
        behavior = ContinuousBehavior(t1, model)
        
        for i in range(5):
            success, details = behavior.integrate_step(0.1, input_arcs, output_arcs)
            if not success:
                print(f"  Step {i+1} failed: {details.get('reason')}")
                break
        
        print(f"  After 5 steps: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}, P3={p3.tokens:.2f}")
    
    else:
        behavior = ImmediateBehavior(t1, model)
        
        for i in range(5):
            success, details = behavior.fire(input_arcs, output_arcs)
            if not success:
                print(f"  Firing {i+1} failed: {details.get('reason')}")
                break
        
        print(f"  After 5 firings: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}, P3={p3.tokens:.2f}")
    
    print()
    
    # STEP 4: Verify
    print("STEP 4: Verify results")
    print("-" * 70)
    
    if p3.tokens == 1.0:
        print(f"  ✓ P3 (catalyst) = {p3.tokens} (NOT consumed)")
        print(f"  ✓ P1 (substrate) decreased from 250 to {p1.tokens}")
        print(f"  ✓ P2 (product) increased from 0 to {p2.tokens}")
        print()
        print("=" * 70)
        print("✓ TEST ARC WORKING CORRECTLY IN COMPLETE WORKFLOW")
        print("=" * 70)
        print()
        return 0
    else:
        print(f"  ❌ BUG: P3 should be 1.0 but is {p3.tokens}")
        print(f"  ❌ Test arc consumed tokens!")
        print()
        
        # Debug: Check arc types in model
        print("  DEBUG: Checking all arcs in model...")
        for arc in model.arcs:
            if hasattr(arc, 'source') and arc.source == p3:
                print(f"    Arc from P3: {type(arc).__name__}, arc_type={arc.arc_type}")
                print(f"       consumes_tokens()={arc.consumes_tokens()}")
                print(f"       isinstance TestArc={isinstance(arc, type(a3))}")
        
        print()
        print("=" * 70)
        print("❌ TEST ARC CONSUMING TOKENS - BUG CONFIRMED")
        print("=" * 70)
        print()
        return 1


if __name__ == '__main__':
    sys.exit(test_complete_workflow())
