#!/usr/bin/env python3
"""
Diagnose conservation issues in drug discovery model.

This script analyzes:
1. What conservation groups were auto-detected
2. Why drug mass increases by 37.9%
3. Model structure and stoichiometry issues
"""
import sys
import json
sys.path.insert(0, 'src')

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.engine.simulation.controller import SimulationController

def load_model(model_path):
    """Load model from JSON file."""
    with open(model_path) as f:
        model_data = json.load(f)
    
    canvas_manager = ModelCanvasManager()
    
    # Load places
    places = []
    for p_data in model_data.get('places', []):
        place = Place.from_dict(p_data)
        places.append(place)
    places_dict = {p.id: p for p in places}
    
    # Load transitions
    transitions = []
    for t_data in model_data.get('transitions', []):
        trans = Transition.from_dict(t_data)
        transitions.append(trans)
    transitions_dict = {t.id: t for t in transitions}
    
    # Load arcs
    arcs = []
    for a_data in model_data['arcs']:
        arc = Arc.from_dict(a_data, places_dict, transitions_dict)
        arcs.append(arc)
    
    canvas_manager.load_objects(places=places, transitions=transitions, arcs=arcs)
    return canvas_manager

def analyze_stoichiometry(model):
    """Analyze stoichiometry for each transition."""
    print("=" * 80)
    print("STOICHIOMETRY ANALYSIS")
    print("=" * 80)
    
    for transition in model.transitions:
        # Get input and output arcs
        input_arcs = [a for a in model.arcs if a.target_id == transition.id]
        output_arcs = [a for a in model.arcs if a.source_id == transition.id]
        
        # Calculate net stoichiometry
        input_weight = sum(a.weight for a in input_arcs)
        output_weight = sum(a.weight for a in output_arcs)
        net = output_weight - input_weight
        
        if abs(net) > 0.001:  # Unbalanced stoichiometry
            print(f"\n⚠️  {transition.name} (ID: {transition.id})")
            print(f"   Inputs:  {input_weight:.3f} tokens")
            print(f"   Outputs: {output_weight:.3f} tokens")
            print(f"   NET:     {net:+.3f} tokens per firing")
            
            print(f"   Input arcs:")
            for arc in input_arcs:
                place = next((p for p in model.places if p.id == arc.source_id), None)
                print(f"     - {place.name if place else arc.source_id}: {arc.weight:.2f}")
            
            print(f"   Output arcs:")
            for arc in output_arcs:
                place = next((p for p in model.places if p.id == arc.target_id), None)
                print(f"     - {place.name if place else arc.target_id}: {arc.weight:.2f}")

def analyze_drug_pathways(model):
    """Analyze drug-related places and transitions."""
    print("\n" + "=" * 80)
    print("DRUG PATHWAY ANALYSIS")
    print("=" * 80)
    
    # Find drug-related places
    drug_places = [p for p in model.places if 'drug' in p.name.lower() or 'macrocycle' in p.name.lower()]
    
    print(f"\nDrug-related places ({len(drug_places)}):")
    for place in drug_places:
        print(f"  {place.name:40s}: {place.tokens:.6f} mM (initial)")
    
    total_drug = sum(p.tokens for p in drug_places)
    print(f"\nTotal drug mass (initial): {total_drug:.6f} mM")
    
    # Find transitions that touch drug places
    drug_transitions = set()
    for place in drug_places:
        for arc in model.arcs:
            if arc.source_id == place.id or arc.target_id == place.id:
                # Find the transition
                trans_id = arc.target_id if arc.source_id == place.id else arc.source_id
                trans = next((t for t in model.transitions if t.id == trans_id), None)
                if trans:
                    drug_transitions.add(trans)
    
    print(f"\nTransitions affecting drug species ({len(drug_transitions)}):")
    for trans in drug_transitions:
        # Check stoichiometry for drug species
        input_arcs = [a for a in model.arcs if a.target_id == trans.id and any(p.id == a.source_id for p in drug_places)]
        output_arcs = [a for a in model.arcs if a.source_id == trans.id and any(p.id == a.target_id for p in drug_places)]
        
        drug_input = sum(a.weight for a in input_arcs)
        drug_output = sum(a.weight for a in output_arcs)
        drug_net = drug_output - drug_input
        
        if abs(drug_net) > 0.001:
            print(f"\n  ⚠️  {trans.name}:")
            print(f"      Drug in:  {drug_input:.3f}")
            print(f"      Drug out: {drug_output:.3f}")
            print(f"      NET:      {drug_net:+.3f} drug tokens per firing")

def test_auto_detection(model):
    """Test what conservation groups are auto-detected."""
    print("\n" + "=" * 80)
    print("AUTO-DETECTION TEST")
    print("=" * 80)
    
    # Create controller (triggers auto-detection)
    controller = SimulationController(model, verbose=False)
    
    print(f"\nAuto-conservation enabled: {controller.auto_conservation_enabled}")
    print(f"Conservation groups before simulation: {len(controller.conservation_enforcer.conservation_groups)}")
    
    # Trigger auto-detection by running one step
    controller.settings.duration = 1.0
    controller.settings.dt = 0.01
    controller.step(0.01)
    
    # Check what was detected
    print(f"\nConservation groups after first step: {len(controller.conservation_enforcer.conservation_groups)}")
    
    if controller.conservation_enforcer.conservation_groups:
        print("\nDetected conservation groups:")
        for name, group in controller.conservation_enforcer.conservation_groups.items():
            print(f"\n  {name}:")
            print(f"    Expected total: {group.expected_total:.6f}")
            print(f"    Places ({len(group.place_ids)}):")
            for place_id in group.place_ids:
                place = next((p for p in model.places if p.id == place_id), None)
                if place:
                    print(f"      - {place.name} (ID: {place_id})")
    else:
        print("\n⚠️  NO conservation groups were auto-detected!")
        print("    This means the drug species are NOT in a closed cycle")
        print("    (i.e., there are sources or sinks)")

def main():
    model_path = 'workspace/projects/My_Project/drug_discovery/.project.shy'
    
    print("=" * 80)
    print("DRUG DISCOVERY MODEL CONSERVATION DIAGNOSTIC")
    print("=" * 80)
    print(f"\nLoading model: {model_path}")
    
    model = load_model(model_path)
    
    print(f"\nModel structure:")
    print(f"  Places:      {len(model.places)}")
    print(f"  Transitions: {len(model.transitions)}")
    print(f"  Arcs:        {len(model.arcs)}")
    
    # Run analyses
    analyze_stoichiometry(model)
    analyze_drug_pathways(model)
    test_auto_detection(model)
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS SUMMARY")
    print("=" * 80)
    print("\nPossible causes of 37.9% drug mass increase:")
    print("  1. Unbalanced stoichiometry (transitions create more than they consume)")
    print("  2. Drug species not in closed cycle (auto-detection skipped them)")
    print("  3. Arc weights incorrectly set (e.g., weight=2 output, weight=1 input)")
    print("  4. Signal flow arcs incorrectly modeled as normal arcs")
    
    print("\nPossible causes of 0.711% energy loss:")
    print("  1. Energy species not detected as closed cycle")
    print("  2. Energy species have sources/sinks (correct behavior)")
    print("  3. Auto-detection algorithm missed the energy cycle")

if __name__ == '__main__':
    main()
