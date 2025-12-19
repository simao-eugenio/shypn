#!/usr/bin/env python3
"""Debug why stochastic transitions are not firing in simulation."""

import logging
logging.basicConfig(level=logging.DEBUG)

from shypn.data.model_canvas_manager import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

# Create a simple test model with stochastic transitions
document = DocumentModel()

# Create places
p1 = document.create_place(x=100, y=100, label="P1")
p1.set_tokens(10.0)

p2 = document.create_place(x=300, y=100, label="P2")
p2.set_tokens(0.0)

# Create a stochastic transition
t1 = document.create_transition(x=200, y=100, label="T1")
t1.transition_type = 'stochastic'
t1.rate = 5.0  # Fixed rate

# Create arcs
arc1 = document.create_arc(source=p1, target=t1, weight=1)
arc2 = document.create_arc(source=t1, target=p2, weight=1)

print("\n=== MODEL STRUCTURE ===")
print(f"Places: {len(document.places)}")
for p in document.places:
    print(f"  {p.label}: tokens={p.tokens}")
print(f"Transitions: {len(document.transitions)}")
for t in document.transitions:
    print(f"  {t.label}: type={t.transition_type}, rate={getattr(t, 'rate', 'NOT SET')}")
print(f"Arcs: {len(document.arcs)}")

# Set up simulation
settings = SimulationSettings()
settings.duration = 10.0
settings.dt = 0.1  # 100 ms steps

controller = SimulationController(document, settings)
controller.reset()

print("\n=== INITIAL STATE ===")
print(f"Time: {controller.time}")
print(f"P1 tokens: {p1.tokens}")
print(f"P2 tokens: {p2.tokens}")

# Check transition behavior
print("\n=== CHECKING BEHAVIOR ===")
behavior = controller._get_behavior(t1)
print(f"Behavior class: {type(behavior).__name__}")
print(f"Behavior rate: {getattr(behavior, 'rate', 'NOT SET')}")
print(f"Has rate function: {getattr(behavior, 'has_rate_function', False)}")

# Try to evaluate propensity
try:
    propensity = behavior._evaluate_rate_at_enablement(controller.time)
    print(f"Propensity: {propensity}")
except Exception as e:
    print(f"Error evaluating propensity: {e}")

# Run simulation for a few steps
print("\n=== RUNNING SIMULATION ===")
for step in range(20):
    success = controller.step()
    if step % 5 == 0:
        print(f"Step {step}: t={controller.time:.2f}, P1={p1.tokens:.2f}, P2={p2.tokens:.2f}")
    if not success:
        print("Simulation stopped")
        break

print("\n=== FINAL STATE ===")
print(f"Time: {controller.time}")
print(f"P1 tokens: {p1.tokens}")
print(f"P2 tokens: {p2.tokens}")
print(f"T1 firing count: {t1.firing_count}")

if t1.firing_count == 0:
    print("\n❌ ERROR: Transition did not fire!")
else:
    print(f"\n✅ SUCCESS: Transition fired {t1.firing_count} times")
