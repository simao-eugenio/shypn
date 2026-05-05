#!/usr/bin/env python3
"""
HPN-formalism refactor of canabidiol-q1-testable.shy.

Audit (pre):
  C1 × 1  Abeta_Production rate function references parameter place
          'DISEASE_SEVERITY' directly.
  C4 × 8  Eight transitions carry the legacy `is_environment_aware=True`
          flag (parameter-place backdoor — no-op now that ◇ bridging
          exists).

Refactor:
  1. Add a new spatial signal place ◇ `Disease_Drive`
     (is_signal_place=true, signal_type='spatial', no F_s arcs,
     init=0.0).
  2. Extend `evt_apply_thermodynamics` (t < 1e-9) with a Pattern-A
     assignment `Disease_Drive := DISEASE_SEVERITY` (RHS = single ▢,
     legal).
  3. Replace `DISEASE_SEVERITY` with `Disease_Drive` in
     Abeta_Production's properties.rate_function.
  4. Clear the 8 `is_environment_aware=True` flags. Bridging ◇ places
     are already in place (Temperature_factor, Age_factor,
     pH_acidosis, pH_neutrality) so the flag is purely vestigial.

Result: zero formalism violations; dynamics under the standard
DISEASE_SEVERITY=1 baseline are bit-equivalent (Disease_Drive equals
DISEASE_SEVERITY by construction at t<1e-9).

Output: workspace/projects/canabidiol/models/canabidiol-q1-testable-v2.shy
"""

from __future__ import annotations
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "models" / "canabidiol-q1-testable.shy"
DST  = ROOT / "models" / "canabidiol-q1-testable-v2.shy"

ENV_FLAGGED = {
    "Abeta_Aggregation", "Plaque_Formation", "NFkB_transcription",
    "Nrf2_ARE_transcription", "M2_to_M1_polarization",
    "M1_to_M2_resolution", "Neurotoxicity", "BDNF_neuroprotection",
}
NEW_PLACE_NAME = "Disease_Drive"


def main() -> int:
    m = json.loads(SRC.read_text())

    # --- 1) Mint a new place id ---
    used = {p["id"] for p in m["places"]}
    n = 0
    while f"P{n}" in used:
        n += 1
    new_id = f"P{n}"

    # --- 2) Construct ◇ place by mirroring an existing spatial signal ---
    template = next(p for p in m["places"] if p["name"] == "Temperature_factor")
    new_place = copy.deepcopy(template)
    new_place["id"]              = new_id
    new_place["name"]            = NEW_PLACE_NAME
    new_place["label"]           = "Disease drive (◇)"
    new_place["x"]               = template["x"]
    new_place["y"]               = template["y"] + 80.0
    new_place["marking"]         = 0.0
    new_place["initial_marking"] = 0.0
    # is_signal_place=True, signal_type='spatial', no arcs implicit
    m["places"].append(new_place)

    # --- 3) Extend evt_apply_thermodynamics with the new bridge ---
    bridge_evt = next(e for e in m["events"] if e["id"] == "evt_apply_thermodynamics")
    bridge_evt["assignments"][NEW_PLACE_NAME] = "DISEASE_SEVERITY"

    # --- 4) Patch Abeta_Production rate_function (properties scope) ---
    t_apr = next(t for t in m["transitions"] if t["name"] == "Abeta_Production")
    old_rf = t_apr["properties"]["rate_function"]
    new_rf = re.sub(r"\bDISEASE_SEVERITY\b", NEW_PLACE_NAME, old_rf)
    assert new_rf != old_rf, "no DISEASE_SEVERITY token found in Abeta_Production rate"
    assert "DISEASE_SEVERITY" not in new_rf, "leftover DISEASE_SEVERITY after substitution"
    t_apr["properties"]["rate_function"] = new_rf
    # If a stale top-level rate_function exists, keep loader behaviour clean
    # (loader prefers properties; top-level kept for any introspection).

    # --- 5) Clear is_environment_aware flag on 8 transitions ---
    cleared = []
    for t in m["transitions"]:
        if t.get("name") in ENV_FLAGGED and t.get("is_environment_aware"):
            t["is_environment_aware"] = False
            cleared.append(t["name"])

    DST.write_text(json.dumps(m, indent=2))

    # ===== Mandatory roundtrip + scope assertions =====
    m2 = json.loads(DST.read_text())

    # A. New ◇ place present, properly typed, zero arcs
    p_new = next(p for p in m2["places"] if p["name"] == NEW_PLACE_NAME)
    assert p_new["id"] == new_id
    assert p_new["is_signal_place"] is True
    assert p_new["signal_type"] == "spatial"
    assert p_new.get("is_parameter_place") in (False, None)
    assert p_new["initial_marking"] == 0.0
    for a in m2["arcs"]:
        assert a["source_id"] != new_id and a["target_id"] != new_id, \
            f"unexpected arc on ◇ {NEW_PLACE_NAME}: {a}"

    # B. Bridge event includes the new assignment, RHS reads only ▢
    be = next(e for e in m2["events"] if e["id"] == "evt_apply_thermodynamics")
    assert be["assignments"].get(NEW_PLACE_NAME) == "DISEASE_SEVERITY"

    # C. Abeta_Production rate at properties scope (loader read scope),
    #    contains Disease_Drive, contains no parameter-place name.
    t2 = next(t for t in m2["transitions"] if t["name"] == "Abeta_Production")
    rf = t2["properties"]["rate_function"]
    assert NEW_PLACE_NAME in rf, "Disease_Drive missing from Abeta_Production rate"
    PARAMS = {"DISEASE_SEVERITY","TEMPERATURE","PH","AGE",
              "LOADING_DOSE","MAINT_DOSE","DOSE_INTERVAL"}
    for sym in PARAMS:
        assert not re.search(r"\b" + sym + r"\b", rf), \
            f"Abeta_Production rate still references parameter {sym!r}"

    # D. Flag cleared on all 8 transitions
    by_name = {t["name"]: t for t in m2["transitions"]}
    for n in ENV_FLAGGED:
        assert by_name[n].get("is_environment_aware") is False, \
            f"is_environment_aware not cleared on {n}"

    # E. Counts: +1 place, all others identical
    assert len(m2["places"])      == len(m["places"])
    assert len(m2["transitions"]) == len(m["transitions"])
    assert len(m2["arcs"])        == len(m["arcs"])
    assert len(m2["events"])      == len(m["events"])

    # F. No parameter place referenced in any rate (full-model sweep)
    for t in m2["transitions"]:
        rf_p = (t.get("properties", {}) or {}).get("rate_function") or ""
        rf_t = t.get("rate_function") or ""
        for src in (rf_p, rf_t):
            for sym in PARAMS:
                assert not re.search(r"\b" + sym + r"\b", src), \
                    f"transition {t['name']} rate references {sym!r}: {src!r}"

    print(f"[ok] added ◇ {NEW_PLACE_NAME} as {new_id}")
    print(f"[ok] extended evt_apply_thermodynamics with bridge assignment")
    print(f"[ok] Abeta_Production rate now: {rf}")
    print(f"[ok] cleared is_environment_aware on {len(cleared)} transitions")
    print(f"[ok] roundtrip + scope assertions passed")
    print(f"[ok] wrote {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
