"""Viewport controller for canvas view management.

Manages viewport state: zoom, pan, and viewport dimensions.
Implements pointer-centered zoom and infinite canvas with clamping.

This is a stateful controller (first one extracted from god class).
Unlike services (stateless), controllers maintain state between operations.
"""

import json
import os


class ViewportController:
    """Controller for viewport state (zoom, pan, dimensions).
    
    Responsibilities:
    - Zoom operations (in, out, by factor, set absolute)
    - Pan operations (delta, absolute, relative)
    - Viewport bounds clamping (infinite canvas)
    - Viewport size management
    - View state persistence (save/load pan and zoom)
    
    State managed:
    - zoom: Current zoom level (1.0 = 100%)
    - pan_x, pan_y: Pan offset in world coordinates
    - viewport_width, viewport_height: Viewport dimensions in screen pixels
    - pointer_x, pointer_y: Current pointer position (for zoom centering)
    - _initial_pan_set: Flag for first-time centering
    
    Design notes:
    - Uses legacy zoom algorithm (world = screen/zoom - pan)
    - Clamps pan to keep canvas within viewport (infinite canvas feel)
    - Saves view state to file after zoom operations
    """
    
    # Zoom configuration
    MIN_ZOOM = 0.3   # 30% minimum (practical engineering range)
    MAX_ZOOM = 3.0   # 300% maximum (practical engineering range)
    ZOOM_STEP = 1.1  # Multiplicative zoom factor (10% per step)
    
    # Canvas extent for infinite canvas (half-extent in logical units)
    CANVAS_EXTENT = 10000.0  # ±10,000 units = 20,000×20,000 total canvas
    
    def __init__(self, viewport_width=800, viewport_height=600, filename="default"):
        """Initialize viewport controller.
        
        Args:
            viewport_width: Initial viewport width in pixels.
            viewport_height: Initial viewport height in pixels.
            filename: Base filename for view state persistence.
        """
        # Viewport state
        self.zoom = 1.0  # Current zoom level (1.0 = 100%)
        self.pan_x = 0.0  # Pan offset X (in world coordinates)
        self.pan_y = 0.0  # Pan offset Y (in world coordinates)
        self._initial_pan_set = False  # Flag to center on first draw
        
        # Viewport dimensions (screen coordinates)
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        
        # Pointer position (for pointer-centered zoom)
        self.pointer_x = 0
        self.pointer_y = 0
        
        # Filename for persistence
        self.filename = filename
        
        # Dirty flag for redraw tracking
        self._needs_redraw = True
    
    # ==================== Zoom Operations ====================
    
    def zoom_in(self, center_x=None, center_y=None):
        """Zoom in by one step (multiply by ZOOM_STEP).
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        self.zoom_by_factor(self.ZOOM_STEP, center_x, center_y)
    
    def zoom_out(self, center_x=None, center_y=None):
        """Zoom out by one step (divide by ZOOM_STEP).
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        self.zoom_by_factor(1.0 / self.ZOOM_STEP, center_x, center_y)
    
    def zoom_by_factor(self, factor, center_x=None, center_y=None):
        """Zoom by a given factor, centered at a point.
        
        Implements pointer-centered zoom using legacy algorithm:
        - Get world coordinate under cursor before zoom
        - Apply new zoom
        - Adjust pan so world coordinate stays at same screen position
        
        Args:
            factor: Multiplicative zoom factor (e.g., 1.1 = zoom in 10%).
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        # Default to viewport center if no center provided
        if center_x is None:
            center_x = self.viewport_width / 2
        if center_y is None:
            center_y = self.viewport_height / 2
        
        # Get world coordinates of zoom center before zoom
        # Legacy formula: world = screen / zoom - pan
        world_x = (center_x / self.zoom) - self.pan_x
        world_y = (center_y / self.zoom) - self.pan_y
        
        # Apply zoom with bounds
        new_zoom = self.zoom * factor
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        
        # Calculate new pan to keep zoom center at same screen position
        # After zoom, we want: world = screen / new_zoom - new_pan
        # So: new_pan = screen / new_zoom - world
        self.pan_x = (center_x / new_zoom) - world_x
        self.pan_y = (center_y / new_zoom) - world_y
        
        self.zoom = new_zoom
        
        # Clamp pan to maintain infinite canvas bounds
        self.clamp_pan()
        
        # Save view state after zoom operation
        self.save_view_state_to_file()
        
        self._needs_redraw = True
    
    def set_zoom(self, zoom_level, center_x=None, center_y=None):
        """Set absolute zoom level.
        
        Args:
            zoom_level: Target zoom level (clamped to MIN_ZOOM..MAX_ZOOM).
            center_x: X coordinate of zoom center (screen space).
            center_y: Y coordinate of zoom center (screen space).
        """
        zoom_level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom_level))
        factor = zoom_level / self.zoom
        self.zoom_by_factor(factor, center_x, center_y)
    
    def zoom_at_point(self, factor, center_x, center_y):
        """Zoom by a factor at a specific point (alias for zoom_by_factor).
        
        Args:
            factor: Multiplicative zoom factor.
            center_x: X coordinate of zoom center (screen space).
            center_y: Y coordinate of zoom center (screen space).
        """
        self.zoom_by_factor(factor, center_x, center_y)
    
    # ==================== Pan Operations ====================
    
    def pan(self, dx, dy):
        """Pan the viewport by a delta in screen coordinates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = drag right = pan increases).
            dy: Pan delta Y in screen pixels (positive = drag down = pan increases).
        """
        # Convert screen delta to world delta
        world_dx = dx / self.zoom
        world_dy = dy / self.zoom
        
        # Update pan (drag right = pan increases, matching legacy behavior)
        self.pan_x += world_dx
        self.pan_y += world_dy
        
        # Clamp pan to canvas bounds
        self.clamp_pan()
        
        self._needs_redraw = True
    
    def pan_to(self, world_x, world_y):
        """Pan so that the given world coordinate is at viewport center.
        
        Args:
            world_x: Target world X coordinate.
            world_y: Target world Y coordinate.
        """
        self.pan_x = world_x - (self.viewport_width / 2) / self.zoom
        self.pan_y = world_y - (self.viewport_height / 2) / self.zoom
        
        # Clamp pan to canvas bounds
        self.clamp_pan()
        
        self._needs_redraw = True
    
    def pan_relative(self, dx, dy):
        """Pan the viewport by incremental deltas (for drag updates).
        
        This is an alias for pan() but with clearer intent for incremental updates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = pan right).
            dy: Pan delta Y in screen pixels (positive = pan down).
        """
        self.pan(dx, dy)
    
    def clamp_pan(self):
        """Clamp pan to keep canvas bounds within viewport.
        
        Creates infinite canvas feeling while preventing blank space.
        Grid always fills viewport regardless of pan/zoom by clamping
        the pan values to ensure the canvas extent covers the screen.
        
        Canvas extent: ±CANVAS_EXTENT in world space
        Viewport: viewport_width × viewport_height in screen space
        
        The constraint is: canvas bounds must fully cover viewport.
        - Left edge: (-extent + pan) * zoom <= 0  →  pan <= extent
        - Right edge: (extent + pan) * zoom >= width  →  pan >= width/zoom - extent
        """
        extent_x = self.CANVAS_EXTENT
        extent_y = self.CANVAS_EXTENT
        
        # Ensure extent is large enough to cover viewport at current zoom
        min_half_x = (self.viewport_width / self.zoom) / 2.0
        min_half_y = (self.viewport_height / self.zoom) / 2.0
        extent_x = max(extent_x, min_half_x)
        extent_y = max(extent_y, min_half_y)
        
        # Calculate pan limits
        # Grid bounds: [-extent, +extent] in world space
        # Screen bounds: [0, viewport] in screen space
        min_pan_x = (self.viewport_width / self.zoom) - extent_x
        max_pan_x = extent_x
        min_pan_y = (self.viewport_height / self.zoom) - extent_y
        max_pan_y = extent_y
        
        # Clamp pan values
        self.pan_x = max(min_pan_x, min(max_pan_x, self.pan_x))
        self.pan_y = max(min_pan_y, min(max_pan_y, self.pan_y))
    
    # ==================== Viewport Management ====================
    
    def set_viewport_size(self, width, height):
        """Update viewport size when widget is resized.
        
        Args:
            width: New viewport width in pixels.
            height: New viewport height in pixels.
        """
        self.viewport_width = width
        self.viewport_height = height
        
        # On first viewport size update, center the canvas
        if not self._initial_pan_set and width > 0 and height > 0:
            # Center the canvas: pan so that (0,0) world coordinate is at screen center
            self.pan_x = -(width / 2) / self.zoom
            self.pan_y = -(height / 2) / self.zoom
            self._initial_pan_set = True
        
        self._needs_redraw = True
    
    def set_pointer_position(self, x, y):
        """Update current pointer position for pointer-centered zoom.
        
        Args:
            x: Pointer X coordinate in screen space.
            y: Pointer Y coordinate in screen space.
        """
        self.pointer_x = x
        self.pointer_y = y
    
    def get_zoom_percentage(self):
        """Get zoom level as percentage string.
        
        Returns:
            str: Zoom percentage (e.g., "100%").
        """
        return f"{int(self.zoom * 100)}%"
    
    def get_viewport_info(self):
        """Get viewport state information for debugging.
        
        Returns:
            dict: Viewport state information.
        """
        return {
            'zoom': self.zoom,
            'zoom_percent': self.get_zoom_percentage(),
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'viewport': (self.viewport_width, self.viewport_height),
            'pointer': (self.pointer_x, self.pointer_y),
        }
    
    # ==================== View State Persistence ====================
    
    def save_view_state_to_file(self):
        """Save current view state (pan and zoom) to file.
        
        Saves to workspace/.view_state_{filename}.json
        This preserves user's view position across sessions.
        """
        view_state = {
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'zoom': self.zoom,
        }
        
        state_file = f"workspace/.view_state_{self.filename}.json"
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        
        try:
            with open(state_file, 'w') as f:
                json.dump(view_state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save view state: {e}")
    
    def load_view_state_from_file(self):
        """Load view state (pan and zoom) from file.
        
        Returns:
            bool: True if state was loaded successfully, False otherwise.
        """
        state_file = f"workspace/.view_state_{self.filename}.json"
        
        if not os.path.exists(state_file):
            return False
        
        try:
            with open(state_file, 'r') as f:
                view_state = json.load(f)
            
            self.pan_x = view_state.get('pan_x', self.pan_x)
            self.pan_y = view_state.get('pan_y', self.pan_y)
            self.zoom = view_state.get('zoom', self.zoom)
            
            # Clamp loaded values
            self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom))
            self.clamp_pan()
            
            self._needs_redraw = True
            return True
        except Exception as e:
            print(f"Warning: Could not load view state: {e}")
            return False
    
    # ==================== Redraw Management ====================
    
    def needs_redraw(self):
        """Check if viewport needs redrawing.
        
        Returns:
            bool: True if redraw is needed.
        """
        return self._needs_redraw
    
    def mark_clean(self):
        """Mark viewport as clean (drawn)."""
        self._needs_redraw = False
    
    def mark_dirty(self):
        """Mark viewport as dirty (needs redraw)."""
        self._needs_redraw = True
    
    # ==================== Reset ====================
    
    def reset(self):
        """Reset viewport to default state (zoom=1.0, centered)."""
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._initial_pan_set = False
        
        # Re-center if viewport size is known
        if self.viewport_width > 0 and self.viewport_height > 0:
            self.pan_x = -(self.viewport_width / 2) / self.zoom
            self.pan_y = -(self.viewport_height / 2) / self.zoom
            self._initial_pan_set = True
        
        self._needs_redraw = True
