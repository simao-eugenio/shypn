"""Centrality analysis for Petri nets."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Optional

if TYPE_CHECKING:
    import networkx as nx


def _nx():
    """Lazy networkx import — deferred to first Topology panel use."""
    import networkx
    return networkx


from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult
from ..base.exceptions import TopologyAnalysisError


class CentralityAnalyzer(TopologyAnalyzer):
    """Analyzer for computing node centrality measures in Petri nets.
    
    Centrality measures identify important nodes in a network beyond simple degree.
    In biochemical networks, central nodes are:
    - Betweenness: Metabolites on many pathways (pyruvate, acetyl-CoA)
    - Closeness: Metabolites near all others (central intermediates)
    - Eigenvector: Metabolites connected to important metabolites (influence)
    - PageRank: Metabolites with high-quality connections
    
    This analyzer computes multiple centrality measures:
    - Betweenness centrality: Fraction of shortest paths through node
    - Closeness centrality: Inverse average distance to all nodes
    - Eigenvector centrality: Connections to high-centrality nodes
    - PageRank: Google's algorithm for node importance
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = CentralityAnalyzer(model)
        result = analyzer.analyze(measures=['betweenness', 'closeness'])
        
        for node in result.get('central_nodes', []):
            print(f"{node['name']}: betweenness={node['betweenness']:.3f}")
    """
    
    def analyze(  # type: ignore[override]
        self,
        measures: Optional[List[str]] = None,
        top_n: int = 20,
        node_type: Optional[str] = None,
        normalize: bool = True,
        weighted: bool = False
    ) -> AnalysisResult:
        """Compute centrality measures for nodes in the Petri net.
        
        Args:
            measures: List of centrality measures to compute 
                     ['betweenness', 'closeness', 'eigenvector', 'pagerank']
                     (None = all measures)
            top_n: Return top N nodes by each measure
            node_type: Filter by node type ('place', 'transition', or None for all)
            normalize: Normalize centrality values to [0, 1]
            weighted: Use arc weights in calculations
            
        Returns:
            AnalysisResult with:
                - central_nodes: List of node centrality dicts
                - measures_computed: List of measures computed
                - top_betweenness: Top N by betweenness centrality
                - top_closeness: Top N by closeness centrality
                - top_eigenvector: Top N by eigenvector centrality
                - top_pagerank: Top N by PageRank
                - summary: Human-readable summary
                - metadata: Analysis parameters and timing
        """
        start_time = self._start_timer()
        
        try:
            nx = _nx()
            self._validate_model()
            if measures is None:
                measures = ['betweenness', 'closeness', 'eigenvector', 'pagerank']
            
            # Validate measures
            valid_measures = ['betweenness', 'closeness', 'eigenvector', 'pagerank']
            for measure in measures:
                if measure not in valid_measures:
                    raise TopologyAnalysisError(
                        f"Invalid centrality measure: {measure}. "
                        f"Valid measures: {valid_measures}"
                    )
            
            # Build graph
            graph = self._build_graph()
            
            # Filter nodes by type if requested
            if node_type:
                nodes = self._filter_nodes_by_type(graph, node_type)
            else:
                nodes = list(graph.nodes())
            
            if not nodes:
                return AnalysisResult(
                    success=True,
                    data={
                        'central_nodes': [],
                        'measures_computed': measures,
                        'node_count': 0,
                        'summary': f'No nodes of type {node_type} found'
                    },
                    metadata={'analysis_time': self._end_timer(start_time)}
                )
            
            # Compute centrality measures
            centrality_data = {}
            
            if 'betweenness' in measures:
                centrality_data['betweenness'] = self._compute_betweenness(
                    graph, nodes, normalize, weighted
                )
            
            if 'closeness' in measures:
                centrality_data['closeness'] = self._compute_closeness(
                    graph, nodes, normalize
                )
            
            if 'eigenvector' in measures:
                centrality_data['eigenvector'] = self._compute_eigenvector(
                    graph, nodes, normalize, weighted
                )
            
            if 'pagerank' in measures:
                centrality_data['pagerank'] = self._compute_pagerank(
                    graph, nodes, normalize, weighted
                )
            
            # Build central_nodes list with all measures per node
            central_nodes = []
            for node_id in nodes:
                node_data = {
                    'id': node_id,
                    'name': self._get_node_name(node_id),
                    'type': self._get_node_type(node_id)
                }
                
                # Add centrality values
                for measure, values in centrality_data.items():
                    node_data[measure] = values.get(node_id, 0.0)  # type: ignore[assignment]
                
                central_nodes.append(node_data)
            
            # Sort by first measure for general ordering
            if central_nodes and measures:
                first_measure = measures[0]
                central_nodes.sort(
                    key=lambda x: x.get(first_measure, 0),
                    reverse=True
                )
            
            # Create top-N lists for each measure
            top_results = {}
            for measure in measures:
                sorted_nodes = sorted(
                    central_nodes,
                    key=lambda x: x.get(measure, 0),
                    reverse=True
                )
                top_results[f'top_{measure}'] = sorted_nodes[:top_n]
            
            # Generate summary
            summary_lines = [
                f"Centrality Analysis: {len(central_nodes)} nodes analyzed"
            ]
            
            for measure in measures:
                top_node = top_results[f'top_{measure}'][0] if top_results[f'top_{measure}'] else None
                if top_node:
                    summary_lines.append(
                        f"Top {measure}: {top_node['name']} "
                        f"({top_node[measure]:.4f})"
                    )
            
            return AnalysisResult(
                success=True,
                data={
                    'central_nodes': central_nodes,
                    'measures_computed': measures,
                    'node_count': len(central_nodes),
                    **top_results,
                    'summary': '\n'.join(summary_lines)
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'top_n': top_n,
                    'node_type_filter': node_type,
                    'normalized': normalize,
                    'weighted': weighted
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Centrality analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _compute_betweenness(
        self,
        graph: nx.Graph,
        nodes: List[str],
        normalize: bool,
        weighted: bool
    ) -> Dict[str, float]:
        """Compute betweenness centrality.
        
        Betweenness measures the fraction of shortest paths that pass through
        each node. High betweenness indicates a node is on many paths between
        other nodes (a bridge or bottleneck).
        """
        nx = _nx()
        weight = 'weight' if weighted else None
        
        # Compute for all nodes
        all_betweenness = nx.betweenness_centrality(
            graph,
            normalized=normalize,
            weight=weight
        )
        
        # Filter to requested nodes
        return {node: all_betweenness.get(node, 0.0) for node in nodes}
    
    def _compute_closeness(
        self,
        graph: nx.Graph,
        nodes: List[str],
        normalize: bool
    ) -> Dict[str, float]:
        """Compute closeness centrality.
        
        Closeness measures how close a node is to all other nodes (inverse of
        average distance). High closeness indicates a node can quickly reach
        all others.
        """
        nx = _nx()
        # Handle both directed and undirected graphs
        # For directed graphs, we use the undirected version for simplicity
        if graph.is_directed():
            undirected_graph = graph.to_undirected()
        else:
            undirected_graph = graph
        
        # Handle disconnected graphs
        all_closeness = {}
        
        if nx.is_connected(undirected_graph):
            all_closeness = nx.closeness_centrality(
                undirected_graph,
                distance=None,
                wf_improved=True
            )
        else:
            # For disconnected graphs, use subgraphs
            for component in nx.connected_components(undirected_graph):
                subgraph = undirected_graph.subgraph(component)
                component_closeness = nx.closeness_centrality(
                    subgraph,
                    distance=None,
                    wf_improved=True
                )
                all_closeness.update(component_closeness)
        
        # Filter to requested nodes
        return {node: all_closeness.get(node, 0.0) for node in nodes}
    
    def _compute_eigenvector(
        self,
        graph: nx.Graph,
        nodes: List[str],
        normalize: bool,
        weighted: bool
    ) -> Dict[str, float]:
        """Compute eigenvector centrality.
        
        Eigenvector centrality measures a node's influence based on connections
        to other high-centrality nodes. High eigenvector indicates a node is
        connected to important nodes.
        """
        nx = _nx()
        weight = 'weight' if weighted else None
        
        # Convert to undirected for eigenvector centrality
        if graph.is_directed():
            undirected_graph = graph.to_undirected()
        else:
            undirected_graph = graph
        
        try:
            all_eigenvector = nx.eigenvector_centrality(
                undirected_graph,
                max_iter=500,
                weight=weight
            )
        except nx.PowerIterationFailedConvergence:
            # Fallback to eigenvector_centrality_numpy if available
            try:
                all_eigenvector = nx.eigenvector_centrality_numpy(undirected_graph, weight=weight)
            except (AttributeError, ImportError, ValueError) as e:
                # Numpy centrality not available or also failed
                import logging
                logging.getLogger(__name__).debug(f"Eigenvector centrality fallback failed: {e}")
                # If still fails, return zeros
                all_eigenvector = {node: 0.0 for node in undirected_graph.nodes()}
        
        # Filter to requested nodes
        return {node: all_eigenvector.get(node, 0.0) for node in nodes}
    
    def _compute_pagerank(
        self,
        graph: nx.Graph,
        nodes: List[str],
        normalize: bool,
        weighted: bool
    ) -> Dict[str, float]:
        """Compute PageRank centrality.
        
        PageRank (Google's algorithm) measures importance based on the quality
        and quantity of connections. High PageRank indicates a node receives
        connections from important nodes.
        """
        nx = _nx()
        weight = 'weight' if weighted else None
        
        # Convert to directed graph for PageRank
        if graph.is_directed():
            digraph = graph
        else:
            digraph = graph.to_directed()
        
        all_pagerank = nx.pagerank(
            digraph,
            alpha=0.85,
            max_iter=500,
            weight=weight
        )
        
        # Normalize to [0, 1] if requested
        if normalize and all_pagerank:
            max_pr = max(all_pagerank.values())
            if max_pr > 0:
                all_pagerank = {
                    node: val / max_pr
                    for node, val in all_pagerank.items()
                }
        
        # Filter to requested nodes
        return {node: all_pagerank.get(node, 0.0) for node in nodes}
    
    def _get_node_type(self, node_id: str) -> str:
        """Get node type (place or transition)."""
        if node_id.startswith('p_'):
            return 'place'
        elif node_id.startswith('t_'):
            return 'transition'
        else:
            return 'unknown'
