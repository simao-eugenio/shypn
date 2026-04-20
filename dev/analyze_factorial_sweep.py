#!/usr/bin/env python3
"""
Factorial Sweep Analysis: CBD × Age × pH
==========================================
Analyzes a 3-factor factorial sweep (run_20260420_150932).
Computes main effects, interactions, dissociation metrics, MED tables.

Run on server:  .venv/bin/python dev/analyze_factorial_sweep.py [run_dir]
"""

import json
import csv
import os
import sys
import re
import numpy as np
from pathlib import Path
from itertools import product
from collections import defaultdict

# ─── Configuration ──────────────────────────────────────────────────────────

DEFAULT_RUN_DIR = Path("workspace/projects/canabidiol/experiments/results/run_20260420_150932")
RUN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RUN_DIR

# Primary endpoints
PRIMARY = [
    "Neuron_Health",
    "NFkB_p65",
    "ROS",
    "Glutathione",
    "Abeta_Oligomer",
]

# Secondary endpoints
SECONDARY = [
    "TNFa", "IL1b", "IL6", "COX2",
    "Microglia_M1", "Microglia_M2",
    "HO1", "SOD", "PPARg_active",
    "GSSG", "Abeta_Plaque", "BDNF", "Nrf2_free",
]

ALL_ENDPOINTS = PRIMARY + SECONDARY

# Response direction (True = higher is better / increases with CBD)
DIRECTION = {
    "Neuron_Health": True, "Glutathione": True, "HO1": True, "SOD": True,
    "BDNF": True, "Microglia_M2": True, "Nrf2_free": True, "PPARg_active": True,
    "NFkB_p65": False, "ROS": False, "Abeta_Oligomer": False, "Abeta_Plaque": False,
    "TNFa": False, "IL1b": False, "IL6": False, "COX2": False, "Microglia_M1": False,
    "GSSG": False,
}


# ─── Parsing ────────────────────────────────────────────────────────────────

def parse_condition_name(dirname: str):
    """Extract factor levels from condition directory name.
    Returns (cbd, age, ph) or None for Baseline/unparseable.
    """
    m = re.match(
        r"condition_CBD_extracellular_eq_([\d.]+)_Age_eq_([\d.]+)_pH_eq_([\d.]+)",
        dirname,
    )
    if m:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    return None


