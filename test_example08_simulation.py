#!/usr/bin/env python3
"""Test Example 08 with actual simulation steps."""

import sys
import json
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Load Example 08
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/08_Energy_Sensing_Motif/model.shy'

print("=" * 80)
print("EXAMPLE 08 SIMULATION TEST")
print("=" * 80)

# Load model
with open(model_path, 'r') as f:
    data = json.load(f)

doc = DocumentModel.from_dict(data)

# Get initial state
p1_f6p = next(p for p in doc.places if p.id == "P1")
p2_atp = next(p for p in doc.places if p.id == "P2")
p6_pep = next(p for p in doc.places if p.id == "P6")

print(f"\nInitial state:")
print(f"  P1 (F6P): {p1_f6p.tokens}")
print(f"  P2 (ATP): {p2_atp.tokens}")
print(f"  P6 (PEP): {p6_pep.tokens}")

# Create simulation controller
controller = SimulationController(doc)

print(f"\nRunning 5 simulation steps (dt=0.1)...")
print(f"Expected: NO changes (both transitions blocked by inhibitors)")
print()

for i in range(5):
    result = controller.step(time_step=0.1)
    print(f"Step {i+1}: time={controller.time:.1f}, P1={p1_f6p.tokens:.4f}, P2={p2_atp.tokens:.4f}, P6={p6_pep.tokens:.4f}")
    
print(f"\nFinal state:")
print(f"  P1 (F6P): {p1_f6p.tokens} (expected: 0.1)")
print(f"  P2 (ATP): {p2_atp.tokens} (expected: 3.0)")
print(f"  P6 (PEP): {p6_pep.tokens} (expected: 0.05)")

# Check if values changed
f6p_changed = abs(p1_f6p.tokens - 0.1) > 0.001
atp_changed = abs(p2_atp.tokens - 3.0) > 0.001
pep_changed = abs(p6_pep.tokens - 0.05) > 0.001

if f6p_changed or atp_changed or pep_changed:
    print("\n❌ ERROR: Tokens changed when transitions should be inhibited!")
    if f6p_changed:
        print(f"   F6P changed from 0.1 to {p1_f6p.tokens}")
    if atp_changed:
        print(f"   ATP changed from 3.0 to {p2_atp.tokens}")
    if pep_changed:
        print(f"   PEP changed from 0.05 to {p6_pep.tokens}")
else:
    print("\n✅ CORRECT: No tokens consumed (transitions properly inhibited)")
