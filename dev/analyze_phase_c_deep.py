#!/usr/bin/env python3
"""Phase C deep analysis — run_20260305_220333.
Goes beyond final-state ratios. Examines:
  §A  EPOR/GCSFR receptor dynamics (binding, internalization)
  §B  Cytoplasmic vs nuclear protein partitioning
  §C  Gene copy state (GATA1_Gene, PU1_Gene)
  §D  mRNA cytoplasmic/nuclear balance
  §E  Energy state (ATP/ADP, GTP/GDP, Pi)
  §F  Convergence dynamics from time-series (EPO=0.449 spotlight)
  §G  Phase portrait: GATA1_nuc vs PU1_nuc across all conditions
  §H  Receptor conservation checks
  §I  Simulation cost (wall-clock time per condition)
"""

import os

BASE = "workspace/projects/gata/experiments/results/run_20260305_220333"

# ── collection ────────────────────────────────────────────────────────────────

records = []   # (epo, ph, fate, row) where row = replicates.csv parsed dict
ts_data = {}   # (epo, ph) -> list of dicts { 'time':[], 'G1n':[], 'PU1n':[], ... }

# column indices in results.csv time-series
TS_COL = {
    'Time': 0, 'EPOR_free': 1, 'EPOR_internalized': 2,
    'GCSFR_bound': 3, 'GCSFR_internalized': 4,
    'GATA1_Gene': 5, 'PU1_Gene': 6,
    'GATA1_mRNA_nuc': 7, 'PU1_mRNA_nuc': 8,
    'GATA1_mRNA_cyto': 9, 'PU1_mRNA_cyto': 10,
    'GATA1_Protein_cyto': 11, 'PU1_Protein_cyto': 12,
    'GATA1_Protein_nuc': 13, 'PU1_Protein_nuc': 14,
    'ATP': 15, 'ADP': 16, 'GTP': 17, 'GDP': 18, 'Pi': 19,
    'EPOR_bound': 24, 'pGATA1_nuc': 27,
    'GCSFR_free': 23,
}

for d in sorted(os.listdir(BASE)):
    dpath = os.path.join(BASE, d)
    mf_path  = os.path.join(dpath, "mean_final_state.csv")
    rep_path = os.path.join(dpath, "replicates.csv")
    res_path = os.path.join(dpath, "results.csv")

    # ── true EPO / pH from header ──
    epo = ph = None
    for line in open(mf_path):
        if line.startswith("# P1_EPO_external:"):
            epo = float(line.split(":")[1].strip().split()[0])
        elif line.startswith("# P25_pH_nucleus:"):
            ph = float(line.split(":")[1].strip().split()[0])

    # ── replicates.csv (single row, N=1) ──
    rep_lines = [l for l in open(rep_path) if not l.startswith("#") and l.strip()]
    rep_hdr   = rep_lines[0].strip().split(",")
    rep_row   = rep_lines[1].strip().split(",")
    row = dict(zip(rep_hdr, rep_row))
    fate = row.get("fate_class", "?")

    records.append((epo, ph, fate, row))

    # ── results.csv time-series ──
    res_lines = [l for l in open(res_path) if not l.startswith("#") and l.strip()]
    ts_start = None
    for i, l in enumerate(res_lines):
        if "Species Statistics" in l:
            ts_start = i + 2  # skip header line
            break
    if ts_start is None:
        continue

    series = {k: [] for k in TS_COL}
    for l in res_lines[ts_start:]:
        parts = l.strip().split(",")
        if len(parts) < 29:
            break
        try:
            for k, ci in TS_COL.items():
                series[k].append(float(parts[ci]))
        except (ValueError, IndexError):
            break

    ts_data[(epo, ph)] = series

records.sort()
EPO_VALS = sorted({r[0] for r in records})
PH_VALS  = sorted({r[1] for r in records})
lookup   = {(r[0], r[1]): r for r in records}

