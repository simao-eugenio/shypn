#!/usr/bin/env python3
"""
Test ID type change from int to str.

Verifies that Place, Transition, and Arc now accept string IDs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_place_with_string_id():
    """Test Place accepts string IDs"""
    from shypn.netobjs.place import Place
    
    # String ID (KEGG format)
    p1 = Place(100, 100, "P45", "CompoundP45", label="Glucose")
    assert p1.id == "P45"
    assert isinstance(p1.id, str)
    print(f"✓ Place with string ID: {p1.id} ({type(p1.id).__name__})")
    
    # Numeric string ID
    p2 = Place(200, 200, "1", "P1", label="ATP")
    assert p2.id == "1"
    assert isinstance(p2.id, str)
    print(f"✓ Place with numeric string ID: {p2.id} ({type(p2.id).__name__})")
    
    # Integer ID (should be converted to string)
    p3 = Place(300, 300, 123, "P123", label="Test")
    assert p3.id == "123"
    assert isinstance(p3.id, str)
    print(f"✓ Place with int ID (converted): {p3.id} ({type(p3.id).__name__})")
    
    return True

def test_transition_with_string_id():
    """Test Transition accepts string IDs"""
    from shypn.netobjs.transition import Transition
    
    # String ID (KEGG reaction format)
    t1 = Transition(100, 100, "R00710", "ReactionR00710", label="Glycolysis")
    assert t1.id == "R00710"
    assert isinstance(t1.id, str)
    print(f"✓ Transition with string ID: {t1.id} ({type(t1.id).__name__})")
    
    # Numeric string ID
    t2 = Transition(200, 200, "1", "T1", label="Fire")
    assert t2.id == "1"
    assert isinstance(t2.id, str)
    print(f"✓ Transition with numeric string ID: {t2.id} ({type(t2.id).__name__})")
    
    return True

def test_arc_with_string_id():
    """Test Arc accepts string IDs"""
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    from shypn.netobjs.arc import Arc
    
    p = Place(100, 100, "P45", "P45")
    t = Transition(200, 200, "R00710", "R00710")
    
    # String ID
    a1 = Arc(p, t, "A123", "A123", weight=2)
    assert a1.id == "A123"
    assert isinstance(a1.id, str)
    print(f"✓ Arc with string ID: {a1.id} ({type(a1.id).__name__})")
    
    # Verify object references
    assert a1.source is p, "Arc should store Place object reference"
    assert a1.target is t, "Arc should store Transition object reference"
    print(f"✓ Arc uses object references (not IDs)")
    
    return True

def test_id_uniqueness():
    """Test that different ID formats are unique"""
    from shypn.netobjs.place import Place
    
    p1 = Place(100, 100, "P45", "P45")
    p2 = Place(200, 200, "P46", "P46")
    p3 = Place(300, 300, "hsa:123", "hsa:123")
    
    ids = {p1.id, p2.id, p3.id}
    assert len(ids) == 3, "All IDs should be unique"
    print(f"✓ ID uniqueness: {ids}")
    
    return True

def main():
    print("=" * 70)
    print("Testing ID Type Change: int → str")
    print("=" * 70)
    
    tests = [
        ("Place with string IDs", test_place_with_string_id),
        ("Transition with string IDs", test_transition_with_string_id),
        ("Arc with string IDs", test_arc_with_string_id),
        ("ID uniqueness", test_id_uniqueness),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[{name}]")
            result = test_func()
            if result:
                passed += 1
                print(f"  → PASS")
        except Exception as e:
            failed += 1
            print(f"  → FAIL: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("✅ All tests passed - ID type change successful!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
