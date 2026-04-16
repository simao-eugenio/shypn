#!/usr/bin/env python3
"""
Enhance tumor N-methylation series models (0-7) with spatial properties.
Applies the same spatial configuration as normal cell models for direct comparison.
"""

import json
from pathlib import Path

def enhance_tumor_model(input_file: Path, output_file: Path, variant_num: int) -> tuple[bool, str]:
    """
    Enhance a single tumor model with spatial properties.
    
    Args:
        input_file: Path to original model
        output_file: Path to save enhanced model
        variant_num: N-methylation level (0-7)
    
    Returns:
        (success: bool, message: str)
    """
    try:
        with open(input_file, 'r') as f:
            model = json.load(f)
        
        # Spatial properties configuration (same as normal cells)
        spatial_config = {
            'P3': {  # Drug_extended
                'compartment_volume': 0.8,
                'diffusion_coefficient': 150.0,
                'boundary_type': 'impermeable',
                'gradient_vector': None
            },
            'P4': {  # Drug_compact
                'compartment_volume': 0.5,
                'diffusion_coefficient': 80.0,
                'boundary_type': 'impermeable',
                'gradient_vector': None
            },
            'P7': {  # ATP
                'compartment_volume': 5.0,
                'diffusion_coefficient': 300.0,
                'boundary_type': 'impermeable',
                'gradient_vector': None
            },
            'P8': {  # ADP
                'compartment_volume': 5.0,
                'diffusion_coefficient': 400.0,
                'boundary_type': 'impermeable',
                'gradient_vector': None
            },
            'P9': {  # Pi
                'compartment_volume': 5.0,
                'diffusion_coefficient': 600.0,
                'boundary_type': 'impermeable',
                'gradient_vector': None
            },
            'P10': {  # H2O
                'compartment_volume': 1000.0,
                'diffusion_coefficient': 2200.0,
                'boundary_type': 'permeable',
                'gradient_vector': None
            },
            'P11': {  # Intracellular_gradient (out_gradient)
                'compartment_volume': 0.1,
                'diffusion_coefficient': 0.0,
                'boundary_type': 'selective',
                'gradient_vector': [1.0, 0.0, 0.0]
            },
            'P12': {  # Extracellular_gradient (in_gradient)
                'compartment_volume': 0.1,
                'diffusion_coefficient': 0.0,
                'boundary_type': 'selective',
                'gradient_vector': [1.0, 0.0, 0.0]
            }
        }
        
        # Apply spatial properties to places
        updates_count = 0
        for place in model.get('places', []):
            place_id = place.get('id')
            if place_id in spatial_config:
                config = spatial_config[place_id]
                place['compartment_volume'] = config['compartment_volume']
                place['diffusion_coefficient'] = config['diffusion_coefficient']
                place['boundary_type'] = config['boundary_type']
                place['gradient_vector'] = config['gradient_vector']
                updates_count += 1
        
        # Ensure all continuous transitions have rate_function property
        # Copy from N-Me 6 enhanced model if missing
        n_me_6_enhanced_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_nme_6_enhanced.shy')
        if n_me_6_enhanced_path.exists():
            with open(n_me_6_enhanced_path, 'r') as f:
                reference_model = json.load(f)
            
            # Create mapping of transition names to rate functions
            rate_function_map = {}
            for trans in reference_model.get('transitions', []):
                if trans.get('type') == 'continuous' and 'rate_function' in trans:
                    rate_function_map[trans['name']] = trans['rate_function']
            
            # Apply rate functions to tumor model transitions
            for trans in model.get('transitions', []):
                if trans.get('type') == 'continuous':
                    trans_name = trans['name']
                    if 'rate_function' not in trans and trans_name in rate_function_map:
                        trans['rate_function'] = rate_function_map[trans_name]
                        updates_count += 1
        
        # Save enhanced model
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(model, f, indent=2)
        
        return True, f"Enhanced N-Me {variant_num} tumor model: {updates_count} properties updated"
    
    except Exception as e:
        return False, f"Failed to enhance N-Me {variant_num} tumor model: {str(e)}"


def main():
    """Enhance all tumor models in the series."""
    base_dir = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    
    print("=" * 70)
    print("TUMOR N-METHYLATION SERIES ENHANCEMENT")
    print("=" * 70)
    print("\nApplying spatial properties to tumor models (N-Me 0-7)...")
    print("Configuration: Same as normal cell models for direct comparison\n")
    
    results = []
    for i in range(8):
        input_file = base_dir / f'macrocycle_transport_tumor_nme_{i}.shy'
        output_file = base_dir / f'macrocycle_transport_tumor_nme_{i}_enhanced.shy'
        
        if not input_file.exists():
            results.append((i, False, f"Input file not found: {input_file}"))
            continue
        
        success, message = enhance_tumor_model(input_file, output_file, i)
        results.append((i, success, message))
    
    # Summary
    print("\n" + "=" * 70)
    print("ENHANCEMENT SUMMARY")
    print("=" * 70)
    
    successes = 0
    failures = 0
    
    for variant_num, success, message in results:
        status = "✓" if success else "✗"
        print(f"{status} N-Me {variant_num} (tumor): {message}")
        if success:
            successes += 1
        else:
            failures += 1
    
    print("\n" + "=" * 70)
    print(f"Total: {successes} succeeded, {failures} failed")
    print("=" * 70)
    
    if failures == 0:
        print("\n✓ All tumor models enhanced successfully!")
        print("Next step: Verify configurations with verify_tumor_spatial_properties.py")
    else:
        print("\n⚠ Some models failed to enhance. Review error messages above.")


if __name__ == '__main__':
    main()
