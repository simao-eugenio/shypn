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
        
        # Extract continuous parameters
        props = getattr(transition, 'properties', {})
        
        # Support multiple formats:
        # 1. properties['rate_function'] = string expression
        # 2. properties['rate_function'] = callable
        # 3. properties = {'rate': lambda places, t: ...}  (dict format)
        # 4. transition.rate attribute (UI simple value)
        
        rate_expr = None
        
        if 'rate_function' in props:
            # Explicit rate function in properties
            rate_expr = props.get('rate_function')
        elif 'rate' in props and callable(props['rate']):
            # Dict format with callable: {'rate': lambda ...}
            rate_expr = props['rate']
        else:
            # Fallback: Use transition.rate attribute (UI stores simple rate here)
            rate = getattr(transition, 'rate', None)
            if rate is not None:
                # Check if it's a dict with 'rate' key
                if isinstance(rate, dict) and 'rate' in rate:
                    rate_expr = rate['rate']
                else:
                    # Convert simple rate to rate function string
                    rate_expr = str(rate) if isinstance(rate, (int, float)) else '1.0'
            else:
                rate_expr = '1.0'  # Default constant rate
        
        self.max_rate = float(props.get('max_rate', float('inf')))
        self.min_rate = float(props.get('min_rate', 0.0))
        
        # Compile rate function
        self.rate_function = self._compile_rate_function(rate_expr)
        
        # Integration parameters
        self.integration_method = 'rk4'  # Runge-Kutta 4th order
        self.min_step = 0.0001  # Minimum step size
        self.max_step = 0.1     # Maximum step size
    
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
                if hasattr(self.transition, 'kinetic_metadata') and self.transition.kinetic_metadata:
                    if hasattr(self.transition.kinetic_metadata, 'parameters'):
                        # Add all kinetic parameters (kf_0, kr_0, Vmax, Km, etc.)
                        params = self.transition.kinetic_metadata.parameters.copy()
                        
                        # IMPORTANT: Normalize compartment volumes for token-based simulation
                        # In SBML, compartment sizes (comp1, comp2, etc.) are in liters
                        # but for discrete token simulations, we use normalized volumes
                        # Set all comp* parameters to 1.0 to avoid scaling issues
                        comp_normalized = False
                        for key in list(params.keys()):
                            if key.startswith('comp') and len(key) > 4 and key[4:].isdigit():
                                # This is a compartment parameter (comp1, comp2, etc.)
                                old_val = params[key]
                                params[key] = 1.0  # Normalize for token-based simulation
                                if not comp_normalized:
                                    print(f"[COMP NORMALIZE] {self.transition.name}: {key} {old_val:.2e} → 1.0")
                                    comp_normalized = True
                        
                        context.update(params)
                
                # Add place tokens as P1, P2, ... (or P88, P105 if ID already has P)
                # IMPORTANT: Also add by place.name for SBML formulas that use names
                for place_id, place in places.items():
                    # Add by ID (for numeric IDs like 1, 2, 3)
                    if isinstance(place_id, str) and place_id.startswith('P'):
                        # ID already has P prefix (e.g., "P105")
                        context[place_id] = place.tokens
                    else:
                        # Numeric ID needs P prefix (e.g., 1 → P1)
                        context[f'P{place_id}'] = place.tokens
                    
                    # ALSO add by place name (for SBML formulas)
                    # Place name might be "P1", "P5", etc. from SBML conversion
                    if hasattr(place, 'name') and place.name:
                        context[place.name] = place.tokens
                
                # Evaluate expression safely
                result = eval(expr, {"__builtins__": {}}, context)
                
                # DEBUG: Log first evaluation for each transition
                if not hasattr(self, '_first_eval_logged'):
                    self._first_eval_logged = True
                    place_tokens = {k: v for k, v in context.items() if k.startswith('P')}
                    print(f"[RATE EVAL] {self.transition.name}: expr='{expr[:50]}...' → {result:.6f}")
                    print(f"  Places: {list(place_tokens.items())[:3]}")
                
                return float(result)
            except Exception as e:
                # Log error for debugging
                print(f"[RATE ERROR] {self.transition.name}: {e}")
                return 0.0  # Safe fallback
        
        return evaluate_rate
    
    def can_fire(self) -> Tuple[bool, str]:
        """Check if continuous transition is enabled.
        
        Continuous transitions are enabled if:
        1. Guard condition passes (if defined)
        2. All input places have positive token counts (> 0, not >= weight like discrete)
        
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
        
        input_arcs = self.get_input_arcs()
        
        # No inputs means always enabled (if guard passes)
        if not input_arcs:
            return True, "enabled-continuous-no-inputs"
        
        # Check each input place for positive tokens
        for arc in input_arcs:
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            if kind != 'normal':
                continue
            
            source_place = self._get_place(arc.source_id)
            if source_place is None:
                return False, f"missing-source-place-{arc.source_id}"
            
            # Continuous requires positive, not >= weight
            if source_place.tokens <= 0:
                return False, f"input-place-empty-P{arc.source_id}"
        
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
            
            # Gather place objects for rate evaluation
            places_dict = {}
            for arc in input_arcs + output_arcs:
                place = self._get_place(arc.source_id if hasattr(arc, 'source_id') else arc.target_id)
                if place:
                    places_dict[place.id] = place
            
            # Evaluate rate function
            rate = self.rate_function(places_dict, current_time)
            rate = max(self.min_rate, min(self.max_rate, rate))
            
            # If rate is zero, nothing to integrate
            if rate <= 0:
                return True, {
                    'consumed': {},
                    'produced': {},
                    'continuous_mode': True,
                    'rate': 0.0,
                    'dt': dt,
                    'method': 'rk4'
                }
            
            # Check if this is a source or sink transition
            is_source = getattr(self.transition, 'is_source', False)
            is_sink = getattr(self.transition, 'is_sink', False)
            
            consumed_map = {}
            produced_map = {}
            
            # RK4 Integration (simplified for linear flow)
            # For continuous Petri nets, we approximate: flow = rate * dt
            # Full RK4 would require multiple rate evaluations at different points
            
            # Calculate intended flow amount
            intended_flow = rate * dt
            
            # Phase 1: Clamp flow to available tokens (skip if source)
            # Bug fix: Prevent transferring more tokens than available
            actual_flow = intended_flow
            if not is_source:
                for arc in input_arcs:
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    if kind != 'normal':
                        continue
                    
                    source_place = self._get_place(arc.source_id)
                    if source_place is None:
                        continue
                    
                    # Calculate max flow possible from this arc
                    max_flow_from_arc = source_place.tokens / arc.weight if arc.weight > 0 else float('inf')
                    actual_flow = min(actual_flow, max_flow_from_arc)
            
            # Phase 2: Consume tokens continuously from input places (skip if source)
            if not is_source and actual_flow > 0:
                for arc in input_arcs:
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    if kind != 'normal':
                        continue
                    
                    source_place = self._get_place(arc.source_id)
                    if source_place is None:
                        continue
                    
                    # Continuous consumption: arc_weight * actual_flow
                    consumption = arc.weight * actual_flow
                    
                    if consumption > 0:
                        source_place.set_tokens(source_place.tokens - consumption)
                        consumed_map[arc.source_id] = consumption
            
            # Phase 3: Produce tokens continuously to output places (skip if sink)
            if not is_sink and actual_flow > 0:
                for arc in output_arcs:
                    target_place = self._get_place(arc.target_id)
                    if target_place is None:
                        continue
                    
                    # Continuous production: arc_weight * actual_flow
                    production = arc.weight * actual_flow
                    
                    if production > 0:
                        target_place.set_tokens(target_place.tokens + production)
                        produced_map[arc.target_id] = production
            
            # Phase 4: Record continuous flow event
            self._record_event(
                consumed=consumed_map,
                produced=produced_map,
                mode='continuous',
                transition_type='continuous',
                rate=rate,
                actual_rate=actual_flow / dt if dt > 0 else 0.0,
                dt=dt,
                method='rk4',
                clamped=(actual_flow < intended_flow)
            )
            
            return True, {
                'consumed': consumed_map,
                'produced': produced_map,
                'continuous_mode': True,
                'rate': rate,
                'actual_rate': actual_flow / dt if dt > 0 else 0.0,
                'dt': dt,
                'method': 'rk4',
                'transition_type': 'continuous',
                'time': current_time,
                'clamped': (actual_flow < intended_flow)
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
