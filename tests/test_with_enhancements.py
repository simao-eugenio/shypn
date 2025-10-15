#!/usr/bin/env python3
"""Test conversion WITH enhancements to see if that causes the issue."""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
from shypn.pathway.options import get_standard_options

# Import with enhancements (like GUI does)
client = KEGGAPIClient()
kgml_data = client.fetch_kgml('hsa00010')
parser = KGMLParser()
pathway = parser.parse(kgml_data)

# Convert WITH enhancements (like GUI)
enhancement_options = get_standard_options()
document = convert_pathway_enhanced(
    pathway,
    coordinate_scale=2.5,
    include_cofactors=True,
    filter_isolated_compounds=True,
    enhancement_options=enhancement_options
)

print("=== WITH ENHANCEMENTS (like GUI) ===\n")
print(f"Places: {len(document.places)}")
print(f"Transitions: {len(document.transitions)}")
print(f"Arcs: {len(document.arcs)}\n")

# Check for place-to-place arcs AFTER enhancements
place_ids = {p.id for p in document.places}
transition_ids = {t.id for t in document.transitions}

place_to_place_arcs = []

for arc in document.arcs:
    source_is_place = arc.source_id in place_ids
    target_is_place = arc.target_id in place_ids
    
    if source_is_place and target_is_place:
        place_to_place_arcs.append(arc)

print(f"Place-to-place arcs: {len(place_to_place_arcs)}")

if place_to_place_arcs:
    print(f"\n⚠️  Enhancement pipeline CREATED place-to-place arcs!")
    for arc in place_to_place_arcs[:5]:
        source_place = next((p for p in document.places if p.id == arc.source_id), None)
        target_place = next((p for p in document.places if p.id == arc.target_id), None)
        print(f"  {arc.id}: {source_place.label} → {target_place.label}")
        print(f"    Arc type: {type(arc).__name__}")
        if hasattr(arc, 'arc_type'):
            print(f"    Arc subtype: {arc.arc_type}")
else:
    print("✅ No place-to-place arcs even after enhancements")

# Check if curved arcs exist
curved_arcs = [arc for arc in document.arcs if hasattr(arc, 'control_points') and arc.control_points]
print(f"\nCurved arcs: {len(curved_arcs)}")
if curved_arcs:
    print("  Enhancement pipeline added curved arcs for parallel connections")

