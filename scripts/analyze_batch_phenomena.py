#!/usr/bin/env python3
"""
Comprehensive Batch Data Phenomena Analysis
Explores characteristic patterns in 70 chameleon cycle replicates across 7 doses

Author: Batch Analysis Pipeline
Date: February 14, 2026
"""

import csv
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import sys

# Batch result directories
BATCH_DIRS = [
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_201954",  # 1 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_204246",  # 5 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_211132",  # 10 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_213143",  # 50 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_214404",  # 100 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_233952",  # 500 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_232102",  # 1000 µM
]

DOSE_LABELS = ["1 µM", "5 µM", "10 µM", "50 µM", "100 µM", "500 µM", "1000 µM"]
DOSE_VALUES = [1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]


def parse_csv_file(filepath: Path) -> Dict:
    """Parse a batch CSV file and extract all data."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find data start
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith('time,'):
            header = line.strip().split(',')
            data_start = i + 1
            break
    
    # Parse data
    data = {col: [] for col in header}
    for line in lines[data_start:]:
        if line.strip():
            parts = line.strip().split(',')
            for col, val in zip(header, parts):
                try:
                    data[col].append(float(val))
                except ValueError:
                    data[col].append(val)
    
    # Convert to numpy arrays
    for col in data:
        if col != 'time' and len(data[col]) > 0:
            try:
                data[col] = np.array(data[col])
            except:
                pass
    
    data['time'] = np.array(data['time'])
    
    return data


def load_all_batch_data() -> Dict:
    """Load all 70 batch replicate CSVs."""
    print("Loading batch data...")
    all_data = {}
    
    for dose_label, batch_dir in zip(DOSE_LABELS, BATCH_DIRS):
        batch_path = Path(batch_dir)
        if not batch_path.exists():
            print(f"  ✗ {dose_label}: Directory not found: {batch_dir}")
            continue
        
        all_data[dose_label] = []
        for i in range(1, 11):  # 10 replicates
            csv_path = batch_path / f"run_{i:03d}.csv"
            if csv_path.exists():
                data = parse_csv_file(csv_path)
                all_data[dose_label].append(data)
            else:
                print(f"  ✗ {dose_label} run_{i:03d}: File not found")
        
        print(f"  ✓ {dose_label}: {len(all_data[dose_label])} replicates loaded")
    
    total_loaded = sum(len(reps) for reps in all_data.values())
    print(f"\nTotal: {total_loaded}/70 replicates loaded\n")
    
    return all_data


def analyze_trajectory_dynamics(all_data: Dict) -> Dict:
    """
    PHENOMENON 1: Trajectory Dynamics
    Do replicates follow different paths to similar endpoints?
    """
    print("=" * 70)
    print("PHENOMENON 1: TRAJECTORY DYNAMICS")
    print("=" * 70)
    
    results = {}
    
    for dose_label in DOSE_LABELS:
        if dose_label not in all_data or len(all_data[dose_label]) == 0:
            continue
        
        print(f"\n{dose_label}:")
        replicates = all_data[dose_label]
        
        # Extract T5+T6 trajectories (chameleon cycles over time)
        trajectories = []
        for rep in replicates:
            if 'T5' in rep and 'T6' in rep:
                cycles = rep['T5'] + rep['T6']
                trajectories.append(cycles)
        
        if len(trajectories) == 0:
            continue
        
        # Analyze trajectory characteristics
        final_values = [traj[-1] for traj in trajectories]
        
        # Time to half-maximum
        half_max_times = []
        for traj, rep in zip(trajectories, replicates):
            final = traj[-1]
            half_max = final / 2
            # Find first time exceeding half-max
            idx = np.where(traj >= half_max)[0]
            if len(idx) > 0:
                t_half = rep['time'][idx[0]]
                half_max_times.append(t_half)
        
        # Early rate (0-100s)
        early_rates = []
        for traj, rep in zip(trajectories, replicates):
            times = rep['time']
            early_idx = times <= 100
            if np.sum(early_idx) > 1:
                early_cycles = traj[early_idx]
                early_time = times[early_idx]
                if len(early_cycles) > 0 and early_cycles[-1] > 0:
                    rate = early_cycles[-1] / early_time[-1]  # cycles/s
                    early_rates.append(rate * 60)  # cycles/min
        
        # Late rate (last 500s)
        late_rates = []
        for traj, rep in zip(trajectories, replicates):
            times = rep['time']
            late_idx = times >= (times[-1] - 500)
            if np.sum(late_idx) > 1:
                late_cycles = traj[late_idx]
                late_time = times[late_idx]
                delta_cycles = late_cycles[-1] - late_cycles[0]
                delta_time = late_time[-1] - late_time[0]
                if delta_time > 0:
                    rate = delta_cycles / delta_time
                    late_rates.append(rate * 60)  # cycles/min
        
        print(f"  Final values: {np.mean(final_values):.1f} ± {np.std(final_values):.1f}")
        if len(half_max_times) > 0:
            print(f"  Time to half-max: {np.mean(half_max_times):.1f} ± {np.std(half_max_times):.1f} s")
        if len(early_rates) > 0:
            print(f"  Early rate (0-100s): {np.mean(early_rates):.2f} ± {np.std(early_rates):.2f} cycles/min")
        if len(late_rates) > 0:
            print(f"  Late rate (last 500s): {np.mean(late_rates):.2f} ± {np.std(late_rates):.2f} cycles/min")
        
        # Check for trajectory types
        fast_responders = sum(1 for t in half_max_times if t < np.median(half_max_times)) if len(half_max_times) > 0 else 0
        slow_responders = len(half_max_times) - fast_responders
        
        if len(half_max_times) > 0:
            print(f"  Fast responders: {fast_responders}/{len(half_max_times)}")
            print(f"  Slow responders: {slow_responders}/{len(half_max_times)}")
        
        results[dose_label] = {
            'final_mean': np.mean(final_values),
            'final_sd': np.std(final_values),
            'half_max_time_mean': np.mean(half_max_times) if len(half_max_times) > 0 else None,
            'early_rate_mean': np.mean(early_rates) if len(early_rates) > 0 else None,
            'late_rate_mean': np.mean(late_rates) if len(late_rates) > 0 else None,
        }
    
    return results


def analyze_transport_correlations(all_data: Dict) -> Dict:
    """
    PHENOMENON 2: Transport Mode Correlations
    Are there hidden relationships between transport mechanisms?
    """
    print("\n" + "=" * 70)
    print("PHENOMENON 2: TRANSPORT MODE CORRELATIONS")
    print("=" * 70)
    
    results = {}
    
    for dose_label in DOSE_LABELS:
        if dose_label not in all_data or len(all_data[dose_label]) == 0:
            continue
        
        print(f"\n{dose_label}:")
        replicates = all_data[dose_label]
        
        # Extract final transport mode counts
        active = []
        facilitated = []
        efflux = []
        cycles = []
        
        for rep in replicates:
            if 'T1' in rep and 'T3' in rep and 'T2' in rep and 'T5' in rep and 'T6' in rep:
                active.append(rep['T1'][-1])
                facilitated.append(rep['T3'][-1])
                efflux.append(rep['T2'][-1])
                cycles.append(rep['T5'][-1] + rep['T6'][-1])
        
        if len(active) == 0:
            continue
        
        active = np.array(active)
        facilitated = np.array(facilitated)
        efflux = np.array(efflux)
        cycles = np.array(cycles)
        
        # Calculate correlations
        corr_active_cycles = np.corrcoef(active, cycles)[0, 1]
        corr_facilitated_cycles = np.corrcoef(facilitated, cycles)[0, 1]
        corr_efflux_cycles = np.corrcoef(efflux, cycles)[0, 1]
        corr_active_facilitated = np.corrcoef(active, facilitated)[0, 1]
        
        print(f"  Active ↔ Cycles:      r = {corr_active_cycles:+.3f}")
        print(f"  Facilitated ↔ Cycles: r = {corr_facilitated_cycles:+.3f}")
        print(f"  Efflux ↔ Cycles:      r = {corr_efflux_cycles:+.3f}")
        print(f"  Active ↔ Facilitated: r = {corr_active_facilitated:+.3f}")
        
        # Identify strong correlations (|r| > 0.5)
        strong = []
        if abs(corr_active_cycles) > 0.5:
            strong.append(f"Active-Cycles ({corr_active_cycles:+.2f})")
        if abs(corr_facilitated_cycles) > 0.5:
            strong.append(f"Facilitated-Cycles ({corr_facilitated_cycles:+.2f})")
        if abs(corr_efflux_cycles) > 0.5:
            strong.append(f"Efflux-Cycles ({corr_efflux_cycles:+.2f})")
        if abs(corr_active_facilitated) > 0.5:
            strong.append(f"Active-Facilitated ({corr_active_facilitated:+.2f})")
        
        if strong:
            print(f"  Strong correlations: {', '.join(strong)}")
        else:
            print(f"  No strong correlations (all |r| < 0.5)")
        
        results[dose_label] = {
            'active_cycles_corr': corr_active_cycles,
            'facilitated_cycles_corr': corr_facilitated_cycles,
            'efflux_cycles_corr': corr_efflux_cycles,
            'active_facilitated_corr': corr_active_facilitated,
        }
    
    return results


def analyze_metabolic_efficiency(all_data: Dict) -> Dict:
    """
    PHENOMENON 3: Metabolic Efficiency
    What's the ATP cost per chameleon cycle?
    """
    print("\n" + "=" * 70)
    print("PHENOMENON 3: METABOLIC EFFICIENCY")
    print("=" * 70)
    
    results = {}
    
    for dose_label in DOSE_LABELS:
        if dose_label not in all_data or len(all_data[dose_label]) == 0:
            continue
        
        print(f"\n{dose_label}:")
        replicates = all_data[dose_label]
        
        # Extract ATP synthesis and cycles
        atp_synthesis = []
        cycles = []
        active_transport = []
        
        for rep in replicates:
            if 'T12' in rep and 'T5' in rep and 'T6' in rep and 'T1' in rep:
                atp_syn = rep['T12'][-1]
                cyc = rep['T5'][-1] + rep['T6'][-1]
                act = rep['T1'][-1]
                
                if cyc > 0:  # Avoid division by zero
                    atp_synthesis.append(atp_syn)
                    cycles.append(cyc)
                    active_transport.append(act)
        
        if len(cycles) == 0:
            continue
        
        # Calculate efficiency metrics
        atp_per_cycle = np.array(atp_synthesis) / np.array(cycles)
        atp_per_active = np.array(atp_synthesis) / (np.array(active_transport) + 1e-6)
        
        print(f"  ATP synthesis: {np.mean(atp_synthesis):.0f} ± {np.std(atp_synthesis):.0f}")
        print(f"  Chameleon cycles: {np.mean(cycles):.0f} ± {np.std(cycles):.0f}")
        print(f"  ATP/cycle: {np.mean(atp_per_cycle):.2f} ± {np.std(atp_per_cycle):.2f}")
        print(f"  ATP/active_transport: {np.mean(atp_per_active):.2f} ± {np.std(atp_per_active):.2f}")
        
        # Check for efficiency correlation with cycles
        corr = np.corrcoef(cycles, atp_per_cycle)[0, 1]
        print(f"  Efficiency ↔ Cycles: r = {corr:+.3f}")
        
        if abs(corr) > 0.3:
            if corr > 0:
                print(f"  → High-cycle replicates are LESS efficient (need more ATP per cycle)")
            else:
                print(f"  → High-cycle replicates are MORE efficient (need less ATP per cycle)")
        else:
            print(f"  → Efficiency independent of cycle count")
        
        results[dose_label] = {
            'atp_synthesis_mean': np.mean(atp_synthesis),
            'atp_per_cycle_mean': np.mean(atp_per_cycle),
            'atp_per_cycle_std': np.std(atp_per_cycle),
            'efficiency_cycles_corr': corr,
        }
    
    return results


def analyze_transient_behavior(all_data: Dict) -> Dict:
    """
    PHENOMENON 4: Transient Behavior
    Are there lag phases, spikes, or adaptation patterns?
    """
    print("\n" + "=" * 70)
    print("PHENOMENON 4: TRANSIENT BEHAVIOR (Early vs Late)")
    print("=" * 70)
    
    results = {}
    
    for dose_label in DOSE_LABELS:
        if dose_label not in all_data or len(all_data[dose_label]) == 0:
            continue
        
        print(f"\n{dose_label}:")
        replicates = all_data[dose_label]
        
        # Analyze early (0-500s) vs late (1500-2000s) dynamics
        early_cycles = []
        late_cycles = []
        has_lag_phase = 0
        
        for rep in replicates:
            if 'T5' in rep and 'T6' in rep and 'time' in rep:
                times = rep['time']
                cycles = rep['T5'] + rep['T6']
                
                # Early period
                early_idx = times <= 500
                if np.sum(early_idx) > 0:
                    early_val = cycles[early_idx][-1]
                    early_cycles.append(early_val)
                
                # Late period
                late_idx = times >= 1500
                if np.sum(late_idx) > 0:
                    late_start = cycles[late_idx][0]
                    late_end = cycles[late_idx][-1]
                    late_delta = late_end - late_start
                    late_cycles.append(late_delta)
                
                # Detect lag phase (< 10 cycles in first 100s)
                lag_idx = times <= 100
                if np.sum(lag_idx) > 0:
                    lag_cycles = cycles[lag_idx][-1]
                    if lag_cycles < 10:
                        has_lag_phase += 1
        
        if len(early_cycles) > 0:
            print(f"  Early cycles (at 500s): {np.mean(early_cycles):.1f} ± {np.std(early_cycles):.1f}")
        if len(late_cycles) > 0:
            print(f"  Late activity (1500-2000s): {np.mean(late_cycles):.1f} ± {np.std(late_cycles):.1f} cycles added")
        
        print(f"  Lag phase detected: {has_lag_phase}/{len(replicates)} replicates")
        
        # Check if system is still active late
        if len(late_cycles) > 0:
            still_active = sum(1 for lc in late_cycles if lc > 10)
            print(f"  Still active in late phase: {still_active}/{len(late_cycles)}")
        
        results[dose_label] = {
            'early_cycles_mean': np.mean(early_cycles) if len(early_cycles) > 0 else None,
            'late_delta_mean': np.mean(late_cycles) if len(late_cycles) > 0 else None,
            'lag_phase_fraction': has_lag_phase / len(replicates) if len(replicates) > 0 else None,
        }
    
    return results


def analyze_rare_events(all_data: Dict) -> Dict:
    """
    PHENOMENON 5: Rare Event Patterns
    When/how do rare events (efflux, passive diffusion) occur?
    """
    print("\n" + "=" * 70)
    print("PHENOMENON 5: RARE EVENT PATTERNS")
    print("=" * 70)
    
    results = {}
    
    for dose_label in DOSE_LABELS:
        if dose_label not in all_data or len(all_data[dose_label]) == 0:
            continue
        
        print(f"\n{dose_label}:")
        replicates = all_data[dose_label]
        
        # Count event occurrences
        efflux_activated = 0
        passive_activated = 0
        high_efflux = 0  # > 5 events
        
        efflux_amounts = []
        passive_amounts = []
        
        for rep in replicates:
            if 'T2' in rep:  # ABC efflux
                efflux_val = rep['T2'][-1]
                if efflux_val > 0:
                    efflux_activated += 1
                if efflux_val > 5:
                    high_efflux += 1
                efflux_amounts.append(efflux_val)
            
            if 'T4' in rep:  # Passive diffusion
                passive_val = rep['T4'][-1]
                if passive_val > 0:
                    passive_activated += 1
                passive_amounts.append(passive_val)
        
        n_reps = len(replicates)
        
        print(f"  ABC Efflux (T2):")
        print(f"    Activated: {efflux_activated}/{n_reps} ({100*efflux_activated/n_reps:.0f}%)")
        if len(efflux_amounts) > 0:
            print(f"    Amount: {np.mean(efflux_amounts):.1f} ± {np.std(efflux_amounts):.1f} firings")
            print(f"    High activity (>5): {high_efflux}/{n_reps}")
        
        print(f"  Passive Diffusion (T4):")
        print(f"    Activated: {passive_activated}/{n_reps} ({100*passive_activated/n_reps:.0f}%)")
        if passive_activated > 0:
            active_amounts = [a for a in passive_amounts if a > 0]
            print(f"    Amount (when active): {np.mean(active_amounts):.1f} ± {np.std(active_amounts):.1f} firings")
        
        results[dose_label] = {
            'efflux_activation_rate': efflux_activated / n_reps if n_reps > 0 else 0,
            'passive_activation_rate': passive_activated / n_reps if n_reps > 0 else 0,
            'efflux_mean': np.mean(efflux_amounts) if len(efflux_amounts) > 0 else 0,
        }
    
    return results


def summarize_key_findings(all_results: Dict):
    """Generate summary of most interesting phenomena."""
    print("\n" + "=" * 70)
    print("KEY FINDINGS SUMMARY")
    print("=" * 70)
    
    print("\n1. TRAJECTORY DYNAMICS:")
    traj = all_results.get('trajectories', {})
    if traj:
        # Check if there's dose-dependence in response times
        half_max_times = [v['half_max_time_mean'] for v in traj.values() if v.get('half_max_time_mean') is not None]
        if len(half_max_times) > 1:
            cv = np.std(half_max_times) / np.mean(half_max_times)
            print(f"   - Time to half-max varies: {np.min(half_max_times):.0f}-{np.max(half_max_times):.0f}s (CV={cv*100:.1f}%)")
    
    print("\n2. TRANSPORT CORRELATIONS:")
    corrs = all_results.get('correlations', {})
    strong_correlations = []
    for dose, vals in corrs.items():
        for key, val in vals.items():
            if abs(val) > 0.5:
                strong_correlations.append(f"{dose}: {key} (r={val:.2f})")
    if strong_correlations:
        for sc in strong_correlations[:5]:  # Top 5
            print(f"   - {sc}")
    else:
        print(f"   - No strong correlations found at any dose")
    
    print("\n3. METABOLIC EFFICIENCY:")
    metab = all_results.get('metabolism', {})
    if metab:
        atp_per_cycle_vals = [v['atp_per_cycle_mean'] for v in metab.values() if 'atp_per_cycle_mean' in v]
        if len(atp_per_cycle_vals) > 0:
            print(f"   - ATP cost: {np.mean(atp_per_cycle_vals):.1f} ± {np.std(atp_per_cycle_vals):.1f} ATP/cycle")
            if np.std(atp_per_cycle_vals) / np.mean(atp_per_cycle_vals) < 0.2:
                print(f"   - Highly consistent across doses (CV < 20%)")
    
    print("\n4. TRANSIENT PATTERNS:")
    trans = all_results.get('transients', {})
    if trans:
        lag_fractions = [v['lag_phase_fraction'] for v in trans.values() if v.get('lag_phase_fraction') is not None]
        if len(lag_fractions) > 0:
            avg_lag = np.mean(lag_fractions)
            print(f"   - Lag phase frequency: {avg_lag*100:.0f}% of replicates")
    
    print("\n5. RARE EVENTS:")
    rare = all_results.get('rare_events', {})
    if rare:
        efflux_rates = [v['efflux_activation_rate'] for v in rare.values()]
        passive_rates = [v['passive_activation_rate'] for v in rare.values()]
        print(f"   - Efflux activation: {np.mean(efflux_rates)*100:.0f}% across all doses")
        print(f"   - Passive diffusion: {np.mean(passive_rates)*100:.0f}% across all doses")


def main():
    """Main analysis pipeline."""
    print("=" * 70)
    print("COMPREHENSIVE BATCH PHENOMENA ANALYSIS")
    print("Exploring 70 replicates across 7 doses")
    print("=" * 70)
    print()
    
    # Load all data
    all_data = load_all_batch_data()
    
    if not all_data:
        print("ERROR: No batch data loaded. Check directory paths.")
        sys.exit(1)
    
    # Run all analyses
    all_results = {}
    
    all_results['trajectories'] = analyze_trajectory_dynamics(all_data)
    all_results['correlations'] = analyze_transport_correlations(all_data)
    all_results['metabolism'] = analyze_metabolic_efficiency(all_data)
    all_results['transients'] = analyze_transient_behavior(all_data)
    all_results['rare_events'] = analyze_rare_events(all_data)
    
    # Summary
    summarize_key_findings(all_results)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nResults saved in dictionary structure for further exploration.")
    print("Next steps: Focus on most interesting phenomena for detailed visualization.")


if __name__ == "__main__":
    main()
