#!/usr/bin/env python3
"""Data Collector for simulation time-series recording.

Collects place tokens and transition firing counts at each simulation step.
"""
from typing import Any, Dict, List, Set, Tuple, Optional
import logging
from shypn.core.value_objects import RecordingConfig
from shypn.utils.safe_eval import safe_eval_numeric


class DataCollector:
    """Collects time-series data during simulation.
    
    Records:
    - Time points (list of floats)
    - Place tokens at each time point (dict: place_id -> list of token counts)
    - Transition firings at each time point (dict: transition_id -> cumulative count)
    
    Thread-safe for single-threaded GTK event loop.
    """
    
    def __init__(self, model: Any, controller: Any=None, config: Optional[Any] = None):
        """Initialize data collector.
        
        REFACTORED: Now uses RecordingConfig value object (reduced from 6 parameters to 2).
        
        Args:
            model: DocumentModel instance with places and transitions
            controller: Optional SimulationController for accessing behavior cache
            config: RecordingConfig with recording parameters (default: RecordingConfig.default())
        """
        if config is None:
            config = RecordingConfig.default()
        
        self.model = model
        self.controller = controller  # For accessing behavior cache
        self.recorded_objects = config.recorded_objects  # Store for filtering
        self.time_points: List[float] = []
        self.place_data: Dict[str, List[Any]] = {}
        self.transition_data: Dict[str, List[Any]] = {}  # Cumulative counts
        self.transition_rates: Dict[str, List[float]] = {}  # Instantaneous rates/propensities
        self.is_collecting: bool = False
        self.recording_interval = config.recording_interval
        self._record_counter = 0  # Track calls to record_state
        self.time_based_recording = config.time_based_recording
        self.recording_time_interval = config.recording_time_interval
        self._last_recorded_time: Optional[float] = None  # Track last recording time for time-based mode
        
        # Thermodynamic validation results (populated at simulation end)
        self.validation_results = None
        
    def start_collection(self) -> None:
        """Initialize data structures and start collecting.
        
        If recorded_objects is None or empty, records ALL places and transitions.
        Otherwise, only records objects in the recorded_objects set.
        """
        self.time_points = []
        self._record_counter = 0  # Reset counter
        self._last_recorded_time = None  # Reset time tracking
        
        # Refresh recorded_objects from controller settings if available
        # This ensures we pick up any objects added to analysis after initialization
        if self.controller and hasattr(self.controller, 'settings'):
            if hasattr(self.controller.settings, 'recorded_objects'):
                self.recorded_objects = self.controller.settings.recorded_objects
        
        # If no objects specified, record everything (default behavior)
        if not self.recorded_objects:
            # Initialize place data with empty lists for ALL places
            self.place_data = {p.id: [] for p in self.model.places}
            
            # Initialize transition data with empty lists for ALL transitions
            self.transition_data = {t.id: [] for t in self.model.transitions}
            
            # Initialize transition rates for ALL transitions
            self.transition_rates = {t.id: [] for t in self.model.transitions}
        else:
            # Selective recording: only initialize data for recorded objects
            self.place_data = {p.id: [] for p in self.model.places if p.id in self.recorded_objects}
            self.transition_data = {t.id: [] for t in self.model.transitions if t.id in self.recorded_objects}
            self.transition_rates = {t.id: [] for t in self.model.transitions if t.id in self.recorded_objects}
        
        self.is_collecting = True
        
    def record_state(self, current_time: float, force: bool = False) -> None:
        """Record current state at given time point.
        
        Args:
            current_time: Current simulation time
            force: If True, bypass recording interval checks (for initial/final states)
        """
        if not self.is_collecting:
            return
        
        # Time-based recording: guarantees consistent data density regardless of playback speed
        if self.time_based_recording and not force:
            # Always record first point
            if self._last_recorded_time is None:
                self._last_recorded_time = current_time
            # Record if enough model time has elapsed
            elif (current_time - self._last_recorded_time) >= self.recording_time_interval:
                self._last_recorded_time = current_time
            else:
                return  # Skip - not enough time elapsed
        elif not force:
            # Legacy step-based recording - only record every Nth call
            self._record_counter += 1
            if self._record_counter % self.recording_interval != 0:
                return  # Skip this recording
            
        self.time_points.append(current_time)
        
        # Record place tokens as (time, tokens) tuples
        for place in self.model.places:
            tokens = place.tokens
            self.place_data[place.id].append((current_time, tokens))
            
        # Record transition firing counts (cumulative) AND instantaneous rates as tuples
        for transition in self.model.transitions:
            # Cumulative firing count stored as (time, count) tuple
            count = getattr(transition, 'firing_count', 0)
            self.transition_data[transition.id].append((current_time, count))
            
            # Instantaneous rate/propensity - evaluate with CURRENT token state
            rate = 0.0
            
            # Get behavior from controller's cache (behaviors are created on-demand by controller)
            behavior = None
            if self.controller and hasattr(self.controller, 'behavior_cache'):
                behavior = self.controller.behavior_cache.get(id(transition))
                if not behavior:
                    # Behavior not in cache - try to create it
                    from shypn.engine import behavior_factory
                    try:
                        behavior = behavior_factory.create_behavior(transition, self.model)
                        self.controller.behavior_cache[id(transition)] = behavior
                    except Exception as e:
                        logging.getLogger(__name__).debug(f"Behavior creation failed for transition {transition.id}: {e}")
                        pass
            
            if behavior:
                try:
                    # Evaluate rate based on transition type
                    if hasattr(behavior, 'evaluate_rate'):
                        # Continuous transitions use evaluate_rate()
                        places_dict = {p.id: p for p in self.model.places}
                        rate = behavior.evaluate_rate(places_dict, current_time)
                    elif hasattr(behavior, 'get_propensity'):
                        # Stochastic transitions use get_propensity() which evaluates formula
                        rate = behavior.get_propensity()
                    elif hasattr(behavior, '_evaluate_rate_at_enablement'):
                        # Timed transitions - evaluate rate formula with current tokens
                        rate = behavior._evaluate_rate_at_enablement(current_time)
                    else:
                        # Fallback: try to evaluate rate as a number or formula
                        if hasattr(transition, 'rate'):
                            rate_value = transition.rate
                            if isinstance(rate_value, (int, float)):
                                rate = float(rate_value)
                            elif isinstance(rate_value, str):
                                # Try to evaluate formula with place tokens
                                try:
                                    # Build evaluation context with place tokens
                                    eval_context = {p.id: p.tokens for p in self.model.places}
                                    # Also add place names as variables
                                    for p in self.model.places:
                                        eval_context[p.name] = p.tokens
                                    # Safely evaluate rate formula (replaces eval() for security)
                                    rate = safe_eval_numeric(rate_value, eval_context, default_on_error=0.0)
                                except Exception as eval_err:
                                    rate = 0.0
                            else:
                                rate = 0.0
                        else:
                            rate = 0.0
                except Exception as e:
                    # If rate evaluation fails, log the error and use 0.0
                    import logging
                    logger = logging.getLogger(__name__)
                    if not hasattr(self, '_rate_eval_errors'):
                        self._rate_eval_errors: Set[Any] = set()
                    if transition.id not in self._rate_eval_errors:
                        logger.warning(f"Rate evaluation failed for transition {transition.id}: {e}")
                        self._rate_eval_errors.add(transition.id)
                    rate = 0.0
            
            self.transition_rates[transition.id].append(rate)
    
    def record_event(self, time: float, event_type: str, data: Optional[dict] = None) -> None:
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
    
    def record_firing(self, time: float, transition: Any, consumed: Optional[dict] = None, produced: Optional[dict] = None, mode: Optional[str] = None, firings: int = 1) -> None:
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
    
    def stop_collection(self) -> None:
        """Stop collecting data."""
        self.is_collecting = False
        
    def clear(self) -> None:
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
    
    def get_data(self) -> Dict[str, Any]:
        """Get collected data in format expected by exporters.
        
        Returns dictionary with:
        - time_points: List of time values
        - place_data: Dict mapping place_id to token counts
        - transition_data: Dict mapping transition_id to firing counts
        - model: Reference to DocumentModel
        - validation_results: Dict of thermodynamic validation results (if available)
        
        Returns:
            Dict containing all collected trajectory data
        """
        return {
            'time_points': self.time_points,
            'place_data': self.place_data,
            'transition_data': self.transition_data,
            'model': self.model,
            'validation_results': self.validation_results
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
