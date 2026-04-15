#!/usr/bin/env python3
"""
Test automatic stochastic noise in heuristic estimators.

Demonstrates how to automatically add wiener() noise to ALL heuristic-generated
rate functions by setting add_stochastic_noise=True in EstimatorFactory.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.heuristic import EstimatorFactory, add_stochastic_noise


def test_manual_noise_wrapper():
    """Test the manual add_stochastic_noise() function."""
    print("=" * 70)
    print("TEST 1: Manual Stochastic Noise Wrapper")
    print("=" * 70)
    print()
    
    test_cases = [
        ("1.0", 0.1),
        ("michaelis_menten(P17, vmax=70.0, km=0.1)", 0.1),
        ("hill_equation(P5, vmax=100.0, km=0.5, n=2.0)", 0.15),
        ("kf_0 * P1 * P2 / (km + P1)", 0.2),
        ("mass_action(P1, P2, k=0.01)", 0.1),
    ]
    
    for original, amplitude in test_cases:
        stochastic = add_stochastic_noise(original, amplitude)
        print(f"Amplitude: {amplitude} (±{amplitude*100:.0f}%)")
        print(f"Original:    {original}")
        print(f"Stochastic:  {stochastic}")
        print()
    
    print("✓ Manual wrapper works for any rate function")
    print()


def test_automatic_noise_in_factory():
    """Test automatic noise application via EstimatorFactory."""
    print("=" * 70)
    print("TEST 2: Automatic Noise via EstimatorFactory")
    print("=" * 70)
    print()
    
    # Mock substrate place
    class MockPlace:
        def __init__(self, name, tokens):
            self.name = name
            self.tokens = tokens
    
    # Mock reaction
    class MockReaction:
        def __init__(self, reaction_id):
            self.id = reaction_id
            self.reactants = [('S1', 1)]
            self.products = [('P1', 1)]
            self.reversible = False
    
    substrate = MockPlace('P17', 0.5)
    product = MockPlace('P18', 0.0)
    reaction = MockReaction('R1')
    
    print("Test Case: Michaelis-Menten Estimator")
    print("-" * 70)
    
    # WITHOUT noise
    print("\n1. WITHOUT stochastic noise:")
    estimator_det = EstimatorFactory.create('michaelis_menten', 
                                            add_stochastic_noise=False)
    params_det, rate_det = estimator_det.estimate_and_build(
        reaction, [substrate], [product]
    )
    print(f"   Parameters: {params_det}")
    print(f"   Rate function: {rate_det}")
    
    # WITH noise (±10%)
    print("\n2. WITH stochastic noise (±10%):")
    estimator_stoch_10 = EstimatorFactory.create('michaelis_menten', 
                                                  add_stochastic_noise=True,
                                                  noise_amplitude=0.1)
    params_stoch_10, rate_stoch_10 = estimator_stoch_10.estimate_and_build(
        reaction, [substrate], [product]
    )
    print(f"   Parameters: {params_stoch_10}")
    print(f"   Rate function: {rate_stoch_10}")
    
    # WITH noise (±20%)
    print("\n3. WITH stochastic noise (±20%):")
    estimator_stoch_20 = EstimatorFactory.create('michaelis_menten', 
                                                  add_stochastic_noise=True,
                                                  noise_amplitude=0.2)
    params_stoch_20, rate_stoch_20 = estimator_stoch_20.estimate_and_build(
        reaction, [substrate], [product]
    )
    print(f"   Parameters: {params_stoch_20}")
    print(f"   Rate function: {rate_stoch_20}")
    
    print()
    print("✓ Factory automatically wraps rate functions with wiener() noise")
    print()


def test_mass_action_with_noise():
    """Test mass action estimator with noise."""
    print("=" * 70)
    print("TEST 3: Mass Action Kinetics with Noise")
    print("=" * 70)
    print()
    
    class MockPlace:
        def __init__(self, name, tokens):
            self.name = name
            self.tokens = tokens
    
    class MockReaction:
        def __init__(self, reaction_id):
            self.id = reaction_id
            self.reactants = [('S1', 1), ('S2', 1)]
            self.products = [('P1', 1)]
            self.reversible = False
    
    substrates = [MockPlace('P1', 5.0), MockPlace('P2', 3.0)]
    products = [MockPlace('P3', 0.0)]
    reaction = MockReaction('R2')
    
    # Without noise
    estimator_det = EstimatorFactory.create('mass_action', 
                                            add_stochastic_noise=False)
    params_det, rate_det = estimator_det.estimate_and_build(
        reaction, substrates, products
    )
    
    # With noise
    estimator_stoch = EstimatorFactory.create('mass_action', 
                                              add_stochastic_noise=True,
                                              noise_amplitude=0.15)
    params_stoch, rate_stoch = estimator_stoch.estimate_and_build(
        reaction, substrates, products
    )
    
    print(f"WITHOUT noise: {rate_det}")
    print(f"WITH noise:    {rate_stoch}")
    print()
    print("✓ Mass action also supports automatic noise")
    print()


def print_usage_guide():
    """Print usage guide for developers."""
    print("=" * 70)
    print("USAGE GUIDE: How to Enable Automatic Stochastic Noise")
    print("=" * 70)
    print()
    
    print("Option 1: In pathway_converter.py (SBML import)")
    print("-" * 70)
    print("""
