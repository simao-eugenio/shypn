"""Phase 8: T48 mid-point — 3e-6 -> 6e-6.

Phase-7 over-corrected: brain CBD collapsed 3x and rescue with it.
Aim for brain CBD ~6e-5, plasma t1/2 ~17h.
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

REPO  = Path(__file__).resolve().parents[3].parent
MODEL = REPO / "workspace/projects/canabidiol/models/canabidiol-q1-testable.shy"

T48_OLD = "0.000003 * CBD_plasma * Temperature_factor"
T48_NEW = "0.000006 * CBD_plasma * Temperature_factor"


def main() -> int:
    bak = MODEL.with_suffix(MODEL.suffix + ".bak")
    shutil.copy2(MODEL, bak)
    print(f"backup: {bak}")
    m = json.loads(MODEL.read_text())
    t48 = next(t for t in m["transitions"] if t["id"] == "T48")
    props = t48.setdefault("properties", {})
    if props.get("rate_function") != T48_OLD:
        print(f"WARNING: T48 not at expected pre-patch:\n  got: {props.get('rate_function')}")
    props["rate_function"] = T48_NEW
    print(f"[rate] T48 -> {T48_NEW}")
    MODEL.write_text(json.dumps(m, indent=2))

    m2 = json.loads(MODEL.read_text())
    t48b = next(t for t in m2["transitions"] if t["id"]=="T48")
    assert t48b["properties"]["rate_function"] == T48_NEW

    sys.path.insert(0, str(REPO / "src"))
    from shypn.data.canvas.document_model import DocumentModel  # type: ignore
    doc = DocumentModel.from_dict(m2)
    tmap = {t.id: t for t in doc.transitions}
    assert "0.000006 * CBD_plasma" in (tmap["T48"].rate_function or "")
    print("\n✓ roundtrip + loader assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
