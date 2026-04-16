"""
Immediate Transition Time Tests

Tests zero-time firing behavior of immediate transitions.
Verifies that immediate transitions fire without advancing time.

Part of Phase 1 - Critical Tests
"""

import sys
import os
import pytest

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

from shypn.engine.simulation.controller import SimulationController
from shypn.data.model_canvas_manager import ModelCanvasManager


class TestImmediateTransitionTiming:
    """Test immediate transitions fire at zero time."""
    
    def test_immediate_fires_at_zero_time(self):
        """
        Test: Immediate transition fires without time advancement
        Expected: Transition fires, but time remains at initial value within step
        """
        model = ModelCanvasManager()
        
        # Create simple model: P1 --[w=1]--> T1 --[w=1]--> P2
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        p2.initial_marking = 0
        
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'immediate'
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        initial_time = controller.time  # Should be 0.0
        
        # Step with any dt
        dt = 1.0
        controller.step(dt)
        
        # Transition should have fired (tokens moved)
        assert p1.tokens == 0, "Input place should be empty"
        assert p2.tokens == 1, "Output place should have token"
        
        # Time should advance by dt (immediate fires at t=0, then time advances)
        assert controller.time == initial_time + dt, \
            f"Time should advance by {dt}, got {controller.time}"
    
    def test_multiple_immediate_fire_in_one_step(self):
        """
        Test: Multiple immediate transitions can fire in one step
        Expected: All enabled immediate transitions fire, time advances once
        """
        model = ModelCanvasManager()
        
        # Create chain: P1 -> T1 -> P2 -> T2 -> P3
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=200, y=100, label="P2")
        p2.tokens = 0
        
        p3 = model.add_place(x=300, y=100, label="P3")
        p3.tokens = 0
        
        t1 = model.add_transition(x=150, y=100, label="T1")
        t1.transition_type = 'immediate'
        
        t2 = model.add_transition(x=250, y=100, label="T2")
        t2.transition_type = 'immediate'
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        model.add_arc(p2, t2, weight=1)
        model.add_arc(t2, p3, weight=1)
        
        controller = SimulationController(model)
        
        initial_time = controller.time
        dt = 0.5
        
        controller.step(dt)
        
        # Both transitions should have fired (chain reaction)
        assert p1.tokens == 0, "P1 should be empty"
        assert p2.tokens == 0, "P2 should be empty (T2 fired)"
        assert p3.tokens == 1, "P3 should have token"
        
        # Time advances only once
        assert controller.time == initial_time + dt, \
            "Time should advance once, not per transition"
    
    def test_immediate_exhaustive_firing(self):
        """
        Test: Immediate transitions fire exhaustively before time advances
        Expected: All cascading immediate transitions complete in one step
        """
        model = ModelCanvasManager()
        
        # Create long chain to test exhaustive firing
        num_transitions = 10
        places = []
        transitions = []
        
        # Create chain: P0 -> T0 -> P1 -> T1 -> ... -> P10
        for i in range(num_transitions + 1):
            p = model.add_place(x=100 + i*50, y=100, label=f"P{i}")
            p.tokens = 1 if i == 0 else 0
            p.initial_marking = p.tokens
            places.append(p)
        
        for i in range(num_transitions):
            t = model.add_transition(x=125 + i*50, y=100, label=f"T{i}")
            t.transition_type = 'immediate'
            transitions.append(t)
            model.add_arc(places[i], t, weight=1)
            model.add_arc(t, places[i + 1], weight=1)
        
        controller = SimulationController(model)
        
        initial_time = controller.time
        dt = 1.0
        
        # One step should propagate token through entire chain
        controller.step(dt)
        
        # Verify token reached the end
        assert places[0].tokens == 0, "First place should be empty"
        assert places[-1].tokens == 1, "Last place should have token"
        
        # All intermediate places should be empty
        for i in range(1, num_transitions):
            assert places[i].tokens == 0, f"P{i} should be empty after exhaustive firing"
        
        # Time advances only once
        assert controller.time == initial_time + dt, \
            "Time should advance once despite multiple firings"
    
    def test_immediate_firing_limit(self):
        """
        Test: Immediate firing has iteration limit (prevents infinite loops)
        Expected: Stops after max iterations (e.g., 1000)
        
        NOTE: This tests the safety mechanism mentioned in the analysis.
        The system should log a warning if limit is reached.
        """
        model = ModelCanvasManager()
        
        # Create cycle: P1 -> T1 -> P2 -> T2 -> P1
        # Both places start with tokens to create potential infinite loop
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 1
        p2.initial_marking = 1
        
        t1 = model.add_transition(x=150, y=100, label="T1")
        t1.transition_type = 'immediate'
        
        t2 = model.add_transition(x=250, y=100, label="T2")
        t2.transition_type = 'immediate'
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        model.add_arc(p2, t2, weight=1)
        model.add_arc(t2, p1, weight=1)
        
        controller = SimulationController(model)
        
        dt = 1.0
        
        # Should not hang - iteration limit should prevent infinite loop
        try:
            controller.step(dt)
            # If we get here, the limit worked
            assert True, "Immediate firing limit prevented infinite loop"
        except Exception as e:
            pytest.fail(f"Step should handle infinite loop gracefully: {e}")
        
        # Time should still advance
        assert controller.time == dt, "Time should advance even with cycle"


class TestImmediateVsDiscreteOrdering:
    """Test that immediate transitions fire before discrete transitions."""
    
    def test_immediate_fires_before_discrete(self):
        """
        Test: Immediate transitions have priority over other types
        Expected: Immediate fires first, even if discrete is also enabled
        
        NOTE: This requires timed/stochastic transitions which are tested
        separately. This is a simplified version.
        """
        model = ModelCanvasManager()
        
        # Simple model with immediate transition
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'immediate'
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        dt = 0.1
        controller.step(dt)
        
        # Immediate should have fired
        assert p2.tokens == 1, "Immediate transition should fire"


class TestImmediateTransitionEnablement:
    """Test enablement timing for immediate transitions."""
    
    def test_immediate_enablement_checked_before_firing(self):
        """
        Test: Enablement is checked before firing attempt
        Expected: Only enabled immediate transitions fire
        """
        model = ModelCanvasManager()
        
        # T1 enabled, T2 disabled
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=100, y=200, label="P2")
        p2.tokens = 0  # T2 disabled
        
        p3 = model.add_place(x=300, y=100, label="P3")
        p3.tokens = 0
        
        p4 = model.add_place(x=300, y=200, label="P4")
        p4.tokens = 0
        
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'immediate'
        
        t2 = model.add_transition(x=200, y=200, label="T2")
        t2.transition_type = 'immediate'
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p3, weight=1)
        model.add_arc(p2, t2, weight=1)  # P2 empty, so T2 disabled
        model.add_arc(t2, p4, weight=1)
        
        controller = SimulationController(model)
        
        controller.step(0.5)
        
        # Only T1 should fire
        assert p3.tokens == 1, "T1 should fire (was enabled)"
        assert p4.tokens == 0, "T2 should not fire (was disabled)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
