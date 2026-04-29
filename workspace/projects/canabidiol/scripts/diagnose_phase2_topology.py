#!/usr/bin/env python3
"""
Diagnostic: Can the Phase-2 object-net sustain disease without events?

Loads canabidiol-phase-2.shy, REMOVES all events, sets
Abeta_Monomer.initial_marking to a ladder of values, runs N replicates
each for 4 days, and reports whether the inflammatory cascade
(NFkB, IL1b, ROS, Microglia_M1) actually ignites.

If a sustained pathological state appears at *some* initial-marking
amplitude → events were just under-calibrated (legitimate parameter
tuning is the fix).

If pathology never persists at *any* amplitude → topology defect
(arc weights / θ thresholds wrong); the events cannot be saved by
re-sizing.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from statistics import fmean, pstdev

# repo root assumed via ~/shypn/ on server (and ~/projetos/shypn locally)
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.replicate_runner import ReplicateRunner

MODEL_PATH = REPO / "workspace/projects/canabidiol/models/canabidiol-phase-2.shy"
DURATION = 345600.0  # 4 days
N_REPLICATES = 5
LADDER = [0.05, 1.0, 5.0, 25.0, 100.0]
TARGET_PLACE = "Abeta_Monomer"
MARKERS = [
    "Neuron_Health", "Abeta_Monomer", "Abeta_Oligomer", "Abeta_Plaque",
    "NFkB_p65", "IL1b", "TNFa", "ROS",
    "Microglia_M1", "Microglia_M2",
    "Glutathione", "Nrf2_free", "SOD", "HO1",
]


def run_at_amplitude(amp: float):
    raw = json.loads(MODEL_PATH.read_text())
    # Strip ALL events — we want to test the bare object-net
    raw["events"] = []
    # Re-baseline target
    target_id = None
    for p in raw["places"]:
        if p["name"] == TARGET_PLACE:
            p["initial_marking"] = amp
            target_id = p["id"]
            break
    if target_id is None:
        raise RuntimeError(f"{TARGET_PLACE} not found")

    name2id = {p["name"]: p["id"] for p in raw["places"]}
    model = DocumentModel.from_dict(raw)

    runner = ReplicateRunner(model)
    results = runner.run_replicates(
        n=N_REPLICATES,
        use_parallel=False,
        use_tau_leaping=True,
        duration=DURATION,
        termination_condition="time_only",
        epsilon=0.03,
        max_tau=0.1,
        seed_base=42,
        verbose=False,
    )

    endpoints = {m: [] for m in MARKERS}
    peaks = {m: [] for m in MARKERS}
    for r in results:
        if "error" in r:
            continue
        for m in MARKERS:
            pid = name2id.get(m)
            if pid is None or pid not in r["place_data"]:
                continue
            traj = [v[1] if isinstance(v, tuple) else v
                    for v in r["place_data"][pid]]
            if traj:
                endpoints[m].append(traj[-1])
                peaks[m].append(max(traj))
    return endpoints, peaks


def main():
    print(f"# Phase-2 topology diagnostic — events stripped, "
          f"vary {TARGET_PLACE}.initial_marking")
    print(f"  duration={DURATION/86400:.1f} d, n={N_REPLICATES} reps per amplitude")
    print(f"  ladder: {LADDER}\n")

    print(f"{'amp':>6}  ", end="")
    for m in MARKERS:
        print(f"{m[:9]:>10}", end=" ")
    print()
    print(f"{'-':>6}  ", end="")
    for _ in MARKERS:
        print(f"{'------':>10}", end=" ")
    print()

    for amp in LADDER:
        ends, peaks = run_at_amplitude(amp)
        print(f"END  {amp:>4g}  ", end="")
        for m in MARKERS:
            v = fmean(ends[m]) if ends[m] else None
            print(f"{(f'{v:.2f}' if v is not None else '   --   '):>10}",
                  end=" ")
        print()
        print(f"PEAK {amp:>4g}  ", end="")
        for m in MARKERS:
            v = fmean(peaks[m]) if peaks[m] else None
            print(f"{(f'{v:.2f}' if v is not None else '   --   '):>10}",
                  end=" ")
        print()
        print()

    print("INTERPRETATION:")
    print("  - If at high amp (25, 100) NFkB/IL1b/ROS/M1 PEAK > 0 but END ≈ 0:")
    print("      cascade ignites then quenches → topology has aggressive")
    print("      clearance; events cannot sustain disease at any amplitude")
    print("      WITHOUT also dampening clearance arcs (true topology repair).")
    print("  - If at high amp END values for inflammation markers > 0:")
    print("      a self-sustaining diseased fixed point exists; events were")
    print("      simply under-sized → raise install deltas (param tuning, OK).")
    print("  - If even PEAK stays at 0: input arc weights/thresholds block")
    print("      the cascade independent of substrate amount → topology fix.")


if __name__ == "__main__":
    main()
