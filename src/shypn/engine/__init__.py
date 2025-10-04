#!/usr/bin/env python3
"""Transition Engine - Behavior-based Transition Firing System.

This package provides a clean OOP architecture for transition firing behaviors.
Each transition type (immediate, timed, stochastic, continuous) is implemented
as a separate behavior class following the Strategy pattern.

Architecture:
    - TransitionBehavior: Abstract base class defining the interface
    - ImmediateBehavior: Zero-delay discrete firing
    - TimedBehavior: TPN (Time Petri Net) with timing intervals
    - StochasticBehavior: FSPN (Fluid Stochastic) with burst firing
    - ContinuousBehavior: SHPN (Stochastic Hybrid) with rate functions
    - create_behavior(): Factory function to create appropriate behavior

Usage:
    from shypn.engine import create_behavior
    
    # Create behavior for a transition
    behavior = create_behavior(transition, model)
    
    # Check if can fire
    can_fire, reason = behavior.can_fire()
    
    # Execute firing
    if can_fire:
        success, details = behavior.fire(
            behavior.get_input_arcs(),
            behavior.get_output_arcs()
        )

Transition Types:
    - 'immediate': Fire instantly if enabled (zero delay)
    - 'timed': Fire within [earliest, latest] timing window (TPN)
    - 'stochastic': Fire with exponential distribution and bursting (FSPN)
    - 'continuous': Fire with continuous flow and rate functions (SHPN)
"""

# Version info
__version__ = '1.0.0'
__author__ = 'SHYPN Team'

# Base class
from .transition_behavior import TransitionBehavior

# Concrete behaviors (all now implemented)
from .immediate_behavior import ImmediateBehavior
from .timed_behavior import TimedBehavior
from .stochastic_behavior import StochasticBehavior
from .continuous_behavior import ContinuousBehavior

# Factory function
from .behavior_factory import create_behavior, get_available_types, is_type_implemented

# Public API - only export what should be used externally
__all__ = [
    # Base class
    'TransitionBehavior',
    
    # Concrete behaviors
    'ImmediateBehavior',
    'TimedBehavior',
    'StochasticBehavior',
    'ContinuousBehavior',
    
    # Factory functions
    'create_behavior',
    'get_available_types',
    'is_type_implemented',
]
