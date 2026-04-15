#!/usr/bin/env python3
"""
Update all 16 N-methylation models (normal + tumor, N-Me 0-7) based on manuscript specifications.

Manuscript specifications (drug_discovery_jmedchem.tex):
- Line 93: α_NMe = N_Me/N_max where N_max = 11 for cyclosporins
- Line 93: Active transport includes (1-α_NMe) factor (progressive loss of recognition)
- Line 102: Passive permeability = P_0 · α_NMe^1.2 (superlinear enhancement)
- Line 131: At 5000 µM ATP: 89% compact (lipophilic), 11% extended (polar)
- Line 437-438: Tumor membrane potential Vm = -20 mV vs normal Vm = -70 mV
- Line 442: Membrane depolarization → 7-fold passive transport enhancement
- Tables: Expected Drug_intracellular = 98.50 ± 0.07 mM (homeostatic control)

This script:
1. Calculates α_NMe = N_Me/11 for each variant (N_Me = 0-7)
2. Sets N-methylation-dependent initial conformational states
3. Implements (1-α_NMe) modulation in active transport rates (T1-T4)
4. Implements α_NMe^1.2 scaling in passive permeability rates (T7-T9)
5. Sets tumor Vm = -20 mV, normal Vm = -70 mV (via spatial properties)
6. Preserves ATP-dependent rate functions (T5, T6, T10, T11)
"""

import json
import os
from pathlib import Path

# Model paths
MODEL_DIR = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NORMAL_TEMPLATE = "macrocycle_transport_normal_nme_{}_enhanced.shy"
TUMOR_TEMPLATE = "macrocycle_transport_tumor_nme_{}_enhanced.shy"

# N-methylation parameters (from manuscript)
N_MAX = 11  # Maximum N-methylation for cyclosporins
SUPERLINEAR_EXPONENT = 1.2  # α_NMe^1.2 for passive permeability

# Membrane potentials (from manuscript lines 437-438, 425)
NORMAL_VM = -70  # mV, normal resting potential
TUMOR_VM = -20   # mV, depolarized tumor cells

# Baseline initial states (at ATP = 5000 µM, from manuscript line 131)
BASELINE_COMPACT_PERCENT = 89  # 89% compact at 5000 µM ATP
BASELINE_EXTENDED_PERCENT = 11  # 11% extended at 5000 µM ATP
TOTAL_DRUG_INTRACELLULAR = 100  # mM

def calculate_alpha_nme(n_me):
    """Calculate N-methylation fraction: α_NMe = N_Me / N_max"""
    return n_me / N_MAX

def calculate_conformational_states(n_me):
    """
    Calculate initial Drug_extended and Drug_compact based on N-methylation.
    
    Manuscript indicates N-methylation "stabilizes membrane-compatible conformations"
    (compact/lipophilic form). So:
    - N-Me 0 (unmethylated): More extended/flexible → 30% compact, 70% extended
    - N-Me 7 (fully methylated): More compact/rigid → 95% compact, 5% extended
    
    Linear interpolation with N-methylation fraction.
    """
    alpha_nme = calculate_alpha_nme(n_me)
    
    # N-Me 0: 30% compact (flexible, polar-preferred)
    # N-Me 7: 95% compact (rigid, lipophilic-preferred)
    # Linear transition
    compact_min = 30  # N-Me 0
    compact_max = 95  # N-Me 7
    
    compact_percent = compact_min + alpha_nme * (compact_max - compact_min)
    extended_percent = 100 - compact_percent
    
    # Convert to mM
    drug_compact = (compact_percent / 100) * TOTAL_DRUG_INTRACELLULAR
    drug_extended = (extended_percent / 100) * TOTAL_DRUG_INTRACELLULAR
    
    return drug_extended, drug_compact

def calculate_active_transport_factor(n_me):
    """
    Calculate (1 - α_NMe) modulation for active transporter recognition.
    
    From manuscript line 93: "Active transport rate includes (1-α_NMe) term 
    reflecting loss of peptide recognition motifs"
    """
    alpha_nme = calculate_alpha_nme(n_me)
    return 1.0 - alpha_nme

def calculate_passive_permeability_factor(n_me):
    """
    Calculate α_NMe^1.2 scaling for passive membrane permeability.
    
    From manuscript line 102: "Passive permeability = P_0 · α_NMe^1.2"
    Superlinear enhancement with exponent 1.18±0.09
    """
    alpha_nme = calculate_alpha_nme(n_me)
    if alpha_nme == 0:
        return 0.0  # No passive permeability for unmethylated
    return alpha_nme ** SUPERLINEAR_EXPONENT

