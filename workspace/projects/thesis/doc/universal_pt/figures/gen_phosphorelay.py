#!/usr/bin/env python3
"""Generate stacked-subplot phosphorelay cascade figure.

Shows the phosphotransfer pathway:
KinA → KinA~P → Spo0F~P → Spo0A~P
with unphosphorylated forms for context.
"""

import pathlib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ---------- paths ----------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
DATA = (HERE.parents[3] / "My_Project" / "thermodynamics" / "data" /
        "simulation_data.csv")
OUT_PDF = HERE / "fig_phosphorelay.pdf"
OUT_PNG = HERE / "fig_phosphorelay.png"

# ---------- load data ------------------------------------------------------
df = pd.read_csv(DATA)
t = df["Time (s)"].values / 60.0  # minutes

# ---------- define rows ----------------------------------------------------
rows = [
    ("KinA_kinase (mM)", "KinA",     "#1b9e77"),
    ("KinA_P (mM)",      "KinA~P",   "#d95f02"),
    ("Spo0F (mM)",       "Spo0F",    "#7570b3"),
    ("Spo0F_P (mM)",     "Spo0F~P",  "#e7298a"),
    ("Spo0A (mM)",       "Spo0A",    "#66a61e"),
    ("Spo0A_P (mM)",     "Spo0A~P",  "#e6ab02"),
]

n = len(rows)

# ---------- figure ---------------------------------------------------------
fig, axes = plt.subplots(n, 1, figsize=(8, 1.3 * n), sharex=True,
                         gridspec_kw={"hspace": 0.08})

for ax, (col, label, color) in zip(axes, rows):
    y = df[col].values
    ax.plot(t, y, color=color, lw=1.4)
    ax.fill_between(t, 0, y, color=color, alpha=0.15)

    # species name as Y-axis label
    ax.set_ylabel(f"{label}\n(mM)", fontsize=8, rotation=0, labelpad=30,
                  va="center", ha="center", color=color, fontweight="bold")
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, None)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(True, axis="x", ls=":", alpha=0.3)

# bottom axis
axes[-1].set_xlabel("Tempo (min)", fontsize=10)
axes[-1].xaxis.set_major_locator(ticker.MultipleLocator(30))
axes[-1].xaxis.set_minor_locator(ticker.MultipleLocator(10))

fig.suptitle(
    r"Cascata de Fosforretransmissão — Esporulação de $B.\ subtilis$",
    fontsize=12, fontweight="bold", y=0.995,
)
fig.subplots_adjust(left=0.15, right=0.97, top=0.965, bottom=0.07, hspace=0.08)

# ---------- save -----------------------------------------------------------
fig.savefig(OUT_PDF, bbox_inches="tight")
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=200)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
