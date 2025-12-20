#!/usr/bin/env python3
"""Module Boundary Renderer.

Renders visual grouping boxes for modular Bio-PN architecture on canvas.

Rendering Features:
- Rounded rectangle boundaries around modules
- Semi-transparent background fills (color-coded by compartment)
- Module name labels in header
- Collapse/expand button rendering (visual only, interaction handled separately)
- Boundary signal highlighting
- Collapsed module rendering (compact view)

Design Principles:
- Wayland-safe: Pure Cairo rendering, no X11 dependencies
- Non-intrusive: Transparent backgrounds, subtle borders
- Multi-scale: Clean rendering at all zoom levels
- Performance: Efficient bounding box calculation

Integration:
- Called by ModelCanvasManager during rendering pipeline
- Renders between grid and objects (module boxes as background layer)
"""

import math
from typing import List, Tuple, Optional, Set
import logging

try:
    import cairo
except ImportError:
    cairo = None

from shypn.netobjs import Module, Place, Transition


class ModuleRenderer:
    """Renders module boundary boxes and collapse/expand controls on canvas."""
    
    # Visual constants
    BORDER_WIDTH = 2.0  # Module border width in pixels
    CORNER_RADIUS = 10.0  # Rounded corner radius in pixels
    PADDING = 15.0  # Padding inside module box (pixels)
    HEADER_HEIGHT = 30.0  # Height of module header bar (pixels)
    
    # Colors (RGBA tuples)
    DEFAULT_MODULE_COLOR = (0.85, 0.90, 0.95, 0.35)  # Light blue, 35% opacity
    COLLAPSED_MODULE_COLOR = (0.75, 0.80, 0.85, 0.45)  # Gray, 45% opacity
    BORDER_COLOR = (0.4, 0.5, 0.6, 0.9)  # Medium gray-blue, 90% opacity
    LABEL_COLOR = (0.2, 0.3, 0.4, 1.0)  # Dark gray, opaque
    
    # Compartment-specific colors (from SBML color palette) - more distinct and visible
    COMPARTMENT_COLORS = {
        'cytosol': (0.60, 0.80, 0.95, 0.35),  # Sky blue
        'cytoplasm': (0.60, 0.80, 0.95, 0.35),  # Sky blue
        'extracellular': (0.95, 0.70, 0.70, 0.35),  # Coral red
        'mitochondria': (0.70, 0.95, 0.70, 0.35),  # Spring green
        'mitochondrion': (0.70, 0.95, 0.70, 0.35),  # Spring green
        'nucleus': (0.95, 0.80, 0.60, 0.35),  # Peach orange
        'endoplasmic_reticulum': (0.95, 0.70, 0.85, 0.35),  # Rose pink
        'golgi': (0.95, 0.95, 0.60, 0.35),  # Butter yellow
        'membrane': (0.75, 0.70, 0.95, 0.35),  # Lavender purple
    }
    
    def __init__(self):
        """Initialize module renderer."""
        self.logger = logging.getLogger(__name__)
    
    def render_modules(
        self,
        cr,
        modules: List[Module],
        zoom: float = 1.0,
        show_headers: bool = True,
        hovered_module: Optional[Module] = None
    ):
        """Render all module boundary boxes.
        
        Args:
            cr: Cairo context
            modules: List of Module objects to render
            zoom: Current zoom level
            show_headers: If True, render module name headers
            hovered_module: Module currently under mouse (for hover effects)
        """
        if not modules:
            return
        
        for module in modules:
            if module.collapsed:
                self._render_collapsed_module(cr, module, zoom, show_headers)
            else:
                self._render_expanded_module(
                    cr, module, zoom, show_headers,
                    is_hovered=(module == hovered_module)
                )
    
    def _render_expanded_module(
        self,
        cr,
        module: Module,
        zoom: float,
        show_header: bool,
        is_hovered: bool = False
    ):
        """Render a fully expanded module boundary.
        
        Args:
            cr: Cairo context
            module: Module to render
            zoom: Current zoom level
            show_header: If True, render header bar
            is_hovered: If True, highlight with hover effect
        """
        # Calculate bounding box
        bbox = self._calculate_module_bounds(module)
        if not bbox:
            return  # Empty module, skip rendering
        
        min_x, min_y, max_x, max_y = bbox
        
        # Add padding
        padding = self.PADDING / zoom
        min_x -= padding
        min_y -= padding - (self.HEADER_HEIGHT / zoom if show_header else 0)
        max_x += padding
        max_y += padding
        
        # Get module color
        module_color = self._get_module_color(module)
        
        # Add hover glow effect
        if is_hovered:
            self._draw_rounded_rect(
                cr, min_x, min_y, max_x - min_x, max_y - min_y,
                (self.CORNER_RADIUS + 3) / zoom
            )
            r, g, b, a = module_color
            cr.set_source_rgba(r, g, b, a * 2)  # Stronger glow
            cr.fill()
        
        # Draw background fill
        self._draw_rounded_rect(
            cr, min_x, min_y, max_x - min_x, max_y - min_y,
            self.CORNER_RADIUS / zoom
        )
        cr.set_source_rgba(*module_color)
        cr.fill_preserve()
        
        # Draw border
        cr.set_source_rgba(*self.BORDER_COLOR)
        cr.set_line_width(self.BORDER_WIDTH / zoom)
        cr.stroke()
        
        # Draw header bar if enabled
        if show_header:
            self._render_module_header(
                cr, module, min_x, min_y, max_x - min_x, zoom, is_hovered
            )
    
    def _render_collapsed_module(
        self,
        cr,
        module: Module,
        zoom: float,
        show_header: bool
    ):
        """Render a collapsed module (compact box with boundary signals only).
        
        Args:
            cr: Cairo context
            module: Module to render (must be collapsed)
            zoom: Current zoom level
            show_header: If True, render header bar
        """
        # For collapsed modules, show only boundary signals
        # Calculate compact bounding box based on module name + boundary signals
        
        if not module.boundary_signals:
            # No boundary signals, render minimal box
            # Use module's first place position as reference, or fallback
            ref_x = 0.0
            ref_y = 0.0
            if module.places:
                first_place = next(iter(module.places))
                ref_x, ref_y = first_place.x, first_place.y
            
            # Small collapsed box
            width = 150.0
            height = 80.0
            min_x = ref_x - width / 2
            min_y = ref_y - height / 2
            max_x = ref_x + width / 2
            max_y = ref_y + height / 2
        else:
            # Calculate bounds from boundary signals only
            bbox = self._calculate_boundary_signals_bounds(module)
            if not bbox:
                return
            
            min_x, min_y, max_x, max_y = bbox
            padding = self.PADDING / zoom
            min_x -= padding
            min_y -= padding - (self.HEADER_HEIGHT / zoom if show_header else 0)
            max_x += padding
            max_y += padding
        
        # Draw collapsed box (darker, more opaque)
        self._draw_rounded_rect(
            cr, min_x, min_y, max_x - min_x, max_y - min_y,
            self.CORNER_RADIUS / zoom
        )
        cr.set_source_rgba(*self.COLLAPSED_MODULE_COLOR)
        cr.fill_preserve()
        
        # Draw border (thicker for collapsed)
        cr.set_source_rgba(*self.BORDER_COLOR)
        cr.set_line_width((self.BORDER_WIDTH + 1) / zoom)
        cr.stroke()
        
        # Draw header
        if show_header:
            self._render_module_header(
                cr, module, min_x, min_y, max_x - min_x, zoom,
                is_hovered=False, is_collapsed=True
            )
    
    def _render_module_header(
        self,
        cr,
        module: Module,
        x: float,
        y: float,
        width: float,
        zoom: float,
        is_hovered: bool = False,
        is_collapsed: bool = False
    ):
        """Render module header bar with name and collapse button.
        
        Args:
            cr: Cairo context
            module: Module to render header for
            x, y: Top-left corner of module box
            width: Width of module box
            zoom: Current zoom level
            is_hovered: If True, show hover effects
            is_collapsed: If True, show expand button (▶), else collapse (▼)
        """
        header_height = self.HEADER_HEIGHT / zoom
        
        # Draw header background (slightly darker)
        cr.rectangle(x, y, width, header_height)
        r, g, b, a = self._get_module_color(module)
        cr.set_source_rgba(r * 0.8, g * 0.8, b * 0.8, a * 2)
        cr.fill()
        
        # Draw module name
        cr.set_source_rgba(*self.LABEL_COLOR)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(12 / zoom)
        
        text = f"{module.name} [{len(module.places)}P, {len(module.transitions)}T]"
        extents = cr.text_extents(text)
        text_x = x + 10 / zoom
        text_y = y + header_height / 2 + extents.height / 2
        
        cr.move_to(text_x, text_y)
        cr.show_text(text)
        
        # Draw collapse/expand button indicator (visual only)
        # Actual button interaction handled by canvas event system
        button_x = x + width - 25 / zoom
        button_y = y + header_height / 2
        button_size = 10 / zoom
        
        if is_hovered:
            # Show button background on hover
            cr.arc(button_x, button_y, button_size, 0, 2 * math.pi)
            cr.set_source_rgba(0.5, 0.6, 0.7, 0.3)
            cr.fill()
        
        # Draw triangle indicator
        cr.set_source_rgba(*self.LABEL_COLOR)
        if is_collapsed:
            # Expand button: ▶ (right-pointing triangle)
            self._draw_triangle(cr, button_x, button_y, button_size * 0.6, 0)
        else:
            # Collapse button: ▼ (down-pointing triangle)
            self._draw_triangle(cr, button_x, button_y, button_size * 0.6, math.pi / 2)
        
        cr.fill()
        
        # Clear path
        cr.new_path()
    
    def _draw_triangle(self, cr, x: float, y: float, size: float, rotation: float):
        """Draw a triangle (for collapse/expand buttons).
        
        Args:
            cr: Cairo context
            x, y: Center position
            size: Triangle size (distance from center to vertex)
            rotation: Rotation in radians (0 = pointing right)
        """
        # Equilateral triangle vertices
        for i in range(3):
            angle = rotation + i * 2 * math.pi / 3
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            if i == 0:
                cr.move_to(px, py)
            else:
                cr.line_to(px, py)
        cr.close_path()
    
    def _draw_rounded_rect(
        self,
        cr,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float
    ):
        """Draw a rounded rectangle path.
        
        Args:
            cr: Cairo context
            x, y: Top-left corner
            width, height: Rectangle dimensions
            radius: Corner radius
        """
        # Clamp radius to half of smaller dimension
        radius = min(radius, width / 2, height / 2)
        
        # Top-left arc
        cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        # Top-right arc
        cr.arc(x + width - radius, y + radius, radius, 3 * math.pi / 2, 0)
        # Bottom-right arc
        cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
        # Bottom-left arc
        cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
        cr.close_path()
    
    def _calculate_module_bounds(self, module: Module) -> Optional[Tuple[float, float, float, float]]:
        """Calculate bounding box of all objects in module.
        
        Args:
            module: Module to calculate bounds for
        
        Returns:
            (min_x, min_y, max_x, max_y) or None if empty
        """
        if not module.places and not module.transitions:
            return None
        
        # Collect all positions
        xs = []
        ys = []
        
        for place in module.places:
            xs.append(place.x - place.radius)
            xs.append(place.x + place.radius)
            ys.append(place.y - place.radius)
            ys.append(place.y + place.radius)
        
        for transition in module.transitions:
            xs.append(transition.x - transition.width / 2)
            xs.append(transition.x + transition.width / 2)
            ys.append(transition.y - transition.height / 2)
            ys.append(transition.y + transition.height / 2)
        
        if not xs or not ys:
            return None
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def _calculate_boundary_signals_bounds(self, module: Module) -> Optional[Tuple[float, float, float, float]]:
        """Calculate bounding box of boundary signals only.
        
        Args:
            module: Module to calculate bounds for
        
        Returns:
            (min_x, min_y, max_x, max_y) or None if no boundary signals
        """
        if not module.boundary_signals:
            return None
        
        xs = []
        ys = []
        
        for signal in module.boundary_signals:
            xs.append(signal.x - signal.radius)
            xs.append(signal.x + signal.radius)
            ys.append(signal.y - signal.radius)
            ys.append(signal.y + signal.radius)
        
        if not xs or not ys:
            return None
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def _get_module_color(self, module: Module) -> Tuple[float, float, float, float]:
        """Get color for module based on compartment.
        
        Args:
            module: Module to get color for
        
        Returns:
            RGBA tuple
        """
        # Try to match compartment to color
        if module.compartment_id:
            # Normalize compartment name (lowercase, remove special chars)
            comp_key = module.compartment_id.lower().replace(' ', '_').replace('-', '_')
            
            for key, color in self.COMPARTMENT_COLORS.items():
                if key in comp_key or comp_key in key:
                    return color
        
        # Default color
        return self.DEFAULT_MODULE_COLOR
    
    def is_point_in_module_header(
        self,
        module: Module,
        x: float,
        y: float,
        zoom: float
    ) -> bool:
        """Check if point is inside module (for interaction detection).
        
        Args:
            module: Module to check
            x, y: Point coordinates (world space)
            zoom: Current zoom level
        
        Returns:
            True if point is inside module area
        """
        bbox = self._calculate_module_bounds(module)
        if not bbox:
            return False
        
        min_x, min_y, max_x, max_y = bbox
        padding = self.PADDING / zoom
        
        # Make entire module clickable for easier interaction
        # Include padding area around module
        module_min_x = min_x - padding
        module_min_y = min_y - padding
        module_max_x = max_x + padding
        module_max_y = max_y + padding
        
        return (module_min_x <= x <= module_max_x and
                module_min_y <= y <= module_max_y)
    
    def is_point_in_collapse_button(
        self,
        module: Module,
        x: float,
        y: float,
        zoom: float
    ) -> bool:
        """Check if point is inside collapse/expand button.
        
        Args:
            module: Module to check
            x, y: Point coordinates (world space)
            zoom: Current zoom level
        
        Returns:
            True if point is in button area
        """
        if not self.is_point_in_module_header(module, x, y, zoom):
            return False
        
        bbox = self._calculate_module_bounds(module)
        if not bbox:
            return False
        
        min_x, min_y, max_x, max_y = bbox
        padding = self.PADDING / zoom
        header_height = self.HEADER_HEIGHT / zoom
        
        # Button position (top-right of header)
        button_x = max_x + padding - 25 / zoom
        button_y = min_y - padding - header_height / 2
        button_radius = 10 / zoom
        
        # Check if point is within button circle
        dx = x - button_x
        dy = y - button_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        return distance <= button_radius
