#!/usr/bin/env python3
"""
Test the model workspace/projects/My_Project/models/test.shy

This model has:
- P1: substrate (250 tokens) → T1 (normal arc)
- P3: catalyst (1 token) → T1 (TEST ARC - should NOT consume)
- T1 → P2: product (0 tokens)

The test arc from P3 should enable the transition to fire, but P3's
tokens should remain at 1.0 (not consumed).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.continuous_behavior import ContinuousBehavior
from shypn.engine.immediate_behavior import ImmediateBehavior


def test_model_with_test_arc():
    """Load and test the model."""
    print("\n" + "=" * 70)
    print("TESTING MODEL: workspace/projects/My_Project/models/test.shy")
    print("=" * 70)
    print()
    
    # Load model
    model_path = 'workspace/projects/My_Project/models/test.shy'
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return 1
    
    model = DocumentModel.load_from_file(model_path)
    
    if model is None:
        print(f"❌ Failed to load model")
        return 1
    
    print(f"✓ Model loaded successfully")
    print()
    
    # Display model structure
    print("Model Structure:")
    print(f"  Places: {len(model.places)}")
    for p in model.places:
        print(f"    {p.id}: {p.name} = {p.tokens} tokens")
    
    print(f"  Transitions: {len(model.transitions)}")
    for t in model.transitions:
        print(f"    {t.id}: {t.name} ({t.transition_type})")
    
    print(f"  Arcs: {len(model.arcs)}")
    for arc in model.arcs:
        arc_type = getattr(arc, 'arc_type', 'normal')
        consumes = getattr(arc, 'consumes_tokens', lambda: True)()
        print(f"    {arc.id}: {arc.source_id} → {arc.target_id} (type={arc_type}, consumes={consumes})")
    
    print()
    
    # Find the test arc and verify it's correctly identified
    test_arcs = [arc for arc in model.arcs if getattr(arc, 'arc_type', 'normal') == 'test']
    
    if not test_arcs:
        print("❌ No test arcs found in model!")
        print("   Expected: A3 (P3 → T1) should be a test arc")
        return 1
    
    print(f"✓ Found {len(test_arcs)} test arc(s):")
    for arc in test_arcs:
        print(f"    {arc.id}: {arc.source_id} → {arc.target_id}")
        print(f"      arc_type = {arc.arc_type}")
        print(f"      consumes_tokens() = {arc.consumes_tokens()}")
    print()
    
    # Get places
    p1 = next((p for p in model.places if p.id == 'P1'), None)
    p2 = next((p for p in model.places if p.id == 'P2'), None)
    p3 = next((p for p in model.places if p.id == 'P3'), None)  # Catalyst
    t1 = next((t for t in model.transitions if t.id == 'T1'), None)
    
    if not all([p1, p2, p3, t1]):
        print("❌ Missing expected components")
        return 1
    
    print("Initial Marking:")
    print(f"  P1 (substrate): {p1.tokens}")
    print(f"  P2 (product):   {p2.tokens}")
    print(f"  P3 (catalyst):  {p3.tokens} ← TEST ARC (should NOT be consumed)")
    print()
    
    # Get transition behavior
    if t1.transition_type == 'continuous':
        behavior = ContinuousBehavior(t1, model)
        print(f"Transition T1: Continuous (rate={t1.rate_function})")
        print()
        
        # Get arcs
        input_arcs = [arc for arc in model.arcs if arc.target_id == t1.id]
        output_arcs = [arc for arc in model.arcs if arc.source_id == t1.id]
        
        print(f"Input arcs to T1:")
        for arc in input_arcs:
            arc_type = getattr(arc, 'arc_type', 'normal')
            print(f"  {arc.id}: {arc.source_id} → T1 (type={arc_type})")
        
        print(f"Output arcs from T1:")
        for arc in output_arcs:
            print(f"  {arc.id}: T1 → {arc.target_id}")
        print()
        
        # Simulate over small time steps
        print("Simulating 10 time steps (dt=0.1):")
        print("-" * 70)
        
        for i in range(10):
            dt = 0.1
            success, details = behavior.integrate_step(dt, input_arcs, output_arcs)
            
            print(f"  Step {i+1}: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}, P3={p3.tokens:.2f}")
            
            if not success:
                print(f"    Failed: {details.get('reason', 'unknown')}")
                break
        
        print()
        
    else:
        behavior = ImmediateBehavior(t1, model)
        print(f"Transition T1: {t1.transition_type}")
        print()
        
        # Get arcs
        input_arcs = [arc for arc in model.arcs if arc.target_id == t1.id]
        output_arcs = [arc for arc in model.arcs if arc.source_id == t1.id]
        
        # Fire 10 times
        print("Firing 10 times:")
        print("-" * 70)
        
        for i in range(10):
            success, details = behavior.fire(input_arcs, output_arcs)
            
            print(f"  Firing {i+1}: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}, P3={p3.tokens:.2f}")
            
            if not success:
                print(f"    Failed: {details.get('reason', 'unknown')}")
                break
        
        print()
    
    # Final check
    print("Final Marking:")
    print(f"  P1 (substrate): {p1.tokens} (should have decreased)")
    print(f"  P2 (product):   {p2.tokens} (should have increased)")
    print(f"  P3 (catalyst):  {p3.tokens} (should STILL be 1.0)")
    print()
    
    if p3.tokens == 1.0:
        print("=" * 70)
        print("✓ TEST ARC WORKING CORRECTLY")
        print("=" * 70)
        print()
        print("P3 catalyst tokens remain at 1.0 - test arc does NOT consume")
        print()
        return 0
    else:
        print("=" * 70)
        print("❌ BUG DETECTED: TEST ARC CONSUMED TOKENS")
        print("=" * 70)
        print()
        print(f"P3 should be 1.0 but is {p3.tokens}")
        print("Test arcs should be READ ARCS (check presence without consuming)")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(test_model_with_test_arc())
