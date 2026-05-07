"""Phase 3 patch: fix CBD PK floor + BDNF/NFkB inhibition K_d.

Changes:
  1. CBD_intracellular.compartment_volume: 1000.0 -> 1.0
     Harmonises with CBD_plasma/CBD_extracellular (also rescaled to 1.0)
     so absorption produces correctly-scaled intracellular concentration.
  2. T48 CBD_BBB_Transfer rate constant: 0.00005 -> 0.0000001 (500x lower)
     Restores T30 hepatic clearance as dominant plasma sink (~1% brain partition).
  3. T21 BDNF_neuroprotection NFkB inhibition K_d: 2.0 -> 50.0
     Relaxes inhibition so BDNF protection survives moderate inflammation.

Roundtrip-validated; .bak written.
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3].parent  # .../shypn
MODEL = REPO / "workspace/projects/canabidiol/models/canabidiol-q1-testable.shy"

PLACE_CV_UPDATES = {
    "CBD_plasma":         1.0,
    "CBD_extracellular":  1.0,
    "CBD_intracellular":  1.0,
}

T48_OLD = "0.00005 * CBD_plasma * Temperature_factor"
T48_NEW = "0.0000001 * CBD_plasma * Temperature_factor"

T21_OLD_FRAGMENT = "(1 - NFkB_p65 / (2.0 + NFkB_p65))"
T21_NEW_FRAGMENT = "(1 - NFkB_p65 / (50.0 + NFkB_p65))"


def main() -> int:
    if not MODEL.exists():
        print(f"ERROR: model not found at {MODEL}", file=sys.stderr)
        return 1
    bak = MODEL.with_suffix(MODEL.suffix + ".bak")
    shutil.copy2(MODEL, bak)
    print(f"backup: {bak}")

    m = json.loads(MODEL.read_text())

    # 1) compartment_volume harmonisation
    cv_before = {}
    for p in m["places"]:
        if p["name"] in PLACE_CV_UPDATES:
            cv_before[p["name"]] = p.get("compartment_volume")
            p["compartment_volume"] = PLACE_CV_UPDATES[p["name"]]
            print(f"[cv] {p['id']} {p['name']:<22s} {cv_before[p['name']]} -> {p['compartment_volume']}")

    # 2) T48 rate
    t48 = next(t for t in m["transitions"] if t["id"] == "T48")
    props = t48.setdefault("properties", {})
    if props.get("rate_function") != T48_OLD:
        print(f"WARNING: T48 rate is not the expected pre-patch string:\n  got: {props.get('rate_function')}")
    props["rate_function"] = T48_NEW
    print(f"[rate] T48 CBD_BBB_Transfer -> {T48_NEW}")

    # 3) T21 rate fragment
    t21 = next(t for t in m["transitions"] if t["id"] == "T21")
    p21 = t21.setdefault("properties", {})
    rate21 = p21.get("rate_function") or ""
    if T21_OLD_FRAGMENT not in rate21:
        print(f"WARNING: T21 rate fragment not found:\n  got: {rate21}")
    p21["rate_function"] = rate21.replace(T21_OLD_FRAGMENT, T21_NEW_FRAGMENT)
    print(f"[rate] T21 BDNF_neuroprotection -> {p21['rate_function']}")

    MODEL.write_text(json.dumps(m, indent=2))

    # === Roundtrip assertions ===
    m2 = json.loads(MODEL.read_text())
    for p in m2["places"]:
        if p["name"] in PLACE_CV_UPDATES:
            assert p["compartment_volume"] == PLACE_CV_UPDATES[p["name"]], \
                f"cv roundtrip failed on {p['name']}"
            assert "tokens" not in p or p["tokens"] == p.get("initial_marking"), \
                f"stale tokens key on {p['name']}"
    t48b = next(t for t in m2["transitions"] if t["id"] == "T48")
    assert t48b["properties"]["rate_function"] == T48_NEW, "T48 rate roundtrip failed"
    t21b = next(t for t in m2["transitions"] if t["id"] == "T21")
    assert T21_NEW_FRAGMENT in t21b["properties"]["rate_function"], "T21 rate roundtrip failed"
    assert T21_OLD_FRAGMENT not in t21b["properties"]["rate_function"], "T21 old fragment still present"

    # Loader-level verification
    sys.path.insert(0, str(REPO / "src"))
    from shypn.data.canvas.document_model import DocumentModel  # type: ignore
    doc = DocumentModel.from_dict(m2)
    pmap = {p.name: p for p in doc.places}
    for name, want in PLACE_CV_UPDATES.items():
        got = getattr(pmap[name], "compartment_volume", None)
        assert got == want, f"loader cv mismatch on {name}: {got} != {want}"
    tmap = {t.id: t for t in doc.transitions}
    assert "0.0000001" in (tmap["T48"].rate_function or ""), "loader T48 rate mismatch"
    assert "(50.0 + NFkB_p65)" in (tmap["T21"].rate_function or ""), "loader T21 rate mismatch"

    print("\n✓ all roundtrip + loader assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
