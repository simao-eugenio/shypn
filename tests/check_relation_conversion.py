#!/usr/bin/env python3
"""Check if relations create any arcs in converted pathways."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions

# Test TNF signaling pathway (has 56 relations, 0 reactions)
client = KEGGAPIClient()
pathway_id = 'hsa04668'

print(f"Testing relation conversion for {pathway_id} (TNF signaling)\n")
print("=" * 80)

kgml_data = client.fetch_kgml(pathway_id)
parser = KGMLParser()
pathway = parser.parse(kgml_data)

print(f"Parsed pathway:")
print(f"  Entries: {len(pathway.entries)}")
print(f"  Reactions: {len(pathway.reactions)}")
print(f"  Relations: {len(pathway.relations)}")

# Convert
converter = PathwayConverter()
options = ConversionOptions(include_cofactors=False, coordinate_scale=2.5)
document = converter.convert(pathway, options)

print(f"\nConverted document:")
print(f"  Places: {len(document.places)}")
print(f"  Transitions: {len(document.transitions)}")
print(f"  Arcs: {len(document.arcs)}")

if document.arcs:
    print(f"\n⚠️  WARNING: Found {len(document.arcs)} arcs from pathway with 0 reactions!")
    print("This suggests relations are being converted somewhere.")
else:
    print(f"\n✅ No arcs created (correct - pathway has no reactions)")

# Check for gene/protein entries
gene_entries = [e for e in pathway.entries.values() if e.type == 'gene']
print(f"\nGene/protein entries: {len(gene_entries)}")

# Try converting with include_relations option
print(f"\nTesting with include_relations=True:")
options_with_rel = ConversionOptions(
    include_cofactors=False,
    coordinate_scale=2.5,
    include_relations=True
)
document_with_rel = converter.convert(pathway, options_with_rel)

print(f"  Places: {len(document_with_rel.places)}")
print(f"  Transitions: {len(document_with_rel.transitions)}")
print(f"  Arcs: {len(document_with_rel.arcs)}")

if document_with_rel.arcs > document.arcs:
    print(f"  ⚠️  Relations created {document_with_rel.arcs - document.arcs} additional arcs!")

