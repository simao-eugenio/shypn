#!/usr/bin/env python3
"""Sigma_H commitment threshold figure — two-panel, v9 model.

Panel A (left): Sweep A Baseline (run_20260611_231304, N_0=100 µM, 50/50 sporulate).
  All 50 replicates climb toward and cross the analytically predicted
  theta_sigma_H = 1.60 µM, confirming the Gamma-tuple prediction.

Panel B (right): Sweep C SinR=12 (run_20260614_123652, N_0=1440 µM, 48% sporulate).
  Trajectories coloured by eventual fate (sporulating=red, vegetative=grey).
  sigma_H does NOT cross 1.60 µM in either group — fate is decided by
  stochastic septation (T_septation_firings), not sigma_H threshold crossing.
  This is the genuine bet-hedging regime.
"""

import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams.update({
    "font.family":     "serif",
    "font.size":       9,
    "axes.linewidth":  0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "pdf.fonttype":    42,
    "ps.fonttype":     42,
})

# ---------- paths -----------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE.parents[2] / "experiments" / "results"

TRAJ_BASE = (RESULTS / "run_20260611_231304"
             / "condition_Baseline" / "replicates_trajectories")
TRAJ_SIN  = (RESULTS / "run_20260614_123652"
             / "condition_separatrix_SinR12" / "replicates_trajectories")
REP_SIN   = (RESULTS / "run_20260614_123652"
             / "condition_separatrix_SinR12" / "replicates.csv")

OUT_PDF = HERE / "fig_sigma_h_separatrix.pdf"
OUT_PNG = HERE / "fig_sigma_h_separatrix.png"

THETA_SIGMA_H = 1.60   # µM  analytically predicted by Gamma-tuple

# ---------- load Panel A (Baseline) -----------------------------------------
files_a = sorted(TRAJ_BASE.glob("run_*.csv"))
dfs_a   = [pd.read_csv(f, comment="#") for f in files_a]   # 50 replicates
t_a     = dfs_a[0]["time"].values / 60.0

# ---------- load Panel B (SinR=12, mixed fate) ------------------------------
files_b = sorted(TRAJ_SIN.glob("run_*.csv"))
dfs_b   = [pd.read_csv(f, comment="#") for f in files_b]   # 50 replicates
rep_b   = pd.read_csv(REP_SIN, comment="#")
t_b     = dfs_b[0]["time"].values / 60.0

# classify by Mature_spore_final
ms_b        = rep_b["Mature_spore_final"].values
spor_idx    = [i for i, v in enumerate(ms_b) if v > 0.5]
veg_idx     = [i for i, v in enumerate(ms_b) if v <= 0.5]
n_spor, n_veg = len(spor_idx), len(veg_idx)

# ---------- figure ----------------------------------------------------------
fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10.0, 3.4),
                                  gridspec_kw={"wspace": 0.34})

# ------ Panel A -- Baseline -------------------------------------------------
for df in dfs_a:
    ax_a.plot(t_a, df["SigmaH"].values,
              color="#d73027", lw=0.55, alpha=0.30, zorder=2)
sh_mean_a = np.stack([df["SigmaH"].values for df in dfs_a]).mean(axis=0)
ax_a.plot(t_a, sh_mean_a, color="#a50026", lw=1.8, zorder=4,
          label="Media (50/50 esporulam)")
ax_a.axhline(THETA_SIGMA_H, color="#762a83", lw=1.2, ls="--", zorder=5)
ax_a.text(t_a[-1] * 0.96, THETA_SIGMA_H + 0.05,
          r"$\theta_{\sigma H} = 1{,}60\,\mu$M",
          color="#762a83", fontsize=7.5, ha="right", va="bottom")
ax_a.set_xlabel("Tempo (min)", fontsize=9)
ax_a.set_ylabel(r"$\sigma_H\;(\mu\mathrm{M})$", fontsize=9)
ax_a.set_xlim(0, t_a[-1])
ax_a.set_ylim(bottom=0)
ax_a.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
ax_a.yaxis.set_minor_locator(ticker.MultipleLocator(0.25))
ax_a.legend(fontsize=7.5, loc="upper left", framealpha=0.85)
ax_a.set_title("(A) Linha de Base  \u2014  $N_0 = 100\\,\\mu$M\n"
               "Todas as 50 replicas esporulam;\n"
               r"$\sigma_H$ ultrapassa $\theta_{\sigma H}$ (previsto)",
               fontsize=8, loc="left")
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)

# ------ Panel B -- SinR=12 (mixed fate) ------------------------------------
for i in veg_idx:
    ax_b.plot(t_b, dfs_b[i]["SigmaH"].values,
              color="#888888", lw=0.55, alpha=0.35, zorder=2)
for i in spor_idx:
    ax_b.plot(t_b, dfs_b[i]["SigmaH"].values,
              color="#d73027", lw=0.55, alpha=0.45, zorder=3)

sh_mean_spor = np.stack([dfs_b[i]["SigmaH"].values for i in spor_idx]).mean(axis=0)
sh_mean_veg  = np.stack([dfs_b[i]["SigmaH"].values for i in veg_idx]).mean(axis=0)
ax_b.plot(t_b, sh_mean_spor, color="#a50026", lw=1.6, zorder=5,
          label=f"Esporulando ({n_spor}/50) \u2014 media")
ax_b.plot(t_b, sh_mean_veg,  color="#444444", lw=1.6, zorder=5,
          label=f"Vegetativo  ({n_veg}/50) \u2014 media")

ax_b.axhline(THETA_SIGMA_H, color="#762a83", lw=1.2, ls="--", zorder=6)
ax_b.text(t_b[-1] * 0.96, THETA_SIGMA_H + 0.05,
          r"$\theta_{\sigma H} = 1{,}60\,\mu$M",
          color="#762a83", fontsize=7.5, ha="right", va="bottom")
ax_b.set_xlabel("Tempo (min)", fontsize=9)
ax_b.set_xlim(0, t_b[-1])
ax_b.set_ylim(bottom=0)
ax_b.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
ax_b.yaxis.set_minor_locator(ticker.MultipleLocator(0.25))
ax_b.legend(fontsize=7.5, loc="lower left", framealpha=0.85)
ax_b.set_title(f"(B) SinR = 12 \u03bcM  \u2014  $N_0 = 1440\\,\\mu$M\n"
               "Bet-hedging: $\\sigma_H$ similar em ambos os destinos;\n"
               "comprometimento determinado pela septacao",
               fontsize=8, loc="left")
ax_b.spines["top"].set_visible(False)
ax_b.spines["right"].set_visible(False)

# ---------- save ------------------------------------------------------------
fig.tight_layout(pad=0.5)
fig.savefig(OUT_PDF, dpi=300, bbox_inches="tight")
fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT_PDF}")
print(f"Saved: {OUT_PNG}")
