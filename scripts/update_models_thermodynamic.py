#!/usr/bin/env python3
"""
Update drug transport models with thermodynamic integration:
1. Add thermodynamic constraints to rate functions
2. Convert test arcs to signal_flow arcs for thermodynamic places
"""

import json
import shutil
from pathlib import Path

def extract_nme_number(filename):
    """Extract N-methylation number from filename"""
    import re
    match = re.search(r'nme_(\d+)', filename)
    return int(match.group(1)) if match else 0

def update_rate_function(transition, nme_number):
    """Update rate function with thermodynamic constraints"""
    name = transition['name']
    
    # Skip if no rate function
    if 'rate_function' not in transition:
        return False
    
    old_rate = transition['rate_function']
    
    # Extract multiplier from old rate (e.g., "* 1.000" or "* 0.000")
    import re
    mult_match = re.search(r'\*\s*([\d.]+)\s*$', old_rate)
    old_multiplier = float(mult_match.group(1)) if mult_match else 1.0
    
    updates = {
        'passive_diffusion': lambda: (
            f"((20.0 * [Drug_ext] * ([Drug_compact] / ([Drug_extended] + [Drug_compact])) * "
            f"exp(-[Membrane_potential]/25.7) * "
            f"arrhenius(T_celsius, Ea=20, T0=37, celsius=True)) * exp(0.15 * gaussian_noise())) * "
            f"{0.000 + nme_number * 0.553:.3f}"
        ),
        'active_transport': lambda: (
            f"((15.0 * [Drug_ext] * [PEPT1_free] * ([ATP_pool]**2 / (2000**2 + [ATP_pool]**2)) * "
            f"thermo_driving_force(2 * atp_gibbs_free_energy([ATP_pool], [ADP_pool], [Pi_pool], T_celsius, pH, celsius=True), T_celsius, celsius=True) * "
            f"arrhenius(T_celsius, Ea=55, T0=37, celsius=True)) * exp(0.15 * gaussian_noise())) * "
            f"{1.000 - nme_number * 0.143:.3f}"
        ),
        'ABC_efflux': lambda: (
            f"(0.1 * [Drug_intracellular] * ([ATP_pool]**2 / (2000**2 + [ATP_pool]**2)) * "
            f"thermo_driving_force(2 * atp_gibbs_free_energy([ATP_pool], [ADP_pool], [Pi_pool], T_celsius, pH, celsius=True), T_celsius, celsius=True) * "
            f"(1 + [Membrane_potential]/100) * "
            f"arrhenius(T_celsius, Ea=65, T0=37, celsius=True)) * "
            f"{1.000 - nme_number * 0.143:.3f}"
        ),
        'facilitated_diffusion': lambda: (
            f"((3.0 * [Drug_ext] * [PEPT1_free] * ([ATP_pool] / (1000 + [ATP_pool])) * "
            f"(1 + [pH_gradient]) * "
            f"arrhenius(T_celsius, Ea=35, T0=37, celsius=True)) * exp(0.15 * gaussian_noise())) * "
            f"{1.000 - nme_number * 0.143:.3f}"
        ),
        'proteasomal': lambda: (
            f"0.010000 * [Drug_intracellular] * ([ATP_pool]**4 / (3000**4 + [ATP_pool]**4)) * "
            f"thermo_driving_force(4 * atp_gibbs_free_energy([ATP_pool], [ADP_pool], [Pi_pool], T_celsius, pH, celsius=True), T_celsius, celsius=True) * "
            f"arrhenius(T_celsius, Ea=60, T0=37, celsius=True)"
        ),
        'lysosomal': lambda: (
            f"0.005000 * [Drug_intracellular] * ([ATP_pool] / (1000 + [ATP_pool])) * "
            f"arrhenius(T_celsius, Ea=45, T0=37, celsius=True)"
        ),
        'chemical_hydrolysis': lambda: (
            f"0.001000 * [Drug_intracellular] * "
            f"arrhenius(T_celsius, Ea=25, T0=37, celsius=True) * "
            f"(1 + 0.1 * (7.2 - pH))"
        )
    }
    
    if name in updates:
        new_rate = updates[name]()
        transition['rate_function'] = new_rate
        if 'properties' in transition and 'rate_function' in transition['properties']:
            transition['properties']['rate_function'] = new_rate
        return True
    return False

