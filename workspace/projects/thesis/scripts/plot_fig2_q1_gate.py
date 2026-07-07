#!/usr/bin/env python3
"""Figure 2 — Q1: nutrient depletion is the thermodynamic gate.

Panel (a): Sporulation fraction vs INITIAL_NUTRIENTS (FUJITA-2, abrupt route,
           LOADING_DOSE=27, 100 reps/condition).
Panel (b): ATP-pool trajectories, SM (N0=100) vs CH (N0=1440), natural route
           (LOADING_DOSE=0), mean +/- SD across replicates (FUJITA-1).

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/plot_fig2_q1_gate.py

Output: workspace/projects/thesis/manuscript/figures/fig2_q1_gate.png
"""
import csv, math, pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RUN_F2 = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260702_180944")
RUN_F1 = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260702_171823")
OUT    = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig2_q1_gate.png")

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

# ── Panel (a): sporulation fraction vs N0 (FUJITA-2) ─────────────────────────
conds_f2 = {}
for cdir in sorted(RUN_F2.glob("condition_*")):
    m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
    n0 = int(m.group(1)) if m else 100  # Baseline = 100 (LOADING_DOSE=27 default)
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    n = len(rows)
    spore = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    sf = sum(spore)/n
    # Wilson 95% CI
    z = 1.96
    denom = 1+z*z/n
    centre = (sf+z*z/(2*n))/denom
    half = z*math.sqrt(sf*(1-sf)/n + z*z/(4*n*n))/denom
    conds_f2[n0] = (sf, max(0,centre-half), min(1,centre+half))

n0_vals = sorted(conds_f2)
sf_vals = [conds_f2[n][0] for n in n0_vals]
ci_lo   = [conds_f2[n][1] for n in n0_vals]
ci_hi   = [conds_f2[n][2] for n in n0_vals]
yerr_lo = [max(0.0, sf_vals[i]-ci_lo[i]) for i in range(len(n0_vals))]
yerr_hi = [max(0.0, ci_hi[i]-sf_vals[i]) for i in range(len(n0_vals))]

# ── Panel (b): ATP trajectories SM vs CH (FUJITA-1, natural route) ───────────
def load_traj_stats(cdir):
    traj_files = sorted((cdir/"replicates_trajectories").glob("run_*.csv"))
    all_atp = []
    times_ref = None
    for tf in traj_files:
        traj = read_traj(tf)
        if not traj: continue
        times = [float(r["time"])/60 for r in traj]  # minutes
        atp   = [float(r.get("ATP_pool",0))/1000 for r in traj]  # mM
        if times_ref is None or len(times) > len(times_ref):
            times_ref = times
        all_atp.append(atp)
    # Truncate all to shortest length for alignment
    min_len = min(len(a) for a in all_atp)
    arr = np.array([a[:min_len] for a in all_atp])
    t = np.array(times_ref[:min_len])
    return t, arr.mean(axis=0), arr.std(axis=0)

sm_dir = RUN_F1 / "condition_[param]_INITIAL_NUTRIENTS_eq_100_[param]_LOADING_DOSE_eq_0"
ch_dir = RUN_F1 / "condition_[param]_INITIAL_NUTRIENTS_eq_1440_[param]_LOADING_DOSE_eq_0"

t_sm, atp_sm_mean, atp_sm_std = load_traj_stats(sm_dir)
t_ch, atp_ch_mean, atp_ch_std = load_traj_stats(ch_dir)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# Panel a
ax1.errorbar(n0_vals, [100*v for v in sf_vals],
             yerr=[[100*v for v in yerr_lo], [100*v for v in yerr_hi]],
             fmt='o-', color='#1f77b4', capsize=3, markersize=5, linewidth=1.5)
ax1.axhline(50, color='gray', linestyle=':', linewidth=1)
ax1.set_xlabel(r"Initial nutrients $N_0$ ($\mu$M)")
ax1.set_ylabel("Sporulation fraction (%)")
ax1.set_title("(a) Q1: sporulation vs nutrient level\n(FUJITA-2, abrupt route, n=100/cond.)")
ax1.set_ylim(-5, 105)
ax1.grid(alpha=0.3)

# Panel b
ax2.plot(t_sm, atp_sm_mean, color='#d62728', linewidth=1.8)
ax2.fill_between(t_sm, atp_sm_mean-atp_sm_std, atp_sm_mean+atp_sm_std, color='#d62728', alpha=0.2)
ax2.plot(t_ch, atp_ch_mean, color='#2ca02c', linewidth=1.8)
ax2.fill_between(t_ch, atp_ch_mean-atp_ch_std, atp_ch_mean+atp_ch_std, color='#2ca02c', alpha=0.2)
ax2.set_xlabel("Time (min)")
ax2.set_ylabel("ATP pool (mM)")
ax2.set_title("(b) ATP trajectory: SM vs CH medium\n(FUJITA-1, natural route, mean $\\pm$ SD, n=100)")
ax2.grid(alpha=0.3)

plt.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT, dpi=200, bbox_inches='tight')
print("Saved:", OUT)
print()
print("Panel (a) data: N0(uM) -> Sporulation% [95%CI]")
for n0 in n0_vals:
    sf,lo,hi = conds_f2[n0]
    print("  %5d -> %.1f%% [%.1f-%.1f%%]" % (n0, 100*sf, 100*lo, 100*hi))
print()
print("Panel (b): SM final ATP=%.3f mM, CH final ATP=%.3f mM" % (atp_sm_mean[-1], atp_ch_mean[-1]))
