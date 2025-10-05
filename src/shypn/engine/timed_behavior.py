"""Timed Behavior - Time Petri Net (TPN) with timing windows.

Timed transitions use [earliest, latest] timing windows (Merlin & Farber 1976).
A transition becomes newly enabled at time t_enable, and can fire during
the interval [t_enable + earliest, t_enable + latest].

Mathematical Model:
    - Static interval: [α(t), β(t)] where α = earliest, β = latest
    - Enabled interval: [t + α(t), t + β(t)] for enablement time t
    - Firing constraint: t_enable + α(t) ≤ t_fire ≤ t_enable + β(t)
    - Token mode: Discrete (like immediate)

Extracted from: legacy/shypnpy/core/petri.py:1971-2050+
"""
from typing import Dict, Tuple, List, Any, Optional
from .transition_behavior import TransitionBehavior

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
        props = getattr(transition, 'properties', {})
        if 'earliest' in props or 'latest' in props:
            self.earliest = float(props.get('earliest', 0.0))
            self.latest = float(props.get('latest', float('inf')))
        else:
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

    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire (guard, timing window, and tokens).
        
        Timed transitions require:
            pass
        1. Guard condition must pass (if defined)
        2. Structural enablement (sufficient tokens)
        3. Current time within [t_enable + earliest, t_enable + latest]
        
        Returns:
            Tuple of (can_fire: bool, reason: str)
            - (True, "enabled-in-window") if can fire now
            - (False, "guard-fails") if guard condition not met
            - (False, "insufficient-tokens") if not structurally enabled
            - (False, "too-early") if current_time < t_enable + earliest
            - (False, "too-late") if current_time > t_enable + latest
            - (False, "not-enabled-yet") if enablement time not set
        """
        guard_passes, guard_reason = self._evaluate_guard()
        if not guard_passes:
            return (False, guard_reason)
        input_arcs = self.get_input_arcs()
        for arc in input_arcs:
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            if kind != 'normal':
                continue
            source_place = self._get_place(arc.source_id)
            if source_place is None:
                return (False, f'missing-source-place-{arc.source_id}')
            if source_place.tokens < arc.weight:
                return (False, f'insufficient-tokens-P{arc.source_id}')
        if self._enablement_time is None:
            return (False, 'not-enabled-yet')
        current_time = self._get_current_time()
        elapsed = current_time - self._enablement_time
        EPSILON = 1e-09
        DEBUG = False
        if DEBUG and hasattr(self.transition, 'name'):
            pass
        if elapsed + EPSILON < self.earliest:
            return (False, f'too-early (elapsed={elapsed:.3f}, earliest={self.earliest})')
        if elapsed > self.latest + EPSILON:
            return (False, f'too-late (elapsed={elapsed:.3f}, latest={self.latest})')
        return (True, f'enabled-in-window (elapsed={elapsed:.3f})')

    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Execute timed discrete firing.
        
        Firing process (identical to immediate, but respects timing):
            pass
        1. Validate enablement (tokens + timing window)
        2. Consume exactly arc_weight tokens from each input place
        3. Produce exactly arc_weight tokens to each output place
        4. Clear enablement time (will be reset if re-enabled)
        5. Record firing event with timing info
        
        Args:
            input_arcs: List of incoming Arc objects
            output_arcs: List of outgoing Arc objects
        
        Returns:
            Tuple of (success: bool, details: dict)
            
            Success case:
                (True, {
                    'consumed': {place_id: amount, ...},
                    'produced': {place_id: amount, ...},
                    'timed_mode': True,
                    'discrete_firing': True,
                    'elapsed_time': float,
                    'timing_window': [earliest, latest]
                })
            
            Failure case:
                (False, {
                    'reason': 'error-description',
                    'timed_mode': True
                })
        """
        try:
            can_fire, reason = self.can_fire()
            if not can_fire:
                return (False, {'reason': f'timing-violation: {reason}', 'timed_mode': True, 'timing_window': [self.earliest, self.latest]})
            consumed_map = {}
            produced_map = {}
            current_time = self._get_current_time()
            elapsed = current_time - self._enablement_time if self._enablement_time else 0.0
            for arc in input_arcs:
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                if kind != 'normal':
                    continue
                source_place = self._get_place(arc.source_id)
                if source_place is None:
                    return (False, {'reason': 'missing-source-place', 'place_id': arc.source_id, 'timed_mode': True})
                if source_place.tokens < arc.weight:
                    return (False, {'reason': 'insufficient-tokens', 'place_id': arc.source_id, 'required': arc.weight, 'available': source_place.tokens, 'timed_mode': True})
                source_place.set_tokens(source_place.tokens - arc.weight)
                consumed_map[arc.source_id] = float(arc.weight)
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
        elapsed = current_time - self._enablement_time if self._enablement_time else None
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