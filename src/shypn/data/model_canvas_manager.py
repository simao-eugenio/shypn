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
- Petri net object collections (places, transitions, arcs)

The manager maintains the model state separately from GTK widgets,
making it easier to test and maintain.
"""
import math
from datetime import datetime
from shypn.api import Place, Arc, Transition


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
    GRID_MAJOR_EVERY = 5  # Every 5th line is a major line (legacy-compatible)
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
        
        # Tool selection state
        self.current_tool = None  # Currently selected tool ('place', 'transition', 'arc', or None)
        
        # Petri net object collections
        # Creation order: Places and Transitions can be created in any order,
        # but Arcs must come after (they connect P↔T or T↔P)
        self.places = []  # List of Place instances
        self.transitions = []  # List of Transition instances
        self.arcs = []  # List of Arc instances (created last, after P and T)
        
        # ID counters for object naming
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        
        # Dirty flag for redraw optimization
        self._needs_redraw = True
    
    # ==================== Coordinate Transformations ====================
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world (model) coordinates.
        
        Legacy formula: world = screen / zoom - pan
        
        Args:
            screen_x: X coordinate in screen space (pixels).
            screen_y: Y coordinate in screen space (pixels).
            
        Returns:
            tuple: (world_x, world_y) in model coordinate space.
        """
        world_x = (screen_x / self.zoom) - self.pan_x
        world_y = (screen_y / self.zoom) - self.pan_y
        return world_x, world_y
    
    def world_to_screen(self, world_x, world_y):
        """Convert world (model) coordinates to screen coordinates.
        
        Legacy formula: screen = (world + pan) * zoom
        
        Args:
            world_x: X coordinate in world space.
            world_y: Y coordinate in world space.
            
        Returns:
            tuple: (screen_x, screen_y) in screen coordinate space (pixels).
        """
        screen_x = (world_x + self.pan_x) * self.zoom
        screen_y = (world_y + self.pan_y) * self.zoom
        return screen_x, screen_y
    
    # ==================== Tool Management ====================
    
    def set_tool(self, tool_name):
        """Set the currently active tool.
        
        Args:
            tool_name: Tool to activate ('place', 'transition', 'arc') or None to clear.
        """
        self.current_tool = tool_name
    
    def get_tool(self):
        """Get the currently active tool.
        
        Returns:
            str or None: Currently active tool name ('place', 'transition', 'arc') or None.
        """
        return self.current_tool
    
    def clear_tool(self):
        """Clear the current tool selection (return to pan mode)."""
        self.current_tool = None
    
    def is_tool_active(self):
        """Check if any tool is currently active.
        
        Returns:
            bool: True if a tool is active, False if in pan mode.
        """
        return self.current_tool is not None
    
    # ==================== Petri Net Object Management ====================
    
    def add_place(self, x, y, **kwargs):
        """Create and add a Place at the specified position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            **kwargs: Additional Place parameters (radius, label, etc.)
            
        Returns:
            Place: The newly created place instance
        """
        place_id = self._next_place_id
        place_name = f"P{place_id}"
        self._next_place_id += 1
        
        place = Place(x, y, place_id, place_name, **kwargs)
        place.on_changed = self._on_object_changed
        self.places.append(place)
        
        self.mark_modified()
        self.mark_dirty()
        return place
    
    def add_transition(self, x, y, **kwargs):
        """Create and add a Transition at the specified position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            **kwargs: Additional Transition parameters (width, height, label, etc.)
            
        Returns:
            Transition: The newly created transition instance
        """
        transition_id = self._next_transition_id
        transition_name = f"T{transition_id}"
        self._next_transition_id += 1
        
        transition = Transition(x, y, transition_id, transition_name, **kwargs)
        transition.on_changed = self._on_object_changed
        self.transitions.append(transition)
        
        self.mark_modified()
        self.mark_dirty()
        return transition
    
    def add_arc(self, source, target, **kwargs):
        """Create and add an Arc between two objects.
        
        Args:
            source: Source object instance (Place or Transition)
            target: Target object instance (Place or Transition)
            **kwargs: Additional Arc parameters (weight, etc.)
            
        Returns:
            Arc: The newly created arc instance
        """
        arc_id = self._next_arc_id
        arc_name = f"A{arc_id}"
        self._next_arc_id += 1
        
        arc = Arc(source, target, arc_id, arc_name, **kwargs)
        arc.on_changed = self._on_object_changed
        self.arcs.append(arc)
        
        self.mark_modified()
        self.mark_dirty()
        return arc
    
    def remove_place(self, place):
        """Remove a place from the model.
        
        Also removes all arcs connected to this place.
        
        Args:
            place: Place instance to remove
        """
        if place in self.places:
            # Remove connected arcs
            self.arcs = [arc for arc in self.arcs 
                        if arc.source != place and arc.target != place]
            
            self.places.remove(place)
            self.mark_modified()
            self.mark_dirty()
    
    def remove_transition(self, transition):
        """Remove a transition from the model.
        
        Also removes all arcs connected to this transition.
        
        Args:
            transition: Transition instance to remove
        """
        if transition in self.transitions:
            # Remove connected arcs
            self.arcs = [arc for arc in self.arcs 
                        if arc.source != transition and arc.target != transition]
            
            self.transitions.remove(transition)
            self.mark_modified()
            self.mark_dirty()
    
    def remove_arc(self, arc):
        """Remove an arc from the model.
        
        Args:
            arc: Arc instance to remove
        """
        if arc in self.arcs:
            self.arcs.remove(arc)
            self.mark_modified()
            self.mark_dirty()
    
    def get_all_objects(self):
        """Get all Petri net objects in rendering order.
        
        Returns:
            list: All objects in rendering order (arcs behind, then P and T on top)
        """
        # Rendering order: Arcs (behind) → Places and Transitions (on top)
        # Arcs render first so they appear behind the nodes
        # Places and transitions render after (order between P/T doesn't matter)
        return list(self.arcs) + list(self.places) + list(self.transitions)
    
    def find_object_at_position(self, x, y):
        """Find the topmost object at the given world position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            
        Returns:
            Place, Transition, or None: The object at the position, or None
        """
        # Check in reverse rendering order (top to bottom)
        for transition in reversed(self.transitions):
            if transition.contains_point(x, y):
                return transition
        
        for place in reversed(self.places):
            if place.contains_point(x, y):
                return place
        
        # Arcs are harder to click, so they're checked last
        # (and we don't implement arc clicking yet)
        
        return None
    
    def clear_all_objects(self):
        """Remove all Petri net objects from the model."""
        self.places.clear()
        self.transitions.clear()
        self.arcs.clear()
        
        # Reset ID counters
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        
        self.mark_modified()
        self.mark_dirty()
    
    def _on_object_changed(self):
        """Callback when an object's properties change."""
        self.mark_modified()
        self.mark_dirty()
    
    def create_test_objects(self):
        """Create test objects for debugging rendering.
        
        Creates a simple Petri net: P1 -> T1 -> P2
        """
        # Create places
        p1 = self.add_place(-100, 0, label="P1")
        p2 = self.add_place(100, 0, label="P2")
        p1.set_tokens(2)
        
        # Create transition
        t1 = self.add_transition(0, 0, label="T1")
        
        # Create arcs
        a1 = self.add_arc(p1, t1, weight=1)
        a2 = self.add_arc(t1, p2, weight=1)
        
        print(f"Created test network: {p1.name} → {t1.name} → {p2.name}")
        print(f"Total objects: {len(self.places)} places, {len(self.transitions)} transitions, {len(self.arcs)} arcs")
    
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
    
    def pan_relative(self, dx, dy):
        """Pan the viewport by incremental deltas (for drag updates).
        
        This is an alias for pan() but with clearer intent for incremental updates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = pan right).
            dy: Pan delta Y in screen pixels (positive = pan down).
        """
        self.pan(dx, dy)
    
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
        
        Now draws in world space (inside Cairo transform) so grid scales with zoom.
        Line widths are compensated to maintain constant pixel size.
        Uses major/minor line distinction (every 5th line is major).
        
        Args:
            cr: Cairo context to draw on (with zoom transform already applied).
        """
        grid_spacing = self.get_grid_spacing()
        min_x, min_y, max_x, max_y = self.get_visible_bounds()
        
        # Calculate grid positions in world coordinates
        start_x = math.floor(min_x / grid_spacing) * grid_spacing
        start_y = math.floor(min_y / grid_spacing) * grid_spacing
        
        # Calculate starting indices (for major/minor line determination)
        start_index_x = int(math.floor(min_x / grid_spacing))
        start_index_y = int(math.floor(min_y / grid_spacing))
        
        if self.grid_style == self.GRID_STYLE_LINE:
            # Standard line grid - draw in world coordinates with major/minor distinction
            
            # Draw vertical grid lines
            x = start_x
            index_x = start_index_x
            while x <= max_x:
                # Determine if this is a major line
                is_major = (index_x % self.GRID_MAJOR_EVERY) == 0
                
                if is_major:
                    # Major line: darker color, thicker width
                    cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)  # Darker gray
                    cr.set_line_width(1.0 / self.zoom)
                else:
                    # Minor line: lighter color, thinner width
                    cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)  # Lighter gray
                    cr.set_line_width(0.5 / self.zoom)
                
                cr.move_to(x, min_y)
                cr.line_to(x, max_y)
                cr.stroke()
                
                x += grid_spacing
                index_x += 1
            
            # Draw horizontal grid lines
            y = start_y
            index_y = start_index_y
            while y <= max_y:
                # Determine if this is a major line
                is_major = (index_y % self.GRID_MAJOR_EVERY) == 0
                
                if is_major:
                    # Major line: darker color, thicker width
                    cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)  # Darker gray
                    cr.set_line_width(1.0 / self.zoom)
                else:
                    # Minor line: lighter color, thinner width
                    cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)  # Lighter gray
                    cr.set_line_width(0.5 / self.zoom)
                
                cr.move_to(min_x, y)
                cr.line_to(max_x, y)
                cr.stroke()
                
                y += grid_spacing
                index_y += 1
            
        elif self.grid_style == self.GRID_STYLE_DOT:
            # Dot grid - draw small circles at intersections in world coordinates
            # Major intersections (every 5th line) get larger/darker dots
            
            y = start_y
            index_y = start_index_y
            while y <= max_y:
                x = start_x
                index_x = start_index_x
                while x <= max_x:
                    # Check if this is a major intersection
                    is_major_x = (index_x % self.GRID_MAJOR_EVERY) == 0
                    is_major_y = (index_y % self.GRID_MAJOR_EVERY) == 0
                    is_major = is_major_x and is_major_y
                    
                    if is_major:
                        # Major intersection: larger, darker dot
                        cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)
                        dot_radius = 2.0 / self.zoom
                    else:
                        # Minor intersection: smaller, lighter dot
                        cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)
                        dot_radius = 1.5 / self.zoom
                    
                    cr.arc(x, y, dot_radius, 0, 2 * math.pi)
                    cr.fill()
                    
                    x += grid_spacing
                    index_x += 1
                y += grid_spacing
                index_y += 1
                
        elif self.grid_style == self.GRID_STYLE_CROSS:
            # Cross-hair grid - draw small + at intersections in world coordinates
            # Major intersections (every 5th line) get larger/darker crosses
            
            y = start_y
            index_y = start_index_y
            while y <= max_y:
                x = start_x
                index_x = start_index_x
                while x <= max_x:
                    # Check if this is a major intersection
                    is_major_x = (index_x % self.GRID_MAJOR_EVERY) == 0
                    is_major_y = (index_y % self.GRID_MAJOR_EVERY) == 0
                    is_major = is_major_x and is_major_y
                    
                    if is_major:
                        # Major intersection: larger, darker cross
                        cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)
                        cross_size = 4.0 / self.zoom
                        cr.set_line_width(1.0 / self.zoom)
                    else:
                        # Minor intersection: smaller, lighter cross
                        cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)
                        cross_size = 3.0 / self.zoom
                        cr.set_line_width(0.5 / self.zoom)
                    
                    # Horizontal line of cross
                    cr.move_to(x - cross_size, y)
                    cr.line_to(x + cross_size, y)
                    # Vertical line of cross
                    cr.move_to(x, y - cross_size)
                    cr.line_to(x, y + cross_size)
                    cr.stroke()
                    
                    x += grid_spacing
                    index_x += 1
                y += grid_spacing
                index_y += 1
    
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
