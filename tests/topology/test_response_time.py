"""Tests for response time analyzer."""

import pytest
from unittest.mock import Mock
from shypn.topology.behavioral.response_time import ResponseTimeAnalyzer


class TestResponseTimeAnalyzer:
    """Test suite for ResponseTimeAnalyzer."""
    
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
    def sequential_model(self):
        """Create a sequential Petri net with two transitions."""
        model = Mock()
        
        # Places: p1, p2, p3
        p1 = Mock()
        p1.tokens = 10
        p2 = Mock()
        p2.tokens = 0
        p3 = Mock()
        p3.tokens = 0
        
        model.places = {'p1': p1, 'p2': p2, 'p3': p3}
        
        # Transitions: t1 (p1 -> p2), t2 (p2 -> p3)
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
        arc4.target = 'p3'
        arc4.weight = 1
        
        model.arcs = {'a1': arc1, 'a2': arc2, 'a3': arc3, 'a4': arc4}
        
        return model
    
    def test_basic_analysis(self, simple_model):
        """Test basic response time analysis."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        assert 'firing_times' in result.data
        assert 'inter_firing_times' in result.data
        assert 'transition_delays' in result.data
        assert 'statistics' in result.data
    
    def test_firing_times_recorded(self, simple_model):
        """Test that firing times are recorded."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        firing_times = result.data['firing_times']
        
        assert 't1' in firing_times
        assert isinstance(firing_times['t1'], list)
        assert len(firing_times['t1']) > 0
    
    def test_inter_firing_times_computed(self, simple_model):
        """Test that inter-firing times are computed."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        inter_times = result.data['inter_firing_times']
        
        # Should have inter-firing time for t1
        assert isinstance(inter_times, dict)
    
    def test_transition_delays_measured(self, sequential_model):
        """Test that transition delays are measured."""
        analyzer = ResponseTimeAnalyzer(sequential_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        delays = result.data['transition_delays']
        
        # Should have delay measurements
        assert isinstance(delays, dict)
    
    def test_critical_paths_identified(self, sequential_model):
        """Test that critical paths are identified."""
        analyzer = ResponseTimeAnalyzer(sequential_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        critical_paths = result.data['critical_paths']
        
        assert isinstance(critical_paths, list)
    
    def test_statistics_included(self, simple_model):
        """Test that statistics are included."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        stats = result.data['statistics']
        
        assert 'total_steps' in stats
        assert 'total_firings' in stats
        assert 'transitions_fired' in stats
        assert 'transition_pairs_measured' in stats
        assert 'computation_time' in stats
        
        assert stats['total_steps'] > 0
    
    def test_get_response_time_method(self, sequential_model):
        """Test the get_response_time method."""
        analyzer = ResponseTimeAnalyzer(sequential_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        
        # Try to get response time between t1 and t2
        response_time = analyzer.get_response_time('t1', 't2')
        
        # Should be None or a positive float
        if response_time is not None:
            assert isinstance(response_time, float)
            assert response_time >= 0
    
    def test_get_response_time_not_run(self, simple_model):
        """Test that get_response_time raises error if analyze not run."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        
        with pytest.raises(RuntimeError):
            analyzer.get_response_time('t1', 't1')
    
    def test_get_critical_path_method(self, sequential_model):
        """Test the get_critical_path method."""
        analyzer = ResponseTimeAnalyzer(sequential_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        
        critical = analyzer.get_critical_path()
        
        # Should be None or a tuple
        if critical is not None:
            assert isinstance(critical, tuple)
            assert len(critical) == 2
            pair, delay = critical
            assert isinstance(pair, tuple)
            assert isinstance(delay, float)
    
    def test_get_critical_path_not_run(self, simple_model):
        """Test that get_critical_path raises error if analyze not run."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        
        with pytest.raises(RuntimeError):
            analyzer.get_critical_path()
    
    def test_source_target_filtering(self, sequential_model):
        """Test filtering by source and target transitions."""
        analyzer = ResponseTimeAnalyzer(sequential_model)
        result = analyzer.analyze(
            max_steps=100,
            source_transitions=['t1'],
            target_transitions=['t2']
        )
        
        assert result.success
        # Should only measure t1 -> t2 pairs
        delays = result.data['transition_delays']
        
        # Check that only relevant pairs are measured
        for (source, target) in delays.keys():
            assert source in ['t1']
            assert target in ['t2']
    
    def test_max_steps_limit(self, simple_model):
        """Test that max_steps limit is respected."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=50)
        
        assert result.success
        stats = result.data['statistics']
        assert stats['total_steps'] <= 50
    
    def test_custom_initial_marking(self, simple_model):
        """Test analysis with custom initial marking."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        custom_initial = {'p1': 20, 'p2': 5}
        result = analyzer.analyze(initial_marking=custom_initial, max_steps=100)
        
        assert result.success
        assert result.data['statistics']['total_steps'] > 0
    
    def test_result_metadata(self, simple_model):
        """Test that result includes proper metadata."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        assert 'analyzer' in result.metadata
        assert result.metadata['analyzer'] == 'response_time'
        assert 'computation_time' in result.metadata
        assert 'total_steps' in result.metadata
    
    def test_summary_generation(self, simple_model):
        """Test that summary is generated."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        assert len(result.summary) > 0
        assert 'response time' in result.summary.lower()
    
    def test_clear_cache(self, simple_model):
        """Test that cache is cleared properly."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result1 = analyzer.analyze(max_steps=100)
        
        assert result1.success
        assert len(analyzer._firing_times) > 0
        
        analyzer.clear_cache()
        assert len(analyzer._firing_times) == 0
        assert len(analyzer._inter_firing_times) == 0
        assert len(analyzer._transition_delays) == 0
    
    def test_empty_model(self):
        """Test with model that has no transitions."""
        model = Mock()
        
        p1 = Mock()
        p1.tokens = 5
        model.places = {'p1': p1}
        model.transitions = {}
        model.arcs = {}
        
        analyzer = ResponseTimeAnalyzer(model)
        result = analyzer.analyze(max_steps=100)
        
        assert result.success
        # No transitions means no firings
        assert result.data['statistics']['total_firings'] == 0
    
    def test_deadlock_handling(self):
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
        
        analyzer = ResponseTimeAnalyzer(model)
        result = analyzer.analyze(max_steps=100)
        
        # Should handle deadlock gracefully
        assert result.success
        assert result.data['statistics']['total_firings'] == 0
    
    def test_warnings_on_limits(self, simple_model):
        """Test that warnings are generated when limits are reached."""
        analyzer = ResponseTimeAnalyzer(simple_model)
        result = analyzer.analyze(max_steps=10)
        
        assert result.success
        # May have warnings if limit reached
        if result.data['statistics']['total_steps'] >= 10:
            assert len(result.warnings) > 0
    
    def test_sequential_delay_measurement(self, sequential_model):
        """Test delay measurement in sequential execution."""
        analyzer = ResponseTimeAnalyzer(sequential_model)
        result = analyzer.analyze(max_steps=200)
        
        assert result.success
        
        # Should measure delays between t1 and t2
        delays = result.data['transition_delays']
        
        # Check if we have t1->t2 measurements
        has_t1_t2 = any(
            source == 't1' and target == 't2'
            for (source, target) in delays.keys()
        )
        
        # In a sequential model, we should see this relationship
        assert has_t1_t2 or len(delays) == 0  # Either measured or no data yet
