"""Base observer class for state change notifications.

This module defines the abstract base class for all observers in the
application. Observers respond to state change events.
"""

from abc import ABC, abstractmethod
from shypn.events import BaseEvent


class BaseObserver(ABC):
    """Abstract base class for all state change observers.
    
    Observers respond to state changes by implementing the on_event method.
    They can optionally filter which events they handle by overriding
    the can_handle method.
    
    Observers are registered with state managers and receive notifications
    whenever state changes occur.
    
    Example:
        class StatusBarObserver(BaseObserver):
            def __init__(self, status_bar):
                self.status_bar = status_bar
            
            def can_handle(self, event):
                # Only handle specific event types
                return isinstance(event, (ObjectAddedEvent, ObjectRemovedEvent))
            
            def on_event(self, event):
                if isinstance(event, ObjectAddedEvent):
                    self.status_bar.push(f"Added {event.obj.name}")
                elif isinstance(event, ObjectRemovedEvent):
                    self.status_bar.push(f"Removed {event.obj.name}")
    
    Usage:
        # Create observer
        observer = StatusBarObserver(status_bar)
        
        # Register with state manager
        state_manager.add_observer(observer)
        
        # Observer automatically receives events
        state_manager.add_place(x, y)  # → ObjectAddedEvent → observer.on_event()
    """
    
    @abstractmethod
    def on_event(self, event: BaseEvent):
        """Handle a state change event.
        
        This method is called by the state manager when a state change occurs
        and can_handle() returns True for the event.
        
        Args:
            event: The event describing the state change
        
        Example:
            def on_event(self, event):
                if isinstance(event, ZoomChangedEvent):
                    self.update_zoom_display(event.zoom_percent)
                elif isinstance(event, SelectionChangedEvent):
                    self.update_selection_count(event.selection_count)
        """
        pass
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this observer can handle the given event.
        
        Override this method to filter events. By default, all events
        are handled. Return False to ignore specific event types.
        
        Args:
            event: The event to check
        
        Returns:
            True if this observer should handle this event, False otherwise
        
        Example:
            def can_handle(self, event):
                # Only handle viewport events
                return isinstance(event, (ZoomChangedEvent, PanChangedEvent))
        """
        return True
    
    def priority(self) -> int:
        """Get the priority of this observer.
        
        Observers with higher priority are notified first. This is useful
        when the order of notifications matters (e.g., validation before
        persistence).
        
        Returns:
            Priority value (higher = notified first, default = 0)
        
        Example:
            def priority(self):
                return 10  # High priority - notified before others
        """
        return 0
