"""Detailed Analysis: Hub Nodes vs SCCs in Biomodels

This script analyzes the difference between:
1. Hub nodes (high degree) - many connections
2. SCCs (cycles) - feedback loops

It will analyze BIOMD0000000001 to show:
- Which nodes have high degree (hubs like NAD, ADP)
- Whether there are any actual cycles (SCCs)
- The network topology
"""

import sys
import os
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs import Place, Transition, Arc
from shypn.layout.sscc import GraphBuilder, SCCDetector


def parse_sbml_simple(sbml_file):
    """Parse SBML file into simple Petri net."""
    tree = ET.parse(sbml_file)
    root = tree.getroot()
    
    # Try to detect namespace
    ns = {}
    if root.tag.startswith('{'):
        # Extract namespace
        namespace = root.tag.split('}')[0][1:]
        ns = {'sbml': namespace}
    
    # Extract species (places)
    places = []
    
    # Try with namespace first, then without
    if ns:
        species_list = root.findall('.//sbml:species', ns)
    else:
        species_list = root.findall('.//species')
    
    for i, species in enumerate(species_list):
        species_id = species.get('id') or species.get('name') or f'S{i+1}'
        place = Place(x=0, y=0, id=i+1, name=species_id, label=species_id)
        places.append(place)
    
    # Extract reactions (transitions)
    transitions = []
    arcs = []
    arc_id = len(places) + 1
    
    # Try with namespace first, then without
    if ns:
        reactions = root.findall('.//sbml:reaction', ns)
    else:
        reactions = root.findall('.//reaction')
    
    for i, reaction in enumerate(reactions):
        reaction_id = reaction.get('id') or reaction.get('name') or f'R{i+1}'
        trans_id = len(places) + i + 1
        transition = Transition(x=0, y=0, id=trans_id, name=reaction_id, label=reaction_id)
        transitions.append(transition)
        
        # Reactants (place → transition)
        if ns:
            reactants = reaction.findall('.//sbml:listOfReactants/sbml:speciesReference', ns)
        else:
            reactants = reaction.findall('.//listOfReactants/speciesReference')
            
        for reactant in reactants:
            species_ref = reactant.get('species')
            # Find place with this species ID
            source_place = next((p for p in places if p.name == species_ref), None)
            if source_place:
                arc = Arc(source=source_place, target=transition, 
                         id=arc_id, name=f'A{arc_id}', weight=1)
                arcs.append(arc)
                arc_id += 1
        
        # Products (transition → place)
        if ns:
            products = reaction.findall('.//sbml:listOfProducts/sbml:speciesReference', ns)
        else:
            products = reaction.findall('.//listOfProducts/speciesReference')
            
        for product in products:
            species_ref = product.get('species')
            # Find place with this species ID
            target_place = next((p for p in places if p.name == species_ref), None)
            if target_place:
                arc = Arc(source=transition, target=target_place,
                         id=arc_id, name=f'A{arc_id}', weight=1)
                arcs.append(arc)
                arc_id += 1
    
    return places, transitions, arcs


