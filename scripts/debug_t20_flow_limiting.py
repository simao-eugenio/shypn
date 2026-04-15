#!/usr/bin/env python3
"""Debug T20 flow limiting in continuous_behavior.py"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

# Load model
model = DocumentModel.load_from_file('bacillus_sporulation_normal.shy')

# Restore tokens
with open('bacillus_sporulation_normal.shy', 'r') as f:
    model_data = json.load(f)

for place_data in model_data.get('places', []):
    place_id = place_data['id']
    for place in model.places:
        if place.id == place_id:
            place.marking = place_data.get('marking', 0)
            break

print("DEBUGGING T20 FLOW LIMITING")
print("="*80)

# Patch continuous_behavior to log flow limiting
import shypn.engine.continuous_behavior as cb_module

original_integrate = cb_module.ContinuousBehavior.integrate_step

def patched_integrate(self, dt, input_arcs, output_arcs):
    # Only log T20
    if self.transition.id == 'T20':
        result = original_integrate(self, dt, input_arcs, output_arcs)
        
        if result[0]:  # success
            details = result[1]
            rate = details.get('rate', 0)
            actual_rate = details.get('actual_rate', 0)
            clamped = details.get('clamped', False)
            
            if clamped:
                print(f"⚠️  t={controller.time:.3f}s: T20 FLOW CLAMPED! rate={rate:.3f}, actual_rate={actual_rate:.3f}")
            elif abs(rate) > 0.01 and controller.time < 0.5:
                print(f"✓  t={controller.time:.3f}s: T20 firing normally, rate={rate:.3f}")
        
        return result
    else:
        return original_integrate(self, dt, input_arcs, output_arcs)

cb_module.ContinuousBehavior.integrate_step = patched_integrate

# Run simulation
controller = SimulationController(model)

print(f"\nInitial: ATP={model.places[0].marking:.2f}, ADP={model.places[24].marking:.2f}")
print("Running 1-second simulation with flow limiting debug...\n")

while controller.time < 1.0:
    controller.step()

# Get T20
t20 = None
for trans in model.transitions:
    if trans.id == 'T20':
        t20 = trans
        break

print(f"\n" + "="*80)
print(f"After 1.0s:")
print(f"  T20 firing_count: {t20.firing_count:.3f}")
print(f"  T20 rate: {t20.firing_count / 1.0:.3f} firings/s")
print(f"  Expected: ~2.273 firings/s")
print(f"  Ratio: {(t20.firing_count / 1.0) / 2.273:.1%}")
