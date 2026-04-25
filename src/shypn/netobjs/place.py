#!/usr/bin/env python3
"""Place - Circular node in a Petri net.

Places represent conditions or states and can contain tokens.
Rendered as a circle with optional label and token display.
"""
import math
from typing import Any, List, Optional, Tuple
from enum import Enum
from shypn.netobjs.petri_net_object import PetriNetObject
from shypn.netobjs.signal_type import SignalType


class BoundaryType(Enum):
    """Compartment boundary permeability for spatial signal places.
    
    Controls whether signals can cross compartment boundaries and how.
    """
    PERMEABLE = "permeable"      # Free diffusion across boundary
    SELECTIVE = "selective"       # Requires specific transport transition
    IMPERMEABLE = "impermeable"  # Cannot cross boundary


class Place(PetriNetObject):
    """A circular place in a Petri net.
    
    Places represent conditions or states and can contain tokens.
    Rendered as a circle with optional label and token display.
    """
    
    # Default styling (proportional metrics at 1:1 scale)
    DEFAULT_RADIUS = 40.0  # 40px radius = 80px diameter at 100% zoom
    DEFAULT_BORDER_COLOR = (0.0, 0.0, 0.0)  # Black border
    SIGNAL_BORDER_COLOR = (0.0, 0.4, 0.8)  # Blue border for signal places
    DEFAULT_BORDER_WIDTH = 3.0  # 3px for better visibility
    
    def __init__(self, x: float, y: float, id: str, name: str,
                 radius: Optional[float] = None, label: str = ""):
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
        
        # Styling - will be set properly after properties are initialized
        self.border_color = self.DEFAULT_BORDER_COLOR  # Temporary, updated below
        self.border_width = self.DEFAULT_BORDER_WIDTH
        
        # State
        self.tokens: float = 0.0  # Number of tokens in this place
        self.initial_marking: float = 0.0  # Initial marking for simulation reset
        self.capacity = float('inf')  # Maximum token capacity (infinite by default)
        
        # Signal place properties (13-tuple Bio-PN formalism: Ψ)
        # Signal places are any places designated by the modeller as belonging to Ψ ⊆ P.
        # They participate in both normal arcs (F) and signal flow arcs (F_s).
        # Signal flow arcs ARE consumptive — they consume/produce Ws tokens just like
        # normal arcs, AND make the place's marking visible to the signal hierarchy.
        self.is_signal_place = False  # True when this place is in Ψ (modeller-designated signal place)
        self.signal_type: Optional[SignalType] = None  # Classification: quorum, energy, regulatory, spatial
        self.signal_scope: List[str] = []  # Module IDs that can read this signal (empty = global scope)
        
        # Regulatory place properties (gene loci, constant resources)
        # Regulatory places represent genetic elements or constant resource pools
        self.is_regulatory_place = False  # True if this is a gene locus or constant resource
        
        # Energy/metabolic cofactor places (ATP, ADP, GTP, GDP, Pi, etc.)
        # Participate in kinetics via rate functions (Φ), not signal hierarchy
        self.is_energy_place = False  # True if metabolic cofactor (rendered with amber border)

        # Parameter places (exogenous experimental constants — NOT consumed/produced
        # by the reaction network). Read by events, rate functions, or triggers as a
        # constant scalar. Their `initial_marking` is varied across sweep snapshots
        # (factorial mode). Examples: dose, dosing interval, redose time, applied
        # stressor magnitude, ambient pH/temperature when used as a knob.
        # Orthogonal to is_signal_place and is_energy_place.
        self.is_parameter_place: bool = False
        self.parameter_kind: Optional[str] = None    # e.g. 'dose', 'interval', 'time', 'stressor', 'environment'
        self.parameter_units: Optional[str] = None   # e.g. 'µM', 's', 'mg/kg', 'K', 'pH'
        
        # Module assignment (modular Bio-PN architecture)
        # Places belong to modules, enabling network partitioning and compartmentalization
        self.module_id: Optional[str] = None  # Module identifier (e.g., "M_cytoplasm", "M_mitochondria")
        
        # Compartment place marker (backward compatibility)
        # is_compartment_place: True if in non-default compartment (e.g., extracellular)
        #   Rendered as violet circle (NOT hexagon - those are only for signal places)
        self.is_compartment_place = False
        
        # Spatial signal properties (Layer 1 - SPATIAL signals)
        # These properties govern behavior of connected transitions and enable spatial modeling
        self.diffusion_coefficient: Optional[float] = None  # μm²/s - diffusion rate
        self.boundary_type: Optional[BoundaryType] = None  # Permeability control
        self.gradient_vector: Optional[Tuple[float, float, float]] = None  # (dx, dy, dz) direction
        self.compartment_volume: Optional[float] = None  # fL - scales stochasticity
        self.neighbor_compartments: List[str] = []  # Adjacent compartment IDs
        self.spatial_position: Optional[Tuple[float, float, float]] = None  # (x, y, z) in μm
        self.compartment: Optional[str] = None  # Compartment name (e.g., "cytoplasm", "membrane", "extracellular")
        
        # Protected attributes - use properties/methods to access
        self._properties: dict[str, Any] = {}  # Private: place-specific parameters
        self._metadata: dict[str, Any] = {}    # Private: annotations, provenance

        # Optional attributes set dynamically (e.g., from_dict)
        self.is_catalyst: bool = False  # Catalyst flag (set by importers/layout)
        
        # Apply color schema based on place type (after all properties initialized)
        from shypn.utils.color_schema_manager import ColorSchemaManager
        self.border_color = ColorSchemaManager.get_place_border_color(self)
    
    # ========== Property Decorators (OOP Pattern) ==========
    
    @property
    def properties(self) -> dict:
        """Get properties dict (for backward compatibility).
        
        Returns:
            dict: Properties dictionary
        """
        return self._properties
    
    @properties.setter
    def properties(self, value: dict) -> None:
        """Set properties dict (for backward compatibility).
        
        Args:
            value: Properties dictionary
        
        Raises:
            TypeError: If value is not a dict
        """
        if value is not None and not isinstance(value, dict):
            raise TypeError("Properties must be a dictionary")
        self._properties = value if value is not None else {}
    
    @property
    def metadata(self) -> dict:
        """Get metadata dict (for annotations and provenance).
        
        Returns:
            dict: Metadata dictionary
        """
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: dict) -> None:
        """Set metadata dict with validation.
        
        Args:
            value: Metadata dictionary
        
        Raises:
            TypeError: If value is not a dict
        """
        if value is not None and not isinstance(value, dict):
            raise TypeError("Metadata must be a dictionary")
        self._metadata = value if value is not None else {}
    
    # ========== End Property Decorators ==========
    
    def get_bounding_box(self) -> dict:
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
    
    def render(self, cr: Any, zoom: float = 1.0) -> None:  # type: ignore[override]
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
            if self.is_parameter_place:
                # Rounded square for parameter places (experiment-plan, NOT object-net)
                self._draw_rounded_square_path(cr, self.x, self.y, self.radius + 2 / zoom)
            elif self.is_signal_place and self._is_spatial_carrier():
                # Diamond for SPATIAL signal places (environmental scalar,
                # NOT in cascade preemption / POSet, may be remote-sensed via Φ)
                self._draw_diamond_path(cr, self.x, self.y, self.radius + 2 / zoom)
            elif self.is_signal_place:
                # Hexagons only for biological signal places (Ψ, in cascade)
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
        
        # Draw shape based on type — parameter places take priority over signal places
        # because they are NOT part of the object-net topology and must be visually
        # distinct from any biological place (circle or hexagon).
        if self.is_parameter_place:
            # Rounded square for parameter places (experiment-plan metadata)
            self._draw_rounded_square_path(cr, self.x, self.y, self.radius)
        elif self.is_signal_place and self._is_spatial_carrier():
            # Diamond for SPATIAL signal places: environmental/spatial scalar,
            # outside the biological cascade (no PreemptionCheck, no POSet layer).
            # Read remotely by Φ in many transitions, written by events.
            self._draw_diamond_path(cr, self.x, self.y, self.radius)
        elif self.is_signal_place:
            # Draw hexagon for biological signal places (Ψ, in cascade)
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
        except (AttributeError, RuntimeError) as e:
            # Arial font not available, use fallback
            import logging
            logging.getLogger(__name__).debug(f"Arial font not available: {e}")
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
    
    def _is_spatial_carrier(self) -> bool:
        """True iff this place is a SPATIAL signal carrier.

        Per HPN formalism doc §3 and the spatial-vs-biological signal split:
        a signal place flagged as ``signal_type == SignalType.SPATIAL`` is an
        **environmental scalar** — it carries protocol-derived (event-fed)
        values that biology rates may remote-sense via Φ, but it does **not**
        participate in the cascade preemption (PreemptionCheck) nor in the
        POSet layer assignment. This distinguishes it from biological
        signal places (NFkB_p65, Aβ_Oligomer, …) that *are* commitment
        signals in the layered information graph G_s.

        Returns:
            bool: True if this is a signal place AND its signal_type is
            SignalType.SPATIAL.
        """
        if not getattr(self, 'is_signal_place', False):
            return False
        try:
            from shypn.netobjs.signal_type import SignalType
            return getattr(self, 'signal_type', None) == SignalType.SPATIAL
        except ImportError:
            return False

    def _draw_diamond_path(self, cr, x: float, y: float, radius: float):
        """Draw a diamond (rotated square) path for SPATIAL signal places.

        The diamond glyph marks signal places whose ``signal_type`` is
        ``SignalType.SPATIAL`` — environmental / spatial scalars that
        biology rates may read via Φ but that do not participate in the
        biological cascade (no PreemptionCheck, no POSet layer). Visually
        distinct from the hexagon ⬡ (biological signal place, in cascade)
        and the rounded square ▢ (parameter place, outside both graphs).

        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            radius: Distance from center to vertex (world space)
        """
        cr.move_to(x, y - radius)        # top
        cr.line_to(x + radius, y)        # right
        cr.line_to(x, y + radius)        # bottom
        cr.line_to(x - radius, y)        # left
        cr.close_path()

    def _draw_rounded_square_path(self, cr, x: float, y: float, radius: float):
        """Draw a rounded-square path for parameter places.
        
        Parameter places carry experiment-planning metadata (DSev, dose,
        env knobs). They are NOT part of the object-net topology and must
        not be confused with biological places (circles) or signal places
        (hexagons). The rounded square is the visual marker that this node
        sits outside both the execution graph G_E and the information
        graph G_s.
        
        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            radius: Half-side of the bounding square (world space)
        """
        # Square inscribed in the radius bounding box, with corner radius
        # ~25% of the side length so the rounding is clearly visible.
        side = 2.0 * radius
        half = radius
        cr_corner = side * 0.25
        
        x0 = x - half
        y0 = y - half
        x1 = x + half
        y1 = y + half
        
        # Trace clockwise from top-left arc end
        cr.new_sub_path()
        cr.arc(x0 + cr_corner, y0 + cr_corner, cr_corner, math.pi,         3 * math.pi / 2)
        cr.arc(x1 - cr_corner, y0 + cr_corner, cr_corner, 3 * math.pi / 2, 2 * math.pi)
        cr.arc(x1 - cr_corner, y1 - cr_corner, cr_corner, 0,               math.pi / 2)
        cr.arc(x0 + cr_corner, y1 - cr_corner, cr_corner, math.pi / 2,     math.pi)
        cr.close_path()
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this place.
        
        For signal places (hexagons), uses approximate circular hit testing.
        For parameter places (rounded squares), uses square bounding-box test.
        For regular places, uses exact circular hit testing.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is inside the shape
        """
        dx = x - self.x
        dy = y - self.y
        
        # Parameter places: square bounding-box test (rounded square shape)
        if self.is_parameter_place:
            return abs(dx) <= self.radius and abs(dy) <= self.radius
        
        # Spatial signal places: diamond hit-test (|dx| + |dy| <= radius)
        if self._is_spatial_carrier():
            return abs(dx) + abs(dy) <= self.radius
        
        distance = math.sqrt(dx * dx + dy * dy)
        
        # For hexagons, use inscribed circle for hit testing (conservative)
        # Hexagon's inscribed circle radius ≈ 0.866 * circumradius
        if self.is_signal_place:
            return distance <= (self.radius * 0.866)
        else:
            return distance <= self.radius
    
    def set_position(self, x: float, y: float) -> None:
        """Move the place to a new position.
        
        Args:
            x, y: New position (world space)
        """
        self.x = x
        self.y = y
        self._trigger_redraw()
    
    def set_tokens(self, count: float) -> None:
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
    
    def set_initial_marking(self, count: float) -> None:
        """Set the initial marking for this place (for simulation reset).
        
        Supports both discrete (int) and continuous (float) concentrations.
        
        Args:
            count: Initial token count or concentration (non-negative)
        """
        self.initial_marking = max(0.0, float(count))
    
    def reset_to_initial_marking(self) -> None:
        """Reset the current marking to the initial marking."""
        self.tokens = self.initial_marking
        self._trigger_redraw()
    
    # ============================================================================
    # Spatial Signal Helper Methods (Layer 1)
    # ============================================================================
    
    def is_spatial_signal(self) -> bool:
        """Check if this place is a spatial signal (Layer 1).
        
        Returns:
            bool: True if signal_type is SPATIAL
        """
        return self.signal_type == SignalType.SPATIAL
    
    def set_diffusion_properties(
        self,
        coefficient: float,
        boundary: BoundaryType,
        volume: Optional[float] = None
    ) -> None:
        """Set diffusion properties for spatial signal place.
        
        Args:
            coefficient: Diffusion coefficient in μm²/s
            boundary: Boundary permeability type
            volume: Optional compartment volume in fL
        """
        self.diffusion_coefficient = coefficient
        self.boundary_type = boundary
        if volume is not None:
            self.compartment_volume = volume
    
    def set_spatial_gradient(self, dx: float, dy: float, dz: float = 0.0) -> None:
        """Set spatial gradient vector.
        
        Args:
            dx: Gradient component in x direction
            dy: Gradient component in y direction
            dz: Gradient component in z direction (default 0)
        """
        self.gradient_vector = (dx, dy, dz)
    
    def add_neighbor_compartment(self, compartment_id: str) -> None:
        """Add a neighbor compartment ID to topology.
        
        Args:
            compartment_id: ID of adjacent compartment
        """
        if compartment_id not in self.neighbor_compartments:
            self.neighbor_compartments.append(compartment_id)
    
    def is_neighbor(self, compartment_id: str) -> bool:
        """Check if given compartment is a neighbor.
        
        Args:
            compartment_id: ID to check
        
        Returns:
            bool: True if compartment_id is in neighbor list
        """
        return compartment_id in self.neighbor_compartments
    
    def get_gradient_magnitude(self) -> float:
        """Calculate magnitude of gradient vector.
        
        Returns:
            float: ||gradient|| or 0.0 if not set
        """
        if self.gradient_vector is None:
            return 0.0
        
        dx, dy, dz = self.gradient_vector
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def get_spatial_distance(self, other: 'Place') -> Optional[float]:
        """Calculate Euclidean distance to another place.
        
        Args:
            other: Target place
        
        Returns:
            float: Distance in μm, or None if positions not set
        """
        if self.spatial_position is None or other.spatial_position is None:
            return None
        
        x1, y1, z1 = self.spatial_position
        x2, y2, z2 = other.spatial_position
        
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def should_use_stochastic(self, threshold_volume: float = 1.0) -> bool:
        """Check if compartment volume suggests stochastic dynamics.
        
        Args:
            threshold_volume: Volume threshold in fL (default 1.0)
        
        Returns:
            bool: True if volume < threshold (use stochastic)
        """
        if self.compartment_volume is None:
            return False  # No volume set - default to continuous
        
        return self.compartment_volume < threshold_volume
    
    # ============================================================================
    # Serialization
    # ============================================================================
    
    def _serialize_signal_type(self) -> Optional[str]:
        """Serialize signal_type to string for persistence.
        
        Handles both SignalType enum and string values since signal_type
        can be set from UI dialog (string) or from loading (enum).
        
        Returns:
            str or None: Signal type as string ('energy', 'spatial', etc.) or None
        """
        if self.signal_type is None:
            return None
        
        # Handle SignalType enum
        if hasattr(self.signal_type, 'value'):
            return str(self.signal_type.value)
        
        # Already a string (set from dialog)
        if isinstance(self.signal_type, str):
            return self.signal_type
        
        # Fallback: convert to string
        return str(self.signal_type)
    
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
            # CRITICAL DISTINCTION:
            # - initial_marking: Static design-time baseline (used for simulation reset)
            # - marking/tokens: Transient runtime state (may be mid-simulation)
            # For file persistence, we save initial_marking as the canonical baseline
            # and also save current tokens for recovery of in-progress states
            "marking": self.initial_marking,  # Use initial_marking as canonical baseline
            "tokens": self.tokens,  # Also save current transient state for recovery
            "initial_marking": self.initial_marking,  # Explicit field for clarity
            "capacity": "Infinity" if self.capacity == float('inf') else self.capacity,  # Normalize infinity to string for JSON
            "border_color": list(self.border_color),
            "border_width": self.border_width,
            "is_catalyst": getattr(self, 'is_catalyst', False),  # Save catalyst flag
            "is_signal_place": getattr(self, 'is_signal_place', False),  # Save signal place flag (13-tuple Ψ)
            "signal_type": self._serialize_signal_type(),  # Save signal classification (energy/spatial/quorum/regulatory)
            "is_compartment_place": getattr(self, 'is_compartment_place', False),  # Save compartment place flag
            "is_regulatory_place": getattr(self, 'is_regulatory_place', False),  # Save regulatory place flag
            "is_energy_place": getattr(self, 'is_energy_place', False),  # Save energy/metabolic cofactor flag
            "is_parameter_place": getattr(self, 'is_parameter_place', False),  # Save parameter place flag (exogenous constant)
            "parameter_kind": getattr(self, 'parameter_kind', None),
            "parameter_units": getattr(self, 'parameter_units', None),
            
            # Spatial signal properties (Layer 1)
            "diffusion_coefficient": getattr(self, 'diffusion_coefficient', None),
            "boundary_type": self.boundary_type.value if hasattr(self, 'boundary_type') and self.boundary_type else None,
            "gradient_vector": list(self.gradient_vector) if hasattr(self, 'gradient_vector') and self.gradient_vector else None,
            "compartment_volume": getattr(self, 'compartment_volume', None),
            "neighbor_compartments": getattr(self, 'neighbor_compartments', []),
            "spatial_position": list(self.spatial_position) if hasattr(self, 'spatial_position') and self.spatial_position else None,
        })
        
        # Serialize compartment name (biological assignment: membrane/cytoplasm/extracellular)
        if hasattr(self, 'compartment') and self.compartment is not None:
            data["compartment"] = self.compartment
        
        # Serialize metadata (KEGG IDs, ChEBI IDs, data sources, etc.)
        if hasattr(self, 'metadata') and self.metadata:
            data["metadata"] = self.metadata
        
        # Serialize properties (thermodynamic data, custom parameters, etc.)
        if hasattr(self, '_properties') and self._properties:
            data["properties"] = self._properties
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Place':
        """Create place from dictionary (deserialization).
        
        Supports both clean OOP format (flat structure) and legacy format (attrs nested).
        All IDs must be in correct string format with "P" prefix (e.g., "P1", "P101").
        
        Args:
            data: Dictionary containing place properties
            
        Returns:
            Place: New place instance with restored properties
            
        Raises:
            ValueError: If ID format is invalid
        """
        # BACKWARD COMPATIBILITY: Check if old nested 'attrs' format
        # If attrs exists, merge it with root level (attrs takes precedence for conflicts)
        if 'attrs' in data:
            # Legacy format detected - merge attrs into root level
            attrs = data['attrs']
            # Create merged dict: start with root, overlay attrs
            merged = {**data, **attrs}
            # Remove attrs key from merged dict to avoid recursion
            merged.pop('attrs', None)
            data = merged
        
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
            x=float(data.get("x", 0.0)),  # Default to 0.0 if missing (legacy file support)
            y=float(data.get("y", 0.0)),  # Default to 0.0 if missing (legacy file support)
            id=place_id,  # String ID
            name=name,
            radius=float(data.get("radius", cls.DEFAULT_RADIUS)),
            label=str(data.get("label", ""))
        )
        
        # Restore optional properties with CLEAR SEPARATION of static vs transient data
        # Priority: initial_marking (design-time) > marking (legacy compatibility) > tokens (transient)
        if "initial_marking" in data:
            # Modern format: initial_marking is the authoritative baseline
            place.initial_marking = float(data["initial_marking"])
            # Set tokens from saved transient state if available, else use initial_marking
            place.tokens = float(data.get("tokens", place.initial_marking))
        elif "marking" in data:
            # Legacy format: marking was used for both (ambiguous)
            # Assume marking is the baseline and use it for both
            place.initial_marking = float(data["marking"])
            place.tokens = float(data["marking"])
        else:
            # No marking data found - use defaults
            place.initial_marking = 0.0
            place.tokens = 0.0
        
        # Restore catalyst flag (for hierarchical layout)
        place.is_catalyst = data.get("is_catalyst", False)
        # Restore signal place flag (13-tuple formalism: Ψ)
        place.is_signal_place = data.get("is_signal_place", False)
        # Restore energy/metabolic cofactor flag
        place.is_energy_place = data.get("is_energy_place", False)
        
        # Restore signal type classification (energy/spatial/quorum/regulatory)
        signal_type_str = data.get("signal_type")
        if not signal_type_str and "properties" in data:
            # Fallback: check properties dict for signal_type
            signal_type_str = data["properties"].get("signal_type")
        
        if signal_type_str:
            try:
                # Normalize to lowercase for enum lookup
                signal_type_str = str(signal_type_str).lower()
                place.signal_type = SignalType(signal_type_str)
            except (ValueError, KeyError) as e:
                # Invalid signal type - log warning and set to None
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Invalid signal_type '{signal_type_str}' for place {place.id}. "
                    f"Valid types: energy, spatial, quorum, regulatory. Setting to None."
                )
                place.signal_type = None
        else:
            place.signal_type = None
        
        # Restore compartment place flag (non-default compartments)
        place.is_compartment_place = data.get("is_compartment_place", False)
        # Restore regulatory place flag (genes/resources)
        place.is_regulatory_place = data.get("is_regulatory_place", False)
        # Restore parameter place flag (exogenous experimental constant)
        place.is_parameter_place = data.get("is_parameter_place", False)
        place.parameter_kind = data.get("parameter_kind", None)
        place.parameter_units = data.get("parameter_units", None)
        if "capacity" in data:
            capacity_value = data["capacity"]
            # Normalize capacity: handle string "Infinity" or "inf"
            if isinstance(capacity_value, str) and capacity_value.lower() in ('infinity', 'inf'):
                place.capacity = float('inf')
            else:
                place.capacity = capacity_value
        
        # Color handling: Always enforce color schema for semantic types
        from shypn.utils.color_schema_manager import ColorSchemaManager
        if ColorSchemaManager.is_semantic_place_color(place):
            # Semantic places (signal, energy, compartment, regulatory) always get schema color
            ColorSchemaManager.reset_place_color(place)
        elif "border_color" in data:
            # Non-semantic places use saved color (may be analysis/recording color)
            place.border_color = tuple(data["border_color"])
        else:
            # Fallback to default black for regular places
            place.border_color = Place.DEFAULT_BORDER_COLOR
        
        if "border_width" in data:
            place.border_width = data["border_width"]
        
        # Restore metadata (KEGG IDs, ChEBI IDs, data sources, etc.)
        if "metadata" in data:
            place.metadata = data["metadata"]
        
        # Restore properties (thermodynamic data, custom parameters, etc.)
        if "properties" in data:
            place.properties = data["properties"]
        
        # Restore spatial signal properties (Layer 1)
        place.diffusion_coefficient = data.get("diffusion_coefficient", None)
        
        boundary_str = data.get("boundary_type", None)
        if boundary_str:
            try:
                place.boundary_type = BoundaryType(boundary_str)
            except (ValueError, KeyError):
                place.boundary_type = None
        else:
            place.boundary_type = None
        
        gradient = data.get("gradient_vector", None)
        place.gradient_vector = tuple(gradient) if gradient else None
        
        # Load compartment volume (check both top-level and properties dict)
        place.compartment_volume = data.get("compartment_volume", None)
        if place.compartment_volume is None and "properties" in data:
            place.compartment_volume = data["properties"].get("compartment_volume", None)
        
        # Load compartment name
        if "compartment" in data:
            place.compartment = data["compartment"]
        
        place.neighbor_compartments = data.get("neighbor_compartments", [])
        
        position = data.get("spatial_position", None)
        place.spatial_position = tuple(position) if position else None
        
        return place

    def __repr__(self) -> str:
        """Machine-readable representation for debugging."""
        return (
            f"Place(id={self.id!r}, name={self.name!r}, "
            f"tokens={self.tokens})"
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.name} ({self.tokens} tok)" if self.name else self.id
