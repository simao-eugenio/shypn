"""Drag Controller for Canvas Objects.

This module provides drag-and-drop functionality for canvas objects.
It handles the complete drag lifecycle: start, update, end, and cancel.

The DragController is responsible for:
- Detecting drag start conditions
- Tracking drag state and initial positions
- Updating object positions during drag
- Finalizing or canceling drag operations
- Supporting multi-object dragging

Architecture:
- Maintains drag state independently
- Works with any canvas coordinate system
- Supports undo/redo through position history
- Decoupled from selection (receives objects to drag)
"""

from typing import List, Optional, Tuple, Dict, Callable
from shypn.netobjs import PetriNetObject


class DragController:
    """Handles drag-and-drop operations for canvas objects.
    
    This controller manages the complete lifecycle of dragging objects:
    1. start_drag() - Initialize drag with objects and starting position
    2. update_drag() - Update positions as mouse moves
    3. end_drag() - Finalize positions on mouse release
    4. cancel_drag() - Restore original positions (ESC key)
    
    Features:
    - Multi-object dragging (all selected objects move together)
    - Coordinate transformation support (screen → world)
    - Position history for undo support
    - Grid snapping support (optional)
    - Drag constraints (optional, e.g., horizontal/vertical only)
    
    Usage:
        drag_ctrl = DragController()
        
        # On mouse down
        if drag_ctrl.start_drag(selected_objects, event.x, event.y):
            # Drag started
            pass
        
        # On mouse move
        if drag_ctrl.is_dragging():
            drag_ctrl.update_drag(event.x, event.y, canvas)
            widget.queue_draw()
        
        # On mouse up
        if drag_ctrl.is_dragging():
            drag_ctrl.end_drag()
    """
    
    def __init__(self):
        """Initialize the drag controller with empty state."""
        # Drag state
        self._dragging = False
        self._drag_objects: List[PetriNetObject] = []
        
        # Starting position (screen coordinates)
        self._start_screen_x = 0.0
        self._start_screen_y = 0.0
        
        # Initial world positions before drag started
        self._initial_positions: Dict[int, Tuple[float, float]] = {}
        
        # Drag configuration
        self._snap_to_grid = False
        self._grid_spacing = 10.0
        self._constrain_axis: Optional[str] = None  # None, 'horizontal', 'vertical'
        
        # Callbacks
        self._on_drag_start: Optional[Callable[[], None]] = None
        self._on_drag_update: Optional[Callable[[], None]] = None
        self._on_drag_end: Optional[Callable[[], None]] = None
        self._on_drag_cancel: Optional[Callable[[], None]] = None
    
    # ============================================================================
    # Drag Lifecycle
    # ============================================================================
    
    def start_drag(self, objects: List[PetriNetObject], 
                   screen_x: float, screen_y: float) -> bool:
        """Start dragging a set of objects.
        
        Args:
            objects: List of objects to drag (typically selected objects)
            screen_x: Starting X coordinate in screen space
            screen_y: Starting Y coordinate in screen space
        
        Returns:
            True if drag started successfully, False if no objects to drag
        """
        if not objects:
            return False
        
        print(f"DEBUG DragController.start_drag: Received {len(objects)} objects, IDs={[id(o) for o in objects]}")
        
        # Store drag state
        self._dragging = True
        self._drag_objects = objects.copy()  # Make a copy to avoid external changes
        self._start_screen_x = screen_x
        self._start_screen_y = screen_y
        
        # Store initial world positions for each object
        self._initial_positions.clear()
        for obj in self._drag_objects:
            self._initial_positions[id(obj)] = (obj.x, obj.y)
        
        print(f"DEBUG DragController.start_drag: Stored {len(self._initial_positions)} initial positions")
        print(f"DEBUG DragController.start_drag: Position IDs={list(self._initial_positions.keys())}")
        
        # Notify callback
        if self._on_drag_start:
            self._on_drag_start()
        
        return True
    
    def update_drag(self, screen_x: float, screen_y: float, 
                   canvas, snap_to_grid: bool = False) -> bool:
        """Update object positions during drag.
        
        Args:
            screen_x: Current X coordinate in screen space
            screen_y: Current Y coordinate in screen space
            canvas: Canvas object with screen_to_world() method
            snap_to_grid: If True, snap positions to grid
        
        Returns:
            True if positions were updated, False if not dragging
        """
        if not self._dragging:
            return False
        
        # Convert screen coordinates to world coordinates
        start_world_x, start_world_y = canvas.screen_to_world(
            self._start_screen_x, self._start_screen_y
        )
        current_world_x, current_world_y = canvas.screen_to_world(
            screen_x, screen_y
        )
        
        # Calculate delta in world coordinates
        delta_x = current_world_x - start_world_x
        delta_y = current_world_y - start_world_y
        
        # Apply axis constraints if set
        if self._constrain_axis == 'horizontal':
            delta_y = 0
        elif self._constrain_axis == 'vertical':
            delta_x = 0
        
        # Update all dragged objects
        for obj in self._drag_objects:
            obj_id = id(obj)
            if obj_id not in self._initial_positions:
                # This should never happen - it means the object list changed during drag
                print(f"WARNING: Object {obj.name if hasattr(obj, 'name') else obj} (ID: {obj_id}) not in initial positions!")
                print(f"  Initial positions keys: {list(self._initial_positions.keys())}")
                print(f"  Drag objects: {[id(o) for o in self._drag_objects]}")
                # Skip this object to prevent crash
                continue
            
            initial_x, initial_y = self._initial_positions[obj_id]
            new_x = initial_x + delta_x
            new_y = initial_y + delta_y
            
            # Apply grid snapping if enabled
            if snap_to_grid or self._snap_to_grid:
                new_x = self._snap_to_grid_coord(new_x)
                new_y = self._snap_to_grid_coord(new_y)
            
            # Update object position
            obj.x = new_x
            obj.y = new_y
        
        # Notify callback
        if self._on_drag_update:
            self._on_drag_update()
        
        return True
    
    def end_drag(self) -> bool:
        """Finalize drag operation.
        
        This completes the drag, leaving objects at their current positions.
        
        Returns:
            True if drag was ended, False if not dragging
        """
        if not self._dragging:
            return False
        
        # Notify callback before clearing state
        if self._on_drag_end:
            self._on_drag_end()
        
        # Clear drag state
        self._clear_state()
        
        return True
    
    def cancel_drag(self) -> bool:
        """Cancel drag operation and restore original positions.
        
        This is useful when user presses ESC or right-clicks during drag.
        
        Returns:
            True if drag was canceled, False if not dragging
        """
        if not self._dragging:
            return False
        
        # Restore all objects to initial positions
        for obj in self._drag_objects:
            if id(obj) in self._initial_positions:
                initial_x, initial_y = self._initial_positions[id(obj)]
                obj.x = initial_x
                obj.y = initial_y
        
        # Notify callback before clearing state
        if self._on_drag_cancel:
            self._on_drag_cancel()
        
        # Clear drag state
        self._clear_state()
        
        return True
    
    def _clear_state(self):
        """Clear internal drag state."""
        self._dragging = False
        self._drag_objects = []
        self._initial_positions.clear()
        self._constrain_axis = None
    
    # ============================================================================
    # State Queries
    # ============================================================================
    
    def is_dragging(self) -> bool:
        """Check if currently dragging objects.
        
        Returns:
            True if drag is active
        """
        return self._dragging
    
    def get_dragged_objects(self) -> List[PetriNetObject]:
        """Get list of objects currently being dragged.
        
        Returns:
            List of objects, or empty list if not dragging
        """
        return self._drag_objects.copy()
    
    def get_drag_delta(self, canvas) -> Optional[Tuple[float, float]]:
        """Get current drag delta in world coordinates.
        
        Args:
            canvas: Canvas object with screen_to_world() method
        
        Returns:
            (delta_x, delta_y) tuple, or None if not dragging
        """
        if not self._dragging:
            return None
        
        # This would need current mouse position - not stored
        # For now, calculate from first object
        if self._drag_objects:
            obj = self._drag_objects[0]
            initial_x, initial_y = self._initial_positions[id(obj)]
            return (obj.x - initial_x, obj.y - initial_y)
        
        return None
    
    def get_initial_positions(self) -> Dict[int, Tuple[float, float]]:
        """Get initial positions of dragged objects (for undo support).
        
        Returns:
            Dictionary mapping object id() to (x, y) tuples
        """
        return self._initial_positions.copy()
    
    # ============================================================================
    # Configuration
    # ============================================================================
    
    def set_snap_to_grid(self, enabled: bool, grid_spacing: float = 10.0):
        """Enable or disable grid snapping during drag.
        
        Args:
            enabled: True to enable snapping
            grid_spacing: Grid spacing in world units (default 10.0)
        """
        self._snap_to_grid = enabled
        self._grid_spacing = grid_spacing
    
    def set_axis_constraint(self, axis: Optional[str]):
        """Constrain drag to a specific axis.
        
        Args:
            axis: 'horizontal', 'vertical', or None for no constraint
        """
        if axis in ['horizontal', 'vertical', None]:
            self._constrain_axis = axis
        else:
            raise ValueError(f"Invalid axis constraint: {axis}")
    
    def _snap_to_grid_coord(self, value: float) -> float:
        """Snap a coordinate value to grid.
        
        Args:
            value: Coordinate value in world units
        
        Returns:
            Snapped value
        """
        return round(value / self._grid_spacing) * self._grid_spacing
    
    # ============================================================================
    # Callbacks
    # ============================================================================
    
    def set_on_drag_start(self, callback: Callable[[], None]):
        """Set callback for drag start event.
        
        Args:
            callback: Function to call when drag starts
        """
        self._on_drag_start = callback
    
    def set_on_drag_update(self, callback: Callable[[], None]):
        """Set callback for drag update event.
        
        Args:
            callback: Function to call when drag updates (each mouse move)
        """
        self._on_drag_update = callback
    
    def set_on_drag_end(self, callback: Callable[[], None]):
        """Set callback for drag end event.
        
        Args:
            callback: Function to call when drag ends successfully
        """
        self._on_drag_end = callback
    
    def set_on_drag_cancel(self, callback: Callable[[], None]):
        """Set callback for drag cancel event.
        
        Args:
            callback: Function to call when drag is canceled
        """
        self._on_drag_cancel = callback
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def get_drag_info(self) -> Dict:
        """Get comprehensive drag state information (for debugging/logging).
        
        Returns:
            Dictionary with drag state details
        """
        return {
            'is_dragging': self._dragging,
            'object_count': len(self._drag_objects),
            'start_position': (self._start_screen_x, self._start_screen_y),
            'snap_to_grid': self._snap_to_grid,
            'grid_spacing': self._grid_spacing,
            'axis_constraint': self._constrain_axis,
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        if self._dragging:
            return f"<DragController dragging={len(self._drag_objects)} objects>"
        return "<DragController idle>"
