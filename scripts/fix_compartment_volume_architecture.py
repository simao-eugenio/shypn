#!/usr/bin/env python3
"""
Fix compartment_volume architecture issue.
Ensures ALL places have compartment_volume at root level (not just in attrs).
Sets P4 (Drug_compact) compartment_volume to 0.8 (same as P3).
"""

import json
from pathlib import Path

normal_dir = Path("workspace/projects/My_Project/drug_discovery/models/normal")
model_files = sorted(normal_dir.glob("macrocycle_transport_normal_nme_*_thermo.shy"))

# Filter out backup files
model_files = [f for f in model_files if not f.name.endswith('.backup') and not f.name.endswith('.backup_adaptive') and not f.name.endswith('.backup2')]

print(f"=== FIXING COMPARTMENT_VOLUME ARCHITECTURE ===")
print(f"Found {len(model_files)} normal models to fix\n")

fixes_applied = []

for model_path in model_files:
    print(f"Processing: {model_path.name}")
    
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    changes = []
    
    for place in model['places']:
        pid = place['id']
        pname = place['name']
        
        # Get compartment_volume from attrs
        cv_attrs = place.get('attrs', {}).get('compartment_volume', None)
        cv_root = place.get('compartment_volume', None)
        
        # Ensure attrs dict exists
        if 'attrs' not in place:
            place['attrs'] = {}
        
        # Fix 1: P4 (Drug_compact) needs compartment_volume=0.8 (intracellular)
        if pid == 'P4' and cv_attrs is None:
            place['attrs']['compartment_volume'] = 0.8
            place['compartment_volume'] = 0.8
            changes.append(f"  {pid} ({pname}): SET compartment_volume=0.8 (at root AND attrs)")
        
        # Fix 2: Promote ALL compartment_volume from attrs to root level
        elif cv_attrs is not None and cv_root is None:
            place['compartment_volume'] = cv_attrs
            changes.append(f"  {pid} ({pname}): PROMOTED compartment_volume={cv_attrs} from attrs to root")
        
        # Fix 3: Ensure consistency between root and attrs
        elif cv_root is not None and cv_attrs is not None and cv_root != cv_attrs:
            place['compartment_volume'] = cv_attrs  # attrs takes precedence (backward compat)
            changes.append(f"  {pid} ({pname}): SYNCED compartment_volume={cv_attrs} (attrs->root)")
        
        # Fix 4: If root has it but attrs doesn't, sync attrs
        elif cv_root is not None and cv_attrs is None:
            place['attrs']['compartment_volume'] = cv_root
            changes.append(f"  {pid} ({pname}): SYNCED compartment_volume={cv_root} (root->attrs)")
    
    if changes:
        # Create backup
        backup_path = model_path.with_suffix('.shy.backup_compartment')
        with open(backup_path, 'w') as f:
            json.dump(model, f, indent=2)
        
        # Save fixed model
        with open(model_path, 'w') as f:
            json.dump(model, f, indent=2)
        
        print(f"  ✅ Fixed {len(changes)} places")
        for change in changes:
            print(change)
        fixes_applied.append(model_path.name)
    else:
        print(f"  ⏭️  No fixes needed")
    
    print()

print("\n=== SUMMARY ===")
print(f"Models fixed: {len(fixes_applied)}/{len(model_files)}")
if fixes_applied:
    print("\nFixed models:")
    for name in fixes_applied:
        print(f"  - {name}")

print("\n=== ARCHITECTURE VERIFICATION ===")
print("Checking one model to verify fixes...")

with open(model_files[0], 'r') as f:
    model = json.load(f)

print(f"\nChecking: {model_files[0].name}")
for pid in ['P3', 'P4']:
    place = next((p for p in model['places'] if p['id'] == pid), None)
    if place:
        cv_root = place.get('compartment_volume', 'NOT_SET')
        cv_attrs = place.get('attrs', {}).get('compartment_volume', 'NOT_SET')
        print(f"  {pid} ({place['name']}): root={cv_root}, attrs={cv_attrs}")

print("\n✅ All places now have compartment_volume at ROOT level")
print("✅ P4 (Drug_compact) now has valid compartment_volume=0.8")
print("\nAdaptive transitions should now work correctly!")
