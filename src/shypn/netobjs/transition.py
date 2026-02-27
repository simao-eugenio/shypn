#!/usr/bin/env python3
"""Transition - Rectangular bar in a Petri net.

Transitions represent events or actions that transform the net state.
Rendered as a filled black rectangle.
"""
from shypn.netobjs.petri_net_object import PetriNetObject
from typing import Any, Optional

# Import kinetic metadata classes
try:
    from shypn.data.kinetics import KineticMetadata, create_metadata_from_dict
except ImportError:
    # Fallback for when kinetics module not available
    KineticMetadata = None  # type: ignore[misc, assignment]
    create_metadata_from_dict = None  # type: ignore[assignment]


class Transition(PetriNetObject):
    """A rectangular transition in a Petri net.
    
    Transitions represent events or actions that transform the net state.
    Rendered as a filled black rectangle.
    """
    
    # Default styling (proportional to Place circle)
    # Width = Place diameter (60.0), Height adjustable
    DEFAULT_WIDTH = 60.0   # Equal to Place diameter
    DEFAULT_HEIGHT = 20.0  # Thinner bar for better visibility
    DEFAULT_COLOR = (0.0, 0.0, 0.0)  # Black fill
    DEFAULT_BORDER_COLOR = (0.0, 0.0, 0.0)  # Black border
    DEFAULT_BORDER_WIDTH = 3.0  # 3px for better visibility
    
    def __init__(self, x: float, y: float, id: str, name: str,
                 width: Optional[float] = None, height: Optional[float] = None,
                 label: str = "", horizontal: bool = True):
        """Initialize a Transition.
        
        Args:
            x: X coordinate in world space (center)
            y: Y coordinate in world space (center)
            id: Unique string identifier (immutable, system-assigned)
            name: Unique name in format "T1", "T2", etc. (immutable, system-assigned)
            width: Rectangle width (default: 50.0)
            height: Rectangle height (default: 8.0)
            label: Optional user-editable text label (mutable)
            horizontal: True for horizontal bar, False for vertical
        """
        # Initialize base class
        super().__init__(id, name, label)
        
        # Position and dimensions
        self.x = float(x)
        self.y = float(y)
        self.width = float(width) if width is not None else self.DEFAULT_WIDTH
        self.height = float(height) if height is not None else self.DEFAULT_HEIGHT
        self.horizontal = bool(horizontal)
        
        # Styling - temporary defaults, updated after properties initialized
        self.fill_color = self.DEFAULT_COLOR
        self.border_color = self.DEFAULT_BORDER_COLOR
        self.border_width = self.DEFAULT_BORDER_WIDTH
        
        # Behavioral properties
        self.transition_type = 'continuous'  # Transition type: immediate, timed, stochastic, continuous (default: continuous)
        self.enabled = True  # Can this transition fire?
        self.guard = 1  # Guard function/expression (enables/disables transition) - defaults to 1 (always enabled)
        self.rate: Optional[float] = 1.0  # Rate/delay for timed/stochastic/continuous transitions - defaults to 1.0
        self.priority = 0  # Priority for conflict resolution (higher = higher priority)
        self.firing_policy = 'race'  # Firing policy: 'random', 'earliest', 'latest', 'priority', 'race', 'age', 'preemptive-priority' (default: race - biologically realistic)
        
        # Source/Sink markers
        self.is_source = False  # Source transition (generates tokens without input)
        self.is_sink = False    # Sink transition (consumes tokens without output)
        
        # Simulation statistics
        self.firing_count = 0  # Cumulative count of firings during simulation
        
        # Protected attributes - use properties/methods to access
        self._properties: dict[str, Any] = {}  # Private: rate functions, kinetic parameters
        self._metadata: dict[str, Any] = {}    # Private: annotations, provenance
        
        # Set default rate_function for continuous transitions to prevent missing rate errors
        if self.transition_type in ['continuous', 'adaptive']:
            self._properties['rate_function'] = "1"
        
        # Kinetic metadata (optional, added by importers or enrichment)
        self.kinetic_metadata: Optional[KineticMetadata] = None
        
        # Apply color schema based on transition type (after all properties initialized)
        from shypn.utils.color_schema_manager import ColorSchemaManager
        border_color, fill_color = ColorSchemaManager.get_transition_colors(self)
        self.border_color = border_color
        self.fill_color = fill_color
        
        # Quorum sensing / signal dependencies (13-tuple formalism: Ψ: T → 2^P)
        # Places that this transition senses as environmental signals without arc connection
        # Example: AHL concentration in bacterial quorum sensing
        self.signal_places: list[str] = []  # List of place IDs (e.g., ['P10', 'P15'])
        self.is_environment_aware = False  # True if transition has signal dependencies
        
        # Module assignment (modular Bio-PN architecture)
        # Transitions belong to modules, enabling network partitioning
        self.module_id: Optional[str] = None  # Module identifier (e.g., "M_cytoplasm", "M_mitochondria")
        
        # Compartment assignment (biological localization)
        # Used for compartment-specific thermodynamic properties
        self.compartment: Optional[str] = None  # Compartment name (e.g., "cytoplasm", "membrane", "extracellular")

        # Legacy/optional attributes (set by from_dict or external code)
        self.formula: Optional[str] = None  # Petri net formula (legacy field)
        self.earliest_time: Optional[float] = None  # TPN earliest firing time
        self.latest_time: Optional[float] = None    # TPN latest firing time
        self.adaptive_filter: Optional[str] = None  # Adaptive simulation filter
        self.volume_threshold: Optional[float] = None  # Volume threshold for mode selection
        self.prefer_continuous: Optional[bool] = None  # Prefer continuous mode

    # ========== Property Decorators (OOP Pattern) ==========
    
    @property
    def rate_function(self) -> Optional[str]:
        """Get rate function expression (OOP property access).
        
        Returns:
            Optional[str]: Rate function formula, or None if not set
        """
        return self._properties.get('rate_function')
    
    @rate_function.setter
    def rate_function(self, expression: Optional[str]) -> None:
        """Set rate function expression with validation (OOP property access).
        
        Args:
            expression: Rate function formula (e.g., "0.5 * [ADP_pool]")
        
        Raises:
            TypeError: If expression is not a string or None
            ValueError: If continuous/adaptive transition has no rate function
        """
        if expression is not None and not isinstance(expression, str):
            raise TypeError("Rate function must be a string or None")
        
        # Validate that continuous/adaptive transitions have rate functions
        if self.transition_type in ['continuous', 'adaptive'] and not expression:
            raise ValueError(f"{self.transition_type} transitions require a rate function")
        
        self._properties['rate_function'] = expression
    
    @property
    def rate_forward(self) -> Optional[str]:
        """Get forward rate expression for reversible reactions (OOP property access).
        
        Returns:
            Optional[str]: Forward rate formula, or None if not set
        """
        return self._properties.get('rate_forward')
    
    @rate_forward.setter
    def rate_forward(self, expression: Optional[str]) -> None:
        """Set forward rate expression for reversible reactions (OOP property access).
        
        Args:
            expression: Forward rate formula
        
        Raises:
            TypeError: If expression is not a string or None
        """
        if expression is not None and not isinstance(expression, str):
            raise TypeError("Forward rate must be a string or None")
        self._properties['rate_forward'] = expression
    
    @property
    def rate_reverse(self) -> Optional[str]:
        """Get reverse rate expression for reversible reactions (OOP property access).
        
        Returns:
            Optional[str]: Reverse rate formula, or None if not set
        """
        return self._properties.get('rate_reverse')
    
    @rate_reverse.setter
    def rate_reverse(self, expression: Optional[str]) -> None:
        """Set reverse rate expression for reversible reactions (OOP property access).
        
        Args:
            expression: Reverse rate formula
        
        Raises:
            TypeError: If expression is not a string or None
        """
        if expression is not None and not isinstance(expression, str):
            raise TypeError("Reverse rate must be a string or None")
        self._properties['rate_reverse'] = expression
    
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
        """Calculate bounding box for the transition.
        
        Returns bounding box containing the rectangle.
        Rectangle is centered at (x, y) with width and height.
        Dimensions swap based on horizontal/vertical orientation.
        
        Returns:
            dict: {'x': min_x, 'y': min_y, 'width': width, 'height': height}
        """
        # Rectangle is centered at (x, y)
        # Dimensions swap if vertical
        w = self.width
        h = self.height
        if not self.horizontal:
            w, h = h, w
        
        half_w = w / 2
        half_h = h / 2
        
        return {
            'x': self.x - half_w,
            'y': self.y - half_h,
            'width': w,
            'height': h
        }
    
    def render(self, cr: Any, zoom: float = 1.0) -> None:  # type: ignore[override]
        """Render the transition as a filled rectangle with optional markers.
        
        Uses legacy rendering style with Cairo transform approach:
        - Solid fill color (white by default)
        - Black border (3.0px compensated for zoom)
        - fill_preserve to maintain path for border
        - Draws in world coordinates (Cairo transform handles scaling)
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
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
    
    def get_editable_fields(self) -> dict:
        """Get which fields are editable for this transition type.
        
        Returns field visibility based on transition semantics:
        - Immediate: No rate (fires instantly), has firing policy
        - Timed: Has delay time, has firing policy
        - Stochastic: Has rate λ, has firing policy
        - Continuous: Has rate function, has firing policy
        
        All transition types support firing policies at the simulation engine level.
        
        Returns:
            dict: Field name -> bool (True if should be shown/editable)
        """
        field_map = {
            'immediate': {
                'rate': False,           # No rate needed
                'rate_function': False,  # No rate function
                'firing_policy': True    # All 7 policies available
            },
            'timed': {
                'rate': True,            # Delay time
                'rate_function': True,   # Can use expressions
                'firing_policy': True    # All 7 policies available
            },
            'stochastic': {
                'rate': True,            # Rate λ
                'rate_function': True,   # Can use expressions
                'firing_policy': True    # All 7 policies available
            },
            'continuous': {
                'rate': True,            # Rate value/function
                'rate_function': True,   # Rate expressions
                'firing_policy': True    # All 7 policies available
            }
        }
        
        return field_map.get(self.transition_type, field_map['continuous'])
    
    def get_type_description(self) -> str:
        """Get human-readable description of this transition type.
        
        Returns:
            str: Description of transition type semantics
        """
        descriptions = {
            'immediate': "Fires instantly when enabled. Use priority to resolve conflicts.",
            'timed': "Fires after a delay time. Rate specifies the delay duration.",
            'stochastic': "Fires with exponential distribution. Rate λ specifies average frequency.",
            'continuous': "Fires continuously based on rate function. Rate can depend on marking."
        }
        
        return descriptions.get(self.transition_type, "Unknown transition type")
    
    def set_rate(self, rate_value):
        """Set rate with validation based on transition type.
        
        Args:
            rate_value: Can be numeric, string expression, dict, or None
            
        Raises:
            ValueError: If rate is invalid for this transition type
        """
        # Allow None for immediate transitions
        if rate_value is None:
            if self.transition_type == 'immediate':
                self.rate = None
                return
            else:
                raise ValueError(f"{self.transition_type} transitions require a rate value")
        
        # Handle string input
        if isinstance(rate_value, str):
            rate_value = rate_value.strip()
            
            # Empty string
            if not rate_value:
                if self.transition_type == 'immediate':
                    self.rate = None
                    return
                else:
                    raise ValueError(f"{self.transition_type} transitions require a rate value")
            
            # Try to parse as number
            try:
                # Try integer first
                if '.' not in rate_value and 'e' not in rate_value.lower():
                    rate_value = int(rate_value)
                else:
                    rate_value = float(rate_value)
            except ValueError:
                # Not a number, keep as string expression
                pass
        
        # Validate numeric values
        if isinstance(rate_value, (int, float)):
            if rate_value < 0:
                raise ValueError("Rate cannot be negative")
            if rate_value == 0 and self.transition_type != 'immediate':
                raise ValueError(f"{self.transition_type} transitions cannot have zero rate")
        
        # Store the value
        self.rate = rate_value
        
        # NOTE: As of 2026-02-04, rate functions should be stored ONLY in properties dict
        # Continuous transitions: Use properties['rate_function'] for complex expressions
        # Stochastic transitions: Use properties['rate_function'] for formulas OR simple rate attribute
        # This method (set_rate) only sets the rate attribute. For rate functions, set properties['rate_function'] directly.
    
    def get_rate_function(self) -> Optional[str]:
        """Get the rate function expression for this transition.
        
        Returns:
            str: Rate function expression, or None if not set
        """
        if not hasattr(self, 'properties') or self.properties is None:
            return None
        return self.properties.get('rate_function')
    
    def set_rate_function(self, expression: str):
        """Set the rate function expression for this transition.
        
        Args:
            expression: Rate function formula (e.g., "0.5 * [ADP_pool]")
        
        Raises:
            ValueError: If expression is invalid for this transition type
        """
        if not hasattr(self, 'properties') or self.properties is None:
            self.properties = {}
        
        # Validate that continuous/adaptive transitions have rate functions
        if self.transition_type in ['continuous', 'adaptive'] and not expression:
            raise ValueError(f"{self.transition_type} transitions require a rate function")
        
        self.properties['rate_function'] = expression
    
    def get_rate_forward(self) -> Optional[str]:
        """Get the forward rate expression for reversible reactions.
        
        Returns:
            str: Forward rate expression, or None if not set
        """
        if not hasattr(self, 'properties') or self.properties is None:
            return None
        return self.properties.get('rate_forward')
    
    def set_rate_forward(self, expression: str):
        """Set the forward rate expression for reversible reactions.
        
        Args:
            expression: Forward rate formula
        """
        if not hasattr(self, 'properties') or self.properties is None:
            self.properties = {}
        self.properties['rate_forward'] = expression
    
    def get_rate_reverse(self) -> Optional[str]:
        """Get the reverse rate expression for reversible reactions.
        
        Returns:
            str: Reverse rate expression, or None if not set
        """
        if not hasattr(self, 'properties') or self.properties is None:
            return None
        return self.properties.get('rate_reverse')
    
    def set_rate_reverse(self, expression: str):
        """Set the reverse rate expression for reversible reactions.
        
        Args:
            expression: Reverse rate formula
        """
        if not hasattr(self, 'properties') or self.properties is None:
            self.properties = {}
        self.properties['rate_reverse'] = expression

    def set_guard(self, guard_value):
        """Set guard expression with storage for evaluation.
        
        Scientific Convention: Guards default to 1 (always enabled).
        Only explicit user input or system state changes should modify this value.
        
        Args:
            guard_value: Can be string expression, dict, bool, int, or None
                - None: Reset to default (1 = always enabled)
                - 1: Always enabled (default initial state)
                - 0: Always disabled
                - string: Expression to evaluate
                - dict: Complex guard specification
        """
        # Store the guard value (None resets to default = 1)
        self.guard = 1 if guard_value is None else guard_value
        
        # Also store in properties for engine evaluation
        if guard_value is not None:
            if not hasattr(self, 'properties') or self.properties is None:
                self.properties = {}
            
            # Store for evaluation
            if isinstance(guard_value, str):
                self.properties['guard_function'] = guard_value
            else:
                self.properties['guard_function'] = str(guard_value)
    
    def reset_firing_count(self):
        """Reset firing count to zero.
        
        Called when simulation is reset or a new simulation begins.
        """
        self.firing_count = 0
    
    def to_dict(self) -> dict:
        """Serialize transition to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all transition properties
        """
        data = super().to_dict()  # Get base properties (id, name, label)
        data.update({
            "object_type": "transition",  # Renamed from "type" to avoid confusion with transition_type
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
            "firing_policy": self.firing_policy,
            "is_source": self.is_source,
            "is_sink": self.is_sink
        })
        
        # Serialize behavioral properties (guard, rate, formula, properties dict)
        if self.guard is not None:
            data["guard"] = self.guard
        
        # PHASE 3 REFACTORING: Deprecated - rate field no longer serialized
        # All rates should be in properties.rate_function (see RATE_FIELD_REFACTORING_PLAN.md)
        # Commenting out to prevent writing rate field to new/updated models
        # if self.rate is not None:
        #     data["rate"] = self.rate
        
        # NOTE: rate_function/rate_forward/rate_reverse are @property decorators
        # that read/write to properties dict. No need to serialize top-level.
        # from_dict() will migrate legacy top-level entries to properties dict.
        
        # Serialize timed transition parameters (TPN window)
        # These are regular attributes (not @property), so serialize at top-level
        if hasattr(self, 'earliest_time') and self.earliest_time is not None:
            data["earliest_time"] = self.earliest_time
        if hasattr(self, 'latest_time') and self.latest_time is not None:
            data["latest_time"] = self.latest_time
            
        if hasattr(self, 'properties') and self.properties:
            data["properties"] = self.properties
        
        # Serialize quorum sensing / environment awareness (13-tuple Bio-PN formalism)
        if hasattr(self, 'signal_places') and self.signal_places:
            data["signal_places"] = self.signal_places
        if hasattr(self, 'is_environment_aware'):
            data["is_environment_aware"] = self.is_environment_aware
        if hasattr(self, 'module_id') and self.module_id is not None:
            data["module_id"] = self.module_id
        if hasattr(self, 'compartment') and self.compartment is not None:
            data["compartment"] = self.compartment
        
        # Serialize adaptive transition parameters (volume-based mode selection)
        # These are regular attributes (not @property), so serialize at top-level
        if hasattr(self, 'adaptive_filter'):
            data["adaptive_filter"] = self.adaptive_filter
        if hasattr(self, 'volume_threshold'):
            data["volume_threshold"] = self.volume_threshold
        if hasattr(self, 'prefer_continuous'):
            data["prefer_continuous"] = self.prefer_continuous
        
        # Serialize kinetic metadata (new structured metadata)
        if self.kinetic_metadata is not None:
            data["kinetic_metadata"] = self.kinetic_metadata.to_dict()
        
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
        
        Supports both clean OOP format (flat structure) and legacy format (attrs nested).
        All IDs must be in correct string format with "T" prefix (e.g., "T1", "T35").
        
        Args:
            data: Dictionary containing transition properties
            
        Returns:
            Transition: New transition instance with restored properties
            
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
        
        # Validate ID format - must be string with "T" prefix
        raw_id = data.get("id")
        transition_id = str(raw_id)
        
        if not transition_id.startswith("T"):
            raise ValueError(
                f"Invalid transition ID format: '{transition_id}'. "
                f"Transition IDs must start with 'T' (e.g., 'T1', 'T35')"
            )
        
        name = str(data.get("name", transition_id))
        
        # Extract required properties with type conversion
        transition = cls(
            x=float(data.get("x", 0.0)),  # Default to 0.0 if missing (legacy file support)
            y=float(data.get("y", 0.0)),  # Default to 0.0 if missing (legacy file support)
            id=transition_id,  # String ID
            name=name,
            width=float(data.get("width", cls.DEFAULT_WIDTH)),
            height=float(data.get("height", cls.DEFAULT_HEIGHT)),
            label=str(data.get("label", "")),
            horizontal=bool(data.get("horizontal", True))
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
        if "firing_policy" in data:
            transition.firing_policy = data["firing_policy"]
        if "guard" in data:
            # Convert None to 1 (scientific convention: guards default to enabled)
            guard_value = data["guard"]
            transition.guard = 1 if guard_value is None else guard_value
        if "rate" in data:
            transition.rate = data["rate"]
            
        # CRITICAL: Load properties dict FIRST before individual rate fields
        # This ensures rate_function in properties dict takes precedence
        if "properties" in data:
            transition.properties = data["properties"]
        else:
            transition.properties = {}
        
        # PHASE 3 REFACTORING: Migrate legacy rate field to properties.rate_function
        # This automatic migration ensures old models work with new architecture
        if "rate" in data and data["rate"] is not None:
            # Only migrate if rate_function doesn't already exist
            if 'rate_function' not  in transition.properties:
                # Convert numeric rate to string for rate_function
                transition.properties['rate_function'] = str(data["rate"])
                # Note: Engine will parse numeric strings and use as lambda
                # Clear the deprecated rate field after migration
                transition.rate = None
        
        # Legacy support: Load top-level rate_function (only if not in properties)
        if "rate_function" in data and 'rate_function' not in transition.properties:
            transition.rate_function = data["rate_function"]
        if "formula" in data:
            transition.formula = data["formula"]
        
        # Legacy support: Load directional rates (only if not in properties)
        if "rate_forward" in data and 'rate_forward' not in transition.properties:
            transition.rate_forward = data["rate_forward"]
        if "rate_reverse" in data and 'rate_reverse' not in transition.properties:
            transition.rate_reverse = data["rate_reverse"]
        
        # Restore source/sink markers
        if "is_source" in data:
            transition.is_source = data["is_source"]
        if "is_sink" in data:
            transition.is_sink = data["is_sink"]
        
        # Restore timed transition parameters (TPN window)
        if "earliest_time" in data:
            transition.earliest_time = data["earliest_time"]
        if "latest_time" in data:
            transition.latest_time = data["latest_time"]
        
        # Restore kinetic metadata (new structured metadata)
        if "kinetic_metadata" in data and create_metadata_from_dict is not None:
            transition.kinetic_metadata = create_metadata_from_dict(data["kinetic_metadata"])
        
        # Restore generic metadata (added by importers/enrichers)
        if "metadata" in data:
            transition.metadata = data["metadata"]
        
        # Restore signal places (quorum sensing)
        if "signal_places" in data:
            transition.signal_places = data["signal_places"]
        if "is_environment_aware" in data:
            transition.is_environment_aware = data["is_environment_aware"]
        if "module_id" in data:
            transition.module_id = data["module_id"]
        if "compartment" in data:
            transition.compartment = data["compartment"]
        
        # Restore adaptive transition parameters (volume-based mode selection)
        # Check both top-level (new format) and properties dict (legacy)
        if "adaptive_filter" in data:
            transition.adaptive_filter = data["adaptive_filter"]
        elif "properties" in data and "adaptive_filter" in data["properties"]:
            transition.adaptive_filter = data["properties"]["adaptive_filter"]
            
        if "volume_threshold" in data:
            transition.volume_threshold = data["volume_threshold"]
        elif "properties" in data and "volume_threshold" in data["properties"]:
            transition.volume_threshold = data["properties"]["volume_threshold"]
            
        if "prefer_continuous" in data:
            transition.prefer_continuous = data["prefer_continuous"]
        elif "properties" in data and "prefer_continuous" in data["properties"]:
            transition.prefer_continuous = data["properties"]["prefer_continuous"]
        
        # Ensure continuous/adaptive transitions have rate_function (prevent missing rate errors)
        if transition.transition_type in ['continuous', 'adaptive']:
            if 'rate_function' not in transition.properties or not transition.properties['rate_function']:
                transition.properties['rate_function'] = "1"
        
        return transition
    
    def get_signal_dependencies(self):
        """Return list of place IDs used as environmental signals.
        
        Signal places are non-local dependencies used in rate functions
        following quorum sensing principles (e.g., AHL concentration).
        
        Returns:
            list: Place IDs that this transition senses (e.g., ['P10', 'P15'])
        """
        return self.signal_places
    
    def is_environment_aware_transition(self):
        """Check if transition responds to environmental signals.
        
        Returns:
            bool: True if transition has signal dependencies (quorum sensing)
        """
        return len(self.signal_places) > 0
    
    def get_all_place_dependencies(self, arcs_list=None):
        """Return all places used in rate function (local + signals).
        
        Combines:
        - Local places: connected by input/output arcs
        - Signal places: sensed as environmental signals (non-local)
        
        Args:
            arcs_list: List of all arcs (optional, for computing local places)
        
        Returns:
            set: All place IDs that affect this transition's rate
        """
        local_places = set()
        
        if arcs_list is not None:
            # Get connected places
            for arc in arcs_list:
                if hasattr(arc, 'source') and hasattr(arc, 'target'):
                    if arc.target == self.id:  # Input arc
                        local_places.add(arc.source)
                    elif arc.source == self.id:  # Output arc
                        local_places.add(arc.target)
        
        # Combine local and signal places
        return local_places | set(self.signal_places)

    def __repr__(self) -> str:
        """Machine-readable representation for debugging."""
        return (
            f"Transition(id={self.id!r}, name={self.name!r}, "
            f"type={self.transition_type!r})"
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.name} [{self.transition_type}]" if self.name else self.id
