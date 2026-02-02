"""Parallel reachability analyzer for Petri nets.

Modular architecture with pluggable exploration strategies:
- Phase 1: Basic work-stealing (ParallelBasicExplorer)
- Phase 2: Maximal concurrent sets (ParallelMaximalExplorer)
- Phase 3: Layer decomposition (future)

This analyzer provides a thin wrapper around exploration strategies,
following OOP principles with minimal code in the main class.
"""

from typing import Any, Optional
import time

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.behavioral.exploration.sequential_explorer import SequentialExplorer
from shypn.topology.behavioral.exploration.parallel_basic_explorer import ParallelBasicExplorer
from shypn.topology.behavioral.exploration.parallel_maximal_explorer import ParallelMaximalExplorer


class ParallelReachabilityAnalyzer(ReachabilityAnalyzer):
    """Parallel reachability analyzer with modular exploration strategies.
    
    Delegates actual exploration to strategy classes:
    - SequentialExplorer: Baseline BFS
    - ParallelBasicExplorer: Work-stealing parallel BFS (Phase 1)
    - ParallelMaximalExplorer: Maximal concurrent sets (Phase 2)
    
    Example:
        >>> # Phase 1: Basic parallel
        >>> analyzer = ParallelReachabilityAnalyzer(model, num_workers=4)
        >>> result = analyzer.analyze(parallel=True, max_states=10000)
        
        >>> # Phase 2: Maximal concurrent sets
        >>> result = analyzer.analyze(parallel='maximal', max_states=10000)
        >>> print(f"Maximal sets fired: {result.metadata.get('maximal_sets_fired')}")
    """
    
    def __init__(self, model: Any, num_workers: Optional[int] = None):
        """Initialize parallel reachability analyzer.
        
        Args:
            model: Petri net model with places, transitions, arcs
            num_workers: Number of parallel workers (default: CPU count)
        """
        super().__init__(model)
        self.name = "Parallel Reachability"
        self.description = "Parallel exploration with modular strategies"
        self.num_workers = num_workers
    
    def analyze(
        self,
        max_states: int = 10000,
        max_depth: int = 100,
        compute_graph: bool = True,
        find_deadlocks: bool = True,
        parallel: Any = True
    ) -> AnalysisResult:
        """Analyze reachability with configurable parallelization.
        
        Args:
            max_states: Maximum states to explore
            max_depth: Maximum depth to explore
            compute_graph: Whether to build graph structure
            find_deadlocks: Whether to identify deadlock states
            parallel: Parallelization mode:
                - False: Sequential exploration
                - True or 'basic': Phase 1 work-stealing (default)
                - 'maximal': Phase 2 maximal concurrent sets
            
        Returns:
            AnalysisResult with exploration data and metadata
        """
        start_time = self._start_timer()
        
        # Validation
        try:
            self._validate_model()
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        # Size guard (same as base class)
        n_places = len(self.model.places)
        n_transitions = len(self.model.transitions)
        
        if n_places > 30:
            avg_tokens = sum(p.tokens for p in self.model.places) / n_places
            estimated_states = int((avg_tokens + 1) ** n_places)
            
            if estimated_states > 100000:
                return AnalysisResult(
                    success=False,
                    errors=[
                        f"⛔ Model likely has huge state space",
                        f"   Places: {n_places}, Transitions: {n_transitions}",
                        f"   Estimated states: {estimated_states:,}",
                        "",
                        "⚠️  This analysis could take 30-60+ seconds or freeze"
                    ],
                    metadata={
                        'analysis_time': self._end_timer(start_time),
                        'blocked': True,
                        'block_reason': 'state_explosion_risk'
                    }
                )
        
        # Get initial marking
        initial_marking = self._get_initial_marking()
        
        # Select exploration strategy
        if not parallel or (self.num_workers is not None and self.num_workers == 1):
            # Sequential mode
            explorer = SequentialExplorer(self)
            exploration_mode = 'sequential'
        elif parallel == 'maximal':
            # Phase 2: Maximal concurrent sets
            explorer = ParallelMaximalExplorer(self, self.num_workers)
            exploration_mode = 'parallel_maximal'
        else:
            # Phase 1: Basic work-stealing (default parallel mode)
            explorer = ParallelBasicExplorer(self, self.num_workers)
            exploration_mode = 'parallel_basic'
        
        # Execute exploration
        try:
            exploration_start = time.time()
            results = explorer.explore(
                initial_marking=initial_marking,
                max_states=max_states,
                max_depth=max_depth,
                compute_graph=compute_graph,
                find_deadlocks=find_deadlocks
            )
            exploration_time = time.time() - exploration_start
            
            # Check boundedness
            is_bounded = results['total_states'] < max_states
            exploration_complete = is_bounded and results['max_depth'] < max_depth
            
            # Build result data
            result_data = {
                'total_states': results['total_states'],
                'total_transitions': results['total_transitions'],
                'max_depth_reached': results['max_depth'],
                'is_bounded': is_bounded,
                'deadlock_states': results['deadlock_states'],
                'reachability_graph': results['graph'],
                'exploration_complete': exploration_complete,
                'initial_marking': initial_marking
            }
            
            # Add parallelization stats only for parallel mode
            if 'exploration_stats' in results:
                result_data['parallelization_stats'] = results['exploration_stats']
            
            return AnalysisResult(
                success=True,
                data=result_data,
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'exploration_time': exploration_time,
                    'mode': exploration_mode,
                    'num_workers': explorer.num_workers if hasattr(explorer, 'num_workers') else 1,
                    'max_states_limit': max_states,
                    'max_depth_limit': max_depth
                }
            )
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Reachability analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
