#!/usr/bin/env python3
"""Analyze EPO sweep results (0, 50, 500, 5000) from experiments run before full adaptive mode update.

This script compares lineage commitment outcomes across different EPO concentrations.
"""

import json
import pandas as pd
from pathlib import Path
import numpy as np

# Experiment directories
BASE_DIR = Path("workspace/projects/gata/experiments/results")
EPO_VALUES = [0, 50, 500, 5000]

# Find most recent experiments for each EPO value
def find_latest_experiment(epo_value):
    """Find most recent experiment directory for given EPO value (EPO-only, no GCSF)."""
    pattern = f"experiment_EPO_external={epo_value}_20260218*"
    matches = sorted(BASE_DIR.glob(pattern), reverse=True)
    if matches:
        return matches[0]
    return None

print("=" * 80)
print("EPO SWEEP ANALYSIS (0, 50, 500, 5000)")
print("Results from experiments run BEFORE full adaptive mode update")
print("=" * 80)
print()

results = []

for epo in EPO_VALUES:
    exp_dir = find_latest_experiment(epo)
    
    if exp_dir is None:
        print(f"⚠️  EPO={epo}: No experiment found")
        continue
    
    # Load statistics
    stats_file = exp_dir / "statistics.json"
    if not stats_file.exists():
        print(f"⚠️  EPO={epo}: No statistics.json in {exp_dir.name}")
        continue
    
    with open(stats_file) as f:
        stats = json.load(f)
    
    # Load config
    config_file = exp_dir / "config.json"
    with open(config_file) as f:
        config = json.load(f)
    
    # Extract key metrics
    result = {
        'EPO': epo,
        'experiment_dir': exp_dir.name,
        'duration': config.get('duration', 'N/A'),
        'dt': config.get('dt', 'N/A')
    }
    
    # Extract final values from trajectories
    for place_name, trajectory in stats.items():
        if isinstance(trajectory, list) and len(trajectory) > 0:
            result[f'{place_name}_final'] = trajectory[-1]
            result[f'{place_name}_mean'] = np.mean(trajectory)
            result[f'{place_name}_max'] = np.max(trajectory)
    
    results.append(result)
    
    print(f"✅ EPO={epo:5d}: Loaded from {exp_dir.name}")

print()
print("=" * 80)
print("LINEAGE COMMITMENT ANALYSIS")
print("=" * 80)
print()

# Create comparison table
df = pd.DataFrame(results)

# Key places to analyze
key_metrics = {
    'GATA1_Protein_nuc': 'GATA1 (nuclear)',
    'PU1_Protein_nuc': 'PU.1 (nuclear)',
    'ATP': 'ATP',
    'GTP': 'GTP',
    'EPO_external': 'EPO (external)',
}

print("FINAL PROTEIN LEVELS (at t=2000s):")
print("-" * 80)
print(f"{'EPO':>8s}  {'GATA1_nuc':>12s}  {'PU1_nuc':>12s}  {'Ratio':>12s}  {'Lineage':>15s}")
print("-" * 80)

for idx, row in df.iterrows():
    epo = row['EPO']
    gata1 = row.get('GATA1_Protein_nuc_final', 0)
    pu1 = row.get('PU1_Protein_nuc_final', 0)
    
    ratio = gata1 / pu1 if pu1 > 0 else float('inf')
    
    # Determine lineage commitment
    if ratio > 10:
        lineage = "Erythroid ✅"
    elif ratio < 0.1:
        lineage = "Myeloid ✅"
    else:
        lineage = "Uncommitted ⚠️"
    
    print(f"{epo:8d}  {gata1:12.2f}  {pu1:12.2f}  {ratio:12.2f}  {lineage:>15s}")

print()
print()
print("ENERGY CHARGE (final values):")
print("-" * 80)
print(f"{'EPO':>8s}  {'ATP':>12s}  {'GTP':>12s}  {'ATP charge':>12s}  {'GTP charge':>12s}")
print("-" * 80)

for idx, row in df.iterrows():
    epo = row['EPO']
    atp = row.get('ATP_final', 0)
    adp = row.get('ADP_final', 0)
    amp = row.get('AMP_final', 0)
    
    gtp = row.get('GTP_final', 0)
    gdp = row.get('GDP_final', 0)
    
    # Energy charge = (ATP + 0.5*ADP) / (ATP + ADP + AMP)
    total_adenylates = atp + adp + amp
    atp_charge = (atp + 0.5 * adp) / total_adenylates if total_adenylates > 0 else 0
    
    total_guanylates = gtp + gdp
    gtp_charge = gtp / total_guanylates if total_guanylates > 0 else 0
    
    print(f"{epo:8d}  {atp:12.2f}  {gtp:12.2f}  {atp_charge:12.3f}  {gtp_charge:12.3f}")

print()
print()
print("RECEPTOR DYNAMICS (final values):")
print("-" * 80)
print(f"{'EPO':>8s}  {'EPO_external':>15s}  {'EPOR_surface':>15s}  {'EPOR_internal':>15s}")
print("-" * 80)

