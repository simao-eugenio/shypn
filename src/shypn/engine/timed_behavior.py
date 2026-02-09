#!/usr/bin/env python3
"""Timed Behavior - Deterministic delay transitions (Time Petri Net formalism).

Timed transitions fire after a deterministic delay if enabled.
They support delay windows [tmin, tmax] where:
- Transition becomes enabled at t_enable + tmin
- Transition must fire by t_enable + tmax
- If disabled before firing, delay resets on next enablement

Mathematical Model:
    - Static interval: [delay, delay] (single deterministic delay)
    - Dynamic interval: [tmin, tmax] (timing window)
    - Enablement: tokens available AND t ∈ [t_enable + tmin, t_enable + tmax]
    - Firing: Discrete token transfer (like immediate transitions)

Spatial Signal Integration:
    - Reads boundary_type → validates transport
    - Respects neighbor_compartments topology

Extracted from: legacy/shypnpy/core/petri.py:1972-2099
"""

from typing import Dict, Tuple, List, Any, Optional
import logging
from .transition_behavior import TransitionBehavior
from .spatial_utils import BoundaryValidator

logger = logging.getLogger(__name__)

class TimedBehavior(TransitionBehavior):
    """Time Petri Net (TPN) transition firing behavior.
    
    Implements TPN semantics with [earliest, latest] timing windows:
        pass
    - Becomes enabled when all input places have sufficient tokens
    - Must wait at least 'earliest' time units before firing
    - Must fire before 'latest' time units if still enabled
    - Firing consumes/produces tokens discretely (like immediate)
    
    Timing Properties:
        earliest (float): Minimum delay after enablement (α)
        latest (float): Maximum delay after enablement (β)
        t_enable (float): Time when transition became enabled
        
    Constraints:
        0 ≤ earliest ≤ latest
        earliest = 0: can fire immediately after enablement
        latest = ∞: no upper bound (must be forced eventually)
    
    Usage:
        behavior = TimedBehavior(transition, model)
        
        # Check timing window
        can_fire, reason = behavior.can_fire()
        if can_fire:
            success, details = behavior.fire(
                behavior.get_input_arcs(),
                behavior.get_output_arcs()
            )
    """

    def __init__(self, transition, model):
        """Initialize timed behavior.
        
        Args:
            transition: Transition object with timing properties
            model: Model instance for context access
        """
        super().__init__(transition, model)
        
        # Read timing parameters (TPN firing window: [earliest, latest])
        # Priority order:
        #   1. Direct attributes: transition.earliest_time / transition.latest_time (JSON schema)
        #   2. Properties dict: transition.properties['earliest_time'] or ['earliest'] (legacy)
        #   3. Fallback to rate as delay (backward compatibility)
        
        # Try direct attributes first (JSON loads these at top level)
        if hasattr(transition, 'earliest_time') or hasattr(transition, 'latest_time'):
            self.earliest = float(getattr(transition, 'earliest_time', 0.0))
            self.latest = float(getattr(transition, 'latest_time', float('inf')))
        else:
            # Try properties dictionary (legacy or programmatically created)
            props = getattr(transition, 'properties', {})
            if 'earliest_time' in props or 'latest_time' in props:
                self.earliest = float(props.get('earliest_time', 0.0))
                self.latest = float(props.get('latest_time', float('inf')))
            elif 'earliest' in props or 'latest' in props:
                self.earliest = float(props.get('earliest', 0.0))
                self.latest = float(props.get('latest', float('inf')))
            else:
                # Fallback: use rate as delay (backward compatibility)
                rate = getattr(transition, 'rate', None)
                if rate is not None:
                    try:
                        delay = float(rate) if isinstance(rate, (int, float)) else 1.0
                        if delay > 0:
                            self.earliest = delay
                            self.latest = delay
                        else:
                            self.earliest = 1.0
                            self.latest = 1.0
                    except (ValueError, TypeError) as e:
                        self.earliest = 1.0
                        self.latest = 1.0
                else:
                    self.earliest = 1.0
                    self.latest = 1.0
        if self.earliest < 0:
            raise ValueError(f'Earliest time cannot be negative: {self.earliest}')
        if self.latest < self.earliest:
            raise ValueError(f'Latest ({self.latest}) must be >= earliest ({self.earliest})')
        self._enablement_time = None
        self._was_too_early = False  # Track if we've been checked while too early
        self._was_in_window = False  # Track if we've been in the firing window
        
        # Initialize spatial property integration utilities
        self.boundary_validator = BoundaryValidator(model)

    def _is_signal_place(self, place) -> bool:
        """Check if a place is a signal place (read-only, non-consuming).
        
        Signal places (Ψ) in modular Bio-PN architecture provide information
        flow without mass transfer. They are never consumed during simulation.
        
        Args:
            place: Place object to check
        
        Returns:
            bool: True if place is a signal place
        """
        if place is None:
            return False
        
        # Check is_signal_place attribute (primary indicator)
        if hasattr(place, 'is_signal_place') and place.is_signal_place:
            return True
        
        # Check signal_type property (alternative indicator)
        if hasattr(place, 'signal_type') and place.signal_type is not None:
            return True
        
        return False

    def set_enablement_time(self, time: float):
        """Set the time when transition became enabled.
        
        This should be called by the scheduler when structural enablement
        is detected (sufficient tokens in all input places).
        
        Args:
            time: Current simulation time when enablement occurred
        """
        self._enablement_time = time

    def get_enablement_time(self) -> Optional[float]:
        """Get the time when transition was last enabled.
        
        Returns:
            float: Enablement time, or None if never enabled
        """
        return self._enablement_time

    def clear_enablement(self):
        """Clear enablement tracking (when transition becomes disabled).
        
        This should be called when input places no longer have sufficient tokens.
        """
        self._enablement_time = None
        self._was_too_early = False
        self._was_in_window = False

    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire (guard, timing window, and tokens).
        
        Timed transitions require:
        1. Guard condition must pass (if defined)
        2. Structural enablement (sufficient tokens, unless source transition)
        3. Current time within [t_enable + earliest, t_enable + latest]
        
        Source transitions are always structurally enabled.
        
        Returns:
            Tuple of (can_fire: bool, reason: str)
            - (True, "enabled-in-window") if can fire now
            - (True, "enabled-source") if source transition in timing window
            - (False, "guard-fails") if guard condition not met
            - (False, "insufficient-tokens") if not structurally enabled
            - (False, "too-early") if current_time < t_enable + earliest
            - (False, "too-late") if current_time > t_enable + latest
            - (False, "not-enabled-yet") if enablement time not set
        """
        # Check if this is a source or sink transition
        is_source = getattr(self.transition, 'is_source', False)
        is_sink = getattr(self.transition, 'is_sink', False)
        
        guard_passes, guard_reason = self._evaluate_guard()
        if not guard_passes:
            return (False, guard_reason)
        
        # Check structural enablement (skip if source transition)
        if not is_source:
            input_arcs = self.get_input_arcs()
            for arc in input_arcs:
                # Check ALL input arcs (normal, test, inhibitor) for token availability
                # All arc types require tokens >= weight for enablement
                source_place = self._get_place(arc.source_id)
                if source_place is None:
                    return (False, f'missing-source-place-{arc.source_id}')
                
                # TEST ARC: Non-consuming arcs only check presence (weight)
                # Consuming arcs (including SignalFlowArcs) must have sufficient tokens
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                arc_type = getattr(arc, 'arc_type', 'normal')
                
                logger.debug(f"  [ENABLEMENT] Arc {arc.id}: type={type(arc).__name__}, kind={kind}, arc_type={arc_type}")
                
                if kind != 'normal' or arc_type in ('inhibitor', 'test'):
                    required = arc.weight  # Just check presence for test arcs
                    logger.debug(f"    → Test/Inhibitor arc: only checking presence")
                else:
                    required = arc.weight  # Normal and SignalFlowArcs need full weight
                    logger.debug(f"    → Normal arc: will consume tokens")
                
                if source_place.tokens < required:
                    return (False, f'insufficient-tokens-P{arc.source_id}')
        
        # NEW: Validate spatial boundary constraints
        boundary_valid, boundary_reason = self.boundary_validator.validate_transition_arcs(
            self.transition,
            self.get_input_arcs(),
            self.get_output_arcs(),
            self._get_place
        )
        
        if not boundary_valid:
            return (False, boundary_reason)
        
        if self._enablement_time is None:
            return (False, 'not-enabled-yet')
        
        current_time = self._get_current_time()
        elapsed = current_time - self._enablement_time
        EPSILON = 1e-09
        
        # Check if too early
        if elapsed + EPSILON < self.earliest:
            self._was_too_early = True  # Remember we were too early
            return (False, f'too-early (elapsed={elapsed:.3f}, earliest={self.earliest})')
        
        # Check if too late - but detect window crossing
        if elapsed > self.latest + EPSILON:
            # If we were too early before and now we're too late,
            # but we've never been in the window, then we crossed it!
            if self._was_too_early and not self._was_in_window:
                # Window was crossed - allow firing this once
                self._was_in_window = True  # Mark as handled
                if is_source:
                    return (True, f'enabled-source-window-crossed (elapsed={elapsed:.3f})')
                return (True, f'window-crossed-during-step (elapsed={elapsed:.3f})')
            # Genuinely too late
            return (False, f'too-late (elapsed={elapsed:.3f}, latest={self.latest})')
        
        # In the window - can fire
        self._was_in_window = True  # Remember we were in window
        
        if is_source:
            return (True, f'enabled-source (elapsed={elapsed:.3f})')
        return (True, f'enabled-in-window (elapsed={elapsed:.3f})')

    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Fire the transition if timing window is satisfied.
        
        Process:
        1. Validate timing window (earliest <= elapsed <= latest)
        2. Check structural enablement (guard, tokens)
        3. Consume tokens from input places (skip test arcs!)
        4. Produce tokens to output places
        5. Clear enablement
        6. Record transition event
        
        Returns:
            (success: bool, details: dict)
                success=True with details={'consumed', 'produced', 'timed_mode', ...}
                success=False with details={'reason', 'timed_mode', ...}
        """
        try:
            can_fire, reason = self.can_fire()
            if not can_fire:
                return (False, {'reason': f'timing-violation: {reason}', 'timed_mode': True, 'timing_window': [self.earliest, self.latest]})
            
            # Check if this is a source or sink transition
            is_source = getattr(self.transition, 'is_source', False)
            is_sink = getattr(self.transition, 'is_sink', False)
            
            consumed_map = {}
            produced_map = {}
            current_time = self._get_current_time()
            elapsed = current_time - self._enablement_time if self._enablement_time else 0.0
            
            # Consume tokens from input places (skip if source transition)
            if not is_source:
                logger.debug(f"[TIMED FIRE] Transition {self.transition.id}: Consuming input tokens...")
                
                for arc in input_arcs:
                    # Skip inhibitor arcs and test arcs (they don't consume)
                    # Use defensive pattern: check kind, properties['kind'], and arc_type
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    arc_type = getattr(arc, 'arc_type', 'normal')
                    
                    logger.debug(f"  Arc {arc.id}: type={type(arc).__name__}, kind={kind}, arc_type={arc_type}")
                    
                    # DEFENSIVE v2.1.1: Only TEST arcs skip consumption (pure catalysts)
                    # Inhibitor arcs DO consume tokens when threshold permits transition to fire
                    if arc_type == 'test':
                        logger.debug(f"    → SKIP consumption (test arc - catalyst)")
                        continue
                    
                    source_place = arc.source
                    if source_place is None:
                        return (False, {'reason': 'missing-source-place', 'place_id': arc.source_id, 'timed_mode': True})
                    
                    logger.debug(f"    → CONSUMING tokens from {source_place.id}")
                    
                    if source_place.tokens < arc.weight:
                        return (False, {'reason': 'insufficient-tokens', 'place_id': arc.source_id, 'required': arc.weight, 'available': source_place.tokens, 'timed_mode': True})
                    
                    source_place.set_tokens(source_place.tokens - arc.weight)
                    consumed_map[arc.source_id] = float(arc.weight)
            
            # Produce tokens to output places (skip if sink transition)
            if not is_sink:
                for arc in output_arcs:
                    target_place = self._get_place(arc.target_id)
                    if target_place is None:
                        continue
                    
                    target_place.set_tokens(target_place.tokens + arc.weight)
                    produced_map[arc.target_id] = float(arc.weight)
            
            self.clear_enablement()
            self._record_event(consumed=consumed_map, produced=produced_map, mode='logical', transition_type='timed', elapsed_time=elapsed, timing_window=[self.earliest, self.latest])
            
            return (True, {'consumed': consumed_map, 'produced': produced_map, 'timed_mode': True, 'discrete_firing': True, 'transition_type': 'timed', 'elapsed_time': elapsed, 'timing_window': [self.earliest, self.latest], 'time': current_time})
        except Exception as e:
            return (False, {'reason': f'timed-error: {str(e)}', 'timed_mode': True, 'error_type': type(e).__name__})

    def get_type_name(self) -> str:
        """Return human-readable type name.
        
        Returns:
            str: "Timed (TPN)"
        """
        return 'Timed (TPN)'

    def get_timing_info(self) -> Dict[str, Any]:
        """Get detailed timing information.
        
        Returns:
            Dictionary with timing window and current status
        """
        current_time = self._get_current_time()
        elapsed = current_time - self._enablement_time if self._enablement_time is not None else None
        info = {'earliest': self.earliest, 'latest': self.latest, 'enablement_time': self._enablement_time, 'current_time': current_time, 'elapsed': elapsed}
        if elapsed is not None:
            info['can_fire_earliest'] = elapsed >= self.earliest
            info['must_fire_before'] = self._enablement_time + self.latest
            info['time_remaining'] = max(0, self.latest - elapsed)
            info['in_window'] = self.earliest <= elapsed <= self.latest
        else:
            info['in_window'] = False
        return info

    def is_urgent(self, tolerance: float=0.001) -> bool:
        """Check if transition must fire soon (near latest deadline).
        
        Args:
            tolerance: Time tolerance for urgency (default 0.001)
        
        Returns:
            bool: True if within tolerance of latest deadline
        """
        if self._enablement_time is None:
            return False
        current_time = self._get_current_time()
        elapsed = current_time - self._enablement_time
        return abs(elapsed - self.latest) < tolerance and elapsed < self.latest