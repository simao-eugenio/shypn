#!/usr/bin/env python3
"""Verify tau-leaping execution for BIOMD0000000068."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s: %(message)s')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000068.shy"
document = DocumentModel.load_from_file(model_path)

settings = SimulationSettings()
settings.duration = 2.0
settings.dt = 0.1

controller = SimulationController(document, settings)
controller.reset()

print("="*80)
print("TAU-LEAPING EXECUTION TEST")
print("="*80)
print(f"Initial time: {controller.time}")
print(f"Duration: {settings.duration}")
print(f"Time step: {settings.dt}")
print(f"Use tau-leaping: {settings.use_tau_leaping}")

# Check if tau-leaping engine exists
if hasattr(controller, '_tau_leaping_engine'):
    print(f"Tau-leaping engine: EXISTS")
else:
    print(f"Tau-leaping engine: NOT CREATED YET")

print(f"\nStochastic transitions:")
stochastic = [t for t in document.transitions if t.transition_type == 'stochastic']
for t in stochastic:
    print(f"  {t.label}: rate={getattr(t, 'rate', None)}")

print(f"\n{'='*80}")
print("RUNNING 10 STEPS")
print(f"{'='*80}\n")

for step in range(10):
    print(f"Step {step}: t={controller.time:.3f}")
    
    try:
        success = controller.step()
        if not success:
            print(f"  Simulation stopped")
            break
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        break
    
    # Check if any transition fired
    fired_this_step = [t for t in document.transitions if hasattr(t, 'firing_count') and getattr(t, '_last_fire_step', -1) == step]
    if fired_this_step:
        for t in fired_this_step:
            print(f"    🔥 {t.label} fired!")
    
    # Mark transitions that fired
    for t in document.transitions:
        if hasattr(t, 'firing_count'):
            old_count = getattr(t, '_prev_count', 0)
            new_count = t.firing_count
            if new_count > old_count:
                t._last_fire_step = step
            t._prev_count = new_count

print(f"\n{'='*80}")
print("FINAL RESULTS")
print(f"{'='*80}")
print(f"Final time: {controller.time:.3f}")

for t in stochastic:
    count = getattr(t, 'firing_count', 0)
    status = "✅" if count > 0 else "❌"
    print(f"{status} {t.label}: {count} firings")
