"""Strongly Connected Component (SCC) Data Structure.

Represents a single strongly connected component in a directed graph.
"""

from typing import List, Tuple
from shypn.netobjs import Place, Transition


class StronglyConnectedComponent:
    """A strongly connected component (SCC) in a Petri net graph.
    
    An SCC is a maximal subgraph where every node can reach every other node.
    In Petri nets, this represents feedback loops and cyclical structures.
    
    In Solar System Layout, SCCs become "stars" (gravitational centers).
    """
    
    def __init__(self, node_ids: List[int], objects: List[any]):
        """Initialize an SCC.
        
        Args:
            node_ids: List of object IDs in this SCC
            objects: List of actual Petri net objects (Places/Transitions)
        """
        self.node_ids = node_ids
        self.objects = objects
        self.size = len(node_ids)
        
        # Hierarchical properties (set by ComponentRanker)
        self.rank = 0  # Importance rank (higher = more important)
        self.mass = 0.0  # Gravitational mass (for physics simulation)
        self.level = 0  # Orbital level (0 = center, 1+ = orbits)
        
        # Geometric properties
        self.centroid = (0.0, 0.0)  # Center point of SCC
        self.radius = 0.0  # Radius for internal SCC layout
    
    def contains_object(self, obj_id: int) -> bool:
        """Check if this SCC contains a given object ID.
        
        Args:
            obj_id: Object ID to check
            
        Returns:
            True if object is in this SCC
        """
        return obj_id in self.node_ids
    
    def compute_centroid(self, positions: dict) -> Tuple[float, float]:
        """Compute geometric centroid of SCC nodes.
        
        Args:
            positions: Dict mapping object ID to (x, y) position
            
        Returns:
            (x, y) tuple of centroid position
        """
        if not self.node_ids:
            return (0.0, 0.0)
        
        total_x = 0.0
        total_y = 0.0
        
        for node_id in self.node_ids:
            if node_id in positions:
                x, y = positions[node_id]
                total_x += x
                total_y += y
        
        count = len(self.node_ids)
        self.centroid = (total_x / count, total_y / count)
        return self.centroid
    
    def get_places(self) -> List[Place]:
        """Get all Place objects in this SCC.
        
        Returns:
            List of Place objects
        """
        return [obj for obj in self.objects if isinstance(obj, Place)]
    
    def get_transitions(self) -> List[Transition]:
        """Get all Transition objects in this SCC.
        
        Returns:
            List of Transition objects
        """
        return [obj for obj in self.objects if isinstance(obj, Transition)]
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"SCC(size={self.size}, rank={self.rank}, level={self.level})"
    
    def __len__(self) -> int:
        """Return size of SCC."""
        return self.size
