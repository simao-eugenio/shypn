#!/usr/bin/env python3
"""Place - Circular node in a Petri net.

Places represent conditions or states and can contain tokens.
Rendered as a circle with optional label and token display.
"""
import math
from typing import Optional, List
from shypn.netobjs.petri_net_object import PetriNetObject
from shypn.netobjs.signal_type import SignalType


class Place(PetriNetObject):
    """A circular place in a Petri net.
    
    Places represent conditions or states and can contain tokens.
    Rendered as a circle with optional label and token display.
    """
    
    # Default styling (proportional metrics at 1:1 scale)
    DEFAULT_RADIUS = 40.0  # 40px radius = 80px diameter at 100% zoom
    DEFAULT_BORDER_COLOR = (0.0, 0.0, 0.0)  # Black border
    DEFAULT_BORDER_WIDTH = 3.0  # 3px for better visibility
    
    def __init__(self, x: float, y: float, id: str, name: str, 
                 radius: float = None, label: str = ""):
        """Initialize a Place.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            id: Unique string identifier (immutable, system-assigned)
            name: Unique name in format "P1", "P2", etc. (immutable, system-assigned)
            radius: Circle radius (default: 25.0)
            label: Optional user-editable text label (mutable)
        """
        # Initialize base class
        super().__init__(id, name, label)
        
        # Position
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius) if radius is not None else self.DEFAULT_RADIUS
        
        # Styling
        self.border_color = self.DEFAULT_BORDER_COLOR
        self.border_width = self.DEFAULT_BORDER_WIDTH
        
        # State
        self.tokens = 0  # Number of tokens in this place
        self.initial_marking = 0  # Initial marking for simulation reset
        self.capacity = float('inf')  # Maximum token capacity (infinite by default)
        
        # Signal place properties (13-tuple Bio-PN formalism: Ψ)
        # Signal places enable modular architecture through information flow without mass transfer
        self.is_signal_place = False  # True if this place has no arc connections (read-only sensing)
        self.signal_type: Optional[SignalType] = None  # Classification: quorum, energy, regulatory, spatial
        self.signal_scope: List[str] = []  # Module IDs that can read this signal (empty = global scope)
        
        # Regulatory place properties (gene loci, constant resources)
        # Regulatory places represent genetic elements or constant resource pools
        self.is_regulatory_place = False  # True if this is a gene locus or constant resource
        
        # Module assignment (modular Bio-PN architecture)
        # Places belong to modules, enabling network partitioning and compartmentalization
        self.module_id: Optional[str] = None  # Module identifier (e.g., "M_cytoplasm", "M_mitochondria")
        
        # Compartment place marker (backward compatibility)
        # is_compartment_place: True if in non-default compartment (e.g., extracellular)
        #   Rendered as violet circle (NOT hexagon - those are only for signal places)
        self.is_compartment_place = False
    
    def get_bounding_box(self):
        """Calculate bounding box for the place.
        
        Returns bounding box containing the circle or hexagon.
        
        Returns:
            dict: {'x': min_x, 'y': min_y, 'width': width, 'height': height}
        """
        # Circle/hexagon is centered at (x, y) with radius
        # Bounding box is square centered at position
        diameter = 2 * self.radius
        return {
            'x': self.x - self.radius,
            'y': self.y - self.radius,
            'width': diameter,
            'height': diameter
        }
    
    def render(self, cr, zoom=1.0):
        """Render the place as a hollow circle (or hexagon for signal places).
        
        Uses legacy rendering style with Cairo transform approach:
        - Hollow shape (stroke only, no fill) like classic Petri nets
        - Circle for regular places, hexagon for signal places (Ψ)
        - 3.0px line width (compensated for zoom to maintain constant pixel size)
        - Black border by default (blue for signal places)
        - Draws in world coordinates (Cairo transform handles scaling)
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            zoom: Current zoom level for line width compensation
        """
        # Use world coordinates directly (Cairo transform handles conversion)
        # Legacy approach: cr.scale() is already applied, so we draw in world space
        
        # Color coding for different place types
        # Normalized color scheme (2025-12-31): All black by default
        # Signal places distinguished by hexagonal shape, not color
        display_color = self.border_color  # Black for all places unless recording
        
        # Add glow effect for colored objects (CSS-like styling)
        if display_color != self.DEFAULT_BORDER_COLOR:
            if self.is_signal_place:
                # Hexagons only for signal places (no arcs)
                self._draw_hexagon_path(cr, self.x, self.y, self.radius + 2 / zoom)
            elif self.is_regulatory_place:
                # Double circles for regulatory places (genes/resources)
                cr.arc(self.x, self.y, self.radius + 2 / zoom, 0, 2 * math.pi)
            else:
                # Circles for compartment places (have arcs)
                cr.arc(self.x, self.y, self.radius + 2 / zoom, 0, 2 * math.pi)
            r, g, b = display_color
            cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
            cr.set_line_width((self.border_width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw shape based on type
        if self.is_signal_place:
            # Draw hexagon ONLY for signal places (no arcs - Bio-PN Ψ)
            self._draw_hexagon_path(cr, self.x, self.y, self.radius)
        else:
            # Draw circle for all other places (including compartment places with arcs)
            cr.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
        
        cr.set_source_rgb(*display_color)
        cr.set_line_width(self.border_width / max(zoom, 1e-6))  # Compensate for zoom
        cr.stroke()
        
        # Selection rendering moved to ObjectEditingTransforms in src/shypn/api/edit/
        
        # Draw Ψ symbol for signal places (when no tokens shown)
        if self.is_signal_place and self.tokens == 0:
            self._render_signal_symbol(cr, self.x, self.y, self.radius, zoom)
        
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
        text = str(self.tokens) if isinstance(self.tokens, int) else f"{self.tokens:.3f}"
        extents = cr.text_extents(text)
        text_x = x - extents.width / 2
        text_y = y + extents.height / 2
        cr.move_to(text_x, text_y)
        cr.show_text(text)
        cr.fill()
        
        # Clear path to prevent spurious lines to text position
        cr.new_path()
    
    def _render_signal_symbol(self, cr, x: float, y: float, radius: float, zoom: float = 1.0):
        """Render Ψ (psi) symbol inside signal place hexagons.
        
        Signal places are marked with the Greek letter Ψ (psi) to indicate
        information flow without mass transfer. Optional subscript shows signal type.
        
        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            radius: Hexagon radius (world space)
            zoom: Current zoom level for font size compensation
        """
        # Draw Ψ symbol (Unicode U+03A8)
        cr.set_source_rgb(0.0, 0.0, 0.0)  # Black color (normalized color scheme)
        cr.select_font_face("Sans", 0, 0)  # Normal weight for Ψ
        cr.set_font_size(16 / zoom)  # Slightly larger than tokens
        
        psi_symbol = "Ψ"
        extents = cr.text_extents(psi_symbol)
        text_x = x - extents.width / 2
        text_y = y + extents.height / 2
        
        cr.move_to(text_x, text_y)
        cr.show_text(psi_symbol)
        cr.fill()
        
        # Draw subscript type indicator if signal_type is set
        if self.signal_type:
            # Map signal types to subscripts
            type_subscripts = {
                'quorum': 'q',
                'energy': 'e',
                'regulatory': 'r',
                'spatial': 's'
            }
            
            signal_type_name = self.signal_type.value if hasattr(self.signal_type, 'value') else str(self.signal_type)
            subscript = type_subscripts.get(signal_type_name, '?')
            
            # Draw subscript (smaller, slightly offset)
            cr.set_font_size(10 / zoom)
            sub_extents = cr.text_extents(subscript)
            sub_x = text_x + extents.width - 2 / zoom
            sub_y = text_y + 6 / zoom  # Below baseline
            
            cr.move_to(sub_x, sub_y)
            cr.show_text(subscript)
            cr.fill()
        
        # Clear path
        cr.new_path()
    
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
        
        # Clear path to prevent spurious lines to text position
        cr.new_path()
    
    def _draw_hexagon_path(self, cr, x: float, y: float, radius: float):
        """Draw a regular hexagon path for signal places.
        
        Signal places (Ψ) are rendered as hexagons to distinguish them from
        regular circular places. The hexagon is oriented with flat top/bottom.
        
        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            radius: Distance from center to vertex (world space)
        """
        # Regular hexagon with flat top/bottom (6 vertices)
        # Start at top vertex and draw clockwise
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3  # 30°, 90°, 150°, 210°, 270°, 330°
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            
            if i == 0:
                cr.move_to(px, py)
            else:
                cr.line_to(px, py)
        
        cr.close_path()
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this place.
        
        For signal places (hexagons), uses approximate circular hit testing.
        For regular places, uses exact circular hit testing.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is inside the shape
        """
        dx = x - self.x
        dy = y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # For hexagons, use inscribed circle for hit testing (conservative)
        # Hexagon's inscribed circle radius ≈ 0.866 * circumradius
        if self.is_signal_place:
            return distance <= (self.radius * 0.866)
        else:
            return distance <= self.radius
    
    def set_position(self, x: float, y: float):
        """Move the place to a new position.
        
        Args:
            x, y: New position (world space)
        """
        self.x = x
        self.y = y
        self._trigger_redraw()
    
    def set_tokens(self, count: float):
        """Set the number of tokens in this place.
        
        Supports both discrete (int) and continuous (float) concentrations.
        For stochastic/continuous simulations, accepts floating-point values.
        
        Respects capacity constraint if set.
        
        Args:
            count: Token count or concentration (non-negative, will be capped at capacity)
        """
        count = max(0.0, float(count))
        # Handle capacity: None and float('inf') both mean unlimited
        if self.capacity is not None and self.capacity != float('inf'):
            count = min(count, float(self.capacity))
        self.tokens = count
        self._trigger_redraw()
    
    def set_initial_marking(self, count: float):
        """Set the initial marking for this place (for simulation reset).
        
        Supports both discrete (int) and continuous (float) concentrations.
        
        Args:
            count: Initial token count or concentration (non-negative)
        """
        self.initial_marking = max(0.0, float(count))
    
    def reset_to_initial_marking(self):
        """Reset the current marking to the initial marking."""
        self.tokens = self.initial_marking
        self._trigger_redraw()
    
    def to_dict(self) -> dict:
        """Serialize place to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all place properties
        """
        data = super().to_dict()  # Get base properties (id, name, label)
        data.update({
            "object_type": "place",  # Renamed from "type" to avoid confusion
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "marking": self.tokens,  # Use 'marking' for compatibility
            "initial_marking": self.initial_marking,  # Store initial marking for reset
            "capacity": "Infinity" if self.capacity == float('inf') else self.capacity,  # Normalize infinity to string for JSON
            "border_color": list(self.border_color),
            "border_width": self.border_width,
            "is_catalyst": getattr(self, 'is_catalyst', False),  # Save catalyst flag
            "is_signal_place": getattr(self, 'is_signal_place', False),  # Save signal place flag (13-tuple Ψ)
            "is_regulatory_place": getattr(self, 'is_regulatory_place', False)  # Save regulatory place flag
        })
        
        # Serialize metadata (KEGG IDs, ChEBI IDs, data sources, etc.)
        if hasattr(self, 'metadata') and self.metadata:
            data["metadata"] = self.metadata
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Place':
        """Create place from dictionary (deserialization).
        
        All IDs must be in correct string format with "P" prefix (e.g., "P1", "P101").
        
        Args:
            data: Dictionary containing place properties
            
        Returns:
            Place: New place instance with restored properties
            
        Raises:
            ValueError: If ID format is invalid
        """
        # Validate ID format - must be string with "P" prefix
        raw_id = data.get("id")
        place_id = str(raw_id)
        
        if not place_id.startswith("P"):
            raise ValueError(
                f"Invalid place ID format: '{place_id}'. "
                f"Place IDs must start with 'P' (e.g., 'P1', 'P101')"
            )
        
        name = str(data.get("name", place_id))
        
        place = cls(
            x=float(data["x"]),
            y=float(data["y"]),
            id=place_id,  # String ID
            name=name,
            radius=float(data.get("radius", cls.DEFAULT_RADIUS)),
            label=str(data.get("label", ""))
        )
        
        # Restore optional properties
        if "marking" in data:
            place.tokens = data["marking"]
        if "initial_marking" in data:
            place.initial_marking = data["initial_marking"]
        else:
            # If no initial_marking stored, use current marking as initial
            place.initial_marking = place.tokens
        
        # Restore catalyst flag (for hierarchical layout)
        place.is_catalyst = data.get("is_catalyst", False)
        # Restore signal place flag (13-tuple formalism: Ψ)
        place.is_signal_place = data.get("is_signal_place", False)
        # Restore regulatory place flag (genes/resources)
        place.is_regulatory_place = data.get("is_regulatory_place", False)
        if "capacity" in data:
            capacity_value = data["capacity"]
            # Normalize capacity: handle string "Infinity" or "inf"
            if isinstance(capacity_value, str) and capacity_value.lower() in ('infinity', 'inf'):
                place.capacity = float('inf')
            else:
                place.capacity = capacity_value
        if "border_color" in data:
            place.border_color = tuple(data["border_color"])
        if "border_width" in data:
            place.border_width = data["border_width"]
        
        # Restore metadata (KEGG IDs, ChEBI IDs, data sources, etc.)
        if "metadata" in data:
            place.metadata = data["metadata"]
        
        return place
