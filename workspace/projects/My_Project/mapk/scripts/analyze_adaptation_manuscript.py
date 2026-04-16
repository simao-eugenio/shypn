#!/usr/bin/env python3
"""
Analyze adaptation against manuscript criteria:
1. Adaptation > 90%: [ERK_peak - ERK_adapted] / [ERK_peak - ERK_baseline]
2. τ_adapt = 20-40s: Time when ERK crosses 10% above baseline after peak
3. SRR < 5×: Steady-state response ratio = ERK_adapted / ERK_baseline
4. Fold-change > 4×: ERK_peak / ERK_baseline
"""

import pandas as pd
import numpy as np
import sys

def analyze_manuscript_criteria(csv_path):
    """Analyze adaptation using manuscript's 4 criteria"""
    df = pd.read_csv(csv_path)
    
    # Extract data
    time = df['Time (s)'].values
    erk_pp = df['ERK_PP (mM)'].values
    phase_pulse = df['Phase_Pulse (mM)'].values
    mkp = df['MKP (mM)'].values
    
    # Find pulse timing
    pulse_start_idx = np.where(phase_pulse > 0.5)[0]
    if len(pulse_start_idx) > 0:
        pulse_start = time[pulse_start_idx[0]]
        pulse_end = time[pulse_start_idx[-1]]
    else:
        pulse_start = pulse_end = 0
        print("ERROR: No pulse detected!")
        return
    
    # Baseline: average last 5s before pulse
    baseline_mask = (time >= pulse_start - 5) & (time < pulse_start)
    erk_baseline = np.mean(erk_pp[baseline_mask]) if np.any(baseline_mask) else erk_pp[0]
    mkp_baseline = np.mean(mkp[baseline_mask]) if np.any(baseline_mask) else mkp[0]
    
    # Peak: maximum ERK-PP
    erk_peak = np.max(erk_pp)
    peak_time = time[np.argmax(erk_pp)]
    
    # Adapted: last value (steady state)
    erk_adapted = erk_pp[-1]
    mkp_max = np.max(mkp)
    
    # CRITERION 1: Adaptation percentage
    adaptation_pct = 100 * (1 - (erk_adapted - erk_baseline) / (erk_peak - erk_baseline))
    criterion1_pass = adaptation_pct > 90
    
    # CRITERION 2: Adaptation timescale (τ_adapt)
    # Time when ERK crosses 10% above baseline AFTER peak
    threshold = erk_baseline * 1.1
    post_peak_mask = time > peak_time
    post_peak_idx = np.where(post_peak_mask)[0]
    
    tau_adapt = None
    for idx in post_peak_idx:
        if erk_pp[idx] <= threshold:
            tau_adapt = time[idx] - peak_time
            break
    
    if tau_adapt is None:
        tau_adapt = time[-1] - peak_time  # Never adapted
        
    criterion2_pass = 20 <= tau_adapt <= 40
    
    # CRITERION 3: Steady-state response ratio (SRR)
    srr = erk_adapted / erk_baseline if erk_baseline > 0 else float('inf')
    criterion3_pass = srr < 5
    
    # CRITERION 4: Fold-change (sensitivity)
    fold_change = erk_peak / erk_baseline if erk_baseline > 0 else 0
    criterion4_pass = fold_change > 4
    
    # Print results
    print("=" * 70)
    print("MANUSCRIPT ADAPTATION CRITERIA ANALYSIS")
    print("=" * 70)
    print(f"\nPulse: {pulse_start:.2f}s - {pulse_end:.2f}s ({pulse_end - pulse_start:.2f}s)")
    print(f"ERK-PP peak at t={peak_time:.2f}s")
    print(f"\nERK-PP dynamics:")
    print(f"  Baseline:  {erk_baseline:.4f} mM")
    print(f"  Peak:      {erk_peak:.4f} mM")
    print(f"  Adapted:   {erk_adapted:.4f} mM")
    print(f"\nMKP dynamics:")
    print(f"  Baseline:  {mkp_baseline:.4f} mM")
    print(f"  Maximum:   {mkp_max:.4f} mM ({mkp_max/mkp_baseline:.2f}× baseline)")
    
    print(f"\n{'=' * 70}")
    print("MANUSCRIPT CRITERIA (4 total):")
    print(f"{'=' * 70}")
    
    print(f"\n1. ADAPTATION > 90%:")
    print(f"   Formula: [ERK_peak - ERK_adapted] / [ERK_peak - ERK_baseline]")
    print(f"   Result:  {adaptation_pct:.1f}% {'✓ PASS' if criterion1_pass else '✗ FAIL'}")
    
    print(f"\n2. TIMESCALE τ_adapt = 20-40s:")
    print(f"   Formula: Time when ERK drops to 10% above baseline after peak")
    print(f"   Result:  {tau_adapt:.1f}s {'✓ PASS' if criterion2_pass else '✗ FAIL'}")
    
    print(f"\n3. SRR < 5×:")
    print(f"   Formula: ERK_adapted / ERK_baseline")
    print(f"   Result:  {srr:.1f}× {'✓ PASS' if criterion3_pass else '✗ FAIL'}")
    
    print(f"\n4. FOLD-CHANGE > 4×:")
    print(f"   Formula: ERK_peak / ERK_baseline")
    print(f"   Result:  {fold_change:.0f}× {'✓ PASS' if criterion4_pass else '✗ FAIL'}")
    
    # Summary
    passed = sum([criterion1_pass, criterion2_pass, criterion3_pass, criterion4_pass])
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {passed}/4 criteria passed")
    print(f"{'=' * 70}")
    
    if passed == 4:
        print("✓✓✓ PERFECT ADAPTATION - ALL 4 CRITERIA MET!")
    elif passed == 3:
        print("✓✓ NEAR-PERFECT - 3/4 criteria (matches manuscript Iteration 30)")
    elif passed >= 2:
        print("⚠ PARTIAL - More optimization needed")
    else:
        print("✗ FAILED - Major adjustments required")
    
    print()

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "workspace/projects/My_Project/mapk/data/simulation_data_adaptation_new.csv"
    analyze_manuscript_criteria(csv_file)
