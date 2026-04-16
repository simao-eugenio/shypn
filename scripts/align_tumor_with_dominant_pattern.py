#!/usr/bin/env python3
"""
Align tumor series with DOMINANT normal pattern (N-Me 2-7):
- T1-T4, T7-T9: continuous with rate_function at TOP level AND in properties
- T5, T6, T10, T11: stochastic with NO rate_function
"""

import json
from pathlib import Path

BASE_PATH = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NME_VARIANTS = list(range(8))

# Reference model with correct pattern
REFERENCE_MODEL = BASE_PATH / "macrocycle_transport_normal_nme_6_enhanced.shy"

# Continuous transitions (should have rate_function at both levels)
CONTINUOUS_TRANSITIONS = ['T1', 'T2', 'T3', 'T4', 'T7', 'T8', 'T9']

# Stochastic transitions (should NOT have rate_function anywhere)
STOCHASTIC_TRANSITIONS = ['T5', 'T6', 'T10', 'T11']

def load_reference_rates():
    """Load rate functions from reference normal model."""
    with open(REFERENCE_MODEL) as f:
        model = json.load(f)
    
    continuous_rates = {}
    for trans in model['transitions']:
        if trans['id'] in CONTINUOUS_TRANSITIONS:
            continuous_rates[trans['id']] = {
                'rate_function': trans.get('rate_function'),
                'props_rate_function': trans.get('properties', {}).get('rate_function')
            }
    
    return continuous_rates

def align_tumor_model(tumor_path: Path, reference_rates: dict, variant_num: int):
    """Align tumor model with dominant normal pattern."""
    
    with open(tumor_path) as f:
        tumor_model = json.load(f)
    
    tumor_trans = {t['id']: t for t in tumor_model['transitions']}
    
    changes = []
    
    # Fix continuous transitions - should have rate_function at BOTH levels
    for trans_id in CONTINUOUS_TRANSITIONS:
        if trans_id in tumor_trans:
            tumor_t = tumor_trans[trans_id]
            ref = reference_rates.get(trans_id, {})
            
            # Ensure type is continuous
            if tumor_t.get('transition_type') != 'continuous':
                tumor_t['transition_type'] = 'continuous'
                changes.append(f"{trans_id}: Set type to continuous")
            
            # Add top-level rate_function
            if 'rate_function' not in tumor_t and ref.get('rate_function'):
                tumor_t['rate_function'] = ref['rate_function']
                changes.append(f"{trans_id}: Added top-level rate_function")
            
            # Ensure properties.rate_function exists
            if 'properties' not in tumor_t:
                tumor_t['properties'] = {}
            if 'rate_function' not in tumor_t['properties'] and ref.get('props_rate_function'):
                tumor_t['properties']['rate_function'] = ref['props_rate_function']
                changes.append(f"{trans_id}: Added properties.rate_function")
    
    # Fix stochastic transitions - should have NO rate_function anywhere
    for trans_id in STOCHASTIC_TRANSITIONS:
        if trans_id in tumor_trans:
            tumor_t = tumor_trans[trans_id]
            
            # Ensure type is stochastic
            if tumor_t.get('transition_type') != 'stochastic':
                old_type = tumor_t.get('transition_type')
                tumor_t['transition_type'] = 'stochastic'
                changes.append(f"{trans_id}: {old_type} → stochastic")
            
            # Remove top-level rate_function if exists
            if 'rate_function' in tumor_t:
                del tumor_t['rate_function']
                changes.append(f"{trans_id}: Removed top-level rate_function")
            
            # Remove properties.rate_function if exists
            if 'properties' in tumor_t and 'rate_function' in tumor_t['properties']:
                del tumor_t['properties']['rate_function']
                changes.append(f"{trans_id}: Removed properties.rate_function")
                # Clean up empty properties dict
                if not tumor_t['properties']:
                    del tumor_t['properties']
    
    # Save aligned model
    with open(tumor_path, 'w') as f:
        json.dump(tumor_model, f, indent=2)
    
    return changes

def main():
    """Align all tumor models with dominant normal pattern (N-Me 2-7)."""
    print("=" * 80)
    print("ALIGNING TUMOR SERIES WITH DOMINANT NORMAL PATTERN (N-Me 2-7)")
    print("=" * 80)
    print("\nPattern:")
    print("  • T1-T4, T7-T9: continuous with top+props rate_function")
    print("  • T5, T6, T10, T11: stochastic with NO rate_function")
    print()
    
    # Load reference rates from N-Me 6 (dominant pattern)
    reference_rates = load_reference_rates()
    print(f"Loaded {len(reference_rates)} continuous transitions from reference\n")
    
    total_changes = 0
    
    for i in NME_VARIANTS:
        tumor_path = BASE_PATH / f'macrocycle_transport_tumor_nme_{i}_enhanced.shy'
        
        if not tumor_path.exists():
            print(f"❌ N-Me {i}: Tumor model not found")
            continue
        
        print(f"\n{'─' * 80}")
        print(f"N-Me {i} (tumor)")
        print(f"{'─' * 80}")
        
        changes = align_tumor_model(tumor_path, reference_rates, i)
        
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
    print("\n✅ All tumor models now match dominant normal pattern (N-Me 2-7)")

if __name__ == "__main__":
    main()
