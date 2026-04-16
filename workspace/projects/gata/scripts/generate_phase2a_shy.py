#!/usr/bin/env python3
"""
Generate Phase 2A .shy file from model structure

Creates a complete ShyPN model file with proper visual layout
"""

import json
import datetime
from pathlib import Path

def load_model_structure():
    """Load the generated model structure"""
    base_dir = Path(__file__).parent.parent
    structure_file = base_dir / 'models' / 'phase2a_model_structure.json'
    
    with open(structure_file, 'r') as f:
        return json.load(f)

def generate_place_positions(places):
    """Generate x,y positions for places - uses user-edited layout from GUI"""
    
    # Exact positions from edited model (manually arranged in GUI)
    # GATA1 pathway on LEFT (negative x), PU1 pathway on RIGHT (positive x)
    position_map = {
        # Layer 1: Extracellular signals
        'EPO_external': (-230.0, 240.0),
        'GCSF_external': (740.0, 230.0),
        
        # Layer 2: Receptors (EPOR on left, GCSFR on right)
        'EPOR_free': (-230.0, 80.0),
        'EPOR_bound': (-240.0, -100.0),
        'EPOR_internalized': (30.0, -100.0),
        'GCSFR_free': (720.0, 70.0),
        'GCSFR_bound': (720.0, -100.0),
        'GCSFR_internalized': (400.0, -100.0),
        
        # Layer 3: Genes
        'GATA1_Gene': (-350.0, 240.0),
        'PU1_Gene': (880.0, 220.0),
        
        # Layer 4: Nuclear mRNA
        'GATA1_mRNA_nuc': (-60.0, 310.0),
        'PU1_mRNA_nuc': (530.0, 300.0),
        
        # Layer 5: Cytoplasmic mRNA
        'GATA1_mRNA_cyto': (-220.0, 470.0),
        'PU1_mRNA_cyto': (740.0, 450.0),
        
        # Layer 6: Cytoplasmic proteins
        'GATA1_Protein_cyto': (-100.0, 800.0),
        'PU1_Protein_cyto': (690.0, 810.0),
        
        # Layer 7: Nuclear proteins
        'GATA1_Protein_nuc': (-280.0, 720.0),
        'PU1_Protein_nuc': (830.0, 760.0),
        
        # Layer 8: Metabolic pools
        'ATP': (90.0, 1120.0),
        'ADP': (110.0, 1290.0),
        'GTP': (120.0, 870.0),
        'GDP': (420.0, 890.0),
        'Pi': (-140.0, 1210.0),
    }
    
    # Map place IDs to positions using place names
    positions = {}
    for place in places:
        place_name = place['name']
        if place_name in position_map:
            positions[place['id']] = position_map[place_name]
        else:
            # Fallback for any unmapped places
            positions[place['id']] = (250, 500)
    
    return positions

def generate_shy_places(places, positions):
    """Generate places in .shy format"""
    shy_places = []
    
    for place in places:
        pos = positions.get(place['id'], (250, 500))  # Default position
        
        # Determine color based on compartment/type
        if place['compartment'] == 'extracellular' or 'external' in place['name']:
            border_color = [0.0, 0.0, 1.0]  # Blue for signals
            is_signal = True
        elif place['compartment'] == 'membrane' or 'receptor' in place['name'].lower():
            border_color = [1.0, 0.5, 0.0]  # Orange for receptors
            is_signal = False
        elif place['layer'] == 8:  # Metabolic
            border_color = [0.8, 0.0, 0.8]  # Purple for metabolism
            is_signal = False
        else:
            border_color = [0.0, 0.0, 0.0]  # Black for regular
            is_signal = False
        
        shy_place = {
            "id": place['id'],
            "name": place['name'],
            "label": place['name'],
            "object_type": "place",
            "x": pos[0],
            "y": pos[1],
            "radius": 40.0,
            "marking": place['initial'],
            "initial_marking": place['initial'],
            "capacity": "Infinity",
            "border_color": border_color,
            "border_width": 3.0,
            "is_catalyst": False,
            "is_signal_place": is_signal,
            "signal_type": "quorum" if is_signal else None,
            "is_compartment_place": False,
            "is_regulatory_place": False,
            "diffusion_coefficient": None,
            "boundary_type": None,
            "gradient_vector": None,
            "compartment_volume": None,
            "neighbor_compartments": [],
            "spatial_position": None,
            "compartment": place.get('compartment')  # Add biological compartment assignment
        }
        
        shy_places.append(shy_place)
    
    return shy_places

