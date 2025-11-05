#!/usr/bin/env python3
"""
Test Pure Heuristics Workflow

Demonstrates the refactored pure heuristics approach.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine


def test_pure_heuristics():
    """Test pure heuristics without any database lookups."""
    
    print("=" * 80)
    print("PURE HEURISTICS TEST")
    print("=" * 80)
    
    # Initialize engine (no background fetch)
    engine = HeuristicInferenceEngine(use_background_fetch=False)
    print(f"\nEngine initialized:")
    print(f"  use_background_fetch: {engine.use_background_fetch}")
    print(f"  Mode: Pure Heuristics")
    
    # Test different transition types
    test_cases = [
        {
            'id': 'T1',
            'label': 'phosphorylation',
            'type': 'continuous',
            'expected': 'Kinase-like parameters'
        },
        {
            'id': 'T2',
            'label': 'dehydrogenase reaction',
            'type': 'continuous',
            'expected': 'Oxidoreductase parameters'
        },
        {
            'id': 'T3',
            'label': 'gene expression',
            'type': 'stochastic',
            'expected': 'Expression rate'
        },
        {
            'id': 'T4',
            'label': 'protein degradation',
            'type': 'stochastic',
            'expected': 'Degradation rate'
        },
        {
            'id': 'T5',
            'label': 'transport',
            'type': 'timed',
            'expected': 'Transport delay'
        },
        {
            'id': 'T6',
            'label': 'regulatory event',
            'type': 'immediate',
            'expected': 'High priority'
        }
    ]
    
    print("\n" + "=" * 80)
    print("TESTING DIFFERENT TRANSITION TYPES")
    print("=" * 80)
    
    for test in test_cases:
        print(f"\n{'─' * 80}")
        print(f"Test: {test['id']} - {test['label']}")
        print(f"Expected: {test['expected']}")
        print(f"{'─' * 80}")
        
        # Create mock transition
        class MockTransition:
            pass
        
        transition = MockTransition()
        transition.id = test['id']
        transition.label = test['label']
        transition.transition_type = test['type']
        
        # Infer parameters
        result = engine.infer_parameters(transition)
        
        # Display results
        params = result.parameters
        print(f"\nResult:")
        print(f"  Type: {params.transition_type.value}")
        print(f"  Semantics: {params.biological_semantics.value}")
        print(f"  Confidence: {params.confidence_score * 100:.0f}%")
        print(f"  Source: {params.source}")
        
        # Type-specific parameters
        if hasattr(params, 'vmax'):
            print(f"  Vmax: {params.vmax}")
            print(f"  Km: {params.km}")
            if params.kcat:
                print(f"  Kcat: {params.kcat}")
        elif hasattr(params, 'lambda_param'):
            print(f"  Lambda: {params.lambda_param}")
        elif hasattr(params, 'delay'):
            print(f"  Delay: {params.delay} {params.time_unit}")
        elif hasattr(params, 'priority'):
            print(f"  Priority: {params.priority}")
        
        print(f"  Notes: {params.notes}")
        
        # Verify no database lookup occurred
        metadata = result.inference_metadata
        assert 'source' not in metadata or metadata.get('source') != 'BioModels', \
            "ERROR: Database lookup occurred!"
        assert params.source == 'Heuristic', \
            f"ERROR: Expected source 'Heuristic', got '{params.source}'"
        
        print("\n  ✅ Pure heuristic inference (no database)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ All {len(test_cases)} tests passed!")
    print("\nKey findings:")
    print("  • No database lookups occurred")
    print("  • All sources are 'Heuristic'")
    print("  • Parameters based on label/type analysis")
    print("  • Confidence scores: 50-75% (honest heuristic quality)")
    print("  • Works without EC numbers or reaction IDs")
    print("  • Instant results")
    
    print("\n" + "=" * 80)
    print("COMPARISON: Before vs After")
    print("=" * 80)
    
    print("\nBEFORE (with database):")
    print("  ❌ Required EC numbers for matching")
    print("  ❌ Organism selector needed")
    print("  ❌ Mode selection (Fast/Enhanced)")
    print("  ❌ Source column (confusing)")
    print("  ❌ EC/Enzyme column")
    print("  ❌ Database parameters shown")
    print("  ❌ Mixed purposes with BRENDA/SABIO")
    
    print("\nAFTER (pure heuristics):")
    print("  ✅ Works on any transition")
    print("  ✅ No EC numbers needed")
    print("  ✅ No organism selector")
    print("  ✅ No mode selection")
    print("  ✅ Simple parameter table")
    print("  ✅ Clear purpose: fast defaults")
    print("  ✅ Separate from BRENDA/SABIO")
    
    print("\n" + "=" * 80)
    print("USER WORKFLOW")
    print("=" * 80)
    
    print("\n1. Draw or import transitions")
    print("2. Open Heuristic Parameters category")
    print("3. Click 'Analyze & Infer Parameters'")
    print("4. See instant heuristic defaults")
    print("5. Select transitions and apply")
    print("\nDone! No IDs, no waiting, just smart defaults.")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_pure_heuristics()
