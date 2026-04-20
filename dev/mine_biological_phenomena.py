#!/usr/bin/env python3
"""
Biological Phenomena Mining: CBD-AD Factorial Sweep
====================================================
Mines emergent phenomena from replicate-level and time-series data:
  1. Bistability (bimodal attractor distributions)
  2. Preemption cascades (temporal ordering of pathway activation)
  3. Basins of attraction (cluster analysis of replicate endpoints)
  4. Critical slowing down (variance peaks near transitions)
  5. Coupling analysis (inter-endpoint correlations)
  6. Age as bifurcation parameter
  7. Hysteresis / irreversibility signatures

Run on server: .venv/bin/python dev/mine_biological_phenomena.py [run_dir]
"""

import json
import csv
import os
import sys
import re
import numpy as np
from pathlib import Path
from collections import defaultdict

# ─── Configuration ──────────────────────────────────────────────────────────

DEFAULT_RUN_DIR = Path("workspace/projects/canabidiol/experiments/results/run_20260420_150932")
RUN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RUN_DIR

# Place ID → name mapping (from model)
PLACE_MAP = {
    "P1": "CBD_extracellular", "P2": "GPR3", "P3": "Gamma_Secretase",
    "P4": "APP", "P5": "Abeta_Monomer", "P6": "Abeta_Oligomer",
    "P7": "Abeta_Plaque", "P8": "NFkB_IkB", "P9": "NFkB_p65",
    "P10": "IKK", "P11": "TNFa", "P12": "IL1b", "P13": "IL6",
    "P14": "COX2", "P15": "Keap1_Nrf2", "P16": "Nrf2_free",
    "P17": "HO1", "P18": "SOD", "P19": "ROS", "P20": "Glutathione",
    "P21": "Microglia_M1", "P22": "Microglia_M2", "P23": "Neuron_Health",
    "P24": "BDNF", "P25": "HT1A_active", "P26": "PPARg_active",
    "P27": "A2A_active", "P28": "Temperature", "P29": "pH",
    "P30": "CBD_intracellular", "P31": "Age", "P32": "GPR3_inactive",
    "P33": "GSSG", "P34": "APP_mRNA",
}
NAME_TO_PID = {v: k for k, v in PLACE_MAP.items()}

# Key species for cascade / coupling analysis
CASCADE_SPECIES = [
    "CBD_extracellular", "PPARg_active", "NFkB_IkB", "NFkB_p65",
    "TNFa", "IL1b", "IL6", "COX2",
    "Microglia_M1", "Microglia_M2",
    "Nrf2_free", "HO1", "SOD", "ROS", "Glutathione", "GSSG",
    "Abeta_Monomer", "Abeta_Oligomer", "Abeta_Plaque",
    "Neuron_Health", "BDNF",
]

ATTRACTOR_SPECIES = [
    "Neuron_Health", "NFkB_p65", "ROS", "Glutathione",
    "Abeta_Oligomer", "Microglia_M1", "Microglia_M2",
]


# ─── Parsing ────────────────────────────────────────────────────────────────

def parse_condition(dirname):
    m = re.match(
        r"condition_CBD_extracellular_eq_([\d.]+)_Age_eq_([\d.]+)_pH_eq_([\d.]+)",
        dirname,
    )
    return (float(m.group(1)), float(m.group(2)), float(m.group(3))) if m else None


def load_replicates(cond_dir):
    csv_path = cond_dir / "replicates.csv"
    if not csv_path.exists():
        return {}
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
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
            if vals:
                result[name] = np.array(vals)
    return result


def load_timeseries(cond_dir, species_pids=None):
    """Load mean/std time-series from statistics.json.
    Returns (time_points, {species_name: {mean, std, cv}}).
    Only loads requested species to save memory.
    """
    stats_path = cond_dir / "statistics.json"
    if not stats_path.exists():
        return None, {}
    with open(stats_path) as f:
        d = json.load(f)
    tp = np.array(d["time_points"])
    series = {}
    for pid, sp_data in d["species_statistics"].items():
        name = PLACE_MAP.get(pid, pid)
        if species_pids and pid not in species_pids and name not in species_pids:
            continue
        series[name] = {
            "mean": np.array(sp_data["mean"]),
            "std": np.array(sp_data["std"]),
            "cv": np.array(sp_data["cv"]),
        }
    return tp, series


# ─── 1. Bistability Detection ──────────────────────────────────────────────

