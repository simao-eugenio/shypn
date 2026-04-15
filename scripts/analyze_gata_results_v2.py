#!/usr/bin/env python3
"""Analyze GATA1/PU1 factorial experiment results - Version 2.

This script analyzes the complete set of EPO×GCSF dose-response experiments,
focusing on cell fate commitment, energy balance, and bistability emergence.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

# Results directory
RESULTS_DIR = Path("workspace/projects/gata/experiments/results")

def parse_experiment_name(name):
    """Extract EPO and GCSF concentrations from experiment name.
    
    Args:
        name: Experiment directory name (e.g., 'experiment_EPO_external=10_GCSF_external=50_20260216_175656')
        
    Returns:
        tuple: (EPO_µM, GCSF_µM) or (None, None) if cannot parse
    """
    match = re.search(r'EPO_external=(\d+)_GCSF_external=(\d+)', name)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def analyze_metadata(metadata_path):
    """Extract key validation flags and parameters from metadata header.
    
    Args:
        metadata_path: Path to metadata.txt file
        
    Returns:
        dict: Metadata summary with validation flags and parameters
    """
    result = {
        'duration_min': None,
        'n_replicates': None,
        'atp_depleted': False,
        'min_atp': None,
        'execution_time_s': None,
        'homeostasis': False
    }
    
    try:
        with open(metadata_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Time span
                if line.startswith('Time_Span:'):
                    match = re.search(r'0-(\d+)', line)
                    if match:
                        result['duration_min'] = int(match.group(1))
                
                # Replicates
                elif line.startswith('N_Replicates:'):
                    match = re.search(r'N_Replicates:\s*(\d+)', line)
                    if match:
                        result['n_replicates'] = int(match.group(1))
                
                # Energy depletion - check for ATP < 100
                elif line.startswith('Energy_Depletion_Warning:'):
                    if 'YES' in line:
                        result['atp_depleted'] = True
                        # Extract minimum ATP
                        match = re.search(r'Minimum:\s*([0-9.]+)', line)
                        if match:
                            min_val = float(match.group(1))
                            result['min_atp'] = min_val
                            # Only consider it true depletion if < 100 µM
                            if min_val >= 100:
                                result['atp_depleted'] = False
                
                # Execution time
                elif 'Elapsed_Time:' in line:
                    match = re.search(r'Elapsed_Time:\s*([0-9.]+)', line)
                    if match:
                        result['execution_time_s'] = float(match.group(1))
                
                # Homeostasis
                elif line.startswith('Homeostasis_Detected:'):
                    if 'True' in line:
                        result['homeostasis'] = True
                
                # Stop at data section
                elif 'DATA SECTION BEGINS' in line:
                    break
    
    except Exception as e:
        print(f"Warning: Could not parse metadata: {e}")
    
    return result

def analyze_statistics(stats_path):
    """Analyze statistics.json for cell fate and balance metrics.
    
    Args:
        stats_path: Path to statistics.json file
        
    Returns:
        dict: Statistics summary with cell fate and balance metrics
    """
    result = {
        'gata1_final_mean': None,
        'pu1_final_mean': None,
        'gata1_pu1_ratio': None,
        'commitment': None,  # 'GATA1', 'PU1', 'Balanced', or 'Unknown'
        'atp_final_mean': None,
        'atp_min_mean': None,
        'duration_actual_min': None,
        'receptor_conserved': None,
        'energy_conserved': None
    }
    
    try:
        with open(stats_path, 'r') as f:
            data = json.load(f)
        
        # Get species statistics (new format)
        sp_stats = data.get('species_statistics', {})
        time_points = data.get('time_points', [])
        
        if not sp_stats or not time_points:
            return result
        
        # Get actual duration from time_points
        if time_points:
            result['duration_actual_min'] = time_points[-1]
        
        # GATA1 nuclear protein (P17)
        if 'P17' in sp_stats and sp_stats['P17'].get('mean'):
            result['gata1_final_mean'] = sp_stats['P17']['mean'][-1]
        
        # PU1 nuclear protein (P18)
        if 'P18' in sp_stats and sp_stats['P18'].get('mean'):
            result['pu1_final_mean'] = sp_stats['P18']['mean'][-1]
        
        # Calculate GATA1/PU1 ratio
        if result['gata1_final_mean'] is not None and result['pu1_final_mean'] is not None:
            if result['pu1_final_mean'] > 0.1:  # Avoid division by near-zero
                result['gata1_pu1_ratio'] = result['gata1_final_mean'] / result['pu1_final_mean']
            else:
                result['gata1_pu1_ratio'] = float('inf') if result['gata1_final_mean'] > 1 else 0
            
            # Classify commitment
            if result['gata1_pu1_ratio'] > 2.0:
                result['commitment'] = 'GATA1'
            elif result['gata1_pu1_ratio'] < 0.5:
                result['commitment'] = 'PU1'
            else:
                result['commitment'] = 'Balanced'
        
        # ATP final and minimum
        if 'P19' in sp_stats and sp_stats['P19'].get('mean'):
            atp_means = sp_stats['P19']['mean']
            result['atp_final_mean'] = atp_means[-1]
            result['atp_min_mean'] = min(atp_means)
        
        # Check receptor conservation (EPO receptors: P3, P4, P5)
        if all(k in sp_stats for k in ['P3', 'P4', 'P5']):
            epor_total = (sp_stats['P3']['mean'][-1] + 
                          sp_stats['P4']['mean'][-1] + 
                          sp_stats['P5']['mean'][-1])
            # Initial total should be 1000 µM
            result['receptor_conserved'] = abs(epor_total - 1000) < 10
        
        # Check energy conservation (adenylates: P19=ATP, P20=ADP)
        if all(k in sp_stats for k in ['P19', 'P20']):
            adenylate_total = (sp_stats['P19']['mean'][-1] + 
                               sp_stats['P20']['mean'][-1])
            # Initial total should be 3300 µM (3000 ATP + 300 ADP)
            result['energy_conserved'] = abs(adenylate_total - 3300) < 100
    
    except Exception as e:
        print(f"Warning: Could not parse statistics: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def format_time(seconds):
    """Format seconds as human-readable time."""
    if seconds is None:
        return "N/A"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def main():
    """Main analysis routine."""
    print("=" * 80)
    print("GATA1/PU1 FACTORIAL EXPERIMENT ANALYSIS (Version 2)")
    print("=" * 80)
    print()
    
    # Collect all experiment directories
    experiment_dirs = sorted([d for d in RESULTS_DIR.iterdir() if d.is_dir()])
    
    if not experiment_dirs:
        print("Error: No experiment directories found in results/")
        return
    
    print(f"Found {len(experiment_dirs)} experiments\n")
    
    # Analysis results grouped by outcome
    experiments = []
    
    # Process each experiment
    for exp_dir in experiment_dirs:
        epo, gcsf = parse_experiment_name(exp_dir.name)
        if epo is None or gcsf is None:
            print(f"Warning: Could not parse experiment name: {exp_dir.name}")
            continue
        
        # Load metadata
        metadata_path = exp_dir / "metadata.txt"
        config_path = exp_dir / "config.json"
        stats_path = exp_dir / "statistics.json"
        
        if not metadata_path.exists() or not stats_path.exists():
            print(f"Warning: Missing files in {exp_dir.name}")
            continue
        
        # Parse config for actual replicate count
        actual_replicates = None
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                actual_replicates = config.get('n_replicates')
        
        metadata = analyze_metadata(metadata_path)
        stats = analyze_statistics(stats_path)
        
        # Override replicate count from config if available
        if actual_replicates is not None:
            metadata['n_replicates'] = actual_replicates
        
        # Use actual duration from statistics if metadata doesn't have it
        if metadata['duration_min'] is None and stats['duration_actual_min'] is not None:
            metadata['duration_min'] = int(stats['duration_actual_min'])
        
        # Copy ATP min from stats to metadata if not set
        if metadata['min_atp'] is None and stats['atp_min_mean'] is not None:
            metadata['min_atp'] = stats['atp_min_mean']
            # Check for depletion (< 100 µM threshold)
            if stats['atp_min_mean'] < 100:
                metadata['atp_depleted'] = True
        
        experiments.append({
            'epo': epo,
            'gcsf': gcsf,
            'name': exp_dir.name,
            'metadata': metadata,
            'stats': stats
        })
    
    # Sort by EPO then GCSF
    experiments.sort(key=lambda x: (x['epo'], x['gcsf']))
    
    # === SUMMARY TABLE ===
    print("EXPERIMENT SUMMARY")
    print("-" * 80)
    print(f"{'EPO':>4} {'GCSF':>4} | {'Reps':>4} {'Duration':>8} {'ExecTime':>10} | {'Commitment':>10} {'GATA1/PU1':>10} | {'ATP Depl':>8}")
    print("-" * 80)
    
    for exp in experiments:
        epo = exp['epo']
        gcsf = exp['gcsf']
        meta = exp['metadata']
        stats = exp['stats']
        
        # Format values
        reps_str = str(meta['n_replicates']) if meta['n_replicates'] else "?"
        duration_str = f"{meta['duration_min']}min" if meta['duration_min'] else "?"
        exec_time_str = format_time(meta['execution_time_s'])
        commitment_str = stats['commitment'] if stats['commitment'] else "Unknown"
        
        # GATA1/PU1 ratio
        if stats['gata1_pu1_ratio'] is not None:
            if stats['gata1_pu1_ratio'] == float('inf'):
                ratio_str = ">100"
            else:
                ratio_str = f"{stats['gata1_pu1_ratio']:.2f}"
        else:
            ratio_str = "N/A"
        
        # ATP depletion
        atp_depl_str = "YES" if meta['atp_depleted'] else "NO"
        if meta['min_atp'] is not None:
            atp_depl_str += f" ({meta['min_atp']:.1f})"
        
        print(f"{epo:>4} {gcsf:>4} | {reps_str:>4} {duration_str:>8} {exec_time_str:>10} | {commitment_str:>10} {ratio_str:>10} | {atp_depl_str:>8}")
    
    print()
    
    # === CELL FATE ANALYSIS ===
    print("CELL FATE COMMITMENT ANALYSIS")
    print("-" * 80)
    
    commitment_counts = defaultdict(int)
    for exp in experiments:
        commitment = exp['stats']['commitment']
        if commitment:
            commitment_counts[commitment] += 1
    
    print(f"Total experiments analyzed: {len(experiments)}")
    print(f"  - GATA1-committed (ratio > 2.0): {commitment_counts['GATA1']}")
    print(f"  - PU1-committed (ratio < 0.5):   {commitment_counts['PU1']}")
    print(f"  - Balanced (0.5 ≤ ratio ≤ 2.0):  {commitment_counts['Balanced']}")
    print(f"  - Unknown:                        {commitment_counts['Unknown']}")
    print()
    
    if commitment_counts['GATA1'] > 0 or commitment_counts['PU1'] > 0:
        print("✓ Cell fate commitment OBSERVED in some conditions")
    else:
        print("✗ No clear cell fate commitment (all balanced)")
    print()
    
    # === ENERGY DEPLETION ANALYSIS ===
    print("ENERGY BALANCE ANALYSIS")
    print("-" * 80)
    
    depleted_count = sum(1 for exp in experiments if exp['metadata']['atp_depleted'])
    
    print(f"ATP depletion events: {depleted_count}/{len(experiments)}")
    
    if depleted_count > 0:
        print(f"\nExperiments with ATP depletion:")
        for exp in experiments:
            if exp['metadata']['atp_depleted']:
                min_atp = exp['metadata']['min_atp']
                atp_final = exp['stats']['atp_final_mean']
                print(f"  - EPO={exp['epo']:3d}, GCSF={exp['gcsf']:3d}: "
                      f"min ATP = {min_atp:.2f} µM, "
                      f"final ATP = {atp_final:.2f} µM" if atp_final else f"min ATP = {min_atp:.2f} µM")
    else:
        print("✓ No ATP depletion - all experiments maintained energy balance")
    
    print()
    
    # === CONSERVATION LAWS ===
    print("CONSERVATION LAW VALIDATION")
    print("-" * 80)
    
    receptor_ok = sum(1 for exp in experiments if exp['stats']['receptor_conserved'])
    energy_ok = sum(1 for exp in experiments if exp['stats']['energy_conserved'])
    
    print(f"Receptor conservation (EPOR): {receptor_ok}/{len(experiments)} experiments")
    print(f"Energy conservation (ATP+ADP): {energy_ok}/{len(experiments)} experiments")
    
    if receptor_ok < len(experiments) or energy_ok < len(experiments):
        print("\n⚠️  Warning: Some experiments show conservation violations")
    else:
        print("\n✓ All conservation laws satisfied")
    
    print()
    
    # === EXECUTION PERFORMANCE ===
    print("EXECUTION PERFORMANCE")
    print("-" * 80)
    
    total_time = sum(exp['metadata']['execution_time_s'] for exp in experiments if exp['metadata']['execution_time_s'])
    avg_time = total_time / len(experiments) if len(experiments) > 0 else 0
    
    # Get configuration from first experiment
    first_exp = experiments[0]
    duration_min = first_exp['metadata']['duration_min']
    n_replicates = first_exp['metadata']['n_replicates']
    
    print(f"Configuration: {n_replicates} replicates × {duration_min} min duration")
    print(f"Total execution time: {format_time(total_time)}")
    print(f"Average per experiment: {format_time(avg_time)}")
    
    # Only show simulated time if we have valid duration and replicates
    if duration_min and n_replicates:
        total_sim_min = len(experiments) * n_replicates * duration_min
        print(f"Total simulated time: {total_sim_min} experiment-minutes")
    print()
    
    # Calculate efficiency if we have all needed data
    if duration_min and n_replicates and total_time > 0:
        simulated_time_s = duration_min * 60  # Convert minutes to seconds
        total_simulated_s = len(experiments) * n_replicates * simulated_time_s
        efficiency = total_simulated_s / total_time
        print(f"Simulation efficiency: {efficiency:.3f}× real-time")
        print(f"  (1 simulated second = {1/efficiency:.3f} wall-clock seconds)")
    
    print()
    
    # === KEY FINDINGS ===
    print("KEY FINDINGS")
    print("=" * 80)
    
    # Duration comparison
    if duration_min:
        if duration_min == 60:
            print("1. Duration: 60 minutes - SHORT TIMESCALE")
            print("   → May be insufficient for cell fate commitment to emerge")
        elif duration_min == 120:
            print("1. Duration: 120 minutes - MEDIUM TIMESCALE")
            print("   → Sufficient for some commitment dynamics")
        else:
            print(f"1. Duration: {duration_min} minutes")
    
    # Replicate count
    if n_replicates:
        print(f"2. Replicates: {n_replicates} per experiment")
        if n_replicates < 5:
            print("   → Low replicate count may not capture stochastic variability")
        elif n_replicates >= 10:
            print("   → Good statistical power for detecting variability")
    
    # Cell fate
    print(f"3. Cell fate commitment:")
    if commitment_counts['GATA1'] > 0 or commitment_counts['PU1'] > 0:
        print(f"   ✓ OBSERVED: {commitment_counts['GATA1']} GATA1, {commitment_counts['PU1']} PU1")
    else:
        print("   ✗ NOT OBSERVED: All experiments show balanced GATA1/PU1")
        print("   → Recommendation: Increase duration to 240-480 min")
    
    # Energy depletion
    print(f"4. ATP depletion: {'YES' if depleted_count > 0 else 'NO'}")
    if depleted_count > 0:
        print(f"   ⚠️  WARNING: {depleted_count} experiments depleted ATP")
        print("   → This indicates model issues or extreme conditions")
    else:
        print("   ✓ Energy balance maintained in all experiments")
    
    print()
    print("=" * 80)
    print("Analysis complete.")
    print("=" * 80)

if __name__ == "__main__":
    main()
