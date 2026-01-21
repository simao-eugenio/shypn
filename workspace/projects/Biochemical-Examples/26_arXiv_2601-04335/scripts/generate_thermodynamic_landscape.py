#!/usr/bin/env python3
"""
Generate thermodynamic landscape figure from actual simulation data.
Shows free energy landscape with normal (dark blue) and stress (hot red) pathways.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde
from matplotlib.colors import LinearSegmentedColormap

# Configure matplotlib for publication quality
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 11
plt.rcParams['font.family'] = 'serif'

# Load simulation data
print("Loading simulation data...")
normal = pd.read_csv('data/simulation_data_normal.csv', comment='#')
stress = pd.read_csv('data/simulation_data_stress_analysis.csv', comment='#')

# Create commitment coordinate (ξ = sporulation progress)
normal['xi'] = normal['SigmaF (mM)'] + normal['Forespore (mM)'] + normal['Mature_spore (mM)']
stress['xi'] = stress['SigmaF (mM)'] + stress['Forespore (mM)'] + stress['Mature_spore (mM)']

print(f"Normal pathway: ATP {normal['ATP_pool (mM)'].iloc[0]:.0f} → {normal['ATP_pool (mM)'].iloc[-1]:.0f} mM")
print(f"Stress pathway: ATP {stress['ATP_pool (mM)'].iloc[0]:.0f} → {stress['ATP_pool (mM)'].iloc[-1]:.0f} mM")
print(f"Stress ATP minimum: {stress['ATP_pool (mM)'].min():.2f} mM at t={stress.loc[stress['ATP_pool (mM)'].idxmin(), 'Time (s)']:.2f} s")

# Create figure
fig, ax = plt.subplots(figsize=(10, 7))

# Create energy landscape as background (2D density estimation)
# Combine both pathways for landscape
atp_combined = pd.concat([normal['ATP_pool (mM)'], stress['ATP_pool (mM)']])
xi_combined = pd.concat([normal['xi'], stress['xi']])

# Create grid for landscape
atp_grid = np.linspace(0, 5500, 200)
xi_grid = np.linspace(0, 100, 200)
ATP_grid, XI_grid = np.meshgrid(atp_grid, xi_grid)

# Estimate density (free energy landscape)
try:
    positions = np.vstack([atp_combined, xi_combined])
    kernel = gaussian_kde(positions)
    Z = kernel(np.vstack([ATP_grid.ravel(), XI_grid.ravel()]))
    Z = Z.reshape(ATP_grid.shape)
    
    # Convert density to "free energy" (negative log probability)
    Z_energy = -np.log(Z + 1e-10)
    Z_energy = (Z_energy - Z_energy.min()) / (Z_energy.max() - Z_energy.min())
    
    # Plot landscape with gray colormap
    im = ax.contourf(ATP_grid, XI_grid, Z_energy, levels=20, cmap='gray_r', alpha=0.3)
    
except:
    print("Warning: Could not generate KDE landscape, plotting without background")

# Plot trajectories with solid colors
# Normal pathway: dark blue
ax.plot(normal['ATP_pool (mM)'], normal['xi'], 
        color='#00008B', linewidth=3, label='Normal pathway', zorder=10)

# Stress pathway: hot red
ax.plot(stress['ATP_pool (mM)'], stress['xi'], 
        color='#DC143C', linewidth=3, label='Stress pathway', zorder=10)

# Mark critical points
# Find ATP minimum in stress pathway
idx_min = stress['ATP_pool (mM)'].idxmin()
atp_min = stress.loc[idx_min, 'ATP_pool (mM)']
xi_min = stress.loc[idx_min, 'xi']
time_min = stress.loc[idx_min, 'Time (s)']

# Mark ATP crisis point
ax.plot(atp_min, xi_min, 'r*', markersize=20, 
        markeredgecolor='black', markeredgewidth=1.5, zorder=15)

# Mark start and end points
ax.plot(normal['ATP_pool (mM)'].iloc[0], normal['xi'].iloc[0], 
        'o', color='#00008B', markersize=10, markeredgecolor='black', 
        markeredgewidth=1.5, zorder=12)
ax.plot(stress['ATP_pool (mM)'].iloc[0], stress['xi'].iloc[0], 
        'o', color='#DC143C', markersize=10, markeredgecolor='black', 
        markeredgewidth=1.5, zorder=12)

ax.plot(normal['ATP_pool (mM)'].iloc[-1], normal['xi'].iloc[-1], 
        's', color='#00008B', markersize=10, markeredgecolor='black', 
        markeredgewidth=1.5, zorder=12)
ax.plot(stress['ATP_pool (mM)'].iloc[-1], stress['xi'].iloc[-1], 
        's', color='#DC143C', markersize=10, markeredgecolor='black', 
        markeredgewidth=1.5, zorder=12)

# Labels and formatting
ax.set_xlabel('ATP pool (mM)', fontweight='bold')
ax.set_ylabel('Commitment coordinate ξ (mM)', fontweight='bold')
ax.set_title('Thermodynamic Landscape of Bacillus Sporulation', fontweight='bold', pad=20)

# Set limits
ax.set_xlim(0, 5500)
ax.set_ylim(0, 100)

# Legend
ax.legend(loc='upper left', framealpha=0.9)

# Grid
ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)

# Tight layout
plt.tight_layout()

# Save figure
output_file = 'thermodynamic_landscape.pdf'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nFigure saved: {output_file}")

# Also save as PNG for quick viewing
plt.savefig('thermodynamic_landscape.png', dpi=150, bbox_inches='tight')
print(f"Preview saved: thermodynamic_landscape.png")

plt.show()
