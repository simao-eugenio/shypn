#!/usr/bin/env python3
"""Data Collector for simulation time-series recording.

Collects place tokens and transition firing counts at each simulation step.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
import logging
import numpy as np

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

        # S5 (engine_stability_audit 2026-04-29): adaptive recording.
        # When the previous engine step's τ falls below this threshold the next
        # record_state() call is forced, regardless of time-based decimation.
        # Captures sub-second transients on long horizons without exploding
        # storage during coarse-step regions.  None disables.
        self.adaptive_tau_threshold: Optional[float] = getattr(
            config, 'adaptive_tau_threshold', None
        )
        self._last_step_tau: Optional[float] = None
        
        # Thermodynamic validation results (populated at simulation end)
        self.validation_results = None

        # Phase 5 — fast recording state (built in start_collection)
        # Ordered lists of place/transition objects to iterate in record_state.
        # Only contains *recorded* objects so the hot loop skips unrecorded ones.
        self._rec_places: List[Any] = []
        self._rec_transitions: List[Any] = []
        # Flag: skip the expensive _evaluate_rate_at_enablement loop entirely.
        # Set to True in batch mode where rates come from the C accelerator.
        self._skip_rate_eval: bool = False
        # Pre-allocated numpy recording buffers (enabled by n_steps_hint).
        self._buf_enabled: bool = False
        self._buf_ptr: int = 0
        self._t_buf: Optional[np.ndarray] = None     # (max_pts,)           float64
        self._p_buf: Optional[np.ndarray] = None     # (max_pts, n_places)  float32
        self._p_buf_ids: List[str] = []              # place IDs in column order
        self._buf_cap: int = 0                       # allocated row count

    def start_collection(
        self,
        n_steps_hint: Optional[int] = None,
        skip_rate_eval: bool = False,
    ) -> None:
        """Initialize data structures and start collecting.

        If recorded_objects is None or empty, records ALL places and transitions.
        Otherwise, only records objects in the recorded_objects set.

        Args:
            n_steps_hint: Expected number of *recorded* time points.  When
                given, pre-allocates compact numpy float32 buffers for place
                tokens instead of Python list-of-tuples, cutting per-step
                allocation cost to a single numpy row-fill.  The buffers are
                converted back to the standard format by :meth:`finalize_buf`
                (called automatically from :meth:`stop_collection`).
            skip_rate_eval: If True, skip the expensive per-transition rate
                evaluation inside :meth:`record_state`.  Use in batch /
                tau-leaping mode where propensities are already computed by
                the C accelerator.
        """
        self.time_points = []
        self._record_counter = 0
        self._last_recorded_time = None
        self._skip_rate_eval = skip_rate_eval
        self._buf_enabled = False
        self._buf_ptr = 0

        # Refresh recorded_objects from controller settings if available
        if self.controller and hasattr(self.controller, 'settings'):
            if hasattr(self.controller.settings, 'recorded_objects'):
                self.recorded_objects = self.controller.settings.recorded_objects

        # Build place/transition dicts keyed to recorded IDs only
        if not self.recorded_objects:
            self.place_data       = {p.id: [] for p in self.model.places}
            self.transition_data  = {t.id: [] for t in self.model.transitions}
            self.transition_rates = ({} if skip_rate_eval
                                     else {t.id: [] for t in self.model.transitions})
            self._rec_places      = list(self.model.places)
            self._rec_transitions = list(self.model.transitions)
        else:
            self.place_data = {
                p.id: [] for p in self.model.places if p.id in self.recorded_objects
            }
            self.transition_data = {
                t.id: [] for t in self.model.transitions if t.id in self.recorded_objects
            }
            self.transition_rates = ({} if skip_rate_eval else {
                t.id: [] for t in self.model.transitions if t.id in self.recorded_objects
            })
            self._rec_places      = [p for p in self.model.places      if p.id in self.recorded_objects]
            self._rec_transitions = [t for t in self.model.transitions if t.id in self.recorded_objects]

        # Phase 5.1: pre-allocated numpy place-token buffer
        if n_steps_hint and n_steps_hint > 0 and self._rec_places:
            cap = n_steps_hint + 64
            self._buf_cap   = cap
            self._t_buf     = np.empty(cap, dtype=np.float64)
            self._p_buf     = np.empty((cap, len(self._rec_places)), dtype=np.float32)
            self._p_buf_ids = [p.id for p in self._rec_places]
            self._buf_enabled = True

        self.is_collecting = True
        
    def record_state(self, current_time: float, force: bool = False) -> None:
        """Record current state at given time point.
        
        Args:
            current_time: Current simulation time
            force: If True, bypass recording interval checks (for initial/final states)
        """
        if not self.is_collecting:
            return

        # S5: force-record transient steps (small τ indicates fast dynamics).
        if (
            not force
            and self.adaptive_tau_threshold is not None
            and self._last_step_tau is not None
            and self._last_step_tau < self.adaptive_tau_threshold
        ):
            force = True

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

        # ── Phase 5: fast path — numpy buffer fill ────────────────────────────
        if self._buf_enabled:
            assert self._t_buf is not None  # allocated when _buf_enabled is set
            assert self._p_buf is not None
            ptr = self._buf_ptr
            if ptr >= self._buf_cap:
                # Grow buffer by 50 % to handle underestimated n_steps_hint
                new_cap = max(self._buf_cap + 64, int(self._buf_cap * 1.5))
                self._t_buf = np.resize(self._t_buf, new_cap)
                new_p: np.ndarray = np.empty((new_cap, len(self._rec_places)), dtype=np.float32)
                new_p[:self._buf_cap] = self._p_buf
                self._p_buf = new_p
                self._buf_cap = new_cap

            self._t_buf[ptr] = current_time
            p_row = self._p_buf[ptr]
            for col, place in enumerate(self._rec_places):
                p_row[col] = place.tokens
            self._buf_ptr += 1

            # Always record transition firing counts (cheap — just int getAttribute).
            # This must NOT be gated by _skip_rate_eval: that flag controls
            # expensive rate/propensity evaluation, not cumulative firing counts.
            for transition in self._rec_transitions:
                count = getattr(transition, 'firing_count', 0)
                self.transition_data[transition.id].append((current_time, count))
            return  # skip rate-eval entirely in fast path

        # ── Standard path — Python list-of-tuples ────────────────────────────
        # Iterate ONLY the pre-filtered recorded places (fixes selective-recording
        # KeyError bug and avoids touch of all 58 places when only 5 are recorded)
        for place in self._rec_places:
            self.place_data[place.id].append((current_time, place.tokens))

        for transition in self._rec_transitions:
            count = getattr(transition, 'firing_count', 0)
            self.transition_data[transition.id].append((current_time, count))

            if self._skip_rate_eval:
                continue

            # Instantaneous rate/propensity evaluation (expensive — skipped in batch)
            rate = 0.0
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
                    logger = logging.getLogger(__name__)
                    if not hasattr(self, '_rate_eval_errors'):
                        self._rate_eval_errors: Set[Any] = set()
                    if transition.id not in self._rate_eval_errors:
                        logger.warning(f"Rate evaluation failed for transition {transition.id}: {e}")
                        self._rate_eval_errors.add(transition.id)
                    rate = 0.0
            
            self.transition_rates[transition.id].append(rate)

    # ------------------------------------------------------------------
    # Phase 5 helpers
    # ------------------------------------------------------------------

    def finalize_buf(self) -> None:
        """Flush pre-allocated numpy place buffers into place_data.

        Called automatically by :meth:`stop_collection`.  Safe to call
        multiple times (no-op if buffer not enabled or already finalised).

        place_data values are stored as compact float32 numpy arrays (values
        only; the matching time grid lives in self.time_points).  This is
        ~16× smaller than the equivalent Python list-of-(time, value) tuples
        and avoids per-replicate RAM explosions during batch sweeps.
        """
        if not self._buf_enabled or self._buf_ptr == 0:
            return
        n = self._buf_ptr
        t_arr = self._t_buf[:n]         # type: ignore[index]
        p_arr = self._p_buf[:n, :]      # type: ignore[index]

        # Rebuild time_points list (was empty / partial while buf was active)
        self.time_points = list(t_arr)

        # Store place_data as compact float32 numpy arrays (values only).
        # 16× less RAM than list-of-tuples; downstream consumers handle both
        # formats via isinstance(..., np.ndarray) checks.
        for col, pid in enumerate(self._p_buf_ids):
            self.place_data[pid] = p_arr[:, col].copy()

        # Disable buffer so further record_state calls use the list path
        self._buf_enabled = False
        self._buf_ptr = 0
    
    def record_event(self, time: float, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
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

    def notify_step_size(self, tau: float) -> None:
        """Engine hook: report the τ of the step that just executed.

        S5 (engine_stability_audit 2026-04-29): used by adaptive recording so
        the next ``record_state`` call can decide whether to force-record a
        transient sample.  Cheap (single attribute write); call freely.
        """
        self._last_step_tau = tau
    
    def record_firing(self, time: float, transition: Any, consumed: Optional[Dict[str, Any]] = None, produced: Optional[Dict[str, Any]] = None, mode: Optional[str] = None, firings: int = 1) -> None:
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
        self.finalize_buf()  # Phase 5: flush numpy buffer if active
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
            return bool(exporter.export_timeseries_wide(filepath))
        else:  # format == 'long'
            return bool(exporter.export_timeseries_long(filepath))
    
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
        return bool(exporter.export(
            filepath,
            include_metadata=include_metadata,
            include_timeseries=include_timeseries,
            include_statistics=include_statistics
        ))
