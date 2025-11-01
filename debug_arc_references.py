#!/usr/bin/env python3
"""Debug arc object references after model load."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel

# Load model
model_path = 'workspace/projects/Interactive/models/hsa00010.shy'
print("=" * 80)
print(f"LOADING MODEL AND CHECKING OBJECT REFERENCES")
print("=" * 80)

doc = DocumentModel.load_from_file(model_path)

# Find T3
t3 = next((t for t in doc.transitions if t.id == 'T3'), None)
if not t3:
    print("❌ T3 not found!")
    sys.exit(1)

print(f"\nT3 object: {t3}")
print(f"T3 id: {t3.id}")
print(f"T3 Python object id: {id(t3)}")

# Find arcs targeting T3
t3_input_arcs = [arc for arc in doc.arcs if arc.target == t3]
print(f"\nArcs found using 'arc.target == t3': {len(t3_input_arcs)}")

# Also try by ID
t3_input_arcs_by_id = [arc for arc in doc.arcs if hasattr(arc, 'target') and arc.target.id == 'T3']
print(f"Arcs found using 'arc.target.id == T3': {len(t3_input_arcs_by_id)}")

# Check each arc's target reference
print("\n" + "=" * 80)
print("CHECKING ARC TARGET REFERENCES")
print("=" * 80)

for arc in doc.arcs:
    if hasattr(arc, 'target') and hasattr(arc.target, 'id') and arc.target.id == 'T3':
        print(f"\nArc {arc.id}:")
        print(f"  arc.target: {arc.target}")
        print(f"  arc.target Python id: {id(arc.target)}")
        print(f"  arc.target == t3: {arc.target == t3}")
        print(f"  arc.target is t3: {arc.target is t3}")
        print(f"  arc.target.id == t3.id: {arc.target.id == t3.id}")
        
        if arc.target != t3:
            print(f"  ⚠️ WARNING: Objects don't match!")
            print(f"     This arc points to a DIFFERENT T3 object")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if len(t3_input_arcs) == len(t3_input_arcs_by_id):
    print(f"✅ All {len(t3_input_arcs)} arcs have correct object references")
else:
    print(f"❌ MISMATCH!")
    print(f"   By object ref (==): {len(t3_input_arcs)}")
    print(f"   By ID: {len(t3_input_arcs_by_id)}")
    print(f"   Some arc.target references don't match the T3 object!")

