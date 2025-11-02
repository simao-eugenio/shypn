"""
Layout Selector - Automatic Algorithm Selection

Analyzes graph topology and selects the most appropriate layout algorithm.

Decision Tree:
    1. Is graph a DAG (directed acyclic)? → Hierarchical
    2. Does graph have large cycle (>50% nodes)? → Circular
    3. Is graph highly connected (avg degree > 4)? → Force-Directed
    4. Default → Hierarchical
"""

from typing import Dict, Optional
import networkx as nx
from .base import LayoutAlgorithm
from .hierarchical import HierarchicalLayout
from .force_directed import ForceDirectedLayout
from .circular import CircularLayout
from .orthogonal import OrthogonalLayout


class LayoutSelector:
    """
    Automatic layout algorithm selection based on graph topology.
    
    Analyzes graph characteristics and recommends the best algorithm.
    """
    
    def __init__(self):
        self.algorithms = {
            'hierarchical': HierarchicalLayout(),
            'force_directed': ForceDirectedLayout(),
            'circular': CircularLayout(),
            'orthogonal': OrthogonalLayout()
        }
    
    def select(
        self, 
        graph: nx.DiGraph,
        prefer_orthogonal: bool = False
    ) -> str:
        """
        Select best algorithm for graph topology.
        
        Args:
            graph: NetworkX directed graph to analyze
            prefer_orthogonal: If True, prefer orthogonal over hierarchical
            
        Returns:
            Algorithm name: 'hierarchical', 'force_directed', 'circular', or 'orthogonal'
        """
        if graph.number_of_nodes() == 0:
            return 'hierarchical'  # Default
        
        if graph.number_of_nodes() == 1:
            return 'hierarchical'  # Doesn't matter for single node
        
        # Analyze topology
        metrics = self._analyze_graph(graph)
        
        # Decision tree
        algorithm = self._apply_decision_tree(metrics, prefer_orthogonal)
        
        return algorithm
    
    def select_with_explanation(
        self,
        graph: nx.DiGraph,
        prefer_orthogonal: bool = False
    ) -> Dict:
        """
        Select algorithm and explain the decision.
        
        Returns:
            Dictionary with:
            - algorithm: Selected algorithm name
            - reason: Explanation of why this algorithm was chosen
            - metrics: Graph topology metrics
            - alternatives: Other suitable algorithms
        """
        if graph.number_of_nodes() == 0:
            return {
                'algorithm': 'hierarchical',
                'reason': 'Default (empty graph)',
                'metrics': {},
                'alternatives': []
            }
        
        # Analyze
        metrics = self._analyze_graph(graph)
        algorithm = self._apply_decision_tree(metrics, prefer_orthogonal)
        
        # Generate explanation
        reason = self._explain_selection(algorithm, metrics)
        
        # Find alternatives
        alternatives = self._find_alternatives(algorithm, metrics)
        
        return {
            'algorithm': algorithm,
            'reason': reason,
            'metrics': metrics,
            'alternatives': alternatives
        }
    
    def _analyze_graph(self, graph: nx.DiGraph) -> Dict:
        """
        Analyze graph topology using base algorithm metrics.
        """
        # Use a concrete algorithm to get metrics
        # (all algorithms inherit the same analyze_topology method)
        hierarchical = self.algorithms['hierarchical']
        return hierarchical.analyze_topology(graph)
    
    def _apply_decision_tree(
        self,
        metrics: Dict,
        prefer_orthogonal: bool
    ) -> str:
        """
        Apply decision tree to select algorithm.
        """
        # Rule 1: Large cycle detected? → Circular
        if metrics['has_cycles'] and metrics['longest_cycle'] > metrics['node_count'] * 0.5:
            return 'circular'
        
        # Rule 2: Is DAG? → Hierarchical or Orthogonal
        if metrics['is_dag']:
            if prefer_orthogonal:
                return 'orthogonal'
            else:
                return 'hierarchical'
        
        # Rule 3: High connectivity? → Force-Directed
        if metrics['avg_degree'] > 4.0:
            return 'force_directed'
        
        # Rule 4: Dense graph? → Force-Directed
        if metrics['density'] > 0.3:
            return 'force_directed'
        
        # Rule 5: Has cycles but not dominant? → Hierarchical (handle feedback arcs)
        if metrics['has_cycles']:
            if prefer_orthogonal:
                return 'orthogonal'
            else:
                return 'hierarchical'
        
        # Default: Hierarchical
        if prefer_orthogonal:
            return 'orthogonal'
        else:
            return 'hierarchical'
    
    def _explain_selection(self, algorithm: str, metrics: Dict) -> str:
        """
        Generate human-readable explanation for algorithm selection.
        """
        reasons = {
            'hierarchical': self._explain_hierarchical(metrics),
            'force_directed': self._explain_force_directed(metrics),
            'circular': self._explain_circular(metrics),
            'orthogonal': self._explain_orthogonal(metrics)
        }
        
        return reasons.get(algorithm, "Selected based on graph topology")
    
    def _explain_hierarchical(self, metrics: Dict) -> str:
        """Explain hierarchical selection."""
        if metrics['is_dag']:
            return f"Graph is acyclic with clear directional flow ({metrics['node_count']} nodes, {metrics['edge_count']} edges). Hierarchical layout emphasizes this flow."
        else:
            return f"Graph has some cycles but hierarchical structure dominates. Using layered layout with feedback arc handling."
    
    def _explain_force_directed(self, metrics: Dict) -> str:
        """Explain force-directed selection."""
        if metrics['avg_degree'] > 4.0:
            return f"Highly connected graph (avg degree: {metrics['avg_degree']:.1f}). Force-directed layout balances complex relationships."
        elif metrics['density'] > 0.3:
            return f"Dense graph (density: {metrics['density']:.2f}). Physics-based layout prevents clutter."
        else:
            return "Complex topology without clear hierarchy. Force-directed layout provides natural clustering."
    
    def _explain_circular(self, metrics: Dict) -> str:
        """Explain circular selection."""
        cycle_pct = (metrics['longest_cycle'] / metrics['node_count']) * 100 if metrics['node_count'] > 0 else 0
        return f"Dominant cycle detected ({metrics['longest_cycle']} of {metrics['node_count']} nodes = {cycle_pct:.0f}%). Circular layout emphasizes cyclic structure."
    
    def _explain_orthogonal(self, metrics: Dict) -> str:
        """Explain orthogonal selection."""
        if metrics['is_dag']:
            return f"Acyclic graph with structured appearance preference. Orthogonal layout provides clean, grid-aligned visualization."
        else:
            return "Structured layout requested. Using grid-aligned orthogonal layout for clarity."
    
    def _find_alternatives(self, selected: str, metrics: Dict) -> list:
        """
        Find alternative algorithms that could work.
        
        Returns:
            List of (algorithm_name, reason) tuples
        """
        alternatives = []
        
        # Always consider force-directed as fallback
        if selected != 'force_directed':
            alternatives.append((
                'force_directed',
                'Universal algorithm, works for any topology'
            ))
        
        # If DAG, both hierarchical and orthogonal work
        if metrics['is_dag']:
            if selected != 'hierarchical':
                alternatives.append((
                    'hierarchical',
                    'Emphasizes directional flow in acyclic graph'
                ))
            if selected != 'orthogonal':
                alternatives.append((
                    'orthogonal',
                    'Grid-aligned version of hierarchical layout'
                ))
        
        # If has cycles, circular might work
        if metrics['has_cycles'] and selected != 'circular':
            alternatives.append((
                'circular',
                f"Graph has {metrics['longest_cycle']}-node cycle"
            ))
        
        return alternatives
    
    def get_all_suitable_algorithms(self, graph: nx.DiGraph) -> Dict[str, str]:
        """
        Get all algorithms that could work for this graph.
        
        Returns:
            Dictionary mapping algorithm names to suitability descriptions
        """
        metrics = self._analyze_graph(graph)
        suitable = {}
        
        # Hierarchical: Always works
        suitable['hierarchical'] = "Universal layered layout"
        
        # Force-directed: Always works
        suitable['force_directed'] = "Universal physics-based layout"
        
        # Orthogonal: Works well for DAGs and structured graphs
        if metrics['is_dag'] or metrics['avg_degree'] < 3:
            suitable['orthogonal'] = "Grid-aligned structured layout"
        
        # Circular: Best for graphs with cycles
        if metrics['has_cycles']:
            cycle_size = metrics['longest_cycle']
            suitable['circular'] = f"Emphasizes {cycle_size}-node cycle"
        
        return suitable
    
    def recommend_parameters(
        self,
        graph: nx.DiGraph,
        algorithm: str
    ) -> Dict:
        """
        Recommend parameters for the selected algorithm.
        
        Returns:
            Dictionary of recommended parameter values
        """
        metrics = self._analyze_graph(graph)
        n = metrics['node_count']
        
        # Base spacing on graph size
        # IMPORTANT: Larger spacing for bigger pathways to prevent overcrowding
        # This is especially critical for KEGG/SBML imports which often have 50+ nodes
        if n < 10:
            scale = 'small'
            base_spacing = 150  # Small networks: generous spacing
        elif n < 30:
            scale = 'medium'
            base_spacing = 120  # Medium networks: balanced spacing
        elif n < 60:
            scale = 'large'
            base_spacing = 100  # Large networks: compact but readable
        else:
            scale = 'very_large'
            base_spacing = 90  # Very large networks: tight but still clear
        
        params = {
            'scale': scale,
            'node_count': n
        }
        
        # Algorithm-specific parameters
        if algorithm == 'hierarchical' or algorithm == 'orthogonal':
            # Layer spacing: vertical distance between layers (reactions)
            # Node spacing: horizontal distance between nodes in same layer
            # Use 1.5x multiplier for layer spacing to emphasize flow direction
            params['layer_spacing'] = base_spacing * 1.5
            params['node_spacing'] = base_spacing
            if algorithm == 'orthogonal':
                params['grid_size'] = base_spacing
        
        elif algorithm == 'force_directed':
            # More iterations for larger graphs
            params['iterations'] = min(500, 100 + n * 5)
            params['scale'] = 1000.0
        
        elif algorithm == 'circular':
            # Radius based on number of cycle nodes
            cycle_nodes = metrics.get('longest_cycle', n)
            params['radius'] = max(200, cycle_nodes * 30)
        
        return params
