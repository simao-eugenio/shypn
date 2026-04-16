#!/usr/bin/env python3
"""Verify N-Me 7 enhanced model has all required rate_function properties"""

import json
from pathlib import Path

model_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_7_enhanced.shy')

with open(model_path, 'r') as f:
    model = json.load(f)

print("="*80)
print("N-ME 7 ENHANCED MODEL VERIFICATION - TRANSITIONS")
print("="*80)

continuous_transitions = []
missing_rate_functions = []

for transition in model.get('transitions', []):
    trans_type = transition.get('type', '')
    if 'continuous' in trans_type.lower():
        continuous_transitions.append(transition)
        trans_id = transition.get('id')
        trans_name = transition.get('name', 'UNNAMED')
        
        properties = transition.get('properties', {})
        has_rate_function = 'rate_function' in properties
        
        print(f"\n✓ {trans_id} ({trans_name}):")
        print(f"   Type: {trans_type}")
        if has_rate_function:
            print(f"   ✅ rate_function: Present")
        else:
            print(f"   ❌ rate_function: MISSING")
            missing_rate_functions.append(trans_id)

print("\n" + "="*80)
print(f"Continuous transitions found: {len(continuous_transitions)}")
print(f"Missing rate_function: {len(missing_rate_functions)}")

if len(missing_rate_functions) == 0:
    print("\n✅ SUCCESS! All continuous transitions have rate_function properties!")
    print("   The model is ready to be loaded and simulated.")
else:
    print(f"\n❌ FAILED! {len(missing_rate_functions)} transitions still missing rate_function:")
    for trans_id in missing_rate_functions:
        print(f"   • {trans_id}")
print("="*80)
