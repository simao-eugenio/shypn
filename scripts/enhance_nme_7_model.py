#!/usr/bin/env python3
"""
Enhance N-Methylation 7 Model with Spatial Properties
====================================================
Applies correct spatial property configuration to N-Me 7 model.
"""

import json
from pathlib import Path
import shutil

# Correct spatial properties for each place
CORRECT_PROPERTIES = {
    'P3': {  # Drug_extended
        'is_compartment_place': True,
        'boundary_type': 'impermeable',
        'compartment_volume': 0.8,
        'diffusion_coefficient': 150.0,
    },
    'P4': {  # Drug_compact
        'is_compartment_place': True,
        'boundary_type': 'impermeable',
        'compartment_volume': 0.5,
        'diffusion_coefficient': 80.0,
    },
    'P7': {  # ATP_pool
        'is_compartment_place': True,
        'boundary_type': 'impermeable',
        'compartment_volume': 5.0,
        'diffusion_coefficient': 300.0,
        'spatial_position': [0.0, 0.0, 0.0],
    },
    'P8': {  # ADP_pool
        'is_compartment_place': True,
        'boundary_type': 'impermeable',
        'compartment_volume': 5.0,
        'diffusion_coefficient': 400.0,
        'spatial_position': [0.0, 0.0, 0.0],
    },
    'P9': {  # Pi_pool
        'is_compartment_place': True,
        'boundary_type': 'impermeable',
        'compartment_volume': 5.0,
        'diffusion_coefficient': 600.0,
        'spatial_position': [0.0, 0.0, 0.0],
    },
    'P10': {  # H2O_activity
        'is_compartment_place': True,
        'boundary_type': 'permeable',
        'compartment_volume': 1000.0,
        'diffusion_coefficient': 2200.0,
    },
    'P11': {  # Membrane_potential
        'is_compartment_place': True,
        'boundary_type': 'selective',
        'compartment_volume': 0.1,
        'diffusion_coefficient': 0.0,
        'gradient_vector': [1.0, 0.0, 0.0],
        'spatial_position': [5.0, 0.0, 0.0],
    },
    'P12': {  # pH_gradient
        'is_compartment_place': True,
        'boundary_type': 'selective',
        'compartment_volume': 0.1,
        'diffusion_coefficient': 0.0,
        'gradient_vector': [1.0, 0.0, 0.0],
        'spatial_position': [5.0, 0.0, 0.0],
    },
}

def enhance_model(source_path, target_path, backup=True):
    """Enhance model with spatial properties."""
    model_name = Path(source_path).name
    print("="*80)
    print(f"ENHANCING: {model_name}")
    print("="*80)
    
    # Backup original if requested
    if backup:
        backup_path = str(source_path) + '.backup'
        if not Path(backup_path).exists():
            shutil.copy2(source_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
        else:
            print(f"ℹ️  Backup already exists: {backup_path}")
    
    # Load model
    with open(source_path, 'r') as f:
        model = json.load(f)
    
    if 'places' not in model:
        print(f"❌ ERROR: No 'places' in model")
        return False
    
    changes_made = []
    
    # Apply spatial properties to each place
    for place in model['places']:
        place_id = place.get('id')
        
        if place_id not in CORRECT_PROPERTIES:
            continue
        
        place_name = place.get('name', 'UNNAMED')
        print(f"\n📍 {place_id} ({place_name}):")
        
        correct_props = CORRECT_PROPERTIES[place_id]
        
        for prop_name, correct_value in correct_props.items():
            current_value = place.get(prop_name)
            
            if current_value != correct_value:
                print(f"   🔄 {prop_name}: {current_value} → {correct_value}")
                place[prop_name] = correct_value
                changes_made.append(f"{place_id}.{prop_name}")
            else:
                print(f"   ✓ {prop_name}: {correct_value} (already correct)")
    
    # Save enhanced model
    with open(target_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n{'='*80}")
    if changes_made:
        print(f"✅ {model_name}: ENHANCED ({len(changes_made)} properties updated)")
        print(f"   Changes: {', '.join(changes_made)}")
    else:
        print(f"✓ {model_name}: Already has correct properties")
    print(f"   Saved as: {Path(target_path).name}")
    print(f"{'='*80}")
    
    return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == '__main__':
    print("="*80)
    print("N-METHYLATION 7 MODEL ENHANCEMENT")
    print("Applying Spatial Properties Configuration")
    print("="*80)
    print("\nThis script will:")
    print("  1. Backup original N-Me 7 model")
    print("  2. Apply correct spatial properties (P3-P12)")
    print("  3. Create enhanced version")
    print()
    
    base_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    
    source_file = 'macrocycle_transport_normal_nme_7.shy'
    target_file = 'macrocycle_transport_normal_nme_7_enhanced.shy'
    
    source_path = base_path / source_file
    target_path = base_path / target_file
    
    if not source_path.exists():
        print(f"\n❌ ERROR: Source file not found!")
        print(f"   Expected: {source_path}")
        exit(1)
    
    success = enhance_model(source_path, target_path, backup=True)
    
    # ========================================================================
    # VERIFICATION
    # ========================================================================
    if success:
        print(f"\n\n{'='*80}")
        print("📊 ENHANCEMENT SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Source:    {source_file}")
        print(f"Enhanced:  {target_file}")
        print(f"Location:  {base_path}")
        
        if target_path.exists():
            size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"Size:      {size_mb:.2f} MB")
        
        print(f"\n{'='*80}")
        print("🎉 SUCCESS! N-Me 7 model enhanced with spatial properties!")
        print(f"{'='*80}")
        print("\nNext steps:")
        print("  1. Load the enhanced model in the application")
        print("  2. Run simulation to generate CSV data")
        print("  3. Analyze results with analyze_nme_7_simulation.py")
        print()
        exit(0)
    else:
        print(f"\n{'='*80}")
        print("⚠️  ENHANCEMENT FAILED")
        print(f"{'='*80}")
        exit(1)
