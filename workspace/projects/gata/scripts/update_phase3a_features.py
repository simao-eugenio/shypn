#!/usr/bin/env python3
"""
Update Phase 3A Model with Advanced shypn Features

Adds:
1. Spatial properties (EPO/GCSF gradients)
2. Compartment volumes (nucleus/cytoplasm)
3. Thermodynamic terms in rate functions (basic)

Date: 2026-02-17
"""

import json
import sys
from pathlib import Path

def update_phase3a_model():
    """Update phase3a_spatial.shy with all planned features"""
    
    model_path = Path("workspace/projects/gata/models/phase3a_spatial.shy")
    backup_path = model_path.with_suffix('.shy.backup_before_features')
    
    print("🔧 Updating Phase 3A Model with Advanced Features\n")
    
    # Load model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    # Create backup
    with open(backup_path, 'w') as f:
        json.dump(model, f, indent=2)
    print(f"✅ Backup created: {backup_path}\n")
    
    # ============================================================
    # PHASE 3A.1: SPATIAL PROPERTIES
    # ============================================================
    print("=" * 60)
    print("PHASE 3A.1: Adding Spatial Properties")
    print("=" * 60)
    
    spatial_updates = []
    
    for place in model['places']:
        place_name = place.get('name', '')
        
        # EPO_external - Spatial gradient along x-axis
        if 'EPO_external' in place_name or place.get('id') == 'P1':
            if 'properties' not in place:
                place['properties'] = {}
            place['properties']['spatial_properties'] = {
                'compartment': 'extracellular',
                'volume': 10.0,  # fL (large extracellular space)
                'diffusion_coefficient': 100.0,  # μm²/s (small protein)
                'boundary_type': 'PERMEABLE',
                'position': [50.0, 50.0, 0.0],  # Center of 100×100 µm field
                'gradient_vector': [1.0, 0.0, 0.0]  # 1 µM/µm along x-axis
            }
            spatial_updates.append(f"✅ {place_name}: EPO gradient (1 µM/µm along x)")
        
        # GCSF_external - Spatial gradient along y-axis (orthogonal)
        elif 'GCSF_external' in place_name or place.get('id') == 'P2':
            if 'properties' not in place:
                place['properties'] = {}
            place['properties']['spatial_properties'] = {
                'compartment': 'extracellular',
                'volume': 10.0,  # fL
                'diffusion_coefficient': 100.0,  # μm²/s
                'boundary_type': 'PERMEABLE',
                'position': [50.0, 50.0, 0.0],
                'gradient_vector': [0.0, 1.0, 0.0]  # 1 µM/µm along y-axis
            }
            spatial_updates.append(f"✅ {place_name}: GCSF gradient (1 µM/µm along y)")
    
    for update in spatial_updates:
        print(update)
    print()
    
    # ============================================================
    # PHASE 3A.2: COMPARTMENT VOLUMES
    # ============================================================
    print("=" * 60)
    print("PHASE 3A.2: Adding Compartment Volumes")
    print("=" * 60)
    
    nuclear_places = []
    cytoplasmic_places = []
    
    for place in model['places']:
        place_name = place.get('name', '')
        
        # Nuclear places (0.5 fL - 10% of cell volume)
        if any(keyword in place_name.lower() for keyword in ['gene', '_nuc', 'nucleus']):
            if 'properties' not in place:
                place['properties'] = {}
            place['properties']['compartment_volume'] = 0.5  # fL
            place['properties']['compartment_name'] = 'nucleus'
            nuclear_places.append(place_name)
        
        # Cytoplasmic places (4.5 fL - 90% of cell volume)
        elif any(keyword in place_name.lower() for keyword in ['_cyto', 'cytoplasm', 'atp', 'adp', 'gtp', 'gdp', 'pi']):
            if 'properties' not in place:
                place['properties'] = {}
            place['properties']['compartment_volume'] = 4.5  # fL
            place['properties']['compartment_name'] = 'cytoplasm'
            cytoplasmic_places.append(place_name)
        
        # Membrane receptors (1.0 fL - cell membrane surface)
        elif any(keyword in place_name.lower() for keyword in ['receptor', 'epor', 'gcsfr', '_r']):
            if 'properties' not in place:
                place['properties'] = {}
            place['properties']['compartment_volume'] = 1.0  # fL
            place['properties']['compartment_name'] = 'membrane'
    
    print(f"✅ Nuclear places (0.5 fL): {len(nuclear_places)}")
    for p in nuclear_places[:5]:  # Show first 5
        print(f"   - {p}")
    if len(nuclear_places) > 5:
        print(f"   ... and {len(nuclear_places) - 5} more")
    print()
    
    print(f"✅ Cytoplasmic places (4.5 fL): {len(cytoplasmic_places)}")
    for p in cytoplasmic_places[:5]:
        print(f"   - {p}")
    if len(cytoplasmic_places) > 5:
        print(f"   ... and {len(cytoplasmic_places) - 5} more")
    print()
    
    # ============================================================
    # PHASE 3A.3: THERMODYNAMIC TERMS (Basic)
    # ============================================================
    print("=" * 60)
    print("PHASE 3A.3: Adding Basic Thermodynamic Terms")
    print("=" * 60)
    
    thermo_updates = []
    
    for transition in model['transitions']:
        trans_name = transition.get('name', '')
        trans_id = transition.get('id', '')
        
        if 'properties' not in transition:
            transition['properties'] = {}
        
        rate_fn = transition['properties'].get('rate_function', '1.0')
        
        # Add thermodynamic correction to binding reactions
        if 'binding' in trans_name.lower() or 'bind' in trans_name.lower():
            # Simple thermodynamic correction: k * exp(-ΔG/RT)
            # Assume ΔG ~ -20 kJ/mol for stable binding (typical TF-DNA)
            # R = 8.314 J/(mol·K), T = 310 K → ΔG/RT ≈ -7.77
            # exp(-7.77) ≈ 0.00042 (strong binding)
            
            # For now, add a comment indicating where thermodynamic term should go
            if '# Thermodynamic' not in rate_fn:
                new_rate = f"{rate_fn}  # Thermodynamic: To add exp(-Delta_G / (R * T))"
                transition['properties']['rate_function'] = new_rate
                thermo_updates.append(f"✅ {trans_name}: Marked for thermodynamic correction")
        
        # Add temperature dependence to enzymatic reactions
        elif any(keyword in trans_name.lower() for keyword in ['transcription', 'translation', 'degradation']):
            # Arrhenius equation: k(T) = A * exp(-Ea/RT)
            # Typical Ea for protein synthesis ~ 50-70 kJ/mol
            if '# Temperature' not in rate_fn:
                new_rate = f"{rate_fn}  # Temperature: To add Arrhenius exp(-Ea / (R * T))"
                transition['properties']['rate_function'] = new_rate
                thermo_updates.append(f"✅ {trans_name}: Marked for temperature dependence")
    
    for update in thermo_updates[:5]:
        print(update)
    if len(thermo_updates) > 5:
        print(f"   ... and {len(thermo_updates) - 5} more")
    print()
    
    # ============================================================
    # VERIFY ADAPTIVE TRANSITIONS
    # ============================================================
    print("=" * 60)
    print("VERIFICATION: Adaptive Transitions")
    print("=" * 60)
    
    adaptive_count = 0
    for transition in model['transitions']:
        if transition.get('transition_type') == 'adaptive':
            adaptive_count += 1
            trans_name = transition.get('name', 'unnamed')
            threshold = transition['properties'].get('volume_threshold', 'N/A')
            filter_type = transition['properties'].get('adaptive_filter', 'N/A')
            print(f"✅ {trans_name}")
            print(f"   - Type: adaptive")
            print(f"   - Volume threshold: {threshold} fL")
            print(f"   - Filter: {filter_type}")
            print()
    
    print(f"Total adaptive transitions: {adaptive_count}")
    print()
    
    # ============================================================
    # SAVE UPDATED MODEL
    # ============================================================
    print("=" * 60)
    print("SAVING UPDATED MODEL")
    print("=" * 60)
    
    # Update metadata
    if 'metadata' not in model:
        model['metadata'] = {}
    
    if 'provenance' not in model['metadata']:
        model['metadata']['provenance'] = []
    
    model['metadata']['provenance'].append({
        'timestamp': '2026-02-17T00:00:00Z',
        'action': 'phase3a_feature_update',
        'description': 'Added spatial properties, compartment volumes, thermodynamic terms',
        'script': 'update_phase3a_features.py',
        'features_added': [
            'spatial_properties (EPO/GCSF gradients)',
            'compartment_volumes (nucleus 0.5 fL, cytoplasm 4.5 fL)',
            'thermodynamic_markers (ready for Phase 3B)',
            'adaptive_transitions (verified existing configuration)'
        ]
    })
    
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"✅ Model saved: {model_path}")
    print(f"✅ Backup available: {backup_path}")
    print()
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Places: {len(model['places'])}")
    print(f"Transitions: {len(model['transitions'])}")
    print(f"Spatial places: {len(spatial_updates)}")
    print(f"Nuclear compartments: {len(nuclear_places)}")
    print(f"Cytoplasmic compartments: {len(cytoplasmic_places)}")
    print(f"Adaptive transitions: {adaptive_count}")
    print(f"Thermodynamic markers: {len(thermo_updates)}")
    print()
    print("🎉 Phase 3A features successfully added!")
    print()
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Load model in shypn GUI to verify")
    print("2. Run test simulation (single replicate)")
    print("3. Verify adaptive mode switching in logs")
    print("4. Run spatial gradient experiment (500 replicates)")
    print("5. Proceed to Phase 3B (full thermodynamic implementation)")

if __name__ == '__main__':
    update_phase3a_model()
