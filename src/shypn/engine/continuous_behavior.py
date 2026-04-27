#!/usr/bin/env python3
"""Continuous Behavior - Stochastic Hybrid Petri Net (SHPN) with continuous flow.

Continuous transitions use rate functions and continuous token flow.
They support Runge-Kutta 4th order (RK4) integration for smooth evolution.

Mathematical Model:
    - Rate function: r(t) = f(m(t), params)
    - Token flow: dm/dt = r(t)
    - Integration: RK4 method with adaptive step size
    - Enablement: Continuous if ∀p ∈ •t: m(p) > 0

Spatial Signal Integration:
    - Reads diffusion_coefficient from places → scales rate
    - Reads boundary_type → validates transport
    - Reads gradient_vector → directional modulation
    - Reads compartment_volume → stochastic/continuous selection

Extracted from: legacy/shypnpy/core/petri.py:1691-1900
"""

from typing import Dict, Tuple, List, Any, Callable, Optional
from shypn.utils.safe_eval import safe_eval_numeric
import logging
import math
import numpy as np
from .transition_behavior import TransitionBehavior
from .function_catalog import FUNCTION_CATALOG
from .spatial_utils import BoundaryValidator, GradientModulator, VolumeAdaptiveSelector

logger = logging.getLogger(__name__)


