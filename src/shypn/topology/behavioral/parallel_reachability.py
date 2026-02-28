"""Parallel reachability analyzer for Petri nets.

DEPRECATED: Parallel support is now directly integrated into ReachabilityAnalyzer.
This module is kept for backward compatibility but just delegates to the base class.

The base ReachabilityAnalyzer now supports parallel execution via the `parallel`
and `num_workers` parameters. Use ReachabilityAnalyzer.analyze(parallel=True) instead.

Example:
    >>> analyzer = ReachabilityAnalyzer(model)
    >>> result = analyzer.analyze(parallel=True, max_states=10000)
    >>> result = analyzer.analyze(parallel='maximal', num_workers=8)
"""

from typing import Any, Optional

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult


class ParallelReachabilityAnalyzer(ReachabilityAnalyzer):
    """Parallel reachability analyzer (delegates to base class).
    
    DEPRECATED: Use ReachabilityAnalyzer with parallel=True instead.
    
    This class is kept for backward compatibility but simply wraps
    the base ReachabilityAnalyzer with default parallel=True.
    """
    
    def __init__(self, model: Any, num_workers: Optional[int] = None):
        """Initialize parallel reachability analyzer.
        
        Args:
            model: Petri net model with places, transitions, arcs
            num_workers: Number of parallel workers (default: CPU count)
        """
        super().__init__(model)
        self.name = "Parallel Reachability"
        self.description = "Parallel exploration (delegates to base class)"
        self._default_num_workers = num_workers
    
    def analyze(  # type: ignore[override]
        self,
        max_states: int = 10000,
        max_depth: int = 100,
        compute_graph: bool = True,
        find_deadlocks: bool = True,
        parallel: Any = True,
        num_workers: Optional[int] = None
    ) -> AnalysisResult:
        """Analyze reachability with parallel execution.
        
        Delegates to base class ReachabilityAnalyzer.analyze() with parallel=True default.
        
        Args:
            max_states: Maximum states to explore
            max_depth: Maximum depth to explore
            compute_graph: Whether to build graph structure
            find_deadlocks: Whether to identify deadlock states
            parallel: Parallelization mode (default: True)
            num_workers: Number of workers (default: from constructor)
            
        Returns:
            AnalysisResult with exploration data
        """
        # Use instance default if not provided
        if num_workers is None:
            num_workers = self._default_num_workers
        
        # Delegate to base class (which now has parallel support)
        return super().analyze(
            max_states=max_states,
            max_depth=max_depth,
            compute_graph=compute_graph,
            find_deadlocks=find_deadlocks,
            parallel=parallel,
            num_workers=num_workers
        )
