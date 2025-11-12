#!/usr/bin/env python3
"""Test script for pattern recognition engine.

Tests all pattern detectors and repair suggesters with mock data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.viability.knowledge.data_structures import (
    PlaceKnowledge,
    TransitionKnowledge,
    ArcKnowledge
)
from shypn.viability.knowledge.knowledge_base import ModelKnowledgeBase
from shypn.viability.pattern_recognition import (
    PatternRecognitionEngine,
    StructuralPatternDetector,
    KineticPatternDetector,
    PatternType
)


def create_test_kb():
    """Create a test knowledge base with known patterns."""
    kb = ModelKnowledgeBase()
    
    # Create places
    # P1: Dead end (has input, no output, tokens accumulate)
    kb.places['P1'] = PlaceKnowledge(
        place_id='P1',
        current_marking=10,
        avg_tokens=10.0,
        compound_name='Glucose',
        compound_id='C00031'
    )
    
    # P2: Normal place
    kb.places['P2'] = PlaceKnowledge(
        place_id='P2',
        current_marking=5,
        avg_tokens=5.0,
        compound_name='ATP',
        compound_id='C00002'
    )
    
    # P3: Bottleneck (high accumulation)
    kb.places['P3'] = PlaceKnowledge(
        place_id='P3',
        current_marking=50,
        avg_tokens=45.0,
        compound_name='Pyruvate',
        compound_id='C00022'
    )
    
    # P4: Output of bottleneck
    kb.places['P4'] = PlaceKnowledge(
        place_id='P4',
        current_marking=2,
        avg_tokens=2.0,
        compound_name='Acetyl-CoA',
        compound_id='C00024'
    )
    
    # Create transitions
    # T1: Source with no rate (should be detected)
    kb.transitions['T1'] = TransitionKnowledge(
        transition_id='T1',
        firing_count=0,
        current_rate=None,
        kinetic_law=None,
        ec_number='2.7.1.1',  # Has EC but no kinetic law
        reaction_name='Hexokinase'
    )
    
    # T2: Normal transition with kinetic law
    kb.transitions['T2'] = TransitionKnowledge(
        transition_id='T2',
        firing_count=100,
        current_rate=None,
        kinetic_law='michaelis_menten(P2, vmax=10, km=5)',
        reaction_name='Phosphofructokinase'
    )
    
    # T3: Transition that fires frequently
    kb.transitions['T3'] = TransitionKnowledge(
        transition_id='T3',
        firing_count=1000,
        current_rate=None,
        kinetic_law='michaelis_menten(P3, vmax=100, km=10)',
        reaction_name='Pyruvate dehydrogenase upstream'
    )
    
    # T4: Downstream transition that fires slowly (causes bottleneck)
    kb.transitions['T4'] = TransitionKnowledge(
        transition_id='T4',
        firing_count=10,
        current_rate=None,
        kinetic_law='michaelis_menten(P3, vmax=1, km=5)',
        reaction_name='Pyruvate dehydrogenase downstream'
    )
    
    # T5: Enzymatic reaction with no kinetic law (constant rate)
    kb.transitions['T5'] = TransitionKnowledge(
        transition_id='T5',
        firing_count=0,
        current_rate=1.0,
        kinetic_law=None,
        ec_number='1.1.1.1',
        reaction_name='Alcohol dehydrogenase'
    )
    
    # Create arcs
    # T1 → P1 (source feeds dead end)
    kb.arcs['A1'] = ArcKnowledge(
        arc_id='A1',
        source_id='T1',
        target_id='P1',
        arc_type='transition_to_place',
        current_weight=1
    )
    
    # P2 → T2 (normal flow)
    kb.arcs['A2'] = ArcKnowledge(
        arc_id='A2',
        source_id='P2',
        target_id='T2',
        arc_type='place_to_transition',
        current_weight=1
    )
    
    # T2 → P3 (feeds bottleneck)
    kb.arcs['A3'] = ArcKnowledge(
        arc_id='A3',
        source_id='T2',
        target_id='P3',
        arc_type='transition_to_place',
        current_weight=1
    )
    
    # Bottleneck pathway: T3 → P3 → T4 → P4
    kb.arcs['A4'] = ArcKnowledge(
        arc_id='A4',
        source_id='P3',
        target_id='T3',
        arc_type='place_to_transition',
        current_weight=1
    )
    
    kb.arcs['A5'] = ArcKnowledge(
        arc_id='A5',
        source_id='T3',
        target_id='P3',
        arc_type='transition_to_place',
        current_weight=2  # Produces 2 tokens
    )
    
    kb.arcs['A6'] = ArcKnowledge(
        arc_id='A6',
        source_id='P3',
        target_id='T4',
        arc_type='place_to_transition',
        current_weight=5  # HIGH requirement
    )
    
    kb.arcs['A7'] = ArcKnowledge(
        arc_id='A7',
        source_id='T4',
        target_id='P4',
        arc_type='transition_to_place',
        current_weight=1
    )
    
    # T5 has input (not a source)
    kb.arcs['A8'] = ArcKnowledge(
        arc_id='A8',
        source_id='P4',
        target_id='T5',
        arc_type='place_to_transition',
        current_weight=1
    )
    
    return kb


def test_structural_patterns():
    """Test structural pattern detection."""
    print("\n" + "="*80)
    print("TESTING STRUCTURAL PATTERN DETECTION")
    print("="*80)
    
    kb = create_test_kb()
    detector = StructuralPatternDetector()
    
    # Test dead-end detection
    print("\n--- Dead End Detection ---")
    patterns = detector.detect_dead_ends(kb)
    print(f"Found {len(patterns)} dead-end patterns:")
    for pattern in patterns:
        print(f"  ✓ {pattern}")
        print(f"    Evidence: {pattern.evidence}")
    
    # Test bottleneck detection
    print("\n--- Bottleneck Detection ---")
    patterns = detector.detect_bottlenecks(kb)
    print(f"Found {len(patterns)} bottleneck patterns:")
    for pattern in patterns:
        print(f"  ✓ {pattern}")
        print(f"    Evidence: {pattern.evidence}")
    
    # Test unused path detection
    print("\n--- Unused Path Detection ---")
    patterns = detector.detect_unused_paths(kb)
    print(f"Found {len(patterns)} unused path patterns:")
    for pattern in patterns:
        print(f"  ✓ {pattern}")
        print(f"    Evidence: {pattern.evidence}")


def test_kinetic_patterns():
    """Test kinetic pattern detection."""
    print("\n" + "="*80)
    print("TESTING KINETIC PATTERN DETECTION")
    print("="*80)
    
    kb = create_test_kb()
    detector = KineticPatternDetector()
    
    # Test rate too low
    print("\n--- Rate Too Low Detection ---")
    patterns = detector.detect_rate_too_low(kb)
    print(f"Found {len(patterns)} rate-too-low patterns:")
    for pattern in patterns:
        print(f"  ✓ {pattern}")
        print(f"    Evidence: {pattern.evidence}")
    
    # Test missing substrate dependence
    print("\n--- Missing Substrate Dependence ---")
    patterns = detector.detect_missing_substrate_dependence(kb)
    print(f"Found {len(patterns)} missing kinetic law patterns:")
    for pattern in patterns:
        print(f"  ✓ {pattern}")
        print(f"    Evidence: {pattern.evidence}")
    
    # Test pathway imbalance
    print("\n--- Pathway Imbalance Detection ---")
    patterns = detector.detect_pathway_imbalance(kb)
    print(f"Found {len(patterns)} pathway imbalance patterns:")
    for pattern in patterns:
        print(f"  ✓ {pattern}")
        print(f"    Evidence: {pattern.evidence}")


def test_complete_engine():
    """Test the complete pattern recognition engine."""
    print("\n" + "="*80)
    print("TESTING COMPLETE PATTERN RECOGNITION ENGINE")
    print("="*80)
    
    kb = create_test_kb()
    engine = PatternRecognitionEngine(kb)
    
    # Run complete analysis
    print("\nRunning complete analysis...")
    analysis = engine.analyze()
    
    patterns = analysis.get('patterns', [])
    suggestions = analysis.get('suggestions', [])
    
    print(f"\n✓ Detected {len(patterns)} patterns:")
    pattern_counts = {}
    for pattern in patterns:
        pattern_type = pattern.pattern_type.value
        pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
    
    for ptype, count in pattern_counts.items():
        print(f"  - {ptype}: {count}")
    
    print(f"\n✓ Generated {len(suggestions)} repair suggestions:")
    action_counts = {}
    for sugg in suggestions:
        action_counts[sugg.action] = action_counts.get(sugg.action, 0) + 1
    
    for action, count in action_counts.items():
        print(f"  - {action}: {count}")
    
    # Show detailed suggestions
    print("\n--- Detailed Repair Suggestions ---")
    for i, sugg in enumerate(suggestions, 1):
        print(f"\n{i}. {sugg.description}")
        print(f"   Action: {sugg.action}")
        print(f"   Target: {sugg.target}")
        print(f"   Confidence: {sugg.confidence:.2f}")
        print(f"   Rationale: {sugg.rationale}")
        print(f"   Data Source: {sugg.data_source}")
        if sugg.parameters:
            print(f"   Parameters: {sugg.parameters}")


def test_kb_arc_methods():
    """Test the KB arc query methods."""
    print("\n" + "="*80)
    print("TESTING KB ARC QUERY METHODS")
    print("="*80)
    
    kb = create_test_kb()
    
    print("\n--- Testing get_input_arcs_for_place ---")
    for place_id in ['P1', 'P3', 'P4']:
        arcs = kb.get_input_arcs_for_place(place_id)
        print(f"  {place_id}: {len(arcs)} input arcs")
        for arc in arcs:
            print(f"    - {arc.source_id} → {arc.target_id} (weight={arc.current_weight})")
    
    print("\n--- Testing get_output_arcs_for_place ---")
    for place_id in ['P2', 'P3', 'P4']:
        arcs = kb.get_output_arcs_for_place(place_id)
        print(f"  {place_id}: {len(arcs)} output arcs")
        for arc in arcs:
            print(f"    - {arc.source_id} → {arc.target_id} (weight={arc.current_weight})")
    
    print("\n--- Testing get_input_arcs_for_transition ---")
    for trans_id in ['T1', 'T2', 'T4']:
        arcs = kb.get_input_arcs_for_transition(trans_id)
        print(f"  {trans_id}: {len(arcs)} input arcs")
        for arc in arcs:
            print(f"    - {arc.source_id} → {arc.target_id}")
    
    print("\n--- Testing is_source_transition ---")
    for trans_id in ['T1', 'T2', 'T4']:
        is_source = kb.is_source_transition(trans_id)
        print(f"  {trans_id}: is_source={is_source}")


if __name__ == '__main__':
    print("="*80)
    print("PATTERN RECOGNITION ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    try:
        # Test KB methods first
        test_kb_arc_methods()
        
        # Test individual detectors
        test_structural_patterns()
        test_kinetic_patterns()
        
        # Test complete engine
        test_complete_engine()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
