#!/usr/bin/env python3
"""Generate test models with bidirectional flows: P1 → T → P2 patterns.

This tests that constellations with mixed arc directions stay together:
- Input places (P → T): substrates feeding into reaction
- Output places (T → P): products coming from reaction
- Hub transition (T): reaction center with inputs and outputs

Tests:
1. Simple chain: P1 → T → P2 (each transition has input and output)
2. Complex hub: Multiple inputs and outputs around same transition
3. Shared with bidirectional: Shared places connecting multiple hubs
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


def generate_bidirectional_constellation():
    """Generate model with bidirectional flows around hub transitions.
    
    Structure:
    - 3 hub transitions (T1, T2, T3)
    - Each hub has:
      - 3 input places (P → T): substrates
      - 3 output places (T → P): products
    - 2 shared places connecting hubs (P_shared_1_2, P_shared_2_3)
    
    Total: 18 exclusive places + 2 shared = 20 places, 3 transitions, 20 arcs
    """
    
    places = []
    transitions = []
    arcs = []
    
    # Hub positions (centered near origin for visibility)
    hub_positions = [
        (-300, 0),    # T1 - left
        (300, 0),     # T2 - right
        (0, 300),     # T3 - bottom
    ]
    
    # Create 3 hub transitions
    for i in range(3):
        t = SimpleTransition(
            id=100 + i,
            name=f"Hub Transition {i+1}",
            label=f"T{i+1}",
            x=hub_positions[i][0],
            y=hub_positions[i][1]
        )
        transitions.append(t)
    
    place_id = 0
    arc_id = 200
    
    # Create input and output places for each hub
    for hub_idx, hub_t in enumerate(transitions):
        # 3 INPUT places (P → T) - positioned above/left of hub
        for i in range(3):
            angle = (i * 120 - 90) * 3.14159 / 180  # Top semicircle
            offset_x = 150 * (i - 1)  # Spread horizontally
            offset_y = -120  # Above hub
            
            p = SimplePlace(
                id=place_id,
                name=f"Input {hub_idx+1}.{i+1}",
                label=f"Pin{hub_idx+1}.{i+1}",
                x=hub_t.x + offset_x,
                y=hub_t.y + offset_y
            )
            places.append(p)
            
            # Arc: Place → Transition (input flow)
            arc = SimpleArc(
                id=arc_id,
                name=f"Arc_{place_id}_to_{hub_t.id}",
                source=p,
                target=hub_t,
                weight=1.0
            )
            arcs.append(arc)
            arc_id += 1
            place_id += 1
        
        # 3 OUTPUT places (T → P) - positioned below/right of hub
        for i in range(3):
            offset_x = 150 * (i - 1)  # Spread horizontally
            offset_y = 120  # Below hub
            
            p = SimplePlace(
                id=place_id,
                name=f"Output {hub_idx+1}.{i+1}",
                label=f"Pout{hub_idx+1}.{i+1}",
                x=hub_t.x + offset_x,
                y=hub_t.y + offset_y
            )
            places.append(p)
            
            # Arc: Transition → Place (output flow)
            arc = SimpleArc(
                id=arc_id,
                name=f"Arc_{hub_t.id}_to_{place_id}",
                source=hub_t,
                target=p,
                weight=1.0
            )
            arcs.append(arc)
            arc_id += 1
            place_id += 1
    
    # Create 2 shared places that connect hubs bidirectionally
    shared_configs = [
        # (hub1_idx, hub2_idx, label, position, direction)
        (0, 1, "P_shared_1_2", (0, 0), "1_to_2"),      # T1 → P → T2
        (1, 2, "P_shared_2_3", (150, 150), "2_to_3"),  # T2 → P → T3
    ]
    
    for hub1_idx, hub2_idx, label, pos, direction in shared_configs:
        # Create shared place
        p = SimplePlace(
            id=place_id,
            name=f"Shared {hub1_idx+1}-{hub2_idx+1}",
            label=label,
            x=pos[0],
            y=pos[1]
        )
        places.append(p)
        
        # Arc 1: First hub → Place (output from hub1)
        arc1 = SimpleArc(
            id=arc_id,
            name=f"Arc_{transitions[hub1_idx].id}_to_{place_id}",
            source=transitions[hub1_idx],
            target=p,
            weight=1.0
        )
        arcs.append(arc1)
        arc_id += 1
        
        # Arc 2: Place → Second hub (input to hub2)
        arc2 = SimpleArc(
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
    """Generate and save the bidirectional flow model."""
    
    print("=" * 80)
    print("GENERATING BIDIRECTIONAL FLOW CONSTELLATION MODEL")
    print("=" * 80)
    
    places, transitions, arcs = generate_bidirectional_constellation()
    
    # Save to workspace
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "Test_flow", "model")
    os.makedirs(workspace_dir, exist_ok=True)
    
    filename = os.path.join(workspace_dir, "bidirectional_constellation.shy")
    save_as_shy_v2(places, transitions, arcs, filename)
    
    print("\n" + "=" * 80)
    print("MODEL STRUCTURE:")
    print("=" * 80)
    
    print("\nHub Transitions (3):")
    for t in transitions:
        print(f"  {t.label}: {t.name}")
    
    print("\nInput Places (P → T): 9 total (3 per hub)")
    for i in range(3):
        hub_inputs = [p for p in places if p.label.startswith(f"Pin{i+1}.")]
        if hub_inputs:
            print(f"  Hub T{i+1}: {', '.join(p.label for p in hub_inputs)}")
    
    print("\nOutput Places (T → P): 9 total (3 per hub)")
    for i in range(3):
        hub_outputs = [p for p in places if p.label.startswith(f"Pout{i+1}.")]
        if hub_outputs:
            print(f"  Hub T{i+1}: {', '.join(p.label for p in hub_outputs)}")
    
    print("\nShared Places (bidirectional chains): 2")
    shared = [p for p in places if 'shared' in p.label.lower()]
    for p in shared:
        # Find flow pattern
        input_from = None
        output_to = None
        for arc in arcs:
            if arc.target == p and hasattr(arc.source, 'height'):  # T → P
                input_from = arc.source.label
            elif arc.source == p and hasattr(arc.target, 'height'):  # P → T
                output_to = arc.target.label
        print(f"  {p.label}: {input_from} → P → {output_to}")
    
    print("\n" + "=" * 80)
    print("BIDIRECTIONAL FLOW PATTERN:")
    print("=" * 80)
    print("Each hub has:")
    print("  - 3 substrates (input places):  Pin → T")
    print("  - 3 products (output places):   T → Pout")
    print("  - Mixed directions create realistic reaction pattern")
    print("\nShared places form chains:")
    print("  - T1 → P_shared_1_2 → T2  (output from T1, input to T2)")
    print("  - T2 → P_shared_2_3 → T3  (output from T2, input to T3)")
    
    print("\n" + "=" * 80)
    print("EXPECTED LAYOUT (Solar System):")
    print("=" * 80)
    print("✓ Each hub keeps inputs AND outputs nearby (~150-200 units)")
    print("✓ Bidirectional flow preserved (constellation stays together)")
    print("✓ Shared places position between connected hubs")
    print("✓ Hub groups separated (~300-400 units)")
    print("✓ Arc direction doesn't break constellation cohesion")
    print("\n✓ Ready to test in canvas with Solar System Layout!")
    print("=" * 80)


if __name__ == "__main__":
    main()
