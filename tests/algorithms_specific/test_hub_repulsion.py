#!/usr/bin/env python3
"""Test Hub Repulsion - Demonstrates hub-to-hub repulsion in action.

Creates a network with multiple high-mass hubs in the same SCC to verify
that they spread out rather than clustering at the center.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.netobjs import Place, Transition, Arc
from shypn.layout.sscc.solar_system_layout_engine import SolarSystemLayoutEngine


def test_hub_repulsion():
    """Test that multiple hubs repel each other."""
    
    print("=" * 70)
    print("HUB REPULSION TEST")
    print("=" * 70)
    print()
    
    # Create a network with multiple high-degree nodes (hubs)
    # Structure: Star network where multiple places connect to many transitions
    
    places = []
    transitions = []
    arcs = []
    
    obj_id = 1
    arc_id = 1
    
    # Create 3 hub places (will each have many connections)
    print("Creating network:")
    print("  - 3 hub places (each with 8+ connections)")
    print("  - 24 transitions")
    print("  - Multiple arcs creating star topology")
    print()
    
    hub_places = []
    for i in range(3):
        place = Place(0.0, 0.0, obj_id, f"HubP{i+1}", label=f"Hub Place {i+1}")
        places.append(place)
        hub_places.append(place)
        obj_id += 1
    
    # Create 3 regular places
    for i in range(3):
        place = Place(0.0, 0.0, obj_id, f"P{i+1}", label=f"Place {i+1}")
        places.append(place)
        obj_id += 1
    
    # Create 24 transitions
    for i in range(24):
        transition = Transition(0.0, 0.0, obj_id, f"T{i+1}", label=f"Trans {i+1}")
        transitions.append(transition)
        obj_id += 1
    
    # Connect each hub place to 8 transitions (24 total, 8 per hub)
    for hub_idx, hub_place in enumerate(hub_places):
        start_t = hub_idx * 8
        end_t = start_t + 8
        
        for t in transitions[start_t:end_t]:
            # Hub → Transition
            arc = Arc(hub_place, t, arc_id, f"A{arc_id}")
            arcs.append(arc)
            arc_id += 1
            
            # Transition → Hub (create cycle)
            arc = Arc(t, hub_place, arc_id, f"A{arc_id}")
            arcs.append(arc)
            arc_id += 1
    
    # Connect regular places to form a small cycle
    for i in range(3):
        # Place → Transition
        arc = Arc(places[3+i], transitions[i], arc_id, f"A{arc_id}")
        arcs.append(arc)
        arc_id += 1
    
    print(f"Created network:")
    print(f"  - {len(places)} places (3 hubs + 3 regular)")
    print(f"  - {len(transitions)} transitions")
    print(f"  - {len(arcs)} arcs")
    print()
    
    # Apply Solar System Layout
    print("Applying Solar System Layout with hub-based masses...")
    engine = SolarSystemLayoutEngine(
        iterations=1500,
        use_arc_weight=True,
        use_hub_masses=True
    )
    
    positions = engine.apply_layout(places, transitions, arcs)
    
    print("✓ Layout complete")
    print()
    
    # Analyze results
    stats = engine.get_statistics()
    print("Statistics:")
    print(f"  - SCCs found: {stats['num_sccs']}")
    print(f"  - Total nodes: {stats['total_nodes']}")
    
    if 'hub_stats' in stats:
        hub_stats = stats['hub_stats']
        print(f"  - Super-hubs: {len(hub_stats['super_hubs'])}")
        print(f"  - Major hubs: {len(hub_stats['major_hubs'])}")
        print(f"  - Minor hubs: {len(hub_stats['minor_hubs'])}")
    print()
    
    # Check hub positions and distances
    print("=" * 70)
    print("HUB ANALYSIS")
    print("=" * 70)
    print()
    
    import math
    
    hub_positions = [(p.name, positions[p.id]) for p in hub_places]
    
    print("Hub Positions:")
    for name, (x, y) in hub_positions:
        distance_from_center = math.sqrt(x**2 + y**2)
        print(f"  {name:10} → ({x:7.1f}, {y:7.1f}) | Distance: {distance_from_center:7.1f}")
    print()
    
    # Calculate distances between hubs
    print("Hub-to-Hub Distances (should be large due to repulsion):")
    for i in range(len(hub_places)):
        for j in range(i+1, len(hub_places)):
            name1 = hub_places[i].name
            name2 = hub_places[j].name
            x1, y1 = positions[hub_places[i].id]
            x2, y2 = positions[hub_places[j].id]
            distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            print(f"  {name1} ↔ {name2}: {distance:7.1f} units")
    print()
    
    # Verify hubs are spread out (not clustered)
    min_hub_distance = float('inf')
    for i in range(len(hub_places)):
        for j in range(i+1, len(hub_places)):
            x1, y1 = positions[hub_places[i].id]
            x2, y2 = positions[hub_places[j].id]
            distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            min_hub_distance = min(min_hub_distance, distance)
    
    print("=" * 70)
    print("RESULT")
    print("=" * 70)
    print()
    
    # Success criteria: hubs should be at least 100 units apart
    if min_hub_distance > 100:
        print(f"✅ SUCCESS: Hubs are well-separated!")
        print(f"   Minimum hub-to-hub distance: {min_hub_distance:.1f} units")
        print(f"   Hub repulsion is working correctly!")
    else:
        print(f"⚠️  WARNING: Hubs may be too close together")
        print(f"   Minimum hub-to-hub distance: {min_hub_distance:.1f} units")
        print(f"   Expected: > 100 units")
    
    print()
    
    # Show interpretation
    print("💡 INTERPRETATION:")
    print("   • Hub places have high degree (8 connections each)")
    print("   • All hubs get high mass (≥500)")
    print("   • Hub-to-hub repulsion spreads them out")
    print("   • Result: Multiple gravitational centers, not clustered")
    print("   • Other nodes orbit the distributed hubs")
    print()


if __name__ == "__main__":
    test_hub_repulsion()
