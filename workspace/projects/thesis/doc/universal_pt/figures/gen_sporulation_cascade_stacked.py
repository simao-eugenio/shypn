#!/usr/bin/env python3
"""Generate stacked-subplot sporulation cascade figure.

Each sigma factor and morphological milestone gets its own row,
sharing a common time axis. Shows the sequential activation clearly.
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
    / "run_20260516_160934"
    / "condition_Baseline"
    / "replicates_trajectories"
)
OUT_PDF = HERE / "fig_sporulation_cascade_stacked.pdf"
OUT_PNG = HERE / "fig_sporulation_cascade_stacked.png"

# ---------- load data ------------------------------------------------------
dfs    = [pd.read_csv(f, comment="#") for f in sorted(TRAJ_DIR.glob("run_*.csv"))]
n_reps = len(dfs)
t      = dfs[0]["time"].values / 60.0  # s → min

# ---------- define rows ----------------------------------------------------
rows = [
    ("Spo0A_P",    "Spo0A~P",      "#1b9e77"),
    ("SigmaH",     r"$\sigma^H$",  "#d95f02"),
    ("SigmaF",     r"$\sigma^F$",  "#7570b3"),
    ("SigmaE",     r"$\sigma^E$",  "#e7298a"),
    ("SigmaG",     r"$\sigma^G$",  "#66a61e"),
    ("SigmaK",     r"$\sigma^K$",  "#e6ab02"),
    ("Forespore",  "Pré-esporo",   "#377eb8"),
    ("Mature_spore", "Esporo maduro", "#e41a1c"),
]

n = len(rows)

# ---------- figure ---------------------------------------------------------
fig, axes = plt.subplots(n, 1, figsize=(8, 1.3 * n), sharex=True,
                         gridspec_kw={"hspace": 0.08})

for ax, (col, label, color) in zip(axes, rows):
    stack = np.stack([df[col].values for df in dfs])
    mean  = stack.mean(axis=0)

    for rep in stack:
        ax.plot(t, rep, color=color, lw=0.5, alpha=0.18)
    ax.plot(t, mean, color=color, lw=1.6)

    # species name as Y-axis label
    ax.set_ylabel(label, fontsize=8, rotation=0, labelpad=40,
                  va="center", ha="right", color=color, fontweight="bold")
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, None)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(True, axis="x", ls=":", alpha=0.3)

# bottom axis
axes[-1].set_xlabel("Tempo (min)", fontsize=9)
axes[-1].xaxis.set_major_locator(ticker.MultipleLocator(30))
axes[-1].xaxis.set_minor_locator(ticker.MultipleLocator(10))

fig.suptitle(
    r"Cascata de Ativação Sequencial — Esporulação de $B.\ subtilis$",
    fontsize=12, fontweight="bold", y=0.995,
)
fig.subplots_adjust(left=0.15, right=0.97, top=0.965, bottom=0.06, hspace=0.08)
fig.text(0.01, 0.5, "Concentração (µM)", ha="center", va="center",
         rotation="vertical", fontsize=8, color="#444444")

# ---------- save -----------------------------------------------------------
fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
