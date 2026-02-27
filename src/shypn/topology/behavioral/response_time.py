"""Response time analyzer for Petri nets.

This module analyzes response time characteristics of Petri nets,
measuring latency between events, transition firing sequences, and
end-to-end delays.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import logging
import statistics

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


class ResponseTimeAnalyzer(TopologyAnalyzer):
    """Analyzer for computing response time metrics of Petri nets.
    
    Response time analysis measures the latency between events and the
    time required for transitions to complete. This is critical for
    real-time systems and performance evaluation.
    
    Key capabilities:
    - Measure transition-to-transition delays
    - Compute path latencies
    - Identify critical paths (longest delays)
    - Calculate average response times
    - Track inter-firing times
    - Detect timing bottlenecks
    
    The analyzer simulates the net's execution and records timing
    information for each transition firing and token movement.
    
    Example:
        analyzer = ResponseTimeAnalyzer(model)
        result = analyzer.analyze(max_steps=10000)
        if result.success:
            delays = result.data['transition_delays']
            print(f"t1 to t2 delay: {delays.get(('t1', 't2'), 'N/A')}")
    """
    
    def __init__(self, model):
        """Initialize the response time analyzer.
        
        Args:
            model: The Petri net model to analyze
        """
        super().__init__(model)
        self._firing_times: Dict[str, List[int]] = {}
        self._inter_firing_times: Dict[str, List[int]] = {}
        self._transition_delays: Dict[Tuple[str, str], List[int]] = {}
        
    def analyze(
        self,
        initial_marking: Optional[Dict[str, int]] = None,
        max_steps: int = 10000,
        max_time: float = 60.0,
        source_transitions: Optional[List[str]] = None,
        target_transitions: Optional[List[str]] = None
    ) -> AnalysisResult:
        """Analyze response time characteristics of the Petri net.
        
        Args:
            initial_marking: Initial marking (uses model's initial if None)
            max_steps: Maximum simulation steps
            max_time: Maximum computation time in seconds
            source_transitions: Source transitions to measure from (all if None)
            target_transitions: Target transitions to measure to (all if None)
            
        Returns:
            AnalysisResult containing:
                - firing_times: When each transition fired
                - inter_firing_times: Time between consecutive firings
                - transition_delays: Delays between transition pairs
                - avg_response_times: Average delays per pair
                - critical_paths: Longest delay paths
                - statistics: Analysis statistics
                - summary: Text summary
        """
        try:
            self._validate_model()
            start_time = self._start_timer()
            
            # Clear previous analysis
            self._firing_times.clear()
            self._inter_firing_times.clear()
            self._transition_delays.clear()
            
            # Initialize tracking
            # Handle both dict and list formats for transitions
            trans_list = list(self.model.transitions.keys()) if hasattr(self.model.transitions, 'keys') else [t.id for t in self.model.transitions]
            
            for trans_id in trans_list:
                self._firing_times[trans_id] = []
                self._inter_firing_times[trans_id] = []
            
            # Set source and target transitions
            if source_transitions is None:
                source_transitions = trans_list
            if target_transitions is None:
                target_transitions = trans_list
            
            # Get initial marking
            if initial_marking is None:
                initial_marking = self._get_initial_marking()
            
            # Run simulation
            current_marking = initial_marking.copy()
            steps = 0
            recent_firings = deque(maxlen=100)  # Track recent firings for delay calculation
            deadlock_count = 0
            max_deadlocks = 100
            
            while steps < max_steps:
                # Check time limit
                if self._get_elapsed_time(start_time) > max_time:
                    break
                
                # Get enabled transitions
                enabled = self._get_enabled_transitions(current_marking)
                
                if not enabled:
                    deadlock_count += 1
                    if deadlock_count >= max_deadlocks:
                        break
                    # Reset to initial marking
                    current_marking = initial_marking.copy()
                    continue
                
                deadlock_count = 0
                
                # Select and fire a transition
                trans_id = enabled[0]
                
                # Record firing time
                self._firing_times[trans_id].append(steps)
                
                # Calculate inter-firing time
                if len(self._firing_times[trans_id]) > 1:
                    prev_time = self._firing_times[trans_id][-2]
                    inter_time = steps - prev_time
                    self._inter_firing_times[trans_id].append(inter_time)
                
                # Calculate delays from recent firings
                for prev_trans, prev_time in recent_firings:
                    if prev_trans in source_transitions and trans_id in target_transitions:
                        delay = steps - prev_time
                        pair = (prev_trans, trans_id)
                        if pair not in self._transition_delays:
                            self._transition_delays[pair] = []
                        self._transition_delays[pair].append(delay)
                
                # Add to recent firings
                recent_firings.append((trans_id, steps))
                
                # Fire transition
                current_marking = self._fire_transition(current_marking, trans_id)
                
                steps += 1
            
            elapsed = self._end_timer(start_time)
            
            # Compute metrics
            avg_response_times = self._compute_average_delays()
            critical_paths = self._identify_critical_paths()
            avg_inter_firing = self._compute_average_inter_firing()
            
            # Build result
            data = {
                'firing_times': {
                    trans_id: times[:100]  # Limit output
                    for trans_id, times in self._firing_times.items()
                    if times
                },
                'inter_firing_times': avg_inter_firing,
                'transition_delays': avg_response_times,
                'critical_paths': critical_paths,
                'statistics': {
                    'total_steps': steps,
                    'total_firings': sum(len(times) for times in self._firing_times.values()),
                    'transitions_fired': sum(1 for times in self._firing_times.values() if times),
                    'transition_pairs_measured': len(self._transition_delays),
                    'computation_time': elapsed
                }
            }
            
            summary = self._create_summary(
                steps,
                avg_response_times,
                critical_paths
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
                    'analyzer': 'response_time',
                    'computation_time': elapsed,
                    'total_steps': steps,
                    'max_steps': max_steps
                }
            )
            
        except (ValueError, AttributeError, KeyError) as e:
            logger.error(f"Response time analysis failed: {e}", exc_info=True)
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                summary="Response time analysis failed"
            )
    
    def get_response_time(
        self,
        source: str,
        target: str
    ) -> Optional[float]:
        """Get average response time between two transitions.
        
        Args:
            source: Source transition ID
            target: Target transition ID
            
        Returns:
            Average delay in steps, or None if no data
        """
        if not self._transition_delays:
            raise RuntimeError("Must run analyze() before getting response times")
        
        pair = (source, target)
        delays = self._transition_delays.get(pair, [])
        
        if not delays:
            return None
        
        return statistics.mean(delays)
    
    def get_critical_path(self) -> Optional[Tuple[Tuple[str, str], float]]:
        """Get the critical path (longest average delay).
        
        Returns:
            Tuple of ((source, target), delay) or None if no data
        """
        if not self._transition_delays:
            raise RuntimeError("Must run analyze() before getting critical path")
        
        critical = self._identify_critical_paths()
        
        if not critical:
            return None
        
        return critical[0]
    
    def _compute_average_delays(self) -> Dict[Tuple[str, str], float]:
        """Compute average delays for all transition pairs."""
        avg_delays = {}
        
        for pair, delays in self._transition_delays.items():
            if delays:
                avg_delays[pair] = statistics.mean(delays)
        
        return avg_delays
    
    def _compute_average_inter_firing(self) -> Dict[str, float]:
        """Compute average inter-firing times for all transitions."""
        avg_inter = {}
        
        for trans_id, times in self._inter_firing_times.items():
            if times:
                avg_inter[trans_id] = statistics.mean(times)
        
        return avg_inter
    
    def _identify_critical_paths(
        self,
        top_n: int = 5
    ) -> List[Tuple[Tuple[str, str], float]]:
        """Identify critical paths (longest delays).
        
        Args:
            top_n: Number of top paths to return
            
        Returns:
            List of ((source, target), avg_delay) tuples
        """
        if not self._transition_delays:
            return []
        
        # Compute average delays
        avg_delays = []
        for pair, delays in self._transition_delays.items():
            if delays:
                avg_delay = statistics.mean(delays)
                avg_delays.append((pair, avg_delay))
        
        # Sort by delay (descending)
        avg_delays.sort(key=lambda x: x[1], reverse=True)
        
        return avg_delays[:top_n]
    
    def _get_elapsed_time(self, start_time: float) -> float:
        """Get elapsed time since start."""
        import time
        return time.time() - start_time
    
    def _create_summary(
        self,
        steps: int,
        avg_delays: Dict[Tuple[str, str], float],
        critical_paths: List[Tuple[Tuple[str, str], float]]
    ) -> str:
        """Create a human-readable summary."""
        lines = [f"Response time analysis: {steps} steps simulated"]
        
        # Number of transition pairs measured
        lines.append(f"{len(avg_delays)} transition pairs measured")
        
        # Critical path
        if critical_paths:
            (source, target), delay = critical_paths[0]
            lines.append(f"Critical path: {source}→{target} ({delay:.2f} steps)")
        
        return " | ".join(lines)
    
    def clear_cache(self):
        """Clear cached analysis results."""
        super().clear_cache()
        self._firing_times.clear()
        self._inter_firing_times.clear()
        self._transition_delays.clear()
