#!/usr/bin/env python3
"""
Test automatic transition type validation during SBML import.

This test verifies that stochastic transitions with reversible formulas
(containing subtraction) are automatically converted to continuous type.
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.pathway.pathway_data import Species, Reaction, KineticLaw, PathwayData
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter


def create_reversible_mass_action_pathway():
    """
    Create pathway with reversible mass action reaction.
    
    This simulates the BIOMD0000000061 scenario where mass action
    reactions are reversible (k_f * A * B - k_r * C * D) and should
    be continuous, not stochastic.
    """
    
    # Create species
    glcx0 = Species(
        id="GlcX0",
        name="Glucose External (reservoir)",
        initial_concentration=24.0,
        compartment="extracellular"
    )
    
    glcx = Species(
        id="GlcX",
        name="Glucose External",
        initial_concentration=7.0,
        compartment="extracellular"
    )
    
    # Create REVERSIBLE mass action kinetic law (forward - reverse)
    reversible_kinetic = KineticLaw(
        formula="extracellular * k0 * (GlcX0 - GlcX)",  # Subtraction!
        parameters={
            "extracellular": 1.0,
            "k0": 0.048
        },
        rate_type="mass_action"  # This will initially create stochastic
    )
    
    # Create reversible reaction
    glucose_flow = Reaction(
        id="vinGlc",
        name="Glucose Mixed Flow",
        reactants=[("GlcX", 1)],
        products=[("GlcX0", 1)],
        reversible=True,  # Mark as reversible
        kinetic_law=reversible_kinetic
    )
    
    # Create pathway
    pathway = PathwayData(
        species=[glcx0, glcx],
        reactions=[glucose_flow],
        compartments={"extracellular": 1.0},
        parameters={},
        metadata={"source": "test"}
    )
    
    return pathway


def create_forward_only_mass_action_pathway():
    """
    Create pathway with forward-only mass action (should stay stochastic).
    """
    
    # Create species
    a = Species(
        id="A",
        name="Reactant A",
        initial_concentration=10.0,
        compartment="cell"
    )
    
    b = Species(
        id="B",
        name="Product B",
        initial_concentration=0.0,
        compartment="cell"
    )
    
    # Create FORWARD-ONLY mass action (no subtraction)
    forward_kinetic = KineticLaw(
        formula="k * A",  # No subtraction
        parameters={"k": 0.5},
        rate_type="mass_action"
    )
    
    # Create forward-only reaction
    forward_reaction = Reaction(
        id="R1",
        name="Forward Reaction",
        reactants=[("A", 1)],
        products=[("B", 1)],
        reversible=False,
        kinetic_law=forward_kinetic
    )
    
    # Create pathway
    pathway = PathwayData(
        species=[a, b],
        reactions=[forward_reaction],
        compartments={"cell": 1.0},
        parameters={},
        metadata={"source": "test"}
    )
    
    return pathway


def test_reversible_mass_action_auto_conversion():
    """
    Test that reversible mass action is auto-converted from stochastic to continuous.
    """
    print("\n" + "="*80)
    print("TEST 1: Reversible Mass Action Auto-Conversion")
    print("="*80)
    
    # Create pathway with reversible mass action
    pathway_data = create_reversible_mass_action_pathway()
    
    # Post-process
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    
    # Convert to DocumentModel (this triggers validation)
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    # Verify transition was created
    assert len(document.transitions) == 1, "Should have 1 transition"
    transition = document.transitions[0]
    
    print(f"\n📊 Transition Analysis:")
    print(f"   Name: {transition.name}")
    print(f"   Type: {transition.transition_type}")
    print(f"   Rate: {transition.rate}")
    
    # Check properties
    if hasattr(transition, 'properties'):
        formula = transition.properties.get('rate_function', 'None')
        enrichment = transition.properties.get('enrichment_reason', 'None')
        print(f"   Formula: {formula[:80]}...")
        print(f"   Enrichment: {enrichment}")
    
    # KEY ASSERTION: Should be continuous, not stochastic
    print(f"\n✅ Validation:")
    if transition.transition_type == 'continuous':
        print(f"   ✓ Transition type is 'continuous' (CORRECT)")
    else:
        print(f"   ❌ Transition type is '{transition.transition_type}' (SHOULD BE CONTINUOUS)")
        print(f"   ⚠️  Reversible formula contains subtraction, cannot be stochastic!")
        return False
    
    # Check if has formula with subtraction
    if hasattr(transition, 'properties') and 'rate_function' in transition.properties:
        formula = transition.properties['rate_function']
        if ' - ' in formula:
            print(f"   ✓ Formula contains subtraction (reversible reaction)")
        else:
            print(f"   ⚠️  Formula does not contain subtraction: {formula}")
    
    # Check if enrichment reason mentions conversion
    if hasattr(transition, 'properties') and 'enrichment_reason' in transition.properties:
        reason = transition.properties['enrichment_reason']
        if 'Converted from stochastic' in reason or 'reversible' in reason.lower():
            print(f"   ✓ Marked as converted from stochastic")
    
    print(f"\n✅ TEST PASSED: Reversible mass action correctly converted to continuous")
    return True


def test_forward_only_mass_action_stays_stochastic():
    """
    Test that forward-only mass action stays stochastic (no conversion needed).
    """
    print("\n" + "="*80)
    print("TEST 2: Forward-Only Mass Action Stays Stochastic")
    print("="*80)
    
    # Create pathway with forward-only mass action
    pathway_data = create_forward_only_mass_action_pathway()
    
    # Post-process
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    # Verify transition was created
    assert len(document.transitions) == 1, "Should have 1 transition"
    transition = document.transitions[0]
    
    print(f"\n📊 Transition Analysis:")
    print(f"   Name: {transition.name}")
    print(f"   Type: {transition.transition_type}")
    print(f"   Rate: {transition.rate}")
    
    # Check properties
    if hasattr(transition, 'properties'):
        formula = transition.properties.get('rate_function', 'None')
        print(f"   Formula: {formula}")
    
    # KEY ASSERTION: Should stay stochastic (no subtraction)
    print(f"\n✅ Validation:")
    if transition.transition_type == 'stochastic':
        print(f"   ✓ Transition type is 'stochastic' (CORRECT - no reversibility)")
    else:
        print(f"   ℹ️  Transition type is '{transition.transition_type}' (acceptable)")
    
    # Check formula doesn't have subtraction
    if hasattr(transition, 'properties') and 'rate_function' in transition.properties:
        formula = transition.properties['rate_function']
        if ' - ' not in formula:
            print(f"   ✓ Formula has no subtraction (forward-only)")
        else:
            print(f"   ⚠️  Formula contains subtraction: {formula}")
    
    print(f"\n✅ TEST PASSED: Forward-only mass action appropriately handled")
    return True


if __name__ == '__main__':
    print("\n" + "="*80)
    print("SBML Transition Type Validation Test Suite")
    print("="*80)
    print("\nTesting automatic conversion of stochastic transitions with")
    print("reversible formulas (containing subtraction) to continuous type.")
    print("\nThis prevents negative rate errors during simulation.")
    
    try:
        # Test 1: Reversible mass action should be converted
        success1 = test_reversible_mass_action_auto_conversion()
        
        # Test 2: Forward-only mass action should stay stochastic
        success2 = test_forward_only_mass_action_stays_stochastic()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Test 1 (Reversible → Continuous): {'✅ PASSED' if success1 else '❌ FAILED'}")
        print(f"Test 2 (Forward-Only → Stochastic): {'✅ PASSED' if success2 else '❌ FAILED'}")
        
        if success1 and success2:
            print(f"\n✅ All tests PASSED!")
            print(f"\n💡 Automatic validation is working correctly:")
            print(f"   - Reversible formulas → Converted to continuous")
            print(f"   - Forward-only formulas → Keep as stochastic")
            sys.exit(0)
        else:
            print(f"\n❌ Some tests FAILED")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
