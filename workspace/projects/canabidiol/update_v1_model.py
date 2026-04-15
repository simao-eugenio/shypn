#!/usr/bin/env python3
"""Update CBD-AD v1 model: add degradation/clearance transitions, fix source/sink markers."""

import json
from pathlib import Path

MODEL = Path(__file__).parent / "models/cbd_ad_neuroprotection_v1.shy"

with open(MODEL) as f:
    model = json.load(f)

# =============================================================================
# 1. FIX SOURCE/SINK MARKERS ON EXISTING TRANSITIONS
# =============================================================================
# Build arc index: which arcs connect to each transition, and their types
arcs = model["arcs"]
transitions = model["transitions"]

# Map transition ids to their arc sets
t_normal_inputs = {}   # normal arcs from place->transition (material consumed)
t_test_inputs = {}     # test arcs from place->transition (read-only)
t_signal_inputs = {}   # signal_flow arcs from place->transition (read-only)
t_outputs = {}         # arcs from transition->place (material produced)

for a in arcs:
    src, tgt = a["source_id"], a["target_id"]
    atype = a["arc_type"]
    
    if a["target_type"] == "transition":
        tid = tgt
        if atype == "normal":
            t_normal_inputs.setdefault(tid, []).append(a)
        elif atype == "test":
            t_test_inputs.setdefault(tid, []).append(a)
        elif atype == "signal_flow":
            t_signal_inputs.setdefault(tid, []).append(a)
    elif a["source_type"] == "transition":
        tid = src
        t_outputs.setdefault(tid, []).append(a)

# Classify each existing transition
for t in transitions:
    tid = t["id"]
    has_normal_in = len(t_normal_inputs.get(tid, [])) > 0
    has_out = len(t_outputs.get(tid, [])) > 0
    
    # Source: no normal input arcs (only test/signal_flow), has outputs
    # Produces material from nothing (modulated by signals/tests)
    if not has_normal_in and has_out:
        t["is_source"] = True
        t["is_sink"] = False
    # Sink: has normal input arcs, no output arcs
    # Consumes material with no product
    elif has_normal_in and not has_out:
        t["is_source"] = False
        t["is_sink"] = True
    else:
        t["is_source"] = False
        t["is_sink"] = False

# Print what changed for verification
print("Source/sink reclassification:")
for t in transitions:
    src = "SOURCE" if t["is_source"] else ""
    snk = "SINK" if t["is_sink"] else ""
    marker = src + snk if src or snk else "internal"
    print(f"  {t['id']:4s} {t['name']:35s} {marker}")

# =============================================================================
# 2. ADD NEW TRANSITIONS
# =============================================================================
new_transitions = [
    {
        "id": "T23",
        "name": "Cytokine_Degradation",
        "label": "Cytokine\ndegradation\n(proteolysis)",
        "object_type": "transition",
        "x": 1050.0,
        "y": 450.0,
        "width": 60.0,
        "height": 15.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.3, 0.3, 0.3],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "race",
        "is_source": False,
        "is_sink": True,
        "guard": 1,
        "properties": {
            "rate_function": "0.005 * (TNFa + IL1b + IL6 + COX2)",
            "rate_function_display": "k_deg × ([TNFα] + [IL-1β] + [IL-6] + [COX-2])"
        },
        "compartment": "extracellular"
    },
    {
        "id": "T24",
        "name": "Abeta_Oligomer_Clearance",
        "label": "Aβ oligomer\nclearance\n(M2 phagocytosis)",
        "object_type": "transition",
        "x": 850.0,
        "y": 200.0,
        "width": 60.0,
        "height": 15.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.0, 0.5, 1.0],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "race",
        "is_source": False,
        "is_sink": True,
        "guard": 1,
        "properties": {
            "rate_function": "0.003 * Microglia_M2 * Abeta_Oligomer / (10 + Abeta_Oligomer)",
            "rate_function_display": "k_phago × [M2] × [Aβ_olig] / (Km + [Aβ_olig])"
        },
        "compartment": "extracellular"
    },
    {
        "id": "T25",
        "name": "Abeta_Monomer_Clearance",
        "label": "Aβ monomer\ndegradation\n(neprilysin)",
        "object_type": "transition",
        "x": 650.0,
        "y": 200.0,
        "width": 60.0,
        "height": 15.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.3, 0.3, 0.3],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "race",
        "is_source": False,
        "is_sink": True,
        "guard": 1,
        "properties": {
            "rate_function": "0.01 * Abeta_Monomer",
            "rate_function_display": "k_nep × [Aβ_mono]"
        },
        "compartment": "extracellular"
    },
    {
        "id": "T26",
        "name": "BDNF_Turnover",
        "label": "BDNF\nturnover",
        "object_type": "transition",
        "x": 850.0,
        "y": 1000.0,
        "width": 60.0,
        "height": 15.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.3, 0.3, 0.3],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "race",
        "is_source": False,
        "is_sink": True,
        "guard": 1,
        "properties": {
            "rate_function": "0.005 * BDNF",
            "rate_function_display": "k_deg × [BDNF]"
        },
        "compartment": "extracellular"
    },
    {
        "id": "T27",
        "name": "IKK_Dephosphorylation",
        "label": "IKK\ndephosphorylation\n(turnover)",
        "object_type": "transition",
        "x": 450.0,
        "y": 200.0,
        "width": 60.0,
        "height": 15.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.3, 0.3, 0.3],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "transition_type": "continuous",
        "priority": 0,
        "firing_policy": "race",
        "is_source": False,
        "is_sink": True,
        "guard": 1,
        "properties": {
            "rate_function": "0.008 * (IKK - 10) * (IKK > 10)",
            "rate_function_display": "k_dephos × max(0, [IKK] - IKK_basal)"
        },
        "compartment": "cytoplasm"
    }
]

