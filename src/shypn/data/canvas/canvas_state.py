"""Canvas State Management.

This module manages the viewport and document state for the canvas.
It separates state concerns from business logic and rendering.

Components:
- ViewportState: Manages zoom, pan, grid, and coordinate transformations
- DocumentState: Manages document metadata (filename, modified flag, etc.)
"""

import math
from datetime import datetime
from typing import Tuple, Optional


class ViewportState:
    """Manages viewport state including zoom, pan, grid, and coordinate transformations.
    
    This class handles:
    - Zoom level (0.3x to 3.0x range)
    - Pan offset (viewport translation)
    - Grid system with adaptive spacing
    - Screen ↔ World coordinate transformations
    
    The viewport state is independent of the document content, making it
    easy to persist and restore view settings.
    """
    
    # Zoom configuration
    MIN_ZOOM = 0.3   # 30% minimum
    MAX_ZOOM = 3.0   # 300% maximum
    DEFAULT_ZOOM = 1.0
    ZOOM_STEP = 0.1  # 10% per step
    
    # Grid configuration
    BASE_GRID_SPACING = 50  # Base spacing at 1.0x zoom (in world units)
    GRID_LEVELS = [10, 25, 50, 100, 200]  # Available grid spacings
    
    def __init__(self, width: int = 800, height: int = 600):
        """Initialize viewport state.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        # Viewport dimensions
        self.width = width
        self.height = height
        
        # Zoom and pan
        self._zoom = self.DEFAULT_ZOOM
        self._pan_x = 0.0
        self._pan_y = 0.0
        
        # Grid settings
        self.grid_visible = True
        self._grid_spacing = self.BASE_GRID_SPACING
        
    @property
    def zoom(self) -> float:
        """Current zoom level."""
        return self._zoom
    
    @zoom.setter
    def zoom(self, value: float):
        """Set zoom level (clamped to valid range)."""
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, value))
        self._update_grid_spacing()
    
    @property
    def pan_x(self) -> float:
        """Horizontal pan offset in world coordinates."""
        return self._pan_x
    
    @pan_x.setter
    def pan_x(self, value: float):
        """Set horizontal pan offset."""
        self._pan_x = value
    
    @property
    def pan_y(self) -> float:
        """Vertical pan offset in world coordinates."""
        return self._pan_y
    
    @pan_y.setter
    def pan_y(self, value: float):
        """Set vertical pan offset."""
        self._pan_y = value
    
    @property
    def grid_spacing(self) -> float:
        """Current grid spacing in world units."""
        return self._grid_spacing
    
    def _update_grid_spacing(self):
        """Update grid spacing based on zoom level for optimal visibility."""
        # Calculate effective spacing after zoom
        effective_spacing = self.BASE_GRID_SPACING * self._zoom
        
        # Find the best grid level (between 30-100px on screen)
        if effective_spacing < 30:
            # Zoom out: use larger spacing
            for spacing in sorted(self.GRID_LEVELS, reverse=True):
                if spacing * self._zoom >= 30:
                    self._grid_spacing = spacing
                    return
            self._grid_spacing = self.GRID_LEVELS[-1]  # Largest
        elif effective_spacing > 100:
            # Zoom in: use smaller spacing
            for spacing in self.GRID_LEVELS:
                if spacing * self._zoom <= 100:
                    self._grid_spacing = spacing
                    return
            self._grid_spacing = self.GRID_LEVELS[0]  # Smallest
        else:
            # Good range: use base spacing
            self._grid_spacing = self.BASE_GRID_SPACING
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: X coordinate in screen space (pixels)
            screen_y: Y coordinate in screen space (pixels)
            
        Returns:
            (world_x, world_y) tuple in world coordinates
        """
        world_x = (screen_x / self._zoom) - self._pan_x
        world_y = (screen_y / self._zoom) - self._pan_y
        return (world_x, world_y)
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates.
        
        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space
            
        Returns:
            (screen_x, screen_y) tuple in screen coordinates (pixels)
        """
        screen_x = (world_x + self._pan_x) * self._zoom
        screen_y = (world_y + self._pan_y) * self._zoom
        return (screen_x, screen_y)
    
    def zoom_at_point(self, new_zoom: float, screen_x: float, screen_y: float):
        """Zoom while keeping a screen point stationary (pointer-centered zoom).
        
        Args:
            new_zoom: Target zoom level
            screen_x: X coordinate of the zoom center (screen space)
            screen_y: Y coordinate of the zoom center (screen space)
        """
        # Get world coordinates of the point before zoom
        world_x, world_y = self.screen_to_world(screen_x, screen_y)
        
        # Update zoom
        old_zoom = self._zoom
        self.zoom = new_zoom
        
        # Adjust pan to keep world point at same screen position
        self._pan_x = (screen_x / self._zoom) - world_x
        self._pan_y = (screen_y / self._zoom) - world_y
    
    def pan(self, dx: float, dy: float):
        """Pan the viewport by delta in world coordinates.
        
        Args:
            dx: Horizontal delta in world coordinates
            dy: Vertical delta in world coordinates
        """
        self._pan_x += dx
        self._pan_y += dy
    
    def pan_screen(self, dx_screen: float, dy_screen: float):
        """Pan the viewport by delta in screen coordinates.
        
        Args:
            dx_screen: Horizontal delta in screen pixels
            dy_screen: Vertical delta in screen pixels
        """
        dx_world = dx_screen / self._zoom
        dy_world = dy_screen / self._zoom
        self.pan(dx_world, dy_world)
    
    def resize(self, width: int, height: int):
        """Update viewport dimensions.
        
        Args:
            width: New canvas width in pixels
            height: New canvas height in pixels
        """
        self.width = width
        self.height = height
    
    def reset(self):
        """Reset viewport to default state."""
        self._zoom = self.DEFAULT_ZOOM
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._update_grid_spacing()


class DocumentState:
    """Manages document metadata and state.
    
    This class tracks:
    - Document filename and path
    - Modified flag (unsaved changes)
    - Creation and modification timestamps
    - Document properties
    
    This is separate from the document content (DocumentModel) and viewport (ViewportState).
    """
    
    def __init__(self, filename: Optional[str] = None):
        """Initialize document state.
        
        Args:
            filename: Initial filename/path, or None for new unsaved document
        """
        self.filename = filename
        self.filepath = None  # Full path when saved
        self._modified = False
        self.created_at = datetime.now()
        self.modified_at = self.created_at
        
        # Document properties
        self.title = filename or "Untitled"
        self.author = ""
        self.description = ""
        self.version = "1.0"
    
    @property
    def modified(self) -> bool:
        """Whether document has unsaved changes."""
        return self._modified
    
    @modified.setter
    def modified(self, value: bool):
        """Set modified flag and update timestamp if marking as modified."""
        self._modified = value
        if value:
            self.modified_at = datetime.now()
    
    @property
    def is_saved(self) -> bool:
        """Whether document has been saved (has a filepath)."""
        return self.filepath is not None
    
    @property
    def display_name(self) -> str:
        """Display name for UI (filename or 'Untitled')."""
        if self.filename:
            return self.filename
        return "Untitled"
    
    def mark_saved(self, filepath: str):
        """Mark document as saved to a file.
        
        Args:
            filepath: Full path where document was saved
        """
        self.filepath = filepath
        self.filename = filepath.split('/')[-1]  # Extract filename
        self._modified = False
    
    def mark_modified(self):
        """Mark document as modified (has unsaved changes)."""
        self.modified = True
    
    def reset(self, filename: Optional[str] = None):
        """Reset to initial state for new document.
        
        Args:
            filename: New filename, or None for unsaved document
        """
        self.filename = filename
        self.filepath = None
        self._modified = False
        self.created_at = datetime.now()
        self.modified_at = self.created_at
        self.title = filename or "Untitled"