def detect_bimodality(values, n_bins=15):
    """Hartigan's dip test proxy: histogram gap detection + coefficient of bimodality.
    Returns dict with bimodality metrics.
    """
    n = len(values)
    if n < 10:
        return {"bimodal": False, "reason": "too_few"}

    rng = np.max(values) - np.min(values)
    if rng < 1e-8:
        return {"bimodal": False, "reason": "no_variance", "range": float(rng)}

    # Coefficient of bimodality: (skew² + 1) / kurtosis
    # Values > 5/9 ≈ 0.556 suggest bimodality
    mean = np.mean(values)
    std = np.std(values, ddof=1)
    if std < 1e-10:
        return {"bimodal": False, "reason": "zero_std"}

    z = (values - mean) / std
    skew = np.mean(z ** 3)
    kurt = np.mean(z ** 4)

    bc = (skew ** 2 + 1) / kurt if kurt > 0 else 0

    # Histogram gap detection
    hist, edges = np.histogram(values, bins=n_bins)
    centers = 0.5 * (edges[:-1] + edges[1:])

    # Find peaks (local maxima)
    peaks = []
    for i in range(1, len(hist) - 1):
        if hist[i] > hist[i - 1] and hist[i] > hist[i + 1]:
            peaks.append((i, centers[i], hist[i]))

    # Find valleys between peaks
    valleys = []
    if len(peaks) >= 2:
        for j in range(len(peaks) - 1):
            valley_idx = np.argmin(hist[peaks[j][0]:peaks[j + 1][0] + 1]) + peaks[j][0]
            valley_depth = 1 - hist[valley_idx] / min(peaks[j][2], peaks[j + 1][2])
            valleys.append({
                "position": float(centers[valley_idx]),
                "depth": float(valley_depth),  # 0 = no valley, 1 = deep valley
                "left_peak": float(peaks[j][1]),
                "right_peak": float(peaks[j + 1][1]),
            })

    bimodal = bc > 0.555 or (len(peaks) >= 2 and any(v["depth"] > 0.5 for v in valleys))

    return {
        "bimodal": bimodal,
        "bc": float(bc),
        "bc_threshold": 0.555,
        "n_peaks": len(peaks),
        "peaks": [(float(p[1]), int(p[2])) for p in peaks],
        "valleys": valleys,
        "skewness": float(skew),
        "kurtosis": float(kurt),
        "cv": float(std / abs(mean)) if abs(mean) > 1e-10 else float("inf"),
        "range": float(rng),
    }


def scan_bistability(run_dir):
    """Scan all conditions for bistability in key endpoints."""
    print("\n" + "═" * 78)
    print("1. BISTABILITY DETECTION")
    print("   Bimodal distributions in replicate endpoints → multiple attractors")
    print("═" * 78)

    results = []
    for d in sorted(run_dir.iterdir()):
        factors = parse_condition(d.name) if d.is_dir() else None
        if not factors:
            continue
        cbd, age, ph = factors
        data = load_replicates(d)
        for sp in ATTRACTOR_SPECIES:
            if sp not in data or len(data[sp]) < 10:
                continue
            bm = detect_bimodality(data[sp])
            if bm["bimodal"]:
                results.append({
                    "cbd": cbd, "age": age, "ph": ph,
                    "species": sp, **bm,
                })

    if results:
        print(f"\n  Found {len(results)} bimodal distributions:\n")
        # Group by species
        by_sp = defaultdict(list)
        for r in results:
            by_sp[r["species"]].append(r)
        for sp, items in sorted(by_sp.items()):
            print(f"  {sp} ({len(items)} conditions):")
            for r in sorted(items, key=lambda x: (x["cbd"], x["age"])):
                peaks_str = ", ".join(f"{p[0]:.2f}" for p in r["peaks"])
                print(f"    CBD={r['cbd']:>5}, Age={r['age']:.0f}, pH={r['ph']}: "
                      f"BC={r['bc']:.3f}, peaks=[{peaks_str}], "
                      f"CV={r['cv']:.3f}")
    else:
        print("\n  No bimodal distributions detected in any condition.")
        print("  System appears to have a single attractor at each parameter setting.")

    # Also check for high-CV conditions (precursor to bistability)
    print("\n  ─── High-variance conditions (CV > 0.05, potential bistability precursor) ───")
    high_cv = []
    for d in sorted(run_dir.iterdir()):
        factors = parse_condition(d.name) if d.is_dir() else None
        if not factors:
            continue
        cbd, age, ph = factors
        data = load_replicates(d)
        for sp in ATTRACTOR_SPECIES:
            if sp not in data or len(data[sp]) < 5:
                continue
            mean = np.mean(data[sp])
            cv = np.std(data[sp], ddof=1) / abs(mean) if abs(mean) > 1e-10 else 0
            if cv > 0.05:
                high_cv.append((sp, cbd, age, ph, cv, mean, np.std(data[sp], ddof=1)))

    if high_cv:
        high_cv.sort(key=lambda x: -x[4])
        print(f"\n  Top high-CV conditions (of {len(high_cv)} total):")
        for sp, cbd, age, ph, cv, mean, std in high_cv[:20]:
            print(f"    {sp:>18}: CBD={cbd:>5}, Age={age:.0f}, pH={ph} → "
                  f"CV={cv:.4f} (mean={mean:.3f} ± {std:.3f})")
    else:
        print("  None found.")

    return results


