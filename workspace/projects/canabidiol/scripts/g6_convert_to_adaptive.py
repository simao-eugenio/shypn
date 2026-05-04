#!/usr/bin/env python3
"""
G6 — convert all 48 transitions in canabidiol-q1-testable.shy to `adaptive`.

Loader scope per copilot-instructions.md (audited 2026-04-28):
  * transition_type     — top-level only
  * prefer_continuous   — top-level wins, properties fallback (we set top-level)
  * volume_threshold    — top-level wins, properties fallback (we set top-level)
  * rate_function       — properties ONLY (we never touch it)

Rationale (2026-05-02): the model has 40 hand-pinned `continuous`,
7 hand-pinned `stochastic`, and 1 `adaptive`. This bypasses the
engine's auto-classification, leaving CPU/GPU numerical-path
differences to drive basin selection in a bistable system. Letting
every dynamic transition choose its branch per-step (continuous
when volume × propensity × dt is large, stochastic when small)
restores the original design.

Default thresholds:
  volume_threshold  = 0.01    # engine default
  prefer_continuous = True    # tie-breaker toward ODE branch

A `.shy.bak` is written before overwriting.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

MODEL = Path(__file__).resolve().parents[1] / "models" / "canabidiol-q1-testable.shy"
VOLUME_THRESHOLD = 0.01
PREFER_CONTINUOUS = True


def main() -> None:
    if not MODEL.exists():
        raise SystemExit(f"model not found: {MODEL}")

    raw = MODEL.read_text()
    m = json.loads(raw)

    backup = MODEL.with_suffix(MODEL.suffix + ".bak.g6")
    backup.write_text(raw)
    print(f"[g6] backup -> {backup.name}")

    before = {"continuous": 0, "stochastic": 0, "adaptive": 0, "other": 0}
    for t in m["transitions"]:
        tt = t.get("transition_type", "continuous")
        before[tt if tt in before else "other"] += 1

    print(f"[g6] before: {before}")

    changed = 0
    for t in m["transitions"]:
        old = t.get("transition_type")
        # Only convert dynamic biology transitions.
        # Engine treats `immediate` and `timed` as protocol primitives;
        # adaptive selection only makes sense for continuous/stochastic.
        if old not in ("continuous", "stochastic", "adaptive"):
            continue

        # Top-level fields (loader scope).
        t["transition_type"] = "adaptive"
        t["prefer_continuous"] = PREFER_CONTINUOUS
        t["volume_threshold"] = VOLUME_THRESHOLD

        # Strip stale `properties` mirrors so the top-level wins
        # unambiguously (loader: top-level → properties fallback).
        props = t.setdefault("properties", {})
        for stale_key in ("prefer_continuous", "volume_threshold"):
            props.pop(stale_key, None)

        if old != "adaptive":
            changed += 1

    after = {"continuous": 0, "stochastic": 0, "adaptive": 0, "other": 0}
    for t in m["transitions"]:
        tt = t.get("transition_type", "continuous")
        after[tt if tt in after else "other"] += 1
    print(f"[g6] after : {after}  (retyped {changed})")

    MODEL.write_text(json.dumps(m, indent=2))

    # ---------------- roundtrip validation -----------------------------
    m2 = json.loads(MODEL.read_text())
    fail = 0
    for t in m2["transitions"]:
        if t["transition_type"] != "adaptive":
            print(f"  ! {t['name']}: type={t['transition_type']} (not adaptive)")
            fail += 1
            continue
        if t.get("prefer_continuous") is not PREFER_CONTINUOUS:
            print(f"  ! {t['name']}: prefer_continuous={t.get('prefer_continuous')!r}")
            fail += 1
        if t.get("volume_threshold") != VOLUME_THRESHOLD:
            print(f"  ! {t['name']}: volume_threshold={t.get('volume_threshold')!r}")
            fail += 1
        # rate_function untouched in `properties`
        if t["transition_type"] == "adaptive":
            rf = t.get("properties", {}).get("rate_function")
            if not rf:
                print(f"  ! {t['name']}: missing properties.rate_function")
                fail += 1

    if fail:
        raise SystemExit(f"[g6] roundtrip FAILED — {fail} issues")
    print(f"[g6] roundtrip OK — {len(m2['transitions'])} transitions adaptive, "
          f"vol_thr={VOLUME_THRESHOLD}, prefer_continuous={PREFER_CONTINUOUS}")


if __name__ == "__main__":
    main()
