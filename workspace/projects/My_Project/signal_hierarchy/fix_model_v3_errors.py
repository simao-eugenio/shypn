#!/usr/bin/env python3
"""
Fix all errors in lambda_hierarchical_v3.shy:
1. Convert 'mass_action' transitions to 'stochastic'
2. Convert 'source' transitions to 'stochastic'
3. Fix CI_Protein references to use CI_Intact (P3)
4. Fix rate function bracket syntax [P7] to P7
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel

# Load the model
model_path = 'workspace/projects/My_Project/signal_hierarchy/models/lambda_hierarchical_v3.shy'
print(f"Loading model from {model_path}...")
model = DocumentModel.load_from_file(model_path)

print(f"\nModel loaded: {len(model.transitions)} transitions")
print("=" * 80)

# Track fixes
fixes = {
    'mass_action_to_stochastic': [],
    'source_to_stochastic': [],
    'ci_protein_fixed': [],
    'bracket_syntax_fixed': []
}

# Fix all transitions
for trans in model.transitions:
    trans_id = trans.id
    trans_label = trans.label
    
    # Fix 1: Convert mass_action to stochastic
    if trans.transition_type == 'mass_action':
        print(f"✓ {trans_id} ({trans_label}): mass_action → stochastic")
        trans.transition_type = 'stochastic'
        fixes['mass_action_to_stochastic'].append(trans_id)
    
    # Fix 2: Convert source to stochastic
    if trans.transition_type == 'source':
        print(f"✓ {trans_id} ({trans_label}): source → stochastic")
        trans.transition_type = 'stochastic'
        fixes['source_to_stochastic'].append(trans_id)
        # For source transitions, set a default constant rate if none exists
        if not hasattr(trans, 'rate_function') or not trans.rate_function:
            trans.rate_function = '1.0'
            print(f"  Added default rate: 1.0")
    
    # Fix 3 & 4: Fix rate expressions
    # Check both .rate attribute and properties dict
    rate_changed = False
    
    # Fix .rate attribute
    if hasattr(trans, 'rate') and trans.rate:
        original_rate = str(trans.rate)
        fixed_rate = original_rate
        
        # Fix CI_Protein references to CI_Intact
        if 'CI_Protein' in fixed_rate:
            fixed_rate = fixed_rate.replace('CI_Protein', 'CI_Intact')
            fixes['ci_protein_fixed'].append(trans_id)
            rate_changed = True
        
        # Fix bracket syntax [P7] to P7
        if '[P' in fixed_rate and ']' in fixed_rate:
            import re
            fixed_rate = re.sub(r'\[([P]\d+)\]', r'\1', fixed_rate)
            fixes['bracket_syntax_fixed'].append(trans_id)
            rate_changed = True
        
        if rate_changed:
            trans.rate = fixed_rate
            print(f"✓ {trans_id} ({trans_label}): Fixed rate expression")
            print(f"  Original: {original_rate}")
            print(f"  Fixed:    {fixed_rate}")
    
    # Also fix properties dict if it exists
    if hasattr(trans, 'properties') and isinstance(trans.properties, dict):
        for prop_key in ['rate_function', 'rate_function_display']:
            if prop_key in trans.properties and trans.properties[prop_key]:
                original_val = trans.properties[prop_key]
                fixed_val = original_val
                
                if 'CI_Protein' in fixed_val:
                    fixed_val = fixed_val.replace('CI_Protein', 'CI_Intact')
                    rate_changed = True
                
                if '[P' in fixed_val and ']' in fixed_val:
                    import re
                    fixed_val = re.sub(r'\[([P]\d+)\]', r'\1', fixed_val)
                    rate_changed = True
                
                if fixed_val != original_val:
                    trans.properties[prop_key] = fixed_val
                    print(f"  Also fixed {prop_key}: {fixed_val}")

print("\n" + "=" * 80)
print("FIXES SUMMARY:")
print(f"  mass_action → stochastic: {len(fixes['mass_action_to_stochastic'])} transitions")
print(f"    {fixes['mass_action_to_stochastic']}")
print(f"  source → stochastic: {len(fixes['source_to_stochastic'])} transitions")
print(f"    {fixes['source_to_stochastic']}")
print(f"  CI_Protein → CI_Intact: {len(fixes['ci_protein_fixed'])} transitions")
print(f"    {fixes['ci_protein_fixed']}")
print(f"  Bracket syntax fixed: {len(fixes['bracket_syntax_fixed'])} transitions")
print(f"    {fixes['bracket_syntax_fixed']}")

# Save the fixed model
print(f"\nSaving fixed model to {model_path}...")
model.save_to_file(model_path)

print("✅ All fixes applied successfully!")
print(f"\nFinal model: {len(model.places)} places, {len(model.transitions)} transitions")
