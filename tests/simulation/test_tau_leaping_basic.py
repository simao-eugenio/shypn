"""Basic tests for τ-leaping implementation.

Tests the foundational τ-leaping components (Phase 2).
"""

import pytest
import numpy as np
from shypn.engine.simulation.tau_leaping import (
    PoissonSampler,
    LeapSelector,
    TauLeapingEngine
)


class TestPoissonSampler:
    """Tests for Poisson sampling."""
    
    def test_sample_single(self):
        """Test single transition sampling."""
        sampler = PoissonSampler(seed=42)
        
        # Sample with propensity=10, tau=0.1 -> lambda=1.0
        firings = sampler.sample(propensity=10.0, tau=0.1)
        
        assert isinstance(firings, int)
        assert firings >= 0
    
    def test_sample_batch(self):
        """Test batch sampling."""
        sampler = PoissonSampler(seed=42)
        
        propensities = [5.0, 10.0, 15.0]
        tau = 0.1
        
        firings = sampler.sample_batch(propensities, tau)
        
        assert len(firings) == 3
        assert all(f >= 0 for f in firings)
        assert all(isinstance(f, (int, np.integer)) for f in firings)
    
    def test_sample_zero_propensity(self):
        """Test sampling with zero propensity."""
        sampler = PoissonSampler(seed=42)
        
        firings = sampler.sample(propensity=0.0, tau=0.1)
        assert firings == 0
    
    def test_sample_conditional(self):
        """Test conditional sampling with limit."""
        sampler = PoissonSampler(seed=42)
        
        # High propensity but limited firings
        firings = sampler.sample_conditional(
            propensity=1000.0,
            tau=1.0,
            max_firings=5
        )
        
        assert 0 <= firings <= 5
    
    def test_reproducibility(self):
        """Test that same seed gives same results."""
        sampler1 = PoissonSampler(seed=123)
        sampler2 = PoissonSampler(seed=123)
        
        result1 = sampler1.sample(10.0, 0.1)
        result2 = sampler2.sample(10.0, 0.1)
        
        assert result1 == result2


class TestLeapSelector:
    """Tests for leap size selection."""
    
    def test_initialization(self):
        """Test selector initialization."""
        selector = LeapSelector(
            epsilon=0.03,
            critical_threshold=10.0,
            max_tau=1.0,
            min_tau=1e-6
        )
        
        assert selector.epsilon == 0.03
        assert selector.critical_threshold == 10.0
        assert selector.max_tau == 1.0
        assert selector.min_tau == 1e-6
    
    def test_should_use_exact_ssa_all_critical(self):
        """Test detection of all critical reactions."""
        selector = LeapSelector(critical_threshold=10.0)
        
        # All below threshold
        propensities = [2.0, 5.0, 8.0]
        assert selector.should_use_exact_ssa(propensities)
        
        # Some above threshold
        propensities = [2.0, 15.0, 8.0]
        assert not selector.should_use_exact_ssa(propensities)
    
    def test_should_use_exact_ssa_tiny_total(self):
        """Test detection of negligible total propensity."""
        selector = LeapSelector()
        
        propensities = [1e-12, 1e-12]
        assert selector.should_use_exact_ssa(propensities)
    
    def test_calculate_tau_simplified(self):
        """Test simplified tau calculation."""
        selector = LeapSelector(epsilon=0.03)
        
        # Mock model
        class MockModel:
            pass
        
        model = MockModel()
        propensities = [10.0, 20.0, 15.0]
        
        tau = selector._calculate_tau_simplified(propensities, model)
        
        # tau = epsilon / max(propensities) = 0.03 / 20.0 = 0.0015
        expected = 0.03 / 20.0
        assert abs(tau - expected) < 1e-9


class TestTauLeapingEngine:
    """Tests for main tau-leaping engine."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = TauLeapingEngine(
            epsilon=0.03,
            critical_threshold=10.0,
            max_tau=1.0,
            seed=42
        )
        
        assert engine.leap_selector.epsilon == 0.03
        assert engine.leap_selector.critical_threshold == 10.0
        assert engine.stats['total_leaps'] == 0
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        engine = TauLeapingEngine()
        
        stats = engine.get_statistics()
        
        assert 'total_leaps' in stats
        assert 'total_firings' in stats
        assert 'mean_tau' in stats
        assert 'exact_ssa_fallbacks' in stats
        assert 'epsilon' in stats
    
    def test_reset_statistics(self):
        """Test statistics reset."""
        engine = TauLeapingEngine()
        
        # Manually set some stats
        engine.stats['total_leaps'] = 100
        engine.stats['total_firings'] = 500
        
        engine.reset_statistics()
        
        assert engine.stats['total_leaps'] == 0
        assert engine.stats['total_firings'] == 0


class TestTauLeapingTheory:
    """Theoretical validation tests."""
    
    def test_poisson_mean(self):
        """Test that Poisson samples have correct mean."""
        sampler = PoissonSampler(seed=42)
        
        propensity = 10.0
        tau = 0.5
        expected_mean = propensity * tau  # 5.0
        
        # Sample many times
        samples = [sampler.sample(propensity, tau) for _ in range(1000)]
        actual_mean = np.mean(samples)
        
        # Should be close to expected (within 3 standard deviations)
        std_dev = np.sqrt(expected_mean)
        assert abs(actual_mean - expected_mean) < 3 * std_dev / np.sqrt(1000)
    
    def test_poisson_variance(self):
        """Test that Poisson samples have correct variance."""
        sampler = PoissonSampler(seed=42)
        
        propensity = 10.0
        tau = 0.5
        expected_variance = propensity * tau  # 5.0 (mean = variance for Poisson)
        
        samples = [sampler.sample(propensity, tau) for _ in range(1000)]
        actual_variance = np.var(samples, ddof=1)
        
        # Should be close to expected
        assert abs(actual_variance - expected_variance) < 1.0
    
    def test_leap_condition_bounds_change(self):
        """Test that epsilon bounds propensity change."""
        selector = LeapSelector(epsilon=0.03)
        
        # With tau = epsilon / max(a), fastest transition fires ~epsilon times
        # So propensity changes by ~epsilon fraction
        propensities = [100.0]
        
        class MockModel:
            pass
        
        tau = selector._calculate_tau_simplified(propensities, MockModel())
        
        expected_firings = propensities[0] * tau
        
        # Should be approximately epsilon (0.03)
        assert abs(expected_firings - 0.03) < 1e-9


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
