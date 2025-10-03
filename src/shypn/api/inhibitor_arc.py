"""
InhibitorArc class for Petri net inhibitor arcs.
Inherits from Arc but renders with a circular marker instead of an arrowhead.
"""

import math
from .arc import Arc


class InhibitorArc(Arc):
    """
    Represents an inhibitor arc in a Petri net.
    
    An inhibitor arc prevents a transition from firing when the source place
    contains tokens. It is rendered with a circular marker at the target end
    instead of an arrowhead.
    
    Uses legacy rendering style:
    - White-filled circle with colored ring
    - Radius scales with marker size (6-12px range)
    - Arc line stops before marker for clean appearance
    
    Inherits all properties from Arc but overrides the arrowhead rendering
    to display a circle marker.
    """
    
    # Marker size for the inhibitor circle (legacy: 6-12px range)
    MARKER_RADIUS = 8.0
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """
        Initialize an inhibitor arc.
        
        Args:
            source: Source PetriNetObject (typically a Place)
            target: Target PetriNetObject (typically a Transition)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "I1", "I2", etc. (immutable, system-assigned)
            weight: Arc weight (default: 1)
        """
        super().__init__(source, target, id, name, weight)
    
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
    
    def __repr__(self):
        """String representation of the inhibitor arc."""
        return (f"InhibitorArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
