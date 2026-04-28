#!/usr/bin/env python3
"""
Phase-1 envelope miner.

Aggregates the full T x AGE x pH factorial sweep, extracts endpoint
markers, fits per-axis sensitivities + 2-way interactions, identifies
healthy/stress corners, and compares the (T=310.15, AGE=75, pH=7.4)
reference condition against the Phase-0 24h baseline.

Designed to be re-runnable on any Phase-1 sweep run dir.

Usage:
  python3 mine_phase1_envelope.py <run_dir> [--out <markdown_path>]
"""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
from pathlib import Path
from statistics import fmean, pstdev

# Markers we care about (model place names) and the time-slice we report
MARKERS = [
    "Neuron_Health", "ROS",
    "Abeta_Monomer", "Abeta_Oligomer", "Abeta_Plaque",
    "NFkB_p65", "TNFa", "IL1b", "IL6", "COX2",
    "Microglia_M1", "Microglia_M2",
    "BDNF",
    "Glutathione", "GSSG", "Nrf2_free", "Keap1_Nrf2_complex",
    "SOD", "HO1",
    "CBD_intracellular",
    "Temperature_factor", "pH_acidosis", "Age_factor",  # bridge outputs
]

# Phase-0 reference (run_20260428_184351, 24h, DSEV=0)
PHASE0_REF = {
    "horizon_h": 24.0,
    "Neuron_Health": 100.0, "ROS": 0.0,
    "Abeta_Monomer": 0.78, "Abeta_Oligomer": 0.0, "Abeta_Plaque": 0.0,
    "NFkB_p65": 0.0, "TNFa": 0.50, "IL1b": 0.0, "IL6": 0.0, "COX2": 0.0,
    "Microglia_M1": 0.0, "Microglia_M2": 45.0,
    "BDNF": 4.14,
    "Glutathione": 305.8, "GSSG": 33.5, "Nrf2_free": 6.0,
    "Keap1_Nrf2_complex": 54.0,
    "SOD": 21.6, "HO1": 32.4,
    "CBD_intracellular": 9.98,
}

CONDITION_RE = re.compile(
    r"^condition_\[param\]_TEMPERATURE_eq_([0-9.]+)"
    r"_\[param\]_AGE_eq_([0-9.]+)"
    r"_\[param\]_PH_eq_([0-9.]+)$"
)


def load_id_name_map(run_dir: Path) -> dict[str, str]:
    snap = run_dir / "model_snapshot.shy"
    m = json.loads(snap.read_text())
    return {p["id"]: p["name"] for p in m["places"]}


def load_condition(cond_dir: Path, id2name: dict[str, str]) -> dict[str, dict]:
    """Return {marker: {endpoint_mean, endpoint_std, t1h, t2h, t3h, max, min}}."""
    stats_path = cond_dir / "statistics.json"
    if not stats_path.exists():
        return {}
    d = json.loads(stats_path.read_text())
    tp = d["time_points"]
    horizon = tp[-1]
    n = len(tp)

    # find indices for 1h, 2h, 3h, end
    def idx_for_t(t: float) -> int:
        return min(range(n), key=lambda i: abs(tp[i] - t))

    i1 = idx_for_t(3600.0)
    i2 = idx_for_t(7200.0)
    i3 = idx_for_t(10800.0)
    iend = n - 1

    out = {}
    name2id = {v: k for k, v in id2name.items()}
    for marker in MARKERS:
        pid = name2id.get(marker)
        if pid is None or pid not in d["species_statistics"]:
            continue
        s = d["species_statistics"][pid]
        mean = s["mean"]
        std = s["std"]
        out[marker] = {
            "endpoint_mean": mean[iend],
            "endpoint_std": std[iend],
            "t1h": mean[i1],
            "t2h": mean[i2],
            "t3h": mean[i3],
            "tmax_value": max(mean),
            "tmax_at_s": tp[mean.index(max(mean))],
            "tmin_value": min(mean),
        }
    return out


def parse_axes(condition_name: str) -> tuple[float, float, float] | None:
    m = CONDITION_RE.match(condition_name)
    if not m:
        return None
    T, A, pH = (float(x) for x in m.groups())
    return T, A, pH


def axis_slice(rows, axis_idx, marker, fixed=None):
    """Return [(value, mean, std)] grouped by the chosen axis."""
    bins: dict[float, list[float]] = {}
    for r in rows:
        if fixed is not None and any(r[i] != v for i, v in fixed.items()):
            continue
        v = r[axis_idx]
        bins.setdefault(v, []).append(r[3].get(marker, {}).get("endpoint_mean"))
    out = []
    for v in sorted(bins):
        ys = [y for y in bins[v] if y is not None]
        if not ys:
            continue
        out.append((v, fmean(ys), pstdev(ys) if len(ys) > 1 else 0.0, len(ys)))
    return out


def fit_linear_slope(xs, ys):
    """Return slope of simple least-squares line."""
    if len(xs) < 2:
        return 0.0
    mx, my = fmean(xs), fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


