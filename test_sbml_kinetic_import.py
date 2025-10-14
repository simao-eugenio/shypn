#!/usr/bin/env python3
"""
Test SBML Kinetic Law Import Enhancement

Verifies that:
1. Michaelis-Menten kinetics → rate_function with michaelis_menten(substrate, Vmax, Km)
2. Mass action kinetics → stochastic transition with lambda parameter
3. Place references are correctly resolved in rate functions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.pathway.pathway_data import (
    PathwayData, ProcessedPathwayData, Species, Reaction, KineticLaw
)
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def create_test_michaelis_menten_pathway():
    """Create test pathway with Michaelis-Menten kinetics (single substrate)."""
    
    # Create species
    substrate = Species(
        id="S1",
        name="Substrate",
        initial_concentration=10.0,
        compartment="default"
    )
    
    product = Species(
        id="P1",
        name="Product",
        initial_concentration=0.0,
        compartment="default"
    )
    
    # Create Michaelis-Menten kinetic law
    mm_kinetic = KineticLaw(
        formula="Vmax * S1 / (Km + S1)",
        parameters={"Vmax": 10.0, "Km": 5.0},
        rate_type="michaelis_menten"
    )
    
    # Create reaction with MM kinetics
    reaction = Reaction(
        id="R1",
        name="Enzyme Reaction",
        reactants=[("S1", 1.0)],  # (species_id, stoichiometry)
        products=[("P1", 1.0)],
        kinetic_law=mm_kinetic,
        reversible=False
    )
    
    # Create pathway
    pathway = PathwayData(
        species=[substrate, product],
        reactions=[reaction],
        compartments={"default": "Default"},
        metadata={"name": "MM Test Pathway"}
    )
    
    return pathway


def create_test_multi_substrate_mm_pathway():
    """Create test pathway with multi-substrate Michaelis-Menten kinetics."""
    
    # Create species
    substrate_a = Species(
        id="S1",
        name="Substrate A",
        initial_concentration=15.0,
        compartment="default"
    )
    
    substrate_b = Species(
        id="S2",
        name="Substrate B",
        initial_concentration=12.0,
        compartment="default"
    )
    
    product = Species(
        id="P1",
        name="Product",
        initial_concentration=0.0,
        compartment="default"
    )
    
    # Create Michaelis-Menten kinetic law
    mm_kinetic = KineticLaw(
        formula="Vmax * S1 * S2 / (Km + S1 * S2)",
        parameters={"Vmax": 20.0, "Km": 3.0},
        rate_type="michaelis_menten"
    )
    
    # Create bi-substrate reaction
    reaction = Reaction(
        id="R1",
        name="Bi-Substrate Enzyme Reaction",
        reactants=[("S1", 1.0), ("S2", 1.0)],  # Two substrates
        products=[("P1", 1.0)],
        kinetic_law=mm_kinetic,
        reversible=False
    )
    
    # Create pathway
    pathway = PathwayData(
        species=[substrate_a, substrate_b, product],
        reactions=[reaction],
        compartments={"default": "Default"},
        metadata={"name": "Multi-Substrate MM Test Pathway"}
    )
    
    return pathway


def create_test_mass_action_pathway():
    """Create test pathway with mass action kinetics."""
    
    # Create species
    reactant_a = Species(
        id="A",
        name="Reactant A",
        initial_concentration=20.0,
        compartment="default"
    )
    
    reactant_b = Species(
        id="B",
        name="Reactant B",
        initial_concentration=15.0,
        compartment="default"
    )
    
    product_c = Species(
        id="C",
        name="Product C",
        initial_concentration=0.0,
        compartment="default"
    )
    
    # Create mass action kinetic law
    ma_kinetic = KineticLaw(
        formula="k * A * B",
        parameters={"k": 0.1},
        rate_type="mass_action"
    )
    
    # Create bimolecular reaction: A + B → C
    reaction = Reaction(
        id="R2",
        name="Bimolecular Reaction",
        reactants=[("A", 1.0), ("B", 1.0)],
        products=[("C", 1.0)],
        kinetic_law=ma_kinetic,
        reversible=False
    )
    
    # Create pathway
    pathway = PathwayData(
        species=[reactant_a, reactant_b, product_c],
        reactions=[reaction],
        compartments={"default": "Default"},
        metadata={"name": "Mass Action Test Pathway"}
    )
    
    return pathway


def test_michaelis_menten_import():
    """Test that Michaelis-Menten kinetics creates proper rate_function."""
    print("\n" + "="*80)
    print("TEST 1: Michaelis-Menten Kinetics Import")
    print("="*80)
    
    # Create test pathway
    pathway_data = create_test_michaelis_menten_pathway()
    
    # Post-process (adds layout, converts to tokens)
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    # Verify results
    print(f"\nDocument created:")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    
    # Check transition properties
    assert len(document.transitions) == 1, "Should have 1 transition"
    transition = document.transitions[0]
    
    print(f"\nTransition: {transition.name}")
    print(f"  Type: {transition.transition_type}")
    print(f"  Rate: {getattr(transition, 'rate', 'N/A')}")
    
    # Check rate_function
    rate_func = transition.properties.get('rate_function')
    print(f"  Rate Function: {rate_func}")
    
    # Verify Michaelis-Menten setup
    assert transition.transition_type == "continuous", "Should be continuous"
    assert rate_func is not None, "Should have rate_function"
    assert "michaelis_menten" in rate_func, "Should use michaelis_menten function"
    assert "10" in rate_func or "10.0" in rate_func, "Should have Vmax=10"
    assert "5" in rate_func or "5.0" in rate_func, "Should have Km=5"
    
    # Check that substrate place is referenced
    # Find the place (could be named "P1" or "Substrate" depending on naming)
    place_names = [p.name for p in document.places]
    print(f"\n  Place names: {place_names}")
    
    # Check that at least one place name appears in rate function
    place_referenced = any(p_name in rate_func for p_name in place_names)
    assert place_referenced, f"Should reference a place from {place_names} in rate function"
    
    print("\n✅ PASS: Michaelis-Menten kinetics correctly imported")
    print(f"   Rate function: {rate_func}")
    return True


def test_mass_action_import():
    """Test that mass action kinetics creates stochastic transition."""
    print("\n" + "="*80)
    print("TEST 2: Mass Action Kinetics Import (Stochastic)")
    print("="*80)
    
    # Create test pathway
    pathway_data = create_test_mass_action_pathway()
    
    # Post-process
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    # Verify results
    print(f"\nDocument created:")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    
    # Check transition properties
    assert len(document.transitions) == 1, "Should have 1 transition"
    transition = document.transitions[0]
    
    print(f"\nTransition: {transition.name}")
    print(f"  Type: {transition.transition_type}")
    print(f"  Rate (lambda): {getattr(transition, 'rate', 'N/A')}")
    
    # Check rate_function (optional for mass action)
    rate_func = transition.properties.get('rate_function')
    if rate_func:
        print(f"  Rate Function: {rate_func}")
    
    # Verify mass action setup
    assert transition.transition_type == "stochastic", "Should be STOCHASTIC"
    assert hasattr(transition, 'rate'), "Should have rate attribute (lambda for stochastic)"
    assert transition.rate == 0.1, f"Rate should be 0.1, got {transition.rate}"
    
    # Check if rate function was created (for bimolecular)
    if rate_func:
        assert "mass_action" in rate_func, "Should use mass_action function"
        assert "0.1" in rate_func, "Should have k=0.1"
        print(f"   Bimolecular rate function: {rate_func}")
    
    print("\n✅ PASS: Mass action kinetics correctly imported as STOCHASTIC")
    print(f"   Transition type: {transition.transition_type}")
    print(f"   Rate (lambda): {transition.rate}")
    return True


def test_place_name_resolution():
    """Test that place names are correctly resolved in rate functions."""
    print("\n" + "="*80)
    print("TEST 3: Place Name Resolution in Rate Functions")
    print("="*80)
    
    # Use MM pathway
    pathway_data = create_test_michaelis_menten_pathway()
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    # Get places and transition
    places = {p.name: p for p in document.places}
    transition = document.transitions[0]
    rate_func = transition.properties.get('rate_function')
    
    print(f"\nPlaces created:")
    for name, place in places.items():
        print(f"  - {name} (id={place.id}, tokens={place.tokens})")
    
    print(f"\nRate function: {rate_func}")
    
    # Verify a substrate place is referenced (could be named differently)
    substrate_places = [p for p in document.places if p.tokens > 0]  # Substrate has tokens
    assert len(substrate_places) > 0, "Should have at least one place with tokens (substrate)"
    substrate = substrate_places[0]
    assert substrate.name in rate_func, f"Rate function should reference substrate '{substrate.name}'"
    
    print(f"\n✅ PASS: Place name 'Substrate' correctly resolved in rate function")
    return True


def test_multi_substrate_sequential_mm():
    """Test that multi-substrate reactions use sequential Michaelis-Menten."""
    print("\n" + "="*80)
    print("TEST 4: Multi-Substrate Sequential Michaelis-Menten")
    print("="*80)
    
    # Create test pathway with 2 substrates
    pathway_data = create_test_multi_substrate_mm_pathway()
    
    # Post-process
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    # Verify results
    print(f"\nDocument created:")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    
    # Check transition properties
    assert len(document.transitions) == 1, "Should have 1 transition"
    transition = document.transitions[0]
    
    print(f"\nTransition: {transition.name}")
    print(f"  Type: {transition.transition_type}")
    print(f"  Rate: {getattr(transition, 'rate', 'N/A')}")
    
    # Check rate_function
    rate_func = transition.properties.get('rate_function')
    print(f"  Rate Function: {rate_func}")
    
    # Verify sequential MM setup
    assert transition.transition_type == "continuous", "Should be continuous"
    assert rate_func is not None, "Should have rate_function"
    assert "michaelis_menten" in rate_func, "Should use michaelis_menten function"
    
    # Check for sequential structure: primary MM * saturation terms
    # Should look like: michaelis_menten(P1, 20.0, 3.0) * (P2 / (3.0 + P2))
    place_names = [p.name for p in document.places if p.tokens > 0]  # Get substrate places
    print(f"\n  Substrate places: {place_names}")
    
    # Verify both substrates are referenced
    substrates_referenced = sum(1 for p_name in place_names if p_name in rate_func)
    assert substrates_referenced >= 2, f"Should reference both substrates, found {substrates_referenced}"
    
    # Verify sequential structure (primary MM + saturation term)
    assert " * " in rate_func, "Should have multiplication for sequential kinetics"
    assert "/" in rate_func, "Should have division terms for saturation"
    
    print("\n✅ PASS: Multi-substrate sequential Michaelis-Menten correctly imported")
    print(f"   Rate function: {rate_func}")
    print(f"   Substrates referenced: {substrates_referenced}")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SBML KINETIC LAW IMPORT ENHANCEMENT TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Michaelis-Menten (single substrate)
        test_michaelis_menten_import()
        
        # Test 2: Mass Action → Stochastic
        test_mass_action_import()
        
        # Test 3: Place name resolution
        test_place_name_resolution()
        
        # Test 4: Multi-substrate Sequential MM
        test_multi_substrate_sequential_mm()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print("  ✓ Michaelis-Menten (single) → rate_function with michaelis_menten()")
        print("  ✓ Michaelis-Menten (multi) → sequential rate function")
        print("  ✓ Mass action → stochastic transition with lambda")
        print("  ✓ Place names correctly resolved in rate functions")
        print("\nEnhancements working correctly! 🎉")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
