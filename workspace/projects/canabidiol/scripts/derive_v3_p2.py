#!/usr/bin/env python3
"""Derive cbd_ad_neuroprotection_v3_p2.shy from v3 for Protocol P2.

Per protocols/P2__v3.md:
  - MAINT_DOSE.initial_marking := 0      (no scheduled redose)
  - DOSE_INTERVAL.initial_marking := 1e9 (so evt_maint_* never fire)
  - add evt_washout: at t > 5400, CBD_extracellular := 0  (withdrawal)

The model file is written fresh; the v3 source is read-only.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "models" / "cbd_ad_neuroprotection_v3.shy"
DST = PROJECT / "models" / "cbd_ad_neuroprotection_v3_p2.shy"


def main() -> None:
    model = json.loads(SRC.read_text())

    # 1. Pin dose schedule so model's evt_maint_* never fire.
    pinned = {"MAINT_DOSE": 0.0, "DOSE_INTERVAL": 1e9}
    for p in model["places"]:
        if p["name"] in pinned:
            v = pinned[p["name"]]
            p["initial_marking"] = v
            p["marking"] = v
            p["tokens"] = v

    # 2. Append evt_washout to the events list.
    events = model.setdefault("events", [])
    if not any(e.get("id") == "evt_washout" for e in events):
        evt_washout = {
            "id": "evt_washout",
            "name": "evt_washout",
            "trigger": "t > 5400",
            "delay": 0.0,
            "use_values_from_trigger_time": True,
            "priority": 0,
            "assignments": {"CBD_extracellular": "0"},
            "metadata": {
                "group": "withdrawal",
                "purpose": (
                    "Protocol P2 withdrawal challenge: zero extracellular CBD "
                    "at t = 5400 s (90 min) to test post-drug recovery."
                ),
            },
        }
        events.append(evt_washout)

    # 3. Update bookkeeping.
    md = model.setdefault("metadata", {})
    md["derived_from"] = "cbd_ad_neuroprotection_v3.shy"
    md["derivation"] = (
        "Protocol P2 variant: MAINT_DOSE=0, DOSE_INTERVAL=1e9, +evt_washout"
    )
    md.setdefault("object_counts", {})["events"] = len(events)

    DST.write_text(json.dumps(model, indent=2))
    print(f"wrote {DST.relative_to(PROJECT)}  ({len(events)} events)")


if __name__ == "__main__":
    main()