def get(epo, ph):
    return lookup.get((epo, ph))

def fval(epo, ph, field):
    r = get(epo, ph)
    if r is None: return None
    try: return float(r[3].get(f"final_{field}", r[3].get(field, "nan")))
    except: return None

print("=" * 72)
print("PHASE C DEEP ANALYSIS — run_20260305_220333")
print("=" * 72)
print(f"  {len(records)} conditions  ×  1 trajectory each")
print(f"  EPO: {EPO_VALS}")
print(f"  pH:  {PH_VALS}")

# ── §A  EPOR/GCSFR receptor dynamics ─────────────────────────────────────────

print("\n" + "=" * 72)
print("§A  RECEPTOR DYNAMICS  (EPOR and GCSFR, final state)")
print("=" * 72)

print(f"\n{'EPO':>6} {'pH':>4}  {'E_free':>7} {'E_bound':>8} {'E_intern':>9} "
      f"{'E_total':>8} {'%bound':>7} {'%intern':>8}  "
      f"{'G_free':>7} {'G_bound':>8} {'G_intern':>9}")

for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        ef  = fval(epo, ph, "EPOR_free")
        eb  = fval(epo, ph, "EPOR_bound")
        ei  = fval(epo, ph, "EPOR_internalized")
        et  = (ef or 0) + (eb or 0) + (ei or 0)
        pb  = eb / et * 100 if et > 0 else 0
        pi  = ei / et * 100 if et > 0 else 0
        gf  = fval(epo, ph, "GCSFR_free")
        gb  = fval(epo, ph, "GCSFR_bound")
        gi  = fval(epo, ph, "GCSFR_internalized")
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        print(f"{epo:>6.3f} {ph:>4.1f}  {ef:>7.3f} {eb:>8.3f} {ei:>9.3f} "
              f"{et:>8.3f} {pb:>6.1f}% {pi:>7.1f}%  "
              f"{gf:>7.3f} {gb:>8.3f} {gi:>9.3f}{mark}")

print("\nNote: EPOR_internalized = signal-processed receptor (ligand-bound EPOR "
      "that has been endocytosed)")
print("      GCSFR values expected constant (GCSF=0.1 µM fixed across all conditions)")

# ── §B  Cytoplasmic vs nuclear protein partitioning ──────────────────────────

print("\n" + "=" * 72)
print("§B  PROTEIN PARTITIONING  (nuclear / [nuclear + cytoplasmic]  fraction)")
print("=" * 72)

print(f"\n{'EPO':>6} {'pH':>4} {'fate':>4}  "
      f"{'G1_nuc':>8} {'G1_cyto':>8} {'G1_%nuc':>9}  "
      f"{'PU1_nuc':>8} {'PU1_cyto':>8} {'PU1_%nuc':>9}")

for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        g1n  = fval(epo, ph, "GATA1_Protein_nuc")
        g1c  = fval(epo, ph, "GATA1_Protein_cyto")
        pu1n = fval(epo, ph, "PU1_Protein_nuc")
        pu1c = fval(epo, ph, "PU1_Protein_cyto")
        g1_frac  = g1n  / (g1n + g1c)  * 100 if (g1n and g1c and g1n+g1c > 0) else float('nan')
        pu1_frac = pu1n / (pu1n + pu1c) * 100 if (pu1n and pu1c and pu1n+pu1c > 0) else float('nan')
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        print(f"{epo:>6.3f} {ph:>4.1f} {fate:>4s}  "
              f"{g1n:>8.4f} {g1c:>8.4f} {g1_frac:>8.1f}%  "
              f"{pu1n:>8.4f} {pu1c:>8.4f} {pu1_frac:>8.1f}%{mark}")

# ── §C  Gene copy state ───────────────────────────────────────────────────────

print("\n" + "=" * 72)
print("§C  GENE COPY STATE  (final GATA1_Gene and PU1_Gene tokens)")
print("=" * 72)
print("These represent the number of 'active' gene copies driving transcription.\n")

