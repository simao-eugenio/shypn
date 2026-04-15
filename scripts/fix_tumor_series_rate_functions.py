#!/usr/bin/env python3
"""
Fix missing rate_function properties in tumor N-methylation series (0-7).
Copies rate functions from working normal N-Me 6 enhanced model to all tumor models.
"""

import json
from pathlib import Path
from typing import Dict

def load_rate_functions(reference_path: Path) -> Dict[str, Dict[str, str]]:
    """Load rate functions and types from a working reference model."""
    with open(reference_path, 'r') as f:
        model = json.load(f)
    
    transition_data = {}
    for transition in model.get('transitions', []):
        trans_type = transition.get('transition_type', transition.get('type', ''))
        trans_name = transition.get('name', '')
        trans_id = transition.get('id', '')
        
        if trans_type == 'continuous':
            rate_func = transition.get('rate_function') or transition.get('rate', '')
            if rate_func:
                transition_data[trans_name] = {
                    'rate_function': rate_func,
                    'transition_type': 'continuous',
                    'id': trans_id
                }
    
    return transition_data

def fix_tumor_model_rate_functions(
    model_path: Path, 
    transition_data: Dict[str, Dict[str, str]],
    variant_num: int
) -> tuple[bool, str, int]:
    """
    Fix rate functions in a tumor model.
    
    Args:
        model_path: Path to tumor model file
        transition_data: Dict mapping transition names to their data (rate_function, type)
        variant_num: N-methylation level (0-7)
    
    Returns:
        (success: bool, message: str, fixed_count: int)
    """
    try:
        with open(model_path, 'r') as f:
            model = json.load(f)
        
        fixed_count = 0
        for transition in model.get('transitions', []):
            trans_type = transition.get('transition_type', transition.get('type', ''))
            trans_name = transition.get('name', '')
            trans_id = transition.get('id', '')
            
            # Check if this is or should be a continuous transition
            if trans_type == 'continuous' or trans_name in transition_data:
                # Ensure transition_type is set
                if 'transition_type' not in transition or transition['transition_type'] != 'continuous':
                    transition['transition_type'] = 'continuous'
                    fixed_count += 1
                
                # Try to find matching transition data from reference
                if trans_name in transition_data:
                    ref_data = transition_data[trans_name]
                    rate_func = ref_data['rate_function']
                    
                    # Add rate_function field if missing
                    if 'rate_function' not in transition:
                        transition['rate_function'] = rate_func
                        fixed_count += 1
                        print(f"  ✓ Added rate_function to {trans_id}: {trans_name}")
                    
                    # Ensure rate field exists (same as rate_function)
                    if 'rate' not in transition:
                        transition['rate'] = rate_func
                        fixed_count += 1
                    
                    # Ensure properties dict has rate_function
                    if 'properties' not in transition:
                        transition['properties'] = {}
                    
                    if 'rate_function' not in transition['properties']:
                        transition['properties']['rate_function'] = rate_func
                        fixed_count += 1
                        print(f"  ✓ Added rate_function to {trans_id} properties")
                else:
                    # Try to use existing rate field as rate_function
                    if 'rate' in transition and 'rate_function' not in transition:
                        transition['rate_function'] = transition['rate']
                        
                        if 'properties' not in transition:
                            transition['properties'] = {}
                        transition['properties']['rate_function'] = transition['rate']
                        
                        fixed_count += 1
                        print(f"  ✓ Used existing rate for {trans_id}: {trans_name}")
        
        # Save fixed model if changes were made
        if fixed_count > 0:
            with open(model_path, 'w') as f:
                json.dump(model, f, indent=2)
            return True, f"Fixed {fixed_count} properties in N-Me {variant_num} tumor", fixed_count
        else:
            return True, f"N-Me {variant_num} tumor already has all rate functions", 0
    
    except Exception as e:
        return False, f"Failed to fix N-Me {variant_num} tumor: {str(e)}", 0

def main():
    """Fix rate functions for all tumor models."""
    base_dir = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
    reference_path = base_dir / 'macrocycle_transport_normal_nme_6_enhanced.shy'
    
    print("=" * 80)
    print("TUMOR SERIES RATE FUNCTION FIX")
    print("=" * 80)
    print(f"\nReference model: {reference_path.name}")
    
    # Load reference rate functions
    if not reference_path.exists():
        print(f"\n❌ ERROR: Reference model not found: {reference_path}")
        return 1
    
    print("Loading reference rate functions...")
    transition_data = load_rate_functions(reference_path)
    print(f"✅ Loaded {len(transition_data)} continuous transitions from reference\n")
    
    # Display reference rate functions
    print("Reference transitions:")
    for name, data in sorted(transition_data.items()):
        print(f"  • {name} ({data['id']})")
    
    print("\n" + "=" * 80)
    print("FIXING TUMOR MODELS")
    print("=" * 80 + "\n")
    
    # Fix all tumor models
    results = []
    total_fixed = 0
    
    for i in range(8):
        model_path = base_dir / f'macrocycle_transport_tumor_nme_{i}_enhanced.shy'
        
        if not model_path.exists():
            results.append((i, False, f"File not found: {model_path.name}", 0))
            continue
        
        print(f"N-Me {i} (tumor): {model_path.name}")
        success, message, fixed_count = fix_tumor_model_rate_functions(
            model_path, transition_data, i
        )
        results.append((i, success, message, fixed_count))
        total_fixed += fixed_count
        print(f"  {message}\n")
    
    # Summary
    print("=" * 80)
    print("FIX SUMMARY")
    print("=" * 80)
    
    successes = sum(1 for _, success, _, _ in results if success)
    
    for variant, success, message, _ in results:
        icon = "✅" if success else "❌"
        print(f"{icon} N-Me {variant} (tumor): {message}")
    
    print("\n" + "=" * 80)
    print(f"Total: {successes}/8 models processed, {total_fixed} rate functions added")
    print("=" * 80)
    
    if successes == 8 and total_fixed > 0:
        print("\n✅ All tumor models fixed successfully!")
        print("   Rate functions added to continuous transitions.")
        print("   Models are now ready for simulation in UI.")
        return 0
    elif successes == 8 and total_fixed == 0:
        print("\n✅ All tumor models already have rate functions.")
        return 0
    else:
        print("\n❌ Some tumor models could not be fixed.")
        return 1

if __name__ == "__main__":
    exit(main())
