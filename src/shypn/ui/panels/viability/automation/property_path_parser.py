#!/usr/bin/env python3
"""Property Path Parser - Parse and apply object property paths.

Enables explicit property selection for batch sweeps via dot notation:
- "P1.initial_marking" (explicit)
- "T5.volume_threshold" (explicit)
- "A3.threshold" (explicit)
- "P1" (implicit - defaults to initial_marking)

Author: Simão Eugénio
Date: February 17, 2026
"""

import logging
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)


def resolve_object(model: Any, obj_id: str) -> Optional[Any]:
    """Resolve a model object by its ID or name.

    First tries the fast P/T/A prefix-based ID lookup, then falls back to a
    linear name search across all collections.  This handles the common case
    where sweep parameters are specified by place/transition name (e.g.
    "EPO_external") rather than by internal ID (e.g. "P1").

    Args:
        model: DocumentModel instance exposing .places, .transitions, .arcs
        obj_id: Object identifier – either an internal ID ('P1', 'T5', 'A3')
                or a human-readable name ('EPO_external', 'GATA1_transcription')

    Returns:
        Matching Place / Transition / Arc, or None if not found.

    Examples:
        >>> place = resolve_object(model, 'P1')           # by ID
        >>> place = resolve_object(model, 'EPO_external') # by name
        >>> trans = resolve_object(model, 'T5')
    """
    # --- fast path: ID-prefix lookup ---
    if obj_id.startswith('P'):
        result = next((p for p in model.places if p.id == obj_id), None)
        if result is not None:
            return result
    elif obj_id.startswith('T'):
        result = next((t for t in model.transitions if t.id == obj_id), None)
        if result is not None:
            return result
    elif obj_id.startswith('A'):
        result = next((a for a in model.arcs if a.id == obj_id), None)
        if result is not None:
            return result

    # --- fallback: name-based search across all collections ---
    result = next((p for p in model.places if getattr(p, 'name', None) == obj_id), None)
    if result is not None:
        return result
    result = next((t for t in model.transitions if getattr(t, 'name', None) == obj_id), None)
    if result is not None:
        return result
    result = next((a for a in model.arcs if getattr(a, 'name', None) == obj_id), None)
    if result is not None:
        return result

    logger.warning(f"resolve_object: no object found with id or name '{obj_id}'")
    return None


def parse_property_path(param_id: str) -> Tuple[str, str]:
    """Parse parameter ID into object ID and property name.
    
    Supports both explicit dot notation and implicit defaults for
    backward compatibility.
    
    Args:
        param_id: Parameter identifier
            - Explicit: "T5.volume_threshold", "A3.threshold"
            - Implicit: "P1" (defaults to initial_marking)
    
    Returns:
        Tuple of (object_id, property_name)
    
    Examples:
        >>> parse_property_path("P1")
        ('P1', 'initial_marking')
        >>> parse_property_path("T5.volume_threshold")
        ('T5', 'volume_threshold')
        >>> parse_property_path("A3.threshold")
        ('A3', 'threshold')
    """
    if '.' in param_id:
        # Explicit property path
        parts = param_id.split('.', 1)
        return parts[0], parts[1]
    else:
        # Implicit - infer property from object type (backward compatible)
        obj_id = param_id
        
        if obj_id.startswith('P'):
            return obj_id, 'initial_marking'
        elif obj_id.startswith('T'):
            return obj_id, 'rate'
        elif obj_id.startswith('A'):
            return obj_id, 'weight'
        else:
            raise ValueError(f"Cannot infer property for object ID: {obj_id}")