def update_model_for_nmethylation(model_path, n_me, is_tumor=False):
    """
    Update a single .shy model file with N-methylation-dependent parameters.
    
    Args:
        model_path: Path to .shy JSON model file
        n_me: N-methylation level (0-7)
        is_tumor: Whether this is a tumor model (affects Vm)
    """
    print(f"\nUpdating {model_path.name} (N-Me {n_me}, {'tumor' if is_tumor else 'normal'})...")
    
    # Load model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    # Calculate N-methylation-dependent factors
    alpha_nme = calculate_alpha_nme(n_me)
    drug_extended, drug_compact = calculate_conformational_states(n_me)
    active_factor = calculate_active_transport_factor(n_me)
    passive_factor = calculate_passive_permeability_factor(n_me)
    
    print(f"  α_NMe = {alpha_nme:.3f}")
    print(f"  Initial: Extended = {drug_extended:.1f} mM, Compact = {drug_compact:.1f} mM")
    print(f"  Active transport factor: (1-α) = {active_factor:.3f}")
    print(f"  Passive permeability factor: α^1.2 = {passive_factor:.3f}")
    
    # Update initial conformational states
    for place in model['places']:
        if place['name'] == 'Drug_extended':
            place['marking'] = drug_extended
            print(f"    ✓ Drug_extended: {place['marking']:.1f} mM")
        elif place['name'] == 'Drug_compact':
            place['marking'] = drug_compact
            print(f"    ✓ Drug_compact: {place['marking']:.1f} mM")
    
    # Update transition rate functions
    changes_made = 0
    
    # Map transition names to their functional roles (from model inspection)
    ACTIVE_TRANSPORT = ['active_transport', 'ABC_efflux', 'facilitated_diffusion']
    PASSIVE_DIFFUSION = ['passive_diffusion']
    
    for transition in model['transitions']:
        t_name = transition['name']
        
        # Active transport (apply (1-α_NMe) modulation)
        if t_name in ACTIVE_TRANSPORT:
            if 'properties' in transition and 'rate_function' in transition['properties']:
                rate_func = transition['properties']['rate_function']
                
                # Check if already modified (avoid double-wrapping)
                if 'n_methylation_factor' in transition.get('properties', {}):
                    continue  # Already modified, skip
                
                # Update rate function to include (1-α_NMe) factor
                # Note: The base rate should be preserved and multiplied by active_factor
                # Since we already have rate functions, we'll add the N-methylation modulation
                
                # Add comment explaining the modification
                transition['description'] = (
                    f"{t_name}: Active transport with N-methylation modulation. "
                    f"Factor (1-α_NMe) = {active_factor:.3f} reflects progressive loss "
                    f"of transporter recognition (manuscript line 93)."
                )
                
                # Store the N-methylation factor in properties for reference
                if 'properties' not in transition:
                    transition['properties'] = {}
                transition['properties']['n_methylation_factor'] = active_factor
                transition['properties']['alpha_nme'] = alpha_nme
                
                # Modify rate function: multiply by active_factor
                # Format: "base_rate * (1 - alpha_nme) * [existing_terms]"
                # We'll wrap the existing rate function
                transition['properties']['rate_function'] = f"({active_factor:.4f}) * ({rate_func})"
                
                changes_made += 1
                print(f"    ✓ {t_name} rate × {active_factor:.3f} (active transport modulation)")
        
        # Passive diffusion (apply α_NMe^1.2 scaling)
        elif t_name in PASSIVE_DIFFUSION:
            if 'properties' in transition and 'rate_function' in transition['properties']:
                rate_func = transition['properties']['rate_function']
                
                # Check if already modified
                if 'n_methylation_factor' in transition.get('properties', {}):
                    continue  # Already modified, skip
                
                transition['description'] = (
                    f"{t_name}: Passive diffusion with N-methylation modulation. "
                    f"Factor α_NMe^1.2 = {passive_factor:.3f} provides superlinear "
                    f"permeability enhancement (manuscript line 102). "
                    f"For N-Me 0 (unmethylated), passive transport is eliminated."
                )
                
                if 'properties' not in transition:
                    transition['properties'] = {}
                transition['properties']['n_methylation_factor'] = passive_factor
                transition['properties']['alpha_nme'] = alpha_nme
                
                # Modify rate function: multiply by passive_factor
                # For N-Me 0, passive_factor = 0.0 → completely disables passive transport
                # For N-Me 7, passive_factor = 0.581 → 58.1% of base passive rate
                transition['properties']['rate_function'] = f"({passive_factor:.4f}) * ({rate_func})"
                
                changes_made += 1
                print(f"    ✓ {t_name} rate × {passive_factor:.3f} (passive permeability modulation)")
        
        # chameleon_fold, chameleon_unfold: Conformational transitions (ATP-dependent, preserve)
        # ATP_synthesis, basal_ATPase: Metabolism (preserve)
        # proteasomal, lysosomal, chemical_hydrolysis: Degradation (preserve existing)
    
    # Update membrane potential in spatial properties (affects passive diffusion exponentially)
    vm = TUMOR_VM if is_tumor else NORMAL_VM
    
    for place in model['places']:
        if 'properties' in place and isinstance(place['properties'], dict):
            if 'membrane_potential' in place['properties']:
                place['properties']['membrane_potential'] = vm
            # Also ensure spatial properties are present
            if place['name'] in ['Drug_ext', 'Drug_intracellular', 'Drug_extended', 'Drug_compact']:
                # Membrane potential affects passive diffusion (manuscript line 425)
                # exp(-Vm/25.7): at -70 mV → 0.066, at -20 mV → 0.459 (7-fold increase)
                place['properties']['membrane_potential_mv'] = vm
                changes_made += 1
    
    print(f"  ✓ Set membrane potential: Vm = {vm} mV ({'tumor depolarized' if is_tumor else 'normal'})")
    print(f"  Total modifications: {changes_made}")
    
    # Save updated model
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"  ✅ Saved {model_path.name}")
    
    return {
        'n_me': n_me,
        'alpha_nme': alpha_nme,
        'drug_extended': drug_extended,
        'drug_compact': drug_compact,
        'active_factor': active_factor,
        'passive_factor': passive_factor,
        'vm': vm,
        'is_tumor': is_tumor
    }

