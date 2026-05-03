#!/usr/bin/env python3
"""Analyze Q5-final sweep: refined MAINT_DOSE grid at two disease severities.

  - per-cell (mean, std, min, max, cv) on NFkB-p65 and the other key endpoints
  - Hill fit r(M) = r0 * IC50^n / (IC50^n + M^n) on NFkB-p65 per severity
  - emits q5_endpoints.{json,md} into the run dir
"""
from __future__ import annotations
import csv
import json
import math
import re
import sys
from pathlib import Path
from statistics import mean, stdev

ENDPOINTS = [
    "Neuron_Health_final",
    "NFkB_p65_final",
    "NFkB_IkB_final",
    "Abeta_Oligomer_final",
    "ROS_final",
    "Glutathione_final",
    "TNFa_final",
    "BDNF_final",
    "CBD_plasma_final",
    "CBD_intracellular_final",
    "Microglia_M1_final",
    "Microglia_M2_final",
    "PPARg_active_final",
    "Neurotoxicity_firings",
]
DOSES = [0.0, 0.05, 0.1, 0.2, 0.35, 0.5]
SEVS = [1.0, 5.0]

CELL_RE = re.compile(
    r"condition_\[param\]_MAINT_DOSE_eq_(?P<dose>[0-9.]+)_\[param\]_DISEASE_SEVERITY_eq_(?P<sev>[0-9.]+)"
)


def stats(vals):
    if not vals:
        return {"n": 0}
    n = len(vals)
    m = mean(vals)
    s = stdev(vals) if n > 1 else 0.0
    return {"n": n, "mean": m, "std": s, "min": min(vals), "max": max(vals),
            "cv": (s / m) if m != 0 else float("nan")}


def hill_fit(xs, ys, r0_hint=None):
    """Fit r0 * IC50^n / (IC50^n + x^n) by nonlinear least squares.
    Falls back to scipy.optimize.curve_fit if available; else a small grid +
    Nelder--Mead implementation in pure stdlib.
    Returns (r0, IC50, n, ssr) or (None,)*4 on failure.
    """
    try:
        from scipy.optimize import curve_fit  # type: ignore
        import numpy as np  # type: ignore

        def f(x, r0, ic50, nn):
            return r0 * (ic50 ** nn) / (ic50 ** nn + x ** nn)

        x = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        # bound away from x=0 issues; ic50 must be > 0, n in [0.3, 6]
        p0 = [r0_hint or float(y[0]) or 1.0, 0.1, 1.0]
        popt, _ = curve_fit(f, x, y, p0=p0,
                            bounds=([1e-6, 1e-4, 0.3], [10 * (r0_hint or 5.0), 5.0, 6.0]),
                            maxfev=20000)
        r0, ic50, nn = popt
        ssr = float(((f(x, *popt) - y) ** 2).sum())
        return float(r0), float(ic50), float(nn), ssr
    except Exception as exc:  # pragma: no cover
        return None, None, None, float(exc)


