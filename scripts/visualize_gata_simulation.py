#!/usr/bin/env python3
"""
Visualize GATA1/PU1 simulation data trajectories
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Read the simulation data
data_path = Path("workspace/projects/gata/data/simulation_data.csv")
df = pd.read_csv(data_path)

# Convert time to minutes
time_min = df['Time (s)'] / 60

# Create figure with multiple subplots
fig, axes = plt.subplots(3, 2, figsize=(14, 10))
fig.suptitle('GATA1/PU1 Gene Regulatory Network Simulation', fontsize=14, fontweight='bold')

# 1. Nuclear protein dynamics (main pathway)
ax = axes[0, 0]
ax.plot(time_min, df['GATA1_Protein_nuc (mM)'], 'r-', label='GATA1', linewidth=2)
ax.plot(time_min, df['PU1_Protein_nuc (mM)'], 'b-', label='PU1', linewidth=2)
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Concentration (mM)')
ax.set_title('Nuclear Transcription Factors')
ax.legend()
ax.grid(True, alpha=0.3)

# 2. Nuclear mRNA levels
ax = axes[0, 1]
ax.plot(time_min, df['GATA1_mRNA_nuc (mM)'], 'r-', label='GATA1 mRNA', linewidth=2)
ax.plot(time_min, df['PU1_mRNA_nuc (mM)'], 'b-', label='PU1 mRNA', linewidth=2)
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Concentration (mM)')
ax.set_title('Nuclear mRNA Levels')
ax.legend()
ax.grid(True, alpha=0.3)

# 3. External signals
ax = axes[1, 0]
ax.plot(time_min, df['EPO_external (mM)'], 'r-', label='EPO', linewidth=2)
ax.plot(time_min, df['GCSF_external (mM)'], 'b-', label='GCSF', linewidth=2)
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Concentration (mM)')
ax.set_title('External Growth Factors')
ax.legend()
ax.grid(True, alpha=0.3)

# 4. Energy metabolism (ATP)
ax = axes[1, 1]
ax.plot(time_min, df['ATP (mM)'], 'g-', label='ATP', linewidth=2)
ax.plot(time_min, df['ADP (mM)'], 'orange', label='ADP', linewidth=2)
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Concentration (mM)')
ax.set_title('ATP/ADP Energy Metabolism')
ax.legend()
ax.grid(True, alpha=0.3)

# 5. Cytoplasmic protein dynamics
ax = axes[2, 0]
ax.plot(time_min, df['GATA1_Protein_cyto (mM)'], 'r-', label='GATA1', linewidth=2)
ax.plot(time_min, df['PU1_Protein_cyto (mM)'], 'b-', label='PU1', linewidth=2)
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Concentration (mM)')
ax.set_title('Cytoplasmic Proteins')
ax.legend()
ax.grid(True, alpha=0.3)

# 6. GATA1/PU1 ratio over time
ax = axes[2, 1]
ratio = df['GATA1_Protein_nuc (mM)'] / (df['PU1_Protein_nuc (mM)'] + 1e-10)
ax.plot(time_min, ratio, 'purple', linewidth=2)
ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Balance')
ax.axhline(y=1.2, color='r', linestyle=':', alpha=0.5, label='GATA1-dominant')
ax.axhline(y=0.8, color='b', linestyle=':', alpha=0.5, label='PU1-dominant')
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Ratio')
ax.set_title('GATA1/PU1 Nuclear Protein Ratio')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
output_path = Path("workspace/projects/gata/data/simulation_trajectories.png")
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Plot saved to: {output_path}")
plt.close()

# Create a second figure focusing on the final steady state
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle('GATA1/PU1 Simulation - Final Steady State (last 5 minutes)', 
             fontsize=14, fontweight='bold')

# Use only last 5 minutes
cutoff_time = df['Time (s)'].max() - 300
final_df = df[df['Time (s)'] >= cutoff_time].copy()
final_time = (final_df['Time (s)'] - cutoff_time) / 60

# Nuclear proteins closeup
ax = axes[0, 0]
ax.plot(final_time, final_df['GATA1_Protein_nuc (mM)'], 'r-', label='GATA1', linewidth=2)
ax.plot(final_time, final_df['PU1_Protein_nuc (mM)'], 'b-', label='PU1', linewidth=2)
ax.set_xlabel('Time from t=45 min (minutes)')
ax.set_ylabel('Concentration (mM)')
ax.set_title('Nuclear Proteins (Final State)')
ax.legend()
ax.grid(True, alpha=0.3)

# mRNA levels closeup
ax = axes[0, 1]
ax.plot(final_time, final_df['GATA1_mRNA_nuc (mM)'], 'r-', label='GATA1', linewidth=2)
ax.plot(final_time, final_df['PU1_mRNA_nuc (mM)'], 'b-', label='PU1', linewidth=2)
ax.set_xlabel('Time from t=45 min (minutes)')
ax.set_ylabel('Concentration (mM)')
ax.set_title('Nuclear mRNA (Final State)')
ax.legend()
ax.grid(True, alpha=0.3)

# ATP detail
ax = axes[1, 0]
ax.plot(final_time, final_df['ATP (mM)'], 'g-', linewidth=2)
ax.set_xlabel('Time from t=45 min (minutes)')
ax.set_ylabel('ATP Concentration (mM)')
ax.set_title('ATP Level (Final State)')
ax.grid(True, alpha=0.3)

# Ratio detail
ax = axes[1, 1]
final_ratio = final_df['GATA1_Protein_nuc (mM)'] / (final_df['PU1_Protein_nuc (mM)'] + 1e-10)
ax.plot(final_time, final_ratio, 'purple', linewidth=2)
ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
mean_ratio = final_ratio.mean()
ax.axhline(y=mean_ratio, color='green', linestyle='-', alpha=0.7, 
           label=f'Mean: {mean_ratio:.3f}')
ax.set_xlabel('Time from t=45 min (minutes)')
ax.set_ylabel('GATA1/PU1 Ratio')
ax.set_title('Ratio Stability')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
output_path2 = Path("workspace/projects/gata/data/simulation_steady_state.png")
plt.savefig(output_path2, dpi=150, bbox_inches='tight')
print(f"Plot saved to: {output_path2}")
plt.close()

print("\nVisualization complete!")
