#!/usr/bin/env python3
"""Generate test model with shared places between hub transitions.

This tests the Solar System layout algorithm's ability to handle:
- Multiple hub transitions (constellations)
- Shared places that connect to multiple hubs
- Mixed topology: some places exclusive, some shared

Structure:
- 3 hub transitions (T1, T2, T3) - mass=300 each
- Each hub has 4 exclusive satellite places
- 3 shared places that connect multiple hubs:
  - P_shared_1_2: connects T1 and T2
  - P_shared_2_3: connects T2 and T3
  - P_shared_1_3: connects T1 and T3

Expected behavior:
- Hub transitions should separate into distinct groups
- Exclusive places should orbit their hub
- Shared places should position between their connected hubs
- Topology remains correct (locality preserved)
"""

import json
import os
from shypn.netobjs import Place, Transition, Arc


def generate_shared_places_constellation():
    """Generate hub constellation model with shared places."""
    
    places = []
    transitions = []
    arcs = []
    
    # Hub positions (initial rough layout - centered around origin)
    hub_positions = [
        (-200, -150),  # T1 - left
        (200, -150),   # T2 - right
        (0, 200),      # T3 - bottom-center
    ]
    
    # Create 3 hub transitions
    for i in range(3):
        t = Transition(
            id=100 + i,
            name=f"Hub Transition {i+1}",
            label=f"T{i+1}",
            x=hub_positions[i][0],
            y=hub_positions[i][1]
        )
        transitions.append(t)
    
    place_id = 0
    arc_id = 200
    
    # Create exclusive satellite places for each hub
    for hub_idx, hub_t in enumerate(transitions):
        for sat_idx in range(4):
            # Place exclusive to this hub
            p = Place(
                id=place_id,
                name=f"Place {hub_idx+1}.{sat_idx+1}",
                label=f"P{hub_idx+1}.{sat_idx+1}",
                x=hub_t.x + (sat_idx - 2) * 50,  # Rough initial positions
                y=hub_t.y + 100
            )
            places.append(p)
            
            # Arc: Place → Transition (biological flow)
            arc = Arc(
                id=arc_id,
                name=f"Arc_{place_id}_to_{hub_t.id}",
                source=p,
                target=hub_t,
                weight=1.0
            )
            arcs.append(arc)
            arc_id += 1
            place_id += 1
    
    # Create shared places that connect multiple hubs
    shared_places_info = [
        # (hub1_idx, hub2_idx, label, position_between)
        (0, 1, "P_shared_1_2", (0, -150)),    # Between T1 and T2
        (1, 2, "P_shared_2_3", (100, 25)),    # Between T2 and T3
        (0, 2, "P_shared_1_3", (-100, 25)),   # Between T1 and T3
    ]
    
    for hub1_idx, hub2_idx, label, pos in shared_places_info:
        # Create shared place
        p = Place(
            id=place_id,
            name=f"Shared Place ({hub1_idx+1}-{hub2_idx+1})",
            label=label,
            x=pos[0],
            y=pos[1]
        )
        places.append(p)
        
        # Arc from place to first hub
        arc1 = Arc(
            id=arc_id,
            name=f"Arc_{place_id}_to_{transitions[hub1_idx].id}",
            source=p,
            target=transitions[hub1_idx],
            weight=1.0
        )
        arcs.append(arc1)
        arc_id += 1
        
        # Arc from place to second hub
        arc2 = Arc(
            id=arc_id,
            name=f"Arc_{place_id}_to_{transitions[hub2_idx].id}",
            source=p,
            target=transitions[hub2_idx],
            weight=1.0
        )
        arcs.append(arc2)
        arc_id += 1
        
        place_id += 1
    
    return places, transitions, arcs


