#!/usr/bin/env python3
"""
Generate Decision Cascade Figure for Bacillus Sporulation
Created: January 4, 2026
For manuscript: "Thermodynamic Framework for Hierarchical Signal Theory"
"""

import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

# Data files
DATA_NORMAL = Path("data/simulation_data_normal.csv")
DATA_STRESS = Path("data/simulation_data_stress_analysis.csv")

# Create custom colormap: dark blue → cyan → yellow → orange → red (cool to hot)
colors = ['#000033', '#000066', '#003399', '#0066cc', '#0099ff',
          '#00ccff', '#66ffff', '#ffff99', '#ffcc66', '#ff9933', 
          '#ff6600', '#ff3300', '#cc0000']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('cascade_hot', colors, N=n_bins)

def load_cascade_data(csv_file):
    """Load hierarchical layer activation data."""
    with open(csv_file, 'r') as f:
        data = list(csv.DictReader(f))
    
    if not data:
        return None
    
    time = np.array([float(row['Time (s)']) for row in data])
    
    # Hierarchical layers
    layers = {
        'Layer 0: Spo0A~P': np.array([float(row['Spo0A_P (mM)']) for row in data]),
        'Layer 1: SigmaH': np.array([float(row['SigmaH (mM)']) for row in data]),
        'Layer 2: Septum': np.array([float(row['Septum (mM)']) for row in data]),
        'Layer 3: SigmaF': np.array([float(row['SigmaF (mM)']) for row in data]),
        'Layer 4: SigmaE': np.array([float(row['SigmaE (mM)']) for row in data]),
    }
    
    # Normalize each layer to [0, 1] for comparison
    layers_norm = {}
    for name, values in layers.items():
        max_val = values.max()
        if max_val > 0:
            layers_norm[name] = values / max_val
        else:
            layers_norm[name] = values
    
    return {
        'time': time,
        'layers': layers,
        'layers_norm': layers_norm
    }

def plot_decision_cascade():
    """Create clean decision cascade plot."""
    
    # Load data
    normal_data = load_cascade_data(DATA_NORMAL)
    stress_data = load_cascade_data(DATA_STRESS)
    
    if not normal_data or not stress_data:
        print("Error: Could not load cascade data")
        return
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Color map for layers
    layer_colors = {
        'Layer 0: Spo0A~P': '#0066cc',
        'Layer 1: SigmaH': '#00ccff',
        'Layer 2: Septum': '#ffff99',
        'Layer 3: SigmaF': '#ffcc66',
        'Layer 4: SigmaE': '#ff6600',
    }
    
    # === PLOT 1: Normal Pathway (High ATP) ===
    ax1.set_facecolor('#f8f8f8')
    
    for i, (layer_name, color) in enumerate(layer_colors.items()):
        values = normal_data['layers_norm'][layer_name]
        ax1.plot(normal_data['time'], values, 
                color=color, linewidth=2.5, alpha=0.9,
                label=layer_name)
    
    ax1.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Normalized Activity [0-1]', fontsize=12, fontweight='bold')
    ax1.set_title('Normal Pathway (High ATP = 5000 mM)\nSequential Layer Activation', 
                 fontsize=13, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    # ax1.legend(loc='upper left', fontsize=10, framealpha=0.95)  # Removed for manuscript
    ax1.set_xlim(0, normal_data['time'][-1])
    ax1.set_ylim(-0.05, 1.1)
    
    # === PLOT 2: Stress Pathway (Low ATP) ===
    ax2.set_facecolor('#f8f8f8')
    
    for i, (layer_name, color) in enumerate(layer_colors.items()):
        values = stress_data['layers_norm'][layer_name]
        ax2.plot(stress_data['time'], values, 
                color=color, linewidth=2.5, alpha=0.9,
                label=layer_name)
    
    ax2.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Normalized Activity [0-1]', fontsize=12, fontweight='bold')
    ax2.set_title('Stress Pathway (Low ATP = 300 mM)\nInverted Layer Activation', 
                 fontsize=13, fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    # ax2.legend(loc='upper left', fontsize=10, framealpha=0.95)  # Removed for manuscript
    ax2.set_xlim(0, stress_data['time'][-1])
    ax2.set_ylim(-0.05, 1.1)
    
    # Overall title
    fig.suptitle('Hierarchical Layer Decision Cascade: Normal vs Stress Pathways',
                fontsize=15, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save figure
    output_file = Path('figures/decision_cascade.png')
    plt.savefig(output_file, format='png', dpi=200, bbox_inches='tight')
    
    # Also save PDF
    output_pdf = Path('figures/decision_cascade.pdf')
    plt.savefig(output_pdf, format='pdf', dpi=200, bbox_inches='tight')

if __name__ == '__main__':
    plot_decision_cascade()
