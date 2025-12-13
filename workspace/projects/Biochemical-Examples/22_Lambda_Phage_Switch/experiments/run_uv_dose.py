#!/usr/bin/env python3
"""
Experiment 2: UV-Dose Response Curve
Goal: Reproduce experimental UV-induced prophage induction rates
Expected: 18%/82%/98% induction for low/medium/high UV doses
"""

import sys
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add SHYpn to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from shypn.engine.simulation.tau_leaping.tau_leaping_engine import TauLeapingEngine
from shypn.core.document import Document


def load_model():
    """Load lambda phage model"""
    model_path = Path(__file__).parent.parent / "model.shy"
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    doc = Document()
    doc.load_from_dict(data)
    return doc


def setup_lysogenic_state(doc):
    """Initialize model in lysogenic state"""
    # Set initial marking to lysogenic state
    for place_id, place in doc.net_objects.items():
        if hasattr(place, 'marking'):
            if place.name == 'CI_Gene':
                place.marking = 1
            elif place.name == 'CI_Dimer':
                place.marking = 25  # High CI maintains lysogeny
            elif place.name == 'Lysogenic_State':
                place.marking = 1
            elif place.name == 'Energy_ATP':
                place.marking = 100.0
            elif place.name == 'RecA_Inactive':
                place.marking = 100.0
            elif place.name == 'DNA_Damage':
                place.marking = 0  # Will be set per experiment
            else:
                place.marking = 0


def run_uv_induction_simulation(doc, dna_damage, sim_time=300, epsilon=0.03, seed=None):
    """Run single UV-induction simulation"""
    setup_lysogenic_state(doc)
    
    # Add DNA damage (UV exposure)
    dna_damage_place = doc.get_place_by_name("DNA_Damage")
    dna_damage_place.marking = float(dna_damage)
    
    # Run tau-leaping simulation
    engine = TauLeapingEngine(doc, epsilon=epsilon)
    if seed is not None:
        np.random.seed(seed)
    
    time_points = []
    ci_values = []
    cro_values = []
    reca_active_values = []
    lytic_state_values = []
    
    t = 0
    while t < sim_time:
        # Record current state
        time_points.append(t)
        ci_values.append(doc.get_place_by_name("CI_Protein").marking)
        cro_values.append(doc.get_place_by_name("Cro_Protein").marking)
        reca_active_values.append(doc.get_place_by_name("RecA_Active").marking)
        lytic_state_values.append(doc.get_place_by_name("Lytic_Genes_Active").marking)
        
        # Take tau-leaping step
        tau = engine.select_tau_leap(epsilon)
        if tau == 0:
            break
        
        engine.execute_tau_leap(tau)
        t += tau
    
    # Determine if prophage was induced (switched to lytic)
    final_lytic = lytic_state_values[-1]
    final_ci = ci_values[-1]
    final_cro = cro_values[-1]
    
    induced = (final_lytic > 0.5) or (final_cro > 15 and final_ci < 5)
    
    # Find induction time (when lytic genes activated)
    induction_time = None
    for i, lytic in enumerate(lytic_state_values):
        if lytic > 0.5:
            induction_time = time_points[i]
            break
    
    return {
        'induced': induced,
        'induction_time': induction_time,
        'time': np.array(time_points),
        'ci': np.array(ci_values),
        'cro': np.array(cro_values),
        'reca_active': np.array(reca_active_values)
    }


def run_uv_dose_experiment(dna_damage_levels=None, n_per_dose=100, sim_time=300, epsilon=0.03):
    """Run UV-dose response experiment"""
    if dna_damage_levels is None:
        dna_damage_levels = [0, 1, 2, 3, 5, 7, 10]
    
    print(f"Running UV-dose response experiment...")
    print(f"DNA damage levels: {dna_damage_levels}")
    print(f"Simulations per dose: {n_per_dose}")
    print(f"Simulation time: {sim_time} units\n")
    
    doc = load_model()
    all_results = {}
    
    for damage in dna_damage_levels:
        print(f"Testing DNA damage = {damage} lesions...")
        results = []
        
        for i in range(n_per_dose):
            result = run_uv_induction_simulation(
                doc, dna_damage=damage, sim_time=sim_time, 
                epsilon=epsilon, seed=damage*1000 + i
            )
            results.append(result)
        
        induced_count = sum(1 for r in results if r['induced'])
        induction_rate = induced_count / n_per_dose * 100
        
        print(f"  Induction rate: {induced_count}/{n_per_dose} ({induction_rate:.1f}%)")
        
        all_results[damage] = {
            'results': results,
            'induction_rate': induction_rate,
            'induced_count': induced_count
        }
    
    return all_results


