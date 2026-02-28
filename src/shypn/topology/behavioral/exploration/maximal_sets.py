"""Maximal concurrent set computation for Petri nets.

Provides independence analysis and maximal set computation that can be
shared across simulation (firing semantics) and reachability (exploration).

This module extracts the independence logic from SimulationController into
a reusable service following OOP principles.
"""

from typing import Any, List, Set, Dict, FrozenSet


class IndependenceAnalyzer:
    """Analyze structural independence between transitions.
    
    Two transitions are independent if they don't share any places
    (neither inputs nor outputs). Independent transitions can be
    fired concurrently in maximal step semantics.
    
    Example:
        >>> analyzer = IndependenceAnalyzer(model)
        >>> t1_independent = analyzer.are_independent(t1, t2)
        >>> conflict_sets = analyzer.compute_conflict_sets(enabled)
    """
    
    def __init__(self, model: Any):
        """Initialize analyzer with Petri net model.
        
        Args:
            model: Petri net model with transitions and arcs
        """
        self.model = model
        self._locality_cache: Dict[Any, Any] = {}  # Cache place sets for transitions
    
    def get_transition_locality(self, transition: Any) -> Set[str]:
        """Get all places involved in transition's locality.
        
        Locality = input places (•t) ∪ output places (t•)
        
        Args:
            transition: Transition object
            
        Returns:
            Set of place IDs in transition's neighborhood
        """
        trans_id = str(transition.id)
        
        if trans_id in self._locality_cache:
            return self._locality_cache[trans_id]
        
        place_ids = set()
        
        # Scan all arcs for this transition
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            
            # Input arc: place → transition
            if target_id == trans_id:
                place_ids.add(source_id)
            
            # Output arc: transition → place
            if source_id == trans_id:
                place_ids.add(target_id)
        
        self._locality_cache[trans_id] = place_ids
        return place_ids
    
    def are_independent(self, t1: Any, t2: Any) -> bool:
        """Check if two transitions are independent.
        
        Independent: t1 ⊥ t2 ⟺ (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅
        
        Args:
            t1: First transition
            t2: Second transition
            
        Returns:
            True if transitions don't share ANY places
        """
        locality1 = self.get_transition_locality(t1)
        locality2 = self.get_transition_locality(t2)
        
        return locality1.isdisjoint(locality2)
    
    def compute_conflict_sets(self, transitions: List[Any]) -> Dict[str, Set[str]]:
        """Build conflict graph for transitions.
        
        For each transition, compute the set of transitions it conflicts with
        (shares places with).
        
        Args:
            transitions: List of transition objects
            
        Returns:
            Dict mapping transition ID → set of conflicting transition IDs
        """
        conflict_sets = {}
        
        for i, t1 in enumerate(transitions):
            t1_id = str(t1.id)
            conflicts = set()
            
            for j, t2 in enumerate(transitions):
                if i != j and not self.are_independent(t1, t2):
                    conflicts.add(str(t2.id))
            
            conflict_sets[t1_id] = conflicts
        
        return conflict_sets


