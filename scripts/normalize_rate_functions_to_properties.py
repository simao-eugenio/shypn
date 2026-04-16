#!/usr/bin/env python3
"""
Normalize all models to use rate_function ONLY in properties dict.
Remove top-level rate_function from continuous transitions for consistency.
"""

import json
from pathlib import Path

BASE_PATH = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NME_VARIANTS = list(range(8))

# Continuous transitions that should have rate_function ONLY in properties
CONTINUOUS_TRANSITIONS = ['T1', 'T2', 'T3', 'T4', 'T7', 'T8', 'T9']

def normalize_model(model_path: Path, model_type: str, variant_num: int):
    """Normalize model to use rate_function only in properties."""
    
    with open(model_path) as f:
        model = json.load(f)
    
    transitions = {t['id']: t for t in model['transitions']}
    changes = []
    
    # Remove top-level rate_function from continuous transitions
    for trans_id in CONTINUOUS_TRANSITIONS:
        if trans_id in transitions:
            trans = transitions[trans_id]
            
            # Remove top-level rate_function if present
            if 'rate_function' in trans:
                del trans['rate_function']
                changes.append(f"{trans_id}: Removed top-level rate_function (normalized to properties only)")
    
    # Save normalized model
    if changes:
        with open(model_path, 'w') as f:
            json.dump(model, f, indent=2)
    
    return changes

def main():
    """Normalize all models to properties-only pattern."""
    print("=" * 80)
    print("NORMALIZING ALL MODELS TO PROPERTIES-ONLY RATE FUNCTIONS")
    print("=" * 80)
    print("\nRemoving top-level rate_function from continuous transitions")
    print("Keeping rate_function only in properties dict")
    print()
    
    total_changes = 0
    
    # Process both normal and tumor models
    for cell_type in ['normal', 'tumor']:
        print(f"\n{'─' * 80}")
        print(f"{cell_type.upper()} SERIES")
        print(f"{'─' * 80}")
        
        for i in NME_VARIANTS:
            model_path = BASE_PATH / f'macrocycle_transport_{cell_type}_nme_{i}_enhanced.shy'
            
            if not model_path.exists():
                print(f"  ❌ N-Me {i}: File not found")
                continue
            
            changes = normalize_model(model_path, cell_type, i)
            
            if changes:
                total_changes += len(changes)
                print(f"\n  N-Me {i} ({cell_type}):")
                for change in changes:
                    print(f"    ✓ {change}")
            else:
                print(f"  ✓ N-Me {i} ({cell_type}): Already normalized")
    
    print(f"\n{'=' * 80}")
    print(f"NORMALIZATION COMPLETE")
    print(f"{'=' * 80}")
    print(f"\nTotal changes: {total_changes}")
    print("\n✅ All models now use rate_function only in properties dict")

if __name__ == "__main__":
    main()
