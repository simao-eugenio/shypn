#!/usr/bin/env python3
"""
Phase-2 dose-response miner.

Aggregates the DISEASE_SEVERITY x MAINT_DOSE factorial sweep, extracts
endpoint markers per condition, builds:
  - Disease-only damage curve (MAINT_DOSE=0 across all severities)
  - Dose-response curve at each disease severity (NH, ROS, Abeta_Oligomer)
  - CBD pharmacokinetics check (intra/extra ratio vs predicted k=0.454)
  - EC50 estimation per disease-severity slice (Hill fit if possible)
  - Phase-0 / Phase-1 reconciliation at the matched horizon
"""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path
from statistics import fmean, pstdev

MARKERS = [
    "Neuron_Health", "ROS",
    "Abeta_Monomer", "Abeta_Oligomer", "Abeta_Plaque",
    "NFkB_p65", "TNFa", "IL1b", "IL6", "COX2",
    "Microglia_M1", "Microglia_M2",
    "BDNF",
    "Glutathione", "GSSG", "Nrf2_free", "Keap1_Nrf2_complex",
    "SOD", "HO1",
    "CBD_intracellular", "CBD_extracellular",
    "Temperature_factor", "pH_acidosis", "Age_factor",
]

CONDITION_RE = re.compile(
    r"^condition_\[param\]_DISEASE_SEVERITY_eq_([0-9.]+)"
    r"_\[param\]_MAINT_DOSE_eq_([0-9.]+)$"
)


def load_id_name_map(run_dir: Path) -> dict[str, str]:
    m = json.loads((run_dir / "model_snapshot.shy").read_text())
    return {p["id"]: p["name"] for p in m["places"]}


def load_condition(cond_dir: Path, name2id: dict[str, str]) -> dict[str, dict]:
    stats_path = cond_dir / "statistics.json"
    if not stats_path.exists():
        return {}
    d = json.loads(stats_path.read_text())
    tp = d["time_points"]
    n = len(tp)

    def idx_for_t(t: float) -> int:
        return min(range(n), key=lambda i: abs(tp[i] - t))

    i_24h = idx_for_t(86400.0)
    i_48h = idx_for_t(172800.0)
    i_72h = idx_for_t(259200.0)
    i_end = n - 1

    out = {}
    for marker in MARKERS:
        pid = name2id.get(marker)
        if pid is None or pid not in d["species_statistics"]:
            continue
        s = d["species_statistics"][pid]
        out[marker] = {
            "endpoint_mean": s["mean"][i_end],
            "endpoint_std": s["std"][i_end],
            "t24h": s["mean"][i_24h],
            "t48h": s["mean"][i_48h],
            "t72h": s["mean"][i_72h],
            "tmax_value": max(s["mean"]),
            "tmax_at_h": tp[s["mean"].index(max(s["mean"]))] / 3600,
            "tmin_value": min(s["mean"]),
        }
    return out, tp[-1]


def hill_ec50_estimate(doses, responses):
    """Estimate EC50 by linear interpolation on the dose axis where
    response crosses half-max. Returns None if curve isn't monotonic."""
    if len(doses) < 3:
        return None
    paired = sorted(zip(doses, responses))
    ds = [d for d, _ in paired]
    rs = [r for _, r in paired]
    # We want where rescue is half of (max_rescue - min); for damage we
    # invert.  Caller decides direction.
    rmin, rmax = min(rs), max(rs)
    if rmax - rmin < 1e-6:
        return None
    half = (rmin + rmax) / 2
    # Find first crossing
    for i in range(len(rs) - 1):
        if (rs[i] - half) * (rs[i + 1] - half) <= 0:
            d0, d1 = ds[i], ds[i + 1]
            r0, r1 = rs[i], rs[i + 1]
            if abs(r1 - r0) < 1e-9:
                return d0
            return d0 + (half - r0) * (d1 - d0) / (r1 - r0)
    return None