def generate_transition_positions(transitions, place_positions, places):
    """Generate x,y positions for transitions - using exact coordinates from edited layout"""
    # Map transition names to exact (x, y) positions from user's edited layout
    transition_map = {
        'EPO_EPOR_binding': (-70.0, 80.0),
        'GCSF_GCSFR_binding': (550.0, 70.0),
        'EPOR_activation': (-230.0, -50.0),
        'GCSFR_activation': (720.0, -50.0),
        'EPOR_dissociation': (-70.0, 60.0),
        'GCSFR_dissociation': (550.0, 50.0),
        'GATA1_transcription': (-290.0, 400.0),
        'PU1_transcription': (830.0, 380.0),
        'GATA1_mRNA_nuclear_export': (-350.0, 540.0),
        'PU1_mRNA_nuclear_export': (880.0, 570.0),
        'GATA1_translation': (-350.0, 660.0),
        'PU1_translation': (880.0, 690.0),
        'GATA1_protein_nuclear_import': (-430.0, 940.0),
        'PU1_protein_nuclear_import': (940.0, 940.0),
        'GATA1_mRNA_nuc_degradation': (-310.0, 510.0),
        'PU1_mRNA_nuc_degradation': (820.0, 530.0),
        'GATA1_mRNA_cyt_degradation': (-310.0, 640.0),
        'PU1_mRNA_cyt_degradation': (820.0, 660.0),
        'GATA1_Protein_cyt_degradation': (-310.0, 770.0),
        'PU1_Protein_cyt_degradation': (820.0, 780.0),
        'GATA1_Protein_nuc_degradation': (-310.0, 910.0),
        'PU1_Protein_nuc_degradation': (820.0, 900.0),
        'EPOR_synthesis': (30.0, 80.0),
        'GCSFR_synthesis': (400.0, 70.0),
        'EPOR_degradation': (50.0, 20.0),
        'GCSFR_degradation': (420.0, 20.0),
        'ATP_synthesis': (0.0, 1210.0),
        'GTP_regeneration': (220.0, 1190.0),
    }
    
    # Create a name lookup for transitions
    name_to_id = {t['name']: t['id'] for t in transitions}
    
    # Map IDs to positions
    positions = {}
    for trans in transitions:
        trans_name = trans['name']
        trans_id = trans['id']
        
        if trans_name in transition_map:
            positions[trans_id] = transition_map[trans_name]
        else:
            # Fallback to center if transition not in map
            positions[trans_id] = (250, 500)
    
    return positions

