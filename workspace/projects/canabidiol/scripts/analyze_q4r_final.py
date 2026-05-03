#!/usr/bin/env python3
"""Analyze Q4r-final sweep: build the (MAINT_DOSE x DISEASE_SEVERITY) endpoint
surface from per-condition replicates.csv. Emit:
  - tables: NH, NFkB_p65, Abeta_Oligomer, ROS, GSH, GSSG, M1+M2, plasma/intra CBD
  - per-condition (mean, std, min, max, cv) on the key endpoints
  - bimodality flags on ROS / GSH at DSEV=2
  - a JSON of all numerics for substituting into main_v3.tex \\pending markers

Usage:
  python analyze_q4r_final.py <run_dir>

Reads <run_dir>/condition_*/replicates.csv. Writes:
  <run_dir>/q4r_endpoints.json
  <run_dir>/q4r_endpoints.md   (human-readable markdown summary)
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
    "Abeta_Monomer_final",
    "Abeta_Plaque_final",
    "ROS_final",
    "Glutathione_final",
    "GSSG_final",
    "Microglia_M1_final",
    "Microglia_M2_final",
    "TNFa_final",
    "IL1b_final",
    "IL6_final",
    "BDNF_final",
    "CBD_plasma_final",
    "CBD_intracellular_final",
    "CBD_extracellular_final",
    "Nrf2_free_final",
    "HO1_final",
    "SOD_final",
    "Neurotoxicity_firings",
    "BDNF_neuroprotection_firings",
]

# (MAINT_DOSE, DISEASE_SEVERITY) cells we expect.
DOSES = [0.0, 0.5, 2.0, 5.0]
SEVS = [0.0, 1.0, 2.0, 5.0]


def _key(d: float, s: float) -> str:
    return f"{float(d)}|{float(s)}"

CELL_RE = re.compile(
    r"condition_\[param\]_MAINT_DOSE_eq_(?P<dose>[0-9.]+)_\[param\]_DISEASE_SEVERITY_eq_(?P<sev>[0-9.]+)"
)


def parse_replicates(csv_path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with csv_path.open() as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)
    return rows


def stats(vals: list[float]) -> dict[str, float]:
    if not vals:
        return {"n": 0}
    n = len(vals)
    m = mean(vals)
    s = stdev(vals) if n > 1 else 0.0
    return {
        "n": n,
        "mean": m,
        "std": s,
        "min": min(vals),
        "max": max(vals),
        "cv": (s / m) if m != 0 else float("nan"),
    }


def bimodal_flag(vals: list[float], min_split: float = 0.1) -> bool:
    """Crude bimodality: split sorted values at the midpoint between extremes;
    flag bimodal if both halves have non-trivial population AND the per-half
    spread is small relative to the inter-cluster gap."""
    if len(vals) < 6:
        return False
    s = sorted(vals)
    lo, hi = s[0], s[-1]
    if hi - lo < min_split * max(abs(hi), 1e-9):
        return False
    mid = (lo + hi) / 2
    low = [v for v in s if v <= mid]
    high = [v for v in s if v > mid]
    if min(len(low), len(high)) < 0.15 * len(s):
        return False
    spread_low = (max(low) - min(low)) if low else 0.0
    spread_high = (max(high) - min(high)) if high else 0.0
    gap = (min(high) - max(low)) if (low and high) else 0.0
    return gap > max(spread_low, spread_high)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <run_dir>", file=sys.stderr)
        sys.exit(2)
    run_dir = Path(sys.argv[1])
    if not run_dir.is_dir():
        print(f"not a directory: {run_dir}", file=sys.stderr)
        sys.exit(2)

    out: dict = {"run_dir": str(run_dir), "cells": {}, "baseline": None}

    for cond_dir in sorted(run_dir.glob("condition_*")):
        rep = cond_dir / "replicates.csv"
        if not rep.exists():
            continue
        rows = parse_replicates(rep)
        cell: dict = {"n_replicates": len(rows), "endpoints": {}}
        for ep in ENDPOINTS:
            if not rows or ep not in rows[0]:
                continue
            try:
                vals = [float(r[ep]) for r in rows if r[ep] not in ("", None)]
            except ValueError:
                continue
            cell["endpoints"][ep] = stats(vals)
            if ep in ("ROS_final", "Glutathione_final", "Neuron_Health_final"):
                cell["endpoints"][ep]["bimodal"] = bimodal_flag(vals)
                cell["endpoints"][ep]["values"] = vals  # keep raw for histograms
        # M1+M2 invariant
        try:
            m1 = [float(r["Microglia_M1_final"]) for r in rows]
            m2 = [float(r["Microglia_M2_final"]) for r in rows]
            cell["microglia_total"] = stats([a + b for a, b in zip(m1, m2)])
        except (KeyError, ValueError):
            pass

        if cond_dir.name == "condition_Baseline":
            out["baseline"] = cell
            continue

        m = CELL_RE.match(cond_dir.name)
        if not m:
            continue
        dose = float(m["dose"])
        sev = float(m["sev"])
        out["cells"][_key(dose, sev)] = {"dose": dose, "severity": sev, **cell}

    out_json = run_dir / "q4r_endpoints.json"
    out_json.write_text(json.dumps(out, indent=2, default=str))

    # ---- Human-readable markdown ----
    md = []
    md.append(f"# Q4r-final endpoints — {run_dir.name}\n")

    def fmt(s: dict, key="mean", prec=3) -> str:
        if not s or "mean" not in s:
            return "—"
        v = s.get(key)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return "—"
        if abs(v) >= 1000:
            return f"{v:.0f}"
        if abs(v) >= 1:
            return f"{v:.{max(0, prec-1)}f}"
        return f"{v:.{prec}f}"

    def cell_for(d: float, s: float) -> dict:
        return out["cells"].get(_key(d, s), {})

    surface_eps = [
        ("Neuron_Health_final", "Neuron Health"),
        ("NFkB_p65_final", "NFkB p65"),
        ("Abeta_Oligomer_final", "Aβ Oligomer"),
        ("ROS_final", "ROS"),
        ("Glutathione_final", "GSH"),
        ("TNFa_final", "TNFα"),
        ("CBD_plasma_final", "CBD plasma"),
        ("CBD_intracellular_final", "CBD intracellular"),
    ]

    for ep_key, ep_label in surface_eps:
        md.append(f"\n## {ep_label} (mean ± std, n=30)\n")
        md.append("| MAINT \\ DSEV | " + " | ".join(str(s) for s in SEVS) + " |")
        md.append("|---" * (len(SEVS) + 1) + "|")
        for d in DOSES:
            row = [f"**{d}**"]
            for s in SEVS:
                c = cell_for(d, s)
                eps = c.get("endpoints", {})
                st = eps.get(ep_key, {})
                if not st:
                    row.append("—")
                else:
                    row.append(f"{fmt(st, 'mean')} ± {fmt(st, 'std')}")
            md.append("| " + " | ".join(row) + " |")

    # CV table for ROS at every cell — to detect bimodal cusp
    md.append("\n## ROS coefficient of variation (cusp detector)\n")
    md.append("| MAINT \\ DSEV | " + " | ".join(str(s) for s in SEVS) + " |")
    md.append("|---" * (len(SEVS) + 1) + "|")
    for d in DOSES:
        row = [f"**{d}**"]
        for s in SEVS:
            c = cell_for(d, s)
            ros = c.get("endpoints", {}).get("ROS_final", {})
            cv = ros.get("cv")
            bm = ros.get("bimodal", False)
            if cv is None or (isinstance(cv, float) and math.isnan(cv)):
                row.append("—")
            else:
                tag = " ⚠bi" if bm else ""
                row.append(f"{cv:.2%}{tag}")
        md.append("| " + " | ".join(row) + " |")

    md.append("\n## GSH coefficient of variation\n")
    md.append("| MAINT \\ DSEV | " + " | ".join(str(s) for s in SEVS) + " |")
    md.append("|---" * (len(SEVS) + 1) + "|")
    for d in DOSES:
        row = [f"**{d}**"]
        for s in SEVS:
            c = cell_for(d, s)
            gsh = c.get("endpoints", {}).get("Glutathione_final", {})
            cv = gsh.get("cv")
            bm = gsh.get("bimodal", False)
            if cv is None or (isinstance(cv, float) and math.isnan(cv)):
                row.append("—")
            else:
                tag = " ⚠bi" if bm else ""
                row.append(f"{cv:.2%}{tag}")
        md.append("| " + " | ".join(row) + " |")

    # Microglia conservation
    md.append("\n## Microglia M1+M2 (conservation check)\n")
    md.append("| MAINT \\ DSEV | " + " | ".join(str(s) for s in SEVS) + " |")
    md.append("|---" * (len(SEVS) + 1) + "|")
    for d in DOSES:
        row = [f"**{d}**"]
        for s in SEVS:
            c = cell_for(d, s)
            tot = c.get("microglia_total", {})
            row.append(f"{fmt(tot, 'mean')} ± {fmt(tot, 'std')}" if tot else "—")
        md.append("| " + " | ".join(row) + " |")

    # Baseline cell
    if out["baseline"]:
        md.append("\n## Baseline (model defaults, no overrides)\n")
        md.append("| Endpoint | mean | std | min | max |")
        md.append("|---|---|---|---|---|")
        for ep_key, ep_label in surface_eps + [
            ("Microglia_M1_final", "M1"),
            ("Microglia_M2_final", "M2"),
            ("BDNF_final", "BDNF"),
            ("Neurotoxicity_firings", "Neurotox firings"),
        ]:
            st = out["baseline"]["endpoints"].get(ep_key, {})
            if not st:
                continue
            md.append(
                f"| {ep_label} | {fmt(st,'mean')} | {fmt(st,'std')} | "
                f"{fmt(st,'min')} | {fmt(st,'max')} |"
            )

    # Dissociation gap summary at DSEV=1, varying dose
    md.append("\n## Dissociation gap: NF\u03baB vs Neuron Health by dose at DSEV=1\n")
    md.append("| MAINT_DOSE | NFkB p65 (mean) | Neuron Health (mean) |")
    md.append("|---|---|---|")
    for d in DOSES:
        c = cell_for(d, 1)
        eps = c.get("endpoints", {})
        nf = eps.get("NFkB_p65_final", {})
        nh = eps.get("Neuron_Health_final", {})
        md.append(f"| {d} | {fmt(nf,'mean')} | {fmt(nh,'mean')} |")

    out_md = run_dir / "q4r_endpoints.md"
    out_md.write_text("\n".join(md) + "\n")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(f"\n{'='*60}\n{out_md.read_text()}")


if __name__ == "__main__":
    main()
