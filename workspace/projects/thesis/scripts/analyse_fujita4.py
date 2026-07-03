#!/usr/bin/env python3
"""FUJITA-4 analysis — server-side.

Run from: ~/shypn/  with .venv activated.

Analyses run_20260703_141443:
  Natural route N0 titration — LOADING_DOSE=0, k_sigmaH_factor=1
  N0: 100 → 3000 µM, 200 replicates per condition, 6 h horizon.

Key question (Q3):
  What is the full sporulation fraction curve vs N0?
  Where is the 50% crossover N_c (bet-hedging window)?
  Does the ATP vegetative basin floor remain stable at ~2.22 mM?
"""

import pathlib, re, math
import numpy as np
import pandas as pd

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260703_141443"
)

# ── helpers ──────────────────────────────────────────────────────────────────

def load_condition(cond_dir):
    rep   = pd.read_csv(cond_dir / "replicates.csv", comment="#")
    traj_files = sorted((cond_dir / "replicates_trajectories").glob("run_*.csv"))
    trajs = [pd.read_csv(f, comment="#") for f in traj_files]
    return rep, trajs

def spor_frac(rep):
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    return float((ms > 0.5).mean()) if ms is not None else float("nan")

def atp_floor(trajs, rep, fate):
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms is None: return float("nan"), float("nan")
    idx = [i for i, v in enumerate(ms > 0.5 if fate=="spor" else ms <= 0.5) if v]
    if not idx: return float("nan"), float("nan")
    mins = [trajs[i]["ATP_pool"].values.min() for i in idx]
    return np.mean(mins)/1000.0, np.std(mins)/1000.0

def sh_peak(trajs):
    return np.mean([df["SigmaH"].values.max() for df in trajs])

def t_commit_mean(trajs, rep):
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms is None: return float("nan")
    idx = [i for i, v in enumerate(ms) if v > 0.5]
    if not idx: return float("nan")
    times = []
    for i in idx:
        t = trajs[i]["time"].values / 60.0
        ms_traj = trajs[i]["Mature_spore"].values
        first = np.where(ms_traj > 0)[0]
        times.append(t[first[0]] if len(first) else float("nan"))
    valid = [x for x in times if not math.isnan(x)]
    return np.mean(valid) if valid else float("nan")

# ── main ─────────────────────────────────────────────────────────────────────

rows = []
for cond_dir in sorted(RUN.glob("condition_*/")):
    name = cond_dir.name
    m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", name)
    n0 = int(m.group(1)) if m else 100  # Baseline uses model default 100

    rep, trajs = load_condition(cond_dir)
    sf           = spor_frac(rep)
    atp_s, _     = atp_floor(trajs, rep, "spor")
    atp_v, _     = atp_floor(trajs, rep, "veg")
    sh           = sh_peak(trajs)
    tc           = t_commit_mean(trajs, rep)

    rows.append(dict(
        N0_uM       = n0,
        spor_pct    = round(sf * 100, 1),
        n_spor      = int(sf * len(rep) + 0.5),
        n_veg       = len(rep) - int(sf * len(rep) + 0.5),
        ATP_spor_mM = round(atp_s, 3),
        ATP_veg_mM  = round(atp_v, 3),
        SigH_max_uM = round(sh, 3),
        t_commit_min= round(tc, 1) if not math.isnan(tc) else float("nan"),
    ))

df = pd.DataFrame(rows).sort_values("N0_uM").reset_index(drop=True)

# ── print ─────────────────────────────────────────────────────────────────────
print("\n" + "="*75)
print("FUJITA-4  —  run_20260703_141443  (natural route, N0 sweep)")
print("200 replicates per condition  |  LOADING_DOSE=0  |  6-h horizon")
print("="*75)
print(df.to_string(index=False))

# Q3 analysis
print("\n--- Q3: BET-HEDGING FRACTION MAP ---")
print("Sporulation curve (ASCII bar):")
for _, r in df.iterrows():
    bar = "█" * int(r["spor_pct"] / 5)
    gate = "✅" if r["SigH_max_uM"] >= 1.60 else "❌"
    print(f"  N0={r['N0_uM']:5.0f} µM  {r['spor_pct']:5.1f}%  {bar:<20}  "
          f"σH={r['SigH_max_uM']:.3f}µM {gate}")

# Find crossover
print("\n--- CROSSOVER ANALYSIS ---")
above = df[df["spor_pct"] >= 50]
below = df[df["spor_pct"] <  50]
if not above.empty and not below.empty:
    n_above = above["N0_uM"].max()
    n_below = below["N0_uM"].min()
    print(f"  Last N0 with ≥50%: {n_above} µM")
    print(f"  First N0 with <50%: {n_below} µM")
    nc_est = (n_above + n_below) / 2
    print(f"  Estimated N_c ≈ {nc_est:.0f} µM  (midpoint)")
    print(f"  *** Use N_c ≈ {nc_est:.0f} µM to centre NET-T4 fine sweep ***")

# Depletion boundary check
print("\n--- DEPLETION BOUNDARY (N0=2160 µM at 6h) ---")
boundary = df[df["N0_uM"] == 2160]
if not boundary.empty:
    r = boundary.iloc[0]
    print(f"  N0=2160: spor={r['spor_pct']}%  ATP_veg={r['ATP_veg_mM']} mM")
for n0 in [2300, 2500, 3000]:
    row = df[df["N0_uM"] == n0]
    if not row.empty:
        r = row.iloc[0]
        print(f"  N0={n0}: spor={r['spor_pct']}%  (nutrients not fully depleted in 6h)")

# ATP floor consistency
print("\n--- ATP VEGETATIVE BASIN FLOOR ---")
veg_df = df[df["ATP_veg_mM"].notna()]
if not veg_df.empty:
    floor_vals = veg_df["ATP_veg_mM"].values
    print(f"  Range: {floor_vals.min():.3f} – {floor_vals.max():.3f} mM  "
          f"(mean {floor_vals.mean():.3f} ± {floor_vals.std():.3f} mM)")
    print(f"  Prediction: 2.13 mM (topology-derived, no fitting)")

# ── save ──────────────────────────────────────────────────────────────────────
out = RUN / "fujita4_analysis.csv"
df.to_csv(out, index=False)
print(f"\nSaved: {out}")
