#!/usr/bin/env python3
"""Generate test model with Galaxy structure: clusters of constellations.

Galaxy Hierarchy:
1. **Satellites** (Places) - orbit around hubs
2. **Constellations** (Hub + satellites) - stay together via arcs
3. **Galaxies** (Multiple constellations) - grouped by shared metabolites/pathways
4. **Universe** (Multiple galaxies) - separated from each other

This tests multi-level clustering:
- Constellation cohesion (hub group repulsion keeps satellites together)
- Galaxy cohesion (shared places connect constellations within galaxy)
- Galaxy separation (galaxies repel each other at super-cluster level)

Model Structure:
- 3 Galaxies
- Each galaxy has 3 hub transitions (constellations)
- Each hub has 4 satellites (2 inputs, 2 outputs)
- Shared places connect hubs within same galaxy
- No connections between different galaxies

Total: 9 hubs, 36 exclusive places, 6 shared places within galaxies
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


def generate_galaxy_model():
    """Generate model with 3 galaxies, each containing 3 constellations.
    
    Galaxy positions (widely separated to test galaxy-level repulsion):
    - Galaxy A: center at (-800, 0)
    - Galaxy B: center at (800, 0)
    - Galaxy C: center at (0, 800)
    
    Each galaxy has:
    - 3 hub transitions arranged in triangle
    - 4 satellites per hub (2 inputs, 2 outputs)
    - 3 shared places connecting the 3 hubs
    """
    
    places = []
    transitions = []
    arcs = []
    
    # Galaxy configurations: (galaxy_id, name, center_x, center_y)
    galaxies = [
        ('A', 'Glycolysis', -800, 0),
        ('B', 'TCA Cycle', 800, 0),
        ('C', 'Pentose Phosphate', 0, 800),
    ]
    
    place_id = 0
    transition_id = 100
    arc_id = 1000
    
    # Create each galaxy
    for galaxy_id, galaxy_name, gal_x, gal_y in galaxies:
        
        # Hub positions within galaxy (triangle formation, 300 units apart)
        hub_offsets = [
            (-150, -100),  # Left hub
            (150, -100),   # Right hub
            (0, 150),      # Top hub
        ]
        
        galaxy_hubs = []
        
        # Create 3 hubs for this galaxy
        for hub_idx, (offset_x, offset_y) in enumerate(hub_offsets):
            t = SimpleTransition(
                id=transition_id,
                name=f"{galaxy_name} - Reaction {hub_idx+1}",
                label=f"{galaxy_id}{hub_idx+1}",
                x=gal_x + offset_x,
                y=gal_y + offset_y
            )
            transitions.append(t)
            galaxy_hubs.append(t)
            transition_id += 1
            
            # Create 4 satellites for this hub (2 inputs, 2 outputs)
            # Inputs positioned above hub
            for i in range(2):
                offset_x_sat = 100 * (i - 0.5)  # -50, +50
                offset_y_sat = -80
                
                p = SimplePlace(
                    id=place_id,
                    name=f"{galaxy_name} - Substrate {hub_idx+1}.{i+1}",
                    label=f"S_{galaxy_id}{hub_idx+1}_{i+1}",
                    x=t.x + offset_x_sat,
                    y=t.y + offset_y_sat
                )
                places.append(p)
                
                # Arc: Place → Transition (input)
                arc = SimpleArc(
                    id=arc_id,
                    name=f"Arc_{place_id}_to_{t.id}",
                    source=p,
                    target=t,
                    weight=1.0
                )
                arcs.append(arc)
                arc_id += 1
                place_id += 1
            
            # Outputs positioned below hub
            for i in range(2):
                offset_x_sat = 100 * (i - 0.5)  # -50, +50
                offset_y_sat = 80
                
                p = SimplePlace(
                    id=place_id,
                    name=f"{galaxy_name} - Product {hub_idx+1}.{i+1}",
                    label=f"P_{galaxy_id}{hub_idx+1}_{i+1}",
                    x=t.x + offset_x_sat,
                    y=t.y + offset_y_sat
                )
                places.append(p)
                
                # Arc: Transition → Place (output)
                arc = SimpleArc(
                    id=arc_id,
                    name=f"Arc_{t.id}_to_{place_id}",
                    source=t,
                    target=p,
                    weight=1.0
                )
                arcs.append(arc)
                arc_id += 1
                place_id += 1
        
        # Create shared places connecting hubs WITHIN this galaxy
        # This creates galaxy cohesion
        shared_configs = [
            (0, 1, f"I_{galaxy_id}12", (gal_x, gal_y - 100)),  # Hub1 → P → Hub2
            (1, 2, f"I_{galaxy_id}23", (gal_x + 75, gal_y + 25)),  # Hub2 → P → Hub3
            (0, 2, f"I_{galaxy_id}13", (gal_x - 75, gal_y + 25)),  # Hub1 → P → Hub3
        ]
        
        for hub1_idx, hub2_idx, label, pos in shared_configs:
            p = SimplePlace(
                id=place_id,
                name=f"{galaxy_name} - Intermediate {hub1_idx+1}-{hub2_idx+1}",
                label=label,
                x=pos[0],
                y=pos[1]
            )
            places.append(p)
            
            # Arc 1: Hub1 → Place
            arc1 = SimpleArc(
                id=arc_id,
                name=f"Arc_{galaxy_hubs[hub1_idx].id}_to_{place_id}",
                source=galaxy_hubs[hub1_idx],
                target=p,
                weight=1.0
            )
            arcs.append(arc1)
            arc_id += 1
            
            # Arc 2: Place → Hub2
            arc2 = SimpleArc(
                id=arc_id,
                name=f"Arc_{place_id}_to_{galaxy_hubs[hub2_idx].id}",
                source=p,
                target=galaxy_hubs[hub2_idx],
                weight=1.0
            )
            arcs.append(arc2)
            arc_id += 1
            
            place_id += 1
    
    return places, transitions, arcs


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
    print(f"  - {len(places)} places")
    print(f"  - {len(transitions)} transitions")
    print(f"  - {len(arcs)} arcs")


def main():
    """Generate and save the galaxy model."""
    
    print("=" * 80)
    print("GENERATING GALAXY CLUSTER MODEL")
    print("=" * 80)
    print("\nHierarchy:")
    print("  Universe")
    print("    └─ Galaxy A (Glycolysis)")
    print("         ├─ Constellation A1 (4 satellites)")
    print("         ├─ Constellation A2 (4 satellites)")
    print("         └─ Constellation A3 (4 satellites)")
    print("         └─ 3 shared metabolites connecting constellations")
    print("    └─ Galaxy B (TCA Cycle)")
    print("         ├─ Constellation B1 (4 satellites)")
    print("         ├─ Constellation B2 (4 satellites)")
    print("         └─ Constellation B3 (4 satellites)")
    print("         └─ 3 shared metabolites connecting constellations")
    print("    └─ Galaxy C (Pentose Phosphate)")
    print("         ├─ Constellation C1 (4 satellites)")
    print("         ├─ Constellation C2 (4 satellites)")
    print("         └─ Constellation C3 (4 satellites)")
    print("         └─ 3 shared metabolites connecting constellations")
    print("\n" + "=" * 80)
    
    places, transitions, arcs = generate_galaxy_model()
    
    # Save to workspace
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "Test_flow", "model")
    os.makedirs(workspace_dir, exist_ok=True)
    
    filename = os.path.join(workspace_dir, "galaxy_clusters.shy")
    save_as_shy_v2(places, transitions, arcs, filename)
    
    print("\n" + "=" * 80)
    print("MODEL STATISTICS:")
    print("=" * 80)
    
    # Count by galaxy
    for galaxy_id in ['A', 'B', 'C']:
        galaxy_transitions = [t for t in transitions if t.label.startswith(galaxy_id)]
        galaxy_places = [p for p in places if galaxy_id in p.label]
        exclusive_places = [p for p in galaxy_places if not p.label.startswith('I_')]
        shared_places = [p for p in galaxy_places if p.label.startswith('I_')]
        
        print(f"\nGalaxy {galaxy_id}:")
        print(f"  Constellations: {len(galaxy_transitions)}")
        print(f"  Exclusive satellites: {len(exclusive_places)}")
        print(f"  Shared metabolites: {len(shared_places)}")
        print(f"  Total places: {len(galaxy_places)}")
    
    print("\n" + "=" * 80)
    print("PHYSICS PREDICTIONS:")
    print("=" * 80)
    print("\n✓ LEVEL 1 - Satellite orbits:")
    print("    Each place orbits its hub transition (~150-200 units)")
    print("    Input places (P→T) above hub, output places (T→P) below")
    
    print("\n✓ LEVEL 2 - Constellation cohesion:")
    print("    Hub + satellites stay together via oscillatory forces")
    print("    Hub group repulsion treats each constellation as unit")
    
    print("\n✓ LEVEL 3 - Galaxy cohesion:")
    print("    Shared metabolites connect 3 constellations within galaxy")
    print("    Forms triangle pattern (~300 units between hubs)")
    print("    Shared places position between connected hubs")
    
    print("\n✓ LEVEL 4 - Galaxy separation:")
    print("    Galaxies repel each other (no shared connections)")
    print("    Hub group repulsion pushes galaxies apart")
    print("    Expected separation: ~800-1200 units between galaxy centers")
    
    print("\n" + "=" * 80)
    print("EXPECTED VISUAL LAYOUT:")
    print("=" * 80)
    print("""
    Galaxy A          Galaxy B          Galaxy C
    (Glycolysis)      (TCA Cycle)       (Pentose Phosphate)
    
       A3                 B3                 C3
      /  \\               /  \\               /  \\
     A1--A2            B1--B2            C1--C2
    
    Each hub surrounded by 4 satellites (2 inputs, 2 outputs)
    Shared metabolites form triangular connections within galaxy
    Galaxies stay widely separated (~800-1200 units apart)
    """)
    
    print("=" * 80)
    print("✓ Ready to test Galaxy-level clustering in Solar System Layout!")
    print("=" * 80)


if __name__ == "__main__":
    main()
