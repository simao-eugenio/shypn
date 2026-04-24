"""Patch cbd_ad_neuroprotection_v2.shy → v3.

Changes:
  1. Initial markings of pathology-encoding places set to *healthy young
     neuron* values.
  2. New parameter place P38 ``Disease_Severity`` (default 0).
  3. New event ``evt_install_disease`` firing at t > 0.01 that adds
     pathology proportional to ``Disease_Severity`` (1=MCI, 2=AD,
     3=severe).  At Severity=2 the post-event marking matches the
     previous AD baseline.

Per repo rules, this script does NOT overwrite v2; it writes
``cbd_ad_neuroprotection_v3.shy`` next to it.

Usage:
    python workspace/projects/canabidiol/scripts/patch_v2_to_v3_healthy_baseline.py
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = HERE.parent / "models"
SRC = MODELS / "cbd_ad_neuroprotection_v2.shy"
DST = MODELS / "cbd_ad_neuroprotection_v3.shy"

# ---------------------------------------------------------------------------
# (place_name, healthy_young_value, ad_baseline_value)
# Δ_per_severity_unit = (ad - healthy) / 2  → Severity=2 reproduces AD baseline
# ---------------------------------------------------------------------------
PATHOLOGY_TABLE: list[tuple[str, float, float]] = [
    ("Abeta_Monomer",   0.05,   0.3),
    ("Abeta_Oligomer",  0.5,   15.0),
    ("Abeta_Plaque",    0.0,    5.0),
    ("NFkB_p65",        5.0,   30.0),
    ("ROS",             1.0,    5.0),
    ("Microglia_M1",    5.0,   25.0),
    ("Microglia_M2",   40.0,   25.0),   # M2 is anti-inflammatory: drops with disease
    ("Glutathione",    70.0,   40.0),   # antioxidant pool: drops with disease
    ("Neuron_Health", 100.0,   95.0),
    ("TNFa",            0.5,    1.0),
    ("IL1b",            0.5,    1.0),
    ("IL6",             0.5,    1.0),
    ("COX2",            0.5,    1.0),
    ("APP_mRNA",        4.0,    8.0),
]


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing source model: {SRC}")
    model = json.loads(SRC.read_text())

    # ── 1. Update healthy initial markings ────────────────────────────────
    name_to_place = {p["name"]: p for p in model["places"]}
    deltas: dict[str, float] = {}
    for name, healthy, ad in PATHOLOGY_TABLE:
        if name not in name_to_place:
            print(f"  [skip] place {name!r} not found")
            continue
        p = name_to_place[name]
        old = p.get("initial_marking")
        p["initial_marking"] = healthy
        p["marking"] = healthy
        p["tokens"] = healthy
        deltas[name] = (ad - healthy) / 2.0
        print(f"  [M0] {name:<18} {old!r:>8} → {healthy!r:<8} (Δ/severity = {deltas[name]:+.3f})")

    # ── 2. Add Disease_Severity parameter place P38 ───────────────────────
    if "Disease_Severity" in name_to_place:
        print("  [P38] already present, skipping creation")
    else:
        # Use P35 (LOADING_DOSE) as a template for a parameter place
        template = copy.deepcopy(name_to_place["LOADING_DOSE"])
        template.update({
            "id": "P38",
            "name": "Disease_Severity",
            "label": "Disease severity (0=healthy, 2=AD)",
            "x": -1870.0,
            "y": 30.0,
            "marking": 0.0,
            "tokens": 0.0,
            "initial_marking": 0.0,
            "parameter_kind": "severity",
            "parameter_units": "level",
        })
        model["places"].append(template)
        print("  [P38] added Disease_Severity parameter place (default=0)")

    # ── 3. Add per-place install_disease events (one row per target) ─────
    # Split into 14 separate events so the Environment Panel events table
    # (which shows one Target Place per row) renders all 14 assignments
    # clearly. They all share trigger ``t > 0.01`` and priority 10, so
    # they fire in the same simulator step before any drug event.
    existing_event_ids = {e.get("id") for e in model.get("events", [])}
    install_events: list[dict] = []
    skipped: list[str] = []
    for name, delta in deltas.items():
        evt_id = f"evt_install_{name}"
        if evt_id in existing_event_ids:
            skipped.append(evt_id)
            continue
        install_events.append({
            "id": evt_id,
            "name": evt_id,
            "trigger": "t > 0.01",
            "delay": 0.0,
            "use_values_from_trigger_time": True,
            "priority": 10,            # fire before drug events
            "assignments": {name: f"{name} + Disease_Severity * {delta:.4f}"},
            "metadata": {
                "group": "install_disease",
                "target": name,
                "delta_per_severity_unit": delta,
                "purpose": (
                    f"Install AD pathology in {name}. "
                    "Severity=0 → no-op (healthy control); Severity=2 → "
                    "reproduces v2 AD baseline; Severity=3 → ~150% AD."
                ),
            },
        })

    if install_events:
        # Insert at the head of events[] so they appear at the top of the
        # Environment Panel events table.
        model.setdefault("events", [])[:0] = install_events
        print(f"  [evt] added {len(install_events)} per-place install events"
              f"  (group='install_disease', priority=10, trigger='t > 0.01')")
    if skipped:
        print(f"  [evt] {len(skipped)} install events already present, kept as-is")

    # ── 3b. Promote ``evt_load`` to consume LOADING_DOSE additively ──────
    # In v2 the loading event assigned ``LOADING_DOSE`` directly to
    # ``CBD_extracellular``, which means LOADING_DOSE=0 wipes any
    # pre-existing extracellular CBD instead of being a true no-op.
    # v3 changes the expression to ``CBD_extracellular + LOADING_DOSE`` so
    # the vehicle arm (LOADING_DOSE=0) leaves P1 untouched.
    for evt in model.get("events", []):
        if evt.get("id") == "evt_load":
            old_expr = evt["assignments"].get("CBD_extracellular")
            if old_expr == "LOADING_DOSE":
                evt["assignments"]["CBD_extracellular"] = (
                    "CBD_extracellular + LOADING_DOSE"
                )
                print(f"  [evt] evt_load expression: {old_expr!r} → "
                      f"{evt['assignments']['CBD_extracellular']!r}")

    # ── 4. Bump object_counts and write ───────────────────────────────────
    md = model.setdefault("metadata", {}).setdefault("object_counts", {})
    md["places"] = len(model["places"])

    DST.write_text(json.dumps(model, indent=2))
    print(f"\nwrote → {DST}  ({DST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
