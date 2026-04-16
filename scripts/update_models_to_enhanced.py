#!/usr/bin/env python3
"""
Update macrocycle transport models (N_Me 1-6) to enhanced versions
with proper place name references, spatial properties, and rate functions.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

# Base paths
MODELS_DIR = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
REFERENCE_MODEL = MODELS_DIR / "macrocycle_transport_normal_nme_0_enhanced.shy"

# Models to update
MODELS_TO_UPDATE = [
    ("macrocycle_transport_normal_nme_1.shy", "macrocycle_transport_normal_nme_1_enhanced.shy", 1),
    ("macrocycle_transport_normal_nme_2.shy", "macrocycle_transport_normal_nme_2_enhanced.shy", 2),
    ("macrocycle_transport_normal_nme_3.shy", "macrocycle_transport_normal_nme_3_enhanced.shy", 3),
    ("macrocycle_transport_normal_nme_4.shy", "macrocycle_transport_normal_nme_4_enhanced.shy", 4),
    ("macrocycle_transport_normal_nme_5.shy", "macrocycle_transport_normal_nme_5_enhanced.shy", 5),
    ("macrocycle_transport_normal_nme_6.shy", "macrocycle_transport_normal_nme_6_enhanced.shy", 6),
]

# N-methylation dependent parameters (from manuscript Table)
NME_PARAMETERS = {
    0: {"layer0_factor": 1.000, "layer1_factor": 1.000, "layer2_factor": 0.000, "proteasomal": 0.010000, "lysosomal": 0.005000, "chemical": 0.001000},
    1: {"layer0_factor": 0.909, "layer1_factor": 0.909, "layer2_factor": 0.111, "proteasomal": 0.009182, "lysosomal": 0.004636, "chemical": 0.000955},
    2: {"layer0_factor": 0.818, "layer1_factor": 0.818, "layer2_factor": 0.229, "proteasomal": 0.008364, "lysosomal": 0.004273, "chemical": 0.000909},
    3: {"layer0_factor": 0.727, "layer1_factor": 0.727, "layer2_factor": 0.355, "proteasomal": 0.007545, "lysosomal": 0.003909, "chemical": 0.000864},
    4: {"layer0_factor": 0.636, "layer1_factor": 0.636, "layer2_factor": 0.490, "proteasomal": 0.006727, "lysosomal": 0.003545, "chemical": 0.000818},
    5: {"layer0_factor": 0.545, "layer1_factor": 0.545, "layer2_factor": 0.634, "proteasomal": 0.005909, "lysosomal": 0.003182, "chemical": 0.000773},
    6: {"layer0_factor": 0.455, "layer1_factor": 0.455, "layer2_factor": 0.788, "proteasomal": 0.005091, "lysosomal": 0.002818, "chemical": 0.000727},
    7: {"layer0_factor": 0.364, "layer1_factor": 0.364, "layer2_factor": 0.952, "proteasomal": 0.004273, "lysosomal": 0.002455, "chemical": 0.000682},
}

# Spatial/physical properties to add (from enhanced model)
PLACE_ENHANCEMENTS = {
    "Drug_ext": {
        "metadata": {
            "description": "Extracellular drug - large volume favors continuous dynamics",
            "volume_note": "1000 fL >> 1.0 fL threshold → continuous mode for adaptive transitions",
            "boundary_note": "SELECTIVE allows transport only through validated transitions"
        },
        "diffusion_coefficient": 50.0,
        "boundary_type": None,
        "gradient_vector": None,
        "compartment_volume": 1000.0,
        "neighbor_compartments": ["cytoplasm"],
        "spatial_position": [10.0, 0.0, 0.0]
    },
    "Drug_intracellular": {
        "metadata": {
            "description": "Intracellular drug - intermediate volume",
            "volume_note": "5 fL > 1.0 fL → continuous mode but approaching stochastic threshold",
            "diffusion_note": "Slower diffusion than extracellular (crowded cytoplasm)"
        },
        "diffusion_coefficient": 20.0,
        "boundary_type": None,
        "gradient_vector": None,
        "compartment_volume": 5.0,
        "neighbor_compartments": ["extracellular"],
        "spatial_position": [0.0, 0.0, 0.0]
    },
    "Drug_extended": {
        "metadata": {
            "description": "Extended (polar) conformation - low volume for stochastic switching",
            "volume_note": "0.1 fL < 1.0 fL threshold → stochastic mode for chameleon transitions",
            "conformational_note": "High polarity, reduced membrane permeability"
        },
        "diffusion_coefficient": 15.0,
        "compartment_volume": 0.1,
        "spatial_position": [-5.0, -5.0, 0.0]
    },
    "Drug_compact": {
        "metadata": {
            "description": "Compact (lipophilic) conformation - low volume for stochastic switching",
            "volume_note": "0.1 fL < 1.0 fL threshold → stochastic mode",
            "conformational_note": "Masked polarity, enhanced membrane permeability"
        },
        "diffusion_coefficient": 15.0,
        "compartment_volume": 0.1,
        "spatial_position": [5.0, -5.0, 0.0]
    },
    "PEPT1_free": {
        "metadata": {
            "description": "Free PEPT1 transporter - intermediate volume",
            "stoichiometry_note": "Maintains constant pool via catalytic cycle"
        },
        "diffusion_coefficient": 5.0,
        "compartment_volume": 2.0,
        "spatial_position": [-10.0, 0.0, 0.0]
    },
    "Drug_degraded": {
        "metadata": {
            "description": "Degraded drug products - sink",
            "pathway_note": "Sum of proteasomal + lysosomal + chemical degradation"
        },
        "diffusion_coefficient": 30.0,
        "compartment_volume": 10.0,
        "spatial_position": [0.0, 10.0, 0.0]
    },
    "ATP_pool": {
        "metadata": {
            "description": "ATP pool - energy currency and regulatory signal",
            "dual_role": "Consumed in reactions (metabolite) AND controls pathway activation (signal)",
            "cooperativity": "ATP^2 for Layer 0, ATP^4 for proteasomal degradation"
        },
        "diffusion_coefficient": 100.0,
        "compartment_volume": 5.0,
        "spatial_position": [15.0, -10.0, 0.0]
    },
    "ADP_pool": {
        "metadata": {
            "description": "ADP pool - energy depletion marker",
            "regeneration": "Converted back to ATP via synthesis (mitochondrial/glycolytic)"
        },
        "diffusion_coefficient": 100.0,
        "compartment_volume": 5.0,
        "spatial_position": [15.0, 10.0, 0.0]
    },
    "Pi_pool": {
        "metadata": {
            "description": "Inorganic phosphate pool",
            "note": "Product of ATP hydrolysis, substrate for synthesis"
        },
        "diffusion_coefficient": 150.0,
        "compartment_volume": 5.0,
        "spatial_position": [20.0, 0.0, 0.0]
    },
    "H2O_activity": {
        "metadata": {
            "description": "Water activity - constant signal place",
            "note": "Maintains fixed value, used in gradient calculations"
        },
        "diffusion_coefficient": 200.0,
        "compartment_volume": 1000.0,
        "spatial_position": [25.0, -5.0, 0.0]
    },
    "Membrane_potential": {
        "metadata": {
            "description": "Membrane potential signal (-70 mV normal)",
            "effect": "Exponentially suppresses passive diffusion via exp(-Vm/25.7)",
            "biological_note": "Resting potential in healthy cells, depolarized in tumors (-20 mV)"
        },
        "diffusion_coefficient": 0.0,
        "compartment_volume": 1.0,
        "spatial_position": [25.0, 5.0, 0.0]
    },
    "pH_gradient": {
        "metadata": {
            "description": "pH gradient signal (extracellular - intracellular)",
            "effect": "Modulates ATP synthesis rate",
            "typical_value": "0.5-1.0 pH units"
        },
        "diffusion_coefficient": 0.0,
        "compartment_volume": 1.0,
        "spatial_position": [30.0, 0.0, 0.0]
    }
}

# Rate function templates (with proper ATP_pool/ADP_pool references)
RATE_FUNCTION_TEMPLATES = {
    "active_transport": "((15.0 * [Drug_ext] * [PEPT1_free] * ([ATP_pool]**2 / (2000**2 + [ATP_pool]**2))) * exp(0.15 * gaussian_noise())) * {layer0_factor:.3f}",
    "ABC_efflux": "0.1 * [Drug_intracellular] * ([ATP_pool]**2 / (2000**2 + [ATP_pool]**2))",
    "facilitated_diffusion": "(3.0 * [Drug_ext] * [PEPT1_free] * ([ATP_pool] / (1000 + [ATP_pool]))) * exp(0.15 * gaussian_noise())",
    "passive_diffusion": "(20.0 * [Drug_ext] * ([Drug_compact] / ([Drug_extended] + [Drug_compact]))) * exp(0.15 * gaussian_noise()) * {layer2_factor:.3f}",
    "chameleon_fold": "50.0 * [Drug_extended] * ([ATP_pool] / (1000 + [ATP_pool]))",
    "chameleon_unfold": "10.0 * [Drug_compact] * (1 - [ATP_pool] / (2000 + [ATP_pool]))",
    "proteasomal": "{proteasomal:.6f} * [Drug_intracellular] * ([ATP_pool]**4 / (3000**4 + [ATP_pool]**4))",
    "lysosomal": "{lysosomal:.6f} * [Drug_intracellular] * ([ATP_pool] / (1000 + [ATP_pool]))",
    "chemical_hydrolysis": "{chemical:.6f} * [Drug_intracellular]",
    "ATP_synthesis": "0.5 * [ADP_pool]",
    "basal_ATPase": "0.002 * [ATP_pool]"
}


def update_place_properties(place, place_name):
    """Add spatial and physical properties to a place."""
    if place_name in PLACE_ENHANCEMENTS:
        enhancements = PLACE_ENHANCEMENTS[place_name]
        
        # Update metadata
        if "metadata" not in place:
            place["metadata"] = {}
        place["metadata"].update(enhancements.get("metadata", {}))
        
        # Add spatial/physical properties
        for key in ["diffusion_coefficient", "boundary_type", "gradient_vector", 
                    "compartment_volume", "neighbor_compartments", "spatial_position"]:
            if key in enhancements:
                place[key] = enhancements[key]
    
    return place


def update_transition_rate(transition, nme_level):
    """Update transition rate function with proper ATP/ADP references and N-methylation factors."""
    trans_name = transition.get("name", "")
    params = NME_PARAMETERS[nme_level]
    
    # Get the appropriate rate function template
    rate_template = None
    for key in RATE_FUNCTION_TEMPLATES:
        if key in trans_name:
            rate_template = RATE_FUNCTION_TEMPLATES[key]
            break
    
    if rate_template:
        # Format with N-methylation parameters
        new_rate = rate_template.format(**params)
        
        # Update both 'rate' and 'rate_function' fields
        if "rate" in transition:
            transition["rate"] = new_rate
        if "properties" in transition and "rate_function" in transition["properties"]:
            transition["properties"]["rate_function"] = new_rate
        
        # Some models store rate_function at top level
        if "rate_function" in transition:
            transition["rate_function"] = new_rate
        if "rate_function_display" in transition:
            transition["rate_function_display"] = new_rate
    
    return transition


def update_model(source_path, target_path, nme_level):
    """Update a model file to enhanced version."""
    print(f"\n{'='*80}")
    print(f"Updating: {source_path.name} → {target_path.name}")
    print(f"N-methylation level: {nme_level}")
    print(f"{'='*80}")
    
    # Load source model
    with open(source_path, 'r') as f:
        model = json.load(f)
    
    # Update metadata
    model["metadata"]["created"] = datetime.now().isoformat()
    if "object_counts" in model["metadata"]:
        print(f"  Places: {model['metadata']['object_counts']['places']}")
        print(f"  Transitions: {model['metadata']['object_counts']['transitions']}")
    
    # Update places with spatial/physical properties
    print(f"\n  Updating places with spatial properties...")
    for place in model.get("places", []):
        place_name = place.get("name", "")
        update_place_properties(place, place_name)
        print(f"    ✓ {place_name}")
    
    # Update transitions with correct rate functions
    print(f"\n  Updating transitions with enhanced rate functions...")
    params = NME_PARAMETERS[nme_level]
    print(f"    Layer 0 factor: {params['layer0_factor']:.3f}")
    print(f"    Layer 1 factor: {params['layer1_factor']:.3f}")
    print(f"    Layer 2 factor: {params['layer2_factor']:.3f}")
    
    for transition in model.get("transitions", []):
        trans_name = transition.get("name", "")
        update_transition_rate(transition, nme_level)
        print(f"    ✓ {trans_name}")
    
    # Save enhanced model
    with open(target_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n  ✅ Saved: {target_path}")
    print(f"  File size: {target_path.stat().st_size / 1024:.1f} KB")
    
    return True


def main():
    """Main update process."""
    print("="*80)
    print("MODEL ENHANCEMENT PROCESS")
    print("="*80)
    print(f"\nReference model: {REFERENCE_MODEL.name}")
    print(f"Models to update: {len(MODELS_TO_UPDATE)}")
    print(f"Target directory: {MODELS_DIR}")
    
    # Verify reference model exists
    if not REFERENCE_MODEL.exists():
        print(f"\n❌ ERROR: Reference model not found: {REFERENCE_MODEL}")
        return False
    
    print(f"\n✓ Reference model found")
    
    # Update each model
    updated_count = 0
    for source_name, target_name, nme_level in MODELS_TO_UPDATE:
        source_path = MODELS_DIR / source_name
        target_path = MODELS_DIR / target_name
        
        if not source_path.exists():
            print(f"\n⚠️  WARNING: Source not found: {source_name}, skipping...")
            continue
        
        try:
            if update_model(source_path, target_path, nme_level):
                updated_count += 1
        except Exception as e:
            print(f"\n❌ ERROR updating {source_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"  Successfully updated: {updated_count}/{len(MODELS_TO_UPDATE)} models")
    print(f"  Enhanced models saved to: {MODELS_DIR}")
    print(f"\n  ✅ Models ready for simulation with:")
    print(f"     • Proper ATP_pool/ADP_pool references (no 'P' prefix issues)")
    print(f"     • N-methylation layer factors")
    print(f"     • Spatial/physical properties")
    print(f"     • Enhanced metadata descriptions")
    print(f"\n{'='*80}")
    
    return updated_count == len(MODELS_TO_UPDATE)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
