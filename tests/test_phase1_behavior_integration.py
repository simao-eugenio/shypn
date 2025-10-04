#!/usr/bin/env python3
"""Test Phase 1 Behavior Integration.

This test verifies that the SimulationController correctly integrates
with the behavior classes for immediate transitions.
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


def create_simple_net():
    """Create a simple test net: P1 -> T1 -> P2
    
    Initial marking: P1 = 3 tokens, P2 = 0 tokens
    Arc weights: all = 1
    Transition: immediate type
    """
    # Create model
    model = ModelCanvasManager()
    
    # Create places
    p1 = Place(x=100, y=100, id=1, name="P1", label="Input")
    p1.tokens = 3
    p1.initial_marking = 3
    
    p2 = Place(x=300, y=100, id=2, name="P2", label="Output")
    p2.tokens = 0
    p2.initial_marking = 0
    
    # Create transition (can use same ID as place - no collision with references!)
    t1 = Transition(x=200, y=100, id=1, name="T1", label="Transfer")
    t1.transition_type = 'immediate'  # Explicit immediate type
    
    # Create arcs
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    
    # Add to model (directly append to lists)
    model.places.append(p1)
    model.places.append(p2)
    model.transitions.append(t1)
    model.arcs.append(a1)
    model.arcs.append(a2)
    
    return model, p1, t1, p2


def test_behavior_creation():
    """Test that behaviors are created correctly."""
    print("\n=== Test 1: Behavior Creation ===")
    
    model, p1, t1, p2 = create_simple_net()
    controller = SimulationController(model)
    
    # Get behavior for transition
    behavior = controller._get_behavior(t1)
    
    assert behavior is not None, "Behavior should be created"
    assert behavior.__class__.__name__ == "ImmediateBehavior", f"Expected ImmediateBehavior, got {behavior.__class__.__name__}"
    
    # Check caching - should return same instance
    behavior2 = controller._get_behavior(t1)
    assert behavior is behavior2, "Behavior should be cached"
    
    print(f"✓ Behavior created: {behavior}")
    print(f"✓ Behavior cached correctly")
    print("✓ Test 1 PASSED")


def test_transition_enablement():
    """Test that enablement checking uses behavior."""
    print("\n=== Test 2: Transition Enablement ===")
    
    model, p1, t1, p2 = create_simple_net()
    controller = SimulationController(model)
    
    # T1 should be enabled (P1 has 3 tokens, needs 1)
    enabled = controller._is_transition_enabled(t1)
    assert enabled, "T1 should be enabled with 3 tokens in P1"
    print(f"✓ T1 enabled: {enabled} (P1 has {p1.tokens} tokens)")
    
    # Remove all tokens from P1
    p1.set_tokens(0)
    enabled = controller._is_transition_enabled(t1)
    assert not enabled, "T1 should be disabled with 0 tokens in P1"
    print(f"✓ T1 disabled: {not enabled} (P1 has {p1.tokens} tokens)")
    
    print("✓ Test 2 PASSED")


def test_transition_firing():
    """Test that firing uses behavior."""
    print("\n=== Test 3: Transition Firing ===")
    
    model, p1, t1, p2 = create_simple_net()
    controller = SimulationController(model)
    
    print(f"Initial: P1={p1.tokens}, P2={p2.tokens}")
    
    # Fire T1
    controller._fire_transition(t1)
    
    print(f"After firing: P1={p1.tokens}, P2={p2.tokens}")
    
    # Check token transfer
    assert p1.tokens == 2, f"P1 should have 2 tokens after firing, got {p1.tokens}"
    assert p2.tokens == 1, f"P2 should have 1 token after firing, got {p2.tokens}"
    
    print("✓ Token transfer correct: P1 (3→2), P2 (0→1)")
    print("✓ Test 3 PASSED")


def test_simulation_step():
    """Test full simulation step."""
    print("\n=== Test 4: Simulation Step ===")
    
    model, p1, t1, p2 = create_simple_net()
    controller = SimulationController(model)
    
    print(f"Initial: P1={p1.tokens}, P2={p2.tokens}, time={controller.time}")
    
    # Execute one step
    success = controller.step(time_step=0.1)
    
    print(f"After step: P1={p1.tokens}, P2={p2.tokens}, time={controller.time}")
    
    assert success, "Step should succeed"
    assert p1.tokens == 2, f"P1 should have 2 tokens, got {p1.tokens}"
    assert p2.tokens == 1, f"P2 should have 1 token, got {p2.tokens}"
    assert controller.time == 0.1, f"Time should be 0.1, got {controller.time}"
    
    print("✓ Step executed successfully")
    print("✓ Test 4 PASSED")


def test_multiple_firings():
    """Test multiple consecutive firings."""
    print("\n=== Test 5: Multiple Firings ===")
    
    model, p1, t1, p2 = create_simple_net()
    controller = SimulationController(model)
    
    print(f"Initial: P1={p1.tokens}, P2={p2.tokens}")
    
    # Fire 3 times (should consume all tokens from P1)
    for i in range(3):
        success = controller.step(time_step=0.1)
        print(f"Step {i+1}: success={success}, P1={p1.tokens}, P2={p2.tokens}")
        assert success, f"Step {i+1} should succeed"
    
    # Try to fire again (should fail - no tokens)
    success = controller.step(time_step=0.1)
    print(f"Step 4: success={success}, P1={p1.tokens}, P2={p2.tokens}")
    assert not success, "Step 4 should fail (P1 empty)"
    
    # Final state check
    assert p1.tokens == 0, f"P1 should be empty, got {p1.tokens}"
    assert p2.tokens == 3, f"P2 should have 3 tokens, got {p2.tokens}"
    
    print("✓ All tokens transferred correctly: P1 (3→0), P2 (0→3)")
    print("✓ Deadlock detected correctly")
    print("✓ Test 5 PASSED")


def test_model_adapter():
    """Test ModelAdapter dict interface."""
    print("\n=== Test 6: Model Adapter ===")
    
    model, p1, t1, p2 = create_simple_net()
    controller = SimulationController(model)
    
    adapter = controller.model_adapter
    
    # Check dict interface
    assert 1 in adapter.places, "P1 should be in places dict"
    assert 2 in adapter.places, "P2 should be in places dict"
    assert adapter.places[1] is p1, "places[1] should be P1"
    assert adapter.places[2] is p2, "places[2] should be P2"
    
    assert 1 in adapter.transitions, "T1 should be in transitions dict"
    assert adapter.transitions[1] is t1, "transitions[1] should be T1"
    
    assert 1 in adapter.arcs, "A1 should be in arcs dict"
    assert 2 in adapter.arcs, "A2 should be in arcs dict"
    
    print(f"✓ places dict: {list(adapter.places.keys())}")
    print(f"✓ transitions dict: {list(adapter.transitions.keys())}")
    print(f"✓ arcs dict: {list(adapter.arcs.keys())}")
    print("✓ Test 6 PASSED")


def test_arc_properties():
    """Test Arc source_id and target_id properties."""
    print("\n=== Test 7: Arc Properties ===")
    
    model, p1, t1, p2 = create_simple_net()
    
    # Get arcs
    a1 = model.arcs[0]  # P1 -> T1
    a2 = model.arcs[1]  # T1 -> P2
    
    # Check source_id and target_id properties
    assert a1.source_id == p1.id, f"A1 source_id should be {p1.id}, got {a1.source_id}"
    assert a1.target_id == t1.id, f"A1 target_id should be {t1.id}, got {a1.target_id}"
    
    assert a2.source_id == t1.id, f"A2 source_id should be {t1.id}, got {a2.source_id}"
    assert a2.target_id == p2.id, f"A2 target_id should be {p2.id}, got {a2.target_id}"
    
    print(f"✓ A1: source_id={a1.source_id}, target_id={a1.target_id}")
    print(f"✓ A2: source_id={a2.source_id}, target_id={a2.target_id}")
    print("✓ Test 7 PASSED")


def run_all_tests():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("PHASE 1 BEHAVIOR INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_behavior_creation()
        test_transition_enablement()
        test_transition_firing()
        test_simulation_step()
        test_multiple_firings()
        test_model_adapter()
        test_arc_properties()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nPhase 1 implementation is working correctly!")
        print("- Behavior factory integration: ✓")
        print("- Behavior caching: ✓")
        print("- Locality-based enablement: ✓")
        print("- Behavior-based firing: ✓")
        print("- Model adapter: ✓")
        print("- Arc properties: ✓")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
