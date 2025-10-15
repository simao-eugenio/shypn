"""Document-related events for object changes.

This module defines events related to changes in the Petri net document:
- Objects added/removed/modified
- Selection changes
- Document cleared
"""

from typing import List, Optional, Any
from .base_event import BaseEvent


class ObjectAddedEvent(BaseEvent):
    """Event fired when an object is added to the document.
    
    Attributes:
        obj: The object that was added
        obj_type: Type of object ('place', 'transition', 'arc')
    """
    
    def __init__(self, obj: Any, obj_type: str):
        """Initialize event.
        
        Args:
            obj: The object that was added
            obj_type: Type of object ('place', 'transition', 'arc')
        """
        super().__init__()
        self.obj = obj
        self.obj_type = obj_type
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'obj_type': self.obj_type,
            'obj_id': getattr(self.obj, 'id', None),
            'obj_name': getattr(self.obj, 'name', None),
        })
        return data
    
    def __repr__(self):
        obj_name = getattr(self.obj, 'name', 'unnamed')
        return f"ObjectAddedEvent(type={self.obj_type}, name={obj_name})"


class ObjectRemovedEvent(BaseEvent):
    """Event fired when an object is removed from the document.
    
    Attributes:
        obj: The object that was removed
        obj_type: Type of object ('place', 'transition', 'arc')
    """
    
    def __init__(self, obj: Any, obj_type: str):
        """Initialize event.
        
        Args:
            obj: The object that was removed
            obj_type: Type of object ('place', 'transition', 'arc')
        """
        super().__init__()
        self.obj = obj
        self.obj_type = obj_type
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'obj_type': self.obj_type,
            'obj_id': getattr(self.obj, 'id', None),
            'obj_name': getattr(self.obj, 'name', None),
        })
        return data
    
    def __repr__(self):
        obj_name = getattr(self.obj, 'name', 'unnamed')
        return f"ObjectRemovedEvent(type={self.obj_type}, name={obj_name})"


class ObjectModifiedEvent(BaseEvent):
    """Event fired when an object's properties are modified.
    
    Attributes:
        obj: The object that was modified
        obj_type: Type of object ('place', 'transition', 'arc')
        property_name: Name of the property that changed
        old_value: Previous value (optional)
        new_value: New value (optional)
    """
    
    def __init__(self, obj: Any, obj_type: str, property_name: str,
                 old_value: Any = None, new_value: Any = None):
        """Initialize event.
        
        Args:
            obj: The object that was modified
            obj_type: Type of object ('place', 'transition', 'arc')
            property_name: Name of the property that changed
            old_value: Previous value (optional)
            new_value: New value (optional)
        """
        super().__init__()
        self.obj = obj
        self.obj_type = obj_type
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'obj_type': self.obj_type,
            'obj_id': getattr(self.obj, 'id', None),
            'obj_name': getattr(self.obj, 'name', None),
            'property_name': self.property_name,
            'old_value': str(self.old_value),
            'new_value': str(self.new_value),
        })
        return data
    
    def __repr__(self):
        obj_name = getattr(self.obj, 'name', 'unnamed')
        return (f"ObjectModifiedEvent(type={self.obj_type}, name={obj_name}, "
                f"property={self.property_name})")


class SelectionChangedEvent(BaseEvent):
    """Event fired when the selection changes.
    
    Attributes:
        selected_objects: List of currently selected objects
        previously_selected: List of previously selected objects (optional)
    """
    
    def __init__(self, selected_objects: List[Any],
                 previously_selected: Optional[List[Any]] = None):
        """Initialize event.
        
        Args:
            selected_objects: List of currently selected objects
            previously_selected: List of previously selected objects (optional)
        """
        super().__init__()
        self.selected_objects = selected_objects or []
        self.previously_selected = previously_selected or []
    
    @property
    def selection_count(self) -> int:
        """Get number of selected objects."""
        return len(self.selected_objects)
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'selection_count': self.selection_count,
            'selected_ids': [getattr(obj, 'id', None) 
                           for obj in self.selected_objects],
        })
        return data
    
    def __repr__(self):
        return f"SelectionChangedEvent(count={self.selection_count})"


class DocumentClearedEvent(BaseEvent):
    """Event fired when the entire document is cleared.
    
    This is typically fired when creating a new document or closing
    the current one.
    """
    
    def __init__(self):
        """Initialize event."""
        super().__init__()
    
    def __repr__(self):
        return "DocumentClearedEvent()"