def generate_shy_transitions(transitions, positions):
    """Generate transitions in .shy format"""
    shy_transitions = []
    
    for trans in transitions:
        pos = positions.get(trans['id'], (250, 500))
        
        # Determine transition type and color by layer
        layer = trans.get('layer', '')
        trans_name = trans.get('name', '')
        
        if 'signal' in layer:
            fill_color = [0.0, 0.0, 1.0]
            trans_type = "stochastic"
        elif 'receptor' in layer or 'metabolism' in layer:
            fill_color = [1.0, 0.5, 0.0]
            trans_type = "continuous"
        elif 'degradation' in layer:
            fill_color = [0.0, 0.8, 0.0]
            trans_type = "continuous"
        elif 'transcription' in layer:
            fill_color = [0.0, 0.0, 0.0]
            trans_type = "stochastic"
        else:
            fill_color = [0.0, 0.0, 0.0]
            trans_type = "stochastic"
        
        # Check if transition is environment-aware (reads places in rate function)
        is_env_aware = 'transcription' in trans_name.lower() or 'binding' in trans_name.lower()
        
        # Extract signal places for environment-aware transitions
        signal_places = []
        if 'transcription' in trans_name.lower():
            if 'GATA1' in trans_name:
                signal_places = ['P1', 'P17', 'P18']  # EPO, GATA1_nuc, PU1_nuc
            elif 'PU1' in trans_name:
                signal_places = ['P2', 'P17', 'P18']  # GCSF, GATA1_nuc, PU1_nuc
        
        shy_trans = {
            "id": trans['id'],
            "name": trans['name'],
            "label": trans['name'],
            "object_type": "transition",
            "x": pos[0],
            "y": pos[1],
            "width": 60.0,
            "height": 20.0,
            "horizontal": True,
            "enabled": True,
            "fill_color": fill_color,
            "border_color": fill_color,
            "border_width": 3.0,
            "transition_type": trans_type,
            "priority": 0,
            "firing_policy": "race",
            "is_source": False,
            "is_sink": 'degradation' in trans['name'].lower() or 'clearance' in trans['name'].lower(),
            "guard": "1",
            "rate_function": trans['rate'],
            "properties": {
                "rate_function": trans['rate']
            },
            "is_environment_aware": is_env_aware
        }
        
        if signal_places:
            shy_trans['signal_places'] = signal_places
        
        shy_transitions.append(shy_trans)
    
    return shy_transitions

