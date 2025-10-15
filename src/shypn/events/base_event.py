"""Base event class for all state change events.

This module defines the abstract base class for all events in the application.
Events are immutable objects that describe state changes.
"""

from abc import ABC
from datetime import datetime
from typing import Any, Dict


class BaseEvent(ABC):
    """Abstract base class for all state change events.
    
    Events are immutable data objects that describe what changed in the
    application state. They include:
    - Timestamp of when the event occurred
    - Event type (derived from class name)
    - Event-specific data (in subclasses)
    
    Events are created by state managers and consumed by observers.
    
    Attributes:
        timestamp: When the event was created
    
    Example:
        class MyEvent(BaseEvent):
            def __init__(self, data):
                super().__init__()
                self.data = data
        
        # Create event
        event = MyEvent(some_data)
        
        # Event type is automatically derived
        print(event.event_type)  # "MyEvent"
        print(event.timestamp)   # datetime object
    """
    
    def __init__(self):
        """Initialize base event with timestamp."""
        self._timestamp = datetime.now()
    
    @property
    def event_type(self) -> str:
        """Get the event type name.
        
        Returns:
            The class name of this event.
        """
        return self.__class__.__name__
    
    @property
    def timestamp(self) -> datetime:
        """Get the timestamp when this event was created.
        
        Returns:
            Datetime when event was instantiated.
        """
        return self._timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation.
        
        Useful for serialization, logging, and debugging.
        
        Returns:
            Dictionary with event data.
        
        Note:
            Subclasses should override this to include event-specific data.
        """
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def __repr__(self) -> str:
        """Get string representation of event.
        
        Returns:
            String representation including type and timestamp.
        """
        return f"{self.event_type}(timestamp={self.timestamp})"
