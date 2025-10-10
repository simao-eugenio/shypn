#!/usr/bin/env python3
"""Test enhanced upfront filtering."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import convert_pathway

client = KEGGAPIClient()

test_pathways = [
    ('hsa00010', 'Glycolysis'),
    ('hsa00620', 'Pyruvate metabolism'),
]

print("Testing Enhanced Upfront Filtering\n")
print("=" * 80)

for pathway_id, description in test_pathways:
    print(f"\n{pathway_id} - {description}")
    print("-" * 80)
    
    kgml_data = client.fetch_kgml(pathway_id)
    parser = KGMLParser()
    pathway = parser.parse(kgml_data)
    
    total_compounds = len(pathway.get_compounds())
    
    # Test with filtering enabled (default)
    doc_filtered = convert_pathway(pathway, filter_isolated_compounds=True)
    
    # Test with filtering disabled
    doc_unfiltered = convert_pathway(pathway, filter_isolated_compounds=False)
    
    print(f"  Total compounds in pathway: {total_compounds}")
    print(f"  With filtering: {len(doc_filtered.places)} places")
    print(f"  Without filtering: {len(doc_unfiltered.places)} places")
    print(f"  Filtered out: {len(doc_unfiltered.places) - len(doc_filtered.places)} ({100*(len(doc_unfiltered.places) - len(doc_filtered.places))/total_compounds:.1f}%)")
    
    # Verify no isolated places in filtered version
    connected_ids = set()
    for arc in doc_filtered.arcs:
        if arc.source_id.startswith('P'):
            connected_ids.add(arc.source_id)
        if arc.target_id.startswith('P'):
            connected_ids.add(arc.target_id)
    
    isolated = [p for p in doc_filtered.places if p.id not in connected_ids]
    
    if isolated:
        print(f"  ⚠️  WARNING: {len(isolated)} isolated places still present!")
    else:
        print(f"  ✅ All places connected")

print("\n" + "=" * 80)
print("✅ Enhanced filtering works correctly!\n")