def convert_test_arcs_to_signal_flow(model):
    """Convert test arcs to signal_flow arcs"""
    converted = []
    for arc in model['arcs']:
        # Skip if no arc_type field
        if 'arc_type' not in arc:
            continue
            
        if arc['arc_type'] == 'test':
            arc['arc_type'] = 'signal_flow'
            # Update visual properties for signal flow
            arc['color'] = [0.7, 0.7, 0.7]
            if arc.get('consumes') is False:
                del arc['consumes']  # Not needed for signal_flow
            converted.append(arc['id'])
    return converted

def update_model_file(model_path):
    """Update a single model file"""
    nme_number = extract_nme_number(model_path.name)
    
    print(f"\nUpdating: {model_path.name}")
    print(f"  N-methylation number: {nme_number}")
    
    # Backup
    backup_path = model_path.with_suffix('.shy.backup_pre_thermodynamic')
    if not backup_path.exists():
        shutil.copy2(model_path, backup_path)
        print(f"  ✓ Backup created: {backup_path.name}")
    
    # Load model
    with open(model_path) as f:
        model = json.load(f)
    
    # Update rate functions
    updated_transitions = []
    for transition in model['transitions']:
        if update_rate_function(transition, nme_number):
            updated_transitions.append(transition['name'])
    
    print(f"  ✓ Updated {len(updated_transitions)} rate functions:")
    for name in updated_transitions:
        print(f"    - {name}")
    
    # Convert test arcs to signal_flow
    converted_arcs = convert_test_arcs_to_signal_flow(model)
    print(f"  ✓ Converted {len(converted_arcs)} test arcs to signal_flow")
    if converted_arcs:
        for arc_id in converted_arcs:
            arc = next(a for a in model['arcs'] if a.get('id') == arc_id)
            # Get source name (with error handling)
            try:
                source = next((p for p in model['places'] if p.get('id') == arc.get('source_id')), 
                              next((t for t in model['transitions'] if t.get('id') == arc.get('source_id')), None))
                target = next((p for p in model['places'] if p.get('id') == arc.get('target_id')), 
                              next((t for t in model['transitions'] if t.get('id') == arc.get('target_id')), None))
                source_name = source['name'] if source else arc.get('source_id', '?')
                target_name = target['name'] if target else arc.get('target_id', '?')
                print(f"    - {arc_id}: {source_name} -> {target_name}")
            except Exception as e:
                print(f"    - {arc_id}: (error getting details: {e})")
    else:
        print(f"    (no test arcs found - already converted)")
    
    # Save updated model
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"  ✓ Model saved")
    
    return len(updated_transitions), len(converted_arcs)

def main():
    # Find all model files
    models_dir = Path('workspace/projects/My_Project/drug_discovery/models/normal')
    model_files = sorted(models_dir.glob('macrocycle_transport_normal_nme_*_thermo.shy'))
    model_files = [f for f in model_files if not any(
        suffix in str(f) for suffix in ['.backup', '.bak']
    )]
    
    print("="*80)
    print("THERMODYNAMIC INTEGRATION UPDATE")
    print("="*80)
    print(f"\nFound {len(model_files)} models to update")
    
    total_transitions = 0
    total_arcs = 0
    
    for model_path in model_files:
        trans, arcs = update_model_file(model_path)
        total_transitions += trans
        total_arcs += arcs
    
    print("\n" + "="*80)
    print("UPDATE COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  • Models updated: {len(model_files)}")
    print(f"  • Transitions updated: {total_transitions}")
    print(f"  • Arcs converted: {total_arcs}")
    print(f"\nThermodynamic features now active:")
    print(f"  ✓ Temperature-dependent rates (arrhenius)")
    print(f"  ✓ ATP thermodynamic constraints (thermo_driving_force)")
    print(f"  ✓ pH-coupled transport")
    print(f"  ✓ Signal flow arcs for thermodynamic places")
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
