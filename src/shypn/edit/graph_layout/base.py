"""
Base Layout Algorithm

Abstract base class for all graph layout algorithms.
Provides common interface and utility methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional
import networkx as nx


class LayoutAlgorithm(ABC):
    """
    Abstract base class for graph layout algorithms.
    
    All layout algorithms must implement the compute() method which
    takes a NetworkX graph and returns node positions.
    
    Attributes:
        name: Human-readable name of the algorithm
        description: Brief description of the algorithm
        best_for: Description of graph types this algorithm works best for
    """
    
    def __init__(self):
        self.name = "Base Layout"
        self.description = "Abstract base class"
        self.best_for = "N/A"
    
    @abstractmethod
    def compute(self, graph: nx.DiGraph, **kwargs) -> Dict[str, Tuple[float, float]]:
        """
        Compute layout positions for all nodes in the graph.
        
        Args:
            graph: NetworkX directed graph to layout
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions in pixels
            
        Example:
            >>> positions = algorithm.compute(graph, spacing=100)
            >>> positions['place_1']
            (150.0, 200.0)
        """
        pass
    
    def analyze_topology(self, graph: nx.DiGraph) -> Dict:
        """
        Analyze graph topology to determine characteristics.
        
        Returns:
            Dictionary with topology metrics:
            - is_dag: bool - Is directed acyclic graph
            - node_count: int - Number of nodes
            - edge_count: int - Number of edges
            - avg_degree: float - Average node degree
            - max_degree: int - Maximum node degree
            - has_cycles: bool - Has cycles
            - longest_cycle: int - Length of longest cycle
            - connected_components: int - Number of weakly connected components
            - density: float - Graph density (0-1)
        """
        metrics = {
            'is_dag': nx.is_directed_acyclic_graph(graph),
            'node_count': graph.number_of_nodes(),
            'edge_count': graph.number_of_edges(),
            'connected_components': nx.number_weakly_connected_components(graph)
        }
        
        # Degree metrics
        degrees = [d for n, d in graph.degree()]
        metrics['avg_degree'] = sum(degrees) / len(degrees) if degrees else 0
        metrics['max_degree'] = max(degrees) if degrees else 0
        
        # Cycle detection
        try:
            cycles = list(nx.simple_cycles(graph))
            metrics['has_cycles'] = len(cycles) > 0
            metrics['longest_cycle'] = max([len(c) for c in cycles]) if cycles else 0
        except:
            metrics['has_cycles'] = False
            metrics['longest_cycle'] = 0
        
        # Density
        n = metrics['node_count']
        if n > 1:
            metrics['density'] = metrics['edge_count'] / (n * (n - 1))
        else:
            metrics['density'] = 0.0
        
        return metrics
    
    def get_layer_assignment(self, graph: nx.DiGraph) -> Dict[str, int]:
        """
        Assign nodes to layers (y-coordinates) for hierarchical layout.
        Uses longest path algorithm.
        
        Returns:
            Dictionary mapping node IDs to layer numbers (0, 1, 2, ...)
        """
        if not nx.is_directed_acyclic_graph(graph):
            # For graphs with cycles, remove feedback arcs first
            graph = self._remove_feedback_arcs(graph)
        
        layers = {}
        
        # Find source nodes (no predecessors)
        # CRITICAL: Exclude catalyst places (enzyme places with only test arcs)
        # Catalysts are NOT input places - they're decorations showing enzyme presence.
        # Including them as sources causes layout flattening (too many layer 0 nodes).
        sources = [
            n for n in graph.nodes() 
            if graph.in_degree(n) == 0 and not getattr(n, 'is_catalyst', False)
        ]
        
        if not sources:
            # Graph has no sources, use arbitrary starting node (but not a catalyst)
            non_catalyst_nodes = [n for n in graph.nodes() if not getattr(n, 'is_catalyst', False)]
            if non_catalyst_nodes:
                sources = [non_catalyst_nodes[0]]
            else:
                sources = [list(graph.nodes())[0]]
        
        # BFS layer assignment
        for source in sources:
            layers[source] = 0
        
        # Process nodes level by level
        processed = set(sources)
        current_layer = sources
        
        while current_layer:
            next_layer = []
            for node in current_layer:
                for successor in graph.successors(node):
                    if successor not in processed:
                        # Layer = max(predecessor layers) + 1
                        # CRITICAL: Exclude catalyst predecessors from layer calculation
                        # Catalysts shouldn't influence the hierarchical structure
                        pred_layers = [
                            layers.get(pred, 0) 
                            for pred in graph.predecessors(successor)
                            if not getattr(pred, 'is_catalyst', False)
                        ]
                        layers[successor] = max(pred_layers) + 1 if pred_layers else 0
                        next_layer.append(successor)
                        processed.add(successor)
            current_layer = next_layer
        
        # Position catalyst places AFTER main BFS
        # Place catalysts at the same layer as the reactions they catalyze
        # (or one layer above for visual separation)
        for node in graph.nodes():
            if getattr(node, 'is_catalyst', False) and node not in layers:
                # Find the reactions (transitions) this catalyst connects to
                successors = list(graph.successors(node))
                if successors:
                    # Position catalyst at same layer as first catalyzed reaction
                    # (Test arcs connect catalyst → transition)
                    catalyzed_layers = [layers.get(succ, 0) for succ in successors]
                    layers[node] = max(catalyzed_layers) if catalyzed_layers else 0
                else:
                    # No connections (shouldn't happen for catalysts, but fallback)
                    layers[node] = 0
        
        # Handle any remaining unprocessed nodes (disconnected components)
        for node in graph.nodes():
            if node not in layers:
                layers[node] = 0
        
        return layers
    
    def _remove_feedback_arcs(self, graph: nx.DiGraph) -> nx.DiGraph:
        """
        Remove feedback arcs to make graph acyclic.
        Uses greedy heuristic (Eades et al. 1993).
        
        Returns:
            New graph with feedback arcs removed
        """
        acyclic = graph.copy()
        
        # Simple heuristic: remove edges that create cycles
        for edge in list(acyclic.edges()):
            if not nx.is_directed_acyclic_graph(acyclic):
                # Try removing this edge
                acyclic.remove_edge(*edge)
                if nx.is_directed_acyclic_graph(acyclic):
                    continue  # Keep it removed
                else:
                    # Put it back, wasn't the problem
                    acyclic.add_edge(*edge)
        
        return acyclic
    
    def find_main_cycle(self, graph: nx.DiGraph) -> Optional[List[str]]:
        """
        Find the longest cycle in the graph.
        
        Returns:
            List of node IDs forming the cycle, or None if no cycles
        """
        try:
            cycles = list(nx.simple_cycles(graph))
            if not cycles:
                return None
            
            # Return longest cycle
            return max(cycles, key=len)
        except:
            return None
    
    def scale_positions(
        self, 
        positions: Dict[str, Tuple[float, float]], 
        scale: float = 1.0,
        center: Tuple[float, float] = (0, 0)
    ) -> Dict[str, Tuple[float, float]]:
        """
        Scale and center positions.
        
        Args:
            positions: Original positions
            scale: Scaling factor (1.0 = no change)
            center: Center point for scaling
            
        Returns:
            Scaled positions
        """
        scaled = {}
        cx, cy = center
        
        for node, (x, y) in positions.items():
            # Translate to origin, scale, translate to center
            scaled[node] = (
                (x - cx) * scale + cx,
                (y - cy) * scale + cy
            )
        
        return scaled
    
    def normalize_positions(
        self,
        positions: Dict[str, Tuple[float, float]],
        width: float = 1000.0,
        height: float = 1000.0,
        margin: float = 50.0
    ) -> Dict[str, Tuple[float, float]]:
        """
        Normalize positions to fit within specified dimensions.
        
        Args:
            positions: Original positions
            width: Target width
            height: Target height
            margin: Margin around edges
            
        Returns:
            Normalized positions
        """
        if not positions:
            return {}
        
        # Find bounding box
        xs = [x for x, y in positions.values()]
        ys = [y for x, y in positions.values()]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Calculate scale to fit in target dimensions
        x_range = max_x - min_x
        y_range = max_y - min_y
        
        if x_range == 0:
            x_range = 1
        if y_range == 0:
            y_range = 1
        
        x_scale = (width - 2 * margin) / x_range
        y_scale = (height - 2 * margin) / y_range
        
        # Use smaller scale to maintain aspect ratio
        scale = min(x_scale, y_scale)
        
        # Normalize positions
        normalized = {}
        for node, (x, y) in positions.items():
            normalized[node] = (
                (x - min_x) * scale + margin,
                (y - min_y) * scale + margin
            )
        
        return normalized
