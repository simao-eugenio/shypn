#!/usr/bin/env python3
"""
CBD-AD Neuroprotection Sweep Analysis — End-to-End Test
=======================================================
Analyzes the 6-condition CBD dose sweep (run_20260420_132707).
Computes dose-response statistics, phase transition detection,
EC50 estimation, and bistability signatures.

Run on server: python3 dev/analyze_cbd_sweep.py
"""

import json
import csv
import os
import sys
import numpy as np
from pathlib import Path
from dataclasses import dataclass

# ─── Configuration ──────────────────────────────────────────────────────────

RUN_DIR = Path("workspace/projects/canabidiol/experiments/results/run_20260420_132707")

# Primary biomarkers (place name → description)
PRIMARY = {
    "Glutathione": "Antioxidant capacity",
    "NFkB_p65": "Inflammation switch",
    "Neuron_Health": "Neuroprotection endpoint",
    "Abeta_Oligomer": "Toxic amyloid species",
    "ROS": "Oxidative stress",
}

# Secondary biomarkers
SECONDARY = {
    "TNFa": "Pro-inflammatory cytokine",
    "IL1b": "Pro-inflammatory cytokine",
    "IL6": "Pro-inflammatory cytokine",
    "COX2": "Inflammatory mediator",
    "Microglia_M1": "Pro-inflammatory polarization",
    "Microglia_M2": "Anti-inflammatory polarization",
    "HO1": "Nrf2-driven antioxidant",
    "SOD": "Superoxide dismutase",
    "PPARg_active": "CBD anti-inflammatory effector",
    "GSSG": "Oxidized glutathione",
    "Abeta_Plaque": "Plaque burden",
    "BDNF": "Neurotrophic factor",
    "Nrf2_free": "Antioxidant TF",
}

# CBD dose mapping from condition names
# NOTE: Baseline has P1=100 (same as CBD_extracellular_eq_100), so we exclude
# it from dose-response curves to avoid duplication. Keep it for reference.
CONDITION_DOSES = {
    "CBD_extracellular_eq_0": 0.0,
    "CBD_extracellular_eq_15": 15.0,
    "CBD_extracellular_eq_35": 35.0,
    "CBD_extracellular_eq_55": 55.0,
    "CBD_extracellular_eq_100": 100.0,
}


@dataclass
class ConditionStats:
    name: str
    cbd_dose: float
    n_replicates: int
    biomarkers: dict  # name -> {mean, std, ci95_lo, ci95_hi, median, iqr}


def load_replicates(condition_dir: Path) -> dict:
    """Load replicates.csv and return dict of place_name -> array of final values."""
    csv_path = condition_dir / "replicates.csv"
    if not csv_path.exists():
        return {}

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    result = {}
    for col in rows[0].keys():
        if col.endswith("_final"):
            place_name = col.replace("_final", "")
            values = []
            for row in rows:
                try:
                    values.append(float(row[col]))
                except (ValueError, KeyError):
                    pass
            result[place_name] = np.array(values)
    return result


def compute_stats(values: np.ndarray) -> dict:
    """Compute summary statistics with 95% CI."""
    n = len(values)
    mean = np.mean(values)
    std = np.std(values, ddof=1)
    se = std / np.sqrt(n)
    ci95 = 1.96 * se
    return {
        "mean": mean,
        "std": std,
        "ci95_lo": mean - ci95,
        "ci95_hi": mean + ci95,
        "median": np.median(values),
        "iqr": np.percentile(values, 75) - np.percentile(values, 25),
        "min": np.min(values),
        "max": np.max(values),
        "cv": std / mean if mean != 0 else float("inf"),
    }


def estimate_ec50(doses: np.ndarray, responses: np.ndarray, increasing: bool = True) -> float | None:
    """
    Simple linear-interpolation EC50 estimation.
    For increasing response (e.g., Glutathione): find dose where response = 50% of max range.
    For decreasing response (e.g., NFkB_p65): find dose where response = 50% of max range from top.
    """
    if len(doses) < 3:
        return None

    # Sort by dose
    order = np.argsort(doses)
    d = doses[order]
    r = responses[order]

    # Define EC50 target as midpoint of observed range
    r_min, r_max = np.min(r), np.max(r)
    if r_max - r_min < 1e-10:
        return None  # No response range

    target = (r_min + r_max) / 2.0

    # Linear interpolation to find dose at target
    if increasing:
        # Response goes up with dose
        for i in range(len(r) - 1):
            if (r[i] <= target <= r[i + 1]) or (r[i] >= target >= r[i + 1]):
                # Interpolate
                frac = (target - r[i]) / (r[i + 1] - r[i]) if r[i + 1] != r[i] else 0.5
                return float(d[i] + frac * (d[i + 1] - d[i]))
    else:
        # Response goes down with dose
        for i in range(len(r) - 1):
            if (r[i] >= target >= r[i + 1]) or (r[i] <= target <= r[i + 1]):
                frac = (target - r[i]) / (r[i + 1] - r[i]) if r[i + 1] != r[i] else 0.5
                return float(d[i] + frac * (d[i + 1] - d[i]))

    return None  # EC50 not in range


