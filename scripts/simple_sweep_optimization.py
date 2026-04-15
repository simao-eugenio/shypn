#!/usr/bin/env python3
"""Simple EPO sweep optimization - clean output."""

import json
import numpy as np
from pathlib import Path

BASE_DIR = Path("workspace/projects/gata/experiments/results")
EPO_VALUES = [0, 50, 500, 5000]

# Load data
ratios = []
for epo in EPO_VALUES:
    pattern = f"experiment_EPO_external={epo}_20260218*"
    matches = sorted(BASE_DIR.glob(pattern), reverse=True)
    
    if matches:
        with open(matches[0] / "statistics.json") as f:
            stats = json.load(f)
        
        gata1 = stats.get('GATA1_Protein_nuc', [0])[-1]
        pu1 = stats.get('PU1_Protein_nuc', [0])[-1]
        ratio = gata1 / pu1 if pu1 > 0 else 999
        ratios.append((epo, ratio, gata1, pu1))

print("OPTION 9: PARAMETER SWEEP OPTIMIZATION")
print("=" * 80)
print()

print("Current Results:")
for epo, ratio, gata1, pu1 in ratios:
    status = "✅ Committed" if ratio > 10 else "⚠️  Uncommitted"
    print(f"  EPO={epo:5d}: GATA1={gata1:8.2f}, PU.1={pu1:8.2f}, Ratio={ratio:8.2f} {status}")

print()
print("=" * 80)

# Find transition
uncommitted = [(e, r) for e, r, _, _ in ratios if r < 10]
committed = [(e, r) for e, r, _, _ in ratios if r > 10]

if uncommitted and committed:
    min_uncommitted = max(e for e, _ in uncommitted)
    min_committed = min(e for e, _ in committed)
    
    print(f"✅ TRANSITION CAPTURED")
    print(f"   Last uncommitted: EPO = {min_uncommitted}")
    print(f"   First committed:  EPO = {min_committed}")
    print(f"   Gap: {min_committed - min_uncommitted} (large gap!)")
    print()
    
    # Recommend finer sampling
    if min_uncommitted > 0:
        # Log-spaced
        n_points = 7
        log_min = np.log10(min_uncommitted)
        log_max = np.log10(min_committed)
        fine_grid = np.logspace(log_min, log_max, n_points)
        fine_grid = [int(x) for x in fine_grid]
    else:
        fine_grid = [0, 10, 25, 50, 75, 100, 150, 250, 500]
    
    print("RECOMMENDATIONS:")
    print()
    print("🎯 Design 1: High-resolution EPO sweep")
    print(f"   EPO values: {fine_grid}")
    print(f"   Purpose: Accurate EC50 determination")
    print()
    
    print("🎯 Design 2: GCSF sweep (reciprocal control)")
    print(f"   GCSF values: [0, 50, 500, 5000]")
    print(f"   EPO: 0")
    print(f"   Purpose: Test myeloid commitment")
    print()
    
    print("🎯 Design 3: Factorial EPO × GCSF")
    print(f"   EPO: [0, 50, 250, 500]")
    print(f"   GCSF: [0, 50, 250, 500]")
    print(f"   Total: 16 simulations")
    print(f"   Purpose: Signal competition analysis")
    
elif not committed:
    print(f"⚠️  NO COMMITMENT at EPO={max(e for e, _ in ratios)}")
    print(f"   → Increase max EPO to 10000 or troubleshoot model")
    
else:
    print(f"⚠️  ALREADY COMMITTED at EPO=0")
    print(f"   → May need to reduce basal transcription")

print()
print("=" * 80)

# Save simple recommendations
output = {
    "status": "transition_captured" if (uncommitted and committed) else "needs_adjustment",
    "current_epo_range": EPO_VALUES,
    "current_ratios": {str(e): float(r) for e, r, _, _ in ratios},
    "recommendations": {
        "high_res_epo": fine_grid if (uncommitted and committed) else None,
        "gcsf_sweep": [0, 50, 500, 5000],
        "factorial_grid": {"epo": [0, 50, 250, 500], "gcsf": [0, 50, 250, 500]}
    }
}

with open(BASE_DIR / "sweep_recommendations.json", 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ Saved to: sweep_recommendations.json")
