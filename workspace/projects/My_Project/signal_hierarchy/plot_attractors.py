#!/usr/bin/env python3
"""Plot attractor basins for Lambda Phage bistability batches."""

import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Batch directories
BATCH_UV_DEPLETED = Path("workspace/projects/My_Project/signal_hierarchy/data/results/batch_20251224_163233")
BATCH_UV_ACTIVE = Path("workspace/projects/My_Project/signal_hierarchy/data/results/batch_20251224_170509")

def load_final_values(batch_dir):
    """Load final CI and Cro dimer values from all replicates."""
    ci_vals = []
    cro_vals = []
    
    for csv_file in sorted(batch_dir.glob('run_*.csv')):
        with open(csv_file, 'r') as f:
            data = list(csv.DictReader(f))
        
        if not data:
            continue
        
        final = data[-1]
        ci_vals.append(float(final.get('P7', 0)))
        cro_vals.append(float(final.get('P8', 0)))
    
    return np.array(ci_vals), np.array(cro_vals)

def plot_attractors():
    """Create attractor basin plot comparing UV conditions."""
    
    # Load both batches
    ci_depleted, cro_depleted = load_final_values(BATCH_UV_DEPLETED)
    ci_active, cro_active = load_final_values(BATCH_UV_ACTIVE)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: UV Depleted (balanced bistability)
    ax1.scatter(ci_depleted, cro_depleted, alpha=0.6, s=60, c='blue', edgecolors='black', linewidth=0.5)
    ax1.axline((0, 0), slope=1, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='CI = Cro')
    ax1.axline((0, 0), slope=0.5, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Cro = 2×CI')
    ax1.axline((0, 0), slope=2, color='green', linestyle=':', linewidth=1, alpha=0.5, label='CI = 2×Cro')
    
    ax1.set_xlabel('CI Dimer (final)', fontsize=12)
    ax1.set_ylabel('Cro Dimer (final)', fontsize=12)
    ax1.set_title('UV Depleted (Balanced Bistability)\n47% CI-dominant / 38% Cro-dominant', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    ax1.set_xlim(-5, max(ci_depleted.max(), cro_depleted.max()) + 10)
    ax1.set_ylim(-5, max(ci_depleted.max(), cro_depleted.max()) + 10)
    
    # Add attractor region labels
    ax1.text(0.75, 0.15, 'CI-dominant\nattractor', transform=ax1.transAxes,
             fontsize=10, color='green', fontweight='bold', ha='center',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax1.text(0.15, 0.75, 'Cro-dominant\nattractor', transform=ax1.transAxes,
             fontsize=10, color='red', fontweight='bold', ha='center',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Stats text
    stats_text1 = f'n = {len(ci_depleted)}\nCI: {ci_depleted.mean():.1f}±{ci_depleted.std():.1f}\nCro: {cro_depleted.mean():.1f}±{cro_depleted.std():.1f}'
    ax1.text(0.02, 0.98, stats_text1, transform=ax1.transAxes,
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Plot 2: UV Active (lytic bias)
    ax2.scatter(ci_active, cro_active, alpha=0.6, s=60, c='red', edgecolors='black', linewidth=0.5)
    ax2.axline((0, 0), slope=1, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='CI = Cro')
    ax2.axline((0, 0), slope=0.5, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Cro = 2×CI')
    ax2.axline((0, 0), slope=2, color='green', linestyle=':', linewidth=1, alpha=0.5, label='CI = 2×Cro')
    
    ax2.set_xlabel('CI Dimer (final)', fontsize=12)
    ax2.set_ylabel('Cro Dimer (final)', fontsize=12)
    ax2.set_title('UV Active (Lytic Bias)\n3% CI-dominant / 95% Cro-dominant', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.set_xlim(-5, max(ci_active.max(), cro_active.max()) + 10)
    ax2.set_ylim(-5, max(ci_active.max(), cro_active.max()) + 10)
    
    # Add attractor region label
    ax2.text(0.15, 0.75, 'Cro-dominant\nattractor\n(UV-induced)', transform=ax2.transAxes,
             fontsize=10, color='red', fontweight='bold', ha='center',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Stats text
    stats_text2 = f'n = {len(ci_active)}\nCI: {ci_active.mean():.1f}±{ci_active.std():.1f}\nCro: {cro_active.mean():.1f}±{cro_active.std():.1f}'
    ax2.text(0.02, 0.98, stats_text2, transform=ax2.transAxes,
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Save figure
    output_file = Path('attractor_basins_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved figure: {output_file}")
    
    plt.show()

if __name__ == '__main__':
    plot_attractors()
