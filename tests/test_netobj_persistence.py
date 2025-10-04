#!/usr/bin/env python3
"""Test script for netobj persistence (to_dict/from_dict)."""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs import Place, Transition, Arc


def test_place_persistence():
    """Test Place serialization and deserialization."""
    print("\n🔍 Testing Place Persistence...")
    
    # Create a place
    p1 = Place(x=100.0, y=200.0, id=1, name="P1", label="Input Place")
    p1.set_tokens(3)
    
    # Serialize to dict
    data = p1.to_dict()
    print(f"✅ Serialized: {json.dumps(data, indent=2)}")
    
    # Deserialize from dict
    p2 = Place.from_dict(data)
    
    # Verify properties match
    assert p2.id == p1.id, f"ID mismatch: {p2.id} != {p1.id}"
    assert p2.name == p1.name, f"Name mismatch: {p2.name} != {p1.name}"
    assert p2.label == p1.label, f"Label mismatch: {p2.label} != {p1.label}"
    assert p2.x == p1.x, f"X mismatch: {p2.x} != {p1.x}"
    assert p2.y == p1.y, f"Y mismatch: {p2.y} != {p1.y}"
    assert p2.radius == p1.radius, f"Radius mismatch: {p2.radius} != {p1.radius}"
    assert p2.tokens == p1.tokens, f"Tokens mismatch: {p2.tokens} != {p1.tokens}"
    
    print(f"✅ Place persistence verified: {p1.name} → {p2.name}")
    return True


def test_transition_persistence():
    """Test Transition serialization and deserialization."""
    print("\n🔍 Testing Transition Persistence...")
    
    # Create a transition
    t1 = Transition(x=200.0, y=200.0, id=1, name="T1", label="Process", horizontal=True)
    
    # Serialize to dict
    data = t1.to_dict()
    print(f"✅ Serialized: {json.dumps(data, indent=2)}")
    
    # Deserialize from dict
    t2 = Transition.from_dict(data)
    
    # Verify properties match
    assert t2.id == t1.id, f"ID mismatch: {t2.id} != {t1.id}"
    assert t2.name == t1.name, f"Name mismatch: {t2.name} != {t1.name}"
    assert t2.label == t1.label, f"Label mismatch: {t2.label} != {t1.label}"
    assert t2.x == t1.x, f"X mismatch: {t2.x} != {t1.x}"
    assert t2.y == t1.y, f"Y mismatch: {t2.y} != {t1.y}"
    assert t2.horizontal == t1.horizontal, f"Orientation mismatch: {t2.horizontal} != {t1.horizontal}"
    
    print(f"✅ Transition persistence verified: {t1.name} → {t2.name}")
    return True


def test_arc_persistence():
    """Test Arc serialization and deserialization."""
    print("\n🔍 Testing Arc Persistence...")
    
    # Create place and transition
    p1 = Place(x=100.0, y=200.0, id=1, name="P1")
    t1 = Transition(x=200.0, y=200.0, id=1, name="T1")
    
    # Create arc
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=2)
    
    # Serialize to dict
    data = a1.to_dict()
    print(f"✅ Serialized: {json.dumps(data, indent=2)}")
    
    # Prepare lookup dictionaries (simulating document context)
    places = {1: p1}
    transitions = {1: t1}
    
    # Deserialize from dict
    a2 = Arc.from_dict(data, places=places, transitions=transitions)
    
    # Verify properties match
    assert a2.id == a1.id, f"ID mismatch: {a2.id} != {a1.id}"
    assert a2.name == a1.name, f"Name mismatch: {a2.name} != {a1.name}"
    assert a2.weight == a1.weight, f"Weight mismatch: {a2.weight} != {a1.weight}"
    assert a2.source.id == a1.source.id, f"Source mismatch: {a2.source.id} != {a1.source.id}"
    assert a2.target.id == a1.target.id, f"Target mismatch: {a2.target.id} != {a1.target.id}"
    
    print(f"✅ Arc persistence verified: {a1.name} ({a1.source.name} → {a1.target.name})")
    return True


def test_complete_network_persistence():
    """Test serializing a complete Petri net."""
    print("\n🔍 Testing Complete Network Persistence...")
    
    # Create a simple Petri net: P1 → T1 → P2
    p1 = Place(x=100.0, y=200.0, id=1, name="P1", label="Input")
    p1.set_tokens(3)
    
    t1 = Transition(x=200.0, y=200.0, id=1, name="T1", label="Process")
    
    p2 = Place(x=300.0, y=200.0, id=2, name="P2", label="Output")
    
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=2)
    a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    
    # Serialize entire network
    network_data = {
        "version": "2.0",
        "places": [p1.to_dict(), p2.to_dict()],
        "transitions": [t1.to_dict()],
        "arcs": [a1.to_dict(), a2.to_dict()]
    }
    
    print("✅ Network serialized:")
    print(json.dumps(network_data, indent=2))
    
    # Deserialize network
    places_dict = {}
    transitions_dict = {}
    arcs = []
    
    # Restore places first
    for p_data in network_data["places"]:
        place = Place.from_dict(p_data)
        places_dict[place.id] = place
    
    # Restore transitions second
    for t_data in network_data["transitions"]:
        transition = Transition.from_dict(t_data)
        transitions_dict[transition.id] = transition
    
    # Restore arcs last (need places and transitions)
    for a_data in network_data["arcs"]:
        arc = Arc.from_dict(a_data, places=places_dict, transitions=transitions_dict)
        arcs.append(arc)
    
    # Verify network integrity
    assert len(places_dict) == 2, f"Expected 2 places, got {len(places_dict)}"
    assert len(transitions_dict) == 1, f"Expected 1 transition, got {len(transitions_dict)}"
    assert len(arcs) == 2, f"Expected 2 arcs, got {len(arcs)}"
    
    # Verify connectivity
    assert arcs[0].source.name == "P1", f"Arc 1 source should be P1, got {arcs[0].source.name}"
    assert arcs[0].target.name == "T1", f"Arc 1 target should be T1, got {arcs[0].target.name}"
    assert arcs[1].source.name == "T1", f"Arc 2 source should be T1, got {arcs[1].source.name}"
    assert arcs[1].target.name == "P2", f"Arc 2 target should be P2, got {arcs[1].target.name}"
    
    print("✅ Complete network persistence verified!")
    print(f"   - Places: {list(places_dict.values())}")
    print(f"   - Transitions: {list(transitions_dict.values())}")
    print(f"   - Arcs: {arcs}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("🔄 NET OBJECT PERSISTENCE TESTS")
    print("=" * 60)
    
    tests = [
        test_place_persistence,
        test_transition_persistence,
        test_arc_persistence,
        test_complete_network_persistence
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