# ─── 2. Preemption Cascades ────────────────────────────────────────────────

def analyze_preemption(run_dir):
    """Compare temporal ordering of pathway activation at CBD=0 vs CBD>0.
    A preemption cascade occurs when CBD blocks an upstream node before
    the downstream cascade can initiate.
    """
    print("\n" + "═" * 78)
    print("2. PREEMPTION CASCADE ANALYSIS")
    print("   Does CBD block upstream pathways before downstream cascades initiate?")
    print("═" * 78)

    # Select representative conditions: CBD=0 and CBD=1 at same Age/pH
    # (CBD=1 is the dose that resolves inflammation)
    target_age, target_ph = 75.0, 7.0  # middle stratum

    pids_needed = set()
    for sp in CASCADE_SPECIES:
        if sp in NAME_TO_PID:
            pids_needed.add(NAME_TO_PID[sp])

    cascade_order_species = [
        "NFkB_p65", "TNFa", "IL1b", "COX2", "Microglia_M1",
        "ROS", "Neuron_Health",
    ]

    print(f"\n  Reference stratum: Age={target_age:.0f}, pH={target_ph}")

    for cbd_dose in [0.0, 1.0, 4.0, 15.0]:
        cond_name = f"condition_CBD_extracellular_eq_{int(cbd_dose) if cbd_dose == int(cbd_dose) else cbd_dose}_Age_eq_{int(target_age)}_pH_eq_{target_ph}"
        cond_dir = run_dir / cond_name
        if not cond_dir.exists():
            # Try float format
            cond_name2 = f"condition_CBD_extracellular_eq_{cbd_dose:.1f}_Age_eq_{int(target_age)}_pH_eq_{target_ph}"
            cond_dir = run_dir / cond_name2
            if not cond_dir.exists():
                continue

        tp, series = load_timeseries(cond_dir, pids_needed)
        if tp is None:
            continue

        print(f"\n  CBD = {cbd_dose} µM:")

        # For each species, find time to reach 50% of its dynamic range
        # (relative to its initial value)
        for sp in cascade_order_species:
            if sp not in series:
                continue
            mean = series[sp]["mean"]
            initial = mean[0]
            final = mean[-1]
            delta = final - initial

            if abs(delta) < 1e-6:
                print(f"    {sp:>18}: flat (Δ={delta:.6f})")
                continue

            # Time to 10%, 50%, 90% of dynamic range
            target_fracs = [0.1, 0.5, 0.9]
            times = {}
            for frac in target_fracs:
                target_val = initial + frac * delta
                for i in range(len(mean)):
                    if (delta > 0 and mean[i] >= target_val) or \
                       (delta < 0 and mean[i] <= target_val):
                        times[frac] = tp[i]
                        break

            t10 = times.get(0.1)
            t50 = times.get(0.5)
            t90 = times.get(0.9)
            t10_str = f"{t10:.0f}s" if t10 is not None else ">10800s"
            t50_str = f"{t50:.0f}s" if t50 is not None else ">10800s"
            t90_str = f"{t90:.0f}s" if t90 is not None else ">10800s"

            print(f"    {sp:>18}: {initial:.2f}→{final:.2f} "
                  f"(t10%={t10_str}, t50%={t50_str}, t90%={t90_str})")

        # Specific preemption check: does CBD suppress NFkB before TNFa peaks?
        if "NFkB_p65" in series and "TNFa" in series:
            nfkb_mean = series["NFkB_p65"]["mean"]
            tnfa_mean = series["TNFa"]["mean"]
            # Find NFkB peak time
            nfkb_peak_idx = np.argmax(nfkb_mean) if np.max(nfkb_mean) > nfkb_mean[0] * 1.1 else 0
            tnfa_peak_idx = np.argmax(tnfa_mean) if np.max(tnfa_mean) > tnfa_mean[0] * 1.1 else 0

            if nfkb_peak_idx > 0:
                print(f"    {'NFkB peak':>18}: t={tp[nfkb_peak_idx]:.0f}s, val={nfkb_mean[nfkb_peak_idx]:.4f}")
            if tnfa_peak_idx > 0:
                print(f"    {'TNFa peak':>18}: t={tp[tnfa_peak_idx]:.0f}s, val={tnfa_mean[tnfa_peak_idx]:.4f}")

            preempted = cbd_dose > 0 and np.max(nfkb_mean) < 1.0
            if preempted:
                print(f"    >>> PREEMPTION: NFkB never activates → downstream cascade blocked")


# ─── 3. Basins of Attraction ───────────────────────────────────────────────

