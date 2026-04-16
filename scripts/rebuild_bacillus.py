#!/usr/bin/env python3
"""
Rebuild Bacillus sporulation model based on comprehensive README.md documentation
"""
import json

# Create comprehensive Bacillus sporulation model
model = {
    "places": [],
    "transitions": [],
    "arcs": [],
    "view_state": {
        "zoom": 0.6,
        "pan_x": 800.0,
        "pan_y": 500.0
    },
    "metadata": {
        "author": "SHYPN Thermodynamics Study",
        "description": "5-layer hierarchical sporulation cascade in Bacillus subtilis with energy constraints",
        "organism": "Bacillus subtilis",
        "system": "Sporulation cascade",
        "category": "biochemical",
        "date_created": "January 2, 2026"
    }
}

# PLACES (24 total across 5 hierarchy layers)
places = [
    # LAYER 0: ENERGY SIGNALS (highest priority)
    {"id": "P1", "name": "ATP_pool", "x": 100, "y": 100, "marking": 5000.0, "signal_type": "ENERGY", "layer": 0, "compartment": "cytoplasm"},
    {"id": "P2", "name": "GTP_pool", "x": 250, "y": 100, "marking": 3000.0, "signal_type": "ENERGY", "layer": 0, "compartment": "cytoplasm"},
    
    # LAYER 1: ENVIRONMENTAL SIGNALS
    {"id": "P3", "name": "Nutrients", "x": 400, "y": 100, "marking": 100.0, "signal_type": "QUORUM", "layer": 1, "compartment": "cytoplasm"},
    {"id": "P4", "name": "Cell_density", "x": 550, "y": 100, "marking": 1.0, "signal_type": "QUORUM", "layer": 1, "compartment": "cytoplasm"},
    
    # LAYER 2: INTEGRATION (Phosphorelay)
    {"id": "P5", "name": "KinA_kinase", "x": 100, "y": 250, "marking": 10.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm"},
    {"id": "P6", "name": "KinA_P", "x": 250, "y": 250, "marking": 0.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm"},
    {"id": "P7", "name": "Spo0F", "x": 400, "y": 250, "marking": 20.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm"},
    {"id": "P8", "name": "Spo0F_P", "x": 550, "y": 250, "marking": 0.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm"},
    {"id": "P9", "name": "Spo0B", "x": 700, "y": 250, "marking": 15.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_catalyst": True},
    {"id": "P10", "name": "Spo0A", "x": 850, "y": 250, "marking": 25.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm"},
    {"id": "P11", "name": "Spo0A_P", "x": 1000, "y": 250, "marking": 0.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm"},
    {"id": "P12", "name": "RapA", "x": 700, "y": 150, "marking": 5.0, "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_catalyst": True},
    
    # LAYER 3: EARLY COMMITMENT
    {"id": "P13", "name": "SigmaH", "x": 100, "y": 400, "marking": 0.0, "signal_type": "REGULATORY", "layer": 3, "compartment": "cytoplasm"},
    
    # LAYER 4: COMMITMENT POINT (Irreversible)
    {"id": "P14", "name": "Septum", "x": 250, "y": 550, "marking": 0.0, "signal_type": "REGULATORY", "layer": 4, "compartment": "septum"},
    {"id": "P15", "name": "SigmaF", "x": 100, "y": 700, "marking": 0.0, "signal_type": "REGULATORY", "layer": 4, "compartment": "forespore"},
    {"id": "P16", "name": "SigmaE", "x": 400, "y": 700, "marking": 0.0, "signal_type": "REGULATORY", "layer": 4, "compartment": "mother_cell"},
    
    # LAYER 5: TERMINAL DIFFERENTIATION
    {"id": "P17", "name": "SigmaG", "x": 100, "y": 850, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "forespore"},
    {"id": "P18", "name": "SigmaK", "x": 400, "y": 850, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell"},
    
    # STRUCTURAL COMPONENTS
    {"id": "P19", "name": "Forespore", "x": 100, "y": 1000, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "forespore"},
    {"id": "P20", "name": "Mother_cell", "x": 400, "y": 1000, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell"},
    {"id": "P21", "name": "Cortex", "x": 250, "y": 1150, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "forespore"},
    {"id": "P22", "name": "Inner_coat", "x": 400, "y": 1150, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell"},
    {"id": "P23", "name": "Outer_coat", "x": 550, "y": 1150, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell"},
    {"id": "P24", "name": "Mature_spore", "x": 325, "y": 1300, "marking": 0.0, "signal_type": "REGULATORY", "layer": 5, "compartment": "spore"},
]

# Convert to full place objects
for p in places:
    model["places"].append({
        "id": p["id"],
        "name": p["name"],
        "label": f"{p['name']}\n{p['marking']}",
        "object_type": "place",
        "x": p["x"],
        "y": p["y"],
        "radius": 30.0,
        "marking": p["marking"],
        "initial_marking": p["marking"],
        "capacity": None,
        "border_color": [0.0, 0.5, 0.8] if p.get("signal_type") == "ENERGY" else [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "is_catalyst": p.get("is_catalyst", False),
        "metadata": {
            "signal_type": p["signal_type"],
            "hierarchy_layer": p["layer"],
            "compartment": p["compartment"]
        }
    })

print(f"✓ Created {len(model['places'])} places")

# TRANSITIONS (22 total)
transitions = [
    # T1: KinA autophosphorylation
    {"id": "T1", "name": "T_KinA_activation", "x": 175, "y": 250, "type": "stochastic",
     "rate_function": "0.0001 * KinA_kinase * (1 / (1 + Nutrients**2)) * ATP_pool / (50 + ATP_pool)"},
    
    # T2: Spo0F phosphorylation
    {"id": "T2", "name": "T_Spo0F_phosphorylation", "x": 325, "y": 250, "type": "stochastic",
     "rate_function": "0.001 * KinA_P * Spo0F / (10 + Spo0F)"},
    
    # T3: Spo0F dephosphorylation
    {"id": "T3", "name": "T_Spo0F_dephosphorylation", "x": 625, "y": 200, "type": "stochastic",
     "rate_function": "0.0005 * Spo0F_P * RapA / (5 + RapA)"},
    
    # T4: Spo0A phosphorylation
    {"id": "T4", "name": "T_Spo0A_phosphorylation", "x": 775, "y": 250, "type": "stochastic",
     "rate_function": "0.0008 * Spo0F_P * Spo0A * Spo0B / (5 + Spo0B)"},
    
    # T5: Spo0A dephosphorylation
    {"id": "T5", "name": "T_Spo0A_dephosphorylation", "x": 925, "y": 200, "type": "stochastic",
     "rate_function": "0.0001 * Spo0A_P"},
    
    # T6: SigmaH transcription
    {"id": "T6", "name": "T_sigmaH_transcription", "x": 100, "y": 325, "type": "stochastic",
     "rate_function": "0.0001 * Spo0A_P**4 / (50 + Spo0A_P**4) * ATP_pool / (100 + ATP_pool)"},
    
    # T7: Septum formation
    {"id": "T7", "name": "T_septation", "x": 175, "y": 475, "type": "stochastic",
     "rate_function": "0.00005 * SigmaH**2 * Cell_density * ATP_pool / (200 + ATP_pool) * GTP_pool / (100 + GTP_pool)"},
    
    # T8: SigmaF activation
    {"id": "T8", "name": "T_sigmaF_activation", "x": 100, "y": 625, "type": "stochastic",
     "rate_function": "0.0002 * Septum * ATP_pool / (50 + ATP_pool)"},
    
    # T9: SigmaE activation
    {"id": "T9", "name": "T_sigmaE_activation", "x": 400, "y": 625, "type": "stochastic",
     "rate_function": "0.0002 * SigmaF * Septum * GTP_pool / (50 + GTP_pool)"},
    
    # T10: SigmaE-SigmaF feedback
    {"id": "T10", "name": "T_sigmaE_feedback", "x": 250, "y": 700, "type": "stochastic",
     "rate_function": "0.0001 * SigmaE * SigmaF * ATP_pool / (100 + ATP_pool)"},
    
    # T11: SigmaG transcription
    {"id": "T11", "name": "T_sigmaG_transcription", "x": 100, "y": 775, "type": "stochastic",
     "rate_function": "0.00008 * SigmaF * SigmaE * ATP_pool / (150 + ATP_pool)"},
    
    # T12: SigmaK transcription
    {"id": "T12", "name": "T_sigmaK_transcription", "x": 400, "y": 775, "type": "stochastic",
     "rate_function": "0.00008 * SigmaE * ATP_pool / (150 + ATP_pool)"},
    
    # T13: Forespore formation
    {"id": "T13", "name": "T_forespore_formation", "x": 100, "y": 925, "type": "stochastic",
     "rate_function": "0.0001 * SigmaF * Septum * ATP_pool / (100 + ATP_pool)"},
    
    # T14: Mother cell formation
    {"id": "T14", "name": "T_mother_cell_formation", "x": 400, "y": 925, "type": "stochastic",
     "rate_function": "0.0001 * SigmaE * Septum * ATP_pool / (100 + ATP_pool)"},
    
    # T15: Cortex synthesis
    {"id": "T15", "name": "T_cortex_synthesis", "x": 175, "y": 1075, "type": "continuous",
     "rate_function": "0.00005 * SigmaG * Forespore * ATP_pool / (300 + ATP_pool)"},
    
    # T16: Inner coat synthesis
    {"id": "T16", "name": "T_inner_coat_synthesis", "x": 400, "y": 1075, "type": "continuous",
     "rate_function": "0.00004 * SigmaK * Mother_cell * ATP_pool / (200 + ATP_pool) * GTP_pool / (100 + GTP_pool)"},
    
    # T17: Outer coat synthesis
    {"id": "T17", "name": "T_outer_coat_synthesis", "x": 550, "y": 1075, "type": "continuous",
     "rate_function": "0.00003 * Inner_coat * SigmaK * GTP_pool / (150 + GTP_pool)"},
    
    # T18: Spore maturation
    {"id": "T18", "name": "T_spore_maturation", "x": 325, "y": 1225, "type": "stochastic",
     "rate_function": "0.0005 * Cortex * Outer_coat * ATP_pool / (50 + ATP_pool)"},
    
    # CONTINUOUS SOURCES
    {"id": "T19", "name": "Source_nutrient_depletion", "x": 400, "y": 50, "type": "continuous",
     "rate_function": "0.1", "is_source": True},
    
    {"id": "T20", "name": "Source_ATP_regen", "x": 100, "y": 50, "type": "continuous",
     "rate_function": "0.5 * Nutrients / (10 + Nutrients)", "is_source": True},
    
    {"id": "T21", "name": "Source_GTP_regen", "x": 250, "y": 50, "type": "continuous",
     "rate_function": "0.3 * Nutrients / (10 + Nutrients)", "is_source": True},
    
    {"id": "T22", "name": "Source_cell_density", "x": 550, "y": 50, "type": "continuous",
     "rate_function": "0.01", "is_source": True},
]

# Convert to full transition objects
for t in transitions:
    model["transitions"].append({
        "id": t["id"],
        "name": t["name"],
        "label": t["name"],
        "object_type": "transition",
        "x": t["x"],
        "y": t["y"],
        "width": 40.0,
        "height": 20.0,
        "horizontal": True,
        "enabled": True,
        "transition_type": t["type"],
        "rate": 1.0,
        "rate_function": t.get("rate_function", ""),
        "priority": 1,
        "firing_policy": "race",
        "is_source": t.get("is_source", False),
        "is_sink": False,
        "guard": 1,
        "fill_color": [0.9, 0.3, 0.24],
        "border_color": [0.9, 0.3, 0.24],
        "border_width": 3.0,
        "metadata": {}
    })

print(f"✓ Created {len(model['transitions'])} transitions")

# ARCS - Based on biological pathways from README
arcs = []
arc_id = 1

def add_arc(source, target, arc_type='normal', weight=1):
    global arc_id
    source_type = 'place' if source.startswith('P') else 'transition'
    target_type = 'transition' if target.startswith('T') else 'place'
    arcs.append({
        'id': f'A{arc_id}',
        'name': f'A{arc_id}',
        'label': '',
        'object_type': 'arc',
        'arc_type': arc_type,
        'source_id': source,
        'source_type': source_type,
        'target_id': target,
        'target_type': target_type,
        'weight': weight,
        'threshold': None,
        'color': [0.0, 0.0, 0.0],
        'width': 3.0,
        'control_points': []
    })
    arc_id += 1

# T1: KinA activation (consumes ATP, uses KinA, senses Nutrients)
add_arc('P1', 'T1')  # ATP consumed
add_arc('P5', 'T1')  # KinA consumed
add_arc('T1', 'P6')  # Produces KinA~P

# T2: Spo0F phosphorylation (consumes KinA~P and Spo0F)
add_arc('P6', 'T2')  # KinA~P consumed
add_arc('P7', 'T2')  # Spo0F consumed
add_arc('T2', 'P5')  # Regenerates KinA
add_arc('T2', 'P8')  # Produces Spo0F~P

# T3: Spo0F dephosphorylation (RapA is catalyst)
add_arc('P8', 'T3')  # Spo0F~P consumed
add_arc('P12', 'T3', 'test')  # RapA catalyst
add_arc('T3', 'P7')  # Regenerates Spo0F

# T4: Spo0A phosphorylation (Spo0B is catalyst)
add_arc('P8', 'T4')  # Spo0F~P consumed
add_arc('P10', 'T4')  # Spo0A consumed
add_arc('P9', 'T4', 'test')  # Spo0B catalyst
add_arc('T4', 'P7')  # Regenerates Spo0F
add_arc('T4', 'P11')  # Produces Spo0A~P

# T5: Spo0A dephosphorylation
add_arc('P11', 'T5')  # Spo0A~P consumed
add_arc('T5', 'P10')  # Regenerates Spo0A

# T6: SigmaH transcription (Spo0A~P sensed, ATP consumed)
add_arc('P11', 'T6', 'test')  # Spo0A~P activator
add_arc('P1', 'T6')  # ATP consumed
add_arc('T6', 'P13')  # Produces SigmaH

# T7: Septation (SigmaH sensed, cell_density sensed, ATP/GTP consumed)
add_arc('P13', 'T7', 'test')  # SigmaH activator
add_arc('P4', 'T7', 'test')  # Cell_density sensor
add_arc('P1', 'T7')  # ATP consumed
add_arc('P2', 'T7')  # GTP consumed
add_arc('T7', 'P14')  # Produces Septum

# T8: SigmaF activation (Septum sensed, ATP consumed)
add_arc('P14', 'T8', 'test')  # Septum activator
add_arc('P1', 'T8')  # ATP consumed
add_arc('T8', 'P15')  # Produces SigmaF

# T9: SigmaE activation (SigmaF and Septum sensed, GTP consumed)
add_arc('P15', 'T9', 'test')  # SigmaF signal
add_arc('P14', 'T9', 'test')  # Septum sensor
add_arc('P2', 'T9')  # GTP consumed
add_arc('T9', 'P16')  # Produces SigmaE

# T10: SigmaE-SigmaF feedback (both sensed, ATP consumed)
add_arc('P15', 'T10', 'test')  # SigmaF sensor
add_arc('P16', 'T10', 'test')  # SigmaE sensor
add_arc('P1', 'T10')  # ATP consumed
add_arc('T10', 'P15')  # Amplifies SigmaF

# T11: SigmaG transcription (SigmaF and SigmaE sensed, ATP consumed)
add_arc('P15', 'T11', 'test')  # SigmaF activator
add_arc('P16', 'T11', 'test')  # SigmaE activator
add_arc('P1', 'T11')  # ATP consumed
add_arc('T11', 'P17')  # Produces SigmaG

# T12: SigmaK transcription (SigmaE sensed, ATP consumed)
add_arc('P16', 'T12', 'test')  # SigmaE activator
add_arc('P1', 'T12')  # ATP consumed
add_arc('T12', 'P18')  # Produces SigmaK

# T13: Forespore formation (SigmaF and Septum sensed, ATP consumed)
add_arc('P15', 'T13', 'test')  # SigmaF activator
add_arc('P14', 'T13', 'test')  # Septum sensor
add_arc('P1', 'T13')  # ATP consumed
add_arc('T13', 'P19')  # Produces Forespore

# T14: Mother cell formation (SigmaE and Septum sensed, ATP consumed)
add_arc('P16', 'T14', 'test')  # SigmaE activator
add_arc('P14', 'T14', 'test')  # Septum sensor
add_arc('P1', 'T14')  # ATP consumed
add_arc('T14', 'P20')  # Produces Mother_cell

# T15: Cortex synthesis (SigmaG and Forespore sensed, massive ATP consumed)
add_arc('P17', 'T15', 'test')  # SigmaG activator
add_arc('P19', 'T15', 'test')  # Forespore sensor
add_arc('P1', 'T15', 'normal', 100)  # ATP consumed (high cost!)
add_arc('T15', 'P21')  # Produces Cortex

# T16: Inner coat synthesis (SigmaK and Mother_cell sensed, ATP/GTP consumed)
add_arc('P18', 'T16', 'test')  # SigmaK activator
add_arc('P20', 'T16', 'test')  # Mother_cell sensor
add_arc('P1', 'T16', 'normal', 80)  # ATP consumed
add_arc('P2', 'T16', 'normal', 20)  # GTP consumed
add_arc('T16', 'P22')  # Produces Inner_coat

# T17: Outer coat synthesis (Inner_coat and SigmaK sensed, GTP consumed)
add_arc('P22', 'T17', 'test')  # Inner_coat sensor
add_arc('P18', 'T17', 'test')  # SigmaK activator
add_arc('P2', 'T17', 'normal', 50)  # GTP consumed
add_arc('T17', 'P23')  # Produces Outer_coat

# T18: Spore maturation (Cortex and Outer_coat consumed, ATP consumed)
add_arc('P21', 'T18')  # Cortex consumed
add_arc('P23', 'T18')  # Outer_coat consumed
add_arc('P1', 'T18')  # ATP consumed
add_arc('T18', 'P24')  # Produces Mature_spore

# CONTINUOUS SOURCES
# T19: Nutrient depletion (sink)
add_arc('P3', 'T19')  # Nutrients consumed

# T20: ATP regeneration (source, Nutrients sensed)
add_arc('P3', 'T20', 'test')  # Nutrients sensor
add_arc('T20', 'P1')  # Produces ATP

# T21: GTP regeneration (source, Nutrients sensed)
add_arc('P3', 'T21', 'test')  # Nutrients sensor
add_arc('T21', 'P2')  # Produces GTP

# T22: Cell density increase
add_arc('T22', 'P4')  # Produces Cell_density

model["arcs"] = arcs
print(f"✓ Created {len(arcs)} arcs ({sum(1 for a in arcs if a["arc_type"] == "normal")} normal, {sum(1 for a in arcs if a["arc_type"] == "test")} test)")

# Save
with open('workspace/projects/My_Project/thermodynamics/bacillus_sporulation.shy', 'w') as f:
    json.dump(model, f, indent=2)

print(f"\n✅ COMPLETE MODEL SAVED")
print(f"   Places: {len(model['places'])}")
print(f"   Transitions: {len(model['transitions'])} (18 stochastic + 4 continuous sources)")
print(f"   Arcs: {len(model['arcs'])}")
print(f"\n   File: workspace/projects/My_Project/thermodynamics/bacillus_sporulation.shy")
