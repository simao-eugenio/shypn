#!/usr/bin/env python3
"""Figure 4.2 — Morphological assembly programme (v9 Baseline).

Source: run_20260611_231304/condition_Baseline/replicates_trajectories/
50 individual trajectories + mean. Full 360-min horizon with
logarithmic time axis so both the ignition phase (~17 min) and the
slow Outer-coat accumulation are visible in one panel.
No legend; species labelled on y-axis. 300 dpi.
"""

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

# --- publication-quality rcParams ----------------------------------------
plt.rcParams.update({
    "font.family":        "serif",
    "font.size":          9,
    "axes.linewidth":     0.8,
    "xtick.major.width":  0.8,
    "ytick.major.width":  0.8,
    "xtick.minor.width":  0.5,
    "ytick.minor.width":  0.5,
    "xtick.direction":    "in",
    "ytick.direction":    "in",
    "xtick.major.size":   4,
    "ytick.major.size":   4,
    "xtick.minor.size":   2,
    "ytick.minor.size":   2,
    "lines.linewidth":    1.0,
    "pdf.fonttype":       42,
    "ps.fonttype":        42,
})

# ---------- paths ----------------------------------------------------------
HERE     = pathlib.Path(__file__).resolve().parent
TRAJ_DIR = (
    HERE.parents[2]
    / "experiments" / "results"
    / "run_20260611_231304"
    / "condition_Baseline"
    / "replicates_trajectories"
)
OUT_PDF = HERE / "fig_morphological_assembly.pdf"
OUT_PNG = HERE / "fig_morphological_assembly.png"

# ---------- species in biological order -----------------------------------
ROWS = [
    ("Septum",       "Septo",         "#1b9e77"),
    ("Forespore",    "Pré-esporo",    "#377eb8"),
    ("Mother_cell",  "Célula-mãe",   "#984ea3"),
    ("Cortex",       "Cortex",        "#d95f02"),
    ("Inner_coat",   "Capa interna",  "#7570b3"),
    ("Outer_coat",   "Capa externa",  "#e7298a"),
    ("Mature_spore", "Esporo maduro", "#e6ab02"),
]

# ---------- load ----------------------------------------------------------
dfs    = [pd.read_csv(f, comment="#") for f in sorted(TRAJ_DIR.glob("run_*.csv"))]
n_reps = len(dfs)
t      = dfs[0]["time"].values / 60.0   # s → min
# avoid log(0): start at first nonzero time point
t_plot = t[t > 0]
i0     = np.searchsorted(t, t_plot[0])

n = len(ROWS)
fig, axes = plt.subplots(n, 1, figsize=(5.5, 1.25 * n),
                         gridspec_kw={"hspace": 0.08})

for ax, (col, label, color) in zip(axes, ROWS):
    stack = np.stack([df[col].values[i0:] for df in dfs])
    mean  = stack.mean(axis=0)

    for rep in stack:
        ax.plot(t_plot, rep, color=color, lw=0.55, alpha=0.22)
    ax.plot(t_plot, mean, color=color, lw=1.8)

    ax.set_xscale("log")
    ax.set_xlim(t_plot[0], t_plot[-1])
    ax.set_ylim(bottom=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(which="both", labelsize=7)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=3, min_n_ticks=2))

    ax.set_ylabel(label, fontsize=8, rotation=0, labelpad=40,
                  va="center", ha="right", color=color, fontweight="bold")

# x-axis only on bottom panel
for ax in axes[:-1]:
    ax.tick_params(labelbottom=False)

axes[-1].set_xlabel("Tempo (min, escala logarítmica)", fontsize=9)

# shared ignition marker: dashed vertical line at t=17 min (mean SigmaH ignition, v9 Baseline)
for ax in axes:
    ax.axvline(17, color="#999999", lw=0.7, ls="--", zorder=0)

fig.suptitle(
    "Programa de montagem morfológica — Esporulação de B. subtilis (modelo v9, 50 réplicas)",
    fontsize=10, fontweight="bold",
)
fig.subplots_adjust(left=0.22, right=0.97, top=0.94, bottom=0.07)
fig.text(0.01, 0.5, "Contagem", ha="center", va="center",
         rotation="vertical", fontsize=8, color="#444444")

fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