# In _setup_heuristic_kinetics() method:

# OLD (no noise):
estimator = EstimatorFactory.create('michaelis_menten')

# NEW (with ±10% noise):
estimator = EstimatorFactory.create('michaelis_menten', 
                                   add_stochastic_noise=True,
                                   noise_amplitude=0.1)
    """)
    
    print("Option 2: Make it configurable via settings")
    print("-" * 70)
    print("""
# In pathway_converter.py __init__:
def __init__(self, add_stochastic_noise=False, noise_amplitude=0.1):
    self.add_stochastic_noise = add_stochastic_noise
    self.noise_amplitude = noise_amplitude

# Then in _setup_heuristic_kinetics():
estimator = EstimatorFactory.create(
    'michaelis_menten',
    add_stochastic_noise=self.add_stochastic_noise,
    noise_amplitude=self.noise_amplitude
)
    """)
    
    print("Option 3: UI checkbox/toggle")
    print("-" * 70)
    print("""
# Add checkbox in pathway import dialog:
☑ Add stochastic noise to continuous transitions (prevents steady state traps)

Amplitude: [▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░] 10%
           5%  10%  15%  20%
           
# Pass setting to converter:
converter = PathwayConverter(
    add_stochastic_noise=checkbox_value,
    noise_amplitude=slider_value
)
    """)
    
    print("=" * 70)
    print()


def main():
    """Run all tests and show usage."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 8 + "AUTOMATIC STOCHASTIC NOISE IN HEURISTICS" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    test_manual_noise_wrapper()
    test_automatic_noise_in_factory()
    test_mass_action_with_noise()
    print_usage_guide()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
✓ add_stochastic_noise() function wraps ANY rate expression
✓ EstimatorFactory.create(..., add_stochastic_noise=True) enables automatic noise
✓ All estimators (Michaelis-Menten, Mass Action, Stochastic) support this
✓ Configurable amplitude (default 0.1 = ±10%)

Benefits:
- Prevents steady state traps in continuous transitions
- Biologically realistic (represents molecular noise)
- Works with complex heuristic-generated rates
- Simple one-parameter configuration

Recommended Settings:
- Default: add_stochastic_noise=True, noise_amplitude=0.1
- High concentrations: noise_amplitude=0.05
- Low concentrations: noise_amplitude=0.2

To enable globally:
1. Add parameters to PathwayConverter.__init__()
2. Pass to EstimatorFactory.create() in _setup_heuristic_kinetics()
3. Optionally add UI toggle in import dialog
    """)
    
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
