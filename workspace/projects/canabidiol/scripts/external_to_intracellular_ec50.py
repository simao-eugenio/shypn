"""External → intracellular CBD dose mapping.

For each (Age, pH) cell across the canabidiol sweep(s):
  1. Aggregate per-condition mean CBD_extracellular_final, CBD_intracellular_final,
     and Neuron_Health_final from `replicates.csv`.
  2. Fit a Hill curve of Neuron_Health vs CBD_intracellular → EC50_intra (95% CI),
     also derive EC90_intra analytically.
  3. Fit CBD_intracellular vs CBD_extracellular (saturable Hill or linear, whichever
     is better by RMSE) → invert to get the external dose required to maintain a
     given intracellular concentration at steady state.
  4. Report a table per (Age, pH): EC50_intra, EC90_intra, required external dose
     for each, and intra/extra ratio at EC50_intra.

Usage:
    python3 external_to_intracellular_ec50.py \\
        --runs /path/run_A /path/run_B \\
        --report /tmp/intracellular_ec50.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import curve_fit

CONDITION_RE = re.compile(r"condition_(.+)$")
# Accept both "Key=Value" (raw) and "Key_eq_Value" (filesystem-safe) condition dirs.
KV_RE = re.compile(r"(?P<k>[A-Za-z][A-Za-z0-9_]*?)(?:=|_eq_)(?P<v>-?\d+(?:\.\d+)?)")


def parse_condition_name(name: str) -> Optional[Dict[str, float]]:
    m = CONDITION_RE.match(name)
    if not m:
        return None
    body = m.group(1)
    if body.lower() == "baseline":
        return None
    out: Dict[str, float] = {}
    for kv in KV_RE.finditer(body):
        try:
            out[kv.group("k")] = float(kv.group("v"))
        except ValueError:
            return None
    return out


def load_replicates(csv_path: Path) -> Dict[str, List[float]]:
    cols: Dict[str, List[float]] = {}
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k, v in row.items():
                try:
                    cols.setdefault(k, []).append(float(v))
                except (TypeError, ValueError):
                    cols.setdefault(k, []).append(float("nan"))
    return cols


def hill_up(x, ec50, n, e0, emax):
    x = np.asarray(x, dtype=float)
    return e0 + (emax - e0) * (x ** n) / (ec50 ** n + x ** n)


def fit_hill_with_ci(x, y, n_boot=200, rng=None) -> Optional[Dict[str, float]]:
    rng = rng or np.random.default_rng(42)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y) & (x >= 0)
    x, y = x[mask], y[mask]
    if x.size < 4:
        return None
    # Sort by x for stability
    order = np.argsort(x)
    x, y = x[order], y[order]
    e0_init = float(y[0]) if x[0] == 0 else float(np.min(y))
    emax_init = float(np.max(y))
    ec50_init = float(np.median(x[x > 0])) if np.any(x > 0) else 1.0
    p0 = [max(ec50_init, 1e-3), 1.0, e0_init, emax_init]
    try:
        popt, _ = curve_fit(
            hill_up, x, y, p0=p0,
            bounds=([1e-6, 0.1, -1e3, -1e3], [1e6, 8.0, 1e3, 1e3]),
            maxfev=10000,
        )
    except Exception:
        return None
    yfit = hill_up(x, *popt)
    rmse = float(np.sqrt(np.mean((y - yfit) ** 2)))
    # Bootstrap on residuals
    resid = y - yfit
    ec50s: List[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, resid.size, resid.size)
        try:
            popt_b, _ = curve_fit(
                hill_up, x, yfit + resid[idx], p0=popt,
                bounds=([1e-6, 0.1, -1e3, -1e3], [1e6, 8.0, 1e3, 1e3]),
                maxfev=5000,
            )
            ec50s.append(popt_b[0])
        except Exception:
            continue
    if len(ec50s) < 10:
        ci_lo, ci_hi = float("nan"), float("nan")
    else:
        ci_lo = float(np.percentile(ec50s, 2.5))
        ci_hi = float(np.percentile(ec50s, 97.5))
    ec50, n, e0, emax = popt
    return {
        "ec50": float(ec50), "n": float(n), "e0": float(e0), "emax": float(emax),
        "rmse": rmse, "ci_lo": ci_lo, "ci_hi": ci_hi, "n_pts": int(x.size),
    }


def hill_inverse(target_y: float, fit: Dict[str, float]) -> float:
    """Solve target_y = e0 + (emax-e0) * x^n / (ec50^n + x^n) for x."""
    e0, emax, ec50, n = fit["e0"], fit["emax"], fit["ec50"], fit["n"]
    if emax <= e0:
        return float("nan")
    frac = (target_y - e0) / (emax - e0)
    if not (0 < frac < 1):
        return float("nan")
    return ec50 * (frac / (1 - frac)) ** (1.0 / n)


def fit_intra_vs_extra(extra: np.ndarray, intra: np.ndarray) -> Dict[str, float]:
    """Fit intra(extra). Try linear through origin first, then saturable Hill if RMSE
    improves materially."""
    extra = np.asarray(extra, float)
    intra = np.asarray(intra, float)
    mask = np.isfinite(extra) & np.isfinite(intra) & (extra >= 0)
    extra, intra = extra[mask], intra[mask]
    # Linear through origin: intra = k * extra
    nz = extra > 0
    if nz.sum() == 0:
        return {"model": "none"}
    k = float(np.sum(extra[nz] * intra[nz]) / np.sum(extra[nz] ** 2))
    pred_lin = k * extra
    rmse_lin = float(np.sqrt(np.mean((intra - pred_lin) ** 2)))
    out = {"model": "linear", "k": k, "rmse": rmse_lin,
           "max_extra": float(extra.max()), "max_intra": float(intra.max())}
    # Try saturable Hill (e0 fixed at 0)
    try:
        def model(x, ec50, n, vmax):
            return vmax * (x ** n) / (ec50 ** n + x ** n)
        p0 = [float(np.median(extra[nz])), 1.0, float(intra.max() * 1.2)]
        popt, _ = curve_fit(model, extra, intra, p0=p0,
                            bounds=([1e-3, 0.1, 1e-3], [1e6, 8.0, 1e6]),
                            maxfev=5000)
        pred_h = model(extra, *popt)
        rmse_h = float(np.sqrt(np.mean((intra - pred_h) ** 2)))
        if rmse_h < 0.85 * rmse_lin:  # only switch if meaningfully better
            out = {"model": "hill", "ec50": float(popt[0]), "n": float(popt[1]),
                   "vmax": float(popt[2]), "rmse": rmse_h,
                   "max_extra": out["max_extra"], "max_intra": out["max_intra"]}
    except Exception:
        pass
    return out


def invert_extra_for_intra(target_intra: float, fit: Dict) -> float:
    if fit["model"] == "linear":
        if fit["k"] <= 0:
            return float("nan")
        return target_intra / fit["k"]
    if fit["model"] == "hill":
        vmax, ec50, n = fit["vmax"], fit["ec50"], fit["n"]
        if target_intra >= vmax:
            return float("inf")
        frac = target_intra / vmax
        return ec50 * (frac / (1 - frac)) ** (1.0 / n)
    return float("nan")


def aggregate_run(run_dir: Path) -> List[Dict]:
    """Walk one run dir, return list of per-condition records."""
    rows: List[Dict] = []
    for cond_dir in sorted(run_dir.iterdir()):
        if not cond_dir.is_dir():
            continue
        params = parse_condition_name(cond_dir.name)
        if params is None:
            continue
        rep_csv = cond_dir / "replicates.csv"
        if not rep_csv.exists():
            continue
        cols = load_replicates(rep_csv)
        rec = dict(params)
        for k in ("CBD_extracellular_final", "CBD_intracellular_final", "Neuron_Health_final"):
            vals = np.array(cols.get(k, []), dtype=float)
            vals = vals[np.isfinite(vals)]
            rec[k + "_mean"] = float(vals.mean()) if vals.size else float("nan")
            rec[k + "_std"] = float(vals.std(ddof=1)) if vals.size > 1 else 0.0
            rec[k + "_n"] = int(vals.size)
        rec["_run"] = run_dir.name
        rec["_condition"] = cond_dir.name
        rows.append(rec)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True,
                    help="Sweep run directories to ingest")
    ap.add_argument("--report", required=True, help="Output Markdown report path")
    args = ap.parse_args()

    all_rows: List[Dict] = []
    for run in args.runs:
        run_path = Path(run)
        if not run_path.is_dir():
            print(f"warn: {run} is not a directory, skipping", file=sys.stderr)
            continue
        rows = aggregate_run(run_path)
        print(f"{run_path.name}: {len(rows)} conditions ingested", file=sys.stderr)
        all_rows.extend(rows)

    # Group by (Age, pH); within each cell concat data from both runs.
    cells: Dict[Tuple[float, float], List[Dict]] = {}
    for r in all_rows:
        if "Age" not in r or "pH" not in r or "CBD_extracellular" not in r:
            continue
        key = (round(r["Age"], 2), round(r["pH"], 2))
        cells.setdefault(key, []).append(r)

    lines: List[str] = []
    lines.append("# External → intracellular CBD dose mapping\n")
    lines.append(f"Runs ingested: " + ", ".join(Path(r).name for r in args.runs) + "\n")
    lines.append("Method: per (Age, pH) bin, fit Hill of Neuron_Health vs CBD_intracellular_final → EC50_intra; ")
    lines.append("fit transfer function CBD_intracellular_final = f(CBD_extracellular_final); invert at EC50_intra and EC90_intra.\n\n")

    lines.append("## Per (Age, pH) results\n")
    lines.append("**Therapeutic intracellular window** is defined as [EC50_intra, EC90_intra] of the "
                 "Hill fit of `Neuron_Health_final` vs `CBD_intracellular_final`.\n")
    lines.append("**Administered dose** is the set `CBD_extracellular` initial concentration "
                 "(condition-name parameter). Transfer fit `CBD_intracellular_final = f(set_dose)` "
                 "is inverted to give the dose required to reach each intracellular target.\n")
    header = ("| Age | pH | n pts | EC50_intra (µM) | 95% CI | Hill n | E0 | Emax | "
              "EC90_intra (µM) | transfer | k or (ec50,n,vmax) | RMSE_t | "
              "**set dose @ EC50_intra (µM)** | **set dose @ EC90_intra (µM)** | intra/set ratio |")
    sep = ("|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|")
    lines.append(header)
    lines.append(sep)

    summary_rows: List[Dict] = []
    for key in sorted(cells.keys()):
        age, ph = key
        rs = cells[key]
        # Dedup: if both runs supplied the same CBD point, keep both replicate sets
        # by taking weighted mean
        by_cbd: Dict[float, List[Dict]] = {}
        for r in rs:
            by_cbd.setdefault(round(r["CBD_extracellular"], 4), []).append(r)
        ext_arr, intra_arr, neuron_arr, extfin_arr = [], [], [], []
        for cbd, recs in sorted(by_cbd.items()):
            ws = np.array([rec["CBD_extracellular_final_n"] for rec in recs], dtype=float)
            if ws.sum() == 0:
                continue
            extra_set = float(cbd)  # the administered/set dose from the condition name
            extra_fin = np.average([rec["CBD_extracellular_final_mean"] for rec in recs], weights=ws)
            intra_v = np.average([rec["CBD_intracellular_final_mean"] for rec in recs], weights=ws)
            neuron_v = np.average([rec["Neuron_Health_final_mean"] for rec in recs], weights=ws)
            ext_arr.append(extra_set); intra_arr.append(intra_v); neuron_arr.append(neuron_v); extfin_arr.append(extra_fin)
        ext_arr = np.array(ext_arr); intra_arr = np.array(intra_arr)
        neuron_arr = np.array(neuron_arr); extfin_arr = np.array(extfin_arr)

        hill_intra = fit_hill_with_ci(intra_arr, neuron_arr)
        transfer = fit_intra_vs_extra(ext_arr, intra_arr)

        if hill_intra is None:
            lines.append(f"| {age:g} | {ph:g} | {ext_arr.size} | — | — | — | — | — | — | {transfer.get('model','—')} | — | — | — | — | — |")
            continue

        ec50_intra = hill_intra["ec50"]
        e_at_ec90 = hill_intra["e0"] + 0.9 * (hill_intra["emax"] - hill_intra["e0"])
        ec90_intra = hill_inverse(e_at_ec90, hill_intra)

        ext_at_ec50 = invert_extra_for_intra(ec50_intra, transfer)
        ext_at_ec90 = invert_extra_for_intra(ec90_intra, transfer)

        if transfer["model"] == "linear":
            ratio = transfer["k"]
            tparam = f"k={transfer['k']:.4f}"
        elif transfer["model"] == "hill":
            ratio = ec50_intra / ext_at_ec50 if (ext_at_ec50 and np.isfinite(ext_at_ec50) and ext_at_ec50 > 0) else float("nan")
            tparam = f"ec50={transfer['ec50']:.2f}, n={transfer['n']:.2f}, vmax={transfer['vmax']:.2f}"
        else:
            ratio = float("nan")
            tparam = "—"

        rmse_t = transfer.get("rmse", float("nan"))

        def fmt(v, dp=2):
            if v is None or (isinstance(v, float) and (not np.isfinite(v))):
                return "—"
            return f"{v:.{dp}f}"

        lines.append(
            f"| {age:g} | {ph:g} | {ext_arr.size} | {fmt(ec50_intra)} | "
            f"[{fmt(hill_intra['ci_lo'])}, {fmt(hill_intra['ci_hi'])}] | "
            f"{fmt(hill_intra['n'])} | {fmt(hill_intra['e0'])} | {fmt(hill_intra['emax'])} | "
            f"{fmt(ec90_intra)} | {transfer['model']} | {tparam} | {fmt(rmse_t,3)} | "
            f"{fmt(ext_at_ec50)} | {fmt(ext_at_ec90)} | {fmt(ratio,4)} |"
        )

        summary_rows.append({
            "Age": age, "pH": ph,
            "ec50_intra": ec50_intra, "ec90_intra": ec90_intra,
            "ext_at_ec50": ext_at_ec50, "ext_at_ec90": ext_at_ec90,
            "intra_extra_ratio": ratio,
            "n_pts": int(ext_arr.size),
        })

    lines.append("")
    lines.append("## Per-condition raw data (mean across replicates)\n")
    lines.append("| run | Age | pH | CBD_extra (set, µM) | CBD_extra (final, mean) | CBD_intra (final, mean) | Neuron_Health_final (mean) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in sorted(all_rows, key=lambda r: (r.get("Age",-1), r.get("pH",-1), r.get("CBD_extracellular",-1))):
        if "Age" not in r:
            continue
        lines.append(
            f"| {r['_run']} | {r['Age']:g} | {r['pH']:g} | {r['CBD_extracellular']:g} | "
            f"{r['CBD_extracellular_final_mean']:.3f} | {r['CBD_intracellular_final_mean']:.3f} | "
            f"{r['Neuron_Health_final_mean']:.2f} |"
        )

    Path(args.report).write_text("\n".join(lines) + "\n")
    print(f"Wrote {args.report} ({len(lines)} lines)", file=sys.stderr)
    print(json.dumps(summary_rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
