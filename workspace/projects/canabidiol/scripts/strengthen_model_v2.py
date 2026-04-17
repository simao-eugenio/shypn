#!/usr/bin/env python3
"""
Strengthen CBD-AD model v1 → v2:
  - Add 6 turnover/degradation transitions for unbounded species
  - Add GPR3 basal synthesis transition
  - Add Plaque clearance transition  
  - Add ROS→IKK feedback arc (ROS activates IKK)
  - Add TNFα→ROS feedback arc (TNFα amplifies ROS)
  - Update metadata counts
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
SRC = MODEL_DIR / "cbd_ad_neuroprotection_v1.shy"
DST = MODEL_DIR / "cbd_ad_neuroprotection_v2.shy"

# Backup v1
shutil.copy2(SRC, MODEL_DIR / "cbd_ad_neuroprotection_v1.shy.bak")

with open(SRC) as f:
    model = json.load(f)

places = model["places"]
transitions = model["transitions"]
arcs = model["arcs"]

# ─── Helper: build transition dict matching existing schema ───────────────
def make_transition(
    tid, name, label, x, y, rate_function, rate_function_display,
    compartment, is_source=False, is_sink=False, priority=0,
    transition_type="continuous", signal_places=None,
    is_environment_aware=False
):
    t = {
        "id": tid,
        "name": name,
        "label": label,
        "object_type": "transition",
        "x": x,
        "y": y,
        "width": 60.0,
        "height": 15.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.0, 0.8, 0.0],
        "border_color": [0.0, 0.8, 0.0],
        "border_width": 3.0,
        "transition_type": transition_type,
        "priority": priority,
        "firing_policy": "race",
        "is_source": is_source,
        "is_sink": is_sink,
        "guard": 1,
        "properties": {
            "rate_function": rate_function,
            "rate_function_display": rate_function_display,
        },
        "is_environment_aware": is_environment_aware,
        "compartment": compartment,
        "adaptive_filter": None,
        "volume_threshold": None,
        "prefer_continuous": None,
    }
    if signal_places is not None:
        t["signal_places"] = signal_places
    return t


def make_arc(aid, name, source_id, source_type, target_id, target_type,
             arc_type="normal", weight=1.0, threshold=None,
             color=None, consumes=False):
    if color is None:
        if arc_type == "test":
            color = [0.0, 0.0, 1.0]
        elif arc_type == "signal_flow":
            color = [0.6, 0.0, 0.8]
        else:
            color = [0.0, 0.0, 0.0]
    return {
        "id": aid,
        "name": name,
        "label": "",
        "object_type": "arc",
        "arc_type": arc_type,
        "source_id": source_id,
        "source_type": source_type,
        "target_id": target_id,
        "target_type": target_type,
        "weight": weight,
        "threshold": threshold,
        "color": color,
        "width": 3.0,
        "control_points": [],
        "consumes": consumes,
    }


# ═══════════════════════════════════════════════════════════════════════════
# A. SIX TURNOVER TRANSITIONS (T32–T37) for unbounded species
# ═══════════════════════════════════════════════════════════════════════════

# Positions: offset ~120px from the species they degrade

new_transitions = []
new_arcs = []
arc_id = 77  # continue from A76

# T32: PPARg_active degradation — half-life ~4h → k ≈ 0.000048/s ≈ 0.00005
# P26 (PPARg_active) at (310, 470)
new_transitions.append(make_transition(
    "T32", "PPARg_Degradation",
    "PPARγ\nturnover",
    x=310.0, y=590.0,
    rate_function="0.00005 * PPARg_active * 2**((T_celsius - 37)/10)",
    rate_function_display="k_deg_PPARg × [PPARγ_act] × Q10",
    compartment="nucleus",
    is_source=False, is_sink=True,
))
# Arc: P26 → T32 (signal_flow, consumes PPARg_active)
new_arcs.append(make_arc(
    f"A{arc_id}", "PPARg_to_T32",
    "P26", "place", "T32", "transition",
    arc_type="signal_flow", weight=1.0, consumes=True,
))
arc_id += 1

# T33: HT1A_active degradation — receptor desensitization, half-life ~2h → k ≈ 0.0001
# P25 (HT1A_active) at (-420, 950)
new_transitions.append(make_transition(
    "T33", "HT1A_Desensitization",
    "5-HT1A\ndesensitization",
    x=-420.0, y=1080.0,
    rate_function="0.0001 * HT1A_active",
    rate_function_display="k_desens × [5-HT1A_act]",
    compartment="plasma_membrane",
    is_source=False, is_sink=True,
))
new_arcs.append(make_arc(
    f"A{arc_id}", "HT1A_to_T33",
    "P25", "place", "T33", "transition",
    arc_type="signal_flow", weight=1.0, consumes=True,
))
arc_id += 1

# T34: A2A_active degradation — half-life ~3h → k ≈ 0.000065
# P27 (A2A_active) at (-590, 1180)
new_transitions.append(make_transition(
    "T34", "A2A_Desensitization",
    "A2A\ndesensitization",
    x=-590.0, y=1310.0,
    rate_function="0.000065 * A2A_active",
    rate_function_display="k_desens × [A2A_act]",
    compartment="plasma_membrane",
    is_source=False, is_sink=True,
))
new_arcs.append(make_arc(
    f"A{arc_id}", "A2A_to_T34",
    "P27", "place", "T34", "transition",
    arc_type="signal_flow", weight=1.0, consumes=True,
))
arc_id += 1

# T35: Gamma_Secretase degradation — half-life ~6h → k ≈ 0.000032
# P3 (Gamma_Secretase) at (410, -220)
new_transitions.append(make_transition(
    "T35", "GammaSec_Turnover",
    "γ-secretase\nturnover",
    x=410.0, y=-340.0,
    rate_function="0.000032 * (Gamma_Secretase - 30) * (Gamma_Secretase > 30)",
    rate_function_display="k_turn × ([γ-sec] - basal) × H(excess)",
    compartment="plasma_membrane",
    is_source=False, is_sink=True,
))
new_arcs.append(make_arc(
    f"A{arc_id}", "GammaSec_to_T35",
    "P3", "place", "T35", "transition",
    arc_type="normal", weight=1.0,
))
arc_id += 1

# T36: HO1 degradation — half-life ~8h → k ≈ 0.000024
# P17 (HO1) at (1360, 880)
new_transitions.append(make_transition(
    "T36", "HO1_Degradation",
    "HO-1\nturnover",
    x=1500.0, y=880.0,
    rate_function="0.000024 * HO1 * 2**((T_celsius - 37)/10)",
    rate_function_display="k_deg × [HO1] × Q10",
    compartment="cytoplasm",
    is_source=False, is_sink=True,
))
new_arcs.append(make_arc(
    f"A{arc_id}", "HO1_to_T36",
    "P17", "place", "T36", "transition",
    arc_type="normal", weight=1.0,
))
arc_id += 1

# T37: SOD degradation — half-life ~12h → k ≈ 0.000016
# P18 (SOD) at (1360, 1010)
new_transitions.append(make_transition(
    "T37", "SOD_Degradation",
    "SOD\nturnover",
    x=1500.0, y=1010.0,
    rate_function="0.000016 * (SOD - 5) * (SOD > 5)",
    rate_function_display="k_deg × ([SOD] - basal) × H(excess)",
    compartment="cytoplasm",
    is_source=False, is_sink=True,
))
new_arcs.append(make_arc(
    f"A{arc_id}", "SOD_to_T37",
    "P18", "place", "T37", "transition",
    arc_type="normal", weight=1.0,
))
arc_id += 1


# ═══════════════════════════════════════════════════════════════════════════
# B. GPR3 BASAL SYNTHESIS (T38) — constitutive expression maintains basal level
# ═══════════════════════════════════════════════════════════════════════════

# P2 (GPR3) at (160, -180), initial=50
new_transitions.append(make_transition(
    "T38", "GPR3_Basal_Synthesis",
    "GPR3\nbasal expression",
    x=160.0, y=-310.0,
    rate_function="0.005 * (50 - GPR3) * (GPR3 < 50)",
    rate_function_display="k_synth × (basal - [GPR3]) × H(deficit)",
    compartment="plasma_membrane",
    is_source=True, is_sink=False,
))
# Arc: T38 → P2 (produces GPR3)
new_arcs.append(make_arc(
    f"A{arc_id}", "T38_to_GPR3",
    "T38", "transition", "P2", "place",
    arc_type="normal", weight=1.0,
))
arc_id += 1


# ═══════════════════════════════════════════════════════════════════════════
# C. PLAQUE CLEARANCE (T39) — M2 microglia-dependent phagocytosis
# ═══════════════════════════════════════════════════════════════════════════

# P7 (Abeta_Plaque) at (1840, 180), P22 (Microglia_M2) at (-40, 1150)
new_transitions.append(make_transition(
    "T39", "Plaque_Clearance",
    "Plaque\nclearance (M2)",
    x=1840.0, y=340.0,
    rate_function="(0.001 * Microglia_M2 * Abeta_Plaque / (50 + Abeta_Plaque) * 2**((T_celsius - 37)/10)) / (1 + 0.02*(Age - 65))",
    rate_function_display="k_clear × [M2] × [Plaque]/(Km+[Plaque]) × Q10 / Age_factor",
    compartment="extracellular",
    is_source=False, is_sink=True,
    is_environment_aware=True,
))
# Arc: P7 → T39 (plaque consumed — normal arc, P7 not signal place)
new_arcs.append(make_arc(
    f"A{arc_id}", "Plaque_to_T39",
    "P7", "place", "T39", "transition",
    arc_type="normal", weight=1.0,
))
arc_id += 1
# Arc: P22 → T39 (M2 as catalyst/test — not consumed)
new_arcs.append(make_arc(
    f"A{arc_id}", "M2_to_T39",
    "P22", "place", "T39", "transition",
    arc_type="test", weight=1.0, threshold=1,
))
arc_id += 1


# ═══════════════════════════════════════════════════════════════════════════
# D. ROS ↔ INFLAMMATION FEEDBACK ARCS
# ═══════════════════════════════════════════════════════════════════════════

# D1: ROS → IKK activation (H2O2 oxidizes IKK regulatory cysteines)
# New transition T40 or modify existing? Better as new transition: ROS_activates_IKK
new_transitions.append(make_transition(
    "T40", "ROS_activates_IKK",
    "ROS → IKK\n(oxidative activation)",
    x=1250.0, y=250.0,
    rate_function="0.05 * ROS / (20 + ROS) * 2**((T_celsius - 37)/10)",
    rate_function_display="k_ox × [ROS]/(Km+[ROS]) × Q10",
    compartment="cytoplasm",
    is_source=True, is_sink=False,
    signal_places=["P19"],
    is_environment_aware=True,
))
# Arc: P19(ROS) → T40 (test, ROS not consumed)
new_arcs.append(make_arc(
    f"A{arc_id}", "ROS_to_T40",
    "P19", "place", "T40", "transition",
    arc_type="test", weight=1.0, threshold=1,
))
arc_id += 1
# Arc: T40 → P10(IKK) (produces IKK)
new_arcs.append(make_arc(
    f"A{arc_id}", "T40_to_IKK",
    "T40", "transition", "P10", "place",
    arc_type="normal", weight=1.0,
))
arc_id += 1

# D2: TNFα → ROS amplification (TNF-R1 complex I inhibition)
# Modify T14 (Basal_ROS_Production) rate function to include TNFα term
for t in transitions:
    if t["id"] == "T14":
        old_rf = t["properties"]["rate_function"]
        # Old: (2.0 + 0.5 * Abeta_Oligomer) * 2**((T_celsius - 37)/10)
        # New: (2.0 + 0.5 * Abeta_Oligomer + 0.3 * TNFa / (15 + TNFa)) * 2**((T_celsius - 37)/10)
        t["properties"]["rate_function"] = \
            "(2.0 + 0.5 * Abeta_Oligomer + 0.3 * TNFa / (15 + TNFa)) * 2**((T_celsius - 37)/10)"
        t["properties"]["rate_function_display"] = \
            "(basal + k_Ab × [Aβ_olig] + k_TNF × [TNFα]/(Km+[TNFα])) × Q10"
        # T14 now depends on TNFa (P11) — add signal_places if not present
        if "signal_places" not in t:
            t["signal_places"] = []
        if "P11" not in t["signal_places"]:
            t["signal_places"].append("P11")
        if "P6" not in t["signal_places"]:
            t["signal_places"].append("P6")
        t["is_environment_aware"] = True
        print(f"Updated T14 rate: {old_rf} → {t['properties']['rate_function']}")
        break

# Add arc: P11(TNFa) → T14 (test arc, TNFa not consumed — catalytic read)
new_arcs.append(make_arc(
    f"A{arc_id}", "TNFa_to_T14",
    "P11", "place", "T14", "transition",
    arc_type="test", weight=1.0, threshold=1,
))
arc_id += 1

# Also need arc P6(Abeta_Oligomer) → T14 if it doesn't exist
existing_t14_inputs = {a["source_id"] for a in arcs if a["target_id"] == "T14"}
if "P6" not in existing_t14_inputs:
    new_arcs.append(make_arc(
        f"A{arc_id}", "Abeta_Olig_to_T14",
        "P6", "place", "T14", "transition",
        arc_type="test", weight=1.0, threshold=1,
    ))
    arc_id += 1


# ═══════════════════════════════════════════════════════════════════════════
# APPEND AND UPDATE COUNTS
# ═══════════════════════════════════════════════════════════════════════════

transitions.extend(new_transitions)
arcs.extend(new_arcs)

n_places = len(places)
n_transitions = len(transitions)
n_arcs = len(arcs)

model["metadata"]["object_counts"]["places"] = n_places
model["metadata"]["object_counts"]["transitions"] = n_transitions
model["metadata"]["object_counts"]["arcs"] = n_arcs
model["metadata"]["modified"] = datetime.now().isoformat()
model["metadata"]["version_note"] = (
    "v2: Added 6 turnover transitions (PPARg, HT1A, A2A, GammaSec, HO1, SOD), "
    "GPR3 basal synthesis, Plaque clearance, ROS↔inflammation feedback (ROS→IKK, TNFα→ROS)"
)

with open(DST, "w") as f:
    json.dump(model, f, indent=2)

print(f"\nModel v2 saved: {DST}")
print(f"  Places:      {n_places}")
print(f"  Transitions: {n_transitions}")
print(f"  Arcs:        {n_arcs}")
print(f"  New transitions: {[t['id'] + ' ' + t['name'] for t in new_transitions]}")
print(f"  New arcs:        {[a['id'] + ' ' + a['name'] for a in new_arcs]}")
