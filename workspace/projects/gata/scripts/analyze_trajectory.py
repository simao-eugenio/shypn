#!/usr/bin/env python3
"""
Analyze GATA1/PU.1 Phase 1 Simulation Data
==========================================

Analyzes single trajectory from Gillespie SSA simulation to determine:
1. Final fate (erythroid vs myeloid)
2. Commitment time
3. Trajectory dynamics
4. Validation against expected behavior

Author: Simão Eugénio
Date: February 14, 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

print("="*70)
print("GATA1/PU.1 Phase 1 Simulation Analysis")
print("="*70)

# Load data
data_path = Path("workspace/projects/gata/data/simulation_data.csv")
print(f"\n📂 Loading: {data_path}")
df = pd.read_csv(data_path)

print(f"✓ Loaded {len(df)} time points")
print(f"  Duration: {df['Time (s)'].min():.1f} - {df['Time (s)'].max():.1f} seconds")
print(f"  Time step: ~{df['Time (s)'].diff().mean():.3f} seconds (mean)")

# Extract key columns
time = df['Time (s)'].values
gata1_protein = df['GATA1_Protein (mM)'].values
pu1_protein = df['PU1_Protein (mM)'].values
gata1_mrna = df['GATA1_mRNA (mM)'].values
pu1_mrna = df['PU1_mRNA (mM)'].values

# ============================================================================
# FATE DETERMINATION
# ============================================================================
print("\n" + "="*70)
print("FATE DETERMINATION")
print("="*70)

# Final values
final_gata1 = gata1_protein[-1]
final_pu1 = pu1_protein[-1]
final_ratio = final_gata1 / final_pu1 if final_pu1 > 0 else np.inf

print(f"\nFinal State (t={time[-1]:.1f} s):")
print(f"  GATA1_Protein: {final_gata1:.2f} mM")
print(f"  PU1_Protein:   {final_pu1:.2f} mM")
print(f"  GATA1/PU1 ratio: {final_ratio:.2f}")

# Commitment classification
if final_ratio > 2.0:
    fate = "ERYTHROID"
    marker = "🔴"
elif final_ratio < 0.5:
    fate = "MYELOID"
    marker = "🔵"
else:
    fate = "UNCOMMITTED"
    marker = "⚪"

print(f"\n{marker} Committed Fate: {fate}")

# ============================================================================
# COMMITMENT TIME ANALYSIS
# ============================================================================
print("\n" + "="*70)
print("COMMITMENT TIME ANALYSIS")
print("="*70)

# Calculate GATA1/PU1 ratio over time
ratio_over_time = np.divide(gata1_protein, pu1_protein, 
                             out=np.ones_like(gata1_protein)*np.nan, 
                             where=pu1_protein>0.1)

# Find first time ratio crosses 2.0 (erythroid) or 0.5 (myeloid)
if fate == "ERYTHROID":
    commit_idx = np.where(ratio_over_time > 2.0)[0]
    if len(commit_idx) > 0:
        commitment_time = time[commit_idx[0]]
        print(f"✓ Commitment to ERYTHROID at t = {commitment_time:.1f} seconds")
        print(f"  GATA1 = {gata1_protein[commit_idx[0]]:.2f} mM")
        print(f"  PU1 = {pu1_protein[commit_idx[0]]:.2f} mM")
    else:
        commitment_time = None
        print("⚠ Ratio threshold never crossed (gradual commitment)")
elif fate == "MYELOID":
    commit_idx = np.where(ratio_over_time < 0.5)[0]
    if len(commit_idx) > 0:
        commitment_time = time[commit_idx[0]]
        print(f"✓ Commitment to MYELOID at t = {commitment_time:.1f} seconds")
        print(f"  GATA1 = {gata1_protein[commit_idx[0]]:.2f} mM")
        print(f"  PU1 = {pu1_protein[commit_idx[0]]:.2f} mM")
    else:
        commitment_time = None
        print("⚠ Ratio threshold never crossed (gradual commitment)")
else:
    commitment_time = None
    print("⚠ Cell remained uncommitted")

# ============================================================================
# TRAJECTORY STATISTICS
# ============================================================================
print("\n" + "="*70)
print("TRAJECTORY STATISTICS")
print("="*70)

print("\nGATA1 Protein:")
print(f"  Initial: {gata1_protein[0]:.2f} mM")
print(f"  Maximum: {gata1_protein.max():.2f} mM (at t={time[gata1_protein.argmax()]:.1f} s)")
print(f"  Final:   {gata1_protein[-1]:.2f} mM")
print(f"  Change:  {gata1_protein[-1] - gata1_protein[0]:+.2f} mM")

print("\nPU1 Protein:")
print(f"  Initial: {pu1_protein[0]:.2f} mM")
print(f"  Maximum: {pu1_protein.max():.2f} mM (at t={time[pu1_protein.argmax()]:.1f} s)")
print(f"  Final:   {pu1_protein[-1]:.2f} mM")
print(f"  Change:  {pu1_protein[-1] - pu1_protein[0]:+.2f} mM")

# mRNA statistics
print("\nGATA1 mRNA:")
print(f"  Mean: {gata1_mrna.mean():.2f} mM (±{gata1_mrna.std():.2f})")
print(f"  Range: {gata1_mrna.min():.2f} - {gata1_mrna.max():.2f} mM")

print("\nPU1 mRNA:")
print(f"  Mean: {pu1_mrna.mean():.2f} mM (±{pu1_mrna.std():.2f})")
print(f"  Range: {pu1_mrna.min():.2f} - {pu1_mrna.max():.2f} mM")

# ============================================================================
# TRANSITION FIRING ANALYSIS
# ============================================================================
print("\n" + "="*70)
print("TRANSITION FIRING RATES")
print("="*70)

gata1_txn_firings = df['GATA1_Transcription (firings)'].values[-1]
pu1_txn_firings = df['PU1_Transcription (firings)'].values[-1]
duration = time[-1]

print(f"\nTranscription Events:")
print(f"  GATA1: {gata1_txn_firings:.0f} firings ({gata1_txn_firings/duration:.3f} Hz)")
print(f"  PU1:   {pu1_txn_firings:.0f} firings ({pu1_txn_firings/duration:.3f} Hz)")
print(f"  Ratio: {gata1_txn_firings/pu1_txn_firings if pu1_txn_firings > 0 else np.inf:.2f}")

# ============================================================================
# VALIDATION CHECKS
# ============================================================================
print("\n" + "="*70)
print("VALIDATION CHECKS")
print("="*70)

checks_passed = 0
checks_total = 0

# Check 1: Commitment achieved
checks_total += 1
if fate != "UNCOMMITTED":
    print("✓ Cell committed to a fate (not stuck in intermediate)")
    checks_passed += 1
else:
    print("✗ Cell did not commit (remained in bistable region)")

# Check 2: Winner takes all
checks_total += 1
if final_ratio > 3.0 or final_ratio < 0.33:
    print(f"✓ Strong winner-take-all dynamics (ratio = {final_ratio:.2f})")
    checks_passed += 1
else:
    print(f"✗ Weak differentiation (ratio = {final_ratio:.2f}, expected >3 or <0.33)")

# Check 3: Proteins changed significantly
checks_total += 1
max_change = max(abs(gata1_protein[-1] - gata1_protein[0]), 
                 abs(pu1_protein[-1] - pu1_protein[0]))
if max_change > 50:
    print(f"✓ Significant protein change (Δmax = {max_change:.1f} mM)")
    checks_passed += 1
else:
    print(f"✗ Minimal protein change (Δmax = {max_change:.1f} mM)")

# Check 4: Commitment time reasonable
checks_total += 1
if commitment_time and 200 < commitment_time < 2000:
    print(f"✓ Commitment time reasonable ({commitment_time:.1f} s)")
    checks_passed += 1
elif commitment_time:
    print(f"⚠ Commitment time unusual ({commitment_time:.1f} s, expected 200-2000 s)")
else:
    print("⚠ Commitment time not determined")

print(f"\n{'='*70}")
print(f"Validation: {checks_passed}/{checks_total} checks passed")
print(f"{'='*70}")

# ============================================================================
# GENERATE PLOT
# ============================================================================
print("\n📊 Generating trajectory plot...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(f'GATA1/PU.1 Lineage Commitment - Single Trajectory\n'
             f'Final Fate: {fate} (GATA1/PU1 = {final_ratio:.2f})', 
             fontsize=14, fontweight='bold')

# Panel A: Protein dynamics
ax1 = axes[0, 0]
ax1.plot(time, gata1_protein, 'r-', linewidth=2, label='GATA1', alpha=0.8)
ax1.plot(time, pu1_protein, 'b-', linewidth=2, label='PU.1', alpha=0.8)
if commitment_time:
    ax1.axvline(commitment_time, color='gray', linestyle='--', alpha=0.5,
                label=f'Commitment ({commitment_time:.0f}s)')
ax1.set_xlabel('Time (s)', fontsize=11)
ax1.set_ylabel('Protein Level (mM)', fontsize=11)
ax1.set_title('A. Protein Dynamics', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Panel B: mRNA dynamics
ax2 = axes[0, 1]
ax2.plot(time, gata1_mrna, 'r-', linewidth=1.5, label='GATA1 mRNA', alpha=0.7)
ax2.plot(time, pu1_mrna, 'b-', linewidth=1.5, label='PU.1 mRNA', alpha=0.7)
ax2.set_xlabel('Time (s)', fontsize=11)
ax2.set_ylabel('mRNA Level (mM)', fontsize=11)
ax2.set_title('B. mRNA Dynamics', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# Panel C: GATA1/PU1 ratio
ax3 = axes[1, 0]
ax3.plot(time, ratio_over_time, 'g-', linewidth=2, alpha=0.8)
ax3.axhline(2.0, color='red', linestyle='--', alpha=0.5, label='Erythroid threshold (2.0)')
ax3.axhline(0.5, color='blue', linestyle='--', alpha=0.5, label='Myeloid threshold (0.5)')
ax3.axhline(1.0, color='gray', linestyle=':', alpha=0.3, label='Balanced (1.0)')
if commitment_time:
    ax3.axvline(commitment_time, color='gray', linestyle='--', alpha=0.5)
ax3.set_xlabel('Time (s)', fontsize=11)
ax3.set_ylabel('GATA1/PU1 Ratio', fontsize=11)
ax3.set_title('C. Commitment Trajectory', fontsize=12, fontweight='bold')
ax3.set_yscale('log')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# Panel D: Phase portrait
ax4 = axes[1, 1]
# Color by time
scatter = ax4.scatter(gata1_protein, pu1_protein, c=time, cmap='viridis', 
                      s=10, alpha=0.6)
ax4.plot(gata1_protein[0], pu1_protein[0], 'go', markersize=12, 
         label='Start', zorder=5)
ax4.plot(gata1_protein[-1], pu1_protein[-1], 'r*', markersize=15, 
         label='End', zorder=5)
# Diagonal lines for ratio thresholds
max_val = max(gata1_protein.max(), pu1_protein.max())
ax4.plot([0, max_val], [0, max_val/2], 'r--', alpha=0.3, label='GATA1/PU1=2')
ax4.plot([0, max_val/2], [0, max_val], 'b--', alpha=0.3, label='PU1/GATA1=2')
ax4.set_xlabel('GATA1 Protein (mM)', fontsize=11)
ax4.set_ylabel('PU1 Protein (mM)', fontsize=11)
ax4.set_title('D. Phase Portrait', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)
cbar = plt.colorbar(scatter, ax=ax4)
cbar.set_label('Time (s)', fontsize=10)

plt.tight_layout()

# Save figure
output_path = Path("workspace/projects/gata/data/trajectory_analysis.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ Figure saved: {output_path}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print(f"\nSummary:")
print(f"  Fate: {marker} {fate}")
print(f"  Final GATA1/PU1 ratio: {final_ratio:.2f}")
print(f"  Commitment time: {commitment_time:.1f} s" if commitment_time else "  Commitment time: Not determined")
print(f"  Validation: {checks_passed}/{checks_total} checks passed")
print(f"\nOutputs:")
print(f"  - Analysis: workspace/projects/gata/data/trajectory_analysis.png")
print(f"\nNext steps:")
if fate == "UNCOMMITTED":
    print("  ⚠ Cell did not commit - consider:")
    print("    1. Longer simulation time (try 5000-10000 sec)")
    print("    2. Stronger feedback (increase FEEDBACK_STRENGTH)")
    print("    3. Run 100 replicates to see distribution")
elif checks_passed == checks_total:
    print("  ✅ Excellent! Model working as expected")
    print("    1. Run 100 replicates for statistical validation")
    print("    2. Proceed to Phase 2: Threshold sweep")
else:
    print("  ⚠ Some validation checks failed - review parameters")
    print("    1. Check rate function symmetry")
    print("    2. Adjust INHIBITION_KI or FEEDBACK_STRENGTH")
    print("    3. Run longer simulation if needed")
