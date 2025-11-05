#!/usr/bin/env python3
"""
Diagnostic test to investigate isolated places in KEGG imports.

This test imports a pathway and analyzes which places have no arcs,
to understand why isolated places are appearing despite filtering.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg import parse_kgml
from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
from shypn.importer.kegg.converter_base import ConversionOptions


def analyze_isolated_places(filepath, show_catalysts=False):
    """Analyze isolated places in a KEGG pathway file.
    
    Args:
        filepath: Path to .kgml file
        show_catalysts: Whether to create enzyme places
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {filepath}")
    print(f"Show catalysts: {show_catalysts}")
    print(f"{'='*80}\n")
    
    # Read KGML file
    with open(filepath, 'r') as f:
        kgml_data = f.read()
    
    # Parse and convert
    parsed = parse_kgml(kgml_data)
    
    print(f"Parsed pathway: {parsed.name} ({parsed.org})")
    print(f"  Reactions: {len(parsed.reactions)}")
    print(f"  Compounds: {len(parsed.get_compounds())}")
    print(f"  Genes: {len([e for e in parsed.entries.values() if e.is_gene()])}\n")
    
    # Convert with filtering enabled
    document = convert_pathway_enhanced(
        parsed,
        coordinate_scale=2.5,
        include_cofactors=False,  # Exclude cofactors for cleaner test
        filter_isolated_compounds=True,  # THIS IS THE KEY OPTION
        create_enzyme_places=show_catalysts
    )
    
    print(f"Converted document:")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}\n")
    
    # Build arc connectivity map
    place_arcs = {place: [] for place in document.places}
    
    for arc in document.arcs:
        # Check if source is a place
        if arc.source in document.places:
            place_arcs[arc.source].append(arc)
        # Check if target is a place
        if arc.target in document.places:
            place_arcs[arc.target].append(arc)
    
    # Find isolated places (places with no arcs)
    isolated_places = []
    catalyst_places = []
    
    for place in document.places:
        arc_count = len(place_arcs[place])
        is_catalyst = getattr(place, 'is_catalyst', False)
        
        if arc_count == 0:
            if is_catalyst:
                catalyst_places.append(place)
            else:
                isolated_places.append(place)
    
    # Report results
    print(f"{'='*80}")
    print(f"ISOLATED PLACES ANALYSIS")
    print(f"{'='*80}\n")
    
    print(f"Total places: {len(document.places)}")
    print(f"Places with arcs: {sum(1 for p in document.places if len(place_arcs[p]) > 0)}")
    print(f"Isolated non-catalyst places: {len(isolated_places)}")
    print(f"Isolated catalyst places: {len(catalyst_places)}")
    print()
    
    if isolated_places:
        print(f"⚠️  FOUND {len(isolated_places)} ISOLATED NON-CATALYST PLACES:")
        for i, place in enumerate(isolated_places, 1):
            metadata = getattr(place, 'metadata', {})
            kegg_id = metadata.get('kegg_id', 'N/A')
            print(f"  {i}. {place.label} (ID: {place.id}, KEGG: {kegg_id})")
        print()
    else:
        print("✓ No isolated non-catalyst places found")
        print()
    
    if catalyst_places:
        print(f"ℹ️  FOUND {len(catalyst_places)} ISOLATED CATALYST PLACES:")
        print("   (These are enzyme places with no test arcs - might be expected)")
        for i, place in enumerate(catalyst_places[:5], 1):  # Show first 5
            metadata = getattr(place, 'metadata', {})
            kegg_id = metadata.get('kegg_id', 'N/A')
            catalyzes = metadata.get('catalyzes_reaction', 'N/A')
            print(f"  {i}. {place.label} (ID: {place.id}, KEGG: {kegg_id}, Catalyzes: {catalyzes})")
        if len(catalyst_places) > 5:
            print(f"  ... and {len(catalyst_places) - 5} more")
        print()
    
    # Check if all places in reactions are in the document
    print(f"{'='*80}")
    print(f"VERIFICATION: Are all reaction compounds in place_map?")
    print(f"{'='*80}\n")
    
    used_compound_ids = set()
    for reaction in parsed.reactions:
        for substrate in reaction.substrates:
            used_compound_ids.add(substrate.id)
        for product in reaction.products:
            used_compound_ids.add(product.id)
    
    place_ids_in_doc = {p.metadata.get('kegg_entry_id') for p in document.places if hasattr(p, 'metadata')}
    
    missing_compounds = used_compound_ids - place_ids_in_doc
    extra_compounds = place_ids_in_doc - used_compound_ids
    
    print(f"Compounds used in reactions: {len(used_compound_ids)}")
    print(f"Compound places in document: {len(place_ids_in_doc)}")
    print(f"Missing compounds (should have places but don't): {len(missing_compounds)}")
    print(f"Extra compounds (have places but not in reactions): {len(extra_compounds)}\n")
    
    if missing_compounds:
        print("⚠️  Missing compounds (first 10):")
        for comp_id in list(missing_compounds)[:10]:
            print(f"  - {comp_id}")
        print()
    
    if extra_compounds:
        print("⚠️  Extra compounds (first 10):")
        for comp_id in list(extra_compounds)[:10]:
            print(f"  - {comp_id}")
        print()


def main():
    """Run diagnostic tests."""
    # Test with a known pathway (adjust path as needed)
    test_pathways = [
        'workspace/examples/pathways/hsa00010.kgml',  # Glycolysis
        'workspace/examples/pathways/hsa00020.kgml',  # TCA cycle
    ]
    
    for pathway_file in test_pathways:
        if os.path.exists(pathway_file):
            # Test without catalysts
            analyze_isolated_places(pathway_file, show_catalysts=False)
            
            # Test with catalysts
            analyze_isolated_places(pathway_file, show_catalysts=True)
        else:
            print(f"⚠️  Pathway file not found: {pathway_file}")


if __name__ == '__main__':
    main()
