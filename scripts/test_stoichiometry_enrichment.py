#!/usr/bin/env python3
"""Manual testing script for KEGG stoichiometry enrichment.

This script tests the enrichment functionality with real KEGG pathways.
Used for development and debugging.

Usage:
    python scripts/test_stoichiometry_enrichment.py
    python scripts/test_stoichiometry_enrichment.py --pathway hsa00020
    python scripts/test_stoichiometry_enrichment.py --verbose
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway_enhanced
from shypn.services.enrichment import KEGGStoichiometryEnricher
from shypn.netobjs import DocumentModel


def progress_callback(current, total, message):
    """Progress callback for enrichment."""
    percent = (current / total) * 100 if total > 0 else 0
    sys.stdout.write(f"\r[{percent:5.1f}%] {message:<60}")
    sys.stdout.flush()


def test_basic_enrichment(pathway_id="hsa00010"):
    """Test basic enrichment workflow.
    
    Args:
        pathway_id: KEGG pathway ID (default: hsa00010 - Glycolysis)
    """
    print("=" * 80)
    print(f"TEST 1: Basic Enrichment ({pathway_id})")
    print("=" * 80)
    print()
    
    # Import pathway
    print(f"Importing {pathway_id}...")
    kgml = fetch_pathway(pathway_id)
    pathway = parse_kgml(kgml)
    document = convert_pathway_enhanced(
        pathway,
        include_cofactors=False,  # Don't include cofactors initially
        filter_isolated_compounds=True
    )
    
    print(f"✓ Imported: {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")
    print()
    
    # Show reactions with IDs
    reactions = [t for t in document.transitions 
                 if hasattr(t, 'metadata') and t.metadata 
                 and t.metadata.get('kegg_reaction_id')]
    print(f"Found {len(reactions)} transitions with reaction IDs:")
    for t in reactions[:5]:  # Show first 5
        reaction_id = t.metadata.get('kegg_reaction_id')
        print(f"  - {t.label}: {reaction_id}")
    if len(reactions) > 5:
        print(f"  ... and {len(reactions) - 5} more")
    print()
    
    # Enrich
    print("Enriching model with complete stoichiometry...")
    enricher = KEGGStoichiometryEnricher(progress_callback=progress_callback)
    result = enricher.enrich_document(document)
    print()  # New line after progress
    print()
    
    # Results
    print(result.get_summary())
    print()
    print(f"✓ After enrichment: {len(document.places)} places, {len(document.arcs)} arcs")
    print()
    
    # Show added compounds
    added_places = [p for p in document.places 
                    if hasattr(p, 'metadata') and p.metadata 
                    and p.metadata.get('source') == 'stoichiometry_enrichment']
    if added_places:
        print(f"Added {len(added_places)} cofactor places:")
        for p in added_places:
            compound_id = p.metadata.get('compound_id', 'unknown')
            print(f"  - {p.name} ({compound_id})")
    print()
    
    return result


def test_validation():
    """Test document validation."""
    print("=" * 80)
    print("TEST 2: Document Validation")
    print("=" * 80)
    print()
    
    enricher = KEGGStoichiometryEnricher()
    
    # Test 1: Valid KEGG document
    print("Test 2.1: Valid KEGG document")
    kgml = fetch_pathway("hsa00010")
    pathway = parse_kgml(kgml)
    document = convert_pathway_enhanced(pathway)
    
    is_valid, issues = enricher.validate_document(document)
    print(f"  Valid: {is_valid}")
    if issues:
        print(f"  Issues: {issues}")
    print()
    
    # Test 2: Non-KEGG document
    print("Test 2.2: Non-KEGG document")
    document = DocumentModel()
    document.metadata = {'data_source': 'manual'}
    
    is_valid, issues = enricher.validate_document(document)
    print(f"  Valid: {is_valid}")
    if issues:
        print(f"  Issues:")
        for issue in issues:
            print(f"    - {issue}")
    print()
    
    # Test 3: Already enriched
    print("Test 2.3: Already enriched document")
    kgml = fetch_pathway("hsa00010")
    pathway = parse_kgml(kgml)
    document = convert_pathway_enhanced(pathway)
    document.metadata['stoichiometry_enriched'] = True
    
    is_valid, issues = enricher.validate_document(document)
    print(f"  Valid: {is_valid}")
    if issues:
        print(f"  Issues:")
        for issue in issues:
            print(f"    - {issue}")
    print()


def test_reaction_parsing():
    """Test reaction equation parsing."""
    print("=" * 80)
    print("TEST 3: Reaction Equation Parsing")
    print("=" * 80)
    print()
    
    enricher = KEGGStoichiometryEnricher()
    
    # Test different equation formats
    test_reactions = [
        ("R00200", "Simple reaction"),
        ("R00710", "With coefficients"),
        ("R00756", "Isomerization"),
    ]
    
    for reaction_id, description in test_reactions:
        print(f"Test: {reaction_id} ({description})")
        try:
            stoich = enricher._fetch_reaction_stoichiometry(reaction_id)
            print(f"  ✓ Equation: {stoich.equation}")
            print(f"  ✓ Reversible: {stoich.is_reversible}")
            print(f"  ✓ Substrates: {[f'{s.coefficient} {s.compound_id}' for s in stoich.substrates]}")
            print(f"  ✓ Products: {[f'{p.coefficient} {p.compound_id}' for p in stoich.products]}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
        print()


def test_caching():
    """Test reaction caching."""
    print("=" * 80)
    print("TEST 4: Caching Behavior")
    print("=" * 80)
    print()
    
    enricher = KEGGStoichiometryEnricher()
    
    # First fetch
    import time
    reaction_id = "R00200"
    
    print(f"First fetch of {reaction_id}...")
    start = time.time()
    stoich1 = enricher._fetch_reaction_stoichiometry(reaction_id)
    duration1 = time.time() - start
    print(f"  ✓ Took {duration1:.2f}s")
    print()
    
    # Second fetch (should be cached)
    print(f"Second fetch of {reaction_id} (should be cached)...")
    start = time.time()
    stoich2 = enricher._fetch_reaction_stoichiometry(reaction_id)
    duration2 = time.time() - start
    print(f"  ✓ Took {duration2:.2f}s")
    print()
    
    speedup = duration1 / duration2 if duration2 > 0 else float('inf')
    print(f"Speedup: {speedup:.1f}x faster")
    print()


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Test KEGG stoichiometry enrichment"
    )
    parser.add_argument(
        '--pathway',
        default='hsa00010',
        help='KEGG pathway ID to test (default: hsa00010)'
    )
    parser.add_argument(
        '--test',
        choices=['basic', 'validation', 'parsing', 'caching', 'all'],
        default='all',
        help='Which test to run (default: all)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "KEGG STOICHIOMETRY ENRICHMENT TESTS" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    try:
        if args.test in ('basic', 'all'):
            test_basic_enrichment(args.pathway)
        
        if args.test in ('validation', 'all'):
            test_validation()
        
        if args.test in ('parsing', 'all'):
            test_reaction_parsing()
        
        if args.test in ('caching', 'all'):
            test_caching()
        
        print("=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print()
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
