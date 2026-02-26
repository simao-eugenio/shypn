"""Event system for decoupling GUI panels and components.

Provides a centralized event bus for pub/sub communication between
loosely coupled components. Replaces direct panel-to-panel references.

Example:
    # Publisher (Pathway Operations Panel)
    EventBus.emit('pathway.imported', {
        'source': 'kegg',
        'pathway_id': 'hsa00010',
        'document': document_model
    })
    
    # Subscriber (Report Panel)
    class ReportPanel:
        def __init__(self):
            EventBus.subscribe('pathway.imported', self._on_pathway_imported)
        
        def _on_pathway_imported(self, event_data):
            self.refresh_metadata(event_data['document'])

Author: SHYpn Development Team
Date: February 2026
"""

from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import logging
import traceback

logger = logging.getLogger(__name__)


class EventBus:
    """Centralized event bus for publish-subscribe pattern.
    
    Allows components to communicate without direct coupling.
    Thread-safe for GTK main loop (all callbacks in main thread).
    
    Features:
    - Subscribe to events with callbacks
    - Emit events with arbitrary data
    - Wildcard subscriptions (e.g., 'model.*')
    - Priority ordering for subscribers
    - Error handling (one bad subscriber doesn't break others)
    """
    
    # Class-level storage for subscribers
    # Modified for multi-document support: (document_id, priority, handler)
    _subscribers: Dict[str, List[tuple[Optional[int], int, Callable]]] = defaultdict(list)
    _wildcard_subscribers: List[tuple[str, Optional[int], int, Callable]] = []
    
    # Event name registry for documentation
    _registered_events: Dict[str, str] = {}
    
    @classmethod
    def subscribe(
        cls,
        event_name: str,
        handler: Callable[[Any], None],
        document_id: Optional[int] = None,
        priority: int = 0
    ) -> None:
        """Subscribe to an event.
        
        Args:
            event_name: Event name (e.g., 'model.changed', 'simulation.complete')
                       Use wildcards: 'model.*' matches all model events
            handler: Callback function(event_data) -> None
            document_id: If provided, only receive events for this document.
                        If None, receive events for ALL documents (global subscription).
                        Use id(drawing_area) for document identification.
            priority: Higher values called first (default: 0)
        
        Example (Global):
            # Receive events from all documents
            EventBus.subscribe('model.loaded', self._on_any_model_loaded)
        
        Example (Document-Specific):
            # Only receive events for THIS document
            document_id = id(drawing_area)
            EventBus.subscribe('model.changed', self._on_this_model_changed,
                             document_id=document_id)
        """
        if '*' in event_name:
            # Wildcard subscription
            pattern = event_name.replace('*', '')
            cls._wildcard_subscribers.append((pattern, document_id, priority, handler))
            cls._wildcard_subscribers.sort(key=lambda x: -x[2])  # Sort by priority desc
        else:
            # Exact match subscription
            cls._subscribers[event_name].append((document_id, priority, handler))
            cls._subscribers[event_name].sort(key=lambda x: -x[1])  # Sort by priority desc
        
        doc_str = f" (document_id={document_id})" if document_id else " (global)"
        logger.debug(f"Subscribed to '{event_name}'{doc_str} with priority {priority}")
    
    @classmethod
    def unsubscribe(cls, event_name: str, handler: Callable, document_id: Optional[int] = None) -> bool:
        """Unsubscribe from an event.
        
        Args:
            event_name: Event name to unsubscribe from
            handler: The exact handler function that was subscribed
            document_id: Optional document_id if it was a document-specific subscription
        
        Returns:
            True if handler was found and removed, False otherwise
        
        Example:
            EventBus.unsubscribe('model.loaded', self._on_model_loaded)
            # Or for document-specific:
            EventBus.unsubscribe('model.loaded', self._on_model_loaded, document_id=doc_id)
        """
        if '*' in event_name:
            # Remove from wildcard subscribers
            pattern = event_name.replace('*', '')
            original_len = len(cls._wildcard_subscribers)
            cls._wildcard_subscribers = [
                (p, doc_id, pri, h) for p, doc_id, pri, h in cls._wildcard_subscribers
                if not (p == pattern and h == handler and doc_id == document_id)
            ]
            return len(cls._wildcard_subscribers) < original_len
        else:
            # Remove from exact match subscribers
            if event_name in cls._subscribers:
                original_len = len(cls._subscribers[event_name])
                cls._subscribers[event_name] = [
                    (doc_id, pri, h) for doc_id, pri, h in cls._subscribers[event_name]
                    if not (h == handler and doc_id == document_id)
                ]
                return len(cls._subscribers[event_name]) < original_len
        
        return False
    
    @classmethod
    def emit(cls, event_name: str, data: Any = None, document_id: Optional[int] = None) -> None:
        """Emit an event to all subscribers.
        
        Args:
            event_name: Event name (e.g., 'model.changed')
            data: Optional event data (dict, object, or primitive)
            document_id: Document ID this event belongs to (use id(drawing_area)).
                        If None, this is a global event (e.g., 'application.quit').
                        If provided, only subscribers for THIS document + global subscribers receive it.
        
        Example (Global Event):
            EventBus.emit('application.quit')
        
        Example (Document Event):
            document_id = id(drawing_area)
            EventBus.emit('simulation.progress', {
                'progress': 0.75,
                'replicate': 50,
                'total': 100
            }, document_id=document_id)
        
        Note:
            - Subscribers are called in priority order (highest first)
            - If a subscriber raises an exception, it's logged but other subscribers still get called
            - Document-specific subscribers only receive events for their document
            - Global subscribers (no document_id) receive ALL events
        """
        # Add document_id to event data for convenience
        if data is None:
            data = {}
        if isinstance(data, dict) and document_id is not None:
            data['_document_id'] = document_id
        
        doc_str = f" for document_id={document_id}" if document_id else " (global)"
        logger.debug(f"Emitting event '{event_name}'{doc_str} with data: {type(data).__name__}")
        
        # Call exact match subscribers
        if event_name in cls._subscribers:
            for sub_doc_id, priority, handler in cls._subscribers[event_name]:
                if cls._should_call_handler(sub_doc_id, document_id):
                    try:
                        handler(data)
                    except Exception as e:
                        logger.error(
                            f"Error in subscriber {handler.__name__} for event '{event_name}': {e}\n"
                            f"{traceback.format_exc()}"
                        )
        
        # Call wildcard subscribers
        for pattern, sub_doc_id, priority, handler in cls._wildcard_subscribers:
            if event_name.startswith(pattern) and cls._should_call_handler(sub_doc_id, document_id):
                try:
                    handler(data)
                except Exception as e:
                    logger.error(
                        f"Error in wildcard subscriber {handler.__name__} for event '{event_name}': {e}\n"
                        f"{traceback.format_exc()}"
                    )
    
    @classmethod
    def _should_call_handler(cls, subscriber_doc_id: Optional[int], event_doc_id: Optional[int]) -> bool:
        """Determine if handler should be called based on document IDs.
        
        Logic:
            - If subscriber has NO document_id (global subscription) → always call
            - If event has NO document_id (global event) → only call global subscribers
            - If both have document_id → call only if they match
        
        Args:
            subscriber_doc_id: Document ID the subscriber is bound to (None = global)
            event_doc_id: Document ID the event was emitted for (None = global event)
        
        Returns:
            True if handler should be called, False otherwise
        """
        if subscriber_doc_id is None:
            # Global subscription - always call
            return True
        if event_doc_id is None:
            # Event has no document - don't call document-specific subscribers
            return False
        # Both have document IDs - must match
        return subscriber_doc_id == event_doc_id
    
    @classmethod
    def register_event(cls, event_name: str, description: str) -> None:
        """Register an event name with documentation.
        
        This is optional but helps with discoverability and documentation.
        
        Args:
            event_name: Event name
            description: Human-readable description of when this event is emitted
        
        Example:
            EventBus.register_event(
                'model.changed',
                'Emitted when the Petri net model structure changes'
            )
        """
        cls._registered_events[event_name] = description
        logger.debug(f"Registered event '{event_name}': {description}")
    
    @classmethod
    def get_registered_events(cls) -> Dict[str, str]:
        """Get all registered events with descriptions.
        
        Returns:
            Dictionary of event_name -> description
        """
        return cls._registered_events.copy()
    
    @classmethod
    def clear_document(cls, document_id: int) -> int:
        """Remove all subscriptions bound to a specific document.
        
        Call this when a document tab is closed to prevent handler leaks.
        Removes both exact-match and wildcard subscriptions for the document.
        
        Args:
            document_id: The document ID (previously passed to subscribe/emit).
                         Use the same value that was used when subscribing.
        
        Returns:
            Number of subscriptions removed.
        
        Example:
            # In ModelCanvasLoader.close_document():
            EventBus.clear_document(id(drawing_area))
        """
        removed = 0
        for event_name in list(cls._subscribers.keys()):
            before = len(cls._subscribers[event_name])
            cls._subscribers[event_name] = [
                (did, pri, h) for did, pri, h in cls._subscribers[event_name]
                if did != document_id
            ]
            removed += before - len(cls._subscribers[event_name])
        before_wc = len(cls._wildcard_subscribers)
        cls._wildcard_subscribers = [
            (p, did, pri, h) for p, did, pri, h in cls._wildcard_subscribers
            if did != document_id
        ]
        removed += before_wc - len(cls._wildcard_subscribers)
        logger.debug(f"clear_document({document_id}): removed {removed} subscriptions")
        return removed

    @classmethod
    def clear_all(cls) -> None:
        """Clear all subscriptions (useful for testing).
        
        Warning: This removes ALL subscribers. Only use in tests or shutdown.
        """
        cls._subscribers.clear()
        cls._wildcard_subscribers.clear()
        logger.debug("Cleared all event subscriptions")


