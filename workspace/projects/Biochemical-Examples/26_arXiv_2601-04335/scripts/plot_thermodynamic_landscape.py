#!/usr/bin/env python3
"""
Generate Thermodynamic Landscape Figure for Bacillus Sporulation
Created: January 4, 2026
For manuscript: "Thermodynamic Framework for Hierarchical Signal Theory"
Shows free energy landscape and ATP-driven commitment
"""

import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

# Data files
DATA_NORMAL = Path("workspace/projects/My_Project/thermodynamics/data/simulation_data_normal.csv")
DATA_STRESS = Path("workspace/projects/My_Project/thermodynamics/data/simulation_data_stress_analysis.csv")

# Create custom colormap: dark blue → purple → dark red (low to high energy)
colors = ['#00001a', '#000033', '#00004d', '#000066', '#1a004d',
          '#330066', '#4d0066', '#660052', '#800033', '#990000', 
          '#b30000', '#cc0000', '#e60000']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('energy_landscape', colors, N=n_bins)

def load_thermodynamic_data(csv_file):
    """Load ATP and commitment state data."""
    with open(csv_file, 'r') as f:
        data = list(csv.DictReader(f))
    
    if not data:
        return None
    
    atp = np.array([float(row['ATP_pool (mM)']) for row in data])
    forespore = np.array([float(row['Forespore (mM)']) for row in data])
    sigmaf = np.array([float(row['SigmaF (mM)']) for row in data])
    
    # Commitment coordinate: combined SigmaF + Forespore
    commitment = sigmaf + forespore
    
    return {
        'atp': atp,
        'commitment': commitment,
        'atp_initial': atp[0],
        'atp_final': atp[-1],
        'commitment_final': commitment[-1]
    }

def plot_thermodynamic_landscape():
    """Create thermodynamic free energy landscape plot."""
    
    # Load data
    normal_data = load_thermodynamic_data(DATA_NORMAL)
    stress_data = load_thermodynamic_data(DATA_STRESS)
    
    if not normal_data or not stress_data:
        print("Error: Could not load thermodynamic data")
        return
    
    # Create grid for free energy landscape
    ATP = np.linspace(0, 5500, 300)
    Commitment = np.linspace(0, 50, 300)
    ATP_grid, Commitment_grid = np.meshgrid(ATP, Commitment)
    
    # Model free energy landscape
    # Low ATP → high barrier for commitment (ATP-dependent pathway blocked)
    # High ATP → lower barrier for commitment (normal pathway accessible)
    # Energy minima at: (ATP_high, Committed) and (ATP_low, Uncommitted)
    
    # Free energy function (arbitrary units scaled appropriately)
    # Barrier height depends on ATP availability
    barrier_height = 50 * np.exp(-ATP_grid / 2000)  # High barrier when ATP low
    commitment_cost = 0.01 * (Commitment_grid - 25)**2  # Quadratic well at commitment
    atp_depletion_cost = 0.00001 * (ATP_grid - 2500)**2  # Optimal ATP around 2500
    
    # Combined free energy landscape
    free_energy = barrier_height + commitment_cost + atp_depletion_cost
    
    # Normalize to [0, 1] for visualization
    free_energy = (free_energy - free_energy.min()) / (free_energy.max() - free_energy.min())
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    
    # Plot contour with smooth gradient (inverted: low energy = hot/red, high energy = cold/blue)
    levels = np.linspace(0, 1, 50)
    contourf = ax.contourf(ATP_grid, Commitment_grid, 1 - free_energy,  # Invert for visual clarity
                           levels=levels, cmap=cmap, alpha=0.95)
    
    # Add subtle contour lines
    ax.contour(ATP_grid, Commitment_grid, 1 - free_energy, 
              levels=levels[::5], colors='black', linewidths=0.3, alpha=0.15)
    
    # Plot NORMAL trajectory (High ATP → gradual commitment)
    ax.plot(normal_data['atp'], normal_data['commitment'], 
           color='white', linewidth=3, alpha=0.95, zorder=4)
    # Arrow at end
    ax.arrow(normal_data['atp'][-2], normal_data['commitment'][-2],
            normal_data['atp'][-1] - normal_data['atp'][-2],
            normal_data['commitment'][-1] - normal_data['commitment'][-2],
            head_width=1.5, head_length=100, fc='white', ec='white',
            linewidth=2.5, zorder=4)
    
    # Plot STRESS trajectory (Low ATP → rapid commitment)
    # Add gray outline for visibility against dark blue
    ax.plot(stress_data['atp'], stress_data['commitment'], 
           color='lightgray', linewidth=5, alpha=0.6, zorder=3)
    ax.plot(stress_data['atp'], stress_data['commitment'], 
           color='black', linewidth=3, alpha=0.95, zorder=4)
    # Arrow at end
    ax.arrow(stress_data['atp'][-2], stress_data['commitment'][-2],
            stress_data['atp'][-1] - stress_data['atp'][-2],
            stress_data['commitment'][-1] - stress_data['commitment'][-2],
            head_width=1.5, head_length=100, fc='black', ec='black',
            linewidth=2.5, zorder=4)
    
    # Mark initial states
    ax.scatter([normal_data['atp_initial']], [0], 
              color='white', s=250, marker='o', edgecolors='navy', linewidth=3,
              zorder=5, label='Normal Start')
    ax.scatter([stress_data['atp_initial']], [0], 
              color='black', s=250, marker='o', edgecolors='red', linewidth=3,
              zorder=5, label='Stress Start')
    
    # Mark final states (attractor)
    commitment_attractor = max(normal_data['commitment_final'], stress_data['commitment_final'])
    ax.scatter([normal_data['atp_final']], [normal_data['commitment_final']], 
              color='darkred', s=300, marker='*', edgecolors='white', linewidth=2.5,
              zorder=5)
    ax.scatter([stress_data['atp_final']], [stress_data['commitment_final']], 
              color='darkred', s=300, marker='*', edgecolors='white', linewidth=2.5,
              zorder=5)
    
    # Axis labels
    ax.set_xlabel('ATP Pool [mM]', fontsize=13, fontweight='bold')
    ax.set_ylabel('Commitment Coordinate [σF + Forespore, mM]', fontsize=13, fontweight='bold')
    ax.set_title('Thermodynamic Free Energy Landscape for Sporulation Decision',
                fontsize=14, fontweight='bold', pad=15)
    
    # Colorbar
    cbar = plt.colorbar(contourf, ax=ax, label='Relative Free Energy', pad=0.02)
    cbar.set_ticks([0, 0.5, 1])
    cbar.set_ticklabels(['High\n(Barrier)', 'Medium', 'Low\n(Favorable)'])
    
    # Legend
    legend = ax.legend(loc='upper left', fontsize=11, framealpha=0.3)
    plt.setp(legend.get_texts(), color='white')
    legend.get_frame().set_edgecolor('white')
    legend.get_frame().set_linewidth(1.5)
    
    # Limits
    ax.set_xlim(0, 5500)
    ax.set_ylim(0, 50)
    
    plt.tight_layout()
    
    # Save figure
    output_file = Path('workspace/projects/My_Project/thermodynamics/figures/thermodynamic_landscape.png')
    plt.savefig(output_file, format='png', dpi=200, bbox_inches='tight')
    
    # Also save PDF
    output_pdf = Path('figures/thermodynamic_landscape.pdf')
    plt.savefig(output_pdf, format='pdf', dpi=200, bbox_inches='tight')

if __name__ == '__main__':
    plot_thermodynamic_landscape()
