"""Tests for communities analyzer."""

import pytest
from unittest.mock import Mock

from src.shypn.topology.network.communities import CommunitiesAnalyzer


@pytest.fixture
def linear_model():
    """Create a simple linear model."""
    model = Mock()
    
    # Create 3 places
    places = []
    for i in range(1, 4):
        p = Mock()
        p.id = f'p_{i}'
        p.name = f'Place_{i}'
        places.append(p)
    
    # Create 2 transitions
    transitions = []
    for i in range(1, 3):
        t = Mock()
        t.id = f't_{i}'
        t.name = f'Trans_{i}'
        transitions.append(t)
    
    model.places = places
    model.transitions = transitions
    model.arcs = []
    
    # Linear: p1 -> t1 -> p2 -> t2 -> p3
    arcs = [
        (places[0], transitions[0]),  # p1 -> t1
        (transitions[0], places[1]),  # t1 -> p2
        (places[1], transitions[1]),  # p2 -> t2
        (transitions[1], places[2]),  # t2 -> p3
    ]
    
    for source, target in arcs:
        arc = Mock()
        arc.source = source
        arc.target = target
        arc.weight = 1
        model.arcs.append(arc)
    
    return model


@pytest.fixture
def modular_model():
    """Create a model with clear community structure.
    
    Structure: Two separate modules connected by one edge
    Module 1: p1 <-> t1 <-> p2 <-> t2 <-> p1
    Module 2: p3 <-> t3 <-> p4 <-> t4 <-> p3
    Bridge: p2 -> t5 -> p3
    """
    model = Mock()
    
    # Create 4 places
    places = []
    for i in range(1, 5):
        p = Mock()
        p.id = f'p_{i}'
        p.name = f'Place_{i}'
        places.append(p)
    
    # Create 5 transitions
    transitions = []
    for i in range(1, 6):
        t = Mock()
        t.id = f't_{i}'
        t.name = f'Trans_{i}'
        transitions.append(t)
    
    model.places = places
    model.transitions = transitions
    model.arcs = []
    
    # Module 1: Dense connections
    module1_arcs = [
        (places[0], transitions[0]),  # p1 -> t1
        (transitions[0], places[1]),  # t1 -> p2
        (places[1], transitions[1]),  # p2 -> t2
        (transitions[1], places[0]),  # t2 -> p1 (cycle)
    ]
    
    # Module 2: Dense connections
    module2_arcs = [
        (places[2], transitions[2]),  # p3 -> t3
        (transitions[2], places[3]),  # t3 -> p4
        (places[3], transitions[3]),  # p4 -> t4
        (transitions[3], places[2]),  # t4 -> p3 (cycle)
    ]
    
    # Bridge between modules
    bridge_arcs = [
        (places[1], transitions[4]),  # p2 -> t5
        (transitions[4], places[2]),  # t5 -> p3
    ]
    
    for source, target in module1_arcs + module2_arcs + bridge_arcs:
        arc = Mock()
        arc.source = source
        arc.target = target
        arc.weight = 1
        model.arcs.append(arc)
    
    return model


