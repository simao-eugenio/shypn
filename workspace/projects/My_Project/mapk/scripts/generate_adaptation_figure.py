#!/usr/bin/env python3
"""
Generate clean adaptation figure for manuscript Figure 4.
Shows near-perfect adaptation to sustained growth factor pulse.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load data
data_file = Path(__file__).parent.parent / "data" / "manuscript" / "simulation_data_adaptation_new.csv"
df = pd.read_csv(data_file)

time = df['Time (s)'].values
erk_pp = df['ERK_PP (mM)'].values * 1000  # Convert mM to nM
gf = df['Growth_Factor (mM)'].values * 1000  # Convert mM to nM
mkp = df['MKP (mM)'].values * 1000  # Convert mM to nM

# Create figure
fig, ax1 = plt.subplots(1, 1, figsize=(10, 6))

# Plot ERK-PP (main y-axis)
ax1.plot(time, erk_pp, 'r-', linewidth=2.5, label='ERK-PP', color='#D32F2F')

# Create second y-axis for GF and MKP
ax2 = ax1.twinx()
ax2.plot(time, gf, 'g--', linewidth=2.0, alpha=0.7, label='Growth Factor', color='#388E3C')
ax2.plot(time, mkp, 'b:', linewidth=2.0, alpha=0.7, label='MKP', color='#1976D2')

# Labels and title
ax1.set_xlabel('Time (s)', fontsize=13, fontweight='bold')
ax1.set_ylabel('ERK-PP (nM)', fontsize=13, fontweight='bold', color='#D32F2F')
ax2.set_ylabel('GF / MKP (nM)', fontsize=13, fontweight='bold', color='#424242')
ax1.set_title('Adaptive MAPK Cascade Dynamics', fontsize=14, fontweight='bold', pad=10)

# Color the y-axis ticks
ax1.tick_params(axis='y', labelcolor='#D32F2F', labelsize=11)
ax2.tick_params(axis='y', labelcolor='#424242', labelsize=11)
ax1.tick_params(axis='x', labelsize=11)

# Grid
ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=11, frameon=True)

plt.tight_layout()

# Save figure
output_dir = Path(__file__).parent.parent / "figures"
output_dir.mkdir(parents=True, exist_ok=True)
output_pdf = output_dir / "adaptation_spike_timecourse.pdf"
output_png = output_dir / "adaptation_spike_timecourse.png"

plt.savefig(output_pdf, format='pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_png, format='png', dpi=150, bbox_inches='tight')

print(f"Figure saved to: {output_pdf}")
print(f"PNG preview saved to: {output_png}")

# Calculate statistics matching caption
baseline = erk_pp[time < 10].mean()
peak = erk_pp.max()
peak_time = time[erk_pp.argmax()]
adapted = erk_pp[time > 150].mean()
fold_change = peak / baseline

# Adaptation percentage
adaptation_pct = ((peak - adapted) / (peak - baseline)) * 100

print(f"\n=== Adaptation Statistics ===")
print(f"Baseline ERK-PP: {baseline:.1f} nM")
print(f"Peak ERK-PP: {peak:.1f} nM at t={peak_time:.1f}s")
print(f"Adapted ERK-PP (t>150s): {adapted:.1f} nM")
print(f"Fold-change: {fold_change:.0f}×")
print(f"Adaptation: {adaptation_pct:.1f}%")
print(f"Steady-state response ratio: {adapted/baseline:.0f}×")

plt.close()
