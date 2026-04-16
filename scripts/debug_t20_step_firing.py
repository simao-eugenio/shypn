#!/usr/bin/env python3
"""Check if T20 fires on every step"""

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

print("CHECKING IF T20 FIRES ON EVERY STEP")
print("="*80)

# Patch controller to track firing
import shypn.engine.simulation.controller as ctrl_module

original_step = ctrl_module.SimulationController.step
t20_fired_steps = []
total_steps = 0

def patched_step(self, time_step=None):
    global total_steps
    total_steps += 1
    
    # Get T20 firing count before
    t20 = None
    for trans in self.model.transitions:
        if trans.id == 'T20':
            t20 = trans
            break
    
    before_count = t20.firing_count if t20 else 0
    
    # Do the step
    result = original_step(self, time_step)
    
    # Check if T20 fired
    after_count = t20.firing_count if t20 else 0
    
    if after_count > before_count:
        t20_fired_steps.append((total_steps, self.time, before_count, after_count, after_count - before_count))
    
    return result

ctrl_module.SimulationController.step = patched_step

controller = SimulationController(model)

print("\nRunning 0.5s simulation...\n")
while controller.time < 0.5:
    controller.step()

print(f"Total simulation steps: {total_steps}")
print(f"T20 fired on: {len(t20_fired_steps)} steps")
print(f"T20 fire rate: {len(t20_fired_steps)} / {total_steps} = {len(t20_fired_steps)/total_steps:.1%}")

print(f"\n{'Step':<8} {'Time':<12} {'Before':<12} {'After':<12} {'Increment':<12}")
print("-"*60)
for step_num, time, before, after, increment in t20_fired_steps:
    print(f"{step_num:<8} {time:<12.6f} {before:<12.6f} {after:<12.6f} {increment:<12.6f}")

# Get T20
t20 = None
for trans in model.transitions:
    if trans.id == 'T20':
        t20 = trans
        break

print(f"\nFinal T20 firing_count: {t20.firing_count:.6f}")
print(f"Sum of increments: {sum(inc for _, _, _, _, inc in t20_fired_steps):.6f}")

print("\n" + "="*80)
if len(t20_fired_steps) < total_steps:
    print(f"🔴 T20 is SKIPPING steps! Only fired on {len(t20_fired_steps)}/{total_steps} steps")
    print("   This explains the reduced firing rate!")
else:
    print(f"✓ T20 fires on every step")