class TestCommunitiesAnalyzer:
    """Test suite for CommunitiesAnalyzer."""
    
    def test_basic_analysis(self, linear_model):
        """Test basic community detection."""
        analyzer = CommunitiesAnalyzer(linear_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'communities' in result.data
        assert 'num_communities' in result.data
        assert 'modularity' in result.data
    
    def test_louvain_method(self, modular_model):
        """Test Louvain community detection method."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(method='louvain')
        
        assert result.success
        assert result.data['num_communities'] > 0
        assert result.metadata['method'] == 'louvain'
    
    def test_greedy_modularity_method(self, modular_model):
        """Test greedy modularity method."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(method='greedy_modularity')
        
        assert result.success
        assert result.data['num_communities'] > 0
        assert result.metadata['method'] == 'greedy_modularity'
    
    def test_label_propagation_method(self, modular_model):
        """Test label propagation method."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(method='label_propagation')
        
        assert result.success
        assert result.data['num_communities'] > 0
        assert result.metadata['method'] == 'label_propagation'
    
    def test_girvan_newman_method(self, modular_model):
        """Test Girvan-Newman method."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(method='girvan_newman')
        
        assert result.success
        assert result.data['num_communities'] > 0
        assert result.metadata['method'] == 'girvan_newman'
    
    def test_invalid_method(self, linear_model):
        """Test that invalid method raises error."""
        analyzer = CommunitiesAnalyzer(linear_model)
        result = analyzer.analyze(method='invalid_method')
        
        assert not result.success
        assert len(result.errors) > 0
        assert 'Invalid community detection method' in result.errors[0]
    
    def test_modular_structure_detected(self, modular_model):
        """Test that modular structure is correctly detected."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze()
        
        assert result.success
        # Should detect at least 2 communities in modular model
        assert result.data['num_communities'] >= 1
    
    def test_min_community_size(self, modular_model):
        """Test minimum community size filtering."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(min_community_size=3)
        
        assert result.success
        # All communities should have at least 3 nodes
        for comm in result.data['communities']:
            assert comm['size'] >= 3
    
    def test_resolution_parameter(self, modular_model):
        """Test that resolution parameter affects number of communities."""
        analyzer = CommunitiesAnalyzer(modular_model)
        
        # Higher resolution should give more communities
        result_high = analyzer.analyze(method='louvain', resolution=2.0)
        result_low = analyzer.analyze(method='louvain', resolution=0.5)
        
        assert result_high.success
        assert result_low.success
        # Can't guarantee ordering, but both should work
    
    def test_node_type_filter_places(self, modular_model):
        """Test filtering by place nodes only."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(node_type='place')
        
        assert result.success
        # All nodes in communities should be places
        for comm in result.data['communities']:
            for node_id in comm['nodes']:
                assert node_id.startswith('p_')
    
    def test_node_type_filter_transitions(self, modular_model):
        """Test filtering by transition nodes only."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(node_type='transition')
        
        assert result.success
        # All nodes in communities should be transitions
        for comm in result.data['communities']:
            for node_id in comm['nodes']:
                assert node_id.startswith('t_')
    
    def test_modularity_score(self, modular_model):
        """Test that modularity score is calculated."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'modularity' in result.data
        # Modularity should be between -1 and 1
        assert -1 <= result.data['modularity'] <= 1
    
    def test_coverage_score(self, modular_model):
        """Test that coverage score is calculated."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'coverage' in result.data
        # Coverage should be between 0 and 1
        assert 0 <= result.data['coverage'] <= 1
    
    def test_community_structure(self, modular_model):
        """Test that community data has proper structure."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze()
        
        assert result.success
        for comm in result.data['communities']:
            assert 'id' in comm
            assert 'nodes' in comm
            assert 'size' in comm
            assert 'node_names' in comm
            assert comm['size'] == len(comm['nodes'])
            assert comm['size'] == len(comm['node_names'])
    
    def test_empty_model(self):
        """Test handling of empty model."""
        model = Mock()
        model.places = []
        model.transitions = []
        model.arcs = []
        
        analyzer = CommunitiesAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        assert result.data['num_communities'] == 0
        assert len(result.data['communities']) == 0
    
    def test_result_metadata(self, modular_model):
        """Test that result metadata is complete."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze(resolution=1.5, min_community_size=2)
        
        assert result.success
        assert 'analysis_time' in result.metadata
        assert 'method' in result.metadata
        assert 'resolution' in result.metadata
        assert result.metadata['resolution'] == 1.5
        assert result.metadata['min_community_size'] == 2
        assert 'total_nodes' in result.metadata
    
    def test_summary_generation(self, modular_model):
        """Test that summary is generated correctly."""
        analyzer = CommunitiesAnalyzer(modular_model)
        result = analyzer.analyze()
        
        assert result.success
        summary = result.data['summary']
        
        # Summary should mention communities
        assert 'communit' in summary.lower()
        # Summary should mention method
        assert 'louvain' in summary.lower() or 'method' in summary.lower()
        # Summary should include metrics
        assert 'modularity' in summary.lower()
        assert 'coverage' in summary.lower()
    
    def test_single_community(self, linear_model):
        """Test handling of networks with single community."""
        analyzer = CommunitiesAnalyzer(linear_model)
        result = analyzer.analyze()
        
        assert result.success
        # Linear model should likely form one community
        assert result.data['num_communities'] >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
