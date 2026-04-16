#!/usr/bin/env python3
"""
Fix normal models 1-7 to match N-Me 0 configuration.
Copy rate functions from N-Me 0 for T5, T6, T10, T11.
"""

import json
from pathlib import Path

BASE_PATH = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NME_VARIANTS = list(range(8))

# Transitions that should have rate functions (from N-Me 0)
ADAPTIVE_TRANSITIONS = ['T5', 'T6', 'T10', 'T11']

def load_reference_config():
    """Load configuration from N-Me 0 (reference)."""
    reference_path = BASE_PATH / "macrocycle_transport_normal_nme_0_enhanced.shy"
    
    with open(reference_path) as f:
        model = json.load(f)
    
    # Extract transition configurations
    transitions_config = {}
    for trans in model['transitions']:
        if trans['id'] in ADAPTIVE_TRANSITIONS:
            transitions_config[trans['id']] = {
                'transition_type': trans.get('transition_type'),
                'properties': trans.get('properties', {}).copy(),
                'name': trans['name']
            }
    
    return transitions_config

def fix_normal_model(normal_path: Path, reference_config: dict, variant_num: int):
    """Fix normal model to match N-Me 0 configuration."""
    
    with open(normal_path) as f:
        model = json.load(f)
    
    transitions = {t['id']: t for t in model['transitions']}
    changes = []
    
    # Fix adaptive transitions
    for trans_id, ref_config in reference_config.items():
        if trans_id in transitions:
            trans = transitions[trans_id]
            
            # Set type to adaptive
            old_type = trans.get('transition_type', '')
            if old_type != 'adaptive':
                trans['transition_type'] = 'adaptive'
                changes.append(f"{trans_id}: {old_type} → adaptive")
            
            # Copy all properties from reference
            if 'properties' not in trans:
                trans['properties'] = {}
            
            # Copy rate_function and other properties
            for key, value in ref_config['properties'].items():
                if key not in trans['properties'] or trans['properties'][key] != value:
                    trans['properties'][key] = value
                    changes.append(f"{trans_id}: Set properties.{key}")
    
    # Save fixed model
    with open(normal_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    return changes

def main():
    """Fix all normal models 1-7 to match N-Me 0."""
    print("=" * 80)
    print("FIXING NORMAL SERIES 1-7 TO MATCH N-ME 0 CONFIGURATION")
    print("=" * 80)
    print("\nRestoring:")
    print("  • T5, T6: ATP-dependent conformational switching rates")
    print("  • T10, T11: Energy metabolism rates")
    print()
    
    # Load reference configuration from N-Me 0
    reference_config = load_reference_config()
    
    print("Loaded configuration from N-Me 0:")
    for trans_id, config in reference_config.items():
        rate_func = config['properties'].get('rate_function', 'N/A')
        print(f"  {trans_id} ({config['name']}): {rate_func}")
    print()
    
    total_changes = 0
    
    # Fix models 1-7 (model 0 is already correct)
    for i in range(1, 8):
        normal_path = BASE_PATH / f'macrocycle_transport_normal_nme_{i}_enhanced.shy'
        
        if not normal_path.exists():
            print(f"❌ N-Me {i}: File not found")
            continue
        
        print(f"\n{'─' * 80}")
        print(f"N-Me {i} (normal)")
        print(f"{'─' * 80}")
        
        changes = fix_normal_model(normal_path, reference_config, i)
        
        if changes:
            total_changes += len(changes)
            for change in changes:
                print(f"  ✓ {change}")
        else:
            print(f"  ℹ Already correct")
    
    print(f"\n{'=' * 80}")
    print(f"NORMAL SERIES FIX COMPLETE")
    print(f"{'=' * 80}")
    print(f"\nTotal changes: {total_changes}")
    print("\n✅ Normal models 1-7 now match N-Me 0 configuration")

if __name__ == "__main__":
    main()
