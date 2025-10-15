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
        
        PHYSICS MODEL (Fruchterman-Reingold):
        
        1. MASS NODES (Places + Transitions):
           - ALL mass nodes repel ALL other mass nodes (universal repulsion)
           - Place ↔ Place: repel
           - Transition ↔ Transition: repel
           - Place ↔ Transition: repel
           - Force: F_repulsion = -k² / distance
           - This prevents overlap and creates spacing
        
        2. SPRINGS (Arcs):
           - ONLY connected mass nodes attract each other (selective attraction)
           - Springs pull connected mass nodes together
           - Force: F_spring = k × distance × spring_strength
           - Spring strength = arc weight (stoichiometry)
        
        3. EQUILIBRIUM:
           - Each mass node settles where forces balance
           - Connected nodes: spring pull ⇄ repulsion → optimal distance
           - Disconnected nodes: only repulsion → maximum separation
        
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
        
        # DIAGNOSTIC: Count and log what we're loading
        print(f"\n{'='*80}")
        print(f"🔍 GRAPH BUILD DIAGNOSTIC")
        print(f"{'='*80}")
        print(f"📊 Document has:")
        print(f"   - {len(doc.places)} places")
        print(f"   - {len(doc.transitions)} transitions")
        print(f"   - {len(doc.arcs)} arcs")
        
        # Add mass nodes (places and transitions)
        # Use the actual objects as node IDs - NetworkX handles this perfectly
        # This automatically avoids ID collisions since Python objects are unique by identity
        place_count = 0
        for i, place in enumerate(doc.places):
            graph.add_node(place, type='place')  # Use object itself as node ID
            place_count += 1
            if i < 5:  # Show first 5
                place_name = getattr(place, 'name', 'unnamed')
                print(f"   Place {i+1}: id={place.id}, name='{place_name}'")
        
        if len(doc.places) > 5:
            print(f"   ... and {len(doc.places) - 5} more places")
        
        transition_count = 0
        for transition in doc.transitions:
            graph.add_node(transition, type='transition')  # Use object itself as node ID
            transition_count += 1
        
        print(f"\n📦 Added to graph:")
        print(f"   - {place_count} place nodes")
        print(f"   - {transition_count} transition nodes")
        print(f"   - Total nodes in graph: {graph.number_of_nodes()}")
        
        # Add springs (arcs) with weight as spring strength
        # Arcs have .source and .target which are OBJECT REFERENCES, not IDs!
        arcs_added = 0
        for arc in doc.arcs:
            # Arc weight = stoichiometry = spring strength
            # Higher weight = stronger spring = pulls mass nodes closer
            weight = getattr(arc, 'weight', 1.0)  # Default weight = 1.0
            
            # arc.source and arc.target are the actual Place/Transition objects
            # These are already in the graph as node IDs
            source_obj = arc.source
            target_obj = arc.target
            
            if source_obj in graph and target_obj in graph:
                # Don't store arc object - it contains GObject references that can't be deepcopied
                # Just store the weight (stoichiometry) which is all we need for layout
                graph.add_edge(source_obj, target_obj, weight=weight)
                arcs_added += 1
            else:
                # This shouldn't happen if everything is wired correctly
                source_name = getattr(source_obj, 'name', 'unknown')
                target_name = getattr(target_obj, 'name', 'unknown')
                print(f"   ⚠️ Arc skipped: {source_name} → {target_name} (nodes not in graph)")
        
        print(f"   - {arcs_added} arcs/edges")
        print(f"{'='*80}\n")
        
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
        
        # Node IDs in the graph are the actual Place/Transition objects
        # positions dict maps: {place_obj: (x, y), transition_obj: (x, y)}
        # So we can directly use the node_id (which IS the object) to set positions
        
        # Apply positions
        for obj, (x, y) in positions.items():
            # obj is the actual Place or Transition object
            if hasattr(obj, 'x') and hasattr(obj, 'y'):
                obj.x = x
                obj.y = y
                nodes_moved += 1
            else:
                print(f"⚠️ Warning: Object {obj} has no x/y attributes")
        
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