def analyze_node_degrees(places, transitions, arcs):
    """Analyze node degrees (in-degree and out-degree)."""
    print("\n" + "="*70)
    print("📊 NODE DEGREE ANALYSIS (Hub Detection)")
    print("="*70)
    
    # Calculate degrees
    in_degree = {}
    out_degree = {}
    
    for obj in places + transitions:
        in_degree[obj.id] = 0
        out_degree[obj.id] = 0
    
    for arc in arcs:
        out_degree[arc.source.id] += 1
        in_degree[arc.target.id] += 1
    
    # Find hubs (nodes with high degree)
    print("\n🔍 HIGH-DEGREE NODES (Potential Hubs):")
    print("-" * 70)
    
    # Sort by total degree
    nodes_with_degree = []
    for obj in places + transitions:
        total_degree = in_degree[obj.id] + out_degree[obj.id]
        if total_degree > 0:
            nodes_with_degree.append((obj, in_degree[obj.id], out_degree[obj.id], total_degree))
    
    nodes_with_degree.sort(key=lambda x: x[3], reverse=True)
    
    # Show top 10 hubs
    print(f"{'Node':<20} {'Type':<12} {'In-Degree':<12} {'Out-Degree':<12} {'Total':<8}")
    print("-" * 70)
    
    for obj, in_deg, out_deg, total_deg in nodes_with_degree[:15]:
        obj_type = "Place" if isinstance(obj, Place) else "Transition"
        print(f"{obj.name:<20} {obj_type:<12} {in_deg:<12} {out_deg:<12} {total_deg:<8}")
    
    # Identify hub categories
    print("\n📌 HUB CATEGORIES:")
    print("-" * 70)
    
    high_in = [x for x in nodes_with_degree if x[1] >= 5]
    high_out = [x for x in nodes_with_degree if x[2] >= 5]
    high_total = [x for x in nodes_with_degree if x[3] >= 8]
    
    if high_in:
        print(f"\n🎯 HIGH IN-DEGREE (≥5) - Convergence Hubs:")
        for obj, in_deg, out_deg, total in high_in[:5]:
            print(f"   {obj.name}: {in_deg} arcs converging")
    
    if high_out:
        print(f"\n🎯 HIGH OUT-DEGREE (≥5) - Divergence Hubs:")
        for obj, in_deg, out_deg, total in high_out[:5]:
            print(f"   {obj.name}: {out_deg} arcs diverging")
    
    if high_total:
        print(f"\n🎯 HIGH TOTAL DEGREE (≥8) - Major Hubs:")
        for obj, in_deg, out_deg, total in high_total[:5]:
            print(f"   {obj.name}: {total} total connections")
    
    return in_degree, out_degree


def analyze_sccs_detailed(places, transitions, arcs):
    """Detect and analyze SCCs (cycles)."""
    print("\n" + "="*70)
    print("🔄 STRONGLY CONNECTED COMPONENT ANALYSIS (Cycle Detection)")
    print("="*70)
    
    # Build graph and detect SCCs
    builder = GraphBuilder()
    graph = builder.build_graph(places, transitions, arcs)
    
    detector = SCCDetector()
    sccs = detector.find_sccs(graph, builder.id_to_object)
    
    print(f"\n📊 RESULTS:")
    print("-" * 70)
    print(f"Total nodes: {len(places) + len(transitions)}")
    print(f"Total arcs: {len(arcs)}")
    print(f"SCCs found: {len(sccs)}")
    
    if sccs:
        print(f"\n⭐ DETECTED CYCLES (SCCs):")
        print("-" * 70)
        for i, scc in enumerate(sccs, 1):
            print(f"\n🌟 SCC #{i} (Size: {scc.size} nodes)")
            print(f"   Nodes: {[builder.id_to_object[nid].name for nid in scc.node_ids]}")
            print(f"   Contains:")
            places_in_scc = scc.get_places()
            transitions_in_scc = scc.get_transitions()
            print(f"      - {len(places_in_scc)} places")
            print(f"      - {len(transitions_in_scc)} transitions")
    else:
        print(f"\n❌ NO CYCLES DETECTED")
        print("   This is a DAG (Directed Acyclic Graph)")
        print("   The network has NO feedback loops")
        print("   All paths flow in one direction")
    
    return sccs


