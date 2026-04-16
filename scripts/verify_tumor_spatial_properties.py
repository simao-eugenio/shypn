#!/usr/bin/env python3
"""
Verify spatial properties in tumor N-methylation series models.
Checks that all expected properties are correctly configured.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

def verify_place_properties(place: Dict[str, Any], expected_config: Dict[str, Any]) -> List[str]:
    """
    Verify a single place has expected spatial properties.
    
    Returns:
        List of error messages (empty if all correct)
    """
    errors = []
    place_id = place.get('id', 'UNKNOWN')
    
    # Check required properties
    for prop, expected_value in expected_config.items():
        if prop == 'gradient':
            if expected_value is not None:
                if 'gradient' not in place:
                    errors.append(f"  {place_id}: Missing 'gradient' property")
                elif place['gradient'] != expected_value:
                    errors.append(f"  {place_id}: gradient is {place['gradient']}, expected {expected_value}")
            # If expected_value is None, gradient is optional
        else:
            if prop not in place:
                errors.append(f"  {place_id}: Missing '{prop}' property")
            elif place[prop] != expected_value:
                errors.append(f"  {place_id}: {prop} is {place[prop]}, expected {expected_value}")
    
    return errors


def verify_transition_rate_functions(transition: Dict[str, Any]) -> List[str]:
    """
    Verify continuous transitions have rate_function property.
    
    Returns:
        List of error messages (empty if correct)
    """
    errors = []
    
    if transition.get('type') == 'continuous':
        trans_id = transition.get('id', 'UNKNOWN')
        trans_name = transition.get('name', 'UNKNOWN')
        
        if 'rate_function' not in transition:
            errors.append(f"  {trans_id} ({trans_name}): Missing 'rate_function' property")
    
    return errors


def verify_tumor_model(model_path: Path, variant_num: int) -> Tuple[bool, List[str]]:
    """
    Verify a single tumor model.
    
    Returns:
        (all_correct: bool, error_messages: List[str])
    """
    try:
        with open(model_path, 'r') as f:
            model = json.load(f)
    except Exception as e:
        return False, [f"Failed to load model: {str(e)}"]
    
    errors = []
    
    # Expected spatial properties configuration
    expected_config = {
        'P3': {  # Drug_extended
            'volume_fL': 0.8,
            'diffusion_coeff_um2_s': 150.0,
            'boundary_type': 'impermeable',
            'gradient': None
        },
        'P4': {  # Drug_compact
            'volume_fL': 0.5,
            'diffusion_coeff_um2_s': 80.0,
            'boundary_type': 'impermeable',
            'gradient': None
        },
        'P7': {  # ATP
            'volume_fL': 5.0,
            'diffusion_coeff_um2_s': 300.0,
            'boundary_type': 'impermeable',
            'gradient': None
        },
        'P8': {  # ADP
            'volume_fL': 5.0,
            'diffusion_coeff_um2_s': 400.0,
            'boundary_type': 'impermeable',
            'gradient': None
        },
        'P9': {  # Pi
            'volume_fL': 5.0,
            'diffusion_coeff_um2_s': 600.0,
            'boundary_type': 'impermeable',
            'gradient': None
        },
        'P10': {  # H2O
            'volume_fL': 1000.0,
            'diffusion_coeff_um2_s': 2200.0,
            'boundary_type': 'permeable',
            'gradient': None
        },
        'P11': {  # Intracellular_gradient
            'volume_fL': 0.1,
            'diffusion_coeff_um2_s': 0.0,
            'boundary_type': 'selective',
            'gradient': [1, 0, 0]
        },
        'P12': {  # Extracellular_gradient
            'volume_fL': 0.1,
            'diffusion_coeff_um2_s': 0.0,
            'boundary_type': 'selective',
            'gradient': [1, 0, 0]
        }
    }
    
    # Verify places
    places_found = set()
    for place in model.get('places', []):
        place_id = place.get('id')
        if place_id in expected_config:
            places_found.add(place_id)
            place_errors = verify_place_properties(place, expected_config[place_id])
            errors.extend(place_errors)
    
    # Check for missing places
    expected_places = set(expected_config.keys())
    missing_places = expected_places - places_found
    if missing_places:
        for place_id in sorted(missing_places):
            errors.append(f"  {place_id}: Place not found in model")
    
    # Verify transitions have rate_function
    for transition in model.get('transitions', []):
        trans_errors = verify_transition_rate_functions(transition)
        errors.extend(trans_errors)
    
    return len(errors) == 0, errors


def main():
    """Verify all tumor models in the series."""
    base_dir = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    
    print("=" * 70)
    print("TUMOR N-METHYLATION SERIES VERIFICATION")
    print("=" * 70)
    print("\nVerifying spatial properties in tumor models (N-Me 0-7)...\n")
    
    results = []
    for i in range(8):
        model_path = base_dir / f'macrocycle_transport_tumor_nme_{i}_enhanced.shy'
        
        if not model_path.exists():
            results.append((i, False, [f"Enhanced model not found: {model_path}"]))
            continue
        
        all_correct, errors = verify_tumor_model(model_path, i)
        results.append((i, all_correct, errors))
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passes = 0
    failures = 0
    
    for variant_num, all_correct, errors in results:
        if all_correct:
            print(f"✓ N-Me {variant_num} (tumor): All properties correct")
            passes += 1
        else:
            print(f"✗ N-Me {variant_num} (tumor): {len(errors)} error(s)")
            for error in errors:
                print(error)
            failures += 1
    
    print("\n" + "=" * 70)
    print(f"Total: {passes} passed, {failures} failed")
    print("=" * 70)
    
    if failures == 0:
        print("\n✓ All tumor models verified successfully!")
        print("Next step: Run tumor simulations")
    else:
        print("\n⚠ Some models have configuration errors. Review above.")


if __name__ == '__main__':
    main()
