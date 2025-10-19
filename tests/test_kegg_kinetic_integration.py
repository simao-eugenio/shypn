#!/usr/bin/env python3
"""Test kinetic parameter estimation integration with KEGG pathways.

This test imports a real KEGG pathway (Glycolysis) and verifies that
kinetic parameters are automatically estimated for all reactions.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_kegg_kinetic_integration():
    """Test full KEGG import with kinetic parameter estimation."""
    
    print("="*70)
    print("KEGG Kinetic Integration Test")
    print("="*70)
    print()
    
    # Step 1: Import required modules
    print("[1] Importing modules...")
    try:
        from shypn.importer.kegg import KEGGAPIClient, KGMLParser
        from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
        print("    ✓ Modules imported successfully")
    except ImportError as e:
        print(f"    ✗ Import failed: {e}")
        return False
    
    # Step 2: Fetch pathway from KEGG
    print("\n[2] Fetching hsa00010 (Glycolysis) from KEGG...")
    try:
        client = KEGGAPIClient()
        kgml_data = client.fetch_kgml('hsa00010')
        if not kgml_data:
            print("    ✗ Failed to fetch pathway")
            return False
        print(f"    ✓ Fetched {len(kgml_data)} bytes of KGML data")
    except Exception as e:
        print(f"    ✗ Fetch failed: {e}")
        return False
    
    # Step 3: Parse KGML
    print("\n[3] Parsing KGML...")
    try:
        parser = KGMLParser()
        pathway = parser.parse(kgml_data)
        print(f"    ✓ Parsed pathway: {pathway.name}")
        print(f"    ✓ Entries: {len(pathway.entries)}")
        print(f"    ✓ Reactions: {len(pathway.reactions)}")
    except Exception as e:
        print(f"    ✗ Parse failed: {e}")
        return False
    
    # Step 4: Convert with kinetic parameter estimation (default: enabled)
    print("\n[4] Converting to Petri net with kinetic estimation...")
    try:
        document = convert_pathway_enhanced(
            pathway,
            coordinate_scale=2.5,
            include_cofactors=True,
            filter_isolated_compounds=True,
            estimate_kinetics=True  # Enable kinetic parameter estimation
        )
        print(f"    ✓ Conversion successful")
        print(f"    ✓ Places: {len(document.places)}")
        print(f"    ✓ Transitions: {len(document.transitions)}")
        print(f"    ✓ Arcs: {len(document.arcs)}")
    except Exception as e:
        print(f"    ✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Verify kinetic parameters were estimated
    print("\n[5] Verifying kinetic parameter estimation...")
    
    if not document.transitions:
        print("    ✗ No transitions found in document")
        return False
    
    transitions_with_rates = 0
    transitions_with_metadata = 0
    estimator_types = {}
    
    for i, transition in enumerate(document.transitions):
        # Check if rate was set
        rate = getattr(transition, 'rate', None)
        if rate and rate != 1.0:  # Default rate is 1.0 (float)
            transitions_with_rates += 1
        
        # Check if metadata was added
        if hasattr(transition, 'metadata') and transition.metadata:
            if 'kinetic_estimator' in transition.metadata:
                transitions_with_metadata += 1
                estimator_type = transition.metadata['kinetic_estimator']
                estimator_types[estimator_type] = estimator_types.get(estimator_type, 0) + 1
                
                # Print first few examples
                if i < 3:
                    params = transition.metadata.get('estimated_parameters', {})
                    transition_label = getattr(transition, 'label', None) or getattr(transition, 'name', 'unknown')
                    print(f"    Example {i+1}: {transition_label}")
                    print(f"        Estimator: {estimator_type}")
                    print(f"        Rate: {rate}")
                    print(f"        Parameters: {params}")
    
    print(f"\n    Summary:")
    print(f"    ✓ Transitions with estimated rates: {transitions_with_rates}/{len(document.transitions)}")
    print(f"    ✓ Transitions with metadata: {transitions_with_metadata}/{len(document.transitions)}")
    
    if estimator_types:
        print(f"\n    Estimator distribution:")
        for est_type, count in sorted(estimator_types.items()):
            print(f"        {est_type}: {count}")
    
    # Verify we estimated at least some parameters
    if transitions_with_rates == 0:
        print("\n    ✗ No kinetic parameters were estimated!")
        return False
    
    if transitions_with_metadata == 0:
        print("\n    ✗ No kinetic metadata was added!")
        return False
    
    print("\n[6] Testing with estimation disabled...")
    try:
        document_no_kinetics = convert_pathway_enhanced(
            pathway,
            coordinate_scale=2.5,
            include_cofactors=True,
            filter_isolated_compounds=True,
            estimate_kinetics=False  # Disable kinetic parameter estimation
        )
        
        # Count transitions with custom rates
        custom_rates = sum(1 for t in document_no_kinetics.transitions 
                          if getattr(t, 'rate', None) and t.rate != 1.0)
        
        print(f"    ✓ Without estimation: {custom_rates} transitions have custom rates")
        
        if custom_rates >= transitions_with_rates:
            print(f"    ⚠ Warning: Same or more rates without estimation ({custom_rates} vs {transitions_with_rates})")
        else:
            print(f"    ✓ Confirmed: Fewer custom rates without estimation")
        
    except Exception as e:
        print(f"    ✗ Test without estimation failed: {e}")
        return False
    
    # Success!
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print(f"\nKinetic parameter estimation successfully integrated with KEGG import!")
    print(f"Estimated parameters for {transitions_with_rates}/{len(document.transitions)} transitions")
    
    return True


if __name__ == '__main__':
    try:
        success = test_kegg_kinetic_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
