"""Path finding analyzer for Petri nets."""

from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx

from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult
from ..base.exceptions import TopologyAnalysisError


class PathAnalyzer(TopologyAnalyzer):
    """Analyzer for finding paths in Petri nets.
    
    This analyzer finds various types of paths between nodes in the Petri net:
    - Shortest paths (Dijkstra's algorithm)
    - All simple paths (depth-first search)
    - Critical paths (longest weighted paths)
    
    For biochemical networks, paths represent:
    - Metabolic routes (e.g., Glucose → Pyruvate → Acetyl-CoA)
    - Substrate fate tracking (14C-labeled compound pathways)
    - Alternative pathways (glycolysis vs pentose phosphate)
    - Signaling cascades
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = PathAnalyzer(model)
        
        # Find shortest path between two places
        result = analyzer.find_shortest_path(source_id=1, target_id=5)
        
        # Find all simple paths
        result = analyzer.find_all_paths(source_id=1, target_id=5, max_length=10)
    """
    
    def analyze(
        self,
        source_id: Optional[int] = None,
        target_id: Optional[int] = None,
        max_paths: int = 100,
        max_length: int = 20
    ) -> AnalysisResult:
        """Analyze paths in the Petri net.
        
        If source and target are specified, finds paths between them.
        Otherwise, analyzes general path properties.
        
        Args:
            source_id: Source node ID (optional)
            target_id: Target node ID (optional)
            max_paths: Maximum number of paths to return
            max_length: Maximum path length to consider
            
        Returns:
            AnalysisResult with path information
        """
        start_time = self._start_timer()
        
        try:
            self._validate_model()
            
            # Build graph
            graph = self._build_graph()
            
            if source_id is not None and target_id is not None:
                # Find paths between specific nodes
                return self._analyze_specific_paths(
                    graph, source_id, target_id, max_paths, max_length, start_time
                )
            else:
                # Analyze general path properties
                return self._analyze_general_paths(
                    graph, max_paths, max_length, start_time
                )
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Path analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def find_shortest_path(
        self,
        source_id: int,
        target_id: int
    ) -> AnalysisResult:
        """Find shortest path between two nodes.
        
        Uses Dijkstra's algorithm for weighted graphs.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            AnalysisResult with shortest path information
        """
        start_time = self._start_timer()
        
        try:
            self._validate_model()
            graph = self._build_graph()
            
            # Check if nodes exist
            if source_id not in graph or target_id not in graph:
                return AnalysisResult(
                    success=False,
                    errors=["Source or target node not found in graph"],
                    metadata={'analysis_time': self._end_timer(start_time)}
                )
            
            # Find shortest path
            try:
                path = nx.shortest_path(graph, source_id, target_id)
                length = len(path) - 1  # Number of edges
                
                # Analyze path
                path_info = self._analyze_path(path, graph)
                
                summary = f"Shortest path: {length} step(s)"
                
                return AnalysisResult(
                    success=True,
                    data={
                        'path': path_info,
                        'length': length,
                        'exists': True,
                    },
                    summary=summary,
                    metadata={
                        'source_id': source_id,
                        'target_id': target_id,
                        'analysis_time': self._end_timer(start_time),
                    }
                )
            
            except nx.NetworkXNoPath:
                return AnalysisResult(
                    success=True,
                    data={'exists': False},
                    summary="No path exists between nodes",
                    metadata={
                        'source_id': source_id,
                        'target_id': target_id,
                        'analysis_time': self._end_timer(start_time),
                    }
                )
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Shortest path search failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def find_all_paths(
        self,
        source_id: int,
        target_id: int,
        max_paths: int = 100,
        max_length: int = 20
    ) -> AnalysisResult:
        """Find all simple paths between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_paths: Maximum number of paths to return
            max_length: Maximum path length
            
        Returns:
            AnalysisResult with all paths information
        """
        start_time = self._start_timer()
        
        try:
            self._validate_model()
            graph = self._build_graph()
            
            # Check if nodes exist
            if source_id not in graph or target_id not in graph:
                return AnalysisResult(
                    success=False,
                    errors=["Source or target node not found in graph"],
                    metadata={'analysis_time': self._end_timer(start_time)}
                )
            
            # Find all simple paths with cutoff
            all_paths = list(nx.all_simple_paths(
                graph, source_id, target_id, cutoff=max_length
            ))
            
            total_count = len(all_paths)
            truncated = total_count > max_paths
            
            if truncated:
                # Keep shortest paths first
                all_paths.sort(key=len)
                paths_to_analyze = all_paths[:max_paths]
            else:
                paths_to_analyze = all_paths
            
            # Analyze each path
            path_data = []
            for path_nodes in paths_to_analyze:
                path_info = self._analyze_path(path_nodes, graph)
                path_data.append(path_info)
            
            # Find shortest and longest
            if path_data:
                shortest = min(path_data, key=lambda p: p['length'])
                longest = max(path_data, key=lambda p: p['length'])
            else:
                shortest = longest = None
            
            # Create summary
            summary = self._create_paths_summary(
                total_count, shortest, longest, truncated
            )
            
            duration = self._end_timer(start_time)
            
            result = AnalysisResult(
                success=True,
                data={
                    'paths': path_data,
                    'count': total_count,
                    'truncated': truncated,
                    'shortest_length': shortest['length'] if shortest else 0,
                    'longest_length': longest['length'] if longest else 0,
                },
                summary=summary,
                metadata={
                    'source_id': source_id,
                    'target_id': target_id,
                    'max_paths': max_paths,
                    'max_length': max_length,
                    'analysis_time': duration,
                }
            )
            
            if truncated:
                result.add_warning(
                    f"Results truncated to {max_paths} paths (found {total_count} total)"
                )
            
            return result
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Path search failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _build_graph(self) -> nx.DiGraph:
        """Build directed graph from Petri net."""
        graph = nx.DiGraph()
        
        # Add place nodes
        for place in self.model.places:
            graph.add_node(
                place.id,
                type='place',
                obj=place,
                name=getattr(place, 'name', f'P{place.id}')
            )
        
        # Add transition nodes
        for transition in self.model.transitions:
            graph.add_node(
                transition.id,
                type='transition',
                obj=transition,
                name=getattr(transition, 'name', f'T{transition.id}')
            )
        
        # Add arc edges
        for arc in self.model.arcs:
            graph.add_edge(
                arc.source_id,
                arc.target_id,
                obj=arc,
                weight=getattr(arc, 'weight', 1)
            )
        
        return graph
    
    def _analyze_path(self, path_nodes: List[int], graph: nx.DiGraph) -> Dict[str, Any]:
        """Analyze a single path.
        
        Args:
            path_nodes: List of node IDs in path
            graph: NetworkX graph
            
        Returns:
            Dictionary with path information
        """
        # Get names
        names = []
        for node_id in path_nodes:
            node_data = graph.nodes[node_id]
            names.append(node_data.get('name', f'N{node_id}'))
        
        # Count places and transitions
        place_count = sum(1 for nid in path_nodes if graph.nodes[nid]['type'] == 'place')
        transition_count = sum(1 for nid in path_nodes if graph.nodes[nid]['type'] == 'transition')
        
        # Get edge weights
        weights = []
        for i in range(len(path_nodes) - 1):
            edge_data = graph.edges[path_nodes[i], path_nodes[i+1]]
            weights.append(edge_data.get('weight', 1))
        
        return {
            'nodes': path_nodes,
            'names': names,
            'length': len(path_nodes) - 1,  # Number of edges
            'place_count': place_count,
            'transition_count': transition_count,
            'weights': weights,
            'total_weight': sum(weights),
        }
    
    def _analyze_specific_paths(
        self,
        graph: nx.DiGraph,
        source_id: int,
        target_id: int,
        max_paths: int,
        max_length: int,
        start_time: float
    ) -> AnalysisResult:
        """Analyze paths between specific nodes."""
        return self.find_all_paths(source_id, target_id, max_paths, max_length)
    
    def _analyze_general_paths(
        self,
        graph: nx.DiGraph,
        max_paths: int,
        max_length: int,
        start_time: float
    ) -> AnalysisResult:
        """Analyze general path properties of the network."""
        # Calculate diameter (longest shortest path)
        try:
            if nx.is_strongly_connected(graph):
                diameter = nx.diameter(graph)
            else:
                # For disconnected graphs, use largest component
                largest_cc = max(nx.strongly_connected_components(graph), key=len)
                subgraph = graph.subgraph(largest_cc)
                diameter = nx.diameter(subgraph) if len(largest_cc) > 1 else 0
        except:
            diameter = 0
        
        # Calculate average shortest path length
        try:
            if nx.is_strongly_connected(graph):
                avg_path_length = nx.average_shortest_path_length(graph)
            else:
                avg_path_length = 0
        except:
            avg_path_length = 0
        
        summary = f"Network diameter: {diameter}\n"
        summary += f"Average shortest path: {avg_path_length:.2f}"
        
        return AnalysisResult(
            success=True,
            data={
                'diameter': diameter,
                'average_path_length': avg_path_length,
                'is_connected': nx.is_strongly_connected(graph),
            },
            summary=summary,
            metadata={
                'analysis_time': self._end_timer(start_time),
            }
        )
    
    def _create_paths_summary(
        self,
        count: int,
        shortest: Optional[Dict],
        longest: Optional[Dict],
        truncated: bool
    ) -> str:
        """Create human-readable summary of paths."""
        if count == 0:
            return "No paths found"
        
        parts = [f"Found {count} path(s)"]
        
        if truncated:
            parts.append("(results truncated)")
        
        if shortest:
            parts.append(f"• Shortest: {shortest['length']} step(s)")
        
        if longest and longest != shortest:
            parts.append(f"• Longest: {longest['length']} step(s)")
        
        return "\n".join(parts)
    
    def find_paths_through_node(
        self,
        node_id: int,
        max_paths: int = 100
    ) -> List[Dict[str, Any]]:
        """Find all paths that pass through a specific node.
        
        This is useful for property dialogs to show which pathways
        use a particular place or transition.
        
        Args:
            node_id: ID of node to find paths through
            max_paths: Maximum number of paths to return
            
        Returns:
            List of path info dicts that pass through the node
        """
        try:
            graph = self._build_graph()
            
            if node_id not in graph:
                return []
            
            # Find all nodes that can reach this node
            predecessors = set(nx.ancestors(graph, node_id))
            predecessors.add(node_id)
            
            # Find all nodes reachable from this node
            successors = set(nx.descendants(graph, node_id))
            successors.add(node_id)
            
            # Find paths from any predecessor to any successor through node_id
            paths = []
            count = 0
            
            for pred in predecessors:
                if count >= max_paths:
                    break
                for succ in successors:
                    if count >= max_paths:
                        break
                    if pred != succ:
                        try:
                            # Find paths from pred to succ
                            for path in nx.all_simple_paths(graph, pred, succ, cutoff=20):
                                if node_id in path:
                                    path_info = self._analyze_path(path, graph)
                                    paths.append(path_info)
                                    count += 1
                                    if count >= max_paths:
                                        break
                        except nx.NetworkXNoPath:
                            continue
            
            return paths
        
        except Exception:
            return []
