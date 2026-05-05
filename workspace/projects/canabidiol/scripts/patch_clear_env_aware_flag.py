#!/usr/bin/env python3
"""
Clear the legacy `is_environment_aware=True` flag on 8 transitions of
canabidiol-phase-1.shy.

The model is already substantively HPN-compliant:
- Temperature_factor / Age_factor / pH_acidosis / pH_neutrality exist as
  spatial signal places (◇), and `evt_apply_thermodynamics` (trigger
  t < 1e-9) bridges ▢ TEMPERATURE/AGE/PH into them per the
  ▢ + event → ◇ → Φ rule.
- Rate functions reference only the ◇ bridge symbols (verified by grep:
  zero direct mentions of TEMPERATURE / PH / AGE / DISEASE_SEVERITY /
  Q10 / DSev in any Φ).

The only audit hits (C4) come from the leftover `is_environment_aware`
flag on 8 transitions. With ◇ bridging in place the flag is a no-op —
clearing it makes the model audit-clean without changing dynamics.

Output: workspace/projects/canabidiol/models/canabidiol-phase-1-v2.shy
"""

from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "models" / "canabidiol-phase-1.shy"
DST  = ROOT / "models" / "canabidiol-phase-1-v2.shy"

ENV_FLAGGED = {
    "Abeta_Aggregation", "Plaque_Formation", "NFkB_transcription",
    "Nrf2_ARE_transcription", "M2_to_M1_polarization",
    "M1_to_M2_resolution", "Neurotoxicity", "BDNF_neuroprotection",
}


def main() -> int:
    m = json.loads(SRC.read_text())

    cleared: list[str] = []
    for t in m["transitions"]:
        if t.get("name") in ENV_FLAGGED and t.get("is_environment_aware"):
            t["is_environment_aware"] = False
            cleared.append(t["name"])

    if len(cleared) != len(ENV_FLAGGED):
        missing = ENV_FLAGGED - set(cleared)
        print(f"[warn] expected {len(ENV_FLAGGED)} hits, got {len(cleared)}; missing: {missing}")

    DST.write_text(json.dumps(m, indent=2))

    # ----- Mandatory roundtrip assertions -----
    m2 = json.loads(DST.read_text())

    # 1. All 8 transitions now flag-cleared at top-level
    by_name = {t["name"]: t for t in m2["transitions"]}
    for n in ENV_FLAGGED:
        assert by_name[n].get("is_environment_aware") is False, \
            f"is_environment_aware not cleared on {n}"

    # 2. Bridge ◇ places intact
    bridge_names = {"Temperature_factor", "Age_factor", "pH_acidosis", "pH_neutrality"}
    bridges = {p["name"]: p for p in m2["places"] if p["name"] in bridge_names}
    for n in bridge_names:
        p = bridges[n]
        assert p.get("is_signal_place") is True, f"{n} lost is_signal_place"
        assert p.get("signal_type") == "spatial", f"{n} signal_type changed"
        assert p.get("is_parameter_place") in (False, None), f"{n} became parameter"
    # No arcs touching bridge places
    bridge_ids = {p["id"] for p in bridges.values()}
    for a in m2["arcs"]:
        assert a["source_id"] not in bridge_ids and a["target_id"] not in bridge_ids, \
            f"unexpected arc on a ◇ bridge place: {a}"

    # 3. evt_apply_thermodynamics still bridges all four
    bridge_evt = next(e for e in m2.get("events", []) if e.get("id") == "evt_apply_thermodynamics")
    assigns = bridge_evt.get("assignments", {})
    for n in bridge_names:
        assert n in assigns, f"evt_apply_thermodynamics missing assignment for {n}"

    # 4. Parameter places untouched
    expected_params = {"TEMPERATURE","PH","AGE","LOADING_DOSE","MAINT_DOSE",
                       "DOSE_INTERVAL","DISEASE_SEVERITY"}
    actual_params = {p["name"] for p in m2["places"] if p.get("is_parameter_place")}
    assert actual_params == expected_params, \
        f"parameter set drift: got {actual_params}, expected {expected_params}"

    # 5. Counts unchanged
    assert len(m2["places"])      == len(m["places"])
    assert len(m2["transitions"]) == len(m["transitions"])
    assert len(m2["arcs"])        == len(m["arcs"])
    assert len(m2.get("events", [])) == len(m.get("events", []))

    print(f"[ok] cleared is_environment_aware on {len(cleared)} transitions:")
    for n in cleared:
        print(f"     - {n}")
    print(f"[ok] roundtrip + scope assertions passed")
    print(f"[ok] wrote {DST.relative_to(ROOT.parent.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
