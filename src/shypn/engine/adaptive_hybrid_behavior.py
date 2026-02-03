#!/usr/bin/env python3
"""Adaptive Hybrid Behavior - Runtime switching between ODE and Stochastic.

This behavior dynamically selects between continuous (ODE) and stochastic (SSA/τ-leaping)
execution based on compartment volume and molecular counts at runtime.

Key Features:
    - Automatic method selection based on volume thresholds
    - Seamless switching during simulation
    - Maintains state consistency across mode changes
    - Integrates with existing τ-leaping and continuous engines

Biological Motivation:
    Real biological systems operate in regimes where molecule counts vary:
    - Few molecules (< 100) → Stochastic noise dominates → Use SSA/τ-leaping
    - Many molecules (> 1000) → Deterministic approximation valid → Use ODE
    
    This adaptive approach matches how advanced hybrid simulation algorithms
    (like adaptive hybrid SSA/ODE) work in computational systems biology.

Usage:
    # Create adaptive transition (automatically switches based on volume)
    transition = Transition(..., transition_type='adaptive')
    behavior = AdaptiveHybridBehavior(transition, model)
    
    # During simulation:
    # - If volume < 1.0 fL → Uses stochastic (τ-leaping)
    # - If volume ≥ 1.0 fL → Uses continuous (ODE integration)
"""

import logging
from typing import Dict, Tuple, List, Any, Optional

from .transition_behavior import TransitionBehavior
from .continuous_behavior import ContinuousBehavior
from .stochastic_behavior import StochasticBehavior
from .spatial_utils import VolumeAdaptiveSelector


