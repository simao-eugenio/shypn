#!/usr/bin/env python3
"""Quick script to check structure of an imported pathway."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg import fetch_pathway, parse_kgml
from shypn.importer.kegg.pathway_converter import convert_pathway, convert_pathway_enhanced
from shypn.pathway.options import get_standard_options

# Fetch a small pathway
pathway_id = 'hsa04668'
print(f"Fetching {pathway_id}...")
kgml = fetch_pathway(pathway_id)
pathway = parse_kgml(kgml)

print(f"\n=== Parsed Pathway ===")
print(f"Compounds: {len(pathway.get_compounds())}")
print(f"Reactions: {len(pathway.reactions)}")

# Try basic conversion first
print(f"\n=== Basic Conversion ===")
try:
    document_basic = convert_pathway(pathway)
    print(f"Places: {len(document_basic.places)}")
    print(f"Transitions: {len(document_basic.transitions)}")
    print(f"Arcs: {len(document_basic.arcs)}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Try enhanced conversion
print(f"\n=== Enhanced Conversion ===")
try:
    options = get_standard_options()
    document_enhanced = convert_pathway_enhanced(pathway, enhancement_options=options)
    print(f"Places: {len(document_enhanced.places)}")
    print(f"Transitions: {len(document_enhanced.transitions)}")
    print(f"Arcs: {len(document_enhanced.arcs)}")
    
    # Check for invalid arcs
    if len(document_enhanced.arcs) > 0:
        print(f"\n=== Arc Validation ===")
        place_ids = {p.id for p in document_enhanced.places}
        transition_ids = {t.id for t in document_enhanced.transitions}
        
        place_to_place = []
        trans_to_trans = []
        
        for arc in document_enhanced.arcs:
            source_is_place = arc.source_id in place_ids
            target_is_place = arc.target_id in place_ids
            
            if source_is_place and target_is_place:
                place_to_place.append(arc)
            elif not source_is_place and not target_is_place:
                trans_to_trans.append(arc)
        
        print(f"Place-to-Place arcs: {len(place_to_place)}")
        print(f"Transition-to-Transition arcs: {len(trans_to_trans)}")
        
        if place_to_place:
            print(f"\n⚠️  WARNING: Found {len(place_to_place)} Place-to-Place arcs!")
            for arc in place_to_place[:5]:
                source_place = next((p for p in document_enhanced.places if p.id == arc.source_id), None)
                target_place = next((p for p in document_enhanced.places if p.id == arc.target_id), None)
                print(f"  Arc {arc.id}: Place '{source_place.label or source_place.name}' → Place '{target_place.label or target_place.name}'")
        
        if not place_to_place and not trans_to_trans:
            print("✅ All arcs follow bipartite property")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
