"""Q1 DISEASE_SEVERITY transient-aware dose-response — run_20260505_135411.

Endpoint at 24h is DOMINATED by basal clearance — disease installation events fire
at t=0.01s and the resulting Aβ_Oligomer / Aβ_Plaque / NFkB peaks are cleared back
to ~baseline within 10 min. So endpoint analysis hides the dose-response.

Outputs:
  figures/q1_dsev_transient_features.csv       — peak, AUC, t-to-peak per condition × marker
  figures/q1_dsev_transient_curves.png         — first 30 min trajectories
  figures/q1_dsev_transient_dose_response.png  — peak, AUC, half-decay vs DSev
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJ = Path(__file__).resolve().parents[1]
RUN = PROJ / "experiments" / "results" / "run_20260505_135411"
FIG = PROJ / "figures"
FIG.mkdir(exist_ok=True)

KEY_READOUTS = [
    ("P5", "Abeta_Monomer"),
    ("P6", "Abeta_Oligomer"),
    ("P7", "Abeta_Plaque"),
    ("P9", "NFkB_p65"),
    ("P11", "TNFa"),
    ("P12", "IL1b"),
    ("P19", "ROS"),
    ("P20", "Glutathione"),
    ("P21", "Microglia_M1"),
    ("P23", "Neuron_Health"),
    ("P24", "BDNF"),
]

# ── Discover conditions
model = json.loads((RUN / "model_snapshot.shy").read_text())
p38_default = float(
    next(p for p in model["places"] if p["id"] == "P38").get("initial_marking", 0.0)
)

conditions = []
for d in sorted(RUN.iterdir()):
    if not d.is_dir() or not d.name.startswith("condition_"):
        continue
    name = d.name.replace("condition_", "")
    if "DISEASE_SEVERITY_eq_" in name:
        dsev = float(name.split("eq_")[1])
    else:
        dsev = p38_default
    conditions.append((dsev, d))
conditions.sort(key=lambda r: r[0])

stats_by_dsev = {
    dsev: json.loads((d / "statistics.json").read_text()) for dsev, d in conditions
}
t = np.array(stats_by_dsev[conditions[0][0]]["time_points"])
print(f"Timeline: n={len(t)}  step={t[1]-t[0]} s  span={t[-1]/3600:.1f} h")

# ── Transient feature extraction
def features(t: np.ndarray, x: np.ndarray, baseline: float | None = None):
    """Return peak, t_peak, AUC over first 30 min, half-decay time."""
    win = t <= 30 * 60  # first 30 min
    tw = t[win]
    xw = x[win]
    if baseline is None:
        baseline = xw[0]
    delta = xw - baseline
    peak_idx = int(np.argmax(np.abs(delta)))
    peak_val = xw[peak_idx]
    peak_delta = delta[peak_idx]
    t_peak = tw[peak_idx]
    auc = float(np.trapezoid(delta, tw))  # signed AUC of deflection
    # Half-decay: time after peak when |delta| falls to 50% of peak |delta|
    if abs(peak_delta) > 1e-12:
        post = np.where(np.abs(delta[peak_idx:]) <= 0.5 * abs(peak_delta))[0]
        t_half = float(tw[peak_idx + post[0]] - t_peak) if len(post) else float("nan")
    else:
        t_half = float("nan")
    return peak_val, peak_delta, t_peak, auc, t_half


rows = []
for dsev, _ in conditions:
    s = stats_by_dsev[dsev]
    for pid, name in KEY_READOUTS:
        m = np.array(s["species_statistics"][pid]["mean"])
        peak, dpeak, tp, auc, thalf = features(t, m)
        rows.append({
            "DISEASE_SEVERITY": dsev,
            "marker": name,
            "pid": pid,
            "baseline_t0": float(m[0]),
            "peak_value": peak,
            "peak_delta": dpeak,
            "t_peak_s": tp,
            "AUC_30min": auc,
            "t_half_decay_s": thalf,
            "endpoint_24h": float(m[-1]),
        })
feat = pd.DataFrame(rows)
feat.to_csv(FIG / "q1_dsev_transient_features.csv", index=False)
print(f"\n→ {FIG / 'q1_dsev_transient_features.csv'}")

# Pivot for peak_delta
print("\n=== Peak Δ vs baseline (first 30 min) ===")
pv = feat.pivot(
    index="DISEASE_SEVERITY", columns="marker", values="peak_delta"
)[[n for _, n in KEY_READOUTS]]
print(pv.round(3).to_string())

print("\n=== AUC over 30 min (signed deflection from t=0) ===")
pa = feat.pivot(
    index="DISEASE_SEVERITY", columns="marker", values="AUC_30min"
)[[n for _, n in KEY_READOUTS]]
print(pa.round(1).to_string())

# ── Trajectories (first 30 min, log-y where useful)
fig, axes = plt.subplots(3, 4, figsize=(16, 10), sharex=True)
axes = axes.flatten()
cmap = plt.get_cmap("viridis")
dsev_sorted = sorted(stats_by_dsev)
norm_v = (np.array(dsev_sorted) - min(dsev_sorted)) / max(
    1e-9, max(dsev_sorted) - min(dsev_sorted)
)
T_WIN = 30 * 60  # 30 min
mask = t <= T_WIN
t_win = t[mask] / 60.0  # minutes

for ax, (pid, name) in zip(axes, KEY_READOUTS):
    for dsev, c in zip(dsev_sorted, norm_v):
        s = stats_by_dsev[dsev]
        m = np.array(s["species_statistics"][pid]["mean"])[mask]
        sd = np.array(s["species_statistics"][pid]["std"])[mask]
        ax.plot(t_win, m, color=cmap(c), lw=1.4, label=f"{dsev:.1f}")
        ax.fill_between(t_win, m - sd, m + sd, color=cmap(c), alpha=0.10)
    ax.set_title(f"{name}  ({pid})", fontsize=10)
    ax.set_xlabel("time (min)")
    ax.set_ylabel("mean ± SD over 50 reps")
    ax.grid(alpha=0.3)
for ax in axes[len(KEY_READOUTS):]:
    ax.axis("off")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles, labels, title="DSev", loc="lower center",
    bbox_to_anchor=(0.5, -0.01), ncol=len(dsev_sorted), fontsize=8,
)
fig.suptitle(
    "Q1 transient (first 30 min): mean ± SD across 50 replicates",
    y=1.00, fontsize=13,
)
fig.tight_layout()
fig.savefig(FIG / "q1_dsev_transient_curves.png", dpi=140, bbox_inches="tight")
print(f"\n→ {FIG / 'q1_dsev_transient_curves.png'}")

# ── Dose-response on transient features
fig, axes = plt.subplots(3, 4, figsize=(16, 10), sharex=True)
axes = axes.flatten()
for ax, (pid, name) in zip(axes, KEY_READOUTS):
    sub = feat[feat.marker == name].sort_values("DISEASE_SEVERITY")
    x = sub["DISEASE_SEVERITY"].values
    ax.plot(x, sub["peak_delta"].values, "o-", label="peak Δ", color="C0")
    ax2 = ax.twinx()
    ax2.plot(x, sub["AUC_30min"].values, "s--", label="AUC 30min", color="C3", alpha=0.7)
    ax.set_xlabel("DISEASE_SEVERITY")
    ax.set_ylabel("peak Δ", color="C0")
    ax2.set_ylabel("AUC 30 min", color="C3")
    ax.set_title(f"{name}  ({pid})", fontsize=10)
    ax.grid(alpha=0.3)
for ax in axes[len(KEY_READOUTS):]:
    ax.axis("off")
fig.suptitle(
    "Q1 transient dose-response: peak Δ (blue) and AUC (red) vs DSev",
    y=1.00, fontsize=13,
)
fig.tight_layout()
fig.savefig(FIG / "q1_dsev_transient_dose_response.png", dpi=140, bbox_inches="tight")
print(f"→ {FIG / 'q1_dsev_transient_dose_response.png'}")

# ── Monotonicity on transient features
from scipy.stats import spearmanr  # type: ignore

print("\n=== Monotonicity on PEAK Δ vs DSev ===")
for pid, name in KEY_READOUTS:
    sub = feat[feat.marker == name].sort_values("DISEASE_SEVERITY")
    x = sub["DISEASE_SEVERITY"].values
    y = sub["peak_delta"].values
    if np.allclose(y, y[0]):
        print(f"  {name:18s}  (constant — no response)")
        continue
    rho, p = spearmanr(x, y)
    direction = "↑" if rho > 0 else "↓"
    print(f"  {name:18s}  ρ={rho:+.3f}  p={p:.2e}  {direction}")

# ── Decay summary: how fast does the AD signal die?
print("\n=== Half-decay times of disease signals (s) ===")
for pid, name in [("P6", "Abeta_Oligomer"), ("P7", "Abeta_Plaque"),
                  ("P9", "NFkB_p65"), ("P11", "TNFa"), ("P12", "IL1b"),
                  ("P19", "ROS")]:
    sub = feat[feat.marker == name].sort_values("DISEASE_SEVERITY")
    print(f"  {name:18s}  " + "  ".join(
        f"DSev={r['DISEASE_SEVERITY']:.1f}:{r['t_half_decay_s']:6.0f}s"
        for _, r in sub.iterrows()
    ))

print("\nDone.")
