"""Phase 7: restore Aβ aggregation dynamics + trim T48 PK.

Changes:
  1. T4 Abeta_Aggregation: transition_type 'adaptive' -> 'continuous'
     Adaptive switching flipped T4 to stochastic in Phase-6 low-marking regime,
     where Aβ_Monomer < 1.0 throughout. With W=1.0 input arc, stochastic mode
     can never satisfy M >= W, so T4 fires 0 times. Continuous mode handles
     fractional flows correctly.
  2. T5 Plaque_Formation: transition_type 'stochastic' -> 'continuous'
     Same root cause for Aβ_Oligomer < 1.0; T5 = 0 firings.
  3. T48 CBD_BBB_Transfer rate: 1e-5 -> 3e-6
     Phase-6 boost was too aggressive — degraded plasma t½ from 19h to 12h.
     3e-6 keeps brain partition at ~3-5% with t½ closer to 19h.

Receptor K_d (T10/T15/T19/T11): NOT changed. Current K=1 µM is biologically
realistic for CBD intermediate-affinity. Brain CBD is low (10^-4 µM) but the
PPARγ→NFkB amplification cascade is already engaging measurably (T9 fires
2986x). Lowering K_d below 1 µM is physiologically suspect.
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

REPO  = Path(__file__).resolve().parents[3].parent
MODEL = REPO / "workspace/projects/canabidiol/models/canabidiol-q1-testable.shy"

T48_OLD = "0.00001 * CBD_plasma * Temperature_factor"
T48_NEW = "0.000003 * CBD_plasma * Temperature_factor"


def main() -> int:
    bak = MODEL.with_suffix(MODEL.suffix + ".bak")
    shutil.copy2(MODEL, bak)
    print(f"backup: {bak}")

    m = json.loads(MODEL.read_text())

    # 1) T4 adaptive -> continuous
    t4 = next(t for t in m["transitions"] if t["id"] == "T4")
    old4 = t4.get("transition_type")
    t4["transition_type"] = "continuous"
    # Drop adaptive-only fields (loader ignores when type=continuous, but clean)
    for k in ("adaptive_filter", "volume_threshold", "prefer_continuous"):
        t4.pop(k, None)
        if "properties" in t4 and isinstance(t4["properties"], dict):
            t4["properties"].pop(k, None)
    print(f"[type] T4 Abeta_Aggregation  {old4} -> continuous")

    # 2) T5 stochastic -> continuous
    t5 = next(t for t in m["transitions"] if t["id"] == "T5")
    old5 = t5.get("transition_type")
    t5["transition_type"] = "continuous"
    print(f"[type] T5 Plaque_Formation   {old5} -> continuous")

    # 3) T48 rate
    t48 = next(t for t in m["transitions"] if t["id"] == "T48")
    props = t48.setdefault("properties", {})
    if props.get("rate_function") != T48_OLD:
        print(f"WARNING: T48 not at expected pre-patch:\n  got: {props.get('rate_function')}")
    props["rate_function"] = T48_NEW
    print(f"[rate] T48 -> {T48_NEW}")

    MODEL.write_text(json.dumps(m, indent=2))

    # Roundtrip
    m2 = json.loads(MODEL.read_text())
    assert next(t for t in m2["transitions"] if t["id"]=="T4")["transition_type"] == "continuous"
    assert next(t for t in m2["transitions"] if t["id"]=="T5")["transition_type"] == "continuous"
    t48b = next(t for t in m2["transitions"] if t["id"]=="T48")
    assert t48b["properties"]["rate_function"] == T48_NEW

    sys.path.insert(0, str(REPO / "src"))
    from shypn.data.canvas.document_model import DocumentModel  # type: ignore
    doc = DocumentModel.from_dict(m2)
    tmap = {t.id: t for t in doc.transitions}
    assert tmap["T4"].transition_type == "continuous"
    assert tmap["T5"].transition_type == "continuous"
    assert "0.000003 * CBD_plasma" in (tmap["T48"].rate_function or "")

    print("\n✓ all roundtrip + loader assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
