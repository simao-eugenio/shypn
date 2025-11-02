#!/usr/bin/env python3
"""
Test to verify that enzyme places are only created for reactions in the pathway.

This prevents isolated enzyme places from appearing in the GUI.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg import parse_kgml, convert_pathway_enhanced


def test_enzyme_filtering():
    """Test that enzyme places are filtered based on pathway reactions."""
    
    # Read hsa00010 (Glycolysis pathway)
    kgml_path = 'workspace/projects/Interactive/pathways/hsa00010.kgml'
    
    if not os.path.exists(kgml_path):
        print(f"⚠️  Test skipped: {kgml_path} not found")
        return
    
    with open(kgml_path, 'r') as f:
        kgml_data = f.read()
    
    parsed = parse_kgml(kgml_data)
    
    # Convert with enzyme places enabled
    document = convert_pathway_enhanced(
        parsed,
        coordinate_scale=2.5,
        include_cofactors=False,
        filter_isolated_compounds=True,
        create_enzyme_places=True
    )
    
    # Find isolated places
    place_arcs = {place: [] for place in document.places}
    for arc in document.arcs:
        if arc.source in document.places:
            place_arcs[arc.source].append(arc)
        if arc.target in document.places:
            place_arcs[arc.target].append(arc)
    
    isolated_places = [p for p in document.places if len(place_arcs[p]) == 0]
    isolated_catalysts = [p for p in isolated_places if getattr(p, 'is_catalyst', False)]
    isolated_compounds = [p for p in isolated_places if not getattr(p, 'is_catalyst', False)]
    
    # Verify results
    print(f"Test: Enzyme Filtering")
    print(f"="*80)
    print(f"Total places: {len(document.places)}")
    print(f"Total arcs: {len(document.arcs)}")
    print(f"Isolated catalyst places: {len(isolated_catalysts)}")
    print(f"Isolated compound places: {len(isolated_compounds)}")
    
    # Check expectations
    success = True
    
    if isolated_catalysts:
        print(f"\n❌ FAIL: Found {len(isolated_catalysts)} isolated catalyst places:")
        for place in isolated_catalysts[:5]:
            metadata = getattr(place, 'metadata', {})
            reaction = metadata.get('catalyzes_reaction', 'N/A')
            print(f"  - {place.label} → {reaction}")
        success = False
    else:
        print(f"\n✓ PASS: No isolated catalyst places")
    
    if isolated_compounds:
        print(f"\n❌ FAIL: Found {len(isolated_compounds)} isolated compound places:")
        for place in isolated_compounds[:5]:
            print(f"  - {place.label}")
        success = False
    else:
        print(f"✓ PASS: No isolated compound places")
    
    # Verify enzyme count is reasonable
    catalyst_places = [p for p in document.places if getattr(p, 'is_catalyst', False)]
    if len(catalyst_places) > 50:
        print(f"\n⚠️  WARNING: {len(catalyst_places)} catalyst places (expected ~39 for hsa00010)")
        success = False
    else:
        print(f"✓ PASS: Reasonable enzyme count ({len(catalyst_places)} catalyst places)")
    
    if success:
        print(f"\n{'='*80}")
        print(f"✓ ALL TESTS PASSED")
        print(f"{'='*80}")
        return 0
    else:
        print(f"\n{'='*80}")
        print(f"❌ SOME TESTS FAILED")
        print(f"{'='*80}")
        return 1


if __name__ == '__main__':
    exit_code = test_enzyme_filtering()
    sys.exit(exit_code if exit_code is not None else 0)
