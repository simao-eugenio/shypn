#!/usr/bin/env python3
"""
Test Stoichiometry-Based Heuristics

Demonstrates how network structure (stoichiometry) improves parameter inference.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine


def test_stoichiometry_heuristics():
    """Test parameter inference with stoichiometry."""
    
    print("=" * 80)
    print("STOICHIOMETRY-BASED HEURISTICS TEST")
    print("=" * 80)
    
    engine = HeuristicInferenceEngine(use_background_fetch=False)
    
    print("\n" + "=" * 80)
    print("TEST 1: Simple Reaction (1:1 stoichiometry)")
    print("=" * 80)
    print("Structure: A →(1) T →(1) B")
    print("Expected: Baseline parameters")
    
    # Mock transition with simple 1:1 stoichiometry
    class MockArc:
        def __init__(self, weight, marking=0):
            self.weight = weight
            self.marking = marking
            self.source = type('obj', (object,), {'initial_marking': marking})
            self.target = type('obj', (object,), {'initial_marking': marking})
    
    class SimpleTransition:
        id = "T1"
        label = "simple reaction"
        transition_type = "continuous"
        input_arcs = [MockArc(weight=1, marking=10)]
        output_arcs = [MockArc(weight=1, marking=0)]
    
    result1 = engine.infer_parameters(SimpleTransition())
    params1 = result1.parameters
    
    print(f"\nResult:")
    print(f"  Source: {params1.source}")
    print(f"  Vmax: {params1.vmax:.2f}")
    print(f"  Km: {params1.km:.2f}")
    print(f"  Confidence: {params1.confidence_score * 100:.0f}%")
    print(f"  Notes: {params1.notes}")
    
    # Test 2: Multi-substrate reaction
    print("\n" + "=" * 80)
    print("TEST 2: Multi-Substrate Reaction (2:1 stoichiometry)")
    print("=" * 80)
    print("Structure: A →(1) T →(1) C")
    print("           B →(1) ↗")
    print("Expected: Lower Vmax (complex reaction), adjusted Km")
    
    class MultiSubstrateTransition:
        id = "T2"
        label = "complex reaction"
        transition_type = "continuous"
        input_arcs = [
            MockArc(weight=1, marking=10),
            MockArc(weight=1, marking=15)
        ]
        output_arcs = [MockArc(weight=1, marking=0)]
    
    result2 = engine.infer_parameters(MultiSubstrateTransition())
    params2 = result2.parameters
    
    print(f"\nResult:")
    print(f"  Source: {params2.source}")
    print(f"  Vmax: {params2.vmax:.2f} (vs {params1.vmax:.2f} baseline)")
    print(f"  Km: {params2.km:.2f} (vs {params1.km:.2f} baseline)")
    print(f"  Confidence: {params2.confidence_score * 100:.0f}%")
    print(f"  Notes: {params2.notes}")
    print(f"\n  Analysis:")
    print(f"    Vmax reduction: {(1 - params2.vmax/params1.vmax) * 100:.1f}% (expected ~30% for complex)")
    
    # Test 3: High stoichiometry
    print("\n" + "=" * 80)
    print("TEST 3: High Stoichiometry (3A → B)")
    print("=" * 80)
    print("Structure: A →(3) T →(1) B")
    print("Expected: Higher Km (need more substrate)")
    
    class HighStoichTransition:
        id = "T3"
        label = "polymerization"
        transition_type = "continuous"
        input_arcs = [MockArc(weight=3, marking=20)]
        output_arcs = [MockArc(weight=1, marking=0)]
    
    result3 = engine.infer_parameters(HighStoichTransition())
    params3 = result3.parameters
    
    print(f"\nResult:")
    print(f"  Source: {params3.source}")
    print(f"  Vmax: {params3.vmax:.2f}")
    print(f"  Km: {params3.km:.2f} (vs {params1.km:.2f} baseline)")
    print(f"  Confidence: {params3.confidence_score * 100:.0f}%")
    print(f"  Notes: {params3.notes}")
    print(f"\n  Analysis:")
    print(f"    Km increase: {(params3.km/params1.km):.1f}× (scaled by stoichiometry)")
    
    # Test 4: High locality (abundant substrates)
    print("\n" + "=" * 80)
    print("TEST 4: High Locality (Abundant Substrates)")
    print("=" * 80)
    print("Structure: A(100) →(1) T →(1) B")
    print("Expected: Higher Vmax (fast with abundant substrate)")
    
    class HighLocalityTransition:
        id = "T4"
        label = "fast reaction"
        transition_type = "continuous"
        input_arcs = [MockArc(weight=1, marking=100)]
        output_arcs = [MockArc(weight=1, marking=0)]
    
    result4 = engine.infer_parameters(HighLocalityTransition())
    params4 = result4.parameters
    
    print(f"\nResult:")
    print(f"  Source: {params4.source}")
    print(f"  Vmax: {params4.vmax:.2f} (vs {params1.vmax:.2f} baseline)")
    print(f"  Km: {params4.km:.2f}")
    print(f"  Confidence: {params4.confidence_score * 100:.0f}%")
    print(f"  Notes: {params4.notes}")
    print(f"\n  Analysis:")
    print(f"    Vmax boost: {(params4.vmax/params1.vmax - 1) * 100:.1f}% (abundant substrates)")
    
    # Test 5: Low locality (scarce substrates)
    print("\n" + "=" * 80)
    print("TEST 5: Low Locality (Scarce Substrates)")
    print("=" * 80)
    print("Structure: A(0) →(1) T →(1) B")
    print("Expected: Lower Vmax (slow with scarce substrate)")
    
    class LowLocalityTransition:
        id = "T5"
        label = "slow reaction"
        transition_type = "continuous"
        input_arcs = [MockArc(weight=1, marking=0)]
        output_arcs = [MockArc(weight=1, marking=0)]
    
    result5 = engine.infer_parameters(LowLocalityTransition())
    params5 = result5.parameters
    
    print(f"\nResult:")
    print(f"  Source: {params5.source}")
    print(f"  Vmax: {params5.vmax:.2f} (vs {params1.vmax:.2f} baseline)")
    print(f"  Km: {params5.km:.2f}")
    print(f"  Confidence: {params5.confidence_score * 100:.0f}%")
    print(f"  Notes: {params5.notes}")
    print(f"\n  Analysis:")
    print(f"    Vmax reduction: {(1 - params5.vmax/params1.vmax) * 100:.1f}% (scarce substrates)")
    
    # Test 6: Stochastic with multi-substrate
    print("\n" + "=" * 80)
    print("TEST 6: Stochastic Multi-Substrate")
    print("=" * 80)
    print("Structure: A + B →(1,1) T →(1) C  (stochastic)")
    print("Expected: Lower rate (harder to get all molecules together)")
    
    class StochasticMultiTransition:
        id = "T6"
        label = "binding reaction"
        transition_type = "stochastic"
        input_arcs = [
            MockArc(weight=1, marking=5),
            MockArc(weight=1, marking=5)
        ]
        output_arcs = [MockArc(weight=1, marking=0)]
    
    # First get baseline stochastic
    class SimpleStochasticTransition:
        id = "T6_baseline"
        label = "simple binding"
        transition_type = "stochastic"
        input_arcs = [MockArc(weight=1, marking=5)]
        output_arcs = [MockArc(weight=1, marking=0)]
    
    result6_base = engine.infer_parameters(SimpleStochasticTransition())
    result6 = engine.infer_parameters(StochasticMultiTransition())
    params6_base = result6_base.parameters
    params6 = result6.parameters
    
    print(f"\nResult:")
    print(f"  Source: {params6.source}")
    print(f"  Lambda: {params6.lambda_param:.4f} (vs {params6_base.lambda_param:.4f} baseline)")
    print(f"  Confidence: {params6.confidence_score * 100:.0f}%")
    print(f"  Notes: {params6.notes}")
    print(f"\n  Analysis:")
    print(f"    Rate reduction: {(1 - params6.lambda_param/params6_base.lambda_param) * 100:.1f}%")
    print(f"    (2 substrates = 0.5× rate)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY: Stoichiometry-Based Adjustments")
    print("=" * 80)
    
    print("\n📊 Continuous Parameters:")
    print(f"  • Multi-substrate (2) → Vmax ×0.7 (complex)")
    print(f"  • High stoichiometry (3:1) → Km ×1.5 (need more)")
    print(f"  • High locality (100 tokens) → Vmax ×1.3 (abundant)")
    print(f"  • Low locality (0 tokens) → Vmax ×0.7 (scarce)")
    print(f"  • Balanced reactions → +10% confidence")
    
    print("\n📊 Stochastic Parameters:")
    print(f"  • Multi-substrate → Rate ×0.5 per substrate")
    print(f"  • High stoichiometry → Rate ÷ weight")
    print(f"  • High locality → Rate ×1.5")
    print(f"  • Low locality → Rate ×0.5")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    
    print("\n✨ Network Structure Matters:")
    print("  • Stoichiometry reflects biological complexity")
    print("  • Token distribution shows substrate availability")
    print("  • Multi-substrate reactions are naturally slower")
    print("  • High concentrations enable faster kinetics")
    
    print("\n✨ Automatic Adjustments:")
    print("  • No manual tuning needed")
    print("  • Parameters adapt to model structure")
    print("  • Locality balance considered")
    print("  • Overall balance respected")
    
    print("\n✨ Benefits:")
    print("  • More realistic defaults")
    print("  • Context-aware inference")
    print("  • Better starting points for simulation")
    print("  • Respects Petri net semantics")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_stoichiometry_heuristics()
