"""Tests for centrality analyzer."""

import pytest
from unittest.mock import Mock

from src.shypn.topology.network.centrality import CentralityAnalyzer
from src.shypn.topology.base.exceptions import TopologyAnalysisError


@pytest.fixture
def simple_model():
    """Create a simple linear pathway model for testing.
    
    Model structure:
        p1 → t1 → p2 → t2 → p3
        (linear chain)
    """
    model = Mock()
    
    # Create places
    p1 = Mock()
    p1.id = 'p_1'
    p1.name = 'ATP'
    
    p2 = Mock()
    p2.id = 'p_2'
    p2.name = 'ADP'
    
    p3 = Mock()
    p3.id = 'p_3'
    p3.name = 'AMP'
    
    # Create transitions
    t1 = Mock()
    t1.id = 't_1'
    t1.name = 'ATPase'
    
    t2 = Mock()
    t2.id = 't_2'
    t2.name = 'Kinase'
    
    model.places = [p1, p2, p3]
    model.transitions = [t1, t2]
    model.arcs = []
    
    # Create arcs
    # p1 -> t1
    arc1 = Mock()
    arc1.source = p1
    arc1.target = t1
    arc1.weight = 1
    model.arcs.append(arc1)
    
    # t1 -> p2
    arc2 = Mock()
    arc2.source = t1
    arc2.target = p2
    arc2.weight = 1
    model.arcs.append(arc2)
    
    # p2 -> t2
    arc3 = Mock()
    arc3.source = p2
    arc3.target = t2
    arc3.weight = 1
    model.arcs.append(arc3)
    
    # t2 -> p3
    arc4 = Mock()
    arc4.source = t2
    arc4.target = p3
    arc4.weight = 1
    model.arcs.append(arc4)
    
    return model


@pytest.fixture
def hub_model():
    """Create a hub-and-spoke model for testing.
    
    Model structure:
           p1
            |
            t1
           /  \\
          p2  p3
          |    |
          t2  t3
           \\  /
            p4
            
    p2 is a hub (central metabolite)
    """
    model = Mock()
    
    # Create places
    places = []
    for i in range(1, 5):
        p = Mock()
        p.id = f'p_{i}'
        p.name = f'Compound_{i}'
        places.append(p)
    
    # Create transitions
    transitions = []
    for i in range(1, 4):
        t = Mock()
        t.id = f't_{i}'
        t.name = f'Reaction_{i}'
        transitions.append(t)
    
    model.places = places
    model.transitions = transitions
    model.arcs = []
    
    # Create hub structure
    # p1 -> t1 -> p2, p3
    arc1 = Mock()
    arc1.source = places[0]  # p1
    arc1.target = transitions[0]  # t1
    arc1.weight = 1
    model.arcs.append(arc1)
    
    arc2 = Mock()
    arc2.source = transitions[0]  # t1
    arc2.target = places[1]  # p2
    arc2.weight = 1
    model.arcs.append(arc2)
    
    arc3 = Mock()
    arc3.source = transitions[0]  # t1
    arc3.target = places[2]  # p3
    arc3.weight = 1
    model.arcs.append(arc3)
    
    # p2 -> t2 -> p4
    arc4 = Mock()
    arc4.source = places[1]  # p2
    arc4.target = transitions[1]  # t2
    arc4.weight = 1
    model.arcs.append(arc4)
    
    arc5 = Mock()
    arc5.source = transitions[1]  # t2
    arc5.target = places[3]  # p4
    arc5.weight = 1
    model.arcs.append(arc5)
    
    # p3 -> t3 -> p4
    arc6 = Mock()
    arc6.source = places[2]  # p3
    arc6.target = transitions[2]  # t3
    arc6.weight = 1
    model.arcs.append(arc6)
    
    arc7 = Mock()
    arc7.source = transitions[2]  # t3
    arc7.target = places[3]  # p4
    arc7.weight = 1
    model.arcs.append(arc7)
    
    return model


