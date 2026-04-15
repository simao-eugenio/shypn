#!/usr/bin/env python3
"""EPO sweep analysis - write results to file."""

import json
from pathlib import Path

BASE_DIR = Path("workspace/projects/gata/experiments/results")
OUTPUT_FILE = Path("workspace/projects/gata/experiments/results/EPO_SWEEP_SUMMARY.txt")
EPO_VALUES = [0, 50, 500, 5000]

with open(OUTPUT_FILE, 'w') as out:
    out.write("=" * 80 + "\n")
    out.write("EPO SWEEP RESULTS (0, 50, 500, 5000)\n")
    out.write("Experiments run: 2026-02-18 09:03-09:04\n")
    out.write("Before full adaptadaptive mode update (already all transitions were adaptive)\n")
    out.write("=" * 80 + "\n\n")
    
    results = []
    
    for epo in EPO_VALUES:
        pattern = f"experiment_EPO_external={epo}_20260218*"
        matches = sorted(BASE_DIR.glob(pattern), reverse=True)
        
        if not matches:
            out.write(f"EPO={epo}: NO DATA FOUND\n")
            continue
        
        exp_dir = matches[0]
        stats_file = exp_dir / "statistics.json"
        
        with open(stats_file) as f:
            stats = json.load(f)
        
        # Extract key metrics
        gata1 = stats.get('GATA1_Protein_nuc', [0])[-1] if 'GATA1_Protein_nuc' in stats else 0
        pu1 = stats.get('PU1_Protein_nuc', [0])[-1] if 'PU1_Protein_nuc' in stats else 0
        ratio = gata1 / pu1 if pu1 > 0 else 999
        
        atp = stats.get('ATP', [0])[-1] if 'ATP' in stats else 0
        gtp = stats.get('GTP', [0])[-1] if 'GTP' in stats else 0
        
        lineage = "Erythroid ✅" if ratio > 10 else ("Myeloid ✅" if ratio < 0.1 else "Uncommitted ⚠️")
        
        results.append({
            'epo': epo,
            'gata1': gata1,
            'pu1': pu1,
            'ratio': ratio,
            'lineage': lineage,
            'atp': atp,
            'gtp': gtp
        })
        
        out.write(f"✅ EPO={epo} loaded from {exp_dir.name}\n")
    
    out.write("\n" + "=" * 80 + "\n")
    out.write("LINEAGE COMMITMENT (Final values at t=2000s)\n")
    out.write("=" * 80 + "\n\n")
    out.write(f"{'EPO':>8s}  {'GATA1':>12s}  {'PU.1':>12s}  {'Ratio':>12s}  {'Lineage':>18s}\n")
    out.write("-" * 80 + "\n")
    
    for r in results:
        out.write(f"{r['epo']:8d}  {r['gata1']:12.2f}  {r['pu1']:12.2f}  {r['ratio']:12.2f}  {r['lineage']:>18s}\n")
    
    out.write("\n" + "=" * 80 + "\n")
    out.write("DOSE-RESPONSE ANALYSIS\n")
    out.write("=" * 80 + "\n\n")
    
    out.write(f"GATA1 response to EPO:\n")
    for i, r in enumerate(results):
        if i == 0:
            out.write(f"  EPO={r['epo']:5d}: GATA1={r['gata1']:8.2f} (baseline)\n")
        else:
            fold_change = r['gata1'] / results[0]['gata1']
            percent = (fold_change - 1) * 100
            out.write(f"  EPO={r['epo']:5d}: GATA1={r['gata1']:8.2f} ({fold_change:.2f}x baseline, {percent:+.1f}%)\n")
    
    out.write(f"\nPU.1 response to EPO:\n")
    for i, r in enumerate(results):
        if i == 0:
            out.write(f"  EPO={r['epo']:5d}: PU.1={r['pu1']:8.2f} (baseline)\n")
        else:
            fold_change = r['pu1'] / results[0]['pu1']
            percent = (fold_change - 1) * 100
            out.write(f"  EPO={r['epo']:5d}: PU.1={r['pu1']:8.2f} ({fold_change:.2f}x baseline, {percent:+.1f}%)\n")
    
    out.write(f"\nLineage commitment ratio (GATA1/PU.1):\n")
    for r in results:
        out.write(f"  EPO={r['epo']:5d}: Ratio={r['ratio']:8.2f}\n")
    
    out.write("\n" + "=" * 80 + "\n")
    out.write("KEY FINDINGS\n")
    out.write("=" * 80 + "\n\n")
    
    # Analyze commitment
    committed_indices = [i for i, r in enumerate(results) if r['ratio'] > 10]
    if committed_indices:
        first_committed = committed_indices[0]
        if first_committed == 0:
            out.write("• System already erythroid-committed at EPO=0 (basal transcription sufficient)\n")
        else:
            out.write(f"• Commitment threshold crossed between EPO={results[first_committed-1]['epo']} and EPO={results[first_committed]['epo']}\n")
    else:
        out.write("• NO erythroid commitment achieved (all ratios < 10)\n")
    
    out.write(f"\n• GATA1 increases {results[-1]['gata1']/results[0]['gata1']:.2f}-fold from EPO=0 to EPO=5000\n")
    out.write(f"• PU.1 changes {results[-1]['pu1']/results[0]['pu1']:.2f}-fold from EPO=0 to EPO=5000\n")
    out.write(f"• Final ratio at EPO=5000: {results[-1]['ratio']:.2f}\n")
    
    out.write("\n" + "=" * 80 + "\n")

print(f"✅ Analysis written to: {OUTPUT_FILE}")
print("Preview:")
with open(OUTPUT_FILE) as f:
    for i, line in enumerate(f):
        if i < 50:  # Show first 50 lines
            print(line.rstrip())
        else:
            print("...")
            break
