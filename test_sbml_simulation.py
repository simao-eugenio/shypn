#!/usr/bin/env python3
"""Test simulation of SBML model with stochastic transitions."""

import sys
import os
sys.path.insert(0, 'src')

# Minimal imports to avoid GTK issues  
from shypn.data.canvas.document_model import DocumentModel
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

def test_sbml_stochastic_simulation():
    """Test that stochastic transitions can be scheduled and fire in SBML model."""
    
    # Load SBML model
    model_path = 'workspace/projects/SBML/models/BIOMD0000000001.shy'
    print(f"Loading: {model_path}\n")
    
    doc_model = DocumentModel.load_from_file(model_path)
    
    # Create manager
    manager = ModelCanvasManager()
    manager.document_controller.places = list(doc_model.places)
    manager.document_controller.transitions = list(doc_model.transitions)
    manager.document_controller.arcs = list(doc_model.arcs)
    
    print(f"Model structure:")
    print(f"  Places: {len(manager.document_controller.places)}")
    print(f"  Transitions: {len(manager.document_controller.transitions)}")
    print(f"  Arcs: {len(manager.document_controller.arcs)}")
    
    # Count transition types
    type_counts = {}
    for t in manager.document_controller.transitions:
        t_type = t.transition_type
        type_counts[t_type] = type_counts.get(t_type, 0) + 1
    
    print(f"\nTransition types:")
    for t_type, count in sorted(type_counts.items()):
        print(f"  {t_type}: {count}")
    
    # Add a source transition manually (simulating what user does in GUI)
    # to give the model something to start with
    stoch_trans = manager.document_controller.transitions[0]
    print(f"\nMarking transition '{stoch_trans.label}' as source...")
    stoch_trans.is_source = True
    
    # Create simulation controller
    print(f"\nCreating simulation controller...")
    controller = SimulationController(manager.document_controller)
    
    print(f"Initial time: {controller.time}")
    print(f"Initial transition states: {len(controller.transition_states)}")
    
    # Check if stochastic behaviors are created
    print(f"\nChecking behaviors...")
    for t in manager.document_controller.transitions[:3]:
        behavior = controller._get_behavior(t)
        print(f"  {t.id} ({t.transition_type}): behavior={behavior.__class__.__name__}")
        
        if hasattr(behavior, 'get_scheduled_fire_time'):
            scheduled = behavior.get_scheduled_fire_time()
            print(f"    Scheduled time: {scheduled}")
        
        can_fire, reason = behavior.can_fire()
        print(f"    Can fire: {can_fire} - {reason}")
    
    # Try one step
    print(f"\n=== STEP 1 ===")
    result = controller.step()
    print(f"Step returned: {result}")
    print(f"Time after step: {controller.time}")
    
    # Check stochastic transitions after step
    print(f"\nStochastic transitions after step:")
    stoch_transitions = [t for t in manager.document_controller.transitions 
                         if t.transition_type == 'stochastic']
    for t in stoch_transitions[:5]:
        behavior = controller._get_behavior(t)
        scheduled = behavior.get_scheduled_fire_time() if hasattr(behavior, 'get_scheduled_fire_time') else None
        can_fire, reason = behavior.can_fire()
        print(f"  {t.id}: scheduled={scheduled}, can_fire={can_fire} ({reason})")
    
    # Try more steps
    print(f"\n=== Running 10 more steps ===")
    for i in range(10):
        result = controller.step()
        if result:
            stoch_enabled = [t for t in stoch_transitions 
                           if controller._is_transition_enabled(t)]
            if stoch_enabled:
                print(f"Step {i+2}: time={controller.time:.4f}, {len(stoch_enabled)} stochastic enabled!")
                break
        else:
            print(f"Step {i+2}: Stopped (result=False)")
            break
    else:
        print(f"Completed 10 steps, final time: {controller.time:.4f}")
        print(f"No stochastic transitions fired")
    
    print(f"\n✅ Test complete")

if __name__ == '__main__':
    test_sbml_stochastic_simulation()
