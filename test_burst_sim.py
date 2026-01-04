#!/usr/bin/env python3
"""Test burst limiting with inhibitor arcs on simple model."""
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.core.adapter import Adapter
from shypn.engine.simulation.controller import SimulationController

# Load test model
model_path = 'workspace/projects/My_Project/thermodynamics/test_burst_inhibitor.shy'
print(f"Loading test model: {model_path}")
adapter = Adapter(model_path)

# Configure simulation
sim_config = {
    'end_time': 50.0,
    'time_step': 0.01,
    'output_interval': 0.05,
    'output_file': 'workspace/projects/My_Project/thermodynamics/data/test_burst_results.csv'
}

print("\nModel structure:")
print(f"  Places: {len(adapter.places)}")
for p in adapter.places:
    print(f"    - {p.name}: {p.initial_tokens} tokens")
print(f"  Transitions: {len(adapter.transitions)}")
for t in adapter.transitions:
    print(f"    - {t.name}: {t.transition_type}")
print(f"  Arcs: {len(adapter.arcs)}")
for a in adapter.arcs:
    arc_type = a.__class__.__name__
    threshold = getattr(a, 'threshold', None)
    if threshold:
        print(f"    - {arc_type}: {a.source_id} → {a.target_id}, threshold={threshold}")
    else:
        print(f"    - {arc_type}: {a.source_id} → {a.target_id}")

print("\nRunning simulation...")
controller = SimulationController(adapter, sim_config)
controller.run()

print("\n✅ Simulation complete")
print(f"Results saved to: {sim_config['output_file']}")
