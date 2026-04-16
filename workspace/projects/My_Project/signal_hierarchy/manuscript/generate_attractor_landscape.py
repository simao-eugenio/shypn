#!/usr/bin/env python3
"""
Generate 3D attractor landscape visualization showing hierarchical preemption
through decision space collapse in Lambda phage lysis-lysogeny decision.

Shows three scenarios:
1. Bistable baseline (two attractors)
2. Monostable lysogenic (Low RecA - CII saturated)
3. Monostable lytic (High RecA - CII subsaturated)
"""

import sys
# Remove system paths to avoid matplotlib conflicts
sys.path = [p for p in sys.path if 'dist-packages' not in p]

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

def potential_bistable(CI, Cro):
    """
    Bistable potential landscape with two attractors:
    - Lysogenic attractor (high CI, low Cro)
    - Lytic attractor (low CI, high Cro)
    """
    # Double-well potential
    V = (CI**2 - 100)**2 / 10000 + (Cro**2 - 100)**2 / 10000 - 0.5 * (CI * Cro) / 2500
    return V

def potential_monostable_lysogenic(CI, Cro):
    """
    Monostable lysogenic (Low RecA context):
    Deep single attractor at high CI, low Cro
    CII saturated - all paths lead to lysogenic
    """
    # Single deep well at lysogenic state
    V = ((CI - 120)**2 + (Cro - 20)**2) / 5000 + 0.5
    return V

def potential_monostable_lytic(CI, Cro):
    """
    Monostable lytic (High RecA context):
    Deep single attractor at low CI, high Cro
    CII subsaturated - most paths lead to lytic, 15% escape to lysogenic
    """
    # Single deep well at lytic state with shallow escape route
    V_lytic = ((CI - 20)**2 + (Cro - 120)**2) / 5000
    # Shallow escape route to lysogenic (15% probability)
    V_escape = 3.0 * np.exp(-((CI - 100)**2 + (Cro - 30)**2) / 3000)
    V = V_lytic - V_escape + 0.5
    return V

# Create grid
CI = np.linspace(0, 150, 100)
Cro = np.linspace(0, 150, 100)
CI_grid, Cro_grid = np.meshgrid(CI, Cro)

# Calculate potentials
V_bistable = potential_bistable(CI_grid, Cro_grid)
V_lysogenic = potential_monostable_lysogenic(CI_grid, Cro_grid)
V_lytic = potential_monostable_lytic(CI_grid, Cro_grid)

# Create figure with three 3D subplots
fig = plt.figure(figsize=(15, 5))

# Subplot 1: Bistable
ax1 = fig.add_subplot(131, projection='3d')
surf1 = ax1.plot_surface(CI_grid, Cro_grid, V_bistable, cmap=cm.viridis, 
                          linewidth=0, antialiased=True, alpha=0.8)
ax1.set_xlabel('CI (mM)', fontsize=10)
ax1.set_ylabel('Cro (mM)', fontsize=10)
ax1.set_zlabel('Potential Energy', fontsize=10)
ax1.set_title('Bistable Baseline\n(RecA variable)', fontsize=11, fontweight='bold')
ax1.view_init(elev=25, azim=45)
# Mark attractors
ax1.scatter([100], [20], [potential_bistable(100, 20)], color='blue', s=100, 
            marker='o', edgecolors='white', linewidth=2, label='Lysogenic')
ax1.scatter([20], [100], [potential_bistable(20, 100)], color='red', s=100, 
            marker='o', edgecolors='white', linewidth=2, label='Lytic')
ax1.legend(loc='upper left', fontsize=8)

# Subplot 2: Monostable Lysogenic
ax2 = fig.add_subplot(132, projection='3d')
surf2 = ax2.plot_surface(CI_grid, Cro_grid, V_lysogenic, cmap=cm.viridis, 
                          linewidth=0, antialiased=True, alpha=0.8)
ax2.set_xlabel('CI (mM)', fontsize=10)
ax2.set_ylabel('Cro (mM)', fontsize=10)
ax2.set_zlabel('Potential Energy', fontsize=10)
ax2.set_title('Monostable Lysogenic\n(Low RecA, CII saturated, 98%)', 
              fontsize=11, fontweight='bold')
ax2.view_init(elev=25, azim=45)
# Mark single attractor
ax2.scatter([120], [20], [potential_monostable_lysogenic(120, 20)], color='blue', 
            s=150, marker='o', edgecolors='white', linewidth=2, label='Lysogenic')
ax2.legend(loc='upper left', fontsize=8)

# Subplot 3: Monostable Lytic
ax3 = fig.add_subplot(133, projection='3d')
surf3 = ax3.plot_surface(CI_grid, Cro_grid, V_lytic, cmap=cm.viridis, 
                          linewidth=0, antialiased=True, alpha=0.8)
ax3.set_xlabel('CI (mM)', fontsize=10)
ax3.set_ylabel('Cro (mM)', fontsize=10)
ax3.set_zlabel('Potential Energy', fontsize=10)
ax3.set_title('Monostable Lytic\n(High RecA, CII subsaturated, 85%)', 
              fontsize=11, fontweight='bold')
ax3.view_init(elev=25, azim=45)
# Mark main attractor and escape route
ax3.scatter([20], [120], [potential_monostable_lytic(20, 120)], color='red', 
            s=150, marker='o', edgecolors='white', linewidth=2, label='Lytic (85%)')
ax3.scatter([100], [30], [potential_monostable_lytic(100, 30)], color='orange', 
            s=80, marker='^', edgecolors='white', linewidth=2, label='Escape (15%)')
ax3.legend(loc='upper left', fontsize=8)

plt.tight_layout()

# Save as PDF
output_path = 'figure2_attractor_landscapes.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"Figure saved to: {output_path}")

# Also save as PNG for quick preview
plt.savefig('figure2_attractor_landscapes.png', format='png', dpi=150, bbox_inches='tight')
print(f"Preview saved to: figure2_attractor_landscapes.png")

# Don't show - we're using Agg backend
# plt.show()