def analyze_basins(run_dir):
    """Cluster replicate endpoints to identify distinct attractors.
    Uses simple k-means-like approach on standardized endpoint vectors.
    """
    print("\n" + "═" * 78)
    print("3. BASINS OF ATTRACTION")
    print("   Cluster analysis of replicate endpoint vectors")
    print("═" * 78)

    # Collect all replicate vectors across all conditions
    basin_species = ["Neuron_Health", "NFkB_p65", "ROS", "Glutathione",
                     "Abeta_Oligomer", "Microglia_M1"]

    # First pass: collect all CBD=0 endpoints as "disease attractor"
    # and all CBD=15 endpoints as "treated attractor"
    attractors = {"disease": [], "treated": []}
    all_vectors = []

    for d in sorted(run_dir.iterdir()):
        factors = parse_condition(d.name) if d.is_dir() else None
        if not factors:
            continue
        cbd, age, ph = factors
        data = load_replicates(d)

        # Build replicate vectors
        n_rep = None
        valid = True
        for sp in basin_species:
            if sp not in data:
                valid = False
                break
            if n_rep is None:
                n_rep = len(data[sp])
            elif len(data[sp]) != n_rep:
                valid = False
                break
        if not valid or n_rep is None:
            continue

        for i in range(n_rep):
            vec = [data[sp][i] for sp in basin_species]
            all_vectors.append({
                "vec": vec, "cbd": cbd, "age": age, "ph": ph, "rep": i,
            })
            if cbd == 0:
                attractors["disease"].append(vec)
            elif cbd == 15:
                attractors["treated"].append(vec)

    if not all_vectors:
        print("  No data.")
        return

    # Compute attractor centroids
    disease_centroid = np.mean(attractors["disease"], axis=0)
    treated_centroid = np.mean(attractors["treated"], axis=0)

    print(f"\n  Attractor centroids ({', '.join(basin_species)}):")
    print(f"    Disease (CBD=0):  [{', '.join(f'{v:.2f}' for v in disease_centroid)}]")
    print(f"    Treated (CBD=15): [{', '.join(f'{v:.2f}' for v in treated_centroid)}]")

    # Euclidean distance between centroids
    centroid_dist = np.linalg.norm(disease_centroid - treated_centroid)
    print(f"    Centroid distance: {centroid_dist:.2f}")

    # For each condition: compute fraction of replicates closer to each attractor
    print(f"\n  Basin membership by condition (fraction closer to 'treated' attractor):")
    print(f"  {'CBD':>6} {'Age':>4} {'pH':>5} | {'frac_treated':>12} {'mean_dist_D':>12} {'mean_dist_T':>12}")
    print(f"  {'─' * 60}")

    by_cbd = defaultdict(list)
    for d in sorted(run_dir.iterdir()):
        factors = parse_condition(d.name) if d.is_dir() else None
        if not factors:
            continue
        cbd, age, ph = factors
        data = load_replicates(d)

        vecs = []
        n_rep = None
        valid = True
        for sp in basin_species:
            if sp not in data:
                valid = False
                break
            if n_rep is None:
                n_rep = len(data[sp])
        if not valid:
            continue

        dists_disease = []
        dists_treated = []
        for i in range(n_rep):
            vec = np.array([data[sp][i] for sp in basin_species])
            dd = np.linalg.norm(vec - disease_centroid)
            dt = np.linalg.norm(vec - treated_centroid)
            dists_disease.append(dd)
            dists_treated.append(dt)

        frac_treated = sum(1 for dd, dt in zip(dists_disease, dists_treated) if dt < dd) / n_rep
        mean_dd = np.mean(dists_disease)
        mean_dt = np.mean(dists_treated)

        by_cbd[cbd].append(frac_treated)

        # Only print a few representative strata
        if age == 75 and ph == 7.0:
            print(f"  {cbd:>6.0f} {age:>4.0f} {ph:>5.1f} | {frac_treated:>12.1%} "
                  f"{mean_dd:>12.2f} {mean_dt:>12.2f}")

    # Summary: marginal basin membership by CBD
    print(f"\n  Marginal basin membership (fraction in 'treated' attractor) by CBD:")
    for cbd in sorted(by_cbd.keys()):
        fracs = by_cbd[cbd]
        print(f"    CBD={cbd:>5.0f}: {np.mean(fracs):.1%} "
              f"(range: {np.min(fracs):.1%} – {np.max(fracs):.1%})")


# ─── 4. Critical Slowing Down ──────────────────────────────────────────────