def generate_arcs(transitions, places):
    """Generate arcs connecting places and transitions"""
    arcs = []
    arc_id = 1
    
    # Create place name lookup
    place_id_to_name = {p['id']: p['name'] for p in places}
    place_name_to_id = {p['name']: p['id'] for p in places}
    
    for trans in transitions:
        trans_id = trans['id']
        trans_name = trans['name']
        rate_func = trans.get('rate', '')
        
        # Input arcs (place → transition)
        for place_id in trans.get('reactants', []):
            arcs.append({
                "id": f"A{arc_id}",
                "name": f"A{arc_id}",
                "label": "",
                "object_type": "arc",
                "arc_type": "normal",
                "source_id": place_id,
                "source_type": "place",
                "target_id": trans_id,
                "target_type": "transition",
                "weight": 1.0,
                "threshold": None,
                "color": [0.0, 0.0, 0.0],
                "width": 3.0,
                "control_points": []
            })
            arc_id += 1
        
        # Catalyst arcs (test arcs - don't consume)
        for place_id in trans.get('catalysts', []):
            arcs.append({
                "id": f"A{arc_id}",
                "name": f"A{arc_id}",
                "label": "",
                "object_type": "arc",
                "arc_type": "test",
                "source_id": place_id,
                "source_type": "place",
                "target_id": trans_id,
                "target_type": "transition",
                "weight": 1.0,
                "threshold": None,
                "color": [0.0, 0.0, 1.0],
                "width": 3.0,
                "control_points": [],
                "consumes": False
            })
            arc_id += 1
        
        # Special handling for transcription transitions - add test arcs for rate dependencies
        if 'transcription' in trans_name.lower():
            # GATA1 transcription needs: EPO signal, GATA1_nuc (self), PU1_nuc (repressor)
            if 'GATA1' in trans_name:
                # EPO signal input
                if 'EPO' in rate_func or 'EPO_Signal' in rate_func:
                    epo_id = place_name_to_id.get('EPO_external')
                    if epo_id and epo_id not in trans.get('catalysts', []):
                        arcs.append({
                            "id": f"A{arc_id}",
                            "name": f"A{arc_id}",
                            "label": "",
                            "object_type": "arc",
                            "arc_type": "test",
                            "source_id": epo_id,
                            "source_type": "place",
                            "target_id": trans_id,
                            "target_type": "transition",
                            "weight": 1.0,
                            "threshold": None,
                            "color": [0.0, 0.0, 1.0],
                            "width": 3.0,
                            "control_points": [],
                            "consumes": False
                        })
                        arc_id += 1
                
                # GATA1 self-activation feedback
                gata1_nuc_id = place_name_to_id.get('GATA1_Protein_nuc')
                if gata1_nuc_id and gata1_nuc_id not in trans.get('catalysts', []):
                    arcs.append({
                        "id": f"A{arc_id}",
                        "name": f"A{arc_id}",
                        "label": "",
                        "object_type": "arc",
                        "arc_type": "test",
                        "source_id": gata1_nuc_id,
                        "source_type": "place",
                        "target_id": trans_id,
                        "target_type": "transition",
                        "weight": 1.0,
                        "threshold": None,
                        "color": [1.0, 0.0, 0.0],  # Red for self-activation
                        "width": 3.0,
                        "control_points": [],
                        "consumes": False
                    })
                    arc_id += 1
                
                # PU1 cross-repression
                pu1_nuc_id = place_name_to_id.get('PU1_Protein_nuc')
                if pu1_nuc_id and pu1_nuc_id not in trans.get('catalysts', []):
                    arcs.append({
                        "id": f"A{arc_id}",
                        "name": f"A{arc_id}",
                        "label": "",
                        "object_type": "arc",
                        "arc_type": "test",
                        "source_id": pu1_nuc_id,
                        "source_type": "place",
                        "target_id": trans_id,
                        "target_type": "transition",
                        "weight": 1.0,
                        "threshold": None,
                        "color": [1.0, 0.0, 0.0],  # Red for inhibition
                        "width": 3.0,
                        "control_points": [],
                        "consumes": False
                    })
                    arc_id += 1
            
            # PU1 transcription needs: GCSF signal, PU1_nuc (self), GATA1_nuc (repressor)
            elif 'PU1' in trans_name or 'PU.1' in trans_name:
                # GCSF signal input
                if 'GCSF' in rate_func or 'GCSF_Signal' in rate_func:
                    gcsf_id = place_name_to_id.get('GCSF_external')
                    if gcsf_id and gcsf_id not in trans.get('catalysts', []):
                        arcs.append({
                            "id": f"A{arc_id}",
                            "name": f"A{arc_id}",
                            "label": "",
                            "object_type": "arc",
                            "arc_type": "test",
                            "source_id": gcsf_id,
                            "source_type": "place",
                            "target_id": trans_id,
                            "target_type": "transition",
                            "weight": 1.0,
                            "threshold": None,
                            "color": [0.0, 0.0, 1.0],
                            "width": 3.0,
                            "control_points": [],
                            "consumes": False
                        })
                        arc_id += 1
                
                # PU1 self-activation feedback
                pu1_nuc_id = place_name_to_id.get('PU1_Protein_nuc')
                if pu1_nuc_id and pu1_nuc_id not in trans.get('catalysts', []):
                    arcs.append({
                        "id": f"A{arc_id}",
                        "name": f"A{arc_id}",
                        "label": "",
                        "object_type": "arc",
                        "arc_type": "test",
                        "source_id": pu1_nuc_id,
                        "source_type": "place",
                        "target_id": trans_id,
                        "target_type": "transition",
                        "weight": 1.0,
                        "threshold": None,
                        "color": [1.0, 0.0, 0.0],  # Red for self-activation
                        "width": 3.0,
                        "control_points": [],
                        "consumes": False
                    })
                    arc_id += 1
                
                # GATA1 cross-repression
                gata1_nuc_id = place_name_to_id.get('GATA1_Protein_nuc')
                if gata1_nuc_id and gata1_nuc_id not in trans.get('catalysts', []):
                    arcs.append({
                        "id": f"A{arc_id}",
                        "name": f"A{arc_id}",
                        "label": "",
                        "object_type": "arc",
                        "arc_type": "test",
                        "source_id": gata1_nuc_id,
                        "source_type": "place",
                        "target_id": trans_id,
                        "target_type": "transition",
                        "weight": 1.0,
                        "threshold": None,
                        "color": [1.0, 0.0, 0.0],  # Red for inhibition
                        "width": 3.0,
                        "control_points": [],
                        "consumes": False
                    })
                    arc_id += 1
        
        # Output arcs (transition → place)
        for place_id in trans.get('products', []):
            arcs.append({
                "id": f"A{arc_id}",
                "name": f"A{arc_id}",
                "label": "",
                "object_type": "arc",
                "arc_type": "normal",
                "source_id": trans_id,
                "source_type": "transition",
                "target_id": place_id,
                "target_type": "place",
                "weight": 1.0,
                "threshold": None,
                "color": [0.0, 0.0, 0.0],
                "width": 3.0,
                "control_points": []
            })
            arc_id += 1
    
    return arcs

