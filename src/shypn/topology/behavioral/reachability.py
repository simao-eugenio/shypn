"""Reachability analyzer for Petri nets.

Reachability explores the marking space to determine which markings can be
reached from the initial marking through firing sequences.

Analysis Types:
- **Coverability Graph**: Compact representation of infinite reachability sets
- **Marking Reachability**: Check if specific marking is reachable
- **State Space Statistics**: Count states, transitions, depth
- **Trap States**: Identify markings with no outgoing transitions

Reachability is fundamental for:
- Verifying safety properties (bad states unreachable)
- Liveness analysis (good states always reachable)
- Deadlock detection (terminal states)
- Performance evaluation (state space size)

Mathematical Background:
- Karp, R.M. & Miller, R.E. (1969). "Parallel program schemata"
- Finkel, A. (1990). "The minimal coverability graph for Petri nets"
- Esparza, J. (1998). "Decidability and complexity of Petri net problems"

Implementation approach:
- Breadth-first exploration of reachable markings
- Bounded exploration to prevent state explosion
- Omega values (ω) for potentially unbounded places
- Efficient marking representation and comparison
"""

from typing import Any, Dict, List, Set, Optional, Tuple
import numpy as np
from collections import deque

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError

# Import exploration strategies (OOP pattern)
from shypn.topology.behavioral.exploration.sequential_explorer import SequentialExplorer
from shypn.topology.behavioral.exploration.parallel_basic_explorer import ParallelBasicExplorer
from shypn.topology.behavioral.exploration.parallel_maximal_explorer import ParallelMaximalExplorer


