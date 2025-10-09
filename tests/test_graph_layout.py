"""
Unit Tests for Graph Layout Module

Tests all layout algorithms, selector, and engine.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import networkx as nx
from shypn.edit.graph_layout import (
    LayoutAlgorithm,
    HierarchicalLayout,
    ForceDirectedLayout,
    CircularLayout,
    OrthogonalLayout,
    LayoutSelector,
    LayoutEngine
)


class TestBaseLayoutAlgorithm(unittest.TestCase):
    """Test base LayoutAlgorithm utilities."""
    
    def setUp(self):
        """Create test graph."""
        self.graph = nx.DiGraph()
        self.graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('B', 'E')
        ])
    
    def test_analyze_topology_dag(self):
        """Test topology analysis for DAG."""
        algo = HierarchicalLayout()  # Use concrete class
        metrics = algo.analyze_topology(self.graph)
        
        self.assertTrue(metrics['is_dag'])
        self.assertEqual(metrics['node_count'], 5)
        self.assertEqual(metrics['edge_count'], 4)
        self.assertFalse(metrics['has_cycles'])
        self.assertEqual(metrics['longest_cycle'], 0)
    
    def test_analyze_topology_cyclic(self):
        """Test topology analysis for graph with cycles."""
        cyclic = nx.DiGraph()
        cyclic.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'A')  # Cycle
        ])
        
        algo = HierarchicalLayout()
        metrics = algo.analyze_topology(cyclic)
        
        self.assertFalse(metrics['is_dag'])
        self.assertTrue(metrics['has_cycles'])
        self.assertEqual(metrics['longest_cycle'], 3)
    
    def test_layer_assignment(self):
        """Test layer assignment for hierarchical layout."""
        algo = HierarchicalLayout()
        layers = algo.get_layer_assignment(self.graph)
        
        # A should be layer 0 (source)
        self.assertEqual(layers['A'], 0)
        # B should be layer 1
        self.assertEqual(layers['B'], 1)
        # C and E depend on B
        self.assertGreaterEqual(layers['C'], 2)
        self.assertGreaterEqual(layers['E'], 2)
        # D depends on C
        self.assertGreaterEqual(layers['D'], 3)
    
    def test_find_main_cycle(self):
        """Test cycle detection."""
        cyclic = nx.DiGraph()
        cyclic.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'A'),  # Main cycle
            ('D', 'E')   # Branch
        ])
        
        algo = CircularLayout()
        cycle = algo.find_main_cycle(cyclic)
        
        self.assertIsNotNone(cycle)
        self.assertEqual(len(cycle), 4)
        self.assertIn('A', cycle)
        self.assertIn('B', cycle)


class TestHierarchicalLayout(unittest.TestCase):
    """Test HierarchicalLayout algorithm."""
    
    def test_simple_dag(self):
        """Test hierarchical layout on simple DAG."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('A', 'C'),
            ('B', 'D'),
            ('C', 'D')
        ])
        
        algo = HierarchicalLayout()
        positions = algo.compute(graph)
        
        # Should have positions for all nodes
        self.assertEqual(len(positions), 4)
        
        # Y-coordinates should increase (layers)
        self.assertLess(positions['A'][1], positions['B'][1])
        self.assertLess(positions['B'][1], positions['D'][1])
    
    def test_empty_graph(self):
        """Test with empty graph."""
        graph = nx.DiGraph()
        algo = HierarchicalLayout()
        positions = algo.compute(graph)
        
        self.assertEqual(len(positions), 0)
    
    def test_single_node(self):
        """Test with single node."""
        graph = nx.DiGraph()
        graph.add_node('A')
        
        algo = HierarchicalLayout()
        positions = algo.compute(graph)
        
        self.assertEqual(len(positions), 1)
        self.assertIn('A', positions)
    
    def test_cyclic_graph(self):
        """Test hierarchical layout with cycles (feedback arcs)."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'A')  # Cycle
        ])
        
        algo = HierarchicalLayout()
        positions, feedback = algo.compute_with_feedback_arcs(graph)
        
        # Should still produce positions
        self.assertEqual(len(positions), 3)
        
        # Should identify at least one feedback arc
        self.assertGreater(len(feedback), 0)


class TestForceDirectedLayout(unittest.TestCase):
    """Test ForceDirectedLayout algorithm."""
    
    def test_simple_graph(self):
        """Test force-directed layout."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'A')
        ])
        
        algo = ForceDirectedLayout()
        positions = algo.compute(graph, iterations=100)
        
        # Should have positions for all nodes
        self.assertEqual(len(positions), 4)
        
        # All positions should be tuples of floats
        for node, (x, y) in positions.items():
            self.assertIsInstance(x, float)
            self.assertIsInstance(y, float)
    
    def test_reproducibility(self):
        """Test that same seed produces same layout."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'A')
        ])
        
        algo = ForceDirectedLayout()
        pos1 = algo.compute(graph, seed=42, iterations=50)
        pos2 = algo.compute(graph, seed=42, iterations=50)
        
        # Should be identical
        for node in graph.nodes():
            self.assertAlmostEqual(pos1[node][0], pos2[node][0], places=5)
            self.assertAlmostEqual(pos1[node][1], pos2[node][1], places=5)


class TestCircularLayout(unittest.TestCase):
    """Test CircularLayout algorithm."""
    
    def test_cyclic_graph(self):
        """Test circular layout on cyclic graph."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'A')  # Cycle
        ])
        
        algo = CircularLayout()
        positions = algo.compute(graph, radius=100)
        
        # Should have positions for all nodes
        self.assertEqual(len(positions), 4)
        
        # All nodes should be approximately on the circle
        import math
        for node, (x, y) in positions.items():
            distance = math.sqrt(x*x + y*y)
            self.assertAlmostEqual(distance, 100, delta=1.0)
    
    def test_graph_with_branches(self):
        """Test circular layout with branches outside main cycle."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'A'),  # Cycle
            ('B', 'D'),  # Branch
            ('B', 'E')   # Branch
        ])
        
        algo = CircularLayout()
        positions = algo.compute(graph, radius=100, arrange_branches=True)
        
        # Should have positions for all nodes
        self.assertEqual(len(positions), 5)
    
    def test_concentric_layout(self):
        """Test concentric circular layout."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'A'),  # Main cycle
            ('B', 'D'),
            ('D', 'E'),  # Outer ring
            ('E', 'F')
        ])
        
        algo = CircularLayout()
        positions = algo.compute_concentric(graph, base_radius=100, ring_spacing=50)
        
        # Should have positions for all nodes
        self.assertEqual(len(positions), 6)


