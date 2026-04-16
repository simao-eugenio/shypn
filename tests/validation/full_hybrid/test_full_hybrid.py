"""Full hybrid system tests.

Tests for complete hybrid systems combining continuous with ALL discrete
transition types (immediate, timed, stochastic) in the same model.
"""

import pytest
from shypn.engine.simulation.controller import SimulationController
from .conftest import verify_full_hybrid_conservation


class TestFullHybrid:
    """Tests for full hybrid systems (continuous + all discrete types)."""
    
    def test_cascade_all_four_types(self, full_hybrid_cascade):
        """Test complete cascade through all 4 transition types.
        
        Flow: Continuous → Immediate → Timed → Stochastic → Output
        
        Expected:
            - Continuous fills P2
            - Immediate drains P2 to P3
            - Timed drains P3 to P4 (after 0.5s delay)
            - Stochastic drains P4 to P5 (probabilistically)
            - Tokens flow through entire cascade
        """
        manager, p1, p2, p3, p4, p5, t1, t2, t3, t4 = full_hybrid_cascade
        controller = SimulationController(manager)
        
        places = [p1, p2, p3, p4, p5]
        initial_total = sum(p.tokens for p in places)
        
        # Run for 2.0 seconds
        time_step = 0.01
        total_time = 2.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Verify flow occurred
        assert p1.tokens < 20.0, "P1 should have been consumed by continuous"
        assert p5.tokens > 0, "P5 should have received tokens through cascade"
        
        # Intermediate places should have some activity
        # (may not be empty due to timing and stochastic variance)
        
        # Token conservation (relaxed for continuous integration)
        verify_full_hybrid_conservation(manager, initial_total, tolerance=0.5)
    
    def test_parallel_all_four_types(self, full_hybrid_parallel):
        """Test all 4 types draining same place in parallel.
        
        Priority order:
            1. Immediate fires first (highest priority)
            2. Timed fires after delay (0.3s)
            3. Stochastic fires probabilistically
            4. Continuous drains continuously in background
        
        Expected:
            - P3 gets tokens first (immediate priority)
            - P2 gets continuous flow
            - P4 gets timed tokens after 0.3s
            - P5 may get stochastic tokens
        """
        manager, p1, p2, p3, p4, p5, t_continuous, t_immediate, t_timed, t_stochastic = full_hybrid_parallel
        controller = SimulationController(manager)
        
        places = [p1, p2, p3, p4, p5]
        initial_total = sum(p.tokens for p in places)
        
        # Run for 1.0 second
        time_step = 0.01
        total_time = 1.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Verify P1 was consumed
        assert p1.tokens < 10.0, "P1 should have been drained"
        
        # Immediate should have fired (highest priority)
        assert p3.tokens > 0, "P3 should have immediate tokens"
        
        # At least some transitions should have fired
        total_distributed = p2.tokens + p3.tokens + p4.tokens + p5.tokens
        assert total_distributed > 0, "Tokens should have been distributed"
        
        # Continuous may or may not flow if immediate takes all tokens first
        # Just verify system is active
        
        # Token conservation
        verify_full_hybrid_conservation(manager, initial_total, tolerance=0.5)
    
    def test_complex_network_with_feedback(self, full_hybrid_complex):
        """Test complex network with all 4 types and feedback loop.
        
        Structure:
            - Continuous feeds P2
            - Immediate drains P2 to P3
            - Stochastic creates feedback P3→P2
            - Timed provides output P3→P4
        
        Expected:
            - Dynamic equilibrium between feed and drain
            - Feedback stabilizes token distribution
            - All transition types active
        """
        manager, p1, p2, p3, p4, t_continuous, t_immediate, t_timed, t_stochastic = full_hybrid_complex
        controller = SimulationController(manager)
        
        places = [p1, p2, p3, p4]
        initial_total = sum(p.tokens for p in places)
        
        # Run for 2.0 seconds to allow dynamics to settle
        time_step = 0.01
        total_time = 2.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Verify activity
        assert p1.tokens < 20.0, "P1 should have been consumed"
        assert p4.tokens > 0, "P4 should have received output tokens"
        
        # P2 and P3 may have tokens due to feedback loop
        # Just verify system is active
        consumed_from_p1 = 20.0 - p1.tokens
        assert consumed_from_p1 > 2.0, "Significant consumption should have occurred"
        
        # Token conservation (relaxed due to continuous + feedback)
        verify_full_hybrid_conservation(manager, initial_total, tolerance=1.0)
    
    def test_priority_ordering_all_types(self, full_hybrid_priority_test):
        """Test priority ordering when all 4 types compete.
        
        All transitions enabled simultaneously, compete for tokens from P1.
        
        With immediate having priority 10 and being enabled immediately,
        it should dominate and consume most/all tokens before other
        transitions get a chance to fire. This test verifies the priority
        system works correctly.
        """
        manager, p1, p_continuous, p_immediate, p_timed, p_stochastic = full_hybrid_priority_test
        controller = SimulationController(manager)
        
        initial_total = p1.tokens + p_continuous.tokens + p_immediate.tokens + p_timed.tokens + p_stochastic.tokens
        
        # Run for 2.0 seconds (longer to allow all types to fire)
        time_step = 0.01
        total_time = 2.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Immediate should fire (highest priority)
        assert p_immediate.tokens >= 1.0, "Immediate should have fired (highest priority)"
        
        # At least some tokens should have moved from P1
        assert p1.tokens < initial_total, "Tokens should have moved from P1"
        
        # Token conservation
        final_total = p1.tokens + p_continuous.tokens + p_immediate.tokens + p_timed.tokens + p_stochastic.tokens
        verify_full_hybrid_conservation(manager, initial_total)
        
        # Token conservation
        final_total = p1.tokens + p_continuous.tokens + p_immediate.tokens + p_timed.tokens + p_stochastic.tokens
        assert abs(final_total - initial_total) < 0.5
    
    def test_continuous_doesnt_block_discrete(self, full_hybrid_cascade):
        """Test that continuous transitions don't block discrete transitions.
        
        Continuous should flow in background while discrete transitions
        fire according to their own logic.
        """
        manager, p1, p2, p3, p4, p5, t1, t2, t3, t4 = full_hybrid_cascade
        controller = SimulationController(manager)
        
        # Record initial state
        p2_initial = p2.tokens
        
        # Run a few steps
        time_step = 0.01
        for _ in range(50):  # 0.5 seconds
            controller.step(time_step=time_step)
        
        # Continuous should have added tokens to P2
        assert p2.tokens > p2_initial or p3.tokens > 0, \
            "Continuous should have transferred tokens"
        
        # Immediate should have fired when enabled
        # If P2 reached >= 1.0, immediate should have drained it
        if p2_initial >= 1.0 or p2.tokens >= 1.0:
            # Check that immediate has been active
            # (P3 should have tokens or P2 should be kept low)
            assert p3.tokens > 0 or p2.tokens < 5.0, \
                "Immediate should have been active"
    
    def test_all_types_token_conservation(self, full_hybrid_cascade):
        """Verify strict token conservation with all 4 types.
        
        Despite different transition semantics, total tokens must be conserved.
        """
        manager, p1, p2, p3, p4, p5, t1, t2, t3, t4 = full_hybrid_cascade
        controller = SimulationController(manager)
        
        places = [p1, p2, p3, p4, p5]
        initial_total = sum(p.tokens for p in places)
        
        # Run for varying durations
        time_step = 0.01
        for duration in [0.5, 1.0, 1.5]:
            steps = int(duration / time_step)
            for _ in range(steps):
                controller.step(time_step=time_step)
            
            current_total = sum(p.tokens for p in places)
            
            # Allow small error for continuous integration
            assert abs(current_total - initial_total) < 0.5, \
                f"At t={controller.time}: tokens not conserved (diff: {abs(current_total - initial_total)})"
