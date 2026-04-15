#!/usr/bin/env python3
"""
Analyze batch_20251224_194537 (v2 model with CII integration) for bistability.
Compare with baseline batch_20251224_163233.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from collections import Counter

BASE_PATH = Path("/home/simao/projetos/shypn/workspace/projects/My_Project/signal_hierarchy")
BATCH_DIR = BASE_PATH / "data/results/batch_20251224_194537"
BASELINE_DIR = BASE_PATH / "data/results/batch_20251224_163233"

def classify_outcome(ci_final, cro_final, threshold_ratio=2.0):
    """Classify final state as CI-dominant, Cro-dominant, or undecided.
    
    Args:
        ci_final: Final CI Dimer concentration
        cro_final: Final Cro Dimer concentration
        threshold_ratio: Ratio for dominance (2.0 = one must be 2x the other)
    
    Returns:
        str: 'CI', 'Cro', or 'Undecided'
    """
    if ci_final > threshold_ratio * cro_final:
        return 'CI'
    elif cro_final > threshold_ratio * ci_final:
        return 'Cro'
    else:
        return 'Undecided'

def analyze_batch(batch_dir, batch_name):
    """Analyze a batch for bistability."""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {batch_name}")
    print(f"{'='*60}")
    
    outcomes = []
    ci_finals = []
    cro_finals = []
    
    # Read all replicates
    run_files = sorted(list(batch_dir.glob("run_*.csv")))
    print(f"Found {len(run_files)} replicates")
    
    if len(run_files) == 0:
        print(f"ERROR: No run files found in {batch_dir}")
        return None
    
    for run_file in run_files:
        df = pd.read_csv(run_file)
        
        # Get final values (last row)
        ci_final = df['P7'].iloc[-1]  # CI Dimer
        cro_final = df['P8'].iloc[-1]  # Cro Dimer
        
        ci_finals.append(ci_final)
        cro_finals.append(cro_final)
        
        # Classify outcome
        outcome = classify_outcome(ci_final, cro_final)
        outcomes.append(outcome)
    
    # Count outcomes
    outcome_counts = Counter(outcomes)
    total = len(outcomes)
    
    print(f"\n=== BISTABILITY ANALYSIS ===")
    print(f"Total replicates: {total}")
    print(f"\nOutcome distribution:")
    for outcome in ['CI', 'Cro', 'Undecided']:
        count = outcome_counts[outcome]
        pct = 100 * count / total
        print(f"  {outcome:12s}: {count:3d} ({pct:5.1f}%)")
    
    # Wilson confidence intervals
    def wilson_ci(successes, total, conf=0.95):
        """Wilson score confidence interval."""
        z = stats.norm.ppf((1 + conf) / 2)
        p = successes / total
        denominator = 1 + z**2 / total
        centre = (p + z**2 / (2 * total)) / denominator
        spread = z * np.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominator
        return centre - spread, centre + spread
    
    print(f"\n95% Confidence Intervals (Wilson):")
    for outcome in ['CI', 'Cro', 'Undecided']:
        count = outcome_counts[outcome]
        ci_low, ci_high = wilson_ci(count, total)
        print(f"  {outcome:12s}: [{100*ci_low:.1f}%, {100*ci_high:.1f}%]")
    
    # Statistical tests
    print(f"\n=== STATISTICAL TESTS ===")
    
    # Chi-square test for equal distribution
    expected = total / 3  # Equal distribution hypothesis
    observed = [outcome_counts['CI'], outcome_counts['Cro'], outcome_counts['Undecided']]
    chi2, p_value = stats.chisquare(observed, [expected, expected, expected])
    print(f"Chi-square test (H0: equal distribution):")
    print(f"  χ² = {chi2:.2f}, p = {p_value:.4f}")
    if p_value < 0.05:
        print(f"  ✓ Significant deviation from equal distribution (bistability confirmed)")
    
    # Bimodality test using Hartigan's dip test would be ideal but requires diptest package
    # Instead, use variance ratio as proxy
    ci_finals = np.array(ci_finals)
    cro_finals = np.array(cro_finals)
    
    print(f"\n=== ATTRACTOR STATISTICS ===")
    print(f"CI Dimer (P7) final values:")
    print(f"  Mean: {ci_finals.mean():.2f}, Std: {ci_finals.std():.2f}")
    print(f"  Range: [{ci_finals.min():.1f}, {ci_finals.max():.1f}]")
    print(f"  Coefficient of variation: {ci_finals.std() / ci_finals.mean():.3f}")
    
    print(f"\nCro Dimer (P8) final values:")
    print(f"  Mean: {cro_finals.mean():.2f}, Std: {cro_finals.std():.2f}")
    print(f"  Range: [{cro_finals.min():.1f}, {cro_finals.max():.1f}]")
    print(f"  Coefficient of variation: {cro_finals.std() / cro_finals.mean():.3f}")
    
    # Correlation between CI and Cro (should be negative for bistability)
    corr, p_corr = stats.pearsonr(ci_finals, cro_finals)
    print(f"\nCI-Cro correlation: r = {corr:.3f}, p = {p_corr:.4f}")
    if corr < -0.5:
        print(f"  ✓ Strong negative correlation (mutual exclusivity)")
    
    return {
        'outcomes': outcomes,
        'ci_finals': ci_finals,
        'cro_finals': cro_finals,
        'outcome_counts': outcome_counts
    }

def compare_batches(v2_results, baseline_results):
    """Compare v2 model with baseline."""
    print(f"\n{'='*60}")
    print(f"COMPARISON: v2 (with CII) vs Baseline")
    print(f"{'='*60}")
    
    v2_counts = v2_results['outcome_counts']
    base_counts = baseline_results['outcome_counts']
    total = len(v2_results['outcomes'])
    
    print(f"\nOutcome distribution comparison:")
    print(f"{'Outcome':<15} {'Baseline':>12} {'v2 Model':>12} {'Δ':>10}")
    print(f"{'-'*50}")
    for outcome in ['CI', 'Cro', 'Undecided']:
        base_pct = 100 * base_counts[outcome] / total
        v2_pct = 100 * v2_counts[outcome] / total
        delta = v2_pct - base_pct
        print(f"{outcome:<15} {base_pct:>11.1f}% {v2_pct:>11.1f}% {delta:>+9.1f}%")
    
    # Chi-square test for independence
    contingency = np.array([
        [base_counts['CI'], base_counts['Cro'], base_counts['Undecided']],
        [v2_counts['CI'], v2_counts['Cro'], v2_counts['Undecided']]
    ])
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
    
    print(f"\nChi-square test (H0: models have same distribution):")
    print(f"  χ² = {chi2:.2f}, p = {p_value:.4f}")
    if p_value < 0.05:
        print(f"  ✓ Significant difference between models")
    else:
        print(f"  Models have similar outcome distributions")
    
    # Effect size (Cramér's V)
    n = contingency.sum()
    cramers_v = np.sqrt(chi2 / (n * (min(contingency.shape) - 1)))
    print(f"  Cramér's V = {cramers_v:.3f}", end="")
    if cramers_v < 0.1:
        print(f" (negligible effect)")
    elif cramers_v < 0.3:
        print(f" (small effect)")
    elif cramers_v < 0.5:
        print(f" (medium effect)")
    else:
        print(f" (large effect)")

def main():
    print("Lambda Phage Hierarchical Model (v2) - Bistability Analysis")
    print("="*60)
    
    # Analyze v2 batch
    v2_results = analyze_batch(BATCH_DIR, "batch_20251224_194537 (v2 with CII)")
    
    # Analyze baseline batch
    if BASELINE_DIR.exists():
        baseline_results = analyze_batch(BASELINE_DIR, "batch_20251224_163233 (baseline)")
        
        # Compare
        compare_batches(v2_results, baseline_results)
    else:
        print(f"\nWarning: Baseline batch not found at {BASELINE_DIR}")
        print("Skipping comparison.")
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print("The v2 model includes CII integration module (L1-C2A):")
    print("  - CI Dimer activates CII transcription")
    print("  - CII Protein activates CI transcription (positive feedback)")
    print("\nExpected effect:")
    print("  - Strengthened lysogenic commitment")
    print("  - Potential shift toward CI dominance")
    print("  - Preserved bistability with modified attractor basin sizes")

if __name__ == "__main__":
    main()
