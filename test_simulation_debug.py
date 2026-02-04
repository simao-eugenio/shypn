#!/usr/bin/env python3
"""
Simple simulation test to trigger rate function evaluation debugging
"""
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

# Load the model
model_path = 'workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy'

# Load using from_file
model = DocumentModel.load_from_file(model_path)

print("Model loaded successfully")
print(f"Found {len(model.transitions)} transitions")

# Find ATP transitions
for t in model.transitions:
    if t.id in ['T10', 'T11']:
        print(f"\nTransition {t.id} ({t.name}):")
        print(f"  Type: {t.transition_type}")
        print(f"  Has properties: {hasattr(t, 'properties')}")
        if hasattr(t, 'properties'):
            print(f"  Properties: {t.properties}")
            print(f"  rate_function: {t.properties.get('rate_function')}")

# Setup simulation
settings = SimulationSettings()
settings.algorithm = 'tau-leap'
settings.duration = 0.1  # Very short - just 0.1 seconds
settings.dt = 0.01

# Create controller
controller = SimulationController(model)
controller.settings = settings  # Set settings on controller
print("\n" + "="*70)
print("Starting simulation...")
print("="*70)

try:
    controller.run(time_step=settings.dt)
    print("\n✅ Simulation completed")
except Exception as e:
    print(f"\n❌ Simulation failed: {e}")
    import traceback
    traceback.print_exc()
