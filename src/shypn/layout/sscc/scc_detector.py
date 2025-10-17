"""SCC Detector - Finds strongly connected components using Tarjan's algorithm.

This module implements Tarjan's algorithm for detecting strongly connected
components (SCCs) in a directed graph. SCCs represent cycles/feedback loops
in Petri nets.

Time complexity: O(V + E) where V = nodes, E = edges
"""

from typing import Dict, List, Set
from shypn.layout.sscc.strongly_connected_component import StronglyConnectedComponent


class SCCDetector:
    """Detects strongly connected components using Tarjan's algorithm.
    
    Tarjan's algorithm is a depth-first search based algorithm that finds
    all SCCs in a single pass through the graph.
    
    Reference:
        Tarjan, R. (1972). "Depth-first search and linear graph algorithms"
    """
    
    def __init__(self):
        """Initialize SCC detector."""
        # Algorithm state
        self._index = 0
        self._stack: List[int] = []
        self._indices: Dict[int, int] = {}
        self._lowlinks: Dict[int, int] = {}
        self._on_stack: Set[int] = set()
        self._sccs: List[List[int]] = []
    
    def find_sccs(self, graph: Dict[int, List[int]], 
                  id_to_object: Dict[int, any]) -> List[StronglyConnectedComponent]:
        """Find all strongly connected components in the graph.
        
        Args:
            graph: Adjacency list (node_id -> list of target_ids)
            id_to_object: Mapping from node ID to actual object
            
        Returns:
            List of StronglyConnectedComponent objects
            
        Algorithm:
            1. For each unvisited node, run DFS
            2. Track discovery index and low-link value for each node
            3. When low-link == index, found an SCC root
            4. Pop stack until root to get all nodes in SCC
        """
        # Reset state
        self._index = 0
        self._stack = []
        self._indices = {}
        self._lowlinks = {}
        self._on_stack = set()
        self._sccs = []
        
        # Run Tarjan's algorithm on each unvisited node
        for node_id in graph:
            if node_id not in self._indices:
                self._strongconnect(node_id, graph)
        
        # Convert raw SCCs to StronglyConnectedComponent objects
        scc_objects = []
        for scc_node_ids in self._sccs:
            # Get actual objects for each node ID
            objects = [id_to_object[node_id] for node_id in scc_node_ids 
                      if node_id in id_to_object]
            
            # Only create SCC if it has 2+ nodes (single nodes aren't cycles)
            if len(scc_node_ids) >= 2:
                scc = StronglyConnectedComponent(scc_node_ids, objects)
                scc_objects.append(scc)
        
        return scc_objects
    
    def _strongconnect(self, node: int, graph: Dict[int, List[int]]):
        """Tarjan's strongconnect subroutine (recursive DFS).
        
        Args:
            node: Current node ID
            graph: Adjacency list
        """
        # Set discovery index and low-link value
        self._indices[node] = self._index
        self._lowlinks[node] = self._index
        self._index += 1
        
        # Push node onto stack
        self._stack.append(node)
        self._on_stack.add(node)
        
        # Consider successors (neighbors)
        for neighbor in graph.get(node, []):
            if neighbor not in self._indices:
                # Successor not yet visited; recurse on it
                self._strongconnect(neighbor, graph)
                self._lowlinks[node] = min(self._lowlinks[node], self._lowlinks[neighbor])
            elif neighbor in self._on_stack:
                # Successor is on stack (part of current SCC)
                self._lowlinks[node] = min(self._lowlinks[node], self._indices[neighbor])
        
        # If node is a root node, pop the stack to get SCC
        if self._lowlinks[node] == self._indices[node]:
            scc = []
            while True:
                w = self._stack.pop()
                self._on_stack.remove(w)
                scc.append(w)
                if w == node:
                    break
            self._sccs.append(scc)
    
    def get_scc_count(self) -> int:
        """Get number of SCCs found in last run.
        
        Returns:
            Number of SCCs
        """
        return len(self._sccs)
    
    def get_largest_scc_size(self) -> int:
        """Get size of largest SCC found.
        
        Returns:
            Size of largest SCC (number of nodes)
        """
        if not self._sccs:
            return 0
        return max(len(scc) for scc in self._sccs)
