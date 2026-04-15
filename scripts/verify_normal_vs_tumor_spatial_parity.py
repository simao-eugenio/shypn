#!/usr/bin/env python3
"""
Verify that tumor series has identical spatial properties to normal series.
Compares each N-Me variant (0-7) between normal and tumor models.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

# Model paths
BASE_PATH = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NME_VARIANTS = list(range(8))  # 0-7

# Spatial properties to verify (stored as direct attributes in JSON)
SPATIAL_PROPERTIES = [
    'compartment_volume',
    'diffusion_coefficient', 
    'boundary_type',
    'gradient_vector'
]

# Expected places with spatial properties
SPATIAL_PLACES = [
    'P3',  # Drug_extended
    'P4',  # Drug_compact
    'P7',  # ATP
    'P8',  # ADP
    'P9',  # Pi
    'P10', # H2O
    'P11', # out_gradient
    'P12'  # in_gradient
]

def load_place_properties(model_path: Path) -> Dict[str, Dict[str, str]]:
    """Load spatial properties for all places from a model file (JSON format)."""
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    properties = {}
    
    # Navigate to places in the JSON structure
    places = model_data.get('places', [])
    
    for place in places:
        place_id = place.get('id')
        if place_id in SPATIAL_PLACES:
            place_props = {}
            # Spatial properties are stored as direct attributes on place objects
            for prop_name in SPATIAL_PROPERTIES:
                if prop_name in place and place[prop_name] is not None:
                    # Convert to string for comparison
                    value = place[prop_name]
                    # Handle gradient_vector specially (it's a list or null)
                    if prop_name == 'gradient_vector':
                        place_props[prop_name] = str(value) if value is not None else 'None'
                    else:
                        place_props[prop_name] = str(value)
            properties[place_id] = place_props
    
    return properties

def compare_properties(normal_props: Dict, tumor_props: Dict, nme_variant: int) -> List[str]:
    """Compare spatial properties between normal and tumor models."""
    issues = []
    
    # Check if both models have the same places
    normal_places = set(normal_props.keys())
    tumor_places = set(tumor_props.keys())
    
    if normal_places != tumor_places:
        missing_in_tumor = normal_places - tumor_places
        extra_in_tumor = tumor_places - normal_places
        if missing_in_tumor:
            issues.append(f"  ❌ Places missing in tumor: {missing_in_tumor}")
        if extra_in_tumor:
            issues.append(f"  ⚠️  Extra places in tumor: {extra_in_tumor}")
    
    # Compare properties for each place
    for place_id in SPATIAL_PLACES:
        if place_id not in normal_props:
            continue
            
        if place_id not in tumor_props:
            issues.append(f"  ❌ Place {place_id}: Missing in tumor model")
            continue
        
        normal_place = normal_props[place_id]
        tumor_place = tumor_props[place_id]
        
        for prop_name in SPATIAL_PROPERTIES:
            normal_val = normal_place.get(prop_name, 'NOT_SET')
            tumor_val = tumor_place.get(prop_name, 'NOT_SET')
            
            if normal_val != tumor_val:
                issues.append(
                    f"  ❌ Place {place_id}.{prop_name}: "
                    f"Normal={normal_val}, Tumor={tumor_val}"
                )
    
    return issues

def main():
    """Main verification workflow."""
    print("=" * 80)
    print("SPATIAL PROPERTY PARITY CHECK: Normal vs Tumor Series")
    print("=" * 80)
    print("\nVerifying that tumor models have identical spatial properties to normal models")
    print("across all N-methylation variants (0-7)...\n")
    
    all_passed = True
    total_comparisons = 0
    
    for nme in NME_VARIANTS:
        print(f"\n{'=' * 80}")
        print(f"N-Me {nme} Comparison")
        print(f"{'=' * 80}")
        
        # Construct file paths
        normal_path = BASE_PATH / f"macrocycle_transport_normal_nme_{nme}_enhanced.shy"
        tumor_path = BASE_PATH / f"macrocycle_transport_tumor_nme_{nme}_enhanced.shy"
        
        # Check if files exist
        if not normal_path.exists():
            print(f"❌ Normal model not found: {normal_path}")
            all_passed = False
            continue
            
        if not tumor_path.exists():
            print(f"❌ Tumor model not found: {tumor_path}")
            all_passed = False
            continue
        
        print(f"📂 Normal: {normal_path.name}")
        print(f"📂 Tumor:  {tumor_path.name}")
        
        # Load properties
        try:
            normal_props = load_place_properties(normal_path)
            tumor_props = load_place_properties(tumor_path)
            
            print(f"\n🔍 Checking {len(SPATIAL_PLACES)} places × {len(SPATIAL_PROPERTIES)} properties...")
            
            # Compare
            issues = compare_properties(normal_props, tumor_props, nme)
            total_comparisons += 1
            
            if issues:
                print(f"\n❌ MISMATCH DETECTED ({len(issues)} issues):")
                for issue in issues:
                    print(issue)
                all_passed = False
            else:
                print(f"\n✅ PERFECT MATCH - All spatial properties identical")
                
                # Show summary of verified properties
                print(f"\nVerified properties for {len(normal_props)} places:")
                for place_id in sorted(normal_props.keys()):
                    props = normal_props[place_id]
                    prop_count = len([v for v in props.values() if v != 'NOT_SET'])
                    print(f"  • {place_id}: {prop_count} spatial properties ✓")
        
        except Exception as e:
            print(f"❌ Error comparing models: {e}")
            all_passed = False
    
    # Final summary
    print(f"\n{'=' * 80}")
    print("VERIFICATION SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total comparisons: {total_comparisons}/8")
    
    if all_passed and total_comparisons == 8:
        print("\n✅ SUCCESS: All tumor models have identical spatial properties to normal models")
        print("   The series are directly comparable for structure-activity analysis.")
        print("\n🎯 READY FOR SIMULATION - Tumor series validated")
    else:
        print("\n❌ FAILED: Spatial property mismatches detected")
        print("   Review and fix issues before running simulations")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