# Register standard SHYpn events for documentation
def register_standard_events():
    """Register all standard SHYpn events."""
    
    # Model events
    EventBus.register_event('model.loaded', 'Model loaded from file')
    EventBus.register_event('model.saved', 'Model saved to file')
    EventBus.register_event('model.changed', 'Model structure changed (place/transition/arc added/removed)')
    EventBus.register_event('model.closed', 'Model closed')
    
    # Pathway import events
    EventBus.register_event('pathway.imported', 'Pathway imported from SBML/KEGG/BiGG')
    EventBus.register_event('pathway.enriched', 'Pathway enriched with BRENDA/SABIO-RK data')
    
    # Simulation events
    EventBus.register_event('simulation.started', 'Simulation run started')
    EventBus.register_event('simulation.progress', 'Simulation progress update (for batch runs)')
    EventBus.register_event('simulation.complete', 'Simulation run completed')
    EventBus.register_event('simulation.cancelled', 'Simulation cancelled by user')
    EventBus.register_event('simulation.error', 'Simulation error occurred')
    
    # Analysis events
    EventBus.register_event('topology.analyzed', 'Topology analysis completed')
    EventBus.register_event('thermodynamics.validated', 'Thermodynamic validation completed')
    
    # Project events
    EventBus.register_event('project.opened', 'Project opened')
    EventBus.register_event('project.closed', 'Project closed')
    EventBus.register_event('project.settings.changed', 'Project settings changed')
    
    # UI events
    EventBus.register_event('tab.switched', 'Main notebook tab switched')
    EventBus.register_event('selection.changed', 'Canvas object selection changed')
    
    # Settings events (global scope)
    EventBus.register_event('settings.changed', 'Workspace setting modified')
    
    # File operation events (document-scoped)
    EventBus.register_event('file.opened', 'Document loaded from filesystem')
    EventBus.register_event('file.saved', 'Document saved to filesystem')
    EventBus.register_event('file.closed', 'Document/tab closed')
    EventBus.register_event('file.imported', 'External format imported')
    
    # Model modification events (document-scoped, hierarchical)
    EventBus.register_event('model.place.created', 'Place created')
    EventBus.register_event('model.place.deleted', 'Place deleted')
    EventBus.register_event('model.place.modified', 'Place modified')
    
    EventBus.register_event('model.transition.created', 'Transition created')
    EventBus.register_event('model.transition.deleted', 'Transition deleted')
    EventBus.register_event('model.transition.modified', 'Transition modified')
    
    EventBus.register_event('model.arc.created', 'Arc created')
    EventBus.register_event('model.arc.deleted', 'Arc deleted')
    EventBus.register_event('model.arc.modified', 'Arc modified')
    
    EventBus.register_event('model.batch.started', 'Batch modification started')
    EventBus.register_event('model.batch.completed', 'Batch modification completed')
    
    # Lifecycle events (Week 2 - Phase 4)
    # Enables automatic cleanup and observer pattern for object lifecycle
    EventBus.register_event('lifecycle.object.created', 'Object created and registered in lifecycle')
    EventBus.register_event('lifecycle.object.modified', 'Object modified after creation')
    EventBus.register_event('lifecycle.object.deleted', 'Object deleted and unregistered from lifecycle')


# Auto-register on module import
register_standard_events()
