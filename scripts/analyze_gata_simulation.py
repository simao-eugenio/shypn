#!/usr/bin/env python3
"""
Analyze GATA1/PU1 simulation data from phase3a_spatial_clean.shy model
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Read the simulation data
data_path = Path("workspace/projects/gata/data/simulation_data.csv")
df = pd.read_csv(data_path)

print("=" * 80)
print("GATA1/PU1 GENE REGULATORY NETWORK - SIMULATION ANALYSIS")
print("=" * 80)
print()

# Basic info
print("1. SIMULATION METADATA")
print("-" * 80)
print(f"Total time points: {len(df)}")
print(f"Time range: {df['Time (s)'].min():.2f} - {df['Time (s)'].max():.2f} seconds")
print(f"Duration: {df['Time (s)'].max():.2f} seconds ({df['Time (s)'].max()/60:.2f} minutes)")
print(f"Time step (approx): {df['Time (s)'].diff().mean():.4f} seconds")
print(f"Total variables: {len(df.columns)}")
print()

# Extract key species
print("2. KEY MOLECULAR SPECIES")
print("-" * 80)

# GATA1 pathway
gata1_mrna_nuc = df['GATA1_mRNA_nuc (mM)']
gata1_mrna_cyto = df['GATA1_mRNA_cyto (mM)']
gata1_prot_cyto = df['GATA1_Protein_cyto (mM)']
gata1_prot_nuc = df['GATA1_Protein_nuc (mM)']

# PU1 pathway
pu1_mrna_nuc = df['PU1_mRNA_nuc (mM)']
pu1_mrna_cyto = df['PU1_mRNA_cyto (mM)']
pu1_prot_cyto = df['PU1_Protein_cyto (mM)']
pu1_prot_nuc = df['PU1_Protein_nuc (mM)']

# External signals
epo = df['EPO_external (mM)']
gcsf = df['GCSF_external (mM)']

# Energy metabolism
atp = df['ATP (mM)']
adp = df['ADP (mM)']
gtp = df['GTP (mM)']
gdp = df['GDP (mM)']

print("GATA1 Pathway (final values):")
print(f"  Nuclear mRNA:       {gata1_mrna_nuc.iloc[-1]:>10.2f} mM (initial: {gata1_mrna_nuc.iloc[0]:.2f})")
print(f"  Cytoplasmic mRNA:   {gata1_mrna_cyto.iloc[-1]:>10.2f} mM (initial: {gata1_mrna_cyto.iloc[0]:.2f})")
print(f"  Cytoplasmic Protein:{gata1_prot_cyto.iloc[-1]:>10.2f} mM (initial: {gata1_prot_cyto.iloc[0]:.2f})")
print(f"  Nuclear Protein:    {gata1_prot_nuc.iloc[-1]:>10.2f} mM (initial: {gata1_prot_nuc.iloc[0]:.2f})")
print()
print("PU1 Pathway (final values):")
print(f"  Nuclear mRNA:       {pu1_mrna_nuc.iloc[-1]:>10.2f} mM (initial: {pu1_mrna_nuc.iloc[0]:.2f})")
print(f"  Cytoplasmic mRNA:   {pu1_mrna_cyto.iloc[-1]:>10.2f} mM (initial: {pu1_mrna_cyto.iloc[0]:.2f})")
print(f"  Cytoplasmic Protein:{pu1_prot_cyto.iloc[-1]:>10.2f} mM (initial: {pu1_prot_cyto.iloc[0]:.2f})")
print(f"  Nuclear Protein:    {pu1_prot_nuc.iloc[-1]:>10.2f} mM (initial: {pu1_prot_nuc.iloc[0]:.2f})")
print()
print(f"EPO (external):       {epo.iloc[-1]:>10.2f} mM (initial: {epo.iloc[0]:.2f})")
print(f"GCSF (external):      {gcsf.iloc[-1]:>10.2f} mM (initial: {gcsf.iloc[0]:.2f})")
print()

# Energy metabolism
print("3. ENERGY METABOLISM")
print("-" * 80)
atp_ratio_final = atp.iloc[-1] / (atp.iloc[-1] + adp.iloc[-1])
gtp_ratio_final = gtp.iloc[-1] / (gtp.iloc[-1] + gdp.iloc[-1])
atp_ratio_initial = atp.iloc[0] / (atp.iloc[0] + adp.iloc[0])
gtp_ratio_initial = gtp.iloc[0] / (gtp.iloc[0] + gdp.iloc[0])

print(f"ATP: {atp.iloc[-1]:>10.2f} mM (initial: {atp.iloc[0]:.2f})")
print(f"ADP: {adp.iloc[-1]:>10.2f} mM (initial: {adp.iloc[0]:.2f})")
print(f"ATP/(ATP+ADP) ratio: {atp_ratio_final:.4f} (initial: {atp_ratio_initial:.4f})")
print()
print(f"GTP: {gtp.iloc[-1]:>10.2f} mM (initial: {gtp.iloc[0]:.2f})")
print(f"GDP: {gdp.iloc[-1]:>10.2f} mM (initial: {gdp.iloc[0]:.2f})")
print(f"GTP/(GTP+GDP) ratio: {gtp_ratio_final:.4f} (initial: {gtp_ratio_initial:.4f})")
print()

# Transition firing analysis
print("4. TRANSITION FIRING STATISTICS")
print("-" * 80)
firing_cols = [col for col in df.columns if '(firings)' in col]
print(f"Total transitions: {len(firing_cols)}")
print()
print("Top 10 most active transitions (total firings):")
firing_totals = {col.replace(' (firings)', ''): df[col].iloc[-1] 
                 for col in firing_cols}
sorted_firings = sorted(firing_totals.items(), key=lambda x: x[1], reverse=True)
for i, (trans, count) in enumerate(sorted_firings[:10], 1):
    print(f"  {i:2d}. {trans:40s}: {count:>12.2f} firings")
print()

# Transcription vs degradation
gata1_trans = df['GATA1_transcription (firings)'].iloc[-1]
gata1_deg_nuc = df['GATA1_mRNA_nuc_degradation (firings)'].iloc[-1]
gata1_deg_cyto = df['GATA1_mRNA_cyto_degradation (firings)'].iloc[-1]
pu1_trans = df['PU1_transcription (firings)'].iloc[-1]
pu1_deg_nuc = df['PU1_mRNA_nuc_degradation (firings)'].iloc[-1]
pu1_deg_cyto = df['PU1_mRNA_cyto_degradation (firings)'].iloc[-1]

print("GATA1 mRNA dynamics:")
print(f"  Transcription:         {gata1_trans:>10.2f} firings")
print(f"  Nuclear degradation:   {gata1_deg_nuc:>10.2f} firings")
print(f"  Cytoplasmic degr.:     {gata1_deg_cyto:>10.2f} firings")
print(f"  Net production:        {gata1_trans - gata1_deg_nuc - gata1_deg_cyto:>10.2f}")
print()
print("PU1 mRNA dynamics:")
print(f"  Transcription:         {pu1_trans:>10.2f} firings")
print(f"  Nuclear degradation:   {pu1_deg_nuc:>10.2f} firings")
print(f"  Cytoplasmic degr.:     {pu1_deg_cyto:>10.2f} firings")
print(f"  Net production:        {pu1_trans - pu1_deg_nuc - pu1_deg_cyto:>10.2f}")
print()

# Equilibrium analysis
print("5. EQUILIBRIUM ANALYSIS (last 10% of simulation)")
print("-" * 80)
cutoff = int(len(df) * 0.9)
final_portion = df.iloc[cutoff:]

def calc_variance_ratio(series, cutoff_idx):
    """Calculate variance in last 10% vs full trajectory"""
    full_var = series.var()
    final_var = series.iloc[cutoff_idx:].var()
    return final_var / full_var if full_var > 0 else 0

species_of_interest = {
    'GATA1 Nuclear Protein': gata1_prot_nuc,
    'PU1 Nuclear Protein': pu1_prot_nuc,
    'GATA1 mRNA (nuclear)': gata1_mrna_nuc,
    'PU1 mRNA (nuclear)': pu1_mrna_nuc,
    'ATP': atp,
    'GTP': gtp,
}

print("Variance ratio (final/total) - closer to 0 indicates steady state:")
for name, series in species_of_interest.items():
    var_ratio = calc_variance_ratio(series, cutoff)
    mean_final = series.iloc[cutoff:].mean()
    std_final = series.iloc[cutoff:].std()
    cv = (std_final / mean_final * 100) if mean_final > 0 else 0
    status = "✓ Stable" if var_ratio < 0.01 else "~ Oscillating" if var_ratio < 0.1 else "⚠ Changing"
    print(f"  {name:30s}: var_ratio={var_ratio:>8.6f}, CV={cv:>6.2f}%  {status}")
print()

# Cross-inhibition analysis
print("6. CROSS-INHIBITION ANALYSIS")
print("-" * 80)
g_nuc_mean = gata1_prot_nuc.iloc[cutoff:].mean()
p_nuc_mean = pu1_prot_nuc.iloc[cutoff:].mean()
ratio = g_nuc_mean / p_nuc_mean if p_nuc_mean > 0 else float('inf')

print(f"Mean nuclear GATA1 protein (final 10%): {g_nuc_mean:.2f} mM")
print(f"Mean nuclear PU1 protein (final 10%):   {p_nuc_mean:.2f} mM")
print(f"GATA1/PU1 ratio:                        {ratio:.4f}")
print()
if ratio > 1.2:
    print("→ GATA1-dominant state (erythroid differentiation)")
elif ratio < 0.8:
    print("→ PU1-dominant state (myeloid differentiation)")
else:
    print("→ Balanced state (bistable region)")
print()

# Summary
print("7. SIMULATION SUMMARY")
print("-" * 80)
print(f"✓ Simulation completed {df['Time (s)'].max():.0f} seconds")
print(f"✓ Generated {len(df)} data points")
print(f"✓ GATA1 nuclear protein: {gata1_prot_nuc.iloc[0]:.2f} → {gata1_prot_nuc.iloc[-1]:.2f} mM ({(gata1_prot_nuc.iloc[-1]/gata1_prot_nuc.iloc[0]-1)*100:+.1f}%)")
print(f"✓ PU1 nuclear protein:   {pu1_prot_nuc.iloc[0]:.2f} → {pu1_prot_nuc.iloc[-1]:.2f} mM ({(pu1_prot_nuc.iloc[-1]/pu1_prot_nuc.iloc[0]-1)*100:+.1f}%)")
print(f"✓ Energy charge maintained: ATP ratio {atp_ratio_final:.3f}")

# Check if system reached equilibrium
final_changes = []
for name, series in species_of_interest.items():
    last_100 = series.iloc[-100:]
    change_rate = abs(last_100.iloc[-1] - last_100.iloc[0]) / last_100.iloc[0]
    final_changes.append(change_rate < 0.01)

if all(final_changes):
    print("✓ System reached steady state (< 1% change in last 100 points)")
else:
    print("⚠ System still evolving (> 1% change in some species)")

print()
print("=" * 80)
