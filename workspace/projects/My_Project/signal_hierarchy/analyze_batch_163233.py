#!/usr/bin/env python3
"""Quick bistability analysis for batch_20251224_163233."""

import csv
import json
import numpy as np
from pathlib import Path
from scipy import stats

BATCH_DIR = Path("workspace/projects/My_Project/signal_hierarchy/data/results/batch_20251224_170509")

def load_final_values():
    """Load final values from all replicates."""
    results = []
    
    for csv_file in sorted(BATCH_DIR.glob('run_*.csv')):
        with open(csv_file, 'r') as f:
            data = list(csv.DictReader(f))
        
        if not data:
            continue
        
        final = data[-1]
        ci_dimer = float(final.get('P7', 0))  # CI_Dimer
        cro_dimer = float(final.get('P8', 0))  # Cro_Dimer
        p3 = float(final.get('P3', 0))
        p6 = float(final.get('P6', 0))
        
        results.append({
            'ci_dimer': ci_dimer,
            'cro_dimer': cro_dimer,
            'p3': p3,
            'p6': p6
        })
    
    return results

def classify_outcome(ci, cro, threshold_ratio=2.0):
    """Classify outcome based on dimer dominance.
    
    Args:
        ci: CI_Dimer final concentration
        cro: Cro_Dimer final concentration
        threshold_ratio: Ratio required for dominance (default 2x)
    
    Returns:
        'ci_dominant', 'cro_dominant', or 'undecided'
    """
    if ci >= threshold_ratio * cro:
        return 'ci_dominant'
    elif cro >= threshold_ratio * ci:
        return 'cro_dominant'
    else:
        return 'undecided'

def analyze_bistability():
    """Analyze batch results for bistability."""
    print(f"📊 Analyzing batch: {BATCH_DIR.name}")
    print(f"Duration: 3000s, UV ACTIVE (stochastic), CI/Cro dimers with infinite capacity\n")
    
    results = load_final_values()
    n_total = len(results)
    
    print(f"Total replicates: {n_total}\n")
    
    # Extract final values
    ci_vals = np.array([r['ci_dimer'] for r in results])
    cro_vals = np.array([r['cro_dimer'] for r in results])
    p3_vals = np.array([r['p3'] for r in results])
    p6_vals = np.array([r['p6'] for r in results])
    
    # Statistics
    print("=" * 60)
    print("FINAL VALUE STATISTICS")
    print("=" * 60)
    print(f"CI_Dimer (P7):  {ci_vals.mean():.1f} ± {ci_vals.std():.1f}  [range: {ci_vals.min():.0f}-{ci_vals.max():.0f}]")
    print(f"Cro_Dimer (P8): {cro_vals.mean():.1f} ± {cro_vals.std():.1f}  [range: {cro_vals.min():.0f}-{cro_vals.max():.0f}]")
    print(f"P3:             {p3_vals.mean():.1f} ± {p3_vals.std():.1f}  [range: {p3_vals.min():.0f}-{p3_vals.max():.0f}]")
    print(f"P6:             {p6_vals.mean():.1f} ± {p6_vals.std():.1f}  [range: {p6_vals.min():.0f}-{p6_vals.max():.0f}]")
    print()
    
    # Classify outcomes
    outcomes = [classify_outcome(r['ci_dimer'], r['cro_dimer']) for r in results]
    n_ci = outcomes.count('ci_dominant')
    n_cro = outcomes.count('cro_dominant')
    n_undecided = outcomes.count('undecided')
    
    print("=" * 60)
    print("BISTABILITY ANALYSIS (2× dominance threshold)")
    print("=" * 60)
    print(f"CI dominant:   {n_ci:3d} ({100*n_ci/n_total:5.1f}%)")
    print(f"Cro dominant:  {n_cro:3d} ({100*n_cro/n_total:5.1f}%)")
    print(f"Undecided:     {n_undecided:3d} ({100*n_undecided/n_total:5.1f}%)")
    print()
    
    # Chi-square test for bistability
    if n_ci > 0 and n_cro > 0:
        # Two-state bistability expected: equal proportions
        expected = (n_ci + n_cro) / 2
        chi2, p_value = stats.chisquare([n_ci, n_cro], [expected, expected])
        print(f"Chi-square test (H0: equal proportions): χ²={chi2:.2f}, p={p_value:.4f}")
        if p_value > 0.05:
            print("✓ Proportions are statistically balanced (bistable switch)")
        else:
            print("✗ Proportions are significantly unbalanced")
        print()
    
    # Correlation between CI and Cro
    corr, p_corr = stats.pearsonr(ci_vals, cro_vals)
    print(f"CI-Cro correlation: r={corr:.3f}, p={p_corr:.4e}")
    if abs(corr) < 0.3:
        print("✓ Weak correlation (expected for bistable system)")
    else:
        print("⚠ Strong correlation (may indicate single attractor)")
    print()
    
    # Coefficient of variation (noise)
    cv_ci = ci_vals.std() / ci_vals.mean() * 100
    cv_cro = cro_vals.std() / cro_vals.mean() * 100
    print("=" * 60)
    print("VARIABILITY")
    print("=" * 60)
    print(f"CI_Dimer CV:  {cv_ci:.1f}%")
    print(f"Cro_Dimer CV: {cv_cro:.1f}%")
    print()
    
    # Summary
    print("=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    if n_ci > 0 and n_cro > 0 and n_undecided < 0.5 * n_total:
        print("✓ BISTABLE behavior detected:")
        print(f"  - {n_ci + n_cro} replicates committed to CI or Cro dominance")
        print(f"  - {n_undecided} replicates remain undecided")
    elif n_undecided > 0.8 * n_total:
        print("✗ NO bistability - all replicates undecided:")
        print(f"  - CI and Cro levels are balanced (no clear winner)")
        print(f"  - Infinite capacity removes competitive exclusion")
    elif n_ci > 0.9 * n_total or n_cro > 0.9 * n_total:
        print("⚠ MONOSTABLE behavior - single attractor:")
        winner = "CI" if n_ci > n_cro else "Cro"
        print(f"  - {winner} dominates in >90% of replicates")
    else:
        print("⚠ UNCLEAR pattern - further analysis needed")

if __name__ == '__main__':
    analyze_bistability()
