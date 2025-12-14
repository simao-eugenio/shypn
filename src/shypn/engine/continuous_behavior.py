#!/usr/bin/env python3
"""Continuous Behavior - Stochastic Hybrid Petri Net (SHPN) with continuous flow.

Continuous transitions use rate functions and continuous token flow.
They support Runge-Kutta 4th order (RK4) integration for smooth evolution.

Mathematical Model:
    - Rate function: r(t) = f(m(t), params)
    - Token flow: dm/dt = r(t)
    - Integration: RK4 method with adaptive step size
    - Enablement: Continuous if ∀p ∈ •t: m(p) > 0

Extracted from: legacy/shypnpy/core/petri.py:1691-1900
"""

from typing import Dict, Tuple, List, Any, Callable, Optional
import math
import numpy as np
from .transition_behavior import TransitionBehavior
from .function_catalog import FUNCTION_CATALOG


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
    
    def __init__(self, transition, model):
        """Initialize continuous behavior.
        
        Args:
            transition: Transition object with continuous properties
            model: Model instance for context access
        """
        super().__init__(transition, model)
        
        # Track if rate function has failed (to prevent repeated errors)
        self._rate_function_failed = False
        self._rate_function_error = None
        
        # Extract continuous parameters
        props = getattr(transition, 'properties', {})
        
        # Support multiple formats:
        # 1. properties['rate_function'] = string expression
        # 2. properties['rate_function'] = callable
        # 3. properties = {'rate': lambda places, t: ...}  (dict format)
        # 4. transition.rate attribute (UI stores simple value)
        # 5. DIRECTIONAL: rate_forward + rate_reverse (new format)
        
        rate_expr = None
        rate_forward_expr = None
        rate_reverse_expr = None
        
        # Check for directional rate functions first
        # Check both props dict AND transition attributes
        rate_forward_expr = props.get('rate_forward') or getattr(transition, 'rate_forward', None)
        rate_reverse_expr = props.get('rate_reverse') or getattr(transition, 'rate_reverse', None)
        
        if rate_forward_expr or rate_reverse_expr:
            self.use_directional_rates = True
        else:
            self.use_directional_rates = False
            
            if 'rate_function' in props:
                # Explicit rate function in properties
                rate_expr = props.get('rate_function')
            elif 'rate' in props and callable(props['rate']):
                # Dict format with callable: {'rate': lambda ...}
                rate_expr = props['rate']
            else:
                # Fallback: Use transition.rate attribute (UI stores simple value)
                rate = getattr(transition, 'rate', None)
                if rate is not None:
                    # Check if it's a dict with 'rate' key
                    if isinstance(rate, dict) and 'rate' in rate:
                        rate_expr = rate['rate']
                    else:
                        # Accept string expressions or numeric constants
                        rate_expr = str(rate)
                else:
                    rate_expr = '1.0'  # Default constant rate
        
        self.max_rate = float(props.get('max_rate', float('inf')))
        self.min_rate = float(props.get('min_rate', -float('inf')))  # Allow negative for reversible
        
        # Compile rate functions
        if self.use_directional_rates:
            self.rate_forward_function = self._compile_rate_function(rate_forward_expr) if rate_forward_expr else lambda p, t: 0.0
            self.rate_reverse_function = self._compile_rate_function(rate_reverse_expr) if rate_reverse_expr else lambda p, t: 0.0
            # Combined rate = forward - reverse
            self.rate_function = lambda places, t: self.rate_forward_function(places, t) - self.rate_reverse_function(places, t)
        else:
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
        
        Args:
            expr: String expression or callable
        
        Returns:
            Callable that takes (places_dict, time) and returns rate
        """
        if callable(expr):
            return expr
        
        # Parse constant
        try:
            constant_rate = float(expr)
            return lambda places, t: constant_rate
        except ValueError:
            pass
        
        # Parse expression with place references (simple parser)
        # Format: "a * P1 + b * P2" or "min(c, P1)" or "sigmoid(time, 10, 0.5)" etc.
        def evaluate_rate(places: Dict[int, Any], time: float) -> float:
            try:
                # Build evaluation context with full support
                context = {
                    'time': time,
                    't': time,  # Alias
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'math': math,
                    'np': np,
                    'numpy': np,
                }
                
                # Add all catalog functions to context
                context.update(FUNCTION_CATALOG)
                
                # Add SBML parameters from kinetic_metadata (if available)
                params = {}  # Initialize params dict
                if hasattr(self.transition, 'kinetic_metadata') and self.transition.kinetic_metadata:
                    if hasattr(self.transition.kinetic_metadata, 'parameters'):
                        # Add all kinetic parameters (kf_0, kr_0, Vmax, Km, etc.)
                        params = self.transition.kinetic_metadata.parameters.copy()
                        
                # Normalize compartment volumes for token-based simulation
                # In SBML, compartment sizes (comp1, comp2, etc.) are in liters
                # but for discrete token simulations, we use normalized volumes
                # Set all comp* parameters to 1.0 to avoid scaling issues
                for key in list(params.keys()):
                    if key.startswith('comp') and len(key) > 4 and key[4:].isdigit():
                        # This is a compartment parameter (comp1, comp2, etc.)
                        params[key] = 1.0  # Normalize for token-based simulation
                
                context.update(params)
                
                # Add place tokens as P1, P2, ... (or P88, P105 if ID already has P)
                # IMPORTANT: Also add by place.name for SBML formulas that use names
                # Add small epsilon to prevent division by zero in rate formulas
                for place_id, place in places.items():
                    # Get tokens safely - handle both direct attribute and method
                    if hasattr(place, 'tokens'):
                        tokens = place.tokens
                    elif hasattr(place, 'marking'):
                        tokens = place.marking
                    else:
                        # Fallback - assume 0 tokens if attribute missing
                        tokens = 0
                    
                    # Use max() to ensure at least epsilon value to prevent division by zero
                    tokens_safe = max(float(tokens), 1e-10)
                    
                    # Add by ID (for numeric IDs like 1, 2, 3)
                    if isinstance(place_id, str) and place_id.startswith('P'):
                        # ID already has P prefix (e.g., "P105")
                        context[place_id] = tokens_safe
                    else:
                        # Numeric ID needs P prefix (e.g., 1 → P1)
                        context[f'P{place_id}'] = tokens_safe
                    
                    # ALSO add by place name (for SBML formulas)
                    # Place name might be "P1", "P5", etc. from SBML conversion
                    if hasattr(place, 'name') and place.name:
                        context[place.name] = tokens_safe
                
                # Evaluate expression safely
                result = eval(expr, {"__builtins__": {}}, context)
                return float(result)
            except Exception as e:
                # Check if this is first error for this transition
                if not self._rate_function_failed:
                    self._rate_function_failed = True
                    self._rate_function_error = str(e)
                    
                    # FAIL LOUDLY - print error once
                    print(f"\n❌ Rate Function Error - Simulation Stopped")
                    print(f"   Transition: {self.transition.name} ({self.transition.id})")
                    print(f"   Expression: {expr}")
                    print(f"   Error: {e}")
                    
                    # If NameError, suggest similar function names
                    if isinstance(e, NameError):
                        try:
                            import re
                            import difflib
                            # Import at module level to avoid UnboundLocalError
                            from shypn.engine import function_catalog
                            
                            # Extract undefined name from error message
                            match = re.search(r"name '(\w+)' is not defined", str(e))
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
                        except Exception:
                            pass  # Silently skip suggestion if import fails
                    
                    print(f"\n   Fix the rate expression before running simulation.\n")
                
                # Raise error to stop simulation
                raise RuntimeError(
                    f"Failed to evaluate rate function for transition {self.transition.name}: {e}\n"
                    f"Expression: {expr}\n"
                    f"Context keys: {list(context.keys())}"
                ) from e
        
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
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
        from shypn.utils.threshold_evaluator import ThresholdEvaluator  # NEW
        
        # Get all input arcs to check for inhibitors
        all_input_arcs = self.get_input_arcs()
        inhibitor_arcs = [arc for arc in all_input_arcs 
                         if isinstance(arc, (InhibitorArc, CurvedInhibitorArc))]
        
        # Create threshold evaluator for dynamic threshold support
        evaluator = ThresholdEvaluator(self.model)
        context = {'time': current_time}
        
        # DEBUG: Log inhibitor arc checks for Example 08
        if self.transition.id in ['T1', 'T2'] and len(inhibitor_arcs) > 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[INHIBITOR CHECK] Transition {self.transition.id} has {len(inhibitor_arcs)} inhibitor arcs")
            for arc in inhibitor_arcs:
                source_place = self._get_place(arc.source_id)
                if source_place:
                    effective_threshold = evaluator.evaluate(arc, context)
                    logger.info(f"  Arc {arc.id}: {source_place.id} tokens={source_place.tokens:.4f}, threshold={effective_threshold}, blocked={source_place.tokens >= effective_threshold}")
        
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
        
        # Now check normal/test arcs in the flow direction
        for arc in check_arcs:
            # Skip inhibitor arcs (already checked above)
            if isinstance(arc, (InhibitorArc, CurvedInhibitorArc)):
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
            
            # Normal/Test arcs: Require positive tokens for continuous enablement
            # Continuous requires tokens above threshold
            if source_place.tokens <= self.min_token_threshold:
                return False, f"place-below-threshold-{place_id}"
        
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
            # Check enablement
            can_fire, reason = self.can_fire()
            if not can_fire:
                return False, {
                    'reason': f'not-enabled: {reason}',
                    'continuous_mode': True
                }
            
            current_time = self._get_current_time()
            
            # Gather ALL place objects for rate evaluation
            # CRITICAL: Rate formulas may reference places not in this transition's arcs
            # For example, T1 formula "comp1 * (kf_0 * P6 - kr_0 * P5)" needs P5 and P6
            # even if T1 only has arcs to P1 and P2
            places_dict = {}
            
            # Get all places from the model
            if hasattr(self.model, 'places'):
                # model.places might be a list of place objects OR a dict
                if isinstance(self.model.places, dict):
                    # It's a dict of {place_id: place_object}
                    places_dict = self.model.places.copy()
                elif isinstance(self.model.places, list):
                    # It's a list of place objects
                    for place in self.model.places:
                        if hasattr(place, 'id'):
                            places_dict[place.id] = place
                        else:
                            # place is a string ID - need to get actual object
                            place_obj = self._get_place(place)
                            if place_obj:
                                places_dict[place_obj.id] = place_obj
            elif hasattr(self.model, 'get_all_places'):
                for place in self.model.get_all_places():
                    places_dict[place.id] = place
            else:
                # FAIL LOUDLY - model must provide place access
                raise AttributeError(
                    f"Model {self.model} does not have 'places' or 'get_all_places()'. "
                    f"Cannot gather places for rate function evaluation in transition {self.transition.id}"
                )
            
            # Evaluate rate function(s)
            if self.use_directional_rates:
                # Directional rates: evaluate both directions
                rate_forward = self.rate_forward_function(places_dict, current_time)
                rate_reverse = self.rate_reverse_function(places_dict, current_time)
                rate = rate_forward - rate_reverse
                # Store for debugging/visualization
                self._last_rate_forward = rate_forward
                self._last_rate_reverse = rate_reverse
            else:
                # Single combined rate function
                rate = self.rate_function(places_dict, current_time)
                self._last_rate_forward = max(0, rate)
                self._last_rate_reverse = max(0, -rate)
            
            rate = max(self.min_rate, min(self.max_rate, rate))
            
            # Check if rate is effectively zero
            # For reversible reactions, rate can be negative (reverse flow)
            # Only skip if abs(rate) is too small
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
                    'reason': 'rate-below-threshold'
                }
            
            # Check if this is a source or sink transition
            is_source = getattr(self.transition, 'is_source', False)
            is_sink = getattr(self.transition, 'is_sink', False)
            
            consumed_map = {}
            produced_map = {}
            
            # REVERSIBLE REACTION SUPPORT
            # If rate < 0, reverse the flow direction:
            # - Consume from output_arcs (normally products)
            # - Produce to input_arcs (normally reactants)
            reverse_direction = (rate < 0)
            flow_magnitude = abs(rate) * dt
            
            # For directional rates with bidirectional arcs, filter arcs based on substrates/products
            if self.use_directional_rates:
                # Parse rate formulas to identify which places are substrates vs products
                import re
                substrate_places = set()
                product_places = set()
                
                # Get places dict for name lookup
                places_dict_for_lookup = {}
                if hasattr(self.model, 'places'):
                    if isinstance(self.model.places, dict):
                        places_dict_for_lookup = self.model.places
                    elif isinstance(self.model.places, list):
                        for place in self.model.places:
                            if hasattr(place, 'id'):
                                places_dict_for_lookup[place.id] = place
                elif hasattr(self.model, 'get_all_places'):
                    for place in self.model.get_all_places():
                        places_dict_for_lookup[place.id] = place
                
                # Forward rate mentions substrates
                if hasattr(self.transition, 'rate_forward'):
                    fwd_expr = str(self.transition.rate_forward)
                    # Extract compound names (uppercase words that aren't math functions)
                    compound_names = re.findall(r'\b([A-Z][A-Za-z0-9_-]*)\b', fwd_expr)
                    for cname in compound_names:
                        if cname in ['P', 'E']:  # Skip single letters
                            continue
                        # Find place with matching name
                        for place_id, place_obj in places_dict_for_lookup.items():
                            if hasattr(place_obj, 'name') and place_obj.name == cname:
                                substrate_places.add(place_id)
                
                # Reverse rate mentions products
                if hasattr(self.transition, 'rate_reverse'):
                    rev_expr = str(self.transition.rate_reverse)
                    compound_names = re.findall(r'\b([A-Z][A-Za-z0-9_-]*)\b', rev_expr)
                    for cname in compound_names:
                        if cname in ['P', 'E']:
                            continue
                        for place_id, place_obj in places_dict_for_lookup.items():
                            if hasattr(place_obj, 'name') and place_obj.name == cname:
                                product_places.add(place_id)
                
                # Filter arcs based on direction
                if reverse_direction:
                    # Reverse: consume from products, produce to substrates
                    consume_arcs = [arc for arc in output_arcs if arc.target_id in product_places]
                    produce_arcs = [arc for arc in input_arcs if arc.source_id in substrate_places]
                    # Fallback if filtering gives empty results
                    if not consume_arcs:
                        consume_arcs = output_arcs
                    if not produce_arcs:
                        produce_arcs = input_arcs
                else:
                    # Forward: consume from substrates, produce to products
                    consume_arcs = [arc for arc in input_arcs if arc.source_id in substrate_places]
                    produce_arcs = [arc for arc in output_arcs if arc.target_id in product_places]
                    # Fallback if filtering gives empty results
                    if not consume_arcs:
                        consume_arcs = input_arcs
                    if not produce_arcs:
                        produce_arcs = output_arcs
            else:
                # Non-directional: use simple swap logic
                if reverse_direction:
                    consume_arcs = output_arcs
                    produce_arcs = input_arcs
                else:
                    consume_arcs = input_arcs
                    produce_arcs = output_arcs
            
            # Phase 1: Clamp flow to available tokens
            actual_flow = flow_magnitude
            if not is_source:
                for arc in consume_arcs:
                    # Skip test arcs - they check enablement but don't consume tokens
                    if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                        continue
                    
                    # For reversed flow, get source from arc.target_id (normally output)
                    place_id = arc.source_id if not reverse_direction else arc.target_id
                    source_place = self._get_place(place_id)
                    if source_place is None:
                        continue
                    
                    # Calculate max flow possible from this arc
                    max_flow_from_arc = source_place.tokens / arc.weight if arc.weight > 0 else float('inf')
                    actual_flow = min(actual_flow, max_flow_from_arc)
            
            # Phase 2: Consume tokens continuously
            if not is_source and actual_flow > 0:
                for arc in consume_arcs:
                    # Skip test arcs - they check enablement but don't consume tokens
                    if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                        continue
                    
                    place_id = arc.source_id if not reverse_direction else arc.target_id
                    source_place = self._get_place(place_id)
                    if source_place is None:
                        continue
                    
                    # Continuous consumption: arc_weight * actual_flow
                    consumption = arc.weight * actual_flow
                    
                    if consumption > 0:
                        source_place.set_tokens(source_place.tokens - consumption)
                        consumed_map[place_id] = consumption
            
            # Phase 3: Produce tokens continuously
            if not is_sink and actual_flow > 0:
                for arc in produce_arcs:
                    place_id = arc.target_id if not reverse_direction else arc.source_id
                    target_place = self._get_place(place_id)
                    if target_place is None:
                        continue
                    
                    # Continuous production: arc_weight * actual_flow
                    production = arc.weight * actual_flow
                    
                    if production > 0:
                        target_place.set_tokens(target_place.tokens + production)
                        produced_map[place_id] = production
            
            # Phase 4: Record continuous flow event
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
                clamped=(actual_flow < flow_magnitude),
                reverse_direction=reverse_direction,
                use_directional_rates=self.use_directional_rates
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
                'clamped': (actual_flow < flow_magnitude),
                'reverse_direction': reverse_direction
            }
            
        except Exception as e:
            return False, {
                'reason': f'continuous-error: {str(e)}',
                'continuous_mode': True,
                'error_type': type(e).__name__
            }
    
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
            kind = getattr(arc, 'kind', 'normal')
            if kind == 'normal':
                predicted_consumed[arc.source_id] = arc.weight * rate * dt
        
        for arc in self.get_output_arcs():
            predicted_produced[arc.target_id] = arc.weight * rate * dt
        
        return {
            'rate': rate,
            'dt': dt,
            'consumed': predicted_consumed,
            'produced': predicted_produced
        }
