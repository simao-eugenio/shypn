"""Base class for state-space exploration strategies.

This module provides the abstract base class for different exploration
strategies used in reachability analysis (sequential, parallel, maximal).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import queue


class StateSpaceExplorer(ABC):
    """Abstract base class for state-space exploration strategies.
    
    Defines the interface that all exploration strategies must implement.
    Concrete implementations include:
    - SequentialExplorer: Single-thread BFS
    - ParallelBasicExplorer: Multi-process work-stealing
    - ParallelMaximalExplorer: Multi-process with maximal concurrent sets
    """
    
    def __init__(self, analyzer: Any):
        """Initialize explorer with reference to parent analyzer.
        
        Args:
            analyzer: Parent ReachabilityAnalyzer instance (provides model access)
        """
        self.analyzer = analyzer
        self.model = analyzer.model
    
    @abstractmethod
    def explore(
        self,
        initial_marking: Dict[str, int],
        max_states: int,
        max_depth: int,
        compute_graph: bool,
        find_deadlocks: bool
    ) -> Dict[str, Any]:
        """Explore reachable state space.
        
        Args:
            initial_marking: Starting marking
            max_states: Maximum states to explore
            max_depth: Maximum depth to explore
            compute_graph: Whether to build graph structure
            find_deadlocks: Whether to identify deadlock states
            
        Returns:
            Dictionary with exploration results:
                - total_states: Number of states discovered
                - total_transitions: Number of transitions fired
                - max_depth: Maximum depth reached
                - states: List of markings (if requested)
                - graph: Graph structure (if requested)
                - deadlock_states: List of deadlock states (if requested)
                - exploration_stats: Strategy-specific statistics
        """
        pass
    
    # ========================================================================
    # Helper methods (shared across all strategies)
    # ========================================================================
    
    def _marking_to_tuple(self, marking: Dict[str, int]) -> Tuple:
        """Convert marking dict to hashable tuple."""
        return tuple(sorted(marking.items()))
    
    def _tuple_to_marking(self, marking_tuple: Tuple) -> Dict[str, int]:
        """Convert marking tuple back to dict."""
        return dict(marking_tuple)
    
    def _get_enabled_transitions(self, marking: Dict[str, int]) -> List[str]:
        """Get enabled transitions using analyzer's method."""
        return self.analyzer._get_enabled_transitions(marking)
    
    def _fire_transition(self, marking: Dict[str, int], trans_id: str) -> Dict[str, int]:
        """Fire transition using analyzer's method."""
        return self.analyzer._fire_transition(marking, trans_id)
    
    def _is_deadlock(self, marking: Dict[str, int]) -> bool:
        """Check if marking is a deadlock state."""
        return len(self._get_enabled_transitions(marking)) == 0


class WorkQueue:
    """Wrapper for work queue operations (abstraction for parallel strategies)."""
    
    def __init__(self, queue_impl: Any):
        """Initialize with queue implementation (deque or Manager.Queue)."""
        self._queue = queue_impl
        self._is_multiprocessing = hasattr(queue_impl, 'get')
    
    def put(self, item: Any) -> None:
        """Add item to queue."""
        if self._is_multiprocessing:
            self._queue.put(item)
        else:
            self._queue.append(item)
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """Get item from queue."""
        if self._is_multiprocessing:
            if timeout is not None:
                return self._queue.get(timeout=timeout)
            return self._queue.get()
        else:
            if len(self._queue) == 0:
                raise queue.Empty()
            return self._queue.popleft()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        if self._is_multiprocessing:
            return self._queue.empty()
        return len(self._queue) == 0
    
    def qsize(self) -> int:
        """Get approximate queue size."""
        if self._is_multiprocessing:
            return self._queue.qsize()
        return len(self._queue)
