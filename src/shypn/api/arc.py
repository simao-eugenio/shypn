#!/usr/bin/env python3
"""Arc - Directed connection in a Petri net.

Arcs connect places to transitions or transitions to places.
Rendered as an arrow with optional weight label.
"""
import math
from typing import List, Tuple
from shypn.api.petri_net_object import PetriNetObject


class Arc(PetriNetObject):
    """A directed arc in a Petri net.
    
    Arcs connect places to transitions or transitions to places.
    Rendered as an arrow with optional weight label.
    """
    
    # Default styling (legacy renderer values)
    DEFAULT_COLOR = (0.0, 0.0, 0.0)  # Black
    DEFAULT_WIDTH = 3.0  # Legacy: 3.0px line width
    ARROW_SIZE = 15.0    # Legacy: 15px arrowhead length
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """Initialize an Arc.
        
        Args:
            source: Source object instance (Place or Transition)
            target: Target object instance (Place or Transition)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "A1", "A2", etc. (immutable, system-assigned)
            weight: Arc weight (multiplicity)
        
        Raises:
            ValueError: If source and target are of the same type (violates bipartite property)
        """
        # Validate bipartite connection (Place↔Transition only)
        self._validate_connection(source, target)
        
        # Initialize base class (arcs don't have user labels typically)
        super().__init__(id, name, label="")
        
        # Connection (references to object instances)
        self.source = source
        self.target = target
        self.weight = weight
        
        # Styling
        self.color = self.DEFAULT_COLOR
        self.width = self.DEFAULT_WIDTH
        
        # Control points for curved arcs (optional)
        self.control_points: List[Tuple[float, float]] = []
    
    @staticmethod
    def _validate_connection(source, target):
        """Validate that connection follows bipartite property.
        
        Petri nets are bipartite graphs: arcs must connect Place↔Transition only.
        - Valid: Place → Transition
        - Valid: Transition → Place
        - Invalid: Place → Place
        - Invalid: Transition → Transition
        
        Args:
            source: Source object
            target: Target object
        
        Raises:
            ValueError: If source and target are of the same type
        """
        from shypn.api.place import Place
        from shypn.api.transition import Transition
        
        source_is_place = isinstance(source, Place)
        target_is_place = isinstance(target, Place)
        
        # Both are places or both are transitions → invalid
        if source_is_place == target_is_place:
            source_type = "Place" if source_is_place else "Transition"
            target_type = "Place" if target_is_place else "Transition"
            raise ValueError(
                f"Invalid connection: {source_type} → {target_type}. "
                f"Arcs must connect Place↔Transition (bipartite property). "
                f"Valid connections: Place→Transition or Transition→Place."
            )
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render the arc using Cairo.
        
        Uses legacy rendering style with Cairo transform approach:
        - 3.0px line width (compensated for zoom to maintain constant pixel size)
        - Two-line arrowhead (15px, π/5 angle)
        - Bold Arial 12pt weight text with white background
        - Only shows weight if > 1
        - Draws in world coordinates (Cairo transform handles scaling)
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Calculate direction in world space
        dx_world = tgt_world_x - src_world_x
        dy_world = tgt_world_y - src_world_y
        length_world = math.sqrt(dx_world * dx_world + dy_world * dy_world)
        
        if length_world < 1:
            return  # Too short to draw
        
        # Normalize direction
        dx_world /= length_world
        dy_world /= length_world
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_world, dy_world)
        end_world_x, end_world_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_world, -dy_world)
        
        # Draw line in world coordinates
        cr.move_to(start_world_x, start_world_y)
        cr.line_to(end_world_x, end_world_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))  # Compensate for zoom
        cr.stroke()
        
        # Draw arrowhead at target (with zoom compensation)
        self._render_arrowhead(cr, end_world_x, end_world_y, dx_world, dy_world, zoom)
        
        # Draw weight label if > 1
        if self.weight > 1:
            self._render_weight(cr, start_world_x, start_world_y, end_world_x, end_world_y, zoom)
        
        # Draw selection highlight if selected
        if self.selected:
            cr.move_to(start_world_x, start_world_y)
            cr.line_to(end_world_x, end_world_y)
            cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)
            cr.set_line_width((self.width + 4) / zoom)  # Compensate for zoom
            cr.stroke()
    
    def _get_boundary_point(self, obj, cx: float, cy: float, 
                           dx: float, dy: float) -> Tuple[float, float]:
        """Calculate where arc intersects object boundary.
        
        Args:
            obj: Place or Transition object
            cx, cy: Object center
            dx, dy: Direction vector (normalized)
            
        Returns:
            tuple: (x, y) point on object boundary
        """
        # Import here to avoid circular dependency
        from shypn.api.place import Place
        from shypn.api.transition import Transition
        
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
    
    def _render_arrowhead(self, cr, x: float, y: float, dx: float, dy: float, zoom: float = 1.0):
        """Render two-line arrowhead at arrow tip (legacy style).
        
        Legacy rendering characteristics:
        - Two separate lines (not a filled triangle)
        - 15px length (compensated for zoom), π/5 angle (36 degrees)
        - Same color and width as arc line
        
        Args:
            cr: Cairo context
            x, y: Arrow tip position (world coords)
            dx, dy: Direction vector (normalized, world space)
            zoom: Current zoom level for size compensation
        """
        # Legacy style: π/5 angle (36 degrees, not 30)
        angle = math.atan2(dy, dx)
        arrow_angle = math.pi / 5  # 36 degrees
        
        # Arrow size compensated for zoom (15px constant screen size)
        arrow_size = self.ARROW_SIZE / zoom
        
        # Calculate wing endpoints
        left_x = x - arrow_size * math.cos(angle - arrow_angle)
        left_y = y - arrow_size * math.sin(angle - arrow_angle)
        
        right_x = x - arrow_size * math.cos(angle + arrow_angle)
        right_y = y - arrow_size * math.sin(angle + arrow_angle)
        
        # Draw two lines (legacy style, not filled triangle)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))
        
        # Left wing line
        cr.move_to(x, y)
        cr.line_to(left_x, left_y)
        cr.stroke()
        
        # Right wing line
        cr.move_to(x, y)
        cr.line_to(right_x, right_y)
        cr.stroke()
    
    def _render_weight(self, cr, x1: float, y1: float, x2: float, y2: float, zoom: float = 1.0):
        """Render weight label near the arc midpoint.
        
        Uses legacy rendering style:
        - Bold Arial 12pt font (compensated for zoom)
        - White semi-transparent background (0.8 alpha)
        - Positioned perpendicular to arc
        
        Args:
            cr: Cairo context
            x1, y1: Start point (world coords)
            x2, y2: End point (world coords)
            zoom: Current zoom level for font/offset compensation
        """
        # Calculate midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Legacy style: Bold Arial 12pt (compensated for zoom)
        cr.select_font_face("Arial", 0, 1)  # Normal slant, Bold weight
        cr.set_font_size(12 / zoom)
        text = str(self.weight)
        extents = cr.text_extents(text)
        
        # Calculate perpendicular offset (8px screen size = 8/zoom world space)
        offset = 8 / zoom
        dx = y2 - y1  # Perpendicular direction
        dy = x1 - x2
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            dx = dx / length * offset
            dy = dy / length * offset
        
        # Text position (centered)
        text_x = mid_x + dx - extents.width / 2
        text_y = mid_y + dy + extents.height / 2
        
        # Draw white background (legacy style: semi-transparent)
        padding = 2 / zoom
        cr.rectangle(text_x - padding, text_y - extents.height - padding,
                    extents.width + 2 * padding, extents.height + 2 * padding)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)  # White, 0.8 alpha
        cr.fill()
        
        # Draw text
        cr.move_to(text_x, text_y)
        cr.set_source_rgb(0, 0, 0)  # Black text
        cr.show_text(text)
    
    def _render_weight(self, cr, x1: float, y1: float, x2: float, y2: float):
        """Render weight label near the arc midpoint.
        
        Uses legacy rendering style:
        - Bold Arial 12pt font
        - White semi-transparent background (0.8 alpha)
        - Positioned perpendicular to arc
        
        Args:
            cr: Cairo context
            x1, y1: Start point
            x2, y2: End point
        """
        # Calculate midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Legacy style: Bold Arial 12pt
        cr.select_font_face("Arial", 0, 1)  # Normal slant, Bold weight
        cr.set_font_size(12)
        text = str(self.weight)
        extents = cr.text_extents(text)
        
        # Calculate perpendicular offset (8px from arc line)
        offset = 8
        dx = y2 - y1  # Perpendicular direction
        dy = x1 - x2
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            dx = dx / length * offset
            dy = dy / length * offset
        
        # Text position (centered)
        text_x = mid_x + dx - extents.width / 2
        text_y = mid_y + dy + extents.height / 2
        
        # Draw white background (legacy style: semi-transparent)
        padding = 2
        cr.rectangle(text_x - padding, text_y - extents.height - padding,
                    extents.width + 2 * padding, extents.height + 2 * padding)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)  # White, 0.8 alpha
        cr.fill()
        
        # Draw text
        cr.move_to(text_x, text_y)
        cr.set_source_rgb(0, 0, 0)  # Black text
        cr.show_text(text)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is near this arc.
        
        Arcs are thin and harder to click, so this uses a tolerance distance.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is near the arc line
        """
        # TODO: Implement proper line distance calculation
        # For now, arcs are not easily selectable
        return False
    
    def set_position(self, x: float, y: float):
        """Arcs don't have a direct position (they connect other objects).
        
        This method is not applicable for arcs.
        
        Args:
            x, y: Position (ignored)
        """
        pass  # Arcs move when their source/target objects move
    
    def set_weight(self, weight: int):
        """Set the arc weight.
        
        Args:
            weight: New weight (positive integer)
        """
        self.weight = max(1, weight)
        self._trigger_redraw()
