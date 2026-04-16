#!/usr/bin/env python3
"""
Analyze N-Methylation 2 Enhanced Simulation Results
===================================================
Two N-methyl groups macrocycle transport simulation analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)

# Load simulation data
data_path = Path('workspace/projects/My_Project/drug_discovery/data/n_methylation/sim_nme_normal_2_enhanced.csv')
df = pd.read_csv(data_path)

print("="*80)
print("N-METHYLATION 2 ENHANCED SIMULATION ANALYSIS")
print("="*80)
print(f"\nData file: {data_path}")
print(f"Total timepoints: {len(df)}")
print(f"Time range: {df['Time (s)'].min():.2f}s - {df['Time (s)'].max():.2f}s")
print(f"\nColumns ({len(df.columns)}): {', '.join(df.columns[:10])}...")

# ============================================================================
# KEY METRICS ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("KEY PERFORMANCE METRICS")
print("="*80)

# Initial and final states
initial = df.iloc[0]
final = df.iloc[-1]

# Drug accumulation (Drug_intracellular = Drug_in, Drug_ext = Drug_out)
drug_in_initial = initial['Drug_intracellular (mM)']
drug_in_final = final['Drug_intracellular (mM)']
drug_out_initial = initial['Drug_ext (mM)']
drug_out_final = final['Drug_ext (mM)']
total_drug = initial['Drug_intracellular (mM)'] + initial['Drug_ext (mM)']

accumulation_pct = (drug_in_final / total_drug) * 100

print(f"\n🎯 DRUG ACCUMULATION:")
print(f"   Initial Drug_in:  {drug_in_initial:>8.2f} molecules")
print(f"   Final Drug_in:    {drug_in_final:>8.2f} molecules ({accumulation_pct:.1f}%)")
print(f"   Δ Drug_in:        {drug_in_final - drug_in_initial:>+8.2f} molecules")
print(f"   Total drug:       {total_drug:>8.2f} molecules")

# Pi depletion analysis
print(f"\n⚡ ENERGETICS (Pi Consumption):")
pi_initial = initial['Pi_pool (mM)']
pi_final = final['Pi_pool (mM)']
pi_consumed = pi_initial - pi_final
pi_consumed_pct = (pi_consumed / pi_initial) * 100

# Find Pi depletion time
pi_threshold = pi_initial * 0.01  # 1% remaining
depletion_mask = df['Pi_pool (mM)'] <= pi_threshold
if depletion_mask.any():
    depletion_time = df[depletion_mask].iloc[0]['Time (s)']
    print(f"   Initial Pi:       {pi_initial:>8.2f} molecules")
    print(f"   Pi depleted at:   {depletion_time:>8.2f}s")
    print(f"   Pi consumed:      {pi_consumed:>8.2f} molecules ({pi_consumed_pct:.1f}%)")
else:
    print(f"   Initial Pi:       {pi_initial:>8.2f} molecules")
    print(f"   Final Pi:         {pi_final:>8.2f} molecules")
    print(f"   Pi consumed:      {pi_consumed:>8.2f} molecules ({pi_consumed_pct:.1f}%)")
    print(f"   Status:           Not fully depleted")

# Conformational dynamics
print(f"\n🔄 CONFORMATIONAL EQUILIBRIUM:")
drug_ext_final = final['Drug_extended (mM)']
drug_comp_final = final['Drug_compact (mM)']
total_internal = drug_ext_final + drug_comp_final
ext_pct = (drug_ext_final / total_internal) * 100 if total_internal > 0 else 0
comp_pct = (drug_comp_final / total_internal) * 100 if total_internal > 0 else 0

print(f"   Drug_extended:    {drug_ext_final:>8.2f} molecules ({ext_pct:.1f}%)")
print(f"   Drug_compact:     {drug_comp_final:>8.2f} molecules ({comp_pct:.1f}%)")
print(f"   Ratio (E:C):      {ext_pct/comp_pct if comp_pct > 0 else 0:.2f}:1")

# Count folding events (transitions)
if len(df) > 1:
    ext_changes = np.abs(np.diff(df['Drug_extended (mM)']))
    comp_changes = np.abs(np.diff(df['Drug_compact (mM)']))
    # Significant changes (> 0.5 molecules)
    significant_ext = np.sum(ext_changes > 0.5)
    significant_comp = np.sum(comp_changes > 0.5)
    total_transitions = significant_ext + significant_comp
    print(f"   Folding events:   ~{total_transitions:,} transitions")

# Mass conservation check
print(f"\n⚖️  MASS CONSERVATION:")
initial_total = (initial['Drug_intracellular (mM)'] + initial['Drug_ext (mM)'] + 
                 initial['Drug_extended (mM)'] + initial['Drug_compact (mM)'])
final_total = (final['Drug_intracellular (mM)'] + final['Drug_ext (mM)'] + 
               final['Drug_extended (mM)'] + final['Drug_compact (mM)'])
conservation_pct = (final_total / initial_total) * 100

print(f"   Initial total:    {initial_total:>8.2f} molecules")
print(f"   Final total:      {final_total:>8.2f} molecules")
print(f"   Conservation:     {conservation_pct:.3f}%")
if abs(conservation_pct - 100.0) < 0.01:
    print(f"   Status:           ✅ Perfect conservation")
elif abs(conservation_pct - 100.0) < 0.1:
    print(f"   Status:           ✅ Excellent conservation")
else:
    print(f"   Status:           ⚠️  Check boundary conditions")

# ATP/ADP cycle
print(f"\n🔋 ATP/ADP CYCLE:")
atp_ratio = final['ATP_pool (mM)'] / initial['ATP_pool (mM)'] if initial['ATP_pool (mM)'] > 0 else 0
adp_ratio = final['ADP_pool (mM)'] / initial['ADP_pool (mM)'] if initial['ADP_pool (mM)'] > 0 else 0
print(f"   ATP final/initial: {atp_ratio:.3f}x")
print(f"   ADP final/initial: {adp_ratio:.3f}x")

# ============================================================================
# VISUALIZATION
# ============================================================================
print("\n" + "="*80)
print("GENERATING COMPREHENSIVE VISUALIZATION")
print("="*80)

fig, axes = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle('N-Methylation 2 Enhanced - Comprehensive Analysis', fontsize=16, fontweight='bold')

# 1. Drug Accumulation Over Time
ax1 = axes[0, 0]
ax1.plot(df['Time (s)'], df['Drug_intracellular (mM)'], linewidth=2, label='Drug_intracellular', color='darkgreen')
ax1.plot(df['Time (s)'], df['Drug_ext (mM)'], linewidth=2, label='Drug_ext', color='orange', alpha=0.7)
ax1.set_xlabel('Time (s)', fontsize=11)
ax1.set_ylabel('Drug Molecules', fontsize=11)
ax1.set_title('Drug Compartmentalization', fontsize=12, fontweight='bold')
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)

# 2. Conformational States
ax2 = axes[0, 1]
ax2.plot(df['Time (s)'], df['Drug_extended (mM)'], linewidth=2, label='Extended', color='blue')
ax2.plot(df['Time (s)'], df['Drug_compact (mM)'], linewidth=2, label='Compact', color='red')
ax2.set_xlabel('Time (s)', fontsize=11)
ax2.set_ylabel('Molecules', fontsize=11)
ax2.set_title('Drug Conformational Dynamics', fontsize=12, fontweight='bold')
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3)

# 3. ATP/ADP/Pi Energy Pools
ax3 = axes[1, 0]
ax3.plot(df['Time (s)'], df['ATP_pool (mM)'], linewidth=2, label='ATP', color='green')
ax3.plot(df['Time (s)'], df['ADP_pool (mM)'], linewidth=2, label='ADP', color='blue')
ax3.plot(df['Time (s)'], df['Pi_pool (mM)'], linewidth=2, label='Pi', color='red')
ax3.set_xlabel('Time (s)', fontsize=11)
ax3.set_ylabel('Molecules', fontsize=11)
ax3.set_title('Energy Currency Pools', fontsize=12, fontweight='bold')
ax3.legend(loc='best')
ax3.grid(True, alpha=0.3)

# 4. Membrane Gradients
ax4 = axes[1, 1]
ax4.plot(df['Time (s)'], df['Membrane_potential (mM)'], linewidth=2, label='Membrane Potential', color='purple')
ax4_twin = ax4.twinx()
ax4_twin.plot(df['Time (s)'], df['pH_gradient (mM)'], linewidth=2, label='pH Gradient', color='teal', alpha=0.7)
ax4.set_xlabel('Time (s)', fontsize=11)
ax4.set_ylabel('Membrane Potential', fontsize=11, color='purple')
ax4_twin.set_ylabel('pH Gradient', fontsize=11, color='teal')
ax4.set_title('Electrochemical Gradients', fontsize=12, fontweight='bold')
ax4.tick_params(axis='y', labelcolor='purple')
ax4_twin.tick_params(axis='y', labelcolor='teal')
ax4.grid(True, alpha=0.3)

# 5. Mass Conservation Check
ax5 = axes[2, 0]
total_mass = (df['Drug_intracellular (mM)'] + df['Drug_ext (mM)'] + 
              df['Drug_extended (mM)'] + df['Drug_compact (mM)'])
conservation_error = ((total_mass - initial_total) / initial_total) * 100
ax5.plot(df['Time (s)'], conservation_error, linewidth=2, color='darkred')
ax5.axhline(y=0, color='green', linestyle='--', linewidth=1, alpha=0.5)
ax5.set_xlabel('Time (s)', fontsize=11)
ax5.set_ylabel('Conservation Error (%)', fontsize=11)
ax5.set_title('Mass Conservation Verification', fontsize=12, fontweight='bold')
ax5.grid(True, alpha=0.3)

# 6. Transport Rate (Drug_in derivative)
ax6 = axes[2, 1]
if len(df) > 1:
    transport_rate = np.gradient(df['Drug_intracellular (mM)'], df['Time (s)'])
    ax6.plot(df['Time (s)'], transport_rate, linewidth=2, color='darkgreen', alpha=0.7)
    ax6.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.3)
    ax6.set_xlabel('Time (s)', fontsize=11)
    ax6.set_ylabel('Transport Rate (molecules/s)', fontsize=11)
    ax6.set_title('Drug Influx Rate', fontsize=12, fontweight='bold')
    ax6.grid(True, alpha=0.3)

plt.tight_layout()

# Save figure
output_path = Path('nme_2_comprehensive_analysis.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n✅ Visualization saved: {output_path}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
summary_stats = {
    'Model': 'N-Me 2 Enhanced',
    'Total_Time_s': df['Time (s)'].max(),
    'Drug_Accumulation_pct': accumulation_pct,
    'Drug_In_Final': drug_in_final,
    'Pi_Consumed_pct': pi_consumed_pct,
    'Pi_Depletion_Time_s': depletion_time if depletion_mask.any() else None,
    'Drug_Extended_pct': ext_pct,
    'Drug_Compact_pct': comp_pct,
    'Conformational_Ratio_E_C': ext_pct/comp_pct if comp_pct > 0 else 0,
    'Folding_Events': total_transitions if len(df) > 1 else 0,
    'Mass_Conservation_pct': conservation_pct,
    'ATP_Ratio': atp_ratio,
    'ADP_Ratio': adp_ratio,
}

summary_df = pd.DataFrame([summary_stats])
summary_path = Path('nme_2_summary_statistics.csv')
summary_df.to_csv(summary_path, index=False)
print(f"✅ Summary statistics saved: {summary_path}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\n📊 Generated Files:")
print(f"   • {output_path}")
print(f"   • {summary_path}")
print()
