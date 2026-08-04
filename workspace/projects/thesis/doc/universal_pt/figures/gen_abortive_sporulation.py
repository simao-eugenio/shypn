#!/usr/bin/env python3
"""Outer_coat vs Mature_spore endpoint scatter across all 18 factorial
conditions (run_20260512_210205) — log-log axes.

Each point is the 16-replicate mean for one condition.  Log–log scale
keeps all three N₀ groups visible.  Iso-efficiency contour lines at
1 %, 10 %, and 50 % (Mature_spore / Outer_coat ratio) are straight
lines on log–log axes; N₀ = 300 conditions plot clearly below 1 %,
exposing the abortive-sporulation regime.

N₀ levels are distinguished by marker shape (○ ▪ ◆) and colour; no
legend box.  Direct text annotations identify each group.
"""

import re
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams.update({
    "font.family":    "serif",
    "font.size":      9,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 4,
    "ytick.major.size": 4,
    "pdf.fonttype":   42,
    "ps.fonttype":    42,
})

# ---------- paths -----------------------------------------------------------
HERE    = pathlib.Path(__file__).resolve().parent
RUN_DIR = HERE.parents[2] / "experiments" / "results" / "run_20260512_210205"
OUT_PDF = HERE / "fig_abortive_sporulation.pdf"
OUT_PNG = HERE / "fig_abortive_sporulation.png"


# ---------- helpers ---------------------------------------------------------
def parse_params(dirname: str) -> dict:
    out = {}
    for key in ("INITIAL_NUTRIENTS", "TEMPERATURE_K", "SIGMA_HALFLIFE_MIN"):
        m = re.search(rf'\[param\]_{key}_eq_([\d.]+)', dirname)
        if m:
            out[key] = float(m.group(1))
    return out


# ---------- load ------------------------------------------------------------
data: list[dict] = []
seen: set        = set()

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
    data.append({
        "N":     key[0],
        "T":     key[1],
        "HL":    key[2],
        "outer": float(df["Outer_coat_final"].mean()),
        "spore": float(df["Mature_spore_final"].mean()),
    })

# ---------- visual encoding -------------------------------------------------
COLORS  = {10: "#1a9850", 100: "#d97b00", 300: "#d73027"}
MARKERS = {10: "o",       100: "s",       300: "D"}
SIZES   = {10: 65,        100: 65,        300: 65}

# ---------- log-log iso-efficiency lines ------------------------------------
all_outer = [d["outer"] for d in data if d["outer"] > 0]
all_spore = [d["spore"] for d in data if d["spore"] > 0]
x_min_log = 0.5
x_max_log = max(all_outer) * 2.5 if all_outer else 3000.0
x_iso = np.logspace(np.log10(x_min_log), np.log10(x_max_log), 400)

# ---------- figure ----------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.5, 4.8))

# iso-efficiency contours — straight lines in log-log space
# label fractions chosen so each label lands within the y_data range
_lbl_frac = {0.50: 0.38, 0.10: 0.50, 0.01: 0.65}
for eff, label, ls in [(0.50, "50 %", "-"),
                       (0.10, "10 %", "--"),
                       (0.01,  "1 %", ":")]:
    y_iso = eff * x_iso
    ax.plot(x_iso, y_iso, color="#999999", lw=0.9, ls=ls, zorder=1)
    frac = _lbl_frac[eff]
    x_lbl = np.exp(np.log(x_min_log) + frac * (np.log(x_max_log) - np.log(x_min_log)))
    y_lbl = eff * x_lbl
    ax.text(x_lbl, y_lbl * 1.18, label, fontsize=7, color="#777777",
            va="bottom",
            bbox=dict(facecolor="white", edgecolor="none", pad=0.5))

# guard: replace 0 with small positive for log scale
for d in data:
    ax.scatter(
        max(d["outer"], 0.3), max(d["spore"], 0.3),
        s=SIZES[d["N"]], c=COLORS[d["N"]], marker=MARKERS[d["N"]],
        zorder=4, alpha=0.88, linewidths=0.6, edgecolors="white",
    )

# direct group annotations — one per N₀ group near its centroid
for N_val in (10, 100, 300):
    group = [d for d in data if d["N"] == N_val]
    cx = np.exp(np.mean(np.log([max(d["outer"], 0.3) for d in group])))
    cy = np.exp(np.mean(np.log([max(d["spore"],  0.3) for d in group])))
    offsets = {10: (1.5, 1.8), 100: (0.5, 2.5), 300: (1.5, 0.4)}
    fx, fy = offsets[N_val]
    ax.annotate(
        f"$N_0$ = {N_val}",
        xy=(cx, cy),
        xytext=(cx * fx, cy * fy),
        fontsize=8, color=COLORS[N_val], fontweight="bold",
        arrowprops=dict(arrowstyle="-", color=COLORS[N_val],
                        lw=0.6, shrinkA=0, shrinkB=2),
    )

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(x_min_log, x_max_log)
ax.set_ylim(0.25, max(all_spore) * 3.5 if all_spore else 100)
ax.set_xlabel("Capa externa — valor final médio (contagem)", fontsize=9)
ax.set_ylabel("Esporo maduro — valor final médio (contagem)", fontsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.xaxis.set_major_formatter(ticker.LogFormatterSciNotation(labelOnlyBase=True))
ax.yaxis.set_major_formatter(ticker.LogFormatterSciNotation(labelOnlyBase=True))

fig.suptitle(
    r"Esporulação Abortiva — Eficiência da Cascata Morfogenética ($B.\ subtilis$)",
    fontsize=12, fontweight="bold", y=1.01,
)
fig.tight_layout()
fig.savefig(OUT_PDF, bbox_inches="tight", dpi=300)
fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
print(f"Saved {OUT_PDF.name}  ({OUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"Saved {OUT_PNG.name}  ({OUT_PNG.stat().st_size / 1024:.0f} KB)")
plt.close(fig)
