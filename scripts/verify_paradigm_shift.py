#!/usr/bin/env python3
"""Verify the paradigm shift: Transitions as hubs, Places orbit.

This script checks:
1. Test model structure (3 hub transitions, 18 orbiting places)
2. Mass assignment (transitions should have high mass)
3. Arc directions (Place → Transition biological flow)
4. Arc weights (all 1.0, no manipulation)
5. Final layout quality (places spread around transitions)
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.layout.sscc.hub_based_mass_assigner import HubBasedMassAssigner
from shypn.layout.sscc.scc_detector import SCCDetector
from shypn.layout.sscc.solar_system_layout_engine import SolarSystemLayoutEngine
import math


def verify_paradigm_shift():
    """Verify new paradigm implementation."""
    
    print("="*80)
    print("PARADIGM SHIFT VERIFICATION")
    print("="*80)
    print()
    
    # Load test model
    model_path = "workspace/Test_flow/model/hub_constellation.shy"
    print(f"Loading: {model_path}")
    
    document = DocumentModel.load_from_file(model_path)
    places = document.places
    transitions = document.transitions
    arcs = document.arcs
    
    print(f"  ✓ Loaded: {len(places)} places, {len(transitions)} transitions, {len(arcs)} arcs")
    print()
    
    # Verify model structure
    print("Model Structure:")
    print("-"*80)
    
    # Check transition degrees (should be 6 each - hub transitions)
    transition_degrees = {}
    for t in transitions:
        in_degree = sum(1 for arc in arcs if arc.target.id == t.id)
        out_degree = sum(1 for arc in arcs if arc.source.id == t.id)
        total = in_degree + out_degree
        transition_degrees[t.id] = (in_degree, out_degree, total)
        print(f"  Transition {t.id} ({t.label}): in={in_degree}, out={out_degree}, total={total}")
    
    print()
    
    # Check place degrees (should be 1 each - orbiting places)
    place_degrees = {}
    for p in places:
        in_degree = sum(1 for arc in arcs if arc.target.id == p.id)
        out_degree = sum(1 for arc in arcs if arc.source.id == p.id)
        total = in_degree + out_degree
        place_degrees[p.id] = (in_degree, out_degree, total)
    
    print(f"  Place degree range: {min(d[2] for d in place_degrees.values())}-{max(d[2] for d in place_degrees.values())}")
    print()
    
    # Verify arc directions and weights
    print("Arc Analysis:")
    print("-"*80)
    
    p_to_t_count = 0
    t_to_p_count = 0
    weights = []
    
    for arc in arcs:
        is_place_source = any(p.id == arc.source.id for p in places)
        is_transition_target = any(t.id == arc.target.id for t in transitions)
        
        if is_place_source and is_transition_target:
            p_to_t_count += 1
        else:
            t_to_p_count += 1
        
        weights.append(arc.weight)
    
    print(f"  Place → Transition arcs: {p_to_t_count}")
    print(f"  Transition → Place arcs: {t_to_p_count}")
    print(f"  Arc weight range: {min(weights):.1f}-{max(weights):.1f}")
    print(f"  Arc weight average: {sum(weights)/len(weights):.1f}")
    print()
    
    # Check paradigm correctness
    if p_to_t_count == len(arcs) and min(weights) == max(weights) == 1.0:
        print("  ✅ CORRECT PARADIGM:")
        print("     - All arcs: Place → Transition (biological flow)")
        print("     - All weights: 1.0 (no manipulation)")
    else:
        print("  ⚠️ PARADIGM ISSUE:")
        if p_to_t_count != len(arcs):
            print(f"     - Found {t_to_p_count} Transition→Place arcs (should be 0)")
        if min(weights) != 1.0 or max(weights) != 1.0:
            print(f"     - Weights not 1.0 (found {min(weights):.1f}-{max(weights):.1f})")
    print()
    
    # Verify mass assignment
    print("Mass Assignment:")
    print("-"*80)
    
    # Build graph for SCC detection
    from shypn.layout.sscc.graph_builder import GraphBuilder
    graph_builder = GraphBuilder()
    graph = graph_builder.build_graph(places, transitions, arcs)
    id_to_object = graph_builder.id_to_object
    
    # Detect SCCs
    detector = SCCDetector()
    sccs = detector.find_sccs(graph, id_to_object)
    
    # Assign masses
    assigner = HubBasedMassAssigner()
    masses = assigner.assign_masses(sccs, places, transitions, arcs)
    
    # Show transition masses (should be HIGH for hubs)
    print("  Transition masses:")
    for t in sorted(transitions, key=lambda x: x.id):
        mass = masses[t.id]
        degree = transition_degrees[t.id][2]
        print(f"    {t.label}: mass={mass:.1f} (degree={degree})")
    
    print()
    print(f"  Place mass range: {min(masses[p.id] for p in places):.1f}-{max(masses[p.id] for p in places):.1f}")
    print()
    
    # Check if transitions got hub mass
    hub_transitions = [t for t in transitions if masses[t.id] >= 500.0]
    if hub_transitions:
        print(f"  ✅ HUB TRANSITIONS DETECTED: {len(hub_transitions)}/3")
        print(f"     Transitions with high mass (≥500): {[t.label for t in hub_transitions]}")
    else:
        print(f"  ⚠️ NO HUB TRANSITIONS (all masses < 500)")
        print(f"     Expected 3 transitions with mass=1000 (degree≥6)")
    print()
    
    # Apply layout
    print("Layout Application:")
    print("-"*80)
    
    engine = SolarSystemLayoutEngine()
    new_positions = engine.apply_layout(places, transitions, arcs)
    
    print(f"  ✓ Layout calculated: {len(new_positions)} positions")
    print()
    
    # Measure place-to-transition distances
    print("Place Orbital Analysis:")
    print("-"*80)
    
    # Group places by their connected transition
    transition_orbits = {}
    for arc in arcs:
        if any(p.id == arc.source.id for p in places):
            place_id = arc.source.id
            transition_id = arc.target.id
            if transition_id not in transition_orbits:
                transition_orbits[transition_id] = []
            transition_orbits[transition_id].append(place_id)
    
    # Measure orbital distances
    for trans_id, place_ids in transition_orbits.items():
        trans = next(t for t in transitions if t.id == trans_id)
        tx, ty = new_positions[trans_id]
        
        # Calculate distances from transition to its places
        distances = []
        for place_id in place_ids:
            px, py = new_positions[place_id]
            dist = math.sqrt((px - tx)**2 + (py - ty)**2)
            distances.append(dist)
        
        avg_dist = sum(distances) / len(distances)
        min_dist = min(distances)
        max_dist = max(distances)
        
        print(f"  {trans.label} orbit:")
        print(f"    Places: {len(place_ids)}")
        print(f"    Distance: {min_dist:.1f}-{max_dist:.1f} units (avg={avg_dist:.1f})")
    
    print()
    
    # Measure place-to-place distances (within same orbit)
    print("Place-to-Place Spacing (within orbits):")
    print("-"*80)
    
    for trans_id, place_ids in transition_orbits.items():
        trans = next(t for t in transitions if t.id == trans_id)
        
        # Calculate inter-place distances
        inter_distances = []
        for i, p1_id in enumerate(place_ids):
            for p2_id in place_ids[i+1:]:
                p1x, p1y = new_positions[p1_id]
                p2x, p2y = new_positions[p2_id]
                dist = math.sqrt((p2x - p1x)**2 + (p2y - p1y)**2)
                inter_distances.append(dist)
        
        if inter_distances:
            avg_spacing = sum(inter_distances) / len(inter_distances)
            min_spacing = min(inter_distances)
            max_spacing = max(inter_distances)
            
            print(f"  {trans.label} places:")
            print(f"    Spacing: {min_spacing:.1f}-{max_spacing:.1f} units (avg={avg_spacing:.1f})")
    
    print()
    
    # Measure transition-to-transition distances (hub separation)
    print("Hub Separation (Transition-to-Transition):")
    print("-"*80)
    
    hub_distances = []
    for i, t1 in enumerate(transitions):
        for t2 in transitions[i+1:]:
            t1x, t1y = new_positions[t1.id]
            t2x, t2y = new_positions[t2.id]
            dist = math.sqrt((t2x - t1x)**2 + (t2y - t1y)**2)
            hub_distances.append((t1.label, t2.label, dist))
    
    for t1_label, t2_label, dist in sorted(hub_distances, key=lambda x: x[2]):
        print(f"  {t1_label} ↔ {t2_label}: {dist:.1f} units")
    
    print()
    
    # Final assessment
    print("="*80)
    print("ASSESSMENT:")
    print("="*80)
    
    # Check criteria
    correct_structure = (p_to_t_count == len(arcs))
    correct_weights = (min(weights) == max(weights) == 1.0)
    transitions_are_hubs = (len(hub_transitions) == 3)
    places_spread = (min(inter_distances) if inter_distances else 0) > 30.0  # Places not clustering
    hubs_separated = min(d[2] for d in hub_distances) > 200.0  # Hubs well separated
    
    print()
    if correct_structure:
        print("  ✅ Structure: All arcs Place→Transition (biological flow)")
    else:
        print(f"  ⚠️ Structure: {t_to_p_count} incorrect Transition→Place arcs")
    
    if correct_weights:
        print("  ✅ Weights: All 1.0 (no manipulation)")
    else:
        print(f"  ⚠️ Weights: Range {min(weights):.1f}-{max(weights):.1f} (expected 1.0)")
    
    if transitions_are_hubs:
        print("  ✅ Hubs: 3 transitions with high mass (activity centers)")
    else:
        print(f"  ⚠️ Hubs: Only {len(hub_transitions)} transitions detected as hubs")
    
    if places_spread:
        print(f"  ✅ Orbital spreading: Places separated (min={min(inter_distances):.1f} units)")
    else:
        print(f"  ⚠️ Orbital clustering: Places too close (min={min(inter_distances) if inter_distances else 0:.1f} units)")
    
    if hubs_separated:
        print(f"  ✅ Hub separation: Transitions well separated (min={min(d[2] for d in hub_distances):.1f} units)")
    else:
        print(f"  ⚠️ Hub clustering: Transitions too close (min={min(d[2] for d in hub_distances):.1f} units)")
    
    print()
    
    if all([correct_structure, correct_weights, transitions_are_hubs, places_spread, hubs_separated]):
        print("🎉 PARADIGM SHIFT SUCCESSFUL!")
        print("   Transitions are activity center hubs, Places orbit naturally.")
        print("   Ready for canvas visualization!")
    else:
        print("⚠️ PARADIGM SHIFT INCOMPLETE")
        print("   Some issues remain - see assessment above.")
    
    print()
    print("="*80)


if __name__ == '__main__':
    verify_paradigm_shift()
