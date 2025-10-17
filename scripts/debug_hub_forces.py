#!/usr/bin/env python3
"""Debug force calculation - check if hub repulsion is actually being applied."""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.layout.sscc.solar_system_layout_engine import SolarSystemLayoutEngine
from shypn.layout.sscc.scc_detector import SCCDetector
from shypn.layout.sscc.graph_builder import GraphBuilder
from shypn.layout.sscc.hub_based_mass_assigner import HubBasedMassAssigner


def debug_forces():
    """Debug why hub repulsion isn't working."""
    
    print("="*80)
    print("FORCE DEBUG: Hub Repulsion Analysis")
    print("="*80)
    print()
    
    # Load model
    model_path = "workspace/Test_flow/model/hub_constellation.shy"
    document = DocumentModel.load_from_file(model_path)
    places = document.places
    transitions = document.transitions
    arcs = document.arcs
    
    print(f"Model: {len(places)} places, {len(transitions)} transitions, {len(arcs)} arcs")
    print()
    
    # Build graph and detect SCCs
    graph_builder = GraphBuilder()
    graph = graph_builder.build_graph(places, transitions, arcs)
    id_to_object = graph_builder.id_to_object
    
    detector = SCCDetector()
    sccs = detector.find_sccs(graph, id_to_object)
    
    # Assign masses
    assigner = HubBasedMassAssigner()
    masses = assigner.assign_masses(sccs, places, transitions, arcs)
    
    print("Mass Assignment:")
    print("-"*80)
    print("\nTransitions:")
    for t in sorted(transitions, key=lambda x: x.id):
        mass = masses[t.id]
        print(f"  {t.label} (ID {t.id}): mass = {mass:.1f}")
    
    print("\nPlaces (first 3):")
    for p in sorted(places, key=lambda x: x.id)[:3]:
        mass = masses[p.id]
        print(f"  {p.label} (ID {p.id}): mass = {mass:.1f}")
    print("  ...")
    print()
    
    # Check if transitions qualify as "hubs"
    PROXIMITY_THRESHOLD = 500.0
    print("Hub Detection (mass >= 500):")
    print("-"*80)
    
    hub_transitions = [t for t in transitions if masses[t.id] >= PROXIMITY_THRESHOLD]
    non_hub_transitions = [t for t in transitions if masses[t.id] < PROXIMITY_THRESHOLD]
    
    print(f"  Hub transitions (mass >= {PROXIMITY_THRESHOLD}): {len(hub_transitions)}")
    for t in hub_transitions:
        print(f"    - {t.label}: mass={masses[t.id]:.1f} ✅ QUALIFIES")
    
    if non_hub_transitions:
        print(f"\n  Non-hub transitions (mass < {PROXIMITY_THRESHOLD}): {len(non_hub_transitions)}")
        for t in non_hub_transitions:
            print(f"    - {t.label}: mass={masses[t.id]:.1f} ❌ DOES NOT QUALIFY")
    print()
    
    # Calculate hub-hub forces
    print("Hub-to-Hub Repulsion Forces:")
    print("-"*80)
    
    PROXIMITY_CONSTANT = 2000000.0  # Current value
    
    for i, t1 in enumerate(transitions):
        for t2 in list(transitions)[i+1:]:
            m1 = masses[t1.id]
            m2 = masses[t2.id]
            
            # Distance
            import math
            distance = math.sqrt((t2.x - t1.x)**2 + (t2.y - t1.y)**2)
            
            # Check if hub repulsion applies
            if m1 >= PROXIMITY_THRESHOLD or m2 >= PROXIMITY_THRESHOLD:
                extra_force = (PROXIMITY_CONSTANT * m1 * m2) / (distance * distance)
                print(f"\n  {t1.label} ↔ {t2.label}:")
                print(f"    Distance: {distance:.1f} units")
                print(f"    Masses: {m1:.1f} × {m2:.1f}")
                print(f"    Force: {extra_force:.2e} ✅ HUB REPULSION ACTIVE")
            else:
                print(f"\n  {t1.label} ↔ {t2.label}:")
                print(f"    Distance: {distance:.1f} units")
                print(f"    Masses: {m1:.1f} × {m2:.1f}")
                print(f"    Force: 0 ❌ NO HUB REPULSION (both mass < {PROXIMITY_THRESHOLD})")
    
    print()
    print("="*80)
    print("DIAGNOSIS:")
    print("="*80)
    print()
    
    if len(hub_transitions) == 3:
        print("✅ All 3 transitions are detected as hubs (mass >= 500)")
        print("✅ Hub repulsion should be active between all transition pairs")
        print()
        print("⚠️ IF HUBS ARE STILL CLUSTERING:")
        print("   The arc attraction forces may be overwhelming the repulsion.")
        print("   Check:")
        print("   1. Are there arcs connecting the transitions directly?")
        print("   2. Is GRAVITY_CONSTANT too high?")
        print("   3. Is PROXIMITY_CONSTANT high enough?")
    else:
        print(f"❌ Only {len(hub_transitions)}/3 transitions qualify as hubs!")
        print("   Hub repulsion won't work properly.")
        print("   Fix: Increase transition degrees or lower PROXIMITY_THRESHOLD")
    
    print()


if __name__ == '__main__':
    debug_forces()