def analyze_results(all_results):
    """Analyze UV-dose response"""
    print("\n" + "="*60)
    print("UV-DOSE RESPONSE EXPERIMENT RESULTS")
    print("="*60)
    
    # Extract dose-response data
    doses = sorted(all_results.keys())
    induction_rates = [all_results[d]['induction_rate'] for d in doses]
    
    for dose, rate in zip(doses, induction_rates):
        print(f"DNA damage {dose:2d} lesions: {rate:5.1f}% induction")
    
    print("\n" + "="*60)
    print("VALIDATION AGAINST LITERATURE")
    print("="*60)
    print("Roberts & Roberts 1978:")
    print("  Low UV dose:    ~20% induction")
    print(f"  Model (1 lesion): {all_results[1]['induction_rate']:.1f}% induction")
    if 15 <= all_results[1]['induction_rate'] <= 25:
        print("  ✓ MATCH: Within experimental range\n")
    else:
        print("  ✗ MISMATCH: Outside experimental range\n")
    
    print("  Medium UV dose:  ~80% induction")
    print(f"  Model (5 lesions): {all_results[5]['induction_rate']:.1f}% induction")
    if 75 <= all_results[5]['induction_rate'] <= 85:
        print("  ✓ MATCH: Within experimental range\n")
    else:
        print("  ✗ MISMATCH: Outside experimental range\n")
    
    print("  High UV dose:    >95% induction")
    print(f"  Model (10 lesions): {all_results[10]['induction_rate']:.1f}% induction")
    if all_results[10]['induction_rate'] >= 95:
        print("  ✓ MATCH: Within experimental range")
    else:
        print("  ✗ MISMATCH: Outside experimental range")
    
    print("="*60 + "\n")
    
    return doses, induction_rates


def plot_results(all_results, doses, induction_rates, output_dir):
    """Generate Figure 3: UV-dose response curve"""
    fig = plt.figure(figsize=(12, 5))
    
    # Main plot: Dose-response curve
    ax1 = plt.subplot(1, 2, 1)
    
    # Model data (sigmoid fit)
    ax1.plot(doses, induction_rates, 'o-', color='blue', linewidth=2, 
             markersize=8, label='Model')
    
    # Experimental data points (Roberts 1978)
    exp_doses = [1, 5, 10]
    exp_rates = [20, 80, 95]
    exp_errors = [5, 5, 3]
    ax1.errorbar(exp_doses, exp_rates, yerr=exp_errors, fmt='s', 
                 color='red', markersize=8, capsize=5, capthick=2,
                 label='Roberts 1978')
    
    ax1.set_xlabel('DNA Damage (lesions)')
    ax1.set_ylabel('Prophage Induction Rate (%)')
    ax1.set_title('UV-Dose Response Curve')
    ax1.set_ylim([0, 105])
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Inset: RecA activation dynamics
    ax2 = plt.subplot(1, 2, 2)
    
    # Plot RecA activation for different doses
    selected_doses = [1, 5, 10]
    colors = ['green', 'orange', 'red']
    
    for dose, color in zip(selected_doses, colors):
        results = all_results[dose]['results']
        # Average over all simulations
        time = results[0]['time']
        reca_avg = np.mean([r['reca_active'] for r in results], axis=0)
        ax2.plot(time, reca_avg, color=color, linewidth=2, 
                label=f'{dose} lesions')
    
    ax2.set_xlabel('Time (simulation units)')
    ax2.set_ylabel('RecA Active (molecules)')
    ax2.set_title('RecA Activation Dynamics')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "figure3_uv_dose_response.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Figure saved: {output_path}")
    plt.close()


def main():
    """Run UV-dose experiment and generate results"""
    # Create output directory
    output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    # Run experiment
    all_results = run_uv_dose_experiment(
        dna_damage_levels=[0, 1, 2, 3, 5, 7, 10],
        n_per_dose=100,
        sim_time=300,
        epsilon=0.03
    )
    
    # Analyze results
    doses, induction_rates = analyze_results(all_results)
    
    # Plot results
    plot_results(all_results, doses, induction_rates, output_dir)
    
    # Save raw data
    data_path = output_dir / "uv_dose_results.json"
    serializable_data = {}
    for dose, data in all_results.items():
        serializable_data[str(dose)] = {
            'induction_rate': float(data['induction_rate']),
            'induced_count': int(data['induced_count'])
        }
    
    with open(data_path, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    print(f"✓ Raw data saved: {data_path}\n")


if __name__ == "__main__":
    main()
