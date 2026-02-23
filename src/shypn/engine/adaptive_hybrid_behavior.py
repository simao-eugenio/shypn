#!/usr/bin/env python3
"""Adaptive Hybrid Behavior - Runtime switching between ODE and Stochastic.

This behavior dynamically selects between continuous (ODE) and stochastic (SSA/τ-leaping)
execution based on molecular population size (tokens × compartment_volume) at runtime.

Key Features:
    - Automatic method selection based on molecule count thresholds
    - Seamless switching during simulation as populations change
    - Maintains state consistency across mode changes
    - Integrates with existing τ-leaping and continuous engines

Biological Motivation:
    Real biological systems operate in regimes where molecule counts vary:
    - Few molecules (< 100) → Stochastic noise dominates → Use SSA/τ-leaping
    - Many molecules (> 1000) → Deterministic approximation valid → Use ODE
    
    This adaptive approach matches how advanced hybrid simulation algorithms
    (like adaptive hybrid SSA/ODE) work in computational systems biology.

Usage:
    # Create adaptive transition (automatically switches based on molecule count)
    transition = Transition(..., transition_type='adaptive')
    behavior = AdaptiveHybridBehavior(transition, model)
    
    # During simulation:
    # - If molecule_count < 100 → Uses stochastic (τ-leaping)
    # - If molecule_count ≥ 100 → Uses continuous (ODE integration)
    # - Mode switches dynamically as populations change

# RESOLVED: Mass conservation enforced globally via ConservationEnforcer.
#           Mode switching WAS the primary issue (firing imbalance from desynchronization),
#           but this is now corrected after each simulation step.
#           Mathematical proof: Petri nets with asymmetric stoichiometry (2→1, 1→2)
#           violate token conservation when firings are imbalanced. This is NOT a bug,
#           but a fundamental property requiring external enforcement.
#           See CONSERVATION_ENFORCEMENT_INTEGRATION.md for proof & validation.
"""

import logging
from typing import Dict, Tuple, List, Any, Optional

from .transition_behavior import TransitionBehavior
from .continuous_behavior import ContinuousBehavior
from .stochastic_behavior import StochasticBehavior
from .spatial_utils import VolumeAdaptiveSelector


