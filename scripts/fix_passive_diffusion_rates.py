#!/usr/bin/env python3
"""
Fix passive diffusion rate fields in N-methylation models.

ISSUE: The 'rate' field has embedded multipliers that don't match the correct
α^1.2 formula for passive permeability. The 'properties.rate_function' field
has the correct factors, but the 'rate' field used by the simulator is wrong.

SOLUTION: Set rate=None for transport transitions to force the simulator to
use the correct rate_function from properties.

Author: Fix script for N-methylation study
Date: 2026-02-05
"""

import json
import os
from pathlib import Path

# Model directory
MODEL_DIR = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")

# Transitions to fix
TRANSPORT_TRANSITIONS = ['active_transport', 'passive_diffusion', 'facilitated_diffusion']

def fix_model(model_path):
    """Fix rate fields in a single model file."""
    print(f"\n{'='*80}")
    print(f"Processing: {model_path.name}")
    print(f"{'='*80}")
    
    # Load model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    changes = []
    
    # Check each transport transition
    for trans in model['transitions']:
        if trans['name'] in TRANSPORT_TRANSITIONS:
            old_rate = trans.get('rate')
            rate_func = trans.get('properties', {}).get('rate_function')
            factor = trans.get('properties', {}).get('n_methylation_factor', 'N/A')
            
            if old_rate is not None:
                # Set rate to None to use rate_function from properties
                trans['rate'] = None
                changes.append(f"  {trans['name']:25} | rate: {str(old_rate)[:60]:60} → None (use rate_function)")
                print(f"  ✓ {trans['name']:25} | Factor: {factor}")
            else:
                print(f"  ✓ {trans['name']:25} | rate already None (correct)")
    
    if changes:
        # Save corrected model
        with open(model_path, 'w') as f:
            json.dump(model, f, indent=2)
        
        print(f"\n  💾 Saved {len(changes)} changes:")
        for change in changes:
            print(change)
        return len(changes)
    else:
        print(f"\n  ℹ️  No changes needed")
        return 0

def main():
    print("="*80)
    print("FIX PASSIVE DIFFUSION RATE FIELDS")
    print("="*80)
    print("\nISSUE: Embedded rate multipliers don't match α^1.2 formula")
    print("SOLUTION: Set rate=None to use correct rate_function from properties\n")
    
    total_changes = 0
    models_fixed = 0
    
    # Process all N-Me models (normal and tumor, 1-7)
    for series in ['normal', 'tumor']:
        print(f"\n{'─'*80}")
        print(f"SERIES: {series.upper()}")
        print(f"{'─'*80}")
        
        for nme in range(1, 8):  # N-Me 1-7 (skip N-Me 0 which is correct)
            model_path = MODEL_DIR / f"macrocycle_transport_{series}_nme_{nme}_enhanced.shy"
            
            if model_path.exists():
                changes = fix_model(model_path)
                total_changes += changes
                if changes > 0:
                    models_fixed += 1
            else:
                print(f"\n⚠️  File not found: {model_path}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Models fixed: {models_fixed}")
    print(f"Total transitions updated: {total_changes}")
    print(f"\nℹ️  Note: N-Me 0 models were skipped (already correct with rate=None)")
    print(f"ℹ️  Simulator will now use rate_function from properties (which has correct α^1.2 formula)")
    print(f"\n✓ All models ready for re-simulation")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
