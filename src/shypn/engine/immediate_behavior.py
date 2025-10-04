#!/usr/bin/env python3
"""Immediate Behavior - Zero-delay discrete transition firing.

Immediate transitions fire instantly if enabled, with zero time delay.
They follow standard Petri net firing rules: consume Pre(p,t), produce Post(t,p).

Mathematical Model:
    - Enablement: ∀p ∈ •t: m(p) ≥ Pre(p,t)
    - Firing: m' = m - Pre + Post
    - Time delay: 0 (instant)
    - Token mode: Discrete (arc_weight units)

Extracted from: legacy/shypnpy/core/petri.py:1908-1970
"""

from typing import Dict, Tuple, List, Any
from .transition_behavior import TransitionBehavior


class ImmediateBehavior(TransitionBehavior):
    """Immediate transition firing behavior.
    
    Implements zero-delay discrete firing semantics:
    - Fires immediately if enabled (no timing constraints)
    - Consumes exactly arc_weight tokens from each input place
    - Produces exactly arc_weight tokens to each output place
    - Fails if any input place has insufficient tokens
    
    This is the simplest transition type and serves as the baseline
    for all other transition types.
    
    Usage:
        behavior = ImmediateBehavior(transition, model)
        
        if behavior.can_fire()[0]:
            success, details = behavior.fire(
                behavior.get_input_arcs(),
                behavior.get_output_arcs()
            )
    """
    
    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire (sufficient tokens in input places).
        
        For immediate transitions, the only constraint is structural enablement:
        all input places must have at least arc_weight tokens.
        
        Returns:
            Tuple of (can_fire: bool, reason: str)
            - (True, "enabled") if can fire
            - (False, "insufficient-tokens") if any input place lacks tokens
            - (False, "no-input-arcs") if transition has no inputs (always fires)
        """
        input_arcs = self.get_input_arcs()
        
        # Transition with no inputs is always enabled
        if not input_arcs:
            return True, "enabled-no-inputs"
        
        # Check each input place for sufficient tokens
        for arc in input_arcs:
            # Skip inhibitor arcs (they don't consume tokens)
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            if kind != 'normal':
                continue
            
            # Get source place directly from arc reference
            source_place = arc.source
            if source_place is None:
                return False, f"missing-source-place-{arc.name}"
            
            # Check sufficient tokens
            if source_place.tokens < arc.weight:
                return False, f"insufficient-tokens-{source_place.name}"
        
        return True, "enabled"
    
    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Execute immediate discrete firing.
        
        Firing process:
        1. Validate enablement (sufficient tokens)
        2. Consume exactly arc_weight tokens from each input place
        3. Produce exactly arc_weight tokens to each output place
        4. Record firing event
        
        Args:
            input_arcs: List of incoming Arc objects
            output_arcs: List of outgoing Arc objects
        
        Returns:
            Tuple of (success: bool, details: dict)
            
            Success case:
                (True, {
                    'consumed': {place_id: amount, ...},
                    'produced': {place_id: amount, ...},
                    'immediate_mode': True,
                    'discrete_firing': True
                })
            
            Failure case:
                (False, {
                    'reason': 'error-description',
                    'immediate_mode': True
                })
        """
        try:
            consumed_map = {}
            produced_map = {}
            
            # Phase 1: Consume tokens from input places
            for arc in input_arcs:
                # Skip inhibitor arcs (they don't consume)
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                if kind != 'normal':
                    continue
                
                # Get source place directly from arc reference
                source_place = arc.source
                if source_place is None:
                    return False, {
                        'reason': 'missing-source-place',
                        'place_name': arc.name,
                        'immediate_mode': True
                    }
                
                # Check sufficient tokens for immediate firing
                if source_place.tokens < arc.weight:
                    return False, {
                        'reason': 'insufficient-tokens',
                        'place_name': source_place.name,
                        'required': arc.weight,
                        'available': source_place.tokens,
                        'immediate_mode': True
                    }
                
                # Consume exactly arc_weight tokens (discrete semantics)
                old_tokens = source_place.tokens
                source_place.set_tokens(source_place.tokens - arc.weight)
                consumed_map[source_place.id] = float(arc.weight)
                
                # Debug validation
                assert source_place.tokens == old_tokens - arc.weight, \
                    f"Token consumption error: expected {old_tokens - arc.weight}, got {source_place.tokens}"
            
            # Phase 2: Produce tokens to output places
            for arc in output_arcs:
                # Get target place directly from arc reference
                target_place = arc.target
                if target_place is None:
                    # Skip if target place missing (shouldn't happen in valid net)
                    continue
                
                # Produce exactly arc_weight tokens (discrete semantics)
                old_tokens = target_place.tokens
                target_place.set_tokens(target_place.tokens + arc.weight)
                produced_map[target_place.id] = float(arc.weight)
                
                # Debug validation
                assert target_place.tokens == old_tokens + arc.weight, \
                    f"Token production error: expected {old_tokens + arc.weight}, got {target_place.tokens}"
            
            # Phase 3: Record the immediate firing event
            self._record_event(
                consumed=consumed_map,
                produced=produced_map,
                mode='logical',
                transition_type='immediate'
            )
            
            # Return success with details
            return True, {
                'consumed': consumed_map,
                'produced': produced_map,
                'immediate_mode': True,
                'discrete_firing': True,
                'transition_type': 'immediate',
                'time': self._get_current_time()
            }
            
        except Exception as e:
            # Catch any unexpected errors
            return False, {
                'reason': f'immediate-error: {str(e)}',
                'immediate_mode': True,
                'error_type': type(e).__name__
            }
    
    def get_type_name(self) -> str:
        """Return human-readable type name.
        
        Returns:
            str: "Immediate"
        """
        return "Immediate"
    
    # ============================================================================
    # Additional Helper Methods
    # ============================================================================
    
    def get_enablement_info(self) -> Dict[str, Any]:
        """Get detailed enablement information for debugging.
        
        Returns:
            Dictionary with enablement details for each input place
        """
        input_arcs = self.get_input_arcs()
        info = {
            'is_enabled': True,
            'input_places': []
        }
        
        for arc in input_arcs:
            kind = getattr(arc, 'kind', 'normal')
            if kind != 'normal':
                continue
            
            source_place = self._get_place(arc.source_id)
            if source_place is None:
                info['is_enabled'] = False
                info['input_places'].append({
                    'place_id': arc.source_id,
                    'required': arc.weight,
                    'available': 0,
                    'sufficient': False,
                    'missing': True
                })
                continue
            
            sufficient = source_place.tokens >= arc.weight
            if not sufficient:
                info['is_enabled'] = False
            
            info['input_places'].append({
                'place_id': arc.source_id,
                'place_name': getattr(source_place, 'name', f'P{arc.source_id}'),
                'required': arc.weight,
                'available': source_place.tokens,
                'sufficient': sufficient
            })
        
        return info
