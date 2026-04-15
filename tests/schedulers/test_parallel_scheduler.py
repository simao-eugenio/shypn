"""Tests for parallel stochastic scheduler (Phase 3).

Tests weak independence-based parallel execution.
"""

import pytest
from unittest.mock import Mock, MagicMock
from shypn.engine.simulation.tau_leaping import ParallelStochasticScheduler


class TestParallelScheduler:
    """Tests for parallel stochastic scheduler."""
    
    def test_initialization(self):
        """Test scheduler initialization."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(
            model=model,
            enable_parallel=True
        )
        
        assert scheduler.model == model
        assert scheduler.max_workers > 0  # Auto-determined from CPU count
        assert scheduler.enable_parallel is True
        assert scheduler._dependency_groups is None
    
    def test_disabled_parallel_mode(self):
        """Test that parallel can be disabled."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(
            model=model,
            enable_parallel=False
        )
        
        assert scheduler.enable_parallel is False
    
    def test_has_competitive_dependency(self):
        """Test competitive dependency detection."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        # Create mock transitions
        t1 = Mock()
        t1.id = 1
        t2 = Mock()
        t2.id = 2
        
        # Set up competitive pairs
        scheduler._competitive_pairs = {(1, 2), (2, 1)}
        
        assert scheduler._has_competitive_dependency(t1, t2)
        assert scheduler._has_competitive_dependency(t2, t1)
    
    def test_no_competitive_dependency(self):
        """Test independent transitions."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        t1 = Mock()
        t1.id = 1
        t2 = Mock()
        t2.id = 2
        
        scheduler._competitive_pairs = set()
        
        assert not scheduler._has_competitive_dependency(t1, t2)
    
    def test_partition_single_transition(self):
        """Test partitioning with single transition."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        scheduler._competitive_pairs = set()
        
        t1 = Mock()
        t1.id = 1
        
        groups = scheduler._partition_for_parallel_execution([t1])
        
        assert len(groups) == 1
        assert groups[0] == [t1]
    
    def test_partition_independent_transitions(self):
        """Test partitioning independent transitions into one group."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        scheduler._competitive_pairs = set()
        
        t1, t2, t3 = Mock(), Mock(), Mock()
        t1.id, t2.id, t3.id = 1, 2, 3
        
        groups = scheduler._partition_for_parallel_execution([t1, t2, t3])
        
        # All independent → should be in one group
        assert len(groups) == 1
        assert len(groups[0]) == 3
    
    def test_partition_competitive_transitions(self):
        """Test partitioning competitive transitions into separate groups."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        t1, t2 = Mock(), Mock()
        t1.id, t2.id = 1, 2
        
        # t1 and t2 compete
        scheduler._competitive_pairs = {(1, 2), (2, 1)}
        
        groups = scheduler._partition_for_parallel_execution([t1, t2])
        
        # Competitive → separate groups
        assert len(groups) == 2
    
    def test_partition_mixed_dependencies(self):
        """Test partitioning with mixed dependencies."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        t1, t2, t3, t4 = Mock(), Mock(), Mock(), Mock()
        t1.id, t2.id, t3.id, t4.id = 1, 2, 3, 4
        
        # t1-t2 compete, t3-t4 independent, t2-t3 independent
        scheduler._competitive_pairs = {(1, 2), (2, 1)}
        
        groups = scheduler._partition_for_parallel_execution([t1, t2, t3, t4])
        
        # Should have at least 2 groups (t1 and t2 separate)
        assert len(groups) >= 2
        
        # t1 and t2 should not be in same group
        for group in groups:
            if t1 in group:
                assert t2 not in group
            if t2 in group:
                assert t1 not in group
    
    def test_sample_sequential_fallback(self):
        """Test sequential sampling fallback."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        t1, t2 = Mock(), Mock()
        t1.id, t2.id = 1, 2
        
        transitions = [t1, t2]
        propensities = [10.0, 20.0]
        tau = 0.1
        
        firings = scheduler._sample_sequential(transitions, propensities, tau)
        
        assert len(firings) == 2
        assert t1 in firings
        assert t2 in firings
        assert all(f >= 0 for f in firings.values())
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        # Manually increment stats
        scheduler.stats['total_parallel_samples'] = 10
        scheduler.stats['total_sequential_samples'] = 5
        
        stats = scheduler.get_statistics()
        
        assert stats['total_samples'] == 15
        assert stats['parallel_percentage'] > 0
        assert 'parallel_groups' in stats
    
    def test_reset_statistics(self):
        """Test statistics reset."""
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        scheduler.stats['total_parallel_samples'] = 100
        scheduler.reset_statistics()
        
        assert scheduler.stats['total_parallel_samples'] == 0
        assert scheduler.stats['total_sequential_samples'] == 0


class TestParallelSchedulerIntegration:
    """Integration tests requiring model setup."""
    
    def test_sample_parallel_small_problem(self):
        """Test that small problems use sequential."""
        model = Mock()
        model.transitions = []
        
        scheduler = ParallelStochasticScheduler(
            model=model,
            enable_parallel=True
        )
        scheduler._dependency_groups = {}
        scheduler._competitive_pairs = set()
        
        # Only 2 transitions (< 4 threshold)
        t1, t2 = Mock(), Mock()
        t1.id, t2.id = 1, 2
        
        transitions = [t1, t2]
        propensities = [10.0, 20.0]
        tau = 0.1
        
        firings = scheduler.sample_parallel(transitions, propensities, tau)
        
        # Should work (uses sequential fallback)
        assert len(firings) == 2
        assert all(isinstance(f, int) for f in firings.values())


class TestWeakIndependenceTheory:
    """Theoretical validation for weak independence."""
    
    def test_convergent_transitions_can_be_parallel(self):
        """Test that convergent coupling allows parallel execution.
        
        Theory: Shared outputs → rates superpose → independent Poisson sampling OK
        """
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        # Two transitions sharing only outputs (convergent)
        t1, t2 = Mock(), Mock()
        t1.id, t2.id = 1, 2
        
        # No competitive dependency (no shared inputs)
        scheduler._competitive_pairs = set()
        
        groups = scheduler._partition_for_parallel_execution([t1, t2])
        
        # Should be in same parallel group
        assert len(groups) == 1
        assert len(groups[0]) == 2
    
    def test_competitive_transitions_must_be_sequential(self):
        """Test that competitive coupling requires sequential execution.
        
        Theory: Shared inputs → resource competition → must be sequential
        """
        model = Mock()
        scheduler = ParallelStochasticScheduler(model=model)
        
        t1, t2 = Mock(), Mock()
        t1.id, t2.id = 1, 2
        
        # Competitive dependency (shared inputs)
        scheduler._competitive_pairs = {(1, 2), (2, 1)}
        
        groups = scheduler._partition_for_parallel_execution([t1, t2])
        
        # Should be in separate groups
        assert len(groups) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
