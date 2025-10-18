#!/usr/bin/env python3
"""Base Petri Net Object.

This module defines the base class for all Petri net objects (Place, Transition, Arc).
It contains shared properties and behaviors that all objects inherit.
"""
from typing import Optional, Callable


class PetriNetObject:
    """Base class for all Petri net objects.
    
    All Petri net objects (Place, Transition, Arc) inherit from this base class,
    which provides common identity management, state tracking, and redraw callbacks.
    
    Identity Properties (immutable, system-managed):
        - id (str): Unique internal identifier (string format supports flexible naming)
        - name (str): Human-readable unique name (P1, T1, A1, ...)
    
    User Properties (mutable):
        - label (str): User-editable display text
        - selected (bool): Selection state
    
    System Properties:
        - on_changed (Callable): Callback to trigger redraw when object changes
    """
    
    def __init__(self, id: str, name: str, label: str = ""):
        """Initialize the base Petri net object.
        
        Args:
            id: Unique string identifier (immutable, system-assigned)
            name: Unique name like "P1", "T1", "A1" (immutable, system-assigned)
            label: Optional user-editable text label (mutable)
        """
        # Identity properties (immutable - system managed)
        self._id = str(id)  # Ensure ID is string
        self._name = str(name)
        
        # User-editable properties
        self.label = label
        
        # State
        self.selected = False
        
        # Callback for triggering redraws
        self.on_changed: Optional[Callable] = None
    
    @property
    def id(self) -> str:
        """Get the unique identifier (read-only).
        
        Returns:
            str: Unique internal identifier
        """
        return self._id
    
    @property
    def name(self) -> str:
        """Get the unique name (read-only).
        
        Returns:
            str: Unique name like "P1", "T1", "A1"
        """
        return self._name
    
    def _trigger_redraw(self):
        """Request a redraw if callback is set.
        
        This method should be called by subclasses whenever the object's
        visual properties change.
        """
        if self.on_changed:
            self.on_changed()
    
    def render(self, cr, transform=None):
        """Render the object using Cairo.
        
        This is an abstract method that must be implemented by subclasses.
        
        Args:
            cr: Cairo context
            transform: Optional function to transform world coords to screen coords
        """
        raise NotImplementedError("Subclasses must implement render()")
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this object.
        
        This is an abstract method that must be implemented by subclasses.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is inside the object
        """
        raise NotImplementedError("Subclasses must implement contains_point()")
    
    def set_position(self, x: float, y: float):
        """Move the object to a new position.
        
        This is an abstract method that must be implemented by subclasses
        that have a position.
        
        Args:
            x, y: New position (world space)
        """
        raise NotImplementedError("Subclasses must implement set_position()")
    
    def to_dict(self) -> dict:
        """Serialize object to dictionary for persistence.
        
        This base implementation serializes common properties.
        Subclasses should override and call super().to_dict() to extend.
        
        Returns:
            dict: Dictionary containing object properties
        """
        return {
            "id": self.id,
            "name": self.name,
            "label": self.label if self.label else ""
        }
    
    def __repr__(self):
        """String representation for debugging.
        
        Returns:
            str: String representation
        """
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}', label='{self.label}')"
