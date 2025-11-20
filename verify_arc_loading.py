#!/usr/bin/env python3
"""Check exact arc loading from model.shy file."""

import sys
import json
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.inhibitor_arc import InhibitorArc

# Load Example 08
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/08_Energy_Sensing_Motif/model.shy'

print("=" * 80)
print("ARC LOADING VERIFICATION")
print("=" * 80)

# Load raw JSON
with open(model_path, 'r') as f:
    data = json.load(f)

print("\nRAW JSON DATA:")
for arc_data in data.get('arcs', []):
    if arc_data.get('id') in ['A9', 'A10']:
        print(f"\n{arc_data['id']}:")
        print(f"  arc_type: {arc_data.get('arc_type')}")
        print(f"  object_type: {arc_data.get('object_type')}")
        print(f"  weight: {arc_data.get('weight')} (type: {type(arc_data.get('weight'))})")
        print(f"  source_id: {arc_data.get('source_id')}")
        print(f"  target_id: {arc_data.get('target_id')}")

# Load through DocumentModel
doc = DocumentModel.from_dict(data)

print("\n" + "=" * 80)
print("LOADED ARC OBJECTS:")
print("=" * 80)

for arc in doc.arcs:
    if arc.id in ['A9', 'A10']:
        print(f"\n{arc.id}:")
        print(f"  Type: {type(arc).__name__}")
        print(f"  Is InhibitorArc: {isinstance(arc, InhibitorArc)}")
        print(f"  weight: {arc.weight} (type: {type(arc.weight)})")
        print(f"  source: {arc.source.id} ({arc.source.name})")
        print(f"  target: {arc.target.id} ({arc.target.name})")
        if hasattr(arc, 'arc_type'):
            print(f"  arc_type: {arc.arc_type}")

# Check source tokens
p2 = next(p for p in doc.places if p.id == "P2")
print(f"\n" + "=" * 80)
print(f"P2 (ATP) tokens: {p2.tokens}")
print(f"A9 threshold (should block T1): {next(a for a in doc.arcs if a.id == 'A9').weight}")
print(f"A10 threshold (should block T2): {next(a for a in doc.arcs if a.id == 'A10').weight}")
print(f"\nP2 >= A9 threshold? {p2.tokens} >= {next(a for a in doc.arcs if a.id == 'A9').weight} = {p2.tokens >= next(a for a in doc.arcs if a.id == 'A9').weight}")
print(f"P2 >= A10 threshold? {p2.tokens} >= {next(a for a in doc.arcs if a.id == 'A10').weight} = {p2.tokens >= next(a for a in doc.arcs if a.id == 'A10').weight}")
