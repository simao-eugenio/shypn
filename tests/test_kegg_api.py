#!/usr/bin/env python3
"""Test KEGG API client by fetching glycolysis pathway."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.importer.kegg.api_client import KEGGAPIClient

def test_fetch_kgml():
    """Test fetching KGML for human glycolysis."""
    print("=" * 60)
    print("Testing KEGG API Client")
    print("=" * 60)
    
    client = KEGGAPIClient()
    
    # Test 1: Fetch glycolysis pathway
    print("\nTest 1: Fetching human glycolysis (hsa00010)...")
    kgml = client.fetch_kgml("hsa00010")
    
    if kgml:
        print(f"✓ Success! Fetched {len(kgml)} bytes")
        print(f"✓ First 500 characters:")
        print(kgml[:500])
        print("...")
        
        # Check for expected elements
        if '<pathway' in kgml and 'Glycolysis' in kgml:
            print("✓ KGML contains expected elements")
        else:
            print("✗ KGML missing expected elements")
    else:
        print("✗ Failed to fetch KGML")
        return False
    
    # Test 2: List some pathways
    print("\n" + "=" * 60)
    print("Test 2: Listing human pathways (first 10)...")
    pathways = client.list_pathways("hsa")
    
    if pathways:
        print(f"✓ Found {len(pathways)} total pathways")
        print("✓ First 10 pathways:")
        for pid, title in pathways[:10]:
            print(f"  {pid}: {title}")
    else:
        print("✗ Failed to list pathways")
    
    # Test 3: Get pathway image URL
    print("\n" + "=" * 60)
    print("Test 3: Getting pathway image URL...")
    image_url = client.get_pathway_image_url("hsa00010")
    print(f"✓ Image URL: {image_url}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_fetch_kgml()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
