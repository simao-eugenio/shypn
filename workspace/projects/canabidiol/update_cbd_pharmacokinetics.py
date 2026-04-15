#!/usr/bin/env python3
"""Add 2-compartment pharmacokinetic model for CBD with membrane permeation.

Biological rationale:
  CBD is administered externally (bolus injection). It must cross the cell
  membrane to reach intracellular targets (PPARγ, Nrf2/Keap1). Membrane
  receptors (GPR3, 5-HT1A, A2A) are activated from the extracellular side.

  CBD is highly lipophilic (logP ≈ 6.3, MW = 314.5 Da), crossing membranes
  via passive diffusion (Fick's law). It is metabolized by CYP3A4/CYP2C19.

Model changes:
  1. Rename CBD → CBD_extracellular (P1, bolus injection site)
  2. Add CBD_intracellular (P30, intracellular/brain compartment)
  3. Add 4 PK transitions:
     - T28: CBD_Absorption       (membrane permeation, extracellular → intracellular)
     - T29: CBD_Efflux            (back-transport, intracellular → extracellular)
     - T30: CBD_Systemic_Clearance (hepatic/renal elimination, SINK)
     - T31: CBD_Brain_Metabolism   (CYP450 local metabolism, SINK)
  4. Redirect intracellular target arcs/rates to CBD_intracellular
  5. Add 6 new arcs for PK transitions

  PK kinetics (2-compartment, first-order):
    dCe/dt = -k_abs*Ce + k_efflux*Ci - k_sys*Ce
    dCi/dt = +k_abs*Ce - k_efflux*Ci - k_met*Ci

  Eigenvalue analysis:
    Fast phase: t½ ≈ 10 min (distribution equilibrium)
    Slow phase: t½ ≈ 4.3 hours (elimination)
    At 6 hours: ~38% of CBD activity remains

  Target compartment mapping:
    Extracellular targets (membrane receptors):
      - GPR3 (inverse agonism)     → CBD_extracellular
      - 5-HT1A (allosteric)        → CBD_extracellular
      - A2A (agonism)              → CBD_extracellular
    Intracellular targets (nuclear/cytoplasmic):
      - PPARγ (nuclear receptor)   → CBD_intracellular
      - Nrf2/Keap1 (redox sensor)  → CBD_intracellular
"""

import json
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "models" / "cbd_ad_neuroprotection_v1.shy"


def make_arc(arc_id, name, source_id, source_type, target_id, target_type,
             arc_type="normal", weight=1.0, consumes=True):
    return {
        "id": arc_id,
        "name": name,
        "label": name,
        "object_type": "arc",
        "arc_type": arc_type,
        "source_id": source_id,
        "source_type": source_type,
        "target_id": target_id,
        "target_type": target_type,
        "weight": weight,
        "threshold": None,
        "color": [0, 0, 0],
        "width": 2.0,
        "control_points": [],
        "consumes": consumes,
    }


def make_transition(tid, name, label, x, y, rate_function,
                    is_source=False, is_sink=False):
    return {
        "id": tid,
        "name": name,
        "label": label,
        "object_type": "transition",
        "x": x,
        "y": y,
        "width": 15.0,
        "height": 60.0,
        "horizontal": False,
        "enabled": True,
        "fill_color": [0, 0, 0],
        "border_color": [0, 0, 0],
        "border_width": 1.0,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "race_with_resampling",
        "is_source": is_source,
        "is_sink": is_sink,
        "guard": None,
        "properties": {"rate_function": rate_function},
        "is_environment_aware": False,
        "compartment": None,
        "adaptive_filter": None,
        "volume_threshold": None,
        "prefer_continuous": True,
    }


