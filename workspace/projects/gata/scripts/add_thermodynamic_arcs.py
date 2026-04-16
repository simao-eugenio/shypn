#!/usr/bin/env python3
"""
Add test arcs from thermodynamic parameter places to transitions.

Connects pH_cytoplasm, pH_nucleus, Mg_cytoplasm, Temperature places
to transitions that use them in rate functions.
"""

import json
import shutil
from pathlib import Path

MODEL_FILE = Path(__file__).parent.parent / 'models' / 'phase3a_spatial.shy'

print("=" * 70)
print("ADD THERMODYNAMIC PARAMETER ARCS")
print("=" * 70)
print()

# Backup
backup_file = MODEL_FILE.with_suffix('.shy.backup_before_thermo_arcs')
shutil.copy2(MODEL_FILE, backup_file)
print(f"✅ Backup created: {backup_file.name}")
print()

# Load model
with open(MODEL_FILE, 'r') as f:
    model = json.load(f)

# Find parameter place IDs
place_ids = {}
for p in model['places']:
    if p['name'] in ['pH_cytoplasm', 'pH_nucleus', 'Mg_cytoplasm', 'Temperature']:
        place_ids[p['name']] = p['id']

print("Thermodynamic parameter places:")
for name, pid in place_ids.items():
    print(f"  {name}: {pid}")
print()

# Find transitions that use these parameters
transitions_needing_arcs = []

for t in model['transitions']:
    rate = t.get('properties', {}).get('rate_function', '')
    needs = []
    
    if 'pH_cytoplasm' in rate:
        needs.append('pH_cytoplasm')
    if 'pH_nucleus' in rate:
        needs.append('pH_nucleus')
    if 'Mg_cytoplasm' in rate:
        needs.append('Mg_cytoplasm')
    if 'Temperature' in rate:
        needs.append('Temperature')
    
    if needs:
        transitions_needing_arcs.append({
            'id': t['id'],
            'name': t['name'],
            'params': needs
        })

print(f"Found {len(transitions_needing_arcs)} transitions needing parameter arcs:")
for t in transitions_needing_arcs:
    print(f"  {t['name']} ({t['id']}): {', '.join(t['params'])}")
print()

# Find next available arc ID
existing_arc_ids = {arc['id'] for arc in model['arcs']}
next_arc_num = max([int(arc['id'][1:]) for arc in model['arcs']]) + 1

def get_new_arc_id():
    global next_arc_num
    while f"A{next_arc_num}" in existing_arc_ids:
        next_arc_num += 1
    arc_id = f"A{next_arc_num}"
    existing_arc_ids.add(arc_id)
    next_arc_num += 1
    return arc_id

# Create test arcs (read arcs that don't consume tokens)
new_arcs = []

print("=" * 70)
print("CREATING TEST ARCS")
print("=" * 70)
print()

for t_info in transitions_needing_arcs:
    transition_id = t_info['id']
    transition_name = t_info['name']
    
    print(f"{transition_name} ({transition_id}):")
    
    for param_name in t_info['params']:
        param_id = place_ids[param_name]
        arc_id = get_new_arc_id()
        
        # Create test arc (inhibitor type with threshold = infinity acts as read arc)
        # Or use bidirectional normal arc with weight 0
        # Best: use "test" arc type if supported, otherwise "inhibitor" with high threshold
        
        arc = {
            "id": arc_id,
            "name": arc_id,
            "label": "",
            "object_type": "arc",
            "arc_type": "test",  # Test arc - reads but doesn't consume
            "source_id": param_id,
            "source_type": "place",
            "target_id": transition_id,
            "target_type": "transition",
            "weight": 1.0,
            "threshold": None,
            "color": [0.5, 0.5, 0.5],  # Gray for parameter arcs
            "width": 1.5,
            "control_points": []
        }
        
        new_arcs.append(arc)
        print(f"  ✅ {arc_id}: {param_name} ({param_id}) --test--> {transition_id}")

print()
print(f"Total new arcs: {len(new_arcs)}")
print()

# Add arcs to model
model['arcs'].extend(new_arcs)

# Save model
with open(MODEL_FILE, 'w') as f:
    json.dump(model, f, indent=2)

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print(f"✅ Added {len(new_arcs)} test arcs")
print(f"✅ Model saved: {MODEL_FILE}")
print(f"✅ Backup: {backup_file.name}")
print()

print("Test arcs connect parameters to transitions without consuming tokens.")
print("This allows rate functions to read parameter values while keeping them constant.")
print()

print("=" * 70)
print("ARC CONNECTIONS COMPLETE")
print("=" * 70)
