#!/usr/bin/env python3
"""
Comprehensive Analysis of N-Methylation = 0 Simulation Results
==============================================================

Analyzes the baseline drug transport simulation without N-methylation.
Provides detailed metrics, dynamics, and visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Load data
csv_path = 'workspace/projects/My_Project/drug_discovery/data/n_methylation/sim_nme_normal_0_enhanced.csv'
df = pd.read_csv(csv_path)

print("=" * 80)
print("N-METHYLATION = 0 SIMULATION ANALYSIS")
print("=" * 80)

# Basic info
print(f"\n📊 DATASET OVERVIEW:")
print(f"   • Total time points: {len(df)}")
print(f"   • Simulation duration: {df['Time (s)'].max():.2f} seconds")
print(f"   • Sampling rate: ~{len(df)/df['Time (s)'].max():.1f} samples/second")
print(f"   • Total columns: {len(df.columns)}")

# Rename columns for easier access
df_renamed = df.rename(columns=lambda x: x.replace(' (s)', '').replace(' (mM)', '').replace(' (firings)', ''))

# ============================================================================
# DRUG TRANSPORT ANALYSIS
# ============================================================================
print(f"\n{'='*80}")
print("💊 DRUG TRANSPORT DYNAMICS")
print("=" * 80)

initial = df_renamed.iloc[0]
final = df_renamed.iloc[-1]

print(f"\n📈 Drug Distribution (Initial → Final):")
print(f"   • Extracellular:    {initial['Drug_ext']:>8.4f} → {final['Drug_ext']:>8.4f} mM (Δ = {final['Drug_ext'] - initial['Drug_ext']:+.4f})")
print(f"   • Intracellular:    {initial['Drug_intracellular']:>8.4f} → {final['Drug_intracellular']:>8.4f} mM (Δ = {final['Drug_intracellular'] - initial['Drug_intracellular']:+.4f})")
print(f"   • Extended form:    {initial['Drug_extended']:>8.4f} → {final['Drug_extended']:>8.4f} mM (Δ = {final['Drug_extended'] - initial['Drug_extended']:+.4f})")
print(f"   • Compact form:     {initial['Drug_compact']:>8.4f} → {final['Drug_compact']:>8.4f} mM (Δ = {final['Drug_compact'] - initial['Drug_compact']:+.4f})")
print(f"   • Degraded:         {initial['Drug_degraded']:>8.4f} → {final['Drug_degraded']:>8.4f} mM (Δ = {final['Drug_degraded'] - initial['Drug_degraded']:+.4f})")

# Calculate total drug accounting
initial_total = initial['Drug_ext'] + initial['Drug_intracellular'] + initial['Drug_degraded']
final_total = final['Drug_ext'] + final['Drug_intracellular'] + final['Drug_degraded']

print(f"\n🧮 Mass Balance (with degradation):")
print(f"   • Initial total: {initial_total:.4f} mM")
print(f"   • Final total:   {final_total:.4f} mM")
print(f"   • Conservation:  {(final_total/initial_total)*100:.3f}%")

# Transport metrics
accumulation = final['Drug_intracellular'] - initial['Drug_intracellular']
accumulation_rate = accumulation / final['Time']
print(f"\n📊 Transport Performance:")
print(f"   • Net accumulation: {accumulation:.4f} mM ({(accumulation/initial['Drug_ext'])*100:.2f}% of initial external drug)")
print(f"   • Accumulation rate: {accumulation_rate:.6f} mM/s")
print(f"   • Degradation: {final['Drug_degraded']:.4f} mM ({(final['Drug_degraded']/initial_total)*100:.2f}% of total)")

# ============================================================================
# ENERGY METABOLISM ANALYSIS
# ============================================================================
print(f"\n{'='*80}")
print("⚡ ENERGY METABOLISM")
print("=" * 80)

print(f"\n🔋 ATP/ADP/Pi Pools (Initial → Final):")
print(f"   • ATP:  {initial['ATP_pool']:>8.2f} → {final['ATP_pool']:>8.2f} mM (Δ = {final['ATP_pool'] - initial['ATP_pool']:+.2f})")
print(f"   • ADP:  {initial['ADP_pool']:>8.2f} → {final['ADP_pool']:>8.2f} mM (Δ = {final['ADP_pool'] - initial['ADP_pool']:+.2f})")
print(f"   • Pi:   {initial['Pi_pool']:>8.2f} → {final['Pi_pool']:>8.2f} mM (Δ = {final['Pi_pool'] - initial['Pi_pool']:+.2f})")

# Energy charge
initial_ec = initial['ATP_pool'] / (initial['ATP_pool'] + initial['ADP_pool'])
final_ec = final['ATP_pool'] / (final['ATP_pool'] + final['ADP_pool'])

print(f"\n⚡ Energy Charge (ATP / (ATP + ADP)):")
print(f"   • Initial: {initial_ec:.4f}")
print(f"   • Final:   {final_ec:.4f}")
print(f"   • Change:  {final_ec - initial_ec:+.4f}")

# ATP consumption
atp_consumed = initial['ATP_pool'] - final['ATP_pool']
atp_consumption_rate = atp_consumed / final['Time']

print(f"\n📉 ATP Consumption:")
print(f"   • Total consumed: {atp_consumed:.2f} mM")
print(f"   • Consumption rate: {atp_consumption_rate:.4f} mM/s")
print(f"   • ATP/Drug ratio: {atp_consumed/accumulation:.2f} ATP per mM drug accumulated")

# Transport efficiency
transport_efficiency = accumulation / atp_consumed if atp_consumed > 0 else 0
print(f"   • Transport efficiency: {transport_efficiency:.6f} mM drug / mM ATP")

# ============================================================================
# TRANSITION FIRING ANALYSIS
# ============================================================================
print(f"\n{'='*80}")
print("🔥 TRANSITION FIRING STATISTICS")
print("=" * 80)

transitions = [
    'active_transport', 'ATP_synthesis', 'basal_ATPase', 'ABC_efflux',
    'facilitated_diffusion', 'passive_diffusion', 'chameleon_fold', 
    'chameleon_unfold', 'proteasomal', 'lysosomal', 'chemical_hydrolysis'
]

print(f"\n🎯 Final Firing Counts:")
for trans in transitions:
    if trans in df_renamed.columns:
        count = final[trans]
        rate = count / final['Time'] if final['Time'] > 0 else 0
        print(f"   • {trans:25s}: {count:>6.1f} firings ({rate:>7.3f} Hz)")

# Key process analysis
print(f"\n🔑 Key Transport Processes:")
total_import = final['active_transport'] + final['facilitated_diffusion'] + final['passive_diffusion']
total_export = final['ABC_efflux']
total_degradation = final['proteasomal'] + final['lysosomal'] + final['chemical_hydrolysis']

print(f"   • Total import events: {total_import:.1f}")
print(f"   • Total export events: {total_export:.1f}")
print(f"   • Total degradation events: {total_degradation:.1f}")
print(f"   • Net transport (import - export): {total_import - total_export:.1f}")

# Conformational changes
print(f"\n🔄 Conformational Dynamics:")
print(f"   • Folding (extended→compact): {final['chameleon_fold']:.1f}")
print(f"   • Unfolding (compact→extended): {final['chameleon_unfold']:.1f}")
print(f"   • Net folding: {final['chameleon_fold'] - final['chameleon_unfold']:.1f}")

# ============================================================================
# TIME SERIES ANALYSIS - KEY MILESTONES
# ============================================================================
print(f"\n{'='*80}")
print("⏱️  TEMPORAL DYNAMICS")
print("=" * 80)

# Find key milestones
t_50_accumulation = df_renamed[df_renamed['Drug_intracellular'] >= accumulation * 0.5 + initial['Drug_intracellular']].iloc[0]['Time'] if accumulation > 0 else None
t_90_accumulation = df_renamed[df_renamed['Drug_intracellular'] >= accumulation * 0.9 + initial['Drug_intracellular']].iloc[0]['Time'] if accumulation > 0 else None

print(f"\n📍 Accumulation Milestones:")
if t_50_accumulation:
    print(f"   • 50% accumulation reached at: {t_50_accumulation:.2f} s")
if t_90_accumulation:
    print(f"   • 90% accumulation reached at: {t_90_accumulation:.2f} s")

# Pi depletion check
pi_depleted_idx = df_renamed[df_renamed['Pi_pool'] == 0].index
if len(pi_depleted_idx) > 0:
    t_pi_depletion = df_renamed.loc[pi_depleted_idx[0], 'Time']
    print(f"   • Pi pool depleted at: {t_pi_depletion:.2f} s ⚠️")

# Calculate rates at different phases
early_phase = df_renamed[df_renamed['Time'] <= 10]
late_phase = df_renamed[df_renamed['Time'] >= 50]

if len(early_phase) > 1:
    early_rate = (early_phase.iloc[-1]['Drug_intracellular'] - early_phase.iloc[0]['Drug_intracellular']) / (early_phase.iloc[-1]['Time'] - early_phase.iloc[0]['Time'])
    print(f"\n📈 Phase-Specific Rates:")
    print(f"   • Early phase (0-10s) accumulation: {early_rate:.6f} mM/s")

if len(late_phase) > 1:
    late_rate = (late_phase.iloc[-1]['Drug_intracellular'] - late_phase.iloc[0]['Drug_intracellular']) / (late_phase.iloc[-1]['Time'] - late_phase.iloc[0]['Time'])
    print(f"   • Late phase (50-60s) accumulation: {late_rate:.6f} mM/s")
    if early_phase is not None and len(early_phase) > 1:
        print(f"   • Rate change: {((late_rate/early_rate - 1) * 100):+.1f}%")

# ============================================================================
# VISUALIZATION
# ============================================================================
print(f"\n{'='*80}")
print("📊 GENERATING VISUALIZATIONS")
print("=" * 80)

fig, axes = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle('N-Methylation = 0: Comprehensive Simulation Analysis', fontsize=16, fontweight='bold')

# 1. Drug concentrations over time
ax1 = axes[0, 0]
ax1.plot(df_renamed['Time'], df_renamed['Drug_ext'], label='Extracellular', linewidth=2)
ax1.plot(df_renamed['Time'], df_renamed['Drug_intracellular'], label='Intracellular', linewidth=2)
ax1.plot(df_renamed['Time'], df_renamed['Drug_degraded'], label='Degraded', linewidth=2, linestyle='--')
ax1.set_xlabel('Time (s)', fontsize=11)
ax1.set_ylabel('Concentration (mM)', fontsize=11)
ax1.set_title('Drug Distribution Over Time', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# 2. ATP/ADP/Pi pools
ax2 = axes[0, 1]
ax2.plot(df_renamed['Time'], df_renamed['ATP_pool'], label='ATP', linewidth=2)
ax2.plot(df_renamed['Time'], df_renamed['ADP_pool'], label='ADP', linewidth=2)
ax2.plot(df_renamed['Time'], df_renamed['Pi_pool'], label='Pi', linewidth=2)
ax2.set_xlabel('Time (s)', fontsize=11)
ax2.set_ylabel('Concentration (mM)', fontsize=11)
ax2.set_title('Energy Metabolite Pools', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# 3. Energy charge
ax3 = axes[1, 0]
energy_charge = df_renamed['ATP_pool'] / (df_renamed['ATP_pool'] + df_renamed['ADP_pool'])
ax3.plot(df_renamed['Time'], energy_charge, linewidth=2, color='purple')
ax3.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='Optimal threshold (0.8)')
ax3.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Critical threshold (0.5)')
ax3.set_xlabel('Time (s)', fontsize=11)
ax3.set_ylabel('Energy Charge', fontsize=11)
ax3.set_title('Energy Charge: ATP / (ATP + ADP)', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# 4. Drug conformations
ax4 = axes[1, 1]
ax4.plot(df_renamed['Time'], df_renamed['Drug_extended'], label='Extended', linewidth=2)
ax4.plot(df_renamed['Time'], df_renamed['Drug_compact'], label='Compact', linewidth=2)
ax4.set_xlabel('Time (s)', fontsize=11)
ax4.set_ylabel('Concentration (mM)', fontsize=11)
ax4.set_title('Drug Conformational States', fontsize=12, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)

# 5. Cumulative firing counts for transport
ax5 = axes[2, 0]
ax5.plot(df_renamed['Time'], df_renamed['active_transport'], label='Active transport', linewidth=2)
ax5.plot(df_renamed['Time'], df_renamed['facilitated_diffusion'], label='Facilitated diffusion', linewidth=2)
ax5.plot(df_renamed['Time'], df_renamed['ABC_efflux'], label='ABC efflux', linewidth=2, linestyle='--')
ax5.set_xlabel('Time (s)', fontsize=11)
ax5.set_ylabel('Cumulative Firings', fontsize=11)
ax5.set_title('Transport Mechanism Activity', fontsize=12, fontweight='bold')
ax5.legend(fontsize=9)
ax5.grid(True, alpha=0.3)

# 6. Degradation pathways
ax6 = axes[2, 1]
ax6.plot(df_renamed['Time'], df_renamed['proteasomal'], label='Proteasomal', linewidth=2)
ax6.plot(df_renamed['Time'], df_renamed['lysosomal'], label='Lysosomal', linewidth=2)
ax6.plot(df_renamed['Time'], df_renamed['chemical_hydrolysis'], label='Chemical hydrolysis', linewidth=2)
ax6.set_xlabel('Time (s)', fontsize=11)
ax6.set_ylabel('Cumulative Firings', fontsize=11)
ax6.set_title('Degradation Pathway Activity', fontsize=12, fontweight='bold')
ax6.legend(fontsize=9)
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('nme_0_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: nme_0_comprehensive_analysis.png")

# ============================================================================
# SUMMARY STATISTICS TABLE
# ============================================================================
print(f"\n{'='*80}")
print("📋 SUMMARY STATISTICS")
print("=" * 80)

summary_stats = {
    'Metric': [
        'Simulation Duration (s)',
        'Final Drug Accumulation (mM)',
        'Accumulation Rate (mM/s)',
        'Total Degraded (mM)',
        'ATP Consumed (mM)',
        'ATP Consumption Rate (mM/s)',
        'Transport Efficiency (drug/ATP)',
        'Energy Charge (final)',
        'Active Transport Events',
        'ABC Efflux Events',
        'Total Degradation Events',
        'Net Conformational Change'
    ],
    'Value': [
        f"{final['Time']:.2f}",
        f"{accumulation:.4f}",
        f"{accumulation_rate:.6f}",
        f"{final['Drug_degraded']:.4f}",
        f"{atp_consumed:.2f}",
        f"{atp_consumption_rate:.4f}",
        f"{transport_efficiency:.6f}",
        f"{final_ec:.4f}",
        f"{final['active_transport']:.1f}",
        f"{final['ABC_efflux']:.1f}",
        f"{total_degradation:.1f}",
        f"{final['chameleon_fold'] - final['chameleon_unfold']:.1f}"
    ]
}

summary_df = pd.DataFrame(summary_stats)
print(summary_df.to_string(index=False))

# Save summary to CSV
summary_df.to_csv('nme_0_summary_statistics.csv', index=False)
print(f"\n✅ Saved: nme_0_summary_statistics.csv")

print(f"\n{'='*80}")
print("✨ ANALYSIS COMPLETE")
print("=" * 80)
print(f"\nGenerated files:")
print(f"   • nme_0_comprehensive_analysis.png - 6-panel visualization")
print(f"   • nme_0_summary_statistics.csv - Summary metrics table")
