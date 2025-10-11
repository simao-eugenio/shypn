#!/usr/bin/env python3
"""Deep investigation: Find the source of place-to-place arcs."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions

# Import pathway that user is seeing
client = KEGGAPIClient()
kgml_data = client.fetch_kgml('hsa00010')
parser = KGMLParser()
pathway = parser.parse(kgml_data)

# Convert with filtering DISABLED to see everything
converter = PathwayConverter()
options = ConversionOptions(
    include_cofactors=True,  # Include everything
    coordinate_scale=2.5,
    filter_isolated_compounds=False  # Don't filter
)
document = converter.convert(pathway, options)

print("=== DEEP ARC INVESTIGATION ===\n")
print(f"Total arcs: {len(document.arcs)}\n")

# Check EVERY arc for place-to-place connections
place_ids = {p.id for p in document.places}
transition_ids = {t.id for t in document.transitions}

place_to_place_arcs = []
place_to_trans_arcs = []
trans_to_place_arcs = []
invalid_arcs = []

for arc in document.arcs:
    source_is_place = arc.source_id in place_ids
    target_is_place = arc.target_id in place_ids
    
    source_is_trans = arc.source_id in transition_ids
    target_is_trans = arc.target_id in transition_ids
    
    # Categorize arc
    if source_is_place and target_is_place:
        place_to_place_arcs.append(arc)
    elif source_is_place and target_is_trans:
        place_to_trans_arcs.append(arc)
    elif source_is_trans and target_is_place:
        trans_to_place_arcs.append(arc)
    else:
        invalid_arcs.append(arc)

print(f"Arc Classification:")
print(f"  Place → Transition: {len(place_to_trans_arcs)} ✅")
print(f"  Transition → Place: {len(trans_to_place_arcs)} ✅")
print(f"  Place → Place: {len(place_to_place_arcs)} ⚠️")
print(f"  Invalid (missing nodes): {len(invalid_arcs)} ⚠️")

if place_to_place_arcs:
    print(f"\n⚠️⚠️⚠️ FOUND {len(place_to_place_arcs)} PLACE-TO-PLACE ARCS! ⚠️⚠️⚠️\n")
    
    # Show first 10
    for i, arc in enumerate(place_to_place_arcs[:10], 1):
        # Find the places
        source_place = next((p for p in document.places if p.id == arc.source_id), None)
        target_place = next((p for p in document.places if p.id == arc.target_id), None)
        
        print(f"{i}. Arc {arc.id}:")
        print(f"   Source: {arc.source_id} = {source_place.label if source_place else 'UNKNOWN'}")
        print(f"   Target: {arc.target_id} = {target_place.label if target_place else 'UNKNOWN'}")
        print(f"   Arc type: {type(arc).__name__}")
        if hasattr(arc, 'metadata'):
            print(f"   Metadata: {arc.metadata}")
        print()
    
    # This is a CRITICAL BUG!
    print("🐛 BUG CONFIRMED: Place-to-place arcs are being created!")
    print("   This violates Petri net bipartite property.")
    print("   Source of bug: Need to trace through arc creation...")
    
else:
    print("\n✅ NO place-to-place arcs found!")
    print("   If you're seeing them in GUI, it might be a rendering issue.")

