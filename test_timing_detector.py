#!/usr/bin/env python3
"""Test the timing conflict detector on test.shy model."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.viability.pattern_recognition import PatternRecognitionEngine, PatternType
from shypn.viability.knowledge import ModelKnowledgeBase

def test_timing_detector():
    """Test timing conflict detection on test.shy."""
    
    print("=" * 80)
    print("TIMING CONFLICT DETECTOR TEST")
    print("=" * 80)
    print()
    
    # Load the test model
    model_path = "workspace/projects/Interactive/models/test.shy"
    print(f"Loading model: {model_path}")
    
    try:
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        print(f"✓ Model file loaded")
        print(f"  Places: {len(model_data['places'])}")
        print(f"  Transitions: {len(model_data['transitions'])}")
        print(f"  Arcs: {len(model_data['arcs'])}")
        print()
    except Exception as e:
        print(f"✗ Failed to load model file: {e}")
        return
    
    # Create knowledge base and populate it
    kb = ModelKnowledgeBase()
    
    # Debug: Let me see the first transition
    if model_data['transitions']:
        print("First transition in model data:")
        import pprint
        pprint.pprint(model_data['transitions'][0])
        print()
    
    # Debug: Let me see the arcs
    if model_data['arcs']:
        print("First 3 arcs in model data:")
        for i, arc in enumerate(model_data['arcs'][:3]):
            print(f"Arc {i}:")
            pprint.pprint(arc)
        print()
    
    try:
        kb.update_topology_structural(
            model_data['places'],
            model_data['transitions'],
            model_data['arcs']
        )
        print(f"✓ Knowledge base populated")
        print(f"  Places: {len(kb.places)}")
        print(f"  Transitions: {len(kb.transitions)}")
        print(f"  Arcs: {len(kb.arcs)}")
        
        # Debug: Let's see what's in the KB
        print()
        print("Transitions in KB:")
        for tid, trans in kb.transitions.items():
            print(f"  {tid}: type={trans.transition_type}, label={trans.label}")
        print()
    except Exception as e:
        print(f"✗ Failed to populate knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create pattern recognition engine
    print("Creating pattern recognition engine...")
    engine = PatternRecognitionEngine(kb)
    print("✓ Engine created")
    print()
    
    # Run analysis
    print("Running viability analysis...")
    try:
        result = engine.analyze()
        print(f"✓ Analysis complete")
        print()
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Continuing anyway to see what was detected...")
        return
    
    # Look for timing conflicts
    timing_conflicts = [
        p for p in result['patterns'] 
        if p.pattern_type == PatternType.TIMING_CONFLICT
    ]
    
    print("=" * 80)
    print(f"TIMING CONFLICTS DETECTED: {len(timing_conflicts)}")
    print("=" * 80)
    print()
    
    if not timing_conflicts:
        print("⚠ No timing conflicts detected!")
        print()
        print("All detected patterns:")
        for p in result['patterns']:
            print(f"  - {p.pattern_type.value}: {p.description}")
        return
    
    # Display timing conflict details
    for i, pattern in enumerate(timing_conflicts, 1):
        print(f"Conflict {i}:")
        print(f"  Type: {pattern.pattern_type.value}")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print()
        
        print("  Evidence:")
        ev = pattern.evidence
        for key, value in ev.items():
            if isinstance(value, list):
                print(f"    {key}: {', '.join(str(v) for v in value)}")
            else:
                print(f"    {key}: {value}")
        print()
        
        print("  Affected elements:")
        for elem in pattern.affected_elements:
            print(f"    - {elem}")
        print()
    
    # Get repair suggestions
    print("=" * 80)
    print("REPAIR SUGGESTIONS")
    print("=" * 80)
    print()
    
    # Since suggestions is a flat list, we need to correlate them with patterns
    # For timing conflicts, we'll just show all suggestions
    suggestions = result['suggestions']
    
    if not suggestions:
        print("  ⚠ No suggestions generated!")
    else:
        for j, sug in enumerate(suggestions, 1):
            print(f"  Suggestion {j} (confidence: {sug.confidence:.2f}):")
            print(f"    Action: {sug.action}")
            print(f"    Target: {sug.target}")
            print(f"    Description: {sug.description}")
            print(f"    Rationale: {sug.rationale}")
            print(f"    Data source: {sug.data_source}")
            print()
            print(f"    Parameters:")
            for key, value in sug.parameters.items():
                print(f"      {key}: {value}")
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✓ Timing conflict detector successfully identified {len(timing_conflicts)} conflict(s)")
    print(f"✓ Generated {len(suggestions)} repair suggestion(s)")
    print()
    
    if suggestions:
        top_suggestion = suggestions[0]
        print("Top recommendation:")
        print(f"  → {top_suggestion.description}")
        print(f"    (confidence: {top_suggestion.confidence:.2f})")
        print()

if __name__ == '__main__':
    test_timing_detector()
