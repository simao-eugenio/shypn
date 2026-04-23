#!/usr/bin/env python3
"""
Create a basin-of-attraction figure using a Waddington pseudo-potential.

The script tries to read endpoint statistics from a run directory with layout:
  run_xxx/condition_*/statistics.json
If that data is not available locally, it uses a verified fallback table from
run_20260420_143905 (37 C, 30 replicates).

Outputs:
  workspace/projects/canabidiol/figures/fig_waddington_landscape.{png,pdf}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# Verified endpoints extracted from run_20260420_143905 on remote-gpu.
# Columns: CBD_uM, Neuron_Health_mean, Neuron_Health_std, NFkB_p65_mean
FALLBACK_ENDPOINTS = [
    (0.0, 80.967, 3.886, 79.999),
    (1.0, 91.533, 1.688, 0.152),
    (2.0, 92.633, 1.197, 0.078),
    (4.0, 93.233, 1.230, 0.041),
    (6.0, 93.567, 1.334, 0.029),
    (8.0, 93.700, 1.345, 0.023),
    (10.0, 93.800, 1.327, 0.019),
    (12.0, 93.867, 1.335, 0.016),
    (14.0, 93.900, 1.300, 0.015),
    (15.0, 93.933, 1.340, 0.014),
]


def condition_to_cbd_uM(condition_dir_name: str) -> float | None:
    if "CBD_extracellular_eq_" not in condition_dir_name:
        return None
    raw = condition_dir_name.split("CBD_extracellular_eq_")[-1]
    try:
        return float(raw)
    except ValueError:
        return None


def load_endpoints(run_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    if not run_dir.exists():
        return None

    rows: list[tuple[float, float, float, float]] = []
    for cond_dir in sorted(run_dir.iterdir()):
        if not cond_dir.is_dir():
            continue

        cbd_uM = condition_to_cbd_uM(cond_dir.name)
        if cbd_uM is None:
            continue

        stats_file = cond_dir / "statistics.json"
        if not stats_file.exists():
            continue

        try:
            stats = json.loads(stats_file.read_text())
            species = stats["species_statistics"]
            p23 = species.get("P23", species.get("Neuron_Health", {}))
            p9 = species.get("P9", species.get("NFkB_p65", {}))

            nh_mean = float(p23["mean"][-1])
            nh_std = float(p23["std"][-1])
            nfkb_mean = float(p9["mean"][-1])
            rows.append((cbd_uM, nh_mean, nh_std, nfkb_mean))
        except Exception:
            continue

    if not rows:
        return None

    rows.sort(key=lambda x: x[0])
    arr = np.array(rows, dtype=float)
    return arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]


def alpha_from_probability(p: np.ndarray, noise_temperature: float = 0.5) -> np.ndarray:
    eps = 1e-5
    p_safe = np.clip(p, eps, 1.0 - eps)
    return -noise_temperature * np.log(p_safe / (1.0 - p_safe))


def waddington_potential(x: np.ndarray, alpha: float) -> np.ndarray:
    return (x * x - 1.0) ** 2 + alpha * x


def build_figure(cbd: np.ndarray, nh_mean: np.ndarray, nh_std: np.ndarray, output_dir: Path) -> Path:
    nh_lo = float(np.min(nh_mean))
    nh_hi = float(np.max(nh_mean))

    # Basin probability proxy: normalized Neuron_Health between disease and best-treated endpoints.
    p_treated = (nh_mean - nh_lo) / max(nh_hi - nh_lo, 1e-9)
    alpha = alpha_from_probability(p_treated)

    x = np.linspace(-1.6, 1.6, 700)
    shown_cbd = [0.0, 1.0, 2.0, 4.0, 8.0, 15.0]

    fig = plt.figure(figsize=(12.0, 5.0))
    gs = fig.add_gridspec(1, 2, wspace=0.27, left=0.07, right=0.97, top=0.88, bottom=0.13)
    ax_l = fig.add_subplot(gs[0])
    ax_r = fig.add_subplot(gs[1])

    cmap = plt.get_cmap("viridis")

    # Left panel: Waddington pseudo-potential family across CBD doses.
    for dose in shown_cbd:
        idx = int(np.argmin(np.abs(cbd - dose)))
        dose_real = float(cbd[idx])
        a = float(alpha[idx])
        color = cmap(idx / max(len(cbd) - 1, 1))
        y = waddington_potential(x, a)
        ax_l.plot(x, y, lw=2.0, color=color, label=f"CBD={dose_real:.0f} uM")

        # Mark local basin bottoms by searching each side separately.
        left_mask = x < 0.0
        right_mask = x > 0.0
        xl = x[left_mask][np.argmin(y[left_mask])]
        yl = waddington_potential(np.array([xl]), a)[0]
        xr = x[right_mask][np.argmin(y[right_mask])]
        yr = waddington_potential(np.array([xr]), a)[0]
        ax_l.scatter([xl, xr], [yl, yr], s=25, color=color, zorder=5)

    ax_l.axvspan(-1.6, 0.0, color="#fdd0a2", alpha=0.25, zorder=0)
    ax_l.axvspan(0.0, 1.6, color="#c6dbef", alpha=0.25, zorder=0)
    ax_l.axvline(0.0, color="#666666", lw=0.8, ls="--")
    ax_l.text(-1.2, 1.22, "Disease basin", fontsize=9, color="#8c2d04", style="italic")
    ax_l.text(0.72, 1.22, "Protected basin", fontsize=9, color="#08519c", style="italic")
    ax_l.set_xlim(-1.6, 1.6)
    ax_l.set_ylim(-0.6, 1.45)
    ax_l.set_xticks([])
    ax_l.set_xlabel("Cell fate coordinate (disease <- -> protected)")
    ax_l.set_ylabel("Pseudo-potential (a.u.)")
    ax_l.set_title("A. Waddington landscape vs CBD dose", loc="left", fontweight="bold")
    ax_l.legend(frameon=False, fontsize=8, ncol=2, loc="lower center")

    # Right panel: basin occupancy proxy and endpoint response.
    ax_r.plot(cbd, p_treated, color="#08519c", marker="o", lw=2.2, label="P(protected basin)")
    ax_r.fill_between(cbd, np.maximum(p_treated - 0.05, 0.0), np.minimum(p_treated + 0.05, 1.0),
                      color="#9ecae1", alpha=0.25, linewidth=0)

    ax_r2 = ax_r.twinx()
    ax_r2.errorbar(cbd, nh_mean, yerr=nh_std, color="#a50f15", marker="s", lw=1.8,
                   ms=4.5, capsize=3, label="Neuron_Health")

    ax_r.axhline(0.5, color="#666666", lw=0.9, ls="--")
    ax_r.text(float(cbd[-1]) - 0.6, 0.53, "basin split", fontsize=8, color="#555555")

    ax_r.set_xlim(float(cbd[0]) - 0.2, float(cbd[-1]) + 0.4)
    ax_r.set_ylim(-0.02, 1.05)
    ax_r2.set_ylim(float(np.min(nh_mean) - 1.0), float(np.max(nh_mean) + 1.5))

    ax_r.set_xlabel("CBD extracellular (uM)")
    ax_r.set_ylabel("Basin occupancy probability")
    ax_r2.set_ylabel("Neuron_Health endpoint")
    ax_r.set_title("B. Basin occupancy and endpoint response", loc="left", fontweight="bold")

    # Combined legend from both axes.
    h1, l1 = ax_r.get_legend_handles_labels()
    h2, l2 = ax_r2.get_legend_handles_labels()
    ax_r.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="lower right")

    fig.suptitle("CBD-AD model: basin-of-attraction view (Waddington pseudo-potential)", fontsize=12)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_png = output_dir / "fig_waddington_landscape.png"
    out_pdf = output_dir / "fig_waddington_landscape.pdf"
    fig.savefig(out_png, dpi=250, bbox_inches="tight")
    fig.savefig(out_pdf, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return out_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Waddington basin-of-attraction figure")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("workspace/projects/canabidiol/experiments/results/run_20260420_143905"),
        help="Run directory with condition_*/statistics.json files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("workspace/projects/canabidiol/figures"),
        help="Figure output directory",
    )
    args = parser.parse_args()

    loaded = load_endpoints(args.run_dir)
    if loaded is None:
        arr = np.array(FALLBACK_ENDPOINTS, dtype=float)
        cbd, nh_mean, nh_std, _nfkb = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
        print(f"Using fallback endpoint table; run data not found at: {args.run_dir}")
    else:
        cbd, nh_mean, nh_std, _nfkb = loaded
        print(f"Loaded endpoint table from: {args.run_dir}")

    out = build_figure(cbd, nh_mean, nh_std, args.output_dir)
    print(f"Saved figure: {out}")


if __name__ == "__main__":
    main()
