#!/usr/bin/env python3
"""FUJITA-2 analysis — server-side.

Run from: ~/shypn/  with .venv activated.

Analyses run_20260702_180944:
  N0 titration with LOADING_DOSE=27 fixed
  100, 300, 600, 900, 1200, 1440, 1600, 1800, 2000, 2200 µM
  100 replicates, 6 h horizon.

Key question (Q1 extension):
  Does sporulation fraction decrease monotonically with N0 when
  the abrupt pulse is fixed?  Where is the crossover (ATP floor)?
"""

import pathlib, re
import numpy as np
import pandas as pd

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260702_180944"
)

# ── helpers (same as fujita1) ────────────────────────────────────────────────

def load_condition(cond_dir):
    rep = pd.read_csv(cond_dir / "replicates.csv", comment="#")
    traj_files = sorted((cond_dir / "replicates_trajectories").glob("run_*.csv"))
    trajs = [pd.read_csv(f, comment="#") for f in traj_files]
    return rep, trajs

def sporulation_fraction(rep):
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    return (ms > 0.5).mean() if ms is not None else float("nan")

def atp_floor(trajs, rep, fate):
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms is None: return float("nan"), float("nan")
    idx = [i for i, v in enumerate(ms > 0.5 if fate == "spor" else ms <= 0.5) if v]
    if not idx: return float("nan"), float("nan")
    mins = [trajs[i]["ATP_pool"].values.min() for i in idx]
    return np.mean(mins) / 1000.0, np.std(mins) / 1000.0  # → mM

def sigmah_peak(trajs, rep, fate):
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms is None: return float("nan"), float("nan")
    idx = [i for i, v in enumerate(ms > 0.5 if fate == "spor" else ms <= 0.5) if v]
    if not idx: return float("nan"), float("nan")
    peaks = [trajs[i]["SigmaH"].values.max() for i in idx]
    return np.mean(peaks), np.std(peaks)

def t_first_spore(trajs, rep):
    ms_col = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms_col is None: return float("nan"), float("nan")
    spor_idx = [i for i, v in enumerate(ms_col) if v > 0.5]
    if not spor_idx: return float("nan"), float("nan")
    times = []
    for i in spor_idx:
        t = trajs[i]["time"].values / 60.0
        ms = trajs[i]["Mature_spore"].values
        first = np.where(ms > 0)[0]
        times.append(t[first[0]] if len(first) else float("nan"))
    valid = [x for x in times if not np.isnan(x)]
    return (np.mean(valid), np.std(valid)) if valid else (float("nan"), float("nan"))

# ── main ────────────────────────────────────────────────────────────────────

rows = []
for cond_dir in sorted(RUN.glob("condition_*/")):
    name = cond_dir.name
    n0_m   = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", name)
    dose_m = re.search(r"LOADING_DOSE_eq_(\d+)", name)
    n0   = int(n0_m.group(1))   if n0_m   else 100
    dose = int(dose_m.group(1)) if dose_m else 0

    rep, trajs = load_condition(cond_dir)
    sf                      = sporulation_fraction(rep)
    atp_s_m, atp_s_s        = atp_floor(trajs, rep, "spor")
    atp_v_m, atp_v_s        = atp_floor(trajs, rep, "veg")
    sh_s_m, sh_s_s          = sigmah_peak(trajs, rep, "spor")
    sh_v_m, sh_v_s          = sigmah_peak(trajs, rep, "veg")
    tc_m, tc_s              = t_first_spore(trajs, rep)

    rows.append(dict(
        N0_uM          = n0,
        DOSE_uM        = dose,
        spor_pct       = round(sf * 100, 1),
        ATP_spor_mM    = round(atp_s_m, 3),
        ATP_veg_mM     = round(atp_v_m, 3),
        SigH_spor_uM   = round(sh_s_m, 3),
        SigH_veg_uM    = round(sh_v_m, 3),
        t_commit_min   = round(tc_m, 1),
        t_commit_std   = round(tc_s, 1),
        n_spor         = int(sf * len(rep) + 0.5),
        n_veg          = len(rep) - int(sf * len(rep) + 0.5),
    ))

df = pd.DataFrame(rows).sort_values("N0_uM").reset_index(drop=True)

# ── print ────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("FUJITA-2  —  run_20260702_180944  (LOADING_DOSE=27, N0 sweep)")
print("="*80)
print(df.to_string(index=False))

# Crossover analysis
print("\n--- Q1 PREDICTION TEST: monotonic decrease with N0? ---")
sf_vals = df["spor_pct"].values
n0_vals = df["N0_uM"].values
is_mono = all(sf_vals[i] >= sf_vals[i+1] - 5 for i in range(len(sf_vals)-1))
print(f"  Monotonic decrease: {'YES ✅' if is_mono else 'NOT strictly — check values'}")

# Find crossover ~50%
cross50 = None
for i in range(len(df)-1):
    if df.iloc[i]["spor_pct"] >= 50 and df.iloc[i+1]["spor_pct"] < 50:
        cross50 = (df.iloc[i]["N0_uM"], df.iloc[i+1]["N0_uM"])
        break
if cross50:
    print(f"  50% crossover between N0 = {cross50[0]} and {cross50[1]} µM  ← ATP basin floor region")
else:
    lo = df[df["spor_pct"] >= 50]["N0_uM"].max() if (df["spor_pct"] >= 50).any() else "?"
    hi = df[df["spor_pct"] <  50]["N0_uM"].min() if (df["spor_pct"] <  50).any() else "?"
    print(f"  50% crossover: last ≥50% at N0={lo} µM, first <50% at N0={hi} µM")

# Compare SM_abrupt from FUJITA-1 (expect ~100%)
row100 = df[df["N0_uM"] == 100]
row1440 = df[df["N0_uM"] == 1440]
row2200 = df[df["N0_uM"] == 2200]
if not row100.empty:
    print(f"\n  N0=100  (SM-like):  {row100.iloc[0]['spor_pct']:.1f}%   [FUJITA-1 confirmed: 100%]")
if not row1440.empty:
    print(f"  N0=1440 (CH-like):  {row1440.iloc[0]['spor_pct']:.1f}%   [FUJITA-1 confirmed: 56%]")
if not row2200.empty:
    print(f"  N0=2200 (rich):     {row2200.iloc[0]['spor_pct']:.1f}%   [Fujita Fig2C/D target: ~5%]")

# ATP veg floor
print("\n--- ATP VEGETATIVE BASIN FLOOR ---")
for _, r in df[df["ATP_veg_mM"].notna()].iterrows():
    print(f"  N0={r['N0_uM']:5.0f}  veg_ATP_min={r['ATP_veg_mM']:.3f} mM  (spor={r['spor_pct']}%)")

# SigmaH gate
print("\n--- σ_H PEAK vs θ_σH=1.60 µM ---")
for _, r in df.iterrows():
    gate = "✅ above" if r["SigH_spor_uM"] >= 1.60 else "❌ below"
    print(f"  N0={r['N0_uM']:5.0f}  σH_spor={r['SigH_spor_uM']:.3f}  σH_veg={r['SigH_veg_uM']:.3f}  gate: {gate}")

# ── save ────────────────────────────────────────────────────────────────────
out = RUN / "fujita2_analysis.csv"
df.to_csv(out, index=False)
print(f"\nSaved: {out}")
