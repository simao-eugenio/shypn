#!/usr/bin/env python3
"""
Set signal type designation in place properties for all 16 N-methylation models.

This sets the 'type' property in place.properties (used by shypn UI combo box) to:
- 'signal' for regulatory places (ATP, ADP, Pi, Membrane_potential, pH_gradient)
- 'material' for transported/metabolized species (Drug species, transporters, etc.)

Signal places are regulatory species that control pathway selection hierarchically,
distinct from material places that represent transported/metabolized species.

From manuscript: Signal Hierarchy Petri Nets distinguish signal places (P_S) 
encoding energy availability from material places (P_M) representing molecular species.
"""

import json
from pathlib import Path

MODEL_DIR = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NORMAL_TEMPLATE = "macrocycle_transport_normal_nme_{}_enhanced.shy"
TUMOR_TEMPLATE = "macrocycle_transport_tumor_nme_{}_enhanced.shy"

# Define which places are signals vs materials
SIGNAL_PLACES = {
    'ATP_pool': 'Energy signal controlling Layer 0/1 pathway activation',
    'ADP_pool': 'Energy depletion signal indicating metabolic stress',
    'Pi_pool': 'Phosphate availability signal for ATP synthesis',
    'Membrane_potential': 'Electrochemical signal controlling passive diffusion rate',
    'pH_gradient': 'Proton gradient signal for active transport coupling'
}

MATERIAL_PLACES = {
    'Drug_ext': 'Extracellular drug (material)',
    'Drug_intracellular': 'Intracellular drug pool (material)',
    'Drug_extended': 'Extended conformer (polar, material)',
    'Drug_compact': 'Compact conformer (lipophilic, material)',
    'PEPT1_free': 'Free transporter (material, membrane protein)',
    'Drug_degraded': 'Degraded drug fragments (material)',
    'H2O_activity': 'Water activity (material, solvent)'
}

def update_place_types(model_path, n_me, is_tumor=False):
    """Set type property in place properties to designate signal vs material places."""
    
    # Load model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    signals_marked = 0
    materials_marked = 0
    
    for place in model['places']:
        place_name = place['name']
        
        # Ensure properties dict exists
        if 'properties' not in place:
            place['properties'] = {}
        
        # Set type in properties (used by shypn UI combo box)
        if place_name in SIGNAL_PLACES:
            place['properties']['type'] = 'signal'
            place['properties']['description'] = SIGNAL_PLACES[place_name]
            signals_marked += 1
        elif place_name in MATERIAL_PLACES:
            place['properties']['type'] = 'material'
            place['properties']['description'] = MATERIAL_PLACES[place_name]
            materials_marked += 1
        else:
            print(f"    ⚠️  Unknown place: {place_name}")
    
    # Save updated model
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    return signals_marked, materials_marked

def main():
    """Update signal types in all 16 models."""
    
    print("="*80)
    print("SETTING SIGNAL TYPE IN PLACE PROPERTIES (UI COMBO BOX)")
    print("="*80)
    print("\nSignal places (regulatory, control pathway selection):")
    for name, desc in SIGNAL_PLACES.items():
        print(f"  • {name}: {desc}")
    print("\nMaterial places (transported/metabolized species):")
    for name, desc in MATERIAL_PLACES.items():
        print(f"  • {name}: {desc}")
    
    total_signals = 0
    total_materials = 0
    
    # Process normal series
    print("\n" + "="*80)
    print("NORMAL SERIES")
    print("="*80)
    
    for n_me in range(8):
        model_file = MODEL_DIR / NORMAL_TEMPLATE.format(n_me)
        if not model_file.exists():
            print(f"⚠️ {model_file} not found, skipping...")
            continue
        
        signals, materials = update_place_types(model_file, n_me, is_tumor=False)
        total_signals += signals
        total_materials += materials
        print(f"✓ N-Me {n_me}: {signals} signals, {materials} materials")
    
    # Process tumor series
    print("\n" + "="*80)
    print("TUMOR SERIES")
    print("="*80)
    
    for n_me in range(8):
        model_file = MODEL_DIR / TUMOR_TEMPLATE.format(n_me)
        if not model_file.exists():
            print(f"⚠️ {model_file} not found, skipping...")
            continue
        
        signals, materials = update_place_types(model_file, n_me, is_tumor=True)
        total_signals += signals
        total_materials += materials
        print(f"✓ N-Me {n_me}: {signals} signals, {materials} materials")
    
    # Summary
    print("\n" + "="*80)
    print("UPDATE SUMMARY")
    print("="*80)
    print(f"\nTotal signal places marked: {total_signals}")
    print(f"Total material places marked: {total_materials}")
    print(f"Expected: {len(SIGNAL_PLACES)} signals × 16 models = {len(SIGNAL_PLACES) * 16}")
    print(f"Expected: {len(MATERIAL_PLACES)} materials × 16 models = {len(MATERIAL_PLACES) * 16}")
    
    if total_signals == len(SIGNAL_PLACES) * 16 and total_materials == len(MATERIAL_PLACES) * 16:
        print("\n✅ ALL PLACE TYPES SUCCESSFULLY SET IN PROPERTIES!")
        print("\nSignal type designation (place.properties.type) now set for UI:")
        print("  ✓ Signal places: ATP, ADP, Pi, Membrane_potential, pH_gradient")
        print("  ✓ Material places: Drug species, transporters, degraded products")
        print("  ✓ Type designation visible in shypn UI combo box")
        print("  ✓ Signal Hierarchy Petri Net formalism complete")
        print("\n✅ All 16 models ready for Signal Hierarchy simulation")
    else:
        print(f"\n⚠️ WARNING: Expected {len(SIGNAL_PLACES) * 16} signals and {len(MATERIAL_PLACES) * 16} materials")
        print(f"   Got: {total_signals} signals, {total_materials} materials")

if __name__ == '__main__':
    main()