def two_way_interaction(rows, axisA, axisB, marker):
    """Range of marginal slopes of marker over axisA, evaluated at each level of axisB.
    Large range => strong interaction."""
    # Collect levels of B
    levels_b = sorted({r[axisB] for r in rows})
    slopes = []
    for vb in levels_b:
        sub = [r for r in rows if r[axisB] == vb]
        # marginalise out the third axis
        third = ({0, 1, 2} - {axisA, axisB}).pop()
        # group by axisA, mean over third
        xa = sorted({r[axisA] for r in sub})
        ys = []
        for xa_v in xa:
            yvals = [r[3].get(marker, {}).get("endpoint_mean")
                     for r in sub if r[axisA] == xa_v]
            yvals = [y for y in yvals if y is not None]
            if yvals:
                ys.append(fmean(yvals))
            else:
                ys.append(None)
        if any(y is None for y in ys):
            continue
        slopes.append((vb, fit_linear_slope(xa, ys)))
    return slopes


def fmt(x, w=8, p=3):
    if x is None:
        return " " * w
    if isinstance(x, float):
        return f"{x:>{w}.{p}f}"
    return f"{str(x):>{w}}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None,
                    help="Optional markdown report path")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()

    id2name = load_id_name_map(run_dir)
    print(f"# Phase-1 envelope mining: {run_dir.name}")
    prov = json.loads((run_dir / "provenance.json").read_text())
    print(f"  dispatched: {prov['dispatched_at']}")
    print(f"  model sha:  {prov['model']['sha256'][:16]}")
    print(f"  server git: {prov.get('server',{}).get('git',{}).get('head_sha','?')[:8]}")
    horizon_s = None

    # Load all envelope conditions
    rows = []  # (T, A, pH, markers_dict)
    baseline = None
    for child in sorted(run_dir.iterdir()):
        if not child.is_dir() or not child.name.startswith("condition_"):
            continue
        if child.name == "condition_Baseline":
            baseline = load_condition(child, id2name)
            continue
        ax = parse_axes(child.name)
        if ax is None:
            continue
        markers = load_condition(child, id2name)
        if markers:
            rows.append((ax[0], ax[1], ax[2], markers))
            if horizon_s is None:
                # peek at first stats file
                d = json.loads((child / "statistics.json").read_text())
                horizon_s = d["time_points"][-1]
    print(f"  envelope conditions: {len(rows)} | horizon: {horizon_s/3600:.1f} h")

    # ---------------- Section 1: Baseline reproduction ----------------
    print("\n## 1. 'Baseline' condition vs Phase-0")
    print(f"{'marker':<22} {'phase0_24h':>12} {'phase1_4h(B)':>12} {'phase1_t1h':>12}")
    if baseline:
        for m in MARKERS:
            p0 = PHASE0_REF.get(m)
            p1 = baseline.get(m, {})
            v_end = p1.get("endpoint_mean")
            v_t1 = p1.get("t1h")
            print(f"{m:<22} "
                  f"{fmt(p0,12,3) if p0 is not None else 'n/a':>12} "
                  f"{fmt(v_end,12,3)} "
                  f"{fmt(v_t1,12,3)}")

    # ---------------- Section 2: Reference physiological condition ----------------
    REF = (310.15, 75.0, 7.4)
    ref = next((r for r in rows if r[:3] == REF), None)
    print(f"\n## 2. Reference physiological condition T={REF[0]} A={REF[1]} pH={REF[2]}")
    if ref:
        print(f"{'marker':<22} {'phase0_24h':>12} {'p1_ref_4h':>12} {'p1_ref_t1h':>12} {'delta_vs_p0':>14}")
        for m in MARKERS:
            p0 = PHASE0_REF.get(m)
            v_end = ref[3].get(m, {}).get("endpoint_mean")
            v_t1 = ref[3].get(m, {}).get("t1h")
            d = (v_end - p0) if (v_end is not None and p0 is not None) else None
            print(f"{m:<22} "
                  f"{fmt(p0,12,3) if p0 is not None else 'n/a':>12} "
                  f"{fmt(v_end,12,3)} "
                  f"{fmt(v_t1,12,3)} "
                  f"{fmt(d,14,3)}")
    else:
        print("  REFERENCE CONDITION NOT FOUND")

    # ---------------- Section 3: Per-axis marginal effect ----------------
    AXIS_LABEL = {0: "Temperature(K)", 1: "Age(y)", 2: "pH"}
    print("\n## 3. Marginal effects (mean across the other two axes)")
    for marker in ["Neuron_Health", "ROS", "Abeta_Oligomer", "Glutathione",
                   "Nrf2_free", "Microglia_M1", "BDNF",
                   "Temperature_factor", "Age_factor", "pH_acidosis"]:
        print(f"\n### {marker}")
        for axis in (0, 1, 2):
            slc = axis_slice(rows, axis, marker)
            if not slc:
                continue
            xs = [v for v, _, _, _ in slc]
            ys = [m for _, m, _, _ in slc]
            slope = fit_linear_slope(xs, ys)
            print(f"  {AXIS_LABEL[axis]:<14}", end="")
            for v, mu, sd, n in slc:
                print(f" {v:>6g}={mu:>7.3f}±{sd:.2f}", end="")
            print(f"  | slope={slope:+.4g} per unit")

    # ---------------- Section 4: 2-way interactions on Neuron_Health ----------------
    print("\n## 4. 2-way interactions on Neuron_Health")
    for axisA, axisB in [(0, 1), (0, 2), (1, 2)]:
        sl = two_way_interaction(rows, axisA, axisB, "Neuron_Health")
        if not sl:
            continue
        s_vals = [s for _, s in sl]
        rng = max(s_vals) - min(s_vals)
        print(f"  slope(NH vs {AXIS_LABEL[axisA]}) at each level of {AXIS_LABEL[axisB]}:")
        for vb, s in sl:
            print(f"    {AXIS_LABEL[axisB]}={vb:>6g}  slope={s:+.4g}")
        print(f"    -> interaction range = {rng:.4g}  "
              f"({'STRONG' if rng > 0.05 else 'modest' if rng > 0.01 else 'negligible'})")

    # ---------------- Section 5: Top-10 protective and stressful corners ----------------
    print("\n## 5. Top corners by Neuron_Health")
    rows_ranked = sorted(rows, key=lambda r: r[3].get("Neuron_Health", {}).get("endpoint_mean", -1))
    def _fmt_corner(r):
        nh = r[3].get("Neuron_Health", {}).get("endpoint_mean")
        ros = r[3].get("ROS", {}).get("endpoint_mean")
        ao = r[3].get("Abeta_Oligomer", {}).get("endpoint_mean")
        gsh = r[3].get("Glutathione", {}).get("endpoint_mean")
        f = lambda x, w=6, p=2: (f"{x:>{w}.{p}f}" if x is not None else " " * w)
        return (f"    T={r[0]:>6g} A={r[1]:>4g} pH={r[2]:<4g}  "
                f"NH={f(nh)}  ROS={f(ros,5,2)}  AbOlig={f(ao,5,2)}  GSH={f(gsh,6,1)}")
    print("  10 most stressful:")
    for r in rows_ranked[:10]:
        print(_fmt_corner(r))
    print("  10 most protective:")
    for r in rows_ranked[-10:]:
        print(_fmt_corner(r))

    # ---------------- Section 6: Bridge functional check (▢→event→◇) ----------------
    print("\n## 6. Bridge (▢→event→◇) functional verification")
    print("  Check that Temperature_factor / Age_factor / pH_acidosis values track inputs:")
    for marker in ["Temperature_factor", "Age_factor", "pH_acidosis"]:
        # which axis should drive it?
        drive_axis = {"Temperature_factor": 0, "Age_factor": 1, "pH_acidosis": 2}[marker]
        slc = axis_slice(rows, drive_axis, marker)
        if not slc:
            print(f"  {marker:<22}  NO DATA")
            continue
        rng = max(m for _, m, _, _ in slc) - min(m for _, m, _, _ in slc)
        print(f"  {marker:<22}  drives by {AXIS_LABEL[drive_axis]:<14} "
              f"value-range={rng:.4g}  "
              f"verdict={'ACTIVE' if rng > 1e-3 else 'INERT (BRIDGE BROKEN?)'}")
        for v, mu, sd, n in slc:
            print(f"    {AXIS_LABEL[drive_axis]}={v:>6g}  {marker}={mu:.4g}")

    # ---------------- Section 7: Healthy/stress envelope summary ----------------
    HEALTHY_BOUNDS = {
        "Neuron_Health": (95.0, None),
        "ROS": (None, 5.0),
        "Abeta_Oligomer": (None, 1.0),
        "Microglia_M1": (None, 5.0),
        "Microglia_M2": (40.0, None),
    }
    print("\n## 7. Endpoint envelope across 80 conditions")
    print(f"{'marker':<22} {'min':>10} {'mean':>10} {'max':>10} {'CV%':>6} "
          f"{'bound':<14} {'pass':>4}")
    for m in MARKERS:
        vals = [r[3].get(m, {}).get("endpoint_mean") for r in rows]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        mu = fmean(vals); mn = min(vals); mx = max(vals)
        sd = pstdev(vals) if len(vals) > 1 else 0
        cv = (sd / mu * 100) if mu > 0 else 0
        bnd = HEALTHY_BOUNDS.get(m)
        if bnd is None:
            verdict = ""
            bnd_s = ""
        else:
            lo, hi = bnd
            ok = (lo is None or mn >= lo) and (hi is None or mx <= hi)
            verdict = "OK" if ok else "VIO"
            bnd_s = f"[{lo if lo else '-'},{hi if hi else '-'}]"
        print(f"{m:<22} {mn:>10.3f} {mu:>10.3f} {mx:>10.3f} "
              f"{cv:>5.1f}  {bnd_s:<14} {verdict:>4}")


if __name__ == "__main__":
    main()
