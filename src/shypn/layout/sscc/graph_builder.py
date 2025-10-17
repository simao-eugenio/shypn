"""Graph Builder - Converts Petri net to directed graph.

This module builds a directed graph representation from Petri net objects
(places, transitions, arcs) for use in SCC detection and layout algorithms.
"""

from typing import Dict, List, Set
from shypn.netobjs import Place, Transition, Arc


class GraphBuilder:
    """Converts Petri net objects into a directed graph adjacency list.
    
    The graph is represented as a dictionary where:
    - Keys are object IDs (int)
    - Values are lists of target object IDs (List[int])
    
    This representation is suitable for SCC detection and graph algorithms.
    """
    
    def __init__(self):
        """Initialize graph builder."""
        self._graph: Dict[int, List[int]] = {}
        self.id_to_object: Dict[int, any] = {}  # Public: expose for SCC detector
    
    def build_graph(self, places: List[Place], transitions: List[Transition], 
                    arcs: List[Arc]) -> Dict[int, List[int]]:
        """Build directed graph from Petri net objects.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
            arcs: List of Arc objects connecting places and transitions
            
        Returns:
            Dict mapping object ID to list of target IDs (adjacency list)
            
        Example:
            graph = {
                1: [2, 3],  # Node 1 connects to nodes 2 and 3
                2: [3],     # Node 2 connects to node 3
                3: []       # Node 3 has no outgoing edges
            }
        """
        self._graph = {}
        self.id_to_object = {}
        
        # Add all nodes (places and transitions)
        for place in places:
            self._graph[place.id] = []
            self.id_to_object[place.id] = place
        
        for transition in transitions:
            self._graph[transition.id] = []
            self.id_to_object[transition.id] = transition
        
        # Add all edges (arcs)
        for arc in arcs:
            source_id = arc.source.id
            target_id = arc.target.id
            
            if source_id in self._graph:
                self._graph[source_id].append(target_id)
        
        return self._graph
    
    def get_object_by_id(self, obj_id: int):
        """Get Petri net object by its ID.
        
        Args:
            obj_id: Object ID to look up
            
        Returns:
            Place or Transition object
            
        Raises:
            KeyError: If object ID not found
        """
        return self.id_to_object[obj_id]
    
    def get_all_nodes(self) -> Set[int]:
        """Get set of all node IDs in the graph.
        
        Returns:
            Set of all node IDs
        """
        return set(self._graph.keys())
    
    def get_neighbors(self, node_id: int) -> List[int]:
        """Get list of neighbor IDs for a given node.
        
        Args:
            node_id: Node ID
            
        Returns:
            List of target node IDs
        """
        return self._graph.get(node_id, [])
    
    def get_reverse_graph(self) -> Dict[int, List[int]]:
        """Build reverse graph (transpose) where all edges are reversed.
        
        Useful for some graph algorithms.
        
        Returns:
            Dict mapping node ID to list of source IDs (reverse edges)
        """
        reverse_graph = {node_id: [] for node_id in self._graph}
        
        for source_id, targets in self._graph.items():
            for target_id in targets:
                if target_id in reverse_graph:
                    reverse_graph[target_id].append(source_id)
        
        return reverse_graph
    
    def get_graph_stats(self) -> Dict[str, int]:
        """Get statistics about the graph.
        
        Returns:
            Dict with node count, edge count, etc.
        """
        num_nodes = len(self._graph)
        num_edges = sum(len(targets) for targets in self._graph.values())
        
        return {
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'avg_degree': num_edges / num_nodes if num_nodes > 0 else 0
        }