for idx, row in df.iterrows():
    epo = row['EPO']
    epo_ext = row.get('EPO_external_final', 0)
    epor_surf = row.get('EPOR_surface_final', 0)
    epor_int = row.get('EPOR_internal_final', 0)
    
    print(f"{epo:8d}  {epo_ext:15.2f}  {epor_surf:15.2f}  {epor_int:15.2f}")

print()
print()
print("=" * 80)
print("DOSE-RESPONSE SUMMARY")
print("=" * 80)
print()

print("📊 Key Observations:")
print()

# Analyze dose-response
gata1_values = []
pu1_values = []
ratios = []

for idx, row in df.iterrows():
    gata1 = row.get('GATA1_Protein_nuc_final', 0)
    pu1 = row.get('PU1_Protein_nuc_final', 0)
    ratio = gata1 / pu1 if pu1 > 0 else float('inf')
    
    gata1_values.append(gata1)
    pu1_values.append(pu1)
    ratios.append(ratio)

print(f"1. GATA1 (erythroid TF) levels:")
print(f"   • EPO=0:    {gata1_values[0]:.2f}")
print(f"   • EPO=50:   {gata1_values[1]:.2f} ({(gata1_values[1]/gata1_values[0] - 1)*100:+.1f}%)")
print(f"   • EPO=500:  {gata1_values[2]:.2f} ({(gata1_values[2]/gata1_values[0] - 1)*100:+.1f}%)")
print(f"   • EPO=5000: {gata1_values[3]:.2f} ({(gata1_values[3]/gata1_values[0] - 1)*100:+.1f}%)")
print()

print(f"2. PU.1 (myeloid TF) levels:")
print(f"   • EPO=0:    {pu1_values[0]:.2f}")
print(f"   • EPO=50:   {pu1_values[1]:.2f} ({(pu1_values[1]/pu1_values[0] - 1)*100:+.1f}%)")
print(f"   • EPO=500:  {pu1_values[2]:.2f} ({(pu1_values[2]/pu1_values[0] - 1)*100:+.1f}%)")
print(f"   • EPO=5000: {pu1_values[3]:.2f} ({(pu1_values[3]/pu1_values[0] - 1)*100:+.1f}%)")
print()

print(f"3. Lineage commitment ratio (GATA1/PU.1):")
print(f"   • EPO=0:    {ratios[0]:.2f}")
print(f"   • EPO=50:   {ratios[1]:.2f}")
print(f"   • EPO=500:  {ratios[2]:.2f}")
print(f"   • EPO=5000: {ratios[3]:.2f}")
print()

# Determine EC50 (approximate)
print("4. Dose-response characteristics:")
if ratios[0] < 10 and ratios[-1] > 10:
    print("   ✅ System shows EPO dose-dependent commitment")
    print(f"   • Switch occurs between EPO={EPO_VALUES[0]} and EPO={EPO_VALUES[-1]}")
    
    # Find approximate EC50
    for i in range(len(ratios)-1):
        if ratios[i] < 10 and ratios[i+1] > 10:
            print(f"   • Commitment threshold crossed between EPO={EPO_VALUES[i]} and EPO={EPO_VALUES[i+1]}")
            break
elif ratios[0] > 10:
    print("   ⚠️  Already committed at EPO=0 (basal transcription sufficient)")
else:
    print("   ⚠️  No commitment achieved even at EPO=5000")

print()
print()
print("=" * 80)
print("EXPORT DATA FOR PLOTTING")
print("=" * 80)
print()

# Create summary CSV
summary_file = BASE_DIR / "epo_sweep_summary_20260218.csv"
summary_data = []

for idx, row in df.iterrows():
    epo = row['EPO']
    gata1 = row.get('GATA1_Protein_nuc_final', 0)
    pu1 = row.get('PU1_Protein_nuc_final', 0)
    ratio = gata1 / pu1 if pu1 > 0 else float('inf')
    
    atp = row.get('ATP_final', 0)
    gtp = row.get('GTP_final', 0)
    
    summary_data.append({
        'EPO_concentration': epo,
        'GATA1_nuclear': gata1,
        'PU1_nuclear': pu1,
        'GATA1_PU1_ratio': ratio,
        'ATP': atp,
        'GTP': gtp,
        'experiment_dir': row['experiment_dir']
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv(summary_file, index=False)

print(f"✅ Summary saved to: {summary_file}")
print()
print("Columns:")
for col in summary_df.columns:
    print(f"  • {col}")
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("These results show model behavior BEFORE full adaptive mode was enabled.")
print("All 28 transitions were already adaptive, so behavior is consistent.")
print()
print("Next steps:")
print("  1. Compare with results after model changes (if any)")
print("  2. Create dose-response plots (GATA1/PU.1 ratio vs EPO)")
print("  3. Analyze commitment timing across different EPO doses")
print("  4. Examine stochastic noise in nucleus vs deterministic cytoplasm behavior")
print()
