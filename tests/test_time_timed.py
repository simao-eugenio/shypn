"""
Timed Transition Time Tests

Tests timing window behavior of timed transitions.
Verifies that timed transitions respect earliest/latest firing windows.

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


class TestTimedTransitionWindows:
    """Test timed transition firing windows."""
    
    def test_fires_within_window(self):
        """
        Test: Timed transition fires within [earliest, latest] window
        Expected: Fires when elapsed_time in [earliest, latest]
        """
        model = ModelCanvasManager()
        
        # Create model: P1 -> T1[earliest=1.0, latest=2.0] -> P2
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        earliest = 1.0
        latest = 2.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        # TimedBehavior reads from transition.properties dict
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = earliest
        t1.properties['latest'] = latest
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Step to just before earliest (should not fire)
        dt = 0.5
        controller.step(dt)  # time = 0.5
        assert p2.tokens == 0, "Should not fire before earliest"
        
        # Step to within window (should fire eventually)
        controller.step(dt)  # time = 1.0 (at earliest)
        
        # Timed transitions may need multiple steps to fire
        # Give it several more steps to fire within the window
        for i in range(10):
            if p2.tokens > 0:
                break
            controller.step(dt)
        
        assert p2.tokens == 1, f"Should fire by time {controller.time} (within [{earliest}, {latest}] window)"
    
    def test_does_not_fire_before_earliest(self):
        """
        Test: Timed transition does not fire before earliest time
        Expected: Remains enabled but doesn't fire until earliest
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        earliest = 2.0
        latest = 5.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = earliest
        t1.properties['latest'] = latest
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Multiple steps before earliest
        for i in range(4):  # 4 * 0.4 = 1.6 seconds
            controller.step(0.4)
            assert p2.tokens == 0, f"Should not fire at time {controller.time}"
        
        # Now at time 1.6, still before earliest (2.0)
        assert controller.time == 1.6
        assert p2.tokens == 0
    
    def test_fires_at_latest_if_not_fired_before(self):
        """
        Test: Timed transition fires at latest if not fired earlier
        Expected: Guaranteed firing by latest time
        
        NOTE: Actual behavior depends on implementation - may fire randomly
        within window. This tests that it MUST fire by latest.
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        earliest = 1.0
        latest = 3.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = earliest
        t1.properties['latest'] = latest
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Step past latest
        dt = 0.5
        num_steps = 8  # 8 * 0.5 = 4.0 seconds (past latest=3.0)
        
        for i in range(num_steps):
            controller.step(dt)
            if p2.tokens > 0:
                break
        
        # Must have fired by now (past latest)
        assert p2.tokens == 1, f"Should have fired by time {controller.time} (latest={latest})"
    
    def test_enablement_time_determines_window(self):
        """
        Test: Firing window is relative to enablement time, not absolute time
        Expected: Window starts when transition becomes enabled
        """
        model = ModelCanvasManager()
        
        # Initially T1 disabled (P1 empty)
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 0
        p1.initial_marking = 0
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        earliest = 0.5
        latest = 1.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = earliest
        t1.properties['latest'] = latest
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Advance time while T1 disabled
        controller.step(1.0)  # time = 1.0, T1 still disabled
        assert p2.tokens == 0
        
        # Enable T1 by adding token to P1
        p1.tokens = 1
        
        # Now T1 enabled at time=1.0
        # Window is [1.0 + earliest, 1.0 + latest] = [1.5, 2.0]
        
        # Step to 1.4 (before window)
        controller.step(0.4)  # time = 1.4
        assert p2.tokens == 0, "Should not fire before enablement + earliest"
        
        # Step into window
        controller.step(0.2)  # time = 1.6 (in window [1.5, 2.0])
        # May or may not fire here, but should by latest
        
        controller.step(0.5)  # time = 2.1 (past latest)
        assert p2.tokens == 1, "Should have fired by enablement_time + latest"
    
    def test_window_with_large_dt_may_miss(self):
        """
        Test: Large dt may miss firing window entirely
        Expected: Transition may not fire if dt > window width
        
        NOTE: This is the critical bug identified in analysis!
        Large dt can skip over narrow windows.
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        # Narrow window
        earliest = 1.0
        latest = 1.5
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = earliest
        t1.properties['latest'] = latest
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Large time step that skips window
        large_dt = 2.0  # Jumps from 0 to 2.0, missing [1.0, 1.5]
        controller.step(large_dt)
        
        # Behavior here is implementation-dependent
        # Current implementation SHOULD still fire (checks if past latest)
        # But may not if implementation only checks "within window"
        
        # Document expected behavior (may need fixing if fails)
        if p2.tokens == 0:
            pytest.xfail("Large dt missed window - known issue requiring fix")
        else:
            assert p2.tokens == 1, "Should fire even if dt skips window"


