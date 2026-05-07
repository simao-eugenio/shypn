"""Phase 9 (Option A): drop receptor-CBD K_d 1 µM -> 0.001 µM (1 nM).

Brain CBD reaches ~6e-5 µM in calibrated Phase-8 PK. With K=1, occupancy is
~6e-5 (negligible). With K=0.001, occupancy is ~6e-5/(1e-3+6e-5) ≈ 0.057
(~6% — therapeutically meaningful).

Affected transitions:
  T10  CBD_activates_PPARg     CBD_intra  / (1 + CBD_intra)   -> /(0.001+...)
  T15  CBD_activates_5HT1A     CBD_extra  / (1 + CBD_extra)   -> /(0.001+...)
  T19  CBD_activates_A2A       CBD_extra  / (1 + CBD_extra)   -> /(0.001+...)
  T11  ROS_releases_Nrf2       embedded CBD term, same change

T9 (PPARg_inhibits_NFkB) is linear in PPARg_active, not Hill — left alone;
the upstream PPARg_active boost (3-order) propagates through the gain factor
0.3 * PPARg_active in T9, lifting effective inhibition from ~6e-5 to ~3e-3
relative to baseline 0.005, ~60% boost in inhibition rate.
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

REPO  = Path(__file__).resolve().parents[3].parent
MODEL = REPO / "workspace/projects/canabidiol/models/canabidiol-q1-testable.shy"

EDITS = {
    "T10": (
        "0.02 * CBD_intracellular / (1 + CBD_intracellular)",
        "0.02 * CBD_intracellular / (0.001 + CBD_intracellular)",
    ),
    "T15": (
        "0.015 * CBD_extracellular / (1 + CBD_extracellular)",
        "0.015 * CBD_extracellular / (0.001 + CBD_extracellular)",
    ),
    "T19": (
        "0.012 * CBD_extracellular / (1 + CBD_extracellular)",
        "0.012 * CBD_extracellular / (0.001 + CBD_extracellular)",
    ),
    "T11": (
        "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD_intracellular / (1 + CBD_intracellular)) * Temperature_factor",
        "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD_intracellular / (0.001 + CBD_intracellular)) * Temperature_factor",
    ),
}


def main() -> int:
    bak = MODEL.with_suffix(MODEL.suffix + ".bak")
    shutil.copy2(MODEL, bak)
    print(f"backup: {bak}")
    m = json.loads(MODEL.read_text())
    for tid, (old, new) in EDITS.items():
        t = next(t for t in m["transitions"] if t["id"] == tid)
        props = t.setdefault("properties", {})
        cur = props.get("rate_function")
        if cur != old:
            print(f"WARNING {tid}: pre-patch mismatch\n  expected: {old}\n  got:      {cur}")
        props["rate_function"] = new
        print(f"[{tid}] {t['name']}  K=1 -> 0.001")
    MODEL.write_text(json.dumps(m, indent=2))

    m2 = json.loads(MODEL.read_text())
    for tid, (_, new) in EDITS.items():
        t = next(t for t in m2["transitions"] if t["id"]==tid)
        assert t["properties"]["rate_function"] == new

    sys.path.insert(0, str(REPO / "src"))
    from shypn.data.canvas.document_model import DocumentModel  # type: ignore
    doc = DocumentModel.from_dict(m2)
    tmap = {t.id: t for t in doc.transitions}
    for tid, (_, new) in EDITS.items():
        assert tmap[tid].rate_function == new, f"loader mismatch {tid}"
    print("\n✓ roundtrip + loader assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