class AdaptiveHybridBehavior(TransitionBehavior):
    """Adaptive behavior that switches between continuous and stochastic.
    
    Implements runtime method selection based on spatial properties:
    - Reads compartment_volume from connected places
    - Switches to stochastic for small volumes (< threshold)
    - Switches to continuous for large volumes (≥ threshold)
    
    The behavior delegates to either ContinuousBehavior or StochasticBehavior
    based on current conditions, providing seamless integration with existing
    simulation engines (τ-leaping for stochastic, RK4 for continuous).
    
    Properties:
        volume_threshold (float): Threshold in fL (default 1.0)
        prefer_continuous (bool): Prefer continuous when volume not set (default True)
        adaptive_filter (str): Which places to check for volume (default 'inputs_only')
            - 'all': Check all input and output places
            - 'inputs_only': Check only input places (substrates drive propensity)
            - 'spatial_only': Check only spatial signal places
            - 'inputs_spatial': Check input places that are spatial signals
        
    State Management:
        - Continuous mode: No scheduling needed, fires based on rate
        - Stochastic mode: Uses enablement_time and scheduled_fire_time
        - Mode switches: Preserves token state, resets scheduling
    
    Biological Rationale for 'inputs_only' (default):
        - Input places = substrates that determine reaction propensity
        - Output places = products that don't affect firing decision
        - Substrate concentrations govern whether reaction uses stochastic or continuous dynamics
    
    Example:
        >>> behavior = AdaptiveHybridBehavior(transition, model)
        >>> # At t=0, input volume=0.5 fL → Uses stochastic
        >>> behavior.fire(...)  # Discrete burst firing
        >>> 
        >>> # Later, input volume=100 fL → Switches to continuous
        >>> behavior.integrate_step(...)  # Smooth ODE integration
    """
    
    def __init__(self, transition, model):
        """Initialize adaptive hybrid behavior.
        
        Creates both continuous and stochastic behavior delegates.
        The volume selector determines which to use at runtime.
        
        Args:
            transition: Transition object with adaptive properties
            model: Model instance for context access
        """
        super().__init__(transition, model)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Extract adaptive parameters
        props = getattr(transition, 'properties', {})
        self.volume_threshold = float(props.get('volume_threshold', 1.0))
        self.prefer_continuous = props.get('prefer_continuous', True)
        
        # Place filtering strategy for mode selection
        # Options: 'all', 'inputs_only', 'spatial_only', 'inputs_spatial'
        self.place_filter = props.get('adaptive_filter', 'inputs_only')
        
        # Create behavior delegates
        self.continuous_behavior = ContinuousBehavior(transition, model)
        self.stochastic_behavior = StochasticBehavior(transition, model)
        
        # Volume-based selector
        self.volume_selector = VolumeAdaptiveSelector(threshold_fL=self.volume_threshold)
        
        # Track current mode for mode change detection
        self._current_mode = None  # 'continuous' or 'stochastic'
        self._last_volume_check = None
        
        self.logger.info(
            f"Created AdaptiveHybridBehavior for '{transition.name}' "
            f"(threshold={self.volume_threshold} fL, filter={self.place_filter})"
        )
    
    def _get_connected_places(self) -> List:
        """Get places for mode selection based on filter strategy.
        
        Filter strategies:
            'all': All input and output places (original behavior)
            'inputs_only': Only input places (substrates drive propensity)
            'spatial_only': Only spatial signal places
            'inputs_spatial': Input places that are spatial signals
        
        Returns:
            List of Place objects filtered by strategy
        """
        all_input_places = []
        all_output_places = []
        
        # Collect input places
        for arc in self.get_input_arcs():
            place = self._get_place(arc.source_id)
            if place and place not in all_input_places:
                all_input_places.append(place)
        
        # Collect output places
        for arc in self.get_output_arcs():
            place = self._get_place(arc.target_id)
            if place and place not in all_output_places:
                all_output_places.append(place)
        
        # Apply filter strategy
        if self.place_filter == 'inputs_only':
            # Only check input places (substrates)
            return all_input_places
        
        elif self.place_filter == 'spatial_only':
            # Only check spatial signal places
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
    
    def _is_spatial_signal(self, place) -> bool:
        """Check if place is a spatial signal.
        
        Args:
            place: Place object
        
        Returns:
            bool: True if place has SPATIAL signal type
        """
        if not hasattr(place, 'is_spatial_signal'):
            return False
        
        try:
            return place.is_spatial_signal()
        except:
            # Fallback: check signal_type attribute
            from shypn.netobjs.signal_type import SignalType
            return getattr(place, 'signal_type', None) == SignalType.SPATIAL
    
    def _select_mode(self) -> str:
        """Select execution mode based on current volumes.
        
        Analyzes compartment volumes of connected places and decides
        whether to use stochastic or continuous execution.
        
        Returns:
            'stochastic' or 'continuous'
        """
        places = self._get_connected_places()
        
        if not places:
            # No places connected - use preferred mode
            return 'continuous' if self.prefer_continuous else 'stochastic'
        
        # Check volumes
        use_stochastic, details = self.volume_selector.analyze_transition(
            places, []  # All places (input and output)
        )
        
        self._last_volume_check = details
        
        return 'stochastic' if use_stochastic else 'continuous'
    
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
            volume_info = self._last_volume_check or {}
            self.logger.info(
                f"Transition '{self.transition.name}' mode change: "
                f"{old_mode} → {new_mode} "
                f"(min_volume={volume_info.get('min_volume', 'N/A')} fL, "
                f"threshold={self.volume_threshold} fL)"
            )
        
        # Clear stochastic scheduling state when switching away from stochastic
        if old_mode == 'stochastic' and new_mode == 'continuous':
            self.stochastic_behavior.clear_enablement()
    
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
                details['volume_info'] = self._last_volume_check
            
            return success, details
        else:
            # Continuous mode - fire() not supported
            return False, {
                'reason': 'use-integrate-step-for-continuous',
                'adaptive_mode': 'continuous',
                'volume_info': self._last_volume_check
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
                details['volume_info'] = self._last_volume_check
            
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
                    details['volume_info'] = self._last_volume_check
                    details['firing_within_dt'] = True
                
                return success, details
            else:
                # No firing within this interval
                return True, {
                    'adaptive_mode': 'stochastic',
                    'volume_info': self._last_volume_check,
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
            Dictionary with threshold, current mode, filter, and volume details
        """
        return {
            'volume_threshold': self.volume_threshold,
            'prefer_continuous': self.prefer_continuous,
            'place_filter': self.place_filter,
            'current_mode': self._current_mode,
            'last_volume_check': self._last_volume_check,
            'continuous_info': self.continuous_behavior.get_continuous_info(),
            'stochastic_info': self.stochastic_behavior.get_stochastic_info()
        }
