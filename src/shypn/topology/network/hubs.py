"""Hub detection analyzer for Petri nets."""

from typing import List, Dict, Any, Optional
import networkx as nx

from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult


class HubAnalyzer(TopologyAnalyzer):
    """Analyzer for detecting hubs (high-degree nodes) in Petri nets.
    
    Hubs are nodes with many connections (high degree). In biochemical networks,
    hubs are typically:
    - Central metabolites (ATP, NAD+, CoA, glucose-6-phosphate)
    - Currency metabolites (water, H+, phosphate)
    - Branch point metabolites (pyruvate, acetyl-CoA)
    
    This analyzer identifies hubs based on:
    - Degree (total connections)
    - In-degree (incoming arcs)
    - Out-degree (outgoing arcs)
    - Weighted degree (considering arc weights)
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = HubAnalyzer(model)
        result = analyzer.analyze(min_degree=5)
        
        for hub in result.get('hubs', []):
    """
    
    def analyze(  # type: ignore[override]
        self,
        min_degree: int = 3,
        top_n: int = 20,
        node_type: Optional[str] = None,
        parallel: bool = False,
        num_workers: Optional[int] = None
    ) -> AnalysisResult:
        """Find hubs (high-degree nodes) in the Petri net.
        
        Args:
            min_degree: Minimum degree to be considered a hub
            top_n: Return top N hubs by degree
            node_type: Filter by node type ('place', 'transition', or None for all)
            parallel: Use parallel processing for degree calculation
            num_workers: Number of worker processes (None = CPU count)
            
        Returns:
            AnalysisResult with:
                - hubs: List of hub info dicts (sorted by degree)
                - count: Number of hubs found
                - max_degree: Highest degree in network
                - avg_degree: Average degree
                - summary: Human-readable summary
                - metadata: Analysis parameters and timing
        """
        start_time = self._start_timer()
        
        try:
            self._validate_model()
            
            # Build graph
            graph = self._build_graph()
            
            # Calculate degrees for all nodes
            if parallel and len(graph.nodes()) > 10:
                node_degrees = self._calculate_degrees_parallel(
                    graph, node_type, num_workers
                )
            else:
                node_degrees = self._calculate_degrees_sequential(
                    graph, node_type
                )
            
            # Continue with filtering and sorting
            # Filter by minimum degree
            hubs = [n for n in node_degrees if n['degree'] >= min_degree]
            
            # Sort by degree (descending)
            hubs.sort(key=lambda x: x['degree'], reverse=True)
            
            # Limit to top N
            total_count = len(hubs)
            truncated = total_count > top_n
            if truncated:
                hubs = hubs[:top_n]
            
            # Calculate statistics
            if node_degrees:
                max_degree = max(n['degree'] for n in node_degrees)
                avg_degree = sum(n['degree'] for n in node_degrees) / len(node_degrees)
            else:
                max_degree = 0
                avg_degree = 0
            
            # Create summary
            summary = self._create_summary(len(hubs), max_degree, avg_degree, node_type, truncated)
            
            duration = self._end_timer(start_time)
            
            result = AnalysisResult(
                success=True,
                data={
                    'hubs': hubs,
                    'count': total_count,
                    'max_degree': max_degree,
                    'avg_degree': avg_degree,
                },
                summary=summary,
                metadata={
                    'min_degree': min_degree,
                    'top_n': top_n,
                    'node_type': node_type,
                    'analysis_time': duration,
                    'total_nodes': len(node_degrees),
                }
            )
            
            if truncated:
                result.add_warning(
                    f"Results truncated to top {top_n} hubs (found {total_count} total)"
                )
            
            return result
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Hub analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def find_place_hubs(self, min_degree: int = 3, top_n: int = 20) -> AnalysisResult:
        """Find hubs among places only.
        
        Args:
            min_degree: Minimum degree to be considered a hub
            top_n: Return top N place hubs
            
        Returns:
            AnalysisResult with place hubs
        """
        return self.analyze(min_degree=min_degree, top_n=top_n, node_type='place')
    
    def find_transition_hubs(self, min_degree: int = 3, top_n: int = 20) -> AnalysisResult:
        """Find hubs among transitions only.
        
        Args:
            min_degree: Minimum degree to be considered a hub
            top_n: Return top N transition hubs
            
        Returns:
            AnalysisResult with transition hubs
        """
        return self.analyze(min_degree=min_degree, top_n=top_n, node_type='transition')
    
    def is_hub(self, node_id: int, min_degree: int = 3) -> bool:
        """Check if a specific node is a hub.
        
        Args:
            node_id: Node ID to check
            min_degree: Minimum degree threshold
            
        Returns:
            True if node is a hub (degree >= min_degree)
        """
        try:
            graph = self._build_graph()
            node_id = str(node_id)  # type: ignore[assignment]
            if node_id not in graph:
                return False
            
            in_degree = graph.in_degree(node_id)
            out_degree = graph.out_degree(node_id)
            total_degree = in_degree + out_degree
            
            return total_degree >= min_degree
        
        except Exception:
            return False
    
    def _calculate_degrees_sequential(
        self,
        graph: nx.DiGraph,
        node_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Calculate node degrees sequentially."""
        node_degrees = []
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            
            # Filter by type if specified
            if node_type and node_data['type'] != node_type:
                continue
            
            degree_info = self._compute_node_degree(graph, node_id, node_data)
            node_degrees.append(degree_info)
        
        return node_degrees
    
    def _calculate_degrees_parallel(
        self,
        graph: nx.DiGraph,
        node_type: Optional[str],
        num_workers: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Calculate node degrees in parallel using multiprocessing."""
        from multiprocessing import Pool, cpu_count
        
        # Get node list with type filter
        nodes_to_process = [
            (node_id, graph.nodes[node_id])
            for node_id in graph.nodes()
            if not node_type or graph.nodes[node_id]['type'] == node_type
        ]
        
        # Use specified workers or default to CPU count
        workers = num_workers if num_workers else cpu_count()
        
        # Prepare data for workers (graph edges as dict for serialization)
        graph_data = {
            'edges': list(graph.edges(data=True)),
            'predecessors': {n: list(graph.predecessors(n)) for n in graph.nodes()},
            'successors': {n: list(graph.successors(n)) for n in graph.nodes()}
        }
        
        # Parallel degree calculation
        with Pool(workers) as pool:
            node_degrees = pool.starmap(
                self._compute_node_degree_worker,
                [(node_id, node_data, graph_data) for node_id, node_data in nodes_to_process]
            )
        
        return node_degrees
    
    def _compute_node_degree(self, graph: Any, node_id: str, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute degree information for a single node."""
        in_degree = graph.in_degree(node_id)
        out_degree = graph.out_degree(node_id)
        total_degree = in_degree + out_degree
        
        # Calculate weighted degrees
        weighted_in = sum(
            graph.edges[u, node_id].get('weight', 1)
            for u in graph.predecessors(node_id)
        )
        weighted_out = sum(
            graph.edges[node_id, v].get('weight', 1)
            for v in graph.successors(node_id)
        )
        weighted_total = weighted_in + weighted_out
        
        # Get node name
        obj = node_data['obj']
        name = getattr(obj, 'name', None)
        if not name or name.strip() == "":
            if node_data['type'] == 'place':
                name = f"P{node_id}"
            else:
                name = f"T{node_id}"
        
        return {
            'id': node_id,
            'name': name,
            'type': node_data['type'],
            'degree': total_degree,
            'in_degree': in_degree,
            'out_degree': out_degree,
            'weighted_degree': weighted_total,
            'weighted_in_degree': weighted_in,
            'weighted_out_degree': weighted_out,
        }
    
    @staticmethod
    def _compute_node_degree_worker(node_id: str, node_data: Dict[str, Any], graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Worker function for parallel degree calculation (must be static for pickling)."""
        predecessors = graph_data['predecessors'].get(node_id, [])
        successors = graph_data['successors'].get(node_id, [])
        
        in_degree = len(predecessors)
        out_degree = len(successors)
        total_degree = in_degree + out_degree
        
        # Calculate weighted degrees from edges
        weighted_in = sum(
            edge[2].get('weight', 1)
            for edge in graph_data['edges']
            if edge[1] == node_id
        )
        weighted_out = sum(
            edge[2].get('weight', 1)
            for edge in graph_data['edges']
            if edge[0] == node_id
        )
        weighted_total = weighted_in + weighted_out
        
        # Get node name
        obj = node_data['obj']
        name = getattr(obj, 'name', None)
        if not name or name.strip() == "":
            if node_data['type'] == 'place':
                name = f"P{node_id}"
            else:
                name = f"T{node_id}"
        
        return {
            'id': node_id,
            'name': name,
            'type': node_data['type'],
            'degree': total_degree,
            'in_degree': in_degree,
            'out_degree': out_degree,
            'weighted_degree': weighted_total,
            'weighted_in_degree': weighted_in,
            'weighted_out_degree': weighted_out,
        }
    
    def get_node_degree_info(self, node_id: int) -> Optional[Dict[str, Any]]:
        """Get degree information for a specific node.
        
        This is useful for property dialogs.
        
        Args:
            node_id: Node ID to analyze
            
        Returns:
            Dictionary with degree information, or None if node not found
        """
        try:
            graph = self._build_graph()
            node_id = str(node_id)  # type: ignore[assignment]
            if node_id not in graph:
                return None
            
            node_data = graph.nodes[node_id]
            
            # Calculate degrees
            in_degree = graph.in_degree(node_id)
            out_degree = graph.out_degree(node_id)
            total_degree = in_degree + out_degree
            
            # Calculate weighted degrees
            weighted_in = sum(
                graph.edges[u, node_id].get('weight', 1)
                for u in graph.predecessors(node_id)
            )
            weighted_out = sum(
                graph.edges[node_id, v].get('weight', 1)
                for v in graph.successors(node_id)
            )
            weighted_total = weighted_in + weighted_out
            
            # Get neighbors
            predecessors = list(graph.predecessors(node_id))
            successors = list(graph.successors(node_id))
            
            # Determine hub status
            is_hub = total_degree >= 3  # Default threshold
            
            return {
                'id': node_id,
                'type': node_data['type'],
                'degree': total_degree,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'weighted_degree': weighted_total,
                'weighted_in_degree': weighted_in,
                'weighted_out_degree': weighted_out,
                'predecessors': predecessors,
                'successors': successors,
                'is_hub': is_hub,
            }
        
        except Exception:
            return None
    
    def _create_summary(
        self,
        hub_count: int,
        max_degree: int,
        avg_degree: float,
        node_type: Optional[str],
        truncated: bool
    ) -> str:
        """Create human-readable summary."""
        if hub_count == 0:
            return "No hubs found"
        
        type_str = f"{node_type} " if node_type else ""
        parts = [f"Found {hub_count} {type_str}hub(s)"]
        
        if truncated:
            parts.append("(results truncated)")
        
        parts.append(f"• Max degree: {max_degree}")
        parts.append(f"• Avg degree: {avg_degree:.2f}")
        
        return "\n".join(parts)
