#!/usr/bin/env python3
"""Test Rate Function Normalizer.

Tests conversion of function call syntax to biochemical expressions.

Author: Signal Classification System
Date: 2024-12-31
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import logging
from shypn.analysis.signal_classification.rate_normalizer import RateFunctionNormalizer


# Setup logging
logging.basicConfig(level=logging.DEBUG)


def test_michaelis_menten_with_parameters():
    """Test M-M function call with explicit parameters"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "michaelis_menten(ATP, vmax=1.0, km=0.5)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Michaelis-Menten with parameters")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "1.0" in result[0]
    assert "ATP" in result[0]
    assert "0.5" in result[0]
    assert "/" in result[0]  # Division for M-M
    print("  ✓ PASS\n")


def test_michaelis_menten_with_defaults():
    """Test M-M function call without parameters (uses defaults)"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "michaelis_menten(Glucose)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Michaelis-Menten with defaults")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "Vmax" in result[0]  # Default parameter name
    assert "Glucose" in result[0]
    assert "Km" in result[0]  # Default parameter name
    print("  ✓ PASS\n")


def test_hill_function():
    """Test Hill equation function call"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "hill(Ca2+, vmax=2.0, k=1.0, n=4)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Hill equation")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "2.0" in result[0]
    assert "Ca2+" in result[0]
    assert "^4" in result[0]  # Hill coefficient
    print("  ✓ PASS\n")


def test_mass_action_single():
    """Test mass action with single reactant"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "mass_action(A, rate_constant=0.1)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Mass action (single reactant)")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "0.1" in result[0]
    assert "A" in result[0]
    print("  ✓ PASS\n")


def test_mass_action_bimolecular():
    """Test mass action with two reactants"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "mass_action(A, B, rate_constant=0.5)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Mass action (bimolecular)")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "0.5" in result[0]
    assert "A" in result[0]
    assert "B" in result[0]
    assert "*" in result[0]  # Multiplication for mass action
    print("  ✓ PASS\n")


def test_reversible_mass_action():
    """Test reversible mass action"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "reversible_mass_action(A, B, kf=0.1, kr=0.05)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Reversible mass action")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "0.1" in result[0]
    assert "0.05" in result[0]
    assert "A" in result[0]
    assert "B" in result[0]
    assert "-" in result[0]  # Subtraction for reversible
    print("  ✓ PASS\n")


def test_competitive_inhibition():
    """Test competitive inhibition function"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "competitive_inhibition(S, I, vmax=1.0, km=0.5, ki=0.1)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Competitive inhibition")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "1.0" in result[0]
    assert "S" in result[0]
    assert "I" in result[0]
    assert "0.5" in result[0]
    assert "0.1" in result[0]
    print("  ✓ PASS\n")


def test_complex_expression_with_function():
    """Test complex expression with function call embedded"""
    normalizer = RateFunctionNormalizer()
    
    # SBML-style: michaelis_menten function followed by saturation term
    rate_func = "michaelis_menten(S1, vmax=1.0, km=0.5) * (S2 / (0.3 + S2))"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Complex expression with function")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert "S1" in result[0]
    assert "S2" in result[0]
    # Function should be converted, saturation term preserved
    assert "*" in result[0]
    print("  ✓ PASS\n")


def test_pure_expression_passthrough():
    """Test that pure expressions pass through unchanged"""
    normalizer = RateFunctionNormalizer()
    
    rate_func = "Vmax * ATP / (Km + ATP)"
    result = normalizer.normalize(rate_func)
    
    print("TEST: Pure expression (no function calls)")
    print(f"  Input:  {rate_func}")
    print(f"  Output: {result}")
    
    assert len(result) == 1
    assert result[0] == rate_func  # Should be unchanged
    print("  ✓ PASS\n")


def test_numeric_rate():
    """Test that numeric rates return empty list"""
    normalizer = RateFunctionNormalizer()
    
    result_int = normalizer.normalize(5)
    result_float = normalizer.normalize(2.5)
    
    print("TEST: Numeric rates")
    print(f"  Input (int):   5")
    print(f"  Output: {result_int}")
    print(f"  Input (float): 2.5")
    print(f"  Output: {result_float}")
    
    assert len(result_int) == 0
    assert len(result_float) == 0
    print("  ✓ PASS\n")


def test_none_and_empty():
    """Test None and empty string handling"""
    normalizer = RateFunctionNormalizer()
    
    result_none = normalizer.normalize(None)
    result_empty = normalizer.normalize("")
    result_whitespace = normalizer.normalize("   ")
    
    print("TEST: None and empty inputs")
    print(f"  Input (None):       {None}")
    print(f"  Output: {result_none}")
    print(f"  Input (empty):      ''")
    print(f"  Output: {result_empty}")
    print(f"  Input (whitespace): '   '")
    print(f"  Output: {result_whitespace}")
    
    assert len(result_none) == 0
    assert len(result_empty) == 0
    assert len(result_whitespace) == 0
    print("  ✓ PASS\n")


def test_is_function_call():
    """Test function call detection"""
    normalizer = RateFunctionNormalizer()
    
    # Should detect
    assert normalizer.is_function_call("michaelis_menten(S, vmax=1.0, km=0.5)")
    assert normalizer.is_function_call("hill(Ca2+, vmax=2.0, k=1.0, n=4)")
    assert normalizer.is_function_call("mass_action(A, B, rate_constant=0.5)")
    
    # Should not detect
    assert not normalizer.is_function_call("Vmax * S / (Km + S)")
    assert not normalizer.is_function_call("2.5 * ATP * Glucose")
    assert not normalizer.is_function_call(None)
    assert not normalizer.is_function_call(42)
    
    print("TEST: Function call detection")
    print("  ✓ All detections correct\n")


def test_get_function_name():
    """Test function name extraction"""
    normalizer = RateFunctionNormalizer()
    
    assert normalizer.get_function_name("michaelis_menten(S, vmax=1.0, km=0.5)") == "michaelis_menten"
    assert normalizer.get_function_name("hill(Ca2+, vmax=2.0, k=1.0, n=4)") == "hill"
    assert normalizer.get_function_name("mass_action(A, rate_constant=0.1)") == "mass_action"
    assert normalizer.get_function_name("Vmax * S / (Km + S)") is None
    
    print("TEST: Function name extraction")
    print("  ✓ All extractions correct\n")


def run_all_tests():
    """Run all normalizer tests"""
    print("="*70)
    print("RATE FUNCTION NORMALIZER TESTS")
    print("="*70)
    print()
    
    try:
        test_michaelis_menten_with_parameters()
        test_michaelis_menten_with_defaults()
        test_hill_function()
        test_mass_action_single()
        test_mass_action_bimolecular()
        test_reversible_mass_action()
        test_competitive_inhibition()
        test_complex_expression_with_function()
        test_pure_expression_passthrough()
        test_numeric_rate()
        test_none_and_empty()
        test_is_function_call()
        test_get_function_name()
        
        print("="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise


if __name__ == '__main__':
    run_all_tests()
