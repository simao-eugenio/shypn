#!/usr/bin/env python3
"""Locality Runtime Analyzer - Runtime execution metrics for localities.

This module provides runtime analysis for locality behavior, including:
    pass
- Recent firing events history
- Throughput calculations over time windows
- Dynamic enablement state checking

This complements the structural analysis in LocalityAnalyzer with
runtime execution metrics.

Example:
    runtime = LocalityRuntimeAnalyzer(model, data_collector)
    
    # Get recent firing events
    events = runtime.get_recent_events(locality, window=10)
    for event in events:
    
        pass
    # Get throughput
    rate = runtime.get_throughput(locality, window=10)
    
    # Check if can fire now
    can_fire, reason = runtime.check_enablement(locality)
"""

from typing import Dict, List, Any, Tuple, Optional


class LocalityRuntimeAnalyzer:
    """Analyzer for runtime execution metrics of localities.
    
    Provides analysis of:
        pass
    - Transition firing history
    - Throughput/rate calculations
    - Dynamic enablement checking
    - Precondition evaluation
    
    This class works with the simulation data collector to provide
    real-time execution metrics that complement the structural analysis.
    
    Attributes:
        model: Reference to PetriNetModel
        data_collector: SimulationDataCollector for execution data
    
    Example:
        runtime = LocalityRuntimeAnalyzer(model, collector)
        
        # Get diagnostics for a transition
        diag = runtime.get_transition_diagnostics(transition, window=10)
    """
    
    def __init__(self, model: Any, data_collector: Any):
        """Initialize runtime analyzer.
        
        Args:
            model: PetriNetModel instance
            data_collector: SimulationDataCollector instance
        """
        self.model = model
        self.data_collector = data_collector
    
    def get_transition_diagnostics(self, transition: Any, window: int = 10) -> Dict[str, Any]:
        """Get comprehensive runtime diagnostics for a transition.
        
        Returns a diagnostic bundle with:
            pass
        - Logical time
        - Enabled state
        - Recent firing events
        - Throughput over window
        - Precondition details
        
        Args:
            transition: Transition object to analyze
            window: Number of recent events to include (default: 10)
            
        Returns:
            Dict containing:
                - transition_id: int
                - transition_name: str
                - logical_time: float (current simulation time)
                - enabled: bool (can fire now)
                - enablement_reason: str (why enabled/disabled)
                - recent_events: List[Dict] (firing history)
                - event_count: int (total events in window)
                - throughput: float (fires per time unit)
                - last_fired: float or None (time of last firing)
                - time_since_fire: float or None (time since last firing)
        
        Example:
            diag = runtime.get_transition_diagnostics(transition)
            
            
            if diag['last_fired']:
                pass
        """
        transition_id = transition.id
        transition_name = getattr(transition, 'name', f'T{transition_id}')
        
        # Get current simulation time
        logical_time = self._get_logical_time()
        
        # Check enablement
        enabled, reason = self.check_enablement(transition)
        
        # Get recent firing events
        recent_events = self.get_recent_events(transition, window)
        
        # Calculate throughput
        throughput = self.get_throughput(transition, window)
        
        # Find last firing time
        last_fired = None
        time_since_fire = None
        if recent_events:
            last_event = recent_events[-1]
            last_fired = last_event.get('time', 0.0)
            time_since_fire = logical_time - last_fired
        
        return {
            'transition_id': transition_id,
            'transition_name': transition_name,
            'logical_time': logical_time,
            'enabled': enabled,
            'enablement_reason': reason,
            'recent_events': recent_events,
            'event_count': len(recent_events),
            'throughput': throughput,
            'last_fired': last_fired,
            'time_since_fire': time_since_fire,
        }
    
    def get_recent_events(self, transition: Any, window: int = 10) -> List[Dict[str, Any]]:
        """Get recent firing events for a transition.
        
        Returns the last N firing events from the execution history.
        Events are returned in chronological order (oldest to newest).
        
        Args:
            transition: Transition object
            window: Maximum number of events to return (default: 10)
            
        Returns:
            List of event dicts, each containing:
                - time: float (when event occurred)
                - type: str (event type, e.g., 'fire', 'enable', 'disable')
                - tokens_consumed: Dict[int, float] (optional)
                - tokens_produced: Dict[int, float] (optional)
        
        Example:
            events = runtime.get_recent_events(transition, window=5)
            for event in events:
                pass
        """
        if not self.data_collector:
            return []
        
        transition_id = transition.id
        
        # Try to get transition-specific data from collector
        try:
            # Get transition firing data (time, event_type, details format)
            transition_data = self.data_collector.get_transition_data(transition_id)
            
            if transition_data:
            
                pass
            if not transition_data:
                return []
            
            # Convert to event format and take last N
            # transition_data format: [(time, event_type, details), ...]
            events = []
            for entry in transition_data[-window:]:
                try:
                    time, event_type, details = entry  # Unpack all 3 elements
                    event = {
                        'time': time,
                        'type': event_type,
                        'transition_id': transition_id,
                    }
                    # Add details if available
                    if details:
                        event['details'] = details
                    events.append(event)
                except Exception as e:
                    print(f"[LocalityRuntime] ERROR unpacking event: {e}, entry={entry}")
                    continue
            
            return events
            
        except (AttributeError, KeyError) as e:
            # Fallback: no data available
            print(f"[LocalityRuntime] ERROR in get_recent_events: {e}")
            return []
    
    def get_throughput(self, transition: Any, window: int = 10) -> float:
        """Calculate transition throughput over time window.
        
        Computes the firing rate (fires per time unit) by counting
        firing events within the time window.
        
        Args:
            transition: Transition object
            window: Time window size (in simulation time units)
            
        Returns:
            Throughput in fires per time unit
            Returns 0.0 if no data or time window is zero
        
        Example:
            rate = runtime.get_throughput(transition, window=10.0)
        """
        if not self.data_collector:
            return 0.0
        
        transition_id = transition.id
        logical_time = self._get_logical_time()
        
        try:
            # Get all transition data
            transition_data = self.data_collector.get_transition_data(transition_id)
            
            if not transition_data:
                return 0.0
            
            # Count events within time window
            window_start = max(0.0, logical_time - window)
            fire_count = 0
            
            for entry in transition_data:
                time, event_type, details = entry  # Unpack all 3 elements
                if time >= window_start and time <= logical_time:
                    # Count firing events (not just enable/disable)
                    if 'fire' in str(event_type).lower() or event_type == 'transition':
                        fire_count += 1
            
            # Calculate rate
            actual_window = logical_time - window_start
            if actual_window > 0:
                return fire_count / actual_window
            else:
                return 0.0
                
        except (AttributeError, KeyError):
            return 0.0
    
    def check_enablement(self, transition: Any) -> Tuple[bool, str]:
        """Check if transition can fire now and why.
        
        Performs dynamic precondition evaluation including:
            pass
        - Input place token availability
        - Arc weight requirements
        - Guard conditions (if any)
        - Transition type constraints
        
        Args:
            transition: Transition object to check
            
        Returns:
            Tuple of (can_fire: bool, reason: str)
            - can_fire: True if all preconditions satisfied
            - reason: Human-readable explanation
        
        Example:
            can_fire, reason = runtime.check_enablement(transition)
            if can_fire:
                pass
            else:
                pass
        """
        transition_id = transition.id
        transition_name = getattr(transition, 'name', f'T{transition_id}')
        transition_type = getattr(transition, 'transition_type', 'immediate')
        
        try:
            # Get input arcs
            input_arcs = [arc for arc in self.model.arcs 
                         if arc.target == transition_id and arc.arc_type == 'normal']
            
            if not input_arcs:
                return (True, f"No input arcs - can fire (type: {transition_type})")
            
            # Check each input place has sufficient tokens
            insufficient = []
            for arc in input_arcs:
                place = next((p for p in self.model.places if p.id == arc.source), None)
                if place:
                    required = getattr(arc, 'weight', 1)
                    available = getattr(place, 'tokens', 0)
                    
                    if available < required:
                        place_name = getattr(place, 'name', f'P{place.id}')
                        insufficient.append(f"{place_name} (need {required}, have {available})")
            
            if insufficient:
                return (False, f"Insufficient tokens: {', '.join(insufficient)}")
            
            # Check guard condition if present
            guard = getattr(transition, 'guard', None)
            if guard and guard.strip() and guard.strip().lower() != 'true':
                # TODO: Could evaluate guard here if needed
                return (True, f"Tokens available, guard: '{guard[:30]}...'")
            
            return (True, f"All preconditions satisfied (type: {transition_type})")
            
        except Exception as e:
            return (False, f"Error checking preconditions: {str(e)}")
    
    def _get_logical_time(self) -> float:
        """Get current simulation logical time.
        
        Returns:
            Current simulation time, or 0.0 if not available
        """
        try:
            if hasattr(self.model, 'logical_time'):
                return float(self.model.logical_time)
            elif hasattr(self.model, 'current_time'):
                return float(self.model.current_time)
            elif hasattr(self.model, 'time'):
                return float(self.model.time)
            else:
                return 0.0
        except (AttributeError, TypeError):
            return 0.0
    
    def format_diagnostics_report(self, transition: Any, window: int = 10) -> str:
        """Generate formatted diagnostic report for display.
        
        Creates a multi-line text report suitable for displaying
        in a TextView or console output.
        
        Args:
            transition: Transition to analyze
            window: Time window for metrics (default: 10)
            
        Returns:
            Formatted multi-line string report
        
        Example:
            report = runtime.format_diagnostics_report(transition)
            textview.get_buffer().set_text(report)
        """
        diag = self.get_transition_diagnostics(transition, window)
        
        lines = [
            "=== Runtime Diagnostic Report ===",
            "",
            f"Transition: {diag['transition_name']} (ID: {diag['transition_id']})",
            f"Simulation Time: {diag['logical_time']:.2f}s",
            "",
            "--- Current State ---",
            f"Enabled: {'✓ Yes' if diag['enabled'] else '✗ No'}",
            f"Reason: {diag['enablement_reason']}",
            "",
        ]
        
        # Last firing info
        if diag['last_fired'] is not None:
            lines.extend([
                "--- Recent Activity ---",
                f"Last Fired: {diag['last_fired']:.2f}s",
                f"Time Since: {diag['time_since_fire']:.2f}s ago",
                f"Event Count (last {window} events): {diag['event_count']}",
                f"Throughput: {diag['throughput']:.3f} fires/sec",
                "",
            ])
        else:
            lines.extend([
                "--- Recent Activity ---",
                "No firing events recorded",
                "",
            ])
        
        # Recent events list
        if diag['recent_events']:
            lines.append("--- Recent Events ---")
            for i, event in enumerate(diag['recent_events'][-5:], 1):  # Show last 5
                time_val = event.get('time', 0.0)
                event_type = event.get('type', 'unknown')
                lines.append(f"  {i}. t={time_val:.2f}s: {event_type}")
            
            if len(diag['recent_events']) > 5:
                lines.append(f"  ... and {len(diag['recent_events']) - 5} more")
        
        return "\n".join(lines)


__all__ = ['LocalityRuntimeAnalyzer']
