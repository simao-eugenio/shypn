#!/usr/bin/env python3
"""
Generate Basin of Attraction Figure for Bacillus Sporulation Decision
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
DATA_NORMAL = Path("workspace/projects/My_Project/thermodynamics/data/simulation_data_normal.csv")
DATA_STRESS = Path("workspace/projects/My_Project/thermodynamics/data/simulation_data_stress_analysis.csv")

# Create custom colormap: dark blue → cyan → yellow → orange → red (cool to hot)
colors = ['#000033', '#000066', '#003399', '#0066cc', '#0099ff',
          '#00ccff', '#66ffff', '#ffff99', '#ffcc66', '#ff9933', 
          '#ff6600', '#ff3300', '#cc0000']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('basin_hot', colors, N=n_bins)

def load_trajectory(csv_file):
    """Load final state from simulation data."""
    with open(csv_file, 'r') as f:
        data = list(csv.DictReader(f))
    
    if not data:
        return None
    
    # Extract key state variables (final values)
    final = data[-1]
    return {
        'sigmaf': float(final['SigmaF (mM)']),
        'forespore': float(final['Forespore (mM)']),
        'atp_initial': float(data[0]['ATP_pool (mM)']),
        'atp_final': float(final['ATP_pool (mM)'])
    }

def load_full_trajectory(csv_file):
    """Load full trajectory for plotting."""
    with open(csv_file, 'r') as f:
        data = list(csv.DictReader(f))
    
    sigmaf = [float(row['SigmaF (mM)']) for row in data]
    forespore = [float(row['Forespore (mM)']) for row in data]
    
    return sigmaf, forespore

def plot_basin_attraction():
    """Create clean basin of attraction plot."""
    
    # Load final states
    normal_state = load_trajectory(DATA_NORMAL)
    stress_state = load_trajectory(DATA_STRESS)
    
    if not normal_state or not stress_state:
        print("Error: Could not load trajectory data")
        return
    
    # Define attractors for Bacillus sporulation
    attractor_SPORE = np.array([stress_state['sigmaf'], stress_state['forespore']])  # Sporulation attractor
    attractor_VEG = np.array([0.0, 0.0])  # Vegetative growth attractor
    
    # Create grid for basin of attraction
    SigmaF = np.linspace(0, max(attractor_SPORE[0] * 1.2, 20), 300)
    Forespore = np.linspace(0, max(attractor_SPORE[1] * 1.2, 20), 300)
    SigmaF_grid, Forespore_grid = np.meshgrid(SigmaF, Forespore)
    
    # Calculate basin of attraction (distance-based potential)
    dist_to_SPORE = np.sqrt((SigmaF_grid - attractor_SPORE[0])**2 + (Forespore_grid - attractor_SPORE[1])**2)
    dist_to_VEG = np.sqrt(SigmaF_grid**2 + Forespore_grid**2)
    
    # Attraction field: negative for SPORE basin, positive for VEG basin
    attraction_field = np.tanh((dist_to_VEG - dist_to_SPORE) * 0.3)
    
    # Create figure with single subplot (clean)
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    
    # Plot contour with smooth gradient
    levels = np.linspace(-1, 1, 50)  # More levels for smoother transition
    contourf = ax.contourf(SigmaF_grid, Forespore_grid, attraction_field, 
                           levels=levels, cmap=cmap, alpha=0.95)
    
    # Add subtle contour lines for structure
    ax.contour(SigmaF_grid, Forespore_grid, attraction_field, 
              levels=levels[::5], colors='black', linewidths=0.3, alpha=0.15)
    
    # Plot attractors with minimal style
    ax.scatter([attractor_SPORE[0]], [attractor_SPORE[1]], 
              color='darkred', s=300, marker='o', 
              edgecolors='white', linewidth=2.5, 
              label='Sporulation', zorder=5)
    ax.scatter([attractor_VEG[0]], [attractor_VEG[1]], 
              color='navy', s=300, marker='o', 
              edgecolors='white', linewidth=2.5, 
              label='Vegetative', zorder=5)
    
    # Load trajectories for plotting
    sigmaf_normal, forespore_normal = load_full_trajectory(DATA_NORMAL)
    sigmaf_stress, forespore_stress = load_full_trajectory(DATA_STRESS)
    
    # NORMAL trajectory (High ATP → gradual sporulation)
    # Subsample for cleaner visualization
    step = max(len(sigmaf_normal) // 20, 1)
    ax.plot(sigmaf_normal[::step], forespore_normal[::step], 
           color='white', linewidth=2.5, alpha=0.9, zorder=4)
    ax.arrow(sigmaf_normal[-2], forespore_normal[-2], 
            sigmaf_normal[-1] - sigmaf_normal[-2], 
            forespore_normal[-1] - forespore_normal[-2],
            head_width=0.8, head_length=0.5, fc='white', ec='white', 
            linewidth=2, zorder=4)
    
    # STRESS trajectory (Low ATP → rapid sporulation)
    step_stress = max(len(sigmaf_stress) // 20, 1)
    ax.plot(sigmaf_stress[::step_stress], forespore_stress[::step_stress], 
           color='black', linewidth=2.5, alpha=0.9, zorder=4)
    ax.arrow(sigmaf_stress[-2], forespore_stress[-2], 
            sigmaf_stress[-1] - sigmaf_stress[-2], 
            forespore_stress[-1] - forespore_stress[-2],
            head_width=0.8, head_length=0.5, fc='black', ec='black', 
            linewidth=2, zorder=4)
    
    # Text annotations with matching background colors
    ax.text(0.98, 0.12, f'High ATP\n({normal_state["atp_initial"]:.0f} mM)', 
           fontsize=10, color='white', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='#cc0000', alpha=0.8, edgecolor='white', linewidth=1.5),
           transform=ax.transAxes, ha='right', va='bottom')
    ax.text(0.98, 0.02, f'Low ATP\n({stress_state["atp_initial"]:.0f} mM)', 
           fontsize=10, color='white', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='#003366', alpha=0.8, edgecolor='white', linewidth=1.5),
           transform=ax.transAxes, ha='right', va='bottom')
    
    # Clean axis labels
    ax.set_xlabel('σF (SigmaF) [mM]', fontsize=13, fontweight='normal')
    ax.set_ylabel('Forespore Commitment [mM]', fontsize=13, fontweight='normal')
    ax.set_title('Basin of Attraction: Bacillus Sporulation Decision', 
                fontsize=14, fontweight='bold', pad=15)
    
    # Add colorbar with minimal style
    cbar = plt.colorbar(contourf, ax=ax, label='Basin Field', pad=0.02)
    cbar.set_ticks([-1, 0, 1])
    cbar.set_ticklabels(['Vegetative', 'Boundary', 'Sporulation'])
    
    # Clean legend
    ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    
    # Set axis limits for clean presentation
    ax.set_xlim(0, max(SigmaF))
    ax.set_ylim(0, max(Forespore))
    
    plt.tight_layout()
    
    # Save with high resolution
    output_file = Path('workspace/projects/My_Project/thermodynamics/figures/bacillus_basin_of_attraction.png')
    plt.savefig(output_file, format='png', dpi=200, bbox_inches='tight')
    
    # Also save PDF
    output_pdf = Path('figures/bacillus_basin_of_attraction.pdf')
    plt.savefig(output_pdf, format='pdf', dpi=200, bbox_inches='tight')

if __name__ == '__main__':
    plot_basin_attraction()
