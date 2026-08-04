#!/usr/bin/env python3
"""Option 2 — Violin plot of per-replicate onset times for cascade species.

Source: run_20260512_210205/condition_Baseline/replicates_trajectories/
X-axis: cascade species in biological order.
Y-axis: onset time (minutes) per replicate.
Shows both the sequential order and the stochastic spread between replicates.
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
OUT_PDF = HERE / "fig_cascade_onset_violin.pdf"
OUT_PNG = HERE / "fig_cascade_onset_violin.png"

# ---------- cascade species in biological order ----------------------------
CASCADE = [
    ("KinA_kinase", "KinA",          "#8dd3c7"),
    ("KinA_P",      "KinA~P",        "#8dd3c7"),
    ("Spo0F_P",     "Spo0F~P",       "#80b1d3"),
    ("Spo0A_P",     "Spo0A~P",       "#80b1d3"),
    ("SigmaH",      "σH",            "#bebada"),
    ("SigmaF",      "σF",            "#bebada"),
    ("SigmaE",      "σE",            "#bebada"),
    ("SigmaG",      "σG",            "#bebada"),
    ("SigmaK",      "σK",            "#bebada"),
    ("Septum",      "Septo",         "#1b9e77"),
    ("Forespore",   "Pré-esporo",    "#377eb8"),
    ("Mother_cell", "Célula-mãe",   "#984ea3"),
    ("Cortex",      "Cortex",        "#ff7f00"),
    ("Inner_coat",  "Capa interna",  "#a65628"),
    ("Outer_coat",  "Capa externa",  "#e7298a"),
    ("Mature_spore","Esporo maduro", "#e41a1c"),
]

THRESH = 0.5   # mM onset threshold

# ---------- load trajectories ---------------------------------------------
dfs    = [pd.read_csv(f, comment="#") for f in sorted(TRAJ_DIR.glob("run_*.csv"))]
n_reps = len(dfs)
t      = dfs[0]["time"].values / 60.0   # s → min

# compute per-replicate onset for each species
onset_data = {}   # col -> list of onset times (one per replicate)
for col, label, color in CASCADE:
    onsets = []
    for df in dfs:
        vals = df[col].values
        idx  = np.argmax(vals >= THRESH)
        onsets.append(t[idx] if vals[idx] >= THRESH else np.nan)
    onset_data[col] = np.array(onsets)

# ---------- figure --------------------------------------------------------
x_labels = [label for _, label, _ in CASCADE]
colors    = [color for _, _, color in CASCADE]
n         = len(CASCADE)

fig, ax = plt.subplots(figsize=(10, 4))

for i, (col, label, color) in enumerate(CASCADE):
    data = onset_data[col]
    valid = data[~np.isnan(data)]
    if len(valid) == 0:
        continue

    if len(np.unique(valid)) > 1:
        parts = ax.violinplot(
            valid, positions=[i], widths=0.7,
            showmedians=True, showextrema=False,
        )
        for pc in parts["bodies"]:
            pc.set_facecolor(color)
            pc.set_alpha(0.55)
        parts["cmedians"].set_color(color)
        parts["cmedians"].set_linewidth(2)
    else:
        # all replicates identical — single scatter point
        ax.scatter([i] * len(valid), valid, color=color, s=40, zorder=3, alpha=0.8)

    # individual replicate dots
    jitter = np.random.default_rng(42).uniform(-0.12, 0.12, len(valid))
    ax.scatter(
        np.full(len(valid), i) + jitter, valid,
        color=color, s=18, alpha=0.7, zorder=4
    )

# group separators
ax.axvline(3.5, color="#cccccc", lw=0.7, ls="--", zorder=0)
ax.axvline(8.5, color="#cccccc", lw=0.7, ls="--", zorder=0)

ax.set_xticks(range(n))
ax.set_xticklabels(x_labels, rotation=38, ha="right", fontsize=8.5)
ax.set_ylabel("Tempo de início (min)", fontsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.grid(True, axis="y", ls=":", alpha=0.25, zorder=0)
fig.tight_layout(pad=1.2)

fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
