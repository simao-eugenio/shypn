#!/usr/bin/env python3
"""
Fix thermodynamic parameter places to have proper compartment structure.

They should be regular metabolite-like places, not spatial signals.
"""

import json
import shutil
from pathlib import Path

MODEL_FILE = Path(__file__).parent.parent / 'models' / 'phase3a_spatial.shy'

print("=" * 70)
print("FIX THERMODYNAMIC PARAMETER PLACE TYPES")
print("=" * 70)
print()

# Backup
backup_file = MODEL_FILE.with_suffix('.shy.backup_before_place_type_fix')
shutil.copy2(MODEL_FILE, backup_file)
print(f"✅ Backup created: {backup_file.name}")
print()

# Load model
with open(MODEL_FILE, 'r') as f:
    model = json.load(f)

# Define correct structures for thermodynamic parameters
param_configs = {
    'pH_cytoplasm': {
        'compartment': 'cytoplasm',
        'compartment_volume': 4.5,
        'signal_type': None,
        'is_signal_place': False
    },
    'pH_nucleus': {
        'compartment': 'nucleus',
        'compartment_volume': 0.5,
        'signal_type': None,
        'is_signal_place': False
    },
    'Mg_cytoplasm': {
        'compartment': 'cytoplasm',
        'compartment_volume': 4.5,
        'signal_type': None,
        'is_signal_place': False
    },
    'Temperature': {
        'compartment': None,  # Global parameter
        'compartment_volume': None,
        'signal_type': None,
        'is_signal_place': False
    }
}

print("Fixing thermodynamic parameter places:")
print("=" * 70)

updated_count = 0
for p in model['places']:
    if p['name'] in param_configs:
        config = param_configs[p['name']]
        
        print(f"{p['name']} ({p['id']}):")
        
        # Update compartment fields
        old_compartment = p.get('compartment')
        old_volume = p.get('compartment_volume')
        old_signal = p.get('is_signal_place')
        
        p['compartment'] = config['compartment']
        p['compartment_volume'] = config['compartment_volume']
        p['signal_type'] = config['signal_type']
        p['is_signal_place'] = config['is_signal_place']
        
        # Update properties to match
        if 'properties' not in p:
            p['properties'] = {}
        
        if config['compartment']:
            p['properties']['compartment_name'] = config['compartment']
        if config['compartment_volume']:
            p['properties']['compartment_volume'] = config['compartment_volume']
        
        print(f"  compartment: {old_compartment} → {config['compartment']}")
        print(f"  compartment_volume: {old_volume} → {config['compartment_volume']}")
        print(f"  is_signal_place: {old_signal} → {config['is_signal_place']}")
        print(f"  signal_type: → {config['signal_type']}")
        print()
        
        updated_count += 1

# Save model
with open(MODEL_FILE, 'w') as f:
    json.dump(model, f, indent=2)

print("=" * 70)
print(f"SUMMARY: Updated {updated_count} places")
print("=" * 70)
print()
print(f"✅ Model saved: {MODEL_FILE}")
print(f"✅ Backup: {backup_file.name}")
print()

print("Thermodynamic parameters are now properly typed:")
print()
print("  pH_cytoplasm:")
print("    - Compartment: cytoplasm (4.5 fL)")
print("    - Type: Regular metabolite place")
print("    - Not a spatial signal")
print()
print("  pH_nucleus:")
print("    - Compartment: nucleus (0.5 fL)")
print("    - Type: Regular metabolite place")
print("    - Not a spatial signal")
print()
print("  Mg_cytoplasm:")
print("    - Compartment: cytoplasm (4.5 fL)")
print("    - Type: Regular metabolite place")
print("    - Not a spatial signal")
print()
print("  Temperature:")
print("    - Compartment: None (global)")
print("    - Type: Global parameter")
print("    - Not a spatial signal")
print()

print("=" * 70)
print("PLACE TYPES FIXED")
print("=" * 70)
