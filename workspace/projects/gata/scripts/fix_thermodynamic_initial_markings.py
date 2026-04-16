#!/usr/bin/env python3
"""
Set initial_marking for thermodynamic parameter places.

The places were created with 'tokens' but shypn uses 'initial_marking'.
"""

import json
import shutil
from pathlib import Path

MODEL_FILE = Path(__file__).parent.parent / 'models' / 'phase3a_spatial.shy'

print("=" * 70)
print("FIX THERMODYNAMIC PARAMETER INITIAL MARKINGS")
print("=" * 70)
print()

# Backup
backup_file = MODEL_FILE.with_suffix('.shy.backup_before_marking_fix')
shutil.copy2(MODEL_FILE, backup_file)
print(f"✅ Backup created: {backup_file.name}")
print()

# Load model
with open(MODEL_FILE, 'r') as f:
    model = json.load(f)

# Define correct initial markings
initial_markings = {
    'pH_cytoplasm': 7.2,      # Physiological cytoplasmic pH
    'pH_nucleus': 7.5,         # Nuclear pH (slightly basic)
    'Mg_cytoplasm': 1.0,       # mM free Mg²⁺
    'Temperature': 310.15      # K (37°C)
}

print("Setting initial markings:")
print("=" * 70)

updated_count = 0
for p in model['places']:
    if p['name'] in initial_markings:
        old_marking = p.get('initial_marking', 0)
        new_marking = initial_markings[p['name']]
        
        p['initial_marking'] = new_marking
        
        # Also set capacity to Infinity so they can't be depleted
        p['capacity'] = 'Infinity'
        
        # Remove 'tokens' field if present (not used)
        if 'tokens' in p:
            del p['tokens']
        
        print(f"✅ {p['name']} ({p['id']}):")
        print(f"   initial_marking: {old_marking} → {new_marking}")
        print(f"   capacity: 0 → Infinity")
        print()
        
        updated_count += 1

# Save model
with open(MODEL_FILE, 'w') as f:
    json.dump(model, f, indent=2)

print("=" * 70)
print(f"SUMMARY: Updated {updated_count} parameter places")
print("=" * 70)
print()
print(f"✅ Model saved: {MODEL_FILE}")
print(f"✅ Backup: {backup_file.name}")
print()

print("Thermodynamic parameters now have correct initial markings:")
for name, value in initial_markings.items():
    print(f"  • {name}: {value}")
print()
print("All parameter places set to capacity=Infinity (constant values)")
print()

print("=" * 70)
print("INITIAL MARKINGS FIXED")
print("=" * 70)
