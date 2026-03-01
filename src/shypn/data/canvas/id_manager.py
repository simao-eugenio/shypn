"""Centralized ID generation and management for Petri net objects.

This module ensures consistent ID generation across all model creation paths:
- Interactive drawing (create_place, create_transition, create_arc)
- KEGG import (compound_mapper, reaction_mapper, arc_builder)
- SBML import (pathway converter)
- Copy/paste operations
- Undo/redo operations

ID Format Convention:
- Places: "P1", "P2", "P3", ...
- Transitions: "T1", "T2", "T3", ...
- Arcs: "A1", "A2", "A3", ...

All IDs are strings, never integers. The numeric part is extracted when needed
for counter management.

LIFECYCLE INTEGRATION:
This IDManager can optionally delegate to a global IDScopeManager for
canvas-scoped ID generation. Set _lifecycle_scope_manager at module level
to enable multi-canvas support with isolated ID sequences.

LIFECYCLE HOOKS (Week 2 - Phase 4):
IDManager can track object lifecycle and emit events for observers:
- on_create: Called when object is created (for UndoManager, DataCollector)
- on_modify: Called when object properties change (for dirty tracking)
- on_delete: Called when object is deleted (for cleanup, reference removal)
"""

from typing import Tuple, Optional, Callable, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Global reference to lifecycle ID scope manager (set by lifecycle system)
_lifecycle_scope_manager: Optional['IDScopeManager'] = None  # type: ignore


def set_lifecycle_scope_manager(scope_manager: Optional['IDScopeManager']):  # type: ignore
    """Set global lifecycle scope manager for multi-canvas ID isolation.
    
    When set, all IDManager instances will delegate ID generation to this
    scope manager, enabling independent ID sequences per canvas.
    
    Args:
        scope_manager: IDScopeManager instance or None to disable
    """
    global _lifecycle_scope_manager
    _lifecycle_scope_manager = scope_manager


def get_lifecycle_scope_manager() -> Optional['IDScopeManager']:  # type: ignore
    """Get current lifecycle scope manager if set.
    
    Returns:
        IDScopeManager instance or None
    """
    return _lifecycle_scope_manager


@contextmanager
def suspend_lifecycle_delegation():
    """Temporarily disable lifecycle delegation for ID operations.
    
    Useful when parsing/loading a document off-canvas so that registering
    existing IDs does not contaminate whichever canvas scope happens to be
    active at the time (e.g., page 0).
    
    Example:
        with suspend_lifecycle_delegation():
            id_manager.register_place_id("P100")
    """
    global _lifecycle_scope_manager
    saved = _lifecycle_scope_manager
    _lifecycle_scope_manager = None
    try:
        yield
    finally:
        _lifecycle_scope_manager = saved


