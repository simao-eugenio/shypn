#!/usr/bin/env python3
"""Run simulation without GUI"""
import sys
import os

# Suppress GTK
os.environ['DISPLAY'] = ''

sys.path.insert(0, 'src')

# Minimal imports - no GUI
from shypn.engine.simulation.controller import SimulationController
from shypn.canvas.model_canvas_manager import ModelCanvasManager

# Load model
model_path = 'workspace/projects/My_Project/thermodynamics/bacillus_sporulation_normal.shy'
print(f"Loading model: {model_path}")

manager = ModelCanvasManager()
manager.load_from_file(model_path)

print(f"Model loaded: {len(manager.places)} places, {len(manager.transitions)} transitions")

# Configure simulation
controller = SimulationController(manager, verbose=False)
controller.settings.end_time = 50.0
controller.settings.time_step = 0.01
controller.data_collector.output_file = 'workspace/projects/My_Project/thermodynamics/data/simulation_data_normal.csv'
controller.data_collector.output_interval = 0.05

print("Running simulation...")
controller.run()

print(f"\n✅ Simulation complete: {controller.time:.1f}s")
print(f"Results: {controller.data_collector.output_file}")
