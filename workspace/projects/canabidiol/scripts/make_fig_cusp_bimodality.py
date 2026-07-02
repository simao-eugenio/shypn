"""Figure 3: Cusp bimodality — ROS endpoint stats across severity, untreated vs treated.

Two panels: (a) Q3-final no-treatment cascade across DSEV; (b) Q4r-final at MAINT=2
across DSEV. Each cell shown as mean (filled circle), ±std (thick bar),
min/max whiskers (thin line). Wide whiskers + std signal bimodality.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
Q3 = json.loads((ROOT / "experiments/results/run_20260503_140103/q3_endpoints.json").read_text())
Q4 = json.loads((ROOT / "experiments/results/run_20260503_130113/q4r_endpoints.json").read_text())
OUT = ROOT / "figures" / "fig_cusp_bimodality.pdf"


def collect_q3():
    sevs, m, s, lo, hi, cv = [], [], [], [], [], []
    for sv in [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]:
        e = Q3["cells"].get(f"{sv}", {}).get("endpoints", {}).get("ROS_final", {})
        if not e:
            continue
        sevs.append(sv); m.append(e["mean"]); s.append(e["std"])
        lo.append(e["min"]); hi.append(e["max"])
        cv.append(e["cv"] if e["cv"] is not None else float("nan"))
    return list(map(np.array, (sevs, m, s, lo, hi, cv)))


def collect_q4(maint):
    sevs, m, s, lo, hi, cv = [], [], [], [], [], []
    for sv in [0.0, 1.0, 2.0, 5.0]:
        e = Q4["cells"].get(f"{maint}|{sv}", {}).get("endpoints", {}).get("ROS_final", {})
        if not e:
            continue
        sevs.append(sv); m.append(e["mean"]); s.append(e["std"])
        lo.append(e["min"]); hi.append(e["max"])
        cv.append(e["cv"] if e["cv"] is not None else float("nan"))
    return list(map(np.array, (sevs, m, s, lo, hi, cv)))


fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6), constrained_layout=True, sharey=True)

for ax, collect_fn, title, xshift in [
    (axes[0], collect_q3, "Untreated", 0.0),
    (axes[1], lambda: collect_q4(2.0), "Maintenance dose 2", 0.0),
]:
    sevs, m, s, lo, hi, cv = collect_fn()
    # min/max whiskers
    ax.vlines(sevs + xshift, lo, hi, color="0.55", lw=0.9, zorder=1)
    # std bars
    ax.vlines(sevs + xshift, m - s, m + s, color="black", lw=3.0, zorder=2)
    # mean dots
    ax.plot(sevs + xshift, m, "o", color="white", mec="black",
            ms=7, mew=1.2, zorder=3)
    # CV labels above bimodal cells (offset above max-whisker AND std-bar top)
    for x, y, m_, s_, c in zip(sevs, hi, m, s, cv):
        if not np.isnan(c) and c > 0.10:
            y_label = max(y, m_ + s_) + 12
            ax.text(x, y_label, f"CV {c*100:.0f}%", ha="center", va="bottom",
                    fontsize=8, color="#b03030")
    ax.set_xlabel("Disease severity")
    ax.set_title(title, fontsize=10)
    ax.set_xticks([0, 1, 2, 3, 5])
    ax.grid(alpha=0.25, lw=0.5)

axes[0].set_ylabel("Reactive O species endpoint")
axes[0].set_ylim(-10, 130)

fig.savefig(OUT)
fig.savefig(OUT.with_suffix(".png"), dpi=160)
print(f"wrote {OUT}")
