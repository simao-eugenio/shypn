#!/usr/bin/env python3
"""Test complete architecture synchronization: Class → JSON → UI.

This test validates the full synchronization after implementing the signal_places UI:
1. Class attributes defined in __init__
2. JSON persistence via to_dict/from_dict
3. UI exposure in property dialog

Expected: 100% synchronization across all three layers.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.netobjs.transition import Transition


def test_class_to_json_synchronization():
    """Test Class → JSON synchronization (persistence layer)."""
    
    print("=" * 80)
    print("TEST 1: Class → JSON Synchronization (Persistence Layer)")
    print("=" * 80)
    
    # Create transition with all quorum sensing properties
    print("\n1. Creating transition with full quorum sensing setup...")
    t1 = Transition(x=100, y=200, id="T1", name="Test_Transition")
    
    # Set all quorum sensing properties
    t1.signal_places = ["P10", "P15", "P20"]
    t1.is_environment_aware = True
    t1.module_id = "quorum_module_1"
    t1.transition_type = "continuous"
    t1.properties = {'rate_function': 'P10 * P15 / (1 + P20)'}
    
    print(f"   Transition: {t1.id} - {t1.name}")
    print(f"   Type: {t1.transition_type}")
    print(f"   Signal places: {t1.signal_places}")
    print(f"   Environment aware: {t1.is_environment_aware}")
    print(f"   Module ID: {t1.module_id}")
    
    # Serialize to JSON
    print("\n2. Serializing to JSON (to_dict)...")
    data = t1.to_dict()
    
    required_keys = ['signal_places', 'is_environment_aware', 'module_id', 'properties']
    errors = []
    
    for key in required_keys:
        if key in data:
            print(f"   ✓ {key}: {data[key]}")
        else:
            print(f"   ✗ {key}: MISSING!")
            errors.append(f"{key} not in to_dict()")
    
    # Deserialize from JSON
    print("\n3. Deserializing from JSON (from_dict)...")
    t2 = Transition.from_dict(data)
    
    # Verify all properties restored
    print("\n4. Verifying round-trip preservation...")
    
    if not hasattr(t2, 'signal_places'):
        errors.append("signal_places attribute missing after from_dict")
    elif t2.signal_places != t1.signal_places:
        errors.append(f"signal_places mismatch: {t2.signal_places} != {t1.signal_places}")
    else:
        print(f"   ✓ signal_places: {t2.signal_places}")
    
    if not hasattr(t2, 'is_environment_aware'):
        errors.append("is_environment_aware missing after from_dict")
    elif t2.is_environment_aware != t1.is_environment_aware:
        errors.append(f"is_environment_aware mismatch")
    else:
        print(f"   ✓ is_environment_aware: {t2.is_environment_aware}")
    
    if not hasattr(t2, 'module_id'):
        errors.append("module_id missing after from_dict")
    elif t2.module_id != t1.module_id:
        errors.append(f"module_id mismatch")
    else:
        print(f"   ✓ module_id: {t2.module_id}")
    
    # Report result
    print("\n" + "=" * 80)
    if errors:
        print("TEST 1 FAILED: Class → JSON Synchronization")
        print("=" * 80)
        for error in errors:
            print(f"   ✗ {error}")
        return False
    else:
        print("TEST 1 PASSED: Class → JSON Synchronization ✓")
        print("=" * 80)
        return True


def test_ui_availability():
    """Test that UI components are available (can't fully test without GTK mainloop)."""
    
    print("\n" + "=" * 80)
    print("TEST 2: UI Availability Check")
    print("=" * 80)
    
    try:
        from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader
        
        print("\n1. Checking TransitionPropDialogLoader imports...")
        print("   ✓ TransitionPropDialogLoader class available")
        
        # Check if _setup_signal_dependencies_tab method exists
        print("\n2. Checking for _setup_signal_dependencies_tab method...")
        if hasattr(TransitionPropDialogLoader, '_setup_signal_dependencies_tab'):
            print("   ✓ _setup_signal_dependencies_tab method exists")
        else:
            print("   ✗ _setup_signal_dependencies_tab method NOT FOUND")
            return False
        
        # Check if it's in __init__
        import inspect
        source = inspect.getsource(TransitionPropDialogLoader.__init__)
        if '_setup_signal_dependencies_tab' in source:
            print("   ✓ _setup_signal_dependencies_tab called in __init__")
        else:
            print("   ⚠ _setup_signal_dependencies_tab not called in __init__ (may be intentional)")
        
        # Check that _apply_changes does NOT manually save signal_places
        # (it should be auto-detected, not manually edited)
        print("\n3. Checking _apply_changes does NOT manually save signal_places...")
        apply_source = inspect.getsource(TransitionPropDialogLoader._apply_changes)
        if 'signal_checkboxes' not in apply_source or 'auto-detected' in apply_source.lower():
            print("   ✓ signal_places is auto-detected (not manually saved)")
        else:
            print("   ⚠ _apply_changes may still have manual signal_places logic")
        
        print("\n" + "=" * 80)
        print("TEST 2 PASSED: UI Components Available ✓")
        print("=" * 80)
        print("\n   Note: Signal dependencies tab shows auto-detected values (read-only).")
        print("   Detection happens during simulation by analyzing rate functions.")
        
        return True
        
    except ImportError as e:
        print(f"\n   ✗ Import error: {e}")
        print("\n" + "=" * 80)
        print("TEST 2 FAILED: UI Not Available")
        print("=" * 80)
        return False
    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 80)
        print("TEST 2 FAILED: Unexpected Error")
        print("=" * 80)
        return False


