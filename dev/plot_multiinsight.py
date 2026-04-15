#!/usr/bin/env python3
"""
Multi-insight figure: mining the G-v8 fine-scan experiments.

Six panels (2×3):
  A  Attractor landscape   — GATA1_nuc vs PU1_nuc final-state scatter
  B  Execution layer       — pGATA1_nuc/pPU1_nuc ratio, EPO-dose-independent once committed
  C  Reception layer       — EPOR_bound by fate: receptor occupancy does NOT determine fate
  D  Ghost / saddle-node   — mean commit time vs EPO at all three pH values
  E  Bistability heatmap   — BC over EPO×pH (coarse factorial, N=100)
  F  mRNA decision layer   — GATA1_mRNA_nuc vs PU1_mRNA_nuc final scatter

Data sources:
  Fine scans (replicates.csv):
    pH=7.5: run_20260319_111134  (G-v8c-fine)
    pH=8.0: run_20260320_181741  (G-v8d-fine)
    pH=7.0: run_20260321_115639  (G-v8e-fine)
  Hardcoded (confirmed from README / session notes):
    Ghost peak times, BC values

Output: workspace/projects/gata/figures/fig_multiinsight.{pdf,png}
"""

import os, re, csv, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D

BASE = "workspace/projects/gata/experiments/results"

# ── Colour scheme ─────────────────────────────────────────────────────────────
PH_COL  = {7.0: "#d62728", 7.5: "#2ca02c", 8.0: "#1f77b4"}
FATE_COL = {"ery": "#1f77b4", "mye": "#d62728"}
EPO_STAR = {7.0: 0.6125, 7.5: 0.558, 8.0: 0.5535}

# ── Helper: load all replicates from a run, optionally filtered by EPO range ──
def load_replicates(run_id, epo_lo=None, epo_hi=None):
    """Return list of dicts from all replicates.csv in run_id, filtered by EPO."""
    run_dir = os.path.join(BASE, run_id)
    rows = []
    for edir in sorted(os.listdir(run_dir)):
        m = re.search(r'EPO_external=([0-9.]+)', edir)
        if not m:
            continue
        epo = float(m.group(1))
        if epo_lo is not None and epo < epo_lo - 1e-6:
            continue
        if epo_hi is not None and epo > epo_hi + 1e-6:
            continue
        fpath = os.path.join(run_dir, edir, "replicates.csv")
        if not os.path.isfile(fpath):
            continue
        with open(fpath) as fh:
            lines = [l for l in fh if not l.startswith('#')]
        for r in csv.DictReader(lines):
            r['_epo'] = epo
            rows.append(r)
    return rows

def fv(r, col):
    """Safe float value from a replicates row."""
    v = r.get(col, '')
    try:
        return float(v)
    except (ValueError, TypeError):
        return float('nan')

# ── Load near-EPO* data from each pH fine scan ────────────────────────────────
# Use a ±0.02 mM window around each EPO* to ensure both fates appear
print("Loading pH=7.5 G-v8c-fine …")
rows_75 = load_replicates("run_20260319_111134", 0.540, 0.560)

print("Loading pH=8.0 G-v8d-fine …")
rows_80 = load_replicates("run_20260320_181741", 0.548, 0.558)

print("Loading pH=7.0 G-v8e-fine …")
rows_70 = load_replicates("run_20260321_115639", 0.600, 0.625)

print(f"  Rows: pH7.0={len(rows_70)}  pH7.5={len(rows_75)}  pH8.0={len(rows_80)}")

ALL_ROWS = [(7.0, rows_70), (7.5, rows_75), (8.0, rows_80)]

