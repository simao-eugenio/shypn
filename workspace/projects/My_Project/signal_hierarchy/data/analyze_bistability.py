#!/usr/bin/env python3
"""
Bistability Analysis for Lambda Phage Signal Hierarchy Models
Analyzes batch simulation data to classify lysogenic vs lytic outcomes.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import matplotlib.pyplot as plt
from scipy import stats

def load_batch_data(batch_dir):
    """Load all replicate data from batch directory."""
    batch_path = Path(batch_dir)
    
    # Load config
    with open(batch_path / "config.json") as f:
        config = json.load(f)
    
    # Load all replicates
    replicates = []
    for i in range(1, config['n_replicates'] + 1):
        csv_file = batch_path / f"run_{i:03d}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            replicates.append(df)
    
    return config, replicates

def classify_outcome(ci_final, cro_final, ci_threshold=40, cro_threshold=40):
    """
    Classify final state as lysogenic or lytic.
    
    Lysogenic: CI_Dimer dominates (CI > threshold, Cro < threshold)
    Lytic: Cro_Dimer dominates (Cro > threshold, CI < threshold)
    """
    if ci_final > ci_threshold and cro_final < ci_threshold:
        return "lysogenic"
    elif cro_final > cro_threshold and ci_final < cro_threshold:
        return "lytic"
    else:
        return "undecided"

def analyze_bistability(batch_dir, ci_threshold=40, cro_threshold=40):
    """Analyze bistability from batch simulation data."""
    
    print(f"Analyzing batch: {batch_dir}")
    print("=" * 60)
    
    config, replicates = load_batch_data(batch_dir)
    n_replicates = len(replicates)
    
    print(f"Total replicates: {n_replicates}")
    print(f"Duration: {config['settings']['duration']} seconds")
    print(f"Recorded places: {config['recorded_objects']}")
    print()
    
    # Extract final states
    outcomes = []
    final_states = []
    
    for i, df in enumerate(replicates):
        # Get final time point
        final_row = df.iloc[-1]
        
        ci_final = final_row['P7']  # CI_Dimer
        cro_final = final_row['P8']  # Cro_Dimer
        
        outcome = classify_outcome(ci_final, cro_final, ci_threshold, cro_threshold)
        outcomes.append(outcome)
        final_states.append({
            'replicate': i + 1,
            'CI_Dimer': ci_final,
            'Cro_Dimer': cro_final,
            'outcome': outcome
        })
    
    # Count outcomes
    lysogenic_count = outcomes.count("lysogenic")
    lytic_count = outcomes.count("lytic")
    undecided_count = outcomes.count("undecided")
    
    lysogenic_pct = 100 * lysogenic_count / n_replicates
    lytic_pct = 100 * lytic_count / n_replicates
    undecided_pct = 100 * undecided_count / n_replicates
    
    print("OUTCOME DISTRIBUTION")
    print("-" * 60)
    print(f"Lysogenic (CI dominates): {lysogenic_count:3d} ({lysogenic_pct:5.1f}%)")
    print(f"Lytic (Cro dominates):    {lytic_count:3d} ({lytic_pct:5.1f}%)")
    print(f"Undecided:                 {undecided_count:3d} ({undecided_pct:5.1f}%)")
    print()
    
    # Wilson confidence intervals (better for proportions)
    def wilson_ci(successes, trials, confidence=0.95):
        """Calculate Wilson score confidence interval."""
        if trials == 0:
            return (0, 0)
        p = successes / trials
        z = stats.norm.ppf((1 + confidence) / 2)
        denominator = 1 + z**2 / trials
        center = (p + z**2 / (2 * trials)) / denominator
        margin = z * np.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denominator
        return (center - margin, center + margin)
    
    lysogenic_ci = wilson_ci(lysogenic_count, n_replicates)
    lytic_ci = wilson_ci(lytic_count, n_replicates)
    
    print("CONFIDENCE INTERVALS (95% Wilson)")
    print("-" * 60)
    print(f"Lysogenic: {lysogenic_pct:5.1f}% [{100*lysogenic_ci[0]:5.1f}%, {100*lysogenic_ci[1]:5.1f}%]")
    print(f"Lytic:     {lytic_pct:5.1f}% [{100*lytic_ci[0]:5.1f}%, {100*lytic_ci[1]:5.1f}%]")
    print()
    
    # Final state statistics
    df_states = pd.DataFrame(final_states)
    
    print("FINAL STATE STATISTICS")
    print("-" * 60)
    print("CI_Dimer (P7):")
    print(f"  Mean ± SD: {df_states['CI_Dimer'].mean():.2f} ± {df_states['CI_Dimer'].std():.2f}")
    print(f"  Range: [{df_states['CI_Dimer'].min():.2f}, {df_states['CI_Dimer'].max():.2f}]")
    print()
    print("Cro_Dimer (P8):")
    print(f"  Mean ± SD: {df_states['Cro_Dimer'].mean():.2f} ± {df_states['Cro_Dimer'].std():.2f}")
    print(f"  Range: [{df_states['Cro_Dimer'].min():.2f}, {df_states['Cro_Dimer'].max():.2f}]")
    print()
    
    # Lysogenic vs Lytic statistics
    lysogenic_states = df_states[df_states['outcome'] == 'lysogenic']
    lytic_states = df_states[df_states['outcome'] == 'lytic']
    
    if len(lysogenic_states) > 0:
        print("Lysogenic state (n={}):")
        print(f"  CI_Dimer: {lysogenic_states['CI_Dimer'].mean():.2f} ± {lysogenic_states['CI_Dimer'].std():.2f}")
        print(f"  Cro_Dimer: {lysogenic_states['Cro_Dimer'].mean():.2f} ± {lysogenic_states['Cro_Dimer'].std():.2f}")
        print()
    
    if len(lytic_states) > 0:
        print(f"Lytic state (n={len(lytic_states)}):")
        print(f"  CI_Dimer: {lytic_states['CI_Dimer'].mean():.2f} ± {lytic_states['CI_Dimer'].std():.2f}")
        print(f"  Cro_Dimer: {lytic_states['Cro_Dimer'].mean():.2f} ± {lytic_states['Cro_Dimer'].std():.2f}")
        print()
    
    return {
        'config': config,
        'n_replicates': n_replicates,
        'outcomes': outcomes,
        'final_states': df_states,
        'lysogenic_count': lysogenic_count,
        'lytic_count': lytic_count,
        'undecided_count': undecided_count,
        'lysogenic_pct': lysogenic_pct,
        'lytic_pct': lytic_pct,
        'lysogenic_ci': lysogenic_ci,
        'lytic_ci': lytic_ci
    }

def plot_bistability(results, output_file=None):
    """Create visualization of bistability analysis."""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    df_states = results['final_states']
    lysogenic = df_states[df_states['outcome'] == 'lysogenic']
    lytic = df_states[df_states['outcome'] == 'lytic']
    undecided = df_states[df_states['outcome'] == 'undecided']
    
    # 1. Outcome distribution (bar chart)
    ax = axes[0, 0]
    outcomes = ['Lysogenic', 'Lytic', 'Undecided']
    counts = [results['lysogenic_count'], results['lytic_count'], results['undecided_count']]
    colors = ['#2ecc71', '#e74c3c', '#95a5a6']
    
    bars = ax.bar(outcomes, counts, color=colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Number of Replicates', fontsize=11)
    ax.set_title('Outcome Distribution', fontsize=12, fontweight='bold')
    ax.set_ylim(0, max(counts) * 1.2)
    
    # Add percentage labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        pct = 100 * count / results['n_replicates']
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{count}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 2. Phase portrait (CI vs Cro)
    ax = axes[0, 1]
    
    if len(lysogenic) > 0:
        ax.scatter(lysogenic['CI_Dimer'], lysogenic['Cro_Dimer'], 
                  c='#2ecc71', s=50, alpha=0.6, label='Lysogenic', edgecolors='black', linewidths=0.5)
    if len(lytic) > 0:
        ax.scatter(lytic['CI_Dimer'], lytic['Cro_Dimer'], 
                  c='#e74c3c', s=50, alpha=0.6, label='Lytic', edgecolors='black', linewidths=0.5)
    if len(undecided) > 0:
        ax.scatter(undecided['CI_Dimer'], undecided['Cro_Dimer'], 
                  c='#95a5a6', s=50, alpha=0.6, label='Undecided', edgecolors='black', linewidths=0.5)
    
    ax.set_xlabel('CI_Dimer (molecules)', fontsize=11)
    ax.set_ylabel('Cro_Dimer (molecules)', fontsize=11)
    ax.set_title('Phase Portrait (Final States)', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # 3. CI_Dimer distribution
    ax = axes[1, 0]
    
    if len(lysogenic) > 0:
        ax.hist(lysogenic['CI_Dimer'], bins=20, alpha=0.6, color='#2ecc71', 
               label='Lysogenic', edgecolor='black')
    if len(lytic) > 0:
        ax.hist(lytic['CI_Dimer'], bins=20, alpha=0.6, color='#e74c3c', 
               label='Lytic', edgecolor='black')
    
    ax.set_xlabel('CI_Dimer (molecules)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('CI_Dimer Distribution', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # 4. Cro_Dimer distribution
    ax = axes[1, 1]
    
    if len(lysogenic) > 0:
        ax.hist(lysogenic['Cro_Dimer'], bins=20, alpha=0.6, color='#2ecc71', 
               label='Lysogenic', edgecolor='black')
    if len(lytic) > 0:
        ax.hist(lytic['Cro_Dimer'], bins=20, alpha=0.6, color='#e74c3c', 
               label='Lytic', edgecolor='black')
    
    ax.set_xlabel('Cro_Dimer (molecules)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Cro_Dimer Distribution', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Figure saved: {output_file}")
    
    return fig

def compare_models(batch_original, batch_refactored, ci_threshold=40, cro_threshold=40):
    """Compare bistability between original and refactored models."""
    
    print("\n" + "="*60)
    print("COMPARING ORIGINAL vs SIGNAL HIERARCHY MODELS")
    print("="*60 + "\n")
    
    print("ORIGINAL MODEL")
    results_orig = analyze_bistability(batch_original, ci_threshold, cro_threshold)
    
    print("\n")
    print("SIGNAL HIERARCHY MODEL")
    results_refact = analyze_bistability(batch_refactored, ci_threshold, cro_threshold)
    
    # Chi-square test for behavioral equivalence
    print("\n" + "="*60)
    print("BEHAVIORAL EQUIVALENCE TEST (Chi-Square)")
    print("="*60)
    
    observed = np.array([
        [results_orig['lysogenic_count'], results_orig['lytic_count']],
        [results_refact['lysogenic_count'], results_refact['lytic_count']]
    ])
    
    chi2, p_value, dof, expected = stats.chi2_contingency(observed)
    
    print(f"Observed frequencies:")
    print(f"                Lysogenic    Lytic")
    print(f"  Original:     {results_orig['lysogenic_count']:3d}          {results_orig['lytic_count']:3d}")
    print(f"  Refactored:   {results_refact['lysogenic_count']:3d}          {results_refact['lytic_count']:3d}")
    print()
    print(f"Chi-square statistic: χ² = {chi2:.4f}")
    print(f"Degrees of freedom: {dof}")
    print(f"P-value: {p_value:.4f}")
    print()
    
    if p_value > 0.05:
        print("✓ CONCLUSION: Models are behaviorally equivalent (p > 0.05)")
        print("  No significant difference in outcome distributions.")
    else:
        print("✗ CONCLUSION: Models differ significantly (p ≤ 0.05)")
        print("  Outcome distributions are statistically different.")
    print()
    
    return {
        'original': results_orig,
        'refactored': results_refact,
        'chi2': chi2,
        'p_value': p_value,
        'behaviorally_equivalent': p_value > 0.05
    }

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_bistability.py <batch_directory> [output_figure.png]")
        print("   or: python analyze_bistability.py <batch_orig> <batch_refact> [output_figure.png]")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        # Single batch analysis
        batch_dir = sys.argv[1]
        results = analyze_bistability(batch_dir)
        
        # Create visualization
        output_file = f"{batch_dir}/bistability_analysis.png"
        plot_bistability(results, output_file)
        
    elif len(sys.argv) >= 3:
        # Compare two batches
        batch_orig = sys.argv[1]
        batch_refact = sys.argv[2]
        
        comparison = compare_models(batch_orig, batch_refact)
        
        # Create comparison figure
        output_file = sys.argv[3] if len(sys.argv) > 3 else "model_comparison.png"
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Original model
        results_orig = comparison['original']
        df_orig = results_orig['final_states']
        lysogenic_orig = df_orig[df_orig['outcome'] == 'lysogenic']
        lytic_orig = df_orig[df_orig['outcome'] == 'lytic']
        
        ax = axes[0]
        if len(lysogenic_orig) > 0:
            ax.scatter(lysogenic_orig['CI_Dimer'], lysogenic_orig['Cro_Dimer'], 
                      c='#2ecc71', s=50, alpha=0.6, label='Lysogenic', edgecolors='black', linewidths=0.5)
        if len(lytic_orig) > 0:
            ax.scatter(lytic_orig['CI_Dimer'], lytic_orig['Cro_Dimer'], 
                      c='#e74c3c', s=50, alpha=0.6, label='Lytic', edgecolors='black', linewidths=0.5)
        
        ax.set_xlabel('CI_Dimer', fontsize=11)
        ax.set_ylabel('Cro_Dimer', fontsize=11)
        ax.set_title(f'Original Model\nLysogenic: {results_orig["lysogenic_pct"]:.1f}%', 
                    fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Refactored model
        results_refact = comparison['refactored']
        df_refact = results_refact['final_states']
        lysogenic_refact = df_refact[df_refact['outcome'] == 'lysogenic']
        lytic_refact = df_refact[df_refact['outcome'] == 'lytic']
        
        ax = axes[1]
        if len(lysogenic_refact) > 0:
            ax.scatter(lysogenic_refact['CI_Dimer'], lysogenic_refact['Cro_Dimer'], 
                      c='#2ecc71', s=50, alpha=0.6, label='Lysogenic', edgecolors='black', linewidths=0.5)
        if len(lytic_refact) > 0:
            ax.scatter(lytic_refact['CI_Dimer'], lytic_refact['Cro_Dimer'], 
                      c='#e74c3c', s=50, alpha=0.6, label='Lytic', edgecolors='black', linewidths=0.5)
        
        ax.set_xlabel('CI_Dimer', fontsize=11)
        ax.set_ylabel('Cro_Dimer', fontsize=11)
        ax.set_title(f'Signal Hierarchy Model\nLysogenic: {results_refact["lysogenic_pct"]:.1f}%', 
                    fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nComparison figure saved: {output_file}")
    
    plt.show()
