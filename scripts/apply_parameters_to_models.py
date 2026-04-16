#!/usr/bin/env python3
"""
Apply tuned parameters from parameter file to all NMe models in the series.

This script:
1. Loads parameters from model_parameters_nme_0.json
2. Updates rate functions in all models (NMe-0 through NMe-7)
3. Preserves N-methylation-specific scaling (passive diffusion)
4. Creates backups before modifying

Usage:
    python apply_parameters_to_models.py [--dry-run]
"""

import json
import re
from pathlib import Path
from datetime import datetime
import argparse

# Configuration
MODELS_DIR = Path('workspace/projects/My_Project/drug_discovery/models/normal')
PARAM_FILE = Path('model_parameters_nme_0.json')
BACKUP_SUFFIX = '.backup_before_params'

def load_parameters():
    """Load parameter configuration."""
    with open(PARAM_FILE, 'r') as f:
        return json.load(f)

def extract_nme_number(filename):
    """Extract NMe number from filename."""
    match = re.search(r'nme_(\d+)', filename.lower())
    return int(match.group(1)) if match else None

def update_rate_function(transition_name, current_rate_func, params, nme_number):
    """
    Update rate function with new parameters.
    
    Args:
        transition_name: Name of the transition
        current_rate_func: Current rate function string
        params: Parameter dictionary
        nme_number: N-methylation level (0-7)
    
    Returns:
        Updated rate function string, or None if no update needed
    """
    
    # Get parameter set based on transition name
    param_set = None
    base_rate = None
    
    # Check each parameter category
    for category in ['transport_parameters', 'degradation_parameters', 
                     'energy_metabolism', 'conformational_dynamics', 'protein_turnover']:
        if category in params and transition_name in params[category]:
            param_set = params[category][transition_name]
            base_rate = param_set.get('base_rate')
            break
    
    if param_set is None:
        return None  # No parameters defined for this transition
    
    # SPECIAL CASE: Passive diffusion scales with NMe number
    if transition_name == 'passive_diffusion' and base_rate is not None:
        # NMe-0: blocked (rate ~0)
        # NMe-7: fully active (rate = base_rate)
        # Linear scaling: rate = base_rate * (nme_number / 7)
        scaling_factor = nme_number / 7.0
        scaled_rate = base_rate * scaling_factor
        
        # Update first number in rate function (base rate)
        updated_func = re.sub(r'^\d+\.?\d*', f'{scaled_rate:.1f}', current_rate_func)
        return updated_func
    
    # For other transitions, just update base rate if available
    if base_rate is not None:
        # Update first number in rate function
        updated_func = re.sub(r'^[\d\.]+(?:e[+-]?\d+)?', str(base_rate), current_rate_func)
        return updated_func
    
    return None

def apply_parameters_to_model(model_path, params, dry_run=False):
    """Apply parameters to a single model file."""
    
    # Extract NMe number
    nme_number = extract_nme_number(model_path.name)
    if nme_number is None:
        print(f"  ⚠️  Could not extract NMe number from {model_path.name}")
        return False
    
    print(f"\nProcessing: {model_path.name} (NMe-{nme_number})")
    
    # Load model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    # Create backup (if not dry-run)
    if not dry_run:
        backup_path = model_path.with_suffix(model_path.suffix + BACKUP_SUFFIX)
        with open(backup_path, 'w') as f:
            json.dump(model, f, indent=2)
        print(f"  ✓ Backup created: {backup_path.name}")
    
    # Update thermodynamic settings
    if 'thermodynamic_settings' in params:
        model['thermodynamic_settings'] = params['thermodynamic_settings']
        print(f"  ✓ Updated thermodynamic settings (T={params['thermodynamic_settings']['temperature']} K)")
    
    # Track changes
    transitions_updated = 0
    
    # Update transitions
    for transition in model['transitions']:
        if 'rate_function' not in transition or not transition['rate_function']:
            continue
        
        transition_name = transition['name']
        current_func = transition['rate_function']
        
        # Try to update rate function
        new_func = update_rate_function(transition_name, current_func, params, nme_number)
        
        if new_func and new_func != current_func:
            transitions_updated += 1
            if dry_run:
                print(f"  [DRY-RUN] Would update {transition_name}")
                print(f"    Current: {current_func[:60]}...")
                print(f"    New:     {new_func[:60]}...")
            else:
                transition['rate_function'] = new_func
                print(f"  ✓ Updated {transition_name}")
    
    # Save model (if not dry-run)
    if not dry_run and transitions_updated > 0:
        with open(model_path, 'w') as f:
            json.dump(model, f, indent=2)
        print(f"  ✓ Saved {transitions_updated} transition updates")
    elif dry_run:
        print(f"  [DRY-RUN] Would update {transitions_updated} transitions")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Apply parameters to NMe model series')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be changed without modifying files')
    parser.add_argument('--model', type=int, choices=range(8),
                       help='Apply to specific NMe model only (0-7)')
    args = parser.parse_args()
    
    print("="*70)
    print("APPLYING PARAMETERS TO NMe MODEL SERIES")
    print("="*70)
    
    # Load parameters
    if not PARAM_FILE.exists():
        print(f"❌ Parameter file not found: {PARAM_FILE}")
        return 1
    
    print(f"\nLoading parameters from: {PARAM_FILE}")
    params = load_parameters()
    
    print(f"Parameters loaded:")
    print(f"  Base model: {params['model_metadata']['base_model']}")
    print(f"  Description: {params['model_metadata']['description']}")
    print(f"  Key change: ATP_synthesis_active = {params['energy_metabolism']['ATP_synthesis_active']['base_rate']}")
    
    if args.dry_run:
        print("\n⚠️  DRY-RUN MODE: No files will be modified\n")
    
    # Find models
    if args.model is not None:
        # Single model
        pattern = f'macrocycle_transport_normal_nme_{args.model}_thermo.shy'
        model_files = list(MODELS_DIR.glob(pattern))
    else:
        # All models
        model_files = list(MODELS_DIR.glob('macrocycle_transport_normal_nme_*_thermo.shy'))
    
    if not model_files:
        print(f"❌ No model files found in {MODELS_DIR}")
        return 1
    
    model_files.sort()
    print(f"\nFound {len(model_files)} models to update")
    
    # Apply parameters to each model
    success_count = 0
    for model_path in model_files:
        try:
            if apply_parameters_to_model(model_path, params, dry_run=args.dry_run):
                success_count += 1
        except Exception as e:
            print(f"  ❌ Error processing {model_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Successfully processed: {success_count}/{len(model_files)} models")
    
    if args.dry_run:
        print(f"\nThis was a DRY-RUN. To apply changes, run without --dry-run flag")
    else:
        print(f"\nBackups created with suffix: {BACKUP_SUFFIX}")
        print(f"\nNow re-run simulations to validate parameters:")
        print(f"  • Accumulation ratio should be 0.1-100:1")
        print(f"  • Nucleotide conservation < 5% drift")
        print(f"  • Energy charge 0.70-0.95")
        print(f"  • Efflux and degradation should fire")
    
    return 0 if success_count == len(model_files) else 1

if __name__ == '__main__':
    exit(main())
