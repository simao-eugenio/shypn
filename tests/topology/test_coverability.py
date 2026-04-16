"""Tests for coverability analyzer."""

import pytest
from unittest.mock import Mock
from shypn.topology.behavioral.coverability import (
    CoverabilityAnalyzer,
    OMEGA,
    CoverabilityNode
)


class TestCoverabilityAnalyzer:
    """Test suite for CoverabilityAnalyzer."""
    
    @pytest.fixture
    def bounded_model(self):
        """Create a simple bounded Petri net."""
        model = Mock()
        
        # Places: p1, p2
        p1 = Mock()
        p1.tokens = 1
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
    def unbounded_model(self):
        """Create an unbounded Petri net (tokens increase indefinitely)."""
        model = Mock()
        
        # Places: p1, p2
        p1 = Mock()
        p1.tokens = 1
        p2 = Mock()
        p2.tokens = 0
        
        model.places = {'p1': p1, 'p2': p2}
        
        # Transition: t1 (p1 -> p1 + p2, creates more tokens)
        t1 = Mock()
        model.transitions = {'t1': t1}
        
        # Arcs: consume 1 from p1, produce 2 to p1 and 1 to p2
        arc1 = Mock()
        arc1.source = 'p1'
        arc1.target = 't1'
        arc1.weight = 1
        
        arc2 = Mock()
        arc2.source = 't1'
        arc2.target = 'p1'
        arc2.weight = 2  # Creates more tokens!
        
        arc3 = Mock()
        arc3.source = 't1'
        arc3.target = 'p2'
        arc3.weight = 1
        
        model.arcs = {'a1': arc1, 'a2': arc2, 'a3': arc3}
        
        return model
    
    def test_basic_analysis(self, bounded_model):
        """Test basic coverability analysis."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'nodes' in result.data
        assert 'edges' in result.data
        assert 'unbounded_places' in result.data
        assert 'statistics' in result.data
    
    def test_bounded_net_detected(self, bounded_model):
        """Test that bounded nets are correctly identified."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        assert result.data['is_bounded'] is True
        assert len(result.data['unbounded_places']) == 0
        assert 'bounded' in result.summary.lower()
    
    def test_unbounded_net_detected(self, unbounded_model):
        """Test that unbounded nets are correctly identified."""
        analyzer = CoverabilityAnalyzer(unbounded_model)
        result = analyzer.analyze(max_nodes=50, max_omega=5)
        
        assert result.success
        assert result.data['is_bounded'] is False
        assert len(result.data['unbounded_places']) > 0
        assert 'unbounded' in result.summary.lower()
    
    def test_omega_introduction(self, unbounded_model):
        """Test that omega is introduced for unbounded places."""
        analyzer = CoverabilityAnalyzer(unbounded_model)
        result = analyzer.analyze(max_nodes=20, max_omega=5)
        
        assert result.success
        
        # Check that some node has omega
        has_omega = False
        for node in result.data['nodes']:
            marking = node['marking']
            for place_id, tokens in marking.items():
                if tokens == OMEGA:
                    has_omega = True
                    break
        
        assert has_omega, "Omega should be introduced in unbounded net"
    
    def test_nodes_structure(self, bounded_model):
        """Test that nodes have correct structure."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        assert len(result.data['nodes']) > 0
        
        node = result.data['nodes'][0]
        assert 'id' in node
        assert 'marking' in node
        assert 'is_duplicate' in node
        assert isinstance(node['marking'], dict)
    
    def test_edges_structure(self, bounded_model):
        """Test that edges have correct structure."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        
        if len(result.data['edges']) > 0:
            edge = result.data['edges'][0]
            assert 'from' in edge
            assert 'to' in edge
            assert 'transition' in edge
    
    def test_statistics_computed(self, bounded_model):
        """Test that statistics are computed."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        stats = result.data['statistics']
        
        assert 'total_nodes' in stats
        assert 'total_edges' in stats
        assert 'omega_occurrences' in stats
        assert 'max_depth' in stats
        assert stats['total_nodes'] > 0
    
    def test_dead_nodes_detection(self, bounded_model):
        """Test detection of dead markings."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'dead_nodes' in result.data
        assert isinstance(result.data['dead_nodes'], list)
    
    def test_is_coverable_method(self, bounded_model):
        """Test the is_coverable method."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        
        # Initial marking should be coverable
        initial = {'p1': 1, 'p2': 0}
        assert analyzer.is_coverable(initial)
        
        # Final marking should be coverable
        final = {'p1': 0, 'p2': 1}
        assert analyzer.is_coverable(final)
    
    def test_is_coverable_not_run(self, bounded_model):
        """Test that is_coverable raises error if analyze not run."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        
        with pytest.raises(RuntimeError):
            analyzer.is_coverable({'p1': 1, 'p2': 0})
    
    def test_get_unbounded_places_method(self, unbounded_model):
        """Test the get_unbounded_places method."""
        analyzer = CoverabilityAnalyzer(unbounded_model)
        result = analyzer.analyze(max_nodes=20, max_omega=5)
        
        assert result.success
        unbounded = analyzer.get_unbounded_places()
        
        assert isinstance(unbounded, list)
        assert len(unbounded) > 0
    
    def test_get_unbounded_places_not_run(self, bounded_model):
        """Test that get_unbounded_places raises error if analyze not run."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        
        with pytest.raises(RuntimeError):
            analyzer.get_unbounded_places()
    
    def test_max_nodes_limit(self, unbounded_model):
        """Test that max_nodes limit is respected."""
        analyzer = CoverabilityAnalyzer(unbounded_model)
        result = analyzer.analyze(max_nodes=10, max_omega=5)
        
        assert result.success
        assert len(result.data['nodes']) <= 10
        # Omega introduction makes the graph finite, so it may complete
        # even with unbounded net. Just check that limit is respected.
    
    def test_custom_initial_marking(self, bounded_model):
        """Test analysis with custom initial marking."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        custom_initial = {'p1': 2, 'p2': 1}
        result = analyzer.analyze(initial_marking=custom_initial)
        
        assert result.success
        # First node should have custom marking
        first_node = result.data['nodes'][0]
        assert first_node['marking']['p1'] == 2
        assert first_node['marking']['p2'] == 1
    
    def test_result_metadata(self, bounded_model):
        """Test that result includes proper metadata."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'analyzer' in result.metadata
        assert result.metadata['analyzer'] == 'coverability'
        assert 'computation_time' in result.metadata
        assert 'nodes_explored' in result.metadata
        assert 'edges_found' in result.metadata
    
    def test_summary_generation(self, bounded_model):
        """Test that summary is generated."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result = analyzer.analyze()
        
        assert result.success
        assert len(result.summary) > 0
        assert 'coverability' in result.summary.lower()
    
    def test_clear_cache(self, bounded_model):
        """Test that cache is cleared properly."""
        analyzer = CoverabilityAnalyzer(bounded_model)
        result1 = analyzer.analyze()
        
        assert result1.success
        nodes_before = len(analyzer._nodes)
        assert nodes_before > 0
        
        analyzer.clear_cache()
        assert len(analyzer._nodes) == 0
        assert len(analyzer._edges) == 0
        assert analyzer._node_counter == 0
    
    def test_empty_model(self):
        """Test with empty model."""
        model = Mock()
        model.places = {}
        model.transitions = {}
        model.arcs = {}
        
        analyzer = CoverabilityAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        assert len(result.data['nodes']) == 1  # Only initial marking
        assert len(result.data['edges']) == 0
    
    def test_coverability_node_equality(self):
        """Test CoverabilityNode equality and hashing."""
        node1 = CoverabilityNode((1, 2, 3), 0)
        node2 = CoverabilityNode((1, 2, 3), 1)
        node3 = CoverabilityNode((1, 2, 4), 2)
        
        # Same marking should be equal
        assert node1 == node2
        assert hash(node1) == hash(node2)
        
        # Different marking should not be equal
        assert node1 != node3
        assert hash(node1) != hash(node3)
    
    def test_omega_constant(self):
        """Test that OMEGA constant is properly defined."""
        assert OMEGA == float('inf')
        assert OMEGA > 1000000
        assert OMEGA + 1 == OMEGA  # Infinity property
    
    def test_self_loop_handling(self):
        """Test handling of self-loops (transitions that return to same marking)."""
        model = Mock()
        
        # Single place with self-loop transition
        p1 = Mock()
        p1.tokens = 1
        model.places = {'p1': p1}
        
        t1 = Mock()
        model.transitions = {'t1': t1}
        
        # Self-loop: p1 -> t1 -> p1
        arc1 = Mock()
        arc1.source = 'p1'
        arc1.target = 't1'
        arc1.weight = 1
        
        arc2 = Mock()
        arc2.source = 't1'
        arc2.target = 'p1'
        arc2.weight = 1
        
        model.arcs = {'a1': arc1, 'a2': arc2}
        
        analyzer = CoverabilityAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        # Should detect the duplicate marking (self-loop back to same state)
        assert len(result.data['nodes']) == 1  # Only initial marking
        assert len(result.data['edges']) == 1  # Edge back to itself
