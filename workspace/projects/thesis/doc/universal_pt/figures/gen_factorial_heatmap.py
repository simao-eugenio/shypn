#!/usr/bin/env python3
"""Factorial heatmap of mean Mature_spore final value (tokens) across
the full 3 × 2 × 3 parameter grid: N₀ × Temperature × σ half-life.

Left panel : T = 310.15 K
Right panel: T = 320.15 K

Rows  = σ half-life (30 / 120 / 600 min) — bet-hedging axis.
Cols  = Initial nutrients N₀ (10 / 100 / 300 tokens) — nutrient axis.
Colour = mean Mature_spore_final (tokens) across 16 replicates.

Numeric values are printed in each cell.  A shared colorbar replaces
any legend.  Non-monotonic temperature suppression and the σ_½
bet-hedging dial are both visible without any legend box.
"""

import re
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm

plt.rcParams.update({
    "font.family":    "serif",
    "font.size":      9,
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "pdf.fonttype":   42,
    "ps.fonttype":    42,
})

# ---------- paths -----------------------------------------------------------
HERE    = pathlib.Path(__file__).resolve().parent
RUN_DIR = HERE.parents[2] / "experiments" / "results" / "run_20260512_210205"
OUT_PDF = HERE / "fig_factorial_heatmap.pdf"
OUT_PNG = HERE / "fig_factorial_heatmap.png"


# ---------- helpers ---------------------------------------------------------
def parse_params(dirname: str) -> dict:
    out = {}
    for key in ("INITIAL_NUTRIENTS", "TEMPERATURE_K", "SIGMA_HALFLIFE_MIN"):
        m = re.search(rf'\[param\]_{key}_eq_([\d.]+)', dirname)
        if m:
            out[key] = float(m.group(1))
    return out


# ---------- load ------------------------------------------------------------
cell_data: dict[tuple, float] = {}
seen: set                     = set()

for cdir in sorted(RUN_DIR.glob("condition_*")):
    raw_name = cdir.name.replace("condition_", "", 1)
    if raw_name == "Baseline":
        continue
    params = parse_params(raw_name)
    if not params or "INITIAL_NUTRIENTS" not in params:
        continue
    key = (int(params["INITIAL_NUTRIENTS"]),
           params["TEMPERATURE_K"],
           int(params["SIGMA_HALFLIFE_MIN"]))
    if key in seen:
        continue
    seen.add(key)
    rep_csv = cdir / "replicates.csv"
    if not rep_csv.exists():
        continue
    df = pd.read_csv(rep_csv)
    cell_data[key] = float(df["Mature_spore_final"].mean())

# ---------- grid ------------------------------------------------------------
N_vals  = [10, 100, 300]
T_vals  = [310.15, 320.15]
HL_vals = [30, 120, 600]

# grid shape: (n_T, n_HL, n_N)
grid = np.full((len(T_vals), len(HL_vals), len(N_vals)), np.nan)
for ti, T in enumerate(T_vals):
    for hi, HL in enumerate(HL_vals):
        for ni, N in enumerate(N_vals):
            k = (N, T, HL)
            if k in cell_data:
                grid[ti, hi, ni] = cell_data[k]

vmin, vmax = 0.0, float(np.nanmax(grid))
norm = Normalize(vmin=vmin, vmax=vmax)
cmap = "YlOrRd"

# ---------- figure ----------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0),
                         gridspec_kw={"wspace": 0.08})

T_labels = ["T = 310 K", "T = 320 K"]
for pi, (ax, T_val) in enumerate(zip(axes, T_vals)):
    mat = grid[pi]          # shape (n_HL, n_N)
    im  = ax.imshow(mat, cmap=cmap, norm=norm, aspect="auto",
                    interpolation="nearest")

    # cell annotations
    for hi in range(len(HL_vals)):
        for ni in range(len(N_vals)):
            val = mat[hi, ni]
            if not np.isnan(val):
                text_color = "white" if val > vmax * 0.60 else "#222222"
                ax.text(ni, hi, f"{val:.0f}",
                        ha="center", va="center",
                        fontsize=9.0, color=text_color, fontweight="bold")

    ax.set_xticks(range(len(N_vals)))
    ax.set_xticklabels([f"$N_0$={n}" for n in N_vals], fontsize=8.5)
    ax.set_yticks(range(len(HL_vals)))

    if pi == 0:
        ax.set_yticklabels([f"HL = {hl} min" for hl in HL_vals], fontsize=8.5)
    else:
        ax.set_yticklabels([])          # shared y-axis; hide duplicates

    ax.set_title(T_labels[pi], fontsize=9, fontweight="bold", pad=6)
    ax.tick_params(length=0)           # ticks invisible — cells carry the data

# shared colorbar
sm = cm.ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])
cbar = fig.colorbar(sm, ax=axes.ravel().tolist(),
                    fraction=0.040, pad=0.02, shrink=0.92)
cbar.set_label("Esporos maduros\n(média, contagem)", fontsize=8.5)
cbar.ax.tick_params(labelsize=8)

fig.suptitle(
    r"Mapa Fatorial — Esporos Maduros por Condição ($B.\ subtilis$)",
    fontsize=12, fontweight="bold", y=1.01,
)
fig.subplots_adjust(left=0.14, right=0.86, top=0.86, bottom=0.10)
fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
