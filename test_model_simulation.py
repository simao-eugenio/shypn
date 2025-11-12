#!/usr/bin/env python3
"""Test script to load and simulate test.shy model."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation import SimulationController
from shypn.helpers.serialization import Serializer


def test_model_simulation():
    """Load test.shy and run a simulation to check if transitions fire."""
    
    model_path = "workspace/projects/Interactive/models/test.shy"
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return False
    
    print(f"{'='*80}")
    print(f"Testing Model: {model_path}")
    print(f"{'='*80}\n")
    
    # Load model
    print("Loading model...")
    serializer = Serializer()
    
    try:
        model_data = serializer.load(model_path)
        
        # Extract model components
        places = model_data.get('places', [])
        transitions = model_data.get('transitions', [])
        arcs = model_data.get('arcs', [])
        
        print(f"✓ Model loaded successfully")
        print(f"  Places: {len(places)}")
        print(f"  Transitions: {len(transitions)}")
        print(f"  Arcs: {len(arcs)}\n")
        
        # Show model structure
        print("Model Structure:")
        print("-" * 80)
        
        print("\nPlaces:")
        for place in places:
            tokens = place.get('tokens', 0)
            place_id = place.get('id', 'unknown')
            label = place.get('label', place_id)
            print(f"  {place_id}: {label} (tokens={tokens})")
        
        print("\nTransitions:")
        for trans in transitions:
            trans_id = trans.get('id', 'unknown')
            label = trans.get('label', trans_id)
            rate = trans.get('rate', 'not set')
            metadata = trans.get('metadata', {})
            kinetic_law = metadata.get('kinetic_law', None)
            print(f"  {trans_id}: {label}")
            if kinetic_law:
                print(f"    Kinetic law: {kinetic_law}")
            else:
                print(f"    Rate: {rate}")
        
        print("\nArcs:")
        for arc in arcs:
            arc_id = arc.get('id', 'unknown')
            source = arc.get('source', 'unknown')
            target = arc.get('target', 'unknown')
            weight = arc.get('weight', 1)
            print(f"  {arc_id}: {source} → {target} (weight={weight})")
        
        # Create document model
        print("\n" + "="*80)
        print("Creating Document Model")
        print("="*80)
        
        doc_model = DocumentModel()
        
        # Recreate places
        place_map = {}
        for place_data in places:
            place_id = place_data.get('id')
            x = place_data.get('x', 0)
            y = place_data.get('y', 0)
            label = place_data.get('label', place_id)
            tokens = place_data.get('tokens', 0)
            
            place = doc_model.create_place(x, y, label)
            place.id = place_id
            place.tokens = tokens
            place_map[place_id] = place
        
        # Recreate transitions
        trans_map = {}
        for trans_data in transitions:
            trans_id = trans_data.get('id')
            x = trans_data.get('x', 0)
            y = trans_data.get('y', 0)
            label = trans_data.get('label', trans_id)
            rate = trans_data.get('rate', 1.0)
            
            trans = doc_model.create_transition(x, y, label)
            trans.id = trans_id
            trans.rate = rate
            
            # Copy metadata (including kinetic_law)
            if 'metadata' in trans_data:
                trans.metadata = trans_data['metadata'].copy()
            
            trans_map[trans_id] = trans
        
        # Recreate arcs
        for arc_data in arcs:
            source_id = arc_data.get('source')
            target_id = arc_data.get('target')
            weight = arc_data.get('weight', 1)
            
            source = place_map.get(source_id) or trans_map.get(source_id)
            target = place_map.get(target_id) or trans_map.get(target_id)
            
            if source and target:
                arc = doc_model.create_arc(source, target, weight=weight)
                arc.id = arc_data.get('id', arc.id)
        
        print(f"✓ Document model created")
        
        # Create simulation controller
        print("\n" + "="*80)
        print("Running Simulation")
        print("="*80 + "\n")
        
        controller = SimulationController(doc_model)
        
        # Show initial state
        print("Initial State:")
        for place in doc_model.places:
            print(f"  {place.id}: {place.tokens} tokens")
        
        # Run simulation
        print("\nRunning 10 steps...")
        steps = 0
        max_steps = 10
        
        while steps < max_steps:
            # Check enabled transitions
            enabled = []
            for trans in doc_model.transitions:
                if controller._is_transition_enabled(trans):
                    enabled.append(trans.id)
            
            if not enabled:
                print(f"\n✗ No enabled transitions at step {steps}")
                break
            
            print(f"\nStep {steps + 1}:")
            print(f"  Enabled transitions: {enabled}")
            
            # Fire first enabled transition
            trans_to_fire = None
            for trans in doc_model.transitions:
                if trans.id in enabled:
                    trans_to_fire = trans
                    break
            
            if trans_to_fire:
                # Fire the transition
                controller._fire_transition(trans_to_fire)
                print(f"  → Fired: {trans_to_fire.id}")
                
                # Show new state
                print(f"  New state:")
                for place in doc_model.places:
                    print(f"    {place.id}: {place.tokens} tokens")
            
            steps += 1
        
        # Final results
        print("\n" + "="*80)
        print("Simulation Complete")
        print("="*80)
        
        print(f"\nFinal State (after {steps} steps):")
        for place in doc_model.places:
            print(f"  {place.id}: {place.tokens} tokens")
        
        # Check if any transitions fired
        transitions_fired = steps > 0
        
        if transitions_fired:
            print(f"\n✓ SUCCESS: Transitions fired ({steps} steps)")
            return True
        else:
            print(f"\n✗ FAILURE: No transitions fired")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_model_simulation()
    sys.exit(0 if success else 1)
