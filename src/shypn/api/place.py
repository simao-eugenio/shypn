#!/usr/bin/env python3
"""Place - Circular node in a Petri net.

Places represent conditions or states and can contain tokens.
Rendered as a circle with optional label and token display.
"""
import math
from shypn.api.petri_net_object import PetriNetObject


class Place(PetriNetObject):
    """A circular place in a Petri net.
    
    Places represent conditions or states and can contain tokens.
    Rendered as a circle with optional label and token display.
    """
    
    # Default styling (proportional metrics at 1:1 scale)
    DEFAULT_RADIUS = 25.0  # 25px radius = 50px diameter at 100% zoom
    DEFAULT_BORDER_COLOR = (0.0, 0.0, 0.0)  # Black border
    DEFAULT_BORDER_WIDTH = 3.0  # 3px for better visibility
    
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
        # Initialize base class
        super().__init__(id, name, label)
        
        # Position
        self.x = x
        self.y = y
        self.radius = radius if radius is not None else self.DEFAULT_RADIUS
        
        # Styling
        self.border_color = self.DEFAULT_BORDER_COLOR
        self.border_width = self.DEFAULT_BORDER_WIDTH
        
        # State
        self.tokens = 0  # Number of tokens in this place
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render the place using Cairo.
        
        Uses legacy rendering style with Cairo transform approach:
        - Hollow circle (stroke only, no fill) like classic Petri nets
        - 3.0px line width (compensated for zoom to maintain constant pixel size)
        - Black border by default
        - Draws in world coordinates (Cairo transform handles scaling)
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
        # Use world coordinates directly (Cairo transform handles conversion)
        # Legacy approach: cr.scale() is already applied, so we draw in world space
        
        # Draw hollow circle (legacy style: stroke only, no fill)
        cr.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
        cr.set_source_rgb(*self.border_color)
        cr.set_line_width(self.border_width / max(zoom, 1e-6))  # Compensate for zoom
        cr.stroke()
        
        # Draw selection highlight if selected
        if self.selected:
            # Offset by 3px in screen space = 3/zoom in world space
            cr.arc(self.x, self.y, self.radius + 3 / zoom, 0, 2 * math.pi)
            cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)  # Blue highlight
            cr.set_line_width(3.0 / zoom)  # Compensate for zoom
            cr.stroke()
        
        # Draw tokens if any
        if self.tokens > 0:
            self._render_tokens(cr, self.x, self.y, self.radius, zoom)
        
        # Draw label if provided
        if self.label:
            self._render_label(cr, self.x, self.y, self.radius, zoom)
    
    def _render_tokens(self, cr, x: float, y: float, radius: float, zoom: float = 1.0):
        """Render token indicators inside the place.
        
        Legacy style: Shows token count as centered text (Arial 14pt).
        For 0 tokens, nothing is shown.
        
        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            radius: Circle radius (world space)
            zoom: Current zoom level for font size compensation
        """
        if self.tokens == 0:
            return
        
        # Always show as text number (legacy style)
        cr.set_source_rgb(0, 0, 0)
        try:
            # Try to use Arial (legacy style)
            cr.select_font_face("Arial", 0, 0)  # Arial, Normal, Normal
        except:
            cr.select_font_face("Sans", 0, 0)  # Fallback to Sans
        
        # Font size compensated for zoom (14pt constant screen size)
        cr.set_font_size(14 / zoom)
        text = str(self.tokens) if isinstance(self.tokens, int) else f"{self.tokens:.1f}"
        extents = cr.text_extents(text)
        text_x = x - extents.width / 2
        text_y = y + extents.height / 2
        cr.move_to(text_x, text_y)
        cr.show_text(text)
        cr.fill()
    
    def _render_label(self, cr, x: float, y: float, radius: float, zoom: float = 1.0):
        """Render text label below the place.
        
        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            radius: Circle radius (world space)
            zoom: Current zoom level for font/offset compensation
        """
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 0)  # Normal, Normal
        cr.set_font_size(12 / zoom)  # Compensate for zoom
        extents = cr.text_extents(self.label)
        cr.move_to(x - extents.width / 2, y + radius + 15 / zoom)
        cr.show_text(self.label)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this place.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is inside the circle
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