class AdaptiveHybridBehavior(TransitionBehavior):
    """Adaptive behavior that switches between continuous and stochastic.
    
    Implements runtime method selection based on molecular population size:
    - Calculates molecule count as: tokens × compartment_volume for each connected place
    - Switches to stochastic for low molecule counts (< threshold)
    - Switches to continuous for high molecule counts (≥ threshold)
    
    The behavior delegates to either ContinuousBehavior or StochasticBehavior
    based on current conditions, providing seamless integration with existing
    simulation engines (τ-leaping for stochastic, RK4 for continuous).
    
    Properties:
        volume_threshold (float): Molecule count threshold (default 100 molecules)
            Note: Despite the name 'volume_threshold' for backward compatibility,
            this now represents the molecule count threshold (tokens × volume)
        prefer_continuous (bool): Prefer continuous when volume not set (default True)
        adaptive_filter (str): Which places to check for molecule count (default 'inputs_only')
            - 'all': Check all input and output places
            - 'inputs_only': Check only input places (substrates drive propensity)
            - 'spatial_only': Check only places with compartment_volume property
            - 'inputs_spatial': Check input places with compartment_volume property
        suppress_adaptive_warnings (bool): Suppress warnings about missing places/volumes (default False)
        
    State Management:
        - Continuous mode: No scheduling needed, fires based on rate
        - Stochastic mode: Uses enablement_time and scheduled_fire_time
        - Mode switches: Preserves token state, resets scheduling
    
    Biological Rationale for 'inputs_only' (default):
        - Input places = substrates that determine reaction propensity
        - Output places = products that don't affect firing decision
        - Substrate molecule counts govern whether reaction uses stochastic or continuous dynamics
    
    Example:
        >>> behavior = AdaptiveHybridBehavior(transition, model)
        >>> # At t=0, input has 10 molecules → Uses stochastic
        >>> behavior.fire(...)  # Discrete burst firing
        >>> 
        >>> # Later, input has 500 molecules → Switches to continuous
        >>> behavior.integrate_step(...)  # Smooth ODE integration
    """
    
    # Class-level tracking to prevent duplicate warnings across all instances
    _warned_no_places_transitions = set()
    _warned_no_volumes_transitions = set()
    
    def __init__(self, transition, model):
        """Initialize adaptive hybrid behavior.
        
        Creates both continuous and stochastic behavior delegates.
        The volume selector determines which to use at runtime based on
        molecular population size (tokens × compartment_volume).
        
        Args:
            transition: Transition object with adaptive properties
            model: Model instance for context access
        """
        super().__init__(transition, model)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Extract adaptive parameters
        props = getattr(transition, 'properties', {})
        
        # Backward compatibility: 'volume_threshold' now means molecule count threshold
        # Old models: volume_threshold=1.0 (fL) → treat as legacy, use default 100
        # New models: volume_threshold=100 (molecules) → use as-is
        raw_threshold = props.get('volume_threshold', 100.0)
        
        # Heuristic: if threshold < 10, assume it's old fL-based value, use default
        if raw_threshold < 10.0:
            self.volume_threshold = 100.0  # Modern default: 100 molecules
            self.logger.info(
                f"Transition '{transition.name}': Converting legacy volume_threshold={raw_threshold} fL "
                f"to molecule_threshold={self.volume_threshold}"
            )
        else:
            self.volume_threshold = float(raw_threshold)
        
        self.prefer_continuous = props.get('prefer_continuous', True)
        
        # Place filtering strategy for mode selection
        # Options: 'all', 'inputs_only', 'spatial_only', 'inputs_spatial'
        self.place_filter = props.get('adaptive_filter', 'inputs_only')
        
        # Warning suppression (useful for transitions that intentionally have no connected places)
        self.suppress_warnings = props.get('suppress_adaptive_warnings', False)
        
        # Create behavior delegates
        self.continuous_behavior = ContinuousBehavior(transition, model)
        self.stochastic_behavior = StochasticBehavior(transition, model)
        
        # Volume-based selector (now uses molecule counts)
        self.volume_selector = VolumeAdaptiveSelector(threshold_molecules=self.volume_threshold)
        
        # Track current mode for mode change detection
        self._current_mode = None  # 'continuous' or 'stochastic'
        self._last_volume_check = None
        
        # Diagnostic counters (populated by _get_connected_places)
        self._input_count = 0
        self._output_count = 0
        self._input_with_volume = 0
        self._output_with_volume = 0
        
        # Deferred initialization flag (avoid accessing arcs during model loading)
        self._initialized = False
        
        self.logger.info(
            f"Created AdaptiveHybridBehavior for '{transition.name}' "
            f"(threshold={self.volume_threshold} molecules, filter={self.place_filter})"
        )
    
    def _get_connected_places(self) -> List:
        """Get places for mode selection based on filter strategy.
        
        Filter strategies:
            'all': All input and output places (original behavior)
            'inputs_only': Only input places (substrates drive propensity)
            'spatial_only': Only places with volume information
            'inputs_spatial': Input places with volume information
        
        Returns:
            List of Place objects filtered by strategy
        """
        # Check if arcs are loaded yet (avoid accessing during deserialization)
        if not hasattr(self.model, 'arcs') or not self.model.arcs:
            return []  # Silently return empty - model still loading
        
        # Mark as initialized on first successful arc access
        self._initialized = True
        
        all_input_places = []
        all_output_places = []
        
        # Get arcs connected to this transition
        input_arcs = self.get_input_arcs()
        output_arcs = self.get_output_arcs()

        
        # Collect input places
        # Input arcs: Place -> Transition, so arc.source is the Place
        for arc in input_arcs:
            # arc.source is already a Place object reference
            place = arc.source
            if place and place not in all_input_places:
                all_input_places.append(place)
        
        # Collect output places
        # Output arcs: Transition -> Place, so arc.target is the Place
        for arc in output_arcs:
            # arc.target is already a Place object reference
            place = arc.target
            if place and place not in all_output_places:
                all_output_places.append(place)
        
        # Store full counts for diagnostics
        self._input_count = len(all_input_places)
        self._output_count = len(all_output_places)
        self._input_with_volume = sum(1 for p in all_input_places if self._has_volume_info(p))
        self._output_with_volume = sum(1 for p in all_output_places if self._has_volume_info(p))
        
        # Apply filter strategy
        if self.place_filter == 'inputs_only':
            # Only check input places (substrates)
            return all_input_places
        
        elif self.place_filter == 'spatial_only':
            # Only check places that are spatial signals (signal_type == SPATIAL)
            # THEN check their volumes for mode selection
            all_places = all_input_places + all_output_places
            return [p for p in all_places if self._is_spatial_signal(p)]
        
        elif self.place_filter == 'inputs_spatial':
            # Only check input places that are spatial signals
            return [p for p in all_input_places if self._is_spatial_signal(p)]
        
        else:  # 'all' or unknown
            # Check all connected places (original behavior)
            all_places = all_input_places + all_output_places
            # Remove duplicates while preserving order
            seen = set()
            unique_places = []
            for p in all_places:
                if p.id not in seen:
                    seen.add(p.id)
                    unique_places.append(p)
            return unique_places
    
    def _has_volume_info(self, place) -> bool:
        """Check if place has volume information for adaptive mode selection.
        
        Args:
            place: Place object
        
        Returns:
            bool: True if place has compartment_volume property set
        """
        # Check for compartment_volume property (can be on ANY place)
        if hasattr(place, 'compartment_volume'):
            volume = getattr(place, 'compartment_volume', None)
            return volume is not None and volume > 0
        return False
    
    def _is_spatial_signal(self, place) -> bool:
        """Check if place is a spatial signal (legacy method, kept for compatibility).
        
        Args:
            place: Place object
        
        Returns:
            bool: True if place has SPATIAL signal type
        """
        if not hasattr(place, 'is_spatial_signal'):
            return False
        
        try:
            return place.is_spatial_signal()
        except (AttributeError, TypeError) as e:
            # Fallback: check signal_type attribute
            import logging
            logging.getLogger(__name__).debug(f"Failed to check is_spatial_signal, using fallback: {e}")
            from shypn.netobjs.signal_type import SignalType
            return getattr(place, 'signal_type', None) == SignalType.SPATIAL
    
    def _select_mode(self) -> str:
        """Select execution mode based on current molecule counts.
        
        Analyzes molecule counts (tokens × volume) of connected places and decides
        whether to use stochastic or continuous execution.
        
        Returns:
            'stochastic' or 'continuous'
        """
        places = self._get_connected_places()
        
        if not places:
            # No places matched filter - provide detailed diagnostic
            # Suppress warnings during initialization (arcs may not be loaded yet)
            if not self.suppress_warnings and self._initialized:
                transition_key = self.transition.name
                if transition_key not in AdaptiveHybridBehavior._warned_no_places_transitions:
                    # Build diagnostic message
                    if self._input_count == 0 and self._output_count == 0:
                        detail = "Transition has NO connected input or output arcs."
                    elif self.place_filter == 'inputs_only' and self._input_count == 0:
                        detail = f"Transition has NO input arcs ({self._output_count} output arcs exist)."
                    elif self.place_filter == 'inputs_spatial' and self._input_count > 0:
                        detail = f"Transition has {self._input_count} input place(s) but NONE have 'compartment_volume' property. Set compartment_volume on input places."
                    elif self.place_filter == 'spatial_only':
                        total = self._input_count + self._output_count
                        detail = f"Transition has {total} connected place(s) but NONE have 'compartment_volume' property. Set compartment_volume on places."
                    else:
                        detail = f"Filter '{self.place_filter}' matched no places (inputs={self._input_count}, outputs={self._output_count}, with_volume={self._input_with_volume + self._output_with_volume})."
                    
                    self.logger.warning(
                        f"Adaptive transition '{self.transition.name}': {detail} "
                        f"Defaulting to {'continuous' if self.prefer_continuous else 'stochastic'} mode."
                    )
                    AdaptiveHybridBehavior._warned_no_places_transitions.add(transition_key)
            return 'continuous' if self.prefer_continuous else 'stochastic'
        
        # Check volumes
        use_stochastic, details = self.volume_selector.analyze_transition(
            places, []  # All places (input and output)
        )
        
        self._last_volume_check = details
        
        # Warn if no volumes found (silent failure prevention - warn once per transition unless suppressed)
        if details.get('reason') == 'no-molecule-counts':
            if not self.suppress_warnings:
                transition_key = self.transition.name
                if transition_key not in AdaptiveHybridBehavior._warned_no_volumes_transitions:
                    self.logger.warning(
                        f"Adaptive transition '{self.transition.name}' has {len(places)} connected places "
                        f"but none have 'compartment_volume' or 'tokens' properties set. "
                        f"Defaulting to continuous mode. Set place.compartment_volume to enable adaptive behavior."
                    )
                    AdaptiveHybridBehavior._warned_no_volumes_transitions.add(transition_key)
        
        mode = 'stochastic' if use_stochastic else 'continuous'
        
        # Cache the mode (without triggering full mode change logic)
        if self._current_mode != mode:
            self._current_mode = mode
        
        return mode
    
    def _handle_mode_change(self, new_mode: str):
        """Handle transition between execution modes.
        
        When mode changes, we need to:
        1. Clear stochastic scheduling state if switching away
        2. Log the mode change for diagnostics
        3. Update current mode tracker
        
        Args:
            new_mode: New mode ('continuous' or 'stochastic')
        """
        if self._current_mode == new_mode:
            return  # No change
        
        old_mode = self._current_mode
        self._current_mode = new_mode
        
        # Log mode change
        if old_mode is not None:
            check_info = self._last_volume_check or {}
            self.logger.info(
                f"Transition '{self.transition.name}' mode change: "
                f"{old_mode} → {new_mode} "
                f"(min_molecules={check_info.get('min_molecules', 'N/A')}, "
                f"threshold={self.volume_threshold} molecules)"
            )
        
        # Clear stochastic scheduling state when switching away from stochastic
        if old_mode == 'stochastic' and new_mode == 'continuous':
            self.stochastic_behavior.clear_enablement()
    
    def _evaluate_rate_at_enablement(self, time: float) -> float:
        """Evaluate propensity/rate for stochastic sampling.
        
        This method is called by tau-leaping engine to calculate propensities.
        Delegates to the currently selected behavior.
        
        Args:
            time: Current simulation time
            
        Returns:
            Propensity value (rate × tokens for stochastic mode)
        """
        mode = self._select_mode()
        self._handle_mode_change(mode)
        
        if mode == 'stochastic':
            # Delegate to stochastic behavior
            return self.stochastic_behavior._evaluate_rate_at_enablement(time)
        else:
            # Continuous mode: use evaluate_rate
            # Build places dict with numeric token values
            places = {}
            places_to_iterate = self.model.places.values() if isinstance(self.model.places, dict) else self.model.places
            for p in places_to_iterate:
                if hasattr(p, 'id') and hasattr(p, 'tokens'):
                    places[p.id] = p.tokens
                    if hasattr(p, 'name') and p.name:
                        places[p.name] = p.tokens
            return self.continuous_behavior.evaluate_rate(places, time)
    
    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire (delegates to current mode).
        
        Selects execution mode based on current volumes, then delegates
        enablement check to the appropriate behavior.
        
        Returns:
            Tuple of (can_fire: bool, reason: str)
        """
        # Select mode based on current volumes
        mode = self._select_mode()
        self._handle_mode_change(mode)
        
        # Delegate to appropriate behavior
        if mode == 'stochastic':
            return self.stochastic_behavior.can_fire()
        else:
            return self.continuous_behavior.can_fire()
    
    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Execute transition firing (delegates to current mode).
        
        For stochastic mode: Discrete burst firing
        For continuous mode: Returns error (use integrate_step instead)
        
        Args:
            input_arcs: List of incoming Arc objects
            output_arcs: List of outgoing Arc objects
        
        Returns:
            Tuple of (success: bool, details: dict)
        """
        mode = self._select_mode()
        self._handle_mode_change(mode)
        
        if mode == 'stochastic':
            # Delegate to stochastic behavior
            success, details = self.stochastic_behavior.fire(input_arcs, output_arcs)
            
            # Annotate result with mode info
            if success:
                details['adaptive_mode'] = 'stochastic'
                details['molecule_check'] = self._last_volume_check
            
            return success, details
        else:
            # Continuous mode - fire() not supported
            return False, {
                'reason': 'use-integrate-step-for-continuous',
                'adaptive_mode': 'continuous',
                'molecule_check': self._last_volume_check
            }
    
    def integrate_step(self, dt: float, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Integrate continuous flow over time step (delegates to current mode).
        
        For continuous mode: Smooth RK4 integration
        For stochastic mode: Multiple discrete firings within dt
        
        Args:
            dt: Time step size
            input_arcs: List of incoming Arc objects
            output_arcs: List of outgoing Arc objects
        
        Returns:
            Tuple of (success: bool, details: dict)
        """
        mode = self._select_mode()
        self._handle_mode_change(mode)
        
        if mode == 'continuous':
            # Delegate to continuous behavior
            success, details = self.continuous_behavior.integrate_step(dt, input_arcs, output_arcs)
            
            # Annotate result with mode info
            if success:
                details['adaptive_mode'] = 'continuous'
                details['molecule_check'] = self._last_volume_check
            
            return success, details
        else:
            # Stochastic mode - simulate multiple firings within dt
            # This is called by continuous engine in hybrid models
            # We approximate by checking if scheduled firing falls within [t, t+dt]
            
            behavior = self.stochastic_behavior
            
            # Check if scheduled to fire within this interval
            scheduled_time = behavior.get_scheduled_fire_time()
            current_time = self._get_current_time()
            
            if scheduled_time is not None and scheduled_time <= current_time + dt:
                # Should fire within this interval
                success, details = behavior.fire(input_arcs, output_arcs)
                
                if success:
                    details['adaptive_mode'] = 'stochastic'
                    details['molecule_check'] = self._last_volume_check
                    details['firing_within_dt'] = True
                
                return success, details
            else:
                # No firing within this interval
                return True, {
                    'adaptive_mode': 'stochastic',
                    'molecule_check': self._last_volume_check,
                    'firing_within_dt': False,
                    'scheduled_time': scheduled_time,
                    'current_time': current_time,
                    'dt': dt
                }
    
    def set_enablement_time(self, time: float):
        """Set enablement time (delegates to stochastic behavior if needed).
        
        This is called by the scheduler when transition becomes enabled.
        Only relevant for stochastic mode.
        
        Args:
            time: Current simulation time when enablement occurred
        """
        mode = self._select_mode()
        
        if mode == 'stochastic':
            self.stochastic_behavior.set_enablement_time(time)
    
    def clear_enablement(self):
        """Clear enablement (delegates to stochastic behavior)."""
        self.stochastic_behavior.clear_enablement()
    
    def get_scheduled_fire_time(self) -> Optional[float]:
        """Get scheduled firing time (relevant for stochastic mode only).
        
        Returns:
            float: Scheduled time, or None if not in stochastic mode or not scheduled
        """
        mode = self._select_mode()
        
        if mode == 'stochastic':
            return self.stochastic_behavior.get_scheduled_fire_time()
        else:
            return None  # Continuous mode doesn't use scheduling
    
    def get_type_name(self) -> str:
        """Return human-readable type name.
        
        Returns:
            str: "Adaptive Hybrid (ODE/Stochastic)"
        """
        return "Adaptive Hybrid (ODE/Stochastic)"
    
    def get_current_mode(self) -> Optional[str]:
        """Get current execution mode.
        
        Returns:
            'continuous', 'stochastic', or None if not determined yet
        """
        return self._current_mode
    
    def get_adaptive_info(self) -> Dict[str, Any]:
        """Get detailed adaptive behavior information.
        
        Returns:
            Dictionary with threshold (molecules), current mode, filter, and molecule count details
        """
        return {
            'molecule_threshold': self.volume_threshold,  # Note: stored as volume_threshold for backward compat
            'prefer_continuous': self.prefer_continuous,
            'place_filter': self.place_filter,
            'current_mode': self._current_mode,
            'last_molecule_check': self._last_volume_check,
            'continuous_info': self.continuous_behavior.get_continuous_info(),
            'stochastic_info': self.stochastic_behavior.get_stochastic_info()
        }
