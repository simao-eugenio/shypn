#!/usr/bin/env python3
"""Data Collector for simulation time-series recording.

Collects place tokens and transition firing counts at each simulation step.
"""
from typing import Dict, List, Tuple, Optional


class DataCollector:
    """Collects time-series data during simulation.
    
    Records:
    - Time points (list of floats)
    - Place tokens at each time point (dict: place_id -> list of token counts)
    - Transition firings at each time point (dict: transition_id -> cumulative count)
    
    Thread-safe for single-threaded GTK event loop.
    """
    
    def __init__(self, model, controller=None):
        """Initialize data collector.
        
        Args:
            model: DocumentModel instance with places and transitions
            controller: Optional SimulationController for accessing behavior cache
        """
        self.model = model
        self.controller = controller  # For accessing behavior cache
        self.time_points: List[float] = []
        self.place_data: Dict[str, List[int]] = {}
        self.transition_data: Dict[str, List[int]] = {}  # Cumulative counts
        self.transition_rates: Dict[str, List[float]] = {}  # Instantaneous rates/propensities
        self.is_collecting: bool = False
        
    def start_collection(self):
        """Initialize data structures and start collecting."""
        self.time_points = []
        
        # Initialize place data with empty lists
        self.place_data = {p.id: [] for p in self.model.places}
        
        # Initialize transition data with empty lists (cumulative counts)
        self.transition_data = {t.id: [] for t in self.model.transitions}
        
        # Initialize transition rates (instantaneous propensity/rate values)
        self.transition_rates = {t.id: [] for t in self.model.transitions}
        
        self.is_collecting = True
        
    def record_state(self, current_time: float):
        """Record current state at given time point.
        
        Args:
            current_time: Current simulation time
        """
        if not self.is_collecting:
            return
            
        self.time_points.append(current_time)
        
        # Record place tokens
        for place in self.model.places:
            tokens = place.tokens
            self.place_data[place.id].append(tokens)
            
        # Record transition firing counts (cumulative) AND instantaneous rates
        for transition in self.model.transitions:
            # Cumulative firing count
            count = getattr(transition, 'firing_count', 0)
            self.transition_data[transition.id].append(count)
            
            # Instantaneous rate/propensity - evaluate with CURRENT token state
            rate = 0.0
            
            # Get behavior from controller's cache (behaviors are created on-demand by controller)
            behavior = None
            if self.controller and hasattr(self.controller, 'behavior_cache'):
                behavior = self.controller.behavior_cache.get(transition.id)
                if not behavior:
                    # Behavior not in cache - try to create it
                    from shypn.engine import behavior_factory
                    try:
                        behavior = behavior_factory.create_behavior(transition, self.model)
                        self.controller.behavior_cache[transition.id] = behavior
                    except Exception as e:
                        pass
            
            if behavior:
                try:
                    # Force re-evaluation with current tokens by calling the method
                    # This ensures we get the rate based on current marking, not cached value
                    if hasattr(behavior, '_evaluate_rate_at_enablement'):
                        # This method evaluates the rate formula with current place tokens
                        rate = behavior._evaluate_rate_at_enablement(current_time)
                    elif hasattr(behavior, 'evaluate_rate'):
                        # For continuous transitions - needs places dict
                        places_dict = {p.id: p for p in self.model.places}
                        rate = behavior.evaluate_rate(places_dict, current_time)
                    elif hasattr(transition, 'rate'):
                        # Fallback: use static rate attribute (won't reflect token changes)
                        rate = float(transition.rate) if transition.rate else 0.0
                except Exception as e:
                    # If rate evaluation fails, log the error and use 0.0
                    import logging
                    logger = logging.getLogger(__name__)
                    if not hasattr(self, '_rate_eval_errors'):
                        self._rate_eval_errors = set()
                    if transition.id not in self._rate_eval_errors:
                        logger.warning(f"Rate evaluation failed for transition {transition.id}: {e}")
                        self._rate_eval_errors.add(transition.id)
                    rate = 0.0
            
            self.transition_rates[transition.id].append(rate)
    
    def record_event(self, time: float, event_type: str, data: dict = None):
        """Record a simulation event (for logging/debugging).
        
        This is used by τ-leaping and other advanced features to log
        internal events. Currently just logs, doesn't store long-term.
        
        Args:
            time: Event timestamp
            event_type: Type of event (e.g., 'tau_leap', 'ssa_step')
            data: Optional event data dictionary
        """
        # For now, just pass - this is used for debugging/logging
        # Could extend to store event history if needed
        pass
    
    def record_firing(self, time: float, transition, consumed: dict = None, 
                     produced: dict = None, mode: str = None, firings: int = 1):
        """Record a transition firing event.
        
        Used by τ-leaping and other engines to record firing details.
        Updates the transition's firing count.
        
        Args:
            time: Time of firing
            transition: Transition object that fired
            consumed: Map of place_id -> tokens consumed
            produced: Map of place_id -> tokens produced
            mode: Firing mode ('tau_leaping', 'gillespie', etc.)
            firings: Number of firings (for batch firings in τ-leaping)
        """
        # Update transition firing count
        if hasattr(transition, 'firing_count'):
            transition.firing_count += firings
        
        # For now, detailed firing events are just logged, not stored
        # Could extend to store firing history if needed for analysis
        pass
    
    def stop_collection(self):
        """Stop collecting data."""
        self.is_collecting = False
        
    def clear(self):
        """Clear all collected data."""
        self.time_points.clear()
        self.place_data.clear()
        self.transition_data.clear()
        self.is_collecting = False

    def clear_transition(self, transition_id: str) -> None:
        """Clear recorded series for a single transition.

        Keeps global time points and other transitions intact so that
        only the specified transition's firing history is reset.

        Args:
            transition_id: Identifier of the transition to clear.
        """
        if transition_id in self.transition_data:
            self.transition_data[transition_id].clear()
        
    def get_place_series(self, place_id: str) -> Tuple[List[float], List[int]]:
        """Get time-series for a specific place.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Tuple of (time_points, token_counts)
        """
        return self.time_points.copy(), self.place_data.get(place_id, []).copy()
        
    def get_transition_series(self, transition_id: str) -> Tuple[List[float], List[int]]:
        """Get time-series for a specific transition (cumulative firing counts).
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Tuple of (time_points, firing_counts)
        """
        return self.time_points.copy(), self.transition_data.get(transition_id, []).copy()
    
    def get_transition_rate_series(self, transition_id: str) -> Tuple[List[float], List[float]]:
        """Get instantaneous rate time-series for a specific transition.
        
        For transitions with rate functions, returns the evaluated rate values over time.
        For constant-rate transitions, returns the static rate repeated at each time point.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Tuple of (time_points, rate_values)
        """
        return self.time_points.copy(), self.transition_rates.get(transition_id, []).copy()
        
    def has_data(self) -> bool:
        """Check if any data has been collected.
        
        Returns:
            True if data is available, False otherwise
        """
        return len(self.time_points) > 0
    
    def get_data(self) -> Dict[str, any]:
        """Get collected data in format expected by exporters.
        
        Returns dictionary with:
        - time_points: List of time values
        - place_data: Dict mapping place_id to token counts
        - transition_data: Dict mapping transition_id to firing counts
        - model: Reference to DocumentModel
        
        Returns:
            Dict containing all collected trajectory data
        """
        return {
            'time_points': self.time_points,
            'place_data': self.place_data,
            'transition_data': self.transition_data,
            'model': self.model
        }
    
    def export_csv(self, filepath: str, format: str = 'wide') -> bool:
        """Export time-series data to CSV file.
        
        Wrapper around CSVSimulationExporter for programmatic export.
        
        Args:
            filepath: Output file path
            format: 'wide' (matrix layout) or 'long' (tidy format)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If format is not 'wide' or 'long'
        """
        from shypn.reporting.exporters.csv_simulation_exporter import CSVSimulationExporter
        
        if format not in ('wide', 'long'):
            raise ValueError(f"Invalid format '{format}'. Must be 'wide' or 'long'")
        
        exporter = CSVSimulationExporter(self.get_data(), {})
        
        if format == 'wide':
            return exporter.export_timeseries_wide(filepath)
        else:  # format == 'long'
            return exporter.export_timeseries_long(filepath)
    
    def export_json(self, filepath: str, 
                   include_metadata: bool = True,
                   include_timeseries: bool = True,
                   include_statistics: bool = True) -> bool:
        """Export complete simulation data to JSON file.
        
        Wrapper around JSONSimulationExporter for programmatic export.
        
        Args:
            filepath: Output file path
            include_metadata: Include metadata section (default: True)
            include_timeseries: Include time-series data (default: True)
            include_statistics: Include summary statistics (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        from shypn.reporting.exporters.json_simulation_exporter import JSONSimulationExporter
        
        exporter = JSONSimulationExporter(self.get_data(), {}, self.model)
        return exporter.export(
            filepath,
            include_metadata=include_metadata,
            include_timeseries=include_timeseries,
            include_statistics=include_statistics
        )
