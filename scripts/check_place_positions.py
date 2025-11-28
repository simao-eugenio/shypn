#!/usr/bin/env python3
"""Check place positions after layout - are they spreading or clustering?"""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.layout.sscc.solar_system_layout_engine import SolarSystemLayoutEngine
import math


def check_place_positions():
    """Check if places are spreading around their transitions or clustering."""
    
    print("="*80)
    print("PLACE POSITION ANALYSIS")
    print("="*80)
    print()
    
    # Load model
    model_path = "workspace/Test_flow/model/hub_constellation.shy"
    document = DocumentModel.load_from_file(model_path)
    places = document.places
    transitions = document.transitions
    arcs = document.arcs
    
    # Apply layout
    engine = SolarSystemLayoutEngine()
    new_positions = engine.apply_layout(places, transitions, arcs)
    
    # Group places by their transition
    transition_groups = {t.id: [] for t in transitions}
    for arc in arcs:
        # Place → Transition arc
        place_id = arc.source.id
        trans_id = arc.target.id
        transition_groups[trans_id].append(place_id)
    
    # Analyze each group
    for t in sorted(transitions, key=lambda x: x.id):
        tx, ty = new_positions[t.id]
        place_ids = transition_groups[t.id]
        
        print(f"{t.label}:")
        print(f"  Position: ({tx:.1f}, {ty:.1f})")
        print(f"  Places: {len(place_ids)}")
        print()
        
        # Calculate place positions relative to transition
        for i, p_id in enumerate(place_ids):
            px, py = new_positions[p_id]
            dx = px - tx
            dy = py - ty
            dist = math.sqrt(dx*dx + dy*dy)
            angle = math.degrees(math.atan2(dy, dx))
            print(f"    Place {p_id}: ({px:.1f}, {py:.1f}) - dist={dist:.1f}, angle={angle:.1f}°")
        print()
    
    # Check overall place spread
    all_place_positions = [new_positions[p.id] for p in places]
    
    min_x = min(pos[0] for pos in all_place_positions)
    max_x = max(pos[0] for pos in all_place_positions)
    min_y = min(pos[1] for pos in all_place_positions)
    max_y = max(pos[1] for pos in all_place_positions)
    
    print("="*80)
    print(f"Overall place bounding box:")
    print(f"  X: {min_x:.1f} to {max_x:.1f} (width={max_x-min_x:.1f})")
    print(f"  Y: {min_y:.1f} to {max_y:.1f} (height={max_y-min_y:.1f})")
    print()


if __name__ == '__main__':
    check_place_positions()