def main():
    with open(MODEL_PATH) as f:
        model = json.load(f)

    places = model["places"]
    transitions = model["transitions"]
    arcs = model["arcs"]

    # ========================================================================
    #  1. Rename P1 from "CBD" to "CBD_extracellular"
    # ========================================================================
    for p in places:
        if p["id"] == "P1" and p["name"] == "CBD":
            p["name"] = "CBD_extracellular"
            p["label"] = "CBD_extracellular\n(Cannabidiol)\n100 nM bolus"
            p["metadata"]["compartment"] = "extracellular"
            print("  Renamed P1: CBD → CBD_extracellular")
            break

    # ========================================================================
    #  2. Add P30: CBD_intracellular
    # ========================================================================
    cbd_intra = {
        "id": "P30",
        "name": "CBD_intracellular",
        "label": "CBD_intracellular\n(cytoplasmic CBD)\n0 nM",
        "metadata": {
            "kegg_id": "D10915",
            "chebi_id": "CHEBI:69478",
            "pubchem_cid": "644019",
            "compound_name": "Cannabidiol (intracellular)",
            "formula": "C21H30O2",
            "mw": 314.469,
            "partition": "signal",
            "function": "intracellular_effector",
            "hierarchy_layer": 3,
            "compartment": "intracellular",
        },
        "object_type": "place",
        "x": -160.0,
        "y": 350.0,
        "radius": 40.0,
        "marking": 0.0,
        "tokens": 0.0,
        "initial_marking": 0.0,
        "capacity": 1000,
        "border_color": [0.0, 0.0, 1.0],
        "border_width": 5.0,
        "is_catalyst": False,
        "is_signal_place": True,
        "signal_type": "regulatory",
        "is_compartment_place": False,
        "is_regulatory_place": False,
        "is_energy_place": False,
        "diffusion_coefficient": None,
        "boundary_type": None,
        "gradient_vector": None,
        "compartment_volume": None,
        "neighbor_compartments": [],
        "spatial_position": None,
    }
    places.append(cbd_intra)
    print("  Added P30: CBD_intracellular (0 mM, intracellular compartment)")

    # ========================================================================
    #  3. Add 4 PK transitions
    # ========================================================================

    # PK rate constants (literature-based for CBD):
    #   k_abs    = 0.0008 /s  → membrane permeation inward (τ ≈ 21 min)
    #   k_efflux = 0.0003 /s  → back-transport to extracellular
    #   k_sys    = 0.00003 /s → systemic clearance (hepatic CYP3A4)
    #   k_met    = 0.00005 /s → local brain CYP metabolism
    # All T-dependent via Q10

    pk_transitions = [
        make_transition(
            "T28", "CBD_Absorption",
            "CBD_Absorption\n(membrane permeation)\nFick's law",
            x=-260.0, y=280.0,
            rate_function="0.0008 * CBD_extracellular * 2**((T_celsius - 37)/10)",
        ),
        make_transition(
            "T29", "CBD_Efflux",
            "CBD_Efflux\n(back-transport)\npassive diffusion",
            x=-260.0, y=420.0,
            rate_function="0.0003 * CBD_intracellular * 2**((T_celsius - 37)/10)",
        ),
        make_transition(
            "T30", "CBD_Systemic_Clearance",
            "CBD_Systemic_Clearance\n(hepatic CYP3A4)\nelimination",
            x=-460.0, y=250.0,
            rate_function="0.00003 * CBD_extracellular * 2**((T_celsius - 37)/10)",
            is_sink=True,
        ),
        make_transition(
            "T31", "CBD_Brain_Metabolism",
            "CBD_Brain_Metabolism\n(local CYP450)\nmetabolism",
            x=-60.0, y=250.0,
            rate_function="0.00005 * CBD_intracellular * 2**((T_celsius - 37)/10)",
            is_sink=True,
        ),
    ]
    transitions.extend(pk_transitions)
    print("  Added T28: CBD_Absorption (k=0.0008/s, membrane permeation)")
    print("  Added T29: CBD_Efflux (k=0.0003/s, back-transport)")
    print("  Added T30: CBD_Systemic_Clearance (k=0.00003/s, SINK)")
    print("  Added T31: CBD_Brain_Metabolism (k=0.00005/s, SINK)")

    # ========================================================================
    #  4. Add 6 PK arcs
    # ========================================================================
    new_arcs = [
        # T28 CBD_Absorption: CBD_extra → T28 → CBD_intra
        make_arc("A71", "CBD_extra_to_Absorption",
                 "P1", "place", "T28", "transition",
                 arc_type="normal", consumes=True),
        make_arc("A72", "Absorption_to_CBD_intra",
                 "T28", "transition", "P30", "place",
                 arc_type="normal", consumes=True),

        # T29 CBD_Efflux: CBD_intra → T29 → CBD_extra
        make_arc("A73", "CBD_intra_to_Efflux",
                 "P30", "place", "T29", "transition",
                 arc_type="normal", consumes=True),
        make_arc("A74", "Efflux_to_CBD_extra",
                 "T29", "transition", "P1", "place",
                 arc_type="normal", consumes=True),

        # T30 CBD_Systemic_Clearance: CBD_extra → T30 (SINK, no output)
        make_arc("A75", "CBD_extra_to_SysClearance",
                 "P1", "place", "T30", "transition",
                 arc_type="normal", consumes=True),

        # T31 CBD_Brain_Metabolism: CBD_intra → T31 (SINK, no output)
        make_arc("A76", "CBD_intra_to_BrainMet",
                 "P30", "place", "T31", "transition",
                 arc_type="normal", consumes=True),
    ]
    arcs.extend(new_arcs)
    print("  Added 6 PK arcs (A71-A76)")

    # ========================================================================
    #  5. Redirect intracellular target arcs to CBD_intracellular
    # ========================================================================
    # A25: P1 → T10 (PPARg) — nuclear receptor, needs intracellular CBD
    # A29: P1 → T11 (ROS_releases_Nrf2) — intracellular pathway
    # Change source from P1 (CBD_extra) to P30 (CBD_intra)

    redirected = 0
    for a in arcs:
        if a["id"] == "A25":  # CBD → PPARg activation
            a["source_id"] = "P30"
            a["name"] = "CBD_intra_to_PPARg_activation"
            redirected += 1
            print("  Redirected A25: P1→T10 changed to P30→T10 (PPARγ = nuclear receptor)")
        elif a["id"] == "A29":  # CBD → Nrf2 release
            a["source_id"] = "P30"
            a["name"] = "CBD_intra_to_Nrf2_release"
            redirected += 1
            print("  Redirected A29: P1→T11 changed to P30→T11 (Nrf2 = intracellular)")

    # ========================================================================
    #  6. Update rate functions to use correct CBD compartment names
    # ========================================================================
    rate_updates = {
        # Extracellular targets (membrane receptors) — use CBD_extracellular
        "CBD_activates_GPR3_inv": (
            "0.1 * CBD * GPR3",
            "0.1 * CBD_extracellular * GPR3",
        ),
        "CBD_activates_5HT1A": (
            "0.15 * CBD",
            "0.15 * CBD_extracellular",
        ),
        "CBD_activates_A2A": (
            "0.12 * CBD",
            "0.12 * CBD_extracellular",
        ),
        # Intracellular targets — use CBD_intracellular
        "CBD_activates_PPARg": (
            "0.2 * CBD",
            "0.2 * CBD_intracellular",
        ),
        "ROS_releases_Nrf2": (
            "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD / (50 + CBD)) * 2**((T_celsius - 37)/10)",
            "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD_intracellular / (50 + CBD_intracellular)) * 2**((T_celsius - 37)/10)",
        ),
    }

    updated = 0
    for t in transitions:
        name = t.get("name", "")
        if name in rate_updates:
            old_rate, new_rate = rate_updates[name]
            current = t["properties"]["rate_function"]
            if current != old_rate:
                print(f"  WARNING: {name} rate mismatch!")
                print(f"    Expected: {old_rate}")
                print(f"    Found:    {current}")
                continue
            t["properties"]["rate_function"] = new_rate
            updated += 1
            print(f"  Updated rate: {name}")

    # ========================================================================
    #  7. Summary & Save
    # ========================================================================
    n_places = len(places)
    n_trans = len(transitions)
    n_arcs = len(arcs)
    n_source = sum(1 for t in transitions if t.get("is_source"))
    n_sink = sum(1 for t in transitions if t.get("is_sink"))

    print(f"\n  Summary:")
    print(f"    Places:      {n_places} (was {n_places - 1})")
    print(f"    Transitions: {n_trans} (was {n_trans - 4})")
    print(f"    Arcs:        {n_arcs} (was {n_arcs - 6})")
    print(f"    Sources: {n_source}, Sinks: {n_sink}")
    print(f"    Rate functions updated: {updated}/5")
    print(f"    Arcs redirected: {redirected}/2")

    with open(MODEL_PATH, "w") as f:
        json.dump(model, f, indent=2)
    print(f"\n  Saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
