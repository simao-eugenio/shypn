#!/usr/bin/env python3
"""Part 2 trajectory extraction for tab:v4-factorial and tab:v4-atp-floor.

Targets: run_20260512_210205 (factorial sweep)
Extracts:
  - ATP trajectory minimum (mean ± std) per condition  → tab:v4-atp-floor
  - First-crossing time t1 where Outer_coat mean >= 1  → tab:v4-factorial
  - Endpoint OC mean ± std                             → tab:v4-factorial
"""
import json, os, sys, re
import statistics as stats_mod

RUN = "/home/simao/shypn/workspace/projects/thesis/experiments/results/run_20260512_210205"
if not os.path.isdir(RUN):
    sys.exit(f"Run dir not found: {RUN}")

snap = json.load(open(os.path.join(RUN, "model_snapshot.shy")))
NAME2ID = {p["name"]: p["id"] for p in snap.get("places", [])}

OC_THRESHOLD = 1.0   # first token in Outer_coat / Mature_spore
ATP_PLACE    = "ATP_pool"
ADP_PLACE    = "ADP_pool"
OC_PLACE     = "Outer_coat"
MS_PLACE     = "Mature_spore"   # t1 is first-crossing of Mature_spore

conds = sorted(d for d in os.listdir(RUN) if d.startswith("condition_"))

rows = []

for cond in conds:
    stat_path = os.path.join(RUN, cond, "statistics.json")
    if not os.path.exists(stat_path):
        print(f"  [skip] {cond} — no statistics.json")
        continue

    s  = json.load(open(stat_path))
    ss = s.get("species_statistics", {})
    tp = s.get("time_points") or s.get("times") or s.get("time") or None

    def mean_traj(place_name):
        pid = NAME2ID.get(place_name)
        if not pid:
            return None
        return ss.get(pid, {}).get("mean")

    def std_traj(place_name):
        pid = NAME2ID.get(place_name)
        if not pid:
            return None
        return ss.get(pid, {}).get("std")

    atp_m = mean_traj(ATP_PLACE)
    atp_s = std_traj(ATP_PLACE)
    oc_m  = mean_traj(OC_PLACE)
    oc_s  = std_traj(OC_PLACE)
    adp_m = mean_traj(ADP_PLACE)

    # ATP floor: minimum of the mean trajectory
    atp_floor_mean = round(min(atp_m), 2) if atp_m else None
    atp_floor_idx  = atp_m.index(min(atp_m)) if atp_m else None
    # std at the floor index
    atp_floor_std  = round(atp_s[atp_floor_idx], 2) if (atp_s and atp_floor_idx is not None) else None
    # t_min in minutes (time_points are in seconds)
    if tp and atp_floor_idx is not None:
        atp_tmin_min = round(tp[atp_floor_idx] / 60.0, 1)
    elif atp_floor_idx is not None:
        atp_tmin_min = round(atp_floor_idx * (21600.0 / (len(atp_m) - 1)) / 60.0, 1)
    else:
        atp_tmin_min = None

    ms_m  = mean_traj(MS_PLACE)   # for t1 computation

    # OC endpoint
    oc_end_mean = round(oc_m[-1], 2) if oc_m else None
    oc_end_std  = round(oc_s[-1], 2) if oc_s else None

    # t1: first index where Mature_spore mean >= OC_THRESHOLD
    t1_idx = None
    if ms_m:
        for i, v in enumerate(ms_m):
            if v >= OC_THRESHOLD:
                t1_idx = i
                break

    if tp and t1_idx is not None:
        t1_min = round(tp[t1_idx] / 60.0, 2)
    elif t1_idx is not None:
        t1_min = round(t1_idx * (21600.0 / (len(ms_m) - 1)) / 60.0, 2)
    else:
        t1_min = None  # never crosses within horizon => "---"

    # parse params from dirname  (format: INITIAL_NUTRIENTS_eq_X, TEMPERATURE_K_eq_X, SIGMA_HALFLIFE_MIN_eq_X)
    n0m  = re.search(r"INITIAL_NUTRIENTS_eq_([\d.]+)",   cond)
    tkm  = re.search(r"TEMPERATURE_K_eq_([\d.]+)",       cond)
    shlm = re.search(r"SIGMA_HALFLIFE_MIN_eq_([\d.]+)",  cond)

    def g(m):
        if not m:
            return None
        return float(m.group(1))

    rows.append({
        "cond":           cond,
        "N0":             g(n0m),
        "T":              g(tkm),
        "shl":            g(shlm),
        "oc_end_mean":    oc_end_mean,
        "oc_end_std":     oc_end_std,
        "t1_min":         t1_min,
        "atp_floor_mean": atp_floor_mean,
        "atp_floor_std":  atp_floor_std,
        "atp_tmin_min":   atp_tmin_min,
        "n":              s.get("n_replicates", 0),
    })

