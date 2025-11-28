#!/usr/bin/env python3
"""Generate galaxy with BLACK HOLE (SCC/cycle) at center.

Concept:
- Black Hole = Strongly Connected Component (cycle) at galaxy center
- Constellations = Hub transitions orbiting the black hole
- Shared places = Attracted toward black hole gravity well

Structure:
- 1 Black Hole (3-node cycle: P1→T1→P2→T2→P3→T3→P1)
- 3 Constellations orbiting black hole (each with 3 satellites)
- Shared places connecting constellations to black hole
"""

import json
import os
from datetime import datetime


class SimplePlace:
    def __init__(self, id, name, label, x, y):
        self.id = id
        self.name = name
        self.label = label
        self.x = x
        self.y = y
        self.radius = 25.0


class SimpleTransition:
    def __init__(self, id, name, label, x, y):
        self.id = id
        self.name = name
        self.label = label
        self.x = x
        self.y = y
        self.width = 50.0
        self.height = 25.0


class SimpleArc:
    def __init__(self, id, name, source, target, weight):
        self.id = id
        self.name = name
        self.source = source
        self.target = target
        self.weight = weight


def generate_blackhole_galaxy():
    """Generate galaxy with black hole (cycle/SCC) at center.
    
    Structure:
    1. Black Hole (SCC): 3 transitions + 3 places forming cycle
    2. 3 Constellations: Each has 1 hub transition + 2 satellites
    3. Shared places: Connect constellations to black hole nodes
    """
    
    places = []
    transitions = []
    arcs = []
    
    place_id = 0
    transition_id = 100
    arc_id = 1000
    
    # ==========================================
    # BLACK HOLE (SCC - Cycle at center)
    # ==========================================
    
    blackhole_positions = [
        (0, -100),    # Top
        (87, 50),     # Bottom-right (120 degree spacing)
        (-87, 50),    # Bottom-left
    ]
    
    blackhole_transitions = []
    blackhole_places = []
    
    print("Creating BLACK HOLE (SCC/Cycle)...")
    
    for i in range(3):
        # Create transition in black hole
        t = SimpleTransition(
            id=transition_id,
            name=f"Black Hole Reaction {i+1}",
            label=f"BH_T{i+1}",
            x=blackhole_positions[i][0],
            y=blackhole_positions[i][1]
        )
        transitions.append(t)
        blackhole_transitions.append(t)
        transition_id += 1
        
        # Create place in black hole
        # Position between current and next transition
        next_i = (i + 1) % 3
        mid_x = (blackhole_positions[i][0] + blackhole_positions[next_i][0]) / 2
        mid_y = (blackhole_positions[i][1] + blackhole_positions[next_i][1]) / 2
        
        p = SimplePlace(
            id=place_id,
            name=f"Black Hole Metabolite {i+1}",
            label=f"BH_P{i+1}",
            x=mid_x,
            y=mid_y
        )
        places.append(p)
        blackhole_places.append(p)
        place_id += 1
    
    # Create CYCLE: T1→P1→T2→P2→T3→P3→T1 (back to start)
    for i in range(3):
        next_i = (i + 1) % 3
        
        # Arc: Ti → Pi
        arc1 = SimpleArc(
            id=arc_id,
            name=f"Arc_BH_T{i+1}_to_P{i+1}",
            source=blackhole_transitions[i],
            target=blackhole_places[i],
            weight=1.0
        )
        arcs.append(arc1)
        arc_id += 1
        
        # Arc: Pi → T(i+1)
        arc2 = SimpleArc(
            id=arc_id,
            name=f"Arc_BH_P{i+1}_to_T{next_i+1}",
            source=blackhole_places[i],
            target=blackhole_transitions[next_i],
            weight=1.0
        )
        arcs.append(arc2)
        arc_id += 1
    
    print(f"✓ Black hole created: {len(blackhole_transitions)} transitions, {len(blackhole_places)} places")
    print("  Cycle: BH_T1→BH_P1→BH_T2→BH_P2→BH_T3→BH_P3→BH_T1")
    
    # ==========================================
    # CONSTELLATIONS (Orbiting black hole)
    # ==========================================
    
    constellation_positions = [
        (0, -400),      # Top constellation
        (346, 200),     # Bottom-right (120 degrees)
        (-346, 200),    # Bottom-left
    ]
    
    print("\nCreating CONSTELLATIONS orbiting black hole...")
    
    constellation_hubs = []
    
    for const_idx, (cx, cy) in enumerate(constellation_positions):
        # Create hub transition for this constellation
        t = SimpleTransition(
            id=transition_id,
            name=f"Constellation {const_idx+1} - Hub",
            label=f"C{const_idx+1}_Hub",
            x=cx,
            y=cy
        )
        transitions.append(t)
        constellation_hubs.append(t)
        transition_id += 1
        
        # Create 2 satellite places
        for sat_idx in range(2):
            offset_x = 100 if sat_idx == 0 else -100
            offset_y = 0
            
            p = SimplePlace(
                id=place_id,
                name=f"Constellation {const_idx+1} - Satellite {sat_idx+1}",
                label=f"C{const_idx+1}_S{sat_idx+1}",
                x=cx + offset_x,
                y=cy + offset_y
            )
            places.append(p)
            
            # Arc: Satellite → Hub (input)
            arc = SimpleArc(
                id=arc_id,
                name=f"Arc_C{const_idx+1}_S{sat_idx+1}_to_Hub",
                source=p,
                target=t,
                weight=1.0
            )
            arcs.append(arc)
            arc_id += 1
            place_id += 1
    
    print(f"✓ {len(constellation_hubs)} constellations created")
    
    # ==========================================
    # SHARED PLACES (Connect constellations to black hole)
    # ==========================================
    
    print("\nCreating SHARED PLACES (constellation ↔ black hole)...")
    
    # Each constellation connects to one black hole transition
    for const_idx, hub in enumerate(constellation_hubs):
        # Connect to corresponding black hole transition
        bh_transition = blackhole_transitions[const_idx]
        
        # Shared place position: between constellation and black hole
        mid_x = (hub.x + bh_transition.x) / 2
        mid_y = (hub.y + bh_transition.y) / 2
        
        p_shared = SimplePlace(
            id=place_id,
            name=f"Shared: Constellation {const_idx+1} ↔ Black Hole",
            label=f"SH_{const_idx+1}",
            x=mid_x,
            y=mid_y
        )
        places.append(p_shared)
        
        # Arc 1: Constellation Hub → Shared Place
        arc1 = SimpleArc(
            id=arc_id,
            name=f"Arc_C{const_idx+1}_to_SH",
            source=hub,
            target=p_shared,
            weight=1.0
        )
        arcs.append(arc1)
        arc_id += 1
        
        # Arc 2: Shared Place → Black Hole Transition
        arc2 = SimpleArc(
            id=arc_id,
            name=f"Arc_SH_to_BH_T{const_idx+1}",
            source=p_shared,
            target=bh_transition,
            weight=1.0
        )
        arcs.append(arc2)
        arc_id += 1
        
        place_id += 1
    
    print(f"✓ 3 shared places created (feeding into black hole)")
    
    return places, transitions, arcs, len(blackhole_transitions), len(blackhole_places)


