"""Phase 4 patch: boost T48 (CBD BBB transfer) 10x, revert A49/A50 to test.

Changes:
  1. T48 CBD_BBB_Transfer rate constant: 1e-7 -> 1e-6 (10x boost)
     Restores brain delivery while keeping ~10:1 hepatic:brain ratio.
  2. A49 (P26 PPARg_active -> T18) signal_flow -> test
  3. A50 (P27 A2A_active   -> T18) signal_flow -> test
     Removes M2-trap deadlock so basal 0.005*M1 term in T18 can fire.
     PPARγ/A2A still modulate T18 rate via remote sensing in rate_function.

Roundtrip-validated; .bak written.
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3].parent
MODEL = REPO / "workspace/projects/canabidiol/models/canabidiol-q1-testable.shy"

T48_OLD = "0.0000001 * CBD_plasma * Temperature_factor"
T48_NEW = "0.000001 * CBD_plasma * Temperature_factor"

REVERT_TO_TEST = ["A49", "A50"]


def main() -> int:
    if not MODEL.exists():
        print(f"ERROR: model not found at {MODEL}", file=sys.stderr)
        return 1
    bak = MODEL.with_suffix(MODEL.suffix + ".bak")
    shutil.copy2(MODEL, bak)
    print(f"backup: {bak}")

    m = json.loads(MODEL.read_text())

    # 1) T48 rate
    t48 = next(t for t in m["transitions"] if t["id"] == "T48")
    props = t48.setdefault("properties", {})
    if props.get("rate_function") != T48_OLD:
        print(f"WARNING: T48 rate not the expected pre-patch string:\n  got: {props.get('rate_function')}")
    props["rate_function"] = T48_NEW
    print(f"[rate] T48 -> {T48_NEW}")

    # 2 & 3) Revert A49/A50 to test
    for aid in REVERT_TO_TEST:
        a = next(a for a in m["arcs"] if a["id"] == aid)
        old = a.get("arc_type")
        a["arc_type"] = "test"
        a["color"] = [0.0, 0.0, 1.0]  # blue (test)
        # Strip signal_flow-only fields and properties.kind
        for k in ("michaelis_K", "hill_n", "suppression_epsilon",
                  "activation_energy", "reference_temperature",
                  "consumes", "produces"):
            a.pop(k, None)
        if "properties" in a and isinstance(a["properties"], dict):
            a["properties"].pop("kind", None)
        # Test arcs typically have weight 1; restore
        a["weight"] = 1.0
        print(f"[arc] {aid} {old} -> test  (W=1, color=blue)")

    MODEL.write_text(json.dumps(m, indent=2))

    # === Roundtrip ===
    m2 = json.loads(MODEL.read_text())
    t48b = next(t for t in m2["transitions"] if t["id"] == "T48")
    assert t48b["properties"]["rate_function"] == T48_NEW, "T48 rate roundtrip failed"
    for aid in REVERT_TO_TEST:
        a = next(a for a in m2["arcs"] if a["id"] == aid)
        assert a["arc_type"] == "test", f"{aid} did not roundtrip to test"
        assert a["weight"] == 1.0, f"{aid} weight not 1"
        assert "michaelis_K" not in a, f"{aid} retains michaelis_K"

    # Loader-level
    sys.path.insert(0, str(REPO / "src"))
    from shypn.data.canvas.document_model import DocumentModel  # type: ignore
    from shypn.netobjs.test_arc import TestArc  # type: ignore
    doc = DocumentModel.from_dict(m2)
    amap = {a.id: a for a in doc.arcs}
    for aid in REVERT_TO_TEST:
        assert isinstance(amap[aid], TestArc), \
            f"{aid} loaded as {type(amap[aid]).__name__}, expected TestArc"
    tmap = {t.id: t for t in doc.transitions}
    assert "0.000001" in (tmap["T48"].rate_function or ""), "T48 loader rate mismatch"

    print("\n✓ all roundtrip + loader assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
