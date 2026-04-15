#!/usr/bin/env python3
"""
Fix compartment assignments in series*.shy files.

Assigns proper compartments to all transitions based on their biological function:
- Membrane transitions: Transport across membranes
- Cytoplasm transitions: Intracellular processes
"""

import json
import shutil
from pathlib import Path
from typing import Dict

# Compartment assignment rules based on biological function
TRANSITION_COMPARTMENTS = {
    # Membrane transport mechanisms
    'active_transport': 'membrane',
    'ABC_efflux': 'membrane',
    'facilitated_diffusion': 'membrane',
    'passive_diffusion': 'membrane',
    
    # Conformational dynamics (cytoplasmic)
    'chameleon_fold': 'cytoplasm',
    'chameleon_unfold': 'cytoplasm',
    
    # Degradation pathways (cytoplasmic)
    'proteasomal': 'cytoplasm',
    'lysosomal': 'cytoplasm',
    'chemical_hydrolysis': 'cytoplasm',
    
    # Energy metabolism (cytoplasmic)
    'basal_ATPase': 'cytoplasm',
    'ATP_synthesis_active': 'cytoplasm',
    
    # Membrane pumps
    'NaK_ATPase_pump': 'membrane',
    'ion_leak': 'membrane',
    
    # Protein turnover (cytoplasmic)
    'PEPT1_synthesis': 'cytoplasm',
    'PEPT1_degradation': 'cytoplasm',
}

# Place compartment assignments
PLACE_COMPARTMENTS = {
    'Drug_ext': 'extracellular',
    'Drug_intracellular': 'cytoplasm',
    'Drug_extended': 'cytoplasm',
    'Drug_compact': 'cytoplasm',
    'PEPT1_free': 'membrane',
    'Drug_degraded': 'cytoplasm',
    'ATP_pool': 'cytoplasm',
    'ADP_pool': 'cytoplasm',
    'Pi_pool': 'cytoplasm',
    'H2O_activity': 'cytoplasm',
    'Membrane_potential': 'membrane',
    'pH_gradient': 'membrane',
}


def fix_compartments(model_path: Path) -> Dict[str, int]:
    """Fix compartment assignments in a model file.
    
    Args:
        model_path: Path to .shy model file
    
    Returns:
        Dict with statistics
    """
    print(f"\n{'='*60}")
    print(f"Processing: {model_path.name}")
    print(f"{'='*60}")
    
    # Backup
    backup_path = model_path.with_suffix('.shy.backup_pre_compartments')
    if not backup_path.exists():
        shutil.copy2(model_path, backup_path)
        print(f"✓ Backup created: {backup_path.name}")
    
    # Load model
    with open(model_path) as f:
        model = json.load(f)
    
    # Fix transitions
    transitions_fixed = 0
    for transition in model.get('transitions', []):
        t_name = transition['name']
        
        if t_name in TRANSITION_COMPARTMENTS:
            compartment = TRANSITION_COMPARTMENTS[t_name]
            
            # Only update if not already set
            if transition.get('compartment') != compartment:
                transition['compartment'] = compartment
                transitions_fixed += 1
                print(f"  ✓ {t_name:<30} → {compartment}")
    
    # Fix places
    places_fixed = 0
    for place in model.get('places', []):
        p_name = place['name']
        
        if p_name in PLACE_COMPARTMENTS:
            compartment = PLACE_COMPARTMENTS[p_name]
            
            # Only update if not already set
            current = place.get('compartment')
            if current != compartment:
                place['compartment'] = compartment
                places_fixed += 1
                print(f"  ✓ {p_name:<30} → {compartment}")
    
    # Save updated model
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n✓ Model saved")
    
    return {
        'transitions_fixed': transitions_fixed,
        'places_fixed': places_fixed
    }


def main():
    """Main script."""
    print("="*80)
    print("FIX COMPARTMENT ASSIGNMENTS IN SERIES FILES")
    print("="*80)
    print("\nAssigning biological compartments:")
    print("  • membrane: Transport transitions, membrane pumps")
    print("  • cytoplasm: Metabolism, degradation, conformational changes")
    print("  • extracellular: External spaces")
    print()
    
    # Find series files
    models_dir = Path('workspace/projects/My_Project/drug_discovery/models/normal')
    
    if not models_dir.exists():
        print(f"\n❌ ERROR: Directory not found: {models_dir}")
        print("   Run this script from the shypn root directory")
        return 1
    
    series_files = sorted(models_dir.glob('series_*.shy'))
    
    if not series_files:
        print(f"\n❌ ERROR: No series_*.shy files found in {models_dir}")
        return 1
    
    print(f"✓ Found {len(series_files)} series files to update:")
    for f in series_files:
        print(f"  - {f.name}")
    
    # Process each file
    total_stats = {
        'files': 0,
        'transitions_fixed': 0,
        'places_fixed': 0
    }
    
    for model_path in series_files:
        try:
            stats = fix_compartments(model_path)
            total_stats['files'] += 1
            total_stats['transitions_fixed'] += stats['transitions_fixed']
            total_stats['places_fixed'] += stats['places_fixed']
        except Exception as e:
            print(f"\n❌ Error processing {model_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print("\n" + "="*80)
    print("UPDATE COMPLETE")
    print("="*80)
    print(f"\nStatistics:")
    print(f"  • Files processed: {total_stats['files']}/{len(series_files)}")
    print(f"  • Transitions fixed: {total_stats['transitions_fixed']}")
    print(f"  • Places fixed: {total_stats['places_fixed']}")
    
    print(f"\nCompartment assignments:")
    print(f"  ✓ Membrane: Active/passive transport, pumps, gradients")
    print(f"  ✓ Cytoplasm: Metabolism, degradation, folding")
    print(f"  ✓ Extracellular: Drug_ext space")
    
    print(f"\nBenefits:")
    print(f"  • Proper spatial organization for analysis")
    print(f"  • Compartment-aware visualization")
    print(f"  • Enables compartment volume scaling")
    print(f"  • Better biological accuracy")
    
    print("\n" + "="*80)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
