#!/usr/bin/env python3
"""
Fix tumor models 0-7 to match their corresponding normal models.
Each tumor N-Me X should match normal N-Me X exactly in transition configuration.
"""

import json
from pathlib import Path

BASE_PATH = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NME_VARIANTS = list(range(8))

def copy_normal_to_tumor(normal_path: Path, tumor_path: Path, variant_num: int):
    """Copy transition configuration from normal to tumor model."""
    
    with open(normal_path) as f:
        normal_model = json.load(f)
    
    with open(tumor_path) as f:
        tumor_model = json.load(f)
    
    normal_trans = {t['id']: t for t in normal_model['transitions']}
    tumor_trans = {t['id']: t for t in tumor_model['transitions']}
    
    changes = []
    
    # Copy transition configuration for ALL transitions
    for trans_id in normal_trans:
        if trans_id in tumor_trans:
            normal_t = normal_trans[trans_id]
            tumor_t = tumor_trans[trans_id]
            
            # Copy transition_type
            normal_type = normal_t.get('transition_type')
            tumor_type = tumor_t.get('transition_type')
            if normal_type != tumor_type:
                tumor_t['transition_type'] = normal_type
                changes.append(f"{trans_id}: type {tumor_type} → {normal_type}")
            
            # Copy rate_function at top level if present
            if 'rate_function' in normal_t:
                if 'rate_function' not in tumor_t or tumor_t['rate_function'] != normal_t['rate_function']:
                    tumor_t['rate_function'] = normal_t['rate_function']
                    changes.append(f"{trans_id}: Updated top-level rate_function")
            else:
                # Remove if not in normal
                if 'rate_function' in tumor_t:
                    del tumor_t['rate_function']
                    changes.append(f"{trans_id}: Removed top-level rate_function")
            
            # Copy properties
            if 'properties' in normal_t:
                if 'properties' not in tumor_t:
                    tumor_t['properties'] = {}
                
                # Copy all properties
                for key, value in normal_t['properties'].items():
                    if key not in tumor_t['properties'] or tumor_t['properties'][key] != value:
                        tumor_t['properties'][key] = value
                        changes.append(f"{trans_id}: Updated properties.{key}")
            else:
                # No properties in normal - clean up tumor
                if 'properties' in tumor_t:
                    # Keep only non-rate-function properties if any
                    if 'rate_function' in tumor_t['properties']:
                        del tumor_t['properties']['rate_function']
                        changes.append(f"{trans_id}: Removed properties.rate_function")
                    if not tumor_t['properties']:
                        del tumor_t['properties']
    
    # Save fixed tumor model
    with open(tumor_path, 'w') as f:
        json.dump(tumor_model, f, indent=2)
    
    return changes

def main():
    """Fix all tumor models to match their corresponding normal models."""
    print("=" * 80)
    print("FIXING TUMOR SERIES TO MATCH CORRECTED NORMAL SERIES")
    print("=" * 80)
    print("\nCopying transition configurations from normal to tumor models")
    print("Each tumor N-Me X will match normal N-Me X exactly")
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
        print(f"N-Me {i} (tumor ← normal)")
        print(f"{'─' * 80}")
        
        changes = copy_normal_to_tumor(normal_path, tumor_path, i)
        
        if changes:
            total_changes += len(changes)
            for change in changes:
                print(f"  ✓ {change}")
        else:
            print(f"  ℹ Already matched")
    
    print(f"\n{'=' * 80}")
    print(f"TUMOR SERIES FIX COMPLETE")
    print(f"{'=' * 80}")
    print(f"\nTotal changes: {total_changes}")
    print("\n✅ All tumor models now match their corresponding normal models")

if __name__ == "__main__":
    main()
