#!/usr/bin/env python3
"""Check KEGG relations in pathways."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser

# Test pathways
test_pathways = [
    ('hsa00010', 'Glycolysis'),
    ('hsa04668', 'TNF signaling'),
    ('hsa04010', 'MAPK signaling'),
]

client = KEGGAPIClient()

print("Checking KEGG Relations in Pathways\n")
print("=" * 80)

for pathway_id, description in test_pathways:
    print(f"\n{pathway_id} - {description}")
    print("-" * 80)
    
    try:
        kgml_data = client.fetch_kgml(pathway_id)
        parser = KGMLParser()
        pathway = parser.parse(kgml_data)
        
        if not pathway:
            print("  Failed to parse")
            continue
        
        print(f"  Total entries: {len(pathway.entries)}")
        print(f"  Total reactions: {len(pathway.reactions)}")
        print(f"  Total relations: {len(pathway.relations)}")
        
        if pathway.relations:
            print(f"\n  Relation Types:")
            relation_types = {}
            for relation in pathway.relations:
                rel_type = relation.type
                relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
            
            for rel_type, count in sorted(relation_types.items()):
                print(f"    - {rel_type}: {count}")
            
            # Show first few relations
            print(f"\n  Sample Relations (first 5):")
            for i, relation in enumerate(pathway.relations[:5]):
                entry1 = pathway.entries.get(relation.entry1)
                entry2 = pathway.entries.get(relation.entry2)
                
                if entry1 and entry2:
                    print(f"\n    Relation {i+1}: {relation.type}")
                    print(f"      Entry1 ({entry1.id}): {entry1.type} - {entry1.name}")
                    if entry1.graphics:
                        print(f"        Label: {entry1.graphics.name}")
                    print(f"      Entry2 ({entry2.id}): {entry2.type} - {entry2.name}")
                    if entry2.graphics:
                        print(f"        Label: {entry2.graphics.name}")
                    
                    if relation.subtypes:
                        print(f"      Subtypes: {', '.join(st.name for st in relation.subtypes)}")
        else:
            print("  No relations found")
    
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)

