#!/usr/bin/env python3
"""
Quick diagnostic script to check if model migration was successful.
Run with: python check_migration.py
"""

import json

model_path = "workspace/projects/Biochemical-Examples/17_Lac_Operon_Regulation/model.shy"

print("=" * 60)
print("CHECKING MODEL MIGRATION STATUS")
print("=" * 60)

try:
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    print(f"\n✓ Successfully loaded {model_path}")
    
    # Check transitions
    transitions = model_data.get('transitions', [])
    print(f"\nFound {len(transitions)} transitions")
    
    # Check T4, T5, T6 specifically
    target_transitions = ['T4', 'T5', 'T6']
    
    for trans_id in target_transitions:
        trans = next((t for t in transitions if t.get('id') == trans_id), None)
        if trans:
            print(f"\n--- Transition {trans_id} ---")
            print(f"  Name: {trans.get('name')}")
            print(f"  Type: {trans.get('transition_type')}")
            
            props = trans.get('properties', {})
            if 'rate_function' in props:
                print(f"  ✓ Has rate_function: {props['rate_function']}")
            else:
                print(f"  ✗ NO rate_function in properties!")
                print(f"  Properties keys: {list(props.keys())}")
            
            # Check if old rate field exists
            if 'rate' in trans:
                print(f"  ⚠ Still has 'rate' field: {trans['rate']}")
        else:
            print(f"\n✗ Transition {trans_id} NOT FOUND!")
    
    # Check places
    places = model_data.get('places', [])
    print(f"\n\nFound {len(places)} places:")
    for place in places:
        print(f"  - {place.get('name')} (ID: {place.get('id')})")
    
    print("\n" + "=" * 60)
    print("MIGRATION CHECK COMPLETE")
    print("=" * 60)
    
except FileNotFoundError:
    print(f"\n✗ ERROR: Could not find {model_path}")
    print("Make sure you're running from the shypn project root directory")
except json.JSONDecodeError as e:
    print(f"\n✗ ERROR: Invalid JSON in {model_path}")
    print(f"Details: {e}")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
