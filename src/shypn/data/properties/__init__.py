"""Property managers for netobjects.

This package contains business logic for property editing,
separated from UI concerns for testability and maintainability.
"""

from .property_manager import (
    PropertyManager,
    PlacePropertyManager,
    TransitionPropertyManager,
    ArcPropertyManager,
)

__all__ = [
    'PropertyManager',
    'PlacePropertyManager',
    'TransitionPropertyManager',
    'ArcPropertyManager',
]