model["transitions"].extend(new_transitions)

# =============================================================================
# 3. ADD NEW ARCS
# =============================================================================
new_arcs = [
    # T23: Cytokine_Degradation — consumes TNFα, IL-1β, IL-6, COX-2
    {
        "id": "A62", "name": "TNFa_to_T23", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P11", "source_type": "place",
        "target_id": "T23", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [1.0, 0.0, 0.0], "width": 3.0, "control_points": []
    },
    {
        "id": "A63", "name": "IL1b_to_T23", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P12", "source_type": "place",
        "target_id": "T23", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [1.0, 0.0, 0.0], "width": 3.0, "control_points": []
    },
    {
        "id": "A64", "name": "IL6_to_T23", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P13", "source_type": "place",
        "target_id": "T23", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [1.0, 0.0, 0.0], "width": 3.0, "control_points": []
    },
    {
        "id": "A65", "name": "COX2_to_T23", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P14", "source_type": "place",
        "target_id": "T23", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [0.8, 0.2, 0.2], "width": 3.0, "control_points": []
    },
    # T24: Abeta_Oligomer_Clearance — M2 phagocytosis
    {
        "id": "A66", "name": "Abeta_olig_to_T24", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P6", "source_type": "place",
        "target_id": "T24", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [1.0, 0.0, 0.0], "width": 3.0, "control_points": []
    },
    {
        "id": "A67", "name": "M2_to_T24", "label": "",
        "object_type": "arc", "arc_type": "test",
        "source_id": "P22", "source_type": "place",
        "target_id": "T24", "target_type": "transition",
        "weight": 1.0, "threshold": 1,
        "color": [0.0, 0.5, 1.0], "width": 2.0, "control_points": [],
        "consumes": False
    },
    # T25: Abeta_Monomer_Clearance — neprilysin
    {
        "id": "A68", "name": "Abeta_mono_to_T25", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P5", "source_type": "place",
        "target_id": "T25", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [0.8, 0.2, 0.0], "width": 3.0, "control_points": []
    },
    # T26: BDNF_Turnover
    {
        "id": "A69", "name": "BDNF_to_T26", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P24", "source_type": "place",
        "target_id": "T26", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [0.0, 0.4, 0.8], "width": 3.0, "control_points": []
    },
    # T27: IKK_Dephosphorylation
    {
        "id": "A70", "name": "IKK_to_T27", "label": "",
        "object_type": "arc", "arc_type": "normal",
        "source_id": "P10", "source_type": "place",
        "target_id": "T27", "target_type": "transition",
        "weight": 1.0, "threshold": None,
        "color": [0.3, 0.3, 0.8], "width": 3.0, "control_points": []
    }
]

model["arcs"].extend(new_arcs)

# =============================================================================
# 4. UPDATE METADATA
# =============================================================================
model["metadata"]["object_counts"] = {
    "places": len(model["places"]),
    "transitions": len(model["transitions"]),
    "arcs": len(model["arcs"]),
    "modules": 0
}

# Update notes to reflect changes
model["metadata"]["notes"] = (
    "Five integrated modules:\n"
    "1. CBD Pharmacokinetics (external input)\n"
    "2. Amyloid Pathway (GPR3 → γ-secretase → APP → Aβ cascade + clearance)\n"
    "3. Neuroinflammation (NFκB/IκB switch, cytokines + degradation)\n"
    "4. Oxidative Stress (Nrf2/Keap1 → ARE → antioxidants vs ROS)\n"
    "5. Neuroprotection (microglial M1/M2 polarization, BDNF + turnover, neuronal health)\n"
    "\n"
    "Signal hierarchy:\n"
    "- Layer 3: CBD (pharmacokinetic input)\n"
    "- Layer 2: Receptor states (GPR3, PPARγ, 5-HT1A, A2A)\n"
    "- Layer 1: Intracellular signaling (NFκB, Nrf2, γ-secretase)\n"
    "- Layer 0: Effectors (Aβ, cytokines, ROS, BDNF)\n"
    "\n"
    "Key phenomena:\n"
    "- Bistability: M1/M2 microglial switch, NFκB ON/OFF\n"
    "- Preemption: CBD → GPR3 inverse agonism preempts Aβ production\n"
    "- Siphon: Neuron_health (irreversible loss)\n"
    "- Trap: Aβ_plaque (irreversible accumulation)\n"
    "- Conservation: M1 + M2 = total microglia (P-invariant)\n"
    "\n"
    "v1 updates:\n"
    "- Added cytokine degradation (T23) — prevents unbounded cytokine accumulation\n"
    "- Added Aβ oligomer clearance via M2 phagocytosis (T24)\n"
    "- Added Aβ monomer degradation via neprilysin (T25)\n"
    "- Added BDNF turnover (T26)\n"
    "- Added IKK dephosphorylation/turnover (T27)\n"
    "- Fixed source/sink markers on all transitions\n"
    "\n"
    "References:\n"
    "- Atalay et al. (2020) PMC7023045\n"
    "- Shannon et al. (2019) PMC6326553\n"
    "- KEGG D10915, ChEBI:69478, PubChem CID:644019"
)

# =============================================================================
# 5. WRITE BACK
# =============================================================================
with open(MODEL, "w") as f:
    json.dump(model, f, indent=2)

print(f"\nModel updated: {len(model['places'])} places, {len(model['transitions'])} transitions, {len(model['arcs'])} arcs")
print("Source/sink markers fixed, degradation/clearance transitions added.")
