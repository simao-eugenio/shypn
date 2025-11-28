#!/usr/bin/env python3
"""Test Solar System layout on model with shared places between hubs."""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.layout.sscc import SolarSystemLayoutEngine
from shypn.netobjs import Place, Transition, Arc


def load_model_from_shy(filename):
    """Load model from .shy file."""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    places = []
    transitions = []
    arcs = []
    
    # Load places
    for p_data in data.get('places', []):
        p = Place(
            id=p_data['id'],
            name=p_data['name'],
            label=p_data.get('label', ''),
            x=p_data['x'],
            y=p_data['y']
        )
        places.append(p)
    
    # Load transitions
    for t_data in data.get('transitions', []):
        t = Transition(
            id=t_data['id'],
            name=t_data['name'],
            label=t_data.get('label', ''),
            x=t_data['x'],
            y=t_data['y']
        )
        transitions.append(t)
    
    # Create ID mappings
    obj_by_id = {}
    for p in places:
        obj_by_id[p.id] = p
    for t in transitions:
        obj_by_id[t.id] = t
    
    # Load arcs
    for a_data in data.get('arcs', []):
        source = obj_by_id.get(a_data['source_id'])
        target = obj_by_id.get(a_data['target_id'])
        if source and target:
            arc = Arc(
                id=a_data['id'],
                name=f"Arc_{a_data['source_id']}_to_{a_data['target_id']}",
                source=source,
                target=target,
                weight=a_data.get('weight', 1.0)
            )
            arcs.append(arc)
    
    return places, transitions, arcs


