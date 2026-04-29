"""Apply arc-type fixes to canabidiol-phase-0.shy per AGENT_RULES.md §8.

Fixes derived from the 2026-04-29 Phase-0 4-day audit:

  M1 (catalyst as normal — should be test):
    P19 (ROS) -> T11 (ROS_releases_Nrf2)        normal -> test
    P19 (ROS) -> T40 (ROS_activates_IKK)        normal -> test
    Rationale: ROS oxidises Keap1 cysteines / sulfenylates IKK Cys179.
    Both reactions are catalytic — ROS is regenerated, not consumed.
    T13 (Antioxidant_Scavenging) keeps ROS as `normal` because GSH+ROS->GSSG
    actually consumes ROS.

  M2 (basal turnover as signal_flow — should be normal):
    P16 (Nrf2_free)         -> T22 (Nrf2_degradation)         signal_flow -> normal
    P30 (CBD_intracellular) -> T29 (CBD_Efflux)               signal_flow -> normal
    P30 (CBD_intracellular) -> T31 (CBD_Brain_Metabolism)     signal_flow -> normal
    Rationale: degradation/turnover/metabolism are basal sinks, not
    cascade-coordinated regulators. signal_flow inputs trigger
    PreemptionCheck which deadlocks the cycle.

Output: canabidiol-phase-0-v2.shy (sibling of phase-0).

Round-trip assertion is mandatory per .github/copilot-instructions.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
SRC = PROJECT / "models" / "canabidiol-phase-0.shy"
DST = PROJECT / "models" / "canabidiol-phase-0-v2.shy"

# (source_id, target_id, expected_old_type, new_type, color)
ARC_FIXES = [
    ("P19", "T11", "normal",      "test",   [0.0, 0.0, 1.0]),  # ROS->T11 catalytic
    ("P19", "T40", "normal",      "test",   [0.0, 0.0, 1.0]),  # ROS->T40 catalytic
    ("P16", "T22", "signal_flow", "normal", [0.0, 0.0, 0.0]),  # Nrf2 turnover
    ("P30", "T29", "signal_flow", "normal", [0.0, 0.0, 0.0]),  # CBD efflux
    ("P30", "T31", "signal_flow", "normal", [0.0, 0.0, 0.0]),  # CBD metabolism
]


def main() -> int:
    m = json.loads(SRC.read_text())

    arc_idx = {(a["source_id"], a["target_id"]): a for a in m["arcs"]}

    for src, tgt, expected_old, new_type, color in ARC_FIXES:
        a = arc_idx.get((src, tgt))
        if a is None:
            print(f"FAIL: arc {src}->{tgt} not found", file=sys.stderr)
            return 1
        if a.get("arc_type") != expected_old:
            print(
                f"FAIL: arc {src}->{tgt} expected arc_type={expected_old} "
                f"but found {a.get('arc_type')}",
                file=sys.stderr,
            )
            return 1
        a["arc_type"] = new_type
        a["color"] = color
        # Clear stale properties.kind if present (per copilot-instructions).
        props = a.get("properties")
        if isinstance(props, dict) and "kind" in props:
            props["kind"] = new_type

    DST.write_text(json.dumps(m, indent=2))

    # Mandatory round-trip validation.
    m2 = json.loads(DST.read_text())
    arc_idx2 = {(a["source_id"], a["target_id"]): a for a in m2["arcs"]}
    for src, tgt, _, new_type, _ in ARC_FIXES:
        a = arc_idx2[(src, tgt)]
        assert a["arc_type"] == new_type, (
            f"round-trip failure: {src}->{tgt} arc_type={a['arc_type']} "
            f"expected {new_type}"
        )
        props = a.get("properties", {})
        if "kind" in props:
            assert props["kind"] == new_type, (
                f"stale properties.kind on {src}->{tgt}: {props['kind']} "
                f"vs arc_type={new_type}"
            )

    print(f"OK  wrote {DST.relative_to(PROJECT.parent.parent.parent)}")
    print("    Applied 5 arc-type fixes; round-trip validated.")
    for src, tgt, old, new, _ in ARC_FIXES:
        print(f"      {src}->{tgt}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
