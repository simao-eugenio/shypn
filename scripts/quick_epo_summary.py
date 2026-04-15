#!/usr/bin/env python3
"""Quick EPO sweep summary - minimal output."""

import json
from pathlib import Path
import numpy as np

BASE_DIR = Path("workspace/projects/gata/experiments/results")
EPO_VALUES = [0, 50, 500, 5000]

print("EPO Sweep Summary (before model update)")
print("=" * 60)

for epo in EPO_VALUES:
    pattern = f"experiment_EPO_external={epo}_20260218*"
    matches = sorted(BASE_DIR.glob(pattern), reverse=True)
    
    if not matches:
        print(f"EPO={epo:5d}: NO DATA")
        continue
    
    exp_dir = matches[0]
    stats_file = exp_dir / "statistics.json"
    
    with open(stats_file) as f:
        stats = json.load(f)
    
    # Get final values
    gata1 = stats.get('GATA1_Protein_nuc', [0])[-1] if 'GATA1_Protein_nuc' in stats else 0
    pu1 = stats.get('PU1_Protein_nuc', [0])[-1] if 'PU1_Protein_nuc' in stats else 0
    ratio = gata1 / pu1 if pu1 > 0 else 999
    
    lineage = "Erythroid" if ratio > 10 else ("Myeloid" if ratio < 0.1 else "Uncommitted")
    
    print(f"EPO={epo:5d}: GATA1={gata1:8.2f}, PU.1={pu1:8.2f}, Ratio={ratio:8.2f} → {lineage}")

print("=" * 60)
