"""Event system for state change notifications.

This module provides the event infrastructure for communicating state changes
throughout the application using the observer pattern.

Events are immutable data objects that describe what changed in the application
state. They flow from state managers to observers, enabling loose coupling
between components.

New in 2.5.6: EventBus for centralized pub/sub pattern (recommended for new code).

Example (Observer Pattern - Legacy):
    # State manager fires event
    event = ObjectAddedEvent(place)
    state_manager.notify_observers(event)
    
    # Observer receives event
    class MyObserver(BaseObserver):
        def on_event(self, event):
            if isinstance(event, ObjectAddedEvent):
                pass

Example (EventBus - New):
    from shypn.events import EventBus
    
    # Subscribe
    EventBus.subscribe('model.changed', self._on_model_changed)
    
    # Publish
    EventBus.emit('model.changed', model_data)
"""

from .base_event import BaseEvent
from .event_bus import EventBus
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
__all__ = [
    'BaseEvent',
    'EventBus',  # New in 2.5.6
    'ObjectAddedEvent',
    'ObjectRemovedEvent',
    'ObjectModifiedEvent',
    'SelectionChangedEvent',
    'DocumentClearedEvent',
    'ViewportChangedEvent',
    'ZoomChangedEvent',
    'PanChangedEvent',
]
