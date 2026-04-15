#!/usr/bin/env python3
"""
Generate clean oscillations figure for manuscript Figure 3.
Shows sustained periodic ERK-PP activation matching caption requirements.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.signal import find_peaks

# Load data
data_file = Path(__file__).parent.parent / "data" / "manuscript" / "simulation_data_oscillation.csv"
df = pd.read_csv(data_file)

time = df['Time (s)'].values
erk_pp = df['ERK_PP (mM)'].values * 1000  # Convert mM to nM
mkp = df['MKP (mM)'].values * 1000  # Convert mM to nM

# Create figure with single panel
fig, ax = plt.subplots(1, 1, figsize=(10, 6))

# Plot ERK-PP oscillations
ax.plot(time, erk_pp, 'r-', linewidth=2.5, label='ERK-PP', color='#D32F2F')

# Add MKP for context (optional, lighter line)
ax2 = ax.twinx()
ax2.plot(time, mkp, 'b--', linewidth=2.0, alpha=0.6, label='MKP', color='#1976D2')

# Labels and title
ax.set_xlabel('Time (s)', fontsize=13, fontweight='bold')
ax.set_ylabel('ERK-PP (nM)', fontsize=13, fontweight='bold', color='#D32F2F')
ax2.set_ylabel('MKP (nM)', fontsize=13, fontweight='bold', color='#1976D2')
ax.set_title('Oscillatory MAPK Cascade Dynamics', fontsize=14, fontweight='bold', pad=10)

# Color the y-axis ticks to match the lines
ax.tick_params(axis='y', labelcolor='#D32F2F', labelsize=11)
ax2.tick_params(axis='y', labelcolor='#1976D2', labelsize=11)
ax.tick_params(axis='x', labelsize=11)

# Grid
ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)

# Legends
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=11, frameon=True)

plt.tight_layout()

# Save figure
output_dir = Path(__file__).parent.parent / "figures"
output_dir.mkdir(parents=True, exist_ok=True)
output_pdf = output_dir / "mapk_oscillations_timed.pdf"
output_png = output_dir / "mapk_oscillations_timed.png"

plt.savefig(output_pdf, format='pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_png, format='png', dpi=150, bbox_inches='tight')

print(f"Figure saved to: {output_pdf}")
print(f"PNG preview saved to: {output_png}")

# Calculate statistics matching caption
erk_peaks, properties = find_peaks(erk_pp, height=100, distance=50)
if len(erk_peaks) > 1:
    periods = np.diff(time[erk_peaks])
    mean_period = np.mean(periods)
    std_period = np.std(periods)
    frequency = 1/mean_period * 60  # oscillations per minute
    
    print(f"\n=== Oscillation Statistics ===")
    print(f"Number of peaks: {len(erk_peaks)}")
    print(f"Period: {mean_period:.2f} ± {std_period:.2f} s")
    print(f"Frequency: {frequency:.1f} oscillations/min")
    print(f"ERK-PP amplitude: {erk_pp.min():.0f} - {erk_pp.max():.0f} nM")
    print(f"Simulation time: {time[-1]:.0f} s")

plt.close()
