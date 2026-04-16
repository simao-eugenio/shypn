"""Tests for throughput analyzer."""

import pytest
from unittest.mock import Mock
from shypn.topology.behavioral.throughput import ThroughputAnalyzer


class TestThroughputAnalyzer:
    """Test suite for ThroughputAnalyzer."""
    
    @pytest.fixture
    def simple_model(self):
        """Create a simple Petri net for testing."""
        model = Mock()
        
        # Places: p1, p2
        p1 = Mock()
        p1.tokens = 10
        p2 = Mock()
        p2.tokens = 0
        
        model.places = {'p1': p1, 'p2': p2}
        
        # Transition: t1 (p1 -> p2)
        t1 = Mock()
        model.transitions = {'t1': t1}
        
        # Arcs
        arc1 = Mock()
        arc1.source = 'p1'
        arc1.target = 't1'
        arc1.weight = 1
        
        arc2 = Mock()
        arc2.source = 't1'
        arc2.target = 'p2'
        arc2.weight = 1
        
        model.arcs = {'a1': arc1, 'a2': arc2}
        
        return model
    
    @pytest.fixture
    def cyclic_model(self):
        """Create a cyclic Petri net."""
        model = Mock()
        
        # Places: p1, p2
        p1 = Mock()
        p1.tokens = 5
        p2 = Mock()
        p2.tokens = 5
        
        model.places = {'p1': p1, 'p2': p2}
        
        # Transitions: t1 (p1 -> p2), t2 (p2 -> p1)
        t1 = Mock()
        t2 = Mock()
        model.transitions = {'t1': t1, 't2': t2}
        
        # Arcs for t1
        arc1 = Mock()
        arc1.source = 'p1'
        arc1.target = 't1'
        arc1.weight = 1
        
        arc2 = Mock()
        arc2.source = 't1'
        arc2.target = 'p2'
        arc2.weight = 1
        
        # Arcs for t2
        arc3 = Mock()
        arc3.source = 'p2'
        arc3.target = 't2'
        arc3.weight = 1
        
        arc4 = Mock()
        arc4.source = 't2'
        arc4.target = 'p1'
        arc4.weight = 1
        
        model.arcs = {'a1': arc1, 'a2': arc2, 'a3': arc3, 'a4': arc4}
        
        return model
    
    def test_basic_analysis(self, simple_model):
        """Test basic throughput analysis."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        assert 'firing_rates' in result.data
        assert 'firing_counts' in result.data
        assert 'token_flow' in result.data
        assert 'place_occupancy' in result.data
        assert 'throughput' in result.data
    
    def test_firing_rates_computed(self, simple_model):
        """Test that firing rates are computed correctly."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        firing_rates = result.data['firing_rates']
        
        assert 't1' in firing_rates
        assert isinstance(firing_rates['t1'], float)
        assert 0.0 <= firing_rates['t1'] <= 1.0
    
    def test_firing_counts_tracked(self, simple_model):
        """Test that firing counts are tracked."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        firing_counts = result.data['firing_counts']
        
        assert 't1' in firing_counts
        assert isinstance(firing_counts['t1'], int)
        assert firing_counts['t1'] >= 0
    
    def test_token_flow_measured(self, simple_model):
        """Test that token flow is measured."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        token_flow = result.data['token_flow']
        
        assert 'p1' in token_flow
        assert 'p2' in token_flow
        assert isinstance(token_flow['p2'], int)
    
    def test_place_occupancy_computed(self, simple_model):
        """Test that place occupancy is computed."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100, sampling_interval=10)
        
        assert result.success
        occupancy = result.data['place_occupancy']
        
        assert 'p1' in occupancy
        assert 'p2' in occupancy
        assert isinstance(occupancy['p1'], float)
        assert occupancy['p1'] >= 0
    
    def test_cyclic_model_throughput(self, cyclic_model):
        """Test throughput on cyclic model."""
        analyzer = ThroughputAnalyzer(cyclic_model)
        result = analyzer.analyze(max_steps=1000)
        
        assert result.success
        
        # Both transitions should fire
        firing_counts = result.data['firing_counts']
        assert firing_counts['t1'] > 0
        assert firing_counts['t2'] > 0
        
        # System throughput should be positive
        assert result.data['throughput'] > 0
    
    def test_bottleneck_detection(self, cyclic_model):
        """Test bottleneck detection."""
        analyzer = ThroughputAnalyzer(cyclic_model)
        result = analyzer.analyze(max_steps=1000)
        
        assert result.success
        assert 'bottlenecks' in result.data
        assert isinstance(result.data['bottlenecks'], list)
    
    def test_utilization_metrics(self, simple_model):
        """Test utilization metrics."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        utilization = result.data['utilization']
        
        assert isinstance(utilization, dict)
        assert 'p1' in utilization
        assert 'p2' in utilization
        
        # Utilization should be between 0 and 1
        for value in utilization.values():
            assert 0.0 <= value <= 1.0
    
    def test_statistics_included(self, simple_model):
        """Test that statistics are included."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        stats = result.data['statistics']
        
        assert 'total_steps' in stats
        assert 'total_firings' in stats
        assert 'computation_time' in stats
        assert 'transitions_active' in stats
        assert 'transitions_total' in stats
        
        assert stats['total_steps'] > 0
        assert stats['transitions_total'] > 0
    
    def test_get_firing_rate_method(self, simple_model):
        """Test the get_firing_rate method."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        
        rate = analyzer.get_firing_rate('t1')
        assert isinstance(rate, float)
        assert rate >= 0.0
    
    def test_get_firing_rate_not_run(self, simple_model):
        """Test that get_firing_rate raises error if analyze not run."""
        analyzer = ThroughputAnalyzer(simple_model)
        
        with pytest.raises(RuntimeError):
            analyzer.get_firing_rate('t1')
    
    def test_get_bottlenecks_method(self, cyclic_model):
        """Test the get_bottlenecks method."""
        analyzer = ThroughputAnalyzer(cyclic_model)
        result = analyzer.analyze(max_steps=1000)
        
        assert result.success
        
        bottlenecks = analyzer.get_bottlenecks(threshold=0.1)
        assert isinstance(bottlenecks, list)
    
    def test_get_bottlenecks_not_run(self, simple_model):
        """Test that get_bottlenecks raises error if analyze not run."""
        analyzer = ThroughputAnalyzer(simple_model)
        
        with pytest.raises(RuntimeError):
            analyzer.get_bottlenecks()
    
    def test_max_steps_limit(self, cyclic_model):
        """Test that max_steps limit is respected."""
        analyzer = ThroughputAnalyzer(cyclic_model)
        result = analyzer.analyze(max_steps=50)
        
        assert result.success
        stats = result.data['statistics']
        assert stats['total_steps'] <= 50
    
    def test_custom_initial_marking(self, simple_model):
        """Test analysis with custom initial marking."""
        analyzer = ThroughputAnalyzer(simple_model)
        custom_initial = {'p1': 20, 'p2': 5}
        result = analyzer.analyze(initial_marking=custom_initial, max_steps=100)
        
        assert result.success
        # Should run with custom marking
        assert result.data['statistics']['total_steps'] > 0
    
    def test_sampling_interval(self, simple_model):
        """Test that sampling interval affects occupancy samples."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100, sampling_interval=10)
        
        assert result.success
        # Occupancy should be computed
        assert 'place_occupancy' in result.data
    
    def test_result_metadata(self, simple_model):
        """Test that result includes proper metadata."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        assert 'analyzer' in result.metadata
        assert result.metadata['analyzer'] == 'throughput'
        assert 'computation_time' in result.metadata
        assert 'total_steps' in result.metadata
    
    def test_summary_generation(self, simple_model):
        """Test that summary is generated."""
        analyzer = ThroughputAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        assert len(result.summary) > 0
        assert 'throughput' in result.summary.lower()
    
    def test_clear_cache(self, simple_model):
        """Test that cache is cleared properly."""
        analyzer = ThroughputAnalyzer(simple_model)
        result1 = analyzer.analyze(max_steps=100)
        
        assert result1.success
        assert len(analyzer._firing_counts) > 0
        
        analyzer.clear_cache()
        assert len(analyzer._firing_counts) == 0
        assert len(analyzer._token_flow) == 0
    
    def test_empty_model(self):
        """Test with model that has no transitions."""
        model = Mock()
        
        p1 = Mock()
        p1.tokens = 5
        model.places = {'p1': p1}
        model.transitions = {}
        model.arcs = {}
        
        analyzer = ThroughputAnalyzer(model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        # No transitions means no firings
        assert result.data['statistics']['total_firings'] == 0
    
    def test_deadlock_recovery(self):
        """Test that analyzer handles deadlock situations."""
        model = Mock()
        
        # Places with no initial tokens
        p1 = Mock()
        p1.tokens = 0
        p2 = Mock()
        p2.tokens = 0
        
        model.places = {'p1': p1, 'p2': p2}
        
        # Transition that can't fire
        t1 = Mock()
        model.transitions = {'t1': t1}
        
        arc1 = Mock()
        arc1.source = 'p1'
        arc1.target = 't1'
        arc1.weight = 1
        
        model.arcs = {'a1': arc1}
        
        analyzer = ThroughputAnalyzer(model)
        result = analyzer.analyze(max_steps=100)
        
        # Should handle deadlock gracefully
        assert result.success
        assert result.data['statistics']['total_firings'] == 0
    
    def test_warnings_on_limits(self, cyclic_model):
        """Test that warnings are generated when limits are reached."""
        analyzer = ThroughputAnalyzer(cyclic_model)
        result = analyzer.analyze(max_steps=10)
        
        assert result.success
        # May have warnings if limit reached
        if result.data['statistics']['total_steps'] >= 10:
            assert len(result.warnings) > 0
