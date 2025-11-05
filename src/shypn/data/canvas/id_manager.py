"""Centralized ID generation and management for Petri net objects.

This module ensures consistent ID generation across all model creation paths:
- Interactive drawing (create_place, create_transition, create_arc)
- KEGG import (compound_mapper, reaction_mapper, arc_builder)
- SBML import (pathway converter)
- Copy/paste operations
- Undo/redo operations

ID Format Convention:
- Places: "P1", "P2", "P3", ...
- Transitions: "T1", "T2", "T3", ...
- Arcs: "A1", "A2", "A3", ...

All IDs are strings, never integers. The numeric part is extracted when needed
for counter management.
"""

from typing import Tuple


class IDManager:
    """Manages ID generation for places, transitions, and arcs.
    
    This class centralizes ID generation logic to ensure consistency across
    the entire application. It maintains separate counters for each object type
    and provides methods to generate new IDs and parse existing ones.
    
    Attributes:
        _next_place_id: Next available place counter
        _next_transition_id: Next available transition counter
        _next_arc_id: Next available arc counter
    """
    
    def __init__(self):
        """Initialize ID manager with counters starting at 1."""
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
    
    def generate_place_id(self) -> str:
        """Generate a new place ID.
        
        Returns:
            String ID in format "P1", "P2", etc.
        """
        place_id = f"P{self._next_place_id}"
        self._next_place_id += 1
        return place_id
    
    def generate_transition_id(self) -> str:
        """Generate a new transition ID.
        
        Returns:
            String ID in format "T1", "T2", etc.
        """
        transition_id = f"T{self._next_transition_id}"
        self._next_transition_id += 1
        return transition_id
    
    def generate_arc_id(self) -> str:
        """Generate a new arc ID.
        
        Returns:
            String ID in format "A1", "A2", etc.
        """
        arc_id = f"A{self._next_arc_id}"
        self._next_arc_id += 1
        return arc_id
    
    def register_place_id(self, place_id: str):
        """Register an existing place ID to prevent duplicates.
        
        Updates the counter if the registered ID is higher than current.
        
        Args:
            place_id: Existing ID (e.g., "P101", "101", or numeric)
        """
        numeric_id = self.extract_numeric_id(place_id, 'P')
        if numeric_id >= self._next_place_id:
            self._next_place_id = numeric_id + 1
    
    def register_transition_id(self, transition_id: str):
        """Register an existing transition ID to prevent duplicates.
        
        Updates the counter if the registered ID is higher than current.
        
        Args:
            transition_id: Existing ID (e.g., "T35", "35", or numeric)
        """
        numeric_id = self.extract_numeric_id(transition_id, 'T')
        if numeric_id >= self._next_transition_id:
            self._next_transition_id = numeric_id + 1
    
    def register_arc_id(self, arc_id: str):
        """Register an existing arc ID to prevent duplicates.
        
        Updates the counter if the registered ID is higher than current.
        
        Args:
            arc_id: Existing ID (e.g., "A113", "113", or numeric)
        """
        numeric_id = self.extract_numeric_id(arc_id, 'A')
        if numeric_id >= self._next_arc_id:
            self._next_arc_id = numeric_id + 1
    
    @staticmethod
    def extract_numeric_id(id_value: any, prefix: str = '') -> int:
        """Extract numeric part from an ID.
        
        Handles various ID formats:
        - String with prefix: "P101" → 101
        - String without prefix: "101" → 101
        - Integer: 101 → 101
        
        Args:
            id_value: ID in any format (str, int)
            prefix: Optional prefix to strip (e.g., 'P', 'T', 'A')
            
        Returns:
            Numeric part of the ID
            
        Raises:
            ValueError: If ID cannot be parsed
        """
        try:
            # Convert to string
            id_str = str(id_value)
            
            # Remove prefix if present
            if prefix and id_str.startswith(prefix):
                id_str = id_str[len(prefix):]
            
            # Convert to integer
            return int(id_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot extract numeric ID from '{id_value}': {e}")
    
    def reset(self):
        """Reset all counters to 1."""
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
    
    def get_state(self) -> Tuple[int, int, int]:
        """Get current counter state.
        
        Returns:
            Tuple of (next_place_id, next_transition_id, next_arc_id)
        """
        return (self._next_place_id, self._next_transition_id, self._next_arc_id)
    
    def set_state(self, place_id: int, transition_id: int, arc_id: int):
        """Set counter state directly.
        
        Args:
            place_id: Next place counter value
            transition_id: Next transition counter value
            arc_id: Next arc counter value
        """
        self._next_place_id = place_id
        self._next_transition_id = transition_id
        self._next_arc_id = arc_id
