"""
ID Scope Manager - Manages scoped ID generation for canvas isolation.

Provides thread-safe, canvas-scoped ID generation to prevent ID collisions
when multiple canvases are open simultaneously. Each canvas gets its own
ID namespace (scope).
"""

import threading
from typing import Dict, Tuple, Optional


class IDScopeManager:
    """Thread-safe ID manager with canvas-scoped namespaces.
    
    This class wraps the original IDManager to provide per-canvas ID scopes,
    ensuring that IDs don't collide between different open documents.
    
    Usage:
        # Set scope for canvas 1
        manager.set_scope("canvas_12345")
        id1 = manager.generate_place_id()  # Returns "P1"
        
        # Switch to canvas 2
        manager.set_scope("canvas_67890")
        id2 = manager.generate_place_id()  # Also returns "P1" (different scope!)
        
        # Back to canvas 1
        manager.set_scope("canvas_12345")
        id3 = manager.generate_place_id()  # Returns "P2" (continues from before)
    """
    
    def __init__(self):
        """Initialize scope manager."""
        self._lock = threading.Lock()
        self._scopes: Dict[str, Dict[str, int]] = {}  # scope -> {type: counter}
        self._current_scope: Optional[str] = None
        self._default_scope = "global"
    
    def set_scope(self, scope: str):
        """Set the current ID generation scope.
        
        Args:
            scope: Scope identifier (e.g., 'canvas_12345', 'global')
        """
        with self._lock:
            self._current_scope = scope
            
            # Initialize scope if new
            if scope not in self._scopes:
                self._scopes[scope] = {
                    'place': 1,
                    'transition': 1,
                    'arc': 1
                }
    
    def get_current_scope(self) -> str:
        """Get the current active scope.
        
        Returns:
            Current scope identifier, or default if none set
        """
        with self._lock:
            return self._current_scope or self._default_scope
    
    def reset_scope(self, scope: str):
        """Reset all counters for a specific scope to 1.
        
        Args:
            scope: Scope identifier to reset
        """
        with self._lock:
            if scope in self._scopes:
                self._scopes[scope] = {
                    'place': 1,
                    'transition': 1,
                    'arc': 1
                }
    
    def delete_scope(self, scope: str):
        """Delete a scope entirely (canvas closed).
        
        Args:
            scope: Scope identifier to delete
        """
        with self._lock:
            if scope in self._scopes:
                del self._scopes[scope]
            
            # If deleting current scope, reset to default
            if self._current_scope == scope:
                self._current_scope = self._default_scope
    
    def generate_place_id(self) -> str:
        """Generate a new place ID in current scope.
        
        Returns:
            String ID in format "P1", "P2", etc.
        """
        with self._lock:
            scope = self._current_scope or self._default_scope
            
            # Ensure scope exists
            if scope not in self._scopes:
                self._scopes[scope] = {'place': 1, 'transition': 1, 'arc': 1}
            
            place_id = f"P{self._scopes[scope]['place']}"
            self._scopes[scope]['place'] += 1
            return place_id
    
    def generate_transition_id(self) -> str:
        """Generate a new transition ID in current scope.
        
        Returns:
            String ID in format "T1", "T2", etc.
        """
        with self._lock:
            scope = self._current_scope or self._default_scope
            
            if scope not in self._scopes:
                self._scopes[scope] = {'place': 1, 'transition': 1, 'arc': 1}
            
            transition_id = f"T{self._scopes[scope]['transition']}"
            self._scopes[scope]['transition'] += 1
            return transition_id
    
    def generate_arc_id(self) -> str:
        """Generate a new arc ID in current scope.
        
        Returns:
            String ID in format "A1", "A2", etc.
        """
        with self._lock:
            scope = self._current_scope or self._default_scope
            
            if scope not in self._scopes:
                self._scopes[scope] = {'place': 1, 'transition': 1, 'arc': 1}
            
            arc_id = f"A{self._scopes[scope]['arc']}"
            self._scopes[scope]['arc'] += 1
            return arc_id
    
    def register_place_id(self, place_id: str):
        """Register an existing place ID to prevent duplicates.
        
        Args:
            place_id: Existing ID (e.g., "P101")
        """
        with self._lock:
            scope = self._current_scope or self._default_scope
            
            if scope not in self._scopes:
                self._scopes[scope] = {'place': 1, 'transition': 1, 'arc': 1}
            
            numeric_id = self._extract_numeric_id(place_id, 'P')
            if numeric_id >= self._scopes[scope]['place']:
                self._scopes[scope]['place'] = numeric_id + 1
    
    def register_transition_id(self, transition_id: str):
        """Register an existing transition ID to prevent duplicates.
        
        Args:
            transition_id: Existing ID (e.g., "T35")
        """
        with self._lock:
            scope = self._current_scope or self._default_scope
            
            if scope not in self._scopes:
                self._scopes[scope] = {'place': 1, 'transition': 1, 'arc': 1}
            
            numeric_id = self._extract_numeric_id(transition_id, 'T')
            if numeric_id >= self._scopes[scope]['transition']:
                self._scopes[scope]['transition'] = numeric_id + 1
    
    def register_arc_id(self, arc_id: str):
        """Register an existing arc ID to prevent duplicates.
        
        Args:
            arc_id: Existing ID (e.g., "A113")
        """
        with self._lock:
            scope = self._current_scope or self._default_scope
            
            if scope not in self._scopes:
                self._scopes[scope] = {'place': 1, 'transition': 1, 'arc': 1}
            
            numeric_id = self._extract_numeric_id(arc_id, 'A')
            if numeric_id >= self._scopes[scope]['arc']:
                self._scopes[scope]['arc'] = numeric_id + 1
    
    def get_scope_state(self, scope: str) -> Optional[Tuple[int, int, int]]:
        """Get counter state for a specific scope.
        
        Args:
            scope: Scope identifier
            
        Returns:
            Tuple of (next_place, next_transition, next_arc) or None if scope doesn't exist
        """
        with self._lock:
            if scope not in self._scopes:
                return None
            
            s = self._scopes[scope]
            return (s['place'], s['transition'], s['arc'])
    
    def set_scope_state(self, scope: str, place_id: int, transition_id: int, arc_id: int):
        """Set counter state for a specific scope.
        
        Args:
            scope: Scope identifier
            place_id: Next place counter value
            transition_id: Next transition counter value
            arc_id: Next arc counter value
        """
        with self._lock:
            self._scopes[scope] = {
                'place': place_id,
                'transition': transition_id,
                'arc': arc_id
            }
    
    @staticmethod
    def _extract_numeric_id(id_value: str, prefix: str = '') -> int:
        """Extract numeric part from an ID.
        
        Args:
            id_value: ID string (e.g., "P101")
            prefix: Prefix to strip (e.g., 'P')
            
        Returns:
            Numeric part of the ID
            
        Raises:
            ValueError: If ID cannot be parsed
        """
        try:
            id_str = str(id_value)
            
            # Remove prefix if present
            if prefix and id_str.startswith(prefix):
                id_str = id_str[len(prefix):]
            
            return int(id_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot extract numeric ID from '{id_value}': {e}")
    
    def get_all_scopes(self) -> list:
        """Get list of all active scopes.
        
        Returns:
            List of scope identifiers
        """
        with self._lock:
            return list(self._scopes.keys())
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        with self._lock:
            return (
                f"IDScopeManager("
                f"current='{self._current_scope}', "
                f"scopes={len(self._scopes)}, "
                f"active={list(self._scopes.keys())})"
            )
