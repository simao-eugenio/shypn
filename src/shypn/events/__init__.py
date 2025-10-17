"""Event system for state change notifications.

This module provides the event infrastructure for communicating state changes
throughout the application using the observer pattern.

Events are immutable data objects that describe what changed in the application
state. They flow from state managers to observers, enabling loose coupling
between components.

Example:
    # State manager fires event
    event = ObjectAddedEvent(place)
    state_manager.notify_observers(event)
    
    # Observer receives event
    class MyObserver(BaseObserver):
        def on_event(self, event):
            if isinstance(event, ObjectAddedEvent):
"""

from .base_event import BaseEvent
from .document_events import (
    ObjectAddedEvent,
    ObjectRemovedEvent,
    ObjectModifiedEvent,
    SelectionChangedEvent,
    DocumentClearedEvent,
)
from .viewport_events import (
    ViewportChangedEvent,
    ZoomChangedEvent,
    PanChangedEvent,
)
from .mode_events import (
    ModeChangedEvent,
    ToolChangedEvent,
)

__all__ = [
    'BaseEvent',
    'ObjectAddedEvent',
    'ObjectRemovedEvent',
    'ObjectModifiedEvent',
    'SelectionChangedEvent',
    'DocumentClearedEvent',
    'ViewportChangedEvent',
    'ZoomChangedEvent',
    'PanChangedEvent',
    'ModeChangedEvent',
    'ToolChangedEvent',
]