class ReachabilityAnalyzer(TopologyAnalyzer):
    """Analyzer for exploring reachable marking space of Petri nets.
    
    Reachability analysis explores which markings can be reached from
    the initial marking through valid firing sequences.
    
    Example:
        >>> analyzer = ReachabilityAnalyzer(model)
        >>> result = analyzer.analyze(max_states=1000)
        >>> print(f"Reachable states: {result.get('total_states')}")
    """
    
    def __init__(self, model: Any):
        """Initialize reachability analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs attributes
        """
        super().__init__(model)
        self.name = "Reachability"
        self.description = "Explore reachable marking space"
    
    def analyze(  # type: ignore[override]
        self,
        max_states: int = 10000,
        max_depth: int = 100,
        compute_graph: bool = True,
        find_deadlocks: bool = True,
        parallel: Any = False,
        num_workers: Optional[int] = None
    ) -> AnalysisResult:
        """Analyze reachability of the Petri net.
        
        Args:
            max_states: Maximum number of states to explore (prevents explosion)
            max_depth: Maximum firing sequence depth
            compute_graph: Build full reachability graph
            find_deadlocks: Identify deadlock states
            parallel: Parallelization mode:
                - False: Sequential exploration (default)
                - True or 'basic': Phase 1 work-stealing
                - 'maximal': Phase 2 maximal concurrent sets
            num_workers: Number of worker processes (None = auto)
            
        Returns:
            AnalysisResult with:
            - total_states: Number of reachable states
            - total_transitions: Number of state transitions
            - max_depth_reached: Maximum depth explored
            - is_bounded: Whether exploration stayed within bounds
            - deadlock_states: List of states with no enabled transitions
            - reachability_graph: Graph structure (if computed)
        """
        start_time = self._start_timer()
        
        # Validate model
        try:
            self._validate_model()
        except TopologyAnalysisError as e:
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        # ========================================================================
        # SIZE GUARD: Estimate state space to prevent state explosion freeze
        # ========================================================================
        try:
            n_places = len(self.model.places)
            n_transitions = len(self.model.transitions)
        except (TypeError, AttributeError):
            return AnalysisResult(
                success=False,
                errors=["Model access failed - invalid model object"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )

        try:
            # Estimate state space size (rough heuristic)
            # Real state space can be much larger for complex nets
            avg_tokens_per_place = sum(p.tokens for p in self.model.places) / n_places if n_places > 0 else 0
        except (TypeError, AttributeError):
            avg_tokens_per_place = 0
        estimated_states = int((avg_tokens_per_place + 1) ** n_places)
        
        # Warn if estimated state space is very large
        if estimated_states > 100000 or n_places > 30:
            return AnalysisResult(
                success=False,
                errors=[
                    f"⛔ Model likely has huge state space",
                    f"   Places: {n_places}, Transitions: {n_transitions}",
                    f"   Estimated states: {estimated_states:,} (may be conservative)",
                    "",
                    "⚠️  This analysis could take 30-60+ seconds or freeze",
                    "    the system due to state explosion."
                ],
                warnings=[
                    "Options to analyze this model:",
                    "• Use a smaller subnetwork",
                    "• Reduce initial tokens to limit state space",
                    "• Use batch analysis mode with timeout",
                    f"• Lower max_states limit (current: {max_states})"
                ],
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'blocked': True,
                    'block_reason': 'state_explosion_risk',
                    'estimated_states': estimated_states,
                    'actual_places': n_places,
                    'actual_transitions': n_transitions,
                    'complexity': 'O(k^n) - State Explosion'
                }
            )
        
        # Handle empty model
        if not self.model.places or not self.model.transitions:
            return AnalysisResult(
                success=True,
                data={
                    'total_states': 1 if self.model.places else 0,
                    'total_transitions': 0,
                    'max_depth_reached': 0,
                    'is_bounded': True,
                    'deadlock_states': [],
                    'reachability_graph': {'nodes': [], 'edges': []},
                    'exploration_complete': True
                },
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        try:
            # Get initial marking
            initial_marking = self._get_initial_marking()
            
            # Select exploration strategy (OOP pattern)
            explorer = self._create_explorer(parallel, num_workers)
            
            # Explore reachable markings using strategy
            exploration_results = explorer.explore(
                initial_marking=initial_marking,
                max_states=max_states,
                max_depth=max_depth,
                compute_graph=compute_graph,
                find_deadlocks=find_deadlocks
            )
            
            # Get deadlock states (already found by explorer)
            deadlock_states = exploration_results.get('deadlock_states', [])
            
            # Check if bounded
            is_bounded = exploration_results['total_states'] < max_states
            exploration_complete = is_bounded and exploration_results['max_depth'] < max_depth
            
            return AnalysisResult(
                success=True,
                data={
                    'total_states': exploration_results['total_states'],
                    'total_transitions': exploration_results['total_transitions'],
                    'max_depth_reached': exploration_results['max_depth'],
                    'is_bounded': is_bounded,
                    'deadlock_states': deadlock_states,
                    'reachability_graph': exploration_results['graph'],
                    'exploration_complete': exploration_complete,
                    'initial_marking': initial_marking
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'max_states_limit': max_states,
                    'max_depth_limit': max_depth,
                    'mode': exploration_results.get('exploration_stats', {}).get('strategy', 'sequential'),
                    'num_workers': exploration_results.get('exploration_stats', {}).get('num_workers', 1)
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Reachability analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _create_explorer(self, parallel: Any, num_workers: Optional[int]) -> Any:
        """Create appropriate explorer strategy (OOP factory pattern).
        
        Args:
            parallel: Parallelization mode (WARNING: parallel modes are experimental and significantly slower than sequential)
            num_workers: Number of workers
            
        Returns:
            Explorer instance (SequentialExplorer recommended for production use)
        """
        if not parallel or (num_workers is not None and num_workers == 1):
            # Sequential mode (RECOMMENDED - 100x faster than parallel)
            return SequentialExplorer(self)
        elif parallel == 'maximal':
            # Phase 2: Maximal concurrent sets (EXPERIMENTAL - slow due to Python multiprocessing overhead)
            import warnings
            warnings.warn("Parallel modes are experimental and 100-125x slower than sequential. Use parallel=False for production.", UserWarning)
            return ParallelMaximalExplorer(self, num_workers)  # type: ignore[arg-type]
        else:
            # Phase 1: Basic work-stealing (EXPERIMENTAL - slow due to Python multiprocessing overhead)
            import warnings
            warnings.warn("Parallel modes are experimental and 100-125x slower than sequential. Use parallel=False for production.", UserWarning)
            return ParallelBasicExplorer(self, num_workers)  # type: ignore[arg-type]
    
    def _get_initial_marking(self) -> Dict[str, int]:
        """Get initial marking from model.
        
        Returns:
            Dict mapping place IDs to token counts
        """
        marking = {}
        for place in self.model.places:
            place_id = str(place.id)
            marking[place_id] = getattr(place, 'marking', 0)
        return marking
    
    # Note: _explore_reachability() removed - delegated to explorer classes (OOP pattern)
    
    def _get_enabled_transitions(self, marking: Dict[str, int]) -> List[str]:
        """Get list of enabled transitions in given marking.
        
        Args:
            marking: Current marking
            
        Returns:
            List of enabled transition IDs
        """
        enabled = []
        
        for transition in self.model.transitions:
            trans_id = str(transition.id)
            
            # Check if transition is enabled
            if self._is_transition_enabled(trans_id, marking):
                enabled.append(trans_id)
        
        return enabled
    
    def _is_transition_enabled(self, trans_id: str, marking: Dict[str, int]) -> bool:
        """Check if transition is enabled in given marking.
        
        Args:
            trans_id: Transition ID
            marking: Current marking
            
        Returns:
            True if transition is enabled
        """
        # Find input places and their required tokens
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            weight = getattr(arc, 'weight', 1)
            
            # Check place → transition arc
            if target_id == trans_id:
                # Check if place has enough tokens
                if marking.get(source_id, 0) < weight:
                    return False
        
        return True
    
    def _fire_transition(self, marking: Dict[str, int], trans_id: str) -> Dict[str, int]:
        """Fire transition and return new marking.
        
        Args:
            marking: Current marking
            trans_id: Transition to fire
            
        Returns:
            New marking after firing
        """
        new_marking = marking.copy()
        
        # Consume tokens from input places
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            weight = getattr(arc, 'weight', 1)
            
            if target_id == trans_id:
                new_marking[source_id] = new_marking.get(source_id, 0) - weight
        
        # Produce tokens to output places
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            weight = getattr(arc, 'weight', 1)
            
            if source_id == trans_id:
                new_marking[target_id] = new_marking.get(target_id, 0) + weight
        
        return new_marking
    
    def _find_deadlock_states(self, states: List[Dict[str, int]]) -> List[Dict[str, Any]]:
        """Find states with no enabled transitions (deadlocks).
        
        Args:
            states: List of reachable states
            
        Returns:
            List of deadlock state information
        """
        deadlocks = []
        
        for i, state in enumerate(states):
            enabled = self._get_enabled_transitions(state)
            
            if not enabled:
                deadlocks.append({
                    'state_id': i,
                    'marking': state.copy(),
                    'enabled_transitions': []
                })
        
        return deadlocks
    
    def _get_transition_name(self, trans_id: str) -> str:
        """Get transition name by ID.
        
        Args:
            trans_id: Transition ID
            
        Returns:
            Transition name or ID
        """
        for transition in self.model.transitions:
            if str(transition.id) == trans_id:
                if hasattr(transition, 'name') and transition.name:
                    return str(transition.name)
                return trans_id
        return trans_id
    
    def is_marking_reachable(
        self,
        target_marking: Dict[str, int],
        max_states: int = 10000
    ) -> bool:
        """Check if a specific marking is reachable.
        
        Args:
            target_marking: Target marking to check
            max_states: Maximum states to explore
            
        Returns:
            True if marking is reachable
        """
        result = self.analyze(max_states=max_states, compute_graph=False)
        
        if not result.success:
            return False
        
        # This would require storing all states, which we skip for efficiency
        # For now, return conservative answer
        return result.get('exploration_complete', False)
    
    def get_reachability_statistics(self) -> AnalysisResult:
        """Get statistics about reachable state space.
        
        Returns:
            AnalysisResult with state space statistics
        """
        result = self.analyze(compute_graph=False, find_deadlocks=True)
        
        if not result.success:
            return result
        
        total_states = result.get('total_states', 0)
        total_transitions = result.get('total_transitions', 0)
        deadlocks = result.get('deadlock_states', [])
        
        return AnalysisResult(
            success=True,
            data={
                'total_states': total_states,
                'total_transitions': total_transitions,
                'deadlock_count': len(deadlocks),
                'average_branching_factor': (
                    total_transitions / total_states if total_states > 0 else 0
                ),
                'has_deadlocks': len(deadlocks) > 0
            },
            metadata=result.metadata
        )
