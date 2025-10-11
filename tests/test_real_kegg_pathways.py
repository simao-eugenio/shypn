#!/usr/bin/env python3
"""Test pathway enhancement on real KEGG pathways.

This script fetches real KEGG pathways and tests the complete enhancement
pipeline to validate integration and measure performance.
"""

import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg import fetch_pathway, parse_kgml
from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
from shypn.pathway.options import get_standard_options


def test_pathway(pathway_id: str, description: str):
    """Test a single KEGG pathway.
    
    Args:
        pathway_id: KEGG pathway ID (e.g., 'hsa00010')
        description: Human-readable description
        
    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"Testing: {pathway_id} - {description}")
    print(f"{'='*60}")
    
    try:
        # Fetch pathway
        print("1. Fetching pathway from KEGG...")
        start = time.time()
        kgml = fetch_pathway(pathway_id)
        fetch_time = time.time() - start
        print(f"   Fetched in {fetch_time:.2f}s")
        
        # Parse KGML
        print("2. Parsing KGML...")
        start = time.time()
        pathway = parse_kgml(kgml)
        parse_time = time.time() - start
        print(f"   Parsed in {parse_time:.3f}s")
        print(f"   Found: {len(pathway.entries)} entries, {len(pathway.reactions)} reactions")
        
        # Convert with enhancements
        print("3. Converting with enhancements...")
        options = get_standard_options()
        start = time.time()
        document = convert_pathway_enhanced(pathway, enhancement_options=options)
        convert_time = time.time() - start
        print(f"   Converted in {convert_time:.3f}s")
        print(f"   Result: {len(document.places)} places, "
              f"{len(document.transitions)} transitions, "
              f"{len(document.arcs)} arcs")
        
        # Calculate per-element time
        total_elements = len(document.places) + len(document.transitions)
        per_element = 0.0
        if total_elements > 0:
            per_element = (convert_time / total_elements) * 1000  # ms
            print(f"   Performance: {per_element:.2f}ms per element")
        
        # Verify quality
        print("4. Verifying output quality...")
        
        # Check no disconnected arcs
        disconnected = 0
        all_node_ids = set([p.id for p in document.places] + [t.id for t in document.transitions])
        for arc in document.arcs:
            if arc.source_id not in all_node_ids or arc.target_id not in all_node_ids:
                disconnected += 1
        
        print(f"   Disconnected arcs: {disconnected}")
        
        # Check valid positions
        invalid_positions = 0
        for place in document.places:
            if not (isinstance(place.x, (int, float)) and isinstance(place.y, (int, float))):
                invalid_positions += 1
            elif place.x < 0 or place.y < 0 or place.x > 100000 or place.y > 100000:
                invalid_positions += 1
        
        for transition in document.transitions:
            if not (isinstance(transition.x, (int, float)) and isinstance(transition.y, (int, float))):
                invalid_positions += 1
            elif transition.x < 0 or transition.y < 0 or transition.x > 100000 or transition.y > 100000:
                invalid_positions += 1
        
        print(f"   Invalid positions: {invalid_positions}")
        
        # Overall result
        passed = (disconnected == 0 and invalid_positions == 0)
        if passed:
            print("   ✅ PASSED - Output quality verified")
        else:
            print("   ❌ FAILED - Quality issues detected")
        
        return {
            'pathway_id': pathway_id,
            'description': description,
            'elements': total_elements,
            'places': len(document.places),
            'transitions': len(document.transitions),
            'arcs': len(document.arcs),
            'fetch_time': fetch_time,
            'parse_time': parse_time,
            'convert_time': convert_time,
            'per_element_ms': per_element,
            'disconnected_arcs': disconnected,
            'invalid_positions': invalid_positions,
            'passed': passed,
            'error': None
        }
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'pathway_id': pathway_id,
            'description': description,
            'elements': 0,
            'places': 0,
            'transitions': 0,
            'arcs': 0,
            'fetch_time': 0,
            'parse_time': 0,
            'convert_time': 0,
            'per_element_ms': 0,
            'disconnected_arcs': 0,
            'invalid_positions': 0,
            'passed': False,
            'error': str(e)
        }


def main():
    """Run integration tests on real KEGG pathways."""
    print("="*60)
    print("KEGG Pathway Enhancement Integration Test")
    print("="*60)
    print("Testing enhancement pipeline on real KEGG pathways")
    print("This will fetch pathways from KEGG and measure performance")
    print()
    
    # Test cases: (pathway_id, description, expected_size)
    test_cases = [
        ('hsa04668', 'TNF signaling pathway', 'Small (~30 elements)'),
        ('hsa00010', 'Glycolysis / Gluconeogenesis', 'Medium (~60 elements)'),
        ('hsa04010', 'MAPK signaling pathway', 'Large (~250 elements)'),
    ]
    
    results = []
    
    for pathway_id, description, size_desc in test_cases:
        full_desc = f"{description} - {size_desc}"
        result = test_pathway(pathway_id, full_desc)
        results.append(result)
        time.sleep(0.5)  # Be nice to KEGG servers
    
    # Summary table
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Pathway':<12} {'Description':<30} {'Elems':<7} {'Time(ms)':<10} {'ms/elem':<9} {'Result'}")
    print(f"{'-'*80}")
    
    for r in results:
        status = '✅ PASS' if r['passed'] else ('❌ ERROR' if r['error'] else '❌ FAIL')
        desc = r['description'].split(' - ')[0][:28]  # Truncate description
        time_ms = r['convert_time'] * 1000 if r['convert_time'] > 0 else 0
        
        print(f"{r['pathway_id']:<12} {desc:<30} {r['elements']:<7} "
              f"{time_ms:<10.1f} {r['per_element_ms']:<9.2f} {status}")
    
    print(f"{'-'*80}")
    
    # Statistics
    passed = sum(1 for r in results if r['passed'])
    failed = len(results) - passed
    total_elements = sum(r['elements'] for r in results)
    total_time = sum(r['convert_time'] for r in results)
    
    print(f"\nResults: {passed} passed, {failed} failed out of {len(results)} tests")
    print(f"Total elements processed: {total_elements}")
    print(f"Total processing time: {total_time:.3f}s")
    if total_elements > 0:
        avg_ms_per_element = (total_time / total_elements) * 1000
        print(f"Average: {avg_ms_per_element:.2f}ms per element")
    
    # Performance assessment
    print(f"\n{'='*80}")
    print("PERFORMANCE ASSESSMENT")
    print(f"{'='*80}")
    
    for r in results:
        if r['elements'] == 0:
            continue
            
        ms_per_elem = r['per_element_ms']
        
        # Performance thresholds
        if ms_per_elem < 0.1:
            perf = "⚡ EXCELLENT"
        elif ms_per_elem < 0.5:
            perf = "✅ GOOD"
        elif ms_per_elem < 1.0:
            perf = "⚠️  ACCEPTABLE"
        else:
            perf = "❌ SLOW"
        
        print(f"{r['pathway_id']}: {ms_per_elem:.2f}ms/element - {perf}")
    
    # Final verdict
    print(f"\n{'='*80}")
    if passed == len(results):
        print("✅ ALL TESTS PASSED - Integration validated successfully!")
    else:
        print(f"⚠️  {failed} test(s) failed - Review errors above")
    print(f"{'='*80}\n")
    
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
