#!/usr/bin/env python3
"""Figure 4 — Q3: N_c = 1346 uM, exclusive Mode B commitment mechanism.

Panel (a): Full sporulation titration curve, N0=100-3000 uM (FUJITA-4,
           run_20260704_163628, 200 reps/condition), N_c marked.
Panel (b): Commitment timing (mean t_septation) near N_c, combining
           NET-T4 wide (run_20260706_190903) + dense sub-critical
           (run_20260707_134537), 300 reps/condition.
Panel (c): Mean SigmaH peak vs N0 near N_c, with threshold theta=1.60 uM.

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/plot_fig4_q3_Nc.py

Output: workspace/projects/thesis/manuscript/figures/fig4_q3_Nc.png
"""
import csv, math, pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUN_F4    = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260704_163628")
RUN_WIDE  = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260706_190903")
RUN_DENSE = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260707_134537")
OUT = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig4_q3_Nc.png")

Nc = 1346.4

def mean(v): return sum(v)/len(v) if v else float("nan")
def std(v):
    if len(v)<2: return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

def wilson_ci(sf, n):
    z = 1.96
    denom = 1+z*z/n
    centre = (sf+z*z/(2*n))/denom
    half = z*math.sqrt(sf*(1-sf)/n + z*z/(4*n*n))/denom
    return max(0,centre-half), min(1,centre+half)

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

# ── Panel (a): full sporulation curve (FUJITA-4) ─────────────────────────────
sf_data = {}
for cdir in sorted(RUN_F4.glob("condition_*")):
    m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
    n0 = int(m.group(1)) if m else 100
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    n = len(rows)
    spore = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    sf = sum(spore)/n
    lo, hi = wilson_ci(sf, n)
    sf_data[n0] = (sf, lo, hi)

n0_a = sorted(sf_data)
sf_a = [100*sf_data[n][0] for n in n0_a]
lo_a = [max(0,100*(sf_data[n][0]-sf_data[n][1])) for n in n0_a]
hi_a = [max(0,100*(sf_data[n][2]-sf_data[n][0])) for n in n0_a]

# ── Panel (b)+(c): commitment timing + SigmaH peak, sample 60 traj/condition ──
def cond_stats(cdir, sample=60):
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    traj_files = sorted((cdir/"replicates_trajectories").glob("run_*.csv"))[:sample]
    spore_mask = [float(r.get("Mature_spore_final",0))>0.5 for r in rows][:len(traj_files)]
    t_sept, sh_peak = [], []
    for i, tf in enumerate(traj_files):
        traj = read_traj(tf)
        if not traj: continue
        times = [float(r["time"])/60 for r in traj]
        sept  = [float(r.get("Septum",0)) for r in traj]
        sigh  = [float(r.get("SigmaH",0)) for r in traj]
        sh_peak.append(max(sigh))
        if i < len(spore_mask) and spore_mask[i]:
            first = [t for t,s in zip(times,sept) if s>0.5]
            if first: t_sept.append(first[0])
    return mean(t_sept), std(t_sept), mean(sh_peak), std(sh_peak)

near_nc_conds = {}
for run in [RUN_WIDE, RUN_DENSE]:
    for cdir in sorted(run.glob("condition_*")):
        m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
        if not m: continue
        n0 = int(m.group(1))
        if abs(n0 - Nc) <= 350 and n0 not in near_nc_conds:
            near_nc_conds[n0] = cdir

n0_bc = sorted(near_nc_conds)
t_sept_m, t_sept_s, sh_peak_m, sh_peak_s = [], [], [], []
for n0 in n0_bc:
    tm, ts, shm, shs = cond_stats(near_nc_conds[n0])
    t_sept_m.append(tm); t_sept_s.append(ts)
    sh_peak_m.append(shm); sh_peak_s.append(shs)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 4.2))
ax1 = fig.add_subplot(1, 3, 1)
ax2 = fig.add_subplot(1, 3, 2)
ax3 = fig.add_subplot(1, 3, 3)

# Panel a
ax1.errorbar(n0_a, sf_a, yerr=[lo_a,hi_a], fmt='o-', color='#1f77b4',
             capsize=3, markersize=4, linewidth=1.5)
ax1.axvline(Nc, color='red', linestyle='--', linewidth=1.2)
ax1.axhline(50, color='gray', linestyle=':', linewidth=1)
ax1.set_xlabel(r"Initial nutrients $N_0$ ($\mu$M)")
ax1.set_ylabel("Sporulation fraction (%)")
ax1.set_title("(a) Full titration\n(FUJITA-4, n=200/cond.)")
ax1.set_ylim(-5, 105)
ax1.grid(alpha=0.3)

# Panel b
valid_b = [(n0,t,s) for n0,t,s in zip(n0_bc,t_sept_m,t_sept_s) if not math.isnan(t)]
if valid_b:
    nb, tb, sb = zip(*valid_b)
    ax2.errorbar(nb, tb, yerr=sb, fmt='s-', color='#2ca02c', capsize=3, markersize=5, linewidth=1.5)
ax2.axvline(Nc, color='red', linestyle='--', linewidth=1.2)
ax2.set_xlabel(r"Initial nutrients $N_0$ ($\mu$M)")
ax2.set_ylabel("Mean commitment time (min)")
ax2.set_title("(b) Critical slowing down\n(near $N_c$, n=300/cond., 60 traj sampled)")
ax2.grid(alpha=0.3)

# Panel c
ax3.errorbar(n0_bc, sh_peak_m, yerr=sh_peak_s, fmt='^-', color='#9467bd',
             capsize=3, markersize=5, linewidth=1.5)
ax3.axhline(1.60, color='black', linestyle=':', linewidth=1)
ax3.axvline(Nc, color='red', linestyle='--', linewidth=1.2)
ax3.set_xlabel(r"Initial nutrients $N_0$ ($\mu$M)")
ax3.set_ylabel(r"Mean $\sigma_H$ peak ($\mu$M)")
ax3.set_title("(c) Threshold-crossing mechanism\n(near $N_c$, n=300/cond., 60 traj sampled)")
ax3.grid(alpha=0.3)

plt.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT, dpi=200, bbox_inches='tight')
print("Saved:", OUT)
print()
print("Panel (a) N_c region:")
for n0 in n0_a:
    if 1200 <= n0 <= 1650:
        print("  N0=%d -> %.1f%%" % (n0, 100*sf_data[n0][0]))
print()
print("Panel (b)/(c) near-Nc data:")
for i,n0 in enumerate(n0_bc):
    print("  N0=%5d  t_commit=%.1f+-%.1f min  sigH_peak=%.3f+-%.3f uM" % (
        n0, t_sept_m[i], t_sept_s[i], sh_peak_m[i], sh_peak_s[i]))