def detect_phase_transition(doses: np.ndarray, responses: np.ndarray, threshold_slope_ratio: float = 3.0) -> dict:
    """
    Detect phase-transition-like behavior: a region where the slope is much steeper
    than the average slope. Returns transition zone info.
    """
    order = np.argsort(doses)
    d = doses[order]
    r = responses[order]

    if len(d) < 3:
        return {"detected": False}

    # Remove duplicate dose levels (keep first)
    unique_mask = np.concatenate(([True], np.diff(d) > 0))
    d = d[unique_mask]
    r = r[unique_mask]
    if len(d) < 3:
        return {"detected": False}

    # Compute local slopes
    slopes = np.diff(r) / np.diff(d)
    abs_slopes = np.abs(slopes)
    mean_slope = np.mean(abs_slopes)

    if mean_slope < 1e-10:
        return {"detected": False}

    # Find max slope region
    max_idx = np.argmax(abs_slopes)
    max_slope = abs_slopes[max_idx]

    # Phase transition = max slope >> mean slope
    ratio = max_slope / mean_slope
    detected = ratio > threshold_slope_ratio

    return {
        "detected": detected,
        "slope_ratio": float(ratio),
        "transition_zone": (float(d[max_idx]), float(d[max_idx + 1])),
        "max_slope": float(slopes[max_idx]),
        "mean_slope": float(mean_slope),
    }


def detect_bistability(values: np.ndarray, n_bins: int = 10) -> dict:
    """
    Detect bimodal distribution (bistability signature) via dip test heuristic.
    Uses histogram gap detection as a simple proxy.
    """
    if len(values) < 10:
        return {"detected": False}

    # Histogram
    hist, bin_edges = np.histogram(values, bins=n_bins)

    # Find valleys (bins with 0 or very low count between two peaks)
    peaks = []
    for i in range(1, len(hist) - 1):
        if hist[i] > hist[i - 1] and hist[i] > hist[i + 1]:
            peaks.append(i)

    bimodal = len(peaks) >= 2
    cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 0

    return {
        "detected": bimodal,
        "n_peaks": len(peaks),
        "cv": float(cv),
        "range": float(np.max(values) - np.min(values)),
    }


def analyze_m1_m2_ratio(condition_data: dict) -> dict:
    """Analyze microglial polarization ratio."""
    m1 = condition_data.get("Microglia_M1")
    m2 = condition_data.get("Microglia_M2")
    if m1 is None or m2 is None:
        return {}

    ratio = m1 / np.maximum(m2, 0.01)  # Avoid div/0
    total = m1 + m2

    return {
        "m1_m2_ratio_mean": float(np.mean(ratio)),
        "m1_m2_ratio_std": float(np.std(ratio)),
        "total_microglia_mean": float(np.mean(total)),
        "m1_fraction_mean": float(np.mean(m1 / np.maximum(total, 0.01))),
        "m2_fraction_mean": float(np.mean(m2 / np.maximum(total, 0.01))),
        "polarization_bistability": detect_bistability(ratio),
    }


