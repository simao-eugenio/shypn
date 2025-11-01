"""
Hierarchical Layout Algorithm (Sugiyama Framework)

Implements layered graph drawing for directed graphs.
Best for linear pathways with clear flow direction (e.g., glycolysis).

Based on:
    Sugiyama et al. (1981) - "Methods for visual understanding of 
    hierarchical system structures" IEEE Trans. SMC
    
Algorithm phases:
    1. Layer Assignment - Assign nodes to horizontal layers
    2. Crossing Reduction - Minimize edge crossings between layers
    3. Coordinate Assignment - Assign x-coordinates to minimize edge length
"""

from typing import Dict, Tuple, List
import networkx as nx
from .base import LayoutAlgorithm


class HierarchicalLayout(LayoutAlgorithm):
    """
    Hierarchical (layered) layout using Sugiyama framework.
    
    Creates a top-to-bottom layout with nodes arranged in layers.
    Minimizes edge crossings and emphasizes flow direction.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Hierarchical Layout"
        self.description = "Layered graph drawing (Sugiyama framework)"
        self.best_for = "Directed acyclic graphs, linear pathways, metabolic flows"
    
    def compute(
        self, 
        graph: nx.DiGraph,
        layer_spacing: float = 150.0,
        node_spacing: float = 100.0,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute hierarchical layout positions.
        
        Args:
            graph: NetworkX directed graph
            layer_spacing: Vertical spacing between layers (pixels)
            node_spacing: Horizontal spacing between nodes (pixels)
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Filter out completely isolated nodes (no arcs at all)
        # These are likely manual annotations or artifacts
        connected_graph = graph.copy()
        isolated_nodes = [
            n for n in connected_graph.nodes() 
            if connected_graph.degree(n) == 0
        ]
        if isolated_nodes:
            connected_graph.remove_nodes_from(isolated_nodes)
            print(f"🔍 Hierarchical layout: Filtered {len(isolated_nodes)} isolated nodes (no arcs)")
        
        # Also filter catalyst places (only test arcs, not part of main hierarchy)
        catalyst_nodes = [
            n for n in connected_graph.nodes()
            if getattr(n, 'is_catalyst', False)
        ]
        if catalyst_nodes:
            connected_graph.remove_nodes_from(catalyst_nodes)
            print(f"🔍 Hierarchical layout: Filtered {len(catalyst_nodes)} catalyst nodes (test arcs only)")
        
        if connected_graph.number_of_nodes() == 0:
            print("⚠️ Hierarchical layout: No connected nodes after filtering")
            return {}
        
        # Phase 1: Layer Assignment
        layers = self._assign_layers(connected_graph)
        
        # Group nodes by layer
        layer_groups = self._group_by_layer(layers)
        
        # Phase 2: Crossing Reduction (barycentric heuristic)
        layer_groups = self._reduce_crossings(connected_graph, layer_groups)
        
        # Phase 3: Coordinate Assignment
        positions = self._assign_coordinates(
            layer_groups, 
            layer_spacing, 
            node_spacing
        )
        
        return positions
    
    def _assign_layers(self, graph: nx.DiGraph) -> Dict[str, int]:
        """
        Assign each node to a layer using longest path method.
        
        Returns:
            Dictionary mapping node IDs to layer numbers (0, 1, 2, ...)
        """
        # Use base class implementation
        return self.get_layer_assignment(graph)
    
    def _group_by_layer(self, layers: Dict[str, int]) -> List[List[str]]:
        """
        Group nodes by their layer assignment.
        
        Returns:
            List of layers, each layer is a list of node IDs
        """
        if not layers:
            return []
        
        max_layer = max(layers.values())
        layer_groups = [[] for _ in range(max_layer + 1)]
        
        for node, layer in layers.items():
            layer_groups[layer].append(node)
        
        return layer_groups
    
    def _reduce_crossings(
        self, 
        graph: nx.DiGraph, 
        layer_groups: List[List[str]]
    ) -> List[List[str]]:
        """
        Reduce edge crossings between layers using barycentric heuristic.
        
        Sweeps down and up through layers, reordering nodes to minimize crossings.
        
        Returns:
            Reordered layer groups
        """
        if len(layer_groups) <= 1:
            return layer_groups
        
        # Make a copy to modify
        layers = [list(layer) for layer in layer_groups]
        
        # Multiple passes for better results
        for iteration in range(3):
            # Downward sweep
            for i in range(1, len(layers)):
                layers[i] = self._barycentric_ordering(
                    graph, layers[i], layers[i-1], direction='down'
                )
            
            # Upward sweep
            for i in range(len(layers) - 2, -1, -1):
                layers[i] = self._barycentric_ordering(
                    graph, layers[i], layers[i+1], direction='up'
                )
        
        return layers
    
    def _barycentric_ordering(
        self,
        graph: nx.DiGraph,
        current_layer: List[str],
        adjacent_layer: List[str],
        direction: str
    ) -> List[str]:
        """
        Order nodes in current layer by barycenter of adjacent nodes.
        
        Args:
            current_layer: Nodes to reorder
            adjacent_layer: Reference layer
            direction: 'down' (use predecessors) or 'up' (use successors)
            
        Returns:
            Reordered list of nodes
        """
        if not current_layer:
            return current_layer
        
        # Create position map for adjacent layer
        adjacent_positions = {node: i for i, node in enumerate(adjacent_layer)}
        
        # Calculate barycenter for each node
        barycenters = []
        for node in current_layer:
            if direction == 'down':
                # Look at predecessors
                neighbors = list(graph.predecessors(node))
            else:
                # Look at successors
                neighbors = list(graph.successors(node))
            
            # Filter to neighbors in adjacent layer
            neighbors = [n for n in neighbors if n in adjacent_positions]
            
            if neighbors:
                # Barycenter = average position of neighbors
                positions = [adjacent_positions[n] for n in neighbors]
                barycenter = sum(positions) / len(positions)
            else:
                # No neighbors, use current position
                barycenter = len(adjacent_layer) / 2
            
            barycenters.append((node, barycenter))
        
        # Sort by barycenter
        barycenters.sort(key=lambda x: x[1])
        
        return [node for node, _ in barycenters]
    
    def _assign_coordinates(
        self,
        layer_groups: List[List[str]],
        layer_spacing: float,
        node_spacing: float
    ) -> Dict[str, Tuple[float, float]]:
        """
        Assign (x, y) coordinates to nodes.
        
        Args:
            layer_groups: Nodes grouped by layer
            layer_spacing: Vertical spacing between layers
            node_spacing: Horizontal spacing between nodes
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        positions = {}
        
        for layer_idx, layer_nodes in enumerate(layer_groups):
            if not layer_nodes:
                continue
            
            # Y-coordinate is based on layer
            y = layer_idx * layer_spacing
            
            # X-coordinates: center the layer horizontally
            layer_width = (len(layer_nodes) - 1) * node_spacing
            x_start = -layer_width / 2  # Center at x=0
            
            for node_idx, node in enumerate(layer_nodes):
                x = x_start + node_idx * node_spacing
                positions[node] = (x, y)
        
        return positions
    
    def compute_with_feedback_arcs(
        self,
        graph: nx.DiGraph,
        layer_spacing: float = 150.0,
        node_spacing: float = 100.0
    ) -> Tuple[Dict[str, Tuple[float, float]], List[Tuple[str, str]]]:
        """
        Compute layout for graphs with cycles, identifying feedback arcs.
        
        Returns:
            Tuple of (positions, feedback_arcs)
            feedback_arcs: List of (source, target) edges that point backwards
        """
        # Identify feedback arcs
        feedback_arcs = []
        
        if not nx.is_directed_acyclic_graph(graph):
            # Find feedback arc set
            acyclic = self._remove_feedback_arcs(graph)
            
            # Identify which arcs were removed
            for edge in graph.edges():
                if edge not in acyclic.edges():
                    feedback_arcs.append(edge)
            
            # Compute layout on acyclic graph
            positions = self.compute(acyclic, layer_spacing, node_spacing)
        else:
            positions = self.compute(graph, layer_spacing, node_spacing)
        
        return positions, feedback_arcs
