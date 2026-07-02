"""
Analyze P6 dose-response sweep (run_20260425_154907) from compact_summary.json.

Builds:
  1. Console table: final-value dose-response across the 7 swept DSev cells
     (plus Baseline) for the key biological readouts.
  2. Three PNG figures:
     - dose_response_finals.png : final-value bar/dot plot of key species
     - dose_response_trajectories.png : 12-panel time-series, one panel per
       key species, one curve per DSev cell.
     - cbd_pk.png : CBD_extracellular and CBD_intracellular trajectories
       (sanity check the loading + maintenance dosing event chain).

Run from repo root:
    python workspace/projects/canabidiol/scripts/p6_sweep_analysis.py
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RUN = (
    ROOT
    / "workspace/projects/canabidiol/experiments/results/run_20260425_154907"
)
SUMMARY = RUN / "compact_summary.json"
FIG_DIR = ROOT / "workspace/projects/canabidiol/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

KEY_SPECIES = [
    "Neuron_Health",
    "Abeta_Monomer",
    "Abeta_Oligomer",
    "Abeta_Plaque",
    "Microglia_M1",
    "Microglia_M2",
    "ROS",
    "Glutathione",
    "NFkB_p65",
    "TNFa",
    "IL1b",
    "IL6",
    "PPARg_active",
    "HO1",
    "CBD_extracellular",
    "CBD_intracellular",
]

with SUMMARY.open() as f:
    s = json.load(f)

name_to_id = {v: k for k, v in s["place_id_to_name"].items()}

# Order conditions: Baseline first, then DSev sorted ascending
def parse_dsev(c: str) -> float:
    # condition dir name: '[param]_Disease_Severity_eq_0.5'
    return float(c.rsplit("_eq_", 1)[-1])

def cond_key(c: str) -> tuple:
    if c == "Baseline":
        return (-1.0,)
    try:
        return (parse_dsev(c),)
    except Exception:
        return (999.0,)

condition_names = sorted(s["conditions"].keys(), key=cond_key)

def dsev_label(c: str) -> str:
    if c == "Baseline":
        return "Baseline"
    return c.replace("[param]_Disease_Severity_eq_", "DSev=")

# -----------------------------------------------------------------------
# 1. Dose-response final-value table
# -----------------------------------------------------------------------
print("\n=== P6 dose-response — final values at t=14400 s (mean ± std, n=30) ===\n")
header = f"{'species':<22}" + "".join(f"{dsev_label(c):>14s}" for c in condition_names)
print(header)
print("-" * len(header))
for sp in KEY_SPECIES:
    pid = name_to_id.get(sp)
    if pid is None:
        continue
    row = f"{sp:<22}"
    for c in condition_names:
        spc = s["conditions"][c]["species"][pid]
        row += f"{spc['final_mean']:>8.2f}±{spc['final_std']:<5.2f}"
    print(row)

# -----------------------------------------------------------------------
# 2. Final-value figure: each species, x-axis DSev, line plot with err bar
# -----------------------------------------------------------------------
swept = [c for c in condition_names if c != "Baseline"]
xs = [parse_dsev(c) for c in swept]
baseline_cond = "Baseline" if "Baseline" in s["conditions"] else None

n = len(KEY_SPECIES)
ncol = 4
nrow = (n + ncol - 1) // ncol
fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 3 * nrow), sharex=True)
axes = axes.flatten()
for ax, sp in zip(axes, KEY_SPECIES):
    pid = name_to_id.get(sp)
    if pid is None:
        ax.set_visible(False)
        continue
    means = [s["conditions"][c]["species"][pid]["final_mean"] for c in swept]
    stds = [s["conditions"][c]["species"][pid]["final_std"] for c in swept]
    ax.errorbar(xs, means, yerr=stds, marker="o", capsize=3, lw=1.5)
    if baseline_cond is not None:
        bm = s["conditions"][baseline_cond]["species"][pid]["final_mean"]
        ax.axhline(bm, color="gray", lw=1, ls="--", label="Baseline")
    ax.set_title(sp, fontsize=10)
    ax.grid(alpha=0.3)
for ax in axes[n:]:
    ax.set_visible(False)
for ax in axes[-ncol:]:
    ax.set_xlabel("Disease_Severity")
fig.suptitle(
    "P6 sweep: final-value dose-response (t = 14400 s, n=30 replicates)",
    fontsize=12,
)
fig.tight_layout()
out = FIG_DIR / "p6_dose_response_finals.png"
fig.savefig(out, dpi=110)
plt.close(fig)
print(f"\nwrote {out}")

# -----------------------------------------------------------------------
# 3. Trajectory figure: 1 panel per species, one line per DSev cell
# -----------------------------------------------------------------------
fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 3 * nrow), sharex=True)
axes = axes.flatten()
cmap = plt.get_cmap("viridis")
ord_swept = sorted(swept, key=cond_key)
n_swept = len(ord_swept)
for ax, sp in zip(axes, KEY_SPECIES):
    pid = name_to_id.get(sp)
    if pid is None:
        ax.set_visible(False)
        continue
    if baseline_cond is not None:
        spc = s["conditions"][baseline_cond]["species"][pid]
        ax.plot(spc["downsampled_t"], spc["downsampled_mean"],
                color="black", ls=":", lw=1.0, label="Baseline")
    for i, c in enumerate(ord_swept):
        spc = s["conditions"][c]["species"][pid]
        ax.plot(spc["downsampled_t"], spc["downsampled_mean"],
                color=cmap(i / max(1, n_swept - 1)),
                lw=1.2, label=dsev_label(c))
    ax.set_title(sp, fontsize=10)
    ax.grid(alpha=0.3)
for ax in axes[n:]:
    ax.set_visible(False)
for ax in axes[-ncol:]:
    ax.set_xlabel("time (s)")
# single shared legend
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=min(8, n_swept + 1),
           fontsize=8, bbox_to_anchor=(0.5, -0.01))
fig.suptitle("P6 sweep: mean trajectories by Disease_Severity (n=30)", fontsize=12)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
out = FIG_DIR / "p6_dose_response_trajectories.png"
fig.savefig(out, dpi=110, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}")

# -----------------------------------------------------------------------
# 4. CBD PK sanity check
# -----------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
for ax, sp in zip(axes, ["CBD_extracellular", "CBD_intracellular"]):
    pid = name_to_id.get(sp)
    if pid is None:
        continue
    if baseline_cond is not None:
        spc = s["conditions"][baseline_cond]["species"][pid]
        ax.plot(spc["downsampled_t"], spc["downsampled_mean"],
                color="black", ls=":", lw=1.2, label="Baseline")
    for i, c in enumerate(ord_swept):
        spc = s["conditions"][c]["species"][pid]
        ax.plot(spc["downsampled_t"], spc["downsampled_mean"],
                color=cmap(i / max(1, n_swept - 1)),
                lw=1.2, label=dsev_label(c))
    ax.set_title(sp)
    ax.set_xlabel("time (s)")
    ax.grid(alpha=0.3)
axes[0].legend(fontsize=8)
fig.suptitle("CBD PK trajectory (LOADING + 3 MAINT events)", fontsize=11)
fig.tight_layout()
out = FIG_DIR / "p6_cbd_pk.png"
fig.savefig(out, dpi=110)
plt.close(fig)
print(f"wrote {out}")
