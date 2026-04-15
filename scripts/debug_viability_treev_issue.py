#!/usr/bin/env python3
"""Debug script to trace why viability panel TreeView shows EPO=0 instead of 0.1."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.place import Place
from shypn.data.model_canvas_manager import ModelCanvasManager

def test_place_loading():
    """Test Place loading from file."""
    model_path = Path("workspace/projects/gata/models/phase3a_spatial_clean.shy")
    
    print("=" * 80)
    print("STEP 1: Loading model from file")
    print("=" * 80)
    
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    # Find EPO and GCSF in file
    for place_data in data.get('places', []):
        if place_data.get('name') in ['EPO_external', 'GCSF_external']:
            name = place_data['name']
            print(f"\n{name} in FILE:")
            print(f"  marking: {place_data.get('marking')}")
            print(f"  initial_marking: {place_data.get('initial_marking')}")
            print(f"  tokens: {place_data.get('tokens', '(not present)')}")
            
            # Deserialize
            print(f"\n{name} after Place.from_dict():")
            place_obj = Place.from_dict(place_data)
            print(f"  place_obj.tokens: {place_obj.tokens}")
            print(f"  place_obj.initial_marking: {place_obj.initial_marking}")
            
            # Test TreeView logic
            marking = place_obj.initial_marking if hasattr(place_obj, 'initial_marking') else (
                place_obj.tokens if hasattr(place_obj, 'tokens') else 0
            )
            print(f"  TreeView would show: {marking}")
    
    print("\n" + "=" * 80)
    print("STEP 2: Check if ModelCanvasManager modifies places")
    print("=" * 80)
    print("(This would require full app context - checking manually)")
    
    # Check if there's a reset_to_initial_state or similar
    print("\nLooking for methods that might reset tokens...")
    print("Potential culprits:")
    print("  - ModelCanvasManager.load_from_dict()")
    print("  - DocumentModel.reset_simulation()")
    print("  - Place initialization after loading")

if __name__ == '__main__':
    test_place_loading()
