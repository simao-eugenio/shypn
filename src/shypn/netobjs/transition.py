#!/usr/bin/env python3
"""Transition - Rectangular bar in a Petri net.

Transitions represent events or actions that transform the net state.
Rendered as a filled black rectangle.
"""
from shypn.netobjs.petri_net_object import PetriNetObject


class Transition(PetriNetObject):
    """A rectangular transition in a Petri net.
    
    Transitions represent events or actions that transform the net state.
    Rendered as a filled black rectangle.
    """
    
    # Default styling (proportional to Place circle)
    # Width = Place diameter (50.0), Height = Place radius (25.0)
    DEFAULT_WIDTH = 50.0   # Equal to Place diameter
    DEFAULT_HEIGHT = 25.0  # Equal to Place radius
    DEFAULT_COLOR = (0.0, 0.0, 0.0)  # Black fill
    DEFAULT_BORDER_COLOR = (0.0, 0.0, 0.0)  # Black border
    DEFAULT_BORDER_WIDTH = 3.0  # 3px for better visibility
    
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
        # Initialize base class
        super().__init__(id, name, label)
        
        # Position and dimensions
        self.x = x
        self.y = y
        self.width = width if width is not None else self.DEFAULT_WIDTH
        self.height = height if height is not None else self.DEFAULT_HEIGHT
        self.horizontal = horizontal
        
        # Styling
        self.fill_color = self.DEFAULT_COLOR
        self.border_color = self.DEFAULT_BORDER_COLOR
        self.border_width = self.DEFAULT_BORDER_WIDTH
        
        # State
        self.enabled = True  # Can this transition fire?
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render the transition using Cairo.
        
        Uses legacy rendering style with Cairo transform approach:
        - Black fill with colored border
        - 3.0px line width (compensated for zoom to maintain constant pixel size)
        - fill_preserve to maintain path for border
        - Draws in world coordinates (Cairo transform handles scaling)
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
        # Use world coordinates directly (Cairo transform handles conversion)
        
        # Swap dimensions if vertical
        width = self.width
        height = self.height
        if not self.horizontal:
            width, height = height, width
        
        # Calculate rectangle corners (center-based)
        half_w = width / 2
        half_h = height / 2
        
        # Draw rectangle (legacy style: fill_preserve then stroke)
        cr.rectangle(self.x - half_w, self.y - half_h, width, height)
        cr.set_source_rgb(*self.fill_color)
        cr.fill_preserve()  # Fill but keep path for border
        
        # Draw border (legacy style: 3.0px compensated for zoom)
        cr.set_source_rgb(*self.border_color)
        cr.set_line_width(self.border_width / max(zoom, 1e-6))
        cr.stroke()
        
        # Selection rendering moved to ObjectEditingTransforms in src/shypn/api/edit/
        
        # Draw label if provided
        if self.label:
            self._render_label(cr, self.x, self.y, height, self.horizontal, zoom)
    
    def _render_label(self, cr, x: float, y: float, height: float, horizontal: bool, zoom: float = 1.0):
        """Render text label next to the transition.
        
        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            height: Rectangle height (world space)
            horizontal: Orientation flag
            zoom: Current zoom level for font/offset compensation
        """
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 0)  # Normal, Normal
        cr.set_font_size(12 / zoom)  # Compensate for zoom
        extents = cr.text_extents(self.label)
        
        if horizontal:
            # Label below horizontal transition
            cr.move_to(x - extents.width / 2, y + height / 2 + 15 / zoom)
        else:
            # Label to the right of vertical transition
            cr.move_to(x + height / 2 + 5 / zoom, y + extents.height / 2)
        
        cr.show_text(self.label)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this transition.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is inside the rectangle
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
