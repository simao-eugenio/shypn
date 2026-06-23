#!/usr/bin/env python3
"""
Figure 2v3 — Preemption Cascade: single spaghetti panel

Three stacked horizontal strips (Spo0A~P → σH → σF), 50 individual
replicate trajectories coloured by fate. No legend, no arrows.

Data: run_20260614_123652 · N0=1440 µM, dose=0, SinR=12 · 50 replicates
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────────────────────────────────────
PROJECT  = Path(__file__).resolve().parents[1]
RUN_DIR  = PROJECT / "experiments/results/run_20260614_123652"
FIG_DIR  = PROJECT / "doc/review/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

T_MAX      = 360.0
SEPARATRIX = 1.60    # µM, σH commitment threshold
T_COMMIT   = 300.0   # min
SPOR_THR   = 0.50
SMOOTH     = 40

# Strip order: bottom = upstream (stochastic), top = downstream (execution)
STRIPS = [
    ("Spo0A$\\sim$P", "Spo0A_P",  "#cc3311"),
    ("$\\sigma_H$",   "SigmaH",   "#aa3377"),
    ("$\\sigma_F$",   "SigmaF",   "#009988"),
]

# ──────────────────────────────────────────────────────────────────────────────
def find_cond(N0, sinr, dose):
    for d in RUN_DIR.iterdir():
        if not d.is_dir():
            continue
        m = {k: re.search(p, d.name) for k, p in [
            ("N0",   r"INITIAL_NUTRIENTS_eq_([\d.]+)"),
            ("sinr", r"SinR_eq_([\d.]+)"),
            ("dose", r"LOADING_DOSE_eq_([\d.]+)")]}
        if (m["N0"] and abs(float(m["N0"].group(1)) - N0) < 1 and
                m["sinr"] and abs(float(m["sinr"].group(1)) - sinr) < 1 and
                m["dose"] and abs(float(m["dose"].group(1)) - dose) < 1):
            return d
    return None

cond = find_cond(1440, 12, 0)
assert cond, "Condition not found"

# ──────────────────────────────────────────────────────────────────────────────
print("Loading trajectories...")
trajs = []
for f in sorted((cond / "replicates_trajectories").glob("run_*.csv")):
    rows, hdr = [], None
    with open(f) as fh:
        for line in fh:
            if line.startswith("#"): continue
            if hdr is None: hdr = line.strip().split(","); continue
            rows.append(line.strip().split(","))
    if hdr and rows:
        df = pd.DataFrame(rows, columns=hdr).astype(float)
        df["time_min"] = df["time"] / 60.0
        trajs.append(df)

n_rep = len(trajs)
n_tp  = min(len(t) for t in trajs)
time_min = trajs[0]["time_min"].values[:n_tp]
t_mask   = time_min <= T_MAX

fate_spor = np.array([
    t["Mature_spore"].values[:n_tp].max() > SPOR_THR for t in trajs
])
print(f"  {n_rep} replicates, {fate_spor.sum()} sporulating")

# ──────────────────────────────────────────────────────────────────────────────
BAND = 1.2        # vertical band height per strip
SPOR_COL = "#cc3311"
VEG_COL  = "#aaaaaa"
ALPHA_IND  = 0.25
ALPHA_MEAN = 0.92
LW_IND     = 0.5
LW_MEAN    = 2.0

fig, ax = plt.subplots(figsize=(10, 6))

for band_i, (label, sp, accent) in enumerate(STRIPS):
    y0 = band_i * BAND

    # Individual trajectories
    data = np.vstack([t[sp].values[:n_tp] for t in trajs])
    mx   = max(data.max(), 1e-9)

    for r in range(n_rep):
        ys = uniform_filter1d(data[r] / mx, size=SMOOTH)
        col = SPOR_COL if fate_spor[r] else VEG_COL
        ax.plot(time_min[t_mask], y0 + ys[t_mask],
                color=col, lw=LW_IND, alpha=ALPHA_IND, zorder=2)

    # Mean traces per fate
    for is_spor, fc in [(True, SPOR_COL), (False, VEG_COL)]:
        idx = np.where(fate_spor == is_spor)[0]
        if len(idx) == 0:
            continue
        mu = uniform_filter1d(data[idx].mean(0) / mx, size=SMOOTH)
        ax.plot(time_min[t_mask], y0 + mu[t_mask],
                color=fc, lw=LW_MEAN, alpha=ALPHA_MEAN, zorder=5)

    # θ_σH separatrix for SigmaH strip
    if sp == "SigmaH":
        theta_n = SEPARATRIX / mx
        ax.axhline(y0 + theta_n, color="#6600aa", lw=1.1,
                   ls=(0, (5, 4)), alpha=0.80, zorder=6)
        ax.text(T_MAX - 2, y0 + theta_n + 0.02, r"$\theta_{\sigma H}$",
                color="#6600aa", fontsize=8.5, ha="right", va="bottom", zorder=7)

    # Strip label on the left
    ax.text(-4, y0 + 0.50, label,
            color=accent, fontsize=12, fontweight="bold",
            ha="right", va="center")

    # Horizontal separator between strips
    if band_i < len(STRIPS) - 1:
        ax.axhline(y0 + BAND - 0.12, color="#cccccc", lw=0.6, alpha=0.5, zorder=0)

# Commitment vertical line
ax.axvline(T_COMMIT, color="#ff4444", lw=1.5, ls="--", alpha=0.75, zorder=3)
ax.text(T_COMMIT + 3, len(STRIPS) * BAND - 0.08,
        f"$t_{{\\rm commit}}={T_COMMIT:.0f}$ min",
        color="#ff4444", fontsize=9, va="top", ha="left")

ax.set_xlim(-5, T_MAX)
ax.set_ylim(-0.12, len(STRIPS) * BAND)
ax.set_yticks([])
ax.set_xlabel("Time (min)", fontsize=12)
ax.set_title(
    r"Preemption Cascade — $\it{B.\/subtilis}$ Sporulation"
    "\n"
    r"50 stochastic $\tau$-leaping replicates  ·  $N_0 = 1440\,\mu$M",
    fontsize=11,
)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.xaxis.grid(True, alpha=0.15, lw=0.5)

plt.tight_layout()

out_png = FIG_DIR / "fig_preemption_cascade_v3.png"
out_pdf = FIG_DIR / "fig_preemption_cascade_v3.pdf"
fig.savefig(out_png, dpi=200, bbox_inches="tight")
fig.savefig(out_pdf,          bbox_inches="tight")
plt.close(fig)
print(f"\nSaved:\n  {out_png}\n  {out_pdf}")
