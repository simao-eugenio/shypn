#!/usr/bin/env python3
"""Plot the EPO*(pH) bifurcation curve from G-v8 fine-scan results.

Confirmed values (Mar 21 2026):
    pH=7.0 → EPO* = 0.6125 ± 0.0025   (G-v8e-fine)
    pH=7.5 → EPO* = 0.558  ± 0.003    (G-v8c-fine)
    pH=8.0 → EPO* = 0.5535 ± 0.0005   (G-v8d-fine)

Output: workspace/projects/gata/figures/fig_bifurcation_curve.{pdf,png}
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

# ── Gold-standard EPO* values ────────────────────────────────────────────────
pH_vals  = np.array([7.0,    7.5,   8.0  ])
EPO_star = np.array([0.6125, 0.558, 0.5535])
EPO_err  = np.array([0.0025, 0.003, 0.0005])

# ── Linear fit (3-pt OLS) ────────────────────────────────────────────────────
slope, intercept = np.polyfit(pH_vals, EPO_star, 1)
pH_fit = np.linspace(6.7, 8.3, 300)
EPO_fit = slope * pH_fit + intercept
R2 = 1 - np.sum((EPO_star - (slope * pH_vals + intercept))**2) / \
         np.sum((EPO_star - EPO_star.mean())**2)

# ── Figure ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5.5, 4.2))

# Shaded error bands
ax.fill_between(
    pH_vals, EPO_star - EPO_err, EPO_star + EPO_err,
    color="#2171b5", alpha=0.18, zorder=2
)

# Linear fit
ax.plot(
    pH_fit, EPO_fit,
    color="#6baed6", linewidth=1.4, linestyle="--", zorder=3
)

# Data points with error bars
ax.errorbar(
    pH_vals, EPO_star, yerr=EPO_err,
    fmt="o", color="#08519c", markersize=7, capsize=5,
    linewidth=1.6, capthick=1.6, zorder=4
)

# Annotate points
labels = {
    7.0: ("G-v8e-fine", "right", 0.006),
    7.5: ("G-v8c-fine", "right", 0.006),
    8.0: ("G-v8d-fine", "right", 0.006),
}
for ph, (run, ha, dy) in labels.items():
    idx = list(pH_vals).index(ph)
    ax.annotate(
        f"{EPO_star[idx]:.4f} mM",
        xy=(ph, EPO_star[idx]),
        xytext=(ph + 0.12, EPO_star[idx] + dy),
        fontsize=8, color="#08519c",
        arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.8),
        ha="left", va="bottom"
    )

# Mean-field prediction line
ax.axhline(0.52, color="#d7301f", linewidth=1.1, linestyle=":",
           zorder=1)
# Net-flux label on plot
ax.text(6.72, 0.521, "net-flux EPO*", fontsize=7.5, color="#d7301f", va="bottom")

# Axes formatting
ax.set_xlabel("Nuclear pH", fontsize=11)
ax.set_ylabel("EPO* (mM)", fontsize=11)
ax.set_title("EPO Commitment Threshold vs Nuclear pH\n(GATA1/PU.1 model, GCSF = 1.1 mM, G-v8 fine scans)",
             fontsize=10)
ax.set_xlim(6.65, 8.45)
ax.set_ylim(0.50, 0.66)
ax.set_xticks([7.0, 7.5, 8.0])
ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.25))
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.02))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.01))
ax.tick_params(which="both", direction="in", top=True, right=True)
ax.tick_params(which="major", labelsize=10)
ax.grid(True, which="major", linestyle=":", linewidth=0.5, alpha=0.5)

# Slope annotation in plot area
slope_txt = f"Slope: {slope*1000:.1f} µM per pH unit"
ax.text(0.04, 0.08, slope_txt, transform=ax.transAxes,
        fontsize=8.5, color="#555555",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cccccc", lw=0.8))

# Ghost peak time annotation below each point
ghost_times = {7.0: "t_commit peak\n450s/460s",
               7.5: "383s",
               8.0: "640s/595s"}
for ph, txt in ghost_times.items():
    idx = list(pH_vals).index(ph)
    ax.annotate(
        txt,
        xy=(ph, EPO_star[idx] - EPO_err[idx]),
        xytext=(ph, EPO_star[idx] - EPO_err[idx] - 0.013),
        fontsize=6.5, color="#555555", ha="center", va="top",
        arrowprops=dict(arrowstyle="-", color="#cccccc", lw=0.6)
    )

ax.set_xlim(6.65, 8.45)

# ── Save ─────────────────────────────────────────────────────────────────────
out_dir = "workspace/projects/gata/figures"
os.makedirs(out_dir, exist_ok=True)
for ext in ("pdf", "png"):
    path = os.path.join(out_dir, f"fig_bifurcation_curve.{ext}")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    print(f"Saved: {path}")

plt.close(fig)
