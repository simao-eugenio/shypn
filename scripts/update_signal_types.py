#!/usr/bin/env python3
"""Update Signal Type Classification in All Models.

Sets signal_type property on signal places based on UI combo box options:
- energy: Ψₑ - Energy/Metabolic State (ATP, ADP, Pi, pH_gradient)
- spatial: Ψₛ - Spatial/Compartment Sensing (Membrane_potential)
- quorum: Ψq - Quorum/Cell Communication (not used in these models)
- regulatory: Ψᵣ - Regulatory/Gene Expression (not used in these models)

This enables proper hierarchical layer assignment in signal flow analysis.
"""

import json
import os
from pathlib import Path

# Signal type classification based on place_prop_dialog.ui combo box items
# UI combo box IDs: 'energy', 'regulatory', 'quorum', 'spatial'
SIGNAL_TYPE_CLASSIFICATION = {
    # ENERGY signals (Ψₑ - Layer 0) - Metabolic state indicators
    'ATP_pool': 'energy',        # Energy currency
    'ADP_pool': 'energy',        # Energy depletion
    'Pi_pool': 'energy',         # Phosphate availability
    'pH_gradient': 'energy',     # Proton-motive force (energy storage)
    
    # SPATIAL signals (Ψₛ - Layer 1) - Compartment and location markers
    'Membrane_potential': 'spatial',  # Electrochemical boundary property
}

def update_signal_types(model_path: Path) -> dict:
    """Update signal_type property for all signal places in model.
    
    Args:
        model_path: Path to .shy model file
        
    Returns:
        dict: Statistics about updates
    """
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    stats = {
        'energy_signals': 0,
        'spatial_signals': 0,
        'total_signals': 0,
    }
    
    # Update each place
    for place in model['places']:
        place_name = place['name']
        
        if place_name in SIGNAL_TYPE_CLASSIFICATION:
            signal_type = SIGNAL_TYPE_CLASSIFICATION[place_name]
            
            # Set signal_type at top level (required for Place.from_dict)
            place['signal_type'] = signal_type
            
            # Also set in properties dict for backward compatibility
            if 'properties' not in place:
                place['properties'] = {}
            place['properties']['signal_type'] = signal_type
            
            # Update statistics
            stats['total_signals'] += 1
            if signal_type == 'energy':
                stats['energy_signals'] += 1
            elif signal_type == 'spatial':
                stats['spatial_signals'] += 1
            
            print(f"  ✓ {place_name}: signal_type = '{signal_type}'")
    
    # Save updated model
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    return stats


def main():
    """Update all 16 N-methylation models with signal type classification."""
    print("="*80)
    print("UPDATING SIGNAL TYPE CLASSIFICATION")
    print("="*80)
    print("\nSignal Type Framework (from place_prop_dialog.ui combo box):")
    print("  • energy (Ψₑ - Layer 0): Energy/Metabolic State")
    print("    - ATP_pool, ADP_pool, Pi_pool: Energy currency and phosphate")
    print("    - pH_gradient: Proton-motive force (energy storage)")
    print("  • spatial (Ψₛ - Layer 1): Spatial/Compartment Sensing")
    print("    - Membrane_potential: Electrochemical boundary property")
    print("  • quorum (Ψq - Layer 2): Quorum/Cell Communication")
    print("  • regulatory (Ψᵣ - Layer 3): Regulatory/Gene Expression")
    print()
    
    # Path to models
    models_dir = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    
    total_stats = {
        'models_updated': 0,
        'total_energy': 0,
        'total_spatial': 0,
    }
    
    # Process normal series (N-Me 0-7)
    print("NORMAL SERIES (N-Me 0-7):")
    print("-" * 80)
    for n_me in range(8):
        model_file = f'macrocycle_transport_normal_nme_{n_me}_enhanced.shy'
        model_path = models_dir / model_file
        
        if not model_path.exists():
            print(f"✗ N-Me {n_me}: File not found: {model_file}")
            continue
        
        print(f"\nN-Me {n_me}: {model_file}")
        stats = update_signal_types(model_path)
        
        print(f"  Summary: {stats['energy_signals']} energy, {stats['spatial_signals']} spatial")
        
        total_stats['models_updated'] += 1
        total_stats['total_energy'] += stats['energy_signals']
        total_stats['total_spatial'] += stats['spatial_signals']
    
    # Process tumor series (N-Me 0-7)
    print("\n" + "="*80)
    print("TUMOR SERIES (N-Me 0-7):")
    print("-" * 80)
    for n_me in range(8):
        model_file = f'macrocycle_transport_tumor_nme_{n_me}_enhanced.shy'
        model_path = models_dir / model_file
        
        if not model_path.exists():
            print(f"✗ N-Me {n_me}: File not found: {model_file}")
            continue
        
        print(f"\nN-Me {n_me}: {model_file}")
        stats = update_signal_types(model_path)
        
        print(f"  Summary: {stats['energy_signals']} energy, {stats['spatial_signals']} spatial")
        
        total_stats['models_updated'] += 1
        total_stats['total_energy'] += stats['energy_signals']
        total_stats['total_spatial'] += stats['spatial_signals']
    
    # Final summary
    print("\n" + "="*80)
    print("UPDATE SUMMARY")
    print("="*80)
    print(f"Models updated: {total_stats['models_updated']}/16")
    print(f"Energy signals (Layer 0): {total_stats['total_energy']} (ATP, ADP, Pi, pH_gradient)")
    print(f"Spatial signals (Layer 1): {total_stats['total_spatial']} (Membrane_potential)")
    print(f"Total signal_type assignments: {total_stats['total_energy'] + total_stats['total_spatial']}")
    print()
    print("Expected: 4 energy + 1 spatial = 5 signals per model × 16 models = 80 total")
    print()
    
    if total_stats['models_updated'] == 16:
        print("✅ ALL MODELS UPDATED WITH SIGNAL TYPE CLASSIFICATION!")
        print("\nSignal hierarchy layers now defined:")
        print("  ✓ Layer 0 (Ψₑ - energy): ATP_pool, ADP_pool, Pi_pool, pH_gradient")
        print("  ✓ Layer 1 (Ψₛ - spatial): Membrane_potential")
        print("  ✓ Matches place_prop_dialog.ui combo box options")
        print("  ✓ Enables compositional state space exploration")
        print("  ✓ Compatible with SignalLayerDetector analysis")
    else:
        print(f"⚠ Only {total_stats['models_updated']}/16 models updated")


if __name__ == '__main__':
    main()