def fmt(x, w=8, p=3):
    if x is None:
        return " " * w
    if isinstance(x, float):
        return f"{x:>{w}.{p}f}"
    return f"{str(x):>{w}}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()

    id2name = load_id_name_map(run_dir)
    name2id = {v: k for k, v in id2name.items()}

    print(f"# Phase-2 dose-response mining: {run_dir.name}")
    prov = json.loads((run_dir / "provenance.json").read_text())
    print(f"  dispatched: {prov['dispatched_at']}")
    print(f"  model sha:  {prov['model']['sha256'][:16]}")
    sg = prov.get("server", {}).get("git", {})
    print(f"  server git: {sg.get('head_sha','?')[:8]}  dirty: {sg.get('dirty')}")

    rows = []  # (DSEV, MD, markers, horizon_s)
    baseline = None
    horizon_s = None
    for child in sorted(run_dir.iterdir()):
        if not child.is_dir() or not child.name.startswith("condition_"):
            continue
        if child.name == "condition_Baseline":
            res = load_condition(child, name2id)
            if res:
                baseline, horizon_s = res
            continue
        m_ = CONDITION_RE.match(child.name)
        if not m_:
            continue
        dsev, md = float(m_.group(1)), float(m_.group(2))
        res = load_condition(child, name2id)
        if res:
            markers, h = res
            rows.append((dsev, md, markers))
            horizon_s = h

    print(f"  envelope conditions: {len(rows)} | horizon: {horizon_s/3600:.1f} h "
          f"= {horizon_s/86400:.1f} d")

    # ============== 1. Baseline (DSEV=MD=0 model defaults) ==============
    print("\n## 1. Baseline (model defaults: DSEV=0.5, MD=5.0)")
    print(f"{'marker':<22} {'endpoint':>12} {'t24h':>10} {'t48h':>10} {'t72h':>10}")
    if baseline:
        for m in MARKERS:
            v = baseline.get(m, {})
            print(f"{m:<22} {fmt(v.get('endpoint_mean'),12,3)} "
                  f"{fmt(v.get('t24h'),10,3)} {fmt(v.get('t48h'),10,3)} "
                  f"{fmt(v.get('t72h'),10,3)}")

    # ============== 2. Disease-only damage curve (MD=0) ==============
    print("\n## 2. Disease damage (MAINT_DOSE = 0)")
    print(f"{'marker':<22}", end="")
    dsevs = sorted({r[0] for r in rows if r[1] == 0})
    for d in dsevs:
        print(f"  DSEV={d:<5g}", end="")
    print()
    md0 = {r[0]: r[2] for r in rows if r[1] == 0}
    for m in MARKERS:
        print(f"{m:<22}", end="")
        for d in dsevs:
            v = md0.get(d, {}).get(m, {}).get("endpoint_mean")
            print(f"  {fmt(v,8,3)}", end="")
        print()

    # ============== 3. Dose-response curves per DSEV ==============
    print("\n## 3. Dose-response — Neuron_Health by DISEASE_SEVERITY")
    print(f"{'DSEV':<8}", end="")
    mds = sorted({r[1] for r in rows if r[0] == 0})
    for md in mds:
        print(f"  MD={md:<5g}", end="")
    print(f"  {'rescue_max':>10}  {'EC50':>8}")
    for dsev in sorted({r[0] for r in rows}):
        nh = {}
        for r in rows:
            if r[0] == dsev:
                nh[r[1]] = r[2].get("Neuron_Health", {}).get("endpoint_mean")
        nh_md0 = nh.get(0.0, 0)
        nh_max = max(v for v in nh.values() if v is not None)
        rescue = (nh_max - nh_md0) if nh_md0 is not None else None
        ec50 = hill_ec50_estimate(
            [m for m in mds if nh.get(m) is not None],
            [nh[m] for m in mds if nh.get(m) is not None]
        ) if rescue and rescue > 1.0 else None
        print(f"DSEV={dsev:<3g}", end="")
        for md in mds:
            print(f"  {fmt(nh.get(md),8,2)}", end="")
        print(f"  {fmt(rescue,10,2)}  {fmt(ec50,8,2) if ec50 else '   --   '}")

    print("\n## 3b. Dose-response — Abeta_Oligomer by DISEASE_SEVERITY")
    print(f"{'DSEV':<8}", end="")
    for md in mds:
        print(f"  MD={md:<5g}", end="")
    print(f"  {'damage':>8}  {'IC50':>8}")
    for dsev in sorted({r[0] for r in rows}):
        ao = {}
        for r in rows:
            if r[0] == dsev:
                ao[r[1]] = r[2].get("Abeta_Oligomer", {}).get("endpoint_mean")
        ao_md0 = ao.get(0.0, 0)
        ao_min = min(v for v in ao.values() if v is not None)
        damage = ao_md0 if ao_md0 is not None else None
        ic50 = hill_ec50_estimate(
            [m for m in mds if ao.get(m) is not None],
            [ao[m] for m in mds if ao.get(m) is not None]
        ) if damage and damage > 0.5 else None
        print(f"DSEV={dsev:<3g}", end="")
        for md in mds:
            print(f"  {fmt(ao.get(md),8,3)}", end="")
        print(f"  {fmt(damage,8,3)}  {fmt(ic50,8,2) if ic50 else '   --   '}")

    print("\n## 3c. Dose-response — ROS by DISEASE_SEVERITY")
    print(f"{'DSEV':<8}", end="")
    for md in mds:
        print(f"  MD={md:<5g}", end="")
    print()
    for dsev in sorted({r[0] for r in rows}):
        ros = {r[1]: r[2].get("ROS", {}).get("endpoint_mean")
               for r in rows if r[0] == dsev}
        print(f"DSEV={dsev:<3g}", end="")
        for md in mds:
            print(f"  {fmt(ros.get(md),8,3)}", end="")
        print()

    # ============== 4. CBD pharmacokinetics ==============
    print("\n## 4. CBD pharmacokinetics — intra/maint_dose ratio")
    print(f"  Predicted invariant k=0.454 (per dose_to_maintain_intracellular_cbd.md §5)")
    print(f"{'DSEV':<6}{'MD':>6}{'CBD_intra (4d end)':>20}{'CBD_extra (4d end)':>20}{'k_eff':>10}")
    for dsev in sorted({r[0] for r in rows}):
        for md in mds:
            r = next((rr for rr in rows if rr[0] == dsev and rr[1] == md), None)
            if r is None:
                continue
            ci = r[2].get("CBD_intracellular", {}).get("endpoint_mean")
            ce = r[2].get("CBD_extracellular", {}).get("endpoint_mean")
            k = (ci / md) if (md > 0 and ci is not None) else None
            print(f"  {dsev:<5g}{md:>5g}  {fmt(ci,18,3)} {fmt(ce,18,3)} {fmt(k,10,3)}")

    # ============== 5. Inflammation cascade vs disease and dose ==============
    print("\n## 5. Inflammatory cascade — endpoint by (DSEV, MD)")
    print(f"  Markers: NFkB_p65, TNFa, IL1b, Microglia_M1")
    for marker in ["NFkB_p65", "TNFa", "IL1b", "Microglia_M1", "Microglia_M2"]:
        print(f"\n  ### {marker}")
        print(f"  {'DSEV':<6}", end="")
        for md in mds:
            print(f"  MD={md:<5g}", end="")
        print()
        for dsev in sorted({r[0] for r in rows}):
            print(f"  DSEV={dsev:<3g}", end="")
            for md in mds:
                r = next((rr for rr in rows if rr[0] == dsev and rr[1] == md), None)
                v = r[2].get(marker, {}).get("endpoint_mean") if r else None
                print(f"  {fmt(v,8,3)}", end="")
            print()

    # ============== 6. Antioxidant pool — does CBD restore? ==============
    print("\n## 6. Antioxidant pool by (DSEV, MD)")
    for marker in ["Glutathione", "Nrf2_free", "SOD", "HO1"]:
        print(f"\n  ### {marker}")
        print(f"  {'DSEV':<6}", end="")
        for md in mds:
            print(f"  MD={md:<5g}", end="")
        print()
        for dsev in sorted({r[0] for r in rows}):
            print(f"  DSEV={dsev:<3g}", end="")
            for md in mds:
                r = next((rr for rr in rows if rr[0] == dsev and rr[1] == md), None)
                v = r[2].get(marker, {}).get("endpoint_mean") if r else None
                print(f"  {fmt(v,8,2)}", end="")
            print()

    # ============== 7. Top corners ==============
    print("\n## 7. Best/worst corners by Neuron_Health")
    ranked = sorted(rows, key=lambda r: r[2].get("Neuron_Health", {}).get("endpoint_mean", -1))
    def line(r):
        nh = r[2].get("Neuron_Health", {}).get("endpoint_mean")
        ros = r[2].get("ROS", {}).get("endpoint_mean")
        ao = r[2].get("Abeta_Oligomer", {}).get("endpoint_mean")
        gsh = r[2].get("Glutathione", {}).get("endpoint_mean")
        nfkb = r[2].get("NFkB_p65", {}).get("endpoint_mean")
        return (f"  DSEV={r[0]:<5g} MD={r[1]:<5g}  "
                f"NH={fmt(nh,6,2)} ROS={fmt(ros,5,2)} "
                f"AbOlig={fmt(ao,5,2)} GSH={fmt(gsh,6,1)} "
                f"NFkB={fmt(nfkb,5,3)}")
    print("  Worst 8:")
    for r in ranked[:8]:
        print(line(r))
    print("  Best 8:")
    for r in ranked[-8:]:
        print(line(r))

    # ============== 8. Phase reconciliation ==============
    PHASE0 = {
        "horizon_h": 24.0,
        "Neuron_Health": 100.0, "ROS": 0.0,
        "Abeta_Monomer": 0.78, "Abeta_Oligomer": 0.0, "Abeta_Plaque": 0.0,
        "TNFa": 0.50, "IL1b": 0.0, "Microglia_M1": 0.0, "Microglia_M2": 45.0,
        "Glutathione": 305.8, "Nrf2_free": 6.0, "SOD": 21.6, "HO1": 32.4,
        "BDNF": 4.14, "CBD_intracellular": 9.98,
    }
    print("\n## 8. Phase reconciliation — DSEV=0/MD=0 (4 d) vs Phase-0 (24 h)")
    ref = next((r for r in rows if r[0] == 0 and r[1] == 0), None)
    if ref:
        print(f"{'marker':<22} {'phase0_24h':>12} {'p2_dsev0md0_24h':>18} "
              f"{'p2_dsev0md0_4d':>16} {'delta_24h':>12}")
        for m in MARKERS:
            p0 = PHASE0.get(m)
            v = ref[2].get(m, {})
            p2_24 = v.get("t24h")
            p2_end = v.get("endpoint_mean")
            d = (p2_24 - p0) if (p2_24 is not None and p0 is not None) else None
            print(f"{m:<22} "
                  f"{fmt(p0,12,3) if p0 is not None else 'n/a':>12} "
                  f"{fmt(p2_24,18,3)} {fmt(p2_end,16,3)} "
                  f"{fmt(d,12,3)}")


if __name__ == "__main__":
    main()