def analyze_critical_slowing(run_dir):
    """Near phase transitions, stochastic variance increases (critical slowing down).
    Check if inter-replicate variance peaks at intermediate CBD doses.
    """
    print("\n" + "═" * 78)
    print("4. CRITICAL SLOWING DOWN")
    print("   Does variance peak at intermediate doses (phase transition signature)?")
    print("═" * 78)

    species_check = ["Neuron_Health", "NFkB_p65", "ROS", "Abeta_Oligomer", "Glutathione"]

    # Collect variance by CBD dose (marginal across Age×pH)
    var_by_cbd = defaultdict(lambda: defaultdict(list))

    for d in sorted(run_dir.iterdir()):
        factors = parse_condition(d.name) if d.is_dir() else None
        if not factors:
            continue
        cbd, age, ph = factors
        data = load_replicates(d)
        for sp in species_check:
            if sp in data and len(data[sp]) > 1:
                var_by_cbd[sp][cbd].append(np.std(data[sp], ddof=1))

    print(f"\n  Inter-replicate std by CBD dose (marginal mean across Age×pH strata):")
    header = f"  {'CBD':>6}" + "".join(f" | {sp:>15}" for sp in species_check)
    print(header)
    print(f"  {'─' * len(header)}")

    peak_doses = {}
    for sp in species_check:
        doses = sorted(var_by_cbd[sp].keys())
        stds = [np.mean(var_by_cbd[sp][d]) for d in doses]
        peak_idx = np.argmax(stds)
        peak_doses[sp] = (doses[peak_idx], stds[peak_idx])

    cbd_all = sorted(set().union(*(var_by_cbd[sp].keys() for sp in species_check)))
    for cbd in cbd_all:
        row = f"  {cbd:>6.0f}"
        for sp in species_check:
            vals = var_by_cbd[sp].get(cbd, [])
            if vals:
                mean_std = np.mean(vals)
                is_peak = peak_doses.get(sp, (None,))[0] == cbd
                marker = " ◄" if is_peak else ""
                row += f" | {mean_std:>13.4f}{marker}"
            else:
                row += f" | {'N/A':>15}"
        print(row)

    print(f"\n  Peak variance doses:")
    for sp in species_check:
        dose, val = peak_doses[sp]
        print(f"    {sp:>18}: CBD={dose:.0f} (std={val:.4f})")

    # Also check if variance increases with Age (age as bifurcation parameter)
    print(f"\n  Inter-replicate std by Age (marginal, collapsed across CBD×pH):")
    var_by_age = defaultdict(lambda: defaultdict(list))
    for d in sorted(run_dir.iterdir()):
        factors = parse_condition(d.name) if d.is_dir() else None
        if not factors:
            continue
        cbd, age, ph = factors
        data = load_replicates(d)
        for sp in species_check:
            if sp in data and len(data[sp]) > 1:
                var_by_age[sp][age].append(np.std(data[sp], ddof=1))

    ages = sorted(set().union(*(var_by_age[sp].keys() for sp in species_check)))
    header = f"  {'Age':>6}" + "".join(f" | {sp:>15}" for sp in species_check)
    print(header)
    print(f"  {'─' * len(header)}")
    for age in ages:
        row = f"  {age:>6.0f}"
        for sp in species_check:
            vals = var_by_age[sp].get(age, [])
            row += f" | {np.mean(vals):>15.4f}" if vals else f" | {'N/A':>15}"
        print(row)


# ─── 5. Coupling Analysis ──────────────────────────────────────────────────

def analyze_coupling(run_dir):
    """Cross-endpoint correlations within replicates.
    Are inflammation and oxidative stress independently modulated by CBD,
    or are they tightly coupled?
    """
    print("\n" + "═" * 78)
    print("5. ENDPOINT COUPLING ANALYSIS")
    print("   Correlation structure across replicates (are pathways independent?)")
    print("═" * 78)

    coupling_species = [
        "NFkB_p65", "ROS", "Neuron_Health", "Glutathione",
        "Abeta_Oligomer", "Microglia_M1",
    ]

    # Compute correlation matrices at selected CBD doses
    for cbd_target in [0.0, 1.0, 4.0, 15.0]:
        all_data = {sp: [] for sp in coupling_species}
        n_included = 0

        for d in sorted(run_dir.iterdir()):
            factors = parse_condition(d.name) if d.is_dir() else None
            if not factors:
                continue
            cbd, age, ph = factors
            if cbd != cbd_target:
                continue
            data = load_replicates(d)
            valid = all(sp in data for sp in coupling_species)
            if not valid:
                continue
            n_rep = len(data[coupling_species[0]])
            for i in range(n_rep):
                for sp in coupling_species:
                    all_data[sp].append(data[sp][i])
            n_included += 1

        if not all(all_data[sp] for sp in coupling_species):
            continue

        matrix = np.array([all_data[sp] for sp in coupling_species])
        corr = np.corrcoef(matrix)

        print(f"\n  Correlation matrix at CBD={cbd_target:.0f} ({n_included} strata × 30 replicates):")
        header = f"  {'':>15}" + "".join(f" {sp[:8]:>9}" for sp in coupling_species)
        print(header)
        for i, sp1 in enumerate(coupling_species):
            row = f"  {sp1:>15}"
            for j, sp2 in enumerate(coupling_species):
                r = corr[i, j]
                marker = "*" if abs(r) > 0.7 and i != j else " "
                row += f" {r:>8.3f}{marker}"
            print(row)

    # Specific test: NFkB vs ROS decoupling
    print(f"\n  ─── NFkB–ROS coupling across CBD doses ───")
    print(f"  {'CBD':>6} | {'r(NFkB,ROS)':>12} | {'r(NFkB,Neuron)':>15} | {'r(ROS,Neuron)':>14}")
    print(f"  {'─' * 56}")

    for cbd_target in sorted(set(
        parse_condition(d.name)[0]
        for d in run_dir.iterdir()
        if d.is_dir() and parse_condition(d.name)
    )):
        nfkb_vals, ros_vals, nh_vals = [], [], []
        for d in sorted(run_dir.iterdir()):
            factors = parse_condition(d.name) if d.is_dir() else None
            if not factors or factors[0] != cbd_target:
                continue
            data = load_replicates(d)
            if all(sp in data for sp in ["NFkB_p65", "ROS", "Neuron_Health"]):
                nfkb_vals.extend(data["NFkB_p65"])
                ros_vals.extend(data["ROS"])
                nh_vals.extend(data["Neuron_Health"])

        if len(nfkb_vals) > 2:
            r_nfkb_ros = np.corrcoef(nfkb_vals, ros_vals)[0, 1]
            r_nfkb_nh = np.corrcoef(nfkb_vals, nh_vals)[0, 1]
            r_ros_nh = np.corrcoef(ros_vals, nh_vals)[0, 1]
            print(f"  {cbd_target:>6.0f} | {r_nfkb_ros:>12.4f} | {r_nfkb_nh:>15.4f} | {r_ros_nh:>14.4f}")


