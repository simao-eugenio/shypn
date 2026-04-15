#!/usr/bin/env python3
"""Extract EPO sweep results using correct place IDs."""

import json
from pathlib import Path

BASE_DIR = Path("/home/simao/projetos/shypn/workspace/projects/gata/experiments/results")
EPO_VALUES = [0, 50, 500, 5000]

# Place IDs from metadata
GATA1_PROTEIN_NUC_ID = "P17"
PU1_PROTEIN_NUC_ID = "P18"

results = []
results.append("=" * 80)
results.append("EPO SWEEP OPTIMIZATION - Final Results")
results.append("=" * 80 + "\n")

for epo in EPO_VALUES:
    pattern = f"experiment_EPO_external={epo}_20260218*"
    matches = sorted(BASE_DIR.glob(pattern), reverse=True)
    
    if matches:
        try:
            with open(matches[0] / "statistics.json") as f:
                stats = json.load(f)
            
            # Access species_statistics
            species = stats.get('species_statistics', {})
            
            # Get GATA1 and PU.1 data
            gata1_data = species.get(GATA1_PROTEIN_NUC_ID, {})
            pu1_data = species.get(PU1_PROTEIN_NUC_ID, {})
            
            # Extract mean values (trajectories for replicates)
            gata1_mean = gata1_data.get('mean', [0])
            pu1_mean = pu1_data.get('mean', [0])
            
            # Final values
            g_final = gata1_mean[-1] if gata1_mean else 0
            p_final = pu1_mean[-1] if pu1_mean else 0
            
            # Calculate ratio
            ratio = g_final / p_final if p_final > 0.01 else 999
            
            # Commitment status
            status = "✅ ERYTHROID" if ratio > 10 else "⚠️  Uncommitted"
            
            results.append(f"EPO={epo:5d}:  GATA1={g_final:8.2f}  PU.1={p_final:8.2f}  Ratio={ratio:8.2f}  {status}")
            
        except Exception as e:
            results.append(f"EPO={epo:5d}:  ERROR: {str(e)[:60]}")
    else:
        results.append(f"EPO={epo:5d}:  NOT FOUND")

results.append("\n" + "=" * 80)

# Write results
output_file = BASE_DIR / "EPO_FINAL_RESULTS.txt"
with open(output_file, 'w') as f:
    f.write('\n'.join(results))

# Also print
for line in results:
    print(line)

print(f"\n✅ Results saved to: {output_file.name}")
