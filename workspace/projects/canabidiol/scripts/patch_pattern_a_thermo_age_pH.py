"""Pattern A bridge — refactor cbd_ad_neuroprotection_v3_p6.shy so that rate
functions stop reading the parameter places (▢) Temperature, pH, Age directly.

Per AGENT_RULES.md §1 / §3 (Pattern A) and EXPERIMENT_PLAN_VS_OBJECT_NET.md,
parameter places are experiment-plan metadata and must NEVER appear in any
object-net Φ. The legal bridge is::

    ▢ (parameter)  ──event── ◇ (spatial signal)  ──Φ──>  rate function

This script:

  (1) Strips the stale ``is_compartment_place=True`` flag from Temperature,
      pH, Age (they are exogenous constants, not biological compartments).
  (2) Adds four spatial signal places ◇ (is_signal_place=True,
      signal_type=SPATIAL, no F_s arcs):
          - Temperature_factor    Q10-style multiplier
          - Age_factor            (1 + 0.02*(Age - 65))
          - pH_acidosis           max(0, 7.0 - pH)
          - pH_neutrality         (1 - 0.3*abs(pH - 7.4))
  (3) Adds a pre-protocol event ``evt_apply_thermodynamics`` (t=0,
      ordering=-1000) that reads ▢ Temperature/pH/Age and writes the four ◇
      scalars.
  (4) Rewrites every rate function (27 transitions) to reference the ◇ scalars
      instead of inlining ▢ algebra.

Writes the patched model to ``cbd_ad_neuroprotection_v3_p7.shy`` (versioned;
never overwrites the canonical file in place — see copilot-instructions §4).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"
SRC = MODELS_DIR / "cbd_ad_neuroprotection_v3_p6.shy"
DST = MODELS_DIR / "cbd_ad_neuroprotection_v3_p7.shy"

# ---------------------------------------------------------------------------
# Substitutions applied to every rate-function string.
# Order matters: longer patterns first so we never partially match.
# ---------------------------------------------------------------------------
RATE_SUBS: list[tuple[str, str]] = [
    # Temperature — both single- and double-paren variants, in that order.
    ("2**((((Temperature - 273.15) - 37))/10)", "Temperature_factor"),
    ("2**(((Temperature - 273.15) - 37)/10)",   "Temperature_factor"),
    # Age
    ("(1 + 0.02*(Age - 65))", "Age_factor"),
    # pH — neutrality (abs) form first
    ("(1 - 0.3*abs(pH - 7.4))",  "pH_neutrality"),
    # pH — linear acidosis forms; same scaffold differs only by coefficient
    ("(1 + 0.5*(7.0 - pH))", "(1 + 0.5*pH_acidosis)"),
    ("(1 + 0.4*(7.0 - pH))", "(1 + 0.4*pH_acidosis)"),
    ("(1 + 0.3*(7.0 - pH))", "(1 + 0.3*pH_acidosis)"),
]

# ---------------------------------------------------------------------------
# New ◇ spatial-signal places. Coordinates picked to sit near Temperature/pH
# in the existing layout; tweak in the GUI later if needed.
# ---------------------------------------------------------------------------
NEW_SIGNAL_PLACES = [
    {
        "name": "Temperature_factor",
        "label": "Q10 thermo",
        "marking": 1.0,           # 2**((310.15-273.15-37)/10) = 1.0 at 37 °C
        "x": 1750.0,
        "y": 100.0,
    },
    {
        "name": "Age_factor",
        "label": "age multiplier",
        "marking": 1.2,           # 1 + 0.02*(75-65) = 1.20 at default Age=75
        "x": 1750.0,
        "y": 170.0,
    },
    {
        "name": "pH_acidosis",
        "label": "max(0, 7-pH)",
        "marking": 0.0,           # max(0, 7.0 - 7.4) = 0 at default pH=7.4
        "x": 1750.0,
        "y": 240.0,
    },
    {
        "name": "pH_neutrality",
        "label": "1 - 0.3·|pH-7.4|",
        "marking": 1.0,           # 1 - 0.3*0 = 1 at default pH=7.4
        "x": 1750.0,
        "y": 310.0,
    },
]

# Event that bridges ▢ → ◇.  RHS uses only target + parameter places, so it
# satisfies Pattern A discipline (audit code C12).
THERMO_EVENT = {
    "id": "evt_apply_thermodynamics",
    "name": "evt_apply_thermodynamics",
    "label": "▢→◇ thermo bridge",
    "trigger_type": "time",
    "trigger": "0.0",
    "ordering": -1000,            # run before any biology event
    "enabled": True,
    "assignments": {
        "Temperature_factor": "2**(((Temperature - 273.15) - 37)/10)",
        "Age_factor":         "1 + 0.02*(Age - 65)",
        "pH_acidosis":        "max(0, 7.0 - pH)",
        "pH_neutrality":      "1 - 0.3*abs(pH - 7.4)",
    },
    "description": (
        "Pattern A bridge: at t=0 read parameter places ▢ "
        "(Temperature, pH, Age) and write the spatial-signal scalars ◇ "
        "consumed by Φ.  Object-net rate functions never reference ▢ "
        "directly (AGENT_RULES.md §3)."
    ),
}


def find_place_by_name(places: list[dict], name: str) -> dict | None:
    for p in places:
        if p.get("name") == name:
            return p
    return None


def next_place_id(places: list[dict]) -> int:
    """Return the next free integer-style place id following the model's
    existing 'P<int>' convention (case-insensitive scan)."""
    used: set[int] = set()
    for p in places:
        pid = p.get("id", "")
        m = re.match(r"^[pP](\d+)$", str(pid))
        if m:
            used.add(int(m.group(1)))
        else:
            try:
                used.add(int(pid))
            except (TypeError, ValueError):
                pass
    n = 1
    while n in used:
        n += 1
    return n


def make_signal_place_dict(template: dict, sig_id: str) -> dict:
    """Produce a place dict mirroring the schema used by existing places."""
    return {
        "id": sig_id,
        "name": template["name"],
        "label": template["label"],
        "object_type": "place",
        "x": template["x"],
        "y": template["y"],
        "radius": 25,
        "marking": template["marking"],
        "initial_marking": template["marking"],
        "tokens": template["marking"],
        "capacity": "Infinity",
        "is_catalyst": False,
        "is_signal_place": True,
        "signal_type": "SPATIAL",
        "is_compartment_place": False,
        "is_regulatory_place": False,
        "is_energy_place": False,
        "is_parameter_place": False,
        "compartment": "environment",
    }


def patch_rate_function(rf: str) -> str:
    out = rf
    for old, new in RATE_SUBS:
        out = out.replace(old, new)
    return out


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: source model not found: {SRC}", file=sys.stderr)
        return 1

    with SRC.open() as fh:
        model = json.load(fh)

    # --- (B) strip stale is_compartment_place from Temperature/pH/Age -------
    for nm in ("Temperature", "pH", "Age"):
        p = find_place_by_name(model["places"], nm)
        if p is not None and p.get("is_compartment_place"):
            p["is_compartment_place"] = False
            print(f"  cleared is_compartment_place on ▢ {nm}")

    # --- (C1) add ◇ spatial-signal places ---------------------------------
    existing_names = {p.get("name") for p in model["places"]}
    next_n = next_place_id(model["places"])
    existing_ids = {p.get("id") for p in model["places"]}
    for tpl in NEW_SIGNAL_PLACES:
        if tpl["name"] in existing_names:
            print(f"  ◇ {tpl['name']} already present — skipping")
            continue
        sig_id = f"P{next_n}"
        while sig_id in existing_ids:
            next_n += 1
            sig_id = f"P{next_n}"
        existing_ids.add(sig_id)
        next_n += 1
        model["places"].append(make_signal_place_dict(tpl, sig_id))
        print(f"  added ◇ {tpl['name']} (id={sig_id}, marking={tpl['marking']})")

    # --- (C2) add the bridge event ----------------------------------------
    events = model.setdefault("events", [])
    if not any(e.get("id") == THERMO_EVENT["id"] for e in events):
        events.append(THERMO_EVENT)
        print(f"  added event {THERMO_EVENT['id']} (t=0)")
    else:
        # update assignments / trigger in case the user re-runs the patch
        for e in events:
            if e.get("id") == THERMO_EVENT["id"]:
                e["assignments"] = THERMO_EVENT["assignments"]
                e["trigger"] = THERMO_EVENT["trigger"]
                print(f"  updated existing event {THERMO_EVENT['id']}")
                break

    # --- (C3) rewrite rate functions --------------------------------------
    rewritten = 0
    for t in model.get("transitions", []):
        props = t.get("properties")
        if not isinstance(props, dict):
            continue
        for key in ("rate_function", "rate_function_display"):
            rf = props.get(key)
            if isinstance(rf, str) and rf:
                new_rf = patch_rate_function(rf)
                if new_rf != rf:
                    props[key] = new_rf
                    if key == "rate_function":
                        rewritten += 1
    print(f"  rewrote rate_function on {rewritten} transitions")

    # --- write output ------------------------------------------------------
    if DST.exists():
        backup = DST.with_suffix(".shy.bak")
        shutil.copy2(DST, backup)
        print(f"  backed up existing {DST.name} → {backup.name}")
    with DST.open("w") as fh:
        json.dump(model, fh, indent=2)
    print(f"\nWrote {DST}")

    # --- post-check: no ▢ name should appear in any rate function anymore --
    bad: list[tuple[str, str]] = []
    needles = ("Temperature", "pH", "Age")
    for t in model.get("transitions", []):
        props = t.get("properties") or {}
        rf = props.get("rate_function", "") if isinstance(props, dict) else ""
        if not isinstance(rf, str):
            continue
        for needle in needles:
            # whole-word match; exclude *_factor / pH_acidosis / pH_neutrality
            for m in re.finditer(rf"\b{needle}\b", rf):
                ctx = rf[max(0, m.start() - 5): m.end() + 12]
                # allow Temperature_factor, Age_factor, pH_acidosis, pH_neutrality
                if (needle == "Temperature" and "Temperature_factor" in ctx):
                    continue
                if needle == "Age" and "Age_factor" in ctx:
                    continue
                if needle == "pH" and (
                    "pH_acidosis" in ctx or "pH_neutrality" in ctx
                ):
                    continue
                bad.append((t.get("id", "?"), rf))
                break
    if bad:
        print("\nWARNING: residual ▢ references in Φ:", file=sys.stderr)
        for tid, rf in bad:
            print(f"  {tid}: {rf}", file=sys.stderr)
        return 2
    print("\n✓ no parameter-place names left in any rate function")
    return 0


if __name__ == "__main__":
    sys.exit(main())
