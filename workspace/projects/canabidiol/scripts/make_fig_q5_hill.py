"""Figure 2: Q5-final Hill fit on NFkB-p65 vs maintenance dose at two severities."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "experiments/results/run_20260503_133835/q5_endpoints.json"
OUT = ROOT / "figures" / "fig_q5_hill.pdf"

q5 = json.loads(DATA.read_text())["hill"]


def hill(x, r0, ic50, n):
    return r0 * ic50 ** n / (ic50 ** n + np.asarray(x) ** n + 1e-30)


fig, ax = plt.subplots(figsize=(5.0, 3.6), constrained_layout=True)

colors = {"DSEV=1.0": "#1f6fb4", "DSEV=5.0": "#b03030"}
labels = {"DSEV=1.0": "Severity 1", "DSEV=5.0": "Severity 5"}

xfit = np.linspace(0, 0.55, 400)
for key, fit in q5.items():
    doses = np.array(fit["doses"])
    means = np.array(fit["means"])
    stds = np.array(fit["stds"])
    c = colors[key]
    ax.errorbar(doses, means, yerr=stds, fmt="o", color=c, ms=5, capsize=2,
                label=f"{labels[key]}  IC$_{{50}}={fit['ic50']:.3f}$, $n={fit['n']:.2f}$")
    ax.plot(xfit, hill(xfit, fit["r0"], fit["ic50"], fit["n"]),
            "-", color=c, lw=1.4, alpha=0.85)

ax.set_xlabel("Maintenance dose")
ax.set_ylabel("NF$\\kappa$B p65 endpoint")
ax.set_xlim(-0.02, 0.55)
ax.set_ylim(bottom=-0.1)
ax.legend(loc="upper right", frameon=False, fontsize=9)
ax.grid(alpha=0.25, lw=0.5)

fig.savefig(OUT)
fig.savefig(OUT.with_suffix(".png"), dpi=160)
print(f"wrote {OUT}")
