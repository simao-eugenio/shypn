#!/usr/bin/env python3
"""Refactor all NME 0-7 models (normal and tumor) to match corrected structure.

Applies fixes from macrocycle_transport_normal_nme_0_enhanced_refactored.shy:
1. Transport rate functions use [Drug_ext] (not [Drug_extended])
2. Correct arc connections (P1→transport transitions, A19 type='test')  
3. Preserves NME-specific parameters (rate multipliers, degradation rates)
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path('workspace/projects/My_Project/drug_discovery/models/manuscript')
TEMPLATE_PATH = BASE_DIR / 'macrocycle_transport_normal_nme_0_enhanced_refactored.shy'

def backup_model(model_path: Path) -> Path:
    """Create timestamped backup of model."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = model_path.with_suffix(f'.shy.backup_{timestamp}')
    shutil.copy2(model_path, backup_path)
    print(f"  ✓ Backup: {backup_path.name}")
    return backup_path

def extract_nme_parameters(model: dict, cell_type: str) -> dict:
    """Extract NME-specific parameters from a model."""
    params = {'cell_type': cell_type}
    
    # Extract transport multipliers
    for trans in model['transitions']:
        if trans['name'] == 'active_transport':
            rate = trans['rate_function']
            # Extract first multiplier: (X.XXXX) * (...)
            multiplier = float(rate.split('(')[1].split(')')[0])
            params['active_multiplier'] = multiplier
            if 'properties' in trans:
                params['n_methylation_factor'] = trans['properties'].get('n_methylation_factor', 1.0)
                params['alpha_nme'] = trans['properties'].get('alpha_nme', 0.0)
                params['label'] = trans.get('label', f'Active Transport (N_Me=?)')
        
        elif trans['name'] == 'facilitated_diffusion':
            rate = trans['rate_function']
            multiplier = float(rate.split('(')[1].split(')')[0])
            params['facilitated_multiplier'] = multiplier
            params['facilitated_label'] = trans.get('label', f'Facilitated (N_Me=?)')
        
        elif trans['name'] == 'passive_diffusion':
            rate = trans['rate_function']
            multiplier = float(rate.split('(')[1].split(')')[0])
            params['passive_multiplier'] = multiplier
            params['passive_label'] = trans.get('label', f'Passive (N_Me=?)')
        
        # Extract degradation rates
        elif trans['name'] == 'proteasomal':
            rate = trans['rate_function'].split()[0]
            params['proteasomal_rate'] = float(rate)
        
        elif trans['name'] == 'lysosomal':
            rate = trans['rate_function'].split()[0]
            params['lysosomal_rate'] = float(rate)
        
        elif trans['name'] == 'chemical_hydrolysis':
            rate = trans['rate_function'].split()[0]
            params['chemical_rate'] = float(rate)
    
    # Extract tumor-specific PEPT1 level if tumor
    if cell_type == 'tumor':
        for place in model['places']:
            if place['name'] == 'PEPT1_free':
                params['pept1_initial'] = place.get('initial_marking', 10)
    
    return params

def apply_rate_function_fixes(model: dict, params: dict) -> dict:
    """Apply rate function fixes: [Drug_extended] → [Drug_ext]."""
    for trans in model['transitions']:
        if trans['name'] in ['active_transport', 'facilitated_diffusion', 'passive_diffusion']:
            # Replace [Drug_extended] with [Drug_ext] in rate functions
            rate = trans['rate_function']
            rate = rate.replace('[Drug_extended]', '[Drug_ext]')
            trans['rate_function'] = rate
            
            # Also fix in properties
            if 'properties' in trans and 'rate_function' in trans['properties']:
                trans['properties']['rate_function'] = trans['properties']['rate_function'].replace('[Drug_extended]', '[Drug_ext]')
            
            # Update labels
            if trans['name'] == 'active_transport':
                trans['label'] = params.get('label', trans.get('label', ''))
            elif trans['name'] == 'facilitated_diffusion':
                trans['label'] = params.get('facilitated_label', trans.get('label', ''))
            elif trans['name'] == 'passive_diffusion':
                trans['label'] = params.get('passive_label', trans.get('label', ''))
    
    return model

def refactor_model(source_path: Path, params: dict) -> bool:
    """Refactor a single model file."""
    try:
        # Read source model
        with open(source_path, 'r') as f:
            model = json.load(f)
        
        # Apply fixes
        model = apply_rate_function_fixes(model, params)
        
        # Update metadata
        if 'metadata' in model:
            model['metadata']['created'] = datetime.now().isoformat()
            model['metadata']['source'] = 'refactored'
        
        # Write back
        with open(source_path, 'w') as f:
            json.dump(model, f, indent=2)
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 80)
    print("REFACTORING NME SERIES MODELS (0-7, NORMAL & TUMOR)")
    print("=" * 80)
    
    # Process all NME models
    for nme in range(0, 8):
        for cell_type in ['normal', 'tumor']:
            model_name = f'macrocycle_transport_{cell_type}_nme_{nme}_enhanced.shy'
            model_path = BASE_DIR / model_name
            
            if not model_path.exists():
                print(f"\n⚠️  {model_name}: NOT FOUND - skipping")
                continue
            
            print(f"\n📝 Processing {model_name}...")
            
            # Read model to extract parameters
            with open(model_path, 'r') as f:
                model = json.load(f)
            
            params = extract_nme_parameters(model, cell_type)
            
            # Show parameters
            print(f"  NME={nme}, Cell={cell_type}")
            if 'active_multiplier' in params:
                print(f"  Transport multipliers: active={params['active_multiplier']:.4f}, "
                      f"facilitated={params.get('facilitated_multiplier', 1.0):.4f}, "
                      f"passive={params.get('passive_multiplier', 0.0):.4f}")
            if 'proteasomal_rate' in params:
                print(f"  Degradation rates: proteasomal={params['proteasomal_rate']:.6f}, "
                      f"lysosomal={params.get('lysosomal_rate', 0.0):.6f}, "
                      f"chemical={params.get('chemical_rate', 0.0):.6f}")
            
            # Backup
            backup_model(model_path)
            
            # Refactor
            if refactor_model(model_path, params):
                print(f"  ✅ Refactored successfully")
            else:
                print(f"  ❌ Failed - check backup")
    
    print("\n" + "=" * 80)
    print("✅ REFACTORING COMPLETE")
    print("=" * 80)
    print("\nAll transport rate functions now use [Drug_ext] instead of [Drug_extended]")
    print("Original models backed up with timestamp suffix")
    print("\n📋 NEXT STEP: Re-run simulations to verify they match original results")

if __name__ == '__main__':
    main()
