#!/usr/bin/env python3
"""
Generate Figure 5: Cascade activation dynamics during 10s growth factor pulse (0-40s window)
Shows coordinated temporal activation of Raf → MEK → ERK
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
data = pd.read_csv('../data/manuscript/simulation_data_adaptation_new.csv')

# Extract time and convert from seconds to seconds (already in seconds)
time = data['Time (s)'].values

# Extract cascade components and convert mM to nM
gf = data['Growth_Factor (mM)'].values * 1e6  # mM to nM
raf = data['Raf_active (mM)'].values * 1e6
mek = data['MEK_PP (mM)'].values * 1e6
erk = data['ERK_PP (mM)'].values * 1e6

# Focus on 0-40s window
mask = time <= 40
time_window = time[mask]
gf_window = gf[mask]
raf_window = raf[mask]
mek_window = mek[mask]
erk_window = erk[mask]

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Plot cascade components
ax.plot(time_window, raf_window, '-', linewidth=2.5, label='Raf-P', color='#1976D2')  # Blue
ax.plot(time_window, mek_window, '-', linewidth=2.5, label='MEK-PP', color='#388E3C')  # Green
ax.plot(time_window, erk_window, '-', linewidth=2.5, label='ERK-PP', color='#D32F2F')  # Red
ax.plot(time_window, gf_window, '--', linewidth=2.0, alpha=0.6, label='Growth Factor', color='#757575')  # Gray

# Formatting
ax.set_xlabel('Time (s)', fontsize=14, fontweight='bold')
ax.set_ylabel('Concentration (nM)', fontsize=14, fontweight='bold')
ax.set_title('Cascade Activation Dynamics During Growth Factor Pulse', 
             fontsize=16, fontweight='bold', pad=15)
ax.legend(loc='upper left', frameon=True, fontsize=11, edgecolor='black')
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_xlim(0, 40)
ax.tick_params(labelsize=11)

# Add shaded region for GF pulse (0-10s)
ax.axvspan(0, 10, alpha=0.1, color='gray', label='_nolegend_')

plt.tight_layout()

# Save
output_path = '../figures/cascade_activation_timecourse.pdf'
plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
print(f"Figure saved to: {output_path}")

# Also save PNG for preview
png_path = output_path.replace('.pdf', '.png')
plt.savefig(png_path, format='png', dpi=150, bbox_inches='tight')
print(f"PNG preview saved to: {png_path}")

plt.close()

# Calculate some statistics for validation
pulse_end_idx = np.argmin(np.abs(time - 10))
peak_raf_idx = np.argmax(raf[:pulse_end_idx+100])
peak_mek_idx = np.argmax(mek[:pulse_end_idx+100])
peak_erk_idx = np.argmax(erk[:pulse_end_idx+100])

print("\n=== Cascade Activation Statistics (0-40s window) ===")
print(f"GF pulse duration: 0-10s")
print(f"Raf peak: {raf[peak_raf_idx]:.1f} nM at t={time[peak_raf_idx]:.1f}s")
print(f"MEK peak: {mek[peak_mek_idx]:.1f} nM at t={time[peak_mek_idx]:.1f}s")
print(f"ERK peak: {erk[peak_erk_idx]:.1f} nM at t={time[peak_erk_idx]:.1f}s")
print(f"Temporal sequence: Raf → MEK → ERK")
print(f"Activation delays: MEK lags Raf by {time[peak_mek_idx] - time[peak_raf_idx]:.1f}s")
print(f"                   ERK lags MEK by {time[peak_erk_idx] - time[peak_mek_idx]:.1f}s")
