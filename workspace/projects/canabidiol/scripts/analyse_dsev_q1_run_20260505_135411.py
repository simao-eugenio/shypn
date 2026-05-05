"""Q1 DISEASE_SEVERITY dose-response — analyse run_20260505_135411.

50 replicates × 24 h × 10 conditions (Baseline + DSev∈{0.5,1,1.5,2,2.5,3,3.5,4,5}).
Engine head a9ab7109 (auto-coupled max_tau).

Outputs:
  figures/q1_dsev_endpoint_table.csv       — per-condition mean±std at t=86400 s
  figures/q1_dsev_dose_response.csv        — same, wide format for plotting
  figures/q1_dsev_dose_response.png        — endpoint vs DSev grid
  figures/q1_dsev_trajectories.png         — mean trajectory per condition
  figures/q1_dsev_cv_at_endpoint.csv       — coefficient of variation at endpoint
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ── Paths
PROJ = Path(__file__).resolve().parents[1]
RUN = PROJ / "experiments" / "results" / "run_20260505_135411"
FIG = PROJ / "figures"
FIG.mkdir(exist_ok=True)

# ── Mapping P-id → biological name (from model_snapshot.shy)
model = json.loads((RUN / "model_snapshot.shy").read_text())
PID2NAME = {p["id"]: p["name"] for p in model["places"]}

KEY_READOUTS = [
    ("P5", "Abeta_Monomer"),
    ("P6", "Abeta_Oligomer"),
    ("P7", "Abeta_Plaque"),
    ("P9", "NFkB_p65"),
    ("P11", "TNFa"),
    ("P12", "IL1b"),
    ("P13", "IL6"),
    ("P19", "ROS"),
    ("P20", "Glutathione"),
    ("P21", "Microglia_M1"),
    ("P22", "Microglia_M2"),
    ("P23", "Neuron_Health"),
    ("P24", "BDNF"),
]

# ── Discover conditions
conditions = []
for d in sorted(RUN.iterdir()):
    if not d.is_dir() or not d.name.startswith("condition_"):
        continue
    name = d.name.replace("condition_", "")
    if "DISEASE_SEVERITY_eq_" in name:
        dsev = float(name.split("eq_")[1])
    else:
        dsev = None  # Baseline — read model default
    conditions.append((dsev, name, d))

# Resolve baseline dsev from model
p38_default = next(p for p in model["places"] if p["id"] == "P38")
baseline_dsev = float(p38_default.get("initial_marking", 0.0))
conditions = [
    (baseline_dsev if dsev is None else dsev, name, d) for dsev, name, d in conditions
]
conditions.sort(key=lambda r: r[0])

print(f"Conditions: {len(conditions)}  baseline DSev = {baseline_dsev}")
for dsev, name, _ in conditions:
    print(f"  DSev={dsev:5.2f}  {name}")

# ── Load all statistics
stats_by_dsev: dict[float, dict] = {}
for dsev, _, d in conditions:
    s = json.loads((d / "statistics.json").read_text())
    stats_by_dsev[dsev] = s

# Reference timeline (all conditions share)
t = np.array(stats_by_dsev[conditions[0][0]]["time_points"])
print(f"Time grid: n={len(t)}  span=[{t[0]}, {t[-1]}]  step={t[1]-t[0]}")

# ── Endpoint table (last time point)
rows = []
for dsev in sorted(stats_by_dsev):
    s = stats_by_dsev[dsev]
    row = {"DISEASE_SEVERITY": dsev}
    for pid, name in KEY_READOUTS:
        ps = s["species_statistics"][pid]
        row[f"{name}_mean"] = ps["mean"][-1]
        row[f"{name}_std"] = ps["std"][-1]
        row[f"{name}_cv"] = ps["cv"][-1] if ps["mean"][-1] != 0 else float("nan")
    rows.append(row)
endpoint = pd.DataFrame(rows).sort_values("DISEASE_SEVERITY").reset_index(drop=True)
endpoint.to_csv(FIG / "q1_dsev_endpoint_table.csv", index=False)
print(f"\n→ {FIG / 'q1_dsev_endpoint_table.csv'}")

# Pretty short table
print("\n=== Endpoint (t=24h) means ===")
short_cols = ["DISEASE_SEVERITY"] + [f"{n}_mean" for _, n in KEY_READOUTS]
print(endpoint[short_cols].round(3).to_string(index=False))

# ── Dose-response grid figure
n = len(KEY_READOUTS)
ncol = 4
nrow = (n + ncol - 1) // ncol
fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 3 * nrow), sharex=True)
axes = axes.flatten()
for ax, (pid, name) in zip(axes, KEY_READOUTS):
    means = endpoint[f"{name}_mean"].values
    stds = endpoint[f"{name}_std"].values
    dsev_vals = endpoint["DISEASE_SEVERITY"].values
    ax.errorbar(
        dsev_vals, means, yerr=stds,
        marker="o", capsize=3, lw=1.5, color="C0",
    )
    ax.set_title(f"{name}  ({pid})", fontsize=10)
    ax.set_xlabel("DISEASE_SEVERITY")
    ax.set_ylabel("endpoint @ 24 h")
    ax.grid(alpha=0.3)
for ax in axes[n:]:
    ax.axis("off")
fig.suptitle(
    "Q1 dose–response: endpoint marker vs DISEASE_SEVERITY  "
    "(50 reps × 24 h, run_20260505_135411)",
    y=1.00, fontsize=12,
)
fig.tight_layout()
fig.savefig(FIG / "q1_dsev_dose_response.png", dpi=140, bbox_inches="tight")
print(f"→ {FIG / 'q1_dsev_dose_response.png'}")

# ── Trajectories grid
fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 3 * nrow), sharex=True)
axes = axes.flatten()
cmap = plt.get_cmap("viridis")
dsev_sorted = sorted(stats_by_dsev)
norm_v = (np.array(dsev_sorted) - min(dsev_sorted)) / max(
    1e-9, max(dsev_sorted) - min(dsev_sorted)
)
t_h = t / 3600.0  # hours
for ax, (pid, name) in zip(axes, KEY_READOUTS):
    for dsev, c in zip(dsev_sorted, norm_v):
        s = stats_by_dsev[dsev]
        m = np.array(s["species_statistics"][pid]["mean"])
        ax.plot(t_h, m, color=cmap(c), lw=1.2, label=f"{dsev:.1f}")
    ax.set_title(f"{name}  ({pid})", fontsize=10)
    ax.set_xlabel("time (h)")
    ax.set_ylabel("mean over 50 reps")
    ax.grid(alpha=0.3)
for ax in axes[n:]:
    ax.axis("off")
# single legend
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles, labels,
    title="DSev",
    loc="lower center", bbox_to_anchor=(0.5, -0.02),
    ncol=len(dsev_sorted), fontsize=8,
)
fig.suptitle(
    "Q1 trajectories: mean over replicates  "
    "(50 reps × 24 h, run_20260505_135411)",
    y=1.00, fontsize=12,
)
fig.tight_layout()
fig.savefig(FIG / "q1_dsev_trajectories.png", dpi=140, bbox_inches="tight")
print(f"→ {FIG / 'q1_dsev_trajectories.png'}")

# ── Monotonicity / pathology consistency check
print("\n=== Monotonicity vs DSev (Spearman ρ) ===")
from scipy.stats import spearmanr  # type: ignore

dsev_arr = endpoint["DISEASE_SEVERITY"].values
mono_rows = []
for pid, name in KEY_READOUTS:
    means = endpoint[f"{name}_mean"].values
    rho, p = spearmanr(dsev_arr, means)
    direction = "↑" if rho > 0 else "↓" if rho < 0 else "·"
    mono_rows.append(
        {"name": name, "rho": rho, "p": p, "direction": direction}
    )
mono = pd.DataFrame(mono_rows)
print(mono.to_string(index=False))
mono.to_csv(FIG / "q1_dsev_monotonicity.csv", index=False)

# ── Pathology axis check
print("\n=== Pathology axis (expected AD direction) ===")
expected = {
    "Abeta_Monomer": "↑", "Abeta_Oligomer": "↑", "Abeta_Plaque": "↑",
    "NFkB_p65": "↑", "TNFa": "↑", "IL1b": "↑", "IL6": "↑",
    "ROS": "↑", "Microglia_M1": "↑",
    "Glutathione": "↓", "Neuron_Health": "↓", "BDNF": "↓",
    "Microglia_M2": "↓",  # M2 is anti-inflammatory; should drop with disease
}
for _, row in mono.iterrows():
    n = row["name"]
    obs = row["direction"]
    exp = expected.get(n, "?")
    flag = "✓" if obs == exp else ("✗" if exp != "?" else "·")
    print(
        f"  {flag}  {n:18s}  obs={obs}  exp={exp}  ρ={row['rho']:+.3f}"
    )

# ── CV table at endpoint
cv_cols = ["DISEASE_SEVERITY"] + [f"{n}_cv" for _, n in KEY_READOUTS]
endpoint[cv_cols].to_csv(FIG / "q1_dsev_cv_at_endpoint.csv", index=False)
print(f"\n→ {FIG / 'q1_dsev_cv_at_endpoint.csv'}")
print("\nDone.")
