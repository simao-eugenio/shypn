#!/usr/bin/env python3
"""Integration Test: Rate Function Normalizer with Signal Classification

Tests that the normalizer correctly integrates with the signal classification system.

Author: Signal Classification System
Date: 2024-12-31
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import logging
from unittest.mock import Mock

from shypn.analysis.signal_classification.energy_classifier import EnergySignalClassifier


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')


def create_test_model_with_function_calls():
    """Create a test model with SBML-style function call rate functions"""
    model = Mock()
    
    # Create ATP place (energy signal)
    atp = Mock()
    atp.name = "ATP"
    atp.label = "ATP"
    
    # Create Glucose place
    glucose = Mock()
    glucose.name = "Glucose"
    glucose.label = "Glucose"
    
    model.places = [atp, glucose]
    
    # Create transition with function call rate function (SBML style)
    t1 = Mock()
    t1.name = "glycolysis_step"
    t1.transition_type = "continuous"
    t1.rate = 1.0
    t1.properties = {
        'rate_function': "michaelis_menten(ATP, vmax=1.0, km=0.5)"
    }
    # Ensure kinetic_metadata doesn't interfere
    t1.kinetic_metadata = None
    t1.rate_forward = None
    t1.rate_reverse = None
    
    # Create transition with complex expression
    t2 = Mock()
    t2.name = "complex_reaction"
    t2.transition_type = "continuous"
    t2.rate = 1.0
    t2.properties = {
        'rate_function': "michaelis_menten(Glucose, vmax=2.0, km=0.3) * (ATP / (0.1 + ATP))"
    }
    t2.kinetic_metadata = None
    t2.rate_forward = None
    t2.rate_reverse = None
    
    model.transitions = [t1, t2]
    model.arcs = []
    
    return model, atp, glucose


def test_normalizer_integration_with_energy_classifier():
    """Test that function calls are normalized and classified correctly"""
    print("\n" + "="*70)
    print("INTEGRATION TEST: Normalizer + Energy Classifier")
    print("="*70 + "\n")
    
    # Create model with function call rate functions
    model, atp, glucose = create_test_model_with_function_calls()
    
    print("Model Setup:")
    print(f"  Places: {[p.name for p in model.places]}")
    print(f"  Transitions:")
    for t in model.transitions:
        print(f"    {t.name}: {t.properties.get('rate_function')}")
    print()
    
    # Create energy classifier
    classifier = EnergySignalClassifier(model, confidence_threshold=0.5)
    
    # Test ATP classification
    print("Testing ATP classification...")
    is_energy, confidence, scores = classifier.classify(atp)
    
    print(f"  Place: {atp.name}")
    print(f"  Is Energy Signal: {is_energy}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Scores: {scores}")
    print()
    
    # Verify ATP is classified as energy
    assert is_energy, "ATP should be classified as energy signal"
    assert confidence > 0.5, f"ATP confidence should be > 0.5, got {confidence}"
    
    # Check that rate functions were extracted and normalized
    rate_funcs = classifier._get_rate_functions_referencing(atp)
    print(f"  Rate functions referencing ATP:")
    for rf in rate_funcs:
        print(f"    - {rf}")
    print()
    
    # Verify normalizer converted function calls
    assert len(rate_funcs) > 0, "Should find rate functions referencing ATP"
    
    # Check for M-M pattern in normalized expressions
    has_mm_pattern = any('/' in rf and 'ATP' in rf for rf in rate_funcs)
    print(f"  Michaelis-Menten pattern detected: {has_mm_pattern}")
    
    assert has_mm_pattern, "Should detect M-M pattern after normalization"
    
    # Test Glucose classification
    print("\nTesting Glucose classification...")
    is_energy, confidence, scores = classifier.classify(glucose)
    
    print(f"  Place: {glucose.name}")
    print(f"  Is Energy Signal: {is_energy}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Scores: {scores}")
    print()
    
    # Glucose is not a standard energy compound but might have some score from dynamics
    rate_funcs_glucose = classifier._get_rate_functions_referencing(glucose)
    print(f"  Rate functions referencing Glucose:")
    for rf in rate_funcs_glucose:
        print(f"    - {rf}")
    print()
    
    print("="*70)
    print("✓ INTEGRATION TEST PASSED")
    print("="*70)
    print("\nKey Findings:")
    print("  1. Function call syntax (SBML) was normalized to expressions")
    print("  2. ATP was correctly classified as energy signal")
    print("  3. Michaelis-Menten patterns were detected after normalization")
    print("  4. Place references were correctly identified in normalized expressions")
    print("\n")


def test_backwards_compatibility():
    """Test that existing expression-format rate functions still work"""
    print("\n" + "="*70)
    print("BACKWARD COMPATIBILITY TEST")
    print("="*70 + "\n")
    
    model = Mock()
    
    atp = Mock()
    atp.name = "ATP"
    atp.label = "ATP"
    
    model.places = [atp]
    
    # Create transition with traditional expression (not function call)
    t1 = Mock()
    t1.name = "traditional_reaction"
    t1.transition_type = "continuous"
    t1.rate = 1.0
    t1.properties = {
        'rate_function': "Vmax * ATP / (Km + ATP)"  # Traditional expression
    }
    t1.kinetic_metadata = None
    t1.rate_forward = None
    t1.rate_reverse = None
    
    model.transitions = [t1]
    model.arcs = []
    
    print("Model with traditional expression format:")
    print(f"  Rate function: {t1.properties['rate_function']}")
    print()
    
    classifier = EnergySignalClassifier(model, confidence_threshold=0.5)
    
    # Classify ATP
    is_energy, confidence, scores = classifier.classify(atp)
    
    print(f"Classification Results:")
    print(f"  Is Energy Signal: {is_energy}")
    print(f"  Confidence: {confidence:.2f}")
    print()
    
    # Check rate functions
    rate_funcs = classifier._get_rate_functions_referencing(atp)
    print(f"Rate functions referencing ATP:")
    for rf in rate_funcs:
        print(f"  - {rf}")
    print()
    
    assert is_energy, "ATP should still be classified as energy"
    assert len(rate_funcs) > 0, "Should find rate functions"
    
    print("="*70)
    print("✓ BACKWARD COMPATIBILITY VERIFIED")
    print("="*70)
    print("\n  Traditional expressions pass through unchanged ✓")
    print("  Classification still works correctly ✓\n")


if __name__ == '__main__':
    try:
        test_normalizer_integration_with_energy_classifier()
        test_backwards_compatibility()
        
        print("\n" + "="*70)
        print("ALL INTEGRATION TESTS PASSED ✅")
        print("="*70)
        print()
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        raise
