#!/usr/bin/env python3
"""Extract only key metrics from EPO sweep - no full trajectory printing."""

import json
import sys
from pathlib import Path

BASE_DIR = Path("workspace/projects/gata/experiments/results")
EPO_VALUES = [0, 50, 500, 5000]

print("\nOPTION 9: SWEEP OPTIMIZATION RESULTS")
print("=" * 60)
print("\nCurrent EPO Sweep Results (4 points):\n")

results = []
for epo in EPO_VALUES:
    pattern = f"experiment_EPO_external={epo}_20260218*"
    matches = sorted(BASE_DIR.glob(pattern), reverse=True)
    
    if not matches:
        print(f"  EPO={epo:5d}: NOT FOUND", file=sys.stderr)
        continue
    
    # Load JSON but extract only final values
    with open(matches[0] / "statistics.json") as f:
        stats = json.load(f)
    
    # Extract ONLY final values (last element)
    gata1_final = stats.get('GATA1_Protein_nuc', [0])[-1]
    pu1_final = stats.get('PU1_Protein_nuc', [0])[-1]
    
    # Calculate ratio
    ratio = gata1_final / pu1_final if pu1_final > 0.001 else 999.0
    
    # Commitment status
    committed = "✅ ERYTHROID" if ratio > 10 else "⚠️  Uncommitted"
    
    results.append((epo, ratio, gata1_final, pu1_final, committed))
    
    print(f"  EPO={epo:5d}: G/P Ratio={ratio:7.2f}  (GATA1={gata1_final:6.1f}, PU.1={pu1_final:6.1f}) {committed}")

print("\n" + "=" * 60)

# Analyze transition
uncommitted = [(epo, r) for epo, r, _, _, status in results if r < 10]
committed = [(epo, r) for epo, r, _, _, status in results if r >= 10]

print("\nTRANSITION ANALYSIS:\n")

if uncommitted and committed:
    epo_low = max(epo for epo, _ in uncommitted)
    epo_high = min(epo for epo, _ in committed)
    ratio_low = [r for e, r in uncommitted if e == epo_low][0]
    ratio_high = [r for e, r in committed if e == epo_high][0]
    
    print(f"  ✅ Transition captured between EPO={epo_low} and EPO={epo_high}")
    print(f"     Last uncommitted: EPO={epo_low:5d}, Ratio={ratio_low:5.2f}")
    print(f"     First committed:  EPO={epo_high:5d}, Ratio={ratio_high:5.2f}")
    print(f"     Gap size: {epo_high - epo_low} (10-fold)")
    print()
    print(f"  📊 Recommendation: Add 5-7 intermediate points\n")
    
    # Suggest finer grid
    import numpy as np
    log_low = np.log10(epo_low) if epo_low > 0 else 0
    log_high = np.log10(epo_high)
    fine_epo = np.logspace(log_low, log_high, 8)
    fine_epo = [int(x) for x in fine_epo if x >= 1]
    
    print("RECOMMENDED SWEEP DESIGNS:")
    print("-" * 60)
    print()
    print(f"🎯 Design 1: High-Resolution EPO Dose-Response")
    print(f"   EPO values: {fine_epo}")
    print(f"   Purpose: Accurate EC50 and Hill coefficient")
    print(f"   Simulations: {len(fine_epo)} × 2000s ≈ {len(fine_epo)*0.5:.1f} min")
    print()
    
    print(f"🎯 Design 2: GCSF Sweep (Myeloid Control)")
    print(f"   GCSF values: [0, 50, 500, 5000]")
    print(f"   EPO: 0 (no erythroid signal)")
    print(f"   Purpose: Validate reciprocal PU.1 commitment")
    print(f"   Simulations: 4 × 2000s ≈ 2 min")
    print()
    
    print(f"🎯 Design 3: Factorial EPO × GCSF")
    print(f"   EPO:  [0, 50, 250, 500]")
    print(f"   GCSF: [0, 50, 250, 500]")
    print(f"   Purpose: Signal competition, lineage conflict")
    print(f"   Simulations: 4×4 = 16 × 2000s ≈ 8 min")
    
elif not committed:
    print(f"  ⚠️  NO COMMITMENT even at EPO={max(epo for epo, _ in results)}")
    print(f"     → May need higher EPO doses or check model")
    
elif not uncommitted:
    print(f"  ⚠️  ALREADY COMMITTED at EPO=0")
    print(f"     → Check basal transcription rates")

print()
print("=" * 60)
print(f"\n✅ Analysis complete\n")

# Save compact summary (no large arrays)
summary = {
    "epo_values": EPO_VALUES,
    "ratios": {str(epo): round(ratio, 2) for epo, ratio, _, _, _ in results},
    "transition": {
        "captured": bool(uncommitted and committed),
        "epo_range": [epo_low, epo_high] if (uncommitted and committed) else None
    }
}

output_file = BASE_DIR / "sweep_analysis_summary.json"
with open(output_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"Summary saved: {output_file.relative_to(Path.cwd())}\n")
