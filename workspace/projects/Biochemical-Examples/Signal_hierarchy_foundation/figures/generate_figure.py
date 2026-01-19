#!/usr/bin/env python3
"""
Generate ATP threshold figure for B. subtilis sporulation manuscript.
Shows SHYPN prediction vs experimental validation.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Set publication-quality style
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 10
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['figure.dpi'] = 300

# ATP concentration range (mM)
atp_range = np.linspace(0, 5, 200)

# SHYPN model prediction (sigmoid)
def sigmoid(x, x0, k, L):
    """Sigmoid function for commitment probability"""
    return L / (1 + np.exp(-k * (x - x0)))

# Parameters fitted from SHYPN model
shypn_threshold = 2.38  # mM
steepness = 4.0  # Steepness of transition
max_prob = 0.95  # Maximum commitment probability

# Compute SHYPN prediction
commitment_prob = sigmoid(atp_range, shypn_threshold, steepness, max_prob)

# Experimental data point (Fujita & Losick 2005)
exp_threshold = 2.21  # mM
exp_error = 0.18  # mM (standard deviation)

# Create figure
fig, ax = plt.subplots(figsize=(6, 4))

# Color gradient based on 7% error barrier
# Navy blue for competence, firebrick for sporulation
error_barrier = (shypn_threshold + exp_threshold) / 2
ax.axvspan(0, error_barrier, alpha=1.0, color='navy', label='Competence Dominant', zorder=0)
ax.axvspan(error_barrier, 5, alpha=1.0, color='firebrick', label='Sporulation Dominant', zorder=0)

# SHYPN prediction curve
ax.plot(atp_range, commitment_prob, 'white', linewidth=2.5, label='SHYPN Model', zorder=3)

# Threshold lines
ax.axvline(shypn_threshold, color='darkblue', linestyle='--', linewidth=2, 
           label=f'SHYPN: {shypn_threshold} mM', zorder=2)
ax.axvline(exp_threshold, color='red', linestyle='--', linewidth=2, 
           label=f'Experiment: {exp_threshold} mM', zorder=2)

# Experimental error bar
ax.errorbar([exp_threshold], [0.5], xerr=[exp_error], 
            fmt='ro', markersize=8, capsize=5, capthick=2, 
            elinewidth=2, label='Fujita & Losick 2005', zorder=4)

# Labels and formatting
ax.set_xlabel('ATP Concentration (mM)', fontsize=11, fontweight='bold')
ax.set_ylabel('Sporulation Commitment Probability', fontsize=9, fontweight='bold')
ax.set_title('ATP Commitment Threshold in B. subtilis Sporulation', 
             fontsize=10, fontweight='bold', pad=10)
ax.set_xlim(0, 5)
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)

# Legend
ax.legend(loc='upper left', framealpha=0.9)

# Tight layout
plt.tight_layout()

# Save figure
plt.savefig('bacillus_atp_threshold.pdf', dpi=300, bbox_inches='tight')
plt.savefig('bacillus_atp_threshold.png', dpi=300, bbox_inches='tight')
print("✅ Figure generated: bacillus_atp_threshold.pdf")
print("✅ Figure generated: bacillus_atp_threshold.png (preview)")

plt.close()
