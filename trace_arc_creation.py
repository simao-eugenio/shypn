#!/usr/bin/env python3
"""Trace arc creation for C01159 and C00036."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions

# Test hsa00010
client = KEGGAPIClient()
kgml_data = client.fetch_kgml('hsa00010')
parser = KGMLParser()
pathway = parser.parse(kgml_data)

# Convert WITH filtering disabled to see all arcs
converter = PathwayConverter()
options = ConversionOptions(
    include_cofactors=False,
    coordinate_scale=2.5,
    filter_isolated_compounds=False  # Disable to see everything
)
document = converter.convert(pathway, options)

print("Glycolysis conversion results:")
print(f"Places: {len(document.places)}")
print(f"Transitions: {len(document.transitions)}")
print(f"Arcs: {len(document.arcs)}\n")

# Find places for C01159 and C00036
c01159_place = None
c00036_place = None

for place in document.places:
    if place.label == 'C01159' or 'C01159' in str(place.name):
        c01159_place = place
        print(f"Found C01159: Place {place.id} at ({place.x}, {place.y})")
    if place.label == 'C00036' or 'C00036' in str(place.name):
        c00036_place = place
        print(f"Found C00036: Place {place.id} at ({place.x}, {place.y})")

if not c01159_place or not c00036_place:
    print("\n⚠️  One or both compounds not found as places!")
    sys.exit(0)

print(f"\nSearching for arcs connecting C01159 ({c01159_place.id}) and C00036 ({c00036_place.id}):")

# Check for direct arc between them
direct_arcs = []
for arc in document.arcs:
    if (arc.source_id == c01159_place.id and arc.target_id == c00036_place.id) or \
       (arc.source_id == c00036_place.id and arc.target_id == c01159_place.id):
        direct_arcs.append(arc)
        print(f"\n⚠️  FOUND DIRECT ARC: {arc.id}")
        print(f"    {arc.source_id} → {arc.target_id}")
        print(f"    Type: {arc.__class__.__name__}")

if not direct_arcs:
    print("  ✅ No direct arcs between these places (correct!)")

# Show all arcs connected to each place
print(f"\nArcs connected to C01159 ({c01159_place.id}):")
c01159_arcs = [arc for arc in document.arcs 
               if arc.source_id == c01159_place.id or arc.target_id == c01159_place.id]
for arc in c01159_arcs[:5]:  # Show first 5
    print(f"  {arc.id}: {arc.source_id} → {arc.target_id}")

print(f"\nArcs connected to C00036 ({c00036_place.id}):")
c00036_arcs = [arc for arc in document.arcs 
               if arc.source_id == c00036_place.id or arc.target_id == c00036_place.id]
for arc in c00036_arcs[:5]:  # Show first 5
    print(f"  {arc.id}: {arc.source_id} → {arc.target_id}")

# Check if they share a common transition
print(f"\nChecking for shared transitions:")
c01159_transitions = set()
c00036_transitions = set()

for arc in c01159_arcs:
    if arc.source_id.startswith('T'):
        c01159_transitions.add(arc.source_id)
    if arc.target_id.startswith('T'):
        c01159_transitions.add(arc.target_id)

for arc in c00036_arcs:
    if arc.source_id.startswith('T'):
        c00036_transitions.add(arc.source_id)
    if arc.target_id.startswith('T'):
        c00036_transitions.add(arc.target_id)

shared = c01159_transitions & c00036_transitions
if shared:
    print(f"  ⚠️  Shared transitions: {shared}")
    print(f"  These compounds are connected through the same reaction(s)")
else:
    print(f"  ✅ No shared transitions (they're in separate reactions)")

