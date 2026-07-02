#!/usr/bin/env python3
"""
Patch canabidiol-phase-0-v2.shy in place: add basal transcription transitions
for SOD and HO1 so the antioxidant pool does not collapse to 0 once ROS clears.

Targets steady-state floors:
  SOD floor ≈ basal_rate / k_deg = 0.5 / 0.0067 ≈ 75
  HO1 floor ≈ 0.3 / 0.0045 ≈ 67

Adds:
  T46 Basal_SOD_Transcription  (continuous, source) -> SOD  via A101
  T47 Basal_HO1_Transcription  (continuous, source) -> HO1  via A102

Roundtrip-validated.
"""
import json
from pathlib import Path

MODEL = Path("workspace/projects/canabidiol/models/canabidiol-phase-0-v2.shy")

m = json.loads(MODEL.read_text())
n2id = {p["name"]: p["id"] for p in m["places"]}
SOD_ID = n2id["SOD"]
HO1_ID = n2id["HO1"]

existing_t = {t["id"] for t in m["transitions"]}
existing_a = {a["id"] for a in m["arcs"]}
assert "T46" not in existing_t and "T47" not in existing_t, "T46/T47 already present"
assert "A101" not in existing_a and "A102" not in existing_a, "A101/A102 already present"

def make_basal(tid, name, rate, x, y):
    return {
        "id": tid,
        "name": name,
        "label": name.replace("_", "\n"),
        "object_type": "transition",
        "x": x,
        "y": y,
        "width": 60.0,
        "height": 15.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.0, 0.8, 0.0],
        "border_color": [0.0, 0.8, 0.0],
        "border_width": 3.0,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "race",
        "is_source": True,
        "is_sink": False,
        "guard": 1,
        "properties": {
            "rate_function": rate,
            "rate_function_display": "k_basal",
        },
        "is_environment_aware": False,
        "compartment": "cytoplasm",
        "adaptive_filter": None,
        "volume_threshold": None,
        "prefer_continuous": None,
    }

def make_arc(aid, src_t, dst_p):
    return {
        "id": aid,
        "name": aid,
        "object_type": "arc",
        "arc_type": "normal",
        "source_id": src_t,
        "target_id": dst_p,
        "source_type": "transition",
        "target_type": "place",
        "weight": 1.0,
        "threshold": 0.0,
        "color": [0.0, 0.0, 0.0],
        "width": 2.0,
        "control_points": [],
    }

# Place near SOD/HO1 for visual clarity (probe their coords)
place_xy = {p["id"]: (p["x"], p["y"]) for p in m["places"]}
sx, sy = place_xy[SOD_ID]
hx, hy = place_xy[HO1_ID]

m["transitions"].append(
    make_basal("T46", "Basal_SOD_Transcription",
               "0.5 * Temperature_factor", sx - 80.0, sy)
)
m["transitions"].append(
    make_basal("T47", "Basal_HO1_Transcription",
               "0.3 * Temperature_factor", hx - 80.0, hy)
)
m["arcs"].append(make_arc("A101", "T46", SOD_ID))
m["arcs"].append(make_arc("A102", "T47", HO1_ID))

MODEL.write_text(json.dumps(m, indent=2))

# ----- Roundtrip validation -----
m2 = json.loads(MODEL.read_text())
ids2 = {t["id"]: t for t in m2["transitions"]}
arcs2 = {a["id"]: a for a in m2["arcs"]}

for tid, expected_rate, target in [
    ("T46", "0.5 * Temperature_factor", SOD_ID),
    ("T47", "0.3 * Temperature_factor", HO1_ID),
]:
    t = ids2[tid]
    assert t["transition_type"] == "continuous"
    assert t["is_source"] is True
    assert t["properties"]["rate_function"] == expected_rate, \
        f"{tid} rate_function did not land in properties (got {t['properties'].get('rate_function')})"

for aid, src, dst in [("A101", "T46", SOD_ID), ("A102", "T47", HO1_ID)]:
    a = arcs2[aid]
    assert a["arc_type"] == "normal"
    assert a["source_id"] == src and a["target_id"] == dst
    for k in ("id", "arc_type", "source_id", "target_id", "weight"):
        assert k in a, f"new arc {aid} missing top-level {k}"

print(f"OK: added T46, T47, A101, A102 to {MODEL.name}")
print(f"  Transitions: {len(m2['transitions'])}, Arcs: {len(m2['arcs'])}")
print("  SOD steady-state floor ≈ 0.5 / 0.0067 ≈ 75")
print("  HO1 steady-state floor ≈ 0.3 / 0.0045 ≈ 67")