print(f"{'EPO':>6} {'pH':>4} {'fate':>4}  {'GATA1_Gene':>12} {'PU1_Gene':>10}")
for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        g1g  = fval(epo, ph, "GATA1_Gene")
        pu1g = fval(epo, ph, "PU1_Gene")
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        print(f"{epo:>6.3f} {ph:>4.1f} {fate:>4s}  {g1g:>12.4f} {pu1g:>10.4f}{mark}")

# ── §D  mRNA cytoplasmic / nuclear balance ────────────────────────────────────

print("\n" + "=" * 72)
print("§D  mRNA EXPORT RATIO  (cytoplasmic / nuclear mRNA, final state)")
print("    Ratio > 1 means more mRNA in cytoplasm than nucleus (normal export)")
print("=" * 72)

print(f"\n{'EPO':>6} {'pH':>4} {'fate':>4}  "
      f"{'G1_mRNA_nuc':>12} {'G1_mRNA_cyto':>13} {'G1_export':>10}  "
      f"{'PU1_mRNA_nuc':>13} {'PU1_mRNA_cyto':>14} {'PU1_export':>11}")

for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        g1mn  = fval(epo, ph, "GATA1_mRNA_nuc")
        g1mc  = fval(epo, ph, "GATA1_mRNA_cyto")
        pu1mn = fval(epo, ph, "PU1_mRNA_nuc")
        pu1mc = fval(epo, ph, "PU1_mRNA_cyto")
        g1_exp  = g1mc  / g1mn  if (g1mn  and g1mn  > 0) else float('nan')
        pu1_exp = pu1mc / pu1mn if (pu1mn and pu1mn > 0) else float('nan')
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        print(f"{epo:>6.3f} {ph:>4.1f} {fate:>4s}  "
              f"{g1mn:>12.4f} {g1mc:>13.4f} {g1_exp:>10.3f}  "
              f"{pu1mn:>13.4f} {pu1mc:>14.4f} {pu1_exp:>11.3f}{mark}")

# ── §E  Energy state ──────────────────────────────────────────────────────────

print("\n" + "=" * 72)
print("§E  ENERGY STATE  (ATP/ADP, GTP/GDP, Pi, final state)")
print("=" * 72)

print(f"\n{'EPO':>6} {'pH':>4} {'fate':>4}  "
      f"{'ATP':>8} {'ADP':>8} {'ATP/ADP':>8}  "
      f"{'GTP':>8} {'GDP':>8} {'GTP/GDP':>8}  {'Pi':>8}")

for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        atp = fval(epo, ph, "ATP")
        adp = fval(epo, ph, "ADP")
        gtp = fval(epo, ph, "GTP")
        gdp = fval(epo, ph, "GDP")
        pi  = fval(epo, ph, "Pi")
        aa  = atp / adp if (adp and adp > 0) else float('nan')
        gg  = gtp / gdp if (gdp and gdp > 0) else float('nan')
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        print(f"{epo:>6.3f} {ph:>4.1f} {fate:>4s}  "
              f"{atp:>8.1f} {adp:>8.1f} {aa:>8.2f}  "
              f"{gtp:>8.1f} {gdp:>8.1f} {gg:>8.2f}  {pi:>8.1f}{mark}")

# ── §F  Convergence dynamics from time-series ─────────────────────────────────

print("\n" + "=" * 72)
print("§F  CONVERGENCE DYNAMICS  (EPO=0.449 spotlight — the pivotal dose)")
print("    Time-series: GATA1_Protein_nuc / PU1_Protein_nuc ratio over time")
print("=" * 72)

SPOTLIGHT_EPO = 0.449
THRESHOLD = 2.0   # ratio > 2.0 → erythroid-leaning

