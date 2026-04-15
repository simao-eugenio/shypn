#!/usr/bin/env python3
"""Comprehensive diagnostic for adaptive test model."""

import sys
import os
import json

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'adaptive_test_simple.shy')
    
    print("="*80)
    print("ADAPTIVE TEST MODEL DIAGNOSTIC")
    print("="*80)
    print()
    
    # Load JSON
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    # Analyze model structure
    print(f"✓ Model loaded from: {model_path}")
    print()
    
    print("PLACES:")
    for place in model_data['places']:
        print(f"  {place['name']} (ID: {place['id']})")
        print(f"    tokens: {place.get('tokens', 'MISSING')}")
        print(f"    initial_marking: {place.get('initial_marking', 'MISSING')}")
        print(f"    compartment_volume: {place.get('compartment_volume', 'MISSING')}")
        print()
    
    print("TRANSITIONS:")
    for trans in model_data['transitions']:
        print(f"  {trans['name']} (ID: {trans['id']})")
        print(f"    type: {trans.get('transition_type', 'MISSING')}")
        print(f"    rate_function: {trans.get('rate_function', 'MISSING')}")
        print()
    
    print("ARCS:")
    arc_map = {arc['id']: arc for arc in model_data['arcs']}
    place_map = {p['id']: p['name'] for p in model_data['places']}
    trans_map = {t['id']: t['name'] for t in model_data['transitions']}
    
    for arc in model_data['arcs']:
        source_name = place_map.get(arc.get('source_id')) or trans_map.get(arc.get('source_id'), 'UNKNOWN')
        target_name = place_map.get(arc.get('target_id')) or trans_map.get(arc.get('target_id'), 'UNKNOWN')
        print(f"  {arc['id']}: {source_name} → {target_name}")
        print(f"    arc_type: {arc.get('arc_type', 'MISSING')}")
        print(f"    weight: {arc.get('weight', 1.0)}")
        print()
    
    # Now try to simulate
    print("="*80)
    print("SIMULATION TEST")
    print("="*80)
    print()
    
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.engine.simulation import SimulationController
    from shypn.engine.simulation.settings import SimulationSettings
    
    # Create model
    document = DocumentModel.from_dict(model_data)
    
    print(f"✓ DocumentModel created:")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    print()
    
    # Check initial tokens after loading
    print("Initial tokens after loading:")
    for place in document.places:
        print(f"  {place.name}: {place.tokens} (initial_marking={place.initial_marking})")
    print()
    
    # Create simulation controller
    controller = SimulationController(document, verbose=True)
    
    # Configure settings
    controller.settings.duration = 10.0
    controller.settings.dt = 0.1
    
    print("✓ SimulationController created")
    print(f"  model.transitions: {len(controller.model.transitions)}")
    print(f"  model.places: {len(controller.model.places)}")
    print(f"  model.arcs: {len(controller.model.arcs)}")
    
    # Debug: Print transition IDs
    print(f"\nTransition IDs in controller.model:")
    for t in controller.model.transitions:
        print(f"  - {t.id}: {t.name} (type={t.transition_type})")
    print()
    
    # Force enablement update to schedule stochastic transitions
    print("Updating enablement states...")
    print(f"Before: {len(controller.transition_states)} states")
    controller._update_enablement_states()
    print(f"After: {len(controller.transition_states)} states")
    print(f"State keys: {list(controller.transition_states.keys())}")
    print(f"Transition IDs: {[t.id for t in document.transitions]}")
    print()
    
    # Check transition types
    print("Transition analysis AFTER enablement update:")
    for trans in document.transitions:
        trans_id = trans.id
        print(f"  {trans.name} (ID={trans_id}, type={type(trans_id)}):")
        print(f"    type: {trans.transition_type}")
        print(f"    rate_function: {trans.rate_function}")
        
        # Get behavior
        behavior = controller._get_behavior(trans)
        print(f"    behavior: {type(behavior).__name__}")
        
        # Check state DIRECTLY
        print(f"    Checking controller.transition_states['{trans_id}']...")
        if trans_id in controller.transition_states:
            state = controller.transition_states[trans_id]
            print(f"    ✓ FOUND state!")
            print(f"      enablement_time: {state.enablement_time}")
            print(f"      scheduled_time: {state.scheduled_time}")
        else:
            print(f"    ❌ NOT FOUND - Keys are: {list(controller.transition_states.keys())}")
            print(f"      trans_id type: {type(trans_id)}, repr: {repr(trans_id)}")
            print(f"      key types: {[type(k) for k in controller.transition_states.keys()]}")
        print()
    
    # Try one step
    print("Executing one simulation step...")
    try:
        success = controller.step()
        print(f"✓ Step executed: {success}")
        print(f"  Time: {controller.time}")
        print()
        
        print("Token counts after step:")
        for place in document.places:
            print(f"  {place.name}: {place.tokens}")
        print()
        
        print("Firing counts:")
        for trans in document.transitions:
            print(f"  {trans.name}: {trans.firing_count}")
    except Exception as e:
        print(f"❌ Error during step: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
