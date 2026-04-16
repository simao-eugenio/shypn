#!/usr/bin/env python3
"""
Verification Script: Spatial Properties in N-Methylation Models
================================================================

Checks that all N-methylation models (0-6 enhanced) have the correct
spatial property configuration for places P3-P12.
"""

import json
from pathlib import Path

# Define expected spatial properties for each place
EXPECTED_PROPERTIES = {
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

def load_model(filepath):
    """Load a .shy model file (JSON format)."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"   ❌ ERROR loading {filepath}: {e}")
        return None

def find_place_by_id(model, place_id):
    """Find a place in the model by its ID."""
    if not model or 'places' not in model:
        return None
    
    for place in model['places']:
        if place.get('id') == place_id:
            return place
    return None

def check_property(place, prop_name, expected_value, tolerance=0.001):
    """Check if a place has the expected property value."""
    if prop_name not in place:
        return False, "MISSING"
    
    actual_value = place[prop_name]
    
    # Handle different value types
    if isinstance(expected_value, (int, float)):
        if abs(actual_value - expected_value) <= tolerance:
            return True, actual_value
        else:
            return False, f"{actual_value} (expected {expected_value})"
    
    elif isinstance(expected_value, list):
        if actual_value == expected_value:
            return True, actual_value
        else:
            return False, f"{actual_value} (expected {expected_value})"
    
    elif isinstance(expected_value, str):
        if actual_value == expected_value:
            return True, actual_value
        else:
            return False, f"{actual_value} (expected {expected_value})"
    
    elif isinstance(expected_value, bool):
        if actual_value == expected_value:
            return True, actual_value
        else:
            return False, f"{actual_value} (expected {expected_value})"
    
    return False, "UNKNOWN TYPE"

def verify_model(filepath):
    """Verify spatial properties for a single model."""
    model_name = Path(filepath).name
    print(f"\n{'='*80}")
    print(f"📋 Checking: {model_name}")
    print(f"{'='*80}")
    
    model = load_model(filepath)
    if not model:
        return False
    
    all_passed = True
    issues = []
    
    for place_id, expected_props in EXPECTED_PROPERTIES.items():
        place = find_place_by_id(model, place_id)
        
        if not place:
            print(f"\n❌ {place_id}: PLACE NOT FOUND IN MODEL")
            all_passed = False
            issues.append(f"{place_id}: MISSING")
            continue
        
        place_name = place.get('name', 'UNNAMED')
        print(f"\n✓ {place_id} ({place_name}):")
        
        place_ok = True
        for prop_name, expected_value in expected_props.items():
            passed, result = check_property(place, prop_name, expected_value)
            
            if passed:
                if isinstance(expected_value, (int, float)):
                    print(f"   ✅ {prop_name}: {result}")
                else:
                    print(f"   ✅ {prop_name}: {result}")
            else:
                print(f"   ❌ {prop_name}: {result}")
                place_ok = False
                all_passed = False
                issues.append(f"{place_id}.{prop_name}")
        
        if place_ok:
            print(f"   🎯 All properties correct!")
    
    print(f"\n{'='*80}")
    if all_passed:
        print(f"✅ {model_name}: ALL SPATIAL PROPERTIES VERIFIED")
    else:
        print(f"❌ {model_name}: ISSUES FOUND")
        print(f"   Issues: {', '.join(issues)}")
    print(f"{'='*80}")
    
    return all_passed

# ============================================================================
# MAIN VERIFICATION
# ============================================================================
if __name__ == '__main__':
    print("="*80)
    print("SPATIAL PROPERTIES VERIFICATION")
    print("Checking N-Methylation Models (0-6 Enhanced)")
    print("="*80)
    
    base_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    
    models_to_check = [
        ('macrocycle_transport_normal_nme_0_enhanced.shy', 'N-Me 0 (Baseline)'),
        ('macrocycle_transport_normal_nme_1_enhanced.shy', 'N-Me 1'),
        ('macrocycle_transport_normal_nme_2_enhanced.shy', 'N-Me 2'),
        ('macrocycle_transport_normal_nme_3_enhanced.shy', 'N-Me 3'),
        ('macrocycle_transport_normal_nme_4_enhanced.shy', 'N-Me 4'),
        ('macrocycle_transport_normal_nme_5_enhanced.shy', 'N-Me 5'),
        ('macrocycle_transport_normal_nme_6_enhanced.shy', 'N-Me 6'),
    ]
    
    results = {}
    
    for model_file, description in models_to_check:
        model_path = base_path / model_file
        
        if not model_path.exists():
            print(f"\n⚠️  WARNING: {model_file} NOT FOUND at {model_path}")
            results[description] = False
            continue
        
        results[description] = verify_model(model_path)
    
    # ========================================================================
    # SUMMARY REPORT
    # ========================================================================
    print(f"\n\n{'='*80}")
    print("📊 VERIFICATION SUMMARY")
    print(f"{'='*80}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Models Checked: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}\n")
    
    for description, passed_check in results.items():
        status = "✅ PASS" if passed_check else "❌ FAIL"
        print(f"   {status} - {description}")
    
    print(f"\n{'='*80}")
    
    if all(results.values()):
        print("🎉 SUCCESS! All models have correct spatial properties!")
        print("="*80)
        exit(0)
    else:
        print("⚠️  ATTENTION: Some models need spatial property configuration!")
        print("="*80)
        exit(1)
