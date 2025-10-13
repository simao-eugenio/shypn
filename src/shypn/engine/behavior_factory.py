#!/usr/bin/env python3
"""Behavior Factory - Create appropriate transition behavior based on type.

This module provides a factory function to instantiate the correct behavior
class based on a transition's type attribute. This follows the Factory pattern,
centralizing behavior creation logic.
"""

from typing import Optional
from .transition_behavior import TransitionBehavior

# Import concrete behaviors (all now implemented)
from .immediate_behavior import ImmediateBehavior
from .timed_behavior import TimedBehavior
from .stochastic_behavior import StochasticBehavior
from .continuous_behavior import ContinuousBehavior


def create_behavior(transition, model) -> TransitionBehavior:
    """Factory method to create appropriate transition behavior.
    
    Examines the transition's type attribute and creates the corresponding
    behavior instance. This is the primary way to instantiate behaviors.
    
    Args:
        transition: Transition object with 'transition_type' attribute
        model: PetriNetModel instance providing context
        
    Returns:
        Appropriate TransitionBehavior subclass instance
        
    Raises:
        ValueError: If transition_type is unknown or not implemented yet
        
    Example:
        >>> transition.transition_type = 'immediate'
        >>> behavior = create_behavior(transition, model)
        >>> print(type(behavior).__name__)
        'ImmediateBehavior'
    """
    # Get transition type (default to 'continuous' if not specified)
    transition_type = getattr(transition, 'transition_type', 'continuous')
    
    # Type mapping (all behaviors now implemented)
    type_map = {
        'immediate': ImmediateBehavior,
        'timed': TimedBehavior,
        'stochastic': StochasticBehavior,
        'continuous': ContinuousBehavior,
    }
    
    # Get behavior class
    behavior_class = type_map.get(transition_type)
    
    if behavior_class is None:
        # Generate helpful error message
        available = ', '.join(f"'{t}'" for t in type_map.keys()) if type_map else 'none'
        raise ValueError(
            f"Unknown or unimplemented transition type: '{transition_type}'. "
            f"Available types: {available}. "
            f"Transition: {transition.name} (id={transition.id})"
        )
    
    # Create and return behavior instance
    return behavior_class(transition, model)


def get_available_types() -> list:
    """Get list of currently implemented transition types.
    
    Returns:
        List of type strings like ['immediate', 'timed', ...]
    """
    return ['immediate', 'timed', 'stochastic', 'continuous']


def is_type_implemented(transition_type: str) -> bool:
    """Check if a transition type is implemented.
    
    Args:
        transition_type: Type string to check
        
    Returns:
        bool: True if implemented, False otherwise
    """
    return transition_type in get_available_types()
