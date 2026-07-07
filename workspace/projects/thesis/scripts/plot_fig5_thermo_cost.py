#!/usr/bin/env python3
"""Figure 5 — Thermodynamic cost: eta_L is topology-constant, FT is inapplicable.

Panel (a): Landauer efficiency eta_L vs sigma_H half-life, NET-T1
           (run_20260704_181236, N0=1440, 100 reps/condition).
Panel (b): Dissipated work distributions W/kBT, FWD vs REV protocols, NET-T3
           (run_20260706_151050, 200 reps/condition).

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/plot_fig5_thermo_cost.py

Output: workspace/projects/thesis/manuscript/figures/fig5_thermo_cost.png
"""
import csv, math, pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUN_T1 = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260704_181236")
RUN_T3 = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260706_151050")
OUT = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig5_thermo_cost.png")

kB  = 1.380649e-23
T   = 310.15
kBT = kB * T
dG_ATP = 57000.0 / 6.022e23
V_cell = 1e-15
NA     = 6.022e23

def mean(v): return sum(v)/len(v) if v else float("nan")

def w_kbt(atp_consumed_uM):
    N = atp_consumed_uM * 1e-6 * V_cell * NA
    return N * dG_ATP / kBT

# ── Panel (a): eta_L vs half-life (NET-T1) ───────────────────────────────────
CONDS_T1 = {
    10:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_10",
    20:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_20",
    30:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_30",
    40:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_40",
    50:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_50",
    60:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_60",
    75:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_75",
    90:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_90",
    120: "condition_Baseline",
}

kBT_ln2 = kB * T * math.log(2)
hl_vals, eta_vals, sf_vals = [], [], []
for hl, cname in sorted(CONDS_T1.items()):
    rows = list(csv.DictReader(open(RUN_T1/cname/"replicates.csv")))
    n = len(rows)
    spore = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    sf = sum(spore)/n
    atp_f = [float(r.get("ATP_pool_final",0)) for r in rows]
    atp_spor = [atp_f[i] for i,s in enumerate(spore) if s]
    if atp_spor:
        atp_consumed = 5000.0 - mean(atp_spor)
        W = w_kbt(atp_consumed)
        eta_L = kBT_ln2/(W*kBT) if W > 0 else float("nan")
        hl_vals.append(hl); eta_vals.append(eta_L*100); sf_vals.append(sf)

# ── Panel (b): work per condition (NET-T3) — bar chart, not histogram ───────
# Note: ATP_final has ~zero replicate variance in every NET-T3 condition
# (deterministic ODE saturation), so a histogram of W is a degenerate spike.
# A bar chart across the five conditions is the correct visualisation.
def load_W_mean(cdir):
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    atp_f = [float(r.get("ATP_pool_final",0)) for r in rows]
    W_list = [w_kbt(5000.0 - a) for a in atp_f]
    return mean(W_list)

CONDS_T3 = {
    "Baseline\n(no step)":       "condition_Baseline",
    "FWD\n(1440→2160)":          "condition_[param]_INITIAL_NUTRIENTS_eq_1440_[param]_NUTRIENTS_STEP_TARGET_eq_2160_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
    "REV\n(2160→1440)":          "condition_[param]_INITIAL_NUTRIENTS_eq_2160_[param]_NUTRIENTS_STEP_TARGET_eq_1440_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
    "Ctrl\n(1440→1440)":         "condition_[param]_INITIAL_NUTRIENTS_eq_1440_[param]_NUTRIENTS_STEP_TARGET_eq_1440_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
    "Ctrl\n(2160→2160)":         "condition_[param]_INITIAL_NUTRIENTS_eq_2160_[param]_NUTRIENTS_STEP_TARGET_eq_2160_[param]_NUTRIENTS_STEP_TIME_S_eq_3600",
}
labels_b, W_means = [], []
for label, cname in CONDS_T3.items():
    labels_b.append(label)
    W_means.append(load_W_mean(RUN_T3/cname))

W_fwd = [load_W_mean(RUN_T3/CONDS_T3["FWD\n(1440→2160)"])]
W_rev = [load_W_mean(RUN_T3/CONDS_T3["REV\n(2160→1440)"])]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# Panel a
ax1.plot(hl_vals, eta_vals, 'o-', color='#1f77b4', markersize=6, linewidth=1.5)
ax1b = ax1.twinx()
ax1b.bar(hl_vals, [100*s for s in sf_vals], width=[max(3,h*0.15) for h in hl_vals],
          alpha=0.15, color='gray')
ax1b.set_ylabel("Sporulation fraction (%)", color='gray')
ax1b.set_ylim(0, 110)
ax1.set_xlabel(r"$\sigma_H$ half-life (min)")
ax1.set_ylabel(r"$\eta_L$ (%)")
ax1.set_title(r"(a) Landauer efficiency vs half-life" + "\n(NET-T1, $N_0$=1440, n=100/cond.)")
ax1.set_xscale('log')
ax1.grid(alpha=0.3)

# Panel b
colors_b = ['#7f7f7f', '#2ca02c', '#d62728', '#98df8a', '#ff9896']
bars = ax2.bar(labels_b, W_means, color=colors_b)
ax2.axhline(0, color='black', linewidth=0.8)
ax2.set_ylabel(r"$W / k_B T$")
ax2.set_title("(b) Dissipated work per condition\n(NET-T3, n=200/condition, zero replicate variance)")
ax2.tick_params(axis='x', labelsize=8)
ax2.grid(alpha=0.3, axis='y')

# Expand y-limits with padding so value annotations stay inside the axes
y_min = min(W_means); y_max = max(W_means)
y_range = y_max - y_min
ax2.set_ylim(y_min - 0.18*y_range, y_max + 0.18*y_range)

for bar, val in zip(bars, W_means):
    va = 'bottom' if val >= 0 else 'top'
    offset = 0.03*y_range if val >= 0 else -0.03*y_range
    ax2.annotate(f"{val:.2e}", (bar.get_x()+bar.get_width()/2, val+offset),
                 ha='center', va=va, fontsize=7)

plt.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT, dpi=200, bbox_inches='tight')
print("Saved:", OUT)
print()
print("Panel (a) data: HL(min) -> eta_L(%)  Spore%")
for hl,eta,sf in zip(hl_vals, eta_vals, sf_vals):
    print("  %4d -> %.3e%%  %.0f%%" % (hl, eta, 100*sf))
print()
print("Panel (b): W_fwd mean=%.3e kBT (n=%d), W_rev mean=%.3e kBT (n=%d)" % (
    mean(W_fwd), len(W_fwd), mean(W_rev), len(W_rev)))
