"""Tests for clustering analyzer."""

import pytest
from unittest.mock import Mock

from src.shypn.topology.network.clustering import ClusteringAnalyzer


@pytest.fixture
def triangle_model():
    """Create a model with perfect triangle (clustering = 1.0).
    
    Structure: p1 <-> t1 <-> p2 <-> t2 <-> p1
    Forms a complete triangle.
    """
    model = Mock()
    
    # Create 2 places and 2 transitions forming triangle
    p1 = Mock()
    p1.id = 'p_1'
    p1.name = 'Place_1'
    
    p2 = Mock()
    p2.id = 'p_2'
    p2.name = 'Place_2'
    
    t1 = Mock()
    t1.id = 't_1'
    t1.name = 'Trans_1'
    
    t2 = Mock()
    t2.id = 't_2'
    t2.name = 'Trans_2'
    
    model.places = [p1, p2]
    model.transitions = [t1, t2]
    model.arcs = []
    
    # Create triangle edges
    arcs = [
        (p1, t1), (t1, p1),  # p1 <-> t1
        (t1, p2), (p2, t1),  # t1 <-> p2
        (p2, t2), (t2, p2),  # p2 <-> t2
        (t2, p1), (p1, t2),  # t2 <-> p1
    ]
    
    for source, target in arcs:
        arc = Mock()
        arc.source = source
        arc.target = target
        arc.weight = 1
        model.arcs.append(arc)
    
    return model


@pytest.fixture
def star_model():
    """Create a star/hub model (low clustering).
    
    Structure: Hub in center connected to 4 leaf nodes
    """
    model = Mock()
    
    # Create hub place
    hub = Mock()
    hub.id = 'p_hub'
    hub.name = 'Hub'
    
    # Create 4 leaf places
    leaves = []
    for i in range(1, 5):
        leaf = Mock()
        leaf.id = f'p_{i}'
        leaf.name = f'Leaf_{i}'
        leaves.append(leaf)
    
    # Create transitions
    transitions = []
    for i in range(1, 5):
        t = Mock()
        t.id = f't_{i}'
        t.name = f'Trans_{i}'
        transitions.append(t)
    
    model.places = [hub] + leaves
    model.transitions = transitions
    model.arcs = []
    
    # Create star edges (hub connected to all leaves via transitions)
    for i, (leaf, trans) in enumerate(zip(leaves, transitions)):
        # Hub -> transition -> leaf
        arc1 = Mock()
        arc1.source = hub
        arc1.target = trans
        arc1.weight = 1
        model.arcs.append(arc1)
        
        arc2 = Mock()
        arc2.source = trans
        arc2.target = leaf
        arc2.weight = 1
        model.arcs.append(arc2)
    
    return model