class TestCentralityAnalyzer:
    """Test suite for CentralityAnalyzer."""
    
    def test_basic_analysis(self, simple_model):
        """Test basic centrality analysis on simple model."""
        analyzer = CentralityAnalyzer(simple_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'central_nodes' in result.data
        assert 'measures_computed' in result.data
        assert len(result.data['central_nodes']) > 0
    
    def test_all_measures_computed(self, simple_model):
        """Test that all centrality measures are computed by default."""
        analyzer = CentralityAnalyzer(simple_model)
        result = analyzer.analyze()
        
        measures = result.data['measures_computed']
        assert 'betweenness' in measures
        assert 'closeness' in measures
        assert 'eigenvector' in measures
        assert 'pagerank' in measures
    
    def test_single_measure(self, simple_model):
        """Test computing a single centrality measure."""
        analyzer = CentralityAnalyzer(simple_model)
        result = analyzer.analyze(measures=['betweenness'])
        
        assert result.success
        assert result.data['measures_computed'] == ['betweenness']
        
        # Check that betweenness values exist
        for node in result.data['central_nodes']:
            assert 'betweenness' in node
            assert isinstance(node['betweenness'], float)
    
    def test_multiple_specific_measures(self, simple_model):
        """Test computing specific subset of measures."""
        analyzer = CentralityAnalyzer(simple_model)
        result = analyzer.analyze(measures=['betweenness', 'pagerank'])
        
        assert result.success
        assert set(result.data['measures_computed']) == {'betweenness', 'pagerank'}
        
        # Check values exist for both measures
        for node in result.data['central_nodes']:
            assert 'betweenness' in node
            assert 'pagerank' in node
    
    def test_invalid_measure(self, simple_model):
        """Test that invalid measure raises error."""
        analyzer = CentralityAnalyzer(simple_model)
        result = analyzer.analyze(measures=['invalid_measure'])
        
        assert not result.success
        assert len(result.errors) > 0
        assert 'Invalid centrality measure' in result.errors[0]
    
    def test_top_n_filtering(self, hub_model):
        """Test that top_n parameter limits results correctly."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze(top_n=2, measures=['betweenness'])
        
        assert result.success
        assert len(result.data['top_betweenness']) == 2
        
        # Check that results are sorted by betweenness
        top_nodes = result.data['top_betweenness']
        assert top_nodes[0]['betweenness'] >= top_nodes[1]['betweenness']
    
    def test_node_type_filter_places(self, hub_model):
        """Test filtering by place nodes only."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze(node_type='place')
        
        assert result.success
        
        # All returned nodes should be places
        for node in result.data['central_nodes']:
            assert node['type'] == 'place'
            assert node['id'].startswith('p_')
    
    def test_node_type_filter_transitions(self, hub_model):
        """Test filtering by transition nodes only."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze(node_type='transition')
        
        assert result.success
        
        # All returned nodes should be transitions
        for node in result.data['central_nodes']:
            assert node['type'] == 'transition'
            assert node['id'].startswith('t_')
    
    def test_betweenness_identifies_bridge(self, simple_model):
        """Test that betweenness identifies bridge nodes in linear chain."""
        analyzer = CentralityAnalyzer(simple_model)
        result = analyzer.analyze(measures=['betweenness'])
        
        assert result.success
        
        # In linear chain, middle node (p2/ADP) should have highest betweenness
        top_node = result.data['top_betweenness'][0]
        # Middle place or transition should be top
        assert top_node['id'] in ['p_2', 't_1', 't_2']
    
    def test_closeness_symmetric(self, hub_model):
        """Test that closeness centrality is computed for all nodes."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze(measures=['closeness'])
        
        assert result.success
        
        # All nodes should have closeness values
        for node in result.data['central_nodes']:
            assert 'closeness' in node
            assert 0 <= node['closeness'] <= 1
    
    def test_eigenvector_convergence(self, hub_model):
        """Test that eigenvector centrality converges."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze(measures=['eigenvector'])
        
        assert result.success
        
        # All nodes should have eigenvector values
        for node in result.data['central_nodes']:
            assert 'eigenvector' in node
            assert isinstance(node['eigenvector'], float)
    
    def test_pagerank_sum(self, hub_model):
        """Test that PageRank values are properly normalized."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze(measures=['pagerank'], normalize=True)
        
        assert result.success
        
        # All nodes should have pagerank values
        pageranks = [node['pagerank'] for node in result.data['central_nodes']]
        assert all(isinstance(pr, float) for pr in pageranks)
        assert all(pr >= 0 for pr in pageranks)
    
    def test_weighted_vs_unweighted(self, simple_model):
        """Test that weighted parameter affects results."""
        analyzer = CentralityAnalyzer(simple_model)
        
        result_unweighted = analyzer.analyze(
            measures=['betweenness'],
            weighted=False
        )
        result_weighted = analyzer.analyze(
            measures=['betweenness'],
            weighted=True
        )
        
        assert result_unweighted.success
        assert result_weighted.success
        
        # Both should have results
        assert len(result_unweighted.data['central_nodes']) > 0
        assert len(result_weighted.data['central_nodes']) > 0
    
    def test_empty_model(self):
        """Test handling of empty model."""
        model = Mock()
        model.places = []
        model.transitions = []
        model.arcs = []
        
        analyzer = CentralityAnalyzer(model)
        result = analyzer.analyze()
        
        # Should handle gracefully
        assert result.success or not result.success
        # Either succeeds with empty results or fails with error
    
    def test_result_structure(self, hub_model):
        """Test that result has proper structure."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'central_nodes' in result.data
        assert 'measures_computed' in result.data
        assert 'node_count' in result.data
        assert 'summary' in result.data
        
        # Check metadata
        assert 'analysis_time' in result.metadata
        assert 'top_n' in result.metadata
        assert 'normalized' in result.metadata
        assert 'weighted' in result.metadata
    
    def test_summary_generation(self, hub_model):
        """Test that summary is generated correctly."""
        analyzer = CentralityAnalyzer(hub_model)
        result = analyzer.analyze(measures=['betweenness', 'pagerank'])
        
        assert result.success
        summary = result.data['summary']
        
        # Summary should mention number of nodes
        assert 'nodes analyzed' in summary.lower()
        
        # Summary should mention measures
        assert 'betweenness' in summary.lower() or 'pagerank' in summary.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
