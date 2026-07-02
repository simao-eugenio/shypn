"""Dose-response analysis for the LOADING_DOSE sweep (run_20260428_134948).

Server-side runner: reads each condition_*/replicates.csv (endpoint
scalars per replicate) plus statistics.json (per-step trajectories
mean/std), and emits a compact text report + dose-response CSV.

Designed to run in-place on the server — no GUI deps, only stdlib.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from statistics import mean, pstdev


RUN_DIR = Path(
    "workspace/projects/canabidiol/experiments/results/run_20260428_134948"
)

# Canonical biological readouts (column suffix in replicates.csv).
# Order matters: report follows it.
READOUTS = [
    # Pathology — want LOW
    "Abeta_Monomer", "Abeta_Oligomer", "Abeta_Plaque",
    # Inflammation — want LOW
    "NFkB_p65", "TNFa", "IL1b", "IL6", "COX2", "ROS",
    # Defence / repair — want HIGH
    "Nrf2_free", "HO1", "SOD", "Glutathione",
    "Neuron_Health", "BDNF",
    # CBD pharmacology
    "CBD_extracellular", "CBD_intracellular",
    "PPARg_active", "HT1A_active", "A2A_active",
    # Microglia state
    "Microglia_M1", "Microglia_M2",
]

KEY_FIRINGS = [
    "CBD_Absorption", "CBD_Efflux", "CBD_Systemic_Clearance",
    "CBD_Brain_Metabolism",
    "Abeta_Production", "Abeta_Aggregation", "Plaque_Formation",
    "Plaque_Clearance",
    "Neurotoxicity", "BDNF_neuroprotection",
    "NFkB_transcription", "PPARg_inhibits_NFkB",
    "Nrf2_ARE_transcription", "Antioxidant_Scavenging",
]


def parse_dose(condition: str) -> float | None:
    """Return numeric LOADING_DOSE or None for Baseline."""
    if condition == "Baseline":
        return None
    m = re.search(r"LOADING_DOSE\D+(\d+(?:\.\d+)?)", condition)
    return float(m.group(1)) if m else None


def load_replicates(cond_dir: Path) -> list[dict]:
    with open(cond_dir / "replicates.csv", newline="") as fh:
        return list(csv.DictReader(fh))


def stat_pair(values: list[float]) -> tuple[float, float, float]:
    """Return (mean, std, cv%)."""
    if not values:
        return (float("nan"),) * 3
    m = mean(values)
    s = pstdev(values) if len(values) > 1 else 0.0
    cv = (s / m * 100.0) if abs(m) > 1e-12 else 0.0
    return m, s, cv


def main() -> int:
    if not RUN_DIR.is_dir():
        print(f"ERROR: run dir not found: {RUN_DIR}", file=sys.stderr)
        return 1

    cond_dirs = sorted(
        p for p in RUN_DIR.glob("condition_*") if p.is_dir()
    )
    print(f"Found {len(cond_dirs)} conditions in {RUN_DIR}\n")

    # ── Per-condition aggregation ─────────────────────────────────────
    rows: list[dict] = []
    for cd in cond_dirs:
        label = cd.name.removeprefix("condition_")
        dose = parse_dose(label)
        reps = load_replicates(cd)
        n = len(reps)

        row: dict = {"condition": label, "dose": dose, "n_reps": n}

        # Stopped-reason distribution
        reasons: dict[str, int] = {}
        for r in reps:
            reasons[r.get("stopped_reason", "")] = reasons.get(
                r.get("stopped_reason", ""), 0) + 1
        row["stopped"] = ";".join(
            f"{k or 'NA'}={v}" for k, v in sorted(reasons.items())
        )
        ftime = [float(r["final_time"]) for r in reps if r.get("final_time")]
        row["final_time_mean"] = mean(ftime) if ftime else float("nan")

        for key in READOUTS + KEY_FIRINGS:
            suffix = "_final" if key in READOUTS else "_firings"
            col = key + suffix
            vals = []
            for r in reps:
                v = r.get(col, "")
                if v == "":
                    continue
                try:
                    vals.append(float(v))
                except ValueError:
                    pass
            if not vals:
                row[key] = (float("nan"),) * 3
            else:
                row[key] = stat_pair(vals)
        rows.append(row)

    # ── Pretty report ─────────────────────────────────────────────────
    baseline = next((r for r in rows if r["condition"] == "Baseline"), None)
    dosed = sorted(
        (r for r in rows if r["dose"] is not None),
        key=lambda r: r["dose"],
    )

    print("=" * 78)
    print("RUN INTEGRITY")
    print("=" * 78)
    print(f"{'condition':40s} {'n':>3} {'final_t':>8} {'stopped'}")
    for r in rows:
        print(f"{r['condition']:40s} {r['n_reps']:>3d} "
              f"{r['final_time_mean']:>8.0f}  {r['stopped']}")

    print()
    print("=" * 78)
    print("DOSE–RESPONSE — endpoints (mean ± std, CV%)")
    print("=" * 78)

    # Header: dose levels
    dose_labels = ([f"Baseline"] +
                   [f"LD={int(d['dose'])}" for d in dosed])
    cols = [baseline] + dosed if baseline else dosed
    header = f"{'readout':22s}"
    for lbl in dose_labels:
        header += f" | {lbl:>22s}"
    print(header)
    print("-" * len(header))

    for key in READOUTS:
        line = f"{key:22s}"
        for c in cols:
            m, s, cv = c[key]
            line += f" | {m:9.3g}±{s:7.3g} ({cv:4.1f}%)"
        print(line)

    print()
    print("=" * 78)
    print("KEY TRANSITION FIRING COUNTS (mean across replicates)")
    print("=" * 78)
    line = f"{'transition':28s}"
    for lbl in dose_labels:
        line += f" | {lbl:>10s}"
    print(line)
    print("-" * len(line))
    for key in KEY_FIRINGS:
        line = f"{key:28s}"
        for c in cols:
            m, _, cv = c[key]
            line += f" | {m:>8.3g}({cv:3.0f}%)"
        print(line)

    # ── Δ vs baseline (% change) ──────────────────────────────────────
    if baseline:
        print()
        print("=" * 78)
        print("Δ ENDPOINTS vs Baseline  (% change of mean; |Δ|>5% bolded with *)")
        print("=" * 78)
        line = f"{'readout':22s}"
        for d in dosed:
            line += f" | LD={int(d['dose']):>4d}"
        print(line)
        print("-" * len(line))
        for key in READOUTS:
            base_m = baseline[key][0]
            line = f"{key:22s}"
            for d in dosed:
                m = d[key][0]
                if abs(base_m) < 1e-9:
                    cell = "  n/a "
                else:
                    pct = (m - base_m) / base_m * 100.0
                    star = "*" if abs(pct) >= 5.0 else " "
                    cell = f"{star}{pct:+6.1f}%"
                line += f" | {cell:>7s}"
            print(line)

    # ── Dump dose-response CSV ────────────────────────────────────────
    out_csv = RUN_DIR / "dose_response_endpoints.csv"
    with open(out_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        header = ["condition", "dose", "n_reps"]
        for k in READOUTS:
            header += [f"{k}_mean", f"{k}_std", f"{k}_cv"]
        for k in KEY_FIRINGS:
            header += [f"{k}_firings_mean", f"{k}_firings_std"]
        w.writerow(header)
        for r in rows:
            row_out: list = [r["condition"], r["dose"], r["n_reps"]]
            for k in READOUTS:
                m, s, cv = r[k]
                row_out += [f"{m:.6g}", f"{s:.6g}", f"{cv:.3f}"]
            for k in KEY_FIRINGS:
                m, s, _ = r[k]
                row_out += [f"{m:.6g}", f"{s:.6g}"]
            w.writerow(row_out)
    print(f"\n[wrote] {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
