"""
Resize handler for Places and Transitions.

This module implements the ResizeHandler which allows users to resize
Places (by changing radius) and Transitions (by changing width/height)
through interactive handle dragging.
"""

import math
from typing import Optional, Dict, Any

from shypn.edit.transformation.transform_handler import TransformHandler


class ResizeHandler(TransformHandler):
    """Handles resize operations for Petri Net objects.
    
    This handler supports:
    - Places: Uniform radius resize (all handles have same effect)
    - Transitions: Width/height resize (edge handles resize one dimension,
                   corner handles resize both dimensions)
    
    Attributes:
        active_handle: The handle being dragged ('n', 'ne', etc.)
        object_being_resized: The object currently being resized
        original_geometry: Dictionary storing original dimensions
    """
    
    # Constraints for Places
    MIN_PLACE_RADIUS = 10.0
    MAX_PLACE_RADIUS = 100.0
    
    # Constraints for Transitions
    MIN_TRANSITION_WIDTH = 20.0
    MAX_TRANSITION_WIDTH = 200.0
    MIN_TRANSITION_HEIGHT = 10.0
    MAX_TRANSITION_HEIGHT = 100.0
    
    def __init__(self, selection_manager):
        """Initialize the resize handler.
        
        Args:
            selection_manager: The SelectionManager instance
        """
        super().__init__(selection_manager)
        self.active_handle: Optional[str] = None
        self.object_being_resized = None
        self.original_geometry: Dict[str, Any] = {}
    
    def can_transform(self, obj) -> bool:
        """Check if this handler can resize the given object.
        
        Resize is supported for Places and Transitions only.
        
        Args:
            obj: The object to check
            
        Returns:
            True if object is a Place or Transition
        """
        from shypn.netobjs import Place, Transition
        return isinstance(obj, (Place, Transition))
    
    def start_transform(self, obj, handle: str, start_x: float, start_y: float):
        """Start resize operation.
        
        Stores the original geometry for undo/redo and to calculate
        relative changes during drag.
        
        Args:
            obj: The object being resized
            handle: Handle identifier ('n', 'ne', etc.)
            start_x: Initial X coordinate in world space
            start_y: Initial Y coordinate in world space
        """
        from shypn.netobjs import Place, Transition
        
        self.is_active = True
        self.active_handle = handle
        self.object_being_resized = obj
        self.drag_start_pos = (start_x, start_y)
        
        # Store original geometry for undo and relative calculations
        if isinstance(obj, Place):
            self.original_geometry = {
                'type': 'place',
                'x': obj.x,
                'y': obj.y,
                'radius': obj.radius
            }
        elif isinstance(obj, Transition):
            self.original_geometry = {
                'type': 'transition',
                'x': obj.x,
                'y': obj.y,
                'width': obj.width,
                'height': obj.height,
                'horizontal': obj.horizontal
            }
        
        self.original_state = self.original_geometry.copy()
    
    def update_transform(self, current_x: float, current_y: float):
        """Update object size during drag.
        
        Calculates the delta from start position and applies appropriate
        resize based on object type and active handle.
        
        Args:
            current_x: Current X coordinate in world space
            current_y: Current Y coordinate in world space
        """
        if not self.is_active or not self.drag_start_pos:
            return
        
        obj = self.object_being_resized
        start_x, start_y = self.drag_start_pos
        
        # Calculate delta from start position
        dx = current_x - start_x
        dy = current_y - start_y
        
        # Apply resize based on object type
        obj_type = self.original_geometry.get('type')
        if obj_type == 'place':
            self._resize_place(obj, dx, dy)
        elif obj_type == 'transition':
            self._resize_transition(obj, dx, dy)
    
    def _resize_place(self, place, dx: float, dy: float):
        """Resize a Place by changing its radius.
        
        For places, all handles have the same effect: they change the radius.
        We use the larger of dx and dy to determine the resize amount.
        
        Args:
            place: The Place object
            dx: X delta from start position
            dy: Y delta from start position
        """
        original_radius = self.original_geometry['radius']
        
        # Use the larger absolute delta for resize
        # This makes diagonal drags feel natural
        delta = dx if abs(dx) > abs(dy) else dy
        
        # Different handles pull in different directions
        # Adjust delta sign based on handle position
        handle = self.active_handle
        if handle in ['nw', 'w', 'sw']:
            delta = -delta  # Left side handles pull left (negative X is smaller)
        if handle in ['nw', 'n', 'ne']:
            delta = -delta if handle in ['n', 'nw'] else delta
        
        # Calculate new radius
        new_radius = original_radius + delta
        
        # Apply constraints
        new_radius = max(self.MIN_PLACE_RADIUS, min(self.MAX_PLACE_RADIUS, new_radius))
        
        # Update place
        place.radius = new_radius
    
    def _resize_transition(self, transition, dx: float, dy: float):
        """Resize a Transition by changing width and/or height.
        
        The resize behavior depends on which handle is being dragged:
        - Edge handles (n, e, s, w): Resize one dimension
        - Corner handles (ne, se, sw, nw): Resize both dimensions
        
        Args:
            transition: The Transition object
            dx: X delta from start position
            dy: Y delta from start position
        """
        orig = self.original_geometry
        handle = self.active_handle
        
        # Get original dimensions (considering orientation)
        orig_width = orig['width']
        orig_height = orig['height']
        is_horizontal = orig['horizontal']
        
        # Calculate new dimensions based on handle
        new_width = orig_width
        new_height = orig_height
        
        if handle == 'e':
            # East handle: increase width (horizontal right)
            new_width = orig_width + dx
        elif handle == 'w':
            # West handle: decrease width (horizontal left)
            new_width = orig_width - dx
        elif handle == 'n':
            # North handle: decrease height (vertical up)
            new_height = orig_height - dy
        elif handle == 's':
            # South handle: increase height (vertical down)
            new_height = orig_height + dy
        elif handle == 'ne':
            # Northeast corner: increase width, decrease height
            new_width = orig_width + dx
            new_height = orig_height - dy
        elif handle == 'se':
            # Southeast corner: increase both
            new_width = orig_width + dx
            new_height = orig_height + dy
        elif handle == 'sw':
            # Southwest corner: decrease width, increase height
            new_width = orig_width - dx
            new_height = orig_height + dy
        elif handle == 'nw':
            # Northwest corner: decrease both
            new_width = orig_width - dx
            new_height = orig_height - dy
        
        # Apply constraints
        new_width = max(self.MIN_TRANSITION_WIDTH, 
                       min(self.MAX_TRANSITION_WIDTH, new_width))
        new_height = max(self.MIN_TRANSITION_HEIGHT, 
                        min(self.MAX_TRANSITION_HEIGHT, new_height))
        
        # Update transition
        transition.width = new_width
        transition.height = new_height
    
    def end_transform(self) -> bool:
        """Complete the resize operation.
        
        Returns:
            True if resize was successful and should be committed
        """
        if not self.is_active:
            return False
        
        # Check if anything actually changed
        obj = self.object_being_resized
        orig = self.original_geometry
        
        if orig.get('type') == 'place':
            changed = abs(obj.radius - orig['radius']) > 0.1
        elif orig.get('type') == 'transition':
            changed = (abs(obj.width - orig['width']) > 0.1 or
                      abs(obj.height - orig['height']) > 0.1)
        else:
            changed = False
        
        # Reset handler state
        self.reset()
        
        return changed
    
    def cancel_transform(self):
        """Cancel the resize and restore original geometry.
        
        This is called when the user presses ESC or if the operation
        needs to be aborted.
        """
        if not self.is_active or not self.object_being_resized:
            return
        
        obj = self.object_being_resized
        orig = self.original_geometry
        
        # Restore original geometry
        if orig.get('type') == 'place':
            obj.x = orig['x']
            obj.y = orig['y']
            obj.radius = orig['radius']
        elif orig.get('type') == 'transition':
            obj.x = orig['x']
            obj.y = orig['y']
            obj.width = orig['width']
            obj.height = orig['height']
            obj.horizontal = orig['horizontal']
        
        # Reset handler state
        self.reset()
    
    def get_preview_geometry(self) -> Optional[Dict[str, Any]]:
        """Get current geometry for preview rendering.
        
        Returns current object dimensions that can be used to draw
        a preview outline during resize.
        
        Returns:
            Dictionary with geometry information, or None
        """
        if not self.is_active or not self.object_being_resized:
            return None
        
        obj = self.object_being_resized
        obj_type = self.original_geometry.get('type')
        
        if obj_type == 'place':
            return {
                'type': 'place',
                'x': obj.x,
                'y': obj.y,
                'radius': obj.radius
            }
        elif obj_type == 'transition':
            return {
                'type': 'transition',
                'x': obj.x,
                'y': obj.y,
                'width': obj.width,
                'height': obj.height,
                'horizontal': obj.horizontal
            }
        
        return None
    
    def reset(self):
        """Reset all handler state."""
        super().reset()
        self.active_handle = None
        self.object_being_resized = None
        self.original_geometry = {}