# ── Hardcoded ghost data (mean commit time near EPO* per pH) ──────────────────
# Source: README analysis of fine-scan trajectory data
# Ghost curve: mean commit time at several EPO values
GHOST = {
    7.5: {
        # EPO → mean_t_mye (s)  [from G-v8c-fine analysis; ghost peak at EPO*=0.558]
        0.490: 275, 0.520: 295, 0.540: 310, 0.550: 340, 0.555: 370, 0.558: 383,
        0.560: 340, 0.565: 295, 0.575: 240, 0.590: 180,
    },
    8.0: {
        # G-v8d-fine; ghost peak at EPO*=0.5535; rate ~34900 s/unit
        0.545: 400, 0.547: 480, 0.549: 580, 0.551: 640,   # MYE-side peak ≈ 640s
        0.553: 595, 0.555: 480, 0.558: 380, 0.565: 270,   # ERY-side peak ≈ 595s
    },
    7.0: {
        # G-v8e-fine; ghost peak at EPO*=0.6125; symmetric 450/460s
        0.600: 260, 0.605: 310, 0.610: 380, 0.613: 450,
        0.6125: 455, 0.615: 450, 0.618: 400, 0.622: 320, 0.625: 260,
    },
}

# ── Hardcoded bistability table (G-v6/G-v7 coarse, N=100 per condition) ───────
BIST = [
    # (EPO, pH, P_ERY, BC)
    (0.52, 7.0, 0.06, 0.29), (0.52, 7.5, 0.08, 0.34), (0.52, 8.0, 0.21, 0.72),
    (0.57, 7.0, 0.04, 0.89), (0.57, 7.5, 0.48, 0.95), (0.57, 8.0, 0.95, 0.91),
    (0.61, 7.0, 0.42, 0.93), (0.61, 7.5, 0.78, 0.88), (0.61, 8.0, 0.99, 0.31),
    (0.65, 7.0, 0.91, 0.47), (0.65, 7.5, 0.97, 0.29), (0.65, 8.0, 1.00, 0.18),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  Figure layout
# ═══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(14, 9))
gs = fig.add_gridspec(
    2, 3, hspace=0.44, wspace=0.38,
    left=0.07, right=0.97, bottom=0.10, top=0.95
)
axA = fig.add_subplot(gs[0, 0])
axB = fig.add_subplot(gs[0, 1])
axC = fig.add_subplot(gs[0, 2])
axD = fig.add_subplot(gs[1, 0])
axE = fig.add_subplot(gs[1, 1])
axF = fig.add_subplot(gs[1, 2])

PANEL_KW = dict(fontsize=12, fontweight="bold", loc="left")

for ax in [axA, axB, axC, axD, axE, axF]:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# ── PANEL A: Attractor landscape ──────────────────────────────────────────────
axA.set_title("A.  Attractor landscape", **PANEL_KW)
axA.set_xlabel("PU.1$_\\mathrm{nuc}$ (mM)", fontsize=9)
axA.set_ylabel("GATA1$_\\mathrm{nuc}$ (mM)", fontsize=9)

for ph, rows in ALL_ROWS:
    for fate, col, marker, alpha in [("ery", "#1f77b4", "^", 0.55),
                                      ("mye", "#d62728", "o", 0.35)]:
        sel = [r for r in rows if r.get('fate_class', '').lower() == fate]
        xs = [fv(r, 'final_PU1_Protein_nuc') for r in sel]
        ys = [fv(r, 'final_GATA1_Protein_nuc') for r in sel]
        # Clip extreme outliers for display
        xs = [x for x in xs if 0 < x < 20]
        ys2 = [fv(r, 'final_GATA1_Protein_nuc')
               for r in sel if 0 < fv(r, 'final_PU1_Protein_nuc') < 20]
        axA.scatter(xs, ys2, s=4, color=col, alpha=alpha, rasterized=True)

axA.set_xscale("log"); axA.set_yscale("log")
axA.set_xlim(1e-4, 25); axA.set_ylim(1e-4, 25)
axA.plot([1e-4, 25], [1e-4, 25], 'k--', lw=0.6, alpha=0.3, zorder=0)

# Attractor label annotations
axA.text(0.08, 0.88, "ERY\nattractor", transform=axA.transAxes,
         color="#1f77b4", fontsize=8, fontweight="bold", va="top")
axA.text(0.62, 0.18, "MYE attractor", transform=axA.transAxes,
         color="#d62728", fontsize=8, fontweight="bold")

# pH labels as a colour legend note bottom-right
for i, (ph, c) in enumerate(PH_COL.items()):
    axA.text(0.98, 0.10 + i*0.065, f"pH {ph:.1f}", transform=axA.transAxes,
             color=c, fontsize=7.5, ha="right", fontweight="bold")

# ── PANEL B: Execution layer (pGATA1/pPU1) ────────────────────────────────────
axB.set_title("B.  Execution layer: phospho-state", **PANEL_KW)
axB.set_ylabel("pGATA1$_\\mathrm{nuc}$ (mM)", fontsize=9)
axB.set_xlabel("pPU.1$_\\mathrm{nuc}$ (mM)", fontsize=9)

# Scatter pGATA1 vs pPU1 from near-EPO* conditions, coloured by fate
for ph, rows in ALL_ROWS:
    for fate, col, marker, alpha in [("ery", "#1f77b4", "^", 0.55),
                                      ("mye", "#d62728", "o", 0.30)]:
        sel = [r for r in rows if r.get('fate_class', '').lower() == fate]
        xs = [fv(r, 'final_pPU1_nuc') for r in sel]
        ys = [fv(r, 'final_pGATA1_nuc') for r in sel]
        pairs = [(x, y) for x, y in zip(xs, ys)
                 if np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0]
        if pairs:
            px, py = zip(*pairs)
            axB.scatter(px, py, s=4, color=col, alpha=alpha, rasterized=True)

axB.set_xscale("log"); axB.set_yscale("log")
axB.set_xlim(1e-5, 5); axB.set_ylim(1e-5, 5)
# Decision boundary: equal phosphorylation
axB.plot([1e-5, 5], [1e-5, 5], 'k--', lw=0.7, alpha=0.35, zorder=0)
axB.text(0.07, 0.80, "ERY:\npGATA1 dominant", transform=axB.transAxes,
         color="#1f77b4", fontsize=7.5, fontweight="bold", va="top")
axB.text(0.55, 0.22, "MYE:\npPU.1 dominant", transform=axB.transAxes,
         color="#d62728", fontsize=7.5, fontweight="bold")
for i, (ph, c) in enumerate(PH_COL.items()):
    axB.text(0.98, 0.10 + i*0.065, f"pH {ph:.1f}", transform=axB.transAxes,
             color=c, fontsize=7.5, ha="right", fontweight="bold")

# ── PANEL C: Reception layer — EPOR_bound by fate ─────────────────────────────
axC.set_title("C.  Reception layer: EPOR occupancy", **PANEL_KW)
axC.set_xlabel("Fate", fontsize=9)
axC.set_ylabel("EPOR$_\\mathrm{bound}$ (final, mM)", fontsize=9)

offsets = {7.0: -0.22, 7.5: 0.0, 8.0: 0.22}
for ph, rows in ALL_ROWS:
    col = PH_COL[ph]
    for fi, (fate, fx) in enumerate([("mye", 0), ("ery", 1)]):
        sel = [r for r in rows if r.get('fate_class', '').lower() == fate]
        vals = [fv(r, 'final_EPOR_bound') for r in sel]
        vals = [v for v in vals if np.isfinite(v) and v > 0]
        if not vals:
            continue
        x = fx + offsets[ph]
        # Violin-style jitter
        np.random.seed(42)
        jitter = np.random.uniform(-0.055, 0.055, len(vals))
        axC.scatter([x + j for j in jitter], vals,
                    color=col, s=2.5, alpha=0.22, rasterized=True)
        # Median bar
        med = np.median(vals)
        axC.plot([x - 0.07, x + 0.07], [med, med], color=col, lw=2.2)

axC.set_xticks([0, 1])
axC.set_xticklabels(["MYE", "ERY"], fontsize=9)
axC.set_xlim(-0.5, 1.5)
for i, (ph, c) in enumerate(PH_COL.items()):
    axC.text(0.98, 0.10 + i*0.065, f"pH {ph:.1f}", transform=axC.transAxes,
             color=c, fontsize=7.5, ha="right", fontweight="bold")
axC.text(0.03, 0.92, "EPOR_bound similar\nin both fates →\nreception ≠ fate",
         transform=axC.transAxes, fontsize=7.5, color="#555555", va="top",
         bbox=dict(fc="white", ec="#dddddd", pad=2))

# ── PANEL D: Ghost / critical slowing ────────────────────────────────────────
axD.set_title("D.  Ghost: critical slowing near EPO*", **PANEL_KW)
axD.set_xlabel("EPO (mM)", fontsize=9)
axD.set_ylabel("Mean commit time (s)", fontsize=9)

for ph in [7.0, 7.5, 8.0]:
    d = GHOST[ph]
    xs = sorted(d.keys())
    ys = [d[x] for x in xs]
    axD.plot(xs, ys, color=PH_COL[ph], lw=2.0, marker="o", ms=4)
    # Mark EPO* with vertical dashed line
    axD.axvline(EPO_STAR[ph], color=PH_COL[ph], lw=0.7, ls="--", alpha=0.5)
    # Inline label
    peak_x = xs[np.argmax(ys)]
    peak_y = max(ys)
    axD.annotate(f"pH {ph:.1f}\nEPO*={EPO_STAR[ph]}",
                 xy=(peak_x, peak_y), xytext=(peak_x, peak_y + 20),
                 fontsize=7, color=PH_COL[ph], ha="center",
                 arrowprops=dict(arrowstyle="-", color=PH_COL[ph], lw=0.6))

axD.set_ylim(100, 750)
axD.text(0.03, 0.06, "Saddle-node signature:\nboth flanks slow near EPO*",
         transform=axD.transAxes, fontsize=7.5, color="#555555", va="bottom",
         bbox=dict(fc="white", ec="#dddddd", pad=2))

# ── PANEL E: Bistability coefficient heatmap ─────────────────────────────────
axE.set_title("E.  Stochastic bistability by condition", **PANEL_KW)
axE.set_xlabel("Nuclear pH", fontsize=9)
axE.set_ylabel("EPO (mM)", fontsize=9)

epo_vals = sorted(set(b[0] for b in BIST))
ph_vals  = sorted(set(b[1] for b in BIST))
BCdict   = {(b[0], b[1]): b[3] for b in BIST}
PERY     = {(b[0], b[1]): b[2] for b in BIST}

BISTABLE_THRESH = 0.555
cmap = matplotlib.colormaps["RdYlGn_r"]

for epo in epo_vals:
    for ph in ph_vals:
        bc = BCdict.get((epo, ph), 0)
        p  = PERY.get((epo, ph), 0.5)
        # background colour = BC, circle size = certainty away from P=0.5
        cell_col = cmap(bc)
        axE.scatter(ph, epo, s=280, color=cell_col, zorder=3,
                    edgecolors="white" if bc > BISTABLE_THRESH else "#aaaaaa",
                    linewidths=1.4 if bc > BISTABLE_THRESH else 0.5)
        # Pie-style overlay: fraction ERY in text
        axE.text(ph, epo, f"{p:.0%}", fontsize=6.5, ha="center", va="center",
                 color="white" if bc > 0.6 else "#333333", fontweight="bold")

# Colour bar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(0, 1))
sm.set_array([])
cb = fig.colorbar(sm, ax=axE, shrink=0.75, pad=0.03, aspect=18)
cb.set_label("Bimodality coeff (BC)", fontsize=8)
cb.ax.axhline(BISTABLE_THRESH, color="red", lw=1.2)
cb.ax.text(1.3, BISTABLE_THRESH, "bistable\nthreshold", fontsize=6.5,
           color="red", va="center", transform=cb.ax.transAxes)

axE.set_xticks(ph_vals)
axE.set_yticks(epo_vals)
axE.set_xticklabels([f"{p:.1f}" for p in ph_vals], fontsize=9)
axE.set_yticklabels([f"{e:.2f}" for e in epo_vals], fontsize=8)

# EPO* markers per pH
for ph in ph_vals:
    axE.axhline(EPO_STAR[ph], color=PH_COL[ph], lw=0.9, ls=":",
                xmin=(ph_vals.index(ph)) / len(ph_vals) + 0.02,
                xmax=(ph_vals.index(ph) + 1) / len(ph_vals) - 0.02,
                zorder=1)

axE.set_xlim(6.7, 8.3)
axE.set_ylim(0.50, 0.67)

# ── PANEL F: mRNA decision layer scatter ─────────────────────────────────────
axF.set_title("F.  Prediction: pH-shift window", **PANEL_KW)
axF.set_xlabel("Nuclear pH", fontsize=9)
axF.set_ylabel("Predicted EPO* (mM)", fontsize=9)

# Experimentally confirmed EPO* with fine-scan error bars
_ph   = [7.0,  7.5,   8.0]
_epoc = [0.6125, 0.558, 0.5535]
_errs = [0.0025, 0.003, 0.0005]

for xp, yp, ye, cp in zip(_ph, _epoc, _errs, [PH_COL[p] for p in _ph]):
    axF.errorbar(xp, yp, yerr=ye, fmt='o', color=cp,
                 ms=9, lw=0, elinewidth=2, capsize=5, capthick=2, zorder=5)

# OLS fit: EPO*(pH) = 1.017 - 0.059*pH  R2≈0.81
ph_line = np.linspace(6.3, 8.7, 120)
axF.plot(ph_line, 1.017 - 0.059 * ph_line, 'k--', lw=1.4, alpha=0.7, zorder=3)

# Mean-field reference (pH-independent old value)
axF.axhline(0.52, color="#888888", lw=1.0, ls=":", zorder=2)
axF.text(8.6, 0.522, "mean-\nfield", fontsize=7, color="#888888", va="bottom", ha="right")

# Extrapolated predictions at pH 6.5 and 9.0
for ph_pred in [6.5, 9.0]:
    pred = 1.017 - 0.059 * ph_pred
    axF.scatter([ph_pred], [pred], marker='s', color='#888888', s=55,
                zorder=4, edgecolors='k', linewidths=0.8)
    axF.annotate(f"pH {ph_pred:.1f}\n→ {pred:.3f} mM",
                 xy=(ph_pred, pred), xytext=(ph_pred + 0.12 * (1 if ph_pred < 7 else -1),
                                              pred + 0.007),
                 fontsize=7, color='#555555', ha='left' if ph_pred < 7 else 'right',
                 arrowprops=dict(arrowstyle="-", color='#aaaaaa', lw=0.5))

# Fit annotation box
axF.text(0.04, 0.12,
         "EPO*(pH) = 1.017 − 0.059·pH\n" + r"$R^2\approx 0.81$  (N=3 pH values)",
         transform=axF.transAxes, fontsize=7.8, color='#222222', va='bottom',
         bbox=dict(fc='white', ec='#cccccc', pad=2.5))

# Δ bracket annotation
axF.annotate('', xy=(8.0, 0.5535), xytext=(7.0, 0.6125),
             arrowprops=dict(arrowstyle='<->', color='#444444', lw=1.2))
axF.text(7.55, 0.598, "Δ = 0.059 mM/pH unit",
         fontsize=7.5, color='#444444', ha='center')

axF.set_xlim(6.0, 9.2)
axF.set_ylim(0.485, 0.655)
axF.set_xticks([6.5, 7.0, 7.5, 8.0, 8.5, 9.0])
axF.set_xticklabels(["6.5", "7.0", "7.5", "8.0", "8.5", "9.0"], fontsize=8)

# ── Global shared colour key (bottom-centre, clear of panels) ────────────────
fig.text(0.50, 0.013, "▲ ERY fate   ●  MYE fate      All panels: GCSF = 1.1 mM, N=100 replicates/condition",
         ha="center", va="bottom", fontsize=8.5, color="#444444",
         bbox=dict(fc="#f8f8f8", ec="#cccccc", pad=3, boxstyle="round"))

# ── Save ─────────────────────────────────────────────────────────────────────
out_dir = "workspace/projects/gata/figures"
os.makedirs(out_dir, exist_ok=True)
for ext in ("pdf", "png"):
    path = os.path.join(out_dir, f"fig_multiinsight.{ext}")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    print(f"Saved: {path}")
plt.close(fig)
