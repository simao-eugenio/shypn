#!/usr/bin/env python3
"""
Phase 0: KEGG Parser Investigation - Test 1
Test if KEGG relations are being converted to arcs or visual lines.

This script analyzes:
1. Number of relations in KEGG file
2. Number of reactions in KEGG file
3. Number of arcs created by converter
4. Whether relations count affects arc count
"""

import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
from shypn.pathway.options import EnhancementOptions

print("=" * 80)
print("PHASE 0 - TEST 1: KEGG Relations vs Arcs Analysis")
print("=" * 80)
print()

# Test multiple KEGG pathways
test_files = [
    ("workspace/examples/pathways/hsa00010.shy", "hsa00010 - Glycolysis"),
    ("workspace/examples/pathways/hsa00020.shy", "hsa00020 - Citric acid cycle"),
    ("workspace/examples/pathways/hsa00030.shy", "hsa00030 - Pentose phosphate"),
]

# First, we need to download fresh KGML files to analyze
kegg_pathways = [
    ("hsa00010", "workspace/test_data/hsa00010.xml"),
    ("hsa00020", "workspace/test_data/hsa00020.xml"),
    ("hsa00030", "workspace/test_data/hsa00030.xml"),
]

print("Step 1: Downloading fresh KEGG pathways...")
print()

import urllib.request
import os

os.makedirs("workspace/test_data", exist_ok=True)

for pathway_id, filepath in kegg_pathways:
    if not os.path.exists(filepath):
        url = f"https://rest.kegg.jp/get/{pathway_id}/kgml"
        print(f"Downloading {pathway_id}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"  ✓ Saved to {filepath}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    else:
        print(f"  ✓ Already exists: {filepath}")

print()
print("=" * 80)
print("Step 2: Analyzing KEGG Files")
print("=" * 80)
print()

parser = KGMLParser()

for pathway_id, filepath in kegg_pathways:
    print(f"Analyzing {pathway_id}:")
    print("-" * 60)
    
    try:
        # Parse KEGG file
        pathway = parser.parse_file(filepath)
        
        # Count elements
        num_entries = len(pathway.entries)
        num_reactions = len(pathway.reactions)
        num_relations = len(pathway.relations)
        
        print(f"  Entries:   {num_entries}")
        print(f"  Reactions: {num_reactions}")
        print(f"  Relations: {num_relations}")
        
        # Analyze relation types
        if num_relations > 0:
            relation_types = {}
            for rel in pathway.relations:
                rel_type = rel.type
                relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
            
            print(f"  Relation types:")
            for rel_type, count in sorted(relation_types.items()):
                print(f"    - {rel_type}: {count}")
        
        # Convert to Petri net
        print(f"  Converting to Petri net...")
        enhancement_options = EnhancementOptions(
            enable_layout_optimization=False,
            enable_arc_routing=False,
            enable_metadata_enhancement=False
        )
        
        document = convert_pathway_enhanced(
            pathway,
            coordinate_scale=1.0,
            include_cofactors=False,
            enhancement_options=enhancement_options
        )
        
        num_places = len(document.places)
        num_transitions = len(document.transitions)
        num_arcs = len(document.arcs)
        
        print(f"  Petri net:")
        print(f"    - Places:      {num_places}")
        print(f"    - Transitions: {num_transitions}")
        print(f"    - Arcs:        {num_arcs}")
        
        # Calculate expected arcs from reactions
        # Each reaction substrate creates 1 arc (Place → Transition)
        # Each reaction product creates 1 arc (Transition → Place)
        expected_arcs = 0
        for reaction in pathway.reactions:
            expected_arcs += len(reaction.substrates) + len(reaction.products)
        
        print(f"    - Expected arcs (from reactions): {expected_arcs}")
        
        # Analysis
        print(f"  Analysis:")
        if num_arcs == expected_arcs:
            print(f"    ✓ Arc count matches reactions (NO extra arcs from relations)")
        else:
            print(f"    ⚠ Arc count DOES NOT match reactions!")
            print(f"      Difference: {num_arcs - expected_arcs} arcs")
            print(f"      Possible relations converted: {num_arcs - expected_arcs}")
        
        if num_relations > 0 and num_arcs > expected_arcs:
            print(f"    ❌ WARNING: Relations may be converted to arcs!")
        elif num_relations > 0 and num_arcs == expected_arcs:
            print(f"    ✓ Relations present but NOT converted to arcs (CORRECT)")
        
        print()
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("If 'Arc count matches reactions' for all pathways:")
print("  → Relations are NOT being converted to arcs (GOOD)")
print()
print("If 'Arc count DOES NOT match' and difference ≈ relations count:")
print("  → Relations ARE being converted to arcs (BUG - needs fix)")
print()
print("=" * 80)
