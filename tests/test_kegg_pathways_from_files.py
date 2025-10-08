#!/usr/bin/env python3
"""Test KEGG pathway conversion with locally saved pathways.

This test uses pre-downloaded KGML files from models/pathways/ directory
to test the complete conversion pipeline without hitting the KEGG API.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.importer.kegg.kgml_parser import parse_kgml
from shypn.importer.kegg import KEGGConverter


def test_pathway_from_file(pathway_id: str, pathway_dir: Path) -> bool:
    """Test converting a pathway from saved KGML file.
    
    Args:
        pathway_id: Pathway ID (e.g., "hsa00010")
        pathway_dir: Directory containing KGML files
        
    Returns:
        True if successful
    """
    kgml_file = pathway_dir / f"{pathway_id}.kgml"
    
    if not kgml_file.exists():
        print(f"✗ File not found: {kgml_file}")
        print(f"  Run: python3 scripts/fetch_kegg_pathway.py {pathway_id}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Testing {pathway_id}")
    print(f"{'='*60}")
    
    # Load KGML
    print(f"\n1. Loading KGML from {kgml_file.name}...")
    with open(kgml_file, 'r', encoding='utf-8') as f:
        kgml_xml = f.read()
    print(f"   ✓ Loaded {len(kgml_xml)} bytes")
    
    # Parse
    print(f"\n2. Parsing KGML...")
    pathway = parse_kgml(kgml_xml)
    if not pathway:
        print("   ✗ Failed to parse")
        return False
    print(f"   ✓ Parsed: {pathway.title}")
    print(f"     - Entries: {len(pathway.entries)}")
    print(f"     - Reactions: {len(pathway.reactions)}")
    print(f"     - Relations: {len(pathway.relations)}")
    
    # Get statistics
    compounds = pathway.get_compounds()
    genes = pathway.get_genes()
    print(f"     - Compounds: {len(compounds)}")
    print(f"     - Genes/Enzymes: {len(genes)}")
    
    # Convert
    print(f"\n3. Converting to Petri net...")
    converter = KEGGConverter()
    document = converter.convert(pathway)
    
    print(f"   ✓ Converted to DocumentModel")
    print(f"     - Places: {len(document.places)}")
    print(f"     - Transitions: {len(document.transitions)}")
    print(f"     - Arcs: {len(document.arcs)}")
    
    # Save
    output_file = pathway_dir / f"{pathway_id}.shy"
    print(f"\n4. Saving to {output_file.name}...")
    document.save_to_file(str(output_file))
    print(f"   ✓ Saved Petri net model")
    
    # Validate
    print(f"\n5. Validating...")
    errors = []
    
    # Check that we have objects
    if len(document.places) == 0:
        errors.append("No places created")
    if len(document.transitions) == 0:
        errors.append("No transitions created")
    
    # Check arcs
    for arc in document.arcs:
        if arc.source is None or arc.target is None:
            errors.append(f"Arc {arc.id} has None source or target")
    
    if errors:
        print("   ✗ Validation errors:")
        for error in errors:
            print(f"     - {error}")
        return False
    else:
        print("   ✓ Validation passed")
    
    print(f"\n{'='*60}")
    print(f"✓ {pathway_id} conversion successful!")
    print(f"{'='*60}")
    
    return True


def main():
    """Run tests on saved pathways."""
    pathway_dir = Path(__file__).parent.parent / 'models' / 'pathways'
    
    print("KEGG Pathway Conversion Test (using saved pathways)")
    print("="*60)
    
    # Test pathways (if they exist)
    test_pathways = ['hsa00010', 'hsa00020', 'hsa00030']
    
    results = {}
    for pathway_id in test_pathways:
        try:
            results[pathway_id] = test_pathway_from_file(pathway_id, pathway_dir)
        except Exception as e:
            print(f"\n✗ Error testing {pathway_id}: {e}")
            import traceback
            traceback.print_exc()
            results[pathway_id] = False
    
    # Summary
    print(f"\n\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for pathway_id, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {pathway_id}")
    
    print(f"\nTotal: {passed}/{total} passed")
    print(f"{'='*60}")
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