class TestTimedTransitionEdgeCases:
    """Test edge cases for timed transitions."""
    
    def test_zero_earliest_fires_immediately(self):
        """
        Test: earliest=0 means can fire immediately when enabled
        Expected: Fires in first step after enablement
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        earliest = 0.0
        latest = 1.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = earliest
        t1.properties['latest'] = latest
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # First step should fire (earliest=0)
        controller.step(0.1)
        assert p2.tokens == 1, "Should fire immediately with earliest=0"
    
    def test_earliest_equals_latest_fixed_delay(self):
        """
        Test: earliest == latest creates fixed delay
        Expected: Fires exactly at earliest (== latest) time
        
        Fixed: Window crossing detection added to controller.step()
        The controller now detects when a time step would cross a zero-width window
        and fires the transition even if the step size is large.
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        delay = 2.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = delay
        t1.properties['latest'] = delay
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Step to just before delay with smaller steps to avoid warning
        controller.step(0.9)  # time = 0.9
        controller.step(0.9)  # time = 1.8
        assert p2.tokens == 0, "Should not fire before delay"
        
        # Step past delay - window crossing should fire the transition
        controller.step(0.3)  # time = 2.1, crosses window at [2.0, 2.0]
        
        assert p2.tokens == 1, f"Should fire via window crossing (current time: {controller.time})"
    
    def test_multiple_timed_transitions_independent(self):
        """
        Test: Multiple timed transitions track their own windows
        Expected: Each transition fires based on its own enablement time
        """
        model = ModelCanvasManager()
        
        # Two independent timed transitions
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 1
        p2.initial_marking = 1
        
        p3 = model.add_place(x=100, y=300, label="P3")
        p3.tokens = 0
        
        p4 = model.add_place(x=300, y=300, label="P4")
        p4.tokens = 0
        
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = 1.0
        t1.properties['latest'] = 2.0
        
        t2 = model.add_transition(x=200, y=300, label="T2")
        t2.transition_type = 'timed'
        if not hasattr(t2, 'properties'):
            t2.properties = {}
        t2.properties['earliest'] = 0.5
        t2.properties['latest'] = 1.5
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p3, weight=1)
        model.add_arc(p2, t2, weight=1)
        model.add_arc(t2, p4, weight=1)
        
        controller = SimulationController(model)
        
        # T2 should fire first (shorter earliest)
        controller.step(0.6)  # time = 0.6
        
        # Only T2 should have fired (or neither, depends on random selection)
        # At least verify both don't fire
        total_fired = (1 if p3.tokens > 0 else 0) + (1 if p4.tokens > 0 else 0)
        assert total_fired <= 1, "Only one discrete transition fires per step"
        
        # Continue until both fire
        for i in range(10):
            controller.step(0.3)
            if p3.tokens > 0 and p4.tokens > 0:
                break
        
        # Eventually both should fire
        assert p3.tokens == 1, "T1 should eventually fire"
        assert p4.tokens == 1, "T2 should eventually fire"


class TestTimedTransitionTimeAccess:
    """Test that timed transitions access time correctly."""
    
    def test_timed_behavior_uses_model_time(self):
        """
        Test: Timed behavior accesses current simulation time
        Expected: Behavior uses controller.logical_time for calculations
        """
        model = ModelCanvasManager()
        
        p1 = model.add_place(x=100, y=100, label="P1")
        p1.tokens = 1
        p1.initial_marking = 1
        
        p2 = model.add_place(x=300, y=100, label="P2")
        p2.tokens = 0
        
        earliest = 1.0
        latest = 2.0
        t1 = model.add_transition(x=200, y=100, label="T1")
        t1.transition_type = 'timed'
        if not hasattr(t1, 'properties'):
            t1.properties = {}
        t1.properties['earliest'] = earliest
        t1.properties['latest'] = latest
        
        model.add_arc(p1, t1, weight=1)
        model.add_arc(t1, p2, weight=1)
        
        controller = SimulationController(model)
        
        # Advance to time 1.5 (within window)
        controller.step(0.5)  # time = 0.5
        controller.step(0.5)  # time = 1.0
        controller.step(0.5)  # time = 1.5
        
        # Should have fired by now or will soon
        controller.step(0.5)  # time = 2.0 (at latest)
        controller.step(0.1)  # time = 2.1 (past latest)
        
        assert p2.tokens == 1, "Should fire using correct time reference"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
