"""Throughput analyzer for Petri nets.

This module analyzes the throughput characteristics of Petri nets,
measuring transition firing rates, token flow, and system capacity.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import logging
import statistics

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


class ThroughputAnalyzer(TopologyAnalyzer):
    """Analyzer for computing throughput metrics of Petri nets.
    
    Throughput analysis measures the rate at which transitions fire and
    tokens flow through the system. This is essential for performance
    evaluation and capacity planning.
    
    Key capabilities:
    - Compute transition firing rates
    - Measure token flow through places
    - Identify bottlenecks
    - Calculate system throughput
    - Detect resource utilization
    - Find critical paths
    
    The analyzer uses marking exploration to simulate the net's behavior
    and collect statistics about transition firings and token movements.
    
    Example:
        analyzer = ThroughputAnalyzer(model)
        result = analyzer.analyze(max_steps=10000)
        if result.success:
            rates = result.data['firing_rates']
            print(f"Transition t1 fires at rate: {rates['t1']}")
    """
    
    def __init__(self, model):
        """Initialize the throughput analyzer.
        
        Args:
            model: The Petri net model to analyze
        """
        super().__init__(model)
        self._firing_counts: Dict[str, int] = {}
        self._token_flow: Dict[str, int] = {}
        self._place_occupancy: Dict[str, List[int]] = {}
        
    def analyze(  # type: ignore[override]
        self,
        initial_marking: Optional[Dict[str, int]] = None,
        max_steps: int = 10000,
        max_time: float = 60.0,
        sampling_interval: int = 100
    ) -> AnalysisResult:
        """Analyze throughput characteristics of the Petri net.
        
        Args:
            initial_marking: Initial marking (uses model's initial if None)
            max_steps: Maximum simulation steps
            max_time: Maximum computation time in seconds
            sampling_interval: Steps between place occupancy samples
            
        Returns:
            AnalysisResult containing:
                - firing_rates: Transition firing frequencies
                - firing_counts: Raw firing counts per transition
                - token_flow: Token flow through places
                - place_occupancy: Average tokens per place
                - bottlenecks: Transitions with low firing rates
                - throughput: Overall system throughput
                - utilization: Resource utilization metrics
                - statistics: Analysis statistics
                - summary: Text summary
        """
        try:
            self._validate_model()
            start_time = self._start_timer()
            
            # Clear previous analysis
            self._firing_counts.clear()
            self._token_flow.clear()
            self._place_occupancy.clear()
            
            # Initialize tracking
            # Handle both dict and list formats
            trans_ids = self.model.transitions.keys() if hasattr(self.model.transitions, 'keys') else [t.id for t in self.model.transitions]
            place_ids = self.model.places.keys() if hasattr(self.model.places, 'keys') else [p.id for p in self.model.places]
            
            for trans_id in trans_ids:
                self._firing_counts[trans_id] = 0
            
            for place_id in place_ids:
                self._token_flow[place_id] = 0
                self._place_occupancy[place_id] = []
            
            # Get initial marking
            if initial_marking is None:
                initial_marking = self._get_initial_marking()
            
            # Run simulation
            current_marking = initial_marking.copy()
            steps = 0
            deadlock_count = 0
            max_deadlocks = 100  # Stop if stuck too long
            
            while steps < max_steps:
                # Check time limit
                if self._get_elapsed_time(start_time) > max_time:
                    break
                
                # Sample place occupancy periodically
                if steps % sampling_interval == 0:
                    for place_id, tokens in current_marking.items():
                        self._place_occupancy[place_id].append(tokens)
                
                # Get enabled transitions
                enabled = self._get_enabled_transitions(current_marking)
                
                if not enabled:
                    deadlock_count += 1
                    if deadlock_count >= max_deadlocks:
                        break
                    # Try to recover by resetting to initial marking
                    current_marking = initial_marking.copy()
                    continue
                
                deadlock_count = 0
                
                # Select and fire a transition (uniform random selection)
                # For deterministic behavior, use first enabled
                trans_id = enabled[0]
                
                # Fire transition
                current_marking = self._fire_transition(current_marking, trans_id)
                self._firing_counts[trans_id] += 1
                
                # Track token flow
                self._update_token_flow(trans_id)
                
                steps += 1
            
            elapsed = self._end_timer(start_time)
            
            # Compute metrics
            firing_rates = self._compute_firing_rates(steps)
            avg_occupancy = self._compute_average_occupancy()
            bottlenecks = self._identify_bottlenecks(firing_rates)
            utilization = self._compute_utilization(avg_occupancy)
            throughput = self._compute_system_throughput(firing_rates)
            
            # Build result
            data = {
                'firing_rates': firing_rates,
                'firing_counts': dict(self._firing_counts),
                'token_flow': dict(self._token_flow),
                'place_occupancy': avg_occupancy,
                'bottlenecks': bottlenecks,
                'throughput': throughput,
                'utilization': utilization,
                'statistics': {
                    'total_steps': steps,
                    'total_firings': sum(self._firing_counts.values()),
                    'computation_time': elapsed,
                    'transitions_active': sum(1 for c in self._firing_counts.values() if c > 0),
                    'transitions_total': len(self.model.transitions)
                }
            }
            
            summary = self._create_summary(
                steps,
                firing_rates,
                bottlenecks,
                throughput
            )
            
            warnings = []
            if steps >= max_steps:
                warnings.append(f"Reached maximum steps ({max_steps})")
            if elapsed >= max_time:
                warnings.append(f"Reached time limit ({max_time}s)")
            if deadlock_count >= max_deadlocks:
                warnings.append("Simulation stopped due to repeated deadlocks")
            
            return AnalysisResult(
                success=True,
                data=data,
                summary=summary,
                warnings=warnings,
                metadata={
                    'analyzer': 'throughput',
                    'computation_time': elapsed,
                    'total_steps': steps,
                    'max_steps': max_steps,
                    'sampling_interval': sampling_interval
                }
            )
            
        except (ValueError, AttributeError, KeyError) as e:
            logger.error(f"Throughput analysis failed: {e}", exc_info=True)
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                summary="Throughput analysis failed"
            )
    
    def get_firing_rate(self, transition_id: str) -> float:
        """Get the firing rate for a specific transition.
        
        Args:
            transition_id: ID of the transition
            
        Returns:
            Firing rate (firings per step)
        """
        if not self._firing_counts:
            raise RuntimeError("Must run analyze() before getting firing rates")
        
        total_steps = sum(self._firing_counts.values())
        if total_steps == 0:
            return 0.0
        
        return self._firing_counts.get(transition_id, 0) / total_steps
    
    def get_bottlenecks(self, threshold: float = 0.1) -> List[str]:
        """Get list of bottleneck transitions.
        
        Bottlenecks are transitions with firing rates below the threshold
        relative to the average firing rate.
        
        Args:
            threshold: Relative threshold (0-1)
            
        Returns:
            List of transition IDs that are bottlenecks
        """
        if not self._firing_counts:
            raise RuntimeError("Must run analyze() before getting bottlenecks")
        
        total_firings = sum(self._firing_counts.values())
        if total_firings == 0:
            return []
        
        avg_rate = total_firings / len(self._firing_counts)
        threshold_rate = avg_rate * threshold
        
        bottlenecks = [
            trans_id
            for trans_id, count in self._firing_counts.items()
            if count < threshold_rate
        ]
        
        return sorted(bottlenecks)
    
    def _update_token_flow(self, trans_id: str) -> None:
        """Update token flow statistics for a transition firing."""
        # Handle both dict and list formats for arcs
        arcs = self.model.arcs.values() if hasattr(self.model.arcs, 'values') else self.model.arcs
        
        # Count tokens flowing through output places
        for arc in arcs:
            arc_source = arc.source.id if hasattr(arc.source, 'id') else arc.source
            arc_target = arc.target.id if hasattr(arc.target, 'id') else arc.target
            
            if arc_source == trans_id:
                place_id = arc_target
                self._token_flow[place_id] += arc.weight
    
    def _compute_firing_rates(self, total_steps: int) -> Dict[str, float]:
        """Compute firing rates for all transitions."""
        if total_steps == 0:
            return {trans_id: 0.0 for trans_id in self._firing_counts}
        
        return {
            trans_id: count / total_steps
            for trans_id, count in self._firing_counts.items()
        }
    
    def _compute_average_occupancy(self) -> Dict[str, float]:
        """Compute average token occupancy for all places."""
        avg_occupancy = {}
        
        for place_id, samples in self._place_occupancy.items():
            if samples:
                avg_occupancy[place_id] = statistics.mean(samples)
            else:
                avg_occupancy[place_id] = 0.0
        
        return avg_occupancy
    
    def _identify_bottlenecks(
        self,
        firing_rates: Dict[str, float],
        threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Identify bottleneck transitions."""
        if not firing_rates:
            return []
        
        # Calculate average rate
        rates = [r for r in firing_rates.values() if r > 0]
        if not rates:
            return []
        
        avg_rate = statistics.mean(rates)
        threshold_rate = avg_rate * threshold
        
        bottlenecks = []
        for trans_id, rate in firing_rates.items():
            if rate < threshold_rate:
                bottlenecks.append({
                    'transition': trans_id,
                    'rate': rate,
                    'avg_rate': avg_rate,
                    'relative': rate / avg_rate if avg_rate > 0 else 0.0
                })
        
        # Sort by rate (lowest first)
        bottlenecks.sort(key=lambda x: x['rate'])  # type: ignore[arg-type, return-value]
        
        return bottlenecks
    
    def _compute_utilization(
        self,
        avg_occupancy: Dict[str, float]
    ) -> Dict[str, float]:
        """Compute resource utilization metrics."""
        utilization = {}
        
        for place_id, avg_tokens in avg_occupancy.items():
            # Get place capacity (if defined, otherwise use a default)
            # Handle both dict and list formats
            if hasattr(self.model.places, 'get'):
                place = self.model.places.get(place_id)
            else:
                # List format - need to find by ID
                place = next((p for p in self.model.places if p.id == place_id), None)
            
            if not place:
                continue
            
            # Try to get capacity attribute, handle Mock objects
            try:
                capacity = getattr(place, 'capacity', None)
                # Check if it's a valid number (not a Mock)
                if capacity is not None and isinstance(capacity, (int, float)) and capacity > 0:
                    utilization[place_id] = min(1.0, avg_tokens / capacity)
                else:
                    # Use relative utilization (normalized by max observed)
                    max_tokens = max(self._place_occupancy[place_id]) if self._place_occupancy[place_id] else 1
                    utilization[place_id] = avg_tokens / max(1, max_tokens)
            except (TypeError, AttributeError):
                # Fallback for Mock or other issues
                max_tokens = max(self._place_occupancy[place_id]) if self._place_occupancy[place_id] else 1
                utilization[place_id] = avg_tokens / max(1, max_tokens)
        
        return utilization
    
    def _compute_system_throughput(
        self,
        firing_rates: Dict[str, float]
    ) -> float:
        """Compute overall system throughput.
        
        System throughput is measured as the average firing rate
        across all transitions.
        """
        if not firing_rates:
            return 0.0
        
        active_rates = [r for r in firing_rates.values() if r > 0]
        if not active_rates:
            return 0.0
        
        return statistics.mean(active_rates)
    
    def _get_elapsed_time(self, start_time: float) -> float:
        """Get elapsed time since start."""
        import time
        return time.time() - start_time
    
    def _create_summary(
        self,
        steps: int,
        firing_rates: Dict[str, float],
        bottlenecks: List[Dict[str, Any]],
        throughput: float
    ) -> str:
        """Create a human-readable summary."""
        lines = [f"Throughput analysis: {steps} steps simulated"]
        
        # Active transitions
        active_count = sum(1 for r in firing_rates.values() if r > 0)
        lines.append(f"{active_count}/{len(firing_rates)} transitions active")
        
        # System throughput
        lines.append(f"System throughput: {throughput:.4f}")
        
        # Bottlenecks
        if bottlenecks:
            lines.append(f"{len(bottlenecks)} bottlenecks detected")
        
        return " | ".join(lines)
    
    def clear_cache(self) -> None:
        """Clear cached analysis results."""
        super().clear_cache()
        self._firing_counts.clear()
        self._token_flow.clear()
        self._place_occupancy.clear()
