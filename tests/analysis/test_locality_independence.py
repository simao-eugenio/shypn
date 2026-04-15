#!/usr/bin/env python3
"""
Test Suite for Locality Independence Detection (Phase 1)

Tests the place-sharing analysis functionality that determines which
transitions are independent (can fire in parallel) vs dependent (conflict).

Key Concept:
    Two transitions are INDEPENDENT ⟺ They DON'T SHARE ANY PLACES
    
    Formally: t1 ⊥ t2  ⟺  (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅

Author: GitHub Copilot
Date: October 11, 2025
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.engine.simulation.controller import SimulationController


class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []


def create_simple_network():
    """Create a simple test network with independent transitions.
    
    Network:
        P1(10) → T1 → P2(0)
        P3(10) → T2 → P4(0)
    
    T1 and T2 are INDEPENDENT (no shared places).
    """
    model = MockModel()
    
    # Create places (x, y, id, name, radius, label)
    p1 = Place(0, 0, 'P1', 'P1', label='P1')
    p1.tokens = 10
    p2 = Place(100, 0, 'P2', 'P2', label='P2')
    p2.tokens = 0
    p3 = Place(0, 100, 'P3', 'P3', label='P3')
    p3.tokens = 10
    p4 = Place(100, 100, 'P4', 'P4', label='P4')
    p4.tokens = 0
    
    model.places = [p1, p2, p3, p4]
    
    # Create transitions (x, y, id, name, transition_type, label)
    t1 = Transition(50, 0, 'T1', 'T1', 'immediate', label='T1')
    t2 = Transition(50, 100, 'T2', 'T2', 'immediate', label='T2')
    
    model.transitions = [t1, t2]
    
    # Create arcs (source, target, id, name, weight)
    arc1 = Arc(p1, t1, 'A1', 'A1', weight=1)
    arc2 = Arc(t1, p2, 'A2', 'A2', weight=1)
    arc3 = Arc(p3, t2, 'A3', 'A3', weight=1)
    arc4 = Arc(t2, p4, 'A4', 'A4', weight=1)
    
    model.arcs = [arc1, arc2, arc3, arc4]
    
    return model, (p1, p2, p3, p4), (t1, t2)


def create_conflicting_network():
    """Create a network with conflicting transitions (share input place).
    
    Network:
        P1(10) → T1 → P2(0)
        P1(10) → T2 → P3(0)
    
    T1 and T2 are DEPENDENT (share P1).
    """
    model = MockModel()
    
    # Create places
    p1 = Place(0, 0, 'P1', 'P1', label='P1')
    p1.tokens = 10
    p2 = Place(100, 0, 'P2', 'P2', label='P2')
    p2.tokens = 0
    p3 = Place(100, 50, 'P3', 'P3', label='P3')
    p3.tokens = 0
    
    model.places = [p1, p2, p3]
    
    # Create transitions
    t1 = Transition(50, 0, 'T1', 'T1', label='T1')
    t1.transition_type = 'immediate'
    t2 = Transition(50, 50, 'T2', 'T2', label='T2')
    t2.transition_type = 'immediate'
    
    model.transitions = [t1, t2]
    
    # Create arcs (both transitions read from P1!)
    arc1 = Arc(p1, t1, 'A1', 'A1', weight=1)
    arc2 = Arc(t1, p2, 'A2', 'A2', weight=1)
    arc3 = Arc(p1, t2, 'A3', 'A3', weight=1)
    arc4 = Arc(t2, p3, 'A4', 'A4', weight=1)
    
    model.arcs = [arc1, arc2, arc3, arc4]
    
    return model, (p1, p2, p3), (t1, t2)


def create_output_conflict_network():
    """Create a network with transitions sharing output place.
    
    Network:
        P1(10) → T1 → P2(0)
        P3(10) → T2 → P2(0)
    
    T1 and T2 are DEPENDENT (share P2 as output).
    """
    model = MockModel()
    
    # Create places
    p1 = Place(0, 0, 'P1', 'P1', label='P1')
    p1.tokens = 10
    p2 = Place(100, 25, 'P2', 'P2', label='P2')
    p2.tokens = 0
    p3 = Place(0, 50, 'P3', 'P3', label='P3')
    p3.tokens = 10
    
    model.places = [p1, p2, p3]
    
    # Create transitions
    t1 = Transition(50, 0, 'T1', 'T1', label='T1')
    t1.transition_type = 'immediate'
    t2 = Transition(50, 50, 'T2', 'T2', label='T2')
    t2.transition_type = 'immediate'
    
    model.transitions = [t1, t2]
    
    # Create arcs (both transitions write to P2!)
    arc1 = Arc(p1, t1, 'A1', 'A1', weight=1)
    arc2 = Arc(t1, p2, 'A2', 'A2', weight=1)
    arc3 = Arc(p3, t2, 'A3', 'A3', weight=1)
    arc4 = Arc(t2, p2, 'A4', 'A4', weight=1)
    
    model.arcs = [arc1, arc2, arc3, arc4]
    
    return model, (p1, p2, p3), (t1, t2)


def create_complex_network():
    """Create a more complex network with mixed dependencies.
    
    Network:
        P1(10) → T1 → P2(0)
        P1(10) → T2 → P3(0)  (shares P1 with T1)
        P4(10) → T3 → P5(0)  (independent)
        P4(10) → T4 → P6(0)  (shares P4 with T3)
    
    Independence groups:
        - T1 and T3 are independent
        - T2 and T4 are independent
        - T1 conflicts with T2 (share P1)
        - T3 conflicts with T4 (share P4)
    """
    model = MockModel()
    
    # Create places
    places = []
    for i in range(1, 7):
        p = Place(((i-1) % 3) * 100, ((i-1) // 3) * 100, f'P{i}', f'P{i}', label=f'P{i}')
        p.tokens = 10 if i in [1, 4] else 0
        places.append(p)
    
    model.places = places
    
    # Create transitions
    transitions = []
    for i in range(1, 5):
        t = Transition(50 + ((i-1) % 2) * 200, ((i-1) // 2) * 100, f'T{i}', f'T{i}', label=f'T{i}')
        t.transition_type = 'immediate'
        transitions.append(t)
    
    model.transitions = transitions
    
    # Create arcs
    arcs = [
        Arc(places[0], transitions[0], 'A1', 'A1', weight=1),
        Arc(transitions[0], places[1], 'A2', 'A2', weight=1),
        Arc(places[0], transitions[1], 'A3', 'A3', weight=1),
        Arc(transitions[1], places[2], 'A4', 'A4', weight=1),
        Arc(places[3], transitions[2], 'A5', 'A5', weight=1),
        Arc(transitions[2], places[4], 'A6', 'A6', weight=1),
        Arc(places[3], transitions[3], 'A7', 'A7', weight=1),
        Arc(transitions[3], places[5], 'A8', 'A8', weight=1),
    ]
    model.arcs = arcs
    
    return model, places, transitions


# ============================================================================
# Test Cases
# ============================================================================

def test_get_all_places_for_transition():
    """Test extraction of all places involved in a transition's locality."""
    print("TEST: _get_all_places_for_transition()")
    
    model, (p1, p2, p3, p4), (t1, t2) = create_simple_network()
    controller = SimulationController(model)
    
    # Test T1: should have {P1, P2}
    places_t1 = controller._get_all_places_for_transition(t1)
    assert 'P1' in places_t1, f"T1 should have P1 in its locality, got {places_t1}"
    assert 'P2' in places_t1, f"T1 should have P2 in its locality, got {places_t1}"
    assert len(places_t1) == 2, f"T1 should have exactly 2 places, got {len(places_t1)}"
    
    # Test T2: should have {P3, P4}
    places_t2 = controller._get_all_places_for_transition(t2)
    assert 'P3' in places_t2, f"T2 should have P3 in its locality, got {places_t2}"
    assert 'P4' in places_t2, f"T2 should have P4 in its locality, got {places_t2}"
    assert len(places_t2) == 2, f"T2 should have exactly 2 places, got {len(places_t2)}"
    
    print("  ✅ Correctly extracts input and output places")


