"""
Abstract base class for object transformation handlers.

This module defines the interface that all transformation handlers must implement.
Transformation handlers manage the lifecycle of a transformation operation:
1. Check if transformation is supported
2. Start transformation (store initial state)
3. Update transformation (apply changes during drag)
4. End transformation (finalize or cancel)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple


class TransformHandler(ABC):
    """Abstract base class for object transformation handlers.
    
    This class defines the interface for all transformation operations
    (resize, rotate, scale, etc.). Concrete handlers must implement all
    abstract methods.
    
    Attributes:
        selection_manager: Reference to the SelectionManager
        is_active: True if transformation is currently in progress
        drag_start_pos: (x, y) tuple of initial click position in world coords
        original_state: Dictionary storing original object geometry for undo
    """
    
    def __init__(self, selection_manager):
        """Initialize the transform handler.
        
        Args:
            selection_manager: The SelectionManager instance
        """
        self.selection_manager = selection_manager
        self.is_active = False
        self.drag_start_pos: Optional[Tuple[float, float]] = None
        self.original_state: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def can_transform(self, obj) -> bool:
        """Check if this handler can transform the given object.
        
        Args:
            obj: The object to check (Place, Transition, Arc, etc.)
            
        Returns:
            True if this handler supports transforming this object type
        """
        pass
    
    @abstractmethod
    def start_transform(self, obj, handle: str, start_x: float, start_y: float):
        """Begin transformation operation.
        
        This method is called when the user clicks on a transform handle.
        It should store the initial state for undo/redo and prepare for
        the transformation.
        
        Args:
            obj: The object being transformed
            handle: Handle identifier ('n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw')
            start_x: Initial X coordinate in world space
            start_y: Initial Y coordinate in world space
        """
        pass
    
    @abstractmethod
    def update_transform(self, current_x: float, current_y: float):
        """Update transformation during drag.
        
        This method is called repeatedly as the user drags the handle.
        It should update the object's geometry to reflect the current
        mouse position.
        
        Args:
            current_x: Current X coordinate in world space
            current_y: Current Y coordinate in world space
        """
        pass
    
    @abstractmethod
    def end_transform(self) -> bool:
        """Complete transformation and finalize changes.
        
        This method is called when the user releases the mouse button.
        It should finalize the transformation and create an undo operation.
        
        Returns:
            True if transformation was successful and should be committed,
            False if transformation should be cancelled
        """
        pass
    
    @abstractmethod
    def cancel_transform(self):
        """Cancel transformation and restore original state.
        
        This method is called if the user presses ESC or if the transformation
        needs to be aborted for any reason. It should restore the object to
        its original geometry.
        """
        pass
    
    @abstractmethod
    def get_preview_geometry(self) -> Optional[Dict[str, Any]]:
        """Get geometry for preview rendering during transform.
        
        This method returns the current geometry that should be used for
        preview rendering (e.g., dotted outline showing the new size).
        
        Returns:
            Dictionary containing geometry information, or None if no preview
            should be shown. The structure depends on the object type:
            - Place: {'x': float, 'y': float, 'radius': float}
            - Transition: {'x': float, 'y': float, 'width': float, 'height': float}
        """
        pass
    
    def is_transforming(self) -> bool:
        """Check if transformation is currently active.
        
        Returns:
            True if a transformation is in progress
        """
        return self.is_active
    
    def get_original_state(self) -> Optional[Dict[str, Any]]:
        """Get the original state stored at transformation start.
        
        Returns:
            Dictionary containing original geometry, or None if no
            transformation is active
        """
        return self.original_state
    
    def reset(self):
        """Reset handler state (called after transform completes or cancels)."""
        self.is_active = False
        self.drag_start_pos = None
        self.original_state = None
