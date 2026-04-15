#!/usr/bin/env python3
"""
Factorial Experiment Analysis for GATA1/PU1 Gene Regulatory Network
Analyzes a 3x3 factorial design with EPO and GCSF external signals
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Experiment directory
EXP_DIR = Path("workspace/projects/gata/experiments/factorial_3")

# EPO and GCSF levels in the factorial design
EPO_LEVELS = [0, 100, 500]
GCSF_LEVELS = [0, 100, 500]

print("=" * 80)
print("FACTORIAL EXPERIMENT ANALYSIS - GATA1/PU1 GENE REGULATORY NETWORK")
print("=" * 80)
print()

# Storage for results
results = []

for epo in EPO_LEVELS:
    for gcsf in GCSF_LEVELS:
        filename = f"EPO_external_{epo}_GCSF_external_{gcsf}.csv"
        filepath = EXP_DIR / filename
        
        if not filepath.exists():
            print(f"⚠ Missing: {filename}")
            continue
        
        # Read the CSV file
        try:
            # Read file skipping metadata lines
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            # Find the header line (starts with "Time,")
            header_line_idx = None
            for i, line in enumerate(lines):
                if line.startswith('Time,'):
                    header_line_idx = i
                    break
            
            if header_line_idx is None:
                print(f"⚠ Could not find header in {filename}")
                continue
            
            #Find where data ends (before Replicate_ID summary)
            end_line_idx = None
            for i in range(header_line_idx + 1, len(lines)):
                if lines[i].startswith('Replicate_ID') or lines[i].strip() == '':
                    end_line_idx = i
                    break
            
            # Read only the data rows
            if end_line_idx:
                nrows = end_line_idx - header_line_idx - 1
                df = pd.read_csv(filepath, skiprows=header_line_idx, nrows=nrows)
            else:
                df = pd.read_csv(filepath, skiprows=header_line_idx)
            
            # Get final time point values
            final = df.iloc[-1]
            
            # Extract key molecular species - using place IDs
            gata1_nuc_protein = final.get('P14', 0)
            pu1_nuc_protein = final.get('P16', 0)
            gata1_cyto_protein = final.get('P13', 0)
            pu1_cyto_protein = final.get('P15', 0)
            
            gata1_nuc_mrna = final.get('P9', 0)
            pu1_nuc_mrna = final.get('P10', 0)
            gata1_cyto_mrna = final.get('P11', 0)
            pu1_cyto_mrna = final.get('P12', 0)
            
            atp = final.get('P21', 0)
            gtp = final.get('P23', 0)
            
            # Calculate ratios
            gata1_pu1_ratio = gata1_nuc_protein / (pu1_nuc_protein + 0.001)
            
            # Determine cell fate based on ratio
            if gata1_pu1_ratio > 1.5:
                fate = "GATA1-dominant (Erythroid)"
            elif gata1_pu1_ratio < 0.67:
                fate = "PU1-dominant (Myeloid)"
            else:
                fate = "Bistable/Mixed"
            
            results.append({
                'EPO': epo,
                'GCSF': gcsf,
                'GATA1_nuc': gata1_nuc_protein,
                'PU1_nuc': pu1_nuc_protein,
                'GATA1/PU1_ratio': gata1_pu1_ratio,
                'Cell_Fate': fate,
                'GATA1_cyto': gata1_cyto_protein,
                'PU1_cyto': pu1_cyto_protein,
                'GATA1_mRNA_nuc': gata1_nuc_mrna,
                'PU1_mRNA_nuc': pu1_nuc_mrna,
                'GATA1_mRNA_cyto': gata1_cyto_mrna,
                'PU1_mRNA_cyto': pu1_cyto_mrna,
                'ATP': atp,
                'GTP': gtp
            })
            
        except Exception as e:
            print(f"⚠ Error reading {filename}: {e}")
            continue

# Create results DataFrame
results_df = pd.DataFrame(results)

print("1. FACTORIAL DESIGN SUMMARY")
print("-" * 80)
print(f"EPO levels: {EPO_LEVELS}")
print(f"GCSF levels: {GCSF_LEVELS}")
print(f"Total conditions: {len(EPO_LEVELS) * len(GCSF_LEVELS)}")
print(f"Conditions analyzed: {len(results_df)}")
print()

print("2. NUCLEAR PROTEIN LEVELS BY CONDITION")
print("-" * 80)
print(f"{'EPO':>5} {'GCSF':>5} {'GATA1_nuc':>12} {'PU1_nuc':>12} {'GATA1/PU1':>12} {'Cell Fate':>25}")
print("-" * 80)
for _, row in results_df.iterrows():
    print(f"{row['EPO']:>5.0f} {row['GCSF']:>5.0f} "
          f"{row['GATA1_nuc']:>12.2f} {row['PU1_nuc']:>12.2f} "
          f"{row['GATA1/PU1_ratio']:>12.3f} {row['Cell_Fate']:>25}")
print()

print("3. CELL FATE DISTRIBUTION")
print("-" * 80)
fate_counts = results_df['Cell_Fate'].value_counts()
for fate, count in fate_counts.items():
    print(f"{fate:>30}: {count:>2} conditions ({100*count/len(results_df):>5.1f}%)")
print()

print("4. SIGNAL RESPONSE PATTERNS")
print("-" * 80)

# EPO response (fixing GCSF at different levels)
print("EPO Response (at different GCSF levels):")
for gcsf in GCSF_LEVELS:
    subset = results_df[results_df['GCSF'] == gcsf].sort_values('EPO')
    if len(subset) > 0:
        print(f"  GCSF={gcsf:>3}: ", end="")
        for _, row in subset.iterrows():
            print(f"EPO={row['EPO']:>3} → GATA1/PU1={row['GATA1/PU1_ratio']:.2f}  ", end="")
        print()

print()
print("GCSF Response (at different EPO levels):")
for epo in EPO_LEVELS:
    subset = results_df[results_df['EPO'] == epo].sort_values('GCSF')
    if len(subset) > 0:
        print(f"  EPO={epo:>3}:  ", end="")
        for _, row in subset.iterrows():
            print(f"GCSF={row['GCSF']:>3} → GATA1/PU1={row['GATA1/PU1_ratio']:.2f}  ", end="")
        print()

print()

print("5. ENERGY METABOLISM")
print("-" * 80)
print(f"ATP range: {results_df['ATP'].min():.2f} - {results_df['ATP'].max():.2f} mM")
print(f"ATP mean:  {results_df['ATP'].mean():.2f} ± {results_df['ATP'].std():.2f} mM")
print(f"GTP range: {results_df['GTP'].min():.2f} - {results_df['GTP'].max():.2f} mM")
print(f"GTP mean:  {results_df['GTP'].mean():.2f} ± {results_df['GTP'].std():.2f} mM")
print()

print("6. mRNA ACCUMULATION")
print("-" * 80)
print(f"GATA1 nuclear mRNA:  {results_df['GATA1_mRNA_nuc'].mean():.1f} ± {results_df['GATA1_mRNA_nuc'].std():.1f} mM")
print(f"PU1 nuclear mRNA:    {results_df['PU1_mRNA_nuc'].mean():.1f} ± {results_df['PU1_mRNA_nuc'].std():.1f} mM")
print(f"GATA1 cyto mRNA:     {results_df['GATA1_mRNA_cyto'].mean():.1f} ± {results_df['GATA1_mRNA_cyto'].std():.1f} mM")
print(f"PU1 cyto mRNA:       {results_df['PU1_mRNA_cyto'].mean():.1f} ± {results_df['PU1_mRNA_cyto'].std():.1f} mM")
print()

print("7. KEY INSIGHTS")
print("-" * 80)

# EPO effect
epo_0 = results_df[results_df['EPO'] == 0]['GATA1/PU1_ratio'].mean()
epo_500 = results_df[results_df['EPO'] == 500]['GATA1/PU1_ratio'].mean()
epo_effect = ((epo_500 - epo_0) / epo_0) * 100

# GCSF effect  
gcsf_0 = results_df[results_df['GCSF'] == 0]['GATA1/PU1_ratio'].mean()
gcsf_500 = results_df[results_df['GCSF'] == 500]['GATA1/PU1_ratio'].mean()
gcsf_effect = ((gcsf_500 - gcsf_0) / gcsf_0) * 100

print(f"• EPO effect on GATA1/PU1 ratio: {epo_effect:+.1f}% (0→500)")
print(f"• GCSF effect on GATA1/PU1 ratio: {gcsf_effect:+.1f}% (0→500)")

# Interaction
high_high = results_df[(results_df['EPO'] == 500) & (results_df['GCSF'] == 500)]['GATA1/PU1_ratio'].values[0]
low_low = results_df[(results_df['EPO'] == 0) & (results_df['GCSF'] == 0)]['GATA1/PU1_ratio'].values[0]
print(f"• Ratio range: {results_df['GATA1/PU1_ratio'].min():.3f} - {results_df['GATA1/PU1_ratio'].max():.3f}")
print(f"• High EPO + High GCSF: GATA1/PU1 = {high_high:.3f}")
print(f"• No signals (baseline): GATA1/PU1 = {low_low:.3f}")

# Check for bistability
bistable_count = len(results_df[results_df['Cell_Fate'].str.contains('Bistable')])
if bistable_count > 0:
    print(f"• {bistable_count} conditions show bistable/mixed behavior")
else:
    print("• Strong lineage commitment observed across all conditions")

print()
print("=" * 80)
print("Analysis complete!")
print("=" * 80)