def load_replicates(condition_dir: Path) -> dict:
    """Load replicates.csv → {place_name: np.array of final values}."""
    csv_path = condition_dir / "replicates.csv"
    if not csv_path.exists():
        return {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    result = {}
    for col in rows[0].keys():
        if col.endswith("_final"):
            name = col.replace("_final", "")
            vals = []
            for row in rows:
                try:
                    vals.append(float(row[col]))
                except (ValueError, KeyError):
                    pass
            result[name] = np.array(vals)
    return result


def compute_stats(values: np.ndarray) -> dict:
    n = len(values)
    mean = np.mean(values)
    std = np.std(values, ddof=1) if n > 1 else 0.0
    se = std / np.sqrt(n) if n > 0 else 0.0
    ci95 = 1.96 * se
    return {
        "mean": float(mean),
        "std": float(std),
        "ci95_lo": float(mean - ci95),
        "ci95_hi": float(mean + ci95),
        "n": n,
    }


# ─── Data Loading ───────────────────────────────────────────────────────────

def load_all_conditions(run_dir: Path):
    """Load all conditions → list of dicts with factors + endpoint stats."""
    records = []
    for d in sorted(run_dir.iterdir()):
        if not d.is_dir() or d.name == "config.json":
            continue
        factors = parse_condition_name(d.name)
        if factors is None:
            continue  # Skip Baseline
        cbd, age, ph = factors
        data = load_replicates(d)
        if not data:
            continue
        rec = {
            "dir": d.name,
            "cbd": cbd, "age": age, "ph": ph,
            "n_rep": len(next(iter(data.values()))),
            "raw": data,
            "stats": {},
        }
        for ep in ALL_ENDPOINTS:
            if ep in data:
                rec["stats"][ep] = compute_stats(data[ep])
        records.append(rec)
    return records


# ─── Analysis Functions ─────────────────────────────────────────────────────

def main_effects(records, endpoint):
    """Compute marginal means for each factor level."""
    factors = {"cbd": set(), "age": set(), "ph": set()}
    for r in records:
        for f in factors:
            factors[f].add(r[f])

    effects = {}
    for fname, levels in factors.items():
        eff = {}
        for lv in sorted(levels):
            vals = [r["stats"][endpoint]["mean"] for r in records
                    if r[fname] == lv and endpoint in r["stats"]]
            eff[lv] = {"marginal_mean": float(np.mean(vals)),
                       "marginal_std": float(np.std(vals)),
                       "n_conditions": len(vals)}
        effects[fname] = eff
    return effects


def interaction_cbd_factor(records, endpoint, factor2):
    """Compute CBD × factor2 cell means."""
    cbd_levels = sorted(set(r["cbd"] for r in records))
    f2_levels = sorted(set(r[factor2] for r in records))

    table = {}
    for cbd in cbd_levels:
        row = {}
        for f2 in f2_levels:
            vals = [r["stats"][endpoint]["mean"] for r in records
                    if r["cbd"] == cbd and r[factor2] == f2 and endpoint in r["stats"]]
            row[f2] = float(np.mean(vals)) if vals else None
        table[cbd] = row
    return cbd_levels, f2_levels, table


def dissociation_analysis(records):
    """For each condition: is inflammation resolved but neuroprotection incomplete?
    Δ_dissociation = (NFkB resolved → 1 if NFkB<1) - (Neuron rescued → 1 if NH≥95)
    """
    results = []
    for r in records:
        nfkb = r["stats"].get("NFkB_p65", {}).get("mean")
        nh = r["stats"].get("Neuron_Health", {}).get("mean")
        if nfkb is None or nh is None:
            continue
        inflam_resolved = nfkb < 1.0
        neuron_rescued = nh >= 95.0
        dissociation = inflam_resolved and not neuron_rescued
        results.append({
            "cbd": r["cbd"], "age": r["age"], "ph": r["ph"],
            "nfkb": nfkb, "neuron": nh,
            "inflam_resolved": inflam_resolved,
            "neuron_rescued": neuron_rescued,
            "dissociated": dissociation,
        })
    return results


def med_table(records, endpoint, threshold, direction="above"):
    """Minimum Effective Dose per Age×pH stratum.
    direction='above': first CBD where endpoint ≥ threshold
    direction='below': first CBD where endpoint ≤ threshold
    """
    age_levels = sorted(set(r["age"] for r in records))
    ph_levels = sorted(set(r["ph"] for r in records))
    cbd_levels = sorted(set(r["cbd"] for r in records))

    table = {}
    for age in age_levels:
        row = {}
        for ph in ph_levels:
            med = None
            for cbd in cbd_levels:
                matching = [r for r in records
                            if r["cbd"] == cbd and r["age"] == age and r["ph"] == ph
                            and endpoint in r["stats"]]
                if not matching:
                    continue
                val = matching[0]["stats"][endpoint]["mean"]
                if direction == "above" and val >= threshold:
                    med = cbd
                    break
                elif direction == "below" and val <= threshold:
                    med = cbd
                    break
            row[ph] = med
            table[(age, ph)] = med
        table[age] = row  # convenience access
    return table, age_levels, ph_levels


def effect_size_eta2(records, factor, endpoint):
    """Compute eta-squared (proportion of variance explained) for a factor."""
    groups = defaultdict(list)
    for r in records:
        if endpoint in r["stats"]:
            groups[r[factor]].append(r["stats"][endpoint]["mean"])

    all_vals = []
    for vals in groups.values():
        all_vals.extend(vals)
    grand_mean = np.mean(all_vals)

    ss_between = sum(len(vals) * (np.mean(vals) - grand_mean) ** 2
                     for vals in groups.values())
    ss_total = sum((v - grand_mean) ** 2 for v in all_vals)

    return float(ss_between / ss_total) if ss_total > 0 else 0.0


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    run_dir = RUN_DIR
    if not run_dir.exists():
        alt = Path(os.environ.get("SHYPN_ROOT", ".")) / run_dir
        if alt.exists():
            run_dir = alt
        else:
            print(f"ERROR: {run_dir} not found")
            sys.exit(1)

    print("=" * 78)
    print("FACTORIAL SWEEP ANALYSIS: CBD × Age × pH")
    print(f"Run: {run_dir.name}")
    print("=" * 78)

    records = load_all_conditions(run_dir)
    cbd_levels = sorted(set(r["cbd"] for r in records))
    age_levels = sorted(set(r["age"] for r in records))
    ph_levels = sorted(set(r["ph"] for r in records))

    print(f"\nLoaded {len(records)} conditions")
    print(f"  CBD levels: {cbd_levels}")
    print(f"  Age levels: {age_levels}")
    print(f"  pH  levels: {ph_levels}")
    print(f"  Replicates: {records[0]['n_rep']} per condition")
    print(f"  Expected: {len(cbd_levels)}×{len(age_levels)}×{len(ph_levels)} "
          f"= {len(cbd_levels)*len(age_levels)*len(ph_levels)}")

    # ═══════════════════════════════════════════════════════════════════════
    # 1. EFFECT SIZE (eta²) — which factor matters most?
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 78)
    print("1. EFFECT SIZE (η²) — Variance explained by each factor")
    print("═" * 78)

    header = f"{'Endpoint':>20} | {'CBD':>8} | {'Age':>8} | {'pH':>8} | {'Dominant'}"
    print(header)
    print("─" * len(header))

    eta2_results = {}
    for ep in PRIMARY:
        eta_cbd = effect_size_eta2(records, "cbd", ep)
        eta_age = effect_size_eta2(records, "age", ep)
        eta_ph = effect_size_eta2(records, "ph", ep)
        dominant = max([("CBD", eta_cbd), ("Age", eta_age), ("pH", eta_ph)],
                       key=lambda x: x[1])
        print(f"{ep:>20} | {eta_cbd:>7.3f} | {eta_age:>7.3f} | {eta_ph:>7.3f} | "
              f"{dominant[0]} ({dominant[1]:.1%})")
        eta2_results[ep] = {"cbd": eta_cbd, "age": eta_age, "ph": eta_ph}

    # ═══════════════════════════════════════════════════════════════════════
    # 2. MAIN EFFECTS — marginal means for each factor
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 78)
    print("2. MAIN EFFECTS — Marginal means per factor level")
    print("═" * 78)

    for ep in PRIMARY:
        eff = main_effects(records, ep)
        print(f"\n  {ep}:")
        for fname in ["cbd", "age", "ph"]:
            vals = eff[fname]
            parts = [f"{lv}→{v['marginal_mean']:.2f}" for lv, v in sorted(vals.items())]
            print(f"    {fname:>4}: {', '.join(parts)}")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. CBD × Age INTERACTION TABLE
    # ═══════════════════════════════════════════════════════════════════════
    for ep in ["Neuron_Health", "NFkB_p65", "ROS"]:
        print(f"\n{'═' * 78}")
        print(f"3. CBD × Age INTERACTION: {ep}")
        print("═" * 78)

        cbd_lvl, age_lvl, tbl = interaction_cbd_factor(records, ep, "age")
        header = f"{'CBD':>6}" + "".join(f" | {'Age='+str(int(a)):>10}" for a in age_lvl)
        print(header)
        print("─" * len(header))
        for cbd in cbd_lvl:
            row = f"{cbd:>6.0f}"
            for a in age_lvl:
                v = tbl[cbd].get(a)
                row += f" | {v:>10.3f}" if v is not None else f" | {'N/A':>10}"
            print(row)

    # ═══════════════════════════════════════════════════════════════════════
    # 4. CBD × pH INTERACTION TABLE
    # ═══════════════════════════════════════════════════════════════════════
    for ep in ["Neuron_Health", "NFkB_p65", "ROS"]:
        print(f"\n{'═' * 78}")
        print(f"4. CBD × pH INTERACTION: {ep}")
        print("═" * 78)

        cbd_lvl, ph_lvl, tbl = interaction_cbd_factor(records, ep, "ph")
        header = f"{'CBD':>6}" + "".join(f" | {'pH='+str(p):>10}" for p in ph_lvl)
        print(header)
        print("─" * len(header))
        for cbd in cbd_lvl:
            row = f"{cbd:>6.0f}"
            for p in ph_lvl:
                v = tbl[cbd].get(p)
                row += f" | {v:>10.3f}" if v is not None else f" | {'N/A':>10}"
            print(row)

    # ═══════════════════════════════════════════════════════════════════════
    # 5. DISSOCIATION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'═' * 78}")
    print("5. DISSOCIATION: Inflammation resolved BUT neuroprotection incomplete")
    print("   (NFkB < 1  AND  Neuron_Health < 95)")
    print("═" * 78)

    dissoc = dissociation_analysis(records)
    n_dissoc = sum(1 for d in dissoc if d["dissociated"])
    n_both = sum(1 for d in dissoc if d["inflam_resolved"] and d["neuron_rescued"])
    n_neither = sum(1 for d in dissoc if not d["inflam_resolved"] and not d["neuron_rescued"])
    n_neuro_only = sum(1 for d in dissoc if not d["inflam_resolved"] and d["neuron_rescued"])

    print(f"\n  Total conditions: {len(dissoc)}")
    print(f"  Full protection (both):        {n_both:>3} ({n_both/len(dissoc):.0%})")
    print(f"  Dissociated (inflam only):     {n_dissoc:>3} ({n_dissoc/len(dissoc):.0%})")
    print(f"  Neuro only (no inflam resol):  {n_neuro_only:>3} ({n_neuro_only/len(dissoc):.0%})")
    print(f"  Unprotected (neither):         {n_neither:>3} ({n_neither/len(dissoc):.0%})")

    if n_dissoc > 0:
        print("\n  Dissociated conditions:")
        for d in sorted(dissoc, key=lambda x: (x["cbd"], x["age"], x["ph"])):
            if d["dissociated"]:
                print(f"    CBD={d['cbd']:>5}, Age={d['age']:>2.0f}, pH={d['ph']}: "
                      f"NFkB={d['nfkb']:.4f}, Neuron={d['neuron']:.2f}")

    # ═══════════════════════════════════════════════════════════════════════
    # 6. MED TABLE — Minimum Effective Dose per stratum
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'═' * 78}")
    print("6. MINIMUM EFFECTIVE DOSE (MED) TABLES")
    print("═" * 78)

    # MED for Neuron_Health ≥ 95 (neuroprotection)
    print("\n  a) MED for Neuron_Health ≥ 95 (neuroprotection threshold)")
    med_nh, age_lvl, ph_lvl = med_table(records, "Neuron_Health", 95.0, "above")
    header = f"{'Age':>6}" + "".join(f" | {'pH='+str(p):>8}" for p in ph_lvl)
    print(f"  {header}")
    print(f"  {'─' * len(header)}")
    for age in age_lvl:
        row = f"{int(age):>6}"
        for ph in ph_lvl:
            v = med_nh.get((age, ph))
            row += f" | {v:>8.0f}" if v is not None else f" | {'>15':>8}"
        print(f"  {row}")

    # MED for NFkB_p65 < 1 (inflammation resolution)
    print("\n  b) MED for NFkB_p65 < 1 (inflammation resolution)")
    med_nfkb, _, _ = med_table(records, "NFkB_p65", 1.0, "below")
    header = f"{'Age':>6}" + "".join(f" | {'pH='+str(p):>8}" for p in ph_lvl)
    print(f"  {header}")
    print(f"  {'─' * len(header)}")
    for age in age_lvl:
        row = f"{int(age):>6}"
        for ph in ph_lvl:
            v = med_nfkb.get((age, ph))
            row += f" | {v:>8.0f}" if v is not None else f" | {'>15':>8}"
        print(f"  {row}")

    # MED for ROS reduction (ROS ≤ initial_ROS * 0.5 — estimate threshold)
    # Use CBD=0 mean as baseline to define 50% reduction target
    cbd0_ros = [r["stats"]["ROS"]["mean"] for r in records if r["cbd"] == 0 and "ROS" in r["stats"]]
    if cbd0_ros:
        ros_baseline = np.mean(cbd0_ros)
        ros_threshold = ros_baseline * 0.5
        print(f"\n  c) MED for ROS ≤ {ros_threshold:.1f} (50% reduction from vehicle={ros_baseline:.1f})")
        med_ros, _, _ = med_table(records, "ROS", ros_threshold, "below")
        header = f"{'Age':>6}" + "".join(f" | {'pH='+str(p):>8}" for p in ph_lvl)
        print(f"  {header}")
        print(f"  {'─' * len(header)}")
        for age in age_lvl:
            row = f"{int(age):>6}"
            for ph in ph_lvl:
                v = med_ros.get((age, ph))
                row += f" | {v:>8.0f}" if v is not None else f" | {'>15':>8}"
            print(f"  {row}")

    # ═══════════════════════════════════════════════════════════════════════
    # 7. DOSE-RESPONSE PER STRATUM (compact)
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'═' * 78}")
    print("7. DOSE-RESPONSE: Neuron_Health by CBD, for each Age×pH cell")
    print("═" * 78)

    for age in age_levels:
        for ph in ph_levels:
            label = f"Age={int(age)}, pH={ph}"
            vals = []
            for cbd in cbd_levels:
                matching = [r for r in records
                            if r["cbd"] == cbd and r["age"] == age and r["ph"] == ph
                            and "Neuron_Health" in r["stats"]]
                if matching:
                    vals.append(f"{matching[0]['stats']['Neuron_Health']['mean']:.1f}")
                else:
                    vals.append("N/A")
            print(f"  {label:<18}: " + " → ".join(
                f"CBD{int(cbd)}={v}" for cbd, v in zip(cbd_levels, vals)))

    # ═══════════════════════════════════════════════════════════════════════
    # 8. ANTIOXIDANT AXIS BY FACTOR
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'═' * 78}")
    print("8. ANTIOXIDANT AXIS: GSH, Nrf2, HO1, SOD (marginal means by CBD)")
    print("═" * 78)

    for ep in ["Glutathione", "Nrf2_free", "HO1", "SOD", "GSSG", "ROS"]:
        eff = main_effects(records, ep)
        if "cbd" in eff:
            parts = [f"{lv:.0f}→{v['marginal_mean']:.2f}" for lv, v in sorted(eff["cbd"].items())]
            print(f"  {ep:>15}: {', '.join(parts)}")

    # ═══════════════════════════════════════════════════════════════════════
    # 9. WORST-CASE CONDITIONS
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'═' * 78}")
    print("9. EXTREME CONDITIONS")
    print("═" * 78)

    # Worst neuron outcome at max CBD
    max_cbd = max(cbd_levels)
    max_cbd_records = [r for r in records if r["cbd"] == max_cbd and "Neuron_Health" in r["stats"]]
    if max_cbd_records:
        worst = min(max_cbd_records, key=lambda r: r["stats"]["Neuron_Health"]["mean"])
        best = max(max_cbd_records, key=lambda r: r["stats"]["Neuron_Health"]["mean"])
        print(f"\n  At CBD={max_cbd:.0f} (max dose):")
        print(f"    Worst: Age={worst['age']:.0f}, pH={worst['ph']} → "
              f"Neuron={worst['stats']['Neuron_Health']['mean']:.2f}")
        print(f"    Best:  Age={best['age']:.0f}, pH={best['ph']} → "
              f"Neuron={best['stats']['Neuron_Health']['mean']:.2f}")

    # Best neuron outcome at CBD=0
    cbd0_records = [r for r in records if r["cbd"] == 0 and "Neuron_Health" in r["stats"]]
    if cbd0_records:
        best0 = max(cbd0_records, key=lambda r: r["stats"]["Neuron_Health"]["mean"])
        worst0 = min(cbd0_records, key=lambda r: r["stats"]["Neuron_Health"]["mean"])
        print(f"\n  At CBD=0 (vehicle):")
        print(f"    Worst: Age={worst0['age']:.0f}, pH={worst0['ph']} → "
              f"Neuron={worst0['stats']['Neuron_Health']['mean']:.2f}")
        print(f"    Best:  Age={best0['age']:.0f}, pH={best0['ph']} → "
              f"Neuron={best0['stats']['Neuron_Health']['mean']:.2f}")

    # ═══════════════════════════════════════════════════════════════════════
    # 10. SUMMARY JSON
    # ═══════════════════════════════════════════════════════════════════════
    summary = {
        "run": run_dir.name,
        "factors": {
            "cbd": cbd_levels,
            "age": age_levels,
            "ph": ph_levels,
        },
        "n_conditions": len(records),
        "n_replicates": records[0]["n_rep"] if records else 0,
        "eta_squared": eta2_results,
        "dissociation": {
            "full_protection": n_both,
            "dissociated": n_dissoc,
            "neuro_only": n_neuro_only,
            "unprotected": n_neither,
        },
        "cell_means": {},
    }

    # Store all cell means for downstream plotting
    for r in records:
        key = f"CBD{r['cbd']}_Age{int(r['age'])}_pH{r['ph']}"
        cell = {}
        for ep in ALL_ENDPOINTS:
            if ep in r["stats"]:
                cell[ep] = r["stats"][ep]
        summary["cell_means"][key] = cell

    out_path = run_dir / "factorial_analysis.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n\n{'═' * 78}")
    print(f"Analysis written to: {out_path}")
    print(f"{'═' * 78}")


if __name__ == "__main__":
    main()
