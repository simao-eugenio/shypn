"""Test Model Generator for Unified Physics Algorithm.

Creates test Petri net models in workspace/Test_flow/model/ that can be opened
in the canvas to visually test the unified physics layout algorithm.
"""

import sys
from pathlib import Path
import json

# Add src to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from shypn.netobjs import Place, Transition, Arc


def create_hub_constellation_model():
    """Create a model with 3 independent transition hubs forming a constellation.
    
    PARADIGM: Places orbit Transitions (not the reverse!)
    - Transitions are activity centers (hubs where transformations happen)
    - Places are passive containers (orbit the activity centers)
    - Simple P-T-P biological flow
    - No artificial arc weight manipulation (weight=1.0)
    
    This tests:
    - Hub detection (high-degree transition nodes)
    - Hub-to-hub repulsion (proximity forces between transitions)
    - Place orbital spreading (places orbit their parent transition)
    - No inter-hub connections (no SCC, pure hub constellation)
    """
    print("Creating: Hub Constellation Model (NEW PARADIGM)")
    print("  3 independent hub TRANSITIONS (activity centers)")
    print("  Each transition has 6 orbiting PLACES")
    print("  Biological P-T-P flow, weight=1.0 (no manipulation)")
    print()
    
    places = []
    transitions = []
    arcs = []
    
    # Create 3 hub TRANSITIONS (spread apart, NO connections between them)
    hub_positions = [(200, 300), (600, 300), (400, 600)]
    arc_id = 100
    
    for hub_idx, (x, y) in enumerate(hub_positions):
        # Create hub TRANSITION (activity center, will get high mass)
        hub_transition = Transition(float(x), float(y), 
                                    100 + hub_idx, 
                                    f"HubT_{hub_idx+1}", 
                                    label=f"Hub Transition {hub_idx+1}")
        transitions.append(hub_transition)
        
        # Add orbiting PLACES around this transition hub (isolated, no cross-connections)
        orbital_angles = [0, 60, 120, 180, 240, 300]  # 6 places per transition
        for place_idx, angle in enumerate(orbital_angles):
            # Calculate position around hub transition
            import math
            radius = 120
            rad = math.radians(angle)
            place_x = x + radius * math.cos(rad)
            place_y = y + radius * math.sin(rad)
            
            # Create orbiting PLACE (passive container)
            p = Place(float(place_x), float(place_y), 
                     hub_idx*10 + place_idx + 1, 
                     f"Place_{hub_idx+1}_{place_idx+1}", 
                     label=f"P{hub_idx+1}.{place_idx+1}")
            places.append(p)
            
            # Connect: Place -> Transition (biological flow direction)
            # Weight=1.0: NO artificial manipulation, respect biological semantics!
            arc = Arc(p, hub_transition, arc_id, f"A{arc_id}")
            arc.weight = 1.0  # Natural weight, no force balancing
            arcs.append(arc)
            arc_id += 1
    
    return places, transitions, arcs


def create_scc_with_hubs_model():
    """Create a model with large SCC and external hubs.
    
    This tests:
    - SCC detection (large cycle)
    - SCC as gravitational center (super-massive)
    - External hubs (massive nodes)
    - Mixed forces (oscillatory + proximity + ambient)
    """
    print("Creating: SCC with External Hubs Model")
    print("  1 large SCC (6 nodes)")
    print("  2 external hubs")
    print()
    
    places = []
    transitions = []
    arcs = []
    
    # Create SCC: 6 places in a hexagonal cycle
    scc_size = 6
    center_x, center_y = 400, 400
    radius = 150
    import math
    
    for i in range(scc_size):
        angle = (i * 360 / scc_size) - 90  # Start at top
        rad = math.radians(angle)
        x = center_x + radius * math.cos(rad)
        y = center_y + radius * math.sin(rad)
        p = Place(float(x), float(y), i+1, f"SCC_P{i+1}", label=f"SCC P{i+1}")
        places.append(p)
    
    # Create transitions between SCC places
    arc_id = 100
    for i in range(scc_size):
        next_i = (i + 1) % scc_size
        # Calculate transition position (midpoint)
        x = (places[i].x + places[next_i].x) / 2
        y = (places[i].y + places[next_i].y) / 2
        t = Transition(float(x), float(y), 10+i, f"SCC_T{i+1}", label=f"SCC T{i+1}")
        transitions.append(t)
        
        # Connect: P -> T -> P_next (creates cycle)
        arcs.append(Arc(places[i], t, arc_id, f"A{arc_id}"))
        arc_id += 1
        arcs.append(Arc(t, places[next_i], arc_id, f"A{arc_id}"))
        arc_id += 1
    
    # Create 2 external hubs
    hub1 = Place(100.0, 400.0, 100, "Hub_1", label="External Hub 1")
    hub2 = Place(700.0, 400.0, 101, "Hub_2", label="External Hub 2")
    places.extend([hub1, hub2])
    
    # Connect hubs to SCC (create high degree)
    for i in range(3):  # Each hub connects to 3 SCC nodes
        # Hub1 connections (Hub → Transition → SCC_Place, no parallel arcs)
        t1 = Transition(float(200 + i*30), float(350 + i*30), 50+i, f"Hub1_T{i}", label=f"H1 T{i+1}")
        transitions.append(t1)
        arcs.append(Arc(hub1, t1, arc_id, f"A{arc_id}"))
        arc_id += 1
        arcs.append(Arc(t1, places[i], arc_id, f"A{arc_id}"))
        arc_id += 1
        
        # Hub2 connections (Hub → Transition → SCC_Place, no parallel arcs)
        t2 = Transition(float(600 - i*30), float(350 + i*30), 60+i, f"Hub2_T{i}", label=f"H2 T{i+1}")
        transitions.append(t2)
        arcs.append(Arc(hub2, t2, arc_id, f"A{arc_id}"))
        arc_id += 1
        arcs.append(Arc(t2, places[i+3], arc_id, f"A{arc_id}"))
        arc_id += 1
    
    return places, transitions, arcs


