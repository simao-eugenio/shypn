#!/usr/bin/env python3
"""Quick gate analysis for the starvation sweep (run_20260513_123339)."""
import json, os, sys, re

RUN = "/home/simao/shypn/workspace/projects/thesis/experiments/results/run_20260513_123339"
if not os.path.isdir(RUN):
    sys.exit(f"Run dir not found: {RUN}")

# Build place name -> ID map from model snapshot
snap = json.load(open(os.path.join(RUN, "model_snapshot.shy")))
NAME2ID = {p["name"]: p["id"] for p in snap.get("places", [])}

conds = sorted(d for d in os.listdir(RUN) if d.startswith("condition_"))
rows = []

for cond in conds:
    stat_path = os.path.join(RUN, cond, "statistics.json")
    if not os.path.exists(stat_path):
        continue
    s = json.load(open(stat_path))
    ss = s.get("species_statistics", {})
    n  = s.get("n_replicates", 0)

    def last(place_name):
        pid = NAME2ID.get(place_name)
        if not pid:
            return None
        m = ss.get(pid, {}).get("mean")
        return round(m[-1], 2) if m else None

    def last_std(place_name):
        pid = NAME2ID.get(place_name)
        if not pid:
            return None
        m = ss.get(pid, {}).get("std")
        return round(m[-1], 2) if m else None

    # parse params from dirname
    n0  = re.search(r"INITIAL_NUTRIENTS_eq_([\d.]+)", cond)
    tk  = re.search(r"TEMPERATURE_K_eq_([\d.]+)",     cond)
    shl = re.search(r"SIGMA_HALFLIFE_MIN_eq_([\d.]+)",cond)

    rows.append({
        "cond":  cond,
        "N0":    float(n0.group(1))  if n0  else None,
        "T":     float(tk.group(1))  if tk  else None,
        "shl":   float(shl.group(1)) if shl else None,
        "OC":    last("Outer_coat"),
        "ATP":   last("ATP_pool"),
        "ADP":   last("ADP_pool"),
        "MS":    last("Mature_spore"),
        "Nutr":  last("Nutrients"),
        "n":     n,
    })

# sort by N0, T, shl
rows.sort(key=lambda r: (r["N0"] or 999, r["T"] or 999, r["shl"] or 999))

hdr = f"{'N0':>5} {'T':>7} {'shl':>5} | {'OC':>8} {'MS':>8} {'ATP':>8} {'ADP':>8} {'Nutr':>6} | n"
print(hdr)
print("-" * len(hdr))
for r in rows:
    n0  = f"{r['N0']:.0f}"   if r["N0"]  is not None else "Base"
    tk  = f"{r['T']:.2f}"   if r["T"]   is not None else "—"
    shl = f"{r['shl']:.0f}" if r["shl"] is not None else "—"
    oc  = f"{r['OC']:.1f}"  if r["OC"]  is not None else "?"
    ms  = f"{r['MS']:.2f}"  if r["MS"]  is not None else "?"
    atp = f"{r['ATP']:.1f}" if r["ATP"] is not None else "?"
    adp = f"{r['ADP']:.1f}" if r["ADP"] is not None else "?"
    nu  = f"{r['Nutr']:.2f}"if r["Nutr"]is not None else "?"
    print(f"{n0:>5} {tk:>7} {shl:>5} | {oc:>8} {ms:>8} {atp:>8} {adp:>8} {nu:>6} | {r['n']}")

print(f"\n{len(rows)}/{len(conds)} conditions complete.")

# --- F-gate checks ---
print("\n=== F-gate checks (completed conditions) ===")

for r in rows:
    flags = []
    # F1: ATP+ADP conservation (expect ~10000)
    if r["ATP"] is not None and r["ADP"] is not None:
        total = r["ATP"] + r["ADP"]
        if abs(total - 10000) > 500:
            flags.append(f"F1 FAIL ATP+ADP={total:.0f}")
        else:
            flags.append(f"F1 ok ({total:.0f})")
    # F3: ATP above floor (k_ATP_target=4800, but we watch for collapse <100)
    if r["ATP"] is not None:
        if r["ATP"] < 100:
            flags.append(f"F3 FAIL ATP={r['ATP']:.1f} (collapsed)")
        elif r["ATP"] < 1000:
            flags.append(f"F3 WARN ATP={r['ATP']:.1f}")
        else:
            flags.append(f"F3 ok ATP={r['ATP']:.1f}")
    # F6: any sporulation signal (OC > 0)
    if r["OC"] is not None:
        if r["OC"] > 0:
            flags.append(f"F6 ok OC={r['OC']:.1f}")
        else:
            flags.append(f"F6 FAIL OC=0")
    # T23 activation check: N<5 should deplete nutrients
    if r["N0"] is not None and r["N0"] < 5 and r["Nutr"] is not None:
        if r["Nutr"] < 1.0:
            flags.append(f"T23-regime ACTIVE (Nutr={r['Nutr']:.3f})")
        else:
            flags.append(f"T23-regime not yet (Nutr={r['Nutr']:.2f})")

    n0  = f"{r['N0']:.0f}"   if r["N0"]  is not None else "Base"
    shl = f"{r['shl']:.0f}" if r["shl"] is not None else "—"
    tk  = f"{r['T']:.2f}"   if r["T"]   is not None else "—"
    print(f"  N0={n0} T={tk} shl={shl}: {' | '.join(flags)}")
