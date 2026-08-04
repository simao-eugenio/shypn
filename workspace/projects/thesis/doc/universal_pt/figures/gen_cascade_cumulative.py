#!/usr/bin/env python3
"""Option 3 — Cumulative activation curves for the sporulation cascade.

Source: run_20260512_210205/condition_Baseline/replicates_trajectories/
For each cascade species: fraction of replicates that have crossed the
onset threshold by time t (Kaplan-Meier-style, but for activation).
Species are colour-coded and ordered by biological cascade position.
A single panel shows all species; the horizontal spread reveals the
stochastic variability; the left-to-right ordering reveals the sequence.
"""

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

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
OUT_PDF = HERE / "fig_cascade_cumulative.pdf"
OUT_PNG = HERE / "fig_cascade_cumulative.png"

# ---------- cascade species — three biological groups ----------------------
PHOSPHORELAY = [
    ("KinA_P",   "KinA~P",    "#4dac26"),
    ("Spo0F_P",  "Spo0F~P",   "#b8e186"),
    ("Spo0A_P",  "Spo0A~P",   "#01665e"),
]
SIGMA = [
    ("SigmaH",  "σH", "#8073ac"),
    ("SigmaF",  "σF", "#b2abd2"),
    ("SigmaE",  "σE", "#542788"),
    ("SigmaG",  "σG", "#d8daeb"),
    ("SigmaK",  "σK", "#fee0b6"),
]
MORPHO = [
    ("Septum",       "Septo",         "#1b9e77"),
    ("Forespore",    "Pré-esporo",    "#377eb8"),
    ("Mother_cell",  "Célula-mãe",   "#984ea3"),
    ("Cortex",       "Cortex",        "#ff7f00"),
    ("Inner_coat",   "Capa interna",  "#a65628"),
    ("Outer_coat",   "Capa externa",  "#e7298a"),
    ("Mature_spore", "Esporo maduro", "#e41a1c"),
]

THRESH = 0.5    # µM (= 0.5 tokens) onset threshold
T_MAX  = 35.0   # min — focus on the cascade activation window

# ---------- load trajectories ---------------------------------------------
dfs    = [pd.read_csv(f, comment="#") for f in sorted(TRAJ_DIR.glob("run_*.csv"))]
n_reps = len(dfs)
t      = dfs[0]["time"].values / 60.0   # s → min
t_mask = t <= T_MAX
t_plot = t[t_mask]

def cumulative_activation(col):
    """Return fraction of replicates activated by each time point."""
    activated = np.zeros(t_mask.sum())
    for df in dfs:
        vals = df[col].values[t_mask]
        # first crossing index
        idx = np.argmax(vals >= THRESH)
        if vals[idx] >= THRESH:
            activated[idx:] += 1
    return activated / n_reps

# ---------- figure: two panels (left = phosphorelay+sigma, right = morpho)
fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(11, 4),
    sharey=True,
    gridspec_kw={"wspace": 0.06},
)

def plot_group(ax, group, linestyle="-"):
    for col, label, color in group:
        curve = cumulative_activation(col)
        ax.step(t_plot, curve, where="post",
                color=color, lw=2.0, ls=linestyle, label=label)

# left panel: phosphorelay (solid) + sigma factors (dashed)
plot_group(ax1, PHOSPHORELAY, linestyle="-")
plot_group(ax1, SIGMA,        linestyle="--")
ax1.set_title("Fosforretransmissão + Fatores σ", fontsize=9, fontweight="bold")
ax1.legend(fontsize=7.5, loc="upper left", framealpha=0.7,
           ncol=2, handlelength=1.8)

# right panel: morphological milestones (solid)
plot_group(ax2, MORPHO, linestyle="-")
ax2.set_title("Marcos morfológicos", fontsize=9, fontweight="bold")
ax2.legend(fontsize=7.5, loc="upper left", framealpha=0.7, handlelength=1.8)

for ax in (ax1, ax2):
    ax.set_xlim(0, T_MAX)
    ax.set_ylim(-0.05, 1.10)
    ax.axhline(0.5, color="#dddddd", lw=0.7, ls=":", zorder=0)
    ax.set_xlabel("Tempo (min)", fontsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="x", ls=":", alpha=0.2, zorder=0)

ax1.set_ylabel("Fracção activada", fontsize=9)
ax2.tick_params(axis="y", labelleft=False)
fig.tight_layout(pad=1.2)

fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
