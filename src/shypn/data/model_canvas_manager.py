#!/usr/bin/env python3
"""Model Canvas Manager.

This module manages the canvas properties, transformations, and behaviors
for the Petri Net model editor. It handles:
- Grid system with adaptive spacing based on zoom level
- Zoom operations (pointer-centered)
- Pan operations (viewport translation)
- Coordinate transformations (screen ↔ world)
- Rendering pipeline for grid and model elements
- Document metadata and state validation

The manager maintains the model state separately from GTK widgets,
making it easier to test and maintain.
"""
import math
from datetime import datetime


class ModelCanvasManager:
    """Manages canvas properties, transformations, and rendering for Petri Net models."""
    
    # Zoom configuration
    MIN_ZOOM = 0.1
    MAX_ZOOM = 10.0
    ZOOM_STEP = 1.1  # Multiplicative zoom factor (10% per step)
    
    # Grid configuration
    # At 100% zoom (1.0), grid should be ~5mm
    # Assuming 96 DPI: 5mm = 5/25.4 inches = 0.1969 inches = 18.9 pixels ≈ 20 pixels
    BASE_GRID_SPACING = 20  # Base grid spacing at zoom=1.0 (~5mm on 96 DPI screen)
    GRID_SUBDIVISION_LEVELS = [1, 2, 5, 10]  # Grid adapts at these zoom thresholds
    GRID_STYLE_LINE = 'line'  # Standard grid lines
    GRID_STYLE_DOT = 'dot'    # Dots at intersections
    GRID_STYLE_CROSS = 'cross'  # Small crosses at intersections
    
    def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
        """Initialize the canvas manager.
        
        Args:
            canvas_width: Logical canvas width in world coordinates.
            canvas_height: Logical canvas height in world coordinates.
            filename: Base filename without extension (default: "default").
        """
        # Canvas logical size (world coordinates)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Document metadata
        self.filename = filename  # Base filename without .shy extension
        self.modified = False  # Document modified flag
        self.created_at = datetime.now()
        self.modified_at = None
        
        # Viewport properties
        self.zoom = 1.0  # Current zoom level (1.0 = 100%)
        # Initialize pan to center the canvas (updated when viewport size is known)
        self.pan_x = 0.0  # Pan offset X (in world coordinates)
        self.pan_y = 0.0  # Pan offset Y (in world coordinates)
        self._initial_pan_set = False  # Flag to center on first draw
        
        # Viewport size (screen coordinates) - updated when widget is allocated
        self.viewport_width = 800
        self.viewport_height = 600
        
        # Pointer position (for pointer-centered zoom)
        self.pointer_x = 0
        self.pointer_y = 0
        
        # Grid style
        self.grid_style = self.GRID_STYLE_LINE  # Default to line grid
        
        # Dirty flag for redraw optimization
        self._needs_redraw = True
    
    # ==================== Coordinate Transformations ====================
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world (model) coordinates.
        
        Args:
            screen_x: X coordinate in screen space (pixels).
            screen_y: Y coordinate in screen space (pixels).
            
        Returns:
            tuple: (world_x, world_y) in model coordinate space.
        """
        world_x = (screen_x / self.zoom) + self.pan_x
        world_y = (screen_y / self.zoom) + self.pan_y
        return world_x, world_y
    
    def world_to_screen(self, world_x, world_y):
        """Convert world (model) coordinates to screen coordinates.
        
        Args:
            world_x: X coordinate in world space.
            world_y: Y coordinate in world space.
            
        Returns:
            tuple: (screen_x, screen_y) in screen coordinate space (pixels).
        """
        screen_x = (world_x - self.pan_x) * self.zoom
        screen_y = (world_y - self.pan_y) * self.zoom
        return screen_x, screen_y
    
    # ==================== Zoom Operations ====================
    
    def zoom_in(self, center_x=None, center_y=None):
        """Zoom in by one step, centered at the given point.
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        self.zoom_by_factor(self.ZOOM_STEP, center_x, center_y)
    
    def zoom_out(self, center_x=None, center_y=None):
        """Zoom out by one step, centered at the given point.
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        self.zoom_by_factor(1.0 / self.ZOOM_STEP, center_x, center_y)
    
    def zoom_by_factor(self, factor, center_x=None, center_y=None):
        """Zoom by a given factor, centered at a point.
        
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
        world_x, world_y = self.screen_to_world(center_x, center_y)
        
        # Apply zoom with bounds
        new_zoom = self.zoom * factor
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        
        # Calculate new pan to keep zoom center at same screen position
        # After zoom, we want screen_to_world(center_x, center_y) to still be (world_x, world_y)
        # (center_x / new_zoom) + new_pan_x = world_x
        # new_pan_x = world_x - (center_x / new_zoom)
        self.pan_x = world_x - (center_x / new_zoom)
        self.pan_y = world_y - (center_y / new_zoom)
        
        self.zoom = new_zoom
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
    
    # ==================== Pan Operations ====================
    
    def pan(self, dx, dy):
        """Pan the viewport by a delta in screen coordinates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = pan right).
            dy: Pan delta Y in screen pixels (positive = pan down).
        """
        # Convert screen delta to world delta
        world_dx = dx / self.zoom
        world_dy = dy / self.zoom
        
        # Update pan (note: screen drag right = pan left in world coords)
        self.pan_x -= world_dx
        self.pan_y -= world_dy
        
        self._needs_redraw = True
    
    def pan_to(self, world_x, world_y):
        """Pan so that the given world coordinate is at viewport center.
        
        Args:
            world_x: Target world X coordinate.
            world_y: Target world Y coordinate.
        """
        self.pan_x = world_x - (self.viewport_width / 2) / self.zoom
        self.pan_y = world_y - (self.viewport_height / 2) / self.zoom
        self._needs_redraw = True
    
    # ==================== Grid Rendering ====================
    
    def get_grid_spacing(self):
        """Get adaptive grid spacing based on current zoom level.
        
        Returns:
            float: Grid spacing in world coordinates.
        """
        # Adapt grid spacing based on zoom to prevent too dense or too sparse grids
        base_spacing = self.BASE_GRID_SPACING
        
        # Find appropriate subdivision level - use smallest spacing that gives at least 10px on screen
        # When zoomed out, we want larger spacing to avoid clutter
        # When zoomed in, we want smaller spacing (subdivisions) for precision
        for level in self.GRID_SUBDIVISION_LEVELS:  # [1, 2, 5, 10] - ascending
            spacing = base_spacing * level
            screen_spacing = spacing * self.zoom
            # Use this spacing if screen spacing is at least 10 pixels
            # This ensures grid lines are never too close together
            if screen_spacing >= 10:
                return spacing
        
        # Fallback to base spacing (shouldn't reach here with proper levels)
        return base_spacing
    
    def get_visible_bounds(self):
        """Calculate the visible area in world coordinates.
        
        Returns:
            tuple: (min_x, min_y, max_x, max_y) in world coordinates.
        """
        min_x = self.pan_x
        min_y = self.pan_y
        max_x = self.pan_x + (self.viewport_width / self.zoom)
        max_y = self.pan_y + (self.viewport_height / self.zoom)
        return min_x, min_y, max_x, max_y
    
    def draw_grid(self, cr):
        """Draw the grid pattern on the cairo context.
        
        Args:
            cr: Cairo context to draw on.
        """
        grid_spacing = self.get_grid_spacing()
        min_x, min_y, max_x, max_y = self.get_visible_bounds()
        
        # Calculate grid positions in world coordinates
        start_x = math.floor(min_x / grid_spacing) * grid_spacing
        start_y = math.floor(min_y / grid_spacing) * grid_spacing
        
        # Set grid appearance
        cr.set_source_rgba(0.7, 0.7, 0.7, 0.6)  # Medium gray, semi-transparent
        
        if self.grid_style == self.GRID_STYLE_LINE:
            # Standard line grid
            cr.set_line_width(1.0 / self.zoom)  # Keep line width constant in screen space
            
            # Draw vertical grid lines
            x = start_x
            while x <= max_x:
                screen_x, _ = self.world_to_screen(x, 0)
                cr.move_to(screen_x, 0)
                cr.line_to(screen_x, self.viewport_height)
                x += grid_spacing
            
            # Draw horizontal grid lines
            y = start_y
            while y <= max_y:
                _, screen_y = self.world_to_screen(0, y)
                cr.move_to(0, screen_y)
                cr.line_to(self.viewport_width, screen_y)
                y += grid_spacing
            
            cr.stroke()
            
        elif self.grid_style == self.GRID_STYLE_DOT:
            # Dot grid - draw small circles at intersections
            dot_radius = 1.5 / self.zoom  # Keep dot size constant in screen space
            
            y = start_y
            while y <= max_y:
                x = start_x
                while x <= max_x:
                    screen_x, screen_y = self.world_to_screen(x, y)
                    cr.arc(screen_x, screen_y, dot_radius, 0, 2 * math.pi)
                    cr.fill()
                    x += grid_spacing
                y += grid_spacing
                
        elif self.grid_style == self.GRID_STYLE_CROSS:
            # Cross-hair grid - draw small + at intersections
            cross_size = 3.0 / self.zoom  # Keep cross size constant in screen space
            cr.set_line_width(1.0 / self.zoom)
            
            y = start_y
            while y <= max_y:
                x = start_x
                while x <= max_x:
                    screen_x, screen_y = self.world_to_screen(x, y)
                    # Horizontal line of cross
                    cr.move_to(screen_x - cross_size, screen_y)
                    cr.line_to(screen_x + cross_size, screen_y)
                    # Vertical line of cross
                    cr.move_to(screen_x, screen_y - cross_size)
                    cr.line_to(screen_x, screen_y + cross_size)
                    x += grid_spacing
                y += grid_spacing
            
            cr.stroke()
    
    # ==================== State Management ====================
    
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
    
    def set_grid_style(self, style):
        """Set the grid rendering style.
        
        Args:
            style: Grid style ('line', 'dot', or 'cross').
        """
        if style in [self.GRID_STYLE_LINE, self.GRID_STYLE_DOT, self.GRID_STYLE_CROSS]:
            self.grid_style = style
            self._needs_redraw = True
    
    def set_pointer_position(self, x, y):
        """Update current pointer position for pointer-centered zoom.
        
        Args:
            x: Pointer X coordinate in screen space.
            y: Pointer Y coordinate in screen space.
        """
        self.pointer_x = x
        self.pointer_y = y
    
    def needs_redraw(self):
        """Check if canvas needs redrawing.
        
        Returns:
            bool: True if redraw is needed.
        """
        return self._needs_redraw
    
    def mark_clean(self):
        """Mark canvas as clean (drawn)."""
        self._needs_redraw = False
    
    def mark_dirty(self):
        """Mark canvas as dirty (needs redraw)."""
        self._needs_redraw = True
    
    # ==================== Info Methods ====================
    
    def get_zoom_percentage(self):
        """Get zoom level as percentage string.
        
        Returns:
            str: Zoom percentage (e.g., "100%").
        """
        return f"{int(self.zoom * 100)}%"
    
    def get_info(self):
        """Get canvas state information for debugging.
        
        Returns:
            dict: Canvas state information.
        """
        return {
            'zoom': self.zoom,
            'zoom_percent': self.get_zoom_percentage(),
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'viewport': (self.viewport_width, self.viewport_height),
            'grid_spacing': self.get_grid_spacing(),
            'visible_bounds': self.get_visible_bounds(),
        }
    
    # ==================== Document Management ====================
    
    def create_new_document(self, filename="default"):
        """Initialize a new document with default state.
        
        Args:
            filename: Base filename without extension.
            
        Returns:
            dict: Validation result with 'valid' bool and 'errors' list.
        """
        # Reset to initial state
        self.filename = filename
        self.modified = False
        self.created_at = datetime.now()
        self.modified_at = None
        
        # Reset zoom and pan to defaults
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._initial_pan_set = False
        
        # Mark for redraw
        self.mark_dirty()
        
        # Validate initial state
        return self.validate_initial_state()
    
    def validate_initial_state(self):
        """Validate the initial state of the document.
        
        Checks:
        - Canvas dimensions are valid (> 0)
        - Zoom is at 100% (1.0)
        - Pan is centered (will be set on first draw)
        - Grid style is valid
        
        Returns:
            dict: {'valid': bool, 'errors': list of error messages}
        """
        errors = []
        
        # Check canvas dimensions
        if self.canvas_width <= 0:
            errors.append(f"Invalid canvas width: {self.canvas_width}")
        if self.canvas_height <= 0:
            errors.append(f"Invalid canvas height: {self.canvas_height}")
        
        # Check zoom is at 100%
        if abs(self.zoom - 1.0) > 0.01:
            errors.append(f"Initial zoom should be 100%, got {self.get_zoom_percentage()}")
        
        # Check zoom is within bounds
        if self.zoom < self.MIN_ZOOM or self.zoom > self.MAX_ZOOM:
            errors.append(f"Zoom out of bounds: {self.zoom} (min: {self.MIN_ZOOM}, max: {self.MAX_ZOOM})")
        
        # Check grid style is valid
        valid_styles = [self.GRID_STYLE_LINE, self.GRID_STYLE_DOT, self.GRID_STYLE_CROSS]
        if self.grid_style not in valid_styles:
            errors.append(f"Invalid grid style: {self.grid_style}")
        
        # Check filename is valid
        if not self.filename or self.filename.strip() == "":
            errors.append("Filename cannot be empty")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_document_state(self):
        """Get the current document state for saving.
        
        Returns:
            dict: Document state including metadata and canvas properties.
        """
        return {
            'filename': self.filename,
            'modified': self.modified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'canvas': {
                'width': self.canvas_width,
                'height': self.canvas_height,
                'zoom': self.zoom,
                'pan_x': self.pan_x,
                'pan_y': self.pan_y,
                'grid_style': self.grid_style,
            },
            'viewport': {
                'width': self.viewport_width,
                'height': self.viewport_height,
            }
        }
    
    def mark_modified(self):
        """Mark document as modified."""
        if not self.modified:
            self.modified = True
            self.modified_at = datetime.now()
            self.mark_dirty()
    
    def set_filename(self, filename):
        """Set the document filename.
        
        Args:
            filename: Base filename without extension.
        """
        if filename != self.filename:
            self.filename = filename
            self.mark_modified()
