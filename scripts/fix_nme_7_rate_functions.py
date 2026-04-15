#!/usr/bin/env python3
"""
Fix N-Me 7 Enhanced Model - Copy Transition Rate Functions
==========================================================
Copies rate_function properties from N-Me 6 to N-Me 7.
"""

import json
from pathlib import Path
import shutil

def fix_nme_7_transitions():
    """Fix N-Me 7 by copying transition properties from N-Me 6."""
    
    base_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    
    nme_6_path = base_path / 'macrocycle_transport_normal_nme_6_enhanced.shy'
    nme_7_path = base_path / 'macrocycle_transport_normal_nme_7_enhanced.shy'
    
    print("="*80)
    print("FIX N-ME 7 ENHANCED MODEL")
    print("Copying transition rate functions from N-Me 6")
    print("="*80)
    
    # Load models
    with open(nme_6_path, 'r') as f:
        nme_6 = json.load(f)
    
    with open(nme_7_path, 'r') as f:
        nme_7 = json.load(f)
    
    # Backup N-Me 7
    backup_path = str(nme_7_path) + '.broken_backup'
    shutil.copy2(nme_7_path, backup_path)
    print(f"✅ Backup created: {backup_path}\n")
    
    # Create mapping of transitions by name pattern
    nme_6_transitions = {t['id']: t for t in nme_6.get('transitions', [])}
    
    changes_made = []
    
    # Fix each transition in N-Me 7
    for transition in nme_7.get('transitions', []):
        trans_id = transition.get('id')
        trans_name = transition.get('name', '')
        
        # Find corresponding transition in N-Me 6
        if trans_id in nme_6_transitions:
            nme_6_trans = nme_6_transitions[trans_id]
            
            # Copy properties that contain rate_function
            if 'properties' in nme_6_trans:
                if 'properties' not in transition:
                    transition['properties'] = {}
                
                # Copy rate_function if it exists in N-Me 6
                if 'rate_function' in nme_6_trans['properties']:
                    old_value = transition['properties'].get('rate_function')
                    new_value = nme_6_trans['properties']['rate_function']
                    
                    if old_value != new_value:
                        transition['properties']['rate_function'] = new_value
                        print(f"✓ {trans_id} ({trans_name}):")
                        print(f"  Added rate_function")
                        changes_made.append(trans_id)
    
    # Save fixed model
    with open(nme_7_path, 'w') as f:
        json.dump(nme_7, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ FIXED {len(changes_made)} transitions:")
    for trans_id in changes_made:
        print(f"   • {trans_id}")
    print(f"\nSaved: {nme_7_path.name}")
    print("="*80)
    
    return len(changes_made) > 0

if __name__ == '__main__':
    success = fix_nme_7_transitions()
    
    if success:
        print("\n🎉 SUCCESS! N-Me 7 model fixed!")
        print("   You can now load and run simulations with this model.")
        exit(0)
    else:
        print("\n⚠️  No changes were needed or fix failed.")
        exit(1)
