#!/usr/bin/env python3
"""
Align tumor series exactly with normal series configuration.
- Set T5, T6, T10, T11 to "adaptive" type
- Copy rate functions from properties to adaptive transitions
- Remove redundant top-level rate_function from continuous transitions
"""

import json
from pathlib import Path

BASE_PATH = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NME_VARIANTS = list(range(8))

# Transitions that should be adaptive
ADAPTIVE_TRANSITIONS = ['T5', 'T6', 'T10', 'T11']

# Continuous transitions (should only have rate_function in properties)
CONTINUOUS_TRANSITIONS = ['T1', 'T2', 'T3', 'T4', 'T7', 'T8', 'T9']

def align_model(normal_path: Path, tumor_path: Path, variant_num: int):
    """Align tumor model with normal model configuration."""
    
    # Load both models
    with open(normal_path, 'r') as f:
        normal_model = json.load(f)
    
    with open(tumor_path, 'r') as f:
        tumor_model = json.load(f)
    
    # Create lookup dictionaries
    normal_trans = {t['id']: t for t in normal_model['transitions']}
    tumor_trans = {t['id']: t for t in tumor_model['transitions']}
    
    changes = []
    
    # Fix adaptive transitions
    for trans_id in ADAPTIVE_TRANSITIONS:
        if trans_id in tumor_trans and trans_id in normal_trans:
            tumor_t = tumor_trans[trans_id]
            normal_t = normal_trans[trans_id]
            
            # Set type to adaptive
            old_type = tumor_t.get('transition_type', '')
            if old_type != 'adaptive':
                tumor_t['transition_type'] = 'adaptive'
                changes.append(f"{trans_id}: {old_type} → adaptive")
            
            # Copy rate_function from normal model's properties
            if 'properties' in normal_t and 'rate_function' in normal_t['properties']:
                if 'properties' not in tumor_t:
                    tumor_t['properties'] = {}
                tumor_t['properties']['rate_function'] = normal_t['properties']['rate_function']
                changes.append(f"{trans_id}: Added properties.rate_function")
            
            # Remove top-level rate_function if exists
            if 'rate_function' in tumor_t:
                del tumor_t['rate_function']
                changes.append(f"{trans_id}: Removed top-level rate_function")
    
    # Fix continuous transitions
    for trans_id in CONTINUOUS_TRANSITIONS:
        if trans_id in tumor_trans:
            tumor_t = tumor_trans[trans_id]
            
            # Remove top-level rate_function (should only be in properties)
            if 'rate_function' in tumor_t:
                # Keep it in properties, remove from top level
                del tumor_t['rate_function']
                changes.append(f"{trans_id}: Removed redundant top-level rate_function")
    
    # Save aligned model
    with open(tumor_path, 'w') as f:
        json.dump(tumor_model, f, indent=2)
    
    return changes

def main():
    """Align all tumor models with normal series."""
    print("=" * 80)
    print("ALIGNING TUMOR SERIES WITH NORMAL SERIES")
    print("=" * 80)
    print("\nChanges:")
    print("  1. Set T5, T6, T10, T11 to 'adaptive' type")
    print("  2. Add rate_function to properties dict for adaptive transitions")
    print("  3. Remove top-level rate_function from continuous transitions")
    print()
    
    total_changes = 0
    
    for i in NME_VARIANTS:
        normal_path = BASE_PATH / f'macrocycle_transport_normal_nme_{i}_enhanced.shy'
        tumor_path = BASE_PATH / f'macrocycle_transport_tumor_nme_{i}_enhanced.shy'
        
        if not normal_path.exists():
            print(f"❌ N-Me {i}: Normal model not found")
            continue
        
        if not tumor_path.exists():
            print(f"❌ N-Me {i}: Tumor model not found")
            continue
        
        print(f"\n{'─' * 80}")
        print(f"N-Me {i} (tumor)")
        print(f"{'─' * 80}")
        
        changes = align_model(normal_path, tumor_path, i)
        
        if changes:
            total_changes += len(changes)
            for change in changes:
                print(f"  ✓ {change}")
        else:
            print(f"  ℹ Already aligned")
    
    print(f"\n{'=' * 80}")
    print(f"ALIGNMENT COMPLETE")
    print(f"{'=' * 80}")
    print(f"\nTotal changes: {total_changes}")
    print("\n✅ All tumor models now match normal series configuration")

if __name__ == "__main__":
    main()
