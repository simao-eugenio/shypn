#!/usr/bin/env python3
"""Integration test: Load ATP_hydrolysis.shy and verify auto-mapping works.

This simulates what happens when you open the model and click Auto-Map.
"""

import sys
import json
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.thermodynamics.mappers import CompoundMapperService


def test_atp_hydrolysis_file():
    """Test auto-mapping on actual ATP_hydrolysis.shy file."""
    
    # Load the actual model file
    file_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/ATP_hydrolysis.shy"
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Create document from file
    document = DocumentModel.from_dict(data)
    
    print(f"Loaded model: {file_path}")
    print(f"Places: {len(document.places)}")
    for place in document.places:
        print(f"  - {place.id}: name='{place.name}', label='{place.label}'")
    
    # Test compound mapping service
    service = CompoundMapperService()
    mappings, confidences = service.map_all_places(document)
    
    print(f"\nAuto-Map Results:")
    print(f"Mapped: {len(mappings)}/{len(document.places)} places")
    
    expected = {
        "P1": "C00002",  # ATP
        "P3": "C00001",  # H2O
        "P4": "C00008",  # ADP
        "P5": "C00009",  # Pi
    }
    
    success = True
    for place_id, expected_compound in expected.items():
        if place_id not in mappings:
            print(f"  ❌ {place_id}: NOT MAPPED (expected {expected_compound})")
            success = False
        elif mappings[place_id] != expected_compound:
            print(f"  ❌ {place_id}: {mappings[place_id]} (expected {expected_compound})")
            success = False
        else:
            conf = confidences.get(place_id, 0.0)
            stars = "⭐" * min(3, int(conf * 5))
            print(f"  ✅ {place_id}: {mappings[place_id]} {stars} (confidence: {conf:.2f})")
    
    if success and len(mappings) == 4:
        print("\n" + "="*60)
        print("✅ INTEGRATION TEST PASSED")
        print("="*60)
        print("\nThe ATP_hydrolysis.shy model will auto-map correctly:")
        print("- All 4 places mapped to correct compound IDs")
        print("- Ready for thermodynamic validation")
        print("\nNext step: Open model in SHYPN and click 'Run Validation'")
        return 0
    else:
        print("\n❌ INTEGRATION TEST FAILED")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(test_atp_hydrolysis_file())
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
