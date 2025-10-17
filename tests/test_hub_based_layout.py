#!/usr/bin/env python3
"""Test Solar System Layout with Hub-Based Mass Assignment.

Tests the layout algorithm on BIOMD0000000001 (a DAG network) using
hub-based mass assignment where high-degree nodes become gravitational centers.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.netobjs import Place, Transition, Arc
from shypn.layout.sscc.graph_builder import GraphBuilder
from shypn.layout.sscc.scc_detector import SCCDetector
from shypn.layout.sscc.hub_based_mass_assigner import HubBasedMassAssigner
from shypn.layout.sscc.gravitational_simulator import GravitationalSimulator
from shypn.layout.sscc.orbit_stabilizer import OrbitStabilizer

import xml.etree.ElementTree as ET


def parse_sbml_simple(sbml_file):
    """Parse SBML file into Petri net objects (simplified)."""
    tree = ET.parse(sbml_file)
    root = tree.getroot()
    
    # Detect namespace
    namespace = ''
    if '}' in root.tag:
        namespace = root.tag.split('}')[0] + '}'
    
    print(f"📄 Parsing: {sbml_file}")
    print(f"   Namespace: {namespace if namespace else 'None'}")
    
    # Create places from species
    places = []
    place_id_counter = 1
    species_list = root.find(f'.//{namespace}listOfSpecies')
    if species_list is not None:
        for species in species_list.findall(f'{namespace}species'):
            species_id = species.get('id')
            species_name = species.get('name', species_id)
            # Place(x, y, id, name, radius=None, label="")
            place = Place(0.0, 0.0, place_id_counter, species_id, label=species_name)
            place_id_counter += 1
            places.append(place)
    
    # Create transitions from reactions
    transitions = []
    transition_id_counter = 1
    reaction_list = root.find(f'.//{namespace}listOfReactions')
    if reaction_list is not None:
        for reaction in reaction_list.findall(f'{namespace}reaction'):
            reaction_id = reaction.get('id')
            reaction_name = reaction.get('name', reaction_id)
            # Transition(x, y, id, name, width=None, height=None, label="", horizontal=True)
            transition = Transition(0.0, 0.0, transition_id_counter, reaction_id, label=reaction_name)
            transition_id_counter += 1
            transitions.append(transition)
    
    # Create arcs from reactants and products
    arcs = []
    arc_id_counter = 1
    
    if reaction_list is not None:
        for reaction in reaction_list.findall(f'{namespace}reaction'):
            reaction_id = reaction.get('id')
            
            # Find the transition object
            transition_obj = next((t for t in transitions if t.name == reaction_id), None)
            if not transition_obj:
                continue
            
            # Reactants -> Transition (input arcs)
            reactants = reaction.find(f'{namespace}listOfReactants')
            if reactants is not None:
                for reactant_ref in reactants.findall(f'{namespace}speciesReference'):
                    species_id = reactant_ref.get('species')
                    place_obj = next((p for p in places if p.name == species_id), None)
                    if place_obj:
                        # Arc(source, target, id, name, weight=1)
                        arc = Arc(place_obj, transition_obj, arc_id_counter, f"A{arc_id_counter}")
                        arcs.append(arc)
                        arc_id_counter += 1
            
            # Transition -> Products (output arcs)
            products = reaction.find(f'{namespace}listOfProducts')
            if products is not None:
                for product_ref in products.findall(f'{namespace}speciesReference'):
                    species_id = product_ref.get('species')
                    place_obj = next((p for p in places if p.name == species_id), None)
                    if place_obj:
                        # Arc(source, target, id, name, weight=1)
                        arc = Arc(transition_obj, place_obj, arc_id_counter, f"A{arc_id_counter}")
                        arcs.append(arc)
                        arc_id_counter += 1
    
    print(f"✓ Created Petri net: {len(places)} places, {len(transitions)} transitions, {len(arcs)} arcs\n")
    
    return places, transitions, arcs


def test_hub_based_layout(sbml_file):
    """Test Solar System Layout with hub-based mass assignment."""
    
    print("=" * 70)
    print("HUB-BASED SOLAR SYSTEM LAYOUT TEST")
    print("=" * 70)
    print()
    
    # Parse SBML
    places, transitions, arcs = parse_sbml_simple(sbml_file)
    
    # Build graph
    print("🔧 Building graph...")
    graph_builder = GraphBuilder()
    graph = graph_builder.build_graph(places, transitions, arcs)
    print(f"✓ Graph built: {len(graph)} nodes\n")
    
    # Detect SCCs
    print("🔍 Detecting SCCs...")
    scc_detector = SCCDetector()
    sccs = scc_detector.find_sccs(graph, graph_builder.id_to_object)
    print(f"✓ Found {len(sccs)} SCC(s)")
    
    # Print SCC details
    for i, scc in enumerate(sccs):
        print(f"   SCC #{i+1}: {len(scc.node_ids)} nodes")
        if len(scc.node_ids) <= 5:  # Show small SCCs
            node_names = [graph_builder.id_to_object[nid].name 
                         for nid in scc.node_ids if nid in graph_builder.id_to_object]
            print(f"           Nodes: {', '.join(node_names)}")
    print()
    
    # Hub-based mass assignment
    print("⚖️  Assigning masses based on hub detection...")
    mass_assigner = HubBasedMassAssigner()
    masses = mass_assigner.assign_masses(sccs, places, transitions, arcs)
    
    # Print hub statistics
    hub_stats = mass_assigner.get_hub_statistics()
    
    print("\n📊 HUB CLASSIFICATION:")
    print("-" * 70)
    
    # Show ALL nodes with their degrees for debugging
    print("\n🔍 ALL NODE DEGREES:")
    all_nodes = sorted(mass_assigner.hub_stats.items(), 
                      key=lambda x: x[1][1], reverse=True)
    for node_id, (category, degree) in all_nodes[:15]:  # Show top 15
        mass = masses.get(node_id, 0)
        # Determine if it's a place or transition
        obj = graph_builder.id_to_object.get(node_id)
        obj_type = type(obj).__name__ if obj else "Unknown"
        obj_name = obj.name if obj else "?"
        print(f"   {obj_name:15} (ID:{node_id:2}) → {degree:2} connections | mass={mass:6.1f} | {category} | {obj_type}")
    
    if hub_stats['super_hubs']:
        print(f"\n🌟 SUPER-HUBS (mass={mass_assigner.MASS_SUPER_HUB}, degree≥{mass_assigner.SUPER_HUB_THRESHOLD}):")
        for node_id, degree in hub_stats['super_hubs']:
            print(f"   • {node_id}: {degree} connections")
    
    if hub_stats['major_hubs']:
        print(f"\n🔵 MAJOR HUBS (mass={mass_assigner.MASS_MAJOR_HUB}, degree≥{mass_assigner.MAJOR_HUB_THRESHOLD}):")
        for node_id, degree in hub_stats['major_hubs']:
            print(f"   • {node_id}: {degree} connections")
    
    if hub_stats['minor_hubs']:
        print(f"\n🟢 MINOR HUBS (mass={mass_assigner.MASS_MINOR_HUB}, degree≥{mass_assigner.MINOR_HUB_THRESHOLD}):")
        for node_id, degree in hub_stats['minor_hubs']:
            print(f"   • {node_id}: {degree} connections")
    
    regular_count = len(hub_stats['regular'])
    if regular_count > 0:
        print(f"\n⚪ REGULAR NODES (mass={mass_assigner.MASS_PLACE}): {regular_count} nodes")
    
    print()
    
    # Run gravitational simulation
    print("🌌 Running gravitational simulation...")
    print(f"   Iterations: 1000")
    print(f"   Using hub-based masses")
    print()
    
    simulator = GravitationalSimulator()
    
    positions = simulator.simulate(
        places=places,
        transitions=transitions,
        arcs=arcs,
        masses=masses,
        iterations=1000,
        use_arc_weight=True
    )
    print(f"✓ Simulation complete: {len(positions)} positions computed\n")
    
    # Orbital stabilization
    print("🔄 Stabilizing orbits...")
    stabilizer = OrbitStabilizer()
    
    final_positions = stabilizer.stabilize(
        positions=positions,
        sccs=sccs,
        places=places,
        transitions=transitions
    )
    print(f"✓ Stabilization complete\n")
    
    # Analyze layout results
    print("=" * 70)
    print("LAYOUT ANALYSIS")
    print("=" * 70)
    print()
    
    # Find hub positions (both places and transitions)
    print("📍 HUB POSITIONS (gravitational centers):")
    print()
    
    # Collect all hubs
    all_hubs = (hub_stats['super_hubs'] + hub_stats['major_hubs'] + 
                hub_stats['minor_hubs'])
    
    if all_hubs:
        # Group by mass level
        super_hubs = [(nid, deg) for nid, deg in all_hubs 
                     if masses.get(nid, 0) == mass_assigner.MASS_SUPER_HUB]
        major_hubs = [(nid, deg) for nid, deg in all_hubs 
                     if masses.get(nid, 0) == mass_assigner.MASS_MAJOR_HUB]
        minor_hubs = [(nid, deg) for nid, deg in all_hubs 
                     if masses.get(nid, 0) == mass_assigner.MASS_MINOR_HUB]
        
        if super_hubs:
            print("🌟 Super-hubs (mass=1000):")
            for node_id, degree in super_hubs:
                obj = graph_builder.id_to_object.get(node_id)
                obj_name = obj.name if obj else f"ID{node_id}"
                obj_type = type(obj).__name__ if obj else "?"
                x, y = final_positions[node_id]
                print(f"   {obj_name:15} ({obj_type:10}) → ({x:7.1f}, {y:7.1f}) | {degree} connections")
        
        if major_hubs:
            print("\n🔵 Major hubs (mass=500):")
            for node_id, degree in major_hubs:
                obj = graph_builder.id_to_object.get(node_id)
                obj_name = obj.name if obj else f"ID{node_id}"
                obj_type = type(obj).__name__ if obj else "?"
                x, y = final_positions[node_id]
                print(f"   {obj_name:15} ({obj_type:10}) → ({x:7.1f}, {y:7.1f}) | {degree} connections")
        
        if minor_hubs:
            print("\n🟢 Minor hubs (mass=200):")
            for node_id, degree in minor_hubs:
                obj = graph_builder.id_to_object.get(node_id)
                obj_name = obj.name if obj else f"ID{node_id}"
                obj_type = type(obj).__name__ if obj else "?"
                x, y = final_positions[node_id]
                print(f"   {obj_name:15} ({obj_type:10}) → ({x:7.1f}, {y:7.1f}) | {degree} connections")
    else:
        print("   No hubs detected (all nodes have regular mass)")

    
    # Calculate distances from center
    print("\n\n📏 DISTANCE FROM CENTER (0, 0):")
    print()
    
    distances = []
    for obj_id, (x, y) in final_positions.items():
        distance = (x**2 + y**2)**0.5
        obj = graph_builder.id_to_object.get(obj_id)
        obj_name = obj.name if obj else f"ID{obj_id}"
        obj_type = type(obj).__name__ if obj else "?"
        mass_val = masses.get(obj_id, 0)
        distances.append((obj_id, obj_name, obj_type, distance, mass_val))
    
    distances.sort(key=lambda x: x[3])  # Sort by distance
    
    print("Closest to center (gravitational centers should be here):")
    for obj_id, obj_name, obj_type, dist, mass_val in distances[:8]:
        print(f"   {obj_name:15} ({obj_type:10}) → {dist:7.1f} units | mass={mass_val:6.1f}")
    
    print("\nFarthest from center:")
    for obj_id, obj_name, obj_type, dist, mass_val in distances[-3:]:
        print(f"   {obj_name:15} ({obj_type:10}) → {dist:7.1f} units | mass={mass_val:6.1f}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print()
    print("💡 INTERPRETATION:")
    print("   • High-degree nodes (hubs) should cluster near center")
    print("   • Their gravitational mass attracts other nodes")
    print("   • Creates natural hierarchy even without cycles (SCCs)")
    print("   • Similar to stars in a galaxy, but based on connectivity")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_hub_based_layout.py <sbml_file>")
        print("Example: python3 test_hub_based_layout.py data/biomodels_test/BIOMD0000000001.xml")
        sys.exit(1)
    
    sbml_file = sys.argv[1]
    
    if not os.path.exists(sbml_file):
        print(f"❌ File not found: {sbml_file}")
        sys.exit(1)
    
    test_hub_based_layout(sbml_file)
