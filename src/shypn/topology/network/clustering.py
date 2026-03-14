"""Clustering coefficient analyzer for Petri nets."""

from typing import List, Dict, Optional
import networkx as nx

from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult


class ClusteringAnalyzer(TopologyAnalyzer):
    """Analyzer for computing clustering coefficients in Petri nets.
    
    Clustering coefficient measures the degree to which nodes cluster together,
    indicating local density of connections. In biochemical networks:
    - High clustering: Tightly integrated pathway modules
    - Low clustering: Star-like hub-dominated structures
    - Transitivity: Overall network cohesiveness
    
    This analyzer computes:
    - Local clustering: Per-node clustering coefficient
    - Global clustering: Average clustering coefficient
    - Transitivity: Ratio of triangles to connected triples
    - Triangles: Count of closed triplets per node
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = ClusteringAnalyzer(model)
        result = analyzer.analyze()
        
        print(f"Average clustering: {result.get('average_clustering'):.3f}")
        print(f"Transitivity: {result.get('transitivity'):.3f}")
        
        for node in result.get('highly_clustered_nodes', []):
            print(f"{node['name']}: {node['clustering']:.3f}")
    """
    
    def analyze(  # type: ignore[override]
        self,
        top_n: int = 20,
        node_type: Optional[str] = None,
        include_triangles: bool = True
    ) -> AnalysisResult:
        """Compute clustering coefficients for the Petri net.
        
        Args:
            top_n: Return top N nodes by clustering coefficient
            node_type: Filter by node type ('place', 'transition', or None for all)
            include_triangles: Include triangle counts per node
            
        Returns:
            AnalysisResult with:
                - node_clustering: List of node clustering dicts
                - average_clustering: Mean clustering coefficient
                - transitivity: Global clustering coefficient
                - highly_clustered_nodes: Top N nodes by clustering
                - distribution: Clustering coefficient distribution stats
                - summary: Human-readable summary
                - metadata: Analysis parameters and timing
        """
        start_time = self._start_timer()
        
        try:
            self._validate_model()
            
            # Build graph
            graph = self._build_graph()
            
            # Convert to undirected for clustering analysis
            if graph.is_directed():
                undirected_graph = graph.to_undirected()
            else:
                undirected_graph = graph
            
            # Filter nodes by type if requested
            if node_type:
                nodes_to_keep = self._filter_nodes_by_type(undirected_graph, node_type)
                undirected_graph = undirected_graph.subgraph(nodes_to_keep).copy()
            
            if len(undirected_graph.nodes()) == 0:
                return AnalysisResult(
                    success=True,
                    data={
                        'node_clustering': [],
                        'average_clustering': 0.0,
                        'transitivity': 0.0,
                        'highly_clustered_nodes': [],
                        'distribution': self._empty_distribution(),
                        'summary': 'No nodes available for clustering analysis'
                    },
                    metadata={'analysis_time': self._end_timer(start_time)}
                )
            
            # Compute local clustering coefficients
            local_clustering = nx.clustering(undirected_graph)
            
            # Compute global metrics
            average_clustering = nx.average_clustering(undirected_graph)
            transitivity = nx.transitivity(undirected_graph)
            
            # Compute triangles if requested
            triangles_dict = {}
            if include_triangles:
                triangles_dict = nx.triangles(undirected_graph)
            
            # Build node clustering data
            node_clustering = []
            for node_id in undirected_graph.nodes():
                node_data = {
                    'id': node_id,
                    'name': self._get_node_name(node_id),
                    'type': self._get_node_type(node_id),
                    'clustering': local_clustering.get(node_id, 0.0),
                    'degree': undirected_graph.degree(node_id)
                }
                
                if include_triangles:
                    node_data['triangles'] = triangles_dict.get(node_id, 0)
                
                node_clustering.append(node_data)
            
            # Sort by clustering coefficient (descending)
            node_clustering.sort(key=lambda x: x['clustering'], reverse=True)
            
            # Get top N highly clustered nodes
            highly_clustered = node_clustering[:top_n]
            
            # Compute distribution statistics
            clustering_values = [n['clustering'] for n in node_clustering]
            distribution = self._compute_distribution(clustering_values)
            
            # Generate summary
            summary = self._create_summary(
                len(node_clustering),
                average_clustering,
                transitivity,
                distribution
            )
            
            return AnalysisResult(
                success=True,
                data={
                    'node_clustering': node_clustering,
                    'average_clustering': average_clustering,
                    'transitivity': transitivity,
                    'highly_clustered_nodes': highly_clustered,
                    'distribution': distribution,
                    'summary': summary
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'top_n': top_n,
                    'node_type_filter': node_type,
                    'include_triangles': include_triangles,
                    'total_nodes': len(node_clustering)
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Clustering analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def get_node_clustering(self, node_id: str) -> Optional[float]:
        """Get clustering coefficient for a specific node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Clustering coefficient (0-1) or None if node not found
        """
        try:
            graph = self._build_graph()
            if graph.is_directed():
                graph = graph.to_undirected()
            
            if node_id not in graph.nodes():
                return None
            
            clustering = nx.clustering(graph, node_id)
            return float(clustering)
            
        except Exception:
            return None
    
    def identify_clustered_regions(
        self,
        min_clustering: float = 0.5,
        min_nodes: int = 3
    ) -> AnalysisResult:
        """Identify regions with high clustering coefficients.
        
        Args:
            min_clustering: Minimum clustering coefficient threshold
            min_nodes: Minimum nodes in region
            
        Returns:
            AnalysisResult with clustered regions
        """
        start_time = self._start_timer()
        
        try:
            self._validate_model()
            
            # Get all node clustering coefficients
            result = self.analyze()
            if not result.success:
                return result
            
            # Filter high clustering nodes
            high_clustering_nodes = [
                node for node in result.data['node_clustering']
                if node['clustering'] >= min_clustering
            ]
            
            # Group into regions based on connectivity
            graph = self._build_graph()
            if graph.is_directed():
                graph = graph.to_undirected()
            
            high_clustering_ids = [n['id'] for n in high_clustering_nodes]
            subgraph = graph.subgraph(high_clustering_ids)
            
            # Find connected components as regions
            regions = []
            for idx, component in enumerate(nx.connected_components(subgraph)):
                if len(component) >= min_nodes:
                    region_nodes = [
                        node for node in high_clustering_nodes
                        if node['id'] in component
                    ]
                    
                    regions.append({
                        'id': idx,
                        'nodes': region_nodes,
                        'size': len(region_nodes),
                        'avg_clustering': sum(n['clustering'] for n in region_nodes) / len(region_nodes)
                    })
            
            summary = f"Found {len(regions)} highly clustered region(s) with clustering ≥ {min_clustering}"
            
            return AnalysisResult(
                success=True,
                data={
                    'regions': regions,
                    'num_regions': len(regions),
                    'summary': summary
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'min_clustering': min_clustering,
                    'min_nodes': min_nodes
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Region identification failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _compute_distribution(self, values: List[float]) -> Dict[str, float]:
        """Compute distribution statistics for clustering values."""
        if not values:
            return self._empty_distribution()
        
        import statistics
        
        return {
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'count': len(values)
        }
    
    def _empty_distribution(self) -> Dict[str, float]:
        """Return empty distribution."""
        return {
            'min': 0.0,
            'max': 0.0,
            'mean': 0.0,
            'median': 0.0,
            'stdev': 0.0,
            'count': 0
        }
    
    def _get_node_type(self, node_id: str) -> str:
        """Get node type (place or transition)."""
        if node_id.startswith('p_'):
            return 'place'
        elif node_id.startswith('t_'):
            return 'transition'
        else:
            return 'unknown'
    
    def _create_summary(
        self,
        num_nodes: int,
        avg_clustering: float,
        transitivity: float,
        distribution: Dict[str, float]
    ) -> str:
        """Create human-readable summary."""
        if num_nodes == 0:
            return "No nodes analyzed"
        
        lines = [
            f"Clustering Analysis: {num_nodes} nodes",
            f"• Average clustering: {avg_clustering:.3f}",
            f"• Transitivity: {transitivity:.3f}",
            f"• Range: {distribution['min']:.3f} - {distribution['max']:.3f}"
        ]
        
        return "\n".join(lines)
