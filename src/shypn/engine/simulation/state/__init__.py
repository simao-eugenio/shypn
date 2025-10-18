"""
Simulation State Management Module

Provides context-aware state detection and queries for simulation system.
Replaces explicit mode tracking with state-based behavior detection.
"""

from .base import SimulationState, StateQuery
from .detector import SimulationStateDetector
from .queries import (
    StructureEditQuery,
    TokenManipulationQuery,
    ObjectMovementQuery,
    TransformHandlesQuery
)

__all__ = [
    'SimulationState',
    'StateQuery',
    'SimulationStateDetector',
    'StructureEditQuery',
    'TokenManipulationQuery',
    'ObjectMovementQuery',
    'TransformHandlesQuery'
]
