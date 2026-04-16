#!/usr/bin/env python3
"""Debug adaptive behavior during can_fire() call."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.document.model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Load model
model_path = '/home/simao/projetos/shypn/workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy'
doc = DocumentModel()
doc.load(model_path)

# Find T5
t5 = next(t for t in doc.transitions if t.name == 'chameleon_fold')

# Create controller
controller = SimulationController(doc)

# Get behavior
behavior = controller._get_behavior(t5)

print(f"\n=== BEFORE can_fire() ===")
print(f"Behavior type: {type(behavior).__name__}")
print(f"model.arcs type: {type(behavior.model.arcs)}")
print(f"model.arcs count: {len(behavior.model.arcs)}")
print(f"model.places type: {type(behavior.model.places)}")
print(f"model.places count: {len(behavior.model.places)}")

# Get input arcs manually
input_arcs = behavior.get_input_arcs()
print(f"\nget_input_arcs() returned: {len(input_arcs)} arcs")
for arc in input_arcs:
    print(f"  Arc: {arc.id}, type={type(arc).__name__}, source={arc.source_id}, target={arc.target_id}")
    place = behavior._get_place(arc.source_id)
    print(f"    _get_place('{arc.source_id}') = {place}")
    if place:
        print(f"    Place: id={place.id}, name={place.name}")
        print(f"    compartment_volume={getattr(place, 'compartment_volume', 'NOT SET')}")

# Now call _get_connected_places manually
places = behavior._get_connected_places()
print(f"\n_get_connected_places() returned: {len(places)} places")
for place in places:
    print(f"  Place: {place.id}, name={place.name}, compartment_volume={getattr(place, 'compartment_volume', 'NOT SET')}")

print(f"\n=== CALLING can_fire() ===")
# This should trigger _select_mode which logs the warning
can_fire_result = behavior.can_fire()
print(f"can_fire() result: {can_fire_result}")

