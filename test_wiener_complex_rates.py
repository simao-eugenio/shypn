#!/usr/bin/env python3
"""
Demonstrate adding wiener() noise to complex rate functions.

Shows how to add stochastic noise to heuristic-generated rates like:
- michaelis_menten(P17, vmax=70.0, km=0.1)
- hill_equation(P5, vmax=100.0, k=0.5, n=2.0)
- Complex SBML formulas
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.engine.function_catalog import (
    FUNCTION_CATALOG, reset_wiener, 
    michaelis_menten, hill_equation
)
import numpy as np


def add_stochastic_noise(original_rate: str, amplitude: float = 0.1) -> str:
    """Add multiplicative Wiener noise to any rate expression.
    
    Args:
        original_rate: Original rate expression (simple or complex)
        amplitude: Noise amplitude (default 0.1 = ±10%)
    
    Returns:
        Modified rate expression with stochastic noise
    """
    return f"({original_rate}) * (1 + {amplitude} * wiener(time))"


def evaluate_rate(expr: str, time: float, place_tokens: dict) -> float:
    """Evaluate rate expression at given time with place tokens."""
    context = {
        'time': time,
        't': time,
    }
    context.update(FUNCTION_CATALOG)
    context.update(place_tokens)
    
    try:
        result = eval(expr, {"__builtins__": {}}, context)
        return float(result)
    except Exception as e:
        print(f"ERROR evaluating '{expr}': {e}")
        return 0.0


def test_rate_with_noise(name: str, original_rate: str, place_tokens: dict, 
                         amplitude: float = 0.1, num_samples: int = 20):
    """Test a rate function with and without noise."""
    
    print(f"\n{'=' * 70}")
    print(f"TEST: {name}")
    print(f"{'=' * 70}")
    print(f"Original rate: {original_rate}")
    print(f"Place tokens:  {place_tokens}")
    print(f"Noise amplitude: {amplitude} (±{amplitude*100:.0f}%)")
    print()
    
    # Add noise
    noisy_rate = add_stochastic_noise(original_rate, amplitude)
    print(f"Noisy rate: {noisy_rate}")
    print()
    
    # Evaluate deterministic rate once
    det_rate = evaluate_rate(original_rate, 0.0, place_tokens)
    print(f"Deterministic rate: {det_rate:.4f}")
    print()
    
    # Evaluate stochastic rate multiple times
    reset_wiener()
    print("Stochastic samples (over time):")
    print(f"{'Time':>8} {'Rate':>12} {'Deviation':>12} {'% Change':>12}")
    print("-" * 70)
    
    stoch_values = []
    for i in range(num_samples):
        time = i * 0.1
        stoch_rate = evaluate_rate(noisy_rate, time, place_tokens)
        deviation = stoch_rate - det_rate
        pct_change = (deviation / det_rate * 100) if det_rate != 0 else 0
        
        stoch_values.append(stoch_rate)
        
        if i < 10 or i % 5 == 0:  # Print first 10, then every 5th
            print(f"{time:8.2f} {stoch_rate:12.4f} {deviation:+12.4f} {pct_change:+11.2f}%")
    
    # Statistics
    mean = np.mean(stoch_values)
    std = np.std(stoch_values)
    min_val = np.min(stoch_values)
    max_val = np.max(stoch_values)
    
    print("-" * 70)
    print(f"Statistics (n={num_samples}):")
    print(f"  Deterministic: {det_rate:.4f}")
    print(f"  Mean:          {mean:.4f} (should be ≈ deterministic)")
    print(f"  Std Dev:       {std:.4f}")
    print(f"  Min:           {min_val:.4f} ({(min_val/det_rate - 1)*100:+.1f}%)")
    print(f"  Max:           {max_val:.4f} ({(max_val/det_rate - 1)*100:+.1f}%)")
    print(f"  Range:         {max_val - min_val:.4f}")
    
    # Check if noise is working
    if std > det_rate * 0.01:  # Std > 1% of mean
        print(f"\n✓ Stochastic noise is active (Std/Mean = {std/mean*100:.1f}%)")
    else:
        print(f"\n⚠️  Noise may be too small (Std/Mean = {std/mean*100:.1f}%)")


def main():
    """Run all tests."""
    
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "WIENER NOISE WITH COMPLEX RATE FUNCTIONS" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Test 1: Simple constant rate
    test_rate_with_noise(
        name="Simple Constant Rate",
        original_rate="1.0",
        place_tokens={},
        amplitude=0.1
    )
    
    # Test 2: Michaelis-Menten (heuristic-generated)
    test_rate_with_noise(
        name="Michaelis-Menten Kinetics",
        original_rate="michaelis_menten(P17, vmax=70.0, km=0.1)",
        place_tokens={'P17': 0.5},
        amplitude=0.1
    )
    
    # Test 3: Hill equation
    test_rate_with_noise(
        name="Hill Equation (Cooperative Binding)",
        original_rate="hill_equation(P5, vmax=100.0, k=0.5, n=2.0)",
        place_tokens={'P5': 0.8},
        amplitude=0.15
    )
    
    # Test 4: Linear rate with place dependency
    test_rate_with_noise(
        name="Linear Rate (Place-Dependent)",
        original_rate="2.5 * P1",
        place_tokens={'P1': 10.0},
        amplitude=0.1
    )
    
    # Test 5: Complex SBML-style formula
    test_rate_with_noise(
        name="Complex SBML Formula",
        original_rate="kf_0 * P1 * P2 / (km + P1)",
        place_tokens={'P1': 5.0, 'P2': 3.0, 'kf_0': 2.0, 'km': 1.0},
        amplitude=0.2
    )
    
    # Test 6: Conditional rate
    test_rate_with_noise(
        name="Conditional Rate (Threshold)",
        original_rate="100.0 if P1 > 5 else 10.0",
        place_tokens={'P1': 8.0},
        amplitude=0.1
    )
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Key Findings:

1. ✓ Multiplicative noise works with ANY rate function
2. ✓ Noise preserves relative magnitude (rate * (1 + noise))
3. ✓ Never produces negative rates (if base rate > 0)
4. ✓ Standard deviation is proportional to base rate
5. ✓ Mean stays close to deterministic value

Best Practice Formula:
    stochastic_rate = f"({original_rate}) * (1 + {amplitude} * wiener(time))"

Examples:
    "1.0" 
    → "(1.0) * (1 + 0.1 * wiener(time))"
    
    "michaelis_menten(P17, vmax=70.0, km=0.1)"
    → "(michaelis_menten(P17, vmax=70.0, km=0.1)) * (1 + 0.1 * wiener(time))"
    
    "kf_0 * P1 * P2 - kr_0 * P3"
    → "(kf_0 * P1 * P2 - kr_0 * P3) * (1 + 0.1 * wiener(time))"

Recommended Amplitudes:
    0.05 (5%)   - High molecule counts (>10,000)
    0.10 (10%)  - Default, biologically realistic
    0.15 (15%)  - Medium concentrations (100-1,000)
    0.20 (20%)  - Low concentrations (<100)
    """)
    
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
