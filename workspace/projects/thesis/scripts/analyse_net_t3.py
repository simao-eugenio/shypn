#!/usr/bin/env python3
"""NET-T3 analysis — Fluctuation theorem / nutrients step protocol.
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t3.py
"""
import csv, json, math, pathlib, re

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260706_151050"
)

CONDS = {
    "Baseline":       "condition_Baseline",
    "FWD_1440to2160": "condition_[param]_INITIAL_NUTRIENTS_eq_1440_[param]_NUTRIENTS_STEP_TARGET_eq_2160_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
    "REV_2160to1440": "condition_[param]_INITIAL_NUTRIENTS_eq_2160_[param]_NUTRIENTS_STEP_TARGET_eq_1440_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
    "Ctrl_1440x1440": "condition_[param]_INITIAL_NUTRIENTS_eq_1440_[param]_NUTRIENTS_STEP_TARGET_eq_1440_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
    "Ctrl_2160x2160": "condition_[param]_INITIAL_NUTRIENTS_eq_2160_[param]_NUTRIENTS_STEP_TARGET_eq_2160_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
}

kB  = 1.380649e-23
T   = 310.15
kBT = kB * T
dG_ATP  = 57000.0 / 6.022e23    # J/molecule
V_cell  = 1e-15                  # L (1 µm^3)
NA      = 6.022e23

def mean(v): return sum(v)/len(v) if v else float("nan")
def std(v):
    if len(v)<2: return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

def w_kbt(atp_consumed_uM):
    """ATP consumed (µM) → W/kBT."""
    N = atp_consumed_uM * 1e-6 * V_cell * NA
    return N * dG_ATP / kBT

print("NET-T3 ANALYSIS — Fluctuation Theorem / Nutrients Step Protocol")
print("Run:", RUN.name)
print("="*70)

rows_by_cond = {}
for label, cname in CONDS.items():
    cdir = RUN / cname

    # Key metrics
    spore  = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    n_s    = sum(spore)
    atp_f  = [float(r.get("ATP_pool_final",0))/1000 for r in rows]   # mM
    nuts_f = [float(r.get("Nutrients_final",0)) for r in rows]
    sigh_f = [float(r.get("SigmaH_final",0)) for r in rows]
    sinr_f = [float(r.get("SinR_final",0)) for r in rows]

    # ATP consumed: init(5000 µM) - final
    atp_consumed = [5.0 - a for a in atp_f]  # mM → consumed
    W_vals = [w_kbt(c*1000) for c in atp_consumed]  # c in mM → µM

    rows_by_cond[name] = {
        "sf": n_s/n, "n": n, "ns": n_s,
        "atp_mean": mean(atp_f), "atp_std": std(atp_f),
        "W_mean": mean(W_vals), "W_std": std(W_vals),
        "nuts_mean": mean(nuts_f),
        "sigh_mean": mean(sigh_f),
        "sinr_mean": mean(sinr_f),
    }

# Print table
print(f"\n{'Condition':<52}  {'Spore%':>6}  {'ATP(mM)':>9}  {'W/kBT':>12}  {'Nuts':>7}")
print("-"*90)
for name, r in sorted(rows_by_cond.items()):
    lbl = name.replace("condition_","").replace("[param]_","")
    lbl = lbl[:50]
    print(f"{lbl:<52}  {100*r['sf']:>5.0f}%  {r['atp_mean']:>9.3f}  {r['W_mean']:>12.2e}  {r['nuts_mean']:>7.0f}")

# Identify the 4 conditions of interest
print("\n--- IRREVERSIBILITY ANALYSIS ---")
fwd = rev = ctrl1 = ctrl2 = baseline = None
for name, r in rows_by_cond.items():
    po_line = name
    if "INITIAL_NUTRIENTS=1440" in po_line and "NUTRIENTS_STEP_TARGET=2160" in po_line:
        fwd = r; fwd_name = "FWD 1440→2160"
    elif "INITIAL_NUTRIENTS=2160" in po_line and "NUTRIENTS_STEP_TARGET=1440" in po_line:
        rev = r; rev_name = "REV 2160→1440"
    elif "INITIAL_NUTRIENTS=1440" in po_line and "NUTRIENTS_STEP_TARGET=1440" in po_line:
        ctrl1 = r
    elif "INITIAL_NUTRIENTS=2160" in po_line and "NUTRIENTS_STEP_TARGET=2160" in po_line:
        ctrl2 = r
    elif "Baseline" in po_line:
        baseline = r

print()
if fwd and rev:
    print(f"  FWD (1440→2160 at 1h): Spore={100*fwd['sf']:.0f}%  ATP={fwd['atp_mean']:.3f}mM  W/kBT={fwd['W_mean']:.2e}")
    print(f"  REV (2160→1440 at 1h): Spore={100*rev['sf']:.0f}%  ATP={rev['atp_mean']:.3f}mM  W/kBT={rev['W_mean']:.2e}")
    delta_W = fwd['W_mean'] - rev['W_mean']
    print(f"  ΔW/kBT (FWD − REV) = {delta_W:.2e}")
    print(f"  Irreversibility: e^|ΔW/kBT| = 10^{abs(delta_W)*math.log10(math.e):.1f}")
    print()
    print(f"  FT verdict: W/kBT >> 1 ({fwd['W_mean']:.1e}) → FT DOES NOT APPLY")
    print(f"  (FT requires |W/kBT| ~ 1 for quasi-static; observed: {fwd['W_mean']:.0e})")

print()
if ctrl1 and ctrl2:
    print(f"  Ctrl_1440→1440 (step to same): Spore={100*ctrl1['sf']:.0f}%  W/kBT={ctrl1['W_mean']:.2e}")
    print(f"  Ctrl_2160→2160 (step to same): Spore={100*ctrl2['sf']:.0f}%  W/kBT={ctrl2['W_mean']:.2e}")

if baseline:
    print(f"  Baseline (no step):           Spore={100*baseline['sf']:.0f}%  W/kBT={baseline['W_mean']:.2e}")
