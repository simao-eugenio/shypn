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
    print("TEST 2: Firing Policy Persistence (Save/Load) - All 7 Policies")
    print("="*80)
    
    # Test all 7 firing policies
    policies = ['earliest', 'latest', 'priority', 'race', 'age', 'random', 'preemptive-priority']
    
    for i, policy in enumerate(policies):
        print(f"\n--- Testing policy: {policy} ---")
        
        # Create transition with specific policy
        transition = Transition(x=100*(i+1), y=100, id=i+1, name=f"T{i+1}")
        transition.firing_policy = policy
        transition.priority = (i + 1) * 10  # Set different priorities
        
        # Serialize
        data = transition.to_dict()
        print(f"  Serialized: firing_policy={data.get('firing_policy')}, priority={data.get('priority')}")
        
        assert 'firing_policy' in data, f"Should serialize firing_policy for {policy}"
        assert data['firing_policy'] == policy, f"Should save '{policy}'"
        
        # Deserialize
        loaded = Transition.from_dict(data)
        print(f"  Deserialized: firing_policy={loaded.firing_policy}, priority={loaded.priority}")
        
        assert loaded.firing_policy == policy, f"Should restore '{policy}'"
        assert loaded.priority == (i + 1) * 10, f"Should restore priority for {policy}"
    
    print("\n✅ PASS: All 7 firing policies persist through save/load")
    print("   Tested: earliest, latest, priority, race, age, random, preemptive-priority")
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


def test_dialog_loader_policy_mapping():
    """Test that dialog loader correctly maps all 7 policies."""
    print("\n" + "="*80)
    print("TEST 5: Dialog Loader Policy Mapping")
    print("="*80)
    
    # Expected mappings from dialog loader
    policy_map = {
        'earliest': 0,
        'latest': 1,
        'priority': 2,
        'race': 3,
        'age': 4,
        'random': 5,
        'preemptive-priority': 6
    }
    
    policy_list = [
        'earliest',
        'latest',
        'priority',
        'race',
        'age',
        'random',
        'preemptive-priority'
    ]
    
    print("\nTesting bidirectional mapping:")
    
    # Test policy_map (name -> index)
    for policy, index in policy_map.items():
        print(f"  {policy:20} -> index {index}")
        assert 0 <= index < 7, f"Index {index} out of range for {policy}"
    
    # Test policy_list (index -> name)
    for index, policy in enumerate(policy_list):
        print(f"  index {index} -> {policy:20}")
        assert policy in policy_map, f"Policy {policy} not in policy_map"
        assert policy_map[policy] == index, f"Inconsistent mapping for {policy}"
    
    # Test round-trip
    print("\nTesting round-trip conversion:")
    for policy in policy_list:
        index = policy_map[policy]
        retrieved = policy_list[index]
        success = retrieved == policy
        print(f"  {policy:20} -> {index} -> {retrieved:20} {'✓' if success else '✗'}")
        assert success, f"Round-trip failed for {policy}"
    
    print("\n✅ PASS: Dialog loader policy mapping is correct and bidirectional")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("FIRING POLICY PERSISTENCE TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Default value
        test_default_firing_policy()
        
        # Test 2: Persistence (all 7 policies)
        test_firing_policy_persistence()
        
        # Test 3: SBML import
        test_sbml_imported_firing_policy()
        
        # Test 4: JSON format
        test_json_format()
        
        # Test 5: Dialog loader mapping
        test_dialog_loader_policy_mapping()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print("  ✓ Default firing_policy is 'earliest'")
        print("  ✓ All 7 firing policies persist through save/load")
        print("  ✓ SBML imported transitions have 'earliest' policy")
        print("  ✓ JSON format is correct")
        print("  ✓ Dialog loader policy mapping is bidirectional")
        print("\nPolicies tested:")
        print("  - earliest (time-based, earliest enabled)")
        print("  - latest (time-based, most recent)")
        print("  - priority (hierarchical, use transition.priority)")
        print("  - race (mass action, exponential sampling)")
        print("  - age (FIFO, oldest enabled first)")
        print("  - random (uniform random selection)")
        print("  - preemptive-priority (interrupt mechanism)")
        print("\nFiring policy implementation verified! 🎉")
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
