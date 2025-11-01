"""
InhibitorArc class for Petri net inhibitor arcs (Living Systems Semantics).

SHYPN uses "cooperation" semantics for inhibitor arcs, reflecting organic/living
systems where no component should be subjected to starvation.

Inherits from Arc but renders with a circular marker instead of an arrowhead.
"""

import math
from .arc import Arc


class InhibitorArc(Arc):
    """
    Represents an inhibitor arc in a Petri net (Classical/Biological Semantics).
    
    **SHYPN Semantics** (Classical Inhibitor = Biological Negative Feedback):
    An inhibitor arc PREVENTS a transition from firing when the source place has
    TOO MANY tokens (tokens >= weight). This implements negative feedback:
    - Transition active when product is LOW (product < threshold)
    - Transition inhibited when product is HIGH (product >= threshold)
    - Does NOT consume tokens (read-only check, like test arcs)
    
    **Enabling Condition**: source.tokens < weight (must be BELOW threshold)
    **Token Transfer**: NO - does not consume (regulatory check only)
    **Biological Role**: End-product inhibition, homeostasis, negative feedback
    
    **Visual Rendering**:
    - White-filled circle with colored ring at target end
    - Radius scales with marker size (8.0px)
    - Arc line stops before marker for clean appearance
    
    **Biological Examples:**
    1. ATP inhibiting glycolysis (energy homeostasis)
    2. Amino acid inhibiting its synthesis pathway
    3. Hormone feedback on its production
    4. Product accumulation stopping enzyme
    
    **Example:**
    ```
    Substrate --[normal]--> Enzyme --[normal]--> Product
                              ↑
                              | [inhibitor, w=10]
                           Product
    
    Behavior:
    - Product < 10: Enzyme ACTIVE (produces more product)
    - Product >= 10: Enzyme INHIBITED (stops production)
    - Classic negative feedback loop
    ```
    
    Inherits all properties from Arc but overrides the arrowhead rendering
    to display a circle marker.
    """
    
    # Marker size for the inhibitor circle (legacy: 6-12px range)
    MARKER_RADIUS = 8.0
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """
        Initialize an inhibitor arc.
        
        Args:
            source: Source PetriNetObject (must be a Place)
            target: Target PetriNetObject (must be a Transition)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "I1", "I2", etc. (immutable, system-assigned)
            weight: Arc weight (threshold for surplus - default: 1)
        """
        super().__init__(source, target, id, name, weight)
    
    @staticmethod
    def _validate_connection(source, target):
        """Validate inhibitor arc connection rules.
        
        Inhibitor arcs have stricter rules than normal arcs:
        - Must follow bipartite property (Place↔Transition)
        - Must go from Place to Transition ONLY
        - Transition to Place is FORBIDDEN (semantically invalid)
        
        In SHYPN's living systems model, an inhibitor arc from a place to a
        transition allows sharing only when the place has surplus (cooperation).
        The reverse direction (Transition→Place) has no semantic meaning.
        
        Args:
            source: Source object (must be Place for inhibitor arcs)
            target: Target object (must be Transition for inhibitor arcs)
        
        Raises:
            ValueError: If connection violates inhibitor arc rules
        """
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        
        # First check bipartite property (Place↔Transition)
        Arc._validate_connection(source, target)
        
        # Additional constraint: inhibitor arcs must go Place → Transition
        if isinstance(source, Transition) and isinstance(target, Place):
            raise ValueError(
                "Invalid inhibitor arc: Transition → Place is forbidden. "
                "Inhibitor arcs must connect Place → Transition only. "
                "An inhibitor arc prevents a transition from firing when "
                "the source place contains tokens."
            )
    
    def _render_arrowhead(self, cr, x: float, y: float, dx: float, dy: float, zoom: float = 1.0):
        """
        Draw circular inhibitor marker instead of arrowhead.
        
        Uses legacy rendering style:
        - White-filled background circle
        - Colored ring using arc color and line width
        - Positioned at target connection point
        - Radius compensated for zoom (constant 8px screen size)
        
        The white fill hides the arc line end for a clean appearance.
        
        Args:
            cr: Cairo context
            x, y: Marker center position (world coords)
            dx, dy: Direction vector (for future use with line trimming)
            zoom: Current zoom level for size compensation
        """
        # Marker radius compensated for zoom (8px constant screen size)
        marker_radius = self.MARKER_RADIUS / zoom
        
        # Draw white-filled circle (legacy style)
        cr.arc(x, y, marker_radius, 0, 2 * math.pi)
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White fill
        cr.fill_preserve()  # Fill but keep path for border
        
        # Draw colored ring border (legacy style)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))  # Compensate for zoom
        cr.stroke()
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render inhibitor arc with line stopping before the hollow circle.
        
        Overrides Arc.render() to adjust the endpoint so the line doesn't
        go through the hollow circle marker. Supports both straight and curved rendering.
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
        # Check if this arc should be rendered as curved
        if getattr(self, 'is_curved', False):
            self._render_curved(cr, zoom)
            return
        
        # Ensure clean Cairo context state
        cr.new_path()
        
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Calculate direction in world space
        dx_world = tgt_world_x - src_world_x
        dy_world = tgt_world_y - src_world_y
        length_world = math.sqrt(dx_world * dx_world + dy_world * dy_world)
        
        if length_world < 1:
            return
        
        # Normalize direction
        dx_world /= length_world
        dy_world /= length_world
        
        # Check for parallel arcs and apply offset
        offset_distance = 0.0
        if hasattr(self, '_manager') and self._manager:
            parallels = self._manager.detect_parallel_arcs(self)
            if parallels:
                offset_distance = self._manager.calculate_arc_offset(self, parallels)
        
        if abs(offset_distance) > 1e-6:
            # Apply perpendicular offset to line endpoints
            perp_x = -dy_world
            perp_y = dx_world
            
            src_world_x += perp_x * offset_distance
            src_world_y += perp_y * offset_distance
            tgt_world_x += perp_x * offset_distance
            tgt_world_y += perp_y * offset_distance
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_world, dy_world)
        
        # Get target boundary point
        boundary_x, boundary_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_world, -dy_world)
        
        # For inhibitor arc: hollow circle must be entirely outside target
        # The circle's outer edge touches the target boundary (edge-to-edge)
        # Position circle center INWARD (away from target) by marker radius
        # This ensures the circle edge at boundary_x, boundary_y, with center outside
        marker_radius = self.MARKER_RADIUS / zoom
        marker_x = boundary_x - dx_world * marker_radius
        marker_y = boundary_y - dy_world * marker_radius
        
        # Line should stop before the circle with a small gap
        gap = 2.0 / zoom  # 2px gap for clean appearance
        end_world_x = marker_x - dx_world * (marker_radius + gap)
        end_world_y = marker_y - dy_world * (marker_radius + gap)
        
        # Add glow effect for colored arcs (CSS-like styling)
        if self.color != self.DEFAULT_COLOR:
            cr.move_to(start_world_x, start_world_y)
            cr.line_to(end_world_x, end_world_y)
            r, g, b = self.color
            cr.set_source_rgba(r, g, b, 0.3)
            cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw line in world coordinates
        cr.move_to(start_world_x, start_world_y)
        cr.line_to(end_world_x, end_world_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))
        cr.stroke()
        
        # Draw hollow circle with edge touching target boundary
        self._render_arrowhead(cr, marker_x, marker_y, dx_world, dy_world, zoom)
        
        # Draw weight label if > 1
        if self.weight > 1:
            self._render_weight(cr, start_world_x, start_world_y, marker_x, marker_y, zoom)
        
        # Ensure clean state for next rendering operation
        cr.new_path()
    
    def _render_curved(self, cr, zoom=1.0):
        """Render curved inhibitor arc using bezier curve.
        
        Similar to CurvedInhibitorArc but uses control_offset_x/y instead of automatic calculation.
        
        Args:
            cr: Cairo context
            zoom: Current zoom level
        """
        # Ensure clean Cairo context state
        cr.new_path()
        
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Calculate midpoint
        mid_x = (src_world_x + tgt_world_x) / 2
        mid_y = (src_world_y + tgt_world_y) / 2
        
        # Get control point from offsets
        control_offset_x = getattr(self, 'control_offset_x', 0.0)
        control_offset_y = getattr(self, 'control_offset_y', 0.0)
        cp_x = mid_x + control_offset_x
        cp_y = mid_y + control_offset_y
        
        # Calculate tangent at end: direction from control point to target
        dx_end = tgt_world_x - cp_x
        dy_end = tgt_world_y - cp_y
        length_end = math.sqrt(dx_end*dx_end + dy_end*dy_end)
        
        if length_end < 1e-6:
            # Degenerate case: fall back to straight line
            super().render(cr, None, zoom)
            return
        
        dx_end /= length_end
        dy_end /= length_end
        
        # Tangent at start: direction from source to control point
        dx_start = cp_x - src_world_x
        dy_start = cp_y - src_world_y
        length_start = math.sqrt(dx_start*dx_start + dy_start*dy_start)
        
        if length_start < 1e-6:
            super().render(cr, None, zoom)
            return
        
        dx_start /= length_start
        dy_start /= length_start
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_start, dy_start)
        
        # Get target boundary point for hollow circle placement
        # Use straight-line direction for boundary calculation (not curve tangent)
        dx_straight = tgt_world_x - src_world_x
        dy_straight = tgt_world_y - src_world_y
        length_straight = math.sqrt(dx_straight*dx_straight + dy_straight*dy_straight)
        
        if length_straight < 1e-6:
            super().render(cr, None, zoom)
            return
            
        dx_straight /= length_straight
        dy_straight /= length_straight
        
        boundary_x, boundary_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_straight, -dy_straight)
        
        # For inhibitor arc: hollow circle must be entirely outside target
        # Position along straight-line direction to ensure edge-to-edge contact
        marker_radius = self.MARKER_RADIUS / zoom
        marker_x = boundary_x - dx_straight * marker_radius
        marker_y = boundary_y - dy_straight * marker_radius
        
        # Curve should end at the near edge of the circle (with small gap)
        gap = 2.0 / zoom  # 2px gap for clean appearance
        end_world_x = marker_x - dx_end * (marker_radius + gap)
        end_world_y = marker_y - dy_end * (marker_radius + gap)
        
        # Add glow effect for colored arcs
        if self.color != self.DEFAULT_COLOR:
            cr.move_to(start_world_x, start_world_y)
            cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
            r, g, b = self.color
            cr.set_source_rgba(r, g, b, 0.3)
            cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw curve in world coordinates
        cr.move_to(start_world_x, start_world_y)
        cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))
        cr.stroke()
        
        # Draw hollow circle at target boundary
        self._render_arrowhead(cr, marker_x, marker_y, dx_end, dy_end, zoom)
        
        # Draw weight label if > 1
        if self.weight > 1:
            self._render_weight_curved(cr, start_world_x, start_world_y, 
                                      end_world_x, end_world_y, 
                                      cp_x, cp_y, zoom)
        
        # Ensure clean state for next rendering operation
        cr.new_path()
    
    def _render_weight_curved(self, cr, x1: float, y1: float, x2: float, y2: float,
                             cp_x: float, cp_y: float, zoom: float = 1.0):
        """Render weight label on curved inhibitor arc.
        
        Args:
            cr: Cairo context
            x1, y1: Start point (world coords)
            x2, y2: End point (world coords)
            cp_x, cp_y: Control point (world coords)
            zoom: Current zoom level
        """
        # Save context
        cr.save()
        
        # Calculate midpoint on bezier curve at t=0.5
        t = 0.5
        b0 = (1 - t) * (1 - t)
        b1 = 2 * (1 - t) * t
        b2 = t * t
        
        mid_x = b0 * x1 + b1 * cp_x + b2 * x2
        mid_y = b0 * y1 + b1 * cp_y + b2 * y2
        
        # Calculate tangent at midpoint
        tangent_x = 2 * (1 - t) * (cp_x - x1) + 2 * t * (x2 - cp_x)
        tangent_y = 2 * (1 - t) * (cp_y - y1) + 2 * t * (y2 - cp_y)
        
        # Normalize tangent
        tangent_length = math.sqrt(tangent_x * tangent_x + tangent_y * tangent_y)
        if tangent_length < 1e-6:
            # Fallback to straight line
            self._render_weight(cr, x1, y1, x2, y2, zoom)
            cr.restore()
            return
        
        tangent_x /= tangent_length
        tangent_y /= tangent_length
        
        # Perpendicular direction (rotate tangent 90° counterclockwise)
        perp_x = -tangent_y
        perp_y = tangent_x
        
        # Determine which side based on curve direction
        dx = x2 - x1
        dy = y2 - y1
        line_length = math.sqrt(dx*dx + dy*dy)
        
        if line_length > 1e-6:
            line_perp_x = -dy / line_length
            line_perp_y = dx / line_length
            
            mid_line_x = (x1 + x2) / 2
            mid_line_y = (y1 + y2) / 2
            cp_offset_x = cp_x - mid_line_x
            cp_offset_y = cp_y - mid_line_y
            
            side = cp_offset_x * line_perp_x + cp_offset_y * line_perp_y
            
            if side < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        
        # Font setup
        cr.select_font_face("Arial", 0, 1)
        cr.set_font_size(12 / zoom)
        text = str(self.weight)
        extents = cr.text_extents(text)
        
        # Position text perpendicular to curve
        offset = 11 / zoom
        text_x = mid_x + perp_x * offset - extents.width / 2
        text_y = mid_y + perp_y * offset + extents.height / 2
        
        # Draw white background
        padding = 2 / zoom
        cr.rectangle(text_x - padding, text_y - extents.height - padding,
                    extents.width + 2 * padding, extents.height + 2 * padding)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)
        cr.fill()
        
        # Draw text
        cr.move_to(text_x, text_y)
        cr.set_source_rgb(0, 0, 0)
        cr.show_text(text)
        
        cr.new_path()
        cr.restore()
    
    def to_dict(self) -> dict:
        """Serialize inhibitor arc to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all arc properties with arc_type='inhibitor'
        """
        data = super().to_dict()
        data["arc_type"] = "inhibitor"  # Override arc_type to distinguish from normal Arc
        return data
    
    def __repr__(self):
        """String representation of the inhibitor arc."""
        return (f"InhibitorArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