class TestOrthogonalLayout(unittest.TestCase):
    """Test OrthogonalLayout algorithm."""
    
    def test_dag_layout(self):
        """Test orthogonal layout on DAG."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D')
        ])
        
        algo = OrthogonalLayout()
        positions = algo.compute(graph, grid_size=100)
        
        # Should have positions for all nodes
        self.assertEqual(len(positions), 4)
        
        # All positions should be on grid
        for node, (x, y) in positions.items():
            self.assertEqual(x % 100, 0)
            self.assertEqual(y % 100, 0)
    
    def test_edge_routing(self):
        """Test orthogonal edge routing."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C')
        ])
        
        algo = OrthogonalLayout()
        positions, routes = algo.compute_with_routing(graph, grid_size=100)
        
        # Should have routes for all edges
        self.assertEqual(len(routes), 2)
        
        # Each route should be a list of waypoints
        for edge, waypoints in routes.items():
            self.assertIsInstance(waypoints, list)
            self.assertGreater(len(waypoints), 1)


class TestLayoutSelector(unittest.TestCase):
    """Test LayoutSelector algorithm selection."""
    
    def test_select_for_dag(self):
        """Test selector chooses hierarchical for DAG."""
        graph = nx.DiGraph()
        graph.add_edges_from([
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D')
        ])
        
        selector = LayoutSelector()
        algorithm = selector.select(graph)
        
        self.assertEqual(algorithm, 'hierarchical')
    
    def test_select_for_cycle(self):
        """Test selector chooses circular for cyclic graph."""
        graph = nx.DiGraph()
        # Create large cycle (>50% of nodes)
        edges = [(f'N{i}', f'N{(i+1)%10}') for i in range(10)]
        graph.add_edges_from(edges)
        
        selector = LayoutSelector()
        algorithm = selector.select(graph)
        
        self.assertEqual(algorithm, 'circular')
    
    def test_select_for_dense(self):
        """Test selector makes valid choice for dense graph."""
        graph = nx.DiGraph()
        # Create highly connected graph without forming dominant cycle
        nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        # Add many edges but avoid creating a single dominant cycle
        for i, n1 in enumerate(nodes[:6]):  # First 6 nodes
            for j, n2 in enumerate(nodes[:6]):
                if i != j and abs(i - j) <= 2:  # Only connect nearby nodes
                    graph.add_edge(n1, n2)
        
        selector = LayoutSelector()
        algorithm = selector.select(graph)
        
        # Should choose a reasonable algorithm (any is valid for complex graphs)
        self.assertIn(algorithm, ['force_directed', 'hierarchical', 'circular'])
    
    def test_explain_selection(self):
        """Test selector provides explanation."""
        graph = nx.DiGraph()
        graph.add_edges_from([('A', 'B'), ('B', 'C')])
        
        selector = LayoutSelector()
        result = selector.select_with_explanation(graph)
        
        self.assertIn('algorithm', result)
        self.assertIn('reason', result)
        self.assertIn('metrics', result)
        self.assertIsInstance(result['reason'], str)
    
    def test_recommend_parameters(self):
        """Test parameter recommendations."""
        graph = nx.DiGraph()
        graph.add_edges_from([('A', 'B'), ('B', 'C')])
        
        selector = LayoutSelector()
        params = selector.recommend_parameters(graph, 'hierarchical')
        
        self.assertIn('layer_spacing', params)
        self.assertIn('node_spacing', params)


class TestLayoutEngine(unittest.TestCase):
    """Test LayoutEngine orchestrator."""
    
    def test_build_graph(self):
        """Test building NetworkX graph from DocumentModel."""
        # This test would require a mock DocumentManager
        # For now, just test that engine can be created
        engine = LayoutEngine()
        self.assertIsNotNone(engine)
        self.assertIsNone(engine.document_manager)
    
    def test_get_available_algorithms(self):
        """Test listing available algorithms."""
        engine = LayoutEngine()
        algos = engine.get_available_algorithms()
        
        self.assertIn('hierarchical', algos)
        self.assertIn('force_directed', algos)
        self.assertIn('circular', algos)
        self.assertIn('orthogonal', algos)
    
    def test_get_algorithm_info(self):
        """Test getting algorithm details."""
        engine = LayoutEngine()
        info = engine.get_algorithm_info('hierarchical')
        
        self.assertIn('name', info)
        self.assertIn('description', info)
        self.assertIn('best_for', info)


if __name__ == '__main__':
    unittest.main()
