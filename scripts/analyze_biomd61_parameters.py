#!/usr/bin/env python3
"""
Extensive analysis of BIOMD0000000061 model to verify that all parameters
referenced in transition formulas are properly instantiated in the model.
"""

import json
import re
from collections import defaultdict
from typing import Set, Dict, List, Tuple

def extract_parameters_from_formula(formula: str, species_names: Set[str]) -> Set[str]:
    """
    Extract parameter names from a formula, excluding species names.
    Returns all identifiers that are NOT species names.
    """
    # Remove common mathematical functions
    formula_clean = re.sub(r'\b(exp|log|ln|sin|cos|tan|sqrt|abs|pow)\b', '', formula)
    
    # Extract all identifiers (alphanumeric + underscore)
    identifiers = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula_clean))
    
    # Remove species names (place names like P1, P2, etc.)
    parameters = identifiers - species_names
    
    # Remove common mathematical constants and operators
    math_constants = {'e', 'pi', 'inf', 'infinity', 'true', 'false'}
    parameters = parameters - math_constants
    
    return parameters


def analyze_model(filepath: str):
    """Main analysis function."""
    
    print("=" * 80)
    print("EXTENSIVE ANALYSIS OF BIOMD0000000061 SBML MODEL")
    print("Checking if all formula parameters are instantiated in the model")
    print("=" * 80)
    print()
    
    # Load the model
    with open(filepath, 'r') as f:
        model = json.load(f)
    
    # Extract place names (species)
    places = model.get('places', [])
    place_names = {p['name'] for p in places}
    print(f"📊 Model Statistics:")
    print(f"   - Places (species): {len(places)}")
    print(f"   - Transitions (reactions): {len(model.get('transitions', []))}")
    print(f"   - Arcs: {len(model.get('arcs', []))}")
    print()
    
    # Collect all parameters defined in the model from kinetic_metadata
    defined_parameters: Dict[str, Set[str]] = defaultdict(set)
    
    transitions = model.get('transitions', [])
    
    # First pass: collect all parameters that are defined
    for trans in transitions:
        kinetic_meta = trans.get('kinetic_metadata', {})
        params = kinetic_meta.get('parameters', {})
        
        for param_name, param_value in params.items():
            defined_parameters['global'].add(param_name)
    
    print(f"📋 Globally Defined Parameters ({len(defined_parameters['global'])} total):")
    for param in sorted(defined_parameters['global']):
        print(f"   - {param}")
    print()
    
    # Second pass: analyze each transition
    print("=" * 80)
    print("DETAILED TRANSITION ANALYSIS")
    print("=" * 80)
    print()
    
    issues_found = []
    all_referenced_params = set()
    
    for i, trans in enumerate(transitions, 1):
        trans_id = trans.get('id', 'unknown')
        trans_name = trans.get('name', 'unknown')
        trans_label = trans.get('label', 'N/A')
        
        kinetic_meta = trans.get('kinetic_metadata', {})
        formula = kinetic_meta.get('formula', '')
        formula_display = trans.get('properties', {}).get('rate_function_display', formula)
        local_params = kinetic_meta.get('parameters', {})
        
        print(f"🔍 Transition {i}/{len(transitions)}: {trans_name}")
        print(f"   ID: {trans_id}")
        print(f"   Label: {trans_label}")
        print(f"   Type: {trans.get('transition_type', 'unknown')}")
        print(f"   Formula: {formula_display}")
        print()
        
        # Extract parameters from formula
        referenced_params = extract_parameters_from_formula(formula, place_names)
        all_referenced_params.update(referenced_params)
        
        # Check which parameters are defined
        local_param_names = set(local_params.keys())
        undefined_params = referenced_params - defined_parameters['global']
        
        print(f"   📝 Parameters referenced in formula ({len(referenced_params)}):")
        for param in sorted(referenced_params):
            if param in local_param_names:
                value = local_params[param]
                status = "✅ DEFINED"
                print(f"      - {param} = {value} ({status})")
            elif param in defined_parameters['global']:
                status = "✅ DEFINED (global)"
                print(f"      - {param} ({status})")
            else:
                status = "❌ UNDEFINED"
                print(f"      - {param} ({status})")
                issues_found.append((trans_name, param, formula_display))
        
        if undefined_params:
            print(f"   ⚠️  WARNING: {len(undefined_params)} undefined parameter(s) found!")
        else:
            print(f"   ✅ All parameters are properly defined")
        
        print()
        print("-" * 80)
        print()
    
    # Summary report
    print("=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    print()
    
    print(f"📊 Overall Statistics:")
    print(f"   - Total transitions analyzed: {len(transitions)}")
    print(f"   - Total unique parameters referenced: {len(all_referenced_params)}")
    print(f"   - Total defined parameters: {len(defined_parameters['global'])}")
    print()
    
    if issues_found:
        print(f"❌ ISSUES FOUND: {len(issues_found)} undefined parameter reference(s)")
        print()
        print("Detailed issue list:")
        for trans_name, param, formula in issues_found:
            print(f"   ⚠️  Transition '{trans_name}' references undefined parameter '{param}'")
            print(f"      Formula: {formula}")
            print()
    else:
        print("✅ SUCCESS: All parameters referenced in formulas are properly defined!")
        print()
    
    # Check for unused parameters (defined but never referenced)
    referenced_in_formulas = all_referenced_params
    unused_params = defined_parameters['global'] - referenced_in_formulas - place_names
    
    if unused_params:
        print(f"ℹ️  NOTE: {len(unused_params)} parameter(s) defined but not used in formulas:")
        for param in sorted(unused_params):
            print(f"   - {param}")
        print()
    
    # Final verdict
    print("=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    if issues_found:
        print("❌ MODEL HAS EXTERNAL REFERENCES TO UNDEFINED PARAMETERS")
        print(f"   {len(issues_found)} issue(s) found that need attention")
    else:
        print("✅ MODEL IS CONSISTENT")
        print("   All parameters used in formulas are properly instantiated")
    print("=" * 80)
    
    return len(issues_found) == 0


if __name__ == '__main__':
    model_path = '/home/simao/projetos/shypn/workspace/projects/SBML/models/BIOMD0000000061.shy'
    success = analyze_model(model_path)
    exit(0 if success else 1)
