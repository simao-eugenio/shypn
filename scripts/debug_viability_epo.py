#!/usr/bin/env python3
"""Debug script to check EPO_external values in viability panel."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.place import Place

def check_epo_in_model_file():
    """Check EPO_external values in the saved .shy file."""
    model_path = Path("workspace/projects/gata/models/phase3a_spatial_clean.shy")
    
    if not model_path.exists():
        print(f"Model file not found: {model_path}")
        return
    
    print(f"Reading model file: {model_path}")
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    # Find EPO_external place
    for place_data in data.get('places', []):
        if place_data.get('name') == 'EPO_external':
            print(f"\nEPO_external in file:")
            print(f"  id: {place_data.get('id')}")
            print(f"  marking: {place_data.get('marking')}")
            print(f"  initial_marking: {place_data.get('initial_marking')}")
            print(f"  tokens: {place_data.get('tokens', '(not present)')}")
            
            # Test deserialization
            print(f"\nTesting Place.from_dict():")
            place_obj = Place.from_dict(place_data)
            print(f"  place_obj.tokens: {place_obj.tokens}")
            print(f"  place_obj.initial_marking: {place_obj.initial_marking}")
            print(f"  hasattr initial_marking: {hasattr(place_obj, 'initial_marking')}")
            
            # Test TreeView value logic
            marking = place_obj.initial_marking if hasattr(place_obj, 'initial_marking') else (
                place_obj.tokens if hasattr(place_obj, 'tokens') else 0
            )
            print(f"  TreeView would show: {marking}")
            return
    
    print("\nEPO_external not found in model file!")

if __name__ == '__main__':
    check_epo_in_model_file()
