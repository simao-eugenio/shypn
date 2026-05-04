"""Figure 2: Waddington pseudo-potential with the three model basins of attraction.

Two-axis landscape over (oxidative depletion, amyloid load). Three minima:
  H  Healthy           low GSH-depletion, low oligomer
  A  Amyloid-disease   moderate GSH-depletion, high oligomer (frozen v3 baseline)
  R  Redox-collapse    severe GSH-depletion, low oligomer (alt attractor, §disc-bistability)

Clean: one contour panel + three labelled minima. No arrows, no legends.
The surrounding manuscript text carries the interpretation.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

OUT = Path(__file__).resolve().parents[1] / "figures" / "fig_waddington_three_basins.pdf"

# Axes:
#   x  oxidative depletion  in [0, 1]   (0 = replete GSH, 1 = depleted)
#   y  amyloid oligomer     in [0, 1]   (0 = cleared,    1 = max)
# Three basin centres (x*, y*, depth, sigma_x, sigma_y)
BASINS = [
    ("H", 0.10, 0.08, 1.00, 0.13, 0.12),  # Healthy
    ("A", 0.55, 0.78, 1.20, 0.16, 0.16),  # Amyloid-disease (deepest, frozen baseline)
    ("R", 0.92, 0.10, 0.90, 0.10, 0.13),  # Redox-collapse
]

x = np.linspace(0, 1, 400)
y = np.linspace(0, 1, 400)
X, Y = np.meshgrid(x, y)


def potential(X, Y):
    # Smooth quadratic bowl pushes states inward (acts as boundary).
    U = 0.6 * ((X - 0.5) ** 4 + (Y - 0.5) ** 4) * 6
    # Subtract gaussians at each basin centre.
    for _, mx, my, depth, sx, sy in BASINS:
        U -= depth * np.exp(-((X - mx) ** 2 / (2 * sx ** 2)
                              + (Y - my) ** 2 / (2 * sy ** 2)))
    # Saddle ridge between A and R (oxidative-collapse barrier).
    ridge = 0.45 * np.exp(-((X - 0.78) ** 2 / 0.005 + (Y - 0.45) ** 2 / 0.18))
    U += ridge
    return U


U = potential(X, Y)

fig, ax = plt.subplots(figsize=(5.6, 4.6), constrained_layout=True)

cmap = LinearSegmentedColormap.from_list(
    "wadd", ["#2b3a55", "#3d6094", "#86a7c8", "#d6e0eb", "#f4eee2", "#e6c89a", "#b8743a"]
)
levels = np.linspace(U.min(), U.max(), 24)
cf = ax.contourf(X, Y, U, levels=levels, cmap=cmap, alpha=0.95)
ax.contour(X, Y, U, levels=12, colors="k", linewidths=0.35, alpha=0.45)

# Mark each basin minimum with a small dot + single-letter label.
for label, mx, my, *_ in BASINS:
    ax.plot(mx, my, "o", color="black", markersize=5,
            markerfacecolor="white", markeredgewidth=1.0)
    ax.annotate(label, xy=(mx, my), xytext=(8, 8),
                textcoords="offset points",
                fontsize=11, fontweight="bold")

ax.set_xlabel("Oxidative depletion  $1 - \\mathrm{GSH}/\\mathrm{GSH}_{\\max}$")
ax.set_ylabel("Amyloid oligomer load  (normalised)")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xticks([0, 0.5, 1])
ax.set_yticks([0, 0.5, 1])

cb = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("Pseudo-potential  $U$ (a.u.)")
cb.set_ticks([])

fig.savefig(OUT)
fig.savefig(OUT.with_suffix(".png"), dpi=160)
print(f"wrote {OUT}")
print(f"wrote {OUT.with_suffix('.png')}")