for ph in PH_VALS:
    key = (SPOTLIGHT_EPO, ph)
    if key not in ts_data:
        print(f"\n  pH={ph}: no time-series data")
        continue
    ts = ts_data[key]
    times = ts["Time"]
    g1n   = ts["GATA1_Protein_nuc"]
    pu1n  = ts["PU1_Protein_nuc"]
    ratios = [g / p if p > 0 else 0.0 for g, p in zip(g1n, pu1n)]

    n = len(times)
    r = get(SPOTLIGHT_EPO, ph)
    fate = r[2] if r else "?"

    # find first crossing of threshold
    cross_t = None
    for i, ratio in enumerate(ratios):
        if ratio > THRESHOLD:
            cross_t = times[i]
            break

    # sample at 0, 20%, 40%, 60%, 80%, final
    sample_idx = [0, n//5, 2*n//5, 3*n//5, 4*n//5, n-1]
    print(f"\n  pH={ph}  fate={fate}  {'threshold crossing t=' + f'{cross_t:.0f}s' if cross_t else 'NEVER crossed (stays uncommitted)'}")
    print(f"  {'time':>8}  {'GATA1_nuc':>10}  {'PU1_nuc':>10}  {'ratio':>8}")
    for i in sample_idx:
        if i < n:
            print(f"  {times[i]:>8.0f}  {g1n[i]:>10.4f}  {pu1n[i]:>10.4f}  {ratios[i]:>8.4f}")

# Also pGATA1 trajectory
print(f"\n  pGATA1_nuc trajectory for EPO=0.449 (signal input to GATA1 axis)")
for ph in PH_VALS:
    key = (SPOTLIGHT_EPO, ph)
    if key not in ts_data:
        continue
    ts = ts_data[key]
    times = ts["Time"]
    pg = ts["pGATA1_nuc"]
    n = len(times)
    sample_idx = [0, n//5, 2*n//5, 3*n//5, 4*n//5, n-1]
    vals = " → ".join(f"{pg[i]:.3f}" for i in sample_idx if i < n)
    r = get(SPOTLIGHT_EPO, ph)
    fate = r[2] if r else "?"
    print(f"  pH={ph} [{fate}]  t-sampled pGATA1: {vals}")

# ── §G  Phase portrait across all conditions ─────────────────────────────────

print("\n" + "=" * 72)
print("§G  PHASE PORTRAIT  (final GATA1_nuc vs PU1_nuc — attractor positions)")
print("=" * 72)
print("    Erythroid attractor: high GATA1, low PU1 (upper-left of diagonal)")
print("    Uncommitted:         near diagonal (GATA1 ≈ PU1)")
print()
print(f"  {'EPO':>6} {'pH':>4} {'fate':>4}  {'GATA1_nuc':>10} {'PU1_nuc':>9}  attractor zone")

for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        g1n  = fval(epo, ph, "GATA1_Protein_nuc")
        pu1n = fval(epo, ph, "PU1_Protein_nuc")
        ratio = g1n / pu1n if (pu1n and pu1n > 0) else 0
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        if ratio > 10:
            zone = "deep erythroid (PU1 depleted)"
        elif ratio > 4:
            zone = "erythroid"
        elif ratio > 2:
            zone = "erythroid-leaning"
        elif ratio > 0.8:
            zone = "SWITCH ZONE (near diagonal)"
        else:
            zone = "PU1-dominant"
        print(f"  {epo:>6.3f} {ph:>4.1f} {fate:>4s}  {g1n:>10.4f} {pu1n:>9.4f}  {zone}{mark}")

# ── §H  Receptor conservation ─────────────────────────────────────────────────

print("\n" + "=" * 72)
print("§H  RECEPTOR CONSERVATION CHECK")
print("    EPOR_free + EPOR_bound + EPOR_internalized should be constant (~50)")
print("    GCSFR_free + GCSFR_bound + GCSFR_internalized should be constant (~50)")
print("=" * 72)

print(f"\n  {'EPO':>6} {'pH':>4}  {'EPOR total':>11}  {'GCSFR total':>12}")
for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        ef  = fval(epo, ph, "EPOR_free") or 0
        eb  = fval(epo, ph, "EPOR_bound") or 0
        ei  = fval(epo, ph, "EPOR_internalized") or 0
        gf  = fval(epo, ph, "GCSFR_free") or 0
        gb  = fval(epo, ph, "GCSFR_bound") or 0
        gi  = fval(epo, ph, "GCSFR_internalized") or 0
        et  = ef + eb + ei
        gt  = gf + gb + gi
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        print(f"  {epo:>6.3f} {ph:>4.1f}  {et:>11.4f}  {gt:>12.4f}{mark}")

# ── §I  Simulation cost ───────────────────────────────────────────────────────

print("\n" + "=" * 72)
print("§I  SIMULATION COST  (wall-clock elapsed_time_s from replicates.csv)")
print("    Higher cost = higher SSA event rate = denser dynamics")
print("=" * 72)

print(f"\n  {'EPO':>6} {'pH':>4} {'fate':>4}  {'elapsed_s':>10}  {'n_events':>10}  {'compress':>9}")
for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        row = r[3]
        elapsed = float(row.get("elapsed_time_s", 0) or 0)
        n_kept  = int(row.get("n_kept", 0) or 0)
        n_tp    = int(row.get("n_timepoints", 0) or 0)
        cr_raw  = row.get("compression_ratio", "")
        cr      = float(cr_raw) if cr_raw else float('nan')
        fate    = r[2]
        mark    = " ◄" if fate == "unc" else ""
        # n_timepoints is the total SSA steps (proxied by n_kept / cr)
        raw_events = int(n_kept * cr) if not (cr != cr) else n_kept
        print(f"  {epo:>6.3f} {ph:>4.1f} {fate:>4s}  {elapsed:>10.1f}  {raw_events:>10d}  {cr:>9.3f}{mark}")

# ── §J  GCSFR signaling cross-comparison ─────────────────────────────────────

print("\n" + "=" * 72)
print("§J  GCSFR OCCUPANCY vs EPOR OCCUPANCY  (myeloid vs erythroid signal input)")
print("=" * 72)

print(f"\n  {'EPO':>6} {'pH':>4} {'fate':>4}  {'EPOR%occ':>9}  {'GCSFR%occ':>10}  mye/ery signal ratio")
for epo in EPO_VALS:
    for ph in PH_VALS:
        r = get(epo, ph)
        if r is None: continue
        ef  = fval(epo, ph, "EPOR_free") or 0
        eb  = fval(epo, ph, "EPOR_bound") or 0
        ei  = fval(epo, ph, "EPOR_internalized") or 0
        gf  = fval(epo, ph, "GCSFR_free") or 0
        gb  = fval(epo, ph, "GCSFR_bound") or 0
        gi  = fval(epo, ph, "GCSFR_internalized") or 0
        et  = ef + eb + ei
        gt  = gf + gb + gi
        epor_occ  = eb / et * 100 if et > 0 else 0
        gcsfr_occ = gb / gt * 100 if gt > 0 else 0
        ratio_sig = gcsfr_occ / epor_occ if epor_occ > 0 else float('nan')
        fate = r[2]
        mark = " ◄" if fate == "unc" else ""
        print(f"  {epo:>6.3f} {ph:>4.1f} {fate:>4s}  {epor_occ:>8.1f}%  {gcsfr_occ:>9.1f}%  {ratio_sig:>7.3f}{mark}")

print("\n  If GCSFR/EPOR ratio is systematically higher at low EPO → myeloid signal")
print("  dominance near the threshold (EPO has to outcompete myeloid signaling)")

print("\n" + "=" * 72)
print("DONE — PHASE C DEEP ANALYSIS")
print("=" * 72)
