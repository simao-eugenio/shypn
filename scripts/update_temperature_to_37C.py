#!/usr/bin/env python3
"""
Update thermodynamic settings in all normal models to use 37°C (310.15 K).
"""

import json
from pathlib import Path

models_dir = Path('workspace/projects/My_Project/drug_discovery/models/normal')
models = list(models_dir.glob('macrocycle_transport_normal_nme_*_thermo.shy'))

print(f"Found {len(models)} models to update\n")

for model_path in sorted(models):
    print(f"Updating {model_path.name}...")
    
    # Load model
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    # Check current temperature
    current_temp = data.get('thermodynamic_settings', {}).get('temperature', 'N/A')
    print(f"  Current temperature: {current_temp} K ({current_temp - 273.15:.2f}°C)")
    
    # Update to 37°C (310.15 K)
    if 'thermodynamic_settings' in data:
        data['thermodynamic_settings']['temperature'] = 310.15
        print(f"  Updated to: 310.15 K (37.0°C)")
    else:
        print(f"  ⚠ No thermodynamic_settings found, skipping")
        continue
    
    # Save updated model
    with open(model_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✓ Saved\n")

print(f"{'='*60}")
print(f"✓ Updated {len(models)} models to 37°C (310.15 K)")
print(f"{'='*60}")
