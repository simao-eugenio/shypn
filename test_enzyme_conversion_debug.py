#!/usr/bin/env python3
"""
Debug test to understand why enzyme places don't have test arcs.

This test will trace through the enzyme conversion process.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg import parse_kgml, convert_pathway_enhanced
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def debug_enzyme_conversion():
    """Debug enzyme conversion for hsa00010."""
    
    # Find the KGML file
    kgml_path = 'workspace/projects/Interactive/pathways/hsa00010.kgml'
    
    if not os.path.exists(kgml_path):
        # Try alternative location
        import glob
        kgml_files = glob.glob('workspace/**/hsa00010.kgml', recursive=True)
        if kgml_files:
            kgml_path = kgml_files[0]
        else:
            print(f"⚠️  Could not find hsa00010.kgml")
            return
    
    print(f"Reading KGML from: {kgml_path}")
    
    with open(kgml_path, 'r') as f:
        kgml_data = f.read()
    
    # Parse
    parsed = parse_kgml(kgml_data)
    
    print(f"\n{'='*80}")
    print(f"PARSED PATHWAY INFO")
    print(f"{'='*80}")
    print(f"Name: {parsed.name}")
    print(f"Organism: {parsed.org}")
    print(f"Total entries: {len(parsed.entries)}")
    print(f"Total reactions: {len(parsed.reactions)}")
    
    # Count enzyme entries
    enzyme_entries = []
    for entry_id, entry in parsed.entries.items():
        if entry.is_gene() and entry.reaction:
            enzyme_entries.append(entry)
    
    print(f"Enzyme entries (genes with reactions): {len(enzyme_entries)}")
    
    # Show first few enzymes
    print(f"\nFirst 5 enzyme entries:")
    for i, entry in enumerate(enzyme_entries[:5], 1):
        print(f"  {i}. Entry {entry.id} ({entry.name}) → reaction: {entry.reaction}")
    
    # Show reaction names
    print(f"\nFirst 10 reactions:")
    for i, reaction in enumerate(parsed.reactions[:10], 1):
        print(f"  {i}. Reaction: {reaction.name}")
    
    # Convert WITH enzyme places
    print(f"\n{'='*80}")
    print(f"CONVERTING WITH create_enzyme_places=True")
    print(f"{'='*80}")
    
    document = convert_pathway_enhanced(
        parsed,
        coordinate_scale=2.5,
        include_cofactors=False,
        filter_isolated_compounds=True,
        create_enzyme_places=True  # ENABLE enzyme places
    )
    
    print(f"\n{'='*80}")
    print(f"CONVERSION RESULTS")
    print(f"{'='*80}")
    print(f"Places: {len(document.places)}")
    print(f"Transitions: {len(document.transitions)}")
    print(f"Arcs: {len(document.arcs)}")
    
    # Count arc types
    test_arcs = []
    normal_arcs = []
    
    for arc in document.arcs:
        arc_type = getattr(arc, 'arc_type', 'normal')
        if arc_type == 'test' or arc.__class__.__name__ == 'TestArc':
            test_arcs.append(arc)
        else:
            normal_arcs.append(arc)
    
    print(f"Normal arcs: {len(normal_arcs)}")
    print(f"Test arcs: {len(test_arcs)}")
    
    # Check metadata
    print(f"\nDocument metadata:")
    if hasattr(document, 'metadata') and document.metadata:
        for key, value in document.metadata.items():
            print(f"  {key}: {value}")
    else:
        print("  NO METADATA")
    
    # Count catalyst places
    catalyst_places = [p for p in document.places if getattr(p, 'is_catalyst', False)]
    print(f"\nCatalyst places: {len(catalyst_places)}")
    
    # Find isolated catalyst places
    place_arcs = {place: [] for place in document.places}
    for arc in document.arcs:
        if arc.source in document.places:
            place_arcs[arc.source].append(arc)
        if arc.target in document.places:
            place_arcs[arc.target].append(arc)
    
    isolated_catalysts = [p for p in catalyst_places if len(place_arcs[p]) == 0]
    print(f"Isolated catalyst places: {len(isolated_catalysts)}")
    
    if test_arcs:
        print(f"\n{'='*80}")
        print(f"TEST ARCS (first 5):")
        print(f"{'='*80}")
        for i, arc in enumerate(test_arcs[:5], 1):
            print(f"{i}. {arc.source.label} → {arc.target.label}")
            if hasattr(arc, 'metadata') and arc.metadata:
                print(f"   Metadata: {arc.metadata}")
    else:
        print(f"\n⚠️  NO TEST ARCS CREATED!")
        print(f"\nThis explains why catalyst places are isolated.")
        print(f"\nPossible reasons:")
        print(f"  1. Enzyme entries don't have matching transitions")
        print(f"  2. reaction_name_to_transition mapping is wrong")
        print(f"  3. entry.reaction format doesn't match reaction.name format")


if __name__ == '__main__':
    debug_enzyme_conversion()
