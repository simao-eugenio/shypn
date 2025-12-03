#!/usr/bin/env python3
"""
Generate parallel simulation speedup plot for the paper.
Data from Chapter 5 thesis (Table: Parallel execution performance on glycolysis)
"""

import matplotlib.pyplot as plt
import numpy as np

# Data from thesis Table 5.1
cores = np.array([1, 2, 4, 8])
execution_time = np.array([12.4, 7.8, 4.9, 3.2])  # seconds
speedup = np.array([1.0, 1.6, 2.5, 3.9])
efficiency = np.array([100, 80, 63, 49])  # percentage

# Ideal linear speedup (for comparison)
ideal_speedup = cores

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

# Plot 1: Speedup vs Cores
ax1.plot(cores, speedup, 'o-', linewidth=2, markersize=8, label='Weak Independence', color='#2E86AB')
ax1.plot(cores, ideal_speedup, '--', linewidth=1.5, label='Ideal Linear', color='gray', alpha=0.7)
ax1.set_xlabel('Number of Cores', fontsize=11)
ax1.set_ylabel('Speedup (×)', fontsize=11)
ax1.set_title('Parallel Simulation Speedup', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(fontsize=10)
ax1.set_xticks(cores)
ax1.set_xlim([0.5, 8.5])
ax1.set_ylim([0, 9])

# Add annotations for key points
for i, (c, s) in enumerate(zip(cores, speedup)):
    ax1.annotate(f'{s:.1f}×', 
                xy=(c, s), 
                xytext=(0, 10), 
                textcoords='offset points',
                ha='center',
                fontsize=9,
                color='#2E86AB',
                fontweight='bold')

# Plot 2: Efficiency vs Cores
ax2.bar(cores, efficiency, width=0.8, color='#A23B72', alpha=0.8, edgecolor='black', linewidth=1.2)
ax2.axhline(y=100, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='100% Efficiency')
ax2.set_xlabel('Number of Cores', fontsize=11)
ax2.set_ylabel('Efficiency (%)', fontsize=11)
ax2.set_title('Parallel Efficiency', fontsize=12, fontweight='bold')
ax2.grid(True, axis='y', alpha=0.3, linestyle='--')
ax2.legend(fontsize=10)
ax2.set_xticks(cores)
ax2.set_xlim([0, 9])
ax2.set_ylim([0, 110])

# Add efficiency values on bars
for c, eff in zip(cores, efficiency):
    ax2.text(c, eff + 3, f'{eff}%', 
            ha='center', va='bottom', 
            fontsize=9, 
            fontweight='bold',
            color='#A23B72')

plt.tight_layout()
plt.savefig('/home/simao/projetos/shypn/doc/papers/figures/speedup_plot.pdf', 
            bbox_inches='tight', 
            dpi=300)
print("✅ Generated: figures/speedup_plot.pdf")

# Also save as PNG for preview
plt.savefig('/home/simao/projetos/shypn/doc/papers/figures/speedup_plot.png', 
            bbox_inches='tight', 
            dpi=150)
print("✅ Generated: figures/speedup_plot.png (preview)")

plt.close()
