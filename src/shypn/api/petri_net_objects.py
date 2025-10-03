#!/usr/bin/env python3
"""Petri Net Objects - Place, Transition, and Arc rendering and management.

This module provides classes for creating and rendering Petri net objects:
- Place: Circular nodes that hold tokens
- Transition: Rectangular bars that represent events/actions
- Arc: Directed arrows connecting places and transitions

Each object knows how to:
- Render itself using Cairo graphics
- Manage its properties (position, size, color, etc.)
- Trigger redraws when modified
- Provide collision detection for mouse interactions
"""
import math
from typing import Optional, Tuple, List, Callable


class Place:
    """A circular place in a Petri net.
    
    Places represent conditions or states and can contain tokens.
    Rendered as a circle with optional label and token display.
    """
    
    # Default styling
    DEFAULT_RADIUS = 25.0
    DEFAULT_COLOR = (1.0, 1.0, 1.0)  # White fill
    DEFAULT_BORDER_COLOR = (0.0, 0.0, 0.0)  # Black border
    DEFAULT_BORDER_WIDTH = 2.0
    
    def __init__(self, x: float, y: float, id: int, name: str, 
                 radius: float = None, label: str = ""):
        """Initialize a Place.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "P1", "P2", etc. (immutable, system-assigned)
            radius: Circle radius (default: 25.0)
            label: Optional user-editable text label (mutable)
        """
        # Identity properties (immutable - system managed)
        self._id = id
        self._name = name
        
        # Position
        self.x = x
        self.y = y
        self.radius = radius if radius is not None else self.DEFAULT_RADIUS
        
        # User-editable label
        self.label = label
        
        # Styling
        self.fill_color = self.DEFAULT_COLOR
        self.border_color = self.DEFAULT_BORDER_COLOR
        self.border_width = self.DEFAULT_BORDER_WIDTH
        
        # State
        self.tokens = 0  # Number of tokens in this place
        self.selected = False
        
        # Callback for triggering redraws
        self.on_changed: Optional[Callable] = None
    
    @property
    def id(self) -> int:
        """Get the unique identifier (read-only)."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the unique name (read-only)."""
        return self._name
    
    def render(self, cr, transform=None):
        """Render the place using Cairo.
        
        Args:
            cr: Cairo context
            transform: Optional function to transform world coords to screen coords
        """
        # Apply transform if provided
        if transform:
            screen_x, screen_y = transform(self.x, self.y)
            screen_radius = self.radius  # TODO: Scale radius with zoom
        else:
            screen_x, screen_y = self.x, self.y
            screen_radius = self.radius
        
        # Draw filled circle
        cr.arc(screen_x, screen_y, screen_radius, 0, 2 * math.pi)
        cr.set_source_rgb(*self.fill_color)
        cr.fill_preserve()
        
        # Draw border
        cr.set_source_rgb(*self.border_color)
        cr.set_line_width(self.border_width)
        cr.stroke()
        
        # Draw selection highlight if selected
        if self.selected:
            cr.arc(screen_x, screen_y, screen_radius + 3, 0, 2 * math.pi)
            cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)  # Blue highlight
            cr.set_line_width(3)
            cr.stroke()
        
        # Draw tokens if any
        if self.tokens > 0:
            self._render_tokens(cr, screen_x, screen_y, screen_radius)
        
        # Draw label if provided
        if self.label:
            self._render_label(cr, screen_x, screen_y, screen_radius)
    
    def _render_tokens(self, cr, x: float, y: float, radius: float):
        """Render token indicators inside the place.
        
        Args:
            cr: Cairo context
            x, y: Center position (screen coords)
            radius: Circle radius
        """
        token_radius = 4.0
        
        if self.tokens == 1:
            # Single token in center
            cr.arc(x, y, token_radius, 0, 2 * math.pi)
            cr.set_source_rgb(0, 0, 0)
            cr.fill()
        elif self.tokens <= 5:
            # Multiple tokens arranged in circle
            angle_step = (2 * math.pi) / self.tokens
            token_distance = radius * 0.5
            for i in range(self.tokens):
                angle = i * angle_step
                tx = x + token_distance * math.cos(angle)
                ty = y + token_distance * math.sin(angle)
                cr.arc(tx, ty, token_radius, 0, 2 * math.pi)
                cr.set_source_rgb(0, 0, 0)
                cr.fill()
        else:
            # Many tokens: show as text number
            cr.set_source_rgb(0, 0, 0)
            cr.select_font_face("Sans", 0, 1)  # Normal, Bold
            cr.set_font_size(14)
            text = str(self.tokens)
            extents = cr.text_extents(text)
            cr.move_to(x - extents.width / 2, y + extents.height / 2)
            cr.show_text(text)
    
    def _render_label(self, cr, x: float, y: float, radius: float):
        """Render text label below the place.
        
        Args:
            cr: Cairo context
            x, y: Center position (screen coords)
            radius: Circle radius
        """
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 0)  # Normal, Normal
        cr.set_font_size(12)
        extents = cr.text_extents(self.label)
        cr.move_to(x - extents.width / 2, y + radius + 15)
        cr.show_text(self.label)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this place.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            True if point is inside the circle
        """
        dx = x - self.x
        dy = y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= self.radius
    
    def set_position(self, x: float, y: float):
        """Move the place to a new position.
        
        Args:
            x, y: New position (world space)
        """
        self.x = x
        self.y = y
        self._trigger_redraw()
    
    def set_tokens(self, count: int):
        """Set the number of tokens in this place.
        
        Args:
            count: Token count (non-negative)
        """
        self.tokens = max(0, count)
        self._trigger_redraw()
    
    def _trigger_redraw(self):
        """Request a redraw if callback is set."""
        if self.on_changed:
            self.on_changed()


class Transition:
    """A rectangular transition in a Petri net.
    
    Transitions represent events or actions that transform the net state.
    Rendered as a filled black rectangle.
    """
    
    # Default styling
    DEFAULT_WIDTH = 50.0
    DEFAULT_HEIGHT = 8.0
    DEFAULT_COLOR = (0.0, 0.0, 0.0)  # Black fill
    DEFAULT_BORDER_COLOR = (0.0, 0.0, 0.0)  # Black border
    DEFAULT_BORDER_WIDTH = 1.0
    
    def __init__(self, x: float, y: float, id: int, name: str,
                 width: float = None, height: float = None, 
                 label: str = "", horizontal: bool = True):
        """Initialize a Transition.
        
        Args:
            x: X coordinate in world space (center)
            y: Y coordinate in world space (center)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "T1", "T2", etc. (immutable, system-assigned)
            width: Rectangle width (default: 50.0)
            height: Rectangle height (default: 8.0)
            label: Optional user-editable text label (mutable)
            horizontal: True for horizontal bar, False for vertical
        """
        # Identity properties (immutable - system managed)
        self._id = id
        self._name = name
        
        # Position and dimensions
        self.x = x
        self.y = y
        self.width = width if width is not None else self.DEFAULT_WIDTH
        self.height = height if height is not None else self.DEFAULT_HEIGHT
        self.horizontal = horizontal
        
        # User-editable label
        self.label = label
        
        # Styling
        self.fill_color = self.DEFAULT_COLOR
        self.border_color = self.DEFAULT_BORDER_COLOR
        self.border_width = self.DEFAULT_BORDER_WIDTH
        
        # State
        self.selected = False
        self.enabled = True  # Can this transition fire?
        
        # Callback for triggering redraws
        self.on_changed: Optional[Callable] = None
    
    @property
    def id(self) -> int:
        """Get the unique identifier (read-only)."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the unique name (read-only)."""
        return self._name
    
    def render(self, cr, transform=None):
        """Render the transition using Cairo.
        
        Args:
            cr: Cairo context
            transform: Optional function to transform world coords to screen coords
        """
        # Apply transform if provided
        if transform:
            screen_x, screen_y = transform(self.x, self.y)
            screen_width = self.width  # TODO: Scale with zoom
            screen_height = self.height
        else:
            screen_x, screen_y = self.x, self.y
            screen_width = self.width
            screen_height = self.height
        
        # Swap dimensions if vertical
        if not self.horizontal:
            screen_width, screen_height = screen_height, screen_width
        
        # Calculate rectangle corners (center-based)
        half_w = screen_width / 2
        half_h = screen_height / 2
        
        # Draw filled rectangle
        cr.rectangle(screen_x - half_w, screen_y - half_h, screen_width, screen_height)
        cr.set_source_rgb(*self.fill_color)
        cr.fill_preserve()
        
        # Draw border
        cr.set_source_rgb(*self.border_color)
        cr.set_line_width(self.border_width)
        cr.stroke()
        
        # Draw selection highlight if selected
        if self.selected:
            cr.rectangle(screen_x - half_w - 3, screen_y - half_h - 3, 
                        screen_width + 6, screen_height + 6)
            cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)  # Blue highlight
            cr.set_line_width(3)
            cr.stroke()
        
        # Draw label if provided
        if self.label:
            self._render_label(cr, screen_x, screen_y, screen_height, self.horizontal)
    
    def _render_label(self, cr, x: float, y: float, height: float, horizontal: bool):
        """Render text label next to the transition.
        
        Args:
            cr: Cairo context
            x, y: Center position (screen coords)
            height: Rectangle height
            horizontal: Orientation flag
        """
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 0)  # Normal, Normal
        cr.set_font_size(12)
        extents = cr.text_extents(self.label)
        
        if horizontal:
            # Label below horizontal transition
            cr.move_to(x - extents.width / 2, y + height / 2 + 15)
        else:
            # Label to the right of vertical transition
            cr.move_to(x + height / 2 + 5, y + extents.height / 2)
        
        cr.show_text(self.label)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this transition.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            True if point is inside the rectangle
        """
        w = self.width if self.horizontal else self.height
        h = self.height if self.horizontal else self.width
        
        half_w = w / 2
        half_h = h / 2
        
        return (self.x - half_w <= x <= self.x + half_w and
                self.y - half_h <= y <= self.y + half_h)
    
    def set_position(self, x: float, y: float):
        """Move the transition to a new position.
        
        Args:
            x, y: New position (world space)
        """
        self.x = x
        self.y = y
        self._trigger_redraw()
    
    def set_orientation(self, horizontal: bool):
        """Change transition orientation.
        
        Args:
            horizontal: True for horizontal, False for vertical
        """
        self.horizontal = horizontal
        self._trigger_redraw()
    
    def _trigger_redraw(self):
        """Request a redraw if callback is set."""
        if self.on_changed:
            self.on_changed()


class Arc:
    """A directed arc in a Petri net.
    
    Arcs connect places to transitions or transitions to places.
    Rendered as an arrow with optional weight label.
    """
    
    # Default styling
    DEFAULT_COLOR = (0.0, 0.0, 0.0)  # Black
    DEFAULT_WIDTH = 2.0
    ARROW_SIZE = 10.0
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """Initialize an Arc.
        
        Args:
            source: Source object instance (Place or Transition)
            target: Target object instance (Place or Transition)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "A1", "A2", etc. (immutable, system-assigned)
            weight: Arc weight (multiplicity)
        """
        # Identity properties (immutable - system managed)
        self._id = id
        self._name = name
        
        # Connection (references to object instances)
        self.source = source
        self.target = target
        self.weight = weight
        
        # Styling
        self.color = self.DEFAULT_COLOR
        self.width = self.DEFAULT_WIDTH
        
        # State
        self.selected = False
        
        # Control points for curved arcs (optional)
        self.control_points: List[Tuple[float, float]] = []
        
        # Callback for triggering redraws
        self.on_changed: Optional[Callable] = None
    
    @property
    def id(self) -> int:
        """Get the unique identifier (read-only)."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the unique name (read-only)."""
        return self._name
    
    def render(self, cr, transform=None):
        """Render the arc using Cairo.
        
        Args:
            cr: Cairo context
            transform: Optional function to transform world coords to screen coords
        """
        # Get source and target positions
        src_x, src_y = self.source.x, self.source.y
        tgt_x, tgt_y = self.target.x, self.target.y
        
        # Apply transform if provided
        if transform:
            src_x, src_y = transform(src_x, src_y)
            tgt_x, tgt_y = transform(tgt_x, tgt_y)
        
        # Calculate direction vector
        dx = tgt_x - src_x
        dy = tgt_y - src_y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return  # Too short to draw
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Adjust start and end points to touch object boundaries
        start_x, start_y = self._get_boundary_point(self.source, src_x, src_y, dx, dy)
        end_x, end_y = self._get_boundary_point(self.target, tgt_x, tgt_y, -dx, -dy)
        
        # Draw line
        cr.move_to(start_x, start_y)
        cr.line_to(end_x, end_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width)
        cr.stroke()
        
        # Draw arrowhead at target
        self._render_arrowhead(cr, end_x, end_y, dx, dy)
        
        # Draw weight label if > 1
        if self.weight > 1:
            self._render_weight(cr, start_x, start_y, end_x, end_y)
        
        # Draw selection highlight if selected
        if self.selected:
            cr.move_to(start_x, start_y)
            cr.line_to(end_x, end_y)
            cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)
            cr.set_line_width(self.width + 4)
            cr.stroke()
    
    def _get_boundary_point(self, obj, cx: float, cy: float, 
                           dx: float, dy: float) -> Tuple[float, float]:
        """Calculate where arc intersects object boundary.
        
        Args:
            obj: Place or Transition object
            cx, cy: Object center
            dx, dy: Direction vector (normalized)
            
        Returns:
            (x, y) point on object boundary
        """
        if isinstance(obj, Place):
            # Circle boundary
            return (cx + dx * obj.radius, cy + dy * obj.radius)
        elif isinstance(obj, Transition):
            # Rectangle boundary - simplified approximation
            w = obj.width if obj.horizontal else obj.height
            h = obj.height if obj.horizontal else obj.width
            # Use larger dimension for approximation
            dist = max(w, h) / 2
            return (cx + dx * dist, cy + dy * dist)
        else:
            return (cx, cy)
    
    def _render_arrowhead(self, cr, x: float, y: float, dx: float, dy: float):
        """Render arrowhead at the target end.
        
        Args:
            cr: Cairo context
            x, y: Arrow tip position
            dx, dy: Direction vector
        """
        # Calculate arrowhead points
        angle = math.atan2(dy, dx)
        arrow_angle = math.pi / 6  # 30 degrees
        
        # Left wing
        left_x = x - self.ARROW_SIZE * math.cos(angle - arrow_angle)
        left_y = y - self.ARROW_SIZE * math.sin(angle - arrow_angle)
        
        # Right wing
        right_x = x - self.ARROW_SIZE * math.cos(angle + arrow_angle)
        right_y = y - self.ARROW_SIZE * math.sin(angle + arrow_angle)
        
        # Draw filled triangle
        cr.move_to(x, y)
        cr.line_to(left_x, left_y)
        cr.line_to(right_x, right_y)
        cr.close_path()
        cr.set_source_rgb(*self.color)
        cr.fill()
    
    def _render_weight(self, cr, x1: float, y1: float, x2: float, y2: float):
        """Render weight label near the arc midpoint.
        
        Args:
            cr: Cairo context
            x1, y1: Start point
            x2, y2: End point
        """
        # Calculate midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Draw weight as text
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 1)  # Normal, Bold
        cr.set_font_size(11)
        text = str(self.weight)
        extents = cr.text_extents(text)
        
        # Offset slightly from line
        offset = 8
        dx = y2 - y1  # Perpendicular direction
        dy = x1 - x2
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            dx = dx / length * offset
            dy = dy / length * offset
        
        cr.move_to(mid_x + dx - extents.width / 2, mid_y + dy + extents.height / 2)
        cr.show_text(text)
    
    def set_weight(self, weight: int):
        """Set the arc weight.
        
        Args:
            weight: New weight (positive integer)
        """
        self.weight = max(1, weight)
        self._trigger_redraw()
    
    def _trigger_redraw(self):
        """Request a redraw if callback is set."""
        if self.on_changed:
            self.on_changed()


# Note: Factory functions are not provided here.
# Object creation with ID and name assignment should be managed by
# a higher-level manager (e.g., PetriNetManager or ModelCanvasManager)
# that maintains counters and ensures uniqueness of IDs and names.
