#!/usr/bin/env python3
"""
Plot attractor basins for v2 hierarchical model and compare with baseline.
Shows CI-Cro phase portraits to visualize bistability.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BASE_PATH = Path("/home/simao/projetos/shypn/workspace/projects/My_Project/signal_hierarchy")
V2_BATCH = BASE_PATH / "data/results/batch_20251224_194537"
BASELINE_BATCH = BASE_PATH / "data/results/batch_20251224_163233"
OUTPUT_DIR = BASE_PATH / "figures"

OUTPUT_DIR.mkdir(exist_ok=True)

def load_batch_finals(batch_dir):
    """Load final CI and Cro values from all replicates."""
    run_files = sorted(list(batch_dir.glob("run_*.csv")))
    
    ci_finals = []
    cro_finals = []
    
    for run_file in run_files:
        df = pd.read_csv(run_file)
        ci_finals.append(df['P7'].iloc[-1])
        cro_finals.append(df['P8'].iloc[-1])
    
    return np.array(ci_finals), np.array(cro_finals)

def classify_outcome(ci, cro, threshold=2.0):
    """Classify outcome for coloring."""
    if ci > threshold * cro:
        return 'Lysogenic'
    elif cro > threshold * ci:
        return 'Lytic'
    else:
        return 'Undecided'

def plot_comparison():
    """Create side-by-side comparison of v2 vs baseline attractors."""
    
    print("Loading batch data...")
    v2_ci, v2_cro = load_batch_finals(V2_BATCH)
    base_ci, base_cro = load_batch_finals(BASELINE_BATCH)
    
    # Classify outcomes
    v2_outcomes = [classify_outcome(ci, cro) for ci, cro in zip(v2_ci, v2_cro)]
    base_outcomes = [classify_outcome(ci, cro) for ci, cro in zip(base_ci, base_cro)]
    
    # Color mapping
    colors = {'Lysogenic': '#2E7D32', 'Lytic': '#C62828', 'Undecided': '#F57C00'}
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot baseline
    for outcome in ['Lysogenic', 'Lytic', 'Undecided']:
        mask = [o == outcome for o in base_outcomes]
        ax1.scatter(base_ci[mask], base_cro[mask], 
                   c=colors[outcome], label=outcome, 
                   alpha=0.6, s=80, edgecolors='black', linewidth=0.5)
    
    ax1.set_xlabel('CI Dimer (molecules)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Cro Dimer (molecules)', fontsize=12, fontweight='bold')
    ax1.set_title('Baseline Model\n(No CII Integration)', fontsize=13, fontweight='bold')
    ax1.legend(loc='upper right', framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-5, max(base_ci.max(), v2_ci.max()) + 10)
    ax1.set_ylim(-5, max(base_cro.max(), v2_cro.max()) + 10)
    
    # Add diagonal line (CI = Cro)
    max_val = max(ax1.get_xlim()[1], ax1.get_ylim()[1])
    ax1.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, linewidth=1, label='CI = Cro')
    
    # Plot v2
    for outcome in ['Lysogenic', 'Lytic', 'Undecided']:
        mask = [o == outcome for o in v2_outcomes]
        ax2.scatter(v2_ci[mask], v2_cro[mask], 
                   c=colors[outcome], label=outcome, 
                   alpha=0.6, s=80, edgecolors='black', linewidth=0.5)
    
    ax2.set_xlabel('CI Dimer (molecules)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cro Dimer (molecules)', fontsize=12, fontweight='bold')
    ax2.set_title('Hierarchical Model v2\n(+ CII Integration Layer)', fontsize=13, fontweight='bold')
    ax2.legend(loc='upper right', framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(-5, max(base_ci.max(), v2_ci.max()) + 10)
    ax2.set_ylim(-5, max(base_cro.max(), v2_cro.max()) + 10)
    
    # Add diagonal line
    ax2.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, linewidth=1, label='CI = Cro')
    
    # Add outcome statistics
    from collections import Counter
    v2_counts = Counter(v2_outcomes)
    base_counts = Counter(base_outcomes)
    
    stats_text_base = f"CI: {base_counts['Lysogenic']}  Cro: {base_counts['Lytic']}  U: {base_counts['Undecided']}"
    stats_text_v2 = f"CI: {v2_counts['Lysogenic']}  Cro: {v2_counts['Lytic']}  U: {v2_counts['Undecided']}"
    
    ax1.text(0.02, 0.98, stats_text_base, transform=ax1.transAxes,
            fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax2.text(0.02, 0.98, stats_text_v2, transform=ax2.transAxes,
            fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Save
    output_file = OUTPUT_DIR / "v2_vs_baseline_attractors.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    
    plt.close()

def plot_v2_with_annotations():
    """Create detailed v2 plot with hierarchical annotations."""
    
    print("Creating detailed v2 attractor plot...")
    v2_ci, v2_cro = load_batch_finals(V2_BATCH)
    v2_outcomes = [classify_outcome(ci, cro) for ci, cro in zip(v2_ci, v2_cro)]
    
    colors = {'Lysogenic': '#2E7D32', 'Lytic': '#C62828', 'Undecided': '#F57C00'}
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    for outcome in ['Lysogenic', 'Lytic', 'Undecided']:
        mask = [o == outcome for o in v2_outcomes]
        ax.scatter(v2_ci[mask], v2_cro[mask], 
                  c=colors[outcome], label=outcome, 
                  alpha=0.7, s=100, edgecolors='black', linewidth=0.8)
    
    ax.set_xlabel('CI Dimer (molecules)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Cro Dimer (molecules)', fontsize=14, fontweight='bold')
    ax.set_title('Lambda Phage Hierarchical Model v2\nAttractor Basin Landscape', 
                fontsize=15, fontweight='bold', pad=20)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Add separatrix annotations
    max_val = max(v2_ci.max(), v2_cro.max()) + 10
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.4, linewidth=2, label='Separatrix')
    
    # Add basin labels
    ax.text(0.75, 0.25, 'Lysogenic\nBasin', transform=ax.transAxes,
           fontsize=13, fontweight='bold', ha='center', va='center',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='lightgreen', alpha=0.7))
    
    ax.text(0.25, 0.75, 'Lytic\nBasin', transform=ax.transAxes,
           fontsize=13, fontweight='bold', ha='center', va='center',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='lightcoral', alpha=0.7))
    
    # Add architecture diagram
    arch_text = "Hierarchical Architecture:\nL0-C1A: RecA (Environmental)\n   ↓\nL1-C2A: CII (Integration) ✓ NEW\n   ↓\nL2-C3: CI-Cro (Decision)"
    ax.text(0.03, 0.03, arch_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
           family='monospace')
    
    plt.tight_layout()
    
    output_file = OUTPUT_DIR / "v2_attractor_detailed.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    
    plt.close()

def main():
    print("="*60)
    print("PLOTTING ATTRACTOR BASINS")
    print("="*60)
    
    plot_comparison()
    plot_v2_with_annotations()
    
    print(f"\n✓ Figures saved to: {OUTPUT_DIR}")
    print("\nNext: Re-run batch with P21 (CII) recorded to visualize 3D phase portrait")

if __name__ == "__main__":
    main()
