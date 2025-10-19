#!/usr/bin/env python3
"""
Add Stochastic Source Transitions to Glycolysis Model

This script enhances the Glycolysis/Gluconeogenesis pathway model by adding
stochastic source transitions to all input places (places with no incoming arcs).

This provides continuous token generation for realistic simulation dynamics,
representing the constant availability of input metabolites in a cell.

Scientific Rationale:
- Input metabolites (glucose, ATP, NAD+, Pi, H2O) are constantly available
- Stochastic sources model the random arrival of substrate molecules
- Rate parameters can be tuned to match cellular concentrations

Usage:
    python3 add_source_transitions.py [input_file] [output_file]
    
Default:
    Input:  workspace/Test_flow/model/Glycolysis_SIMULATION_READY.shy
    Output: workspace/Test_flow/model/Glycolysis_WITH_SOURCES.shy
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def find_input_places(data):
    """Find all input places (places with no incoming arcs).
    
    Args:
        data: Loaded model dictionary
        
    Returns:
        list: List of (place_id, place_dict) tuples for input places
    """
    places = {p['id']: p for p in data['places']}
    arcs = data['arcs']
    
    # Count incoming arcs for each place
    incoming_count = {}
    for arc in arcs:
        target_id = arc.get('target_id', arc.get('target'))  # Handle both formats
        # Only count if target is a place (not transition)
        if target_id in places:
            incoming_count[target_id] = incoming_count.get(target_id, 0) + 1
    
    # Find places with no incoming arcs
    input_places = []
    for place_id, place in places.items():
        if incoming_count.get(place_id, 0) == 0:
            input_places.append((place_id, place))
    
    return input_places

def get_next_ids(data):
    """Get next available IDs for transitions and arcs.
    
    Args:
        data: Loaded model dictionary
        
    Returns:
        tuple: (next_transition_id, next_arc_id)
    """
    # Handle both numeric and string IDs
    transition_ids = []
    for t in data['transitions']:
        tid = t['id']
        if isinstance(tid, str) and tid.startswith('T'):
            transition_ids.append(int(tid[1:]))
        elif isinstance(tid, int):
            transition_ids.append(tid)
    
    arc_ids = []
    for a in data['arcs']:
        aid = a['id']
        if isinstance(aid, str) and aid.startswith('A'):
            arc_ids.append(int(aid[1:]))
        elif isinstance(aid, int):
            arc_ids.append(aid)
    
    next_transition_num = max(transition_ids) + 1 if transition_ids else 0
    next_arc_num = max(arc_ids) + 1 if arc_ids else 0
    
    return f"T{next_transition_num}", f"A{next_arc_num}"

def create_source_transition(transition_id, place, base_rate=0.1):
    """Create a stochastic source transition for a place.
    
    Args:
        transition_id: ID for the new transition
        place: Target place dictionary
        base_rate: Base firing rate (default: 0.1)
        
    Returns:
        dict: Transition object
    """
    # Position source transition to the left of the place
    offset_x = -80
    offset_y = 0
    
    transition = {
        "id": transition_id,
        "name": f"SOURCE_{place['name']}",
        "label": f"Source: {place.get('label', place['name'])}",
        "x": place['x'] + offset_x,
        "y": place['y'] + offset_y,
        "type": "stochastic",
        "rate": base_rate,
        "guard": 1,
        "priority": 1,
        "server": "infinite",
        "orientation": "horizontal",
        "width": 60,
        "height": 40
    }
    
    return transition

def create_source_arc(arc_id, source_transition_id, target_place_id, weight=1):
    """Create an arc from source transition to target place.
    
    Args:
        arc_id: ID for the new arc
        source_transition_id: Source transition ID
        target_place_id: Target place ID
        weight: Arc weight (default: 1)
        
    Returns:
        dict: Arc object
    """
    arc = {
        "id": arc_id,
        "name": "",
        "label": "",
        "type": "arc",
        "source_id": source_transition_id,
        "source_type": "transition",
        "target_id": target_place_id,
        "target_type": "place",
        "weight": weight,
        "color": [0.0, 0.0, 0.0],
        "width": 3.0,
        "control_points": []
    }
    
    return arc

def add_source_transitions(input_file, output_file, base_rate=0.1, verbose=True):
    """Add stochastic source transitions to all input places.
    
    Args:
        input_file: Path to input .shy file
        output_file: Path to output .shy file
        base_rate: Base firing rate for sources (default: 0.1)
        verbose: Print progress information
        
    Returns:
        dict: Statistics about added sources
    """
    # Load model
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if verbose:
        print(f"Loaded model: {input_file}")
        print(f"  Places: {len(data['places'])}")
        print(f"  Transitions: {len(data['transitions'])}")
        print(f"  Arcs: {len(data['arcs'])}")
        print()
    
    # Find input places
    input_places = find_input_places(data)
    
    if verbose:
        print(f"Found {len(input_places)} input places (no incoming arcs):")
        for place_id, place in input_places:
            print(f"  - {place['name']}: {place.get('label', 'N/A')}")
        print()
    
    # Get next available IDs
    next_transition_id, next_arc_id = get_next_ids(data)
    
    # Add source transitions and arcs
    added_transitions = []
    added_arcs = []
    
    for place_id, place in input_places:
        # Create source transition
        source_transition = create_source_transition(
            next_transition_id, place, base_rate
        )
        data['transitions'].append(source_transition)
        added_transitions.append(source_transition)
        
        # Create arc from source to place
        source_arc = create_source_arc(
            next_arc_id, next_transition_id, place_id
        )
        data['arcs'].append(source_arc)
        added_arcs.append(source_arc)
        
        if verbose:
            print(f"Added source for {place['name']}:")
            print(f"  Transition: {source_transition['name']} (ID: {next_transition_id})")
            print(f"  Type: {source_transition['type']}")
            print(f"  Rate: {source_transition['rate']}")
            print(f"  Arc: {next_transition_id} → {place_id} (ID: {next_arc_id})")
            print()
        
        # Increment IDs (handle string format "T123" -> "T124")
        t_num = int(next_transition_id[1:]) + 1
        next_transition_id = f"T{t_num}"
        a_num = int(next_arc_id[1:]) + 1
        next_arc_id = f"A{a_num}"
    
    # Save modified model
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    stats = {
        'input_places': len(input_places),
        'added_transitions': len(added_transitions),
        'added_arcs': len(added_arcs),
        'total_places': len(data['places']),
        'total_transitions': len(data['transitions']),
        'total_arcs': len(data['arcs'])
    }
    
    if verbose:
        print("=" * 80)
        print(f"✓ Successfully added {stats['added_transitions']} source transitions")
        print(f"✓ Model saved to: {output_file}")
        print()
        print("Final model statistics:")
        print(f"  Places: {stats['total_places']}")
        print(f"  Transitions: {stats['total_transitions']} (+{stats['added_transitions']})")
        print(f"  Arcs: {stats['total_arcs']} (+{stats['added_arcs']})")
        print()
        print("Model is now ready for simulation with continuous input!")
        print()
        print("Tuning suggestions:")
        print("  - Adjust source rates to match metabolite availability")
        print("  - Higher rates = more substrate availability")
        print("  - Lower rates = substrate-limited conditions")
        print("  - Typical range: 0.01 (slow) to 1.0 (fast)")
    
    return stats

def main():
    """Main entry point."""
    # Parse arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'workspace/Test_flow/model/Glycolysis_SIMULATION_READY.shy'
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = 'workspace/Test_flow/model/Glycolysis_WITH_SOURCES.shy'
    
    if len(sys.argv) > 3:
        base_rate = float(sys.argv[3])
    else:
        base_rate = 0.1  # Default rate
    
    # Check input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)
    
    # Add sources
    print("=" * 80)
    print("Adding Stochastic Source Transitions to Glycolysis Model")
    print("=" * 80)
    print()
    
    stats = add_source_transitions(input_file, output_file, base_rate)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
