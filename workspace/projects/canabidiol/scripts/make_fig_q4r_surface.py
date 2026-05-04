"""Figure 1: Q4r therapeutic surface — NFκB, ROS, AβO heatmaps over (MAINT, DSEV).

Clean design: three side-by-side heatmaps, shared layout, one colorbar each,
numeric cell labels. No arrows, no annotations beyond axis labels and titles.
The surrounding manuscript text carries the interpretation.
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "experiments/results/run_20260503_130113"
OUT = ROOT / "figures" / "fig_q4r_surface.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

data = json.loads((RUN / "q4r_endpoints.json").read_text())
DOSES = [0.0, 0.5, 2.0, 5.0]
SEVS = [0.0, 1.0, 2.0, 5.0]


def grid(key: str) -> np.ndarray:
    """Rows = severity (top→bottom: 5,2,1,0), cols = dose (0,0.5,2,5)."""
    g = np.zeros((len(SEVS), len(DOSES)))
    for i, s in enumerate(reversed(SEVS)):
        for j, d in enumerate(DOSES):
            cell = data["cells"].get(f"{d}|{s}", {}).get("endpoints", {})
            g[i, j] = cell.get(key, {}).get("mean", np.nan)
    return g


nfkb = grid("NFkB_p65_final")
ros = grid("ROS_final")
gsh = grid("Glutathione_final")  # redox buffer — the third axis with real variation

fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.2), constrained_layout=True)

panels = [
    (axes[0], nfkb, "NF$\\kappa$B p65", "viridis_r", ".2f"),
    (axes[1], ros, "Reactive O species", "magma_r", ".0f"),
    (axes[2], gsh, "Glutathione", "YlGn", ".0f"),
]

xlabels = [f"{d:g}" for d in DOSES]
ylabels = [f"{s:g}" for s in reversed(SEVS)]

for ax, mat, title, cmap, fmt in panels:
    vmax = np.nanmax(mat) if np.nanmax(mat) > 0 else 1.0
    # pcolormesh (vector quads) instead of imshow (raster) — avoids Acrobat
    # "No sufficient data for an image" warnings on small heatmaps.
    nrows, ncols = mat.shape
    xedges = np.arange(ncols + 1) - 0.5
    yedges = np.arange(nrows + 1) - 0.5
    im = ax.pcolormesh(xedges, yedges, mat, cmap=cmap, vmin=0, vmax=vmax,
                       shading="flat", edgecolors="none", rasterized=False)
    ax.set_xticks(range(len(DOSES)))
    ax.set_xticklabels(xlabels)
    ax.set_yticks(range(len(SEVS)))
    ax.set_yticklabels(ylabels)
    ax.invert_yaxis()
    ax.set_xlabel("Maintenance dose")
    if ax is axes[0]:
        ax.set_ylabel("Disease severity")
    ax.set_title(title, fontsize=10)
    # Numeric cell labels
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            # Pick contrasting text colour
            norm = v / vmax if vmax > 0 else 0
            color = "white" if norm > 0.55 else "black"
            ax.text(j, i, format(v, fmt), ha="center", va="center",
                    color=color, fontsize=8)
    # Colorbar omitted — every cell carries a numeric label, and tiny
    # colorbar image strips trigger Acrobat "No sufficient data" warnings.

fig.savefig(OUT)
fig.savefig(OUT.with_suffix(".png"), dpi=160)
print(f"wrote {OUT}")
print(f"wrote {OUT.with_suffix('.png')}")
