#!/usr/bin/env python3
"""Factorial sweep analysis: CBD x Age x pH.

Reads `replicates.csv` from each `condition_*/` dir under a sweep run and
reports endpoint means +/- stdev plus deltas vs Baseline. Writes results to
stdout and to `<run_dir>/factorial_summary.csv`.

Usage:
    python analyze_factorial_cbd.py [<run_dir>]

If <run_dir> is omitted, the most recent run under
workspace/projects/canabidiol/experiments/results/ is used.
"""
from __future__ import annotations

import csv
import re
import statistics as st
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_RESULTS = Path(__file__).resolve().parents[1] / "experiments" / "results"

# Endpoint short names -> CSV column suffix (column = <name>_final)
ENDPOINTS = [
    "Abeta_Plaque", "Abeta_Oligomer", "Abeta_Monomer",
    "TNFa", "IL1b", "IL6", "NFkB_p65", "COX2",
    "ROS", "Glutathione", "Nrf2_free", "HO1", "SOD",
    "Microglia_M1", "Microglia_M2",
    "Neuron_Health", "BDNF",
    "CBD_intracellular",
]

CONDITION_RE = re.compile(
    r"CBD_extracellular_eq_([0-9.]+)_Age_eq_(\d+)_pH_eq_([0-9.]+)"
)


def parse_condition(name: str) -> Tuple[str, ...] | None:
    """Return (cbd, age, pH) or None for Baseline."""
    if name == "Baseline":
        return None
    m = CONDITION_RE.match(name)
    if not m:
        return None
    return (m.group(1), m.group(2), m.group(3))


def load_replicates(csv_path: Path) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    with csv_path.open() as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            converted: Dict[str, float] = {}
            for k, v in r.items():
                try:
                    converted[k] = float(v)
                except (TypeError, ValueError):
                    pass
            rows.append(converted)
    return rows


def summarise(rows: List[Dict[str, float]]) -> Dict[str, Tuple[float, float]]:
    out: Dict[str, Tuple[float, float]] = {}
    for ep in ENDPOINTS:
        col = f"{ep}_final"
        vals = [r[col] for r in rows if col in r]
        if not vals:
            continue
        m = st.mean(vals)
        s = st.stdev(vals) if len(vals) > 1 else 0.0
        out[ep] = (m, s)
    return out


def fmt(m: float, s: float) -> str:
    return f"{m:>10.3g} +/- {s:<8.2g}"


def pct_delta(cur: float, base: float) -> str:
    if base == 0:
        return "  n/a"
    return f"{100.0 * (cur - base) / base:+7.1f}%"


def main(argv: List[str]) -> int:
    if len(argv) > 1:
        run_dir = Path(argv[1]).expanduser().resolve()
    else:
        if not PROJECT_RESULTS.exists():
            print(f"error: results dir not found: {PROJECT_RESULTS}", file=sys.stderr)
            return 1
        runs = sorted(p for p in PROJECT_RESULTS.iterdir() if p.is_dir() and p.name.startswith("run_"))
        if not runs:
            print(f"error: no run_* dirs under {PROJECT_RESULTS}", file=sys.stderr)
            return 1
        run_dir = runs[-1]

    print(f"Run: {run_dir}")
    cond_dirs = sorted(p for p in run_dir.iterdir() if p.is_dir() and p.name.startswith("condition_"))
    if not cond_dirs:
        print("no condition_* dirs found", file=sys.stderr)
        return 1

    summaries: Dict[str, Dict[str, Tuple[float, float]]] = {}
    factor_keys: Dict[str, Tuple[str, ...] | None] = {}
    for d in cond_dirs:
        name = d.name[len("condition_"):]
        rows = load_replicates(d / "replicates.csv")
        summaries[name] = summarise(rows)
        factor_keys[name] = parse_condition(name)
        print(f"  loaded {name}: {len(rows)} replicates")

    baseline = summaries.get("Baseline")
    if not baseline:
        print("warning: no Baseline condition", file=sys.stderr)

    # Print compact endpoint table for each endpoint
    print()
    print("=" * 100)
    print(f"{'Condition':<45}", end="")
    for ep in ENDPOINTS[:6]:
        print(f"  {ep[:14]:>14}", end="")
    print()
    print("-" * 100)
    for name in ["Baseline"] + sorted(n for n in summaries if n != "Baseline"):
        if name not in summaries:
            continue
        print(f"{name[:45]:<45}", end="")
        for ep in ENDPOINTS[:6]:
            m = summaries[name].get(ep, (float("nan"), 0.0))[0]
            print(f"  {m:>14.3g}", end="")
        print()
    print()

    # Delta vs baseline table
    if baseline:
        print("=" * 100)
        print("DELTA vs Baseline (mean of replicates)")
        print("=" * 100)
        for ep in ENDPOINTS:
            base_m = baseline.get(ep, (0.0, 0.0))[0]
            print(f"\n{ep}  (baseline = {base_m:.3g})")
            for name in sorted(summaries):
                if name == "Baseline":
                    continue
                cur = summaries[name].get(ep, (float("nan"), 0.0))[0]
                print(f"  {name:<48} {cur:>10.3g}  ({pct_delta(cur, base_m)})")

    # Marginal effects: average over the other two factors
    print()
    print("=" * 100)
    print("MARGINAL EFFECTS (mean across the other two factors)")
    print("=" * 100)
    factors = {"CBD": 0, "Age": 1, "pH": 2}
    for fname, idx in factors.items():
        levels: Dict[str, List[Dict[str, Tuple[float, float]]]] = {}
        for name, key in factor_keys.items():
            if key is None:
                continue
            levels.setdefault(key[idx], []).append(summaries[name])
        print(f"\n{fname} effect (n_conditions per level):")
        for level in sorted(levels, key=lambda x: float(x)):
            grp = levels[level]
            print(f"  {fname}={level} (n={len(grp)}):")
            for ep in ["Abeta_Plaque", "TNFa", "ROS", "Neuron_Health", "BDNF", "CBD_intracellular"]:
                vals = [s.get(ep, (float("nan"), 0.0))[0] for s in grp]
                m = sum(vals) / len(vals) if vals else float("nan")
                print(f"    {ep:<22} = {m:>10.3g}")

    # Write summary CSV
    out_csv = run_dir / "factorial_summary.csv"
    with out_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        header = ["condition", "CBD", "Age", "pH"]
        for ep in ENDPOINTS:
            header += [f"{ep}_mean", f"{ep}_std"]
        w.writerow(header)
        for name in ["Baseline"] + sorted(n for n in summaries if n != "Baseline"):
            if name not in summaries:
                continue
            key = factor_keys.get(name)
            row = [name] + (list(key) if key else ["", "", ""])
            for ep in ENDPOINTS:
                m, s = summaries[name].get(ep, (float("nan"), float("nan")))
                row += [f"{m:.6g}", f"{s:.6g}"]
            w.writerow(row)
    print(f"\nWrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