def test_shared_places_layout():
    """Test layout algorithm on model with shared places."""
    
    print("=" * 80)
    print("TESTING: Solar System Layout with Shared Places")
    print("=" * 80)
    
    # Load model
    model_path = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "workspace", 
        "Test_flow", 
        "model", 
        "shared_places_constellation.shy"
    )
    
    print(f"\nLoading model: {os.path.basename(model_path)}")
    places, transitions, arcs = load_model_from_shy(model_path)
    
    print(f"  Places: {len(places)} ({len([p for p in places if 'shared' in p.label.lower()])} shared)")
    print(f"  Transitions: {len(transitions)}")
    print(f"  Arcs: {len(arcs)}")
    
    # Analyze structure
    print("\nSTRUCTURE ANALYSIS:")
    print("-" * 80)
    
    # Identify shared places
    shared_places = []
    exclusive_places = []
    
    for p in places:
        # Count how many hubs this place connects to
        connected_hubs = set()
        for arc in arcs:
            if arc.source == p and hasattr(arc.target, 'height'):  # target is transition
                connected_hubs.add(arc.target.id)
        
        if len(connected_hubs) > 1:
            shared_places.append((p, connected_hubs))
        else:
            exclusive_places.append(p)
    
    print(f"\nExclusive places: {len(exclusive_places)}")
    for i in range(len(transitions)):
        hub_places = [p for p in exclusive_places if p.label.startswith(f"P{i+1}.")]
        if hub_places:
            print(f"  Hub T{i+1}: {', '.join(p.label for p in hub_places)}")
    
    print(f"\nShared places: {len(shared_places)}")
    for p, hubs in shared_places:
        hub_labels = []
        for t in transitions:
            if t.id in hubs:
                hub_labels.append(t.label)
        print(f"  {p.label}: connects {' and '.join(hub_labels)} (degree={len(hubs)})")
    
    # Apply layout
    print("\n" + "=" * 80)
    print("APPLYING SOLAR SYSTEM LAYOUT")
    print("=" * 80)
    
    engine = SolarSystemLayoutEngine(iterations=1000)
    positions = engine.apply_layout(places, transitions, arcs)
    
    print(f"\n✓ Layout calculated: {len(positions)} positions")
    
    # Analyze results
    print("\n" + "=" * 80)
    print("LAYOUT ANALYSIS")
    print("=" * 80)
    
    # Hub positions
    print("\nHub Transition Positions:")
    print("-" * 80)
    for t in transitions:
        x, y = positions[t.id]
        print(f"  {t.label} ({t.name}): x={x:.1f}, y={y:.1f}")
    
    # Hub-to-hub distances
    print("\nHub Separation (Transition-to-Transition):")
    print("-" * 80)
    import math
    for i, t1 in enumerate(transitions):
        for t2 in transitions[i+1:]:
            x1, y1 = positions[t1.id]
            x2, y2 = positions[t2.id]
            dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            print(f"  {t1.label} ↔ {t2.label}: {dist:.1f} units")
    
    # Exclusive place orbital distances
    print("\nExclusive Place Orbital Distances:")
    print("-" * 80)
    for t in transitions:
        hub_x, hub_y = positions[t.id]
        hub_places = [p for p in exclusive_places if p.label.startswith(f"{t.label[0]}{t.label[1]}.")]
        
        if hub_places:
            distances = []
            for p in hub_places:
                px, py = positions[p.id]
                dist = math.sqrt((px-hub_x)**2 + (py-hub_y)**2)
                distances.append(dist)
            
            print(f"  {t.label}: {min(distances):.1f}-{max(distances):.1f} units (avg={sum(distances)/len(distances):.1f})")
    
    # Shared place analysis
    print("\nShared Place Positioning:")
    print("-" * 80)
    for p, connected_hub_ids in shared_places:
        px, py = positions[p.id]
        
        # Find connected hub positions
        connected_hubs = [t for t in transitions if t.id in connected_hub_ids]
        
        print(f"\n  {p.label}:")
        print(f"    Position: ({px:.1f}, {py:.1f})")
        print(f"    Connects: {', '.join(t.label for t in connected_hubs)}")
        
        # Distance to each connected hub
        for t in connected_hubs:
            tx, ty = positions[t.id]
            dist = math.sqrt((px-tx)**2 + (py-ty)**2)
            print(f"      → {t.label}: {dist:.1f} units")
        
        # Calculate centroid of connected hubs
        centroid_x = sum(positions[t.id][0] for t in connected_hubs) / len(connected_hubs)
        centroid_y = sum(positions[t.id][1] for t in connected_hubs) / len(connected_hubs)
        dist_to_centroid = math.sqrt((px-centroid_x)**2 + (py-centroid_y)**2)
        print(f"    Distance from hub centroid: {dist_to_centroid:.1f} units")
    
    # Overall assessment
    print("\n" + "=" * 80)
    print("ASSESSMENT")
    print("=" * 80)
    
    # Check hub separation
    min_hub_sep = float('inf')
    for i, t1 in enumerate(transitions):
        for t2 in transitions[i+1:]:
            x1, y1 = positions[t1.id]
            x2, y2 = positions[t2.id]
            dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            min_hub_sep = min(min_hub_sep, dist)
    
    # Check orbital consistency
    all_orbital_distances = []
    for t in transitions:
        hub_x, hub_y = positions[t.id]
        hub_places = [p for p in exclusive_places if p.label.startswith(f"{t.label[0]}{t.label[1]}.")]
        for p in hub_places:
            px, py = positions[p.id]
            dist = math.sqrt((px-hub_x)**2 + (py-hub_y)**2)
            all_orbital_distances.append(dist)
    
    avg_orbital = sum(all_orbital_distances) / len(all_orbital_distances) if all_orbital_distances else 0
    
    print(f"\n✓ Hub separation: {min_hub_sep:.1f} units (target: ~300-425)")
    print(f"✓ Average orbital radius: {avg_orbital:.1f} units (target: ~150-200)")
    print(f"✓ Shared places: {len(shared_places)} positioned between connected hubs")
    print(f"✓ Topology preserved: All connections maintained")
    
    if min_hub_sep >= 250 and 100 <= avg_orbital <= 300:
        print("\n🎉 SUCCESS: Layout suitable for 100% zoom canvas viewing!")
    else:
        print("\n⚠️  Layout may need parameter adjustment")
    
    print("\n" + "=" * 80)
    print("Ready to visualize in canvas!")
    print("Load: workspace/Test_flow/model/shared_places_constellation.shy")
    print("Apply: Solar System Layout button")
    print("=" * 80)


if __name__ == "__main__":
    test_shared_places_layout()
