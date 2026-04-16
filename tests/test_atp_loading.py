#!/usr/bin/env python3
"""Quick test to verify ATP transitions load correctly."""

import sys
import json
# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly with python3', allow_module_level=True)

sys.path.insert(0, 'src')

from shypn.netobjs.transition import Transition

print("=" * 70)
print("TESTING ATP TRANSITIONS RATE FUNCTION LOADING")
print("=" * 70)

# Load model JSON directly
model_path = "workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy"
print(f"\nLoading model: {model_path}")

with open(model_path, 'r') as f:
    data = json.load(f)

# Find ATP transitions in JSON
t10_data = None
t11_data = None

for t_data in data['transitions']:
    if t_data['id'] == 'T10':
        t10_data = t_data
    elif t_data['id'] == 'T11':
        t11_data = t_data

# Load transitions
atp_synthesis = Transition.from_dict(t10_data)
basal_atpase = Transition.from_dict(t11_data)

print(f"\n{'='*70}")
print("TRANSITION: ATP_synthesis (T10)")
print(f"{'='*70}")
print(f"ID: {atp_synthesis.id}")
print(f"Name: {atp_synthesis.name}")
print(f"Label: {atp_synthesis.label}")
print(f"Type: {atp_synthesis.transition_type}")
print(f"\nRate function access:")
print(f"  t.rate_function = '{atp_synthesis.rate_function}'")
print(f"  t.properties['rate_function'] = '{atp_synthesis.properties.get('rate_function')}'")
print(f"\nProperties dict:")
print(f"  {atp_synthesis.properties}")

print(f"\n{'='*70}")
print("TRANSITION: basal_ATPase (T11)")
print(f"{'='*70}")
print(f"ID: {basal_atpase.id}")
print(f"Name: {basal_atpase.name}")
print(f"Label: {basal_atpase.label}")
print(f"Type: {basal_atpase.transition_type}")
print(f"\nRate function access:")
print(f"  t.rate_function = '{basal_atpase.rate_function}'")
print(f"  t.properties['rate_function'] = '{basal_atpase.properties.get('rate_function')}'")
print(f"\nProperties dict:")
print(f"  {basal_atpase.properties}")

# Verify they have rate functions
if atp_synthesis.rate_function and basal_atpase.rate_function:
    print(f"\n{'='*70}")
    print("✓ SUCCESS: Both ATP transitions have rate functions!")
    print(f"{'='*70}")
else:
    print(f"\n{'='*70}")
    print("✗ FAILURE: Missing rate functions!")
    print(f"{'='*70}")
    sys.exit(1)
