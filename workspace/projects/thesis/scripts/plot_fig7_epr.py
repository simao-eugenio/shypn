#!/usr/bin/env python3
"""Figure 7 — Schnakenberg EPR decomposition and septation asymmetry.

Panel (a): Stacked bar chart of per-transition EPR contributions across the
           three conditions (N0=100 sub-critical, N0=1600 critical,
           N0=2200 super-critical), NET-T5 (run_20260707_152611, 300 reps).
           Shows KinA dominance (97.5%) and the stress-sensor relationship.
Panel (b): Septation firing rate, sporulating vs vegetative replicates at
           the critical condition (N0=1600), confirming 14.3x asymmetry.

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/plot_fig7_epr.py

Output: workspace/projects/thesis/manuscript/figures/fig7_epr.png
"""
import csv, math, pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RUN = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260707_152611")
OUT = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig7_epr.png")

kBT    = 1.380649e-23 * 310.15
dG_ATP = 57000.0 / 6.022e23
V_cell = 1e-15
NA     = 6.022e23
DURATION = 21600.0

DG = {
    "T_KinA_activation":          5 * dG_ATP / kBT,   # 116.3 kBT/firing
    "T_Spo0F_phosphorylation":    0.0,
    "T_Spo0F_dephos":             0.0,
    "T_Spo0A_phosphorylation":    0.0,
    "T_Spo0A_dephosphorylation":  0.0,
    "T_septation":                82 * dG_ATP / kBT,  # 1908 kBT/firing
    "T_SinI_synthesis":           5 * dG_ATP / kBT,   # 116.3 kBT/firing
}
TRANSITIONS = list(DG.keys())

def mean(v): return sum(v)/len(v) if v else 0.0

CONDS = {
    100:  "condition_[param]_INITIAL_NUTRIENTS_eq_100",
    1600: "condition_[param]_INITIAL_NUTRIENTS_eq_1600",
    2200: "condition_[param]_INITIAL_NUTRIENTS_eq_2200",
}

# ── Load firing rates and EPR ─────────────────────────────────────────────────
epr_by_cond   = {}
rates_by_cond = {}
spore_mask_by_cond = {}

for n0, cname in CONDS.items():
    rows = list(csv.DictReader(open(RUN/cname/"replicates.csv")))
    spore = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    spore_mask_by_cond[n0] = spore
    fire_rates = {}
    for t in TRANSITIONS:
        col = t + "_firings"
        rates = [float(r.get(col,0))/DURATION for r in rows]
        fire_rates[t] = rates
    rates_by_cond[n0] = fire_rates
    epr = {t: mean(fire_rates[t]) * DG[t] for t in TRANSITIONS}
    epr_by_cond[n0] = epr

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), sharey=False)

# Panel a: grouped bars per condition, stacked by transition contribution
CONDITIONS = [100, 1600, 2200]
LABELS = ["Sub-critical\n($N_0$=100)", "Critical\n($N_0$=1600)", "Super-critical\n($N_0$=2200)"]
x = np.arange(len(CONDITIONS))
width = 0.55

# Two meaningful non-zero groups: KinA and execution (sept+SinI)
kinA_epr  = [epr_by_cond[n]["T_KinA_activation"] for n in CONDITIONS]
sept_epr  = [epr_by_cond[n]["T_septation"] for n in CONDITIONS]
sinI_epr  = [epr_by_cond[n]["T_SinI_synthesis"] for n in CONDITIONS]
exec_epr  = [sept_epr[i] + sinI_epr[i] for i in range(3)]
total_epr = [kinA_epr[i] + exec_epr[i] for i in range(3)]

bars_kina = ax1.bar(x, kinA_epr, width, label=r"$T_{\rm KinA}$ (decision)", color="#1f77b4")
bars_exec = ax1.bar(x, exec_epr, width, bottom=kinA_epr, label=r"Execution ($T_{\rm sept}+T_{\rm SinI}$)", color="#ff7f0e")

# Percentage labels — KinA inside bar, execution above bar
for i, (k, e, tot) in enumerate(zip(kinA_epr, exec_epr, total_epr)):
    if tot > 1e-4:
        ax1.text(x[i], k/2, "%.0f%%" % (100*k/tot), ha='center', va='center',
                 fontsize=10, color='white', fontweight='bold')
        if e > 1e-4*tot:
            # Place label just inside the top of the axes regardless of bar height
            y_max = ax1.get_ylim()[1] if ax1.get_ylim()[1] > 0 else k + e + 0.1
            y_label = min(k + e + tot*0.03, y_max * 0.96)
            ax1.text(x[i], y_label, "%.0f%%" % (100*e/tot),
                     ha='center', va='top', fontsize=9, color='#cc5500', fontweight='bold')
    else:
        ax1.text(x[i], ax1.get_ylim()[1]*0.02 if ax1.get_ylim()[1] > 0 else 0.01,
                 "$\\approx 0$", ha='center', va='bottom', fontsize=9, color='gray')

ax1.set_xticks(x)
ax1.set_xticklabels(LABELS, fontsize=9)
ax1.set_ylabel(r"Stochastic EPR ($k_BT$/s)")
ax1.set_title("(a) Schnakenberg EPR decomposition\n(NET-T5, n=300/condition)")
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(alpha=0.3, axis='y')

# Panel b: septation rate, sporulating vs vegetative at N0=1600
spore_mask = spore_mask_by_cond[1600]
sept_rates = rates_by_cond[1600]["T_septation"]
spor_rates = [r for r,s in zip(sept_rates, spore_mask) if s]
veg_rates  = [r for r,s in zip(sept_rates, spore_mask) if not s]

ratio = mean(spor_rates) / mean(veg_rates) if mean(veg_rates) > 0 else float('inf')
cat_labels = ['Sporulating\n(n=%d)' % len(spor_rates), 'Vegetative\n(n=%d)' % len(veg_rates)]
vals = [mean(spor_rates), mean(veg_rates)]
ax2.set_prop_cycle(None)  # reset color cycle
ax2.bar(cat_labels[0], vals[0], color='#2ca02c', width=0.45, zorder=3)
ax2.bar(cat_labels[1], vals[1], color='#d62728', width=0.45, zorder=3)
ax2.set_yscale('log')
ax2.set_ylim(vals[1]*0.3, vals[0]*4)
for i, (cat, val) in enumerate(zip(cat_labels, vals)):
    ax2.text(i, val*1.4, "%.2e" % val, ha='center', va='bottom', fontsize=9)
ax2.set_ylabel(r"$T_{\rm sept}$ firing rate (s$^{-1}$, log scale)")
ax2.set_title("(b) Septation rate by fate at $N_c$\n($N_0$=1600 $\\mu$M, critical condition)")
ax2.grid(alpha=0.3, axis='y', which='both')

plt.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT, dpi=200, bbox_inches='tight')
print("Saved:", OUT)
print()
for n0 in CONDITIONS:
    tot = sum(epr_by_cond[n0].values())
    kina = epr_by_cond[n0]["T_KinA_activation"]
    print("N0=%d: total EPR=%.3e kBT/s  KinA=%.1f%%  sept=%.1f%%" % (
        n0, tot, 100*kina/tot if tot>0 else 0,
        100*epr_by_cond[n0]["T_septation"]/tot if tot>0 else 0))
print()
print("Septation rate asymmetry at N0=1600:")
print("  Sporulating: %.2e /s (n=%d)" % (mean(spor_rates), len(spor_rates)))
print("  Vegetative:  %.2e /s (n=%d)" % (mean(veg_rates), len(veg_rates)))
print("  Ratio: %.1fx" % ratio)
