#!/usr/bin/env python3
"""
Build bacillus_sporulation_v4_thesis.shy from v3.

Two goals:

  1. Topology fixes from deep_analysis_v3 (analyses E + F):
     - Mass conservation on the adenylate pool: ATP regen transitions now
       CONSUME ADP (signal_flow input arc) instead of using a non-consuming
       `test` arc — eliminates the +37k token drift seen in v3.
     - Sigma-factor degradation: add 5 continuous decay transitions
       (SigmaH/F/E/G/K) so accumulation no longer grows monotonically.

  2. Expose the four-carrier formalism (○ ⬡ ◇ ▢):
     - Add 4 parameter places ▢ (INITIAL_NUTRIENTS, TEMPERATURE_K,
       ATP_SETPOINT, SIGMA_HALFLIFE_MIN) — read by events only, never by Φ.
     - Add 3 spatial signal places ◇ (k_ATP_target, k_sigma_decay,
       k_thermo_factor) — is_signal_place=true, signal_type='spatial',
       no F_s arcs, referenced by Φ.
     - Add 2 events implementing the canonical ▢ + event → ◇ → Φ bridge:
         evt_init_kinetics      — populates the 3 ◇ places at t > 0
         evt_apply_initial_nuts — copies INITIAL_NUTRIENTS ▢ into Nutrients ○
     - Rewrite the rate functions of T20 (Source_ATP_regen),
       T23 (Source_ATP_stationary), and the new sigma-decay transitions
       to read from ◇ places instead of hardcoded constants.

The result: sweeping INITIAL_NUTRIENTS (▢) drives Nutrients (○) at t=0
through the event bridge — exactly the experiment-plan-vs-object-net
discipline from AGENT_RULES.md, fully demonstrated in one model.
"""
from __future__ import annotations

import json
import math
from copy import deepcopy
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/simao/projetos/shypn")
SRC  = ROOT / "workspace/projects/thesis/models/bacillus_sporulation_v3_thesis.shy"
DST  = ROOT / "workspace/projects/thesis/models/bacillus_sporulation_v4_thesis.shy"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def next_id(items, prefix):
    used = {it["id"] for it in items}
    n = 1
    while f"{prefix}{n}" in used:
        n += 1
    return f"{prefix}{n}"


