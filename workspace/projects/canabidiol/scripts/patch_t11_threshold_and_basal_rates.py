#!/usr/bin/env python3
"""
Two fixes on canabidiol-phase-0-v2.shy after run_20260430_000805:

1. A29 (CBD_intracellular -> T11 ROS_releases_Nrf2): drop threshold from 1 to 0.
   The rate function uses CBD as an additive modulator (`0.3 * CBD/(50+CBD)`),
   not a gate; the threshold=1 test arc was preventing T11 from firing in
   any healthy/baseline run (CBD=0), masking the Keap1->Nrf2 release.

2. T46/T47 basal rates lowered ~4x to target steady-state floors near the
   original initial markings (SOD 20, HO1 30) instead of the previous 75/67
   targets, which over-fed the antioxidant pool and unmasked the T11 issue.
     T46: 0.5  -> 0.13  (SS ~ 0.13 / 0.0067 = 19.4)
     T47: 0.3  -> 0.135 (SS ~ 0.135 / 0.0045 = 30)

Round-trip validated.
"""
import json
from pathlib import Path

MODEL = Path("workspace/projects/canabidiol/models/canabidiol-phase-0-v2.shy")
m = json.loads(MODEL.read_text())

# Fix 1: A29 threshold
a29 = next(a for a in m["arcs"] if a["id"] == "A29")
assert a29["arc_type"] == "test"
assert a29["threshold"] == 1, f"expected A29.threshold==1, got {a29['threshold']}"
a29["threshold"] = 0

# Fix 2: T46/T47 rates
t46 = next(t for t in m["transitions"] if t["id"] == "T46")
t47 = next(t for t in m["transitions"] if t["id"] == "T47")
assert t46["properties"]["rate_function"] == "0.5 * Temperature_factor"
assert t47["properties"]["rate_function"] == "0.3 * Temperature_factor"
t46["properties"]["rate_function"] = "0.13 * Temperature_factor"
t47["properties"]["rate_function"] = "0.135 * Temperature_factor"

MODEL.write_text(json.dumps(m, indent=2))

# Roundtrip
m2 = json.loads(MODEL.read_text())
a29b = next(a for a in m2["arcs"] if a["id"] == "A29")
assert a29b["threshold"] == 0, f"A29 threshold did not persist: {a29b['threshold']}"
assert a29b["arc_type"] == "test"
t46b = next(t for t in m2["transitions"] if t["id"] == "T46")
t47b = next(t for t in m2["transitions"] if t["id"] == "T47")
assert t46b["properties"]["rate_function"] == "0.13 * Temperature_factor"
assert t47b["properties"]["rate_function"] == "0.135 * Temperature_factor"

print("OK: A29.threshold 1->0; T46 rate -> 0.13; T47 rate -> 0.135")
print("  expected: T11 fires (no longer CBD-gated)")
print("  expected: SOD steady ~ 19, HO1 steady ~ 30")
