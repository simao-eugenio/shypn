#!/usr/bin/env python3
"""
Test stochastic source transition firing.
"""
import sys
sys.path.insert(0, 'src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.canvas.document_model import DocumentModel
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

# Create a simple T→P model with source transition
document = DocumentModel()

# Create output place
p1 = document.create_place(x=100, y=100, label="Output")
p1.tokens = 0
p1.initial_marking = 0

# Create source transition (no inputs, only output)
t1 = document.create_transition(x=50, y=100, label="Source")
t1.transition_type = 'stochastic'
t1.rate = 1.0
t1.is_source = True  # CRITICAL: Mark as source

# Create arc T→P
a1 = document.create_arc(t1, p1)
a1.weight = 1

print("=" * 80)
print("STOCHASTIC SOURCE TEST")
print("=" * 80)
print(f"Transition: {t1.name}")
print(f"  Type: {t1.transition_type}")
print(f"  Rate: {t1.rate}")
print(f"  is_source: {t1.is_source}")
print(f"Place: {p1.name}")
print(f"  Tokens: {p1.tokens}")
print(f"  Initial marking: {p1.initial_marking}")
print(f"Arc: {a1.source.name} → {a1.target.name}")
print()

# Create canvas manager
manager = ModelCanvasManager()
manager.load_objects(
    places=document.places,
    transitions=document.transitions,
    arcs=document.arcs
)

print(f"Loaded to canvas:")
print(f"  Places: {len(manager.places)}")
print(f"  Transitions: {len(manager.transitions)}")
print(f"  Arcs: {len(manager.arcs)}")
print()

# Create controller
controller = SimulationController(manager)
print(f"Controller created:")
print(f"  Time: {controller.time}")
print()

# Update transition enablement
print("Updating enablement...")
controller._update_transition_enablement()

# Get behavior
from shypn.engine import behavior_factory
behavior = behavior_factory.create_behavior(t1, controller.model_adapter)
print(f"Behavior: {type(behavior).__name__}")
print(f"  Rate: {behavior.rate}")
print(f"  Scheduled fire time: {behavior._scheduled_fire_time}")
print(f"  Sampled burst: {behavior._sampled_burst}")
print()

# Check can_fire
can_fire, reason = behavior.can_fire()
print(f"can_fire(): {can_fire}, reason: {reason}")
print()

# Try to step
if can_fire:
    print("Attempting to fire...")
    controller.step()
    print(f"After firing:")
    print(f"  P1 tokens: {p1.tokens}")
    print(f"  Time: {controller.time}")
else:
    print(f"❌ CANNOT FIRE: {reason}")
    print()
    print("Debugging:")
    print(f"  is_source: {getattr(t1, 'is_source', False)}")
    print(f"  _scheduled_fire_time: {behavior._scheduled_fire_time}")
    print(f"  current_time: {behavior._get_current_time()}")