def make_place(pid, name, x, y, *, M0=0.0, is_signal=False, signal_type=None,
               is_param=False, param_kind=None, param_units=None,
               border_color=None, radius=30.0):
    """Construct a place dict matching the v3 schema."""
    place = {
        "id": pid,
        "name": name,
        "label": f"{name}\n{M0}",
        "metadata": {},
        "object_type": "place",
        "x": float(x),
        "y": float(y),
        "radius": radius,
        "marking": float(M0),
        "initial_marking": float(M0),
        "capacity": "Infinity",
        "border_color": border_color or [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "is_catalyst": False,
        "is_signal_place": bool(is_signal),
        "signal_type": signal_type,                 # lowercase string e.g. "spatial"
        "is_compartment_place": False,
        "is_regulatory_place": False,
        "is_energy_place": False,
        "is_parameter_place": bool(is_param),
        "parameter_kind": param_kind,
        "parameter_units": param_units,
        "diffusion_coefficient": None,
        "boundary_type": None,
        "gradient_vector": None,
        "compartment_volume": None,
        "neighbor_compartments": [],
        "spatial_position": None,
    }
    return place


def make_arc(aid, arc_type, src_id, tgt_id, *, weight=1.0, color=None):
    colors = {
        "normal":                       [0.0, 0.0, 0.0],
        "test":                         [0.0, 0.0, 1.0],
        "signal_flow":                  [0.7, 0.7, 0.7],
        "curved_opposite_signal_flow":  [0.7, 0.7, 0.7],
        "inhibitor":                    [1.0, 0.0, 0.0],
        "curved_inhibitor_arc":         [1.0, 0.0, 0.0],
    }
    return {
        "id": aid,
        "name": aid,
        "arc_type": arc_type,
        "source_id": src_id,
        "target_id": tgt_id,
        "source_type": "place" if src_id.startswith("P") else "transition",
        "target_type": "place" if tgt_id.startswith("P") else "transition",
        "weight": float(weight),
        "threshold": 0.0,
        "color": color or colors.get(arc_type, [0.0, 0.0, 0.0]),
        "width": 2.0,
        "control_points": [],
    }


def make_continuous_transition(tid, name, x, y, rate_function):
    return {
        "id": tid,
        "name": name,
        "label": f"{name}",
        "metadata": {},
        "object_type": "transition",
        "x": float(x),
        "y": float(y),
        "width": 60.0,
        "height": 30.0,
        "horizontal": False,
        "enabled": True,
        "fill_color": [1.0, 1.0, 1.0],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 2.0,
        "transition_type": "continuous",
        "priority": 1,
        "firing_policy": "default",
        "guard": "",
        "is_source": False,
        "is_sink": False,
        "earliest_time": 0.0,
        "latest_time": 0.0,
        "signal_places": [],
        "is_environment_aware": False,
        "module_id": None,
        "compartment": None,
        "kinetic_metadata": {},
        "adaptive_filter": None,
        "volume_threshold": None,
        "prefer_continuous": False,
        "properties": {"rate_function": rate_function},
    }


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    m = json.loads(SRC.read_text())

    # Bookkeeping shortcuts
    place_by_name = {p["name"]: p for p in m["places"]}
    trans_by_name = {t["name"]: t for t in m["transitions"]}

    # ------------------------------------------------------------------
    # 1. PARAMETER PLACES ▢  (right margin, far from biology)
    # ------------------------------------------------------------------
    PARAMS_X = 1850.0
    params = [
        ("INITIAL_NUTRIENTS",  100.0,  "nutrient",     "tokens"),
        ("TEMPERATURE_K",      310.15, "environment",  "K"),
        ("ATP_SETPOINT",       4800.0, "homeostasis",  "tokens"),
        ("SIGMA_HALFLIFE_MIN", 120.0,  "kinetics",     "min"),
    ]
    new_params = []
    for i, (name, M0, kind, units) in enumerate(params):
        pid = next_id(m["places"] + new_params, "P")
        new_params.append(make_place(
            pid, name, PARAMS_X, 400.0 + i * 200.0,
            M0=M0,
            is_signal=False,        # ▢ is NOT a signal place
            signal_type=None,
            is_param=True,
            param_kind=kind,
            param_units=units,
            border_color=[0.4, 0.4, 0.4],
        ))
    m["places"].extend(new_params)
    pname = lambda n: next(p["id"] for p in m["places"] if p["name"] == n)

    # ------------------------------------------------------------------
    # 2. SPATIAL SIGNAL PLACES ◇  (no F_s arcs; referenced by Φ only)
    # ------------------------------------------------------------------
    # k_sigma_decay = ln(2) / SIGMA_HALFLIFE_MIN  ≈ 0.005776
    # k_thermo_factor = Q10**((T - 310.15)/10),  Q10=2  (=> 1.0 at default T)
    # k_ATP_target = ATP_SETPOINT  (separates kinetic scalar from ▢)
    spatials = [
        ("k_ATP_target",      4800.0,                              ),
        ("k_sigma_decay",     math.log(2.0) / 120.0                ),
        ("k_thermo_factor",   1.0                                  ),
    ]
    new_spatials = []
    for i, (name, M0) in enumerate(spatials):
        pid = next_id(m["places"] + new_spatials, "P")
        new_spatials.append(make_place(
            pid, name, PARAMS_X - 350.0, 500.0 + i * 220.0,
            M0=M0,
            is_signal=True,
            signal_type="spatial",          # ◇ — no F_s arcs allowed
            is_param=False,
            border_color=[0.5, 0.0, 0.5],
        ))
    m["places"].extend(new_spatials)

    # ------------------------------------------------------------------
    # 3. TOPOLOGY FIX A — ATP regen now consumes ADP (mass conservation)
    # ------------------------------------------------------------------
    # v3 had:  ADP_pool --test--> Source_ATP_regen   (non-consuming, leak)
    # v4:      ADP_pool --signal_flow--> Source_ATP_regen   (consumed 1:1)
    # Stoichiometry: each firing produces W=40 ATP, must consume W=40 ADP.
    for arc in m["arcs"]:
        # A82 ADP_pool -> Source_ATP_regen (was test W=0.5)
        if arc["source_id"] == pname("ADP_pool") and arc["target_id"] == trans_by_name["Source_ATP_regen"]["id"]:
            arc["arc_type"] = "signal_flow"
            arc["weight"]   = 40.0
            arc["color"]    = [0.7, 0.7, 0.7]
        # A85 ADP_pool -> Source_ATP_stationary (was test W=0.5)
        if arc["source_id"] == pname("ADP_pool") and arc["target_id"] == trans_by_name["Source_ATP_stationary"]["id"]:
            arc["arc_type"] = "signal_flow"
            arc["weight"]   = 40.0
            arc["color"]    = [0.7, 0.7, 0.7]

    # ------------------------------------------------------------------
    # 4. RATE-FUNCTION REWRITES — pull constants from ◇ places
    # ------------------------------------------------------------------
    # T20 Source_ATP_regen: Q10 multiplier + setpoint from ◇
    trans_by_name["Source_ATP_regen"]["properties"]["rate_function"] = (
        "4.4 * k_thermo_factor * Nutrients / (10 + Nutrients) * "
        "max(0, 1 - ATP_pool / (k_ATP_target + 0.5 * ADP_pool))"
    )
    # T23 Source_ATP_stationary: setpoint from ◇
    trans_by_name["Source_ATP_stationary"]["properties"]["rate_function"] = (
        "0.5 * max(0, 1 - Nutrients / 5) * "
        "max(0, 1 - ATP_pool / (k_ATP_target + 0.5 * ADP_pool))"
    )

    # ------------------------------------------------------------------
    # 5. TOPOLOGY FIX B — sigma factor degradation
    # ------------------------------------------------------------------
    # 5 continuous transitions, one per sigma. Rate = k_sigma_decay * SigmaX.
    # Input arc: signal_flow SigmaX -> T_decay (W=1) — proper consumption.
    # k_sigma_decay is read remotely from ◇ in the rate string.
    sigma_targets = [
        ("SigmaH", 1300, 1330),
        ("SigmaF", 1470, 830 ),
        ("SigmaE", 1450, 450 ),
        ("SigmaG", 750,  1580),
        ("SigmaK", 1140, 1410),
    ]
    new_decays = []
    for sigma_name, base_x, base_y in sigma_targets:
        tid = next_id(m["transitions"] + new_decays, "T")
        new_decays.append(make_continuous_transition(
            tid,
            f"T_{sigma_name}_decay",
            base_x + 120.0, base_y + 100.0,
            rate_function=f"k_sigma_decay * {sigma_name}",
        ))
    m["transitions"].extend(new_decays)

    # Add the consumption arcs for each decay transition.
    new_arcs = []
    for sigma_name, _, _ in sigma_targets:
        sigma_pid = pname(sigma_name)
        decay_tid = next(t["id"] for t in m["transitions"] if t["name"] == f"T_{sigma_name}_decay")
        aid = next_id(m["arcs"] + new_arcs, "A")
        new_arcs.append(make_arc(aid, "signal_flow", sigma_pid, decay_tid, weight=1.0))
    m["arcs"].extend(new_arcs)

    # ------------------------------------------------------------------
    # 6. EVENTS — the only legal bridge ▢ → ◇ → Φ
    # ------------------------------------------------------------------
    m["events"] = [
        {
            "id": "evt_init_kinetics",
            "name": "Initialise kinetic scalars from parameter places",
            "trigger": "t > 0",
            "delay": 0.0,
            "use_values_from_trigger_time": True,
            "priority": 10,
            "assignments": {
                # ◇ := f(▢...) — RHS reads parameter places only
                "k_ATP_target":    "ATP_SETPOINT",
                "k_sigma_decay":   "0.6931471805599453 / SIGMA_HALFLIFE_MIN",
                "k_thermo_factor": "2.0 ** ((TEMPERATURE_K - 310.15) / 10.0)",
            },
            "metadata": {
                "purpose": "Pattern A bridge: parameter places → spatial signals",
            },
        },
        {
            "id": "evt_apply_initial_nutrients",
            "name": "Project INITIAL_NUTRIENTS ▢ onto Nutrients ○",
            "trigger": "t > 0",
            "delay": 0.0,
            "use_values_from_trigger_time": True,
            "priority": 5,
            "assignments": {
                "Nutrients": "INITIAL_NUTRIENTS",
            },
            "metadata": {
                "purpose": "Sweep entrypoint: vary INITIAL_NUTRIENTS ▢, "
                           "Nutrients ○ inherits at t=0",
            },
        },
    ]

    # ------------------------------------------------------------------
    # Metadata refresh
    # ------------------------------------------------------------------
    m["metadata"] = {
        "created":    datetime.now().isoformat(timespec="seconds"),
        "source":     "build_v4_thesis.py (from v3_thesis)",
        "model_type": "Petri Net",
        "version_notes": (
            "v4: mass-conserving ATP regen, sigma degradation, "
            "▢ parameter places + ◇ spatial signal places + event bridge"
        ),
        "object_counts": {
            "places":      len(m["places"]),
            "transitions": len(m["transitions"]),
            "arcs":        len(m["arcs"]),
            "modules":     len(m.get("modules", [])),
            "events":      len(m["events"]),
        },
    }

    DST.write_text(json.dumps(m, indent=2))

    # ------------------------------------------------------------------
    # Roundtrip validation (mandatory per copilot-instructions)
    # ------------------------------------------------------------------
    m2 = json.loads(DST.read_text())

    # 1. Parameter places present, properly tagged
    for name, _, kind, units in params:
        p = next(p for p in m2["places"] if p["name"] == name)
        assert p["is_parameter_place"] is True, f"{name} not param-flagged"
        assert p["is_signal_place"]    is False, f"{name} wrongly is_signal"
        assert p["parameter_kind"]     == kind
        assert p["parameter_units"]    == units
        assert p["signal_type"]        is None

    # 2. Spatial signal places present, no F_s arcs touching them
    spatial_ids = set()
    for name, _ in spatials:
        p = next(p for p in m2["places"] if p["name"] == name)
        assert p["is_signal_place"]    is True,    f"{name} not signal"
        assert p["signal_type"]        == "spatial", f"{name} wrong signal_type"
        assert p["is_parameter_place"] is False
        spatial_ids.add(p["id"])
    for a in m2["arcs"]:
        if a["arc_type"] in ("signal_flow", "curved_opposite_signal_flow"):
            assert a["source_id"] not in spatial_ids and a["target_id"] not in spatial_ids, \
                f"◇ {a['id']} has illegal F_s arc"

    # 3. ADP arcs to ATP regen are now signal_flow
    adp_id = next(p["id"] for p in m2["places"] if p["name"] == "ADP_pool")
    for tname in ("Source_ATP_regen", "Source_ATP_stationary"):
        tid = next(t["id"] for t in m2["transitions"] if t["name"] == tname)
        adp_arcs = [a for a in m2["arcs"]
                    if a["source_id"] == adp_id and a["target_id"] == tid]
        assert len(adp_arcs) == 1, f"{tname}: expected 1 ADP arc, got {len(adp_arcs)}"
        assert adp_arcs[0]["arc_type"] == "signal_flow", \
            f"{tname}: ADP arc not signal_flow ({adp_arcs[0]['arc_type']})"
        assert adp_arcs[0]["weight"] == 40.0

    # 4. Sigma decays present and consume tokens
    for sigma_name, _, _ in sigma_targets:
        tname = f"T_{sigma_name}_decay"
        t = next(t for t in m2["transitions"] if t["name"] == tname)
        assert t["transition_type"] == "continuous"
        assert "rate_function" in t["properties"]
        assert "k_sigma_decay" in t["properties"]["rate_function"]
        assert sigma_name in t["properties"]["rate_function"]
        # consumption arc exists
        sigma_pid = next(p["id"] for p in m2["places"] if p["name"] == sigma_name)
        consumes = [a for a in m2["arcs"]
                    if a["source_id"] == sigma_pid and a["target_id"] == t["id"]]
        assert consumes and consumes[0]["arc_type"] == "signal_flow", \
            f"{tname}: missing signal_flow consumption arc from {sigma_name}"

    # 5. Rate functions reference ◇ scalars, not hardcoded constants
    rf_regen = next(t for t in m2["transitions"] if t["name"] == "Source_ATP_regen") \
        ["properties"]["rate_function"]
    assert "k_ATP_target"    in rf_regen
    assert "k_thermo_factor" in rf_regen
    assert "4800"            not in rf_regen, "stale literal 4800 in rate"

    # 6. Events present and well-formed (Pattern A: RHS reads ▢ only)
    assert len(m2["events"]) == 2
    init = m2["events"][0]
    assert init["id"] == "evt_init_kinetics"
    assert set(init["assignments"]) == {"k_ATP_target", "k_sigma_decay", "k_thermo_factor"}
    assert "ATP_SETPOINT" in init["assignments"]["k_ATP_target"]
    nuts = m2["events"][1]
    assert nuts["assignments"] == {"Nutrients": "INITIAL_NUTRIENTS"}

    print(f"✓ v4 written to {DST.name}")
    print(f"  places:      {len(m2['places'])}  (was {len(m['places'])-len(new_params)-len(new_spatials)})")
    print(f"  transitions: {len(m2['transitions'])}  (added {len(new_decays)} σ-decay)")
    print(f"  arcs:        {len(m2['arcs'])}  (added {len(new_arcs)} σ-consumption + 2 retyped)")
    print(f"  events:      {len(m2['events'])}  (was 0)")
    print()
    print("Carrier breakdown:")
    n_param = sum(1 for p in m2["places"] if p["is_parameter_place"])
    n_spatial = sum(1 for p in m2["places"] if p["signal_type"] == "spatial")
    n_signal = sum(1 for p in m2["places"]
                   if p["is_signal_place"] and not p["is_parameter_place"]
                   and p["signal_type"] != "spatial")
    n_regular = sum(1 for p in m2["places"]
                    if not p["is_signal_place"] and not p["is_parameter_place"])
    print(f"  ○ regular places:   {n_regular}")
    print(f"  ⬡ signal places:    {n_signal}")
    print(f"  ◇ spatial signals:  {n_spatial}")
    print(f"  ▢ parameter places: {n_param}")
    print()
    print("All roundtrip assertions passed.")


if __name__ == "__main__":
    build()
