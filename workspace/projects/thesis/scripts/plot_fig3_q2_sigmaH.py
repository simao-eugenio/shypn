#!/usr/bin/env python3
"""Figure 3 — Q2: sigma_H is the irreversible Landauer step.

Panel (a): Sporulation fraction vs k_sigmaH_factor, both routes
           (natural D=0, abrupt D=27), FUJITA-3, 50 reps/condition.
Panel (b): SigmaH trajectory overlay: null (k=0) vs WT (k=1), natural route,
           mean +/- SD across replicates.

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/plot_fig3_q2_sigmaH.py

Output: workspace/projects/thesis/manuscript/figures/fig3_q2_sigmaH.png
"""
import csv, math, pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RUN = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260702_191849")
OUT = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig3_q2_sigmaH.png")

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

def wilson_ci(sf, n):
    z = 1.96
    denom = 1+z*z/n
    centre = (sf+z*z/(2*n))/denom
    half = z*math.sqrt(sf*(1-sf)/n + z*z/(4*n*n))/denom
    return max(0,centre-half), min(1,centre+half)

# ── Panel (a): sporulation vs k_sigmaH_factor, both routes ───────────────────
data = {0: {}, 27: {}}  # dose -> {k_sigmaH: sf}
for cdir in sorted(RUN.glob("condition_*")):
    m = re.search(r"LOADING_DOSE_eq_(\d+)_\[param\]_k_sigmaH_factor_eq_([\d.]+)", cdir.name)
    if not m:
        continue
    dose = int(m.group(1))
    k = float(m.group(2))
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    n = len(rows)
    spore = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    sf = sum(spore)/n
    lo, hi = wilson_ci(sf, n)
    data[dose][k] = (sf, lo, hi, n)

# ── Panel (b): SigmaH trajectory, null vs WT (natural route) ─────────────────
def load_traj_stats(cdir, col="SigmaH"):
    traj_files = sorted((cdir/"replicates_trajectories").glob("run_*.csv"))
    all_v = []
    times_ref = None
    for tf in traj_files:
        traj = read_traj(tf)
        if not traj: continue
        times = [float(r["time"])/60 for r in traj]
        v = [float(r.get(col,0)) for r in traj]
        if times_ref is None or len(times) > len(times_ref):
            times_ref = times
        all_v.append(v)
    min_len = min(len(a) for a in all_v)
    arr = np.array([a[:min_len] for a in all_v])
    t = np.array(times_ref[:min_len])
    return t, arr.mean(axis=0), arr.std(axis=0)

null_dir = RUN / "condition_[param]_LOADING_DOSE_eq_0_[param]_k_sigmaH_factor_eq_0"
wt_dir   = RUN / "condition_[param]_LOADING_DOSE_eq_0_[param]_k_sigmaH_factor_eq_1"

t_null, sh_null_mean, sh_null_std = load_traj_stats(null_dir)
t_wt,   sh_wt_mean,   sh_wt_std   = load_traj_stats(wt_dir)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# Panel a
colors = {0: '#1f77b4', 27: '#ff7f0e'}
markers = {0: 'o', 27: 's'}
for dose in [0, 27]:
    ks = sorted(data[dose])
    sfs = [100*data[dose][k][0] for k in ks]
    lo  = [100*(data[dose][k][0]-data[dose][k][1]) for k in ks]
    hi  = [100*(data[dose][k][2]-data[dose][k][0]) for k in ks]
    lo  = [max(0,v) for v in lo]; hi = [max(0,v) for v in hi]
    label = "natural (D=0)" if dose==0 else "abrupt (D=27)"
    ax1.errorbar(ks, sfs, yerr=[lo,hi], fmt=markers[dose]+'-', color=colors[dose],
                 capsize=3, markersize=5, linewidth=1.5, label=label)
ax1.set_xlabel(r"$k_{\sigma H}$ (transcription capacity)")
ax1.set_ylabel("Sporulation fraction (%)")
ax1.set_title("(a) Q2: sporulation vs $\\sigma_H$ transcription\n(FUJITA-3, $N_0$=100, n=50/cond.)")
ax1.set_ylim(-5, 105)
ax1.legend(loc='center right', fontsize=9)
ax1.grid(alpha=0.3)

# Panel b
ax2.plot(t_null, sh_null_mean, color='#7f7f7f', linewidth=1.8)
ax2.fill_between(t_null, sh_null_mean-sh_null_std, sh_null_mean+sh_null_std, color='#7f7f7f', alpha=0.2)
ax2.plot(t_wt, sh_wt_mean, color='#9467bd', linewidth=1.8)
ax2.fill_between(t_wt, sh_wt_mean-sh_wt_std, sh_wt_mean+sh_wt_std, color='#9467bd', alpha=0.2)
ax2.axhline(1.60, color='black', linestyle=':', linewidth=1)
ax2.set_xlabel("Time (min)")
ax2.set_ylabel(r"$\sigma_H$ concentration ($\mu$M)")
ax2.set_title("(b) $\\sigma_H$ trajectory: null vs wild-type\n(natural route, mean $\\pm$ SD, n=50)")
ax2.grid(alpha=0.3)

plt.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT, dpi=200, bbox_inches='tight')
print("Saved:", OUT)
print()
print("Panel (a) data:")
for dose in [0, 27]:
    print("  D=%d:" % dose)
    for k in sorted(data[dose]):
        sf,lo,hi,n = data[dose][k]
        print("    k=%.1f -> %.1f%% [%.1f-%.1f%%]  n=%d" % (k, 100*sf, 100*lo, 100*hi, n))
print()
print("Panel (b): null sigH_final=%.4f uM, WT sigH_final=%.4f uM (theta=1.60)" % (
    sh_null_mean[-1], sh_wt_mean[-1]))
