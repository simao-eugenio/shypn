#!/usr/bin/env python3
"""
Plot CII protein's role in hierarchical information flow.
Creates 3D phase portrait and distribution analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import cm

BASE_PATH = Path("/home/simao/projetos/shypn/workspace/projects/My_Project/signal_hierarchy")
NEW_BATCH = BASE_PATH / "data/results/batch_20251225_011804"
BASELINE_BATCH = BASE_PATH / "data/results/batch_20251224_163233"
OUTPUT_DIR = BASE_PATH / "figures"

OUTPUT_DIR.mkdir(exist_ok=True)

def classify_outcome(ci, cro, threshold=2.0):
    if ci > threshold * cro:
        return 'Lysogenic'
    elif cro > threshold * ci:
        return 'Lytic'
    else:
        return 'Undecided'

def load_batch_with_cii(batch_dir):
    """Load batch with CII data."""
    run_files = sorted(list(batch_dir.glob("run_*.csv")))
    
    data = {
        'CII': [],
        'CI': [],
        'Cro': [],
        'Outcome': []
    }
    
    for run_file in run_files:
        df = pd.read_csv(run_file)
        
        ci = df['P7'].iloc[-1]
        cro = df['P8'].iloc[-1]
        cii = df['P21'].iloc[-1]
        
        data['CII'].append(cii)
        data['CI'].append(ci)
        data['Cro'].append(cro)
        data['Outcome'].append(classify_outcome(ci, cro))
    
    return data

def plot_3d_phase_portrait():
    """Create multi-view 2D projections of CI × Cro × CII space."""
    
    print("Creating phase portrait projections...")
    data = load_batch_with_cii(NEW_BATCH)
    
    colors = {'Lysogenic': '#2E7D32', 'Lytic': '#C62828', 'Undecided': '#F57C00'}
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # CI vs Cro (classic 2D)
    ax = axes[0]
    for outcome in ['Lysogenic', 'Lytic', 'Undecided']:
        mask = [o == outcome for o in data['Outcome']]
        ci_vals = np.array(data['CI'])[mask]
        cro_vals = np.array(data['Cro'])[mask]
        
        ax.scatter(ci_vals, cro_vals, c=colors[outcome], label=outcome,
                  alpha=0.7, s=80, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('CI Dimer', fontsize=11, fontweight='bold')
    ax.set_ylabel('Cro Dimer', fontsize=11, fontweight='bold')
    ax.set_title('CI-Cro Phase Space', fontsize=12, fontweight='bold')
    ax.legend(framealpha=0.9, fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # CI vs CII
    ax = axes[1]
    for outcome in ['Lysogenic', 'Lytic', 'Undecided']:
        mask = [o == outcome for o in data['Outcome']]
        ci_vals = np.array(data['CI'])[mask]
        cii_vals = np.array(data['CII'])[mask]
        
        ax.scatter(ci_vals, cii_vals, c=colors[outcome], label=outcome,
                  alpha=0.7, s=80, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('CI Dimer', fontsize=11, fontweight='bold')
    ax.set_ylabel('CII Protein', fontsize=11, fontweight='bold')
    ax.set_title('CI-CII Phase Space', fontsize=12, fontweight='bold')
    ax.legend(framealpha=0.9, fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Cro vs CII
    ax = axes[2]
    for outcome in ['Lysogenic', 'Lytic', 'Undecided']:
        mask = [o == outcome for o in data['Outcome']]
        cro_vals = np.array(data['Cro'])[mask]
        cii_vals = np.array(data['CII'])[mask]
        
        ax.scatter(cro_vals, cii_vals, c=colors[outcome], label=outcome,
                  alpha=0.7, s=80, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('Cro Dimer', fontsize=11, fontweight='bold')
    ax.set_ylabel('CII Protein', fontsize=11, fontweight='bold')
    ax.set_title('Cro-CII Phase Space', fontsize=12, fontweight='bold')
    ax.legend(framealpha=0.9, fontsize=9)
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('Multi-View Phase Portrait: Hierarchical Decision Space', 
                fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / "phase_portrait_multiview_cii.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def plot_cii_distributions():
    """Plot CII distributions by outcome."""
    
    print("Creating CII distribution plots...")
    data = load_batch_with_cii(NEW_BATCH)
    
    cii_lysogenic = [data['CII'][i] for i, o in enumerate(data['Outcome']) if o == 'Lysogenic']
    cii_lytic = [data['CII'][i] for i, o in enumerate(data['Outcome']) if o == 'Lytic']
    cii_undecided = [data['CII'][i] for i, o in enumerate(data['Outcome']) if o == 'Undecided']
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # Box plots
    ax = axes[0]
    bp = ax.boxplot([cii_lysogenic, cii_lytic, cii_undecided],
                    labels=['Lysogenic', 'Lytic', 'Undecided'],
                    patch_artist=True,
                    widths=0.6)
    
    colors = ['#2E7D32', '#C62828', '#F57C00']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    ax.set_ylabel('CII Protein (molecules)', fontsize=11, fontweight='bold')
    ax.set_title('CII Distribution by Outcome', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Histograms
    ax = axes[1]
    ax.hist(cii_lysogenic, bins=15, alpha=0.7, color='#2E7D32', label='Lysogenic', edgecolor='black')
    ax.hist(cii_lytic, bins=15, alpha=0.7, color='#C62828', label='Lytic', edgecolor='black')
    ax.set_xlabel('CII Protein (molecules)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax.set_title('CII Histogram (Overlaid)', fontsize=12, fontweight='bold')
    ax.legend(framealpha=0.9)
    ax.grid(True, alpha=0.3)
    
    # CI vs CII scatter
    ax = axes[2]
    for outcome in ['Lysogenic', 'Lytic', 'Undecided']:
        mask = [o == outcome for o in data['Outcome']]
        ci_vals = np.array(data['CI'])[mask]
        cii_vals = np.array(data['CII'])[mask]
        
        color_map = {'Lysogenic': '#2E7D32', 'Lytic': '#C62828', 'Undecided': '#F57C00'}
        ax.scatter(ci_vals, cii_vals, c=color_map[outcome], label=outcome,
                  alpha=0.6, s=60, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('CI Dimer (molecules)', fontsize=11, fontweight='bold')
    ax.set_ylabel('CII Protein (molecules)', fontsize=11, fontweight='bold')
    ax.set_title('CI-CII Feedback Correlation', fontsize=12, fontweight='bold')
    ax.legend(framealpha=0.9, fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Add correlation
    from scipy import stats
    ci_all = np.array(data['CI'])
    cii_all = np.array(data['CII'])
    r, p = stats.pearsonr(ci_all, cii_all)
    ax.text(0.05, 0.95, f'r = {r:.3f}\np = {p:.4f}', 
           transform=ax.transAxes, fontsize=10,
           verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / "cii_distribution_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def plot_information_flow_diagram():
    """Create information flow cascade diagram."""
    
    print("Creating information flow diagram...")
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.axis('off')
    
    # Layer boxes
    layers = [
        {'name': 'L0-C1A\nEnvironmental Sensor', 'y': 0.8, 'elements': 'RecA (DNA Damage)'},
        {'name': 'L1-C2A\nIntegration Layer', 'y': 0.6, 'elements': 'CII Protein\nI(CII; Decision) = 0.11 bits'},
        {'name': 'L2-C3\nDecision Circuit', 'y': 0.4, 'elements': 'CI-Cro Switch\nI(CI; Decision) = 1.00 bits'},
        {'name': 'L3-C4\nEffector Modules', 'y': 0.2, 'elements': 'Lysogenic / Lytic Programs'}
    ]
    
    for i, layer in enumerate(layers):
        # Main box
        rect = plt.Rectangle((0.2, layer['y']-0.05), 0.6, 0.08,
                            facecolor=['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'][i],
                            edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        
        # Layer name
        ax.text(0.15, layer['y'], layer['name'], 
               fontsize=11, fontweight='bold', ha='right', va='center')
        
        # Elements
        ax.text(0.5, layer['y'], layer['elements'],
               fontsize=9, ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Arrows
        if i < len(layers) - 1:
            ax.annotate('', xy=(0.5, layer['y']-0.05), xytext=(0.5, layers[i+1]['y']+0.03),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # Title
    ax.text(0.5, 0.95, 'Hierarchical Information Flow\nLambda Phage Decision Making',
           fontsize=14, fontweight='bold', ha='center', va='top')
    
    # Key findings box
    findings_text = "Key Findings:\n• CII contributes 16.6% to decision uncertainty reduction\n• Strong CI-CII feedback: I(CII; CI) = 0.72 bits\n• CII levels similar in both outcomes (p=0.18)\n• Integration layer modulates but doesn't determine fate"
    ax.text(0.5, 0.05, findings_text,
           fontsize=9, ha='center', va='bottom',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
           family='monospace')
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / "information_flow_diagram.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def main():
    print("="*60)
    print("CII PROTEIN ANALYSIS & VISUALIZATION")
    print("="*60)
    
    plot_cii_distributions()
    plot_3d_phase_portrait()
    plot_information_flow_diagram()
    
    print(f"\n✓ All figures saved to: {OUTPUT_DIR}")
    print("\nFigures generated:")
    print("  1. cii_distribution_analysis.png - CII distributions by outcome")
    print("  2. phase_portrait_multiview_cii.png - Multi-view phase space")
    print("  3. information_flow_diagram.png - Information cascade")

if __name__ == "__main__":
    main()
