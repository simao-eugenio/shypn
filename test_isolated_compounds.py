#!/usr/bin/env python3
"""Test if isolated compounds create any arcs."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions

# Fetch and parse
client = KEGGAPIClient()
kgml_data = client.fetch_kgml('hsa00010')
parser = KGMLParser()
pathway = parser.parse(kgml_data)

# Convert
converter = PathwayConverter()
options = ConversionOptions(include_cofactors=False, coordinate_scale=2.5)
document = converter.convert(pathway, options)

print(f"Pathway: {pathway.title}")
print(f"Input: {len(pathway.entries)} entries, {len(pathway.reactions)} reactions")
print(f"Output: {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")

# Find places for C06186, C06187, C06188
target_compounds = ['C06186', 'C06187', 'C06188']
target_places = []

for place in document.places:
    place_name_str = str(place.name) if place.name else ""
    place_label_str = str(place.label) if place.label else ""
    
    if any(cpd in place_name_str or cpd in place_label_str for cpd in target_compounds):
        target_places.append(place)
        print(f"\nFound place:")
        print(f"  ID: {place.id}")
        print(f"  Name: {place.name}")
        print(f"  Label: {place.label}")
        print(f"  Position: ({place.x}, {place.y})")

# Check if any arcs connect to these places
print(f"\n=== Arcs involving these places ===")
for place in target_places:
    connected_arcs = [arc for arc in document.arcs 
                      if arc.source_id == place.id or arc.target_id == place.id]
    
    if connected_arcs:
        print(f"\nPlace {place.id} ({place.label}) has {len(connected_arcs)} arcs:")
        for arc in connected_arcs:
            print(f"  Arc {arc.id}: {arc.source_id} → {arc.target_id}")
    else:
        print(f"\nPlace {place.id} ({place.label}) has NO arcs (isolated)")

