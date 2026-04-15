#!/usr/bin/env python3
"""
Compare Lambda Phage models: Original vs Signal Hierarchy.
Analyzes batch simulation results to validate behavioral equivalence.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
import json

def load_batch_outcomes(batch_dir):
    """Load outcomes from a batch directory."""
    batch_path = Path(batch_dir)
    
    # Load config
    with open(batch_path / "config.json") as f:
        config = json.load(f)
    
    # Load all replicates and extract final states
    outcomes = []
    n_replicates = config['n_replicates']
    
    for i in range(1, n_replicates + 1):
        csv_file = batch_path / f"run_{i:03d}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            ci_final = df['P7'].iloc[-1]  # CI_Dimer
            cro_final = df['P8'].iloc[-1]  # Cro_Dimer
            
            # Classify (using 40 as threshold)
            if ci_final > 40 and cro_final < 40:
                outcome = "lysogenic"
            elif cro_final > 40 and ci_final < 40:
                outcome = "lytic"
            else:
                outcome = "undecided"
            
            outcomes.append({
                'replicate': i,
                'CI_final': ci_final,
                'Cro_final': cro_final,
                'outcome': outcome
            })
    
    return pd.DataFrame(outcomes), config

def compare_batches(original_batch, signal_batch):
    """Compare two batch results (original vs signal hierarchy)."""
    
    print("\n" + "="*80)
    print("MODEL COMPARISON: Original vs Signal Hierarchy")
    print("="*80 + "\n")
    
    # Load both batches
    print("Loading original model results...")
    df_orig, config_orig = load_batch_outcomes(original_batch)
    
    print("Loading signal hierarchy model results...")
    df_signal, config_signal = load_batch_outcomes(signal_batch)
    
    print(f"\nOriginal model: {len(df_orig)} replicates")
    print(f"Signal hierarchy model: {len(df_signal)} replicates")
    print()
    
    # Count outcomes
    orig_lys = (df_orig['outcome'] == 'lysogenic').sum()
    orig_lyt = (df_orig['outcome'] == 'lytic').sum()
    orig_und = (df_orig['outcome'] == 'undecided').sum()
    
    signal_lys = (df_signal['outcome'] == 'lysogenic').sum()
    signal_lyt = (df_signal['outcome'] == 'lytic').sum()
    signal_und = (df_signal['outcome'] == 'undecided').sum()
    
    # Display table
    print("OUTCOME DISTRIBUTION")
    print("-" * 80)
    print(f"{'Model':<25} {'Lysogenic':>15} {'Lytic':>15} {'Undecided':>15}")
    print("-" * 80)
    print(f"{'Original (embedded)':<25} {orig_lys:>10} ({100*orig_lys/len(df_orig):4.1f}%)  "
          f"{orig_lyt:>10} ({100*orig_lyt/len(df_orig):4.1f}%)  "
          f"{orig_und:>10} ({100*orig_und/len(df_orig):4.1f}%)")
    print(f"{'Signal Hierarchy':<25} {signal_lys:>10} ({100*signal_lys/len(df_signal):4.1f}%)  "
          f"{signal_lyt:>10} ({100*signal_lyt/len(df_signal):4.1f}%)  "
          f"{signal_und:>10} ({100*signal_und/len(df_signal):4.1f}%)")
    print()
    
    # Chi-square test (exclude undecided for cleaner comparison)
    observed = np.array([
        [orig_lys, orig_lyt],
        [signal_lys, signal_lyt]
    ])
    
    if observed.sum() > 0:
        chi2, p_value, dof, expected = stats.chi2_contingency(observed)
        
        print("STATISTICAL EQUIVALENCE TEST (Chi-Square)")
        print("-" * 80)
        print(f"Null hypothesis: Both models have same outcome distribution")
        print(f"Chi-square statistic: χ² = {chi2:.4f}")
        print(f"Degrees of freedom: {dof}")
        print(f"P-value: {p_value:.4f}")
        print()
        
        if p_value > 0.05:
            print("✓ CONCLUSION: Models are behaviorally EQUIVALENT (p > 0.05)")
            print("  No significant difference in bistability outcomes.")
        else:
            print("✗ CONCLUSION: Models show SIGNIFICANT DIFFERENCE (p ≤ 0.05)")
            print("  Outcome distributions differ statistically.")
        print()
    
    # Final state statistics
    print("FINAL STATE STATISTICS")
    print("-" * 80)
    print(f"Original model:")
    print(f"  CI_Dimer:  {df_orig['CI_final'].mean():.2f} ± {df_orig['CI_final'].std():.2f}")
    print(f"  Cro_Dimer: {df_orig['Cro_final'].mean():.2f} ± {df_orig['Cro_final'].std():.2f}")
    print()
    print(f"Signal Hierarchy model:")
    print(f"  CI_Dimer:  {df_signal['CI_final'].mean():.2f} ± {df_signal['CI_final'].std():.2f}")
    print(f"  Cro_Dimer: {df_signal['Cro_final'].mean():.2f} ± {df_signal['Cro_final'].std():.2f}")
    print()
    
    # Create comparison figure
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # 1. Outcome bar chart
    ax = axes[0]
    x = np.arange(3)
    width = 0.35
    
    orig_counts = [orig_lys, orig_lyt, orig_und]
    signal_counts = [signal_lys, signal_lyt, signal_und]
    
    ax.bar(x - width/2, orig_counts, width, label='Original (embedded)', 
           color='#3498db', alpha=0.8, edgecolor='black')
    ax.bar(x + width/2, signal_counts, width, label='Signal Hierarchy', 
           color='#e74c3c', alpha=0.8, edgecolor='black')
    
    ax.set_ylabel('Number of Replicates', fontsize=11)
    ax.set_title('Outcome Distribution Comparison', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Lysogenic', 'Lytic', 'Undecided'])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 2. Original phase portrait
    ax = axes[1]
    
    orig_lys_df = df_orig[df_orig['outcome'] == 'lysogenic']
    orig_lyt_df = df_orig[df_orig['outcome'] == 'lytic']
    orig_und_df = df_orig[df_orig['outcome'] == 'undecided']
    
    if len(orig_lys_df) > 0:
        ax.scatter(orig_lys_df['CI_final'], orig_lys_df['Cro_final'],
                  c='#2ecc71', s=60, alpha=0.7, label='Lysogenic', 
                  edgecolors='black', linewidths=0.5)
    if len(orig_lyt_df) > 0:
        ax.scatter(orig_lyt_df['CI_final'], orig_lyt_df['Cro_final'],
                  c='#e74c3c', s=60, alpha=0.7, label='Lytic',
                  edgecolors='black', linewidths=0.5)
    if len(orig_und_df) > 0:
        ax.scatter(orig_und_df['CI_final'], orig_und_df['Cro_final'],
                  c='#95a5a6', s=60, alpha=0.7, label='Undecided',
                  edgecolors='black', linewidths=0.5)
    
    ax.axvline(40, color='gray', linestyle='--', alpha=0.3)
    ax.axhline(40, color='gray', linestyle='--', alpha=0.3)
    ax.set_xlabel('CI_Dimer (final)', fontsize=11)
    ax.set_ylabel('Cro_Dimer (final)', fontsize=11)
    ax.set_title('Original Model (Embedded Regulation)', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # 3. Signal hierarchy phase portrait
    ax = axes[2]
    
    signal_lys_df = df_signal[df_signal['outcome'] == 'lysogenic']
    signal_lyt_df = df_signal[df_signal['outcome'] == 'lytic']
    signal_und_df = df_signal[df_signal['outcome'] == 'undecided']
    
    if len(signal_lys_df) > 0:
        ax.scatter(signal_lys_df['CI_final'], signal_lys_df['Cro_final'],
                  c='#2ecc71', s=60, alpha=0.7, label='Lysogenic',
                  edgecolors='black', linewidths=0.5)
    if len(signal_lyt_df) > 0:
        ax.scatter(signal_lyt_df['CI_final'], signal_lyt_df['Cro_final'],
                  c='#e74c3c', s=60, alpha=0.7, label='Lytic',
                  edgecolors='black', linewidths=0.5)
    if len(signal_und_df) > 0:
        ax.scatter(signal_und_df['CI_final'], signal_und_df['Cro_final'],
                  c='#95a5a6', s=60, alpha=0.7, label='Undecided',
                  edgecolors='black', linewidths=0.5)
    
    ax.axvline(40, color='gray', linestyle='--', alpha=0.3)
    ax.axhline(40, color='gray', linestyle='--', alpha=0.3)
    ax.set_xlabel('CI_Dimer (final)', fontsize=11)
    ax.set_ylabel('Cro_Dimer (final)', fontsize=11)
    ax.set_title('Signal Hierarchy Model (Inhibitor Arcs)', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_file = "model_comparison_detailed.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Comparison figure saved: {output_file}")
    
    plt.show()
    
    return {
        'original': df_orig,
        'signal': df_signal,
        'chi2': chi2 if observed.sum() > 0 else None,
        'p_value': p_value if observed.sum() > 0 else None
    }

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python compare_models.py <original_batch_dir> <signal_hierarchy_batch_dir>")
        print()
        print("Example:")
        print("  python compare_models.py results/batch_original results/batch_signal")
        sys.exit(1)
    
    original_batch = sys.argv[1]
    signal_batch = sys.argv[2]
    
    results = compare_batches(original_batch, signal_batch)
