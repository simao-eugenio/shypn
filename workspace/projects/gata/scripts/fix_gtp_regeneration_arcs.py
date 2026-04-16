#!/usr/bin/env python3
"""
Fix GTP_regeneration transition by adding missing arcs.

The transition has a rate function but no arcs connecting it to places.
This script adds the necessary stoichiometric arcs.

Reaction: GDP + ATP → GTP + ADP
"""

import json
import shutil
from pathlib import Path

MODEL_FILE = Path(__file__).parent.parent / 'models' / 'phase3a_spatial.shy'

print("=" * 60)
print("FIX GTP_REGENERATION ARCS")
print("=" * 60)
print()

# Backup
backup_file = MODEL_FILE.with_suffix('.shy.backup_before_arcs_fix')
shutil.copy2(MODEL_FILE, backup_file)
print(f"✅ Backup created: {backup_file}")
print()

# Load model
with open(MODEL_FILE, 'r') as f:
    model = json.load(f)

# Find place IDs
places = {p['name']: p['id'] for p in model['places']}
gdp_id = places.get('GDP')
atp_id = places.get('ATP')
gtp_id = places.get('GTP')
adp_id = places.get('ADP')

print(f"Place IDs:")
print(f"  GDP: {gdp_id}")
print(f"  ATP: {atp_id}")
print(f"  GTP: {gtp_id}")
print(f"  ADP: {adp_id}")
print()

if not all([gdp_id, atp_id, gtp_id, adp_id]):
    print("❌ ERROR: Not all required places found!")
    exit(1)

# Find T28 (GTP_regeneration)
t28_id = None
for t in model['transitions']:
    if t.get('name') == 'GTP_regeneration':
        t28_id = t['id']
        break

if not t28_id:
    print("❌ ERROR: GTP_regeneration transition not found!")
    exit(1)

print(f"✅ Found GTP_regeneration: {t28_id}")
print()

# Check existing arcs
existing_arcs = [arc for arc in model['arcs'] 
                 if arc.get('source_id') == t28_id or arc.get('target_id') == t28_id]

if existing_arcs:
    print(f"⚠️  Found {len(existing_arcs)} existing arcs - removing them first")
    model['arcs'] = [arc for arc in model['arcs'] 
                     if arc.get('source_id') != t28_id and arc.get('target_id') != t28_id]

# Generate unique arc IDs
existing_arc_ids = {arc['id'] for arc in model['arcs']}
def get_new_arc_id(base_num):
    arc_id = f"A{base_num}"
    while arc_id in existing_arc_ids:
        base_num += 1
        arc_id = f"A{base_num}"
    return arc_id

# Create new arcs
# Reaction: GDP + ATP → GTP + ADP

arc_id_1 = get_new_arc_id(100)
arc_id_2 = get_new_arc_id(101)
arc_id_3 = get_new_arc_id(102)
arc_id_4 = get_new_arc_id(103)

new_arcs = [
    # INPUT: GDP → T28 (consume GDP)
    {
        "id": arc_id_1,
        "name": arc_id_1,
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": gdp_id,
        "source_type": "place",
        "target_id": t28_id,
        "target_type": "transition",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.0, 0.0],
        "width": 2.0,
        "control_points": []
    },
    # INPUT: ATP → T28 (consume ATP)
    {
        "id": arc_id_2,
        "name": arc_id_2,
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": atp_id,
        "source_type": "place",
        "target_id": t28_id,
        "target_type": "transition",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.0, 0.0],
        "width": 2.0,
        "control_points": []
    },
    # OUTPUT: T28 → GTP (produce GTP)
    {
        "id": arc_id_3,
        "name": arc_id_3,
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": t28_id,
        "source_type": "transition",
        "target_id": gtp_id,
        "target_type": "place",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.0, 0.0],
        "width": 2.0,
        "control_points": []
    },
    # OUTPUT: T28 → ADP (produce ADP)
    {
        "id": arc_id_4,
        "name": arc_id_4,
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": t28_id,
        "source_type": "transition",
        "target_id": adp_id,
        "target_type": "place",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.0, 0.0],
        "width": 2.0,
        "control_points": []
    }
]

model['arcs'].extend(new_arcs)

print("=" * 60)
print("ADDED ARCS:")
print("=" * 60)
print()
print("Inputs (consumed):")
print(f"  GDP → T28 (weight=1)")
print(f"  ATP → T28 (weight=1)")
print()
print("Outputs (produced):")
print(f"  T28 → GTP (weight=1)")
print(f"  T28 → ADP (weight=1)")
print()
print("Stoichiometry: GDP + ATP → GTP + ADP")
print()

# Save
with open(MODEL_FILE, 'w') as f:
    json.dump(model, f, indent=2)

print("=" * 60)
print("✅ Model saved with GTP_regeneration arcs")
print(f"✅ Backup: {backup_file.name}")
print("=" * 60)
print()
print("NEXT STEPS:")
print("  1. Load phase3a_spatial.shy in shypn")
print("  2. Run short test (500s)")
print("  3. Verify GTP charge >70%")
print()
