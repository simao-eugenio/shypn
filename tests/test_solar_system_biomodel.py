"""Test Solar System Layout on Real Biomodel.

This script loads an SBML biomodel, applies the Solar System Layout,
and provides detailed analysis of the detected structure.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.layout.sscc import SolarSystemLayoutEngine
from shypn.netobjs import Place, Transition, Arc


def load_biomodel_simple(model_path: str):
    """Load biomodel using simple XML parsing.
    
    Creates a test Petri net from SBML structure:
    - Species → Places
    - Reactions → Transitions
    - Species References → Arcs
    
    Args:
        model_path: Path to SBML file
        
    Returns:
        Tuple of (places, transitions, arcs) or None if error
    """
    try:
        import xml.etree.ElementTree as ET
        
        print(f"📂 Loading SBML file: {model_path}")
        
        # Parse XML
        tree = ET.parse(model_path)
        root = tree.getroot()
        
        # Handle SBML namespace
        ns = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}
        
        # Extract species (→ Places)
        species_list = root.findall('.//sbml:species', ns)
        if not species_list:
            # Try other common SBML namespaces
            ns = {'sbml': 'http://www.sbml.org/sbml/level2'}
            species_list = root.findall('.//sbml:species', ns)
        if not species_list:
            # Try without namespace
            species_list = root.findall('.//species')
        
        places = []
        species_map = {}
        
        for i, sp in enumerate(species_list, 1):
            sp_id = sp.get('id', f'S{i}')
            sp_name = sp.get('name', sp_id)
            
            # Create place
            place = Place(
                x=100.0 * (i % 10),
                y=100.0 * (i // 10),
                id=i,
                name=f"P{i}",
                label=sp_name
            )
            place.tokens = int(float(sp.get('initialAmount', 0)))
            places.append(place)
            species_map[sp_id] = place
        
        # Extract reactions (→ Transitions)
        reactions_list = root.findall('.//sbml:reaction', ns)
        if not reactions_list:
            reactions_list = root.findall('.//reaction')
        
        transitions = []
        transition_map = {}
        arcs = []
        arc_id = 1
        
        for i, rxn in enumerate(reactions_list, 1):
            rxn_id = rxn.get('id', f'R{i}')
            rxn_name = rxn.get('name', rxn_id)
            
            # Create transition
            trans = Transition(
                x=100.0 * (i % 10) + 50,
                y=100.0 * (i // 10) + 50,
                id=len(places) + i,
                name=f"T{i}",
                label=rxn_name
            )
            transitions.append(trans)
            transition_map[rxn_id] = trans
            
            # Get reactants (→ Arcs from Places to Transition)
            # First try listOfReactants
            reactants_list = rxn.find('sbml:listOfReactants', ns)
            if reactants_list is None:
                reactants_list = rxn.find('listOfReactants')
            
            if reactants_list is not None:
                reactants = reactants_list.findall('sbml:speciesReference', ns)
                if not reactants:
                    reactants = reactants_list.findall('speciesReference')
                
                for react in reactants:
                    species_ref = react.get('species')
                    if species_ref in species_map:
                        arc = Arc(
                            source=species_map[species_ref],
                            target=trans,
                            id=len(places) + len(transitions) + arc_id,
                            name=f"A{arc_id}",
                            weight=int(float(react.get('stoichiometry', 1)))
                        )
                        arcs.append(arc)
                        arc_id += 1
            
            # Get products (→ Arcs from Transition to Places)
            products_list = rxn.find('sbml:listOfProducts', ns)
            if products_list is None:
                products_list = rxn.find('listOfProducts')
            
            if products_list is not None:
                products = products_list.findall('sbml:speciesReference', ns)
                if not products:
                    products = products_list.findall('speciesReference')
                
                for prod in products:
                    species_ref = prod.get('species')
                    if species_ref in species_map:
                        arc = Arc(
                            source=trans,
                            target=species_map[species_ref],
                            id=len(places) + len(transitions) + arc_id,
                            name=f"A{arc_id}",
                            weight=int(float(prod.get('stoichiometry', 1)))
                        )
                        arcs.append(arc)
                        arc_id += 1
        
        print(f"✓ Parsed: {len(places)} places (species), {len(transitions)} transitions (reactions), {len(arcs)} arcs")
        
        return places, transitions, arcs
        
    except Exception as e:
        print(f"❌ Error loading biomodel: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_solar_system_structure(engine, places, transitions, arcs):
    """Analyze the Solar System Layout structure in detail.
    
    Args:
        engine: SolarSystemLayoutEngine with completed layout
        places: List of Place objects
        transitions: List of Transition objects
        arcs: List of Arc objects
    """
    print("\n" + "="*80)
    print("🌌 SOLAR SYSTEM LAYOUT ANALYSIS")
    print("="*80)
    
    # Get statistics
    stats = engine.get_statistics()
    
    print("\n📊 Overall Statistics:")
    print(f"   Total nodes: {stats['total_nodes']}")
    print(f"   SCCs found: {stats['num_sccs']}")
    print(f"   Nodes in SCCs: {stats['num_nodes_in_sccs']}")
    print(f"   Free places: {stats['num_free_places']}")
    print(f"   Free transitions: {stats['num_transitions']}")
    print(f"   Average mass: {stats['avg_mass']:.2f}")
    
    # Analyze each SCC (Stars)
    if engine.sccs:
        print(f"\n⭐ STARS (Strongly Connected Components):")
        print(f"   Found {len(engine.sccs)} SCC(s) representing feedback loops")
        print()
        
        for i, scc in enumerate(engine.sccs, 1):
            print(f"   Star #{i}:")
            print(f"      Size: {scc.size} nodes")
            print(f"      Mass: {scc.mass:.2f}")
            print(f"      Node IDs: {scc.node_ids}")
            
            # Get the actual objects
            scc_places = scc.get_places()
            scc_transitions = scc.get_transitions()
            
            print(f"      Composition:")
            print(f"         Places: {len(scc_places)}")
            if scc_places:
                place_names = [p.name for p in scc_places]
                print(f"         Place names: {', '.join(place_names)}")
            
            print(f"         Transitions: {len(scc_transitions)}")
            if scc_transitions:
                trans_names = [t.name for t in scc_transitions]
                print(f"         Transition names: {', '.join(trans_names)}")
            
            # Show centroid position
            if scc.node_ids and engine.positions:
                centroid = scc.compute_centroid(engine.positions)
                print(f"      Centroid: ({centroid[0]:.1f}, {centroid[1]:.1f})")
            
            print()
    else:
        print(f"\n⭐ STARS (Strongly Connected Components):")
        print(f"   No SCCs found (no feedback loops in this model)")
        print()
    
    # Collect SCC node IDs
    scc_node_ids = set()
    for scc in engine.sccs:
        for node_id in scc.node_ids:
            scc_node_ids.add(node_id)
    
    # Analyze free places (Planets)
    free_places = [p for p in places if p.id not in scc_node_ids]
    
    print(f"🌍 PLANETS (Free Places):")
    if free_places:
        print(f"   Found {len(free_places)} free places orbiting the center")
        print()
        
        # Show first 10 (or all if less than 10)
        display_count = min(10, len(free_places))
        for i, place in enumerate(free_places[:display_count], 1):
            mass = engine.masses.get(place.id, 0)
            pos = engine.positions.get(place.id, (0, 0))
            print(f"   Planet #{i}: {place.name}")
            print(f"      ID: {place.id}")
            print(f"      Mass: {mass:.2f}")
            print(f"      Position: ({pos[0]:.1f}, {pos[1]:.1f})")
            print(f"      Tokens: {place.tokens}")
            if place.label:
                print(f"      Label: {place.label}")
            print()
        
        if len(free_places) > display_count:
            print(f"   ... and {len(free_places) - display_count} more planets")
            print()
    else:
        print(f"   No free places (all places are part of SCCs)")
        print()
    
    # Analyze free transitions (Satellites)
    free_transitions = [t for t in transitions if t.id not in scc_node_ids]
    
    print(f"🛸 SATELLITES (Free Transitions):")
    if free_transitions:
        print(f"   Found {len(free_transitions)} free transitions")
        print()
        
        # Show first 10
        display_count = min(10, len(free_transitions))
        for i, trans in enumerate(free_transitions[:display_count], 1):
            mass = engine.masses.get(trans.id, 0)
            pos = engine.positions.get(trans.id, (0, 0))
            print(f"   Satellite #{i}: {trans.name}")
            print(f"      ID: {trans.id}")
            print(f"      Mass: {mass:.2f}")
            print(f"      Position: ({pos[0]:.1f}, {pos[1]:.1f})")
            if trans.label:
                print(f"      Label: {trans.label}")
            print()
        
        if len(free_transitions) > display_count:
            print(f"   ... and {len(free_transitions) - display_count} more satellites")
            print()
    else:
        print(f"   No free transitions (all transitions are part of SCCs)")
        print()
    
    # Analyze arcs (Gravitational Forces)
    print(f"⚡ GRAVITATIONAL FORCES (Arcs):")
    print(f"   Total arcs: {len(arcs)}")
    
    # Categorize arcs
    arcs_within_scc = []
    arcs_from_scc = []
    arcs_to_scc = []
    arcs_between_free = []
    
    for arc in arcs:
        source_in_scc = arc.source.id in scc_node_ids
        target_in_scc = arc.target.id in scc_node_ids
        
        if source_in_scc and target_in_scc:
            arcs_within_scc.append(arc)
        elif source_in_scc:
            arcs_from_scc.append(arc)
        elif target_in_scc:
            arcs_to_scc.append(arc)
        else:
            arcs_between_free.append(arc)
    
    print(f"   Within SCCs (star internal): {len(arcs_within_scc)}")
    print(f"   From SCCs to free nodes: {len(arcs_from_scc)}")
    print(f"   From free nodes to SCCs: {len(arcs_to_scc)}")
    print(f"   Between free nodes: {len(arcs_between_free)}")
    
    # Weight statistics
    weights = [arc.weight for arc in arcs]
    if weights:
        print(f"\n   Arc weight statistics:")
        print(f"      Min weight: {min(weights)}")
        print(f"      Max weight: {max(weights)}")
        print(f"      Avg weight: {sum(weights)/len(weights):.2f}")
    
    print()


def test_biomodel_layout(model_path: str):
    """Test Solar System Layout on a biomodel.
    
    Args:
        model_path: Path to SBML file
    """
    print("="*80)
    print("🧪 TESTING SOLAR SYSTEM LAYOUT ON BIOMODEL")
    print("="*80)
    print()
    
    # Load the biomodel
    result = load_biomodel_simple(model_path)
    if result is None:
        return False
    
    places, transitions, arcs = result
    
    # Check if we have anything to layout
    if not places and not transitions:
        print("❌ No objects to layout")
        return False
    
    print()
    print("-"*80)
    print("🌟 APPLYING SOLAR SYSTEM LAYOUT")
    print("-"*80)
    
    # Create engine with appropriate parameters
    # For biomodels, use more iterations for better convergence
    engine = SolarSystemLayoutEngine(
        iterations=1000,  # Good balance of quality and speed
        use_arc_weight=True,
        scc_radius=50.0,
        planet_orbit=300.0,
        satellite_orbit=50.0
    )
    
    print("\nEngine parameters:")
    print(f"   Iterations: {engine.iterations}")
    print(f"   Use arc weight: {engine.use_arc_weight}")
    print(f"   SCC radius: {engine.scc_radius}")
    print(f"   Planet orbit: {engine.planet_orbit}")
    print(f"   Satellite orbit: {engine.satellite_orbit}")
    print()
    
    # Apply layout
    try:
        print("⏳ Running layout algorithm (this may take a few seconds)...")
        positions = engine.apply_layout(places, transitions, arcs)
        print(f"✓ Layout completed successfully!")
        print(f"✓ Positioned {len(positions)} objects")
    except Exception as e:
        print(f"❌ Layout failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Analyze the results
    analyze_solar_system_structure(engine, places, transitions, arcs)
    
    # Summary
    stats = engine.get_statistics()
    print("="*80)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    print()
    print("The Solar System Layout has organized the Petri net into:")
    print(f"   ⭐ {len(engine.sccs)} star system(s) (feedback loops)")
    print(f"   🌍 {stats['num_free_places']} planet(s) (free places)")
    print(f"   🛸 {stats['num_transitions']} satellite(s) (free transitions)")
    print(f"   ⚡ {len(arcs)} gravitational force(s) (arcs)")
    print()
    
    return True


if __name__ == '__main__':
    # Get model path from command line or use default
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        # Default to BIOMD0000000001
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(repo_root, 'data', 'biomodels_test', 'BIOMD0000000001.xml')
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        print()
        print("Usage:")
        print(f"   python3 {sys.argv[0]} <path_to_sbml_file>")
        print()
        print("Example:")
        print(f"   python3 {sys.argv[0]} data/biomodels_test/BIOMD0000000001.xml")
        sys.exit(1)
    
    success = test_biomodel_layout(model_path)
    sys.exit(0 if success else 1)
