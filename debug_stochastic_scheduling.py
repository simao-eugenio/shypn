#!/usr/bin/env python3
"""Debug script to trace stochastic transition scheduling in BIOMD0000000001."""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

# Load the model
model_path = 'workspace/projects/SBML/models/BIOMD0000000001.shy'
print(f"Loading model: {model_path}")

document_model = DocumentModel.load_from_file(model_path)

# Create manager and populate with loaded objects
manager = ModelCanvasManager()
manager.document_controller.places = list(document_model.places)
manager.document_controller.transitions = list(document_model.transitions)
manager.document_controller.arcs = list(document_model.arcs)

doc_ctrl = manager.document_controller

print(f"\n=== Model Structure ===")
print(f"Places: {len(doc_ctrl.places)}")
print(f"Transitions: {len(doc_ctrl.transitions)}")

stochastic_transitions = [t for t in doc_ctrl.transitions if t.transition_type == 'stochastic']
print(f"\nStochastic transitions: {len(stochastic_transitions)}")
for t in stochastic_transitions[:3]:  # Show first 3
    max_burst = getattr(t, 'max_burst', 1)
    print(f"  - {t.id}: rate={t.rate}, max_burst={max_burst}")

# Create controller
controller = SimulationController(doc_ctrl)

# Initialize simulation
controller.initialize()
print(f"\n=== After Initialize ===")
print(f"Current time: {controller.time}")

# Check stochastic behaviors
for t in stochastic_transitions[:3]:
    behavior = controller._get_behavior(t)
    scheduled_time = behavior.get_scheduled_fire_time()
    can_fire, reason = behavior.can_fire()
    print(f"\nTransition {t.id}:")
    print(f"  Scheduled time: {scheduled_time}")
    print(f"  Can fire: {can_fire} ({reason})")
    
    # Check if behavior has set_enablement_time
    if hasattr(behavior, 'set_enablement_time'):
        print(f"  Has set_enablement_time: YES")
    else:
        print(f"  Has set_enablement_time: NO")

# Check transition state
print(f"\n=== Transition States ===")
for t in stochastic_transitions[:3]:
    state = controller._get_or_create_state(t)
    print(f"Transition {t.id}:")
    print(f"  enablement_time: {state.enablement_time}")
    print(f"  scheduled_time: {state.scheduled_time}")
    
    # Check structural enablement
    behavior = controller._get_behavior(t)
    input_arcs = behavior.get_input_arcs()
    print(f"  Input arcs: {len(input_arcs)}")
    for arc in input_arcs:
        source_place = doc_ctrl.places[0]  # Find by ID
        for p in doc_ctrl.places:
            if p.id == arc.source_id:
                source_place = p
                break
        print(f"    From {source_place.id}: tokens={source_place.tokens}, weight={arc.weight}")

# Try one step
print(f"\n=== Stepping Once ===")
result = controller.step()
print(f"Step returned: {result}")
print(f"Current time: {controller.time}")

# Check again
for t in stochastic_transitions[:3]:
    behavior = controller._get_behavior(t)
    scheduled_time = behavior.get_scheduled_fire_time()
    can_fire, reason = behavior.can_fire()
    print(f"\nTransition {t.id}:")
    print(f"  Scheduled time: {scheduled_time}")
    print(f"  Can fire: {can_fire} ({reason})")
