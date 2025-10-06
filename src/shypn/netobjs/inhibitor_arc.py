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
    Represents an inhibitor arc in a Petri net (Living Systems / Cooperation Semantics).
    
    **SHYPN Semantics** (Living Systems):
    An inhibitor arc allows a transition to fire ONLY when the source place has
    SURPLUS tokens (tokens >= weight). This implements a cooperation principle:
    - Place can share resources only when it has enough to spare
    - Prevents starvation by maintaining minimum reserve levels
    - Consumes tokens on firing (like normal arcs)
    
    **Enabling Condition**: source.tokens >= weight (must have surplus)
    **Token Transfer**: YES - consumes from source place (cooperation)
    **Protection**: Transition disabled when source.tokens < weight (prevents starvation)
    
    **Visual Rendering**:
    - White-filled circle with colored ring at target end
    - Radius scales with marker size (6-12px range)
    - Arc line stops before marker for clean appearance
    
    **Classical Semantics** (for reference, NOT used in SHYPN):
    In classical Petri net theory, inhibitor arcs enable when place is BELOW threshold
    and don't consume tokens. SHYPN uses the opposite: enable when ABOVE threshold
    and DO consume tokens. This reflects organic systems vs. manufacturing systems.
    
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
        go through the hollow circle marker.
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
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
    
    def to_dict(self) -> dict:
        """Serialize inhibitor arc to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all arc properties with type 'inhibitor_arc'
        """
        data = super().to_dict()
        data["type"] = "inhibitor_arc"  # Override type to distinguish from Arc
        return data
    
    def __repr__(self):
        """String representation of the inhibitor arc."""
        return (f"InhibitorArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