def save_model_to_shy(places, transitions, arcs, filename):
    """Save model to .shy format (Shypn Petri net format)."""
    
    from datetime import datetime
    
    model_data = {
        "version": "2.0",
        "metadata": {
            "created": datetime.now().isoformat(),
            "description": "Test model for Unified Physics Algorithm",
            "object_counts": {
                "places": len(places),
                "transitions": len(transitions),
                "arcs": len(arcs)
            }
        },
        "view_state": {
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0
        },
        "places": [],
        "transitions": [],
        "arcs": []
    }
    
    # Serialize places (Shypn format)
    for p in places:
        model_data["places"].append({
            "id": p.id,
            "name": p.name,
            "label": p.label if p.label else "",
            "type": "place",
            "x": p.x,
            "y": p.y,
            "radius": 25.0,
            "marking": getattr(p, 'marking', 0),
            "initial_marking": getattr(p, 'initial_marking', 0),
            "border_color": [0.0, 0.0, 0.0],
            "border_width": 3.0
        })
    
    # Serialize transitions (Shypn format)
    for t in transitions:
        model_data["transitions"].append({
            "id": t.id,
            "name": t.name,
            "label": t.label if t.label else "",
            "type": "transition",
            "x": t.x,
            "y": t.y,
            "width": 10.0,
            "height": 50.0,
            "angle": 0.0,
            "border_color": [0.0, 0.0, 0.0],
            "border_width": 3.0,
            "fill_color": [0.0, 0.0, 0.0]
        })
    
    # Serialize arcs (Shypn format)
    for arc in arcs:
        # Determine source and target types
        source_type = "place" if isinstance(arc.source, Place) else "transition"
        target_type = "place" if isinstance(arc.target, Place) else "transition"
        
        model_data["arcs"].append({
            "id": arc.id,
            "name": arc.name,
            "type": "arc",
            "source_id": arc.source.id,
            "source_type": source_type,
            "target_id": arc.target.id,
            "target_type": target_type,
            "weight": getattr(arc, 'weight', 1.0),
            "color": [0.0, 0.0, 0.0],
            "width": 2.0,
            "arrow_style": "normal"
        })
    
    # Save to file with .shy extension
    output_dir = Path(__file__).parent.parent / "workspace" / "Test_flow" / "model"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    with open(output_path, 'w') as f:
        json.dump(model_data, f, indent=2)
    
    print(f"✓ Saved: {output_path}")
    return output_path


def main():
    """Generate test models for unified physics algorithm."""
    
    print("=" * 80)
    print("UNIFIED PHYSICS TEST MODEL GENERATOR")
    print("=" * 80)
    print()
    print("Generating test models in: workspace/Test_flow/model/")
    print()
    
    # Model 1: Hub Constellation
    print("-" * 80)
    places1, transitions1, arcs1 = create_hub_constellation_model()
    path1 = save_model_to_shy(places1, transitions1, arcs1, "hub_constellation.shy")
    print(f"  Places: {len(places1)}")
    print(f"  Transitions: {len(transitions1)}")
    print(f"  Arcs: {len(arcs1)}")
    print()
    
    # Model 2: SCC with Hubs
    print("-" * 80)
    places2, transitions2, arcs2 = create_scc_with_hubs_model()
    path2 = save_model_to_shy(places2, transitions2, arcs2, "scc_with_hubs.shy")
    print(f"  Places: {len(places2)}")
    print(f"  Transitions: {len(transitions2)}")
    print(f"  Arcs: {len(arcs2)}")
    print()
    
    # Summary
    print("=" * 80)
    print("TEST MODELS GENERATED")
    print("=" * 80)
    print()
    print("You can now open these models in the canvas:")
    print()
    print(f"1. {path1.name}")
    print("   - 3 INDEPENDENT hubs (no inter-hub connections)")
    print("   - Each hub has 6 isolated satellites")
    print("   - Tests hub constellation pattern")
    print("   - Tests proximity repulsion between hubs")
    print("   - Satellites stay with their parent hub")
    print()
    print(f"2. {path2.name}")
    print("   - 1 large SCC (6-node cycle)")
    print("   - 2 external hubs")
    print("   - Tests SCC as gravitational center")
    print("   - Tests mixed SCC + hub forces")
    print()
    print("To test the unified physics algorithm:")
    print("  1. Open Shypn")
    print("  2. Load model from workspace/Test_flow/model/")
    print("  3. Right-click canvas → 'Layout: Solar System (SSCC)'")
    print("  4. Watch unified physics in action!")
    print()
    print("Expected behavior:")
    print("  ✓ Hubs spread into constellation")
    print("  ✓ SCCs become gravitational centers")
    print("  ✓ No clustering (proximity repulsion)")
    print("  ✓ Natural orbital patterns (oscillatory forces)")
    print("  ✓ Global spacing (ambient tension)")
    print()
    print("=" * 80)
    print("✅ READY FOR CANVAS TESTING")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