def generate_shy_file(model_structure):
    """Generate complete .shy file"""
    
    places = model_structure['places']
    transitions = model_structure['transitions']
    
    # Generate positions
    place_positions = generate_place_positions(places)
    transition_positions = generate_transition_positions(transitions, place_positions, places)
    
    # Generate .shy components
    shy_places = generate_shy_places(places, place_positions)
    shy_transitions = generate_shy_transitions(transitions, transition_positions)
    arcs = generate_arcs(transitions, places)
    
    # Build complete .shy structure
    shy_model = {
        "version": "2.0",
        "metadata": {
            "created": datetime.datetime.now().isoformat(),
            "source": "programmatic",
            "model_type": "Petri Net",
            "model_name": model_structure['metadata']['name'],
            "model_version": model_structure['metadata']['version'],
            "description": model_structure['metadata']['description'],
            "object_counts": {
                "places": len(shy_places),
                "transitions": len(shy_transitions),
                "arcs": len(arcs),
                "modules": 0
            }
        },
        "view_state": {
            "zoom": 0.6,
            "pan_x": 300,
            "pan_y": 100,
            "transformations": {
                "rotation": {
                    "type": "rotation",
                    "angle_degrees": 0.0,
                    "enabled": True
                }
            }
        },
        "thermodynamic_settings": {
            "ph": 7.0,
            "temperature": 298.15,
            "ionic_strength": 0.1,
            "tolerance": 0.5,
            "enable_validation": True,
            "preset": "biochemical_standard"
        },
        "compound_mappings": {},
        "places": shy_places,
        "transitions": shy_transitions,
        "arcs": arcs,
        "modules": []
    }
    
    return shy_model

def main():
    """Main generation workflow"""
    
    print("="*70)
    print("Phase 2A .shy File Generator")
    print("="*70)
    print()
    
    # Load model structure
    print("Loading model structure...")
    model_structure = load_model_structure()
    print(f"✓ Loaded: {model_structure['metadata']['name']}")
    print(f"  Places: {len(model_structure['places'])}")
    print(f"  Transitions: {len(model_structure['transitions'])}")
    print()
    
    # Generate .shy file
    print("Generating .shy file...")
    shy_model = generate_shy_file(model_structure)
    print(f"✓ Generated .shy structure")
    print(f"  Places: {len(shy_model['places'])}")
    print(f"  Transitions: {len(shy_model['transitions'])}")
    print(f"  Arcs: {len(shy_model['arcs'])}")
    print()
    
    # Save to file
    output_dir = Path(__file__).parent.parent / 'models'
    output_file = output_dir / 'phase2a_core_enhanced.shy'
    
    with open(output_file, 'w') as f:
        json.dump(shy_model, f, indent=2)
    
    print(f"✓ Saved to: {output_file}")
    print()
    print("="*70)
    print("GENERATION COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Open in ShyPN GUI: File → Open → phase2a_core_enhanced.shy")
    print("2. Review model layout and connections")
    print("3. Configure signal production functions")
    print("4. Run validation simulations")

if __name__ == '__main__':
    main()
