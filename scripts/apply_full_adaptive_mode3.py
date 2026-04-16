#!/usr/bin/env python3
"""Apply full adaptive capability - Mode 3 (All Transitions).

Non-interactive version that directly applies Option 3.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
MODEL_PATH = Path("workspace/projects/gata/models/phase3a_spatial.shy")
BACKUP_SUFFIX = f".backup_before_full_adaptive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
VOLUME_THRESHOLD = 1.0  # fL
ADAPTIVE_FILTER = "inputs_only"

def main():
    print("=" * 80)
    print("APPLYING FULL ADAPTIVE CAPABILITY - MODE 3")
    print("=" * 80)
    print()
    print("Converting ALL transitions to adaptive mode")
    print(f"Model: {MODEL_PATH}")
    print(f"Threshold: {VOLUME_THRESHOLD} fL")
    print(f"Adaptive filter: {ADAPTIVE_FILTER}")
    print()
    
    # Create backup
    backup_path = MODEL_PATH.parent / (MODEL_PATH.name + BACKUP_SUFFIX)
    shutil.copy2(MODEL_PATH, backup_path)
    print(f"✅ Backup created: {backup_path.name}")
    print()
    
    # Load model
    with open(MODEL_PATH) as f:
        model = json.load(f)
    
    # Get compartment volumes
    compartment_volumes = {}
    for place in model['places']:
        comp_vol = place.get('compartment_volume')
        if comp_vol:
            comp = place.get('compartment', 'unknown')
            if comp not in compartment_volumes:
                compartment_volumes[comp] = comp_vol
    
    print("Expected behavior after conversion:")
    for comp, vol in sorted(compartment_volumes.items()):
        mode = "stochastic" if vol < VOLUME_THRESHOLD else "continuous"
        print(f"  {comp:20s}: {vol:6.1f} fL → {mode.upper()}")
    print()
    
    # Convert all transitions
    by_compartment = {}
    for trans in model['transitions']:
        comp = trans.get('compartment', 'unknown')
        if comp not in by_compartment:
            by_compartment[comp] = []
        by_compartment[comp].append(trans)
    
    total_converted = 0
    total_skipped = 0
    
    for comp in sorted(by_compartment.keys()):
        vol = compartment_volumes.get(comp, 'unknown')
        mode = "stochastic" if vol != 'unknown' and vol < VOLUME_THRESHOLD else "continuous"
        
        print(f"📍 {comp.upper()} ({vol} fL) → Will run {mode.upper()}:")
        
        converted = 0
        skipped = 0
        
        for trans in by_compartment[comp]:
            # Skip if already adaptive
            if trans.get('transition_type') == 'adaptive':
                skipped += 1
                print(f"   ⏭️  {trans['name']} (already adaptive)")
                continue
            
            # Convert to adaptive
            old_type = trans.get('transition_type', 'stochastic')
            trans['transition_type'] = 'adaptive'
            
            # Ensure properties dict exists
            if 'properties' not in trans:
                trans['properties'] = {}
            
            # Set adaptive parameters
            props = trans['properties']
            props['volume_threshold'] = VOLUME_THRESHOLD
            props['adaptive_filter'] = ADAPTIVE_FILTER
            
            # Ensure rate_function exists
            if 'rate_function' not in props:
                props['rate_function'] = "1"
            
            print(f"   ✅ {trans['name']} ({old_type} → adaptive)")
            converted += 1
        
        print(f"   Converted: {converted}, Skipped: {skipped}")
        total_converted += converted
        total_skipped += skipped
        print()
    
    print("=" * 80)
    print(f"✅ Total converted: {total_converted}")
    if total_skipped > 0:
        print(f"⏭️  Total skipped: {total_skipped} (already adaptive)")
    print()
    
    # Show final configuration
    print("FINAL MODEL CONFIGURATION")
    print("=" * 80)
    print()
    
    transition_types = {}
    for trans in model['transitions']:
        ttype = trans.get('transition_type', 'stochastic')
        transition_types[ttype] = transition_types.get(ttype, 0) + 1
    
    print("Transition types:")
    for ttype, count in sorted(transition_types.items()):
        print(f"  {ttype:15s}: {count:2d}")
    print()
    
    # Show adaptive transitions by compartment
    adaptive_by_comp = {}
    for trans in model['transitions']:
        if trans.get('transition_type') == 'adaptive':
            comp = trans.get('compartment', 'unknown')
            if comp not in adaptive_by_comp:
                adaptive_by_comp[comp] = []
            adaptive_by_comp[comp].append(trans['name'])
    
    print("Adaptive transitions by compartment:")
    for comp in sorted(adaptive_by_comp.keys()):
        vol = compartment_volumes.get(comp, 'unknown')
        mode = "stochastic" if vol != 'unknown' and vol < VOLUME_THRESHOLD else "continuous"
        count = len(adaptive_by_comp[comp])
        print(f"\n  {comp} ({vol} fL) → Will run {mode.upper()} [{count} transitions]")
    print()
    
    # Save model
    with open(MODEL_PATH, 'w') as f:
        json.dump(model, f, indent=2)
    
    print("=" * 80)
    print("✅ SUCCESS! Model saved.")
    print("=" * 80)
    print()
    print(f"Backup: {backup_path.name}")
    print(f"Changes: {total_converted} transitions converted to adaptive")
    print()
    print("Next steps:")
    print("  1. Load model in shypn to verify changes")
    print("  2. Run test simulation to confirm behavior")
    print("  3. Check simulation logs for mode switching messages")
    print()
    print("Expected behavior:")
    print("  • Nucleus transitions (0.5 fL < 1.0 fL) → Run STOCHASTIC")
    print("  • Cytoplasm transitions (4.5 fL > 1.0 fL) → Run CONTINUOUS")
    print("  • Extracellular transitions (10.0 fL > 1.0 fL) → Run CONTINUOUS")
    print()
    print("Benefits:")
    print("  ✅ Current behavior preserved")
    print("  ✅ Volume sweeps will automatically adjust simulation mode")
    print("  ✅ No manual transition type management needed")
    print()

if __name__ == '__main__':
    main()
