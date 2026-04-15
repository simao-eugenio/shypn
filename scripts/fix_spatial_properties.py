#!/usr/bin/env python3
"""
Fix Script: Correct Spatial Properties in N-Methylation Models
============================================================

Applies correct spatial property configuration to all N-Me models (0-6).
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
        'diffusion_coefficient': 400.0,  # FIXED from 300.0
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

def fix_model(filepath, backup=True):
    """Fix spatial properties in a model file."""
    model_name = Path(filepath).name
    print(f"\n{'='*80}")
    print(f"🔧 Fixing: {model_name}")
    print(f"{'='*80}")
    
    # Backup original
    if backup:
        backup_path = str(filepath) + '.backup'
        shutil.copy2(filepath, backup_path)
        print(f"✅ Backup created: {backup_path}")
    
    # Load model
    with open(filepath, 'r') as f:
        model = json.load(f)
    
    if 'places' not in model:
        print(f"❌ ERROR: No 'places' in model")
        return False
    
    changes_made = []
    
    # Fix each place
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
    
    # Save fixed model
    with open(filepath, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n{'='*80}")
    if changes_made:
        print(f"✅ {model_name}: FIXED ({len(changes_made)} properties updated)")
        print(f"   Changes: {', '.join(changes_made)}")
    else:
        print(f"✓ {model_name}: No changes needed (already correct)")
    print(f"{'='*80}")
    
    return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == '__main__':
    print("="*80)
    print("SPATIAL PROPERTIES FIX")
    print("Correcting N-Methylation Models (0-6 Enhanced)")
    print("="*80)
    print("\nThis script will:")
    print("  1. Create backup of each model (.backup)")
    print("  2. Update spatial properties to correct values")
    print("  3. Save fixed models")
    print()
    
    base_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    
    models_to_fix = [
        'macrocycle_transport_normal_nme_0_enhanced.shy',
        'macrocycle_transport_normal_nme_1_enhanced.shy',
        'macrocycle_transport_normal_nme_2_enhanced.shy',
        'macrocycle_transport_normal_nme_3_enhanced.shy',
        'macrocycle_transport_normal_nme_4_enhanced.shy',
        'macrocycle_transport_normal_nme_5_enhanced.shy',
        'macrocycle_transport_normal_nme_6_enhanced.shy',
    ]
    
    results = []
    
    for model_file in models_to_fix:
        model_path = base_path / model_file
        
        if not model_path.exists():
            print(f"\n⚠️  WARNING: {model_file} NOT FOUND at {model_path}")
            results.append((model_file, False))
            continue
        
        success = fix_model(model_path, backup=True)
        results.append((model_file, success))
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n\n{'='*80}")
    print("📊 FIX SUMMARY")
    print(f"{'='*80}\n")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Models processed: {total}")
    print(f"Successfully fixed: {successful}")
    print(f"Failed: {total - successful}\n")
    
    for model_file, success in results:
        status = "✅ FIXED" if success else "❌ FAILED"
        print(f"   {status} - {model_file}")
    
    print(f"\n{'='*80}")
    
    if all(success for _, success in results):
        print("🎉 SUCCESS! All models have been corrected!")
        print("\nNext step: Re-run verify_spatial_properties.py to confirm")
        print("="*80)
        exit(0)
    else:
        print("⚠️  ATTENTION: Some models failed to fix!")
        print("="*80)
        exit(1)
