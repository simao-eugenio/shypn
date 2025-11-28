#!/usr/bin/env python3
"""Generate model with Galaxy Cluster hierarchy.

Hierarchy (4 levels):
1. **Satellites** (Places) - orbit hubs (~150-200 units)
2. **Constellations** (Hub + satellites) - stay together via arcs
3. **Galaxies** (Group of constellations) - connected by shared places
4. **Galaxy Clusters** (Group of galaxies) - separated from other clusters

Structure:
- 2 Galaxy Clusters (widely separated)
- Each cluster has 2 galaxies
- Each galaxy has 2 constellations (hubs)
- Each constellation has 3 satellites

Total:
- 2 clusters × 2 galaxies × 2 hubs = 8 hubs
- 8 hubs × 3 satellites = 24 exclusive places
- 2 galaxies per cluster × 1 shared place = 4 shared places within galaxies
- 2 clusters × 1 shared place = 2 shared places within clusters
- Total: 24 + 4 + 2 = 30 places, 8 transitions

Connectivity:
- Within constellation: satellites orbit hub (arc connections)
- Within galaxy: shared places connect 2 hubs
- Within cluster: 1 shared place connects the 2 galaxies
- Between clusters: NO connections (they repel via hub group repulsion)
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


def generate_galaxy_clusters_model():
    """Generate model with 2 galaxy clusters, each containing 2 galaxies.
    
    Cluster positions (very widely separated to test cluster-level repulsion):
    - Cluster 1: center at (-1200, 0)
      - Galaxy A: center at (-1400, 0)
      - Galaxy B: center at (-1000, 0)
    - Cluster 2: center at (1200, 0)
      - Galaxy C: center at (1000, 0)
      - Galaxy D: center at (1400, 0)
    
    Each galaxy has:
    - 2 hub transitions (constellations) separated by ~300 units
    - 3 satellites per hub (2 inputs + 1 output) for compact visualization
    - 1 shared place connecting the 2 hubs within galaxy
    
    Each cluster has:
    - 1 shared place connecting the 2 galaxies (inter-galaxy connection)
    """
    
    places = []
    transitions = []
    arcs = []
    
    # Cluster configurations: (cluster_id, cluster_name, cluster_x)
    # Each cluster has 2 galaxies
    clusters_config = [
        {
            'cluster_id': 'Cluster1',
            'cluster_name': 'Metabolic Cluster',
            'cluster_x': -1200,
            'galaxies': [
                {'galaxy_id': 'A', 'galaxy_name': 'Glycolysis', 'offset_x': -200},
                {'galaxy_id': 'B', 'galaxy_name': 'Fermentation', 'offset_x': 200},
            ]
        },
        {
            'cluster_id': 'Cluster2',
            'cluster_name': 'Biosynthesis Cluster',
            'cluster_x': 1200,
            'galaxies': [
                {'galaxy_id': 'C', 'galaxy_name': 'Amino Acids', 'offset_x': -200},
                {'galaxy_id': 'D', 'galaxy_name': 'Nucleotides', 'offset_x': 200},
            ]
        },
    ]
    
    place_id = 0
    transition_id = 100
    arc_id = 1000
    
    cluster_data = []  # Store cluster info for creating inter-galaxy connections
    
    # Create each cluster
    for cluster_config in clusters_config:
        cluster_id = cluster_config['cluster_id']
        cluster_name = cluster_config['cluster_name']
        cluster_x = cluster_config['cluster_x']
        
        cluster_galaxies = []  # Store galaxy hubs for inter-galaxy connections
        
        # Create each galaxy in the cluster
        for galaxy_config in cluster_config['galaxies']:
            galaxy_id = galaxy_config['galaxy_id']
            galaxy_name = galaxy_config['galaxy_name']
            gal_x = cluster_x + galaxy_config['offset_x']
            gal_y = 0
            
            # Hub positions within galaxy (2 hubs, vertically separated)
            hub_offsets = [
                (0, -150),   # Top hub
                (0, 150),    # Bottom hub
            ]
            
            galaxy_hubs = []
            
            # Create 2 hubs for this galaxy
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
                
                # Create 3 satellites for this hub (2 inputs, 1 output)
                # 2 Inputs positioned to the left
                for i in range(2):
                    offset_x_sat = -100
                    offset_y_sat = 60 * (i - 0.5)  # -30, +30
                    
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
                
                # 1 Output positioned to the right
                p = SimplePlace(
                    id=place_id,
                    name=f"{galaxy_name} - Product {hub_idx+1}",
                    label=f"P_{galaxy_id}{hub_idx+1}",
                    x=t.x + 100,
                    y=t.y
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
            
            # Create 1 shared place connecting the 2 hubs WITHIN this galaxy
            # (This creates galaxy cohesion)
            p_shared_galaxy = SimplePlace(
                id=place_id,
                name=f"{galaxy_name} - Intermediate 1-2",
                label=f"I_{galaxy_id}",
                x=gal_x,
                y=gal_y
            )
            places.append(p_shared_galaxy)
            
            # Hub1 → Shared → Hub2
            arc1 = SimpleArc(
                id=arc_id,
                name=f"Arc_{galaxy_hubs[0].id}_to_{place_id}",
                source=galaxy_hubs[0],
                target=p_shared_galaxy,
                weight=1.0
            )
            arcs.append(arc1)
            arc_id += 1
            
            arc2 = SimpleArc(
                id=arc_id,
                name=f"Arc_{place_id}_to_{galaxy_hubs[1].id}",
                source=p_shared_galaxy,
                target=galaxy_hubs[1],
                weight=1.0
            )
            arcs.append(arc2)
            arc_id += 1
            place_id += 1
            
            cluster_galaxies.append({
                'galaxy_id': galaxy_id,
                'hubs': galaxy_hubs,
                'center_x': gal_x,
                'center_y': gal_y
            })
        
        # Create 1 shared place connecting the 2 GALAXIES within this cluster
        # (This creates cluster cohesion - galaxies within cluster stay together)
        # Connect first hub of Galaxy 1 to first hub of Galaxy 2
        p_shared_cluster = SimplePlace(
            id=place_id,
            name=f"{cluster_name} - Inter-galaxy Metabolite",
            label=f"IC_{cluster_id}",
            x=cluster_x,
            y=0
        )
        places.append(p_shared_cluster)
        
        # Galaxy1.Hub1 → Shared → Galaxy2.Hub1
        arc1 = SimpleArc(
            id=arc_id,
            name=f"Arc_{cluster_galaxies[0]['hubs'][0].id}_to_{place_id}",
            source=cluster_galaxies[0]['hubs'][0],
            target=p_shared_cluster,
            weight=1.0
        )
        arcs.append(arc1)
        arc_id += 1
        
        arc2 = SimpleArc(
            id=arc_id,
            name=f"Arc_{place_id}_to_{cluster_galaxies[1]['hubs'][0].id}",
            source=p_shared_cluster,
            target=cluster_galaxies[1]['hubs'][0],
            weight=1.0
        )
        arcs.append(arc2)
        arc_id += 1
        place_id += 1
        
        cluster_data.append({
            'cluster_id': cluster_id,
            'galaxies': cluster_galaxies,
            'center_x': cluster_x
        })
    
    # NO connections between Cluster1 and Cluster2
    # They will repel each other via hub group repulsion
    
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
    """Generate and save the galaxy clusters model."""
    
    print("=" * 80)
    print("GENERATING GALAXY CLUSTERS MODEL")
    print("=" * 80)
    print("\n4-LEVEL HIERARCHY:")
    print("=" * 80)
    print("""
    UNIVERSE
      │
      ├─ CLUSTER 1 (Metabolic Cluster)
      │    │
      │    ├─ GALAXY A (Glycolysis)
      │    │    ├─ Constellation A1 (3 satellites)
      │    │    ├─ Constellation A2 (3 satellites)
      │    │    └─ 1 shared metabolite (A1 ↔ A2)
      │    │
      │    ├─ GALAXY B (Fermentation)
      │    │    ├─ Constellation B1 (3 satellites)
      │    │    ├─ Constellation B2 (3 satellites)
      │    │    └─ 1 shared metabolite (B1 ↔ B2)
      │    │
      │    └─ 1 inter-galaxy metabolite (Galaxy A ↔ Galaxy B)
      │
      └─ CLUSTER 2 (Biosynthesis Cluster)
           │
           ├─ GALAXY C (Amino Acids)
           │    ├─ Constellation C1 (3 satellites)
           │    ├─ Constellation C2 (3 satellites)
           │    └─ 1 shared metabolite (C1 ↔ C2)
           │
           ├─ GALAXY D (Nucleotides)
           │    ├─ Constellation D1 (3 satellites)
           │    ├─ Constellation D2 (3 satellites)
           │    └─ 1 shared metabolite (D1 ↔ D2)
           │
           └─ 1 inter-galaxy metabolite (Galaxy C ↔ Galaxy D)
    
    NO CONNECTIONS BETWEEN CLUSTER 1 AND CLUSTER 2
    (They repel each other via hub group repulsion)
    """)
    
    places, transitions, arcs = generate_galaxy_clusters_model()
    
    # Save to workspace
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "Test_flow", "model")
    os.makedirs(workspace_dir, exist_ok=True)
    
    filename = os.path.join(workspace_dir, "galaxy_clusters.shy")
    save_as_shy_v2(places, transitions, arcs, filename)
    
    print("\n" + "=" * 80)
    print("MODEL STATISTICS:")
    print("=" * 80)
    
    total_exclusive = len([p for p in places if not p.label.startswith('I')])
    total_shared_galaxy = len([p for p in places if p.label.startswith('I_')])
    total_shared_cluster = len([p for p in places if p.label.startswith('IC_')])
    
    print(f"\nTotal Transitions (Hubs): {len(transitions)}")
    print(f"  - 2 clusters × 2 galaxies × 2 hubs = 8 hubs")
    
    print(f"\nTotal Places: {len(places)}")
    print(f"  - Exclusive satellites (orbit hubs): {total_exclusive}")
    print(f"  - Shared within galaxies: {total_shared_galaxy}")
    print(f"  - Shared within clusters (inter-galaxy): {total_shared_cluster}")
    
    print(f"\nTotal Arcs: {len(arcs)}")
    
    print("\n" + "=" * 80)
    print("PHYSICS PREDICTIONS (4 LEVELS):")
    print("=" * 80)
    
    print("\n✓ LEVEL 1 - Satellite orbits:")
    print("    Each place orbits its hub (~150-200 units)")
    print("    2 inputs left of hub, 1 output right of hub")
    
    print("\n✓ LEVEL 2 - Constellation cohesion:")
    print("    Hub + 3 satellites stay together via arc forces")
    print("    Each constellation acts as single unit")
    
    print("\n✓ LEVEL 3 - Galaxy cohesion:")
    print("    2 constellations connected by 1 shared metabolite")
    print("    Hubs separated by ~300 units vertically")
    print("    Shared place positions between the 2 hubs")
    
    print("\n✓ LEVEL 4 - Cluster cohesion:")
    print("    2 galaxies connected by 1 inter-galaxy metabolite")
    print("    Galaxies separated by ~400 units horizontally")
    print("    Shared place bridges the 2 galaxies")
    
    print("\n✓ LEVEL 5 - Cluster separation:")
    print("    NO connections between Cluster 1 and Cluster 2")
    print("    Hub group repulsion pushes clusters apart")
    print("    Expected: ~2400+ units between cluster centers")
    
    print("\n" + "=" * 80)
    print("EXPECTED VISUAL LAYOUT:")
    print("=" * 80)
    print("""
         CLUSTER 1                           CLUSTER 2
    (Metabolic Cluster)              (Biosynthesis Cluster)
    
      Galaxy A   Galaxy B               Galaxy C   Galaxy D
    (Glycolysis)(Fermentation)      (Amino Acids)(Nucleotides)
    
        A1         B1                     C1         D1
        │          │                      │          │
       [I_A]      [I_B]                  [I_C]      [I_D]
        │          │                      │          │
        A2─[IC_C1]─B2                    C2─[IC_C2]─D2
    
    Legend:
    - A1, A2, etc.: Hub transitions (constellations)
    - [I_X]: Shared metabolite within galaxy (connects 2 hubs)
    - [IC_CX]: Inter-galaxy metabolite (connects 2 galaxies in cluster)
    - Each hub has 3 satellites (not shown for clarity)
    
    Key distances:
    - Satellite to hub: ~150-200 units
    - Hubs within galaxy: ~300 units
    - Galaxies within cluster: ~400 units
    - Clusters: ~2400+ units (NO CONNECTIONS, pure repulsion)
    """)
    
    print("=" * 80)
    print("✓ Ready to test multi-level Galaxy Clustering!")
    print("✓ This tests if groups of galaxies separate from other groups!")
    print("=" * 80)


if __name__ == "__main__":
    main()
