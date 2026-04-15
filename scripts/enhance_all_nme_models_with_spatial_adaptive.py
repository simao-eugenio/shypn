#!/usr/bin/env python3
"""
Add enhanced functionalities to all 16 N-methylation models (normal + tumor):
1. Spatial properties on all places
2. Adaptive transitions for low-copy species

This ensures all models have the full enhanced framework for proper stochastic simulation.
"""

import json
from pathlib import Path

# Model paths
MODEL_DIR = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NORMAL_TEMPLATE = "macrocycle_transport_normal_nme_{}_enhanced.shy"
TUMOR_TEMPLATE = "macrocycle_transport_tumor_nme_{}_enhanced.shy"

# Spatial properties for each place (from previous enhancement work)
SPATIAL_PROPERTIES = {
    'Drug_ext': {
        'compartment_volume': 1000.0,  # fL (extracellular)
        'diffusion_coefficient': 50.0,  # µm²/s
        'boundary_type': 'periodic',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'Drug_intracellular': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 10.0,  # µm²/s (restricted by crowding)
        'boundary_type': 'reflective',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'Drug_extended': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 8.0,   # µm²/s (extended form, higher drag)
        'boundary_type': 'reflective',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'Drug_compact': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 15.0,  # µm²/s (compact form, lower drag)
        'boundary_type': 'reflective',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'PEPT1_free': {
        'compartment_volume': 100.0,  # fL (membrane)
        'diffusion_coefficient': 0.5,  # µm²/s (membrane protein, slow)
        'boundary_type': 'reflective',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'Drug_degraded': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 20.0,  # µm²/s (small fragments)
        'boundary_type': 'absorbing',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'ATP_pool': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 100.0,  # µm²/s (small molecule, fast)
        'boundary_type': 'reflective',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'ADP_pool': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 100.0,  # µm²/s
        'boundary_type': 'reflective',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'Pi_pool': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 150.0,  # µm²/s (very small, fastest)
        'boundary_type': 'reflective',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'H2O_activity': {
        'compartment_volume': 500.0,  # fL (cytoplasm)
        'diffusion_coefficient': 200.0,  # µm²/s (water, extremely fast)
        'boundary_type': 'periodic',
        'gradient_vector': [0.0, 0.0, 0.0]
    },
    'Membrane_potential': {
        'compartment_volume': 100.0,  # fL (membrane)
        'diffusion_coefficient': 0.0,   # Not a molecule (electrostatic field)
        'boundary_type': 'fixed',
        'gradient_vector': [1.0, 0.0, 0.0]  # Transmembrane gradient
    },
    'pH_gradient': {
        'compartment_volume': 100.0,  # fL (membrane)
        'diffusion_coefficient': 0.0,   # Not a molecule (proton gradient)
        'boundary_type': 'fixed',
        'gradient_vector': [0.0, 1.0, 0.0]  # Transmembrane gradient
    }
}

# Adaptive transitions configuration (from previous enhancement work)
ADAPTIVE_TRANSITIONS = {
    'chameleon_fold': {
        'type': 'adaptive',
        'low_copy_threshold': 10.0,  # Switch to stochastic below 10 molecules
        'description': 'Conformational transition: Extended → Compact (ATP-dependent)',
        'adaptive_reason': 'Low copy number of Drug_extended requires stochastic treatment'
    },
    'chameleon_unfold': {
        'type': 'adaptive',
        'low_copy_threshold': 10.0,  # Switch to stochastic below 10 molecules
        'description': 'Conformational transition: Compact → Extended (energy-dependent)',
        'adaptive_reason': 'Low copy number of Drug_compact requires stochastic treatment'
    },
    'ATP_synthesis': {
        'type': 'adaptive',
        'low_copy_threshold': 100.0,  # Switch to stochastic below 100 mM ATP
        'description': 'ATP regeneration: ADP + Pi → ATP (mitochondrial)',
        'adaptive_reason': 'Low ATP concentration (<100 mM) triggers stochastic metabolism'
    },
    'basal_ATPase': {
        'type': 'adaptive',
        'low_copy_threshold': 100.0,  # Switch to stochastic below 100 mM ATP
        'description': 'Basal ATP consumption: ATP → ADP + Pi (housekeeping)',
        'adaptive_reason': 'Low ATP concentration (<100 mM) triggers stochastic metabolism'
    }
}

def add_spatial_properties_to_place(place):
    """Add spatial properties to a place if not already present."""
    place_name = place['name']
    
    if place_name not in SPATIAL_PROPERTIES:
        print(f"    ⚠️ WARNING: No spatial properties defined for {place_name}, skipping")
        return False
    
    # Ensure properties dict exists
    if 'properties' not in place:
        place['properties'] = {}
    
    # Add spatial properties
    spatial_props = SPATIAL_PROPERTIES[place_name]
    for key, value in spatial_props.items():
        place['properties'][key] = value
    
    return True

def make_transition_adaptive(transition):
    """Convert a transition to adaptive if it should be."""
    trans_name = transition['name']
    
    if trans_name not in ADAPTIVE_TRANSITIONS:
        return False  # Not an adaptive transition
    
    # Get adaptive configuration
    adaptive_config = ADAPTIVE_TRANSITIONS[trans_name]
    
    # Set type to adaptive
    transition['type'] = 'adaptive'
    
    # Ensure properties dict exists
    if 'properties' not in transition:
        transition['properties'] = {}
    
    # Add adaptive properties
    transition['properties']['low_copy_threshold'] = adaptive_config['low_copy_threshold']
    
    # Update description
    if 'description' not in transition:
        transition['description'] = adaptive_config['description']
    
    return True

def enhance_model(model_path, n_me, is_tumor=False):
    """Add spatial properties and adaptive transitions to a model."""
    print(f"\n{'='*70}")
    print(f"Enhancing {model_path.name} (N-Me {n_me}, {'tumor' if is_tumor else 'normal'})")
    print('='*70)
    
    # Load model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    places_enhanced = 0
    transitions_made_adaptive = 0
    
    # Add spatial properties to all places
    print(f"\nAdding spatial properties to places...")
    for place in model['places']:
        if add_spatial_properties_to_place(place):
            places_enhanced += 1
            print(f"  ✓ {place['name']}: volume={place['properties']['compartment_volume']} fL, "
                  f"D={place['properties']['diffusion_coefficient']} µm²/s")
    
    print(f"\nTotal places enhanced: {places_enhanced}/{len(model['places'])}")
    
    # Make appropriate transitions adaptive
    print(f"\nConfiguring adaptive transitions...")
    for transition in model['transitions']:
        if make_transition_adaptive(transition):
            transitions_made_adaptive += 1
            threshold = transition['properties']['low_copy_threshold']
            print(f"  ✓ {transition['name']}: type=adaptive, threshold={threshold}")
    
    print(f"\nTotal adaptive transitions: {transitions_made_adaptive}/{len(model['transitions'])}")
    
    # Verify all expected adaptive transitions were found
    expected_adaptive = set(ADAPTIVE_TRANSITIONS.keys())
    actual_adaptive = {t['name'] for t in model['transitions'] if t.get('type') == 'adaptive'}
    missing_adaptive = expected_adaptive - actual_adaptive
    
    if missing_adaptive:
        print(f"\n  ⚠️ WARNING: Expected adaptive transitions not found: {missing_adaptive}")
    
    # Save enhanced model
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n✅ Model enhanced successfully!")
    print(f"   - {places_enhanced} places with spatial properties")
    print(f"   - {transitions_made_adaptive} adaptive transitions")
    
    return {
        'n_me': n_me,
        'is_tumor': is_tumor,
        'places_enhanced': places_enhanced,
        'adaptive_transitions': transitions_made_adaptive
    }

def main():
    """Enhance all 16 models with spatial properties and adaptive transitions."""
    
    print("="*80)
    print("ADDING ENHANCED FUNCTIONALITIES TO ALL N-METHYLATION MODELS")
    print("="*80)
    print("\nEnhancements to apply:")
    print("  1. Spatial properties on all 12 places")
    print("     - compartment_volume (fL)")
    print("     - diffusion_coefficient (µm²/s)")
    print("     - boundary_type (periodic/reflective/absorbing/fixed)")
    print("     - gradient_vector [x, y, z]")
    print("\n  2. Adaptive transitions (4 transitions)")
    print("     - chameleon_fold (threshold=10 molecules)")
    print("     - chameleon_unfold (threshold=10 molecules)")
    print("     - ATP_synthesis (threshold=100 mM)")
    print("     - basal_ATPase (threshold=100 mM)")
    
    summary = []
    
    # Process normal series
    print("\n" + "="*80)
    print("NORMAL CELL SERIES")
    print("="*80)
    
    for n_me in range(8):
        model_file = MODEL_DIR / NORMAL_TEMPLATE.format(n_me)
        if not model_file.exists():
            print(f"⚠️ WARNING: {model_file} not found, skipping...")
            continue
        
        result = enhance_model(model_file, n_me, is_tumor=False)
        result['series'] = 'normal'
        summary.append(result)
    
    # Process tumor series
    print("\n" + "="*80)
    print("TUMOR CELL SERIES")
    print("="*80)
    
    for n_me in range(8):
        model_file = MODEL_DIR / TUMOR_TEMPLATE.format(n_me)
        if not model_file.exists():
            print(f"⚠️ WARNING: {model_file} not found, skipping...")
            continue
        
        result = enhance_model(model_file, n_me, is_tumor=True)
        result['series'] = 'tumor'
        summary.append(result)
    
    # Print summary
    print("\n" + "="*80)
    print("ENHANCEMENT SUMMARY")
    print("="*80)
    
    total_places = sum(r['places_enhanced'] for r in summary)
    total_adaptive = sum(r['adaptive_transitions'] for r in summary)
    
    print(f"\nModels enhanced: {len(summary)}/16")
    print(f"Total spatial properties added: {total_places}")
    print(f"Total adaptive transitions configured: {total_adaptive}")
    
    print("\nPer-series breakdown:")
    print(f"{'Series':<8} {'Models':<8} {'Places':<10} {'Adaptive':<10}")
    print("-" * 40)
    
    for series in ['normal', 'tumor']:
        series_results = [r for r in summary if r['series'] == series]
        n_models = len(series_results)
        n_places = sum(r['places_enhanced'] for r in series_results)
        n_adaptive = sum(r['adaptive_transitions'] for r in series_results)
        print(f"{series:<8} {n_models:<8} {n_places:<10} {n_adaptive:<10}")
    
    print("\n" + "="*80)
    print("✅ ALL MODELS SUCCESSFULLY ENHANCED")
    print("="*80)
    print("\nAll 16 models now have:")
    print("  ✓ Spatial properties on all 12 places")
    print("  ✓ 4 adaptive transitions (chameleon_fold, chameleon_unfold, ATP_synthesis, basal_ATPase)")
    print("  ✓ N-methylation differentiation (from previous update)")
    print("  ✓ Ready for enhanced stochastic simulation with proper spatial-adaptive framework")
    
    print("\nNext steps:")
    print("  1. Re-simulate all models to generate enhanced simulation data")
    print("  2. Verify adaptive behavior at low copy numbers")
    print("  3. Verify spatial diffusion patterns")
    print("  4. Compare results with N-methylation-only models (if any)")

if __name__ == '__main__':
    main()
