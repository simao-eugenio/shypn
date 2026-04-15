#!/usr/bin/env python3
"""
Rebuild Bacillus sporulation model with proper signal hierarchy paradigm
- ALL regulatory components are signal places
- ATP/GTP connected via signal_flow arcs (consuming mode)
- Other signals appear only in rate formulas (sensing mode)
"""
import json

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
        "description": "5-layer hierarchical sporulation cascade - Signal hierarchy stress test",
        "organism": "Bacillus subtilis",
        "system": "Sporulation cascade",
        "category": "biochemical",
        "date_created": "January 2, 2026"
    }
}

# ALL PLACES ARE SIGNAL PLACES (no material flow, only information)
places = [
    # LAYER 0: ENERGY SIGNALS (hierarchical control via signal_flow arcs)
    {"id": "P1", "name": "ATP_pool", "x": 100, "y": 100, "marking": 5000.0, 
     "signal_type": "ENERGY", "layer": 0, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P2", "name": "GTP_pool", "x": 300, "y": 100, "marking": 3000.0, 
     "signal_type": "ENERGY", "layer": 0, "compartment": "cytoplasm", "is_signal": True},
    
    # LAYER 1: ENVIRONMENTAL SIGNALS (sensing only)
    {"id": "P3", "name": "Nutrients", "x": 500, "y": 100, "marking": 100.0, 
     "signal_type": "QUORUM", "layer": 1, "compartment": "extracellular", "is_signal": True},
    {"id": "P4", "name": "Cell_density", "x": 700, "y": 100, "marking": 1.0, 
     "signal_type": "QUORUM", "layer": 1, "compartment": "extracellular", "is_signal": True},
    
    # LAYER 2: INTEGRATION LAYER - Phosphorelay (all signal places)
    {"id": "P5", "name": "KinA_kinase", "x": 100, "y": 300, "marking": 10.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P6", "name": "KinA_P", "x": 300, "y": 300, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P7", "name": "Spo0F", "x": 500, "y": 300, "marking": 20.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P8", "name": "Spo0F_P", "x": 700, "y": 300, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P9", "name": "Spo0B", "x": 900, "y": 250, "marking": 15.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P10", "name": "Spo0A", "x": 1100, "y": 300, "marking": 25.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P11", "name": "Spo0A_P", "x": 1300, "y": 300, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    {"id": "P12", "name": "RapA", "x": 900, "y": 200, "marking": 5.0, 
     "signal_type": "REGULATORY", "layer": 2, "compartment": "cytoplasm", "is_signal": True},
    
    # LAYER 3: EARLY COMMITMENT
    {"id": "P13", "name": "SigmaH", "x": 100, "y": 500, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 3, "compartment": "cytoplasm", "is_signal": True},
    
    # LAYER 4: COMMITMENT POINT (Irreversible)
    {"id": "P14", "name": "Septum", "x": 400, "y": 700, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 4, "compartment": "septum", "is_signal": True},
    {"id": "P15", "name": "SigmaF", "x": 200, "y": 900, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 4, "compartment": "forespore", "is_signal": True},
    {"id": "P16", "name": "SigmaE", "x": 600, "y": 900, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 4, "compartment": "mother_cell", "is_signal": True},
    
    # LAYER 5: TERMINAL DIFFERENTIATION
    {"id": "P17", "name": "SigmaG", "x": 200, "y": 1100, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "forespore", "is_signal": True},
    {"id": "P18", "name": "SigmaK", "x": 600, "y": 1100, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell", "is_signal": True},
    
    # STRUCTURAL COMPONENTS (also signal places for sensing)
    {"id": "P19", "name": "Forespore", "x": 200, "y": 1300, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "forespore", "is_signal": True},
    {"id": "P20", "name": "Mother_cell", "x": 600, "y": 1300, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell", "is_signal": True},
    {"id": "P21", "name": "Cortex", "x": 200, "y": 1500, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "forespore", "is_signal": True},
    {"id": "P22", "name": "Inner_coat", "x": 600, "y": 1500, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell", "is_signal": True},
    {"id": "P23", "name": "Outer_coat", "x": 800, "y": 1500, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "mother_cell", "is_signal": True},
    {"id": "P24", "name": "Mature_spore", "x": 400, "y": 1700, "marking": 0.0, 
     "signal_type": "REGULATORY", "layer": 5, "compartment": "spore", "is_signal": True},
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
        "capacity": "Infinity",
        "border_color": [0.0, 0.5, 0.8] if p.get("signal_type") == "ENERGY" else [0.0, 0.4, 0.7],
        "border_width": 3.0,
        "is_catalyst": False,
        "is_signal_place": True,  # ALL places are signals!
        "metadata": {
            "signal_type": p["signal_type"],
            "hierarchy_layer": p["layer"],
            "compartment": p["compartment"]
        }
    })

print(f"✓ Created {len(model['places'])} signal places")

# TRANSITIONS (sensing signals via rate formulas, consuming only ATP/GTP)
transitions = [
    # T1: KinA autophosphorylation (senses Nutrients, KinA; consumes ATP)
    {"id": "T1", "name": "T_KinA_activation", "x": 200, "y": 300, "type": "stochastic",
     "rate_function": "0.0001 * KinA_kinase * (1 / (1 + Nutrients**2)) * ATP_pool / (50 + ATP_pool)"},
    
    # T2: Spo0F phosphorylation (senses KinA_P, Spo0F)
    {"id": "T2", "name": "T_Spo0F_phosphorylation", "x": 600, "y": 300, "type": "stochastic",
     "rate_function": "0.001 * KinA_P * Spo0F / (10 + Spo0F)"},
    
    # T3: Spo0F dephosphorylation (senses Spo0F_P, RapA)
    {"id": "T3", "name": "T_Spo0F_dephosphorylation", "x": 800, "y": 250, "type": "stochastic",
     "rate_function": "0.0005 * Spo0F_P * RapA / (5 + RapA)"},
    
    # T4: Spo0A phosphorylation (senses Spo0F_P, Spo0A, Spo0B)
    {"id": "T4", "name": "T_Spo0A_phosphorylation", "x": 1000, "y": 300, "type": "stochastic",
     "rate_function": "0.0008 * Spo0F_P * Spo0A * Spo0B / (5 + Spo0B)"},
    
    # T5: Spo0A dephosphorylation
    {"id": "T5", "name": "T_Spo0A_dephosphorylation", "x": 1200, "y": 250, "type": "stochastic",
     "rate_function": "0.0001 * Spo0A_P"},
    
    # T6: SigmaH transcription (senses Spo0A_P; consumes ATP)
    {"id": "T6", "name": "T_sigmaH_transcription", "x": 100, "y": 400, "type": "stochastic",
     "rate_function": "0.0001 * Spo0A_P**4 / (50 + Spo0A_P**4) * ATP_pool / (100 + ATP_pool)"},
    
    # T7: Septum formation (senses SigmaH, Cell_density; consumes ATP, GTP)
    {"id": "T7", "name": "T_septation", "x": 400, "y": 600, "type": "stochastic",
     "rate_function": "0.00005 * SigmaH**2 * Cell_density * ATP_pool / (200 + ATP_pool) * GTP_pool / (100 + GTP_pool)"},
    
    # T8: SigmaF activation (senses Septum; consumes ATP)
    {"id": "T8", "name": "T_sigmaF_activation", "x": 200, "y": 800, "type": "stochastic",
     "rate_function": "0.0002 * Septum * ATP_pool / (50 + ATP_pool)"},
    
    # T9: SigmaE activation (senses SigmaF, Septum; consumes GTP)
    {"id": "T9", "name": "T_sigmaE_activation", "x": 600, "y": 800, "type": "stochastic",
     "rate_function": "0.0002 * SigmaF * Septum * GTP_pool / (50 + GTP_pool)"},
    
    # T10: SigmaE-SigmaF feedback (senses both; consumes ATP)
    {"id": "T10", "name": "T_sigmaE_feedback", "x": 400, "y": 900, "type": "stochastic",
     "rate_function": "0.0001 * SigmaE * SigmaF * ATP_pool / (100 + ATP_pool)"},
    
    # T11: SigmaG transcription (senses SigmaF, SigmaE; consumes ATP)
    {"id": "T11", "name": "T_sigmaG_transcription", "x": 200, "y": 1000, "type": "stochastic",
     "rate_function": "0.00008 * SigmaF * SigmaE * ATP_pool / (150 + ATP_pool)"},
    
    # T12: SigmaK transcription (senses SigmaE; consumes ATP)
    {"id": "T12", "name": "T_sigmaK_transcription", "x": 600, "y": 1000, "type": "stochastic",
     "rate_function": "0.00008 * SigmaE * ATP_pool / (150 + ATP_pool)"},
    
    # T13: Forespore formation (senses SigmaF, Septum; consumes ATP)
    {"id": "T13", "name": "T_forespore_formation", "x": 200, "y": 1200, "type": "stochastic",
     "rate_function": "0.0001 * SigmaF * Septum * ATP_pool / (100 + ATP_pool)"},
    
    # T14: Mother cell formation (senses SigmaE, Septum; consumes ATP)
    {"id": "T14", "name": "T_mother_cell_formation", "x": 600, "y": 1200, "type": "stochastic",
     "rate_function": "0.0001 * SigmaE * Septum * ATP_pool / (100 + ATP_pool)"},
    
    # T15: Cortex synthesis (senses SigmaG, Forespore; MASSIVE ATP consumption)
    {"id": "T15", "name": "T_cortex_synthesis", "x": 200, "y": 1400, "type": "continuous",
     "rate_function": "0.00005 * SigmaG * Forespore * ATP_pool / (300 + ATP_pool)"},
    
    # T16: Inner coat synthesis (senses SigmaK, Mother_cell; consumes ATP, GTP)
    {"id": "T16", "name": "T_inner_coat_synthesis", "x": 600, "y": 1400, "type": "continuous",
     "rate_function": "0.00004 * SigmaK * Mother_cell * ATP_pool / (200 + ATP_pool) * GTP_pool / (100 + GTP_pool)"},
    
    # T17: Outer coat synthesis (senses Inner_coat, SigmaK; consumes GTP)
    {"id": "T17", "name": "T_outer_coat_synthesis", "x": 800, "y": 1400, "type": "continuous",
     "rate_function": "0.00003 * Inner_coat * SigmaK * GTP_pool / (150 + GTP_pool)"},
    
    # T18: Spore maturation (senses Cortex, Outer_coat; consumes ATP)
    {"id": "T18", "name": "T_spore_maturation", "x": 400, "y": 1600, "type": "stochastic",
     "rate_function": "0.0005 * Cortex * Outer_coat * ATP_pool / (50 + ATP_pool)"},
    
    # CONTINUOUS SOURCES (produce signal levels)
    {"id": "T19", "name": "Source_nutrient_depletion", "x": 500, "y": 50, "type": "continuous",
     "rate_function": "0.1", "is_source": True},
    
    {"id": "T20", "name": "Source_ATP_regen", "x": 100, "y": 50, "type": "continuous",
     "rate_function": "0.5 * Nutrients / (10 + Nutrients)", "is_source": True},
    
    {"id": "T21", "name": "Source_GTP_regen", "x": 300, "y": 50, "type": "continuous",
     "rate_function": "0.3 * Nutrients / (10 + Nutrients)", "is_source": True},
    
    {"id": "T22", "name": "Source_cell_density", "x": 700, "y": 50, "type": "continuous",
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

# ARCS: signal_flow for ATP/GTP consumption, normal for signal production
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

# SIGNAL_FLOW ARCS: ATP/GTP consumption (hierarchical control)
# T1: KinA activation consumes ATP
add_arc('P1', 'T1', 'signal_flow', 5)
add_arc('T1', 'P6')  # Produces KinA_P

# T2: Spo0F phosphorylation (signal sensing only, no ATP)
add_arc('T2', 'P8')  # Produces Spo0F_P

# T3: Spo0F dephosphorylation (reverse)
add_arc('T3', 'P7')  # Produces Spo0F

# T4: Spo0A phosphorylation
add_arc('T4', 'P11')  # Produces Spo0A_P

# T5: Spo0A dephosphorylation
add_arc('T5', 'P10')  # Produces Spo0A

# T6: SigmaH transcription consumes ATP
add_arc('P1', 'T6', 'signal_flow', 10)
add_arc('T6', 'P13')  # Produces SigmaH

# T7: Septation consumes ATP and GTP
add_arc('P1', 'T7', 'signal_flow', 50)
add_arc('P2', 'T7', 'signal_flow', 50)
add_arc('T7', 'P14')  # Produces Septum

# T8: SigmaF activation consumes ATP
add_arc('P1', 'T8', 'signal_flow', 15)
add_arc('T8', 'P15')  # Produces SigmaF

# T9: SigmaE activation consumes GTP
add_arc('P2', 'T9', 'signal_flow', 15)
add_arc('T9', 'P16')  # Produces SigmaE

# T10: Feedback consumes ATP
add_arc('P1', 'T10', 'signal_flow', 10)
add_arc('T10', 'P15')  # Amplifies SigmaF

# T11: SigmaG transcription consumes ATP
add_arc('P1', 'T11', 'signal_flow', 20)
add_arc('T11', 'P17')  # Produces SigmaG

# T12: SigmaK transcription consumes ATP
add_arc('P1', 'T12', 'signal_flow', 20)
add_arc('T12', 'P18')  # Produces SigmaK

# T13: Forespore formation consumes ATP
add_arc('P1', 'T13', 'signal_flow', 30)
add_arc('T13', 'P19')  # Produces Forespore

# T14: Mother cell formation consumes ATP
add_arc('P1', 'T14', 'signal_flow', 30)
add_arc('T14', 'P20')  # Produces Mother_cell

# T15: Cortex synthesis - MASSIVE ATP consumption (hierarchical preemption test!)
add_arc('P1', 'T15', 'signal_flow', 100)
add_arc('T15', 'P21')  # Produces Cortex

# T16: Inner coat synthesis consumes ATP and GTP
add_arc('P1', 'T16', 'signal_flow', 80)
add_arc('P2', 'T16', 'signal_flow', 20)
add_arc('T16', 'P22')  # Produces Inner_coat

# T17: Outer coat synthesis consumes GTP
add_arc('P2', 'T17', 'signal_flow', 50)
add_arc('T17', 'P23')  # Produces Outer_coat

# T18: Spore maturation consumes ATP
add_arc('P1', 'T18', 'signal_flow', 20)
add_arc('T18', 'P24')  # Produces Mature_spore

# CONTINUOUS SOURCES (produce signals)
add_arc('P3', 'T19')  # Nutrients depleted
add_arc('T20', 'P1')  # ATP regeneration
add_arc('T21', 'P2')  # GTP regeneration
add_arc('T22', 'P4')  # Cell density increases

model["arcs"] = arcs

signal_flow_count = sum(1 for a in arcs if a['arc_type'] == 'signal_flow')
normal_count = sum(1 for a in arcs if a['arc_type'] == 'normal')

print(f"✓ Created {len(arcs)} arcs ({signal_flow_count} signal_flow, {normal_count} normal)")

# Save
with open('workspace/projects/My_Project/thermodynamics/bacillus_sporulation.shy', 'w') as f:
    json.dump(model, f, indent=2)

print(f"\n✅ SIGNAL HIERARCHY MODEL COMPLETE")
print(f"   ALL places are signal places: {len(model['places'])}")
print(f"   Transitions: {len(model['transitions'])}")
print(f"   Signal_flow arcs (ATP/GTP consumption): {signal_flow_count}")
print(f"   Normal arcs (signal production): {normal_count}")
print(f"\n   KEY FEATURES:")
print(f"   - All regulatory components are signal places")
print(f"   - ATP/GTP use signal_flow arcs (hierarchical preemption)")
print(f"   - Other signals sensed via rate formulas only")
print(f"   - Thermodynamic stress test: 500+ ATP consumed for sporulation")
print(f"\n   File: workspace/projects/My_Project/thermodynamics/bacillus_sporulation.shy")
