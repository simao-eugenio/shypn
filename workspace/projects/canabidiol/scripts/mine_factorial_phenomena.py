#!/usr/bin/env python3
"""Mine a canabidiol factorial sweep for emergent biological phenomena.

Targets a single ``run_<timestamp>/`` directory produced by
``shypn.cli.sweep`` and looks for:

    1. Bimodality / basins of attraction
       - Per-condition Hartigan-like bimodality coefficient (BC) on
         each replicate-final species, plus a mode-gap heuristic.
    2. Critical-slowing / variance peaking
       - Coefficient of variation (CV) of replicate-final values
         across the CBD ladder for each (Age, pH); a peak in CV
         flags a tipping point.
    3. Preemption cascades
       - Mean-trajectory cross-correlation between upstream signals
         (NFkB_p65, ROS, Abeta_Oligomer) and Neuron_Health: lag of
         peak |corr| reveals ordering of regulatory events.
    4. Pseudo-hysteresis (ramp asymmetry surrogate)
       - Without a true forward/reverse ramp we cannot prove
         hysteresis; instead we report dose pairs straddling the
         EC50 whose replicate distributions overlap > 30%, which
         is necessary (not sufficient) for hysteretic switching.

The script is read-only and self-contained: pure stdlib + numpy +
optional scipy.  Designed to run on the GPU server where data lives
(no client fetch required).

Usage (on remote-gpu):

    python3 mine_factorial_phenomena.py \\
        --run /home/simao/data/results/canabidiol/run_20260421_204933 \\
        [--report report.md]

Outputs:
    * stdout / report file: human-readable Markdown summary.
    * <run>/mining_phenomena.json: machine-readable per-condition
      and per-axis findings.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from scipy.stats import skew, kurtosis  # type: ignore
    _HAVE_SCIPY = True
except ImportError:  # pragma: no cover
    _HAVE_SCIPY = False


# ── Per-condition replicate analysis ────────────────────────────────


def bimodality_coefficient(x: np.ndarray) -> float:
    """SAS-style bimodality coefficient (BC > 5/9 ≈ 0.555 suggests bimodal).

    BC = (g² + 1) / (k + 3·(n-1)² / ((n-2)(n-3)))
    where g = sample skewness, k = sample excess kurtosis.
    """
    n = len(x)
    if n < 4 or np.std(x) < 1e-12:
        return float("nan")
    if _HAVE_SCIPY:
        g = float(skew(x, bias=False))
        k = float(kurtosis(x, fisher=True, bias=False))
    else:
        # numpy fallback (biased moments — close enough for screening)
        m = x.mean()
        d = x - m
        m2 = (d ** 2).mean()
        m3 = (d ** 3).mean()
        m4 = (d ** 4).mean()
        if m2 < 1e-24:
            return float("nan")
        g = m3 / (m2 ** 1.5)
        k = m4 / (m2 ** 2) - 3.0
    correction = 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return float((g * g + 1.0) / (k + correction))


def mode_gap(x: np.ndarray, bins: int = 12) -> Tuple[float, float]:
    """Crude two-mode detector: (gap, fraction_in_minor_mode).

    Builds a histogram, finds two highest peaks separated by ≥ 2 bins,
    returns the relative dip depth between them and the population
    fraction in the smaller peak.  Returns (nan, nan) if no clear gap.
    """
    if len(x) < 6 or np.ptp(x) < 1e-12:
        return float("nan"), float("nan")
    hist, edges = np.histogram(x, bins=bins)
    if hist.max() == 0:
        return float("nan"), float("nan")
    # find peaks
    peaks: List[Tuple[int, int]] = []
    for i in range(len(hist)):
        l = hist[i - 1] if i > 0 else -1
        r = hist[i + 1] if i + 1 < len(hist) else -1
        if hist[i] > l and hist[i] >= r and hist[i] > 0:
            peaks.append((i, hist[i]))
    if len(peaks) < 2:
        return float("nan"), float("nan")
    peaks.sort(key=lambda p: -p[1])
    (i1, h1), (i2, h2) = peaks[0], peaks[1]
    if abs(i1 - i2) < 2:
        return float("nan"), float("nan")
    lo, hi = sorted([i1, i2])
    valley = hist[lo + 1:hi].min() if hi - lo > 1 else min(h1, h2)
    gap = 1.0 - valley / max(h1, h2)
    minor_frac = h2 / (h1 + h2)
    return float(gap), float(minor_frac)


def analyse_replicates(replicates_csv: Path) -> Dict[str, Dict[str, float]]:
    """Return {species_final_col: {bc, mode_gap, minor_frac, cv, n}}."""
    out: Dict[str, Dict[str, float]] = {}
    with replicates_csv.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return out
    final_cols = [c for c in rows[0] if c.endswith("_final")]
    for col in final_cols:
        vals = []
        for r in rows:
            try:
                vals.append(float(r[col]))
            except (ValueError, KeyError):
                pass
        if len(vals) < 4:
            continue
        arr = np.asarray(vals, dtype=float)
        mu = float(arr.mean())
        sd = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
        cv = (sd / abs(mu)) if abs(mu) > 1e-12 else float("nan")
        bc = bimodality_coefficient(arr)
        gap, minor = mode_gap(arr)
        out[col] = {
            "n": len(arr),
            "mean": mu,
            "std": sd,
            "cv": cv,
            "bc": bc,
            "mode_gap": gap,
            "minor_frac": minor,
        }
    return out


# ── Trajectory (mean-time-series) analysis ──────────────────────────


def load_trajectory_means(stats_json: Path,
                          species: List[str]) -> Optional[Dict[str, np.ndarray]]:
    """Load mean trajectories for selected species.

    statistics.json schema (observed):
        { "n_replicates": int,
          "time_points": [...],
          "species_statistics": { "<species>": { "mean": [...], "std": [...] } },
          ... }
    """
    try:
        with stats_json.open() as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    out: Dict[str, np.ndarray] = {}
    t = np.asarray(data.get("time_points", []), dtype=float)
    if t.size == 0:
        return None
    out["__t__"] = t
    sp = data.get("species_statistics", {})
    for s in species:
        if s in sp and "mean" in sp[s]:
            arr = np.asarray(sp[s]["mean"], dtype=float)
            if arr.shape == t.shape:
                out[s] = arr
    return out if len(out) > 1 else None


def cross_correlation_lag(x: np.ndarray, y: np.ndarray,
                          dt: float, max_lag_steps: int = 200) -> Tuple[float, float]:
    """Return (best_lag_in_time_units, peak_pearson_r).

    Positive lag means y trails x (x predicts y).
    """
    x = (x - x.mean()) / (x.std() + 1e-12)
    y = (y - y.mean()) / (y.std() + 1e-12)
    n = len(x)
    max_lag = min(max_lag_steps, n // 4)
    best_r = 0.0
    best_k = 0
    for k in range(-max_lag, max_lag + 1):
        if k >= 0:
            xs, ys = x[: n - k], y[k:]
        else:
            xs, ys = x[-k:], y[: n + k]
        if len(xs) < 8:
            continue
        r = float(np.dot(xs, ys) / len(xs))
        if abs(r) > abs(best_r):
            best_r, best_k = r, k
    return best_k * dt, best_r


# ── Sweep-axis aggregation ──────────────────────────────────────────


def parse_condition_name(name: str) -> Dict[str, float]:
    """Parse ``condition_X_eq_v_Y_eq_v_..._<index>`` into dict.

    Tolerant of different separators; falls back to empty dict.
    """
    out: Dict[str, float] = {}
    if not name.startswith("condition_"):
        return out
    body = name[len("condition_"):]
    # tokens look like ``CBD_extracellular_eq_12_Age_eq_65_pH_eq_7.4``
    tokens = body.split("_eq_")
    if len(tokens) < 2:
        return out
    # First token is first param name; subsequent tokens are
    # ``<value>_<next_param_name>`` until last which is just <value>.
    keys = [tokens[0]]
    vals: List[str] = []
    for t in tokens[1:-1]:
        # split off last underscore-segments as param name; greedy:
        # value is the leading numeric run.
        i = 0
        while i < len(t) and (t[i].isdigit() or t[i] in ".-+e"):
            i += 1
        vals.append(t[:i])
        keys.append(t[i + 1:] if i < len(t) else "")
    vals.append(tokens[-1])
    for k, v in zip(keys, vals):
        try:
            out[k] = float(v)
        except ValueError:
            continue
    return out


def index_conditions(run_dir: Path) -> List[Tuple[Path, Dict[str, float]]]:
    out: List[Tuple[Path, Dict[str, float]]] = []
    for d in sorted(run_dir.iterdir()):
        if d.is_dir() and d.name.startswith("condition_"):
            out.append((d, parse_condition_name(d.name)))
    return out


# ── Main mining pipeline ────────────────────────────────────────────


CASCADE_SPECIES = [
    "NFkB_p65", "ROS", "Abeta_Oligomer", "AMPK", "Caspase3",
    "Neuron_Health",
]


def mine_run(run_dir: Path) -> Dict:
    print(f"Mining {run_dir} …", file=sys.stderr)
    conditions = index_conditions(run_dir)
    print(f"  {len(conditions)} conditions", file=sys.stderr)

    per_cond: List[Dict] = []
    for cdir, axes in conditions:
        rep_csv = cdir / "replicates.csv"
        rep_stats = analyse_replicates(rep_csv) if rep_csv.exists() else {}
        per_cond.append({
            "condition": cdir.name,
            "axes": axes,
            "replicate_stats": rep_stats,
        })

    # Cascade timing: pick a representative condition near EC50
    # (CBD ≈ 1 µM, Age 65, pH 7.4) and a saturating one (CBD ≈ 7 µM)
    cascade = mine_cascade_timing(run_dir, conditions)

    # Variance / bimodality landscape across axes
    landscape = build_landscape(per_cond)

    return {
        "run": str(run_dir),
        "n_conditions": len(conditions),
        "cascade_timing": cascade,
        "landscape": landscape,
        "per_condition": per_cond,
    }


def _pick(conds, **want) -> Optional[Path]:
    for cdir, axes in conds:
        if all(abs(axes.get(k, math.nan) - v) < 1e-6 for k, v in want.items()):
            return cdir
    return None


def mine_cascade_timing(run_dir: Path,
                        conds: List[Tuple[Path, Dict[str, float]]]) -> Dict:
    out: Dict = {}
    targets = [
        ("at_ec50",        {"CBD_extracellular": 1.0, "Age": 65, "pH": 7.4}),
        ("near_threshold", {"CBD_extracellular": 0.7, "Age": 65, "pH": 7.4}),
        ("saturating",     {"CBD_extracellular": 7.0, "Age": 65, "pH": 7.4}),
    ]
    for label, want in targets:
        cdir = _pick(conds, **want)
        if cdir is None:
            out[label] = {"selected": None}
            continue
        sj = cdir / "statistics.json"
        if not sj.exists():
            out[label] = {"selected": cdir.name, "error": "no statistics.json"}
            continue
        traj = load_trajectory_means(sj, CASCADE_SPECIES)
        if traj is None:
            out[label] = {"selected": cdir.name, "error": "cannot load trajectories"}
            continue
        t = traj.pop("__t__")
        if len(t) < 4:
            out[label] = {"selected": cdir.name, "error": "trajectory too short"}
            continue
        dt = float(np.median(np.diff(t)))
        anchor = "Neuron_Health"
        if anchor not in traj:
            out[label] = {"selected": cdir.name,
                          "error": f"no {anchor} trajectory"}
            continue
        lags: Dict[str, Dict[str, float]] = {}
        for s, y in traj.items():
            if s == anchor:
                continue
            lag_t, r = cross_correlation_lag(y, traj[anchor], dt=dt)
            lags[s] = {"lag_to_NeuronHealth_s": lag_t, "peak_r": r}
        out[label] = {
            "selected": cdir.name,
            "dt_s": dt,
            "t_max_s": float(t[-1]),
            "lags": lags,
        }
    return out


def build_landscape(per_cond: List[Dict]) -> Dict:
    """Aggregate CV and bimodality counts over the (Age, pH, CBD) grid."""
    by_axis: Dict[str, Dict[Tuple[float, float], List[Dict]]] = defaultdict(
        lambda: defaultdict(list)
    )
    species_seen: set = set()
    for c in per_cond:
        a = c["axes"]
        cbd = a.get("CBD_extracellular")
        age = a.get("Age")
        ph = a.get("pH")
        if None in (cbd, age, ph):
            continue
        for sp, st in c["replicate_stats"].items():
            species_seen.add(sp)
            by_axis[sp][(age, ph)].append({
                "cbd": cbd, **st,
            })

    out: Dict[str, Dict] = {}
    for sp, by_ap in by_axis.items():
        cv_peaks: List[Dict] = []
        bimodal_hits: List[Dict] = []
        for (age, ph), pts in by_ap.items():
            pts.sort(key=lambda r: r["cbd"])
            cvs = [(p["cbd"], p["cv"]) for p in pts
                   if p["cv"] is not None and not math.isnan(p["cv"])]
            if cvs:
                peak_cbd, peak_cv = max(cvs, key=lambda x: x[1])
                # Only flag if peak clearly above the median
                med = float(np.median([v for _, v in cvs]))
                if peak_cv > 1.5 * med and peak_cv > 0.05:
                    cv_peaks.append({"age": age, "pH": ph,
                                     "peak_cbd": peak_cbd,
                                     "peak_cv": peak_cv,
                                     "median_cv": med})
            for p in pts:
                if (p["bc"] is not None and not math.isnan(p["bc"])
                        and p["bc"] > 0.555):
                    bimodal_hits.append({
                        "age": age, "pH": ph, "cbd": p["cbd"],
                        "bc": p["bc"], "mode_gap": p["mode_gap"],
                        "minor_frac": p["minor_frac"],
                    })
        out[sp] = {
            "cv_peaks": cv_peaks,
            "bimodal_hits": bimodal_hits,
        }
    return out


# ── Markdown report ─────────────────────────────────────────────────


def render_report(findings: Dict) -> str:
    lines: List[str] = []
    lines.append(f"# Phenomena mining — {Path(findings['run']).name}")
    lines.append(f"\n**Run:** `{findings['run']}`  ")
    lines.append(f"**Conditions:** {findings['n_conditions']}\n")

    # 1. Cascade timing
    lines.append("## 1. Preemption-cascade ordering")
    lines.append("Lag of peak |Pearson r| between each upstream species "
                 "and Neuron_Health, in seconds. Negative lag → species "
                 "leads Neuron_Health (predictor); positive → trails.\n")
    for label, blk in findings["cascade_timing"].items():
        lines.append(f"### {label} — `{blk.get('selected')}`")
        if "error" in blk:
            lines.append(f"_{blk['error']}_\n")
            continue
        lines.append(f"dt = {blk['dt_s']:.3g} s, t_max = {blk['t_max_s']:.3g} s\n")
        lines.append("| species | lag → Neuron_Health (s) | peak r |")
        lines.append("|---|---:|---:|")
        for s, ld in sorted(blk["lags"].items(),
                            key=lambda kv: kv[1]["lag_to_NeuronHealth_s"]):
            lines.append(f"| {s} | {ld['lag_to_NeuronHealth_s']:+.2f} "
                         f"| {ld['peak_r']:+.3f} |")
        lines.append("")

    # 2. Variance peaks
    lines.append("## 2. CV peaks (critical-slowing surrogates)")
    lines.append("Per (Age, pH) the CBD value where replicate-final "
                 "CV peaks at > 1.5× median.\n")
    any_peak = False
    for sp, lf in findings["landscape"].items():
        if not lf["cv_peaks"]:
            continue
        any_peak = True
        lines.append(f"### {sp}")
        lines.append("| Age | pH | peak CBD | peak CV | median CV |")
        lines.append("|---:|---:|---:|---:|---:|")
        for r in sorted(lf["cv_peaks"], key=lambda r: (r["age"], r["pH"])):
            lines.append(f"| {r['age']:.0f} | {r['pH']:.2f} "
                         f"| {r['peak_cbd']:.2f} | {r['peak_cv']:.3f} "
                         f"| {r['median_cv']:.3f} |")
        lines.append("")
    if not any_peak:
        lines.append("_No CV peaks above threshold._\n")

    # 3. Bimodality
    lines.append("## 3. Bimodality / basins of attraction")
    lines.append("Conditions with bimodality coefficient BC > 0.555 "
                 "(SAS criterion) on replicate-final values.\n")
    any_bim = False
    for sp, lf in findings["landscape"].items():
        if not lf["bimodal_hits"]:
            continue
        any_bim = True
        lines.append(f"### {sp}")
        lines.append("| Age | pH | CBD | BC | mode-gap | minor-frac |")
        lines.append("|---:|---:|---:|---:|---:|---:|")
        for r in sorted(lf["bimodal_hits"],
                        key=lambda r: (r["age"], r["pH"], r["cbd"])):
            lines.append(f"| {r['age']:.0f} | {r['pH']:.2f} | {r['cbd']:.2f} "
                         f"| {r['bc']:.3f} "
                         f"| {r['mode_gap']:.2f} "
                         f"| {r['minor_frac']:.2f} |")
        lines.append("")
    if not any_bim:
        lines.append("_No bimodal conditions detected by BC criterion._\n")

    # 4. Hysteresis surrogate note
    lines.append("## 4. Hysteresis caveat")
    lines.append("True hysteresis requires forward + reverse CBD ramps; "
                 "the current factorial sweep does not provide them.  "
                 "Bimodality + CV peaks at the same CBD value are the "
                 "*necessary* fingerprint and are reported above.")
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", required=True, type=Path,
                   help="Path to a sweep run_<timestamp> directory.")
    p.add_argument("--report", type=Path, default=None,
                   help="Optional output Markdown report path "
                        "(default: prints to stdout).")
    p.add_argument("--json", type=Path, default=None,
                   help="Optional output JSON path "
                        "(default: <run>/mining_phenomena.json).")
    args = p.parse_args(argv)

    if not args.run.is_dir():
        p.error(f"--run {args.run} is not a directory")

    findings = mine_run(args.run)

    json_path = args.json or (args.run / "mining_phenomena.json")
    try:
        json_path.write_text(json.dumps(findings, indent=2, default=str))
        print(f"JSON written to {json_path}", file=sys.stderr)
    except OSError as exc:
        print(f"WARN: cannot write JSON ({exc})", file=sys.stderr)

    report = render_report(findings)
    if args.report:
        args.report.write_text(report)
        print(f"Report written to {args.report}", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
