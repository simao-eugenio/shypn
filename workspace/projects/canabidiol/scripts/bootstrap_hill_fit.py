"""Parametric bootstrap of the four-parameter Hill fit to the Q5 NFkB dose-response.

We do not have per-replicate samples on disk for the Q5 sweep — only aggregated
(mean, std, n) per cell. The parametric bootstrap therefore resamples each cell
mean from its sampling distribution N(mean, std/sqrt(n)) and refits the Hill
curve on every draw, producing CIs on (IC50, n_Hill) via the percentile method.

This is a Wald-style bootstrap of the fit, not a non-parametric resample. Honest
about the assumption: each cell's sample mean is approximately normal by CLT
(n=30, low CV per cell).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

RUN_DIR = Path(__file__).resolve().parents[1] / "experiments/results/run_20260503_133835"
N_BOOT = 2000
RNG = np.random.default_rng(20260504)


def hill4(d, r0, r_inf, ic50, n):
    return r_inf + (r0 - r_inf) / (1.0 + (d / ic50) ** n)


def hill3(d, r0, ic50, n):
    """Three-parameter Hill with r_inf fixed at zero (full suppression at saturation).

    Justified by the Q5 data: NFkB_p65 mean is exactly 0.0 at dose=0.5 µM at both
    severities (and CV is undefined there). A four-parameter fit drives r_inf
    negative, which is biologically inadmissible.
    """
    return r0 / (1.0 + (d / ic50) ** n)


def collect(severity: float):
    data = json.loads((RUN_DIR / "q5_endpoints.json").read_text())
    rows = []
    for cell in data["cells"].values():
        if cell["severity"] != severity:
            continue
        e = cell["endpoints"]["NFkB_p65_final"]
        rows.append((cell["dose"], e["mean"], e["std"], e["n"]))
    rows.sort()
    return np.array(rows, dtype=float)


def fit_hill(doses, means, p0):
    popt, _ = curve_fit(hill3, doses, means, p0=p0, maxfev=20000,
                        bounds=([0.0, 1e-6, 0.1], [10.0, 5.0, 10.0]))
    return popt


def bootstrap(severity: float):
    arr = collect(severity)
    doses, means, stds, ns = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
    sem = stds / np.sqrt(ns)

    p0 = (float(means.max()), 0.1, 1.5)
    point = fit_hill(doses, means, p0)
    print(f"\n=== severity {severity} ===")
    print(f"point estimate: r0={point[0]:.4f}  IC50={point[1]:.4f}  n={point[2]:.4f}")

    boots = []
    for _ in range(N_BOOT):
        resampled = RNG.normal(loc=means, scale=np.maximum(sem, 1e-9))
        try:
            popt = fit_hill(doses, resampled, p0)
            boots.append(popt)
        except Exception:
            continue
    boots = np.array(boots)
    print(f"bootstrap n_success = {len(boots)} / {N_BOOT}")
    for label, idx in [("r0", 0), ("IC50", 1), ("n_Hill", 2)]:
        lo, med, hi = np.percentile(boots[:, idx], [2.5, 50, 97.5])
        print(f"  {label:7s}  median={med:.4f}  95% CI [{lo:.4f}, {hi:.4f}]")
    return point, boots


def severity_independence(boot1, boot5):
    n = min(len(boot1), len(boot5))
    d_ic50 = boot1[:n, 1] - boot5[:n, 1]
    d_nh = boot1[:n, 2] - boot5[:n, 2]
    print("\n=== severity-independence (sev1 - sev5) ===")
    for label, arr in [("ΔIC50", d_ic50), ("Δn_Hill", d_nh)]:
        lo, med, hi = np.percentile(arr, [2.5, 50, 97.5])
        p = 2 * min((arr > 0).mean(), (arr < 0).mean())
        print(f"  {label:9s}  median={med:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]  p={p:.3f}")


def power_calc():
    """Sample size for the wet-lab assay that would discriminate the predicted
    sub-µM IC50 from a 'saturation only at high µM' null hypothesis.

    Concrete contrast: at d = 0.1 µM the model predicts NF-κB suppression to
    about 50 % of the vehicle plateau (≈ 1.4 µM out of 3.2 µM at sev=1). If
    previous studies were operating at saturation only above 1 µM, the
    expected response at 0.1 µM would be near the vehicle plateau. We size
    for a one-sided two-sample t-test that detects this difference at
    biologically realistic CV.
    """
    from statsmodels.stats.power import TTestIndPower
    mu_vehicle = 3.20  # NFkB at d=0, sev=1
    mu_treat = 1.42    # NFkB at d=0.1 µM, sev=1 (model)
    delta = mu_vehicle - mu_treat  # 1.78
    print("\n=== wet-lab power calc (NFkB suppression at d=0.1 µM vs vehicle) ===")
    for cv_pct in (10, 15, 25):
        sigma = (cv_pct / 100.0) * mu_vehicle
        d = delta / sigma
        n = TTestIndPower().solve_power(effect_size=d, alpha=0.05, power=0.80,
                                        alternative="larger")
        n = float(np.atleast_1d(n)[0])
        print(f"  biological CV = {cv_pct:>2d}%  →  Cohen's d = {d:5.2f}  →  "
              f"n per group = {int(np.ceil(n)):>3d}")


if __name__ == "__main__":
    p1, b1 = bootstrap(1.0)
    p5, b5 = bootstrap(5.0)
    severity_independence(b1, b5)
    power_calc()
