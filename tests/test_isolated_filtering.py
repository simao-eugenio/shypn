#!/usr/bin/env python3
"""Test that isolated compounds are filtered from multiple pathways."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.importer.kegg.converter_base import ConversionOptions

# Test multiple pathways
test_pathways = [
    ('hsa00010', 'Glycolysis'),
    ('hsa04668', 'TNF signaling'),
    ('hsa00620', 'Pyruvate metabolism'),
]

client = KEGGAPIClient()
converter = PathwayConverter()
options = ConversionOptions(include_cofactors=False, coordinate_scale=2.5)

print("Testing isolated compound filtering across pathways\n")
print("=" * 80)

for pathway_id, description in test_pathways:
    print(f"\n{pathway_id} - {description}")
    print("-" * 80)
    
    try:
        # Fetch and parse
        kgml_data = client.fetch_kgml(pathway_id)
        pathway = parser = KGMLParser()
        pathway = parser.parse(kgml_data)
        
        if not pathway:
            print("  ❌ Failed to parse pathway")
            continue
        
        # Count compounds before conversion
        total_compounds = len(pathway.get_compounds())
        
        # Convert
        document = converter.convert(pathway, options)
        
        # Verify all places are connected
        connected_place_ids = set()
        for arc in document.arcs:
            if arc.source_id.startswith('P'):
                connected_place_ids.add(arc.source_id)
            if arc.target_id.startswith('P'):
                connected_place_ids.add(arc.target_id)
        
        isolated_places = [p for p in document.places if p.id not in connected_place_ids]
        
        print(f"  Input: {total_compounds} compounds, {len(pathway.reactions)} reactions")
        print(f"  Output: {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")
        print(f"  Filtered: {total_compounds - len(document.places)} isolated compounds")
        
        if isolated_places:
            print(f"  ⚠️  WARNING: {len(isolated_places)} isolated places still present!")
            for p in isolated_places[:3]:
                print(f"    - {p.id}: {p.label}")
        else:
            print(f"  ✅ All places are connected (no isolated compounds)")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 80)
print("Test complete!\n")

