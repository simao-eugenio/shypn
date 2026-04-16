#!/usr/bin/env python3
"""Test script to verify race policy fix for continuous transitions."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Load model
model_path = 'workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy'
print(f"Loading model: {model_path}")
document = DocumentModel.load_from_file(model_path)

print(f"Model loaded successfully!")
print(f"Places: {len(document.places)}")
print(f"Transitions: {len(document.transitions)}")
print(f"Arcs: {len(document.arcs)}")

# Create controller
from shypn.core.value_objects import RecordingConfig
recording_config = RecordingConfig(
    recording_interval=1,
    time_based_recording=True,
    recording_time_interval=0.05,
    recorded_objects=None
)
controller = SimulationController(document, verbose=False, recording_config=recording_config)

# Configure simulation
controller.settings.duration = 100.0
controller.settings.use_tau_leaping = True
controller.settings.tau_epsilon = 0.03
controller.settings.max_tau = 0.01

# Run simulation
print("\nRunning 100s simulation with fixed race policy...")
controller.time = 0.0
controller.data_collector.start_collection()
controller.data_collector.record_state(controller.time)

dt = controller.settings.get_effective_dt()
max_steps = int(100.0 / dt)
print(f"Time step: {dt}s, Max steps: {max_steps}")

controller._update_enablement_states()

for step_num in range(max_steps):
    success = controller.step(time_step=dt)
    if not success:
        print(f"Stopped at step {step_num} (deadlock)")
        break
    if step_num % 1000 == 0:
        print(f"  Step {step_num}/{max_steps} ({100*step_num/max_steps:.1f}%), time={controller.time:.2f}s")

print(f"\nSimulation complete! Final time: {controller.time:.2f}s")

# Export results
output_file = '/tmp/test_race_fix.csv'
controller.data_collector.export_csv(output_file)
print(f"Exported to: {output_file}")

# Analyze results
import csv

with open(output_file, 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
if len(rows) > 0:
    last_row = rows[-1]
    
    if 'ion_leak (firings)' in last_row:
        t14_final = float(last_row['ion_leak (firings)'])
        vm_final = float(last_row['Membrane_potential (mM)'])

        print(f"\nResults:")
        print(f"T14 cumulative firings: {t14_final:.2f}")
        print(f"Final Membrane_potential: {vm_final:.2f} mM")

        # Compare to buggy version
        buggy_t14 = 7.11
        improvement = (t14_final / buggy_t14 - 1) * 100

        print(f"\nComparison:")
        print(f"Buggy version T14 firings: {buggy_t14:.2f}")
        print(f"Fixed version T14 firings: {t14_final:.2f}")
        print(f"Improvement: {improvement:+.1f}%")

        if t14_final > 50:
            print("\n✓ FIX SUCCESSFUL! T14 firing rate dramatically increased!")
        else:
            print("\n✗ Fix may not be working properly.")
    else:
        print(f"\nColumns in output: {list(last_row.keys())}")
        print("\n✗ Could not find ion_leak (firings) column")
else:
    print("\n✗ No data in output file")
