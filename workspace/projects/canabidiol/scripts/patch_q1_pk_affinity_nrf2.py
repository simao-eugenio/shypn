"""Phase 6 patch: CBD pharmacological calibration + Nrf2 output arc fix.

Changes:
 (PK)
  1. T28 CBD_Absorption rate constant: 0.05 -> 5.0       (x100, fast passive diffusion)
  2. T48 CBD_BBB_Transfer rate constant: 1e-6 -> 1e-5    (x10, ~5-10% brain partition)
 (Receptor affinity — bring K_d into intermediate-affinity range)
  3. T10 CBD_activates_PPARg: K 20 -> 1
  4. T15 CBD_activates_5HT1A: K 20 -> 1
  5. T19 CBD_activates_A2A:   K 20 -> 1
  6. T11 ROS_releases_Nrf2 CBD-modulator term: K 50 -> 1
 (Bug fix)
  7. A30 (T11 -> Nrf2_free) arc_type signal_flow -> normal
     Root cause of Nrf2_ARE_transcription = 0 firings.
     signal_flow output arcs are not deposited by the engine; T11 was firing
     17000 times but never depositing Nrf2_free, so the ARE branch starved.
 (Cleanup)
  8. Drop 'Disease_Drive' from evt_apply_thermodynamics assignments (unread).
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

REPO  = Path(__file__).resolve().parents[3].parent
MODEL = REPO / "workspace/projects/canabidiol/models/canabidiol-q1-testable.shy"

T28_OLD = "0.05 * CBD_extracellular * Temperature_factor"
T28_NEW = "5.0 * CBD_extracellular * Temperature_factor"

T48_OLD = "0.000001 * CBD_plasma * Temperature_factor"
T48_NEW = "0.00001 * CBD_plasma * Temperature_factor"

T10_OLD = "0.02 * CBD_intracellular / (20 + CBD_intracellular)"
T10_NEW = "0.02 * CBD_intracellular / (1 + CBD_intracellular)"

T15_OLD = "0.015 * CBD_extracellular / (20 + CBD_extracellular)"
T15_NEW = "0.015 * CBD_extracellular / (1 + CBD_extracellular)"

T19_OLD = "0.012 * CBD_extracellular / (20 + CBD_extracellular)"
T19_NEW = "0.012 * CBD_extracellular / (1 + CBD_extracellular)"

T11_OLD = "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD_intracellular / (50 + CBD_intracellular)) * Temperature_factor"
T11_NEW = "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD_intracellular / (1 + CBD_intracellular)) * Temperature_factor"


def main() -> int:
    bak = MODEL.with_suffix(MODEL.suffix + ".bak")
    shutil.copy2(MODEL, bak)
    print(f"backup: {bak}")

    m = json.loads(MODEL.read_text())

    edits = [
        ("T28", T28_OLD, T28_NEW),
        ("T48", T48_OLD, T48_NEW),
        ("T10", T10_OLD, T10_NEW),
        ("T15", T15_OLD, T15_NEW),
        ("T19", T19_OLD, T19_NEW),
        ("T11", T11_OLD, T11_NEW),
    ]
    for tid, old, new in edits:
        t = next(t for t in m["transitions"] if t["id"] == tid)
        props = t.setdefault("properties", {})
        if props.get("rate_function") != old:
            print(f"WARNING: {tid} rate not the expected pre-patch string:\n  got: {props.get('rate_function')}")
        props["rate_function"] = new
        print(f"[rate] {tid} -> {new}")

    # Fix A30 signal_flow output -> normal
    a30 = next(a for a in m["arcs"] if a["id"] == "A30")
    old_type = a30.get("arc_type")
    a30["arc_type"] = "normal"
    a30["color"] = [0.0, 0.0, 0.0]
    for k in ("michaelis_K", "hill_n", "suppression_epsilon",
              "activation_energy", "reference_temperature",
              "consumes", "produces"):
        a30.pop(k, None)
    if "properties" in a30 and isinstance(a30["properties"], dict):
        a30["properties"].pop("kind", None)
    a30["weight"] = 1.0
    print(f"[arc] A30 (T11->Nrf2_free) {old_type} -> normal")

    # Cleanup: drop Disease_Drive from evt_apply_thermodynamics
    for e in m.get("events", []):
        if e.get("id") == "evt_apply_thermodynamics":
            asg = e.get("assignments", {})
            if "Disease_Drive" in asg:
                asg.pop("Disease_Drive")
                print("[event] removed Disease_Drive from evt_apply_thermodynamics")
            break

    MODEL.write_text(json.dumps(m, indent=2))

    # Roundtrip
    m2 = json.loads(MODEL.read_text())
    for tid, _, new in edits:
        t = next(t for t in m2["transitions"] if t["id"] == tid)
        assert t["properties"]["rate_function"] == new, f"{tid} rate roundtrip failed"
    a30b = next(a for a in m2["arcs"] if a["id"] == "A30")
    assert a30b["arc_type"] == "normal"
    assert "michaelis_K" not in a30b

    # Loader
    sys.path.insert(0, str(REPO / "src"))
    from shypn.data.canvas.document_model import DocumentModel  # type: ignore
    from shypn.netobjs.arc import Arc  # type: ignore
    from shypn.netobjs.signal_flow_arc import SignalFlowArc  # type: ignore
    doc = DocumentModel.from_dict(m2)
    amap = {a.id: a for a in doc.arcs}
    a30c = amap["A30"]
    assert not isinstance(a30c, SignalFlowArc), f"A30 still loaded as SignalFlowArc"
    assert isinstance(a30c, Arc)
    tmap = {t.id: t for t in doc.transitions}
    assert "5.0 * CBD_extracellular" in (tmap["T28"].rate_function or "")
    assert "0.00001 * CBD_plasma" in (tmap["T48"].rate_function or "")
    assert "(1 + CBD_intracellular)" in (tmap["T10"].rate_function or "")
    assert "(1 + CBD_extracellular)" in (tmap["T15"].rate_function or "")
    assert "(1 + CBD_extracellular)" in (tmap["T19"].rate_function or "")
    assert "0.3 * CBD_intracellular / (1 + CBD_intracellular)" in (tmap["T11"].rate_function or "")

    print("\n✓ all roundtrip + loader assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
