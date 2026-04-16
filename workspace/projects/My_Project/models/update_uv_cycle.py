#!/usr/bin/env python3
"""
Update UV cycle in model_biological_realistic.shy to use the better implementation
from simulations/model.shy
"""

import json
from pathlib import Path

# Load current model
model_path = Path(__file__).parent / "model_biological_realistic.shy"
with open(model_path) as f:
    model = json.load(f)

print("Updating UV cycle implementation...")
print(f"Current: {len(model['places'])} places, {len(model['transitions'])} transitions, {len(model['arcs'])} arcs")

# Remove old UV-related arcs (A39-A43)
old_arc_ids = ['A39', 'A40', 'A41', 'A42', 'A43']
model['arcs'] = [arc for arc in model['arcs'] if arc['id'] not in old_arc_ids]
print(f"Removed {len(old_arc_ids)} old UV arcs")

# Update T21, T22, T23, add T24
for trans in model['transitions']:
    if trans['id'] == 'T21':
        trans['name'] = 'DNA_Damage_UV'
        trans['label'] = 'DNA Damage\n(UV radiation)'
        trans['x'] = 100.0
        trans['is_source'] = True
        trans['is_sink'] = False
        trans['rate'] = '0.01'
        trans['fill_color'] = [0.8, 0.0, 0.8]
        trans['border_color'] = [0.8, 0.0, 0.8]
    elif trans['id'] == 'T22':
        trans['name'] = 'RecA_Activation'
        trans['label'] = 'RecA Activation\n(DNA damage)'
        trans['y'] = 150.0
        trans['is_source'] = False
        trans['is_sink'] = False
        trans['rate'] = '0.5 * DNA_Damage * RecA_Inactive'
        trans['fill_color'] = [0.8, 0.2, 0.2]
        trans['border_color'] = [0.8, 0.2, 0.2]
    elif trans['id'] == 'T23':
        trans['name'] = 'RecA_Deactivation'
        trans['label'] = 'RecA\nDeactivation'
        trans['y'] = 250.0
        trans['is_source'] = False
        trans['is_sink'] = False  # Changed from True - RecA goes back to inactive pool
        trans['rate'] = '0.1 * RecA_Active'

# Add T24 - DNA Repair
model['transitions'].append({
    "id": "T24",
    "name": "DNA_Repair",
    "label": "DNA Repair",
    "object_type": "transition",
    "x": 200.0,
    "y": 300.0,
    "width": 60.0,
    "height": 15.0,
    "horizontal": True,
    "enabled": True,
    "fill_color": [0.0, 0.6, 0.2],
    "border_color": [0.0, 0.6, 0.2],
    "border_width": 3.0,
    "transition_type": "stochastic",
    "priority": 0,
    "firing_policy": "race",
    "is_source": False,
    "is_sink": True,
    "guard": 1,
    "rate": "0.05 * DNA_Damage"
})

print("Updated transitions T21, T22, T23 and added T24")

# Add new arcs for UV cycle
new_arcs = [
    # T21 (DNA_Damage_UV) → P15 (DNA_Damage) - source generates damage
    {
        "id": "A39",
        "name": "A39",
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": "T21",
        "source_type": "transition",
        "target_id": "P15",
        "target_type": "place",
        "weight": 1.0,
        "threshold": None,
        "color": [0.8, 0.0, 0.8],
        "width": 3.0,
        "control_points": []
    },
    # P15 (DNA_Damage) → T22 (RecA_Activation) - damage activates RecA
    {
        "id": "A40",
        "name": "A40",
        "label": "",
        "object_type": "arc",
        "arc_type": "test",
        "source_id": "P15",
        "source_type": "place",
        "target_id": "T22",
        "target_type": "transition",
        "weight": 1.0,
        "threshold": 1,
        "color": [0.0, 0.0, 0.0],
        "width": 3.0,
        "control_points": [],
        "consumes": False
    },
    # P13 (RecA_Inactive) → T22 (RecA_Activation) - consumes inactive RecA
    {
        "id": "A41",
        "name": "A41",
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": "P13",
        "source_type": "place",
        "target_id": "T22",
        "target_type": "transition",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.0, 0.0],
        "width": 3.0,
        "control_points": []
    },
    # T22 (RecA_Activation) → P14 (RecA_Active) - produces active RecA
    {
        "id": "A42",
        "name": "A42",
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": "T22",
        "source_type": "transition",
        "target_id": "P14",
        "target_type": "place",
        "weight": 1.0,
        "threshold": None,
        "color": [0.8, 0.2, 0.2],
        "width": 3.0,
        "control_points": []
    },
    # P14 (RecA_Active) → T23 (RecA_Deactivation) - active RecA deactivates
    {
        "id": "A43",
        "name": "A43",
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": "P14",
        "source_type": "place",
        "target_id": "T23",
        "target_type": "transition",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.0, 0.0],
        "width": 3.0,
        "control_points": []
    },
    # T23 (RecA_Deactivation) → P13 (RecA_Inactive) - returns to inactive pool
    {
        "id": "A44",
        "name": "A44",
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": "T23",
        "source_type": "transition",
        "target_id": "P13",
        "target_type": "place",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.0, 0.0],
        "width": 3.0,
        "control_points": []
    },
    # P14 (RecA_Active) → T5 (CI_Protein_Decay) - RecA accelerates CI degradation (TEST arc with weight 5)
    {
        "id": "A45",
        "name": "A45",
        "label": "",
        "object_type": "arc",
        "arc_type": "test",
        "source_id": "P14",
        "source_type": "place",
        "target_id": "T5",
        "target_type": "transition",
        "weight": 5.0,
        "threshold": 1,
        "color": [0.8, 0.2, 0.2],
        "width": 3.0,
        "control_points": [],
        "consumes": False
    },
    # P15 (DNA_Damage) → T24 (DNA_Repair) - damage gets repaired
    {
        "id": "A46",
        "name": "A46",
        "label": "",
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": "P15",
        "source_type": "place",
        "target_id": "T24",
        "target_type": "transition",
        "weight": 1.0,
        "threshold": None,
        "color": [0.0, 0.6, 0.2],
        "width": 3.0,
        "control_points": []
    }
]

model['arcs'].extend(new_arcs)
print(f"Added {len(new_arcs)} new UV cycle arcs")

# Update metadata
model['metadata']['object_counts']['places'] = len(model['places'])
model['metadata']['object_counts']['transitions'] = len(model['transitions'])
model['metadata']['object_counts']['arcs'] = len(model['arcs'])
model['metadata']['modified'] = "2025-12-16T21:30:00.000000"
model['metadata']['description'] = "Bistable lambda phage model with realistic UV-induced lysis pathway using RecA cycling mechanism"

print(f"\nUpdated: {len(model['places'])} places, {len(model['transitions'])} transitions, {len(model['arcs'])} arcs")

# Save updated model
with open(model_path, 'w') as f:
    json.dump(model, f, indent=2)

print(f"\n✓ Model updated successfully: {model_path}")
print("\nUV Cycle Implementation:")
print("  - DNA damage accumulates from UV source (T21)")
print("  - DNA damage activates RecA from inactive pool (T22)")
print("  - Active RecA accelerates CI degradation (test arc to T5)")
print("  - RecA deactivates back to pool (T23)")
print("  - DNA damage gets repaired (T24)")