# ─── 6. Age as Bifurcation Parameter ───────────────────────────────────────

def analyze_age_bifurcation(run_dir):
    """Does increasing age push the system across a bifurcation?
    Check if the CBD dose needed for a given protection level increases
    nonlinearly with age.
    """
    print("\n" + "═" * 78)
    print("6. AGE AS BIFURCATION PARAMETER")
    print("   Does aging shift the system across a critical boundary?")
    print("═" * 78)

    # For each Age level: compute EC50 for Neuron_Health
    # (CBD dose where Neuron_Health reaches midpoint between CBD=0 and CBD=15)
    age_levels = sorted(set(
        parse_condition(d.name)[1]
        for d in run_dir.iterdir()
        if d.is_dir() and parse_condition(d.name)
    ))
    cbd_levels = sorted(set(
        parse_condition(d.name)[0]
        for d in run_dir.iterdir()
        if d.is_dir() and parse_condition(d.name)
    ))

    print(f"\n  Neuron_Health dose-response by Age (marginal across pH):")
    for age in age_levels:
        means = []
        for cbd in cbd_levels:
            vals = [
                np.mean(r_data["Neuron_Health"])
                for d in run_dir.iterdir()
                if d.is_dir() and (f := parse_condition(d.name)) and f[0] == cbd and f[1] == age
                for r_data in [load_replicates(d)]
                if "Neuron_Health" in r_data
            ]
            means.append(np.mean(vals) if vals else None)

        # EC50 interpolation
        valid = [(c, m) for c, m in zip(cbd_levels, means) if m is not None]
        if len(valid) < 3:
            continue
        doses_arr = np.array([v[0] for v in valid])
        means_arr = np.array([v[1] for v in valid])
        mid = (means_arr[0] + means_arr[-1]) / 2
        ec50 = None
        for i in range(len(means_arr) - 1):
            if means_arr[i] <= mid <= means_arr[i + 1]:
                frac = (mid - means_arr[i]) / (means_arr[i + 1] - means_arr[i])
                ec50 = doses_arr[i] + frac * (doses_arr[i + 1] - doses_arr[i])
                break

        # Dynamic range
        dr = means_arr[-1] - means_arr[0]

        # Marginal gain from CBD (slope of dose-response)
        total_gain = means_arr[-1] - means_arr[0]
        gain_0_1 = means_arr[1] - means_arr[0] if len(means_arr) > 1 else 0
        gain_1_15 = means_arr[-1] - means_arr[1] if len(means_arr) > 1 else 0

        ec50_str = f"{ec50:.2f}" if ec50 is not None else "N/A"
        print(f"\n    Age={age:.0f}: range [{means_arr[0]:.1f} → {means_arr[-1]:.1f}], "
              f"Δ={dr:.1f}, EC50={ec50_str}")
        print(f"      Gain CBD 0→1: {gain_0_1:.1f} ({gain_0_1/total_gain*100:.0f}% of total)" if total_gain > 0 else "")
        print(f"      Gain CBD 1→15: {gain_1_15:.1f} ({gain_1_15/total_gain*100:.0f}% of total)" if total_gain > 0 else "")
        print(f"      CBD=0 deficit: {100-means_arr[0]:.1f} neurons lost, "
              f"CBD=15 deficit: {100-means_arr[-1]:.1f} neurons lost")

    # Acceleration: does the CBD=0 deficit grow faster than linearly with age?
    print(f"\n  ─── Age-deficit acceleration ───")
    deficits = []
    for age in age_levels:
        vals = [
            np.mean(r_data["Neuron_Health"])
            for d in run_dir.iterdir()
            if d.is_dir() and (f := parse_condition(d.name)) and f[0] == 0 and f[1] == age
            for r_data in [load_replicates(d)]
            if "Neuron_Health" in r_data
        ]
        if vals:
            deficit = 100 - np.mean(vals)
            deficits.append((age, deficit))
            print(f"    Age={age:.0f}: deficit={deficit:.2f} neurons")

    if len(deficits) >= 3:
        ages = np.array([d[0] for d in deficits])
        defs = np.array([d[1] for d in deficits])
        # Linear fit
        slope, intercept = np.polyfit(ages, defs, 1)
        linear_pred = slope * ages + intercept
        residuals = defs - linear_pred
        nonlinearity = np.max(np.abs(residuals))
        print(f"\n    Linear fit: deficit = {slope:.3f}×Age + {intercept:.1f}")
        print(f"    Max residual from linear: {nonlinearity:.3f}")
        print(f"    {'→ Nonlinear (super-linear) aging effect' if nonlinearity > 0.5 else '→ Approximately linear aging effect'}")


