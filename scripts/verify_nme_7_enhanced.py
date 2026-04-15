#!/usr/bin/env python3
"""Quick verification of N-Me 7 enhanced model spatial properties"""

import json
from pathlib import Path

model_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_7_enhanced.shy')

with open(model_path, 'r') as f:
    model = json.load(f)

print("="*80)
print("N-ME 7 ENHANCED MODEL VERIFICATION")
print("="*80)

expected = {
    'P3': {'compartment_volume': 0.8, 'diffusion_coefficient': 150.0, 'boundary_type': 'impermeable'},
    'P4': {'compartment_volume': 0.5, 'diffusion_coefficient': 80.0, 'boundary_type': 'impermeable'},
    'P7': {'compartment_volume': 5.0, 'diffusion_coefficient': 300.0, 'boundary_type': 'impermeable'},
    'P8': {'compartment_volume': 5.0, 'diffusion_coefficient': 400.0, 'boundary_type': 'impermeable'},
    'P9': {'compartment_volume': 5.0, 'diffusion_coefficient': 600.0, 'boundary_type': 'impermeable'},
    'P10': {'compartment_volume': 1000.0, 'diffusion_coefficient': 2200.0, 'boundary_type': 'permeable'},
    'P11': {'compartment_volume': 0.1, 'diffusion_coefficient': 0.0, 'boundary_type': 'selective', 'gradient_vector': [1.0, 0.0, 0.0]},
    'P12': {'compartment_volume': 0.1, 'diffusion_coefficient': 0.0, 'boundary_type': 'selective', 'gradient_vector': [1.0, 0.0, 0.0]},
}

all_correct = True

for place in model['places']:
    place_id = place.get('id')
    if place_id in expected:
        place_name = place.get('name', 'UNNAMED')
        print(f"\n✓ {place_id} ({place_name}):")
        for prop, value in expected[place_id].items():
            actual = place.get(prop)
            if actual == value:
                print(f"   ✅ {prop}: {value}")
            else:
                print(f"   ❌ {prop}: {actual} (expected {value})")
                all_correct = False

print("\n" + "="*80)
if all_correct:
    print("✅ SUCCESS! All spatial properties correctly configured!")
else:
    print("❌ FAILED! Some properties are incorrect!")
print("="*80)
