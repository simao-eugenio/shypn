#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE_DIR = Path("/home/simao/projetos/shypn/workspace/projects/gata/experiments/results")
EPO_VALUES = [0, 50, 500, 5000]

output = []
output.append("\n" + "=" * 70)
output.append("OPTION 9: EPO SWEEP OPTIMIZATION RESULTS")
output.append("=" * 70 + "\n")

for epo in EPO_VALUES:
    pattern = f"experiment_EPO_external={epo}_20260218*"
    matches = sorted(BASE_DIR.glob(pattern), reverse=True)
    
    if matches:
        try:
            with open(matches[0] / "statistics.json") as f:
                stats = json.load(f)
            
            g = stats.get('GATA1_Protein_nuc', [0])
            p = stats.get('PU1_Protein_nuc', [0])
            
            g_final = g[-1] if g else 0
            p_final = p[-1] if p else 0
            ratio = g_final / p_final if p_final > 0.01 else 999
            status = "✅ ERYTHROID" if ratio > 10 else "⚠️  Uncommitted"
            
            output.append(f"EPO={epo:5d}: GATA1={g_final:7.2f}  PU.1={p_final:7.2f}  Ratio={ratio:7.2f}  {status}")
        except Exception as e:
            output.append(f"EPO={epo:5d}: ERROR - {e}")

# Write to file
output_file = BASE_DIR / "SWEEP_RESULTS.txt"
with open(output_file, 'w') as f:
    f.write('\n'.join(output))

print(f"Results written to: {output_file}")
print("Done!")
