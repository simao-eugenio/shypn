#!/usr/bin/env python3
"""Parameter exploration for MAPK cascade bistability and interesting dynamics.

This script systematically explores parameter space to find:
- Bistability (two stable steady states)
- Oscillations (limit cycles)
- Ultrasensitivity (sharp dose-response)
- Hysteresis (path-dependent behavior)

Key parameters for MAPK bistability:
1. Hill coefficients (cooperativity)
2. Phosphatase concentrations (competition)
3. Feedback strength (ERK → upstream)
4. ATP levels (energy stress)
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.api.model_manager import ModelManager
from shypn.simulator.simulator import Simulator


def run_simulation(model_path, duration=100.0, output_csv=None):
    """Run a single simulation and return final state."""
    manager = ModelManager()
    manager.load_from_file(model_path)
    
    simulator = Simulator(manager)
    simulator.simulate(duration=duration, max_steps=2000)
    
    if output_csv:
        simulator.save_results_csv(output_csv)
    
    # Return final concentrations
    results = simulator.results
    if not results:
        return None
    
    final_state = results[-1]
    return {place.name: final_state[place] for place in final_state}


def explore_hill_coefficients(model_path, output_dir):
    """Explore Hill coefficient space for bistability.
    
    High Hill coefficients (n > 4) can create ultrasensitivity
    and bistability in cascades with feedback.
    """
    print("=" * 60)
    print("EXPLORING HILL COEFFICIENTS")
    print("=" * 60)
    
    # Load base model
    manager = ModelManager()
    manager.load_from_file(model_path)
    
    # Hill coefficient ranges
    n_pp2a_range = [1, 2, 3, 4, 6, 8]  # PP2A inhibition cooperativity
    n_mkp_range = [1, 2, 3, 4, 6, 8]   # MKP inhibition cooperativity
    
    results = []
    
    for n_pp2a in n_pp2a_range:
        for n_mkp in n_mkp_range:
            print(f"\nTesting: n_PP2A={n_pp2a}, n_MKP={n_mkp}")
            
            # Modify Hill coefficients in transition rates
            # Find transitions with Hill terms
            for trans in manager.document.transitions:
                if hasattr(trans, 'rate_formula') and trans.rate_formula:
                    formula = trans.rate_formula
                    
                    # Replace PP2A Hill coefficient
                    if 'PP2A' in formula and '**' in formula:
                        # Pattern: PP2A**n / (Ki**n + PP2A**n)
                        import re
                        formula = re.sub(
                            r'PP2A\*\*\d+',
                            f'PP2A**{n_pp2a}',
                            formula
                        )
                        formula = re.sub(
                            r'(Ki_PP2A\*\*)\d+',
                            rf'\g<1>{n_pp2a}',
                            formula
                        )
                    
                    # Replace MKP Hill coefficient
                    if 'MKP' in formula and '**' in formula:
                        formula = re.sub(
                            r'MKP\*\*\d+',
                            f'MKP**{n_mkp}',
                            formula
                        )
                        formula = re.sub(
                            r'(Ki_MKP\*\*)\d+',
                            rf'\g<1>{n_mkp}',
                            formula
                        )
                    
                    trans.rate_formula = formula
            
            # Run simulation
            simulator = Simulator(manager)
            simulator.simulate(duration=200.0, max_steps=3000)
            
            if not simulator.results:
                continue
            
            # Analyze final state
            final = simulator.results[-1]
            erk_pp = final.get(manager.document.get_place_by_name('ERK-PP'), 0)
            atp = final.get(manager.document.get_place_by_name('ATP'), 0)
            
            # Check for oscillations (variance in last 50s)
            t_cutoff = 150.0
            late_results = [r for t, r in zip(simulator.times, simulator.results) if t > t_cutoff]
            
            if len(late_results) > 10:
                erk_vals = [r.get(manager.document.get_place_by_name('ERK-PP'), 0) 
                           for r in late_results]
                erk_variance = np.var(erk_vals)
                erk_mean = np.mean(erk_vals)
                oscillation_score = erk_variance / (erk_mean + 1e-6)
            else:
                oscillation_score = 0.0
            
            result = {
                'n_PP2A': n_pp2a,
                'n_MKP': n_mkp,
                'ERK_PP_final': erk_pp,
                'ATP_final': atp,
                'oscillation_score': oscillation_score
            }
            results.append(result)
            
            print(f"  ERK-PP: {erk_pp:.1f} mM")
            print(f"  Oscillation score: {oscillation_score:.4f}")
            
            # Save if interesting
            if oscillation_score > 0.01 or erk_pp > 500:
                csv_path = output_dir / f"hill_n{n_pp2a}_{n_mkp}.csv"
                simulator.save_results_csv(str(csv_path))
                print(f"  → Saved interesting dynamics to {csv_path.name}")
    
    return results


def explore_phosphatase_competition(model_path, output_dir):
    """Explore phosphatase concentration ratios.
    
    Low phosphatase/kinase ratios create competition that can
    lead to bistability through zero-order ultrasensitivity.
    """
    print("\n" + "=" * 60)
    print("EXPLORING PHOSPHATASE COMPETITION")
    print("=" * 60)
    
    manager = ModelManager()
    manager.load_from_file(model_path)
    
    # Phosphatase ratios (fraction of normal)
    pp2a_ratios = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    mkp_ratios = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    
    results = []
    
    base_pp2a = 50.0  # mM
    base_mkp = 50.0   # mM
    
    for pp2a_ratio in pp2a_ratios:
        for mkp_ratio in mkp_ratios:
            print(f"\nTesting: PP2A={pp2a_ratio:.2f}x, MKP={mkp_ratio:.2f}x")
            
            # Set initial concentrations
            pp2a_place = manager.document.get_place_by_name('PP2A')
            mkp_place = manager.document.get_place_by_name('MKP')
            
            if pp2a_place:
                pp2a_place.tokens = base_pp2a * pp2a_ratio
            if mkp_place:
                mkp_place.tokens = base_mkp * mkp_ratio
            
            # Run simulation
            simulator = Simulator(manager)
            simulator.simulate(duration=200.0, max_steps=3000)
            
            if not simulator.results:
                continue
            
            final = simulator.results[-1]
            raf_active = final.get(manager.document.get_place_by_name('Raf_Active'), 0)
            mek_pp = final.get(manager.document.get_place_by_name('MEK-PP'), 0)
            erk_pp = final.get(manager.document.get_place_by_name('ERK-PP'), 0)
            
            # Calculate cascade activation
            raf_fraction = raf_active / 1000.0 if raf_active else 0
            mek_fraction = mek_pp / 800.0 if mek_pp else 0
            erk_fraction = erk_pp / 600.0 if erk_pp else 0
            
            result = {
                'PP2A_ratio': pp2a_ratio,
                'MKP_ratio': mkp_ratio,
                'Raf_activation': raf_fraction,
                'MEK_activation': mek_fraction,
                'ERK_activation': erk_fraction,
                'cascade_product': raf_fraction * mek_fraction * erk_fraction
            }
            results.append(result)
            
            print(f"  Raf: {raf_fraction*100:.1f}%")
            print(f"  MEK: {mek_fraction*100:.1f}%")
            print(f"  ERK: {erk_fraction*100:.1f}%")
            
            # Save extreme activations
            if erk_fraction > 0.8 or erk_fraction < 0.1:
                csv_path = output_dir / f"phosphatase_{pp2a_ratio:.2f}_{mkp_ratio:.2f}.csv"
                simulator.save_results_csv(str(csv_path))
                print(f"  → Saved extreme activation to {csv_path.name}")
    
    return results


def explore_feedback_strength(model_path, output_dir):
    """Explore positive feedback strength.
    
    Strong ERK feedback to upstream components can create
    bistability through autocatalytic activation.
    """
    print("\n" + "=" * 60)
    print("EXPLORING FEEDBACK STRENGTH")
    print("=" * 60)
    
    manager = ModelManager()
    manager.load_from_file(model_path)
    
    # Check if model has feedback mechanisms
    # Look for ERK influencing upstream transitions
    feedback_transitions = []
    for trans in manager.document.transitions:
        if hasattr(trans, 'rate_formula') and trans.rate_formula:
            if 'ERK' in trans.rate_formula and ('Raf' in trans.name or 'MEK' in trans.name):
                feedback_transitions.append(trans)
    
    if not feedback_transitions:
        print("No feedback detected in model - skipping feedback exploration")
        print("Consider adding ERK → Raf or ERK → MEK positive feedback")
        return []
    
    print(f"Found {len(feedback_transitions)} feedback transitions")
    
    # Scale feedback terms
    feedback_scales = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
    results = []
    
    for scale in feedback_scales:
        print(f"\nTesting feedback scale: {scale:.1f}x")
        
        # Modify feedback strength
        for trans in feedback_transitions:
            # Store original formula
            if not hasattr(trans, '_original_formula'):
                trans._original_formula = trans.rate_formula
            
            # Scale ERK terms
            import re
            formula = trans._original_formula
            # Pattern: coefficient * ERK terms
            formula = re.sub(
                r'(\d+\.?\d*)\s*\*\s*(ERK[^*\s]*)',
                lambda m: f"{float(m.group(1)) * scale} * {m.group(2)}",
                formula
            )
            trans.rate_formula = formula
        
        # Run simulation
        simulator = Simulator(manager)
        simulator.simulate(duration=200.0, max_steps=3000)
        
        if not simulator.results:
            continue
        
        final = simulator.results[-1]
        erk_pp = final.get(manager.document.get_place_by_name('ERK-PP'), 0)
        raf_active = final.get(manager.document.get_place_by_name('Raf_Active'), 0)
        
        result = {
            'feedback_scale': scale,
            'ERK_PP_final': erk_pp,
            'Raf_Active_final': raf_active
        }
        results.append(result)
        
        print(f"  ERK-PP: {erk_pp:.1f} mM")
        print(f"  Raf-Active: {raf_active:.1f} mM")
        
        csv_path = output_dir / f"feedback_{scale:.1f}x.csv"
        simulator.save_results_csv(str(csv_path))
    
    return results


def hysteresis_analysis(model_path, output_dir):
    """Test for hysteresis by ramping Growth_Factor up and down.
    
    Hysteresis indicates bistability: different steady states
    depending on history (path dependence).
    """
    print("\n" + "=" * 60)
    print("HYSTERESIS ANALYSIS (Growth Factor Ramp)")
    print("=" * 60)
    
    # Ramp up: 0 → 200 mM
    gf_up = np.linspace(0, 200, 20)
    
    # Ramp down: 200 → 0 mM
    gf_down = np.linspace(200, 0, 20)
    
    erk_up = []
    erk_down = []
    
    print("\nRamping UP Growth_Factor...")
    last_state = None
    
    for gf in gf_up:
        manager = ModelManager()
        manager.load_from_file(model_path)
        
        # Set Growth_Factor
        gf_place = manager.document.get_place_by_name('Growth_Factor')
        if gf_place:
            gf_place.tokens = gf
        
        # Use previous steady state as initial condition
        if last_state:
            for place_name, tokens in last_state.items():
                place = manager.document.get_place_by_name(place_name)
                if place:
                    place.tokens = tokens
        
        # Run to steady state
        simulator = Simulator(manager)
        simulator.simulate(duration=100.0, max_steps=2000)
        
        if simulator.results:
            final = simulator.results[-1]
            erk_pp = final.get(manager.document.get_place_by_name('ERK-PP'), 0)
            erk_up.append(erk_pp)
            
            # Save state
            last_state = {place.name: final[place] for place in final}
            
            print(f"  GF={gf:6.1f} → ERK-PP={erk_pp:6.1f}")
        else:
            erk_up.append(0)
    
    print("\nRamping DOWN Growth_Factor...")
    
    for gf in gf_down:
        manager = ModelManager()
        manager.load_from_file(model_path)
        
        gf_place = manager.document.get_place_by_name('Growth_Factor')
        if gf_place:
            gf_place.tokens = gf
        
        if last_state:
            for place_name, tokens in last_state.items():
                place = manager.document.get_place_by_name(place_name)
                if place:
                    place.tokens = tokens
        
        simulator = Simulator(manager)
        simulator.simulate(duration=100.0, max_steps=2000)
        
        if simulator.results:
            final = simulator.results[-1]
            erk_pp = final.get(manager.document.get_place_by_name('ERK-PP'), 0)
            erk_down.append(erk_pp)
            
            last_state = {place.name: final[place] for place in final}
            
            print(f"  GF={gf:6.1f} → ERK-PP={erk_pp:6.1f}")
        else:
            erk_down.append(0)
    
    # Plot hysteresis
    plt.figure(figsize=(10, 6))
    plt.plot(gf_up, erk_up, 'b-o', label='Ramp UP', markersize=4)
    plt.plot(gf_down, erk_down, 'r-s', label='Ramp DOWN', markersize=4)
    plt.xlabel('Growth Factor (mM)')
    plt.ylabel('ERK-PP (mM)')
    plt.title('Hysteresis Test: Path-Dependent ERK Activation')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = output_dir / 'hysteresis.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n→ Hysteresis plot saved to {plot_path}")
    
    # Check for hysteresis
    max_difference = max(abs(np.array(erk_up[:len(erk_down)]) - np.array(erk_down)))
    print(f"\nMaximum hysteresis gap: {max_difference:.1f} mM")
    
    if max_difference > 50:
        print("✓ BISTABILITY DETECTED - significant hysteresis!")
    else:
        print("→ No significant hysteresis - monostable system")
    
    return {
        'gf_up': gf_up.tolist(),
        'erk_up': erk_up,
        'gf_down': gf_down.tolist(),
        'erk_down': erk_down,
        'max_hysteresis': float(max_difference)
    }


def main():
    """Run complete parameter exploration."""
    model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/mapk/models/erk_cascade_stress.shy"
    output_dir = Path("/home/simao/projetos/shypn/workspace/projects/My_Project/mapk/bistability_exploration")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("MAPK CASCADE BISTABILITY EXPLORATION")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Output: {output_dir}")
    print()
    
    # 1. Hill coefficients (ultrasensitivity)
    hill_results = explore_hill_coefficients(model_path, output_dir)
    
    # 2. Phosphatase competition (zero-order ultrasensitivity)
    phosphatase_results = explore_phosphatase_competition(model_path, output_dir)
    
    # 3. Feedback strength (autocatalytic bistability)
    feedback_results = explore_feedback_strength(model_path, output_dir)
    
    # 4. Hysteresis test (direct bistability evidence)
    hysteresis_results = hysteresis_analysis(model_path, output_dir)
    
    print("\n" + "=" * 60)
    print("EXPLORATION COMPLETE")
    print("=" * 60)
    print(f"Results saved to: {output_dir}")
    print("\nKey findings:")
    print(f"  - Hill coefficient tests: {len(hill_results)} parameter sets")
    print(f"  - Phosphatase competition: {len(phosphatase_results)} parameter sets")
    print(f"  - Feedback strength: {len(feedback_results)} parameter sets")
    print(f"  - Hysteresis gap: {hysteresis_results.get('max_hysteresis', 0):.1f} mM")
    
    # Recommendations
    print("\nRecommendations for bistability:")
    print("  1. Increase Hill coefficients (n ≥ 4) for ultrasensitivity")
    print("  2. Reduce phosphatase levels (0.2-0.5x) for competition")
    print("  3. Add/strengthen ERK → Raf positive feedback")
    print("  4. Look for parameter sets with hysteresis > 50 mM")


if __name__ == '__main__':
    main()
