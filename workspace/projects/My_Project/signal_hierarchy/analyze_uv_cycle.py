#!/usr/bin/env python3
"""
UV Cycle Analysis for Lambda Phage Hierarchical Model
Analyzes RecA activation and lytic switch response
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats

# Configuration
BATCH_DIR = Path("data/results/batch_20251225_084841")
OUTPUT_DIR = Path("figures")
OUTPUT_DIR.mkdir(exist_ok=True)

THRESHOLD = 2.0

def load_batch_data():
    """Load all replicates and extract key metrics."""
    print("Loading batch data...")
    
    n_replicates = 100
    data = {
        'ci_final': [], 'cro_final': [], 'cii_final': [], 
        'reca_final': [], 'reca_max': [], 'reca_activation_time': [],
        'outcome': [], 'replicate': []
    }
    
    for i in range(1, n_replicates + 1):
        df = pd.read_csv(BATCH_DIR / f'run_{i:03d}.csv')
        
        ci = df['P7'].iloc[-1]
        cro = df['P8'].iloc[-1]
        cii = df['P21'].iloc[-1]
        reca = df['P14'].iloc[-1]
        
        data['ci_final'].append(ci)
        data['cro_final'].append(cro)
        data['cii_final'].append(cii)
        data['reca_final'].append(reca)
        data['reca_max'].append(df['P14'].max())
        data['replicate'].append(i)
        
        # RecA activation time
        reca_active = df[df['P14'] > 0]
        if len(reca_active) > 0:
            data['reca_activation_time'].append(reca_active['time'].iloc[0])
        else:
            data['reca_activation_time'].append(np.nan)
        
        # Classify outcome
        if ci > THRESHOLD * cro:
            data['outcome'].append('Lysogenic')
        elif cro > THRESHOLD * ci:
            data['outcome'].append('Lytic')
        else:
            data['outcome'].append('Undecided')
    
    return pd.DataFrame(data)

def plot_uv_response_trajectories():
    """Plot example trajectories showing UV-induced lytic switch."""
    print("Creating UV response trajectory plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('UV-Induced Lytic Switch - Example Trajectories', 
                 fontsize=14, fontweight='bold')
    
    # Select 4 representative replicates (2 early, 2 late activation)
    df_meta = load_batch_data()
    df_meta_sorted = df_meta.dropna(subset=['reca_activation_time']).sort_values('reca_activation_time')
    
    # Early activators (around 25th percentile)
    early_idx = [int(df_meta_sorted.iloc[24]['replicate']), 
                 int(df_meta_sorted.iloc[25]['replicate'])]
    # Late activators (around 75th percentile)
    late_idx = [int(df_meta_sorted.iloc[72]['replicate']), 
                int(df_meta_sorted.iloc[73]['replicate'])]
    
    selected = early_idx + late_idx
    titles = ['Early UV (1)', 'Early UV (2)', 'Late UV (1)', 'Late UV (2)']
    
    for idx, (rep, ax) in enumerate(zip(selected, axes.flat)):
        df = pd.read_csv(BATCH_DIR / f'run_{rep:03d}.csv')
        
        # Plot RecA (UV signal)
        ax2 = ax.twinx()
        ax2.plot(df['time'], df['P14'], 'purple', alpha=0.3, linewidth=2, label='RecA (UV)')
        ax2.set_ylabel('RecA Active (P14)', color='purple')
        ax2.tick_params(axis='y', labelcolor='purple')
        ax2.set_ylim(0, 100)
        
        # Plot CI and Cro
        ax.plot(df['time'], df['P7'], 'green', linewidth=2, label='CI Dimer', alpha=0.8)
        ax.plot(df['time'], df['P8'], 'red', linewidth=2, label='Cro Dimer', alpha=0.8)
        ax.plot(df['time'], df['P21'], 'blue', linewidth=1.5, label='CII Protein', 
                linestyle='--', alpha=0.7)
        
        # Mark RecA activation
        reca_active = df[df['P14'] > 0]
        if len(reca_active) > 0:
            t_activation = reca_active['time'].iloc[0]
            ax.axvline(t_activation, color='purple', linestyle=':', alpha=0.5, linewidth=1.5)
            ax.text(t_activation, ax.get_ylim()[1] * 0.95, f'UV: {t_activation:.0f}s',
                   rotation=90, verticalalignment='top', color='purple', fontsize=8)
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Protein Concentration')
        ax.set_title(titles[idx])
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 3000)
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / 'uv_response_trajectories.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def plot_uv_timing_analysis():
    """Analyze relationship between RecA activation timing and outcome."""
    print("Creating UV timing analysis...")
    
    df = load_batch_data()
    df_valid = df.dropna(subset=['reca_activation_time'])
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('UV Cycle Analysis: RecA Activation and Lytic Response', 
                 fontsize=14, fontweight='bold')
    
    # 1. RecA activation time distribution
    ax = axes[0, 0]
    ax.hist(df_valid['reca_activation_time'], bins=30, color='purple', alpha=0.7, edgecolor='black')
    ax.axvline(df_valid['reca_activation_time'].mean(), color='red', 
               linestyle='--', linewidth=2, label=f'Mean: {df_valid["reca_activation_time"].mean():.0f}s')
    ax.set_xlabel('RecA Activation Time (s)')
    ax.set_ylabel('Frequency')
    ax.set_title('RecA Activation Timing Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. RecA max level distribution
    ax = axes[0, 1]
    ax.hist(df['reca_max'], bins=20, color='purple', alpha=0.7, edgecolor='black')
    ax.axvline(df['reca_max'].mean(), color='red', 
               linestyle='--', linewidth=2, label=f'Mean: {df["reca_max"].mean():.1f}')
    ax.set_xlabel('Maximum RecA Level')
    ax.set_ylabel('Frequency')
    ax.set_title('RecA Peak Intensity')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Outcome distribution
    ax = axes[1, 0]
    outcomes = df['outcome'].value_counts()
    colors = {'Lytic': 'red', 'Lysogenic': 'green', 'Undecided': 'gray'}
    outcome_colors = [colors.get(o, 'gray') for o in outcomes.index]
    bars = ax.bar(outcomes.index, outcomes.values, color=outcome_colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Count')
    ax.set_title('Outcome Distribution (UV Cycle)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add percentages on bars
    for bar, val in zip(bars, outcomes.values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val}\n({val/len(df)*100:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 4. CII levels by outcome
    ax = axes[1, 1]
    lytic_cii = df[df['outcome'] == 'Lytic']['cii_final']
    lysogenic_cii = df[df['outcome'] == 'Lysogenic']['cii_final']
    undecided_cii = df[df['outcome'] == 'Undecided']['cii_final']
    
    bp = ax.boxplot([lytic_cii, lysogenic_cii, undecided_cii],
                     labels=['Lytic', 'Lysogenic', 'Undecided'],
                     patch_artist=True)
    
    for patch, color in zip(bp['boxes'], ['red', 'green', 'gray']):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    ax.set_ylabel('CII Protein (final)')
    ax.set_title('CII Levels by Outcome')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add statistical test
    if len(lysogenic_cii) > 0 and len(lytic_cii) > 0:
        t_stat, p_val = stats.ttest_ind(lysogenic_cii, lytic_cii)
        ax.text(0.5, 0.95, f't-test: p={p_val:.4f}', 
                transform=ax.transAxes, ha='center', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / 'uv_cycle_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def plot_phase_portrait_uv():
    """Phase portrait colored by RecA activation time."""
    print("Creating UV-colored phase portrait...")
    
    df = load_batch_data()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot colored by RecA activation time
    scatter = ax.scatter(df['ci_final'], df['cro_final'], 
                        c=df['reca_activation_time'], 
                        s=80, alpha=0.7, cmap='viridis', edgecolors='black', linewidth=0.5)
    
    # Add outcome regions
    ax.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    
    # Diagonal threshold lines
    ci_range = np.linspace(0, df['ci_final'].max(), 100)
    ax.plot(ci_range, ci_range / THRESHOLD, 'g--', alpha=0.3, linewidth=1.5, label='CI threshold')
    ax.plot(ci_range / THRESHOLD, ci_range, 'r--', alpha=0.3, linewidth=1.5, label='Cro threshold')
    
    # Labels for regions
    ax.text(df['ci_final'].max() * 0.8, 5, 'Lysogenic\n(CI dominant)', 
            fontsize=10, color='green', weight='bold', alpha=0.6, ha='center')
    ax.text(5, df['cro_final'].max() * 0.8, 'Lytic\n(Cro dominant)', 
            fontsize=10, color='red', weight='bold', alpha=0.6, ha='center')
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('RecA Activation Time (s)', rotation=270, labelpad=20)
    
    ax.set_xlabel('CI Dimer (P7) - Final')
    ax.set_ylabel('Cro Dimer (P8) - Final')
    ax.set_title('Phase Portrait: UV Cycle Response\n(Color = RecA activation time)', 
                 fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / 'phase_portrait_uv_colored.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == '__main__':
    print("="*60)
    print("UV CYCLE VISUALIZATION")
    print("="*60)
    
    plot_uv_response_trajectories()
    plot_uv_timing_analysis()
    plot_phase_portrait_uv()
    
    print("\n✓ All UV cycle figures generated")
    print(f"Output directory: {OUTPUT_DIR}")
