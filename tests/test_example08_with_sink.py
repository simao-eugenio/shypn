#!/usr/bin/env python3
"""Test Example 08 with ATP sink."""

import sys
import json
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Load Example 08
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/08_Energy_Sensing_Motif/model.shy'

print("=" * 80)
print("EXAMPLE 08 WITH ATP SINK TEST")
print("=" * 80)

# Load model
with open(model_path, 'r') as f:
    data = json.load(f)

doc = DocumentModel.from_dict(data)

# Get places
p1_f6p = next(p for p in doc.places if p.id == "P1")
p2_atp = next(p for p in doc.places if p.id == "P2")

print(f"\nInitial state:")
print(f"  P1 (F6P): {p1_f6p.tokens}")
print(f"  P2 (ATP): {p2_atp.tokens}")

# Check transitions
print(f"\nTransitions:")
for t in doc.transitions:
    print(f"  {t.id} ({t.name}): is_sink={getattr(t, 'is_sink', False)}")

# Create simulation controller
controller = SimulationController(doc)

print(f"\nRunning 10 simulation steps (dt=0.1)...")
print(f"Expected: ATP decreases slowly via T3 sink")
print(f"When ATP < 2.5, T1 activates; when ATP < 2.0, T2 also activates")
print()

for i in range(10):
    result = controller.step(time_step=0.1)
    print(f"Step {i+1}: time={controller.time:.1f}, F6P={p1_f6p.tokens:.4f}, ATP={p2_atp.tokens:.4f}")
    
print(f"\nFinal state:")
print(f"  P1 (F6P): {p1_f6p.tokens}")
print(f"  P2 (ATP): {p2_atp.tokens}")

if p2_atp.tokens < 3.0:
    print("\n✅ SUCCESS: ATP is decreasing (sink is working)")
else:
    print("\n❌ ERROR: ATP not decreasing")
