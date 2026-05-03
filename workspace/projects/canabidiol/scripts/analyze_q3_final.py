#!/usr/bin/env python3
"""Analyze Q3-final sweep: 1D DISEASE_SEVERITY dose-response (no CBD).

Conditions: Baseline (no override) + DSEV ∈ {0, 0.5, 1, 2, 3, 5} via P38.initial_marking.
Emits q3_endpoints.{json,md} into the run dir.

Two questions:
  1. Cascade monotonicity: do Aβ_O / NFκB / ROS / NH / GSH respond monotonically to DSEV?
  2. Override anomaly: does DSEV=0 (override applied, value = default) match Baseline
     (no override)? If not, the override mechanism — not the value — drives the NH=0 collapse.
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
    "Abeta_Monomer_final",
    "Abeta_Oligomer_final",
    "Abeta_Plaque_final",
    "ROS_final",
    "Glutathione_final",
    "TNFa_final",
    "BDNF_final",
    "Microglia_M1_final",
    "Microglia_M2_final",
    "PPARg_active_final",
    "CBD_intracellular_final",
    "Neurotoxicity_firings",
]
SEVS = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]

CELL_RE = re.compile(
    r"condition_\[param\]_DISEASE_SEVERITY_eq_(?P<sev>[0-9.]+)"
)


def stats(vals):
    if not vals:
        return {"n": 0}
    n = len(vals)
    m = mean(vals)
    s = stdev(vals) if n > 1 else 0.0
    return {"n": n, "mean": m, "std": s, "min": min(vals), "max": max(vals),
            "cv": (s / m) if m != 0 else float("nan")}


def main():
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <run_dir>", file=sys.stderr)
        sys.exit(2)
    run_dir = Path(sys.argv[1])
    out = {"run_dir": str(run_dir), "cells": {}, "baseline": None}

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
        s = float(m["sev"])
        out["cells"][f"{s}"] = {"severity": s, **cell}

    out_json = run_dir / "q3_endpoints.json"
    out_json.write_text(json.dumps(out, indent=2, default=str))

    md = [f"# Q3-final endpoints — {run_dir.name}\n",
          "Pure pathology dose-response: DSEV varied, MAINT_DOSE=0 (no CBD).\n"]

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

    # --- Cascade table: severity vs endpoints --------------------------------
    md.append("\n## Cascade response (mean ± std, n=30)\n")
    header = ["Endpoint", "Baseline"] + [f"DSEV={s}" for s in SEVS]
    md.append("| " + " | ".join(header) + " |")
    md.append("|" + "---|" * len(header))
    for ep_key in [
        "Neuron_Health_final", "Abeta_Monomer_final", "Abeta_Oligomer_final",
        "Abeta_Plaque_final", "NFkB_p65_final", "NFkB_IkB_final",
        "ROS_final", "Glutathione_final", "TNFa_final", "BDNF_final",
        "Microglia_M1_final", "Microglia_M2_final",
        "PPARg_active_final", "Neurotoxicity_firings",
    ]:
        row = [ep_key.replace("_final", "").replace("_firings", " (firings)")]
        b = (out["baseline"] or {}).get("endpoints", {}).get(ep_key, {})
        row.append(f"{fmt(b)} ± {fmt(b,'std')}" if b else "—")
        for s in SEVS:
            c = out["cells"].get(f"{s}", {})
            ep = c.get("endpoints", {}).get(ep_key, {})
            row.append(f"{fmt(ep)} ± {fmt(ep,'std')}" if ep else "—")
        md.append("| " + " | ".join(row) + " |")

    # --- Monotonicity check --------------------------------------------------
    md.append("\n## Monotonicity check (means across DSEV grid)\n")
    md.append("| Endpoint | trend | direction | notes |")
    md.append("|---|---|---|---|")
    for ep_key in ENDPOINTS:
        means = []
        for s in SEVS:
            ep = out["cells"].get(f"{s}", {}).get("endpoints", {}).get(ep_key, {})
            if "mean" in ep:
                means.append(ep["mean"])
            else:
                means.append(None)
        if any(m is None for m in means) or len(set(means)) <= 1:
            md.append(f"| {ep_key} | — | — | constant or missing |")
            continue
        diffs = [means[i+1] - means[i] for i in range(len(means)-1)]
        mono_up = all(d >= -1e-9 for d in diffs)
        mono_dn = all(d <= 1e-9 for d in diffs)
        if mono_up:
            trend = "monotone ↑"; direc = f"{means[0]:.3g} → {means[-1]:.3g}"
        elif mono_dn:
            trend = "monotone ↓"; direc = f"{means[0]:.3g} → {means[-1]:.3g}"
        else:
            trend = "non-monotone"
            direc = " → ".join(f"{m:.3g}" for m in means)
        md.append(f"| {ep_key} | {trend} | {direc} | |")

    # --- OVERRIDE ANOMALY DIAGNOSTIC -----------------------------------------
    md.append("\n## Override-mechanism diagnostic: Baseline vs DSEV=0\n")
    md.append("Both should be biologically identical (DSEV=0 ⇒ all install events no-op). "
              "Any divergence points to the override mechanism itself, not the value.\n")
    md.append("| Endpoint | Baseline (no override) | DSEV=0 (override applied) | Δ |")
    md.append("|---|---|---|---|")
    base_eps = (out["baseline"] or {}).get("endpoints", {})
    dsev0 = out["cells"].get("0.0", {}).get("endpoints", {})
    diverge_count = 0
    for ep_key in ENDPOINTS:
        b = base_eps.get(ep_key, {}); d = dsev0.get(ep_key, {})
        bm = b.get("mean"); dm = d.get("mean")
        if bm is None or dm is None:
            continue
        delta = dm - bm
        flag = ""
        if abs(delta) > 1e-6 * max(abs(bm), abs(dm), 1e-9):
            flag = " **⚠**"
            diverge_count += 1
        md.append(f"| {ep_key} | {fmt(b)} ± {fmt(b,'std')} | {fmt(d)} ± {fmt(d,'std')} | {delta:+.4g}{flag} |")
    md.append(f"\n**Divergent endpoints: {diverge_count} / {len(ENDPOINTS)}**.")
    if diverge_count > 0:
        md.append("Override mechanism perturbs the system even when set to its default value — "
                  "this is the source of the NH=0 collapse seen across Q4r and Q5 sweeps.")
    else:
        md.append("Override mechanism is value-neutral. NH collapse must be driven by non-zero DSEV "
                  "or by some other override (e.g. MAINT_DOSE applied separately).")

    out_md = run_dir / "q3_endpoints.md"
    out_md.write_text("\n".join(md) + "\n")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(f"\n{'='*60}\n{out_md.read_text()}")


if __name__ == "__main__":
    main()