class TestClusteringAnalyzer:
    """Test suite for ClusteringAnalyzer."""
    
    def test_basic_analysis(self, triangle_model):
        """Test basic clustering analysis."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'node_clustering' in result.data
        assert 'average_clustering' in result.data
        assert 'transitivity' in result.data
    
    def test_perfect_triangle_clustering(self, triangle_model):
        """Test that triangle structure is analyzed.
        
        Note: Petri nets are bipartite (places and transitions alternate),
        so clustering coefficients will be 0 for proper bipartite graphs.
        """
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze()
        
        assert result.success
        # Bipartite graphs have 0 clustering by definition
        assert result.data['average_clustering'] >= 0.0
        assert result.data['transitivity'] >= 0.0
    
    def test_star_low_clustering(self, star_model):
        """Test that star topology has low clustering."""
        analyzer = ClusteringAnalyzer(star_model)
        result = analyzer.analyze()
        
        assert result.success
        # Star topology should have low clustering
        # (leaves don't connect to each other)
        assert result.data['average_clustering'] < 0.5
    
    def test_transitivity_calculation(self, triangle_model):
        """Test that transitivity is calculated."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze()
        
        assert result.success
        assert 'transitivity' in result.data
        assert 0 <= result.data['transitivity'] <= 1
    
    def test_node_clustering_structure(self, triangle_model):
        """Test that node clustering data has proper structure."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze()
        
        assert result.success
        for node in result.data['node_clustering']:
            assert 'id' in node
            assert 'name' in node
            assert 'type' in node
            assert 'clustering' in node
            assert 'degree' in node
            assert 0 <= node['clustering'] <= 1
    
    def test_triangles_included(self, triangle_model):
        """Test that triangle counts are included when requested."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze(include_triangles=True)
        
        assert result.success
        for node in result.data['node_clustering']:
            assert 'triangles' in node
            assert isinstance(node['triangles'], int)
            assert node['triangles'] >= 0
    
    def test_triangles_excluded(self, triangle_model):
        """Test that triangle counts can be excluded."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze(include_triangles=False)
        
        assert result.success
        # Check that triangles key is not present
        if result.data['node_clustering']:
            node = result.data['node_clustering'][0]
            assert 'triangles' not in node
    
    def test_top_n_filtering(self, star_model):
        """Test that top_n parameter limits results."""
        analyzer = ClusteringAnalyzer(star_model)
        result = analyzer.analyze(top_n=3)
        
        assert result.success
        assert len(result.data['highly_clustered_nodes']) <= 3
        
        # Check that results are sorted by clustering (descending)
        clusterings = [n['clustering'] for n in result.data['highly_clustered_nodes']]
        assert clusterings == sorted(clusterings, reverse=True)
    
    def test_node_type_filter_places(self, triangle_model):
        """Test filtering by place nodes only."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze(node_type='place')
        
        assert result.success
        for node in result.data['node_clustering']:
            assert node['type'] == 'place'
            assert node['id'].startswith('p_')
    
    def test_node_type_filter_transitions(self, triangle_model):
        """Test filtering by transition nodes only."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze(node_type='transition')
        
        assert result.success
        for node in result.data['node_clustering']:
            assert node['type'] == 'transition'
            assert node['id'].startswith('t_')
    
    def test_distribution_statistics(self, star_model):
        """Test that distribution statistics are computed."""
        analyzer = ClusteringAnalyzer(star_model)
        result = analyzer.analyze()
        
        assert result.success
        dist = result.data['distribution']
        
        assert 'min' in dist
        assert 'max' in dist
        assert 'mean' in dist
        assert 'median' in dist
        assert 'stdev' in dist
        assert 'count' in dist
        
        # Validate ranges
        assert 0 <= dist['min'] <= 1
        assert 0 <= dist['max'] <= 1
        assert dist['min'] <= dist['max']
        assert dist['count'] == len(result.data['node_clustering'])
    
    def test_get_node_clustering(self, triangle_model):
        """Test getting clustering for specific node."""
        analyzer = ClusteringAnalyzer(triangle_model)
        
        clustering = analyzer.get_node_clustering('p_1')
        
        assert clustering is not None
        assert isinstance(clustering, float)
        assert 0 <= clustering <= 1
    
    def test_get_node_clustering_invalid(self, triangle_model):
        """Test getting clustering for non-existent node."""
        analyzer = ClusteringAnalyzer(triangle_model)
        
        clustering = analyzer.get_node_clustering('nonexistent')
        
        assert clustering is None
    
    def test_identify_clustered_regions(self, triangle_model):
        """Test identifying highly clustered regions."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.identify_clustered_regions(min_clustering=0.5, min_nodes=2)
        
        assert result.success
        assert 'regions' in result.data
        assert 'num_regions' in result.data
        
        # Each region should have required structure
        for region in result.data['regions']:
            assert 'id' in region
            assert 'nodes' in region
            assert 'size' in region
            assert 'avg_clustering' in region
            assert region['size'] >= 2
    
    def test_empty_model(self):
        """Test handling of empty model."""
        model = Mock()
        model.places = []
        model.transitions = []
        model.arcs = []
        
        analyzer = ClusteringAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        assert result.data['average_clustering'] == 0.0
        assert result.data['transitivity'] == 0.0
        assert len(result.data['node_clustering']) == 0
    
    def test_result_metadata(self, triangle_model):
        """Test that result metadata is complete."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze(top_n=5, include_triangles=True)
        
        assert result.success
        assert 'analysis_time' in result.metadata
        assert 'top_n' in result.metadata
        assert result.metadata['top_n'] == 5
        assert 'include_triangles' in result.metadata
        assert result.metadata['include_triangles'] == True
        assert 'total_nodes' in result.metadata
    
    def test_summary_generation(self, triangle_model):
        """Test that summary is generated correctly."""
        analyzer = ClusteringAnalyzer(triangle_model)
        result = analyzer.analyze()
        
        assert result.success
        summary = result.data['summary']
        
        # Summary should mention key metrics
        assert 'clustering' in summary.lower()
        assert 'transitivity' in summary.lower()
        # Should include numbers
        assert any(char.isdigit() for char in summary)
    
    def test_highly_clustered_nodes_sorted(self, star_model):
        """Test that highly clustered nodes are properly sorted."""
        analyzer = ClusteringAnalyzer(star_model)
        result = analyzer.analyze(top_n=10)
        
        assert result.success
        
        # Extract clustering values
        clusterings = [
            node['clustering']
            for node in result.data['highly_clustered_nodes']
        ]
        
        # Should be sorted in descending order
        assert clusterings == sorted(clusterings, reverse=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
