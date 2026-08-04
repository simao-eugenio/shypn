#!/usr/bin/env python3
"""Generate ATP dynamics / θ_eff threshold figure.

Shows mean ATP depletion (16 Baseline replicates, run_20260512_210205)
crossing the thermodynamic threshold θ_eff = 2.52 mM, with nutrient
depletion on a secondary axis to illustrate the causal chain.
"""

import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.linewidth": 0.8, "pdf.fonttype": 42, "ps.fonttype": 42,
    "xtick.direction": "in", "ytick.direction": "in",
})

# ---------- paths ----------------------------------------------------------
HERE     = pathlib.Path(__file__).resolve().parent
TRAJ_DIR = (
    HERE.parents[2]
    / "experiments" / "results"
    / "run_20260512_210205"
    / "condition_Baseline"
    / "replicates_trajectories"
)
OUT_PDF = HERE / "fig_atp_threshold.pdf"
OUT_PNG = HERE / "fig_atp_threshold.png"

# ---------- load data ------------------------------------------------------
dfs       = [pd.read_csv(f, comment="#") for f in sorted(TRAJ_DIR.glob("run_*.csv"))]
n_reps    = len(dfs)
t         = dfs[0]["time"].values / 60.0          # s → min
atp_stack = np.stack([df["ATP_pool"].values  for df in dfs]) / 1000.0  # µM tokens → mM
nut_stack = np.stack([df["Nutrients"].values for df in dfs])
atp_mean  = atp_stack.mean(axis=0)
nut_mean  = nut_stack.mean(axis=0)

# ---------- key parameters -------------------------------------------------
THETA_EFF = 2.52        # mM  (1 token = 1 µM; 2520 µM ÷ 1000 = 2.52 mM)

# per-replicate first commit time (first index where ATP < THETA_EFF)
commit_times = []
for rep in atp_stack:
    idx = np.where(rep < THETA_EFF)[0]
    if len(idx):
        commit_times.append(t[idx[0]])
T_COMMIT = np.mean(commit_times) if commit_times else float("nan")

# spore appearance from mean trajectory
spore_mean = np.stack([df["Mature_spore"].values for df in dfs]).mean(axis=0)
spore_mask = np.where(spore_mean > 0.1)[0]
T_SPORE    = t[spore_mask[0]] if len(spore_mask) else float("nan")

# ---------- figure ---------------------------------------------------------
T_MAX = 35.0   # min — zoom to the depletion event
mask  = t <= T_MAX

fig, ax1 = plt.subplots(figsize=(8, 4.5))

color_atp = "#2166ac"
color_nut = "#d6604d"

# individual replicates (thin)
for rep in atp_stack:
    ax1.plot(t[mask], rep[mask], color=color_atp, lw=0.5, alpha=0.18)
# mean (bold)
ax1.plot(t[mask], atp_mean[mask], color=color_atp, lw=2.0)

ax1.set_xlabel("Tempo (min)", fontsize=9)
ax1.set_ylabel("ATP (mM)", fontsize=9, color=color_atp)
ax1.tick_params(axis="y", labelcolor=color_atp, labelsize=8)
ax1.set_xlim(0, T_MAX)
ax1.set_ylim(0, None)

# θ_eff horizontal line (appears near y=0 but anchor for the commit line)
ax1.axhline(THETA_EFF, color="#b2182b", ls="--", lw=1.4, zorder=5)

# commit / spore verticals
if not np.isnan(T_COMMIT):
    ax1.axvline(T_COMMIT, color="#b2182b", ls=":", lw=1.2, alpha=0.7)
if not np.isnan(T_SPORE):
    ax1.axvline(T_SPORE, color="#1a9850", ls=":", lw=1.2, alpha=0.7)

# shade commit → spore
if not np.isnan(T_COMMIT) and not np.isnan(T_SPORE) and T_COMMIT <= T_MAX:
    ax1.axvspan(T_COMMIT, min(T_SPORE, T_MAX), alpha=0.08, color="#b2182b")

ax1.grid(True, which="major", ls=":", alpha=0.25)
ax1.spines["top"].set_visible(False)
ax1.xaxis.set_major_locator(ticker.MultipleLocator(5))
ax1.xaxis.set_minor_locator(ticker.MultipleLocator(1))

# Nutrients on secondary axis (linear)
ax2 = ax1.twinx()
ax2.plot(t[mask], nut_mean[mask], color=color_nut, lw=1.4, ls="-", alpha=0.85)
ax2.set_ylabel("Nutrientes (contagem)", fontsize=9, color=color_nut)
ax2.tick_params(axis="y", labelcolor=color_nut, labelsize=8)
ax2.set_ylim(0, None)
ax2.spines["top"].set_visible(False)

fig.suptitle(
    r"Dinâmica de ATP e Limiar Termodinâmico $\theta_{\mathrm{eff}}$"
    r" — Esporulação de $B.\ subtilis$",
    fontsize=11, fontweight="bold", y=0.99,
)
fig.tight_layout(rect=[0, 0, 1, 0.96])

# ---------- save -----------------------------------------------------------
fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
print(f"  T_COMMIT = {T_COMMIT:.1f} min  ({len(commit_times)}/{n_reps} reps crossed {THETA_EFF})")
print(f"  T_SPORE  = {T_SPORE:.1f} min  (Mature_spore mean > 0.1)")
plt.close(fig)
