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
        
        # Behavioral properties
        self.transition_type = 'immediate'  # Transition type: immediate, timed, stochastic, continuous
        self.enabled = True  # Can this transition fire?
        self.guard = None  # Guard function/expression (enables/disables transition)
        self.rate = None  # Rate function for consumption/production dynamics
        self.priority = 0  # Priority for conflict resolution (higher = higher priority)
        
        # Source/Sink markers
        self.is_source = False  # Source transition (generates tokens without input)
        self.is_sink = False    # Sink transition (consumes tokens without output)
    
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
        
        # Add glow effect for colored objects (CSS-like styling)
        if self.border_color != self.DEFAULT_BORDER_COLOR or self.fill_color != self.DEFAULT_COLOR:
            # Draw outer glow (subtle shadow effect)
            cr.rectangle(self.x - half_w - 2 / zoom, self.y - half_h - 2 / zoom, 
                        width + 4 / zoom, height + 4 / zoom)
            
            # Use border color for glow if different from default, otherwise use fill color
            if self.border_color != self.DEFAULT_BORDER_COLOR:
                r, g, b = self.border_color
            else:
                r, g, b = self.fill_color
            
            cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
            cr.set_line_width((self.border_width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw rectangle (legacy style: fill_preserve then stroke)
        cr.rectangle(self.x - half_w, self.y - half_h, width, height)
        cr.set_source_rgb(*self.fill_color)
        cr.fill_preserve()  # Fill but keep path for border
        
        # Draw border (legacy style: 3.0px compensated for zoom)
        cr.set_source_rgb(*self.border_color)
        cr.set_line_width(self.border_width / max(zoom, 1e-6))
        cr.stroke()
        
        # Draw source/sink markers
        self._render_source_sink_markers(cr, self.x, self.y, width, height, zoom)
        
        # Selection rendering moved to ObjectEditingTransforms in src/shypn/api/edit/
        
        # Draw label if provided
        if self.label:
            self._render_label(cr, self.x, self.y, height, self.horizontal, zoom)
    
    def _render_source_sink_markers(self, cr, x: float, y: float, width: float, height: float, zoom: float = 1.0):
        """Render source/sink markers on the transition.
        
        Source transitions get an incoming arrow from the left (or top if vertical).
        Sink transitions get an outgoing arrow to the right (or bottom if vertical).
        
        Args:
            cr: Cairo context
            x, y: Center position (world coords)
            width, height: Rectangle dimensions (already swapped if vertical)
            zoom: Current zoom level (not used - markers scale with zoom)
        """
        # Markers scale with zoom (world space) to match transition size
        arrow_length = 20.0  # Length of arrow in world units
        arrow_head_size = 6.0  # Size of arrow head in world units
        line_width = 2.0  # Line width for arrow in world units
        
        # Use border color for marker, or black if default
        if self.border_color != self.DEFAULT_BORDER_COLOR:
            r, g, b = self.border_color
        else:
            r, g, b = (0.0, 0.0, 0.0)  # Black
        
        cr.set_source_rgb(r, g, b)
        cr.set_line_width(line_width)
        
        # Source marker (incoming arrow)
        if self.is_source:
            if self.horizontal:
                # Arrow pointing right into left side of transition
                start_x = x - width / 2 - arrow_length
                start_y = y
                end_x = x - width / 2
                end_y = y
                
                # Draw arrow shaft
                cr.save()
                cr.move_to(start_x, start_y)
                cr.line_to(end_x, end_y)
                cr.stroke()
                cr.restore()
                
                # Draw arrow head (filled triangle)
                cr.save()
                cr.move_to(end_x, end_y)
                cr.line_to(end_x - arrow_head_size, end_y - arrow_head_size / 2)
                cr.line_to(end_x - arrow_head_size, end_y + arrow_head_size / 2)
                cr.close_path()
                cr.fill()
                cr.restore()
            else:
                # Vertical: Arrow pointing down into top side of transition
                start_x = x
                start_y = y - height / 2 - arrow_length
                end_x = x
                end_y = y - height / 2
                
                # Draw arrow shaft
                cr.save()
                cr.move_to(start_x, start_y)
                cr.line_to(end_x, end_y)
                cr.stroke()
                cr.restore()
                
                # Draw arrow head (filled triangle)
                cr.save()
                cr.move_to(end_x, end_y)
                cr.line_to(end_x - arrow_head_size / 2, end_y - arrow_head_size)
                cr.line_to(end_x + arrow_head_size / 2, end_y - arrow_head_size)
                cr.close_path()
                cr.fill()
                cr.restore()
        
        # Sink marker (outgoing arrow)
        if self.is_sink:
            if self.horizontal:
                # Arrow pointing right from right side of transition
                start_x = x + width / 2
                start_y = y
                end_x = x + width / 2 + arrow_length
                end_y = y
                
                # Draw arrow shaft
                cr.save()
                cr.move_to(start_x, start_y)
                cr.line_to(end_x, end_y)
                cr.stroke()
                cr.restore()
                
                # Draw arrow head (filled triangle)
                cr.save()
                cr.move_to(end_x, end_y)
                cr.line_to(end_x - arrow_head_size, end_y - arrow_head_size / 2)
                cr.line_to(end_x - arrow_head_size, end_y + arrow_head_size / 2)
                cr.close_path()
                cr.fill()
                cr.restore()
            else:
                # Vertical: Arrow pointing down from bottom side of transition
                start_x = x
                start_y = y + height / 2
                end_x = x
                end_y = y + height / 2 + arrow_length
                
                # Draw arrow shaft
                cr.save()
                cr.move_to(start_x, start_y)
                cr.line_to(end_x, end_y)
                cr.stroke()
                cr.restore()
                
                # Draw arrow head (filled triangle)
                cr.save()
                cr.move_to(end_x, end_y)
                cr.line_to(end_x - arrow_head_size / 2, end_y - arrow_head_size)
                cr.line_to(end_x + arrow_head_size / 2, end_y - arrow_head_size)
                cr.close_path()
                cr.fill()
                cr.restore()
    
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
        
        # Clear path to prevent spurious lines to text position
        cr.new_path()
    
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
    
    def to_dict(self) -> dict:
        """Serialize transition to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all transition properties
        """
        data = super().to_dict()  # Get base properties (id, name, label)
        data.update({
            "type": "transition",
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "horizontal": self.horizontal,
            "enabled": self.enabled,
            "fill_color": list(self.fill_color),
            "border_color": list(self.border_color),
            "border_width": self.border_width,
            "transition_type": self.transition_type,
            "priority": self.priority,
            "is_source": self.is_source,
            "is_sink": self.is_sink
        })
        
        # Serialize behavioral properties (guard, rate, properties dict)
        if self.guard is not None:
            data["guard"] = self.guard
        if self.rate is not None:
            data["rate"] = self.rate
        if hasattr(self, 'properties') and self.properties:
            data["properties"] = self.properties
        
        return data
    
    def validate_source_sink_structure(self, arcs_list) -> tuple:
        """Validate that source/sink structure matches formal definition.
        
        Formal definitions (strict):
        - Source transition: •t = ∅ (no input arcs), t• ≠ ∅ (has output arcs)
        - Sink transition: •t ≠ ∅ (has input arcs), t• = ∅ (no output arcs)
        
        Args:
            arcs_list: List of all arcs in the model (or iterable)
            
        Returns:
            tuple: (is_valid: bool, error_message: str, incompatible_arcs: list)
                - is_valid: True if structure is correct, False otherwise
                - error_message: Description of the problem (empty if valid)
                - incompatible_arcs: List of arcs that violate the structure
        """
        incompatible_arcs = []
        
        # Convert dict to list if needed
        if isinstance(arcs_list, dict):
            arcs_list = list(arcs_list.values())
        
        # Find all input and output arcs for this transition
        input_arcs = []
        output_arcs = []
        
        for arc in arcs_list:
            # Check if arc targets this transition (input arc)
            if hasattr(arc, 'target'):
                if arc.target == self or (hasattr(arc.target, 'id') and arc.target.id == self.id):
                    input_arcs.append(arc)
            elif hasattr(arc, 'target_id') and arc.target_id == self.id:
                input_arcs.append(arc)
            
            # Check if arc sources from this transition (output arc)
            if hasattr(arc, 'source'):
                if arc.source == self or (hasattr(arc.source, 'id') and arc.source.id == self.id):
                    output_arcs.append(arc)
            elif hasattr(arc, 'source_id') and arc.source_id == self.id:
                output_arcs.append(arc)
        
        # Validate source transition structure
        if self.is_source:
            if len(input_arcs) > 0:
                incompatible_arcs = input_arcs
                return (
                    False,
                    f"Source transition '{self.name}' cannot have input arcs "
                    f"(found {len(input_arcs)}). Source transitions must have "
                    f"no input places (•t = ∅).",
                    incompatible_arcs
                )
            
            if len(output_arcs) == 0:
                return (
                    False,
                    f"Source transition '{self.name}' must have at least one output arc. "
                    f"Source transitions generate tokens to output places (t• ≠ ∅).",
                    []
                )
        
        # Validate sink transition structure
        if self.is_sink:
            if len(output_arcs) > 0:
                incompatible_arcs = output_arcs
                return (
                    False,
                    f"Sink transition '{self.name}' cannot have output arcs "
                    f"(found {len(output_arcs)}). Sink transitions must have "
                    f"no output places (t• = ∅).",
                    incompatible_arcs
                )
            
            if len(input_arcs) == 0:
                return (
                    False,
                    f"Sink transition '{self.name}' must have at least one input arc. "
                    f"Sink transitions consume tokens from input places (•t ≠ ∅).",
                    []
                )
        
        # Valid structure
        return (True, "", [])
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transition':
        """Create transition from dictionary (deserialization).
        
        Args:
            data: Dictionary containing transition properties
            
        Returns:
            Transition: New transition instance with restored properties
        """
        # Extract required properties
        transition = cls(
            x=data["x"],
            y=data["y"],
            id=data["id"],
            name=data["name"],
            width=data.get("width", cls.DEFAULT_WIDTH),
            height=data.get("height", cls.DEFAULT_HEIGHT),
            label=data.get("label", ""),
            horizontal=data.get("horizontal", True)
        )
        
        # Restore optional properties
        if "enabled" in data:
            transition.enabled = data["enabled"]
        if "fill_color" in data:
            transition.fill_color = tuple(data["fill_color"])
        if "border_color" in data:
            transition.border_color = tuple(data["border_color"])
        if "border_width" in data:
            transition.border_width = data["border_width"]
        
        # Restore behavioral properties
        if "transition_type" in data:
            transition.transition_type = data["transition_type"]
        if "priority" in data:
            transition.priority = data["priority"]
        if "guard" in data:
            transition.guard = data["guard"]
        if "rate" in data:
            transition.rate = data["rate"]
        if "properties" in data:
            transition.properties = data["properties"]
        
        # Restore source/sink markers
        if "is_source" in data:
            transition.is_source = data["is_source"]
        if "is_sink" in data:
            transition.is_sink = data["is_sink"]
        
        return transition
