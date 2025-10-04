#!/usr/bin/env python3
"""Conflict Resolution Policies for Petri Net Simulation.

When multiple transitions are enabled and compete for the same tokens,
a conflict resolution policy determines which transition fires.
"""

from enum import Enum


class ConflictResolutionPolicy(Enum):
    """Conflict resolution strategies for transition selection.
    
    When multiple transitions are enabled, the policy determines
    which one fires in a given simulation step.
    """
    
    RANDOM = "random"
    """Random selection (default).
    
    Selects one enabled transition randomly. Non-deterministic but fair
    over many iterations. Good for general-purpose simulation and exploration.
    """
    
    PRIORITY = "priority"
    """Priority-based selection.
    
    Selects the enabled transition with highest priority (transition.priority).
    Deterministic and reproducible. Good for modeling systems with precedence.
    May cause starvation of low-priority transitions.
    """
    
    TYPE_BASED = "type_based"
    """Type-based priority selection.
    
    Selects based on transition type priority:
    immediate > timed > stochastic > continuous
    
    Matches common Petri net semantics where immediate transitions
    fire before timed ones. Good for hybrid models.
    """
    
    ROUND_ROBIN = "round_robin"
    """Fair round-robin selection.
    
    Cycles through enabled transitions in order, ensuring all get a chance
    to fire. Prevents starvation. Good for resource allocation and fair
    scheduling scenarios.
    """
    
    def __str__(self) -> str:
        """Human-readable name."""
        return self.value
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"ConflictResolutionPolicy.{self.name}"


# Default policy for new simulations
DEFAULT_POLICY = ConflictResolutionPolicy.RANDOM


# Type priority ordering for TYPE_BASED policy
TYPE_PRIORITIES = {
    'immediate': 4,
    'timed': 3,
    'stochastic': 2,
    'continuous': 1,
}