def save_as_shy(places, transitions, arcs, filename):
    """Save model in Shypn .shy format (version 2.0)."""
    
    from datetime import datetime
    
    model_data = {
        "version": "2.0",
        "metadata": {
            "created": datetime.now().isoformat(),
            "object_counts": {
                "places": len(places),
                "transitions": len(transitions),
                "arcs": len(arcs)
            }
        },
        "view_state": {
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "transformations": {
                "rotation": {
                    "type": "rotation",
                    "angle_degrees": 0.0,
                    "enabled": True
                }
            }
        },
        "places": [],
        "transitions": [],
        "arcs": []
    }
    
    # Serialize places
    for p in places:
        model_data["places"].append({
            "id": p.id,
            "name": p.name,
            "label": p.label if p.label else "",
            "type": "place",
            "x": p.x,
            "y": p.y,
            "radius": 25.0,
            "marking": 0,
            "initial_marking": 0,
            "capacity": "Infinity",
            "border_color": [0.0, 0.0, 0.0],
            "border_width": 3.0
        })
    
    # Serialize transitions
    for t in transitions:
        model_data["transitions"].append({
            "id": t.id,
            "name": t.name,
            "label": t.label if t.label else "",
            "type": "transition",
            "x": t.x,
            "y": t.y,
            "width": 50.0,
            "height": 25.0,
            "horizontal": True,
            "enabled": True,
            "fill_color": [0.0, 0.0, 0.0],
            "border_color": [0.0, 0.0, 0.0],
            "border_width": 3.0,
            "transition_type": "continuous",
            "priority": 0,
            "firing_policy": "earliest",
            "is_source": False,
            "is_sink": False,
            "rate": 1.0
        })
    
    # Serialize arcs
    for arc in arcs:
        # Determine source and target types
        source_type = "place" if hasattr(arc.source, 'radius') else "transition"
        target_type = "place" if hasattr(arc.target, 'radius') else "transition"
        
        model_data["arcs"].append({
            "id": arc.id,
            "name": f"A{arc.id}",
            "label": "",
            "type": "arc",
            "source_id": arc.source.id,
            "source_type": source_type,
            "target_id": arc.target.id,
            "target_type": target_type,
            "weight": int(arc.weight),
            "color": [0.0, 0.0, 0.0],
            "width": 3.0,
            "control_points": []
        })
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(model_data, f, indent=2)
    
    print(f"✓ Saved model to {filename}")
    print(f"  - {len(places)} places ({len([p for p in places if 'shared' in p.label.lower()])} shared)")
    print(f"  - {len(transitions)} hub transitions")
    print(f"  - {len(arcs)} arcs")


def main():
    """Generate and save the test model."""
    
    print("Generating shared places constellation model...")
    print("=" * 80)
    
    places, transitions, arcs = generate_shared_places_constellation()
    
    # Save to workspace
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "Test_flow", "model")
    os.makedirs(workspace_dir, exist_ok=True)
    
    filename = os.path.join(workspace_dir, "shared_places_constellation.shy")
    save_as_shy(places, transitions, arcs, filename)
    
    print("\n" + "=" * 80)
    print("STRUCTURE SUMMARY:")
    print("=" * 80)
    print("\nHub Transitions (3):")
    for t in transitions:
        print(f"  - {t.label}: {t.name}")
    
    print("\nExclusive Places (12 total, 4 per hub):")
    exclusive = [p for p in places if 'shared' not in p.label.lower()]
    for i in range(3):
        hub_places = [p for p in exclusive if p.label.startswith(f"P{i+1}.")]
        print(f"  Hub T{i+1}: {', '.join(p.label for p in hub_places)}")
    
    print("\nShared Places (3):")
    shared = [p for p in places if 'shared' in p.label.lower()]
    for p in shared:
        # Find which hubs this place connects to
        connected_hubs = []
        for arc in arcs:
            if arc.source == p:
                connected_hubs.append(arc.target.label)
        print(f"  - {p.label}: connects {' and '.join(connected_hubs)}")
    
    print("\n" + "=" * 80)
    print("EXPECTED LAYOUT BEHAVIOR:")
    print("=" * 80)
    print("1. Hub transitions separate into 3 distinct groups")
    print("2. Exclusive places orbit their hub (~150-200 units)")
    print("3. Shared places position between connected hubs")
    print("4. Hub separation ~300-425 units (canvas-friendly)")
    print("5. Topology preserved (locality principle maintained)")
    print("\nReady to test in canvas with Solar System Layout!")


if __name__ == "__main__":
    main()
