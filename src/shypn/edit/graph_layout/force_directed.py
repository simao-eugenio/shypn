"""
Force-Directed Layout Algorithm (Fruchterman-Reingold)

Implements physics-based layout for complex networks.
Best for highly interconnected pathways without clear hierarchy.

Based on:
    Fruchterman & Reingold (1991) - "Graph drawing by force-directed 
    placement" Software: Practice and Experience
    
Algorithm:
    - Treats nodes as charged particles (repel each other)
    - Treats edges as springs (pull connected nodes together)
    - Simulates until system reaches equilibrium (energy minimum)
    - Uses NetworkX spring_layout implementation
"""

from typing import Dict, Tuple
import networkx as nx
import math
from .base import LayoutAlgorithm


class ForceDirectedLayout(LayoutAlgorithm):
    """
    Force-directed layout using Fruchterman-Reingold algorithm.
    
    Creates a natural, balanced layout where nodes repel each other
    and edges act as springs pulling connected nodes together.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Force-Directed Layout"
        self.description = "Physics-based layout (Fruchterman-Reingold)"
        self.best_for = "Complex networks, highly connected graphs, irregular topology"
    
    def compute(
        self,
        graph: nx.DiGraph,
        iterations: int = 500,
        k: float = None,
        scale: float = 1000.0,
        seed: int = 42,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute force-directed layout positions.
        
        Args:
            graph: NetworkX directed graph
            iterations: Number of simulation steps (more = better, slower)
            k: Optimal distance between nodes (None = auto-calculate)
            scale: Scale factor for final positions
            seed: Random seed for reproducible layouts
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        if graph.number_of_nodes() == 1:
            # Single node at origin
            return {list(graph.nodes())[0]: (0.0, 0.0)}
        
        # Calculate optimal distance if not provided
        if k is None:
            # k = optimal distance = sqrt(area / |V|)
            # For scale=1000, area = 1000*1000 = 1,000,000
            area = scale * scale
            k = math.sqrt(area / graph.number_of_nodes())
        
        # Use NetworkX spring_layout (Fruchterman-Reingold implementation)
        positions = nx.spring_layout(
            graph,
            k=k / scale,  # Normalize to 0-1 range
            iterations=iterations,
            scale=scale,
            center=(0, 0),
            seed=seed
        )
        
        # Convert positions to our format
        result = {}
        for node, (x, y) in positions.items():
            result[node] = (float(x), float(y))
        
        return result
    
    def compute_with_weights(
        self,
        graph: nx.DiGraph,
        weight_attr: str = 'weight',
        iterations: int = 500,
        scale: float = 1000.0,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute layout with edge weights influencing spring strength.
        
        Args:
            graph: NetworkX directed graph
            weight_attr: Edge attribute name for weights
            iterations: Number of simulation steps
            scale: Scale factor for final positions
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Check if edges have weights
        has_weights = any(weight_attr in graph[u][v] for u, v in graph.edges())
        
        if not has_weights:
            # Fall back to unweighted
            return self.compute(graph, iterations=iterations, scale=scale)
        
        # Calculate k based on graph size
        area = scale * scale
        k = math.sqrt(area / graph.number_of_nodes())
        
        # Use NetworkX spring_layout with weights
        positions = nx.spring_layout(
            graph,
            k=k / scale,
            iterations=iterations,
            weight=weight_attr,
            scale=scale,
            center=(0, 0)
        )
        
        # Convert to our format
        result = {}
        for node, (x, y) in positions.items():
            result[node] = (float(x), float(y))
        
        return result
    
    def compute_with_fixed_nodes(
        self,
        graph: nx.DiGraph,
        fixed_positions: Dict[str, Tuple[float, float]],
        iterations: int = 500,
        scale: float = 1000.0,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute layout with some nodes fixed in position.
        
        Useful for incremental layout or preserving user-positioned nodes.
        
        Args:
            graph: NetworkX directed graph
            fixed_positions: Nodes to keep fixed (node_id -> (x, y))
            iterations: Number of simulation steps
            scale: Scale factor for final positions
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Normalize fixed positions to 0-1 range for NetworkX
        normalized_fixed = {}
        for node, (x, y) in fixed_positions.items():
            normalized_fixed[node] = (x / scale, y / scale)
        
        # Calculate k
        area = scale * scale
        k = math.sqrt(area / graph.number_of_nodes())
        
        # Use spring_layout with fixed positions
        positions = nx.spring_layout(
            graph,
            k=k / scale,
            iterations=iterations,
            pos=normalized_fixed,
            fixed=list(fixed_positions.keys()),
            scale=scale,
            center=(0, 0)
        )
        
        # Convert to our format
        result = {}
        for node, (x, y) in positions.items():
            result[node] = (float(x), float(y))
        
        return result
    
    def compute_clustered(
        self,
        graph: nx.DiGraph,
        clusters: Dict[str, int],
        iterations: int = 500,
        scale: float = 1000.0,
        cluster_spacing: float = 1.5,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute layout with nodes grouped into clusters.
        
        Args:
            graph: NetworkX directed graph
            clusters: Mapping of node_id -> cluster_id
            iterations: Number of simulation steps
            scale: Scale factor for final positions
            cluster_spacing: Multiplier for inter-cluster spacing
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if graph.number_of_nodes() == 0:
            return {}
        
        # Group nodes by cluster
        cluster_groups = {}
        for node, cluster_id in clusters.items():
            if cluster_id not in cluster_groups:
                cluster_groups[cluster_id] = []
            cluster_groups[cluster_id].append(node)
        
        # Layout each cluster separately
        all_positions = {}
        cluster_centers = {}
        
        for cluster_id, nodes in cluster_groups.items():
            # Create subgraph for this cluster
            subgraph = graph.subgraph(nodes)
            
            # Layout the cluster
            cluster_pos = self.compute(
                subgraph,
                iterations=iterations,
                scale=scale / len(cluster_groups)
            )
            
            # Calculate cluster center
            xs = [x for x, y in cluster_pos.values()]
            ys = [y for x, y in cluster_pos.values()]
            cluster_centers[cluster_id] = (
                sum(xs) / len(xs),
                sum(ys) / len(ys)
            )
            
            all_positions.update(cluster_pos)
        
        # Layout cluster centers
        if len(cluster_groups) > 1:
            # Create meta-graph of clusters
            meta_graph = nx.DiGraph()
            meta_graph.add_nodes_from(cluster_groups.keys())
            
            # Add meta-edges for inter-cluster connections
            for u, v in graph.edges():
                cluster_u = clusters.get(u)
                cluster_v = clusters.get(v)
                if cluster_u != cluster_v:
                    meta_graph.add_edge(cluster_u, cluster_v)
            
            # Layout cluster centers
            center_positions = self.compute(
                meta_graph,
                iterations=iterations // 2,
                scale=scale * cluster_spacing
            )
            
            # Translate each cluster to its center position
            for cluster_id, (center_x, center_y) in center_positions.items():
                old_center = cluster_centers[cluster_id]
                dx = center_x - old_center[0]
                dy = center_y - old_center[1]
                
                for node in cluster_groups[cluster_id]:
                    x, y = all_positions[node]
                    all_positions[node] = (x + dx, y + dy)
        
        return all_positions
