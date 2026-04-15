#!/usr/bin/env python3
"""
Waddington landscape + dose-response bifurcation figure.

Two-panel figure:
  Panel A — Waddington pseudo-potential double-well at EPO=0.57 mM for
             three nuclear pH values, showing how the same cytokine dose
             produces opposite majority fates at the pH extremes.
  Panel B — Sigmoidal P(ERY) dose-response curves for pH=7.0/7.5/8.0,
             fitted through confirmed EPO* values (G-v8 fine scans) and
             the coarse bistability table data points.

Data sources:
  Fine-scan EPO* (Mar 21 2026):
      pH=7.0: EPO*=0.6125 ±0.0025  (G-v8e-fine)
      pH=7.5: EPO*=0.558  ±0.003   (G-v8c-fine)
      pH=8.0: EPO*=0.5535 ±0.0005  (G-v8d-fine)
  Coarse bistability table (G-v6/G-v7 factorial, N=100, T=21600 s):
      EPO=0.52 → P(ERY): 0.06/0.08/0.21 (pH 7.0/7.5/8.0)
      EPO=0.57 → P(ERY): 0.04/0.48/0.95
      EPO=0.61 → P(ERY): 0.42/0.78/0.99
      EPO=0.65 → P(ERY): 0.91/0.97/1.00

Output: workspace/projects/gata/figures/fig_waddington_bifurcation.{pdf,png}
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from scipy.optimize import brentq
import os

# ── Colour palette (pH axis: red=acidic, green=neutral, blue=alkaline) ───────
PH_COLORS = {7.0: "#d62728", 7.5: "#2ca02c", 8.0: "#1f77b4"}
PH_LABELS = {7.0: "pH 7.0 (acidic)", 7.5: "pH 7.5 (neutral)", 8.0: "pH 8.0 (alkaline)"}

# ── Confirmed EPO* values (G-v8 fine scans) ─────────────────────────────────
EPO_STAR  = {7.0: 0.6125, 7.5: 0.558, 8.0: 0.5535}
EPO_ERR   = {7.0: 0.0025, 7.5: 0.003, 8.0: 0.0005}

# ── Coarse bistability table data ────────────────────────────────────────────
COARSE = {
    7.0: [(0.52, 0.06), (0.57, 0.04), (0.61, 0.42), (0.65, 0.91)],
    7.5: [(0.52, 0.08), (0.57, 0.48), (0.61, 0.78), (0.65, 0.97)],
    8.0: [(0.52, 0.21), (0.57, 0.95), (0.61, 0.99), (0.65, 1.00)],
}

# ── Logistic helper ───────────────────────────────────────────────────────────
def logistic(epo, epo_star, k):
    return 1.0 / (1.0 + np.exp(-k * (epo - epo_star)))

# Fit steepness k for each pH from the coarse data + confirmed EPO*
from scipy.optimize import curve_fit

FIT_K = {}
EPO_RANGE = np.linspace(0.49, 0.72, 400)

for ph in [7.0, 7.5, 8.0]:
    pts = COARSE[ph]
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    epo_s = EPO_STAR[ph]
    try:
        popt, _ = curve_fit(
            lambda epo, k: logistic(epo, epo_s, k),
            xs, ys, p0=[30.0], bounds=(1, 200), maxfev=4000
        )
        FIT_K[ph] = popt[0]
    except Exception:
        FIT_K[ph] = 30.0

# ── Waddington pseudo-potential ───────────────────────────────────────────────
# V(x, α) = (x² − 1)² + α·x
# x ∈ [−1, +1]: −1 = MYE attractor, +1 = ERY attractor
# α is the tilt: α>0 → MYE-biased, α<0 → ERY-biased
# Calibrate α from P(ERY) using Boltzmann:
#   P(ERY) = exp(−V(+1)/T) / [exp(−V(+1)/T) + exp(−V(−1)/T)]
#         = 1 / (1 + exp((V(+1)−V(−1))/T))
# V(+1) = 0 + α  →  ΔV = V(+1)−V(−1) = α − (−α) = 2α
# P(ERY) = 1/(1+exp(2α/T)) with T=0.5 (noise amplitude)
# Solving: α = −T·ln(P/(1−P))

T_NOISE = 0.5  # noise temperature; sets sharpness of the well asymmetry

def alpha_from_p(p_ery, T=T_NOISE):
    eps = 1e-6
    p = np.clip(p_ery, eps, 1 - eps)
    return -T * np.log(p / (1.0 - p))

def waddington(x, alpha):
    return (x**2 - 1.0)**2 + alpha * x

EPO_PROBE = 0.57  # "diagnostic" EPO concentration for the landscape panel
X_AXIS = np.linspace(-1.7, 1.7, 500)

p_at_probe = {ph: logistic(EPO_PROBE, EPO_STAR[ph], FIT_K[ph]) for ph in [7.0, 7.5, 8.0]}
alpha_probe = {ph: alpha_from_p(p_at_probe[ph]) for ph in [7.0, 7.5, 8.0]}

# Find minima of V(x, α) for each pH
def find_minima(alpha):
    """Return (x_mye, x_ery) potential-well minima."""
    # V'(x) = 4x(x²−1) + α = 0  → solve numerically
    dV = lambda x: 4*x*(x**2 - 1) + alpha
    roots = []
    xs = np.linspace(-1.6, 1.6, 1000)
    for i in range(len(xs)-1):
        if dV(xs[i]) * dV(xs[i+1]) < 0:
            try:
                roots.append(brentq(dV, xs[i], xs[i+1]))
            except Exception:
                pass
    # Classify: local minima have V''(x) > 0
    dV2 = lambda x: 4*(3*x**2 - 1)
    minima = [r for r in roots if dV2(r) > 0]
    return sorted(minima)

# ── Figure setup ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(11.5, 4.8))
gs = fig.add_gridspec(1, 2, wspace=0.34, left=0.07, right=0.97, bottom=0.13, top=0.88)

ax_wad = fig.add_subplot(gs[0])
ax_sig = fig.add_subplot(gs[1])

# ═══════════════════════════════════════════════════════════════════════
#  PANEL A — Waddington landscapes
# ═══════════════════════════════════════════════════════════════════════

LANDSCAPE_YMAX = 1.45
LANDSCAPE_YMIN = -0.55

for ph in [7.0, 7.5, 8.0]:
    a = alpha_probe[ph]
    V = waddington(X_AXIS, a)
    col = PH_COLORS[ph]
    # Clip to display window so high walls don't blow the y scale
    mask = (V >= LANDSCAPE_YMIN - 0.3) & (V <= LANDSCAPE_YMAX + 0.5)
    ax_wad.plot(X_AXIS[mask], V[mask], color=col, linewidth=2.2, zorder=3)
    mins = find_minima(a)
    if not mins:
        # Monostable: find the single global minimum on a fine grid
        xg = np.linspace(-1.5, 1.5, 2000)
        vg = waddington(xg, a)
        xm_only = xg[np.argmin(vg)]
        mins = [xm_only]
    for xm in mins:
        vm = waddington(xm, a)
        # Ball radius scales with population fraction in that well
        is_ery = xm > 0
        frac = p_at_probe[ph] if is_ery else (1 - p_at_probe[ph])
        radius = 0.055 + 0.055 * frac   # slightly larger for clarity
        circ = plt.Circle((xm, vm + radius + 0.03), radius,
                           color=col, zorder=5, linewidth=0.8,
                           ec="white")
        ax_wad.add_patch(circ)

# Shade MYE and ERY basins  
ax_wad.axvspan(-1.7, 0, color="#fee0d2", alpha=0.30, zorder=1)
ax_wad.axvspan(0,  1.7, color="#deebf7", alpha=0.30, zorder=1)
ax_wad.axvline(0, color="#999999", linewidth=0.8, linestyle="--", zorder=2)

# Basin labels
ax_wad.text(-1.35, LANDSCAPE_YMAX * 0.92, "MYE\nbasin", fontsize=9.5,
            color="#a63603", ha="center", va="top", style="italic")
ax_wad.text( 1.35, LANDSCAPE_YMAX * 0.92, "ERY\nbasin", fontsize=9.5,
            color="#08519c", ha="center", va="top", style="italic")

# Saddle annotation at x≈0 for pH 7.5 (near-symmetric) — point to the barrier top
a75 = alpha_probe[7.5]
xs_arr = np.linspace(-0.3, 0.3, 200)
saddle_x = xs_arr[np.argmax(waddington(xs_arr, a75))]
saddle_v = waddington(saddle_x, a75)
ax_wad.annotate("unstable\nfixed point", xy=(saddle_x, saddle_v),
                xytext=(-1.1, saddle_v + 0.35), fontsize=7.5,
                color="#555555",
                arrowprops=dict(arrowstyle="-|>", color="#888888",
                                lw=0.9, mutation_scale=8),
                ha="left")

# Inline pH labels positioned near each curve's MYE-side wall
INLINE_POS = {7.0: (0.95, 1.32), 7.5: (-1.48, 0.48), 8.0: (-1.48, 1.32)}
INLINE_HA  = {7.0: "left",       7.5: "left",         8.0: "left"}
for ph in [7.0, 7.5, 8.0]:
    a = alpha_probe[ph]
    xi, yi = INLINE_POS[ph]
    pct = int(round(p_at_probe[ph] * 100))
    ax_wad.text(xi, yi, f"pH {ph:.1f}  P(ERY)={pct}%",
                color=PH_COLORS[ph], fontsize=8.0,
                ha=INLINE_HA[ph], va="bottom", fontweight="bold",
                bbox=dict(fc="white", ec="none", pad=1.0, alpha=0.7))

ax_wad.set_xlim(-1.7, 1.7)
ax_wad.set_ylim(LANDSCAPE_YMIN, LANDSCAPE_YMAX)
ax_wad.set_xlabel("Cell commitment state  (← MYE | ERY →)", fontsize=10)
ax_wad.set_ylabel("Pseudo-potential  (a.u.)", fontsize=10)
ax_wad.set_title(f"A.  Waddington landscape at EPO = {EPO_PROBE} mM", fontsize=11, loc="left", fontweight="bold")
ax_wad.set_xticks([])   # conceptual axis — no numeric ticks
ax_wad.yaxis.set_tick_params(labelsize=9)
ax_wad.set_xlim(-1.7, 1.7)
ax_wad.spines["right"].set_visible(False)
ax_wad.spines["bottom"].set_linewidth(1.2)

# EPO probe annotation
ax_wad.text(0.01, 0.03,
            f"GCSF = 1.1 mM  |  same EPO = {EPO_PROBE} mM\nstochastic N = 100 per condition",
            transform=ax_wad.transAxes, fontsize=7.5, color="#555555",
            va="bottom")

# ═══════════════════════════════════════════════════════════════════════
#  PANEL B — Dose-response sigmoid curves
# ═══════════════════════════════════════════════════════════════════════

for ph in [7.0, 7.5, 8.0]:
    col = PH_COLORS[ph]
    epo_s = EPO_STAR[ph]
    k = FIT_K[ph]

    # Fitted sigmoid
    ax_sig.plot(EPO_RANGE, logistic(EPO_RANGE, epo_s, k),
                color=col, linewidth=2.2, zorder=3)

    # Fine-scan EPO* marker with error bar
    ax_sig.errorbar(epo_s, 0.5, xerr=EPO_ERR[ph],
                    fmt="D", color=col, markersize=6, capsize=4,
                    linewidth=1.5, capthick=1.5, zorder=6)

    # Vertical guide to EPO* at P=0.5
    ax_sig.plot([epo_s, epo_s], [0, 0.5], color=col,
                linewidth=0.9, linestyle=":", zorder=2)

    # Coarse data scatter
    for (epo_pt, p_pt) in COARSE[ph]:
        ax_sig.scatter(epo_pt, p_pt, color=col, s=28, marker="o",
                       zorder=5, edgecolors="white", linewidths=0.5)

    # EPO* label along x-axis
    ax_sig.text(epo_s, -0.07, f"{epo_s:.4f}", fontsize=7.5, color=col,
                ha="center", va="top", rotation=35)

    # Inline pH label on each sigmoid (at P≈0.85, right side of curve)
    x_label = epo_s + 0.025
    if x_label > 0.70:
        x_label = epo_s - 0.025
    ax_sig.text(x_label, 0.85, f"pH {ph:.1f}",
                color=col, fontsize=8.5, fontweight="bold",
                ha="left" if (epo_s + 0.025 <= 0.70) else "right", va="center")

# P=0.5 reference
ax_sig.axhline(0.5, color="#888888", linewidth=0.8, linestyle="--", zorder=1)
ax_sig.text(0.706, 0.515, "P = 0.5", fontsize=8, color="#888888")

# Mean-field EPO*
ax_sig.axvline(0.52, color="#d62728", linewidth=0.9, linestyle="-.",
               alpha=0.6, zorder=1)
ax_sig.text(0.521, 0.92, "mean-field\nEPO*=0.52", fontsize=7, color="#d62728",
            alpha=0.8, va="top")

# Shade the "pH-sensitive window"
ax_sig.axvspan(EPO_STAR[8.0] - EPO_ERR[8.0], EPO_STAR[7.0] + EPO_ERR[7.0],
               color="#ffffb2", alpha=0.45, zorder=0)
# Window label
ax_sig.text((EPO_STAR[8.0] + EPO_STAR[7.0]) / 2, 0.07,
            "pH-sensitive\nwindow", fontsize=7.5, color="#888800",
            ha="center", va="bottom")

ax_sig.set_xlim(0.498, 0.715)
ax_sig.set_ylim(-0.05, 1.08)
ax_sig.set_xlabel("EPO concentration (mM)", fontsize=10)
ax_sig.set_ylabel("P(ERY)  —  erythroid commitment fraction", fontsize=10)
ax_sig.set_title("B.  Dose-response curves by nuclear pH", fontsize=11, loc="left", fontweight="bold")
ax_sig.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.04))
ax_sig.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.01))
ax_sig.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.2))
ax_sig.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
ax_sig.tick_params(which="both", direction="in", top=True, right=True, labelsize=9)
ax_sig.spines["top"].set_visible(False)
ax_sig.spines["right"].set_visible(False)

# ── Save ─────────────────────────────────────────────────────────────────────
out_dir = "workspace/projects/gata/figures"
os.makedirs(out_dir, exist_ok=True)
for ext in ("pdf", "png"):
    path = os.path.join(out_dir, f"fig_waddington_bifurcation.{ext}")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    print(f"Saved: {path}")
plt.close(fig)