# ─── 7. Irreversibility / Hysteresis ───────────────────────────────────────

def analyze_irreversibility(run_dir):
    """Analyze the irreversible siphon (Neuron_Health) and trap (Abeta_Plaque).
    Is neuronal loss proportional to integrated damage, or does it show threshold behavior?
    """
    print("\n" + "═" * 78)
    print("7. IRREVERSIBILITY & HYSTERESIS")
    print("   Siphon (Neuron_Health drain) and Trap (Plaque accumulation) dynamics")
    print("═" * 78)

    # For selected conditions, analyze time-series of Neuron_Health
    pids = {NAME_TO_PID["Neuron_Health"], NAME_TO_PID["ROS"],
            NAME_TO_PID["Abeta_Plaque"], NAME_TO_PID["NFkB_p65"]}

    target_ph = 7.0

    print(f"\n  Neuron_Health time-profile milestones (pH={target_ph}):")
    print(f"  {'CBD':>5} {'Age':>4} | {'t(99→98)':>10} {'t(99→95)':>10} {'t(99→90)':>10} | {'final':>7} {'rate(/h)':>9}")
    print(f"  {'─' * 70}")

    for age in [55.0, 75.0, 85.0]:
        for cbd in [0.0, 1.0, 4.0, 15.0]:
            cond_name = f"condition_CBD_extracellular_eq_{int(cbd)}_Age_eq_{int(age)}_pH_eq_{target_ph}"
            cond_dir = run_dir / cond_name
            if not cond_dir.exists():
                continue

            tp, series = load_timeseries(cond_dir, pids)
            if tp is None or "Neuron_Health" not in series:
                continue

            nh = series["Neuron_Health"]["mean"]
            initial = nh[0]

            # Time to lose 1, 5, 10 neurons (from initial ~95)
            thresholds = {
                "t(99→98)": initial - (100 - 98),
                "t(99→95)": initial - (100 - 95),
                "t(99→90)": initial - (100 - 90),
            }

            times = {}
            for label, thresh in thresholds.items():
                if thresh < nh[-1]:
                    times[label] = ">3h"
                else:
                    for i in range(len(nh)):
                        if nh[i] <= thresh:
                            times[label] = f"{tp[i]/3600:.2f}h"
                            break
                    else:
                        times[label] = "never"

            final = nh[-1]
            rate = (initial - final) / (tp[-1] / 3600)  # neurons lost per hour

            t1 = times.get("t(99→98)", "N/A")
            t5 = times.get("t(99→95)", "N/A")
            t10 = times.get("t(99→90)", "N/A")

            print(f"  {cbd:>5.0f} {age:>4.0f} | {t1:>10} {t5:>10} {t10:>10} | "
                  f"{final:>7.2f} {rate:>9.3f}")

    # Plaque irreversibility: does plaque ever decrease?
    print(f"\n  Abeta_Plaque accumulation (irreversible trap):")
    for age in [55.0, 85.0]:
        for cbd in [0.0, 4.0, 15.0]:
            cond_name = f"condition_CBD_extracellular_eq_{int(cbd)}_Age_eq_{int(age)}_pH_eq_{target_ph}"
            cond_dir = run_dir / cond_name
            if not cond_dir.exists():
                continue
            tp, series = load_timeseries(cond_dir, pids)
            if tp is None or "Abeta_Plaque" not in series:
                continue

            plaque = series["Abeta_Plaque"]["mean"]
            initial = plaque[0]
            final = plaque[-1]
            peak = np.max(plaque)
            peak_t = tp[np.argmax(plaque)]

            # Check monotonicity
            diffs = np.diff(plaque)
            n_decrease = np.sum(diffs < -1e-8)
            monotonic = n_decrease == 0

            print(f"    CBD={cbd:.0f}, Age={age:.0f}: {initial:.2f}→{final:.2f} "
                  f"(peak={peak:.2f} at {peak_t/3600:.2f}h), "
                  f"monotonic={'YES' if monotonic else f'NO ({n_decrease} decreases)'}")


