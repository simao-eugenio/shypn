"""Parallel Stochastic Scheduler using Weak Independence Theory.

Implements Phase 3: Parallel τ-leaping for weakly independent transitions.

Theory:
- Convergent coupling (shared outputs) → Independent Poisson sampling
- Regulatory coupling (shared catalysts) → Independent Poisson sampling  
- Competitive coupling (shared inputs) → Sequential execution

Performance: Expected 2-4× speedup over sequential τ-leaping based on
~65% weakly independent transition pairs in biological models.

References:
- Bioinformatics paper: "Stochastic Weak Independence" section
- doc/stochastic/PARALLEL_STOCHASTIC_PLAN.md
"""

import logging
from typing import List, Dict, Any, Set, Optional
import numpy as np
import os

from .poisson_sampler import PoissonSampler


class ParallelStochasticScheduler:
    """Parallel stochastic transition scheduler using weak independence.
    
    Analyzes transition dependencies and schedules:
    - Weakly independent transitions → Parallel Poisson sampling
    - Competitive transitions → Sequential execution
    
    Key Insight: Stochastic does NOT imply sequential. Molecular collisions
    are inherently parallel - convergent/regulatory coupling represents
    spatially distributed events that can be sampled concurrently.
    
    Example:
        >>> scheduler = ParallelStochasticScheduler(model)
        >>> scheduler.analyze_dependencies()
        >>> firings = scheduler.sample_parallel(transitions, propensities, tau)
    """
    
    def __init__(
        self,
        model: Any,
        enable_parallel: bool = True
    ):
        """Initialize parallel scheduler.
        
        Args:
            model: Petri net model
            enable_parallel: If False, use sequential (for testing)
        
        Note:
            max_workers is automatically determined from os.cpu_count().
            This reflects the computational reality, not biological semantics.
            The biological parallelism is determined by weak independence
            structure in the model.
        """
        self.model = model
        self.enable_parallel = enable_parallel
        
        # Auto-determine optimal worker count based on system
        cpu_count = os.cpu_count() or 4  # Fallback to 4 if unknown
        self.max_workers = min(cpu_count, 8)  # Cap at 8 (diminishing returns)
        
        self.poisson_sampler = PoissonSampler()
        self.logger = logging.getLogger(__name__)
        
        self.logger.debug(
            f"Parallel scheduler initialized: {self.max_workers} workers "
            f"(system has {cpu_count} CPUs)"
        )
        
        # Dependency classification (computed once)
        self._dependency_groups: Optional[Any] = None
        self._competitive_pairs: Optional[Any] = None
        
        # Statistics
        self.stats = {
            'parallel_groups': 0,
            'sequential_groups': 0,
            'total_parallel_samples': 0,
            'total_sequential_samples': 0
        }
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze transition dependencies using dependency coupling classifier.
        
        Returns:
            Dictionary with dependency groups and statistics
        """
        from shypn.topology.biological.dependency_coupling import DependencyAndCouplingAnalyzer
        
        # Run dependency analysis
        analyzer = DependencyAndCouplingAnalyzer(self.model)
        result = analyzer.analyze()
        
        classifications = result.data
        
        # Extract competitive pairs (must be sequential)
        self._competitive_pairs = set()
        for t1_id, t2_id, _ in classifications.get('competitive', []):
            self._competitive_pairs.add((t1_id, t2_id))
            self._competitive_pairs.add((t2_id, t1_id))  # Symmetric
        
        # Build dependency graph
        self._dependency_groups = self._build_dependency_groups(classifications)
        
        stats = result.data.get('statistics', {})
        
        self.logger.info(
            f"Dependency analysis: {stats.get('weakly_independent_pct', 0):.1f}% "
            f"weakly independent, {stats.get('competitive_pct', 0):.1f}% competitive"
        )
        
        return {
            'classifications': classifications,
            'statistics': stats,
            'dependency_groups': self._dependency_groups,
            'competitive_pairs': len(self._competitive_pairs) // 2  # Divide by 2 (symmetric)
        }
    
    def _build_dependency_groups(
        self,
        classifications: Dict[str, List]
    ) -> Dict[int, Set[int]]:
        """Build dependency graph for parallel scheduling.
        
        Args:
            classifications: Dependency classifications from analyzer
        
        Returns:
            Dictionary mapping transition_id -> set of conflicting transition_ids
        """
        dependency_graph: Dict[Any, Any] = {}
        
        # Get all transitions
        transitions = (self.model.transitions.values() 
                      if hasattr(self.model.transitions, 'values') 
                      else self.model.transitions)
        
        # Initialize: no dependencies
        for t in transitions:
            dependency_graph[t.id] = set()
        
        # Add competitive dependencies (only true conflicts)
        for t1_id, t2_id, _ in classifications.get('competitive', []):
            dependency_graph[t1_id].add(t2_id)
            dependency_graph[t2_id].add(t1_id)
        
        return dependency_graph
    
    def sample_parallel(
        self,
        transitions: List[Any],
        propensities: List[float],
        tau: float
    ) -> Dict[Any, int]:
        """Sample firings for all transitions using parallel execution.
        
        Args:
            transitions: List of stochastic transitions
            propensities: Propensities for each transition
            tau: Time leap size
        
        Returns:
            Dictionary mapping transition -> number of firings
        """
        if self._dependency_groups is None:
            # Lazy initialization
            self.analyze_dependencies()
        
        if not self.enable_parallel or len(transitions) < 4:
            # Use sequential for small problems
            return self._sample_sequential(transitions, propensities, tau)
        
        # Partition transitions into parallel groups
        parallel_groups = self._partition_for_parallel_execution(transitions)
        
        firings_map = {}
        
        # Execute each group
        for group in parallel_groups:
            if len(group) == 1:
                # Single transition - no parallelization needed
                t = group[0]
                idx = transitions.index(t)
                firings = self.poisson_sampler.sample(propensities[idx], tau)
                firings_map[t] = firings
                self.stats['total_sequential_samples'] += 1
            else:
                # Multiple independent transitions - parallel sampling
                group_firings = self._sample_group_parallel(
                    group, transitions, propensities, tau
                )
                firings_map.update(group_firings)
                self.stats['parallel_groups'] += 1
                self.stats['total_parallel_samples'] += len(group)
        
        return firings_map
    
    def _partition_for_parallel_execution(
        self,
        transitions: List[Any]
    ) -> List[List[Any]]:
        """Partition transitions into parallel execution groups.
        
        Uses graph coloring-like algorithm:
        - Transitions in same group have no competitive dependencies
        - Transitions in different groups may have dependencies
        
        Args:
            transitions: List of transitions to partition
        
        Returns:
            List of groups, where each group can be executed in parallel
        """
        if not transitions:
            return []
        
        # Greedy coloring algorithm
        groups: List[Any] = []
        assigned = set()
        
        for t in transitions:
            # Try to add to existing group
            placed = False
            for group in groups:
                # Check if t conflicts with any transition in this group
                conflicts = False
                for other in group:
                    if self._has_competitive_dependency(t, other):
                        conflicts = True
                        break
                
                if not conflicts:
                    group.append(t)
                    placed = True
                    break
            
            # Create new group if needed
            if not placed:
                groups.append([t])
            
            assigned.add(t.id)
        
        return groups
    
    def _has_competitive_dependency(self, t1: Any, t2: Any) -> bool:
        """Check if two transitions have competitive dependency.
        
        Args:
            t1: First transition
            t2: Second transition
        
        Returns:
            True if they share input places (competitive)
        """
        if self._competitive_pairs is None:
            return False
        
        return (t1.id, t2.id) in self._competitive_pairs
    
    def _sample_group_parallel(
        self,
        group: List[Any],
        all_transitions: List[Any],
        propensities: List[float],
        tau: float
    ) -> Dict[Any, int]:
        """Sample firings for a group of independent transitions.

        Phase 4b: was ThreadPoolExecutor (GIL-bound, overhead > benefit).
        Now uses a single vectorised numpy Poisson call — O(1) C overhead
        regardless of group size.
        """
        lam = np.array(
            [max(0.0, propensities[all_transitions.index(t)]) for t in group],
            dtype=np.float64,
        ) * tau
        k = self.poisson_sampler.rng.poisson(lam=lam)
        return {t: int(k[i]) for i, t in enumerate(group)}
    
    def _sample_sequential(
        self,
        transitions: List[Any],
        propensities: List[float],
        tau: float
    ) -> Dict[Any, int]:
        """Sample firings for all transitions using vectorised numpy Poisson.

        Phase 4b: replaces the Python for-loop that called poisson_sampler.sample()
        once per transition.  Single numpy C call regardless of N transitions.
        """
        lam = np.maximum(0.0, np.array(propensities, dtype=np.float64)) * tau
        k   = self.poisson_sampler.rng.poisson(lam=lam)
        self.stats['total_sequential_samples'] += len(transitions)
        return {t: int(k[i]) for i, t in enumerate(transitions)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        total_samples = (self.stats['total_parallel_samples'] + 
                        self.stats['total_sequential_samples'])
        
        parallel_pct = (self.stats['total_parallel_samples'] / total_samples * 100 
                       if total_samples > 0 else 0.0)
        
        return {
            **self.stats,
            'total_samples': total_samples,
            'parallel_percentage': parallel_pct
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            'parallel_groups': 0,
            'sequential_groups': 0,
            'total_parallel_samples': 0,
            'total_sequential_samples': 0
        }
