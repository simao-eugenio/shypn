#!/usr/bin/env python3
"""Kymograph (heatmap) of the full sporulation cascade.

Source: run_20260512_210205/condition_Baseline/replicates_trajectories/
Each row = one cascade species (biological order, top→bottom).
Each column = time (minutes).
Colour = mean concentration normalised 0→1 per species (row-wise).
White vertical line = mean onset time per species.
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
OUT_PDF = HERE / "fig_cascade_kymograph.pdf"
OUT_PNG = HERE / "fig_cascade_kymograph.png"

# ---------- cascade species in biological order ----------------------------
# (phosphorelay → sigma factors → morphological milestones)
CASCADE = [
    ("KinA_kinase", "KinA"),
    ("KinA_P",      "KinA~P"),
    ("Spo0F",       "Spo0F"),
    ("Spo0F_P",     "Spo0F~P"),
    ("Spo0B",       "Spo0B"),
    ("Spo0A",       "Spo0A"),
    ("Spo0A_P",     "Spo0A~P"),
    ("SigmaH",      "σH"),
    ("SigmaF",      "σF"),
    ("SigmaE",      "σE"),
    ("SigmaG",      "σG"),
    ("SigmaK",      "σK"),
    ("Septum",      "Septo"),
    ("Forespore",   "Pré-esporo"),
    ("Mother_cell", "Célula-mãe"),
    ("Cortex",      "Cortex"),
    ("Inner_coat",  "Capa interna"),
    ("Outer_coat",  "Capa externa"),
    ("Mature_spore","Esporo maduro"),
]
cols   = [c for c, _ in CASCADE]
labels = [l for _, l in CASCADE]

THRESH = 0.5   # µM (= 0.5 tokens) onset threshold
T_MAX  = 120.0 # min — show first 2 h to capture cascade activation

# ---------- load trajectories ---------------------------------------------
dfs    = [pd.read_csv(f, comment="#") for f in sorted(TRAJ_DIR.glob("run_*.csv"))]
n_reps = len(dfs)
t      = dfs[0]["time"].values / 60.0              # s → min
t_mask = t <= T_MAX
t_plot = t[t_mask]

# mean matrix: shape (n_species, n_timepoints_masked)
means = np.stack(
    [np.stack([df[c].values[t_mask] for df in dfs]).mean(axis=0) for c in cols]
)

# row-wise normalise 0→1
row_max = means.max(axis=1, keepdims=True)
row_max[row_max == 0] = 1.0
norm = means / row_max

# mean onset time per species (over mean trajectory)
onset_times = []
for row in means:
    idx = np.argmax(row >= THRESH)
    onset_times.append(t_plot[idx] if row[idx] >= THRESH else np.nan)

# ---------- figure --------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))

im = ax.imshow(
    norm,
    aspect="auto",
    origin="upper",
    cmap="YlOrRd",
    vmin=0, vmax=1,
    extent=[t_plot[0], t_plot[-1], len(CASCADE) - 0.5, -0.5],
    interpolation="bilinear",
)

# group separators
ax.axhline(11.5, color="white", lw=1.0, ls="--", alpha=0.6)
ax.axhline(7.5,  color="white", lw=1.0, ls="--", alpha=0.6)

# axes
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=8.5)
ax.set_xlabel("Tempo (min)", fontsize=9)
ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(5))

# colourbar
cb = fig.colorbar(im, ax=ax, fraction=0.022, pad=0.02)
cb.set_label("Concentração normalizada", fontsize=8)
cb.ax.tick_params(labelsize=7)

fig.tight_layout(pad=1.2)

fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