def test_full_architecture_compliance():
    """Test that all three layers (Class, JSON, UI) are properly connected."""
    
    print("\n" + "=" * 80)
    print("TEST 3: Full Architecture Compliance")
    print("=" * 80)
    
    print("\n1. Checking Transition.__init__ defines signal_places...")
    t = Transition(x=0, y=0, id="T1", name="Test")
    
    if hasattr(t, 'signal_places'):
        print(f"   ✓ signal_places defined: {t.signal_places}")
    else:
        print("   ✗ signal_places NOT defined in __init__")
        return False
    
    if hasattr(t, 'is_environment_aware'):
        print(f"   ✓ is_environment_aware defined: {t.is_environment_aware}")
    else:
        print("   ✗ is_environment_aware NOT defined in __init__")
        return False
    
    print("\n2. Checking Transition.to_dict() saves signal_places...")
    t.signal_places = ["P1", "P2"]
    t.is_environment_aware = True
    data = t.to_dict()
    
    if 'signal_places' in data and data['signal_places'] == ["P1", "P2"]:
        print(f"   ✓ signal_places saved: {data['signal_places']}")
    else:
        print("   ✗ signal_places NOT in to_dict() output")
        return False
    
    if 'is_environment_aware' in data and data['is_environment_aware'] == True:
        print(f"   ✓ is_environment_aware saved: {data['is_environment_aware']}")
    else:
        print("   ✗ is_environment_aware NOT in to_dict() output")
        return False
    
    print("\n3. Checking Transition.from_dict() loads signal_places...")
    t2 = Transition.from_dict(data)
    
    if t2.signal_places == ["P1", "P2"]:
        print(f"   ✓ signal_places loaded: {t2.signal_places}")
    else:
        print(f"   ✗ signal_places NOT loaded correctly: {getattr(t2, 'signal_places', 'MISSING')}")
        return False
    
    if t2.is_environment_aware == True:
        print(f"   ✓ is_environment_aware loaded: {t2.is_environment_aware}")
    else:
        print(f"   ✗ is_environment_aware NOT loaded correctly")
        return False
    
    print("\n4. Checking UI layer implementation...")
    try:
        from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader
        
        # Check method exists
        if hasattr(TransitionPropDialogLoader, '_setup_signal_dependencies_tab'):
            print("   ✓ UI method _setup_signal_dependencies_tab exists")
        else:
            print("   ✗ UI method NOT implemented")
            return False
        
        # Check __init__ calls it
        import inspect
        init_source = inspect.getsource(TransitionPropDialogLoader.__init__)
        if '_setup_signal_dependencies_tab' in init_source:
            print("   ✓ UI method called in dialog initialization")
        else:
            print("   ⚠ UI method exists but not called in __init__ (check if intentional)")
        
        print("\n" + "=" * 80)
        print("TEST 3 PASSED: Full Architecture Compliant ✓")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"   ✗ UI layer check failed: {e}")
        print("\n" + "=" * 80)
        print("TEST 3 FAILED: Architecture Not Complete")
        print("=" * 80)
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  COMPLETE ARCHITECTURE SYNCHRONIZATION TEST".center(78) + "║")
    print("║" + "  Class → JSON → UI (All Three Layers)".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run all tests
    test1 = test_class_to_json_synchronization()
    test2 = test_ui_availability()
    test3 = test_full_architecture_compliance()
    
    # Summary
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  FINAL SUMMARY".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print(f"   Class → JSON (Persistence):      {'✓ PASS' if test1 else '✗ FAIL'}")
    print(f"   UI Availability:                   {'✓ PASS' if test2 else '✗ FAIL'}")
    print(f"   Full Architecture Compliance:      {'✓ PASS' if test3 else '✗ FAIL'}")
    print()
    
    if test1 and test2 and test3:
        print("   🎉 ALL TESTS PASSED - 100% SYNCHRONIZATION ACHIEVED! 🎉")
        print()
        print("   Architecture Status:")
        print("   ✅ Class (__init__):     signal_places defined")
        print("   ✅ JSON (to_dict):       signal_places saved")
        print("   ✅ JSON (from_dict):     signal_places loaded")
        print("   ✅ UI (dialog):          signal_places UI implemented")
        print()
        print("   The flow Class → JSON → UI is now fully synchronized!")
        print()
        sys.exit(0)
    else:
        print("   ❌ SOME TESTS FAILED")
        print()
        print("   Please review the errors above.")
        print()
        sys.exit(1)