def save_as_shy_v2(places, transitions, arcs, filename):
    """Save model in Shypn .shy format version 2.0."""
    
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
    
    with open(filename, 'w') as f:
        json.dump(model_data, f, indent=2)
    
    print(f"\n✓ Saved model to {filename}")


def main():
    """Generate and save the black hole galaxy model."""
    
    print("=" * 80)
    print("GENERATING BLACK HOLE GALAXY MODEL")
    print("=" * 80)
    print()
    
    places, transitions, arcs, bh_transitions, bh_places = generate_blackhole_galaxy()
    
    # Save to workspace
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "Test_flow", "model")
    os.makedirs(workspace_dir, exist_ok=True)
    
    filename = os.path.join(workspace_dir, "blackhole_galaxy.shy")
    save_as_shy_v2(places, transitions, arcs, filename)
    
    print("\n" + "=" * 80)
    print("MODEL SUMMARY")
    print("=" * 80)
    print(f"\n🌑 BLACK HOLE (SCC - Strongly Connected Component):")
    print(f"   - {bh_transitions} transitions in cycle")
    print(f"   - {bh_places} places in cycle")
    print(f"   - Forms feedback loop: T1→P1→T2→P2→T3→P3→T1")
    print(f"   - MASSIVE combined gravitational mass")
    
    exclusive_places = len([p for p in places if p.label.startswith('C')])
    shared_places = len([p for p in places if p.label.startswith('SH')])
    
    print(f"\n⭐ CONSTELLATIONS:")
    print(f"   - 3 constellations orbiting black hole")
    print(f"   - Each has 1 hub + 2 satellites")
    print(f"   - {exclusive_places} exclusive places total")
    
    print(f"\n🌀 SHARED PLACES:")
    print(f"   - {shared_places} shared places")
    print(f"   - Connect constellations → black hole")
    print(f"   - Gravitationally attracted to black hole center")
    
    print(f"\n📊 TOTAL:")
    print(f"   - Places: {len(places)}")
    print(f"   - Transitions: {len(transitions)}")
    print(f"   - Arcs: {len(arcs)}")
    
    print("\n" + "=" * 80)
    print("PHYSICS PREDICTIONS")
    print("=" * 80)
    print("""
🌑 BLACK HOLE (SCC) at center:
   - Tarjan's algorithm will detect the 3-node cycle
   - Combined mass = 3 transitions × mass + 3 places × mass
   - Acts as gravitational singularity
   - Creates deep gravity well

⭐ CONSTELLATIONS orbit black hole:
   - Each constellation: hub + satellites stay together
   - Orbit radius: ~300-400 units from black hole
   - Constellation separation: 120 degrees around black hole

🌀 SHARED PLACES attracted to black hole:
   - Position between constellation and black hole
   - Pulled toward black hole center
   - Creates spiral arms feeding into black hole

Graph Theory:
✓ SCC detected by Tarjan's algorithm
✓ Highest PageRank centrality (tokens get trapped)
✓ All paths lead TO black hole (attractor)
✓ Tokens never escape (event horizon)

Physics:
✓ Black hole = infinite density → highest mass
✓ Gravity well → objects orbit around it
✓ Shared places = matter spiraling into black hole
✓ Constellations = stars orbiting galactic center
    """)
    
    print("=" * 80)
    print("✓ Ready to test BLACK HOLE galaxy in Solar System Layout!")
    print("=" * 80)


if __name__ == "__main__":
    main()
