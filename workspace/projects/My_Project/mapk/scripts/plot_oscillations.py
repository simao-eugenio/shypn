#!/usr/bin/env python3
"""
Visualize MAPK Cascade Oscillations with Timed MKP Synthesis
Created: January 10, 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load data
data_file = Path(__file__).parent.parent / "data" / "manuscript" / "simulation_data_oscillation.csv"
df = pd.read_csv(data_file)

time = df['Time (s)'].values
erk_pp = df['ERK_PP (mM)'].values
mkp = df['MKP (mM)'].values
erk_nuclear = df['ERK_Nuclear (mM)'].values

# Create figure with 2 subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Top panel: ERK dynamics
ax1.plot(time, erk_pp, 'r-', linewidth=2.0, label='ERK-PP (cytoplasm)')
ax1.plot(time, erk_nuclear, 'darkred', linewidth=2.0, linestyle='--', label='ERK (nuclear)')
ax1.axvline(x=120, color='purple', linestyle=':', linewidth=2.5, alpha=0.6, 
            label='MKP delay threshold (120s)')
ax1.set_ylabel('Concentration [nM]', fontsize=12, fontweight='bold')
ax1.set_title('MAPK Cascade Oscillations with Timed Delay (120s)', 
              fontsize=14, fontweight='bold', pad=15)
ax1.legend(loc='upper right', fontsize=10, framealpha=0.9)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_ylim(bottom=0)

# Bottom panel: MKP dynamics
ax2.plot(time, mkp, 'b-', linewidth=2.0, label='MKP')
ax2.axvline(x=120, color='purple', linestyle=':', linewidth=2.5, alpha=0.6, 
            label='MKP delay threshold (120s)')
ax2.fill_between([0, 120], 0, ax2.get_ylim()[1], alpha=0.1, color='gray', 
                  label='Pre-delay phase')
ax2.set_xlabel('Time [s]', fontsize=12, fontweight='bold')
ax2.set_ylabel('MKP Concentration [nM]', fontsize=12, fontweight='bold')
ax2.legend(loc='upper right', fontsize=10, framealpha=0.9)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_ylim(bottom=0)

# Add annotations
ax1.text(60, ax1.get_ylim()[1]*0.9, 'Fast ERK oscillations\n(~3.2s period)', 
         ha='center', va='top', fontsize=10, 
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
ax2.text(150, ax2.get_ylim()[1]*0.9, 'MKP synthesis activated\nOscillations coupled', 
         ha='center', va='top', fontsize=10,
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))

plt.tight_layout()

# Save figure
output_dir = Path(__file__).parent.parent / "figures"
output_dir.mkdir(parents=True, exist_ok=True)
output_pdf = output_dir / "mapk_oscillations_timed.pdf"
output_png = output_dir / "mapk_oscillations_timed.png"

plt.savefig(output_pdf, format='pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_png, format='png', dpi=300, bbox_inches='tight')

print(f"✓ Oscillation plots saved:")
print(f"  PDF: {output_pdf}")
print(f"  PNG: {output_png}")

# Calculate statistics
from scipy.signal import find_peaks

# ERK peaks
erk_peaks, _ = find_peaks(erk_pp, height=20, distance=50)
if len(erk_peaks) > 1:
    periods = np.diff(time[erk_peaks])
    print(f"\n✓ Oscillation Analysis:")
    print(f"  ERK-PP peaks: {len(erk_peaks)}")
    print(f"  Mean period: {np.mean(periods):.2f}s ± {np.std(periods):.2f}s")
    print(f"  Frequency: {1/np.mean(periods)*60:.1f} oscillations/min")
    print(f"  ERK-PP amplitude: {erk_pp.min():.1f} - {erk_pp.max():.1f} nM")
    print(f"  MKP amplitude: {mkp.min():.1f} - {mkp.max():.1f} nM")

plt.show()
