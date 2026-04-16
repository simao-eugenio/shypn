#!/usr/bin/env python3
"""
EPO Commitment Threshold Sweep
================================
Runs N stochastic replicates at each EPO concentration to find the minimum
EPO level required for robust erythroid (GATA1>PU1) fate commitment.

Outputs:
  - dev/epo_sweep_results.csv   — raw replicate-level results
  - dev/epo_sweep_summary.csv   — commitment probability per EPO level
  - Console: commitment probability curve + threshold estimate

Usage:
    python dev/epo_commitment_sweep.py
"""
import sys
import os
import csv
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.replicate_runner import ReplicateRunner

# ── Configuration ────────────────────────────────────────────────────────────
MODEL_PATH   = "workspace/projects/gata/models/phase3a_spatial_clean.shy"
GCSF_LEVEL   = 0.1     # Fixed GCSF (mM) — match prior single-run baseline
EPO_LEVELS   = [0.40, 0.42, 0.43, 0.44, 0.445, 0.449, 0.450, 0.451, 0.455, 0.46, 0.48, 0.50]
N_REPLICATES = 20
DURATION     = 3600.0  # seconds
TIME_STEP    = 1.0     # seconds per step — coarser for speed (protein dynamics >> 1s)
SEED_BASE    = 42

# Attractor assignment: GATA1_nuc / PU1_nuc ratio at final time
COMMIT_THRESHOLD_RATIO = 1.25   # > threshold → committed ERYTHROID
UNCOMMIT_THRESHOLD_RATIO = 0.8  # < threshold → committed MYELOID
# Between 0.8 and 1.25 → oscillating / undecided

OUT_REPLICATES = "dev/epo_sweep_results.csv"
OUT_SUMMARY    = "dev/epo_sweep_summary.csv"

# ── Place / place names to track ──────────────────────────────────────────────
EPO_PLACE   = "EPO_external"
GCSF_PLACE  = "GCSF_external"
GATA1_NUC   = "GATA1_Protein_nuc"
PU1_NUC     = "PU1_Protein_nuc"

def find_place(model, name):
    for p in model.places:
        if p.name == name:
            return p
    raise ValueError(f"Place '{name}' not found in model")

def set_ic(place, value):
    """Set initial condition on a place — all three canonical fields."""
    place.tokens = value
    place.initial_tokens = value
    if hasattr(place, 'marking'):
        place.marking = value
    if hasattr(place, 'initial_marking'):
        place.initial_marking = value

def build_id_map(model):
    """Return {place_id: place_name} mapping."""
    return {p.id: p.name for p in model.places}

def final_ratio(result, id_map):
    """Return GATA1_nuc / PU1_nuc at the final time point."""
    fm = result.get('final_marking', {})
    gata1 = None
    pu1 = None

    # final_marking keys are place IDs — look up names via id_map
    for pid, val in fm.items():
        name = id_map.get(pid, '')
        if name == GATA1_NUC:
            gata1 = val
        elif name == PU1_NUC:
            pu1 = val

    if gata1 is None or pu1 is None:
        return None
    return gata1 / pu1 if pu1 > 0 else float('inf')

def classify(ratio):
    if ratio is None:
        return "unknown"
    if ratio > COMMIT_THRESHOLD_RATIO:
        return "ERYTHROID"
    if ratio < UNCOMMIT_THRESHOLD_RATIO:
        return "MYELOID"
    return "UNDECIDED"

# ── Main sweep ────────────────────────────────────────────────────────────────
print(f"Loading model: {MODEL_PATH}")
model = DocumentModel.load_from_file(MODEL_PATH)
print(f"  Places: {len(model.places)}, Transitions: {len(model.transitions)}")

p_epo  = find_place(model, EPO_PLACE)
p_gcsf = find_place(model, GCSF_PLACE)

# Fix GCSF at 50 for all runs
set_ic(p_gcsf, GCSF_LEVEL)
print(f"  GCSF fixed at {GCSF_LEVEL} mM")

all_rows = []
summary_rows = []

print(f"\n{'EPO':>8}  {'ERYTH':>6}  {'MYELO':>6}  {'UNDEC':>6}  {'P(eryth)':>9}  {'mean_ratio':>11}")
print("-" * 60)

for epo in EPO_LEVELS:
    set_ic(p_epo, epo)

    id_map = build_id_map(model)
    runner = ReplicateRunner(model)
    t0 = time.time()
    results = runner.run_replicates(
        n=N_REPLICATES,
        use_parallel=True,
        use_tau_leaping=True,
        duration=DURATION,
        termination_condition="time_only",
        time_step=TIME_STEP,
        seed_base=SEED_BASE,
        verbose=False,
    )
    elapsed = time.time() - t0

    counts = {"ERYTHROID": 0, "MYELOID": 0, "UNDECIDED": 0, "unknown": 0}
    ratios = []

    for i, res in enumerate(results):
        r = final_ratio(res, id_map)
        fate = classify(r)
        counts[fate] = counts.get(fate, 0) + 1
        all_rows.append({
            "epo": epo,
            "replicate": i,
            "ratio": round(r, 4) if r is not None else None,
            "fate": fate,
            "stopped": res.get("stopped_reason", "?"),
        })
        if r is not None:
            ratios.append(r)

    n_valid = N_REPLICATES - counts.get("unknown", 0)
    p_eryth = counts["ERYTHROID"] / n_valid if n_valid > 0 else 0
    mean_r = sum(ratios) / len(ratios) if ratios else 0

    summary_rows.append({
        "epo": epo,
        "n_replicates": N_REPLICATES,
        "erythroid": counts["ERYTHROID"],
        "myeloid": counts["MYELOID"],
        "undecided": counts["UNDECIDED"],
        "p_erythroid": round(p_eryth, 3),
        "mean_ratio": round(mean_r, 3),
        "wall_s": round(elapsed, 1),
    })

    bar = "█" * int(p_eryth * 20)
    print(f"{epo:>8.2f}  {counts['ERYTHROID']:>6}  {counts['MYELOID']:>6}  {counts['UNDECIDED']:>6}  "
          f"{p_eryth:>9.3f}  {mean_r:>11.3f}  {bar}")

# ── Save results ──────────────────────────────────────────────────────────────
with open(OUT_REPLICATES, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["epo","replicate","ratio","fate","stopped"])
    w.writeheader()
    w.writerows(all_rows)

with open(OUT_SUMMARY, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["epo","n_replicates","erythroid","myeloid",
                                       "undecided","p_erythroid","mean_ratio","wall_s"])
    w.writeheader()
    w.writerows(summary_rows)

print(f"\nResults saved:")
print(f"  {OUT_REPLICATES}")
print(f"  {OUT_SUMMARY}")

# ── Threshold estimate ────────────────────────────────────────────────────────
print("\n── Commitment threshold estimate ─────────────────────────────────")
for row in summary_rows:
    if row["p_erythroid"] >= 0.5:
        print(f"  50% ERYTHROID commitment first reached at EPO = {row['epo']} mM")
        break
else:
    print("  50% commitment not reached within tested EPO range")

for row in summary_rows:
    if row["p_erythroid"] >= 0.9:
        print(f"  90% ERYTHROID commitment first reached at EPO = {row['epo']} mM")
        break
else:
    print("  90% commitment not reached within tested EPO range")
