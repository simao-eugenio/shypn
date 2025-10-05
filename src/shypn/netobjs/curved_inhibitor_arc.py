#!/usr/bin/env python3
"""CurvedInhibitorArc - Inhibitor arc with bezier curve path.

Combines curved path from CurvedArc with hollow circle marker from InhibitorArc.
"""
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.inhibitor_arc import InhibitorArc


class CurvedInhibitorArc(CurvedArc):
    """Inhibitor arc rendered with a bezier curve path.
    
    Inherits:
    - Bezier curve rendering from CurvedArc
    - Uses InhibitorArc's marker rendering method
    
    This class combines the best of both:
    - Smooth curve to avoid overlap with opposite arcs
    - Hollow circle marker for inhibitor semantics
    """
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """Initialize a curved inhibitor arc.
        
        Args:
            source: Source PetriNetObject (typically a Place)
            target: Target PetriNetObject (typically a Transition)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "CI1", "CI2", etc. (immutable, system-assigned)
            weight: Arc weight (default: 1)
        """
        super().__init__(source, target, id, name, weight)
    
    def _render_arrowhead(self, cr, x: float, y: float, dx: float, dy: float, zoom: float = 1.0):
        """Render hollow circle marker instead of two-line arrowhead.
        
        Delegates to InhibitorArc's implementation to avoid code duplication.
        
        Args:
            cr: Cairo context
            x, y: Marker center position (world coords)
            dx, dy: Direction vector (for future use with line trimming)
            zoom: Current zoom level for size compensation
        """
        # Use InhibitorArc's marker rendering
        # This is composition through method delegation
        InhibitorArc._render_arrowhead(self, cr, x, y, dx, dy, zoom)
    
    def to_dict(self) -> dict:
        """Serialize curved inhibitor arc to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all arc properties with type 'curved_inhibitor_arc'
        """
        data = super().to_dict()
        data["type"] = "curved_inhibitor_arc"  # Override type
        return data
    
    def __repr__(self):
        """String representation of the curved inhibitor arc."""
        return (f"CurvedInhibitorArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