def explain_difference():
    """Explain the difference between hubs and SCCs."""
    print("\n" + "="*70)
    print("📖 CONCEPT CLARIFICATION: Hub Nodes vs SCCs")
    print("="*70)
    
    print("""
🎯 HUB NODES (High Degree):
   - Nodes with MANY connections (high in-degree or out-degree)
   - Like NAD, ADP, ATP in metabolic networks
   - They participate in many reactions
   - NOT necessarily part of cycles
   
   Example (Hub but NOT cycle):
        A ──┐
        B ──┼──→ [HUB] ──┬──→ X
        C ──┘             ├──→ Y
                          └──→ Z
   
   Hub has high degree but no cycle!

🔄 SCCs (Strongly Connected Components):
   - CYCLES where every node can reach every other node
   - Feedback loops in the network
   - Requires BIDIRECTIONAL paths (through intermediates)
   
   Example (SCC - actual cycle):
        A → B → C → A  (all can reach each other)
   
   Or in Petri nets:
        P1 → T1 → P2 → T2 → P1  (feedback loop)

⚠️ KEY DIFFERENCE:
   - NAD/ADP with many arcs = HUBS (high degree)
   - NAD/ADP in feedback loop = SCC (cycle)
   
   If NAD → R1 → Product and Product never returns to NAD:
      → NAD is a HUB but NOT in an SCC
   
   If NAD → R1 → Product → R2 → NAD:
      → NAD is in an SCC (cycle exists!)

🌟 SOLAR SYSTEM LAYOUT ROLES:
   
   IF SCCs exist (cycles detected):
      - SCCs become STARS (mass = 1000, at center)
      - Hub places become PLANETS (mass = 100, orbit stars)
      - Transitions become SATELLITES (mass = 10, orbit planets)
   
   IF NO SCCs (like BIOMD0000000001):
      - ALL places are PLANETS (mass = 100)
      - ALL transitions are SATELLITES (mass = 10)
      - No stars (no gravitational centers)
      - Layout becomes similar to force-directed
      - Hubs naturally attract more connections (more arcs = more force)
    """)


def analyze_biomodel(sbml_file):
    """Complete analysis of a biomodel."""
    print("\n" + "="*70)
    print(f"🧬 ANALYZING BIOMODEL: {os.path.basename(sbml_file)}")
    print("="*70)
    
    # Parse SBML
    places, transitions, arcs = parse_sbml_simple(sbml_file)
    
    print(f"\n📦 MODEL STATISTICS:")
    print(f"   Species (Places): {len(places)}")
    print(f"   Reactions (Transitions): {len(transitions)}")
    print(f"   Connections (Arcs): {len(arcs)}")
    
    # Analyze node degrees (find hubs)
    in_degree, out_degree = analyze_node_degrees(places, transitions, arcs)
    
    # Analyze SCCs (find cycles)
    sccs = analyze_sccs_detailed(places, transitions, arcs)
    
    # Explain concepts
    explain_difference()
    
    # Conclusion
    print("\n" + "="*70)
    print("🎓 CONCLUSION FOR THIS MODEL")
    print("="*70)
    
    hub_places = [p for p in places if (in_degree[p.id] + out_degree[p.id]) >= 5]
    
    if sccs:
        print(f"\n✅ This model HAS cycles (feedback loops)")
        print(f"   - {len(sccs)} SCC(s) detected → These become STARS")
        print(f"   - {len(hub_places)} high-degree nodes → These become PLANETS")
        print(f"   - Solar System Layout will have BINARY/MULTIPLE star system")
    else:
        print(f"\n⚠️  This model has NO cycles (it's a DAG)")
        print(f"   - 0 SCCs → NO STARS in solar system")
        print(f"   - {len(hub_places)} high-degree nodes (hubs like NAD, ADP)")
        print(f"   - These hubs are PLANETS (not stars)")
        print(f"   - Solar System Layout will be similar to force-directed")
        print(f"   - Hubs will naturally cluster due to many arc connections")
    
    if hub_places:
        print(f"\n🎯 Major Hubs in this model:")
        for place in hub_places[:5]:
            total = in_degree[place.id] + out_degree[place.id]
            print(f"   - {place.name}: {total} connections")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 test_hub_vs_scc_analysis.py <sbml_file>")
        print("\nExample:")
        print("  python3 tests/test_hub_vs_scc_analysis.py data/biomodels_test/BIOMD0000000001.xml")
        sys.exit(1)
    
    sbml_file = sys.argv[1]
    
    if not os.path.exists(sbml_file):
        print(f"Error: File not found: {sbml_file}")
        sys.exit(1)
    
    analyze_biomodel(sbml_file)
    
    print("\n" + "="*70)
    print("✅ Analysis complete!")
    print("="*70)
