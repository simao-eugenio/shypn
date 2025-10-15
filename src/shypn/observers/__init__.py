"""Observer pattern implementation for state change notifications.

This module provides the observer infrastructure for responding to state
changes in the application.

Observers register with state managers and receive event notifications
when state changes occur. This enables loose coupling between state
management and UI/persistence/validation logic.

Example:
    class StatusBarObserver(BaseObserver):
        def __init__(self, status_bar):
            self.status_bar = status_bar
        
        def can_handle(self, event):
            return isinstance(event, (ObjectAddedEvent, ZoomChangedEvent))
        
        def on_event(self, event):
            if isinstance(event, ObjectAddedEvent):
                self.status_bar.set_text(f"Added {event.obj.name}")
    
    # Register observer
    observer = StatusBarObserver(status_bar)
    state_manager.add_observer(observer)
"""

from .base_observer import BaseObserver

__all__ = ['BaseObserver']
