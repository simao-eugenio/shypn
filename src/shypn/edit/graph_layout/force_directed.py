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
        k_multiplier: float = 1.5,  # Multiplier for auto-calculated k
        scale: float = 2000.0,  # Increased from 1000.0 → more canvas space
        seed: int = 42,
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute force-directed layout positions using Fruchterman-Reingold algorithm.
        
        PHYSICS MODEL:
        
        1. UNIVERSAL REPULSION (ALL mass nodes):
           - Every place repels every other place
           - Every transition repels every other transition
           - Every place repels every transition
           - Force: F_repulsion = -k² / distance
           - Prevents overlap, creates spacing
        
        2. SELECTIVE ATTRACTION (only via springs/arcs):
           - Springs (arcs) pull connected mass nodes together
           - Force: F_spring = k × distance × spring_strength
           - Spring strength = arc weight (stoichiometry)
           - Example: 2A + B → C means A has 2× stronger spring to reaction
        
        3. EQUILIBRIUM:
           - System converges when forces balance on each mass node
           - Connected nodes: pulled together by spring, pushed apart by repulsion
           - Disconnected nodes: only repulsion, pushed to maximum separation
        
        Args:
            graph: NetworkX directed graph (mass nodes + springs)
            iterations: Number of physics simulation steps (more = better, slower)
            k: Optimal distance between mass nodes (None = auto-calculate using k_multiplier)
            k_multiplier: Multiplier for auto-calculated k (ignored if k is provided)
            scale: Scale factor for final positions (canvas size)
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
        # NetworkX spring_layout uses k internally as 1/sqrt(n) in normalized [0,1] space
        # To control spacing, we adjust the 'scale' parameter instead
        if k is None:
            # User wants more/less spacing via k_multiplier
            # Achieve this by scaling the output coordinates
            adjusted_scale = scale * k_multiplier
        else:
            # User provided explicit k value (rare)
            adjusted_scale = k
        
        scale_to_use = adjusted_scale if k is None else k
        
        # CRITICAL: Convert to undirected graph for UNIVERSAL repulsion
        # DiGraph (directed): Only connected nodes repel → places don't repel other places!
        # Graph (undirected): ALL nodes repel ALL other nodes → correct physics!
        if isinstance(graph, nx.DiGraph):
            # Manually convert to undirected to avoid deepcopy issues with GObject references
            # NetworkX's to_undirected() uses deepcopy which fails on GObject descendants
            undirected_graph = nx.Graph()
            
            # Copy nodes with their attributes (type='place' or 'transition')
            for node, data in graph.nodes(data=True):
                undirected_graph.add_node(node, **data)
            
            # Copy edges with their weights (no deepcopy, just reference)
            for u, v, data in graph.edges(data=True):
                weight = data.get('weight', 1.0)
                undirected_graph.add_edge(u, v, weight=weight)
            
            print(f"🔬 Force-directed: ✓ Converted DiGraph → Graph for universal repulsion")
        else:
            undirected_graph = graph
            print(f"🔬 Force-directed: Already Graph (undirected)")
        
        # Count node types for diagnostics
        places = [n for n, d in undirected_graph.nodes(data=True) if d.get('type') == 'place']
        transitions = [n for n, d in undirected_graph.nodes(data=True) if d.get('type') == 'transition']
        print(f"🔬 Force-directed: Graph contents:")
        print(f"   - Total nodes: {undirected_graph.number_of_nodes()}")
        print(f"   - Places: {len(places)}")
        print(f"   - Transitions: {len(transitions)}")
        print(f"   - Edges: {undirected_graph.number_of_edges()}")
        
        if len(places) < 5:
            print(f"   ⚠️ WARNING: Very few places detected!")
            print(f"   Place IDs: {places}")
        elif len(places) <= 10:
            print(f"   Place IDs (all {len(places)}): {places}")
        
        # Check if edges have weights (arc stoichiometry)
        has_weights = any('weight' in undirected_graph[u][v] for u, v in undirected_graph.edges())
        
        # Use NetworkX spring_layout (Fruchterman-Reingold implementation)
        # If edges have weights (stoichiometry), use them as spring strength
        #
        # NetworkX spring_layout parameters:
        # - k: optimal distance between nodes in normalized space (None = auto: 1/sqrt(n))
        # - scale: output coordinate scale (scales the final positions)
        # - iterations: number of iterations for force-directed algorithm
        # - weight: edge attribute name for spring strength
        layout_params = {
            'k': None,  # Let NetworkX auto-calculate: k = 1/sqrt(n)
            'iterations': iterations,
            'scale': scale_to_use,  # Use adjusted scale for spacing control
            'center': (0, 0),
            'seed': seed
        }
        
        if has_weights:
            # Use arc weights as spring strength (stoichiometry-based)
            layout_params['weight'] = 'weight'
            print(f"🔬 Force-directed: Using arc weights as spring strength")
        
        print(f"🔬 Force-directed: Parameters: iterations={iterations}, scale={scale_to_use:.1f}, k_multiplier={k_multiplier}x")
        
        positions = nx.spring_layout(undirected_graph, **layout_params)
        
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
        
        # FIXED: Use k=None to let NetworkX auto-calculate optimal distance
        # Use scale parameter to control output spacing instead of manipulating k
        
        # Use NetworkX spring_layout with weights
        positions = nx.spring_layout(
            graph,
            k=None,  # Auto-calculate: k = 1/sqrt(n)
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
