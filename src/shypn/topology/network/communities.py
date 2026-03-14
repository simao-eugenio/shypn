"""Community detection analyzer for Petri nets."""

from typing import List, Optional, Set
import networkx as nx
from networkx.algorithms import community

from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult
from ..base.exceptions import TopologyAnalysisError


class CommunitiesAnalyzer(TopologyAnalyzer):
    """Analyzer for detecting communities (modules) in Petri nets.
    
    Communities are groups of nodes that are more densely connected to each other
    than to the rest of the network. In biochemical networks, communities often
    correspond to:
    - Metabolic pathways (glycolysis, TCA cycle, etc.)
    - Functional modules (energy metabolism, biosynthesis)
    - Cellular compartments (mitochondrial, cytoplasmic processes)
    
    This analyzer uses multiple community detection algorithms:
    - Louvain: Fast modularity-based method (default)
    - Greedy modularity: Hierarchical agglomerative method
    - Label propagation: Fast semi-synchronous method
    - Girvan-Newman: Edge betweenness-based method
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = CommunitiesAnalyzer(model)
        result = analyzer.analyze(method='louvain')
        
        for comm in result.get('communities', []):
            print(f"Community {comm['id']}: {len(comm['nodes'])} nodes")
            print(f"  Modularity: {comm['modularity']:.3f}")
    """
    
    def analyze(  # type: ignore[override]
        self,
        method: str = 'louvain',
        resolution: float = 1.0,
        min_community_size: int = 2,
        node_type: Optional[str] = None
    ) -> AnalysisResult:
        """Detect communities in the Petri net.
        
        Args:
            method: Community detection method
                   'louvain' (fast, default)
                   'greedy_modularity' (hierarchical)
                   'label_propagation' (very fast)
                   'girvan_newman' (accurate but slow)
            resolution: Resolution parameter for modularity (higher = more communities)
            min_community_size: Minimum nodes per community
            node_type: Filter by node type ('place', 'transition', or None for all)
            
        Returns:
            AnalysisResult with:
                - communities: List of community dicts
                - num_communities: Number of communities found
                - modularity: Overall modularity score
                - coverage: Fraction of edges within communities
                - summary: Human-readable summary
                - metadata: Analysis parameters and timing
        """
        start_time = self._start_timer()
        
        try:
            self._validate_model()
            
            # Validate method
            valid_methods = ['louvain', 'greedy_modularity', 'label_propagation', 'girvan_newman']
            if method not in valid_methods:
                raise TopologyAnalysisError(
                    f"Invalid community detection method: {method}. "
                    f"Valid methods: {valid_methods}"
                )
            
            # Build graph
            graph = self._build_graph()
            
            # Convert to undirected for community detection
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
                        'communities': [],
                        'num_communities': 0,
                        'modularity': 0.0,
                        'coverage': 0.0,
                        'summary': 'No nodes available for community detection'
                    },
                    metadata={'analysis_time': self._end_timer(start_time)}
                )
            
            # Check if graph has any edges (needed for community detection)
            if undirected_graph.number_of_edges() == 0:
                # Each node is its own community
                single_communities = [{node} for node in undirected_graph.nodes()]
                communities = [
                    {
                        'id': idx,
                        'nodes': [node],
                        'size': 1,
                        'node_names': [self._get_node_name(node)]
                    }
                    for idx, node in enumerate(undirected_graph.nodes())
                ]
                
                return AnalysisResult(
                    success=True,
                    data={
                        'communities': communities,
                        'num_communities': len(communities),
                        'modularity': 0.0,
                        'coverage': 0.0,
                        'summary': f'Found {len(communities)} isolated nodes (no edges)'
                    },
                    metadata={
                        'analysis_time': self._end_timer(start_time),
                        'method': method,
                        'total_nodes': len(undirected_graph.nodes())
                    }
                )
            
            # Detect communities using selected method
            if method == 'louvain':
                communities_sets = self._detect_louvain(undirected_graph, resolution)
            elif method == 'greedy_modularity':
                communities_sets = self._detect_greedy_modularity(undirected_graph)
            elif method == 'label_propagation':
                communities_sets = self._detect_label_propagation(undirected_graph)
            elif method == 'girvan_newman':
                communities_sets = self._detect_girvan_newman(undirected_graph)
            
            # Filter by minimum size
            communities_sets = [
                comm for comm in communities_sets
                if len(comm) >= min_community_size
            ]
            
            # Build community data structures
            communities = []
            for idx, comm_nodes in enumerate(communities_sets):
                comm_data = {
                    'id': idx,
                    'nodes': sorted(list(comm_nodes)),
                    'size': len(comm_nodes),
                    'node_names': [self._get_node_name(n) for n in comm_nodes]
                }
                communities.append(comm_data)
            
            # Calculate modularity
            if communities_sets and undirected_graph.number_of_edges() > 0:
                try:
                    # Ensure all nodes are accounted for in communities
                    all_comm_nodes = set()
                    for comm in communities_sets:
                        all_comm_nodes.update(comm)
                    
                    # Add any missing nodes as singleton communities
                    missing_nodes = set(undirected_graph.nodes()) - all_comm_nodes
                    if missing_nodes:
                        communities_sets_complete = list(communities_sets) + [{node} for node in missing_nodes]
                    else:
                        communities_sets_complete = communities_sets
                    
                    modularity_score = community.modularity(
                        undirected_graph,
                        communities_sets_complete
                    )
                except Exception:
                    # If modularity calculation fails, set to 0
                    modularity_score = 0.0
            else:
                modularity_score = 0.0
            
            # Calculate coverage (fraction of edges within communities)
            coverage_score = self._calculate_coverage(
                undirected_graph,
                communities_sets
            )
            
            # Generate summary
            summary = self._create_summary(
                len(communities),
                modularity_score,
                coverage_score,
                method
            )
            
            return AnalysisResult(
                success=True,
                data={
                    'communities': communities,
                    'num_communities': len(communities),
                    'modularity': modularity_score,
                    'coverage': coverage_score,
                    'summary': summary
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'method': method,
                    'resolution': resolution,
                    'min_community_size': min_community_size,
                    'node_type_filter': node_type,
                    'total_nodes': len(undirected_graph.nodes())
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Community detection failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _detect_louvain(
        self,
        graph: nx.Graph,
        resolution: float
    ) -> List[Set[str]]:
        """Detect communities using Louvain method.
        
        Louvain is a fast greedy optimization method that maximizes modularity.
        """
        try:
            # Try to use louvain_communities if available (NetworkX >= 2.5)
            communities_dict = community.louvain_communities(
                graph,
                resolution=resolution,
                seed=42
            )
            return list(communities_dict)
        except AttributeError:
            # Fallback for older NetworkX versions
            try:
                from community import community_louvain
                partition = community_louvain.best_partition(graph, resolution=resolution)
                # Convert partition dict to list of sets
                communities_dict = {}
                for node, comm_id in partition.items():
                    if comm_id not in communities_dict:
                        communities_dict[comm_id] = set()
                    communities_dict[comm_id].add(node)
                return list(communities_dict.values())
            except ImportError:
                # If python-louvain not available, use greedy modularity as fallback
                return self._detect_greedy_modularity(graph)
    
    def _detect_greedy_modularity(
        self,
        graph: nx.Graph
    ) -> List[Set[str]]:
        """Detect communities using greedy modularity optimization.
        
        Hierarchical agglomerative method that merges communities to maximize modularity.
        """
        communities_generator = community.greedy_modularity_communities(graph)
        return list(communities_generator)
    
    def _detect_label_propagation(
        self,
        graph: nx.Graph
    ) -> List[Set[str]]:
        """Detect communities using label propagation.
        
        Fast semi-synchronous method where nodes adopt labels from their neighbors.
        """
        communities_generator = community.label_propagation_communities(graph)
        return list(communities_generator)
    
    def _detect_girvan_newman(
        self,
        graph: nx.Graph,
        num_communities: Optional[int] = None
    ) -> List[Set[str]]:
        """Detect communities using Girvan-Newman edge betweenness method.
        
        Iteratively removes edges with highest betweenness. Accurate but slow.
        """
        communities_generator = community.girvan_newman(graph)
        
        # If num_communities not specified, try to find optimal number
        # by maximizing modularity
        if num_communities is None:
            best_communities = None
            best_modularity = -1
            
            # Try first 10 levels
            for _ in range(min(10, len(graph.nodes()) - 1)):
                try:
                    current_communities = next(communities_generator)
                    current_communities_list = list(current_communities)
                    current_modularity = community.modularity(
                        graph,
                        current_communities_list
                    )
                    
                    if current_modularity > best_modularity:
                        best_modularity = current_modularity
                        best_communities = current_communities_list
                except StopIteration:
                    break
            
            return best_communities if best_communities else [set(graph.nodes())]
        else:
            # Get specific number of communities
            for _ in range(num_communities - 1):
                try:
                    current_communities = next(communities_generator)
                except StopIteration:
                    break
            return list(current_communities)
    
    def _calculate_coverage(
        self,
        graph: nx.Graph,
        communities: List[Set[str]]
    ) -> float:
        """Calculate coverage: fraction of edges within communities."""
        if not communities or graph.number_of_edges() == 0:
            return 0.0
        
        intra_community_edges = 0
        total_edges = graph.number_of_edges()
        
        for comm in communities:
            subgraph = graph.subgraph(comm)
            intra_community_edges += subgraph.number_of_edges()
        
        return intra_community_edges / total_edges
    
    def _create_summary(
        self,
        num_communities: int,
        modularity: float,
        coverage: float,
        method: str
    ) -> str:
        """Create human-readable summary."""
        if num_communities == 0:
            return "No communities detected"
        
        lines = [
            f"Detected {num_communities} communit{'y' if num_communities == 1 else 'ies'} using {method}",
            f"• Modularity: {modularity:.3f}",
            f"• Coverage: {coverage:.1%}"
        ]
        
        return "\n".join(lines)