class ContinuousBehavior(TransitionBehavior):
    """Stochastic Hybrid Petri Net (SHPN) continuous transition behavior.
    
    Implements continuous semantics with:
    - Rate functions for continuous token flow
    - RK4 (Runge-Kutta 4th order) numerical integration
    - Smooth continuous evolution (no discrete jumps)
    - Enablement based on positive token counts
    
    Continuous Properties:
        rate_function (str/callable): Function defining flow rate
        max_rate (float): Maximum flow rate (optional)
        min_rate (float): Minimum flow rate (optional, default 0)
        
    Rate Function Types:
        - Constant: "5.0" → r(t) = 5.0
        - Linear: "2.0 * P1" → r(t) = 2.0 * tokens(P1)
        - Saturated: "min(10, P1)" → r(t) = min(10, tokens(P1))
        - Custom: callable(places, time) → float
    
    Usage:
        behavior = ContinuousBehavior(transition, model)
        
        # Integrate over time step
        success, details = behavior.integrate_step(
            dt=0.01,
            input_arcs=behavior.get_input_arcs(),
            output_arcs=behavior.get_output_arcs()
        )
    """
    
    def __init__(self, transition: Any, model: Any):
        """Initialize continuous behavior.
        
        Args:
            transition: Transition object with continuous properties
            model: Model instance for context access
        """
        super().__init__(transition, model)
        
        # Track if rate function has failed (to prevent repeated errors)
        self._rate_function_failed = False
        self._rate_function_error: Optional[str] = None
        
        # Static evaluation context cache — built once on first evaluate_rate call.
        # Contains FUNCTION_CATALOG + thermodynamic settings + kinetic params (all static
        # during simulation). Only place token values are added dynamically per call.
        self._static_context_cache: Optional[Dict] = None
        
        # Pre-identified thermodynamic override places (built alongside static context).
        # Avoids str.lower() on all places every step.
        self._thermo_temp_place_ids: Optional[List] = None  # temperature places
        self._thermo_ph_place_ids: Optional[List] = None    # pH places
        
        # Initialize spatial property integration utilities
        self.boundary_validator = BoundaryValidator(model)
        self.gradient_modulator = GradientModulator()
        self.volume_selector = VolumeAdaptiveSelector(threshold_molecules=100.0)
        
        # Extract continuous parameters
        props = getattr(transition, 'properties', {})
        
        # Rate function is stored in properties dict only
        rate_expr = None
        rate_forward_expr = None
        rate_reverse_expr = None
        
        # Check for directional rate functions
        rate_forward_expr = props.get('rate_forward')
        rate_reverse_expr = props.get('rate_reverse')
        
        if rate_forward_expr or rate_reverse_expr:
            self.use_directional_rates = True
        else:
            self.use_directional_rates = False
            rate_expr = props.get('rate_function')
        
        self.max_rate = float(props.get('max_rate', float('inf')))
        self.min_rate = float(props.get('min_rate', -float('inf')))  # Allow negative for reversible
        
        # Compile rate functions
        if self.use_directional_rates:
            self.rate_forward_function: Callable[..., float] = self._compile_rate_function(rate_forward_expr) if rate_forward_expr else lambda p, t: 0.0  # type: ignore[assignment]
            self.rate_reverse_function: Callable[..., float] = self._compile_rate_function(rate_reverse_expr) if rate_reverse_expr else lambda p, t: 0.0  # type: ignore[assignment]
            # Combined rate = forward - reverse
            self.rate_function: Callable[..., float] = lambda places, t: self.rate_forward_function(places, t) - self.rate_reverse_function(places, t)
        else:
            if rate_expr is None:
                raise ValueError(
                    f"Continuous transition '{self.transition.label}' (id={self.transition.id}) "
                    f"missing required 'rate_function' in properties dict"
                )
            self.rate_function = self._compile_rate_function(rate_expr)
        
        # Integration parameters
        self.integration_method = 'rk4'  # Runge-Kutta 4th order
        self.min_step = 0.0001  # Minimum step size
        self.max_step = 0.1     # Maximum step size
        
        # Minimum token threshold for enablement (prevents premature stopping)
        # Default 0.0 means transitions stop only at exactly 0 tokens
        # Setting to small value (e.g., 1e-6) prevents numerical precision issues
        self.min_token_threshold = float(props.get('min_token_threshold', 0.0))
    
    def evaluate_rate(self, places: Dict[int, Any], time: float) -> float:
        """Evaluate rate function at given state and time.
        
        This public method wraps the compiled rate_function to provide
        a consistent API for external callers (e.g., data_collector).
        
        Args:
            places: Dictionary mapping place IDs to place objects
            time: Current simulation time
        
        Returns:
            float: Evaluated rate (clamped to [min_rate, max_rate])
        """
        try:
            rate = self.rate_function(places, time)
            return max(self.min_rate, min(self.max_rate, rate))
        except Exception as e:
            # Log error and return 0.0 as safe fallback
            if not self._rate_function_failed:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Rate function evaluation failed for {self.transition.id}: {e}")
                self._rate_function_failed = True
                self._rate_function_error = str(e)
            return 0.0
    
    def _compile_rate_function(self, expr: str) -> Callable:
        """Compile rate function expression to callable.
        
        Supports both bracket notation [PlaceName] (chemistry convention for concentration)
        and plain PlaceName references.
        
        Args:
            expr: String expression or callable
        
        Returns:
            Callable that takes (places_dict, time) and returns rate
        """
        if expr is None:
            raise ValueError(
                f"Cannot compile None rate expression for transition '{self.transition.label}' (id={self.transition.id})"
            )
        
        if callable(expr):
            return expr
        
        # Parse constant
        try:
            constant_rate = float(expr)
            return lambda places, t: constant_rate
        except ValueError:
            pass
        
        # Preprocess expression: convert [PlaceName] to PlaceName
        # This supports chemistry notation where [X] means "concentration of X"
        import re
        expr_processed = re.sub(r'\[([^\]]+)\]', r'\1', expr)
        
        # Parse expression with place references (simple parser)
        # Format: "a * P1 + b * P2" or "min(c, P1)" or "sigmoid(time, 10, 0.5)" etc.
        def evaluate_rate(places: Dict[int, Any], time: float) -> float:
            try:
                # --- Static context (built once, reused every call) ---
                if self._static_context_cache is None:
                    static: Dict[Any, Any] = {
                        'min': min, 'max': max, 'abs': abs,
                        'math': math, 'np': np, 'numpy': np,
                    }
                    static.update(FUNCTION_CATALOG)
                    
                    # Thermodynamic settings (static during simulation)
                    if hasattr(self.model, 'thermodynamic_settings'):
                        ts = self.model.thermodynamic_settings
                        T = ts.get('temperature', 298.15)
                        static['T'] = T
                        static['Temperature'] = T
                        static['pH'] = ts.get('ph', 7.0)
                        static['ionic_strength'] = ts.get('ionic_strength', 0.1)
                        static['I'] = static['ionic_strength']
                        static['R'] = 0.008314
                        static['R_SI'] = 8.314
                        static['F'] = 96485
                    
                    # Kinetic parameters from SBML metadata (static)
                    if (hasattr(self.transition, 'kinetic_metadata')
                            and self.transition.kinetic_metadata
                            and hasattr(self.transition.kinetic_metadata, 'parameters')):
                        params = self.transition.kinetic_metadata.parameters.copy()
                        for key in list(params.keys()):
                            if key.startswith('comp') and len(key) > 4 and key[4:].isdigit():
                                params[key] = 1.0
                        static.update(params)
                    
                    self._static_context_cache = static
                    
                    # Pre-identify thermodynamic override places (once)
                    temp_ids: List = []
                    ph_ids: List = []
                    all_places = getattr(self.model, 'places', {})
                    places_iter = all_places.values() if isinstance(all_places, dict) else all_places
                    for p in places_iter:
                        pname = getattr(p, 'name', '') or ''
                        pname_lo = pname.lower()
                        if 'temperature' in pname_lo:
                            temp_ids.append(p.id)
                        elif 'ph' in pname_lo and 'gradient' not in pname_lo:
                            ph_ids.append(p.id)
                    self._thermo_temp_place_ids = temp_ids
                    self._thermo_ph_place_ids = ph_ids
                
                # --- Dynamic context (time + place tokens) ---
                context = self._static_context_cache.copy()
                context['time'] = time
                context['t'] = time
                
                for place_id, place in places.items():
                    tokens = getattr(place, 'tokens', None)
                    if tokens is None:
                        tokens = getattr(place, 'marking', 0)
                    tokens_safe = max(float(tokens), 1e-10)
                    context[place_id] = tokens_safe
                    pname = getattr(place, 'name', None)
                    if pname:
                        context[pname] = tokens_safe
                
                # Dynamic thermodynamic overrides (only thermodynamic places)
                for tid in self._thermo_temp_place_ids:  # type: ignore[union-attr]
                    if tid not in places:
                        continue
                    tokens = context.get(tid, 0)
                    pname = getattr(places[tid], 'name', '') or ''
                    pname_lo = pname.lower()
                    if 'celsius' in pname_lo or 'celcius' in pname_lo:
                        context['T'] = tokens + 273.15
                        context['Temperature'] = context['T']
                    else:
                        context['T'] = tokens
                        context['Temperature'] = tokens
                for pid in self._thermo_ph_place_ids:  # type: ignore[union-attr]
                    if pid in places:
                        context['pH'] = context.get(pid, 0)

                # Backward-compatible derived thermodynamic alias used by
                # existing model equations (e.g. Q10 terms).
                if 'T' in context:
                    context['T_celsius'] = context['T'] - 273.15
                
                # Evaluate expression safely (replaces eval() for security)
                result = safe_eval_numeric(expr_processed, context, allow_math=True)
                return result
            except Exception as exc:
                # Check if this is first error for this transition
                if not self._rate_function_failed:
                    self._rate_function_failed = True
                    self._rate_function_error = str(exc)
                    
                    # FAIL LOUDLY - print error once
                    print("\n❌ Rate Function Error - Simulation Stopped")
                    print(f"   Transition: {self.transition.name} ({self.transition.id})")
                    print(f"   Expression: {expr}")
                    print(f"   Error: {exc}")
                    
                    # If NameError, suggest similar function names
                    if isinstance(exc, NameError):
                        try:
                            import re
                            import difflib
                            # Import at module level to avoid UnboundLocalError
                            from shypn.engine import function_catalog
                            
                            # Extract undefined name from error message
                            match = re.search(r"name '(\w+)' is not defined", str(exc))
                            if match:
                                undefined_name = match.group(1)
                                # Find close matches (case-insensitive)
                                close_matches = difflib.get_close_matches(
                                    undefined_name.lower(), 
                                    [name.lower() for name in function_catalog.FUNCTION_CATALOG.keys()],
                                    n=3,
                                    cutoff=0.6
                                )
                                if close_matches:
                                    # Get actual function names (preserving case)
                                    actual_names = [name for name in function_catalog.FUNCTION_CATALOG.keys() 
                                                  if name.lower() in close_matches]
                                    print(f"   💡 Did you mean: {', '.join(actual_names)}?")
                        except (ImportError, AttributeError, KeyError) as e:
                            logger.debug(f"Skipping function suggestion: {e}")
                    
                    print("\n   Fix the rate expression before running simulation.\n")
                
                # Raise error to stop simulation
                raise RuntimeError(
                    f"Failed to evaluate rate function for transition {self.transition.name}: {exc}\n"
                    f"Expression: {expr}\n"
                    f"Context keys: {list(context.keys())}"
                ) from exc
        
        return evaluate_rate
    
    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire in continuous mode.
        
        For continuous transitions:
        - Check if rate != 0 (reversible transitions need rate evaluation)
        - For reversible transitions: only check arcs in current flow direction
        - All required input places must have positive tokens (>0)
        - Guard condition must be satisfied
        - Test arcs don't consume tokens but check for presence
        - Inhibitor arcs disable transition when source >= weight
        
        Source transitions are always enabled (they generate tokens externally).
        
        Returns:
            Tuple of (can_fire: bool, reason: str)
            - (True, "enabled-continuous") if all inputs positive
            - (True, "enabled-source") if source transition
            - (False, "guard-fails") if guard condition not met
            - (False, "input-place-empty") if any input has zero tokens
        """
        # Check if this is a source transition (always enabled)
        is_source = getattr(self.transition, 'is_source', False)
        if is_source:
            return True, "enabled-source"
        
        # Check guard first
        guard_passes, guard_reason = self._evaluate_guard()
        if not guard_passes:
            return False, guard_reason
        
        # For reversible transitions, we need to evaluate rate to know direction
        # This is necessary because bidirectional arcs exist, but only one direction fires
        try:
            # Gather places for rate evaluation
            places_dict = {}
            if hasattr(self.model, 'places'):
                if isinstance(self.model.places, dict):
                    places_dict = self.model.places.copy()
                elif isinstance(self.model.places, list):
                    for place in self.model.places:
                        if hasattr(place, 'id'):
                            places_dict[place.id] = place
            elif hasattr(self.model, 'get_all_places'):
                for place in self.model.get_all_places():
                    places_dict[place.id] = place
            
            # Evaluate rate to determine direction
            current_time = self._get_current_time()
            
            # For directional rates, evaluate forward and reverse separately
            if self.use_directional_rates:
                rate_forward = self.rate_forward_function(places_dict, current_time)
                rate_reverse = self.rate_reverse_function(places_dict, current_time)
                rate = rate_forward - rate_reverse
            else:
                rate = self.rate_function(places_dict, current_time)
            
            # Determine which arcs to check based on rate direction
            input_arcs = self.get_input_arcs()
            output_arcs = self.get_output_arcs()
            
            # For reversible transitions with bidirectional arcs:
            # Only check substrate places for current direction
            reverse_direction = (rate < 0)
            
            # Identify substrate and product places from rate formula
            # For directional rates, we can determine this from the formulas
            substrate_places = set()
            product_places = set()
            
            if self.use_directional_rates:
                # Parse rate formulas to identify substrates vs products
                # Forward formula mentions substrates, reverse formula mentions products
                import re
                
                if hasattr(self, 'rate_forward_function'):
                    # Extract both place IDs (P\d+) and compound names from forward rate
                    fwd_expr = str(getattr(self.transition, 'rate_forward', ''))
                    substrate_places.update(re.findall(r'\b(P\d+)\b', fwd_expr))
                    
                    # Also try to map compound names to place IDs
                    # Extract compound names (words that aren't keywords)
                    compound_names = re.findall(r'\b([A-Z][A-Za-z0-9_-]*)\b', fwd_expr)
                    for cname in compound_names:
                        # Find place with matching name
                        for place_id, place_obj in places_dict.items():
                            if hasattr(place_obj, 'name') and place_obj.name == cname:
                                substrate_places.add(place_id)
                
                if hasattr(self, 'rate_reverse_function'):
                    # Extract both place IDs and compound names from reverse rate
                    rev_expr = str(getattr(self.transition, 'rate_reverse', ''))
                    product_places.update(re.findall(r'\b(P\d+)\b', rev_expr))
                    
                    # Also try to map compound names to place IDs
                    compound_names = re.findall(r'\b([A-Z][A-Za-z0-9_-]*)\b', rev_expr)
                    for cname in compound_names:
                        # Find place with matching name
                        for place_id, place_obj in places_dict.items():
                            if hasattr(place_obj, 'name') and place_obj.name == cname:
                                product_places.add(place_id)
            
            # Filter arcs based on direction
            if reverse_direction and product_places:
                # Reverse: only check arcs consuming from product places
                check_arcs = [arc for arc in output_arcs 
                             if arc.target_id in product_places]
                if not check_arcs:
                    check_arcs = output_arcs  # Fallback
            elif not reverse_direction and substrate_places:
                # Forward: only check arcs consuming from substrate places
                check_arcs = [arc for arc in input_arcs 
                             if arc.source_id in substrate_places]
                if not check_arcs:
                    check_arcs = input_arcs  # Fallback
            elif reverse_direction:
                check_arcs = output_arcs
            else:
                check_arcs = input_arcs
                
        except Exception:
            # Fallback: check all input arcs (old behavior)
            input_arcs = self.get_input_arcs()
            check_arcs = input_arcs
            reverse_direction = False
        
        # No arcs to check means always enabled
        if not check_arcs:
            return True, "enabled-continuous-no-inputs"
        
        # CRITICAL: Always check inhibitor arcs regardless of direction filtering
        # Inhibitor arcs provide regulatory control and must always be evaluated
        from shypn.utils.threshold_evaluator import ThresholdEvaluator  # NEW
        
        # Get all input arcs to check for inhibitors
        all_input_arcs = self.get_input_arcs()
        inhibitor_arcs = []
        for arc in all_input_arcs:
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            arc_type = getattr(arc, 'arc_type', 'normal')
            # FIXED v2.1.2: Detect ALL inhibitor arc variants (includes curved_inhibitor_arc)
            if kind == 'inhibitor' or arc_type == 'inhibitor' or 'inhibitor' in arc_type:
                inhibitor_arcs.append(arc)
        
        # Create threshold evaluator for dynamic threshold support
        evaluator = ThresholdEvaluator(self.model)
        context = {'time': current_time}
        
        # Check inhibitor arcs first (they can block transition regardless of direction)
        for arc in inhibitor_arcs:
            source_place = self._get_place(arc.source_id)
            if source_place is None:
                return False, f"missing-place-{arc.source_id}"
            
            # Evaluate dynamic threshold (supersedes weight if threshold is set)
            effective_threshold = evaluator.evaluate(arc, context)
            
            # Inhibitor arcs: DISABLED when tokens >= threshold (negative feedback)
            if source_place.tokens >= effective_threshold:
                return False, f"inhibited-by-{arc.source_id}"
        
        # NEW: Validate spatial boundary constraints
        # Check if any input/output arcs involve spatial signals with boundary constraints
        boundary_valid, boundary_reason = self.boundary_validator.validate_transition_arcs(
            self.transition,
            all_input_arcs,
            self.get_output_arcs(),
            self._get_place
        )
        
        if not boundary_valid:
            return False, boundary_reason
        
        # Now check normal/test arcs in the flow direction
        for arc in check_arcs:
            # Skip inhibitor arcs (already checked above) using defensive pattern
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            arc_type = getattr(arc, 'arc_type', 'normal')
            # FIXED v2.1.2: Detect ALL inhibitor arc variants (includes curved_inhibitor_arc)
            if kind == 'inhibitor' or arc_type == 'inhibitor' or 'inhibitor' in arc_type:
                continue
                
            # Get the place we're consuming from
            if reverse_direction:
                # Consuming from output arcs (target is the place)
                place_id = arc.target_id
            else:
                # Normal: consuming from input arcs (source is the place)
                place_id = arc.source_id
                
            source_place = self._get_place(place_id)
            if source_place is None:
                return False, f"missing-place-{place_id}"
            
            # ALL arcs (normal, test, signal) must check enablement: tokens >= weight
            # Test arcs enable transitions but don't consume (checked during firing)
            # Continuous requires tokens above threshold for ALL arc types
            # Signal flow arcs additionally require θ_eff tokens as basin
            # floor (formalism: M(ps) ≥ θ_eff + Ws). θ_eff = 0 by default.
            # When activation_energy > 0, θ_eff is temperature-dependent.
            theta = self._get_theta_eff(arc)
            effective_floor = theta + self.min_token_threshold
            # F6 fix: use strict less-than (<) instead of less-or-equal (<=)
            # so that tokens at exactly the floor are considered enabled.
            # This matches ODE rate-expression semantics where rate→0 as
            # tokens→0 naturally, without a hard cutoff at the boundary.
            if source_place.tokens < effective_floor:
                return False, f"place-below-threshold-{place_id}"
        
        # PreemptionCheck: single-layer verification of signal-producing predecessors
        preempt_ok, preempt_reason = self._check_preemption()
        if not preempt_ok:
            return False, preempt_reason

        return True, "enabled-continuous"
    
    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Execute continuous firing (not typically used directly).
        
        For continuous transitions, use integrate_step() instead of fire().
        This method exists to satisfy the abstract interface.
        
        Returns:
            (False, {'reason': 'use-integrate-step'})
        """
        return False, {
            'reason': 'use-integrate-step-for-continuous',
            'continuous_mode': True
        }
    
    def integrate_step(self, dt: float, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Integrate continuous flow over time step using RK4.

        Runge-Kutta 4th order integration:
            k1 = f(t, y)
            k2 = f(t + dt/2, y + k1*dt/2)
            k3 = f(t + dt/2, y + k2*dt/2)
            k4 = f(t + dt, y + k3*dt)
            y_new = y + (k1 + 2*k2 + 2*k3 + k4) * dt / 6

        Args:
            dt: Time step size
            input_arcs: List of incoming Arc objects
            output_arcs: List of outgoing Arc objects

        Returns:
            Tuple of (success: bool, details: dict)

            Success case:
                (True, {
                    'consumed': {place_id: amount, ...},
                    'produced': {place_id: amount, ...},
                    'continuous_mode': True,
                    'rate': float,
                    'dt': float,
                    'method': 'rk4'
                })
        """
        try:
            can_fire, reason = self.can_fire()
            if not can_fire:
                return False, {'reason': f'not-enabled: {reason}', 'continuous_mode': True}

            current_time = self._get_current_time()
            places_dict = self._gather_places_dict()
            rate = self._evaluate_rate(places_dict, current_time)
            rate = max(self.min_rate, min(self.max_rate, rate))

            effective_min_rate = self.min_token_threshold * 1e-3
            if abs(rate) <= effective_min_rate:
                return True, {
                    'consumed': {},
                    'produced': {},
                    'continuous_mode': True,
                    'rate': rate,
                    'rate_forward': getattr(self, '_last_rate_forward', 0.0),
                    'rate_reverse': getattr(self, '_last_rate_reverse', 0.0),
                    'dt': dt,
                    'method': 'rk4',
                    'reason': 'rate-below-threshold',
                }

            is_source = getattr(self.transition, 'is_source', False)
            is_sink = getattr(self.transition, 'is_sink', False)

            consume_arcs, produce_arcs, reverse_direction, flow_magnitude = \
                self._resolve_arc_directions(rate, input_arcs, output_arcs, places_dict)

            consumed_map, produced_map, actual_flow = self._execute_token_flow(
                consume_arcs, produce_arcs, flow_magnitude * dt, is_source, is_sink, reverse_direction
            )

            self._record_event(
                consumed=consumed_map,
                produced=produced_map,
                mode='continuous',
                transition_type='continuous',
                rate=rate,
                rate_forward=getattr(self, '_last_rate_forward', 0.0),
                rate_reverse=getattr(self, '_last_rate_reverse', 0.0),
                actual_rate=(actual_flow / dt if dt > 0 else 0.0) * (1 if not reverse_direction else -1),
                dt=dt,
                method='rk4',
                clamped=(actual_flow < flow_magnitude * dt),
                reverse_direction=reverse_direction,
                use_directional_rates=self.use_directional_rates,
            )

            return True, {
                'consumed': consumed_map,
                'produced': produced_map,
                'continuous_mode': True,
                'rate': rate,
                'rate_forward': getattr(self, '_last_rate_forward', 0.0),
                'rate_reverse': getattr(self, '_last_rate_reverse', 0.0),
                'actual_rate': (actual_flow / dt if dt > 0 else 0.0) * (1 if not reverse_direction else -1),
                'dt': dt,
                'method': 'rk4',
                'use_directional_rates': self.use_directional_rates,
                'transition_type': 'continuous',
                'time': current_time,
                'clamped': (actual_flow < flow_magnitude * dt),
                'reverse_direction': reverse_direction,
            }

        except (ValueError, AttributeError, KeyError, ZeroDivisionError) as e:
            return False, {
                'reason': f'continuous-error: {str(e)}',
                'continuous_mode': True,
                'error_type': type(e).__name__,
            }

    # -----------------------------------------------------------------------
    # Private helpers decomposed from integrate_step
    # -----------------------------------------------------------------------

    def _gather_places_dict(self) -> Dict[str, Any]:
        """Collect all model places into a {place_id: place} dict.

        Rate formulas may reference places outside this transition's immediate
        arc neighbourhood, so we gather the full model inventory.

        Returns:
            Mapping of place_id → place object.

        Raises:
            AttributeError: When the model exposes no place-access interface.
        """
        if hasattr(self.model, 'places'):
            if isinstance(self.model.places, dict):
                return self.model.places.copy()
            places: Dict[str, Any] = {}
            for p in self.model.places:
                if hasattr(p, 'id'):
                    places[p.id] = p
                else:
                    obj = self._get_place(p)
                    if obj:
                        places[obj.id] = obj
            return places
        if hasattr(self.model, 'get_all_places'):
            return {p.id: p for p in self.model.get_all_places()}
        raise AttributeError(
            f"Model {self.model} does not have 'places' or 'get_all_places()'. "
            f"Cannot gather places for rate evaluation in transition {self.transition.id}"
        )

    def _evaluate_rate(self, places_dict: Dict[str, Any], current_time: float) -> float:
        """Evaluate rate function(s) and store directional debugging attributes.

        For directional-rate transitions evaluates both the forward and reverse
        expressions; for single-rate transitions derives them from sign.

        Args:
            places_dict: Current {place_id: place} mapping.
            current_time: Simulation clock used by time-dependent formulas.

        Returns:
            Net signed rate (positive → forward, negative → reverse).
        """
        if self.use_directional_rates:
            rate_forward = self.rate_forward_function(places_dict, current_time)
            rate_reverse = self.rate_reverse_function(places_dict, current_time)
            self._last_rate_forward = rate_forward
            self._last_rate_reverse = rate_reverse
            return rate_forward - rate_reverse
        rate = self.rate_function(places_dict, current_time)
        self._last_rate_forward = max(0.0, rate)
        self._last_rate_reverse = max(0.0, -rate)
        return rate

    def _resolve_arc_directions(
        self,
        rate: float,
        input_arcs: List,
        output_arcs: List,
        places_dict: Dict[str, Any],
    ) -> tuple:
        """Determine consume/produce arc subsets and flow direction.

        For directional-rate transitions the method inspects the rate formula
        tokens to identify substrate and product places before choosing the arc
        subsets; it falls back to the full arc lists when parsing yields no
        matches.

        Args:
            rate: Net signed rate.
            input_arcs: All incoming arcs.
            output_arcs: All outgoing arcs.
            places_dict: {place_id: place} mapping for name look-ups.

        Returns:
            ``(consume_arcs, produce_arcs, reverse_direction, flow_magnitude)``
        """
        reverse_direction = rate < 0
        flow_magnitude = abs(rate)

        if not self.use_directional_rates:
            if reverse_direction:
                return output_arcs, input_arcs, reverse_direction, flow_magnitude
            return input_arcs, output_arcs, reverse_direction, flow_magnitude

        import re
        name_to_id = {
            obj.name: pid
            for pid, obj in places_dict.items()
            if hasattr(obj, 'name')
        }

        def _place_ids_from_expr(expr: str) -> set:
            ids: set = set()
            for cname in re.findall(r'\b([A-Z][A-Za-z0-9_-]*)\b', str(expr)):
                if cname not in ('P', 'E') and cname in name_to_id:
                    ids.add(name_to_id[cname])
            return ids

        substrate_places = (
            _place_ids_from_expr(self.transition.rate_forward)
            if hasattr(self.transition, 'rate_forward') else set()
        )
        product_places = (
            _place_ids_from_expr(self.transition.rate_reverse)
            if hasattr(self.transition, 'rate_reverse') else set()
        )

        # Per 13-tuple Bio-PN formalism, signal_flow arcs are dual-role:
        # they consume/produce tokens AND are visible to the signal hierarchy.
        # The directional-rate filter (regex over rate_forward/rate_reverse
        # text) can omit signal_flow arcs when the signal place name does not
        # appear in the directional split, which would silently break mass
        # balance for the signal place. Always retain signal_flow arcs in
        # both consume and produce sets regardless of name-based matching.
        def _is_signal_flow(a) -> bool:
            return getattr(a, 'arc_type', 'normal') == 'signal_flow'

        if reverse_direction:
            matched_out = [a for a in output_arcs if a.target_id in product_places]
            matched_in = [a for a in input_arcs if a.source_id in substrate_places]
            consume_arcs = matched_out or output_arcs
            produce_arcs = matched_in or input_arcs
            for a in output_arcs:
                if _is_signal_flow(a) and a not in consume_arcs:
                    consume_arcs.append(a)
            for a in input_arcs:
                if _is_signal_flow(a) and a not in produce_arcs:
                    produce_arcs.append(a)
        else:
            matched_in = [a for a in input_arcs if a.source_id in substrate_places]
            matched_out = [a for a in output_arcs if a.target_id in product_places]
            consume_arcs = matched_in or input_arcs
            produce_arcs = matched_out or output_arcs
            for a in input_arcs:
                if _is_signal_flow(a) and a not in consume_arcs:
                    consume_arcs.append(a)
            for a in output_arcs:
                if _is_signal_flow(a) and a not in produce_arcs:
                    produce_arcs.append(a)

        return consume_arcs, produce_arcs, reverse_direction, flow_magnitude

    def _execute_token_flow(
        self,
        consume_arcs: List,
        produce_arcs: List,
        flow_magnitude: float,
        is_source: bool,
        is_sink: bool,
        reverse_direction: bool,
    ) -> tuple:
        """Apply token consumption and production for one continuous time step.

        Phase 1 clamps ``actual_flow`` so no place goes negative.
        Phase 2 consumes tokens (weight × actual_flow per arc).
        Phase 3 produces tokens (weight × actual_flow per arc).

        Args:
            consume_arcs: Arcs that drain tokens.
            produce_arcs: Arcs that add tokens.
            flow_magnitude: Unclamped |rate| × dt.
            is_source: Transition is a source (skip consumption).
            is_sink: Transition is a sink (skip production).
            reverse_direction: True when net rate is negative.

        Returns:
            ``(consumed_map, produced_map, actual_flow)`` where maps are
            ``{place_id: amount}`` and ``actual_flow ≤ flow_magnitude``.
        """
        consumed_map: Dict[str, float] = {}
        produced_map: Dict[str, float] = {}

        # Phase 1: clamp to available tokens
        actual_flow = flow_magnitude
        if not is_source:
            for arc in consume_arcs:
                if not arc.consumes_tokens():
                    continue
                place_id = arc.source_id if not reverse_direction else arc.target_id
                src = self._get_place(place_id)
                if src is None:
                    continue
                # Signal flow arcs: only tokens above θ_eff are spendable.
                # This preserves the basin floor during continuous integration.
                # When activation_energy > 0, θ_eff is temperature-dependent.
                theta = self._get_theta_eff(arc)
                spendable = max(0.0, src.tokens - theta)
                max_flow = spendable / arc.weight if arc.weight > 0 else float('inf')
                actual_flow = min(actual_flow, max_flow)

        # Phase 2: consume
        if not is_source and actual_flow > 0:
            for arc in consume_arcs:
                if getattr(arc, 'arc_type', 'normal') == 'test':
                    continue
                place_id = arc.source_id if not reverse_direction else arc.target_id
                src = self._get_place(place_id)
                if src is None:
                    continue
                amount = arc.weight * actual_flow
                if amount > 0:
                    src.set_tokens(src.tokens - amount)
                    consumed_map[place_id] = amount

        # Phase 3: produce
        if not is_sink and actual_flow > 0:
            for arc in produce_arcs:
                place_id = arc.target_id if not reverse_direction else arc.source_id
                tgt = self._get_place(place_id)
                if tgt is None:
                    continue
                amount = arc.weight * actual_flow
                if amount > 0:
                    tgt.set_tokens(tgt.tokens + amount)
                    produced_map[place_id] = amount

        return consumed_map, produced_map, actual_flow
    
    def get_type_name(self) -> str:
        """Return human-readable type name.
        
        Returns:
            str: "Continuous (SHPN)"
        """
        return "Continuous (SHPN)"
    
    # ============================================================================
    # Additional Helper Methods
    # ============================================================================
    
    def get_continuous_info(self) -> Dict[str, Any]:
        """Get detailed continuous behavior information.
        
        Returns:
            Dictionary with rate function and integration parameters
        """
        return {
            'max_rate': self.max_rate,
            'min_rate': self.min_rate,
            'integration_method': self.integration_method,
            'min_step': self.min_step,
            'max_step': self.max_step
        }
    
    def evaluate_current_rate(self) -> float:
        """Evaluate rate function at current state.
        
        Returns:
            float: Current instantaneous rate
        """
        current_time = self._get_current_time()
        
        # Gather place objects
        places_dict = {}
        for arc in self.get_input_arcs() + self.get_output_arcs():
            place = self._get_place(getattr(arc, 'source_id', None) or getattr(arc, 'target_id', None))
            if place:
                places_dict[place.id] = place
        
        rate = self.rate_function(places_dict, current_time)
        return max(self.min_rate, min(self.max_rate, rate))
    
    def predict_flow(self, dt: float) -> Dict[str, Any]:
        """Predict token flow over time step without applying it.
        
        Args:
            dt: Time step to predict
        
        Returns:
            Dictionary with predicted consumption and production
        """
        rate = self.evaluate_current_rate()
        
        predicted_consumed = {}
        predicted_produced = {}
        
        for arc in self.get_input_arcs():
            # Per formalism: only TEST arcs are non-consuming.
            # signal_flow and inhibitor arcs DO consume tokens.
            arc_type = getattr(arc, 'arc_type', 'normal')
            if arc_type != 'test':
                predicted_consumed[arc.source_id] = arc.weight * rate * dt
        
        for arc in self.get_output_arcs():
            predicted_produced[arc.target_id] = arc.weight * rate * dt
        
        return {
            'rate': rate,
            'dt': dt,
            'consumed': predicted_consumed,
            'produced': predicted_produced
        }
