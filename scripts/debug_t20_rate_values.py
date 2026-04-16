#!/usr/bin/env python3
"""Debug what rate value is returned from integrate_step"""

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

print("DEBUGGING T20 RATE VALUES")
print("="*80)

# Patch integrate_step to capture rate values
import shypn.engine.continuous_behavior as cb_module

original_integrate = cb_module.ContinuousBehavior.integrate_step
rate_samples = []

def patched_integrate(self, dt, input_arcs, output_arcs):
    result = original_integrate(self, dt, input_arcs, output_arcs)
    
    if self.transition.id == 'T20' and result[0]:
        details = result[1]
        rate = details.get('rate', 0)
        actual_rate = details.get('actual_rate', 0)
        
        rate_samples.append({
            'time': controller.time,
            'rate': rate,
            'actual_rate': actual_rate,
            'dt': dt
        })
    
    return result

cb_module.ContinuousBehavior.integrate_step = patched_integrate

# Run simulation
controller = SimulationController(model)

print("Running 0.5s simulation...\n")
while controller.time < 0.5:
    controller.step()

# Get T20
t20 = None
for trans in model.transitions:
    if trans.id == 'T20':
        t20 = trans
        break

print(f"T20 firing_count after 0.5s: {t20.firing_count:.6f}")
print(f"Expected (2.273 * 0.5): {2.273 * 0.5:.6f}")
print(f"\nFirst 10 rate samples:")
print(f"{'Time':<10} {'rate':<12} {'actual_rate':<12} {'dt':<12} {'rate*dt':<12}")
print("-"*70)

for i, sample in enumerate(rate_samples[:10]):
    increment = abs(sample['rate']) * sample['dt']
    print(f"{sample['time']:<10.6f} {sample['rate']:<12.6f} {sample['actual_rate']:<12.6f} {sample['dt']:<12.6f} {increment:<12.6f}")

print("\nSum of first 10 increments:", sum(abs(s['rate']) * s['dt'] for s in rate_samples[:10]))
print(f"Total samples: {len(rate_samples)}")
print(f"Sum of all increments: {sum(abs(s['rate']) * s['dt'] for s in rate_samples):.6f}")
print(f"T20 firing_count: {t20.firing_count:.6f}")

print("\n" + "="*80)
if abs(sum(abs(s['rate']) * s['dt'] for s in rate_samples) - t20.firing_count) < 0.001:
    print("✓ firing_count matches sum of rate*dt increments")
else:
    print("✗ MISMATCH: firing_count ≠ sum of rate*dt increments")
    print(f"  Difference: {t20.firing_count - sum(abs(s['rate']) * s['dt'] for s in rate_samples):.6f}")
