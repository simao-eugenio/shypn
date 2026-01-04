#!/usr/bin/env python3
"""Quick test of inhibitor constraints in simulation."""
import sys
sys.path.insert(0, 'src')

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

# Load model
print("Loading model...")
model = ModelCanvasManager()
model.load_from_file('workspace/projects/My_Project/thermodynamics/bacillus_sporulation_normal.shy')

# Create simulation controller
print("Creating simulation controller...")
controller = SimulationController(model, verbose=True)

# Configure simulation
controller.settings.end_time = 50.0
controller.settings.time_step = 0.1

# Set output file
controller.data_collector.output_file = 'workspace/projects/My_Project/thermodynamics/data/simulation_data_normal.csv'

print("Running simulation...")
print("(Watch for '🔒 Inhibitor constraint' messages)")
print()

# Run
controller.run()

print("\n✅ Simulation complete!")
print(f"Output: {controller.data_collector.output_file}")
