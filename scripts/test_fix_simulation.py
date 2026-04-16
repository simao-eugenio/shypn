#!/usr/bin/env python3
"""Test the conflict resolution fix by running a full simulation."""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
os.chdir('/home/simao/projetos/shypn/workspace/projects/My_Project/thermodynamics')

# Import after path setup
from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

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

# Configure simulation - use model settings
controller = SimulationController(model)

# Set up data export
controller.export_energy_data = True

# Run simulation
print("Running 60-second simulation with conflict resolution fix...")
print("Expected: T19, T20, T21 should all fire on every step (100% rate)")
print()

target_time = 60.0
dt = 0.006
max_steps = int(target_time / dt) + 1

step_count = 0
while controller.time < target_time and step_count < max_steps:
    controller.step()
    step_count += 1
    if step_count % 1000 == 0:
        print(f"  Progress: t={controller.time:.2f}s ({step_count:,} steps)")

print(f"  Completed: t={controller.time:.2f}s ({step_count:,} steps)")


print('\n' + '='*80)
print('SIMULATION COMPLETE - Analyzing Results')
print('='*80)

# Analyze results
import csv
with open('simulation_energy.csv', 'r') as f:
    reader = csv.DictReader(f)
    data = list(reader)
    
# Get final values
final = data[-1]
initial = data[0]

print(f'\nATP Dynamics:')
print(f'  Initial: {float(initial["ATP"]):,.2f} mM')
print(f'  Final:   {float(final["ATP"]):,.2f} mM')
print(f'  Change:  {float(final["ATP"]) - float(initial["ATP"]):+,.2f} mM')

print(f'\nADP Dynamics:')
print(f'  Initial: {float(initial["ADP"]):,.2f} mM')
print(f'  Final:   {float(final["ADP"]):,.2f} mM')
print(f'  Change:  {float(final["ADP"]) - float(initial["ADP"]):+,.2f} mM')

print(f'\nGTP Dynamics:')
print(f'  Initial: {float(initial["GTP"]):,.2f} mM')
print(f'  Final:   {float(final["GTP"]):,.2f} mM')
print(f'  Change:  {float(final["GTP"]) - float(initial["GTP"]):+,.2f} mM')

# Count T20 firing stats
t20_enabled_count = sum(1 for row in data if float(row['T20_enabled']) > 0)
total_steps = len(data)
t20_enabled_pct = (t20_enabled_count / total_steps) * 100

print(f'\nT20 (ATP Regeneration) Status:')
print(f'  Enabled: {t20_enabled_count:,}/{total_steps:,} steps ({t20_enabled_pct:.1f}%)')
print(f'  Expected rate: 2.273 firings/s')
print(f'  Simulation time: 60 seconds')
print(f'  Expected total firings: ~136.4')

# Check if homeostasis achieved
atp_final = float(final["ATP"])
if atp_final > 4000:
    print(f'\n✓ ATP HOMEOSTASIS ACHIEVED: {atp_final:.2f} mM (target: ~5000 mM)')
else:
    print(f'\n✗ ATP HOMEOSTASIS FAILED: {atp_final:.2f} mM (collapsed)')
