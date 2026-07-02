#!/usr/bin/env python3
"""Fix the broken CBD pharmacokinetics chain in ``canabidiol-q1-testable.shy``.

Problem (audited from `data/simulation_data.csv`, 4 h, M0):
    plasma peak  : 10.0 mM   (loading dose at t=2 s)
    extracell    :  6e-5 mM  (60 nM — five orders of magnitude below plasma)
    BBB_Transfer :    1 firing in 4 h
    Brain_Metab. :    0 firings (intracellular CBD never accumulates)
    Efflux       :    0 firings

Root cause (model-side):
    1. ``CBD_BBB_Transfer.rate = 6e-6 * CBD_plasma * Temperature_factor``
       k=6e-6/s yields an influx of 6e-5 mM/s at plasma=10 → an asymptote of
       ~0.1 mM only if no consumption. Realistic BBB permeability for the
       lipophilic CBD molecule gives a brain:plasma ratio of ~0.3–0.6 at
       steady state with τ ~ 30–60 min. That requires k_in roughly two
       orders of magnitude larger.
    2. ``CBD_Absorption.rate = 5.0 * CBD_extracellular * Temperature_factor``
       k=5/s vacuums extracellular into intracellular faster than influx
       can replenish, clamping extracellular near zero regardless of
       plasma. Drop to k≈0.05/s so absorption becomes uptake-limited
       rather than diffusion-limited.

Fix (Pattern A — only properties.rate_function, scope per shy_loader_scopes):
    CBD_BBB_Transfer    : 6e-6  → 5e-4   (≈ 80×, brings τ_BBB ~ 2000 s)
    CBD_Absorption      : 5.0   → 0.05   (slows the drain so extracell
                                          actually accumulates)

This produces a ``canabidiol-q1-testable-pk.shy`` next to the original;
the original is untouched. Re-load the new model in the GUI before
running.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "models" / "canabidiol-q1-testable.shy"
DST = ROOT / "models" / "canabidiol-q1-testable-pk.shy"

PATCHES: dict[str, str] = {
    "CBD_BBB_Transfer": "0.0005 * CBD_plasma * Temperature_factor",
    "CBD_Absorption":   "0.05 * CBD_extracellular * Temperature_factor",
}


def main() -> int:
    if not SRC.exists():
        print(f"[fix_cbd_pk] source missing: {SRC}", file=sys.stderr)
        return 1

    model = json.loads(SRC.read_text())
    by_name = {t["name"]: t for t in model["transitions"]}

    for name, new_rate in PATCHES.items():
        t = by_name.get(name)
        if t is None:
            print(f"[fix_cbd_pk] WARN: transition '{name}' not found, skipped",
                  file=sys.stderr)
            continue
        props = t.setdefault("properties", {})
        old = props.get("rate_function") or t.get("rate_function") or "<unset>"
        props["rate_function"] = new_rate
        # Drop the legacy top-level rate_function so the loader's
        # properties-wins rule has no stale shadow value.
        t.pop("rate_function", None)
        print(f"[fix_cbd_pk] {name}:")
        print(f"    OLD: {old}")
        print(f"    NEW: {new_rate}")

    DST.write_text(json.dumps(model, indent=2))

    # Roundtrip assertion (loader's read scope is properties.rate_function)
    rebuilt = json.loads(DST.read_text())
    by_name2 = {t["name"]: t for t in rebuilt["transitions"]}
    for name, new_rate in PATCHES.items():
        if name not in by_name2:
            continue
        got = by_name2[name].get("properties", {}).get("rate_function")
        assert got == new_rate, f"roundtrip failed for {name}: {got!r}"
    print(f"\n[fix_cbd_pk] wrote {DST}")
    print("[fix_cbd_pk] roundtrip OK — load this file in the GUI before re-running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
