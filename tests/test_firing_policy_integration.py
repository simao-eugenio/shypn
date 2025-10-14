#!/usr/bin/env python3
"""
Firing Policy Integration Test

This test simulates the complete workflow:
1. Create a transition
2. Verify default firing_policy
3. Change firing_policy
4. Save to file
5. Load from file
6. Verify persistence
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.transition import Transition
from shypn.netobjs.place import Place


def test_complete_workflow():
    """Test complete workflow: create, modify, save, load."""
    print("\n" + "="*80)
    print("FIRING POLICY INTEGRATION TEST")
    print("="*80)
    
    # Step 1: Create transition
    print("\n[Step 1] Creating transition...")
    transition = Transition(x=100, y=100, id=1, name="TestTransition")
    
    print(f"  Created: {transition.name}")
    print(f"  Default firing_policy: {transition.firing_policy}")
    
    assert transition.firing_policy == 'earliest', "Should default to 'earliest'"
    print("  ✓ Default verified")
    
    # Step 2: Modify firing_policy
    print("\n[Step 2] Changing firing_policy to 'latest'...")
    transition.firing_policy = 'latest'
    transition.priority = 10
    transition.transition_type = 'stochastic'
    transition.rate = 2.5
    
    print(f"  firing_policy: {transition.firing_policy}")
    print(f"  priority: {transition.priority}")
    print(f"  type: {transition.transition_type}")
    print(f"  rate: {transition.rate}")
    print("  ✓ Modified")
    
    # Step 3: Serialize to dict
    print("\n[Step 3] Serializing to dictionary...")
    data = transition.to_dict()
    
    print(f"  Serialized firing_policy: {data.get('firing_policy')}")
    print(f"  Serialized priority: {data.get('priority')}")
    print(f"  Keys: {', '.join(list(data.keys())[:10])}...")
    
    assert 'firing_policy' in data, "Should have firing_policy in dict"
    assert data['firing_policy'] == 'latest', "Should serialize 'latest'"
    print("  ✓ Serialization verified")
    
    # Step 4: Save to temporary file
    print("\n[Step 4] Saving to temporary file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
        json.dump({'transitions': [data]}, f, indent=2)
    
    print(f"  File: {temp_file}")
    file_size = os.path.getsize(temp_file)
    print(f"  Size: {file_size} bytes")
    print("  ✓ Saved")
    
    # Step 5: Load from file
    print("\n[Step 5] Loading from file...")
    with open(temp_file, 'r') as f:
        loaded_data = json.load(f)
    
    transition_data = loaded_data['transitions'][0]
    print(f"  Loaded firing_policy: {transition_data.get('firing_policy')}")
    print(f"  Loaded priority: {transition_data.get('priority')}")
    print("  ✓ File read")
    
    # Step 6: Deserialize
    print("\n[Step 6] Deserializing transition...")
    loaded_transition = Transition.from_dict(transition_data)
    
    print(f"  Name: {loaded_transition.name}")
    print(f"  firing_policy: {loaded_transition.firing_policy}")
    print(f"  priority: {loaded_transition.priority}")
    print(f"  type: {loaded_transition.transition_type}")
    print(f"  rate: {loaded_transition.rate}")
    
    assert loaded_transition.firing_policy == 'latest', "Should restore 'latest'"
    assert loaded_transition.priority == 10, "Should restore priority"
    assert loaded_transition.transition_type == 'stochastic', "Should restore type"
    assert loaded_transition.rate == 2.5, "Should restore rate"
    print("  ✓ Deserialization verified")
    
    # Step 7: Cleanup
    print("\n[Step 7] Cleaning up...")
    os.unlink(temp_file)
    print(f"  Removed: {temp_file}")
    print("  ✓ Cleanup complete")
    
    # Summary
    print("\n" + "="*80)
    print("✅ INTEGRATION TEST PASSED")
    print("="*80)
    print("\nWorkflow verified:")
    print("  ✓ Create transition with default 'earliest'")
    print("  ✓ Change to 'latest'")
    print("  ✓ Serialize to dict")
    print("  ✓ Save to JSON file")
    print("  ✓ Load from JSON file")
    print("  ✓ Deserialize with correct firing_policy")
    print("\n✨ Firing policy persists correctly through entire workflow!")
    
    return True


def test_multiple_transitions():
    """Test that multiple transitions can have different firing policies."""
    print("\n" + "="*80)
    print("MULTIPLE TRANSITIONS TEST")
    print("="*80)
    
    # Create multiple transitions with different policies
    print("\n[Test] Creating 3 transitions with different policies...")
    
    t1 = Transition(x=100, y=100, id=1, name="T1_Earliest")
    t1.firing_policy = 'earliest'
    t1.priority = 5
    
    t2 = Transition(x=200, y=100, id=2, name="T2_Latest")
    t2.firing_policy = 'latest'
    t2.priority = 5
    
    t3 = Transition(x=300, y=100, id=3, name="T3_Default")
    # t3 keeps default 'earliest'
    t3.priority = 5
    
    print(f"  T1: {t1.name} - priority={t1.priority}, policy={t1.firing_policy}")
    print(f"  T2: {t2.name} - priority={t2.priority}, policy={t2.firing_policy}")
    print(f"  T3: {t3.name} - priority={t3.priority}, policy={t3.firing_policy}")
    
    # Serialize all
    print("\n[Test] Serializing all transitions...")
    data = {
        'transitions': [t1.to_dict(), t2.to_dict(), t3.to_dict()]
    }
    
    # Save to file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
        json.dump(data, f, indent=2)
    
    print(f"  Saved to: {temp_file}")
    
    # Load and verify
    print("\n[Test] Loading and verifying...")
    with open(temp_file, 'r') as f:
        loaded_data = json.load(f)
    
    loaded_transitions = [Transition.from_dict(td) for td in loaded_data['transitions']]
    
    for i, lt in enumerate(loaded_transitions, 1):
        print(f"  T{i}: {lt.name} - policy={lt.firing_policy}")
    
    assert loaded_transitions[0].firing_policy == 'earliest', "T1 should be 'earliest'"
    assert loaded_transitions[1].firing_policy == 'latest', "T2 should be 'latest'"
    assert loaded_transitions[2].firing_policy == 'earliest', "T3 should be 'earliest'"
    
    # Cleanup
    os.unlink(temp_file)
    
    print("\n✅ Multiple transitions with different policies verified!")
    return True


def test_backwards_compatibility():
    """Test that old files without firing_policy load correctly."""
    print("\n" + "="*80)
    print("BACKWARDS COMPATIBILITY TEST")
    print("="*80)
    
    print("\n[Test] Simulating old file format (no firing_policy)...")
    
    # Create dict as if from old file (no firing_policy key)
    old_format = {
        "id": 1,
        "name": "OldTransition",
        "type": "transition",
        "x": 100,
        "y": 100,
        "transition_type": "continuous",
        "priority": 7,
        "rate": 1.5
        # NOTE: No 'firing_policy' key!
    }
    
    print("  Old format keys:", ', '.join(old_format.keys()))
    print("  ✓ No 'firing_policy' in old format")
    
    # Load with Transition.from_dict()
    print("\n[Test] Loading old format transition...")
    transition = Transition.from_dict(old_format)
    
    print(f"  Name: {transition.name}")
    print(f"  Priority: {transition.priority}")
    print(f"  firing_policy: {transition.firing_policy}")
    
    # Should default to 'earliest'
    assert hasattr(transition, 'firing_policy'), "Should have firing_policy attribute"
    assert transition.firing_policy == 'earliest', "Should default to 'earliest'"
    
    print("\n✅ Backwards compatibility verified!")
    print("  ✓ Old files without firing_policy load correctly")
    print("  ✓ Missing attribute defaults to 'earliest'")
    
    return True


def main():
    """Run all integration tests."""
    try:
        # Test 1: Complete workflow
        test_complete_workflow()
        
        # Test 2: Multiple transitions
        test_multiple_transitions()
        
        # Test 3: Backwards compatibility
        test_backwards_compatibility()
        
        print("\n" + "="*80)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*80)
        print("\nFiring policy feature is production-ready! 🎉")
        print("\nSummary:")
        print("  ✓ Complete workflow: create → modify → save → load → verify")
        print("  ✓ Multiple transitions with different policies")
        print("  ✓ Backwards compatibility with old files")
        print("\nThe feature is fully integrated and tested!")
        
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
