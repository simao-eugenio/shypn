#!/usr/bin/env python3
"""Test Place metadata serialization fix."""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place


def test_place_metadata_serialization():
    """Test that Place metadata survives save/load cycle."""
    
    print("="*70)
    print("TEST: Place Metadata Serialization")
    print("="*70)
    
    # Create place with metadata (simulating KEGG import)
    place = Place(x=100.0, y=200.0, id="1", name="C00033", label="C00033")
    place.metadata = {
        'kegg_id': 'cpd:C00033',
        'kegg_entry_id': '45',
        'source': 'KEGG',
        'data_source': 'kegg_import',
        'kegg_type': 'compound'
    }
    
    print(f"\n1. Created Place:")
    print(f"   ID: {place.id}")
    print(f"   Name: {place.name}")
    print(f"   Label: {place.label}")
    print(f"   Metadata keys: {list(place.metadata.keys())}")
    print(f"   KEGG ID: {place.metadata.get('kegg_id')}")
    
    # Serialize to dict
    data = place.to_dict()
    
    print(f"\n2. Serialized to dict:")
    print(f"   Has 'metadata' key: {'metadata' in data}")
    if 'metadata' in data:
        print(f"   Metadata keys: {list(data['metadata'].keys())}")
        print(f"   KEGG ID in dict: {data['metadata'].get('kegg_id')}")
    else:
        print("   ❌ METADATA NOT SERIALIZED!")
        return False
    
    # Serialize to JSON (simulate save to .shy file)
    json_str = json.dumps(data, indent=2)
    print(f"\n3. JSON representation (first 300 chars):")
    print(f"   {json_str[:300]}...")
    
    # Deserialize from dict
    restored_place = Place.from_dict(data)
    
    print(f"\n4. Deserialized Place:")
    print(f"   ID: {restored_place.id}")
    print(f"   Name: {restored_place.name}")
    print(f"   Has metadata: {hasattr(restored_place, 'metadata')}")
    
    if hasattr(restored_place, 'metadata') and restored_place.metadata:
        print(f"   Metadata keys: {list(restored_place.metadata.keys())}")
        print(f"   KEGG ID: {restored_place.metadata.get('kegg_id')}")
        print(f"   Data source: {restored_place.metadata.get('data_source')}")
    else:
        print("   ❌ METADATA NOT RESTORED!")
        return False
    
    # Verify all metadata fields
    print(f"\n5. Verification:")
    success = True
    
    for key, expected_value in place.metadata.items():
        actual_value = restored_place.metadata.get(key)
        if actual_value == expected_value:
            print(f"   ✓ {key}: {actual_value}")
        else:
            print(f"   ❌ {key}: expected '{expected_value}', got '{actual_value}'")
            success = False
    
    if success:
        print(f"\n🎉 SUCCESS: Place metadata serialization working correctly!")
    else:
        print(f"\n❌ FAILURE: Metadata mismatch after deserialization")
    
    return success


if __name__ == "__main__":
    success = test_place_metadata_serialization()
    sys.exit(0 if success else 1)
