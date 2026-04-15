#!/usr/bin/env python3
"""Test script to run lambda phage simulation directly (no GUI)."""

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

# Load model
model_path = 'workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/model.shy'
model = DocumentModel.load_from_file(model_path)

print(f"✅ Loaded model: {len(model.places)} places, {len(model.transitions)} transitions")

# Create controller
controller = SimulationController(model)

# Configure simulation settings
controller.settings.duration = 10.0  # 10 seconds
controller.settings.dt = 0.1  # 100ms time step
controller.settings.tau_epsilon = 0.05
controller.settings.max_tau = 0.5
controller.settings.min_tau = 0.001
controller.settings.critical_threshold = 0.01  # Lower threshold - propensities of 0.1 are NOT critical!

print(f"\n▶️  Starting simulation for {controller.settings.duration}s (dt={controller.settings.dt}s)")
print(f"🔧 Tau-leaping: epsilon={controller.settings.tau_epsilon}, max_tau={controller.settings.max_tau}\n")

# Run simulation step-by-step
step_count = 0
max_steps = 100  # Run 100 steps

while step_count < max_steps and controller.time < controller.settings.duration:
    # Execute one simulation step
    activity = controller.step(controller.settings.dt)
    
    step_count += 1
    
    # Print token counts every 10 steps
    if step_count % 10 == 0:
        print(f"\n📊 Step {step_count}, t={controller.time:.2f}s:")
        for place in model.places:
            if place.tokens > 0:
                print(f"   {place.label}: {place.tokens:.2f}")

print(f"\n✅ Simulation complete! Ran {step_count} steps to t={controller.time:.2f}s")
