#!/usr/bin/env python3
"""FUJITA-1 analysis — server-side (G5 tier, trajectories available).

Run from: ~/shypn/  with .venv activated.

Analyses run_20260702_171823:
  2x2 factorial  INITIAL_NUTRIENTS {100, 1440} x LOADING_DOSE {0, 27}
  + Baseline (N0=100, DOSE=0)
  100 replicates per condition, 6 h horizon.

Outputs:
  - Sporulation fraction per condition
  - ATP trajectory minimum per fate group
  - t_commit distribution (time Mature_spore first > 0)
  - Print table + save CSV to results dir
"""

import pathlib
import numpy as np
import pandas as pd

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260702_171823"
)

# ── helpers ─────────────────────────────────────────────────────────────────

def load_condition(cond_dir: pathlib.Path):
    rep_csv = cond_dir / "replicates.csv"
    traj_dir = cond_dir / "replicates_trajectories"
    rep = pd.read_csv(rep_csv, comment="#")
    traj_files = sorted(traj_dir.glob("run_*.csv"))
    trajs = [pd.read_csv(f, comment="#") for f in traj_files]
    return rep, trajs


def sporulation_fraction(rep: pd.DataFrame) -> float:
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    return (ms > 0.5).mean() if ms is not None else float("nan")


def atp_floor(trajs, rep, fate: str) -> tuple:
    """Mean ATP trajectory minimum for sporulating or vegetative fate."""
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms is None:
        return float("nan"), float("nan")
    mask = (ms > 0.5) if fate == "spor" else (ms <= 0.5)
    idx = [i for i, v in enumerate(mask) if v]
    if not idx:
        return float("nan"), float("nan")
    mins = [trajs[i]["ATP_pool"].values.min() for i in idx]
    return np.mean(mins) / 1000.0, np.std(mins) / 1000.0  # → mM


def t_commit(trajs, rep) -> tuple:
    """Mean time (min) to first Mature_spore token > 0."""
    ms_col = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms_col is None:
        return float("nan"), float("nan")
    spor_idx = [i for i, v in enumerate(ms_col) if v > 0.5]
    if not spor_idx:
        return float("nan"), float("nan")
    times = []
    for i in spor_idx:
        t = trajs[i]["time"].values / 60.0  # s → min
        ms = trajs[i]["Mature_spore"].values
        first = np.where(ms > 0)[0]
        times.append(t[first[0]] if len(first) else float("nan"))
    valid = [x for x in times if not np.isnan(x)]
    return (np.mean(valid), np.std(valid)) if valid else (float("nan"), float("nan"))


def sigmah_max(trajs, rep) -> tuple:
    """Mean peak SigmaH (µM) across all replicates."""
    vals = [df["SigmaH"].values.max() for df in trajs]
    return np.mean(vals), np.std(vals)


# ── main ────────────────────────────────────────────────────────────────────

conditions = sorted(RUN.glob("condition_*/"))

rows = []
for cond_dir in conditions:
    name = cond_dir.name

    # Parse N0 and DOSE from directory name
    import re
    n0_m   = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", name)
    dose_m = re.search(r"LOADING_DOSE_eq_(\d+)", name)
    n0   = int(n0_m.group(1))   if n0_m   else 100
    dose = int(dose_m.group(1)) if dose_m else 0

    rep, trajs = load_condition(cond_dir)
    sf  = sporulation_fraction(rep)
    atp_s_mean, atp_s_std = atp_floor(trajs, rep, "spor")
    atp_v_mean, atp_v_std = atp_floor(trajs, rep, "veg")
    tc_mean, tc_std        = t_commit(trajs, rep)
    sh_mean, sh_std        = sigmah_max(trajs, rep)

    rows.append({
        "condition":          name.replace("condition_", "")[:60],
        "N0 (µM)":            n0,
        "DOSE (µM)":          dose,
        "spor_frac (%)":      round(sf * 100, 1),
        "ATP_spor_floor (mM)": round(atp_s_mean, 3),
        "ATP_veg_floor (mM)":  round(atp_v_mean, 3),
        "t_commit_mean (min)": round(tc_mean, 1),
        "t_commit_std (min)":  round(tc_std, 1),
        "SigmaH_max_mean (µM)": round(sh_mean, 3),
        "SigmaH_max_std (µM)":  round(sh_std, 3),
    })

df = pd.DataFrame(rows).sort_values(["N0 (µM)", "DOSE (µM)"])

# ── print results ────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("FUJITA-1  —  run_20260702_171823")
print("=" * 80)
print(df.to_string(index=False))

print("\n--- KEY PREDICTIONS ---")
sm_nat  = df[(df["N0 (µM)"] == 100)  & (df["DOSE (µM)"] == 0)]["spor_frac (%)"].values
sm_abr  = df[(df["N0 (µM)"] == 100)  & (df["DOSE (µM)"] == 27)]["spor_frac (%)"].values
ch_nat  = df[(df["N0 (µM)"] == 1440) & (df["DOSE (µM)"] == 0)]["spor_frac (%)"].values
ch_abr  = df[(df["N0 (µM)"] == 1440) & (df["DOSE (µM)"] == 27)]["spor_frac (%)"].values

if len(sm_nat): print(f"  SM natural  (N0=100,  DOSE=0 ) : {sm_nat[0]:.1f}%  [expect ~100%]")
if len(sm_abr): print(f"  SM abrupt   (N0=100,  DOSE=27) : {sm_abr[0]:.1f}%  [predict >>5%]  ← KEY")
if len(ch_nat): print(f"  CH natural  (N0=1440, DOSE=0 ) : {ch_nat[0]:.1f}%  [expect ~48%]")
if len(ch_abr): print(f"  CH abrupt   (N0=1440, DOSE=27) : {ch_abr[0]:.1f}%  [expect ~5%]   ← Fujita Fig2C/D")

# Fujita Q1 verdict
if len(sm_abr) and len(ch_abr):
    ratio = sm_abr[0] / max(ch_abr[0], 0.01)
    print(f"\n  SM_abrupt / CH_abrupt = {ratio:.1f}×")
    if sm_abr[0] > 20 and sm_abr[0] > 3 * ch_abr[0]:
        print("  ✅ PREDICTION CONFIRMED: medium (ATP) is the mechanistic gate, not just timing")
    elif sm_abr[0] < 10:
        print("  ❌ prediction not confirmed: abrupt pulse fails even in SM medium")
    else:
        print("  ⚠️  partial: some enhancement but not decisive")

# ── save ────────────────────────────────────────────────────────────────────
out = RUN / "fujita1_analysis.csv"
df.to_csv(out, index=False)
print(f"\nSaved: {out}")
