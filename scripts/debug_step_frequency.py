#!/usr/bin/env python3
"""Debug simulation step frequency"""

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

print("DEBUGGING SIMULATION STEP FREQUENCY")
print("="*80)

controller = SimulationController(model)

step_count = 0
step_times = []

print("\nRunning 0.5s simulation...\n")
while controller.time < 0.5:
    before_time = controller.time
    controller.step()
    after_time = controller.time
    
    dt = after_time - before_time
    step_count += 1
    step_times.append((before_time, after_time, dt))
    
    if step_count <= 10:
        print(f"Step {step_count}: t={before_time:.6f} → {after_time:.6f}, dt={dt:.6f}")

print(f"\n... (showing first 10 steps)")
print(f"\nTotal steps: {step_count}")
print(f"Final time: {controller.time:.6f}s")

# Analyze step sizes
if step_times:
    dts = [dt for _, _, dt in step_times]
    print(f"\nStep size statistics:")
    print(f"  Min dt: {min(dts):.6f}s")
    print(f"  Max dt: {max(dts):.6f}s")
    print(f"  Avg dt: {sum(dts)/len(dts):.6f}s")
    
    # Count unique dt values
    unique_dts = sorted(set(f"{dt:.6f}" for dt in dts))
    print(f"  Unique dt values: {len(unique_dts)}")
    if len(unique_dts) <= 5:
        for dt_str in unique_dts:
            count = sum(1 for dt in dts if f"{dt:.6f}" == dt_str)
            print(f"    {dt_str}s: {count} times")

# Get T20
t20 = None
for trans in model.transitions:
    if trans.id == 'T20':
        t20 = trans
        break

print(f"\nT20 firing_count: {t20.firing_count:.6f}")
print(f"Expected (2.273 * 0.5): {2.273 * 0.5:.6f}")
print(f"Ratio: {t20.firing_count / (2.273 * 0.5):.1%}")
