#!/usr/bin/env python3
"""Test the old converter method."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg import fetch_pathway
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions

# Fetch pathway
pathway_id = 'hsa04668'
print(f"Fetching {pathway_id}...")

from shypn.importer.kegg.api_client import KEGGAPIClient
client = KEGGAPIClient()
kgml_data = client.fetch_kgml(pathway_id)

print(f"KGML data length: {len(kgml_data)} characters")

# Parse with KGMLParser (like GUI does)
parser = KGMLParser()
pathway = parser.parse(kgml_data)

print(f"\n=== Parsed Pathway ===")
print(f"Compounds: {len(pathway.get_compounds()) if pathway else 'None'}")
print(f"Reactions: {len(pathway.reactions) if pathway else 'None'}")

if pathway:
    # Convert with old method
    print(f"\n=== Old Converter Method ===")
    converter = PathwayConverter()
    options = ConversionOptions(
        include_cofactors=False,
        coordinate_scale=2.5
    )
    document = converter.convert(pathway, options)
    
    print(f"Places: {len(document.places)}")
    print(f"Transitions: {len(document.transitions)}")
    print(f"Arcs: {len(document.arcs)}")
    
    # Check for place-to-place arcs
    if len(document.arcs) > 0:
        place_ids = {p.id for p in document.places}
        place_to_place = [arc for arc in document.arcs 
                          if arc.source_id in place_ids and arc.target_id in place_ids]
        
        print(f"\nPlace-to-Place arcs: {len(place_to_place)}")
        if place_to_place:
            print("⚠️  Found place-to-place arcs!")
            for arc in place_to_place[:3]:
                print(f"  {arc.source_id} → {arc.target_id}")
