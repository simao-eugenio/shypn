#!/usr/bin/env python3
"""
Test to verify that user-defined place names (like ATP_pool, ADP_pool) 
are correctly resolved in rate functions without incorrect 'P' prefix addition.
"""
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel

# Load the model with ATP transitions
model_path = 'workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy'
model = DocumentModel.load_from_file(model_path)

print("="*70)
print("PLACE NAME RESOLUTION FIX VERIFICATION")
print("="*70)

# Find ATP transitions
atp_transitions = []
for t in model.transitions:
    if t.id in ['T10', 'T11']:
        atp_transitions.append(t)
        print(f"\n✓ Found {t.id} ({t.name})")
        print(f"  rate_function: {t.properties.get('rate_function')}")

# Verify places exist with correct names
print("\n" + "="*70)
print("PLACE VERIFICATION")
print("="*70)
for place in model.places:
    if 'ATP' in place.name or 'ADP' in place.name:
        print(f"\n✓ {place.id}: name='{place.name}', tokens={place.tokens}")

# Create controller and run minimal simulation
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

settings = SimulationSettings()
settings.algorithm = 'tau-leap'
settings.duration = 0.01  # Very short
settings.dt = 0.001

controller = SimulationController(model)
controller.settings = settings

print("\n" + "="*70)
print("SIMULATION TEST")
print("="*70)
print("Running 0.01s simulation with tau-leaping...")

try:
    controller.run(time_step=settings.dt)
    print("\n✅ SUCCESS: Simulation completed without NameError!")
    print("   The fix works correctly - user-defined names are resolved properly.")
except NameError as e:
    print(f"\n❌ FAILED: {e}")
    print("   Place names are not being resolved correctly.")
    sys.exit(1)
except Exception as e:
    print(f"\n⚠️  Different error (not NameError): {e}")
    print("   The name resolution might be working, but another issue exists.")
    sys.exit(2)

print("\n" + "="*70)
print("TEST PASSED")
print("="*70)
print("User-defined place names (ATP_pool, ADP_pool) are correctly")
print("resolved in rate function expressions without incorrect prefixing.")
