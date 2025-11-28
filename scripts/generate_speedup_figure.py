#!/usr/bin/env python3
"""
Generate parallel speedup figure for Bioinformatics paper.
Based on data from Chapter 11 (glycolysis pathway).
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# Use non-interactive backend
matplotlib.use('Agg')

# Data from thesis Chapter 11, Table: Parallel execution speedup for glycolysis pathway
cores = np.array([1, 2, 4, 8])
runtime = np.array([2.30, 1.45, 0.98, 0.72])  # seconds
speedup = np.array([1.0, 1.6, 2.3, 3.2])

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(6, 4))

# Plot actual speedup
ax.plot(cores, speedup, 'o-', linewidth=2, markersize=8, 
        label='Weak Independence', color='#2E86AB')

# Plot ideal linear speedup for reference
ideal_speedup = cores / cores[0]
ax.plot(cores, ideal_speedup, '--', linewidth=1.5, 
        label='Ideal Linear', color='#A23B72', alpha=0.7)

# Formatting
ax.set_xlabel('Number of Cores', fontsize=11, fontweight='bold')
ax.set_ylabel('Speedup', fontsize=11, fontweight='bold')
ax.set_title('Parallel Simulation Speedup\n(Glycolysis Pathway)', 
             fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

# Set x-axis to show core counts
ax.set_xticks(cores)
ax.set_xticklabels(cores)

# Set reasonable y-axis limits
ax.set_ylim([0, 9])
ax.set_yticks([0, 2, 4, 6, 8])

# Add efficiency annotation
efficiency_8cores = (speedup[-1] / cores[-1]) * 100
ax.text(7.5, 3.5, f'Efficiency: {efficiency_8cores:.0f}%', 
        fontsize=9, ha='right', style='italic', color='#333333')

# Tight layout
plt.tight_layout()

# Save figure
output_path = 'doc/papers/bioinformatics/figures/parallel_speedup.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"✅ Generated: {output_path}")

# Also save as PNG for preview
output_png = 'doc/papers/bioinformatics/figures/parallel_speedup.png'
plt.savefig(output_png, format='png', dpi=150, bbox_inches='tight')
print(f"✅ Generated: {output_png}")

plt.close()