class IDManager:
    """Manages ID generation for places, transitions, and arcs.
    
    This class centralizes ID generation logic to ensure consistency across
    the entire application. It maintains separate counters for each object type
    and provides methods to generate new IDs and parse existing ones.
    
    **Lifecycle Tracking (Week 2 - Phase 4):**
    Optionally tracks object lifecycle and notifies observers when objects are
    created, modified, or deleted. Enables automatic cleanup and synchronization.
    
    Attributes:
        _next_place_id: Next available place counter
        _next_transition_id: Next available transition counter
        _next_arc_id: Next available arc counter
        _lifecycle_enabled: Whether lifecycle tracking is enabled
        _tracked_objects: Dict of object_id -> object for lifecycle tracking
        _lifecycle_callbacks: Dict of event_type -> list of callbacks
    """
    
    def __init__(self, enable_lifecycle: bool = False):
        """Initialize ID manager with counters starting at 1.
        
        Args:
            enable_lifecycle: Enable lifecycle tracking and event emissions
        """
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        self._next_module_id = 1  # Module counter for modular Bio-PN
        
        # Lifecycle tracking (Week 2 - Phase 4)
        self._lifecycle_enabled = enable_lifecycle
        self._tracked_objects: Dict[str, Any] = {}  # obj_id -> object
        self._lifecycle_callbacks: Dict[str, list[Callable]] = {
            'created': [],
            'modified': [],
            'deleted': []
        }
    
    def generate_place_id(self) -> str:
        """Generate a new place ID.
        
        Delegates to lifecycle scope manager if available for canvas isolation.
        Otherwise uses local counter.
        
        Returns:
            String ID in format "P1", "P2", etc.
        """
        global _lifecycle_scope_manager
        if _lifecycle_scope_manager is not None:
            try:
                return _lifecycle_scope_manager.generate_place_id()
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.debug(f"Lifecycle scope manager ID generation failed, using fallback: {e}")
        
        place_id = f"P{self._next_place_id}"
        self._next_place_id += 1
        return place_id
    
    def generate_transition_id(self) -> str:
        """Generate a new transition ID.
        
        Delegates to lifecycle scope manager if available for canvas isolation.
        Otherwise uses local counter.
        
        Returns:
            String ID in format "T1", "T2", etc.
        """
        global _lifecycle_scope_manager
        if _lifecycle_scope_manager is not None:
            try:
                return _lifecycle_scope_manager.generate_transition_id()
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.debug(f"Lifecycle scope manager transition ID generation failed, using fallback: {e}")
        
        transition_id = f"T{self._next_transition_id}"
        self._next_transition_id += 1
        return transition_id
    
    def generate_arc_id(self) -> str:
        """Generate a new arc ID.
        
        Delegates to lifecycle scope manager if available for canvas isolation.
        Otherwise uses local counter.
        
        Returns:
            String ID in format "A1", "A2", etc.
        """
        global _lifecycle_scope_manager
        if _lifecycle_scope_manager is not None:
            try:
                return _lifecycle_scope_manager.generate_arc_id()
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.debug(f"Lifecycle scope manager arc ID generation failed, using fallback: {e}")
        
        arc_id = f"A{self._next_arc_id}"
        self._next_arc_id += 1
        return arc_id
    
    def generate_module_id(self) -> str:
        """Generate a new module ID.
        
        Returns:
            String ID in format "M1", "M2", etc.
            
        Note:
            Modules are document-level, not lifecycle-scoped (no delegation)
        """
        module_id = f"M{self._next_module_id}"
        self._next_module_id += 1
        return module_id
    
    def register_place_id(self, place_id: str):
        """Register an existing place ID to prevent duplicates.
        
        Updates the counter if the registered ID is higher than current.
        Delegates to lifecycle scope manager if available.
        
        Args:
            place_id: Existing ID (e.g., "P101", "101", or numeric)
        """
        global _lifecycle_scope_manager
        if _lifecycle_scope_manager is not None:
            try:
                _lifecycle_scope_manager.register_place_id(str(place_id))
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.debug(f"Lifecycle scope manager place ID registration failed: {e}")
        
        numeric_id = self.extract_numeric_id(place_id, 'P')
        if numeric_id >= self._next_place_id:
            self._next_place_id = numeric_id + 1
    
    def register_transition_id(self, transition_id: str):
        """Register an existing transition ID to prevent duplicates.
        
        Updates the counter if the registered ID is higher than current.
        Delegates to lifecycle scope manager if available.
        
        Args:
            transition_id: Existing ID (e.g., "T35", "35", or numeric)
        """
        global _lifecycle_scope_manager
        if _lifecycle_scope_manager is not None:
            try:
                _lifecycle_scope_manager.register_transition_id(str(transition_id))
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.debug(f"Lifecycle scope manager transition ID registration failed: {e}")
        
        numeric_id = self.extract_numeric_id(transition_id, 'T')
        if numeric_id >= self._next_transition_id:
            self._next_transition_id = numeric_id + 1
    
    def register_arc_id(self, arc_id: str):
        """Register an existing arc ID to prevent duplicates.
        
        Updates the counter if the registered ID is higher than current.
        Delegates to lifecycle scope manager if available.
        
        Args:
            arc_id: Existing ID (e.g., "A113", "113", or numeric)
        """
        global _lifecycle_scope_manager
        if _lifecycle_scope_manager is not None:
            try:
                _lifecycle_scope_manager.register_arc_id(str(arc_id))
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.debug(f"Lifecycle scope manager arc ID registration failed: {e}")
        
        numeric_id = self.extract_numeric_id(arc_id, 'A')
        if numeric_id >= self._next_arc_id:
            self._next_arc_id = numeric_id + 1
    
    def register_module_id(self, module_id: str):
        """Register an existing module ID to prevent duplicates.
        
        Updates the counter if the registered ID is higher than current.
        
        Args:
            module_id: Existing ID (e.g., "M5", "5", or numeric)
            
        Note:
            Modules are document-level (no lifecycle delegation)
        """
        numeric_id = self.extract_numeric_id(module_id, 'M')
        if numeric_id >= self._next_module_id:
            self._next_module_id = numeric_id + 1
    
    @staticmethod
    def extract_numeric_id(id_value: Any, prefix: str = '') -> int:
        """Extract numeric part from an ID.
        
        Handles various ID formats:
        - String with prefix: "P101" → 101
        - String without prefix: "101" → 101
        - Integer: 101 → 101
        
        Args:
            id_value: ID in any format (str, int)
            prefix: Optional prefix to strip (e.g., 'P', 'T', 'A')
            
        Returns:
            Numeric part of the ID
            
        Raises:
            ValueError: If ID cannot be parsed
        """
        try:
            # Convert to string
            id_str = str(id_value)
            
            # Remove prefix if present
            if prefix and id_str.startswith(prefix):
                id_str = id_str[len(prefix):]
            
            # Convert to integer
            return int(id_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot extract numeric ID from '{id_value}': {e}")
    
    def reset(self):
        """Reset all counters to 1."""
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        self._next_module_id = 1
    
    def get_state(self) -> Tuple[int, int, int, int]:
        """Get current counter state.
        
        Returns:
            Tuple of (next_place_id, next_transition_id, next_arc_id, next_module_id)
        """
        return (self._next_place_id, self._next_transition_id, self._next_arc_id, self._next_module_id)
    
    def set_state(self, place_id: int, transition_id: int, arc_id: int, module_id: int = 1):
        """Set counter state directly.
        
        Args:
            place_id: Next place counter value
            transition_id: Next transition counter value
            arc_id: Next arc counter value
            module_id: Next module counter value (default: 1 for backward compatibility)
        """
        self._next_place_id = place_id
        self._next_transition_id = transition_id
        self._next_arc_id = arc_id
        self._next_module_id = module_id    
    # ========== Lifecycle Hooks (Week 2 - Phase 4) ==========
    
    def register_object(
        self, 
        obj: Any, 
        obj_type: str = 'unknown',
        on_create: Optional[Callable] = None,
        on_modify: Optional[Callable] = None,
        on_delete: Optional[Callable] = None
    ) -> None:
        """Register object for lifecycle tracking.
        
        Enables automatic cleanup and observer notifications when objects
        are created, modified, or deleted. UndoManager, DataCollector, and
        OverlayManager can subscribe to these events.
        
        Args:
            obj: Object to track (Place, Transition, Arc)
            obj_type: Type identifier ('place', 'transition', 'arc')
            on_create: Optional callback when object is created
            on_modify: Optional callback when object is modified
            on_delete: Optional callback when object is deleted
        
        Example:
            id_manager.register_object(
                place,
                obj_type='place',
                on_delete=lambda p: undo_manager.track_deletion(p)
            )
        """
        if not self._lifecycle_enabled:
            return
        
        obj_id = getattr(obj, 'id', str(id(obj)))
        self._tracked_objects[obj_id] = obj
        
        # Emit lifecycle event for global observers
        try:
            from shypn.events import EventBus
            EventBus.emit('lifecycle.object.created', {
                'object': obj,
                'object_id': obj_id,
                'object_type': obj_type
            })
        except ImportError:
            pass  # EventBus not available
        
        # Call custom callback if provided
        if on_create:
            try:
                on_create(obj)
            except (TypeError, AttributeError, RuntimeError) as e:
                logger.debug(f"Object creation callback failed: {e}")
    
    def notify_modified(self, obj: Any, property_name: Optional[str] = None, old_value: Any = None, new_value: Any = None):
        """Notify observers that object was modified.
        
        Args:
            obj: Modified object
            property_name: Name of modified property (e.g., 'tokens', 'rate_function')
            old_value: Previous value (optional)
            new_value: New value (optional)
        
        Example:
            place.tokens = 50
            id_manager.notify_modified(place, 'tokens', old_value=10, new_value=50)
        """
        if not self._lifecycle_enabled:
            return
        
        obj_id = getattr(obj, 'id', str(id(obj)))
        
        # Emit lifecycle event
        try:
            from shypn.events import EventBus
            EventBus.emit('lifecycle.object.modified', {
                'object': obj,
                'object_id': obj_id,
                'property': property_name,
                'old_value': old_value,
                'new_value': new_value
            })
        except ImportError:
            pass
        
        # Call registered callbacks
        for callback in self._lifecycle_callbacks['modified']:
            try:
                callback(obj, property_name, old_value, new_value)
            except (TypeError, AttributeError, RuntimeError) as e:
                logger.debug(f"Object modification callback failed: {e}")
    
    def notify_deleted(self, obj: Any, obj_type: str = 'unknown'):
        """Notify observers that object was deleted.
        
        Triggers cleanup in UndoManager, removes references from DataCollector,
        and unregisters from OverlayManager.
        
        Args:
            obj: Deleted object
            obj_type: Type identifier ('place', 'transition', 'arc')
        
        Example:
            id_manager.notify_deleted(place, 'place')
            # UndoManager records deletion, DataCollector removes from tracking
        """
        if not self._lifecycle_enabled:
            return
        
        obj_id = getattr(obj, 'id', str(id(obj)))
        
        # Remove from tracking
        if obj_id in self._tracked_objects:
            del self._tracked_objects[obj_id]
        
        # Emit lifecycle event
        try:
            from shypn.events import EventBus
            EventBus.emit('lifecycle.object.deleted', {
                'object': obj,
                'object_id': obj_id,
                'object_type': obj_type
            })
        except ImportError:
            pass
        
        # Call registered callbacks
        for callback in self._lifecycle_callbacks['deleted']:
            try:
                callback(obj, obj_type)
            except (TypeError, AttributeError, RuntimeError) as e:
                logger.debug(f"Object deletion callback failed: {e}")
    
    def subscribe_lifecycle(self, event_type: str, callback: Callable):
        """Subscribe to lifecycle events.
        
        Args:
            event_type: 'created', 'modified', or 'deleted'
            callback: Function to call when event occurs
        
        Example:
            id_manager.subscribe_lifecycle(
                'deleted',
                lambda obj, obj_type: undo_manager.track_deletion(obj)
            )
        """
        if event_type in self._lifecycle_callbacks:
            self._lifecycle_callbacks[event_type].append(callback)
    
    def unsubscribe_lifecycle(self, event_type: str, callback: Callable):
        """Unsubscribe from lifecycle events.
        
        Args:
            event_type: 'created', 'modified', or 'deleted'
            callback: Function to remove
        """
        if event_type in self._lifecycle_callbacks:
            try:
                self._lifecycle_callbacks[event_type].remove(callback)
            except ValueError:
                pass  # Callback not in list
    
    def get_tracked_objects(self) -> Dict[str, Any]:
        """Get all currently tracked objects.
        
        Returns:
            Dictionary of object_id -> object
        """
        return self._tracked_objects.copy()