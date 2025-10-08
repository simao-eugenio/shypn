#!/usr/bin/env python3
"""Test complete KEGG pathway to Petri net conversion."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.importer.kegg import (
    KEGGAPIClient,
    KGMLParser,
    PathwayConverter,
    ConversionOptions
)

def test_full_conversion():
    """Test complete workflow: fetch → parse → convert."""
    print("=" * 60)
    print("Testing Full KEGG Pathway Conversion")
    print("=" * 60)
    
    # Step 1: Fetch KGML
    print("\nStep 1: Fetching KGML from KEGG API...")
    client = KEGGAPIClient()
    kgml = client.fetch_kgml("hsa00010")
    
    if not kgml:
        print("✗ Failed to fetch KGML")
        return False
    
    print("✓ Fetched KGML successfully")
    
    # Step 2: Parse KGML
    print("\nStep 2: Parsing KGML XML...")
    parser = KGMLParser()
    pathway = parser.parse(kgml)
    
    if not pathway:
        print("✗ Failed to parse KGML")
        return False
    
    print("✓ Parsed pathway successfully")
    print(f"  Title: {pathway.title}")
    print(f"  Compounds: {len(pathway.get_compounds())}")
    print(f"  Genes/Enzymes: {len(pathway.get_genes())}")
    print(f"  Reactions: {len(pathway.reactions)}")
    
    # Step 3: Convert to Petri net (with cofactors)
    print("\n" + "=" * 60)
    print("Step 3a: Converting to Petri net (with cofactors)...")
    options = ConversionOptions(
        coordinate_scale=2.5,
        include_cofactors=True,
        split_reversible=False,
        add_initial_marking=True,
        initial_tokens=1
    )
    
    converter = PathwayConverter()
    document = converter.convert(pathway, options)
    
    print(f"\n✓ Conversion complete!")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    
    # Show sample objects
    print("\n  Sample places:")
    for place in document.places[:5]:
        print(f"    [{place.id}] {place.label} at ({place.x:.1f}, {place.y:.1f})")
    
    print("\n  Sample transitions:")
    for trans in document.transitions[:5]:
        print(f"    [{trans.id}] {trans.label} at ({trans.x:.1f}, {trans.y:.1f})")
    
    # Test saving
    print("\n" + "=" * 60)
    print("Step 4: Saving to file...")
    test_file = "/tmp/glycolysis_with_cofactors.shy"
    document.save_to_file(test_file)
    print(f"✓ Saved to {test_file}")
    
    # Step 5: Convert without cofactors
    print("\n" + "=" * 60)
    print("Step 3b: Converting to Petri net (without cofactors)...")
    options_no_cofactors = ConversionOptions(
        coordinate_scale=2.5,
        include_cofactors=False,
        split_reversible=False,
        add_initial_marking=True
    )
    
    document2 = converter.convert(pathway, options_no_cofactors)
    
    print(f"\n✓ Conversion complete!")
    print(f"  Places: {len(document2.places)}")
    print(f"  Transitions: {len(document2.transitions)}")
    print(f"  Arcs: {len(document2.arcs)}")
    
    # Test saving
    print("\n" + "=" * 60)
    print("Step 5: Saving simplified version...")
    test_file2 = "/tmp/glycolysis_no_cofactors.shy"
    document2.save_to_file(test_file2)
    print(f"✓ Saved to {test_file2}")
    
    # Step 6: Test with split reversible
    print("\n" + "=" * 60)
    print("Step 3c: Converting with split reversible reactions...")
    options_split = ConversionOptions(
        coordinate_scale=2.5,
        include_cofactors=False,
        split_reversible=True,
        add_initial_marking=False
    )
    
    document3 = converter.convert(pathway, options_split)
    
    print(f"\n✓ Conversion complete!")
    print(f"  Places: {len(document3.places)}")
    print(f"  Transitions: {len(document3.transitions)}")
    print(f"  Arcs: {len(document3.arcs)}")
    print(f"  Note: More transitions due to split reversible reactions")
    
    test_file3 = "/tmp/glycolysis_split_reversible.shy"
    document3.save_to_file(test_file3)
    print(f"✓ Saved to {test_file3}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary of Generated Files:")
    print("=" * 60)
    print(f"\n1. {test_file}")
    print(f"   - With cofactors (ATP, NAD+, etc.)")
    print(f"   - {len(document.places)} places, {len(document.transitions)} transitions")
    
    print(f"\n2. {test_file2}")
    print(f"   - Without cofactors (cleaner)")
    print(f"   - {len(document2.places)} places, {len(document2.transitions)} transitions")
    
    print(f"\n3. {test_file3}")
    print(f"   - Split reversible reactions")
    print(f"   - {len(document3.places)} places, {len(document3.transitions)} transitions")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    print("\nYou can now open these files in shypn:")
    print(f"  python3 src/shypn.py")
    print(f"  File > Open > {test_file2}")
    
    return True

if __name__ == '__main__':
    try:
        success = test_full_conversion()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
