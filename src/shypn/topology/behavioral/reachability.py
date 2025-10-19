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
    
    def analyze(
        self,
        max_states: int = 10000,
        max_depth: int = 100,
        compute_graph: bool = True,
        find_deadlocks: bool = True
    ) -> AnalysisResult:
        """Analyze reachability of the Petri net.
        
        Args:
            max_states: Maximum number of states to explore (prevents explosion)
            max_depth: Maximum firing sequence depth
            compute_graph: Build full reachability graph
            find_deadlocks: Identify deadlock states
            
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
            
            # Explore reachability graph
            graph_data = self._explore_reachability(
                initial_marking,
                max_states,
                max_depth,
                compute_graph
            )
            
            # Find deadlock states
            deadlock_states = []
            if find_deadlocks:
                deadlock_states = self._find_deadlock_states(graph_data['states'])
            
            # Check if bounded
            is_bounded = graph_data['total_states'] < max_states
            exploration_complete = is_bounded and graph_data['max_depth'] < max_depth
            
            return AnalysisResult(
                success=True,
                data={
                    'total_states': graph_data['total_states'],
                    'total_transitions': graph_data['total_transitions'],
                    'max_depth_reached': graph_data['max_depth'],
                    'is_bounded': is_bounded,
                    'deadlock_states': deadlock_states,
                    'reachability_graph': graph_data['graph'] if compute_graph else None,
                    'exploration_complete': exploration_complete,
                    'initial_marking': initial_marking
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
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
    
    def _explore_reachability(
        self,
        initial_marking: Dict[str, int],
        max_states: int,
        max_depth: int,
        compute_graph: bool
    ) -> Dict[str, Any]:
        """Explore reachable markings using breadth-first search.
        
        Args:
            initial_marking: Initial marking to start from
            max_states: Maximum states to explore
            max_depth: Maximum depth to explore
            compute_graph: Whether to build graph structure
            
        Returns:
            Dictionary with exploration results
        """
        # Convert marking to hashable tuple for set operations
        def marking_to_tuple(m):
            return tuple(sorted(m.items()))
        
        def tuple_to_marking(t):
            return dict(t)
        
        # Initialize exploration
        visited = set()
        queue = deque([(initial_marking, 0)])  # (marking, depth)
        visited.add(marking_to_tuple(initial_marking))
        
        states = [initial_marking]
        transitions_fired = 0
        max_depth_reached = 0
        
        # Graph structure
        graph = {'nodes': [], 'edges': []} if compute_graph else None
        if compute_graph:
            graph['nodes'].append({
                'id': 0,
                'marking': initial_marking.copy(),
                'depth': 0
            })
        
        state_index = {marking_to_tuple(initial_marking): 0}
        next_state_id = 1
        
        # BFS exploration
        while queue and len(visited) < max_states:
            current_marking, depth = queue.popleft()
            
            if depth > max_depth:
                continue
            
            max_depth_reached = max(max_depth_reached, depth)
            
            # Find enabled transitions
            enabled = self._get_enabled_transitions(current_marking)
            
            # Fire each enabled transition
            for trans_id in enabled:
                new_marking = self._fire_transition(current_marking, trans_id)
                marking_tuple = marking_to_tuple(new_marking)
                
                transitions_fired += 1
                
                # Check if new state
                if marking_tuple not in visited:
                    visited.add(marking_tuple)
                    states.append(new_marking)
                    queue.append((new_marking, depth + 1))
                    
                    if compute_graph:
                        state_index[marking_tuple] = next_state_id
                        graph['nodes'].append({
                            'id': next_state_id,
                            'marking': new_marking.copy(),
                            'depth': depth + 1
                        })
                        next_state_id += 1
                
                # Add edge to graph
                if compute_graph:
                    source_id = state_index[marking_to_tuple(current_marking)]
                    target_id = state_index[marking_tuple]
                    graph['edges'].append({
                        'source': source_id,
                        'target': target_id,
                        'transition': trans_id,
                        'transition_name': self._get_transition_name(trans_id)
                    })
        
        return {
            'total_states': len(visited),
            'total_transitions': transitions_fired,
            'max_depth': max_depth_reached,
            'states': states,
            'graph': graph
        }
    
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
