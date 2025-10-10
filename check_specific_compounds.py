#!/usr/bin/env python3
"""Check specific compound connections: C01159 to C00036."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser

# Search for these compounds in common pathways
target_compounds = ['C01159', 'C00036']

test_pathways = [
    'hsa00010',  # Glycolysis
    'hsa00020',  # Citrate cycle
    'hsa00620',  # Pyruvate metabolism
    'hsa00630',  # Glyoxylate and dicarboxylate metabolism
]

client = KEGGAPIClient()

print("Searching for C01159 and C00036 connections\n")
print("=" * 80)

for pathway_id in test_pathways:
    try:
        kgml_data = client.fetch_kgml(pathway_id)
        parser = KGMLParser()
        pathway = parser.parse(kgml_data)
        
        if not pathway:
            continue
        
        # Find these compounds
        found_entries = {}
        for entry_id, entry in pathway.entries.items():
            for cpd in target_compounds:
                if f'cpd:{cpd}' in entry.name or cpd in entry.name:
                    found_entries[cpd] = entry
        
        if len(found_entries) < 2:
            continue
        
        print(f"\n{pathway_id} - {pathway.title}")
        print("-" * 80)
        
        # Show the entries
        for cpd, entry in found_entries.items():
            print(f"\n{cpd}:")
            print(f"  Entry ID: {entry.id}")
            print(f"  Type: {entry.type}")
            print(f"  Name: {entry.name}")
            if entry.graphics:
                print(f"  Label: {entry.graphics.name}")
                print(f"  Position: ({entry.graphics.x}, {entry.graphics.y})")
        
        # Check reactions involving these compounds
        print(f"\nReactions involving these compounds:")
        found_in_reactions = False
        
        for reaction in pathway.reactions:
            substrate_names = [s.name for s in reaction.substrates]
            product_names = [p.name for p in reaction.products]
            
            has_c01159 = any('C01159' in name for name in substrate_names + product_names)
            has_c00036 = any('C00036' in name for name in substrate_names + product_names)
            
            if has_c01159 or has_c00036:
                found_in_reactions = True
                print(f"\n  Reaction: {reaction.name}")
                print(f"    Substrates: {', '.join(substrate_names)}")
                print(f"    Products: {', '.join(product_names)}")
                
                if has_c01159 and has_c00036:
                    print(f"    ⚠️  BOTH compounds in this reaction!")
        
        if not found_in_reactions:
            print("  None - these compounds are not in any reactions")
        
        # Check relations between these entries
        print(f"\nRelations between these entries:")
        found_in_relations = False
        
        for relation in pathway.relations:
            entry1 = pathway.entries.get(relation.entry1)
            entry2 = pathway.entries.get(relation.entry2)
            
            if entry1 and entry2:
                entry1_has = any(cpd in entry1.name for cpd in ['C01159', 'C00036'])
                entry2_has = any(cpd in entry2.name for cpd in ['C01159', 'C00036'])
                
                if entry1_has and entry2_has:
                    found_in_relations = True
                    print(f"\n  Relation: {relation.type}")
                    print(f"    Entry1 ({entry1.id}): {entry1.type} - {entry1.name}")
                    print(f"    Entry2 ({entry2.id}): {entry2.type} - {entry2.name}")
                    if relation.subtypes:
                        print(f"    Subtypes: {', '.join(st.name for st in relation.subtypes)}")
                    print(f"    ⚠️  This creates a direct compound-to-compound link!")
        
        if not found_in_relations:
            print("  None")
            
    except Exception as e:
        pass

print("\n" + "=" * 80)

