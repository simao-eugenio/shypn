#!/usr/bin/env python3
"""Test Example 08 until transitions activate."""

import sys
import json
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Load Example 08
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/08_Energy_Sensing_Motif/model.shy'

with open(model_path, 'r') as f:
    data = json.load(f)

doc = DocumentModel.from_dict(data)

# Get places
p1_f6p = next(p for p in doc.places if p.id == "P1")
p2_atp = next(p for p in doc.places if p.id == "P2")
p5_f16bp = next(p for p in doc.places if p.id == "P5")

controller = SimulationController(doc)

print("Time\tATP\tF6P\tF16BP\tStatus")
print("-" * 60)

for i in range(100):
    controller.step(time_step=0.1)
    
    status = []
    if p2_atp.tokens >= 2.5:
        status.append("Both blocked")
    elif p2_atp.tokens >= 2.0:
        status.append("T1 active")
    else:
        status.append("Both active")
    
    if i % 10 == 0 or p2_atp.tokens < 2.5:
        print(f"{controller.time:.1f}\t{p2_atp.tokens:.3f}\t{p1_f6p.tokens:.4f}\t{p5_f16bp.tokens:.4f}\t{' '.join(status)}")
    
    if controller.time >= 15.0:
        break

print("\n✅ Simulation complete!")
