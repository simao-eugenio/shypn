#!/usr/bin/env python3
"""Test black hole galaxy layout with SCC-aware mass assignment."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
from shypn.netobjs import Place, Transition, Arc
from shypn.layout.sscc import SolarSystemLayoutEngine


def load_model(filename):
    """Load model from .shy file."""
    with open(filename) as f:
        data = json.load(f)
    
    places = []
    transitions = []
    arcs = []
    
    # Load places
    for p_data in data['places']:
        p = Place(
            id=p_data['id'],
            name=p_data['name'],
            label=p_data.get('label', ''),
            x=p_data['x'],
            y=p_data['y']
        )
        p.initial_marking = p_data.get('initial_marking', 0)
        places.append(p)
    
    # Load transitions
    for t_data in data['transitions']:
        t = Transition(
            id=t_data['id'],
            name=t_data['name'],
            label=t_data.get('label', ''),
            x=t_data['x'],
            y=t_data['y']
        )
        transitions.append(t)
    
    # Create ID lookup
    id_to_obj = {}
    for p in places:
        id_to_obj[p.id] = p
    for t in transitions:
        id_to_obj[t.id] = t
    
    # Load arcs
    for a_data in data['arcs']:
        source = id_to_obj.get(a_data['source_id'])
        target = id_to_obj.get(a_data['target_id'])
        
        if source and target:
            arc = Arc(
                id=a_data['id'],
                name=a_data.get('name', ''),
                source=source,
                target=target,
                weight=a_data.get('weight', 1)
            )
            arcs.append(arc)
    
    return places, transitions, arcs


def main():
    print("=" * 80)
    print("TESTING BLACK HOLE GALAXY WITH SCC-AWARE MASSES")
    print("=" * 80)
    
    # Load model
    model_path = os.path.join(os.path.dirname(__file__), '..', 'workspace', 'Test_flow', 'model', 'blackhole_galaxy.shy')
    places, transitions, arcs = load_model(model_path)
    
    print(f"\nLoaded model:")
    print(f"  Places: {len(places)}")
    print(f"  Transitions: {len(transitions)}")
    print(f"  Arcs: {len(arcs)}")
    
    # Create layout engine
    engine = SolarSystemLayoutEngine(
        iterations=1000,
        use_hub_masses=True  # Enable SCC-aware mass assignment
    )
    
    print("\nApplying Solar System Layout with SCC-aware masses...")
    positions = engine.apply_layout(places, transitions, arcs)
    
    # Analyze results
    print("\n" + "=" * 80)
    print("MASS ASSIGNMENT ANALYSIS")
    print("=" * 80)
    
    # Get hub statistics
    hub_stats = engine.hub_mass_assigner.get_hub_statistics()
    
    print(f"\n🌑 BLACK HOLE NODES (SCC - mass = 3000):")
    scc_nodes = []
    for node_id, mass in engine.masses.items():
        if mass == 3000.0:
            obj = None
            for p in places:
                if p.id == node_id:
                    obj = p
                    break
            if not obj:
                for t in transitions:
                    if t.id == node_id:
                        obj = t
                        break
            if obj:
                scc_nodes.append(obj)
                obj_type = "Place" if isinstance(obj, Place) else "Transition"
                print(f"  {obj.label} ({obj_type}): mass = {mass}")
    
    print(f"\n⭐ CONSTELLATION HUBS (mass = 100-300):")
    hub_nodes = []
    for node_id, mass in engine.masses.items():
        if 100 <= mass <= 300 and mass != 3000.0:
            obj = None
            for t in transitions:
                if t.id == node_id:
                    obj = t
                    break
            if obj and 'Hub' in obj.label:
                hub_nodes.append(obj)
                print(f"  {obj.label}: mass = {mass}")
    
    # Analyze positions
    print("\n" + "=" * 80)
    print("LAYOUT ANALYSIS")
    print("=" * 80)
    
    # Calculate black hole centroid
    if scc_nodes:
        bh_x = sum(positions[obj.id][0] for obj in scc_nodes) / len(scc_nodes)
        bh_y = sum(positions[obj.id][1] for obj in scc_nodes) / len(scc_nodes)
        print(f"\n🌑 Black Hole Center: ({bh_x:.1f}, {bh_y:.1f})")
        
        # Measure black hole radius (distance between nodes in SCC)
        import math
        max_dist = 0
        for i, obj1 in enumerate(scc_nodes):
            for obj2 in scc_nodes[i+1:]:
                x1, y1 = positions[obj1.id]
                x2, y2 = positions[obj2.id]
                dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                max_dist = max(max_dist, dist)
        print(f"   Black Hole Diameter: {max_dist:.1f} units")
        
        # Measure constellation distances from black hole
        if hub_nodes:
            print(f"\n⭐ Constellation Distances from Black Hole:")
            for hub in hub_nodes:
                hx, hy = positions[hub.id]
                dist = math.sqrt((hx - bh_x)**2 + (hy - bh_y)**2)
                print(f"   {hub.label}: {dist:.1f} units")
            
            # Measure constellation separation
            print(f"\n📏 Constellation-to-Constellation Distances:")
            for i, hub1 in enumerate(hub_nodes):
                for hub2 in hub_nodes[i+1:]:
                    x1, y1 = positions[hub1.id]
                    x2, y2 = positions[hub2.id]
                    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    print(f"   {hub1.label} ↔ {hub2.label}: {dist:.1f} units")
    
    print("\n" + "=" * 80)
    print("EXPECTED vs ACTUAL")
    print("=" * 80)
    print("""
Expected with SCC-aware masses (3000):
✓ Black hole nodes stay together (tight cluster at center)
✓ Black hole mass dominates (10× heavier than super-hubs)
✓ Constellations orbit at ~300-400 units from black hole
✓ Constellations separated from each other (~500+ units)
✓ Shared places attracted toward black hole
    """)
    
    print("=" * 80)
    print("✓ SCC-AWARE MASS ASSIGNMENT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