class MaximalSetComputer:
    """Compute maximal concurrent sets of independent transitions.
    
    A maximal concurrent set is a set of transitions that:
    1. Are mutually independent (no shared places)
    2. Cannot be extended without introducing conflicts
    
    Uses hybrid greedy strategies for efficient computation.
    
    Example:
        >>> computer = MaximalSetComputer(independence_analyzer)
        >>> maximal_sets = computer.find_maximal_sets(enabled, max_sets=5)
        >>> selected = computer.select_set(maximal_sets, strategy='largest')
    """
    
    def __init__(self, independence_analyzer: IndependenceAnalyzer):
        """Initialize with independence analyzer.
        
        Args:
            independence_analyzer: IndependenceAnalyzer instance
        """
        self.analyzer = independence_analyzer
    
    def find_maximal_sets(
        self,
        transitions: List[Any],
        max_sets: int = 5
    ) -> List[List[Any]]:
        """Find maximal concurrent sets using hybrid strategies.
        
        Args:
            transitions: List of transition objects
            max_sets: Maximum number of sets to return
            
        Returns:
            List of maximal concurrent sets (each a list of transitions)
        """
        if not transitions:
            return []
        
        if len(transitions) == 1:
            return [[transitions[0]]]
        
        # Build conflict graph
        conflict_sets = self.analyzer.compute_conflict_sets(transitions)
        
        maximal_sets = []
        seen_sets: Set[FrozenSet[str]] = set()
        
        # Strategy 1: Natural order
        maximal_set = self._greedy_maximal_set(
            transitions, conflict_sets, start_index=0
        )
        if maximal_set:
            set_key = frozenset(str(t.id) for t in maximal_set)
            seen_sets.add(set_key)
            maximal_sets.append(maximal_set)
        
        # Strategy 2: Different starting points (rotation)
        for start_idx in range(1, min(len(transitions), max_sets)):
            maximal_set = self._greedy_maximal_set(
                transitions, conflict_sets, start_index=start_idx
            )
            if maximal_set:
                set_key = frozenset(str(t.id) for t in maximal_set)
                if set_key not in seen_sets:
                    seen_sets.add(set_key)
                    maximal_sets.append(maximal_set)
                    if len(maximal_sets) >= max_sets:
                        break
        
        # Strategy 3: Most constrained first
        if len(maximal_sets) < max_sets:
            ordered = self._sort_by_conflict_degree(
                transitions, conflict_sets, ascending=False
            )
            maximal_set = self._greedy_maximal_set(
                ordered, conflict_sets, start_index=0
            )
            if maximal_set:
                set_key = frozenset(str(t.id) for t in maximal_set)
                if set_key not in seen_sets:
                    seen_sets.add(set_key)
                    maximal_sets.append(maximal_set)
        
        # Strategy 4: Least constrained first
        if len(maximal_sets) < max_sets:
            ordered = self._sort_by_conflict_degree(
                transitions, conflict_sets, ascending=True
            )
            maximal_set = self._greedy_maximal_set(
                ordered, conflict_sets, start_index=0
            )
            if maximal_set:
                set_key = frozenset(str(t.id) for t in maximal_set)
                if set_key not in seen_sets:
                    seen_sets.add(set_key)
                    maximal_sets.append(maximal_set)
        
        return maximal_sets
    
    def _greedy_maximal_set(
        self,
        transitions: List[Any],
        conflict_sets: Dict[str, Set[str]],
        start_index: int = 0
    ) -> List[Any]:
        """Build one maximal set using greedy algorithm.
        
        Args:
            transitions: List of transitions to consider
            conflict_sets: Precomputed conflict graph
            start_index: Starting position for rotation
            
        Returns:
            Maximal concurrent set (list of transitions)
        """
        if not transitions:
            return []
        
        # Rotate to start from different position
        ordered = transitions[start_index:] + transitions[:start_index]
        
        # Initialize with first transition
        maximal_set = [ordered[0]]
        maximal_set_ids = {str(ordered[0].id)}
        
        # Greedily add independent transitions
        for t in ordered[1:]:
            t_id = str(t.id)
            
            # Check if independent of ALL in current set
            can_add = True
            for tid in maximal_set_ids:
                if t_id in conflict_sets[tid]:
                    can_add = False
                    break
            
            if can_add:
                maximal_set.append(t)
                maximal_set_ids.add(t_id)
        
        return maximal_set
    
    def _sort_by_conflict_degree(
        self,
        transitions: List[Any],
        conflict_sets: Dict[str, Set[str]],
        ascending: bool = True
    ) -> List[Any]:
        """Sort transitions by number of conflicts.
        
        Args:
            transitions: List of transitions
            conflict_sets: Precomputed conflict graph
            ascending: True for least conflicts first
            
        Returns:
            Sorted list of transitions
        """
        def conflict_count(t):
            return len(conflict_sets[str(t.id)])
        
        return sorted(transitions, key=conflict_count, reverse=not ascending)
    
    def select_set(
        self,
        maximal_sets: List[List[Any]],
        strategy: str = 'largest'
    ) -> List[Any]:
        """Select which maximal set to use.
        
        Args:
            maximal_sets: List of maximal concurrent sets
            strategy: Selection strategy ('largest', 'first', 'random')
            
        Returns:
            Selected maximal set
        """
        if not maximal_sets:
            return []
        
        if strategy == 'largest':
            return max(maximal_sets, key=len)
        elif strategy == 'first':
            return maximal_sets[0]
        else:
            # Default to largest
            return max(maximal_sets, key=len)