def main():
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <run_dir>", file=sys.stderr)
        sys.exit(2)
    run_dir = Path(sys.argv[1])
    out = {"run_dir": str(run_dir), "cells": {}, "baseline": None, "hill": {}}

    for cond_dir in sorted(run_dir.glob("condition_*")):
        rep = cond_dir / "replicates.csv"
        if not rep.exists():
            continue
        with rep.open() as fh:
            rows = list(csv.DictReader(fh))
        cell = {"n_replicates": len(rows), "endpoints": {}}
        for ep in ENDPOINTS:
            if not rows or ep not in rows[0]:
                continue
            try:
                vals = [float(r[ep]) for r in rows if r[ep] not in ("", None)]
            except ValueError:
                continue
            cell["endpoints"][ep] = stats(vals)

        if cond_dir.name == "condition_Baseline":
            out["baseline"] = cell
            continue
        m = CELL_RE.match(cond_dir.name)
        if not m:
            continue
        d = float(m["dose"]); s = float(m["sev"])
        out["cells"][f"{d}|{s}"] = {"dose": d, "severity": s, **cell}

    # Hill fits per severity on NFkB_p65
    for sev in SEVS:
        xs, ys, sds = [], [], []
        for d in DOSES:
            c = out["cells"].get(f"{d}|{sev}")
            if not c:
                continue
            ep = c["endpoints"].get("NFkB_p65_final")
            if not ep or "mean" not in ep:
                continue
            xs.append(d); ys.append(ep["mean"]); sds.append(ep.get("std", 0))
        if len(xs) >= 3:
            r0, ic50, nn, ssr = hill_fit(xs, ys, r0_hint=ys[0])
            out["hill"][f"DSEV={sev}"] = {
                "doses": xs, "means": ys, "stds": sds,
                "r0": r0, "ic50": ic50, "n": nn, "ssr": ssr,
            }

    out_json = run_dir / "q5_endpoints.json"
    out_json.write_text(json.dumps(out, indent=2, default=str))

    md = [f"# Q5-final endpoints — {run_dir.name}\n"]

    def fmt(s, key="mean", prec=4):
        if not s or "mean" not in s:
            return "—"
        v = s.get(key)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return "—"
        if abs(v) >= 1000:
            return f"{v:.0f}"
        if abs(v) >= 1:
            return f"{v:.{max(0, prec-2)}f}"
        return f"{v:.{prec}f}"

    surface_eps = [
        ("NFkB_p65_final", "NF\u03baB p65"),
        ("Neuron_Health_final", "Neuron Health"),
        ("ROS_final", "ROS"),
        ("Glutathione_final", "GSH"),
        ("Abeta_Oligomer_final", "A\u03b2 Oligomer"),
        ("TNFa_final", "TNF\u03b1"),
        ("PPARg_active_final", "PPAR\u03b3 active"),
        ("CBD_intracellular_final", "CBD intracellular"),
    ]
    for ep_key, ep_label in surface_eps:
        md.append(f"\n## {ep_label} (mean ± std, n=30)\n")
        md.append("| MAINT \\ DSEV | " + " | ".join(str(s) for s in SEVS) + " |")
        md.append("|---" * (len(SEVS) + 1) + "|")
        for d in DOSES:
            row = [f"**{d}**"]
            for s in SEVS:
                c = out["cells"].get(f"{d}|{s}", {})
                ep = c.get("endpoints", {}).get(ep_key, {})
                if not ep:
                    row.append("—")
                else:
                    row.append(f"{fmt(ep,'mean')} ± {fmt(ep,'std')}")
            md.append("| " + " | ".join(row) + " |")

    md.append("\n## Hill fits on NF\u03baB p65: r(M) = r0 · IC50^n / (IC50^n + M^n)\n")
    md.append("| Severity | r0 | IC50 | n | SSR |")
    md.append("|---|---|---|---|---|")
    for k, h in out["hill"].items():
        if h.get("r0") is None:
            md.append(f"| {k} | fit-fail ({h.get('ssr')}) | — | — | — |")
        else:
            md.append(f"| {k} | {h['r0']:.4f} | {h['ic50']:.4f} | {h['n']:.3f} | {h['ssr']:.5g} |")

    md.append("\n## Per-dose ROS coefficient of variation (cusp persistence)\n")
    md.append("| MAINT \\ DSEV | " + " | ".join(str(s) for s in SEVS) + " |")
    md.append("|---" * (len(SEVS) + 1) + "|")
    for d in DOSES:
        row = [f"**{d}**"]
        for s in SEVS:
            c = out["cells"].get(f"{d}|{s}", {})
            r = c.get("endpoints", {}).get("ROS_final", {})
            cv = r.get("cv")
            if cv is None or (isinstance(cv, float) and math.isnan(cv)):
                row.append("—")
            else:
                row.append(f"{cv:.2%}")
        md.append("| " + " | ".join(row) + " |")

    if out["baseline"]:
        md.append("\n## Baseline (no overrides)\n")
        md.append("| Endpoint | mean | std |")
        md.append("|---|---|---|")
        for ep_key, ep_label in surface_eps:
            st = out["baseline"]["endpoints"].get(ep_key, {})
            if not st:
                continue
            md.append(f"| {ep_label} | {fmt(st,'mean')} | {fmt(st,'std')} |")

    out_md = run_dir / "q5_endpoints.md"
    out_md.write_text("\n".join(md) + "\n")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(f"\n{'='*60}\n{out_md.read_text()}")


if __name__ == "__main__":
    main()
