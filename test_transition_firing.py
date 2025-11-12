#!/usr/bin/env python3
"""Test transition firing for test.shy model.

Model structure:
- Places: P1(1), P2(1), P4(0), P5(0)  [initial marking in parentheses]
- Transitions: T1, T2 (timed), T3, T4 (stochastic sources)

Arc connections:
- T3 → P4 (source transition produces tokens)
- T4 → P5 (source transition produces tokens)
- P4 → T1 → P1 (T1 consumes P4, produces P1)
- P2 → T1 (T1 also consumes P2)
- P1 → T2 → P2 (T2 consumes P1, produces P2)
- P5 → T2 (T2 also consumes P5)

Expected behavior:
1. Initially: P1=1, P2=1, P4=0, P5=0
2. T1 needs: P2=1 AND P4=1 → BLOCKED (P4=0)
3. T2 needs: P1=1 AND P5=1 → BLOCKED (P5=0)
4. T3 (source) fires → P4=1
5. T4 (source) fires → P5=1
6. Now T1 can fire: P2=1, P4=1 → consumes both, produces P1
7. Now T2 can fire: P1=2, P5=1 → consumes P1 and P5, produces P2

This is a cyclic model where T1 and T2 exchange tokens between P1 and P2,
but they need external tokens from P4 and P5 (provided by source transitions T3, T4).
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

def analyze_model_structure(model_path):
    """Analyze the model structure and enablement."""
    print("\n" + "="*80)
    print("MODEL STRUCTURE ANALYSIS")
    print("="*80 + "\n")
    
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    places = {p['id']: p for p in data['places']}
    transitions = {t['id']: t for t in data['transitions']}
    arcs = data['arcs']
    
    # Print places with initial marking
    print("PLACES (initial marking):")
    for pid, place in sorted(places.items()):
        print(f"  {pid}: marking={place['initial_marking']}")
    
    print("\nTRANSITIONS:")
    for tid, trans in sorted(transitions.items()):
        trans_type = trans['transition_type']
        is_source = trans.get('is_source', False)
        rate = trans.get('rate', 1.0)
        source_str = " [SOURCE]" if is_source else ""
        print(f"  {tid}: type={trans_type}, rate={rate}{source_str}")
    
    # Analyze arc connections
    print("\nARC CONNECTIONS:")
    for arc in arcs:
        source = arc['source_id']
        target = arc['target_id']
        weight = arc['weight']
        arc_type = arc['arc_type']
        print(f"  {arc['id']}: {source} → {target} (weight={weight}, type={arc_type})")
    
    # Analyze transition enablement
    print("\nTRANSITION ENABLEMENT ANALYSIS:")
    
    # Build input/output arcs for each transition
    for tid, trans in sorted(transitions.items()):
        print(f"\n  {tid}:")
        
        # Find input arcs (place → transition)
        inputs = [a for a in arcs if a['target_id'] == tid and a['source_type'] == 'place']
        # Find output arcs (transition → place)
        outputs = [a for a in arcs if a['source_id'] == tid and a['target_type'] == 'place']
        
        if trans.get('is_source', False):
            print(f"    Type: SOURCE (no input requirements)")
        else:
            if inputs:
                print(f"    Inputs (requires tokens):")
                for arc in inputs:
                    place_id = arc['source_id']
                    weight = arc['weight']
                    marking = places[place_id]['initial_marking']
                    sufficient = "✅" if marking >= weight else "❌"
                    print(f"      {place_id}: needs {weight}, has {marking} {sufficient}")
            else:
                print(f"    Inputs: NONE (always enabled if no inhibitor arcs)")
        
        if outputs:
            print(f"    Outputs (produces tokens):")
            for arc in outputs:
                place_id = arc['target_id']
                weight = arc['weight']
                print(f"      {place_id}: produces {weight}")
    
    # Determine initially enabled transitions
    print("\n" + "="*80)
    print("INITIAL ENABLEMENT")
    print("="*80 + "\n")
    
    for tid, trans in sorted(transitions.items()):
        if trans.get('is_source', False):
            print(f"  {tid}: ✅ ENABLED (source transition)")
            continue
        
        inputs = [a for a in arcs if a['target_id'] == tid and a['source_type'] == 'place']
        
        if not inputs:
            print(f"  {tid}: ✅ ENABLED (no inputs)")
            continue
        
        enabled = True
        for arc in inputs:
            place_id = arc['source_id']
            weight = arc['weight']
            marking = places[place_id]['initial_marking']
            if marking < weight:
                enabled = False
                break
        
        if enabled:
            print(f"  {tid}: ✅ ENABLED")
        else:
            print(f"  {tid}: ❌ BLOCKED (insufficient tokens in inputs)")

def test_transition_firing(model_path):
    """Test if transitions fire correctly."""
    print("\n" + "="*80)
    print("SIMULATION TEST")
    print("="*80 + "\n")
    
    # Load model using DocumentModel
    document = DocumentModel.load_from_file(model_path)
    
    if not document:
        print(f"❌ Failed to load model")
        return False
    
    print(f"✅ Model loaded successfully")
    print(f"   Places: {len(document.places)}")
    print(f"   Transitions: {len(document.transitions)}")
    print(f"   Arcs: {len(document.arcs)}")
    
    # Print initial state
    print("\nINITIAL STATE:")
    for place in sorted(document.places, key=lambda p: p.id):
        print(f"  {place.id}: tokens={place.tokens}")
    
    # Create simulation controller with the document
    controller = SimulationController(document)
    
    # Run simulation for 10 steps
    print("\n" + "-"*80)
    print("RUNNING SIMULATION (10 steps)")
    print("-"*80 + "\n")
    
    fired_count = 0
    for step in range(1, 11):
        print(f"Step {step}:")
        
        # Store state before
        state_before = {p.id: p.tokens for p in document.places}
        
        # Execute one step
        any_fired = controller.step()
        
        # Check what changed
        state_after = {p.id: p.tokens for p in document.places}
        changed = {pid: (state_before[pid], state_after[pid]) 
                  for pid in state_before 
                  if state_before[pid] != state_after[pid]}
        
        if any_fired and changed:
            fired_count += 1
            print(f"  ✅ Transitions fired!")
            print(f"  Changes:")
            for pid, (before, after) in sorted(changed.items()):
                delta = after - before
                print(f"    {pid}: {before} → {after} ({delta:+d})")
        elif not any_fired:
            print(f"  ⚠️  No transitions fired (deadlock or completion)")
            break
        else:
            print(f"  ℹ️  Step executed but no token changes")
        
        print()
    
    # Print final state
    print("-"*80)
    print("FINAL STATE:")
    for place in sorted(document.places, key=lambda p: p.id):
        print(f"  {place.id}: tokens={place.tokens}")
    
    # Analyze results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    if fired_count == 0:
        print("❌ NO TRANSITIONS FIRED")
        print("\nPossible reasons:")
        print("  1. All transitions blocked (insufficient tokens)")
        print("  2. Guard conditions not satisfied")
        print("  3. Simulation error")
        print("\nDEBUG INFO:")
        print(f"  Initial tokens: P1={state_before.get('P1',0)}, P2={state_before.get('P2',0)}, "
              f"P4={state_before.get('P4',0)}, P5={state_before.get('P5',0)}")
        
        # Check source transitions
        source_trans = [t for t in document.transitions if hasattr(t, 'is_source') and t.is_source]
        print(f"  Source transitions found: {len(source_trans)}")
        for t in source_trans:
            print(f"    - {t.id}: is_source={getattr(t, 'is_source', False)}")
        
        return False
    
    print(f"✅ TRANSITIONS FIRED: {fired_count} steps with activity")
    print(f"\nSimulation completed successfully!")
    
    return True

if __name__ == '__main__':
    model_path = '/home/simao/projetos/shypn/workspace/projects/Interactive/models/test.shy'
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("TESTING TRANSITION FIRING")
    print(f"Model: {model_path}")
    print("="*80)
    
    # First analyze the structure
    analyze_model_structure(model_path)
    
    # Then test firing
    success = test_transition_firing(model_path)
    
    sys.exit(0 if success else 1)
