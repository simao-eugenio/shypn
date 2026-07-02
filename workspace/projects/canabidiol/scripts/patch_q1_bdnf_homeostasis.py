"""Phase 5 patch: BDNF homeostatic production.

Change T16 HT1A_BDNF_production basal term from constant 0.1 to a
negative-feedback Hill in BDNF, so production rises when BDNF is
depleted by T21 (BDNF_neuroprotection).

Old: 0.1 + 0.3 * HT1A_active / (10 + HT1A_active)
New: 0.2 * 5 / (5 + BDNF) + 0.3 * HT1A_active / (10 + HT1A_active)

Equilibrium math (no HT1A, no neuroprotection):
  prod = 0.2 * 5 / (5 + B)
  cons = 0.02 * B   (T26 BDNF_Turnover)
  prod = cons   →   B² + 5B − 50 = 0   →   B = 5.0  ✓ matches current ss
At B = 5, prod = 0.1 (identical to old basal).
At B = 3, prod = 0.125 (vs old 0.1) — recovers from T21 depletion.
At B = 0, prod = 0.20 — robust floor.
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

REPO  = Path(__file__).resolve().parents[3].parent
MODEL = REPO / "workspace/projects/canabidiol/models/canabidiol-q1-testable.shy"

T16_OLD = "0.1 + 0.3 * HT1A_active / (10 + HT1A_active)"
T16_NEW = "0.2 * 5 / (5 + BDNF) + 0.3 * HT1A_active / (10 + HT1A_active)"


def main() -> int:
    bak = MODEL.with_suffix(MODEL.suffix + ".bak")
    shutil.copy2(MODEL, bak)
    print(f"backup: {bak}")

    m = json.loads(MODEL.read_text())
    t16 = next(t for t in m["transitions"] if t["id"] == "T16")
    props = t16.setdefault("properties", {})
    if props.get("rate_function") != T16_OLD:
        print(f"WARNING: T16 rate not the expected pre-patch string:\n  got: {props.get('rate_function')}")
    props["rate_function"] = T16_NEW
    print(f"[rate] T16 -> {T16_NEW}")

    # T16 reads BDNF (P24) remotely. Per AGENT_RULES C9, regular ○ places
    # referenced in Φ must have at least one F/F_t/F_s arc to the transition,
    # OR be in Ψ. BDNF is regular ○ and currently has only an arc T16→BDNF
    # (output). Add a test arc BDNF→T16 to legalise the read.
    arcs = m["arcs"]
    has_in_arc = any(a for a in arcs if a["target_id"] == "T16" and a["source_id"] == "P24")
    if not has_in_arc:
        existing_ids = {a["id"] for a in arcs}
        nid_n = max(int(a["id"][1:]) for a in arcs if a["id"].startswith("A") and a["id"][1:].isdigit())
        new_id = f"A{nid_n + 1}"
        while new_id in existing_ids:
            nid_n += 1
            new_id = f"A{nid_n + 1}"
        new_arc = {
            "id": new_id,
            "name": new_id,
            "arc_type": "test",
            "source_id": "P24",
            "target_id": "T16",
            "source_type": "place",
            "target_type": "transition",
            "weight": 1.0,
            "color": [0.0, 0.0, 1.0],
            "width": 2.0,
            "control_points": [],
        }
        arcs.append(new_arc)
        print(f"[arc] +{new_id}  P24 BDNF --test--> T16  (legalises C9 read)")

    MODEL.write_text(json.dumps(m, indent=2))

    # Roundtrip
    m2 = json.loads(MODEL.read_text())
    t16b = next(t for t in m2["transitions"] if t["id"] == "T16")
    assert t16b["properties"]["rate_function"] == T16_NEW
    in_arcs = [a for a in m2["arcs"] if a["target_id"] == "T16" and a["source_id"] == "P24"]
    assert len(in_arcs) == 1
    assert in_arcs[0]["arc_type"] == "test"

    # Loader
    sys.path.insert(0, str(REPO / "src"))
    from shypn.data.canvas.document_model import DocumentModel  # type: ignore
    from shypn.netobjs.test_arc import TestArc  # type: ignore
    doc = DocumentModel.from_dict(m2)
    tmap = {t.id: t for t in doc.transitions}
    assert "5 / (5 + BDNF)" in (tmap["T16"].rate_function or "")
    amap = {a.id: a for a in doc.arcs}
    assert isinstance(amap[in_arcs[0]["id"]], TestArc)

    print("\n✓ all roundtrip + loader assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
