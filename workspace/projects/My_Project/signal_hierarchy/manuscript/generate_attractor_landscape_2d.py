#!/usr/bin/env python3
"""
Generate 2D contour attractor landscape visualization showing hierarchical preemption
through decision space collapse in Lambda phage lysis-lysogeny decision.

Shows three scenarios:
1. Bistable baseline (two attractors)
2. Monostable lysogenic (Low RecA - CII saturated)
3. Monostable lytic (High RecA - CII subsaturated)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

def potential_bistable(CI, Cro):
    """Bistable potential landscape with two attractors"""
    V = (CI**2 - 100)**2 / 10000 + (Cro**2 - 100)**2 / 10000 - 0.5 * (CI * Cro) / 2500
    return V

def potential_monostable_lysogenic(CI, Cro):
    """Monostable lysogenic (Low RecA context)"""
    V = ((CI - 120)**2 + (Cro - 20)**2) / 5000 + 0.5
    return V

def potential_monostable_lytic(CI, Cro):
    """Monostable lytic (High RecA context)"""
    V_lytic = ((CI - 20)**2 + (Cro - 120)**2) / 5000
    V_escape = 3.0 * np.exp(-((CI - 100)**2 + (Cro - 30)**2) / 3000)
    V = V_lytic - V_escape + 0.5
    return V

# Create grid
CI = np.linspace(0, 150, 200)
Cro = np.linspace(0, 150, 200)
CI_grid, Cro_grid = np.meshgrid(CI, Cro)

# Calculate potentials
V_bistable = potential_bistable(CI_grid, Cro_grid)
V_lysogenic = potential_monostable_lysogenic(CI_grid, Cro_grid)
V_lytic = potential_monostable_lytic(CI_grid, Cro_grid)

# Create figure with three contour subplots
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Subplot 1: Bistable
levels = np.linspace(V_bistable.min(), V_bistable.max(), 20)
contour1 = axes[0].contourf(CI_grid, Cro_grid, V_bistable, levels=levels, cmap='viridis')
axes[0].contour(CI_grid, Cro_grid, V_bistable, levels=levels, colors='black', linewidths=0.5, alpha=0.3)
axes[0].scatter([100], [20], color='blue', s=200, marker='o', edgecolors='white', linewidth=2, label='Lysogenic', zorder=5)
axes[0].scatter([20], [100], color='red', s=200, marker='o', edgecolors='white', linewidth=2, label='Lytic', zorder=5)
axes[0].set_xlabel('CI (mM)', fontsize=11)
axes[0].set_ylabel('Cro (mM)', fontsize=11)
axes[0].set_title('Bistable Baseline\n(RecA variable)', fontsize=12, fontweight='bold')
axes[0].legend(loc='upper right', fontsize=9)
axes[0].set_aspect('equal')
plt.colorbar(contour1, ax=axes[0], label='Potential Energy')

# Subplot 2: Monostable Lysogenic
levels = np.linspace(V_lysogenic.min(), V_lysogenic.max(), 20)
contour2 = axes[1].contourf(CI_grid, Cro_grid, V_lysogenic, levels=levels, cmap='viridis')
axes[1].contour(CI_grid, Cro_grid, V_lysogenic, levels=levels, colors='black', linewidths=0.5, alpha=0.3)
axes[1].scatter([120], [20], color='blue', s=300, marker='o', edgecolors='white', linewidth=3, label='Lysogenic', zorder=5)
axes[1].set_xlabel('CI (mM)', fontsize=11)
axes[1].set_ylabel('Cro (mM)', fontsize=11)
axes[1].set_title('Monostable Lysogenic\n(Low RecA, CII saturated, 98%)', fontsize=12, fontweight='bold')
axes[1].legend(loc='upper right', fontsize=9)
axes[1].set_aspect('equal')
plt.colorbar(contour2, ax=axes[1], label='Potential Energy')

# Subplot 3: Monostable Lytic
levels = np.linspace(V_lytic.min(), V_lytic.max(), 20)
contour3 = axes[2].contourf(CI_grid, Cro_grid, V_lytic, levels=levels, cmap='viridis')
axes[2].contour(CI_grid, Cro_grid, V_lytic, levels=levels, colors='black', linewidths=0.5, alpha=0.3)
axes[2].scatter([20], [120], color='red', s=300, marker='o', edgecolors='white', linewidth=3, label='Lytic (85%)', zorder=5)
axes[2].scatter([100], [30], color='orange', s=150, marker='^', edgecolors='white', linewidth=2, label='Escape (15%)', zorder=5)
axes[2].set_xlabel('CI (mM)', fontsize=11)
axes[2].set_ylabel('Cro (mM)', fontsize=11)
axes[2].set_title('Monostable Lytic\n(High RecA, CII subsaturated, 85%)', fontsize=12, fontweight='bold')
axes[2].legend(loc='upper right', fontsize=9)
axes[2].set_aspect('equal')
plt.colorbar(contour3, ax=axes[2], label='Potential Energy')

plt.tight_layout()

# Save as PDF
output_path = 'figure2_attractor_landscapes.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"Figure saved to: {output_path}")

# Also save as PNG for quick preview
plt.savefig('figure2_attractor_landscapes.png', format='png', dpi=150, bbox_inches='tight')
print(f"Preview saved to: figure2_attractor_landscapes.png")

print("SUCCESS: 2D contour attractor landscapes generated!")