def validate_property_applicability(obj: Any, property_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a property is applicable to an object.
    
    Args:
        obj: Place, Transition, or Arc instance
        property_name: Property to validate
    
    Returns:
        Tuple of (is_valid, error_message)
            - (True, None) if property is valid
            - (False, "reason") if property is not applicable
    
    Examples:
        >>> trans = Transition(id='T1', transition_type='stochastic')
        >>> validate_property_applicability(trans, 'volume_threshold')
        (False, "volume_threshold only applies to adaptive transitions")
    """
    # Get object type
    obj_type = type(obj).__name__.lower()
    
    # Place properties
    if obj_type == 'place':
        valid_properties = ['initial_marking', 'tokens']
        if property_name not in valid_properties:
            return False, f"Unknown place property: {property_name}"
        return True, None
    
    # Transition properties
    elif obj_type == 'transition':
        # Always valid: rate
        if property_name == 'rate':
            return True, None
        
        # Context-dependent: volume_threshold
        if property_name == 'volume_threshold':
            if hasattr(obj, 'transition_type') and obj.transition_type == 'adaptive':
                return True, None
            else:
                return False, "volume_threshold only applies to adaptive transitions"
        
        # Unknown property
        return False, f"Unknown transition property: {property_name}"
    
    # Arc properties
    elif obj_type == 'arc':
        # Always valid: weight
        if property_name == 'weight':
            return True, None
        
        # Context-dependent: threshold
        if property_name == 'threshold':
            if hasattr(obj, 'arc_type') and obj.arc_type in ['inhibitor', 'test']:
                return True, None
            else:
                return False, "threshold only applies to inhibitor/test arcs"
        
        # Unknown property
        return False, f"Unknown arc property: {property_name}"
    
    # Unknown object type
    else:
        return False, f"Unknown object type: {obj_type}"


def apply_property_to_object(obj: Any, property_name: str, value: float) -> bool:
    """Apply property value to object with validation.
    
    Args:
        obj: Place, Transition, or Arc instance
        property_name: Property to modify
        value: New value
    
    Returns:
        True if applied successfully, False otherwise
    
    Side Effects:
        - Modifies obj attributes directly
        - Logs warnings for invalid operations
    """
    # Validate property is applicable
    is_valid, error_msg = validate_property_applicability(obj, property_name)
    
    if not is_valid:
        logger.warning(f"Cannot apply {property_name} to {obj.id}: {error_msg}")
        return False
    
    # Normalize property names (aliases)
    if property_name == 'initial_marking':
        property_name = 'tokens'  # Internal attribute name
    
    # Apply property
    try:
        setattr(obj, property_name, float(value))
        logger.debug(f"Applied {property_name}={value} to {obj.id}")
        return True
    except AttributeError as e:
        logger.error(f"Failed to set {property_name} on {obj.id}: {e}")
        return False
    except ValueError as e:
        logger.error(f"Invalid value for {property_name}: {value} ({e})")
        return False


def get_available_properties(obj: Any) -> list:
    """Get list of sweepable properties for an object.
    
    Args:
        obj: Place, Transition, or Arc instance
    
    Returns:
        List of tuples: [(property_id, display_name, tooltip), ...]
    
    Examples:
        >>> trans = Transition(id='T1', transition_type='adaptive')
        >>> get_available_properties(trans)
        [('rate', 'Rate', 'Kinetic constant...'),
         ('volume_threshold', 'Volume Threshold', 'Compartment volume...')]
    """
    obj_type = type(obj).__name__.lower()
    
    # Place properties
    if obj_type == 'place':
        return [
            ('initial_marking', 'Initial Marking', 
             'Starting token count or concentration')
        ]
    
    # Transition properties
    elif obj_type == 'transition':
        properties = [
            ('rate', 'Rate', 
             'Kinetic constant (s⁻¹ or concentration/time)')
        ]
        
        # Add volume_threshold only if adaptive
        if hasattr(obj, 'transition_type') and obj.transition_type == 'adaptive':
            properties.append((
                'volume_threshold',
                'Volume Threshold',
                'Compartment volume threshold for adaptive mode switching (fL)'
            ))
        
        return properties
    
    # Arc properties
    elif obj_type == 'arc':
        properties = [
            ('weight', 'Weight', 
             'Stoichiometric coefficient or arc multiplicity')
        ]
        
        # Add threshold only if inhibitor/test arc
        if hasattr(obj, 'arc_type') and obj.arc_type in ['inhibitor', 'test']:
            properties.append((
                'threshold',
                'Threshold',
                'Inhibition/activation threshold (token count)'
            ))
        
        return properties
    
    # Unknown type
    else:
        logger.warning(f"Unknown object type: {obj_type}")
        return []


# Module-level test when run directly
if __name__ == '__main__':
    # Test parsing
    print("Testing parse_property_path:")
    print(f"  P1 → {parse_property_path('P1')}")
    print(f"  T5.volume_threshold → {parse_property_path('T5.volume_threshold')}")
    print(f"  A3.threshold → {parse_property_path('A3.threshold')}")
    
    # Test with mock objects
    print("\nTesting validation:")
    
    class MockTransition:
        def __init__(self, id, transition_type):
            self.id = id
            self.transition_type = transition_type
            self.rate = 1.0
            self.volume_threshold = 1.0
    
    adaptive_trans = MockTransition('T1', 'adaptive')
    stochastic_trans = MockTransition('T2', 'stochastic')
    
    print(f"  Adaptive transition + volume_threshold: "
          f"{validate_property_applicability(adaptive_trans, 'volume_threshold')}")
    print(f"  Stochastic transition + volume_threshold: "
          f"{validate_property_applicability(stochastic_trans, 'volume_threshold')}")
    
    print("\nTesting property application:")
    success = apply_property_to_object(adaptive_trans, 'volume_threshold', 2.5)
    print(f"  Set volume_threshold=2.5: {success}, new value: {adaptive_trans.volume_threshold}")
