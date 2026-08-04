#!/usr/bin/env python3
"""Replicate-level Mature_spore distributions across all 18 factorial
conditions (run_20260512_210205).

Layout: 3 rows (N₀ = 10, 100, 300) × 6 columns (T = 310 / 320 K ×
σ half-life = 30 / 120 / 600 min).  Each sub-panel is a strip chart
of the 16 independent replicate endpoint values; the dashed horizontal
marks the condition mean.

Bistable conditions — those where replicates split into a low-mode
(≤ 5 tokens) and a high-mode (≥ 20 tokens) — are drawn in red.
Non-bistable conditions are drawn in blue.  No legend box on figure;
colour interpretation lives in the caption.
"""

import re
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family":    "serif",
    "font.size":      9,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "pdf.fonttype":   42,
    "ps.fonttype":    42,
})

# ---------- paths -----------------------------------------------------------
HERE    = pathlib.Path(__file__).resolve().parent
RUN_DIR = HERE.parents[2] / "experiments" / "results" / "run_20260512_210205"
OUT_PDF = HERE / "fig_bistability_replicates.pdf"
OUT_PNG = HERE / "fig_bistability_replicates.png"


# ---------- helpers ---------------------------------------------------------
def parse_params(dirname: str) -> dict:
    """Extract sweep parameters from a condition directory name."""
    out = {}
    for key in ("INITIAL_NUTRIENTS", "TEMPERATURE_K", "SIGMA_HALFLIFE_MIN"):
        m = re.search(rf'\[param\]_{key}_eq_([\d.]+)', dirname)
        if m:
            out[key] = float(m.group(1))
    return out


def is_bistable(vals: np.ndarray, low_thr: int = 5,
                high_thr: int = 20, min_count: int = 2) -> bool:
    """True when replicates populate both a low and a high mode."""
    return (np.sum(vals <= low_thr) >= min_count and
            np.sum(vals >= high_thr) >= min_count)


# ---------- load all 18 factorial conditions --------------------------------
conds: list[dict] = []
seen:  set        = set()

for cdir in sorted(RUN_DIR.glob("condition_*")):
    raw_name = cdir.name.replace("condition_", "", 1)
    if raw_name == "Baseline":
        continue                          # Baseline excluded; use factorial grid
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
    conds.append({
        "N":    key[0],
        "T":    key[1],
        "HL":   key[2],
        "spore": df["Mature_spore_final"].values.astype(float),
    })

# ---------- grid organisation -----------------------------------------------
N_vals  = [10, 100, 300]
T_vals  = [310.15, 320.15]
HL_vals = [30, 120, 600]
# 6 columns: T=310/HL=30, T=310/HL=120, T=310/HL=600,
#            T=320/HL=30, T=320/HL=120, T=320/HL=600
col_keys = [(t, hl) for t in T_vals for hl in HL_vals]

# per-row y-limits — use 95th percentile so a single extreme outlier
# does not collapse the rest of the panels; outlier dots are clipped.
row_ymax = {}
for N_val in N_vals:
    all_vals = np.concatenate([c["spore"] for c in conds if c["N"] == N_val])
    row_ymax[N_val] = float(np.percentile(all_vals, 95)) * 1.35 if len(all_vals) else 10.0
    row_ymax[N_val] = max(row_ymax[N_val], 10.0)   # floor

CLR_BIST = "#d73027"   # red  — bistable
CLR_NORM = "#4575b4"   # blue — non-bistable

rng = np.random.default_rng(42)

# ---------- figure ----------------------------------------------------------
fig, axes = plt.subplots(
    3, 6, figsize=(9.5, 5.5),
    gridspec_kw={"wspace": 0.20, "hspace": 0.65},
)

for ri, N_val in enumerate(N_vals):
    for ci, (T_val, HL_val) in enumerate(col_keys):
        ax = axes[ri, ci]
        match = [c for c in conds
                 if c["N"] == N_val and c["T"] == T_val and c["HL"] == HL_val]
        if not match:
            ax.set_visible(False)
            continue

        spore = match[0]["spore"]
        bist  = is_bistable(spore)
        color = CLR_BIST if bist else CLR_NORM

        jx = rng.uniform(-0.22, 0.22, len(spore))
        ax.scatter(jx, spore, s=22, c=color, alpha=0.78, zorder=3,
                   linewidths=0, rasterized=True, clip_on=True)
        ax.axhline(spore.mean(), color=color, lw=1.1, ls="--", alpha=0.65)

        ax.set_xlim(-0.55, 0.55)
        ax.set_ylim(-3.0, row_ymax[N_val])
        ax.set_xticks([])
        ax.tick_params(axis="y", labelsize=6.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)

        # column headers on top row only
        if ri == 0:
            t_str  = "310 K" if T_val < 315 else "320 K"
            ax.set_title(f"T={t_str}\nHL={HL_val} min", fontsize=7.0, pad=3)

    # row y-label
    axes[ri, 0].set_ylabel(f"$N_0$={N_val}", fontsize=8.5, labelpad=2)

# shared x-label
fig.text(0.50, 0.005,
         "Esporos maduros — valor final por réplica (contagem)",
         ha="center", fontsize=9)

# light vertical separator between T=310 K and T=320 K halves
fig.add_artist(
    plt.Line2D([0.525, 0.525], [0.07, 0.97],
               transform=fig.transFigure, color="#999999",
               lw=0.7, ls=":", zorder=10)
)

fig.suptitle(
    r"Bistabilidade Estocástica — Distribuições Finais de Esporos ($B.\ subtilis$)",
    fontsize=12, fontweight="bold", y=0.995,
)
fig.subplots_adjust(left=0.08, right=0.98, top=0.89, bottom=0.08)
fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