def test_independent_transitions():
    """Test detection of independent transitions (no shared places)."""
    print("\nTEST: _are_independent() - Independent transitions")
    
    model, (p1, p2, p3, p4), (t1, t2) = create_simple_network()
    controller = SimulationController(model)
    
    # T1 and T2 should be independent (no shared places)
    independent = controller._are_independent(t1, t2)
    assert independent, "T1 and T2 should be independent (no shared places)"
    
    print("  ✅ Correctly identifies independent transitions")
    print(f"     T1: {controller._get_all_places_for_transition(t1)}")
    print(f"     T2: {controller._get_all_places_for_transition(t2)}")
    print(f"     Independent: {independent}")


def test_conflicting_input_place():
    """Test detection of conflict when transitions share input place."""
    print("\nTEST: _are_independent() - Conflicting input place")
    
    model, (p1, p2, p3), (t1, t2) = create_conflicting_network()
    controller = SimulationController(model)
    
    # T1 and T2 should be dependent (share P1)
    independent = controller._are_independent(t1, t2)
    assert not independent, "T1 and T2 should NOT be independent (share P1)"
    
    print("  ✅ Correctly detects conflict when sharing input place")
    print(f"     T1: {controller._get_all_places_for_transition(t1)}")
    print(f"     T2: {controller._get_all_places_for_transition(t2)}")
    print(f"     Independent: {independent}")


def test_conflicting_output_place():
    """Test detection of conflict when transitions share output place."""
    print("\nTEST: _are_independent() - Conflicting output place")
    
    model, (p1, p2, p3), (t1, t2) = create_output_conflict_network()
    controller = SimulationController(model)
    
    # T1 and T2 should be dependent (share P2)
    independent = controller._are_independent(t1, t2)
    assert not independent, "T1 and T2 should NOT be independent (share P2)"
    
    print("  ✅ Correctly detects conflict when sharing output place")
    print(f"     T1: {controller._get_all_places_for_transition(t1)}")
    print(f"     T2: {controller._get_all_places_for_transition(t2)}")
    print(f"     Independent: {independent}")