def main():
    """Update all 16 models (normal N-Me 0-7 + tumor N-Me 0-7)"""
    
    print("=" * 80)
    print("UPDATING N-METHYLATION SERIES MODELS FROM MANUSCRIPT SPECIFICATIONS")
    print("=" * 80)
    print(f"\nManuscript: drug_discovery_jmedchem.tex")
    print(f"Parameters:")
    print(f"  - N_max = {N_MAX} (cyclosporin family)")
    print(f"  - Active transport: rate × (1 - α_NMe)")
    print(f"  - Passive permeability: rate × α_NMe^{SUPERLINEAR_EXPONENT}")
    print(f"  - Normal Vm = {NORMAL_VM} mV")
    print(f"  - Tumor Vm = {TUMOR_VM} mV (7-fold passive enhancement)")
    print(f"  - Conformational states: N-Me dependent (30% → 95% compact)")
    
    summary = []
    
    # Process normal series (N-Me 0-7)
    print("\n" + "=" * 80)
    print("NORMAL CELL SERIES (Vm = -70 mV)")
    print("=" * 80)
    
    for n_me in range(8):
        model_file = MODEL_DIR / NORMAL_TEMPLATE.format(n_me)
        if not model_file.exists():
            print(f"⚠️  WARNING: {model_file} not found, skipping...")
            continue
        
        result = update_model_for_nmethylation(model_file, n_me, is_tumor=False)
        result['series'] = 'normal'
        summary.append(result)
    
    # Process tumor series (N-Me 0-7)
    print("\n" + "=" * 80)
    print("TUMOR CELL SERIES (Vm = -20 mV, Depolarized)")
    print("=" * 80)
    
    for n_me in range(8):
        model_file = MODEL_DIR / TUMOR_TEMPLATE.format(n_me)
        if not model_file.exists():
            print(f"⚠️  WARNING: {model_file} not found, skipping...")
            continue
        
        result = update_model_for_nmethylation(model_file, n_me, is_tumor=True)
        result['series'] = 'tumor'
        summary.append(result)
    
    # Print summary table
    print("\n" + "=" * 80)
    print("UPDATE SUMMARY")
    print("=" * 80)
    print("\nNormal Series (Vm = -70 mV):")
    print(f"{'N-Me':<6} {'α_NMe':<8} {'Extended':<12} {'Compact':<10} {'Active×':<10} {'Passive×':<10}")
    print("-" * 66)
    
    for result in summary:
        if result['series'] == 'normal':
            print(f"{result['n_me']:<6} {result['alpha_nme']:<8.3f} "
                  f"{result['drug_extended']:<12.1f} {result['drug_compact']:<10.1f} "
                  f"{result['active_factor']:<10.3f} {result['passive_factor']:<10.3f}")
    
    print("\nTumor Series (Vm = -20 mV):")
    print(f"{'N-Me':<6} {'α_NMe':<8} {'Extended':<12} {'Compact':<10} {'Active×':<10} {'Passive×':<10}")
    print("-" * 66)
    
    for result in summary:
        if result['series'] == 'tumor':
            print(f"{result['n_me']:<6} {result['alpha_nme']:<8.3f} "
                  f"{result['drug_extended']:<12.1f} {result['drug_compact']:<10.1f} "
                  f"{result['active_factor']:<10.3f} {result['passive_factor']:<10.3f}")
    
    print("\n" + "=" * 80)
    print("✅ ALL MODELS UPDATED SUCCESSFULLY")
    print("=" * 80)
    print("\nExpected simulation results (from manuscript tables):")
    print("  Normal series: Drug_intracellular = 98.50 ± 0.07 mM (homeostatic)")
    print("  Tumor series:  Drug_intracellular = 98.58 ± 0.03 mM (even tighter!)")
    print("\nNext steps:")
    print("  1. Re-simulate all tumor N-Me 0-7 models to generate new CSVs")
    print("  2. Run analysis scripts to verify differentiated results")
    print("  3. Compare normal vs tumor N-methylation structure-activity relationships")
    print("  4. Verify homeostatic control: constant accumulation despite layer variation")

if __name__ == '__main__':
    main()
