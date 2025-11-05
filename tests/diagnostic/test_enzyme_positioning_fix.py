#!/usr/bin/env python3
"""
Test Enzyme Positioning Fix

Verify that enzyme places are positioned ABOVE their catalyzed reactions,
not using KGML coordinates. This prevents layout flattening.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway


def test_enzyme_positioning():
    """Test that enzymes are positioned above reactions."""
    print("\n" + "="*70)
    print("TEST: Enzyme Positioning Fix")
    print("="*70)
    
    print("\n1. Fetching KEGG pathway hsa00010...")
    kgml = fetch_pathway("hsa00010")
    print(f"   ✓ Fetched pathway data ({len(kgml)} bytes)")
    
    print("\n2. Parsing KGML...")
    pathway = parse_kgml(kgml)
    print(f"   ✓ Parsed: {len(pathway.entries)} entries, {len(pathway.reactions)} reactions")
    
    print("\n3. Converting with create_enzyme_places=True...")
    document = convert_pathway(
        pathway,
        coordinate_scale=3.0,
        include_cofactors=False,
        create_enzyme_places=True,
        filter_isolated_compounds=True
    )
    
    print(f"   ✓ Converted to Petri net:")
    print(f"     - {len(document.places)} places")
    print(f"     - {len(document.transitions)} transitions")
    print(f"     - {len(document.arcs)} arcs")
    
    # Identify enzyme places and check their positions
    print("\n4. Analyzing enzyme place positions...")
    enzyme_places = [p for p in document.places if p.metadata.get('is_enzyme', False)]
    print(f"   Found {len(enzyme_places)} enzyme places")
    
    if not enzyme_places:
        print("   ✗ ERROR: No enzyme places found!")
        return False
    
    # Check that enzymes are positioned above their catalyzed reactions
    correct_positioning = 0
    incorrect_positioning = 0
    
    for enzyme_place in enzyme_places[:5]:  # Check first 5
        reaction_name = enzyme_place.metadata.get('catalyzes_reaction')
        
        # Find the catalyzed transition
        catalyzed_transition = None
        for transition in document.transitions:
            if transition.metadata.get('reaction_name') == reaction_name:
                catalyzed_transition = transition
                break
        
        if catalyzed_transition:
            enzyme_y = enzyme_place.y
            reaction_y = catalyzed_transition.y
            
            if enzyme_y < reaction_y:  # Y increases downward, so enzyme should have smaller Y
                correct_positioning += 1
                print(f"   ✓ {enzyme_place.label}: y={enzyme_y:.1f} (above reaction y={reaction_y:.1f})")
            else:
                incorrect_positioning += 1
                print(f"   ✗ {enzyme_place.label}: y={enzyme_y:.1f} (NOT above reaction y={reaction_y:.1f})")
    
    print(f"\n5. Positioning Summary:")
    print(f"   ✓ Correct: {correct_positioning}")
    print(f"   ✗ Incorrect: {incorrect_positioning}")
    
    if incorrect_positioning > 0:
        print("\n✗ TEST FAILED: Some enzymes not positioned above reactions")
        return False
    
    print("\n" + "="*70)
    print("✓ TEST PASSED: Enzymes correctly positioned above reactions")
    print("="*70)
    return True


if __name__ == '__main__':
    success = test_enzyme_positioning()
    sys.exit(0 if success else 1)
