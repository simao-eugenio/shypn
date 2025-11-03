#!/usr/bin/env python3
"""Test script to check raw KEGG KGML data for compound entries."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser

print("=" * 80)
print("Checking Raw KEGG KGML Data for hsa00010")
print("=" * 80)

# Fetch KGML
client = KEGGAPIClient()
print("\n1. Fetching KGML from KEGG API...")
kgml_xml = client.fetch_kgml('hsa00010')

if not kgml_xml:
    print("✗ Failed to fetch KGML")
    sys.exit(1)

print(f"✓ Fetched {len(kgml_xml)} bytes")

# Parse KGML
print("\n2. Parsing KGML...")
parser = KGMLParser()
pathway = parser.parse(kgml_xml)

print(f"✓ Parsed pathway: {pathway.title}")
print(f"  Total entries: {len(pathway.entries)}")

# Get compound entries
compounds = pathway.get_compounds()
print(f"\n3. Found {len(compounds)} compound entries")

# Show first 5 compounds with their metadata
print("\n4. First 5 compound entries:")
print("-" * 80)

for i, entry in enumerate(compounds[:5], 1):
    print(f"\nCompound {i}:")
    print(f"  Entry ID: {entry.id}")
    print(f"  Name (from XML 'name' attribute): {entry.name}")
    print(f"  Type: {entry.type}")
    print(f"  Graphics name (display label): {entry.graphics.name if entry.graphics else 'N/A'}")
    print(f"  Position: ({entry.graphics.x}, {entry.graphics.y})" if entry.graphics else "  Position: N/A")
    
    # Extract KEGG IDs
    kegg_ids = entry.get_kegg_ids()
    print(f"  KEGG IDs (parsed from name): {kegg_ids}")
    
    # Check if it looks like a compound ID
    if entry.name:
        if entry.name.startswith('cpd:'):
            print(f"  ✓ Has KEGG compound ID prefix 'cpd:'")
        elif entry.name.startswith('C') and entry.name[1:6].isdigit():
            print(f"  ✓ Looks like KEGG compound ID (C#####)")
        else:
            print(f"  ⚠ Unusual format")

print("\n" + "=" * 80)
print("Analysis Complete")
print("=" * 80)
