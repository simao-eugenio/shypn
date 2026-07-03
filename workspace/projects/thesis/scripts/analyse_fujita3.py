#!/usr/bin/env python3
"""FUJITA-3 analysis — server-side.

Run from: ~/shypn/  with .venv activated.

Analyses run_20260702_191849:
  2×2 factorial: k_sigmaH_factor {0.0,0.2,0.4,0.6,0.8,1.0} × LOADING_DOSE {0,27}
  Fixed: INITIAL_NUTRIENTS = 100 (SM-like, fast starvation)
  50 replicates per condition, 6 h horizon.

Key question (Q2):
  Does k_sigmaH_factor=0 produce 0% sporulation (true σ_H-null)?
  How does the feedback gain gradient (0→1) affect commitment?
"""

import pathlib, re
import numpy as np
import pandas as pd

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260702_191849"
)

# ── helpers ──────────────────────────────────────────────────────────────────

def load_condition(cond_dir):
    rep = pd.read_csv(cond_dir / "replicates.csv", comment="#")
    traj_files = sorted((cond_dir / "replicates_trajectories").glob("run_*.csv"))
    trajs = [pd.read_csv(f, comment="#") for f in traj_files]
    return rep, trajs

def sporulation_fraction(rep):
    ms = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    return float((ms > 0.5).mean()) if ms is not None else float("nan")

def sigmah_peak_mean(trajs):
    return np.mean([df["SigmaH"].values.max() for df in trajs])

def t_commit_mean(trajs, rep):
    ms_col = rep.get("Mature_spore_final", rep.get("Forespore_final"))
    if ms_col is None: return float("nan")
    spor_idx = [i for i, v in enumerate(ms_col) if v > 0.5]
    if not spor_idx: return float("nan")
    times = []
    for i in spor_idx:
        t = trajs[i]["time"].values / 60.0
        ms = trajs[i]["Mature_spore"].values
        first = np.where(ms > 0)[0]
        times.append(t[first[0]] if len(first) else float("nan"))
    valid = [x for x in times if not np.isnan(x)]
    return np.mean(valid) if valid else float("nan")

# ── load config to get parameter values ──────────────────────────────────────

cfg = __import__("json").loads((RUN / "config.json").read_text())["sweep_config"]
snaps_by_name = {s["name"]: s for s in cfg.get("snapshots", [])}

def get_param(cond_name, key):
    """Extract parameter value from condition name via regex."""
    m = re.search(key + r"_eq_([0-9.]+)", cond_name)
    return float(m.group(1)) if m else None

# ── main ─────────────────────────────────────────────────────────────────────

rows = []
for cond_dir in sorted(RUN.glob("condition_*/")):
    name = cond_dir.name
    ksf  = get_param(name, "k_sigmaH_factor")
    dose = get_param(name, "LOADING_DOSE")
    if ksf is None: ksf = 1.0   # Baseline uses model default
    if dose is None: dose = 0.0

    rep, trajs = load_condition(cond_dir)
    sf   = sporulation_fraction(rep)
    sh   = sigmah_peak_mean(trajs)
    tc   = t_commit_mean(trajs, rep)

    rows.append(dict(
        k_sigmaH   = ksf,
        DOSE_uM    = dose,
        spor_pct   = round(sf * 100, 1),
        SigH_max   = round(sh, 3),
        t_commit   = round(tc, 1) if not np.isnan(tc) else float("nan"),
        n_spor     = int(sf * len(rep) + 0.5),
        n_total    = len(rep),
    ))

df = pd.DataFrame(rows).sort_values(["DOSE_uM", "k_sigmaH"]).reset_index(drop=True)

# ── print ─────────────────────────────────────────────────────────────────────
print("\n" + "="*75)
print("FUJITA-3  —  run_20260702_191849")
print("k_sigmaH_factor × LOADING_DOSE  |  N0=100 µM (SM)  |  50 reps")
print("="*75)
print(df.to_string(index=False))

# --- Q2 verdict ---
print("\n--- Q2: σ_H-NULL TEST (k_sigmaH_factor=0) ---")
null_nat = df[(df.k_sigmaH==0.0) & (df.DOSE_uM==0.0)]
null_abr = df[(df.k_sigmaH==0.0) & (df.DOSE_uM==27.0)]
full_nat = df[(df.k_sigmaH==1.0) & (df.DOSE_uM==0.0)]
full_abr = df[(df.k_sigmaH==1.0) & (df.DOSE_uM==27.0)]

def row_summary(label, sub):
    if sub.empty: return
    r = sub.iloc[0]
    gate = "✅ above θ" if r["SigH_max"] >= 1.60 else "❌ below θ"
    print(f"  {label:40s}: {r['spor_pct']:5.1f}%  σH_max={r['SigH_max']:.3f} µM  {gate}")

row_summary("k_sigmaH=0.0, DOSE=0  (σ_H-null natural)", null_nat)
row_summary("k_sigmaH=0.0, DOSE=27 (σ_H-null + pulse)",  null_abr)
row_summary("k_sigmaH=1.0, DOSE=0  (normal natural)",     full_nat)
row_summary("k_sigmaH=1.0, DOSE=27 (normal + pulse)",     full_abr)

# Q2 verdict
if not null_nat.empty:
    pct = null_nat.iloc[0]["spor_pct"]
    if pct == 0.0:
        print("\n  ✅ Q2 CONFIRMED: k_sigmaH_factor=0 → 0% sporulation (true σ_H-null)")
    elif pct < 10:
        print(f"\n  ⚠️  Near-null: {pct:.1f}% sporulate at k_sigmaH=0 (stochastic leakage)")
    else:
        print(f"\n  ❌ Q2 NOT confirmed: {pct:.1f}% still sporulate at k_sigmaH=0")

# --- Feedback gain gradient ---
print("\n--- FEEDBACK GAIN GRADIENT (DOSE=0, natural route) ---")
nat = df[df.DOSE_uM == 0.0].sort_values("k_sigmaH")
for _, r in nat.iterrows():
    bar = "█" * int(r["spor_pct"] / 5)
    print(f"  k_sigmaH={r['k_sigmaH']:.1f}  {r['spor_pct']:5.1f}%  {bar}")

print("\n--- FEEDBACK GAIN GRADIENT (DOSE=27, abrupt pulse) ---")
abr = df[df.DOSE_uM == 27.0].sort_values("k_sigmaH")
for _, r in abr.iterrows():
    bar = "█" * int(r["spor_pct"] / 5)
    print(f"  k_sigmaH={r['k_sigmaH']:.1f}  {r['spor_pct']:5.1f}%  {bar}")

# ── save ──────────────────────────────────────────────────────────────────────
out = RUN / "fujita3_analysis.csv"
df.to_csv(out, index=False)
print(f"\nSaved: {out}")
