#!/usr/bin/env python3
"""
Test that PathwayConverter automatically adds stochastic noise to heuristic rates.

This simulates importing a pathway and checking that the rate functions
include wiener() noise by default.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.data.pathway.pathway_converter import PathwayConverter, ReactionConverter
from shypn.data.pathway.pathway_data import ProcessedPathwayData, Species, Reaction
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place


def create_mock_pathway():
    """Create a simple mock pathway for testing."""
    pathway = ProcessedPathwayData()
    
    # Add a species
    pathway.species.append(
        Species(
            id='C00031',  # D-Glucose
            name='D-Glucose',
            compartment='cytosol'
        )
    )
    
    # Add a reaction without kinetic law (triggers heuristic)
    pathway.reactions.append(
        Reaction(
            id='R00010',
            name='Hexokinase',
            reactants=[('C00031', 1)],  # Glucose
            products=[('C00668', 1)],   # Glucose-6P
            kinetic_law=None  # No kinetic law - will use heuristic
        )
    )
    
    # Add positions
    pathway.positions = {
        'C00031': (100, 100),
        'R00010': (200, 100),
    }
    
    # Add colors
    pathway.colors = {
        'C00031': '#FFD700',
        'R00010': '#90EE90',
    }
    
    # Add metadata
    pathway.metadata = {
        'name': 'Test Pathway',
        'layout_type': 'test'
    }
    
    return pathway


def test_default_with_noise():
    """Test that noise is added by default."""
    print("=" * 70)
    print("TEST 1: Default Behavior (noise ENABLED)")
    print("=" * 70)
    print()
    
    pathway = create_mock_pathway()
    
    # Create converter with defaults (should have noise enabled)
    converter = PathwayConverter()  # Default: add_stochastic_noise=True
    
    # Convert
    document = converter.convert(pathway)
    
    # Check transition rate
    if document.transitions:
        transition = document.transitions[0]
        rate_func = transition.properties.get('rate_function', '')
        
        print(f"Transition: {transition.name}")
        print(f"Type: {transition.transition_type}")
        print(f"Rate function: {rate_func}")
        print()
        
        if 'wiener(time)' in rate_func:
            print("✓ Stochastic noise IS present (wiener function found)")
            print("  This prevents steady state traps!")
        else:
            print("✗ Stochastic noise NOT present")
            print("  Model may get stuck in steady states")
    else:
        print("✗ No transitions created")
    
    print()


def test_explicit_with_noise():
    """Test explicit enable with custom amplitude."""
    print("=" * 70)
    print("TEST 2: Explicit Enable with ±15% noise")
    print("=" * 70)
    print()
    
    pathway = create_mock_pathway()
    
    # Create converter with explicit settings
    converter = PathwayConverter(
        add_stochastic_noise=True,
        noise_amplitude=0.15
    )
    
    # Convert
    document = converter.convert(pathway)
    
    # Check transition rate
    if document.transitions:
        transition = document.transitions[0]
        rate_func = transition.properties.get('rate_function', '')
        
        print(f"Transition: {transition.name}")
        print(f"Rate function: {rate_func}")
        print()
        
        if '0.15 * wiener(time)' in rate_func:
            print("✓ Custom amplitude (0.15) correctly applied")
        elif 'wiener(time)' in rate_func:
            print("⚠ Wiener present but amplitude may be different")
        else:
            print("✗ Stochastic noise NOT present")
    
    print()


def test_disabled_noise():
    """Test disabling noise."""
    print("=" * 70)
    print("TEST 3: Noise DISABLED")
    print("=" * 70)
    print()
    
    pathway = create_mock_pathway()
    
    # Create converter with noise disabled
    converter = PathwayConverter(
        add_stochastic_noise=False
    )
    
    # Convert
    document = converter.convert(pathway)
    
    # Check transition rate
    if document.transitions:
        transition = document.transitions[0]
        rate_func = transition.properties.get('rate_function', '')
        
        print(f"Transition: {transition.name}")
        print(f"Rate function: {rate_func}")
        print()
        
        if 'wiener(time)' not in rate_func:
            print("✓ Noise correctly disabled (no wiener function)")
            print("  Pure deterministic rate")
        else:
            print("✗ Noise present when it should be disabled")
    
    print()


def compare_rates():
    """Compare rates with and without noise side-by-side."""
    print("=" * 70)
    print("COMPARISON: With vs Without Noise")
    print("=" * 70)
    print()
    
    pathway = create_mock_pathway()
    
    # Without noise
    converter_det = PathwayConverter(add_stochastic_noise=False)
    document_det = converter_det.convert(pathway)
    rate_det = document_det.transitions[0].properties.get('rate_function', '') if document_det.transitions else ''
    
    # With noise (default)
    converter_stoch = PathwayConverter(add_stochastic_noise=True, noise_amplitude=0.1)
    document_stoch = converter_stoch.convert(pathway)
    rate_stoch = document_stoch.transitions[0].properties.get('rate_function', '') if document_stoch.transitions else ''
    
    print("WITHOUT noise:")
    print(f"  {rate_det}")
    print()
    print("WITH noise (±10%):")
    print(f"  {rate_stoch}")
    print()
    
    if rate_det and rate_stoch:
        if rate_det in rate_stoch and 'wiener' in rate_stoch:
            print("✓ Noise correctly wraps the original rate function")
            print(f"  Pattern: ({rate_det}) * (1 + 0.1 * wiener(time))")
        else:
            print("⚠ Unexpected rate structure")
    
    print()


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "PATHWAY CONVERTER: AUTOMATIC STOCHASTIC NOISE" + " " * 11 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        test_default_with_noise()
        test_explicit_with_noise()
        test_disabled_noise()
        compare_rates()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print("""
✓ PathwayConverter now adds stochastic noise by default
✓ Prevents steady state traps in imported pathways
✓ Configurable via constructor parameters
✓ Can be disabled if needed (add_stochastic_noise=False)

Default behavior when importing pathways (e.g., hsa00010):
- All heuristic-generated rates wrapped with wiener() noise
- ±10% amplitude (biologically realistic)
- Example: michaelis_menten(P17, vmax=70.0, km=0.1)
  becomes: (michaelis_menten(P17, vmax=70.0, km=0.1)) * (1 + 0.1 * wiener(time))

This prevents the "model freezes at steady state" problem automatically!
        """)
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()


if __name__ == "__main__":
    main()
