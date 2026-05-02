"""G5a — Soften ROS-baseline damage in T20 Neurotoxicity (surgical edit).

Lifts the healthy-state NH ceiling (was ~60 at D=0,M=5 in Q4-redux) by
raising the ROS damage threshold 1.0 -> 20.0 and quartering the
coefficient 0.004 -> 0.001. AbO and TNFa damage terms, plus
pH/Age/Temperature factors, preserved verbatim.

Loader scope: properties.rate_function.
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path

MODEL = Path("workspace/projects/canabidiol/models/canabidiol-q1-testable.shy")
TARGET = "Neurotoxicity"

SUB_OLD = "0.004 * (max(0, ROS - 1.0) / (15 + max(0, ROS - 1.0)))"
SUB_NEW = "0.001 * (max(0, ROS - 20.0) / (15 + max(0, ROS - 20.0)))"


def main() -> None:
    backup = MODEL.with_suffix(MODEL.suffix + ".bak.preG5a")
    if not backup.exists():
        shutil.copy2(MODEL, backup)
        print(f"[backup] {backup}")

    m = json.loads(MODEL.read_text())
    t = next(t for t in m["transitions"] if t["name"] == TARGET)
    cur = t["properties"].get("rate_function", "")

    if SUB_NEW in cur:
        print("[noop] G5a already applied")
        return
    if SUB_OLD not in cur:
        raise SystemExit(
            f"fingerprint missing on {TARGET}; cannot patch.\n  current: {cur}"
        )

    new = cur.replace(SUB_OLD, SUB_NEW)
    t["properties"]["rate_function"] = new
    MODEL.write_text(json.dumps(m, indent=2))

    # Roundtrip
    m2 = json.loads(MODEL.read_text())
    t2 = next(t for t in m2["transitions"] if t["name"] == TARGET)
    rf = t2["properties"]["rate_function"]
    assert rf == new and SUB_NEW in rf
    for token in ("Abeta_Oligomer", "TNFa", "Temperature_factor",
                  "pH_acidosis", "Age_factor"):
        assert token in rf, f"G5a regression: lost {token}"
    print(f"[ok] G5a applied to {TARGET}")
    print(f"     {rf}")


if __name__ == "__main__":
    main()
