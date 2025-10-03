"""Document Canvas - Main Canvas Controller.

This module provides the main canvas controller that coordinates all aspects
of a Petri net document canvas:
- Document lifecycle (new, open, save)
- Viewport control (zoom, pan)
- Object operations (add, remove, modify)
- Coordinate transformations
- Event coordination

The DocumentCanvas is the primary interface for working with a canvas document.
It delegates to DocumentModel for data and ViewportState for view management.
"""

from typing import Optional, Tuple, List, Callable
from datetime import datetime

from .canvas_state import ViewportState, DocumentState
from .document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc, PetriNetObject


class DocumentCanvas:
    """Main controller for a Petri net canvas document.
    
    This class coordinates:
    - Document state (DocumentState)
    - Document content (DocumentModel)
    - Viewport state (ViewportState)
    
    It provides high-level operations for:
    - Document lifecycle
    - Viewport manipulation
    - Object creation and manipulation
    - Queries and transformations
    
    Usage:
        # Create new canvas
        canvas = DocumentCanvas(width=800, height=600)
        canvas.new_document("MyNet.pn")
        
        # Add objects
        p1 = canvas.add_place(100, 100)
        t1 = canvas.add_transition(200, 100)
        arc = canvas.add_arc(p1, t1)
        
        # Viewport control
        canvas.zoom_in_at_point(400, 300)
        canvas.pan(50, 50)
        
        # Queries
        obj = canvas.get_object_at_screen_point(150, 150)
        objects = canvas.get_objects_in_screen_rectangle(50, 50, 250, 250)
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        """Initialize a new document canvas.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.document = DocumentModel()
        self.viewport = ViewportState(width, height)
        self.state = DocumentState()
        
        # Change notification callback (for UI updates)
        self._change_callback: Optional[Callable[[], None]] = None
    
    # ============================================================================
    # Change Notification
    # ============================================================================
    
    def set_change_callback(self, callback: Callable[[], None]):
        """Set callback to be called when canvas changes (for UI redraws).
        
        Args:
            callback: Function to call when canvas needs redraw
        """
        self._change_callback = callback
    
    def _notify_change(self):
        """Notify that canvas has changed (triggers UI redraw)."""
        self.state.mark_modified()
        if self._change_callback:
            self._change_callback()
    
    # ============================================================================
    # Document Lifecycle
    # ============================================================================
    
    def new_document(self, filename: Optional[str] = None):
        """Create a new empty document.
        
        Args:
            filename: Optional filename for the document
        """
        self.document.clear()
        self.state.reset(filename)
        self.viewport.reset()
        self._notify_change()
    
    def clear(self):
        """Clear all objects from the document."""
        self.document.clear()
        self._notify_change()
    
    def load_document(self, filepath: str):
        """Load a document from file.
        
        This is a placeholder - actual loading logic should use
        a separate loader/serializer.
        
        Args:
            filepath: Path to file to load
        """
        # TODO: Implement file loading
        # This would typically use a serializer to load from JSON/XML
        pass
    
    def save_document(self, filepath: str) -> bool:
        """Save document to file.
        
        This is a placeholder - actual saving logic should use
        a separate saver/serializer.
        
        Args:
            filepath: Path to save to
            
        Returns:
            True if saved successfully
        """
        # TODO: Implement file saving
        # This would typically use a serializer to save to JSON/XML
        self.state.mark_saved(filepath)
        self._notify_change()
        return True
    
    # ============================================================================
    # Viewport Operations
    # ============================================================================
    
    def zoom_in(self, center_x: Optional[float] = None, 
                center_y: Optional[float] = None):
        """Zoom in by one step.
        
        Args:
            center_x: X coordinate of zoom center (screen space), or None for canvas center
            center_y: Y coordinate of zoom center (screen space), or None for canvas center
        """
        if center_x is None:
            center_x = self.viewport.width / 2
        if center_y is None:
            center_y = self.viewport.height / 2
        
        new_zoom = self.viewport.zoom + ViewportState.ZOOM_STEP
        self.viewport.zoom_at_point(new_zoom, center_x, center_y)
        self._notify_change()
    
    def zoom_out(self, center_x: Optional[float] = None, 
                 center_y: Optional[float] = None):
        """Zoom out by one step.
        
        Args:
            center_x: X coordinate of zoom center (screen space), or None for canvas center
            center_y: Y coordinate of zoom center (screen space), or None for canvas center
        """
        if center_x is None:
            center_x = self.viewport.width / 2
        if center_y is None:
            center_y = self.viewport.height / 2
        
        new_zoom = self.viewport.zoom - ViewportState.ZOOM_STEP
        self.viewport.zoom_at_point(new_zoom, center_x, center_y)
        self._notify_change()
    
    def zoom_in_at_point(self, screen_x: float, screen_y: float):
        """Zoom in centered at a specific point.
        
        Args:
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space
        """
        self.zoom_in(screen_x, screen_y)
    
    def zoom_out_at_point(self, screen_x: float, screen_y: float):
        """Zoom out centered at a specific point.
        
        Args:
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space
        """
        self.zoom_out(screen_x, screen_y)
    
    def set_zoom(self, zoom: float, center_x: Optional[float] = None,
                 center_y: Optional[float] = None):
        """Set absolute zoom level.
        
        Args:
            zoom: Target zoom level (0.3 to 3.0)
            center_x: X coordinate of zoom center, or None for canvas center
            center_y: Y coordinate of zoom center, or None for canvas center
        """
        if center_x is None:
            center_x = self.viewport.width / 2
        if center_y is None:
            center_y = self.viewport.height / 2
        
        self.viewport.zoom_at_point(zoom, center_x, center_y)
        self._notify_change()
    
    def reset_zoom(self):
        """Reset zoom to 100% (1.0x)."""
        self.viewport.zoom = 1.0
        self._notify_change()
    
    def pan(self, dx: float, dy: float):
        """Pan viewport by delta in world coordinates.
        
        Args:
            dx: Horizontal delta in world units
            dy: Vertical delta in world units
        """
        self.viewport.pan(dx, dy)
        self._notify_change()
    
    def pan_screen(self, dx_screen: float, dy_screen: float):
        """Pan viewport by delta in screen coordinates.
        
        Args:
            dx_screen: Horizontal delta in screen pixels
            dy_screen: Vertical delta in screen pixels
        """
        self.viewport.pan_screen(dx_screen, dy_screen)
        self._notify_change()
    
    def resize(self, width: int, height: int):
        """Resize canvas viewport.
        
        Args:
            width: New width in pixels
            height: New height in pixels
        """
        self.viewport.resize(width, height)
        self._notify_change()
    
    # ============================================================================
    # Coordinate Transformations
    # ============================================================================
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: X in screen space
            screen_y: Y in screen space
            
        Returns:
            (world_x, world_y) tuple
        """
        return self.viewport.screen_to_world(screen_x, screen_y)
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates.
        
        Args:
            world_x: X in world space
            world_y: Y in world space
            
        Returns:
            (screen_x, screen_y) tuple
        """
        return self.viewport.world_to_screen(world_x, world_y)
    
    # ============================================================================
    # Object Creation
    # ============================================================================
    
    def add_place(self, x: float, y: float, label: str = "", 
                  in_world_coords: bool = True) -> Place:
        """Add a place to the document.
        
        Args:
            x: X coordinate
            y: Y coordinate
            label: Optional label
            in_world_coords: True if x,y are world coords, False for screen coords
            
        Returns:
            The created Place object
        """
        if not in_world_coords:
            x, y = self.screen_to_world(x, y)
        
        place = self.document.create_place(x, y, label)
        self._notify_change()
        return place
    
    def add_transition(self, x: float, y: float, label: str = "",
                       in_world_coords: bool = True) -> Transition:
        """Add a transition to the document.
        
        Args:
            x: X coordinate
            y: Y coordinate
            label: Optional label
            in_world_coords: True if x,y are world coords, False for screen coords
            
        Returns:
            The created Transition object
        """
        if not in_world_coords:
            x, y = self.screen_to_world(x, y)
        
        transition = self.document.create_transition(x, y, label)
        self._notify_change()
        return transition
    
    def add_arc(self, source: PetriNetObject, target: PetriNetObject,
                weight: int = 1) -> Optional[Arc]:
        """Add an arc connecting source to target.
        
        Args:
            source: Source object (Place or Transition)
            target: Target object (must be different type)
            weight: Arc weight
            
        Returns:
            The created Arc, or None if connection is invalid
        """
        arc = self.document.create_arc(source, target, weight)
        if arc:
            self._notify_change()
        return arc
    
    # ============================================================================
    # Object Removal
    # ============================================================================
    
    def remove_object(self, obj: PetriNetObject) -> bool:
        """Remove an object from the document.
        
        Args:
            obj: Object to remove
            
        Returns:
            True if removed successfully
        """
        result = self.document.remove_object(obj)
        if result:
            self._notify_change()
        return result
    
    def remove_objects(self, objects: List[PetriNetObject]):
        """Remove multiple objects from the document.
        
        Args:
            objects: List of objects to remove
        """
        for obj in objects:
            self.document.remove_object(obj)
        self._notify_change()
    
    # ============================================================================
    # Queries
    # ============================================================================
    
    def get_object_at_point(self, x: float, y: float, 
                           in_world_coords: bool = True,
                           tolerance: float = 5.0) -> Optional[PetriNetObject]:
        """Find object at a point.
        
        Args:
            x: X coordinate
            y: Y coordinate
            in_world_coords: True if x,y are world coords, False for screen coords
            tolerance: Hit test tolerance in world units
            
        Returns:
            Object at point, or None
        """
        if not in_world_coords:
            x, y = self.screen_to_world(x, y)
        
        return self.document.get_object_at_point(x, y, tolerance)
    
    def get_object_at_screen_point(self, screen_x: float, 
                                   screen_y: float) -> Optional[PetriNetObject]:
        """Find object at screen coordinates.
        
        Args:
            screen_x: X in screen space
            screen_y: Y in screen space
            
        Returns:
            Object at point, or None
        """
        return self.get_object_at_point(screen_x, screen_y, in_world_coords=False)
    
    def get_objects_in_rectangle(self, x1: float, y1: float,
                                 x2: float, y2: float,
                                 in_world_coords: bool = True) -> List[PetriNetObject]:
        """Find objects in a rectangle.
        
        Args:
            x1: Left edge
            y1: Top edge
            x2: Right edge
            y2: Bottom edge
            in_world_coords: True if coords are world coords, False for screen coords
            
        Returns:
            List of objects in rectangle
        """
        if not in_world_coords:
            x1, y1 = self.screen_to_world(x1, y1)
            x2, y2 = self.screen_to_world(x2, y2)
        
        return self.document.get_objects_in_rectangle(x1, y1, x2, y2)
    
    def get_objects_in_screen_rectangle(self, x1: float, y1: float,
                                       x2: float, y2: float) -> List[PetriNetObject]:
        """Find objects in a screen rectangle.
        
        Args:
            x1: Left edge (screen)
            y1: Top edge (screen)
            x2: Right edge (screen)
            y2: Bottom edge (screen)
            
        Returns:
            List of objects in rectangle
        """
        return self.get_objects_in_rectangle(x1, y1, x2, y2, in_world_coords=False)
    
    def get_all_objects(self) -> List[PetriNetObject]:
        """Get all objects in the document.
        
        Returns:
            List of all objects
        """
        return self.document.get_all_objects()
    
    def get_all_places(self) -> List[Place]:
        """Get all places in the document.
        
        Returns:
            List of places
        """
        return self.document.places
    
    def get_all_transitions(self) -> List[Transition]:
        """Get all transitions in the document.
        
        Returns:
            List of transitions
        """
        return self.document.transitions
    
    def get_all_arcs(self) -> List[Arc]:
        """Get all arcs in the document.
        
        Returns:
            List of arcs
        """
        return self.document.arcs
    
    def get_connected_arcs(self, obj: PetriNetObject) -> List[Arc]:
        """Get arcs connected to an object.
        
        Args:
            obj: Place or Transition
            
        Returns:
            List of connected arcs
        """
        return self.document.get_connected_arcs(obj)
    
    # ============================================================================
    # State Queries
    # ============================================================================
    
    def is_empty(self) -> bool:
        """Check if document has no objects.
        
        Returns:
            True if empty
        """
        return self.document.is_empty()
    
    def is_modified(self) -> bool:
        """Check if document has unsaved changes.
        
        Returns:
            True if modified
        """
        return self.state.modified
    
    def get_object_count(self) -> Tuple[int, int, int]:
        """Get count of objects.
        
        Returns:
            (places_count, transitions_count, arcs_count)
        """
        return self.document.get_object_count()
    
    def get_display_name(self) -> str:
        """Get display name for UI.
        
        Returns:
            Display name (filename or 'Untitled')
        """
        return self.state.display_name
    
    # ============================================================================
    # Grid Operations
    # ============================================================================
    
    def toggle_grid(self):
        """Toggle grid visibility."""
        self.viewport.grid_visible = not self.viewport.grid_visible
        self._notify_change()
    
    def set_grid_visible(self, visible: bool):
        """Set grid visibility.
        
        Args:
            visible: True to show grid, False to hide
        """
        self.viewport.grid_visible = visible
        self._notify_change()
    
    @property
    def grid_visible(self) -> bool:
        """Get grid visibility state."""
        return self.viewport.grid_visible
    
    @property
    def grid_spacing(self) -> float:
        """Get current grid spacing in world units."""
        return self.viewport.grid_spacing
    
    @property
    def zoom(self) -> float:
        """Get current zoom level."""
        return self.viewport.zoom
