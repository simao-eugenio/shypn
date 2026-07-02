#!/usr/bin/env python3
"""
Cleanup: enforce property-scope discipline on canabidiol-q1-testable.shy.

Fixes (per AGENT_RULES.md §9.3 forbidden patterns):
  P1: strip `properties.thermodynamics` from ▢ parameter places (noise).
  P2: strip `properties.thermodynamics.conditions` from ○/⬡ when equal
      to top-level `thermodynamic_settings` (redundant).
  P3: regenerate `label` text for ▢ TEMPERATURE / ▢ PH from
      `initial_marking` (P28 label drift: "312.15 K (39 °C)" but value
      310.15; P29 label "7.0" but value 7.4).
  P4: promote `metadata.compartment` → top-level `compartment` for any
      place that has the former but not the latter.

Writes <file>.bak alongside the .shy and rewrites in place.
Runs the loader-scope roundtrip assertions before writing.
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path

MODEL = Path("workspace/projects/canabidiol/models/canabidiol-q1-testable.shy")


def is_param(p: dict) -> bool:
    return bool(p.get("is_parameter_place"))


def conditions_equal(local: dict, global_: dict) -> bool:
    """True iff local conditions are a subset that matches global."""
    if not local:
        return False
    keys = ("pH", "temperature", "ionic_strength")
    g = {"pH": global_.get("ph"),
         "temperature": global_.get("temperature"),
         "ionic_strength": global_.get("ionic_strength")}
    for k in keys:
        if k in local and local[k] != g[k]:
            return False
    return True


def regenerate_label(name: str, value: float, units: str | None) -> str | None:
    if name == "TEMPERATURE":
        celsius = value - 273.15
        return f"Temperature\n{value:g} K ({celsius:.2f} °C)"
    if name == "PH":
        return f"pH\n{value:g}"
    if name == "AGE":
        return f"Age\n{value:g} y"
    return None  # leave others untouched


def main() -> int:
    if not MODEL.exists():
        print(f"ERROR: {MODEL} not found", file=sys.stderr)
        return 1

    raw = MODEL.read_text()
    m = json.loads(raw)
    global_thermo = m.get("thermodynamic_settings", {}) or {}

    n_p1 = n_p2 = n_p3 = n_p4 = 0

    for p in m["places"]:
        props = p.get("properties") or {}

        # P1: strip properties.thermodynamics from ▢ parameter places
        if is_param(p) and "thermodynamics" in props:
            props.pop("thermodynamics", None)
            if not props:
                p.pop("properties", None)
            else:
                p["properties"] = props
            n_p1 += 1

        # P2: strip per-place .conditions when equal to global (○ and ⬡ only)
        if not is_param(p):
            props = p.get("properties") or {}
            th = props.get("thermodynamics")
            if isinstance(th, dict):
                cond = th.get("conditions")
                if isinstance(cond, dict) and conditions_equal(cond, global_thermo):
                    th.pop("conditions", None)
                    n_p2 += 1
                # If the thermo block becomes effectively empty (no real
                # chemistry: charge==0, n_protons==0, no conditions), drop
                # it too — it was just inherited boilerplate.
                if (not th
                        or (th.get("charge", 0) == 0
                            and th.get("n_protons", 0) == 0
                            and "conditions" not in th)):
                    props.pop("thermodynamics", None)
                    if not props:
                        p.pop("properties", None)
                    else:
                        p["properties"] = props

        # P3: regenerate label for known ▢ thermodynamic params
        if is_param(p) and p.get("parameter_kind") == "thermodynamic":
            new_label = regenerate_label(
                p["name"], p.get("initial_marking", 0.0), p.get("parameter_units"))
            if new_label and new_label != p.get("label"):
                p["label"] = new_label
                n_p3 += 1
        # also fix AGE label which is parameter_kind=physiological
        elif is_param(p) and p["name"] == "AGE":
            new_label = regenerate_label("AGE", p.get("initial_marking", 0.0), "y")
            if new_label and new_label != p.get("label"):
                p["label"] = new_label
                n_p3 += 1

        # P4: promote metadata.compartment → top-level compartment
        meta = p.get("metadata") or {}
        meta_comp = meta.get("compartment")
        if meta_comp and not p.get("compartment"):
            p["compartment"] = meta_comp
            n_p4 += 1

    # Backup + write
    backup = MODEL.with_suffix(".shy.bak")
    shutil.copy2(MODEL, backup)
    MODEL.write_text(json.dumps(m, indent=2) + "\n")

    # Roundtrip assertions
    m2 = json.loads(MODEL.read_text())
    # P1: no ▢ has properties.thermodynamics
    for p in m2["places"]:
        if is_param(p):
            assert "thermodynamics" not in (p.get("properties") or {}), \
                f"P1 violation remains on {p['id']} {p['name']}"
    # P3: spot-check TEMPERATURE label numeric matches initial_marking
    for p in m2["places"]:
        if p["name"] == "TEMPERATURE":
            assert f"{p['initial_marking']:g}" in p.get("label", ""), \
                f"P3 violation: TEMPERATURE label {p.get('label')!r} vs value {p['initial_marking']}"
        if p["name"] == "PH":
            assert f"{p['initial_marking']:g}" in p.get("label", ""), \
                f"P3 violation: PH label {p.get('label')!r} vs value {p['initial_marking']}"
    # P4: every place with metadata.compartment also has top-level compartment
    for p in m2["places"]:
        meta_comp = (p.get("metadata") or {}).get("compartment")
        if meta_comp:
            assert p.get("compartment") == meta_comp, \
                f"P4 violation on {p['id']} {p['name']}: top={p.get('compartment')!r} meta={meta_comp!r}"

    print(f"OK — backup: {backup}")
    print(f"P1 (▢ thermo block stripped): {n_p1}")
    print(f"P2 (redundant conditions stripped): {n_p2}")
    print(f"P3 (▢ labels regenerated): {n_p3}")
    print(f"P4 (compartment promoted to top-level): {n_p4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