# ─── 8. Pathway Decoupling Point ───────────────────────────────────────────

def analyze_decoupling(run_dir):
    """Find the CBD dose where inflammation resolution decouples from neuroprotection.
    At CBD=0: both bad. At CBD≥1: inflammation resolved but neurons still declining.
    The 'gap' between inflammation EC50 and neuroprotection EC50 is the decoupling zone.
    """
    print("\n" + "═" * 78)
    print("8. PATHWAY DECOUPLING POINT")
    print("   Gap between inflammation resolution and neuronal rescue")
    print("═" * 78)

    cbd_levels = sorted(set(
        parse_condition(d.name)[0]
        for d in run_dir.iterdir()
        if d.is_dir() and parse_condition(d.name)
    ))

    # Compute per-CBD marginals
    nfkb_by_cbd = defaultdict(list)
    nh_by_cbd = defaultdict(list)
    ros_by_cbd = defaultdict(list)

    for d in sorted(run_dir.iterdir()):
        factors = parse_condition(d.name) if d.is_dir() else None
        if not factors:
            continue
        cbd, age, ph = factors
        data = load_replicates(d)
        if "NFkB_p65" in data:
            nfkb_by_cbd[cbd].extend(data["NFkB_p65"])
        if "Neuron_Health" in data:
            nh_by_cbd[cbd].extend(data["Neuron_Health"])
        if "ROS" in data:
            ros_by_cbd[cbd].extend(data["ROS"])

    print(f"\n  {'CBD':>6} | {'NFkB mean':>10} {'inflam?':>8} | "
          f"{'Neuron mean':>12} {'rescued?':>9} | {'ROS mean':>9} | {'GAP':>6}")
    print(f"  {'─' * 72}")

    for cbd in cbd_levels:
        nfkb_mean = np.mean(nfkb_by_cbd[cbd])
        nh_mean = np.mean(nh_by_cbd[cbd])
        ros_mean = np.mean(ros_by_cbd[cbd])
        inflam = nfkb_mean < 1.0
        rescued = nh_mean >= 95.0
        gap = inflam and not rescued
        inflam_str = "✓ resolved" if inflam else "✗ active"
        rescued_str = "✓ rescued" if rescued else "✗ declining"
        gap_str = "← GAP" if gap else ""

        print(f"  {cbd:>6.0f} | {nfkb_mean:>10.4f} {inflam_str:>8} | "
              f"{nh_mean:>12.2f} {rescued_str:>9} | {ros_mean:>9.4f} | {gap_str}")

    # Quantify the gap: how much Neuron_Health improvement is NOT explained
    # by NFkB resolution
    cbd0_nh = np.mean(nh_by_cbd[0])
    cbd1_nh = np.mean(nh_by_cbd[1])
    cbd15_nh = np.mean(nh_by_cbd[15])

    inflammation_gain = cbd1_nh - cbd0_nh  # gain from resolving inflammation
    antioxidant_gain = cbd15_nh - cbd1_nh  # additional gain from antioxidant axis
    total_gap = 95.0 - cbd15_nh  # residual gap to threshold

    print(f"\n  Decomposition of neuroprotection:")
    print(f"    Baseline (CBD=0):         {cbd0_nh:.2f}")
    print(f"    + Inflammation resolution: +{inflammation_gain:.2f} (CBD 0→1)")
    print(f"    + Antioxidant axis:        +{antioxidant_gain:.2f} (CBD 1→15)")
    print(f"    = Best achievable:         {cbd15_nh:.2f}")
    print(f"    Residual gap to 95%:       {total_gap:.2f}")
    print(f"\n    Inflammation contributes {inflammation_gain/(inflammation_gain+antioxidant_gain)*100:.0f}% "
          f"of total CBD neuroprotection")
    print(f"    Antioxidant contributes {antioxidant_gain/(inflammation_gain+antioxidant_gain)*100:.0f}% "
          f"of total CBD neuroprotection")


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

    print("═" * 78)
    print("BIOLOGICAL PHENOMENA MINING: CBD-AD Factorial Sweep")
    print(f"Run: {run_dir.name}")
    print("═" * 78)

    scan_bistability(run_dir)
    analyze_preemption(run_dir)
    analyze_basins(run_dir)
    analyze_critical_slowing(run_dir)
    analyze_coupling(run_dir)
    analyze_age_bifurcation(run_dir)
    analyze_irreversibility(run_dir)
    analyze_decoupling(run_dir)

    print(f"\n\n{'═' * 78}")
    print("Mining complete.")
    print("═" * 78)


if __name__ == "__main__":
    main()
