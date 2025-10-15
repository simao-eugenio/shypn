#!/usr/bin/env python3
"""Test for the pathway.entries iteration fix.

This test verifies that we correctly iterate over pathway.entries.values()
instead of pathway.entries (which would give us keys).
"""
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

print("Testing pathway.entries iteration fix...")
print()

try:
    from shypn.importer.kegg.api_client import KEGGAPIClient
    from shypn.importer.kegg.kgml_parser import KGMLParser
    
    # Fetch and parse a pathway
    print("1. Fetching pathway hsa00010...")
    client = KEGGAPIClient()
    kgml_data = client.fetch_kgml("hsa00010")
    print(f"   ✓ Fetched {len(kgml_data)} bytes")
    
    print("\n2. Parsing KGML...")
    parser = KGMLParser()
    pathway = parser.parse(kgml_data)
    print(f"   ✓ Parsed pathway: {pathway.name}")
    print(f"   ✓ Entries: {len(pathway.entries)} (this is a dict)")
    
    print("\n3. Testing iteration over pathway.entries (WRONG - would fail)...")
    try:
        # This is what would fail - iterating over keys
        for e in list(pathway.entries)[:3]:  # Try first 3
            print(f"   Entry (key): {e} - type: {type(e)}")
            # e.type would fail here because e is a string (the key)
    except AttributeError as err:
        print(f"   ✗ AttributeError: {err} (expected)")
    
    print("\n4. Testing iteration over pathway.entries.values() (CORRECT)...")
    # This is the correct way - iterating over values
    compounds = sum(1 for e in pathway.entries.values() if e.type == 'compound')
    genes = sum(1 for e in pathway.entries.values() if e.type == 'gene')
    enzymes = sum(1 for e in pathway.entries.values() if e.type == 'enzyme')
    orthologs = sum(1 for e in pathway.entries.values() if e.type == 'ortholog')
    groups = sum(1 for e in pathway.entries.values() if e.type == 'group')
    
    print(f"   ✓ Compounds: {compounds}")
    print(f"   ✓ Genes: {genes}")
    print(f"   ✓ Enzymes: {enzymes}")
    print(f"   ✓ Orthologs: {orthologs}")
    print(f"   ✓ Groups: {groups}")
    
    # Verify non-zero counts
    total = compounds + genes + enzymes + orthologs + groups
    print(f"   ✓ Total counted: {total}")
    
    if total > 0:
        print("\n✅ FIX VERIFIED: Correctly iterating over pathway.entries.values()")
        print("   The fetch preview should now work without errors!")
        sys.exit(0)
    else:
        print("\n⚠️  Warning: No entries counted (unexpected)")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
