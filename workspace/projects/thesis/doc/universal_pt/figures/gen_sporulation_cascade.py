#!/usr/bin/env python3
"""Generate dual-panel sporulation cascade figure.

Top panel:  Signalling cascade (Spo0A~P → σH → σF → σE → σG → σK)
Bottom panel: Morphological milestones (Forespore, Cortex, Coats, Mature spore)
"""

import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ---------- paths ----------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
DATA = (HERE.parents[3] / "My_Project" / "thermodynamics" / "data" /
        "simulation_data.csv")
OUT_PDF = HERE / "fig_sporulation_cascade.pdf"
OUT_PNG = HERE / "fig_sporulation_cascade.png"

# ---------- load data ------------------------------------------------------
df = pd.read_csv(DATA)
t = df["Time (s)"].values / 60.0  # convert to minutes

# ---------- figure ---------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True,
                                gridspec_kw={"hspace": 0.12})

# --- Top panel: sigma cascade + Spo0A~P -----------------------------------
cascade = [
    ("Spo0A_P (mM)",  "Spo0A~P",   "#1b9e77", "-"),
    ("SigmaH (mM)",   "σH",         "#d95f02", "-"),
    ("SigmaF (mM)",   "σF",         "#7570b3", "-"),
    ("SigmaE (mM)",   "σE",         "#e7298a", "-"),
    ("SigmaG (mM)",   "σG",         "#66a61e", "-"),
    ("SigmaK (mM)",   "σK",         "#e6ab02", "-"),
]

for col, label, color, ls in cascade:
    ax1.plot(t, df[col].values, label=label, color=color, ls=ls, lw=1.6)

ax1.set_ylabel("Concentration (mM)")
ax1.set_title("Signalling Cascade", fontsize=11, fontweight="bold", loc="left")
ax1.legend(ncol=3, fontsize=8, loc="upper left", framealpha=0.85)
ax1.set_xlim(0, t[-1])

# --- Bottom panel: morphological milestones --------------------------------
morph = [
    ("Forespore (mM)",    "Forespore",    "#377eb8", "-"),
    ("Cortex (mM)",       "Cortex",       "#ff7f00", "-"),
    ("Inner_coat (mM)",   "Inner coat",   "#984ea3", "-"),
    ("Outer_coat (mM)",   "Outer coat",   "#a65628", "-"),
    ("Mature_spore (mM)", "Mature spore", "#e41a1c", "-"),
]

for col, label, color, ls in morph:
    ax2.plot(t, df[col].values, label=label, color=color, ls=ls, lw=1.6)

ax2.set_ylabel("Concentration (mM)")
ax2.set_xlabel("Time (min)")
ax2.set_title("Morphological Programme", fontsize=11, fontweight="bold",
              loc="left")
ax2.legend(ncol=3, fontsize=8, loc="upper left", framealpha=0.85)

# --- shared formatting -----------------------------------------------------
for ax in (ax1, ax2):
    ax.xaxis.set_major_locator(ticker.MultipleLocator(30))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(10))
    ax.grid(True, which="major", ls=":", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.suptitle(
    r"$B.\ subtilis$ Sporulation — Sigma Cascade and Morphogenesis",
    fontsize=12, fontweight="bold", y=0.98,
)
fig.tight_layout(rect=[0, 0, 1, 0.95])

# ---------- save -----------------------------------------------------------
fig.savefig(OUT_PDF, bbox_inches="tight")
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=200)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