def test_compute_conflict_sets():
    """Test conflict graph construction."""
    print("\nTEST: _compute_conflict_sets()")
    
    model, places, transitions = create_complex_network()
    controller = SimulationController(model)
    
    t1, t2, t3, t4 = transitions
    
    # Compute conflict sets
    conflicts = controller._compute_conflict_sets(transitions)
    
    # Verify conflicts
    # T1 and T2 conflict (share P1)
    assert 'T2' in conflicts['T1'], "T1 should conflict with T2"
    assert 'T1' in conflicts['T2'], "T2 should conflict with T1"
    
    # T3 and T4 conflict (share P4)
    assert 'T4' in conflicts['T3'], "T3 should conflict with T4"
    assert 'T3' in conflicts['T4'], "T4 should conflict with T3"
    
    # T1 and T3 should NOT conflict (independent)
    assert 'T3' not in conflicts['T1'], "T1 should NOT conflict with T3"
    assert 'T1' not in conflicts['T3'], "T3 should NOT conflict with T1"
    
    # T2 and T4 should NOT conflict (independent)
    assert 'T4' not in conflicts['T2'], "T2 should NOT conflict with T4"
    assert 'T2' not in conflicts['T4'], "T4 should NOT conflict with T2"
    
    print("  ✅ Correctly builds conflict graph")
    print(f"     Conflicts: {dict(conflicts)}")


def test_get_independent_groups():
    """Test grouping of independent transitions."""
    print("\nTEST: _get_independent_transitions()")
    
    model, places, transitions = create_complex_network()
    controller = SimulationController(model)
    
    # Get independent groups
    groups = controller._get_independent_transitions(transitions)
    
    print(f"  Independent groups: {len(groups)}")
    for i, group in enumerate(groups):
        labels = [t.label for t in group]
        print(f"    Group {i+1}: {labels}")
    
    # Verify at least 2 groups (T1-T2 conflict, T3-T4 conflict)
    assert len(groups) >= 2, f"Expected at least 2 groups, got {len(groups)}"
    
    # Verify all transitions appear exactly once
    all_transitions = [t for group in groups for t in group]
    assert len(all_transitions) == len(transitions), "All transitions should appear in groups"
    
    print("  ✅ Correctly groups independent transitions")


def test_symmetry():
    """Test that independence is symmetric: t1⊥t2 ⟺ t2⊥t1."""
    print("\nTEST: Independence symmetry")
    
    model, (p1, p2, p3, p4), (t1, t2) = create_simple_network()
    controller = SimulationController(model)
    
    # Check symmetry
    ind_12 = controller._are_independent(t1, t2)
    ind_21 = controller._are_independent(t2, t1)
    
    assert ind_12 == ind_21, "Independence should be symmetric"
    
    print("  ✅ Independence is symmetric")
    print(f"     t1⊥t2: {ind_12}")
    print(f"     t2⊥t1: {ind_21}")


def test_reflexivity():
    """Test that a transition is independent of itself (vacuous truth)."""
    print("\nTEST: Independence reflexivity")
    
    model, (p1, p2, p3, p4), (t1, t2) = create_simple_network()
    controller = SimulationController(model)
    
    # A transition shares all its places with itself
    # So technically it's NOT independent of itself
    ind_11 = controller._are_independent(t1, t1)
    
    # This should be False (shares all places with itself)
    assert not ind_11, "A transition is NOT independent of itself"
    
    print("  ✅ Correctly handles self-comparison")
    print(f"     t1⊥t1: {ind_11} (expected False)")


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all Phase 1 tests."""
    print("=" * 70)
    print("LOCALITY INDEPENDENCE DETECTION - PHASE 1 TESTS")
    print("=" * 70)
    print("\nConcept: Two transitions are INDEPENDENT ⟺ DON'T SHARE PLACES")
    print("Formally: t1 ⊥ t2  ⟺  (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅")
    print()
    
    tests = [
        ("Place Extraction", test_get_all_places_for_transition),
        ("Independent Transitions", test_independent_transitions),
        ("Input Conflict", test_conflicting_input_place),
        ("Output Conflict", test_conflicting_output_place),
        ("Conflict Sets", test_compute_conflict_sets),
        ("Independent Groups", test_get_independent_groups),
        ("Symmetry Property", test_symmetry),
        ("Reflexivity Property", test_reflexivity),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Phase 1 Complete: Independence Detection Implemented")
        print("   • _get_all_places_for_transition() works correctly")
        print("   • _are_independent() correctly detects place sharing")
        print("   • _compute_conflict_sets() builds conflict graph")
        print("   • _get_independent_transitions() groups transitions")
        print("\n📋 Next: Phase 2 - Maximal Concurrent Set Algorithm")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review implementation.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
