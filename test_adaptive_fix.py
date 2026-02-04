#!/usr/bin/env python3
"""
Test adaptive transition fix: Simple P1→T→P2 model
P1: Regular place with 10 tokens (no volume)
T: Adaptive transition
P2: Regular output place

Expected behavior AFTER fix:
- No volume → continuous mode
- T should integrate smoothly (no visual firings, but tokens should flow)
- P1 should decrease, P2 should increase
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

# Create model
model = DocumentModel()

# P1: Regular place with 10 tokens
p1 = model.create_place(x=100, y=100, label="P1")
p1.tokens = 10
p1.initial_marking = 10

# P2: Regular output place
p2 = model.create_place(x=300, y=100, label="P2")
p2.tokens = 0
p2.initial_marking = 0

# T: Adaptive transition with rate 1.0
t = model.create_transition(x=200, y=100, label="T")
t.transition_type = 'adaptive'
t.properties = {
    'transition_type': 'adaptive',
    'adaptive_filter': 'inputs_only',  # Default
    'volume_threshold': 1.0,  # Default (fL)
}
t.rate = 1.0  # Flow rate

# Arcs
arc_in = model.create_arc(p1, t, weight=1, arc_type='normal')
arc_out = model.create_arc(t, p2, weight=1, arc_type='normal')

# Setup simulation
settings = SimulationSettings()
settings.duration = 5.0  # 5 seconds
settings.dt = 0.1  # 100ms time steps

controller = SimulationController(model, settings)

print("=" * 60)
print("ADAPTIVE TRANSITION FIX TEST")
print("=" * 60)
print(f"\n  P1 (spatial signal): {p1.tokens} tokens, no volume → continuous mode")
print(f"  T (adaptive): rate={t.rate}, type={t.transition_type}")
print(f"  P2 (output): {p2.tokens} tokens")
print(f"\nSimulation: duration={settings.duration}s, dt={settings.dt}s")
print("=" * 60)

# Record initial state
print(f"\nInitial state (t=0.0):")
print(f"  P1: {p1.tokens:.2f} tokens")
print(f"  P2: {p2.tokens:.2f} tokens")

# Run simulation
print(f"\nRunning simulation...")
step_count = 0
while controller.time < settings.get_duration_seconds():
    success = controller.step(settings.dt)
    step_count += 1
    
    # Print every 10 steps
    if step_count % 10 == 0:
        print(f"  t={controller.time:.2f}s: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}")
    
    if not success:
        break

# Final state
print(f"\nFinal state (t={controller.time:.2f}):")
print(f"  P1: {p1.tokens:.2f} tokens")
print(f"  P2: {p2.tokens:.2f} tokens")
print(f"  Steps: {step_count}")
print("=" * 60)

# Check mass conservation
total_tokens = p1.tokens + p2.tokens
print(f"\nMass conservation:")
print(f"  Initial: 10.0 tokens")
print(f"  Final: {total_tokens:.2f} tokens")
print(f"  Difference: {abs(total_tokens - 10.0):.6f}")

if abs(total_tokens - 10.0) < 0.01:
    print("  ✓ Mass conserved")
else:
    print("  ✗ Mass NOT conserved!")

# Check if transition executed
if p2.tokens > 0:
    print(f"\n✓ SUCCESS: Adaptive transition executed!")
    print(f"  P1 decreased by {10.0 - p1.tokens:.2f}")
    print(f"  P2 increased by {p2.tokens:.2f}")
else:
    print(f"\n✗ FAILURE: Adaptive transition did NOT execute")
    print(f"  P1 unchanged: {p1.tokens:.2f}")
    print(f"  P2 unchanged: {p2.tokens:.2f}")

print("=" * 60)
