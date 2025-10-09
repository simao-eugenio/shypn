"""
Orthogonal Layout Algorithm

Implements Manhattan-style routing with horizontal/vertical edges.
Best for circuit-like pathways and regulatory networks.

Based on:
    Eiglsperger et al. (2003) - "An efficient implementation of Sugiyama's 
    algorithm for layered graph drawing" with orthogonal edge routing
    
Algorithm:
    1. Use hierarchical layer assignment
    2. Assign coordinates with grid alignment
    3. Route edges with orthogonal (horizontal/vertical) segments
    
Note: Full orthogonal routing is complex. This implementation provides
      grid-aligned nodes with hierarchical layout base.
"""

from typing import Dict, Tuple, List
import networkx as nx
from .base import LayoutAlgorithm
from .hierarchical import HierarchicalLayout


class OrthogonalLayout(LayoutAlgorithm):
    """
    Orthogonal layout with Manhattan-style edge routing.
    
    Creates a grid-aligned layout with horizontal/vertical edges.
    Provides clean, structured appearance for circuit-like pathways.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Orthogonal Layout"
        self.description = "Grid-aligned layout with Manhattan routing"
        self.best_for = "Circuit-like pathways, regulatory networks, structured diagrams"
    
    def compute(
        self,
        graph: nx.DiGraph,
        grid_size: float = 100.0,
        layer_spacing: float = 150.0,
        node_spacing: float = 100.0,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute orthogonal layout positions.
        
        Args:
            graph: NetworkX directed graph
            grid_size: Grid cell size for snapping
            layer_spacing: Vertical spacing between layers
            node_spacing: Horizontal spacing between nodes
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        if graph.number_of_nodes() == 1:
            # Single node at origin
            return {list(graph.nodes())[0]: (0.0, 0.0)}
        
        # Use hierarchical layout as base
        hierarchical = HierarchicalLayout()
        positions = hierarchical.compute(
            graph,
            layer_spacing=layer_spacing,
            node_spacing=node_spacing
        )
        
        # Snap to grid
        grid_positions = {}
        for node, (x, y) in positions.items():
            # Round to nearest grid point
            grid_x = round(x / grid_size) * grid_size
            grid_y = round(y / grid_size) * grid_size
            grid_positions[node] = (grid_x, grid_y)
        
        return grid_positions
    
    def compute_with_channels(
        self,
        graph: nx.DiGraph,
        grid_size: float = 100.0,
        layer_spacing: float = 200.0,
        node_spacing: float = 150.0,
        channel_width: float = 50.0,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute orthogonal layout with routing channels.
        
        Adds space between layers for horizontal routing channels.
        
        Args:
            graph: NetworkX directed graph
            grid_size: Grid cell size
            layer_spacing: Vertical spacing (includes channel)
            node_spacing: Horizontal spacing
            channel_width: Width of routing channels
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Get hierarchical layout
        hierarchical = HierarchicalLayout()
        layers_dict = hierarchical._assign_layers(graph)
        layer_groups = hierarchical._group_by_layer(layers_dict)
        layer_groups = hierarchical._reduce_crossings(graph, layer_groups)
        
        # Assign positions with channels
        positions = {}
        
        for layer_idx, layer_nodes in enumerate(layer_groups):
            if not layer_nodes:
                continue
            
            # Y-coordinate includes channel space
            y = layer_idx * (layer_spacing + channel_width)
            
            # X-coordinates on grid
            layer_width = (len(layer_nodes) - 1) * node_spacing
            x_start = -layer_width / 2
            
            for node_idx, node in enumerate(layer_nodes):
                x = x_start + node_idx * node_spacing
                
                # Snap to grid
                grid_x = round(x / grid_size) * grid_size
                grid_y = round(y / grid_size) * grid_size
                
                positions[node] = (grid_x, grid_y)
        
        return positions
    
    def compute_compact(
        self,
        graph: nx.DiGraph,
        grid_size: float = 100.0,
        min_spacing: float = 100.0,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute compact orthogonal layout.
        
        Minimizes whitespace while maintaining orthogonal structure.
        
        Args:
            graph: NetworkX directed graph
            grid_size: Grid cell size
            min_spacing: Minimum spacing between nodes
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Use hierarchical base
        hierarchical = HierarchicalLayout()
        layers_dict = hierarchical._assign_layers(graph)
        layer_groups = hierarchical._group_by_layer(layers_dict)
        layer_groups = hierarchical._reduce_crossings(graph, layer_groups)
        
        # Compact packing algorithm
        positions = {}
        layer_y_positions = {}  # Track y-position for each layer
        
        # First pass: assign y-coordinates compactly
        current_y = 0
        for layer_idx, layer_nodes in enumerate(layer_groups):
            if not layer_nodes:
                continue
            
            layer_y_positions[layer_idx] = current_y
            
            # Next layer starts min_spacing below
            current_y += min_spacing
        
        # Second pass: assign x-coordinates
        for layer_idx, layer_nodes in enumerate(layer_groups):
            if not layer_nodes:
                continue
            
            y = layer_y_positions[layer_idx]
            
            # Compact horizontal packing
            current_x = 0
            for node in layer_nodes:
                # Snap to grid
                grid_x = round(current_x / grid_size) * grid_size
                grid_y = round(y / grid_size) * grid_size
                
                positions[node] = (grid_x, grid_y)
                
                # Next node offset
                current_x += min_spacing
        
        # Center the layout
        if positions:
            xs = [x for x, y in positions.values()]
            center_x = (min(xs) + max(xs)) / 2
            
            centered = {}
            for node, (x, y) in positions.items():
                centered[node] = (x - center_x, y)
            
            positions = centered
        
        return positions
    
    def get_edge_routing(
        self,
        graph: nx.DiGraph,
        positions: Dict[str, Tuple[float, float]],
        grid_size: float = 100.0
    ) -> Dict[Tuple[str, str], List[Tuple[float, float]]]:
        """
        Compute orthogonal edge routing (waypoints).
        
        Returns Manhattan-style routing with horizontal/vertical segments.
        
        Args:
            graph: NetworkX directed graph
            positions: Node positions
            grid_size: Grid cell size for routing
            
        Returns:
            Dictionary mapping (source, target) edge to list of waypoints
            Each waypoint is (x, y) coordinate
            Format: [(x1,y1), (x2,y2), ...] forms polyline from source to target
        """
        edge_routes = {}
        
        for source, target in graph.edges():
            if source not in positions or target not in positions:
                continue
            
            sx, sy = positions[source]
            tx, ty = positions[target]
            
            # Simple 3-segment routing: horizontal, vertical, horizontal
            # This creates a "staircase" effect
            
            if abs(tx - sx) < grid_size / 2:
                # Nodes are vertically aligned, direct vertical line
                waypoints = [(sx, sy), (tx, ty)]
            
            elif abs(ty - sy) < grid_size / 2:
                # Nodes are horizontally aligned, direct horizontal line
                waypoints = [(sx, sy), (tx, ty)]
            
            else:
                # Use Manhattan routing with midpoint
                mid_y = (sy + ty) / 2
                mid_y = round(mid_y / grid_size) * grid_size
                
                waypoints = [
                    (sx, sy),           # Start
                    (sx, mid_y),        # Vertical segment down
                    (tx, mid_y),        # Horizontal segment across
                    (tx, ty)            # Vertical segment to target
                ]
            
            edge_routes[(source, target)] = waypoints
        
        return edge_routes
    
    def compute_with_routing(
        self,
        graph: nx.DiGraph,
        grid_size: float = 100.0,
        layer_spacing: float = 150.0,
        node_spacing: float = 100.0,
        **kwargs
    ) -> Tuple[Dict[str, Tuple[float, float]], Dict[Tuple[str, str], List[Tuple[float, float]]]]:
        """
        Compute layout with edge routing.
        
        Returns both node positions and edge waypoints.
        
        Returns:
            Tuple of (positions, edge_routes)
            positions: node_id -> (x, y)
            edge_routes: (source, target) -> [(x1,y1), (x2,y2), ...]
        """
        # Compute node positions
        positions = self.compute(
            graph,
            grid_size=grid_size,
            layer_spacing=layer_spacing,
            node_spacing=node_spacing
        )
        
        # Compute edge routing
        edge_routes = self.get_edge_routing(graph, positions, grid_size)
        
        return positions, edge_routes
