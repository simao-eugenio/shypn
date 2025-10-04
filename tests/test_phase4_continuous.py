#!/usr/bin/env python3
"""Test Phase 4 Continuous Integration.

This test verifies that the SimulationController correctly handles
continuous transitions alongside discrete transitions in hybrid nets.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController


def create_continuous_net():
    """Create a simple continuous net: P1 -> T1(continuous) -> P2
    
    Initial marking: P1 = 10.0 tokens, P2 = 0.0 tokens
    T1: continuous transition with rate = 2.0
    
    Behavior:
    - T1 continuously transfers tokens from P1 to P2
    - Rate: 2.0 tokens/time unit
    - In dt=0.1, transfers 0.2 tokens
    """
    model = ModelCanvasManager()
    
    # Create places
    p1 = Place(x=100, y=100, id=1, name="P1", label="Source")
    p1.tokens = 10.0
    p1.initial_marking = 10.0
    
    p2 = Place(x=300, y=100, id=2, name="P2", label="Sink")
    p2.tokens = 0.0
    p2.initial_marking = 0.0
    
    # Create continuous transition
    t1 = Transition(x=200, y=100, id=1, name="T1", label="Flow")
    t1.transition_type = 'continuous'
    t1.properties = {
        'rate_function': '2.0',  # Constant rate
        'max_rate': 10.0,
        'min_rate': 0.0
    }
    
    # Create arcs
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    
    # Add to model
    model.places.extend([p1, p2])
    model.transitions.append(t1)
    model.arcs.extend([a1, a2])
    
    return model


def create_hybrid_net():
    """Create a hybrid net with both discrete and continuous transitions.
    
    Structure:
        P1(5) -> T1(immediate) -> P2(0) -> T2(continuous, rate=1.0) -> P3(0)
    
    Behavior:
    - T1 (discrete): fires once, moves 1 token from P1 to P2
    - T2 (continuous): continuously flows tokens from P2 to P3
    """
    model = ModelCanvasManager()
    
    # Create places
    p1 = Place(x=100, y=100, id=1, name="P1", label="Start")
    p1.tokens = 5
    p1.initial_marking = 5
    
    p2 = Place(x=200, y=100, id=2, name="P2", label="Buffer")
    p2.tokens = 0
    p2.initial_marking = 0
    
    p3 = Place(x=300, y=100, id=3, name="P3", label="End")
    p3.tokens = 0.0
    p3.initial_marking = 0.0
    
    # Create transitions
    t1 = Transition(x=150, y=100, id=1, name="T1", label="Discrete")
    t1.transition_type = 'immediate'
    
    t2 = Transition(x=250, y=100, id=2, name="T2", label="Continuous")
    t2.transition_type = 'continuous'
    t2.properties = {
        'rate_function': '1.0',
        'max_rate': 10.0,
        'min_rate': 0.0
    }
    
    # Create arcs
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    a3 = Arc(source=p2, target=t2, id=3, name="A3", weight=1)
    a4 = Arc(source=t2, target=p3, id=4, name="A4", weight=1)
    
    # Add to model
    model.places.extend([p1, p2, p3])
    model.transitions.extend([t1, t2])
    model.arcs.extend([a1, a2, a3, a4])
    
    return model


def create_parallel_hybrid_net():
    """Create a hybrid net with parallel discrete and continuous paths.
    
    Structure:
        P1(5) -> T1(immediate) -> P2(0)
        P3(10.0) -> T2(continuous, rate=2.0) -> P4(0.0)
    
    Behavior:
    - T1 and T2 operate on disjoint localities (independence)
    - T1 fires discretely
    - T2 flows continuously
    - Both can execute in same step
    """
    model = ModelCanvasManager()
    
    # Discrete path
    p1 = Place(x=100, y=50, id=1, name="P1", label="Discrete-In")
    p1.tokens = 5
    p1.initial_marking = 5
    
    p2 = Place(x=300, y=50, id=2, name="P2", label="Discrete-Out")
    p2.tokens = 0
    p2.initial_marking = 0
    
    t1 = Transition(x=200, y=50, id=1, name="T1", label="Discrete")
    t1.transition_type = 'immediate'
    
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    
    # Continuous path
    p3 = Place(x=100, y=150, id=3, name="P3", label="Continuous-In")
    p3.tokens = 10.0
    p3.initial_marking = 10.0
    
    p4 = Place(x=300, y=150, id=4, name="P4", label="Continuous-Out")
    p4.tokens = 0.0
    p4.initial_marking = 0.0
    
    t2 = Transition(x=200, y=150, id=2, name="T2", label="Continuous")
    t2.transition_type = 'continuous'
    t2.properties = {
        'rate_function': '2.0',
        'max_rate': 10.0,
        'min_rate': 0.0
    }
    
    a3 = Arc(source=p3, target=t2, id=3, name="A3", weight=1)
    a4 = Arc(source=t2, target=p4, id=4, name="A4", weight=1)
    
    # Add to model
    model.places.extend([p1, p2, p3, p4])
    model.transitions.extend([t1, t2])
    model.arcs.extend([a1, a2, a3, a4])
    
    return model


def test_continuous_integration():
    """Test that continuous transitions integrate token flow correctly."""
    print("\n" + "="*60)
    print("TEST: Continuous Integration")
    print("="*60)
    
    model = create_continuous_net()
    controller = SimulationController(model)
    
    # Initial state
    assert model.places[0].tokens == 10.0, "P1 should have 10.0 tokens initially"
    assert model.places[1].tokens == 0.0, "P2 should have 0.0 tokens initially"
    
    # Step 1: Integrate for dt=0.1 with rate=2.0
    # Expected transfer: 2.0 * 0.1 = 0.2 tokens
    result = controller.step(time_step=0.1)
    assert result, "Continuous transition should integrate"
    
    p1_after = model.places[0].tokens
    p2_after = model.places[1].tokens
    
    print(f"After step 1: P1={p1_after:.2f}, P2={p2_after:.2f}")
    
    # Check token transfer (with small tolerance for floating point)
    expected_transfer = 0.2
    assert abs((10.0 - p1_after) - expected_transfer) < 0.01, \
        f"P1 should have lost ~{expected_transfer} tokens"
    assert abs(p2_after - expected_transfer) < 0.01, \
        f"P2 should have gained ~{expected_transfer} tokens"
    
    # Step 2: Continue integration
    controller.step(time_step=0.1)
    controller.step(time_step=0.1)
    
    p1_final = model.places[0].tokens
    p2_final = model.places[1].tokens
    
    print(f"After 3 steps: P1={p1_final:.2f}, P2={p2_final:.2f}")
    
    # After 3 steps, should have transferred ~0.6 tokens total
    expected_total_transfer = 0.6
    assert abs((10.0 - p1_final) - expected_total_transfer) < 0.02, \
        "Total transfer should be ~0.6 tokens"
    
    # Conservation check: total tokens should remain constant
    total = p1_final + p2_final
    assert abs(total - 10.0) < 0.01, \
        f"Token conservation: total should be 10.0, got {total:.3f}"
    
    print("✓ Continuous integration working correctly")
    print("✓ Token conservation maintained")
    return True


def test_hybrid_discrete_continuous():
    """Test hybrid net with discrete and continuous transitions."""
    print("\n" + "="*60)
    print("TEST: Hybrid Discrete + Continuous")
    print("="*60)
    
    model = create_hybrid_net()
    controller = SimulationController(model)
    
    # Initial: P1=5, P2=0, P3=0
    assert model.places[0].tokens == 5, "P1 should have 5 tokens"
    assert model.places[1].tokens == 0, "P2 should have 0 tokens"
    assert model.places[2].tokens == 0.0, "P3 should have 0.0 tokens"
    
    # Step 1: T1 (discrete) should fire, T2 (continuous) cannot (P2 empty)
    result = controller.step(time_step=0.1)
    assert result, "Step should execute"
    
    assert model.places[0].tokens == 4, "P1 should have 4 tokens after T1 fires"
    assert model.places[1].tokens == 1, "P2 should have 1 token after T1 fires"
    print(f"After step 1: P1={model.places[0].tokens}, P2={model.places[1].tokens}, P3={model.places[2].tokens:.2f}")
    
    # Step 2: T1 fires again, T2 starts flowing
    controller.step(time_step=0.1)
    
    # P2 should be losing tokens to T2 now
    p2_val = model.places[1].tokens
    p3_val = model.places[2].tokens
    
    print(f"After step 2: P1={model.places[0].tokens}, P2={p2_val:.2f}, P3={p3_val:.2f}")
    
    # T2 should have started flowing (rate=1.0, dt=0.1 → 0.1 tokens/step)
    assert p3_val > 0, "P3 should have received tokens from T2"
    
    # Continue for several steps
    for i in range(10):
        controller.step(time_step=0.1)
    
    print(f"After 12 steps: P1={model.places[0].tokens}, P2={model.places[1].tokens:.2f}, P3={model.places[2].tokens:.2f}")
    
    # Verify both transitions worked
    assert model.places[0].tokens < 5, "T1 should have fired multiple times"
    assert model.places[2].tokens > 0, "T2 should have transferred tokens"
    
    print("✓ Hybrid net execution working correctly")
    print("✓ Discrete and continuous transitions coexist")
    return True


def test_parallel_locality_independence():
    """Test that parallel discrete and continuous paths are independent."""
    print("\n" + "="*60)
    print("TEST: Parallel Locality Independence")
    print("="*60)
    
    model = create_parallel_hybrid_net()
    controller = SimulationController(model)
    
    # Initial state
    assert model.places[0].tokens == 5, "P1 (discrete) should have 5 tokens"
    assert model.places[2].tokens == 10.0, "P3 (continuous) should have 10.0 tokens"
    
    # Step 1: Both T1 (discrete) and T2 (continuous) should execute
    result = controller.step(time_step=0.1)
    assert result, "Step should execute"
    
    # Check discrete path
    p1_after = model.places[0].tokens
    p2_after = model.places[1].tokens
    assert p1_after == 4, f"P1 should have 4 tokens after T1 fires, got {p1_after}"
    assert p2_after == 1, f"P2 should have 1 token after T1 fires, got {p2_after}"
    
    # Check continuous path
    p3_after = model.places[2].tokens
    p4_after = model.places[3].tokens
    expected_transfer = 2.0 * 0.1  # rate * dt
    assert abs((10.0 - p3_after) - expected_transfer) < 0.01, \
        f"P3 should have lost ~{expected_transfer} tokens"
    assert abs(p4_after - expected_transfer) < 0.01, \
        f"P4 should have gained ~{expected_transfer} tokens"
    
    print(f"After step 1:")
    print(f"  Discrete: P1={p1_after}, P2={p2_after}")
    print(f"  Continuous: P3={p3_after:.2f}, P4={p4_after:.2f}")
    
    # Run multiple steps
    for _ in range(4):
        controller.step(time_step=0.1)
    
    print(f"After 5 steps:")
    print(f"  Discrete: P1={model.places[0].tokens}, P2={model.places[1].tokens}")
    print(f"  Continuous: P3={model.places[2].tokens:.2f}, P4={model.places[3].tokens:.2f}")
    
    # Verify independence: both paths progressed
    assert model.places[0].tokens == 0, "All tokens should have moved through discrete path"
    assert model.places[1].tokens == 5, "P2 should have all 5 tokens"
    
    # Continuous path should still be flowing
    assert model.places[3].tokens > 0.5, "P4 should have received tokens from continuous flow"
    
    # Token conservation in each path
    discrete_total = model.places[0].tokens + model.places[1].tokens
    continuous_total = model.places[2].tokens + model.places[3].tokens
    
    assert discrete_total == 5, f"Discrete path conservation: should be 5, got {discrete_total}"
    assert abs(continuous_total - 10.0) < 0.01, \
        f"Continuous path conservation: should be 10.0, got {continuous_total:.3f}"
    
    print("✓ Parallel paths are independent")
    print("✓ Discrete and continuous execute simultaneously")
    print("✓ Token conservation maintained in each path")
    return True


def test_continuous_depletion():
    """Test that continuous transitions stop when source is depleted."""
    print("\n" + "="*60)
    print("TEST: Continuous Depletion")
    print("="*60)
    
    model = create_continuous_net()
    controller = SimulationController(model)
    
    # Initial: P1=10.0 tokens, rate=2.0
    # Time to deplete: 10.0 / 2.0 = 5.0 time units
    # Steps needed: 5.0 / 0.1 = 50 steps
    
    initial_total = model.places[0].tokens + model.places[1].tokens
    
    # Run until depletion
    for i in range(60):
        result = controller.step(time_step=0.1)
        
        if model.places[0].tokens < 0.01:  # Effectively depleted
            print(f"✓ P1 depleted after {i+1} steps (time={controller.time:.2f})")
            break
    
    final_p1 = model.places[0].tokens
    final_p2 = model.places[1].tokens
    final_total = final_p1 + final_p2
    
    print(f"Final state: P1={final_p1:.3f}, P2={final_p2:.3f}, total={final_total:.3f}")
    
    # Check conservation
    assert abs(final_total - initial_total) < 0.1, \
        f"Token conservation violated: initial={initial_total}, final={final_total:.3f}"
    
    # P1 should be nearly empty
    assert final_p1 < 0.1, f"P1 should be depleted, got {final_p1:.3f}"
    
    # Most tokens should be in P2
    assert final_p2 > 9.0, f"P2 should have most tokens, got {final_p2:.3f}"
    
    print("✓ Continuous transition stops when source depleted")
    print("✓ Token conservation maintained throughout")
    return True


def test_continuous_rate_function():
    """Test continuous transitions with non-constant rate functions."""
    print("\n" + "="*60)
    print("TEST: Continuous Rate Functions")
    print("="*60)
    
    # This test verifies that rate functions are evaluated
    # For simplicity, we use a constant rate but verify the mechanism
    model = create_continuous_net()
    controller = SimulationController(model)
    
    t1 = model.transitions[0]
    behavior = controller._get_behavior(t1)
    
    # Verify rate function exists
    assert hasattr(behavior, 'rate_function'), "Behavior should have rate_function"
    assert callable(behavior.rate_function), "Rate function should be callable"
    
    # Get current rate
    places_dict = {p.id: p for p in model.places}
    rate = behavior.rate_function(places_dict, controller.time)
    
    print(f"Initial rate: {rate}")
    assert abs(rate - 2.0) < 0.01, f"Rate should be 2.0, got {rate}"
    
    # Step and verify rate is applied
    controller.step(time_step=0.1)
    
    # Check that tokens moved according to rate
    transferred = 10.0 - model.places[0].tokens
    expected = 2.0 * 0.1  # rate * dt
    
    print(f"Transferred: {transferred:.3f}, expected: {expected:.3f}")
    assert abs(transferred - expected) < 0.01, "Transfer should match rate * dt"
    
    print("✓ Rate function evaluation working correctly")
    return True


def run_all_tests():
    """Run all Phase 4 tests."""
    print("\n" + "="*70)
    print("PHASE 4: CONTINUOUS INTEGRATION TEST SUITE")
    print("="*70)
    
    tests = [
        test_continuous_integration,
        test_hybrid_discrete_continuous,
        test_parallel_locality_independence,
        test_continuous_depletion,
        test_continuous_rate_function,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*70)
    
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
        return True
    else:
        print(f"✗ {failed} TEST(S) FAILED")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
