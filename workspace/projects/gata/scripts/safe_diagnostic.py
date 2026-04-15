#!/usr/bin/env python3
"""Safe diagnostic - read-only analysis of adaptive model behavior."""

import sys
import os
import json
import copy

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'adaptive_test_simple.shy')
    
    print("="*80)
    print("SAFE DIAGNOSTIC - READ-ONLY ANALYSIS")
    print("="*80)
    print()
    
    # Load JSON
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.engine.simulation import SimulationController
    
    # Create model
    document = DocumentModel.from_dict(model_data)
    controller = SimulationController(document, verbose=True)
    
    print("✓ Model and controller created")
    print()
    
    # Snapshot state BEFORE any access
    print("BEFORE calling _update_enablement_states():")
    print(f"  transition_states keys: {list(controller.transition_states.keys())}")
    print()
    
    # Call update
    controller._update_enablement_states()
    
    # Snapshot state AFTER, WITHOUT iterating
    print("AFTER calling _update_enablement_states():")
    states_snapshot = copy.deepcopy(dict(controller.transition_states))
    print(f"  transition_states keys: {list(states_snapshot.keys())}")
    print()
    
    # Now analyze each transition WITHOUT modifying anything
    print("Analyzing each transition (read-only):")
    for trans_id in ['T1', 'T2', 'T3', 'T4']:
        print(f"\n  {trans_id}:")
        
        # Find transition object
        trans = None
        for t in document.transitions:
            if t.id == trans_id:
                trans = t
                break
        
        if not trans:
            print(f"    ❌ Transition not found")
            continue
        
        print(f"    name: {trans.name}")
        print(f"    type: {trans.transition_type}")
        
        # Check if state exists in snapshot
        if trans_id in states_snapshot:
            state = states_snapshot[trans_id]
            print(f"    ✓ State exists in snapshot")
            print(f"      enablement_time: {state.enablement_time}")
            print(f"      scheduled_time: {state.scheduled_time}")
        else:
            print(f"    ❌ State NOT in snapshot")
        
        # Now check current controller state
        if trans_id in controller.transition_states:
            print(f"    ✓ State still in controller.transition_states")
        else:
            print(f"    ❌ State DISAPPEARED from controller.transition_states")
            print(f"       Current keys: {list(controller.transition_states.keys())}")
    
    print()
    print("="*80)
    print("TESTING _get_behavior() impact:")
    print("="*80)
    print()
    
    # Fresh controller
    document2 = DocumentModel.from_dict(model_data)
    controller2 = SimulationController(document2, verbose=False)
    controller2._update_enablement_states()
    
    print(f"After fresh _update_enablement_states(): {len(controller2.transition_states)} states")
    print(f"  Keys: {list(controller2.transition_states.keys())}")
    print()
    
    # Call _get_behavior for first transition
    trans1 = document2.transitions[0]
    print(f"Calling _get_behavior({trans1.id})...")
    behavior1 = controller2._get_behavior(trans1)
    print(f"  Returned: {type(behavior1).__name__}")
    print(f"  States after: {list(controller2.transition_states.keys())}")
    print()
    
    # Call _get_behavior for second transition
    trans2 = document2.transitions[1]
    print(f"Calling _get_behavior({trans2.id})...")
    behavior2 = controller2._get_behavior(trans2)
    print(f"  Returned: {type(behavior2).__name__}")
    print(f"  States after: {list(controller2.transition_states.keys())}")
    print()
    
    print("="*80)
    print("TESTING can_fire() impact:")
    print("="*80)
    print()
    
    # Fresh controller
    document3 = DocumentModel.from_dict(model_data)
    controller3 = SimulationController(document3, verbose=False)
    controller3._update_enablement_states()
    
    print(f"After fresh _update_enablement_states(): {len(controller3.transition_states)} states")
    print(f"  Keys: {list(controller3.transition_states.keys())}")
    print()
    
    # Call can_fire for first transition
    trans1 = document3.transitions[0]
    behavior1 = controller3._get_behavior(trans1)
    print(f"Calling behavior.can_fire() for {trans1.id}...")
    can_fire, reason = behavior1.can_fire()
    print(f"  Result: {can_fire} ({reason})")
    print(f"  States after: {list(controller3.transition_states.keys())}")
    print()

if __name__ == '__main__':
    main()
