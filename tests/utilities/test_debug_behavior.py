#!/usr/bin/env python3
"""Debug test to understand behavior issue."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

# Create simple net
model = ModelCanvasManager()

p1 = Place(x=100, y=100, id=1, name="P1", label="Input")
p1.tokens = 3

p2 = Place(x=300, y=100, id=2, name="P2", label="Output")
p2.tokens = 0

t1 = Transition(x=200, y=100, id=1, name="T1", label="Transfer")
t1.transition_type = 'immediate'

a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)

model.places.append(p1)
model.places.append(p2)
model.transitions.append(t1)
model.arcs.append(a1)
model.arcs.append(a2)

# Create controller and adapter
controller = SimulationController(model)
adapter = controller.model_adapter

print("=== Model Adapter Debug ===")
print(f"adapter.places: {adapter.places}")
print(f"adapter.transitions: {adapter.transitions}")
print(f"adapter.arcs: {adapter.arcs}")

print("\n=== Arc Properties ===")
print(f"a1.source_id: {a1.source_id}")
print(f"a1.target_id: {a1.target_id}")
print(f"a2.source_id: {a2.source_id}")
print(f"a2.target_id: {a2.target_id}")

print("\n=== Behavior Test ===")
behavior = controller._get_behavior(t1)
print(f"behavior: {behavior}")

input_arcs = behavior.get_input_arcs()
output_arcs = behavior.get_output_arcs()
print(f"input_arcs: {input_arcs}")
print(f"output_arcs: {output_arcs}")

print("\n=== Place Lookup Test ===")
for arc in input_arcs:
    print(f"arc.source_id: {arc.source_id}")
    place = behavior._get_place(arc.source_id)
    print(f"place from behavior._get_place({arc.source_id}): {place}")
    print(f"place tokens: {place.tokens if place else 'N/A'}")

print("\n=== Firing Test ===")
print(f"Before: P1={p1.tokens}, P2={p2.tokens}")
success, details = behavior.fire(input_arcs, output_arcs)
print(f"After: P1={p1.tokens}, P2={p2.tokens}")
print(f"Success: {success}")
print(f"Details: {details}")
