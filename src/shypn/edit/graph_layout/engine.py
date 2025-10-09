"""
Layout Engine - Main API for Graph Layout

Orchestrates layout algorithms and applies them to DocumentModel.
Provides high-level interface for the application.

Usage:
    >>> from shypn.edit.graph_layout import LayoutEngine
    >>> engine = LayoutEngine(document_manager)
    >>> 
    >>> # Auto-select algorithm
    >>> engine.apply_layout('auto')
    >>> 
    >>> # Use specific algorithm
    >>> engine.apply_layout('hierarchical')
    >>> engine.apply_layout('force_directed')
    >>> engine.apply_layout('circular')
    >>> engine.apply_layout('orthogonal')
    >>> 
    >>> # Preview without applying
    >>> result = engine.preview_layout('auto')
    >>> print(result['algorithm'])  # Shows selected algorithm
    >>> print(result['reason'])     # Explains why
"""

from typing import Dict, Tuple, List, Optional
import networkx as nx
from .base import LayoutAlgorithm
from .hierarchical import HierarchicalLayout
from .force_directed import ForceDirectedLayout
from .circular import CircularLayout
from .orthogonal import OrthogonalLayout
from .selector import LayoutSelector


class LayoutEngine:
    """
    Main interface for graph layout operations.
    
    Coordinates algorithm selection, execution, and application to DocumentModel.
    """
    
    def __init__(self, document_manager=None):
        """
        Initialize layout engine.
        
        Args:
            document_manager: DocumentManager instance (optional, can be set later)
        """
        self.document_manager = document_manager
        
        # Initialize algorithms
        self.algorithms = {
            'hierarchical': HierarchicalLayout(),
            'force_directed': ForceDirectedLayout(),
            'circular': CircularLayout(),
            'orthogonal': OrthogonalLayout()
        }
        
        # Initialize selector
        self.selector = LayoutSelector()
    
    def set_document_manager(self, document_manager):
        """Set the document manager."""
        self.document_manager = document_manager
    
    def build_graph(self) -> nx.DiGraph:
        """
        Build NetworkX graph from current DocumentModel.
        
        Returns:
            NetworkX directed graph representing the Petri net
            
        Raises:
            ValueError: If document_manager is not set
        """
        if self.document_manager is None:
            raise ValueError("Document manager not set")
        
        # Support both ModelCanvasManager (has places/transitions directly)
        # and DocumentManager (has .document property)
        if hasattr(self.document_manager, 'document'):
            doc = self.document_manager.document
        else:
            doc = self.document_manager  # ModelCanvasManager IS the document
        
        graph = nx.DiGraph()
        
        # Add nodes (places and transitions)
        for place in doc.places:
            graph.add_node(place.id, type='place', obj=place)
        
        for transition in doc.transitions:
            graph.add_node(transition.id, type='transition', obj=transition)
        
        # Add edges (arcs)
        for arc in doc.arcs:
            graph.add_edge(arc.source, arc.target, obj=arc)
        
        return graph
    
    def apply_layout(
        self,
        algorithm: str = 'auto',
        **kwargs
    ) -> Dict:
        """
        Apply layout algorithm to current document.
        
        Args:
            algorithm: Algorithm name ('auto', 'hierarchical', 'force_directed', 
                      'circular', 'orthogonal')
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Dictionary with:
            - algorithm: Name of algorithm used
            - nodes_moved: Number of nodes repositioned
            - success: True if successful
            
        Raises:
            ValueError: If document_manager is not set or algorithm unknown
        """
        if self.document_manager is None:
            raise ValueError("Document manager not set")
        
        # Build graph
        graph = self.build_graph()
        
        if graph.number_of_nodes() == 0:
            return {
                'algorithm': algorithm,
                'nodes_moved': 0,
                'success': True,
                'message': 'No nodes to layout'
            }
        
        # Select algorithm if auto
        if algorithm == 'auto':
            selection_result = self.selector.select_with_explanation(graph)
            algorithm = selection_result['algorithm']
            reason = selection_result['reason']
        else:
            reason = f"User selected {algorithm}"
            
        # Validate algorithm
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}. Must be one of: {list(self.algorithms.keys())}")
        
        # Get algorithm instance
        layout_algo = self.algorithms[algorithm]
        
        # Recommend parameters if not provided
        if not kwargs:
            kwargs = self.selector.recommend_parameters(graph, algorithm)
        
        # Compute layout
        positions = layout_algo.compute(graph, **kwargs)
        
        # Apply positions to document objects
        nodes_moved = self._apply_positions(positions)
        
        # Mark document as modified
        self.document_manager.mark_dirty()
        
        return {
            'algorithm': algorithm,
            'nodes_moved': nodes_moved,
            'success': True,
            'reason': reason,
            'parameters': kwargs
        }
    
    def preview_layout(
        self,
        algorithm: str = 'auto',
        **kwargs
    ) -> Dict:
        """
        Preview layout without applying to document.
        
        Returns layout information and positions without modifying the document.
        
        Args:
            algorithm: Algorithm name
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Dictionary with:
            - algorithm: Name of algorithm selected
            - reason: Explanation of selection
            - positions: Dictionary of node_id -> (x, y)
            - metrics: Graph topology metrics
            - alternatives: Alternative algorithms
        """
        if self.document_manager is None:
            raise ValueError("Document manager not set")
        
        # Build graph
        graph = self.build_graph()
        
        if graph.number_of_nodes() == 0:
            return {
                'algorithm': algorithm,
                'reason': 'Empty graph',
                'positions': {},
                'metrics': {},
                'alternatives': []
            }
        
        # Select algorithm if auto
        if algorithm == 'auto':
            selection_result = self.selector.select_with_explanation(graph)
            algorithm = selection_result['algorithm']
            reason = selection_result['reason']
            metrics = selection_result['metrics']
            alternatives = selection_result['alternatives']
        else:
            reason = f"User selected {algorithm}"
            # Use hierarchical algorithm to get metrics (all inherit same method)
            hierarchical = self.algorithms['hierarchical']
            metrics = hierarchical.analyze_topology(graph)
            alternatives = self.selector._find_alternatives(algorithm, metrics)
        
        # Validate algorithm
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Recommend parameters if not provided
        if not kwargs:
            kwargs = self.selector.recommend_parameters(graph, algorithm)
        
        # Compute layout
        layout_algo = self.algorithms[algorithm]
        positions = layout_algo.compute(graph, **kwargs)
        
        return {
            'algorithm': algorithm,
            'reason': reason,
            'positions': positions,
            'metrics': metrics,
            'alternatives': alternatives,
            'parameters': kwargs
        }
    
    def _apply_positions(self, positions: Dict[str, Tuple[float, float]]) -> int:
        """
        Apply positions to document objects.
        
        Args:
            positions: Dictionary mapping node IDs to (x, y) positions
            
        Returns:
            Number of nodes moved
        """
        # Support both ModelCanvasManager (has places/transitions directly)
        # and DocumentManager (has .document property)
        if hasattr(self.document_manager, 'document'):
            doc = self.document_manager.document
        else:
            doc = self.document_manager  # ModelCanvasManager IS the document
        
        nodes_moved = 0
        
        # Map node IDs to objects
        id_to_obj = {}
        for place in doc.places:
            id_to_obj[place.id] = place
        for transition in doc.transitions:
            id_to_obj[transition.id] = transition
        
        # Apply positions
        for node_id, (x, y) in positions.items():
            if node_id in id_to_obj:
                obj = id_to_obj[node_id]
                obj.x = x
                obj.y = y
                nodes_moved += 1
        
        return nodes_moved
    
    def get_available_algorithms(self) -> Dict[str, str]:
        """
        Get all available algorithms with descriptions.
        
        Returns:
            Dictionary mapping algorithm names to descriptions
        """
        return {
            name: algo.description
            for name, algo in self.algorithms.items()
        }
    
    def get_algorithm_info(self, algorithm: str) -> Dict:
        """
        Get detailed information about an algorithm.
        
        Args:
            algorithm: Algorithm name
            
        Returns:
            Dictionary with algorithm details
        """
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        algo = self.algorithms[algorithm]
        
        return {
            'name': algo.name,
            'description': algo.description,
            'best_for': algo.best_for,
            'algorithm_id': algorithm
        }
    
    def analyze_current_graph(self) -> Dict:
        """
        Analyze current graph topology.
        
        Returns:
            Dictionary with topology metrics and recommendations
        """
        if self.document_manager is None:
            raise ValueError("Document manager not set")
        
        graph = self.build_graph()
        
        if graph.number_of_nodes() == 0:
            return {
                'node_count': 0,
                'edge_count': 0,
                'message': 'Empty graph',
                'recommended_algorithm': 'hierarchical'
            }
        
        # Get metrics
        hierarchical = self.algorithms['hierarchical']
        metrics = hierarchical.analyze_topology(graph)
        
        # Get recommendation
        selection = self.selector.select_with_explanation(graph)
        
        # Get all suitable algorithms
        suitable = self.selector.get_all_suitable_algorithms(graph)
        
        return {
            **metrics,
            'recommended_algorithm': selection['algorithm'],
            'recommendation_reason': selection['reason'],
            'suitable_algorithms': suitable,
            'alternatives': selection['alternatives']
        }
    
    def apply_layout_to_selection(
        self,
        selected_nodes: List[str],
        algorithm: str = 'auto',
        **kwargs
    ) -> Dict:
        """
        Apply layout to a subset of nodes.
        
        Useful for laying out only selected parts of the graph.
        
        Args:
            selected_nodes: List of node IDs to layout
            algorithm: Algorithm name
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Dictionary with layout results
        """
        if self.document_manager is None:
            raise ValueError("Document manager not set")
        
        if not selected_nodes:
            return {
                'algorithm': algorithm,
                'nodes_moved': 0,
                'success': True,
                'message': 'No nodes selected'
            }
        
        # Build full graph
        full_graph = self.build_graph()
        
        # Create subgraph of selected nodes
        subgraph = full_graph.subgraph(selected_nodes)
        
        # Select algorithm if auto
        if algorithm == 'auto':
            algorithm = self.selector.select(subgraph)
        
        # Validate algorithm
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Recommend parameters
        if not kwargs:
            kwargs = self.selector.recommend_parameters(subgraph, algorithm)
        
        # Compute layout
        layout_algo = self.algorithms[algorithm]
        positions = layout_algo.compute(subgraph, **kwargs)
        
        # Apply positions
        nodes_moved = self._apply_positions(positions)
        
        # Mark document as modified
        self.document_manager.mark_dirty()
        
        return {
            'algorithm': algorithm,
            'nodes_moved': nodes_moved,
            'success': True,
            'parameters': kwargs
        }