rows.sort(key=lambda r: (r["N0"] or 9999, r["T"] or 9999, r["shl"] or 9999))

# ── Print for tab:v4-factorial ────────────────────────────────────────────────
print("\n=== tab:v4-factorial (OC endpoint + t1) ===")
hdr = f"{'N0':>5} {'T':>7} {'shl':>5} | {'OC_mean':>9} {'OC_std':>7} | {'t1 (h)':>8} | n"
print(hdr)
print("-" * len(hdr))
for r in rows:
    n0  = f"{r['N0']:.0f}"    if r["N0"]  is not None else "Base"
    tk  = f"{r['T']:.2f}"    if r["T"]   is not None else "—"
    shl = f"{r['shl']:.0f}"  if r["shl"] is not None else "—"
    oc  = f"{r['oc_end_mean']:.1f}" if r["oc_end_mean"] is not None else "?"
    os_ = f"{r['oc_end_std']:.1f}"  if r["oc_end_std"]  is not None else "?"
    t1  = f"{r['t1_min']:.2f}" if r["t1_min"] is not None else "---"
    print(f"{n0:>5} {tk:>7} {shl:>5} | {oc:>9} {os_:>7} | {t1:>8} | {r['n']}")

# ── Print for tab:v4-atp-floor ────────────────────────────────────────────────
print("\n=== tab:v4-atp-floor (ATP trajectory minimum) ===")
hdr2 = f"{'N0':>5} {'T':>7} {'shl':>5} | {'ATP_min':>9} {'ATP_std':>8} | {'t_min(min)':>11} | n"
print(hdr2)
print("-" * len(hdr2))
for r in rows:
    n0  = f"{r['N0']:.0f}"    if r["N0"]  is not None else "Base"
    tk  = f"{r['T']:.2f}"    if r["T"]   is not None else "—"
    shl = f"{r['shl']:.0f}"  if r["shl"] is not None else "—"
    am  = f"{r['atp_floor_mean']:.1f}" if r["atp_floor_mean"] is not None else "?"
    as_ = f"{r['atp_floor_std']:.1f}"  if r["atp_floor_std"]  is not None else "?"
    tm  = f"{r['atp_tmin_min']:.1f}"   if r["atp_tmin_min"]   is not None else "?"
    print(f"{n0:>5} {tk:>7} {shl:>5} | {am:>9} {as_:>8} | {tm:>11} | {r['n']}")

print(f"\n{len(rows)}/{len(conds)} conditions processed.")

# ── Sanity: dump raw time_points keys available ───────────────────────────────
sample_stat = os.path.join(RUN, conds[0], "statistics.json") if conds else None
if sample_stat and os.path.exists(sample_stat):
    sample = json.load(open(sample_stat))
    print(f"\n[debug] statistics.json top-level keys: {list(sample.keys())}")
    if "time_points" in sample:
        tp = sample["time_points"]
        print(f"[debug] time_points: len={len(tp)}, first={tp[0]:.1f}s, last={tp[-1]:.1f}s ({tp[-1]/3600:.1f}h)")
