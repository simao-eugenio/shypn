#!/usr/bin/env python3
"""Test the ATP homeostasis improvements."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

print('Loading updated model...')
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

print('Running 60-second simulation...')
controller = SimulationController(model)

# Run for 60 seconds
step_count = 0
target_time = 60.0
while controller.time < target_time and step_count < 10001:
    controller.step()
    step_count += 1
    if step_count % 2000 == 0:
        # Get ATP level
        for place in model.places:
            if place.name == 'ATP_pool':
                print(f'  t={controller.time:.1f}s: ATP = {place.marking:.2f} mM')
                break

print()
print('='*80)
print('SIMULATION RESULTS')
print('='*80)

# Get final ATP
for place in model.places:
    if place.name == 'ATP_pool':
        atp_final = place.marking
        atp_initial = 5000.0
        print(f'ATP Status:')
        print(f'  Initial: {atp_initial:.2f} mM')
        print(f'  Final:   {atp_final:.2f} mM')
        print(f'  Change:  {atp_final - atp_initial:+.2f} mM ({((atp_final-atp_initial)/atp_initial)*100:+.1f}%)')
        print()
        
        if atp_final > 4000:
            print('✓ SUCCESS: ATP HOMEOSTASIS ACHIEVED!')
            print(f'  Retained {(atp_final/atp_initial)*100:.1f}% of initial ATP')
        elif atp_final > 2000:
            print('✓ IMPROVED: Partial homeostasis')
            print(f'  Better than before (was 19.55 mM, now {atp_final:.2f} mM)')
        elif atp_final > 100:
            print('⚠ BETTER BUT INSUFFICIENT')
            print(f'  ATP still depleting, needs more tuning')
        else:
            print('✗ STILL COLLAPSING')
        break

# Check T20 firing count
for trans in model.transitions:
    if trans.id == 'T20':
        t20_firings = trans.firing_count
        t20_rate = t20_firings / controller.time
        print()
        print(f'T20 (ATP Regen) Performance:')
        print(f'  Total firings: {t20_firings:.2f}')
        print(f'  Rate: {t20_rate:.2f} firings/s')
        print(f'  Expected: ~4.0 firings/s')
        if abs(t20_rate - 4.0) < 0.5:
            print('  Status: ✓ Firing at expected rate')
        break

# Check sporulation completion
for place in model.places:
    if place.name == 'Mature_spore':
        if place.marking > 0:
            print()
            print(f'Sporulation Status:')
            print(f'  Mature spores: {place.marking:.0f} mM')
            print('  Status: ✓ Sporulation completed successfully')
        break

print()
