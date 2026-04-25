#!/usr/bin/env python3
"""Apply HPN formalism / experiment-plan cosmetic fixes to canabidiol models.

Two fixes (verified safe — neither alters simulation physics):

  C4  Flip is_environment_aware -> false on object-net transitions whose
      rate strings DO NOT actually reference any environment symbol.
      This is a stale annotation from earlier model-building sessions;
      the engine recomputes it from the rate string at startup anyway,
      but persisting a stale True confuses the formalism audit and any
      reader of the .shy file.

  C7  Flip Temperature / pH / Age from is_signal_place -> is_parameter_place
      when (a) they have no arcs and (b) they are not referenced by name
      in any rate function. These are pure experiment knobs, not signal
      places (a signal place must have at least one F_s arc per
      §5.4 of doc/pn_formalism/EXPERIMENT_PLAN_VS_OBJECT_NET.md).

  C3  After C7, scrub any references to the now-parameter places from
      every transition's `signal_places` list (a parameter place ▢ cannot
      legally appear in a transition's signal_places per §5.1).

Each modified model is backed up as <name>.shy.bak.<timestamp>.compliant
before being rewritten in place. This preserves all existing protocol
pairings.

Run audit_formalism_compliance.py after this script to verify 0 violations.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
MODELS = sorted((PROJECT / "models").glob("cbd_ad_neuroprotection_*.shy"))

ENV_SYMBOLS = ("Q10", "Temperature", "pH", "Age", "DSev",
               "Disease_Severity", "LOADING_DOSE", "MAINT_DOSE")
SCALAR_KNOB_NAMES = {"Temperature", "pH", "Age"}


def collect_rate_fields(t: dict) -> list[str]:
    out: list[str] = []
    for key in ("rate_function", "rate_expression", "rate", "kinetic_law",
                "propensity", "guard", "guard_function"):
        v = t.get(key)
        if isinstance(v, str) and v.strip():
            out.append(v)
    kin = t.get("kinetics")
    if isinstance(kin, dict):
        for key in ("rate_function", "expression", "formula"):
            v = kin.get(key)
            if isinstance(v, str) and v.strip():
                out.append(v)
    return out


def name_in_expr(name: str, expr: str) -> bool:
    return re.search(rf"\b{re.escape(name)}\b", expr) is not None


def fix_one(path: Path) -> tuple[int, int, int]:
    """Return (n_C4_fixed, n_C7_fixed, n_C3_fixed) for the model at `path`."""
    model = json.loads(path.read_text())
    transitions = model.get("transitions", [])
    places = model.get("places", [])
    arcs = model.get("arcs", [])

    # Index of place names that actually appear in any rate string.
    referenced_in_phi: set[str] = set()
    all_names = {p["name"] for p in places}
    for t in transitions:
        for expr in collect_rate_fields(t):
            for pname in all_names:
                if name_in_expr(pname, expr):
                    referenced_in_phi.add(pname)

    touched_ids = set()
    for a in arcs:
        touched_ids.add(a.get("source_id"))
        touched_ids.add(a.get("target_id"))

    n_c4 = 0
    for t in transitions:
        if not t.get("is_environment_aware"):
            continue
        # Verify the rate string is actually clean.
        joined = " ".join(collect_rate_fields(t))
        actually_uses_env = any(
            name_in_expr(sym, joined) for sym in ENV_SYMBOLS
        )
        if actually_uses_env:
            # Real coupling — leave the flag, the audit will still flag it
            # (and the modeller must decide: add F_s arc or remove the
            # symbol from the rate). We do not auto-fix this case.
            continue
        t["is_environment_aware"] = False
        n_c4 += 1

    n_c7 = 0
    for p in places:
        if p["name"] not in SCALAR_KNOB_NAMES:
            continue
        if p["id"] in touched_ids:
            continue
        if p["name"] in referenced_in_phi:
            continue
        if not p.get("is_signal_place"):
            continue
        # Convert: signal -> parameter
        p["is_signal_place"] = False
        p["is_parameter_place"] = True
        # parameter_kind / units are conventional; set sane defaults if absent.
        if not p.get("parameter_kind"):
            kind = {"Temperature": "thermodynamic",
                    "pH": "thermodynamic",
                    "Age": "demographic"}[p["name"]]
            p["parameter_kind"] = kind
        if not p.get("parameter_units"):
            units = {"Temperature": "K", "pH": "pH", "Age": "year"}[p["name"]]
            p["parameter_units"] = units
        # Remove the now-incorrect signal_type if it leaked in.
        p.pop("signal_type", None)
        n_c7 += 1

    # ----- C3: scrub parameter-place ids/names from signal_places --------
    param_ids = {p["id"] for p in places if p.get("is_parameter_place")}
    param_names = {p["name"] for p in places if p.get("is_parameter_place")}
    n_c3 = 0
    for t in transitions:
        sp = t.get("signal_places")
        if not isinstance(sp, list) or not sp:
            continue
        cleaned = [e for e in sp
                   if e not in param_ids and e not in param_names]
        removed = len(sp) - len(cleaned)
        if removed:
            t["signal_places"] = cleaned
            n_c3 += removed

    if n_c4 == 0 and n_c7 == 0 and n_c3 == 0:
        return (0, 0, 0)

    # Back up then rewrite in place.
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.{ts}.compliant")
    shutil.copy2(path, backup)
    path.write_text(json.dumps(model, indent=2))
    return (n_c4, n_c7, n_c3)


def main() -> int:
    if not MODELS:
        print(f"No models under {PROJECT/'models'}")
        return 2
    total_c4 = total_c7 = total_c3 = touched = 0
    for m in MODELS:
        c4, c7, c3 = fix_one(m)
        if c4 or c7 or c3:
            touched += 1
            print(f"  {m.name:55s}  C4={c4:2d}  C7={c7:2d}  C3={c3:2d}")
        else:
            print(f"  {m.name:55s}  (already clean)")
        total_c4 += c4
        total_c7 += c7
        total_c3 += c3
    print(f"\nTotals: {total_c4} C4 fixes, {total_c7} C7 fixes, "
          f"{total_c3} C3 fixes across {touched}/{len(MODELS)} model(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
