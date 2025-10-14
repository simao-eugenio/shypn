#!/usr/bin/env python3
"""
Test Firing Policy Persistence

Verifies that:
1. Transition has default firing_policy = 'earliest'
2. firing_policy persists through save/load
3. SBML imported transitions have firing_policy = 'earliest'
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.transition import Transition
from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction, KineticLaw
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
import json


def test_default_firing_policy():
    """Test that new transitions default to 'earliest'."""
    print("\n" + "="*80)
    print("TEST 1: Default Firing Policy")
    print("="*80)
    
    # Create a new transition
    transition = Transition(x=100, y=100, id=1, name="T1")
    
    print(f"\nNew transition created:")
    print(f"  ID: {transition.id}")
    print(f"  Name: {transition.name}")
    print(f"  Firing Policy: {transition.firing_policy}")
    
    # Verify default
    assert hasattr(transition, 'firing_policy'), "Should have firing_policy attribute"
    assert transition.firing_policy == 'earliest', f"Should default to 'earliest', got '{transition.firing_policy}'"
    
    print("\n✅ PASS: Default firing_policy is 'earliest'")
    return True


def test_firing_policy_persistence():
    """Test that firing_policy persists through serialization."""
    print("\n" + "="*80)
    print("TEST 2: Firing Policy Persistence (Save/Load)")
    print("="*80)
    
    # Create transition with earliest policy
    transition1 = Transition(x=100, y=100, id=1, name="T1")
    transition1.firing_policy = 'earliest'
    
    # Serialize
    data1 = transition1.to_dict()
    print(f"\nSerialized (earliest):")
    print(f"  firing_policy: {data1.get('firing_policy')}")
    
    assert 'firing_policy' in data1, "Should serialize firing_policy"
    assert data1['firing_policy'] == 'earliest', "Should save 'earliest'"
    
    # Deserialize
    loaded1 = Transition.from_dict(data1)
    print(f"\nDeserialized:")
    print(f"  firing_policy: {loaded1.firing_policy}")
    
    assert loaded1.firing_policy == 'earliest', "Should restore 'earliest'"
    
    # Test with 'latest' policy
    transition2 = Transition(x=200, y=200, id=2, name="T2")
    transition2.firing_policy = 'latest'
    
    data2 = transition2.to_dict()
    print(f"\nSerialized (latest):")
    print(f"  firing_policy: {data2.get('firing_policy')}")
    
    assert data2['firing_policy'] == 'latest', "Should save 'latest'"
    
    loaded2 = Transition.from_dict(data2)
    print(f"\nDeserialized:")
    print(f"  firing_policy: {loaded2.firing_policy}")
    
    assert loaded2.firing_policy == 'latest', "Should restore 'latest'"
    
    print("\n✅ PASS: Firing policy persists through save/load")
    return True


def test_sbml_imported_firing_policy():
    """Test that SBML imported transitions have firing_policy = 'earliest'."""
    print("\n" + "="*80)
    print("TEST 3: SBML Imported Transitions Firing Policy")
    print("="*80)
    
    # Create test SBML pathway
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
    
    kinetic = KineticLaw(
        formula="Vmax * S1 / (Km + S1)",
        parameters={"Vmax": 10.0, "Km": 5.0},
        rate_type="michaelis_menten"
    )
    
    reaction = Reaction(
        id="R1",
        name="Enzyme Reaction",
        reactants=[("S1", 1.0)],
        products=[("P1", 1.0)],
        kinetic_law=kinetic,
        reversible=False
    )
    
    pathway = PathwayData(
        species=[substrate, product],
        reactions=[reaction],
        compartments={"default": "Default"},
        metadata={"name": "Test Pathway"}
    )
    
    # Import
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway)
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    # Verify transition has firing_policy
    assert len(document.transitions) == 1, "Should have 1 transition"
    transition = document.transitions[0]
    
    print(f"\nImported transition:")
    print(f"  Name: {transition.name}")
    print(f"  Type: {transition.transition_type}")
    print(f"  Firing Policy: {transition.firing_policy}")
    
    assert hasattr(transition, 'firing_policy'), "Imported transition should have firing_policy"
    assert transition.firing_policy == 'earliest', f"Should default to 'earliest', got '{transition.firing_policy}'"
    
    # Test persistence of imported transition
    data = transition.to_dict()
    print(f"\nSerialized imported transition:")
    print(f"  firing_policy: {data.get('firing_policy')}")
    
    assert 'firing_policy' in data, "Should serialize firing_policy"
    assert data['firing_policy'] == 'earliest', "Should persist 'earliest'"
    
    print("\n✅ PASS: SBML imported transitions have firing_policy = 'earliest'")
    return True


def test_json_format():
    """Test that firing_policy appears correctly in JSON."""
    print("\n" + "="*80)
    print("TEST 4: JSON Format Verification")
    print("="*80)
    
    # Create transition
    transition = Transition(x=100, y=100, id=1, name="T1")
    transition.firing_policy = 'latest'
    
    # Serialize to dict
    data = transition.to_dict()
    
    # Convert to JSON string (as would be saved to file)
    json_str = json.dumps(data, indent=2)
    
    print(f"\nJSON representation:")
    print(json_str)
    
    # Verify JSON contains firing_policy
    assert '"firing_policy": "latest"' in json_str, "JSON should contain firing_policy"
    
    # Parse back
    parsed = json.loads(json_str)
    assert parsed['firing_policy'] == 'latest', "Parsed JSON should have firing_policy"
    
    print("\n✅ PASS: firing_policy correctly formatted in JSON")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("FIRING POLICY PERSISTENCE TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Default value
        test_default_firing_policy()
        
        # Test 2: Persistence
        test_firing_policy_persistence()
        
        # Test 3: SBML import
        test_sbml_imported_firing_policy()
        
        # Test 4: JSON format
        test_json_format()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print("  ✓ Default firing_policy is 'earliest'")
        print("  ✓ firing_policy persists through save/load")
        print("  ✓ SBML imported transitions have 'earliest' policy")
        print("  ✓ JSON format is correct")
        print("\nFiring policy persistence verified! 🎉")
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
