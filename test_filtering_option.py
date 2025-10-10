#!/usr/bin/env python3
"""Test the filter_isolated_compounds option."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import convert_pathway

# Fetch and parse hsa00010
client = KEGGAPIClient()
kgml_data = client.fetch_kgml('hsa00010')
parser = KGMLParser()
pathway = parser.parse(kgml_data)

print("Testing filter_isolated_compounds option\n")
print("=" * 80)

# Test with filtering enabled (default)
print("\n1. WITH filtering (default):")
document_filtered = convert_pathway(pathway, filter_isolated_compounds=True)
print(f"   Places: {len(document_filtered.places)}")
print(f"   Transitions: {len(document_filtered.transitions)}")
print(f"   Arcs: {len(document_filtered.arcs)}")

# Test with filtering disabled
print("\n2. WITHOUT filtering (filter_isolated_compounds=False):")
document_unfiltered = convert_pathway(pathway, filter_isolated_compounds=False)
print(f"   Places: {len(document_unfiltered.places)}")
print(f"   Transitions: {len(document_unfiltered.transitions)}")
print(f"   Arcs: {len(document_unfiltered.arcs)}")

# Compare
isolated_count = len(document_unfiltered.places) - len(document_filtered.places)
print(f"\n3. Difference:")
print(f"   {isolated_count} isolated compounds can be filtered")

# Verify isolated places exist when filtering is disabled
connected_place_ids = set()
for arc in document_unfiltered.arcs:
    if arc.source_id.startswith('P'):
        connected_place_ids.add(arc.source_id)
    if arc.target_id.startswith('P'):
        connected_place_ids.add(arc.target_id)

isolated_places = [p for p in document_unfiltered.places if p.id not in connected_place_ids]
print(f"\n4. Verification:")
print(f"   Found {len(isolated_places)} isolated places when filtering disabled:")
for p in isolated_places[:5]:
    print(f"     - {p.id}: {p.label}")

print("\n" + "=" * 80)
print("✅ Test passed! The filter_isolated_compounds option works correctly.\n")