def main():
    # Resolve paths
    if not RUN_DIR.exists():
        # Try from shypn root
        alt = Path(os.environ.get("SHYPN_ROOT", ".")) / RUN_DIR
        if alt.exists():
            run_dir = alt
        else:
            print(f"ERROR: Run directory not found: {RUN_DIR}")
            sys.exit(1)
    else:
        run_dir = RUN_DIR

    print("=" * 70)
    print("CBD-AD NEUROPROTECTION SWEEP ANALYSIS")
    print(f"Run: {run_dir.name}")
    print("=" * 70)

    # ─── Load all conditions ────────────────────────────────────────────────
    conditions = []
    for cond_name, cbd_dose in sorted(CONDITION_DOSES.items(), key=lambda x: x[1]):
        cond_dir = run_dir / f"condition_{cond_name}"
        if not cond_dir.exists():
            print(f"  SKIP: {cond_name} (dir not found)")
            continue

        data = load_replicates(cond_dir)
        if not data:
            print(f"  SKIP: {cond_name} (no data)")
            continue

        biomarkers = {}
        for name in list(PRIMARY.keys()) + list(SECONDARY.keys()):
            if name in data:
                biomarkers[name] = compute_stats(data[name])

        conditions.append(ConditionStats(
            name=cond_name,
            cbd_dose=cbd_dose,
            n_replicates=len(next(iter(data.values()))),
            biomarkers=biomarkers,
        ))
        conditions[-1]._raw = data  # Keep raw for downstream

    print(f"\nLoaded {len(conditions)} conditions, "
          f"{conditions[0].n_replicates} replicates each\n")

    # ─── 1. Dose-Response Table ─────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("1. DOSE-RESPONSE: PRIMARY BIOMARKERS (mean ± 95% CI)")
    print("─" * 70)

    doses = np.array([c.cbd_dose for c in conditions])

    # Print table header
    header = f"{'CBD Dose':>10}"
    for name in PRIMARY:
        header += f" | {name:>15}"
    print(header)
    print("-" * len(header))

    for c in conditions:
        row = f"{c.cbd_dose:>10.0f}"
        for name in PRIMARY:
            s = c.biomarkers.get(name, {})
            if s:
                row += f" | {s['mean']:>9.3f}±{s['ci95_hi']-s['mean']:.3f}"
            else:
                row += f" | {'N/A':>15}"
        print(row)

    # ─── 2. EC50 Estimation ─────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("2. EC50 ESTIMATION")
    print("─" * 70)

    # Determine response direction for each biomarker
    response_direction = {
        "Glutathione": True,   # increases with CBD
        "NFkB_p65": False,     # decreases with CBD
        "Neuron_Health": True,  # increases with CBD
        "Abeta_Oligomer": False,  # decreases with CBD
        "ROS": False,          # decreases with CBD
        "HO1": True,           # increases with CBD
        "SOD": True,           # increases with CBD
        "BDNF": True,          # increases with CBD
        "Microglia_M1": False,  # decreases with CBD
        "Microglia_M2": True,   # increases with CBD
    }

    means_by_biomarker = {}
    for name in list(PRIMARY.keys()) + list(SECONDARY.keys()):
        means = np.array([c.biomarkers[name]["mean"] for c in conditions if name in c.biomarkers])
        if len(means) == len(doses):
            means_by_biomarker[name] = means

    print(f"\n{'Biomarker':>20} | {'EC50 (µM)':>10} | {'Direction':>10} | {'Range':>15}")
    print("-" * 65)

    for name in list(PRIMARY.keys()) + ["HO1", "SOD", "BDNF", "Microglia_M1", "Microglia_M2"]:
        if name not in means_by_biomarker:
            continue
        means = means_by_biomarker[name]
        increasing = response_direction.get(name, True)
        ec50 = estimate_ec50(doses, means, increasing=increasing)
        r_range = f"{np.min(means):.3f} → {np.max(means):.3f}"
        direction = "↑" if increasing else "↓"
        ec50_str = f"{ec50:.1f}" if ec50 is not None else "N/A"
        print(f"{name:>20} | {ec50_str:>10} | {direction:>10} | {r_range:>15}")

    # ─── 3. Phase Transition Detection ──────────────────────────────────────
    print("\n" + "─" * 70)
    print("3. PHASE TRANSITION DETECTION (NFkB_p65)")
    print("─" * 70)

    if "NFkB_p65" in means_by_biomarker:
        pt = detect_phase_transition(doses, means_by_biomarker["NFkB_p65"])
        print(f"  Detected: {pt['detected']}")
        print(f"  Slope ratio (max/mean): {pt['slope_ratio']:.2f}")
        if pt["detected"]:
            print(f"  Transition zone: {pt['transition_zone'][0]:.0f} – {pt['transition_zone'][1]:.0f} µM")
            print(f"  Max slope: {pt['max_slope']:.4f}")
    else:
        print("  NFkB_p65 data not available")

    # Also check ROS and Abeta for transitions
    for name in ["ROS", "Abeta_Oligomer", "Glutathione"]:
        if name in means_by_biomarker:
            pt = detect_phase_transition(doses, means_by_biomarker[name])
            print(f"\n  {name}: detected={pt['detected']}, "
                  f"slope_ratio={pt['slope_ratio']:.2f}, "
                  f"zone={pt.get('transition_zone', 'N/A')}")

    # ─── 4. Microglial Polarization (Bistability) ───────────────────────────
    print("\n" + "─" * 70)
    print("4. MICROGLIAL POLARIZATION (M1/M2 Bistability)")
    print("─" * 70)

    for c in conditions:
        m1m2 = analyze_m1_m2_ratio(c._raw)
        if m1m2:
            print(f"  CBD={c.cbd_dose:>5.0f}: "
                  f"M1/M2={m1m2['m1_m2_ratio_mean']:.3f} "
                  f"(M1={m1m2['m1_fraction_mean']:.1%}, M2={m1m2['m2_fraction_mean']:.1%}) "
                  f"bimodal={m1m2['polarization_bistability']['detected']}")

    # ─── 5. Neuronal Siphon & Plaque Trap ───────────────────────────────────
    print("\n" + "─" * 70)
    print("5. IRREVERSIBILITY ANALYSIS")
    print("─" * 70)

    print("\n  Neuron_Health (siphon — irreversible drain):")
    for c in conditions:
        nh = c._raw.get("Neuron_Health")
        if nh is not None:
            pct_full = (np.mean(nh) / 100.0) * 100
            drained = np.sum(nh < 50)  # replicates where >50% neurons lost
            print(f"    CBD={c.cbd_dose:>5.0f}: "
                  f"mean={np.mean(nh):.1f}/100, "
                  f"retention={pct_full:.1f}%, "
                  f"replicates_below_50={drained}/{len(nh)}")

    print("\n  Abeta_Plaque (trap — irreversible accumulation):")
    for c in conditions:
        plaque = c._raw.get("Abeta_Plaque")
        if plaque is not None:
            print(f"    CBD={c.cbd_dose:>5.0f}: "
                  f"mean={np.mean(plaque):.6f}, "
                  f"max={np.max(plaque):.6f}, "
                  f"nonzero={np.sum(plaque > 0)}/{len(plaque)}")

    # ─── 6. Two Therapeutic Windows ─────────────────────────────────────────
    print("\n" + "─" * 70)
    print("6. THERAPEUTIC WINDOWS")
    print("─" * 70)
    print("  Window 1: Neuronal rescue (Neuron_Health ≈ 100)")
    print("  Window 2: Inflammation resolution (NFkB_p65 → 0)")
    print()

    for c in conditions:
        nh = c.biomarkers.get("Neuron_Health", {}).get("mean", 0)
        nfkb = c.biomarkers.get("NFkB_p65", {}).get("mean", 0)
        neuronal_ok = nh >= 95
        inflam_ok = nfkb < 1.0
        status = ""
        if neuronal_ok and inflam_ok:
            status = "FULL PROTECTION"
        elif neuronal_ok:
            status = "Neuronal rescue only"
        elif inflam_ok:
            status = "Anti-inflammatory only"
        else:
            status = "UNPROTECTED"
        print(f"  CBD={c.cbd_dose:>5.0f}: "
              f"Neuron={nh:.1f} ({'✓' if neuronal_ok else '✗'}) "
              f"NFkB={nfkb:.4f} ({'✓' if inflam_ok else '✗'}) "
              f"→ {status}")

    # ─── 7. Nrf2/Antioxidant Response ──────────────────────────────────────
    print("\n" + "─" * 70)
    print("7. Nrf2/ANTIOXIDANT AXIS")
    print("─" * 70)

    for c in conditions:
        gsh = c.biomarkers.get("Glutathione", {}).get("mean", 0)
        gssg = c.biomarkers.get("GSSG", {}).get("mean", 0)
        nrf2 = c.biomarkers.get("Nrf2_free", {}).get("mean", 0)
        ho1 = c.biomarkers.get("HO1", {}).get("mean", 0)
        sod = c.biomarkers.get("SOD", {}).get("mean", 0)
        redox = gsh / (gsh + gssg) if (gsh + gssg) > 0 else 0
        print(f"  CBD={c.cbd_dose:>5.0f}: "
              f"GSH={gsh:.1f}, GSSG={gssg:.2f}, "
              f"Redox={redox:.3f}, "
              f"Nrf2={nrf2:.2f}, HO1={ho1:.1f}, SOD={sod:.1f}")

    # ─── 8. Summary JSON ────────────────────────────────────────────────────
    summary = {
        "run": run_dir.name,
        "n_conditions": len(conditions),
        "n_replicates": conditions[0].n_replicates if conditions else 0,
        "doses": doses.tolist(),
        "primary_endpoints": {},
        "ec50": {},
        "phase_transitions": {},
        "therapeutic_windows": {},
    }

    for name in PRIMARY:
        if name in means_by_biomarker:
            summary["primary_endpoints"][name] = {
                "means": means_by_biomarker[name].tolist(),
                "direction": "increasing" if response_direction.get(name, True) else "decreasing",
            }
            ec50 = estimate_ec50(doses, means_by_biomarker[name],
                                 increasing=response_direction.get(name, True))
            if ec50 is not None:
                summary["ec50"][name] = ec50
            pt = detect_phase_transition(doses, means_by_biomarker[name])
            summary["phase_transitions"][name] = pt

    out_path = run_dir / "analysis_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n\n{'=' * 70}")
    print(f"Analysis summary written to: {out_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
