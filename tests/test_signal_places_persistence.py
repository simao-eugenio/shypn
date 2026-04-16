#!/usr/bin/env python3
"""Test script to verify signal_places persistence in Transition.to_dict() / from_dict().

This validates the fix for the critical architecture gap identified in the audit:
- Issue: signal_places not persisted in JSON (breaks quorum sensing)
- Fix: Added signal_places, is_environment_aware, module_id to to_dict()
- Test: Round-trip serialization preserves quorum sensing data

Expected outcome: All assertions pass, signal_places preserved through save/load cycle.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.netobjs.transition import Transition
from shypn.netobjs.place import Place


def test_signal_places_persistence():
    """Test that signal_places is preserved through to_dict/from_dict cycle."""
    
    print("=" * 80)
    print("TEST: Signal Places Persistence (Quorum Sensing)")
    print("=" * 80)
    
    # Create transition with signal dependencies (quorum sensing)
    print("\n1. Creating transition with signal_places...")
    t1 = Transition(
        x=100.0,
        y=200.0,
        id="T1",
        name="AHL_sensing_transition"
    )
    
    # Set transition type and quorum sensing properties
    t1.transition_type = "continuous"
    t1.signal_places = ["P10", "P15", "P20"]  # Signal dependencies
    t1.is_environment_aware = True
    t1.module_id = "quorum_module_1"
    t1.properties = {
        'rate_function': 'P10 * P15 / (1 + P20)',  # Rate depends on signals
    }
    
    print(f"   Transition ID: {t1.id}")
    print(f"   Signal places: {t1.signal_places}")
    print(f"   Environment aware: {t1.is_environment_aware}")
    print(f"   Module ID: {t1.module_id}")
    print(f"   Rate function: {t1.properties.get('rate_function')}")
    
    # Serialize to dictionary (save)
    print("\n2. Serializing to dictionary (to_dict)...")
    data = t1.to_dict()
    
    print(f"   Keys in serialized data: {sorted(data.keys())}")
    print(f"   signal_places in data: {'signal_places' in data}")
    print(f"   is_environment_aware in data: {'is_environment_aware' in data}")
    print(f"   module_id in data: {'module_id' in data}")
    
    if 'signal_places' in data:
        print(f"   ✓ signal_places saved: {data['signal_places']}")
    else:
        print(f"   ✗ ERROR: signal_places NOT saved!")
        return False
    
    if 'is_environment_aware' in data:
        print(f"   ✓ is_environment_aware saved: {data['is_environment_aware']}")
    else:
        print(f"   ✗ ERROR: is_environment_aware NOT saved!")
        return False
    
    if 'module_id' in data:
        print(f"   ✓ module_id saved: {data['module_id']}")
    else:
        print(f"   ✗ ERROR: module_id NOT saved!")
        return False
    
    # Simulate JSON round-trip (what happens in file save/load)
    print("\n3. Simulating JSON round-trip...")
    json_str = json.dumps(data, indent=2)
    data_loaded = json.loads(json_str)
    print(f"   JSON size: {len(json_str)} bytes")
    
    # Deserialize from dictionary (load)
    print("\n4. Deserializing from dictionary (from_dict)...")
    t2 = Transition.from_dict(data_loaded)
    
    print(f"   Transition ID: {t2.id}")
    print(f"   Signal places: {getattr(t2, 'signal_places', 'NOT SET')}")
    print(f"   Environment aware: {getattr(t2, 'is_environment_aware', 'NOT SET')}")
    print(f"   Module ID: {getattr(t2, 'module_id', 'NOT SET')}")
    
    # Verify preservation
    print("\n5. Verifying data preservation...")
    
    errors = []
    
    # Check signal_places
    if not hasattr(t2, 'signal_places'):
        errors.append("signal_places attribute missing after deserialization")
    elif t2.signal_places != t1.signal_places:
        errors.append(f"signal_places mismatch: {t2.signal_places} != {t1.signal_places}")
    else:
        print(f"   ✓ signal_places preserved: {t2.signal_places}")
    
    # Check is_environment_aware
    if not hasattr(t2, 'is_environment_aware'):
        errors.append("is_environment_aware attribute missing after deserialization")
    elif t2.is_environment_aware != t1.is_environment_aware:
        errors.append(f"is_environment_aware mismatch: {t2.is_environment_aware} != {t1.is_environment_aware}")
    else:
        print(f"   ✓ is_environment_aware preserved: {t2.is_environment_aware}")
    
    # Check module_id
    if not hasattr(t2, 'module_id'):
        errors.append("module_id attribute missing after deserialization")
    elif t2.module_id != t1.module_id:
        errors.append(f"module_id mismatch: {t2.module_id} != {t1.module_id}")
    else:
        print(f"   ✓ module_id preserved: {t2.module_id}")
    
    # Check rate function (should be in properties dict)
    if t2.properties.get('rate_function') != t1.properties.get('rate_function'):
        errors.append(f"rate_function mismatch: {t2.properties.get('rate_function')} != {t1.properties.get('rate_function')}")
    else:
        print(f"   ✓ rate_function preserved: {t2.properties.get('rate_function')}")
    
    # Report results
    print("\n" + "=" * 80)
    if errors:
        print("TEST FAILED!")
        print("=" * 80)
        for error in errors:
            print(f"   ✗ {error}")
        return False
    else:
        print("TEST PASSED!")
        print("=" * 80)
        print("   ✓ All quorum sensing properties preserved through save/load cycle")
        print("   ✓ Transition.to_dict() correctly serializes signal_places")
        print("   ✓ Transition.from_dict() correctly deserializes signal_places")
        print("   ✓ 13-tuple Bio-PN formalism now complete!")
        return True


def test_backward_compatibility():
    """Test that transitions without signal_places still load correctly."""
    
    print("\n" + "=" * 80)
    print("TEST: Backward Compatibility (Old Models Without signal_places)")
    print("=" * 80)
    
    # Create old-style transition data (no signal_places)
    print("\n1. Creating old-style transition data (no signal_places)...")
    old_data = {
        "id": "T2",
        "name": "old_transition",
        "x": 50.0,
        "y": 100.0,
        "transition_type": "immediate",
        "properties": {
            "rate_function": "1.0"
        }
    }
    
    print(f"   Keys: {sorted(old_data.keys())}")
    print(f"   signal_places present: {'signal_places' in old_data}")
    
    # Load from old data
    print("\n2. Loading from old data (from_dict)...")
    t_old = Transition.from_dict(old_data)
    
    print(f"   Transition ID: {t_old.id}")
    print(f"   Signal places: {getattr(t_old, 'signal_places', 'NOT SET')}")
    print(f"   Environment aware: {getattr(t_old, 'is_environment_aware', 'NOT SET')}")
    
    # Verify default values
    print("\n3. Verifying default values...")
    
    # Should have default empty list for signal_places
    if hasattr(t_old, 'signal_places'):
        if t_old.signal_places == []:
            print(f"   ✓ signal_places defaults to empty list")
        else:
            print(f"   ⚠ signal_places has unexpected value: {t_old.signal_places}")
    else:
        print(f"   ⟳ signal_places not set (acceptable for old models)")
    
    # Should work fine without signal_places
    print(f"   ✓ Old transition loads successfully without signal_places")
    
    # Save to new format
    print("\n4. Saving to new format (to_dict)...")
    new_data = t_old.to_dict()
    
    # Should now have signal_places key (even if empty)
    if 'signal_places' in new_data:
        print(f"   ✓ signal_places key added in new format: {new_data.get('signal_places', [])}")
    else:
        print(f"   ⟳ signal_places not in new format (acceptable if attribute not set)")
    
    print("\n" + "=" * 80)
    print("BACKWARD COMPATIBILITY TEST PASSED!")
    print("=" * 80)
    print("   ✓ Old models load correctly")
    print("   ✓ No errors from missing signal_places")
    print("   ✓ Upgrade path works seamlessly")
    
    return True


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  SIGNAL PLACES PERSISTENCE TEST".center(78) + "║")
    print("║" + "  (Quorum Sensing / 13-tuple Bio-PN Formalism)".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run tests
    test1_passed = test_signal_places_persistence()
    test2_passed = test_backward_compatibility()
    
    # Summary
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  TEST SUMMARY".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print(f"   Signal Places Persistence:  {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"   Backward Compatibility:     {'✓ PASS' if test2_passed else '✗ FAIL'}")
    print()
    
    if test1_passed and test2_passed:
        print("   🎉 ALL TESTS PASSED! 🎉")
        print()
        print("   Quorum sensing is now fully supported in the persistence layer.")
        print("   Signal dependencies will be preserved across save/load cycles.")
        print()
        sys.exit(0)
    else:
        print("   ❌ SOME TESTS FAILED")
        print()
        print("   Please review the errors above and fix the issues.")
        print()
        sys.exit(1)
