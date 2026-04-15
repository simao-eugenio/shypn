#!/usr/bin/env python3
"""
Update Bacillus sporulation model to use only essential signal places.

Based on Chapter 5 thesis analysis, only the following places should be signal places:
- ATP_pool: Energy gating and commitment threshold (Layer 3)
- Spo0A_P: Master regulator for commitment decision (Layer 1)  
- SigmaF: Sporulation pathway execution (Layer 0)
- SigmaH: Early sporulation activation (Layer 3)

All other places become normal places (is_signal_place: false).
"""

import json
import sys
from pathlib import Path

# Essential signal places for normal model investigation
ESSENTIAL_SIGNAL_PLACES = {
    "ATP_pool",      # Energy threshold gating
    "Spo0A_P",       # Commitment regulator
    "SigmaF",        # Sporulation execution
    "SigmaH",        # Early sporulation
}

def update_model(input_file: Path, output_file: Path):
    """Update model file to set only essential places as signal places."""
    
    print(f"Reading model from: {input_file}")
    with open(input_file, 'r') as f:
        model = json.load(f)
    
    # Track changes
    signal_to_normal = []
    kept_as_signal = []
    arcs_converted = []
    
    # Build place ID to name mapping and signal place IDs
    place_id_to_name = {}
    signal_place_ids = set()
    
    for place in model.get("places", []):
        place_id = place.get("id")
        place_name = place.get("name", "")
        place_id_to_name[place_id] = place_name
        
        if place_name in ESSENTIAL_SIGNAL_PLACES:
            signal_place_ids.add(place_id)
    
    # Update places
    for place in model.get("places", []):
        place_name = place.get("name", "")
        current_is_signal = place.get("is_signal_place", False)
        
        if place_name in ESSENTIAL_SIGNAL_PLACES:
            if not current_is_signal:
                place["is_signal_place"] = True
                # Ensure signal place has blue border
                place["border_color"] = [0.0, 0.4, 0.8]
                print(f"  ✓ Setting {place_name} as SIGNAL place")
            else:
                kept_as_signal.append(place_name)
                # Ensure signal place has blue border
                place["border_color"] = [0.0, 0.4, 0.8]
        else:
            if current_is_signal:
                place["is_signal_place"] = False
                # Set default black border for normal places
                place["border_color"] = [0.0, 0.0, 0.0]
                signal_to_normal.append(place_name)
    
    # Update arcs: convert signal_flow to normal for non-signal places
    for arc in model.get("arcs", []):
        arc_type = arc.get("arc_type", "")
        source_id = arc.get("source_id")
        target_id = arc.get("target_id")
        
        # Check if arc involves signal flow
        if "signal_flow" in arc_type:
            # Determine if connected place is signal place
            connected_place_id = None
            if arc.get("source_type") == "place":
                connected_place_id = source_id
            elif arc.get("target_type") == "place":
                connected_place_id = target_id
            
            # Convert to normal if connected place is not a signal place
            if connected_place_id and connected_place_id not in signal_place_ids:
                old_arc_type = arc_type
                # Convert signal_flow types to normal equivalents
                if arc_type == "signal_flow":
                    arc["arc_type"] = "normal"
                elif arc_type == "curved_signal_flow":
                    arc["arc_type"] = "curved"
                elif arc_type == "curved_opposite_signal_flow":
                    arc["arc_type"] = "curved_opposite"
                
                # Set default black color for normal arcs
                arc["color"] = [0.0, 0.0, 0.0]
                
                place_name = place_id_to_name.get(connected_place_id, connected_place_id)
                arcs_converted.append((arc.get("id"), place_name, old_arc_type, arc["arc_type"]))
        
        # Ensure signal_flow arcs keep gray color
        elif "signal_flow" in arc_type:
            arc["color"] = [0.7, 0.7, 0.7]
    
    # Update metadata
    if "metadata" not in model:
        model["metadata"] = {}
    
    model["metadata"]["modified"] = "2026-01-31"
    model["metadata"]["modification_note"] = (
        "Updated to use only essential signal places (ATP_pool, Spo0A_P, SigmaF, SigmaH) "
        "for testing Chapter 5 architectural principle"
    )
    
    # Write updated model
    print(f"\nWriting updated model to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(model, f, indent=2)
    
    # Report changes
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"✓ Kept as SIGNAL places ({len(kept_as_signal)}):")
    for name in sorted(kept_as_signal):
        print(f"    - {name}")
    
    print(f"\n→ Changed to NORMAL places ({len(signal_to_normal)}):")
    for name in sorted(signal_to_normal):
        print(f"    - {name}")
    
    print(f"\n→ Arcs converted from signal_flow to normal ({len(arcs_converted)}):")
    if arcs_converted:
        for arc_id, place_name, old_type, new_type in arcs_converted[:10]:  # Show first 10
            print(f"    - {arc_id}: {place_name} ({old_type} → {new_type})")
        if len(arcs_converted) > 10:
            print(f"    ... and {len(arcs_converted) - 10} more")
    else:
        print(f"    - None (all signal_flow arcs connect to signal places)")
    
    print(f"\n{'='*60}")
    print(f"✓ Model updated successfully!")
    print(f"{'='*60}\n")

def main():
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Define file paths
    input_file = script_dir / "bacillus_sporulation_normal.shy"
    output_file = script_dir / "bacillus_sporulation_normal_selective_signals.shy"
    
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)
    
    update_model(input_file, output_file)
    
    print(f"Next steps:")
    print(f"  1. Run simulation with: {output_file.name}")
    print(f"  2. Compare results with original model (all places as signals)")
    print(f"  3. Verify threshold prediction still matches experimental 2.21 mM")

if __name__ == "__main__":
    main()
