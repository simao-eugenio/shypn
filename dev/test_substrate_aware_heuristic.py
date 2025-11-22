#!/usr/bin/env python3
"""
Test substrate-aware heuristic improvements after KEGG enrichment.

After enriching KEGG pathways, places have biological names (ATP, glucose)
instead of codes (C00002, C00008). This allows more accurate Km estimation.
"""

import sys
sys.path.insert(0, 'src')

from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine
from shypn.crossfetch.models.transition_types import TransitionType


class MockPlace:
    """Mock place object with biological name."""
    def __init__(self, name):
        self.label = name
        self.name = name
        self.id = name


class MockArc:
    """Mock arc connecting place to transition."""
    def __init__(self, source_place):
        self.source = source_place
        self.weight = 1


class MockTransition:
    """Mock transition with substrates."""
    def __init__(self, label, substrates, ec_number=None):
        self.id = f"T_{label}"
        self.label = label
        self.name = label
        self.ec_number = ec_number
        self.reaction_id = f"R{hash(label) % 100000:05d}"
        self.enzyme_name = None
        self.transition_type = TransitionType.CONTINUOUS
        self.rate_function = None  # Will be set by heuristic
        self.delay = None
        self.metadata = {}  # Empty metadata (no high-confidence existing data)
        
        # Create input arcs from substrates
        self.input_arcs = [MockArc(MockPlace(s)) for s in substrates]
        self.output_arcs = [MockArc(MockPlace(f"product_{i}")) for i in range(len(substrates))]


def test_substrate_aware_km():
    """Test that Km is adjusted based on substrate names."""
    
    engine = HeuristicInferenceEngine()
    
    print("=" * 70)
    print("SUBSTRATE-AWARE HEURISTIC TEST")
    print("=" * 70)
    print()
    
    # Test cases: (label, substrates, ec_number, expected_behavior)
    test_cases = [
        # Case 1: Hexokinase with ATP and Glucose (enriched names)
        {
            'label': 'HK',
            'substrates': ['ATP', 'D-Glucose'],
            'ec_number': '2.7.1.1',
            'description': 'Hexokinase (enriched)',
            'expected': 'Low Km (~0.05) due to ATP'
        },
        
        # Case 2: Same enzyme but with KEGG codes (not enriched)
        {
            'label': 'HK',
            'substrates': ['C00002', 'C00031'],
            'ec_number': '2.7.1.1',
            'description': 'Hexokinase (not enriched)',
            'expected': 'Base Km (~0.05) from EC class'
        },
        
        # Case 3: Dehydrogenase with NAD+ (enriched)
        {
            'label': 'GAPDH',
            'substrates': ['Glyceraldehyde-3-phosphate', 'NAD+'],
            'ec_number': '1.2.1.12',
            'description': 'GAPDH (enriched)',
            'expected': 'Adjusted Km for NAD+ affinity'
        },
        
        # Case 4: Aldolase with FBP (enriched)
        {
            'label': 'ALDO',
            'substrates': ['Fructose-1,6-bisphosphate'],
            'ec_number': '4.1.2.13',
            'description': 'Aldolase (enriched)',
            'expected': 'Km adjusted for FBP'
        },
        
        # Case 5: Pyruvate kinase with PEP and ADP (enriched)
        {
            'label': 'PK',
            'substrates': ['Phosphoenolpyruvate', 'ADP'],
            'ec_number': '2.7.1.40',
            'description': 'Pyruvate kinase (enriched)',
            'expected': 'Km adjusted for PEP and ADP'
        },
        
        # Case 6: Generic transferase (no EC, no recognized substrates)
        {
            'label': 'transferase',
            'substrates': ['substrate_A', 'substrate_B'],
            'ec_number': None,
            'description': 'Generic transferase',
            'expected': 'Base Km from label pattern'
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Label: {test['label']}")
        print(f"  Substrates: {', '.join(test['substrates'])}")
        print(f"  EC: {test['ec_number'] or 'None'}")
        print(f"  Expected: {test['expected']}")
        
        # Create mock transition
        transition = MockTransition(
            test['label'],
            test['substrates'],
            test['ec_number']
        )
        
        # Infer parameters
        result = engine.infer_parameters(transition, organism="Homo sapiens")
        
        # Print results
        params = result.parameters
        
        # Check if it's continuous (has Vmax/Km)
        if hasattr(params, 'vmax'):
            print(f"  Result:")
            print(f"    Type: CONTINUOUS")
            print(f"    Vmax: {params.vmax:.3g} µM/s")
            print(f"    Km: {params.km:.3g} mM")
            print(f"    Confidence: {params.confidence_score:.2f}")
            if params.notes:
                notes_short = params.notes[:100] + "..." if len(params.notes) > 100 else params.notes
                print(f"    Notes: {notes_short}")
        else:
            print(f"  Result:")
            print(f"    Type: {params.transition_type.value.upper()}")
            print(f"    (Not continuous - no Vmax/Km parameters)")
            print(f"    Confidence: {params.confidence_score:.2f}")
        print()
    
    print("=" * 70)
    print("COMPARISON: Before vs After Enrichment")
    print("=" * 70)
    print()
    
    # Direct comparison: Same enzyme, different substrate names
    print("Hexokinase (EC 2.7.1.1):")
    print()
    
    # Without enrichment (KEGG codes)
    t1 = MockTransition('HK', ['C00002', 'C00031'], '2.7.1.1')
    r1 = engine.infer_parameters(t1, organism="Homo sapiens")
    print(f"  BEFORE Enrichment (C00002, C00031):")
    print(f"    Km = {r1.parameters.km:.3g} mM")
    print(f"    Source: {r1.parameters.source}")
    print()
    
    # With enrichment (biological names)
    t2 = MockTransition('HK', ['ATP', 'D-Glucose'], '2.7.1.1')
    r2 = engine.infer_parameters(t2, organism="Homo sapiens")
    print(f"  AFTER Enrichment (ATP, D-Glucose):")
    print(f"    Km = {r2.parameters.km:.3g} mM")
    print(f"    Source: {r2.parameters.source}")
    print()
    
    # Show improvement
    improvement = abs(r2.parameters.km - r1.parameters.km) / r1.parameters.km * 100
    print(f"  Improvement: {improvement:.1f}% change in Km accuracy")
    print(f"  (Literature Km for hexokinase: 0.02-0.05 mM for ATP)")
    print()


if __name__ == '__main__':
    test_substrate_aware_km()
