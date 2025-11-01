#!/usr/bin/env python3
"""Model Canvas Manager.

This module manages the canvas properties, transformations, and behaviors
for the Petri Net model editor. It handles:
- Grid system with adaptive spacing based on zoom level
- Zoom operations (pointer-centered)
- Pan operations (viewport translation)
- Coordinate transformations (screen ↔ world)
- Rendering pipeline for grid and model elements
- Document metadata and state validation
- Petri net object collections (places, transitions, arcs)
- View state persistence (pan, zoom)

The manager maintains the model state separately from GTK widgets,
making it easier to test and maintain.

REFACTORING NOTE: This class now acts as a Facade, delegating to:
- ViewportController: zoom/pan operations
- DocumentController: object management
- CoordinateTransform: coordinate conversions (service)
- GridRenderer: grid drawing (service)
- ArcGeometryService: arc geometry (service)
"""
import math
import json
import os
from datetime import datetime
from shypn.netobjs import Place, Arc, Transition
from shypn.edit import SelectionManager, ObjectEditingTransforms, RectangleSelection

# Import extracted controllers and services
from shypn.core.controllers import ViewportController, DocumentController
from shypn.core.services import (
    screen_to_world as coord_screen_to_world,
    world_to_screen as coord_world_to_screen,
    mm_to_pixels as coord_mm_to_pixels,
    pixels_to_mm as coord_pixels_to_mm,
    validate_zoom as coord_validate_zoom,
)
from shypn.rendering import (
    draw_grid as render_draw_grid,
    get_adaptive_grid_spacing,
    GRID_STYLE_LINE,
    GRID_STYLE_DOT,
    GRID_STYLE_CROSS,
    BASE_GRID_SPACING,
    GRID_MAJOR_EVERY,
)
from shypn.core.canvas_transformations import TransformationManager
from shypn.core.services import (
    detect_parallel_arcs as arc_detect_parallel,
    calculate_arc_offset as arc_calculate_offset,
    count_parallel_arcs as arc_count_parallel,
    has_parallel_arcs as arc_has_parallel,
    get_arc_offset_for_rendering as arc_get_offset_for_rendering,
)


class ModelCanvasManager:
    """Manages canvas properties, transformations, and rendering for Petri Net models."""
    
    # Zoom configuration
    MIN_ZOOM = 0.3   # 30% minimum (practical engineering range)
    MAX_ZOOM = 3.0   # 300% maximum (practical engineering range)
    ZOOM_STEP = 1.1  # Multiplicative zoom factor (10% per step)
    
    # Canvas extent for infinite canvas (half-extent in logical units)
    CANVAS_EXTENT = 10000.0  # ±10,000 units = 20,000×20,000 total canvas
    
    # Grid configuration
    # DPI-aware grid: 1mm physical spacing at all screen resolutions
    BASE_GRID_SPACING = 1.0  # 1mm physical spacing (DPI-aware)
    GRID_SUBDIVISION_LEVELS = [1, 2, 5, 10]  # Grid adapts at these zoom thresholds
    GRID_MAJOR_EVERY = 5  # Every 5th line is a major line (legacy-compatible)
    GRID_STYLE_LINE = 'line'  # Standard grid lines
    GRID_STYLE_DOT = 'dot'    # Dots at intersections
    GRID_STYLE_CROSS = 'cross'  # Small crosses at intersections
    
    def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
        """Initialize the canvas manager.
        
        Args:
            canvas_width: Logical canvas width in world coordinates.
            canvas_height: Logical canvas height in world coordinates.
            filename: Base filename without extension (default: "default").
        """
        # Canvas logical size (world coordinates)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # DPI detection (defaults to 96.0, updated from widget)
        self.screen_dpi = 96.0
        
        # Grid style
        self.grid_style = GRID_STYLE_LINE  # Default to line grid
        
        # Tool selection state
        self.current_tool = None  # Currently selected tool ('place', 'transition', 'arc', or None)
        
        # Initialize Controllers
        # ViewportController: Manages zoom, pan, viewport state
        self.viewport_controller = ViewportController(
            viewport_width=800,
            viewport_height=600,
            filename=filename
        )
        
        # DocumentController: Manages Petri net objects and metadata
        self.document_controller = DocumentController(filename=filename)
        
        # Set change callback for all objects
        self.document_controller.set_change_callback(self._on_object_changed)
        
        # Flag for initial pan centering
        self._initial_pan_set = False  # Flag to center on first draw
        
        # Flag to trigger fit_to_page on next draw (for SBML/KEGG imports)
        self._fit_to_page_pending = False
        self._fit_to_page_padding = 10  # Default padding percentage
        self._fit_to_page_horizontal_offset = 0  # Default horizontal offset (0% = centered)
        self._fit_to_page_vertical_offset = 0  # Default vertical offset (0% = centered)
        
        # Flag to track if document was imported (needs "Save As" on first save)
        self._is_imported = False
        
        # ===== PER-DOCUMENT FILE STATE (Phase 1: Multi-Document Support) =====
        # Each manager now owns its filepath and dirty state
        # This fixes critical data loss issues from single global persistency
        self.filepath = None  # Full path to saved file (None if unsaved)
        self._is_dirty = False  # Has unsaved changes
        self.on_dirty_changed = None  # Callback(is_dirty) when dirty state changes
        
        # Pointer position (for pointer-centered zoom)
        self.pointer_x = 0
        self.pointer_y = 0
        
        # Selection and transformation system
        self.selection_manager = SelectionManager()
        self.editing_transforms = ObjectEditingTransforms(self.selection_manager)
        self.rectangle_selection = RectangleSelection()
        
        # Canvas transformations (rotation, etc.)
        self.transformation_manager = TransformationManager()
        
        # Dirty flag for redraw optimization
        self._needs_redraw = True
        
        # Callback to trigger widget redraw (set by UI layer)
        self._redraw_callback = None
        
        # Observer pattern for model changes
        self._observers = []  # List of observer callbacks
        
        # Ensure all arcs have proper manager references
        self.ensure_arc_references()
    
    # ==================== Property Proxies (Backward Compatibility) ====================
    # These properties delegate to controllers for backward compatibility
    
    @property
    def zoom(self):
        """Get current zoom level (delegates to ViewportController)."""
        return self.viewport_controller.zoom
    
    @zoom.setter
    def zoom(self, value):
        """Set zoom level (delegates to ViewportController)."""
        self.viewport_controller.zoom = value
    
    @property
    def pan_x(self):
        """Get pan X offset (delegates to ViewportController)."""
        return self.viewport_controller.pan_x
    
    @pan_x.setter
    def pan_x(self, value):
        """Set pan X offset (delegates to ViewportController)."""
        self.viewport_controller.pan_x = value
    
    @property
    def pan_y(self):
        """Get pan Y offset (delegates to ViewportController)."""
        return self.viewport_controller.pan_y
    
    @pan_y.setter
    def pan_y(self, value):
        """Set pan Y offset (delegates to ViewportController)."""
        self.viewport_controller.pan_y = value
    
    @property
    def viewport_width(self):
        """Get viewport width (delegates to ViewportController)."""
        return self.viewport_controller.viewport_width
    
    @viewport_width.setter
    def viewport_width(self, value):
        """Set viewport width (delegates to ViewportController)."""
        self.viewport_controller.viewport_width = value
    
    @property
    def viewport_height(self):
        """Get viewport height (delegates to ViewportController)."""
        return self.viewport_controller.viewport_height
    
    @viewport_height.setter
    def viewport_height(self, value):
        """Set viewport height (delegates to ViewportController)."""
        self.viewport_controller.viewport_height = value
    
    @property
    def places(self):
        """Get places collection (delegates to DocumentController)."""
        return self.document_controller.places
    
    @places.setter
    def places(self, value):
        """Set places collection (delegates to DocumentController)."""
        self.document_controller.places = value
    
    @property
    def transitions(self):
        """Get transitions collection (delegates to DocumentController)."""
        return self.document_controller.transitions
    
    @transitions.setter
    def transitions(self, value):
        """Set transitions collection (delegates to DocumentController)."""
        self.document_controller.transitions = value
    
    @property
    def arcs(self):
        """Get arcs collection (delegates to DocumentController)."""
        return self.document_controller.arcs
    
    @arcs.setter
    def arcs(self, value):
        """Set arcs collection (delegates to DocumentController)."""
        self.document_controller.arcs = value
    
    @property
    def filename(self):
        """Get filename (delegates to DocumentController)."""
        return self.document_controller.filename
    
    @filename.setter
    def filename(self, value):
        """Set filename (delegates to DocumentController)."""
        self.document_controller.filename = value
    
    @property
    def modified(self):
        """Get modified flag (delegates to DocumentController)."""
        return self.document_controller.modified
    
    @modified.setter
    def modified(self, value):
        """Set modified flag (delegates to DocumentController)."""
        self.document_controller.modified = value
    
    @property
    def created_at(self):
        """Get creation timestamp (delegates to DocumentController)."""
        return self.document_controller.created_at
    
    @created_at.setter
    def created_at(self, value):
        """Set creation timestamp (delegates to DocumentController)."""
        self.document_controller.created_at = value
    
    @property
    def modified_at(self):
        """Get modification timestamp (delegates to DocumentController)."""
        return self.document_controller.modified_at
    
    @modified_at.setter
    def modified_at(self, value):
        """Set modification timestamp (delegates to DocumentController)."""
        self.document_controller.modified_at = value
    
    @property
    def _next_place_id(self):
        """Get next place ID (delegates to DocumentController)."""
        return self.document_controller._next_place_id
    
    @_next_place_id.setter
    def _next_place_id(self, value):
        """Set next place ID (delegates to DocumentController)."""
        self.document_controller._next_place_id = value
    
    @property
    def _next_transition_id(self):
        """Get next transition ID (delegates to DocumentController)."""
        return self.document_controller._next_transition_id
    
    @_next_transition_id.setter
    def _next_transition_id(self, value):
        """Set next transition ID (delegates to DocumentController)."""
        self.document_controller._next_transition_id = value
    
    @property
    def _next_arc_id(self):
        """Get next arc ID (delegates to DocumentController)."""
        return self.document_controller._next_arc_id
    
    @_next_arc_id.setter
    def _next_arc_id(self, value):
        """Set next arc ID (delegates to DocumentController)."""
        self.document_controller._next_arc_id = value
    
    # ==================== DPI and Physical Units ====================
    
    def set_screen_dpi(self, dpi):
        """Update screen DPI from widget.
        
        Args:
            dpi: Screen resolution in dots per inch.
        """
        self.screen_dpi = dpi if dpi and dpi > 0 else 96.0
    
    def get_mm_to_pixels(self):
        """Convert millimeters to pixels based on screen DPI.
        
        Returns:
            float: Pixels per millimeter.
        """
        return self.screen_dpi / 25.4
    
    # ==================== Coordinate Transformations ====================
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world (model) coordinates.
        
        Applies transformations in order: zoom/pan inverse, then rotation inverse.
        This matches the drawing pipeline: zoom/pan → rotation.
        
        Args:
            screen_x: X coordinate in screen space (pixels).
            screen_y: Y coordinate in screen space (pixels).
            
        Returns:
            tuple: (world_x, world_y) in model coordinate space.
        """
        # Step 1: Apply zoom/pan inverse transformation (screen → pre-rotation space)
        pre_rot_x, pre_rot_y = coord_screen_to_world(screen_x, screen_y, self.zoom, self.pan_x, self.pan_y)
        
        # Step 2: Apply rotation inverse transformation (pre-rotation → world space)
        # Rotation happens around viewport center in world coordinates
        rotation = self.transformation_manager.get_rotation()
        if rotation and rotation.angle_degrees != 0:
            # Calculate rotation center in world space
            center_world_x = self.viewport_width / (2.0 * self.zoom) - self.pan_x
            center_world_y = self.viewport_height / (2.0 * self.zoom) - self.pan_y
            
            # Translate to origin, rotate inverse, translate back
            dx = pre_rot_x - center_world_x
            dy = pre_rot_y - center_world_y
            
            cos_a = math.cos(-rotation.angle_radians)  # Negative for inverse rotation
            sin_a = math.sin(-rotation.angle_radians)
            
            rotated_dx = dx * cos_a - dy * sin_a
            rotated_dy = dx * sin_a + dy * cos_a
            
            world_x = rotated_dx + center_world_x
            world_y = rotated_dy + center_world_y
            
            return world_x, world_y
        else:
            return pre_rot_x, pre_rot_y
    
    def world_to_screen(self, world_x, world_y):
        """Convert world (model) coordinates to screen coordinates.
        
        Applies transformations in order: rotation, then zoom/pan.
        This matches the drawing pipeline: zoom/pan → rotation (applied in reverse).
        
        Args:
            world_x: X coordinate in world space.
            world_y: Y coordinate in world space.
            
        Returns:
            tuple: (screen_x, screen_y) in screen coordinate space (pixels).
        """
        # Step 1: Apply rotation transformation (world → pre-screen space)
        rotation = self.transformation_manager.get_rotation()
        if rotation and rotation.angle_degrees != 0:
            # Calculate rotation center in world space
            center_world_x = self.viewport_width / (2.0 * self.zoom) - self.pan_x
            center_world_y = self.viewport_height / (2.0 * self.zoom) - self.pan_y
            
            # Translate to origin, rotate, translate back
            dx = world_x - center_world_x
            dy = world_y - center_world_y
            
            cos_a = math.cos(rotation.angle_radians)
            sin_a = math.sin(rotation.angle_radians)
            
            rotated_dx = dx * cos_a - dy * sin_a
            rotated_dy = dx * sin_a + dy * cos_a
            
            pre_screen_x = rotated_dx + center_world_x
            pre_screen_y = rotated_dy + center_world_y
        else:
            pre_screen_x = world_x
            pre_screen_y = world_y
        
        # Step 2: Apply zoom/pan transformation (pre-screen → screen space)
        return coord_world_to_screen(pre_screen_x, pre_screen_y, self.zoom, self.pan_x, self.pan_y)
    
    # ==================== Tool Management ====================
    
    def set_tool(self, tool_name):
        """Set the currently active tool.
        
        Args:
            tool_name: Tool to activate ('place', 'transition', 'arc') or None to clear.
        """
        self.current_tool = tool_name
    
    def get_tool(self):
        """Get the currently active tool.
        
        Returns:
            str or None: Currently active tool name ('place', 'transition', 'arc') or None.
        """
        return self.current_tool
    
    def clear_tool(self):
        """Clear the current tool selection (return to pan mode)."""
        self.current_tool = None
    
    def is_tool_active(self):
        """Check if any tool is currently active.
        
        Returns:
            bool: True if a tool is active, False if in pan mode.
        """
        return self.current_tool is not None
    
    # ==================== Petri Net Object Management ====================
    
    def add_place(self, x, y, **kwargs):
        """Create and add a Place at the specified position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            **kwargs: Additional Place parameters (radius, label, etc.)
            
        Returns:
            Place: The newly created place instance
        """
        # Delegate to DocumentController
        place = self.document_controller.add_place(x, y, **kwargs)
        self._notify_observers('created', place)
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to show new place
        return place
    
    def add_transition(self, x, y, **kwargs):
        """Create and add a Transition at the specified position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            **kwargs: Additional Transition parameters (width, height, label, etc.)
            
        Returns:
            Transition: The newly created transition instance
        """
        # Delegate to DocumentController
        transition = self.document_controller.add_transition(x, y, **kwargs)
        self._notify_observers('created', transition)
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to show new transition
        return transition
    
    def add_arc(self, source, target, **kwargs):
        """Create and add an Arc between two objects.
        
        Args:
            source: Source object instance (Place or Transition)
            target: Target object instance (Place or Transition)
            **kwargs: Additional Arc parameters (weight, etc.)
            
        Returns:
            Arc: The newly created arc instance
        """
        # Delegate to DocumentController
        arc = self.document_controller.add_arc(source, target, **kwargs)
        
        # Additional facade-level logic for parallel arc handling
        arc._manager = self  # Store reference to manager for parallel detection
        self._auto_convert_parallel_arcs_to_curved(arc)
        
        self._notify_observers('created', arc)
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to show new arc
        return arc
    
    def remove_place(self, place):
        """Remove a place from the model.
        
        Also removes all arcs connected to this place.
        
        Args:
            place: Place instance to remove
        """
        # Delegate to DocumentController (handles cascade)
        self.document_controller.remove_place(place)
        self._notify_observers('deleted', place)
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to remove from view
    
    def remove_transition(self, transition):
        """Remove a transition from the model.
        
        Also removes all arcs connected to this transition.
        
        Args:
            transition: Transition instance to remove
        """
        # Delegate to DocumentController (handles cascade)
        self.document_controller.remove_transition(transition)
        self._notify_observers('deleted', transition)
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to remove from view
    
    def remove_arc(self, arc):
        """Remove an arc from the model.
        
        Args:
            arc: Arc instance to remove
        """
        # Delegate to DocumentController
        self.document_controller.remove_arc(arc)
        self._notify_observers('deleted', arc)
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to remove from view
    
    def load_objects(self, places=None, transitions=None, arcs=None):
        """Load objects into the model in bulk (for import/deserialize operations).
        
        This method ensures all objects are added through proper channels with
        automatic observer notification, providing a UNIFIED PATH for both manual
        creation and import/load operations.
        
        This eliminates the dual-path architecture problem where:
        - Manual creation: objects added one-by-one via add_place/transition/arc()
        - Import/load: objects bulk-assigned to manager.places/transitions/arcs lists
        
        Now ALL object loading uses this single method, ensuring:
        - Consistent observer notifications
        - Proper manager references (for arcs)
        - Correct ID counter updates
        - Single code path = consistent behavior
        
        Args:
            places: List of Place objects to add (default: None = no places)
            transitions: List of Transition objects to add (default: None = no transitions)
            arcs: List of Arc objects to add (default: None = no arcs)
        
        Example:
            # For imports/loads:
            manager.load_objects(
                places=document_model.places,
                transitions=document_model.transitions,
                arcs=document_model.arcs
            )
        """
        if places is None:
            places = []
        if transitions is None:
            transitions = []
        if arcs is None:
            arcs = []
        
        
        # Add places with proper notification
        for place in places:
            self.places.append(place)
            self._notify_observers('created', place)
        
        # Add transitions with proper notification
        for transition in transitions:
            self.transitions.append(transition)
            self._notify_observers('created', transition)
        
        # Add arcs with proper notification and manager reference
        for arc in arcs:
            self.arcs.append(arc)
            arc._manager = self  # Set manager reference for parallel detection
            self._notify_observers('created', arc)
        
        # Auto-convert loop arcs and parallel arcs to curved
        # This ensures loaded models have proper curved rendering for loops and parallels
        for arc in arcs:
            self._auto_convert_parallel_arcs_to_curved(arc)
        
        
        # Update ID counters to avoid collisions
        # Handle both numeric IDs (int) and string IDs ("123", "P123", "T45", "A12")
        if places:
            place_ids = []
            for p in self.places:
                if isinstance(p.id, int):
                    place_ids.append(p.id)
                elif isinstance(p.id, str):
                    # Try to extract numeric part - handle both "10" and "P10" formats
                    if p.id.isdigit():
                        # Plain numeric string like "10"
                        place_ids.append(int(p.id))
                    elif len(p.id) > 1 and p.id[1:].isdigit():
                        # Prefixed format like "P10"
                        place_ids.append(int(p.id[1:]))
            if place_ids:
                self.document_controller._next_place_id = max(place_ids) + 1
        
        if transitions:
            trans_ids = []
            for t in self.transitions:
                if isinstance(t.id, int):
                    trans_ids.append(t.id)
                elif isinstance(t.id, str):
                    # Try to extract numeric part - handle both "10" and "T10" formats
                    if t.id.isdigit():
                        # Plain numeric string like "10"
                        trans_ids.append(int(t.id))
                    elif len(t.id) > 1 and t.id[1:].isdigit():
                        # Prefixed format like "T10"
                        trans_ids.append(int(t.id[1:]))
            if trans_ids:
                self.document_controller._next_transition_id = max(trans_ids) + 1
        
        if arcs:
            arc_ids = []
            for a in self.arcs:
                if isinstance(a.id, int):
                    arc_ids.append(a.id)
                elif isinstance(a.id, str):
                    # Try to extract numeric part - handle both "10" and "A10" formats
                    if a.id.isdigit():
                        # Plain numeric string like "10"
                        arc_ids.append(int(a.id))
                    elif len(a.id) > 1 and a.id[1:].isdigit():
                        # Prefixed format like "A10"
                        arc_ids.append(int(a.id[1:]))
            if arc_ids:
                self.document_controller._next_arc_id = max(arc_ids) + 1
        
        # CRITICAL: Reset all places to their initial marking
        # When loading (File Open, KEGG import, SBML import, etc), we want to start
        # with the initial state, not the simulation state that may be in the data.
        # This is especially important for test arcs (catalysts) which must have
        # tokens=initial_marking to function correctly.
        for place in places:
            if hasattr(place, 'initial_marking'):
                place.tokens = place.initial_marking
        
        # Mark document as dirty (unsaved changes) and trigger redraw
        self.mark_dirty()  # Document dirty tracking for save state
        self.mark_needs_redraw()  # Canvas redraw for rendering
    
    def detect_parallel_arcs(self, arc):
        """Find arcs parallel to the given arc (same source/target or reversed).
        
        Parallel arcs are arcs that connect the same two nodes, either in the
        same direction or opposite direction. These need visual offset to
        avoid overlapping.
        
        Args:
            arc: Arc to check for parallels
            
        Returns:
            list: List of parallel arcs (excluding the given arc)
        """
        parallels = []
        
        for other in self.arcs:
            if other == arc:
                continue
            
            # Same direction: same source and target
            if (other.source == arc.source and other.target == arc.target):
                parallels.append(other)
            
            # Opposite direction: reversed source and target
            elif (other.source == arc.target and other.target == arc.source):
                parallels.append(other)
        
        if not parallels:
            pass  # No parallels found
        
        return parallels
    
    def _auto_convert_parallel_arcs_to_curved(self, new_arc):
        """Automatically convert parallel arcs and loop arcs to curved arcs.
        
        When a new arc creates a parallel situation (same source/target or opposite),
        or when it's a loop arc (source == target), convert all involved arcs to
        curved arcs for better visualization.
        
        Parallel arcs MUST always be curved - never straight. Loops MUST be curved.
        This prevents visual overlap and maintains clear distinction between different flows.
        
        For opposite direction arcs (A→B and B→A), BOTH are converted to curved
        simultaneously with perpendicular offsets on opposite sides.
        
        Args:
            new_arc: The newly added arc that may create parallels or be a loop
        """
        from shypn.netobjs import CurvedArc, CurvedInhibitorArc, InhibitorArc
        from shypn.utils.arc_transform import make_curved
        import math
        
        # Check if this is a loop arc (source == target)
        is_loop = (new_arc.source == new_arc.target)
        
        parallels = self.detect_parallel_arcs(new_arc)
        
        # Convert loop arcs or parallel arcs
        if is_loop or parallels:
            
            # For loop arcs, just convert and apply offset
            if is_loop:
                if isinstance(new_arc, Arc) and not isinstance(new_arc, (CurvedArc, CurvedInhibitorArc)):
                    curved_arc = make_curved(new_arc)
                    curved_arc.control_offset_x = 60.0
                    curved_arc.control_offset_y = -60.0
                    
                    try:
                        index = self.arcs.index(new_arc)
                        self.arcs[index] = curved_arc
                        curved_arc._manager = self
                        curved_arc.on_changed = self._on_object_changed
                    except ValueError:
                        pass  # Already replaced
                
                self.mark_dirty()
                return
            
            # For parallel arcs, check if we have an opposite-direction pair
            opposite_arc = None
            for parallel in parallels:
                if parallel.source == new_arc.target and parallel.target == new_arc.source:
                    opposite_arc = parallel
                    break
            
            # If we have an opposite-direction pair, convert BOTH with perpendicular offsets
            if opposite_arc is not None:
                # Calculate perpendicular direction from new_arc direction
                dx = new_arc.target.x - new_arc.source.x
                dy = new_arc.target.y - new_arc.source.y
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > 1:
                    # Normalize
                    dx /= length
                    dy /= length
                    
                    # Perpendicular vector (90° rotation)
                    perp_x = -dy
                    perp_y = dx
                    
                    # Offset distance
                    offset_distance = 50.0
                    
                    # Convert and offset new_arc
                    if isinstance(new_arc, Arc) and not isinstance(new_arc, (CurvedArc, CurvedInhibitorArc)):
                        curved_new = make_curved(new_arc)
                        
                        # Determine offset direction based on ID
                        if new_arc.id < opposite_arc.id:
                            curved_new.control_offset_x = perp_x * offset_distance
                            curved_new.control_offset_y = perp_y * offset_distance
                        else:
                            curved_new.control_offset_x = -perp_x * offset_distance
                            curved_new.control_offset_y = -perp_y * offset_distance
                        
                        try:
                            index = self.arcs.index(new_arc)
                            self.arcs[index] = curved_new
                            curved_new._manager = self
                            curved_new.on_changed = self._on_object_changed
                        except ValueError:
                            pass
                    
                    # Convert and offset opposite_arc
                    if isinstance(opposite_arc, (Arc, InhibitorArc)) and not isinstance(opposite_arc, (CurvedArc, CurvedInhibitorArc)):
                        curved_opposite = make_curved(opposite_arc)
                        
                        # Mirror offset
                        if new_arc.id < opposite_arc.id:
                            curved_opposite.control_offset_x = -perp_x * offset_distance
                            curved_opposite.control_offset_y = -perp_y * offset_distance
                        else:
                            curved_opposite.control_offset_x = perp_x * offset_distance
                            curved_opposite.control_offset_y = perp_y * offset_distance
                        
                        try:
                            index = self.arcs.index(opposite_arc)
                            self.arcs[index] = curved_opposite
                            curved_opposite._manager = self
                            curved_opposite.on_changed = self._on_object_changed
                        except ValueError:
                            pass
            
            else:
                # No opposite pair, just convert parallels without special offsets
                # (This handles same-direction parallels)
                for parallel in parallels:
                    if isinstance(parallel, (Arc, InhibitorArc)) and not isinstance(parallel, (CurvedArc, CurvedInhibitorArc)):
                        curved_arc = make_curved(parallel)
                        
                        try:
                            index = self.arcs.index(parallel)
                            self.arcs[index] = curved_arc
                            curved_arc._manager = self
                            curved_arc.on_changed = self._on_object_changed
                        except ValueError:
                            pass
                
                # Convert new_arc too if it's not curved
                if isinstance(new_arc, Arc) and not isinstance(new_arc, (CurvedArc, CurvedInhibitorArc)):
                    curved_new = make_curved(new_arc)
                    try:
                        index = self.arcs.index(new_arc)
                        self.arcs[index] = curved_new
                        curved_new._manager = self
                        curved_new.on_changed = self._on_object_changed
                    except ValueError:
                        pass
            
            # Mark dirty to trigger redraw
            self.mark_dirty()
    
    def calculate_arc_offset(self, arc, parallels):
        """Calculate offset for arc to avoid overlapping parallels.
        
        For parallel arcs between same nodes, we offset them perpendicular
        to the line connecting the nodes. The offset is calculated to
        distribute arcs evenly on both sides of the center line.
        
        For opposite direction arcs (A→B, B→A), they curve in opposite
        directions to create mirror symmetry.
        
        Args:
            arc: Arc to calculate offset for
            parallels: List of parallel arcs (from detect_parallel_arcs)
            
        Returns:
            float: Offset distance in pixels (positive = counterclockwise,
                   negative = clockwise, 0 = no offset)
        """
        if not parallels:
            return 0.0  # No offset needed for single arc
        
        # Separate same-direction and opposite-direction arcs
        same_direction = []
        opposite_direction = []
        
        for other in parallels:
            if other.source == arc.source and other.target == arc.target:
                same_direction.append(other)
            elif other.source == arc.target and other.target == arc.source:
                opposite_direction.append(other)
        
        # For opposite direction arcs (most common case: A→B, B→A)
        if len(opposite_direction) == 1 and len(same_direction) == 0:
            # Two arcs in opposite directions - mirror each other
            # Use a deterministic rule: arc with lower ID gets positive offset
            other = opposite_direction[0]
            if arc.id < other.id:
                return 50.0  # Curve counterclockwise (increased from 25)
            else:
                return -50.0  # Curve clockwise (mirror, increased from -25)
        
        # For same-direction arcs or mixed cases, use stable ordering
        all_arcs = [arc] + parallels
        all_arcs.sort(key=lambda a: a.id)  # Stable ordering by ID
        
        index = all_arcs.index(arc)
        total = len(all_arcs)
        
        # Calculate offset based on number of parallel arcs
        # For 2 arcs: offsets are +15, -15
        # For 3 arcs: offsets are +20, 0, -20
        # For 4 arcs: offsets are +30, +10, -10, -30
        # Pattern: distribute evenly around center (0)
        
        if total == 1:
            return 0.0
        elif total == 2:
            # Simple case: ±15 pixels
            return 15.0 if index == 0 else -15.0
        else:
            # General case: distribute evenly with 10px spacing
            spacing = 10.0
            center = (total - 1) / 2.0
            return (index - center) * spacing
    
    def replace_arc(self, old_arc, new_arc):
        """Replace an arc with a different type (for arc transformations).
        
        Used when transforming arcs via context menu:
        - Straight ↔ Curved
        - Normal ↔ Inhibitor
        
        The new arc maintains the same ID and properties but has a different
        class type (Arc, InhibitorArc, CurvedArc, or CurvedInhibitorArc).
        
        Args:
            old_arc: Arc instance to replace
            new_arc: New arc instance (different class, same ID/properties)
        """
        try:
            index = self.arcs.index(old_arc)
            self.arcs[index] = new_arc
            
            # Ensure new arc has manager reference and change callback
            new_arc._manager = self
            new_arc.on_changed = self._on_object_changed
            
            self.mark_modified()
            self.mark_dirty()
        except ValueError:
            # Arc not found in list - may have been deleted
            pass
    
    def ensure_arc_references(self):
        """Ensure all arcs have proper manager and callback references.
        
        This is useful after loading files or batch operations to ensure
        all arcs can be transformed and detected for parallel positioning.
        """
        for arc in self.arcs:
            if not hasattr(arc, '_manager') or arc._manager is None:
                arc._manager = self
            if not hasattr(arc, 'on_changed') or arc.on_changed is None:
                arc.on_changed = self._on_object_changed
    
    def get_all_objects(self):
        """Get all Petri net objects in rendering order.
        
        Returns:
            list: All objects in rendering order (arcs behind, then P and T on top)
        """
        # Delegate to DocumentController
        return self.document_controller.get_all_objects()
    
    def find_object_at_position(self, x, y):
        """Find the topmost object at the given world position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            
        Returns:
            Place, Transition, Arc, or None: The object at the position, or None
        """
        # Delegate to DocumentController
        return self.document_controller.find_object_at_position(x, y)
    
    def clear_all_selections(self):
        """Clear selection state on all objects.
        
        Used when SelectionManager needs to clear all selections.
        """
        # Use DocumentController to get all objects, then clear selections
        for obj in self.document_controller.get_all_objects():
            obj.selected = False
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to update selection visuals
    
    def clear_all_objects(self):
        """Remove all Petri net objects from the model and reset to new document state.
        
        This resets the canvas to a fresh "default" state as if creating a new document.
        """
        # Delegate to DocumentController
        self.document_controller.clear_all_objects()
        
        # Clear selection state (additional facade-level logic)
        self.selection_manager.clear_selection()
        
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to clear visual display
    
    def find_object_at_position(self, x, y):
        """Find the topmost object at the given world position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            
        Returns:
            Place, Transition, Arc, or None: The object at the position, or None
        """
        # Check in reverse rendering order (top to bottom)
        # Transitions and places are checked first (easier to click)
        for transition in reversed(self.transitions):
            if transition.contains_point(x, y):
                return transition
        
        for place in reversed(self.places):
            if place.contains_point(x, y):
                return place
        
        # Arcs are thinner and harder to click, check them last
        for arc in reversed(self.arcs):
            if arc.contains_point(x, y):
                return arc
        
        return None
    
    def clear_all_selections(self):
        """Clear selection state on all objects.
        
        Used when SelectionManager needs to clear all selections.
        """
        for obj in self.get_all_objects():
            obj.selected = False
        self.selection_manager.clear_selection()
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to update selection visuals
    
    def _on_object_changed(self):
        """Callback when an object's properties change."""
        self.mark_modified()
        self.mark_dirty()  # Mark document as having unsaved changes
        self.mark_needs_redraw()  # Trigger canvas redraw to show property changes
    
    def create_test_objects(self):
        """Create test objects for debugging rendering.
        
        Creates a CENTER MARKER at world origin (0, 0).
        Use 'Center View' context menu to center the viewport on it.
        """
        # Create a large center marker at document origin (0, 0)
        center = self.add_place(0, 0, label="ORIGIN\n(0,0)", radius=50)
        center.set_tokens(0)
        center.set_initial_marking(0)
        center.border_color = (1.0, 0.0, 0.0)  # Red border for visibility
        center.border_width = 5.0  # Thick border
        
        
        # Show where (0,0) currently appears on screen
        screen_x, screen_y = self.world_to_screen(0, 0)
        
        if screen_x < 0 or screen_x > self.viewport_width or screen_y < 0 or screen_y > self.viewport_height:
            pass  # Origin is off-screen
        
    
    # ==================== Zoom Operations ====================
    
    def zoom_in(self, center_x=None, center_y=None):
        """Zoom in by one step, centered at the given point.
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        # Delegate to ViewportController with center coordinates
        self.viewport_controller.zoom_in(center_x, center_y)
        self._needs_redraw = True
    
    def zoom_out(self, center_x=None, center_y=None):
        """Zoom out by one step, centered at the given point.
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        # Delegate to ViewportController with center coordinates
        self.viewport_controller.zoom_out(center_x, center_y)
        self._needs_redraw = True
    
    def zoom_by_factor(self, factor, center_x=None, center_y=None):
        """Zoom by a given factor, centered at a point.
        
        Implements pointer-centered zoom using legacy algorithm:
        - Get world coordinate under cursor before zoom
        - Apply new zoom
        - Adjust pan so world coordinate stays at same screen position
        
        Args:
            factor: Multiplicative zoom factor (e.g., 1.1 = zoom in 10%).
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        # Delegate to ViewportController with center coordinates
        self.viewport_controller.zoom_by_factor(factor, center_x, center_y)
        self._needs_redraw = True
    
    def set_zoom(self, zoom_level, center_x=None, center_y=None):
        """Set absolute zoom level.
        
        Args:
            zoom_level: Target zoom level (clamped to MIN_ZOOM..MAX_ZOOM).
            center_x: X coordinate of zoom center (screen space).
            center_y: Y coordinate of zoom center (screen space).
        """
        # Delegate to ViewportController with center coordinates
        self.viewport_controller.set_zoom(zoom_level, center_x, center_y)
        self._needs_redraw = True
    
    def zoom_at_point(self, factor, center_x, center_y):
        """Zoom by a factor at a specific point with rotation support.
        
        CORRECTED APPROACH: The issue is that rotation center changes with zoom.
        We need to work backwards from the desired world point position.
        
        Args:
            factor: Multiplicative zoom factor.
            center_x: X coordinate of zoom center (screen space).
            center_y: Y coordinate of zoom center (screen space).
        """
        # STEP 1: Get world coordinates of zoom center BEFORE zoom change
        world_x, world_y = self.screen_to_world(center_x, center_y)
        
        # STEP 2: Apply new zoom with bounds
        new_zoom = self.zoom * factor
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        
        # If zoom didn't change (hit bounds), nothing to do
        if new_zoom == self.zoom:
            return
        
        # STEP 3: Update zoom
        old_zoom = self.zoom
        self.zoom = new_zoom
        self.viewport_controller.zoom = new_zoom
        
        # STEP 4: Calculate new pan
        # We want screen_to_world(center_x, center_y) == (world_x, world_y)
        # 
        # WITHOUT rotation:
        #   screen_to_world: world = screen/zoom - pan
        #   So: pan = screen/zoom - world
        #
        # WITH rotation:
        #   We need to solve this equation working backwards through the pipeline
        
        rotation = self.transformation_manager.get_rotation()
        if rotation and rotation.angle_degrees != 0:
            # The equation we need to solve:
            # 1. screen → pre_rot: pre_rot = screen/zoom - pan  (what we're solving for)
            # 2. pre_rot → world: world = rotate_inverse(pre_rot - rot_center) + rot_center
            #
            # But rot_center = viewport_center/zoom - pan (depends on pan!)
            #
            # So we have circular dependency. Let's solve it algebraically:
            # Let: cx = viewport_width/2, cy = viewport_height/2 (screen center)
            # Let: rcx = cx/zoom - pan_x, rcy = cy/zoom - pan_y (rotation center in world)
            #
            # Step 1: pre_rot = screen/zoom - pan
            # Step 2: world = R_inv(pre_rot - rot_center) + rot_center
            #         where rot_center = (cx/zoom - pan_x, cy/zoom - pan_y)
            #
            # Expanding:
            # world = R_inv((screen/zoom - pan) - (c/zoom - pan)) + (c/zoom - pan)
            # world = R_inv(screen/zoom - c/zoom) + (c/zoom - pan)
            # world = R_inv((screen - c)/zoom) + c/zoom - pan
            #
            # Solving for pan:
            # pan = c/zoom - world + R_inv((screen - c)/zoom)
            
            cx = self.viewport_width / 2.0
            cy = self.viewport_height / 2.0
            
            # (screen - c)/zoom
            screen_offset_x = (center_x - cx) / self.zoom
            screen_offset_y = (center_y - cy) / self.zoom
            
            # R_inv((screen - c)/zoom)
            cos_a = math.cos(-rotation.angle_radians)
            sin_a = math.sin(-rotation.angle_radians)
            
            rotated_x = screen_offset_x * cos_a - screen_offset_y * sin_a
            rotated_y = screen_offset_x * sin_a + screen_offset_y * cos_a
            
            # pan = c/zoom - world + R_inv((screen - c)/zoom)
            self.pan_x = (cx / self.zoom) - world_x + rotated_x
            self.pan_y = (cy / self.zoom) - world_y + rotated_y
        else:
            # No rotation: simple formula
            # world = screen/zoom - pan
            # So: pan = screen/zoom - world
            self.pan_x = (center_x / self.zoom) - world_x
            self.pan_y = (center_y / self.zoom) - world_y
        
        # Clamp pan to maintain infinite canvas bounds
        self.clamp_pan()
        
        # Save view state
        self.save_view_state_to_file()
        
        self._needs_redraw = True
    
    def clamp_pan(self):
        """Clamp pan to keep canvas bounds within viewport.
        
        Creates infinite canvas feeling while preventing blank space.
        Grid always fills viewport regardless of pan/zoom by clamping
        the pan values to ensure the canvas extent covers the screen.
        
        Canvas extent: ±CANVAS_EXTENT in world space
        Viewport: viewport_width × viewport_height in screen space
        
        The constraint is: canvas bounds must fully cover viewport.
        - Left edge: (-extent + pan) * zoom <= 0  →  pan <= extent
        - Right edge: (extent + pan) * zoom >= width  →  pan >= width/zoom - extent
        """
        # Delegate to ViewportController
        self.viewport_controller.clamp_pan()
        self._needs_redraw = True
    
    # ==================== Pan Operations ====================
    
    def pan(self, dx, dy):
        """Pan the viewport by a delta in screen coordinates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = drag right = pan increases).
            dy: Pan delta Y in screen pixels (positive = drag down = pan increases).
        """
        # Get rotation for pan delta transformation
        rotation = self.transformation_manager.get_rotation()
        
        # Delegate to ViewportController with rotation
        self.viewport_controller.pan(dx, dy, rotation=rotation)
        self._needs_redraw = True
    
    def pan_to(self, world_x, world_y):
        """Pan so that the given world coordinate is at viewport center.
        
        Args:
            world_x: Target world X coordinate.
            world_y: Target world Y coordinate.
        """
        # Delegate to ViewportController
        self.viewport_controller.pan_to(world_x, world_y)
        self._needs_redraw = True
    
    def pan_relative(self, dx, dy):
        """Pan the viewport by incremental deltas (for drag updates).
        
        This is an alias for pan() but with clearer intent for incremental updates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = pan right).
            dy: Pan delta Y in screen pixels (positive = pan down).
        """
        # Get rotation for pan delta transformation
        rotation = self.transformation_manager.get_rotation()
        
        # Delegate to ViewportController with rotation
        self.viewport_controller.pan_relative(dx, dy, rotation=rotation)
        self._needs_redraw = True
    
    def get_content_bounds(self):
        """Calculate the bounding box of all content (places and transitions).
        
        Returns:
            tuple: (min_x, min_y, max_x, max_y) or None if no content.
        """
        all_objects = list(self.places) + list(self.transitions)
        if not all_objects:
            return None
        
        # Calculate bounds
        min_x = min(obj.x for obj in all_objects)
        max_x = max(obj.x for obj in all_objects)
        min_y = min(obj.y for obj in all_objects)
        max_y = max(obj.y for obj in all_objects)
        
        return (min_x, min_y, max_x, max_y)
    
    def center_view_on_content(self):
        """Center the viewport on all content.
        
        Pans the view so that the center of all objects is at the viewport center.
        If no content exists, centers on (0, 0).
        """
        bounds = self.get_content_bounds()
        
        if bounds:
            # Calculate center of content
            min_x, min_y, max_x, max_y = bounds
            center_x = (min_x + max_x) / 2.0
            center_y = (min_y + max_y) / 2.0
        else:
            # No content, center on origin
            center_x = 0.0
            center_y = 0.0
        
        # Pan to center the content
        self.pan_to(center_x, center_y)
    
    def fit_to_page(self, padding_percent=10, deferred=False, horizontal_offset_percent=0, vertical_offset_percent=0):
        """Fit all content to viewport with optimal zoom and centering.
        
        Calculates bounding box of all objects, computes zoom level to fit
        content in viewport with padding, and centers view on content.
        
        This is typically called after loading/importing models to ensure
        all content is immediately visible to the user.
        
        Args:
            padding_percent: Percentage of viewport to leave as margin (10% default).
                           Use 15% for larger imported models (SBML/KEGG).
            deferred: If True, defer execution until next draw (when viewport size is known).
            horizontal_offset_percent: Percentage of viewport width to offset center horizontally.
                                     Positive values shift RIGHT (+X direction in Cartesian).
                                     Typical: 20-30% when right panel visible, 0% when closed.
            vertical_offset_percent: Percentage of viewport height to offset center vertically.
                                   Positive values shift UP (increase Y in Cartesian).
                                   Negative values shift DOWN (decrease Y in Cartesian).
                                   Typical: +30% to shift content up when bottom panels are open.
        
        Returns:
            bool: True if content was fitted, False if no content exists or deferred.
        """
        # If deferred, just set the flag and return
        if deferred:
            self._fit_to_page_pending = True
            self._fit_to_page_padding = padding_percent
            self._fit_to_page_horizontal_offset = horizontal_offset_percent
            self._fit_to_page_vertical_offset = vertical_offset_percent
            return False
        
        bounds = self.get_content_bounds()
        
        if not bounds:
            # No content - center on origin at default zoom
            self.zoom = 1.0
            self.viewport_controller.zoom = 1.0
            self.pan_to(0.0, 0.0)
            return False
        
        # Calculate content dimensions (add padding for object sizes)
        min_x, min_y, max_x, max_y = bounds
        
        # Add ~40px padding to account for object sizes (places/transitions are ~20-30px radius)
        content_width = max_x - min_x + 40
        content_height = max_y - min_y + 40
        
        # Handle edge case: single object or very small cluster
        if content_width < 40:
            content_width = 40
        if content_height < 40:
            content_height = 40
        
        
        # Calculate available viewport space (with padding margin)
        # Use viewport controller's dimensions (synchronized with actual widget size)
        padding_factor = 1.0 - (padding_percent / 100.0)
        available_width = self.viewport_controller.viewport_width * padding_factor
        available_height = self.viewport_controller.viewport_height * padding_factor
        
        # Compute zoom to fit both dimensions
        zoom_x = available_width / content_width if content_width > 0 else 1.0
        zoom_y = available_height / content_height if content_height > 0 else 1.0
        target_zoom = min(zoom_x, zoom_y)  # Use smaller to fit both dimensions
        
        # Clamp to zoom limits
        target_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, target_zoom))
        
        
        # Apply zoom
        self.zoom = target_zoom
        self.viewport_controller.zoom = target_zoom
        
        # Center on content
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        
        # Calculate horizontal offset in world coordinates (for right panel accommodation)
        # IMPORTANT: Offset is calculated as percentage of viewport BEFORE dividing by zoom
        # This ensures offset remains constant in screen space regardless of zoom level
        # In Cartesian world space: positive offset shifts content to the RIGHT (+X direction)
        # This is achieved by moving the viewport LEFT (adding to pan_x)
        # When right panel is open, this makes content appear more centered in visible area
        horizontal_offset_world = (horizontal_offset_percent / 100.0) * self.viewport_controller.viewport_width / target_zoom
        
        # Calculate vertical offset in world coordinates
        # IMPORTANT: Offset is calculated as percentage of viewport BEFORE dividing by zoom
        # This ensures offset remains constant in screen space regardless of zoom level
        # In Cartesian world space: positive offset shifts content UP (increase Y)
        # This is achieved by moving the viewport DOWN (adding to pan_y)
        # When bottom panels are open, use positive value to shift content up
        vertical_offset_world = (vertical_offset_percent / 100.0) * self.viewport_controller.viewport_height / target_zoom
        
        # Set pan directly without clamping (we want to show content anywhere)
        # ADD horizontal_offset to pan_x: shifts viewport LEFT, content appears RIGHT (positive X)
        # ADD vertical_offset to pan_y: shifts viewport DOWN, content appears UP (increase Y in Cartesian)
        self.viewport_controller.pan_x = center_x - (self.viewport_controller.viewport_width / 2) / target_zoom + horizontal_offset_world
        self.viewport_controller.pan_y = center_y - (self.viewport_controller.viewport_height / 2) / target_zoom + vertical_offset_world
        
        # Update local references
        self.pan_x = self.viewport_controller.pan_x
        self.pan_y = self.viewport_controller.pan_y
        
        
        # Save view state and trigger redraw (NO clamping - show content anywhere)
        self.save_view_state_to_file()
        self._needs_redraw = True
        
        return True
    
    # ==================== Grid Rendering ====================
    
    def get_grid_spacing(self):
        """Get adaptive grid spacing based on current zoom level.
        
        Uses DPI-aware physical spacing (1mm base) that adapts at zoom thresholds.
        Target at 100% zoom: 1mm minor cell, 5mm major cell (every 5th line).
        
        Returns:
            float: Grid spacing in world coordinates.
        """
        # Convert base spacing from mm to pixels
        px_per_mm = self.get_mm_to_pixels()
        base_px = self.BASE_GRID_SPACING * px_per_mm  # 1mm → pixels
        
        # Adaptive grid: spacing adapts based on zoom level
        # At high zoom (zoomed in), use smaller subdivisions for precision
        # At low zoom (zoomed out), use larger spacing to avoid clutter
        # Target: at zoom=1.0, grid spacing = 1mm (major cell = 5mm with GRID_MAJOR_EVERY=5)
        if self.zoom >= 5.0:
            return base_px / 5   # Very fine grid (0.2mm, major = 1mm)
        elif self.zoom >= 2.0:
            return base_px / 2   # Fine grid (0.5mm, major = 2.5mm)
        elif self.zoom >= 0.5:
            return base_px       # Normal grid (1mm, major = 5mm) ← TARGET at zoom=1.0
        elif self.zoom >= 0.2:
            return base_px * 2   # Coarse grid (2mm, major = 10mm)
        else:
            return base_px * 5   # Very coarse grid (5mm, major = 25mm)
    
    def get_visible_bounds(self):
        """Calculate the visible area in world coordinates.
        
        Uses screen_to_world transform to correctly map viewport corners.
        This ensures grid is regenerated for current view, creating infinite canvas illusion.
        
        IMPORTANT: When canvas is rotated, the viewport becomes a rotated rectangle in world space.
        We calculate the axis-aligned bounding box (AABB) that encompasses all four corners
        to ensure the grid covers the entire visible area at any rotation angle.
        
        This method recalculates bounds on EVERY call, adapting to pan, zoom, and rotation.
        
        Returns:
            tuple: (min_x, min_y, max_x, max_y) in world coordinates (axis-aligned bounding box).
        """
        # Transform all four viewport corners to world space
        # This accounts for rotation - corners form a rotated rectangle in world space
        top_left = self.screen_to_world(0, 0)
        top_right = self.screen_to_world(self.viewport_width, 0)
        bottom_left = self.screen_to_world(0, self.viewport_height)
        bottom_right = self.screen_to_world(self.viewport_width, self.viewport_height)
        
        # Calculate axis-aligned bounding box (AABB) that encompasses all corners
        # This ensures grid fills the entire rotated viewport
        all_x = [top_left[0], top_right[0], bottom_left[0], bottom_right[0]]
        all_y = [top_left[1], top_right[1], bottom_left[1], bottom_right[1]]
        
        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y)
        max_y = max(all_y)
        
        return min_x, min_y, max_x, max_y
    
    def get_visible_bounds_no_rotation(self):
        """Calculate the visible area WITHOUT rotation transformation.
        
        Used when rotation-independent bounds are needed for specific operations.
        Grid rendering uses get_visible_bounds() (with rotation) for infinite canvas effect.
        
        Returns:
            tuple: (min_x, min_y, max_x, max_y) in world coordinates (no rotation).
        """
        # Apply only zoom/pan transformation (skip rotation)
        min_x, min_y = coord_screen_to_world(0, 0, self.zoom, self.pan_x, self.pan_y)
        max_x, max_y = coord_screen_to_world(
            self.viewport_width, self.viewport_height,
            self.zoom, self.pan_x, self.pan_y
        )
        return min_x, min_y, max_x, max_y
    
    def draw_grid(self, cr):
        """Draw the grid pattern on the cairo context.
        
        GRID RECALCULATION: Grid is recalculated on EVERY draw call, adapting to:
        - Pan: Grid position shifts as viewport moves
        - Zoom: Grid spacing adapts (1mm base at 100% zoom)
        - Rotation: Grid bounds expand to cover rotated viewport (AABB of corners)
        
        The grid is drawn in world space with ALL transformations applied (rotation + zoom + pan).
        This creates the infinite canvas illusion - grid rotates with canvas and always fills viewport.
        
        Line widths are compensated to maintain constant pixel size regardless of zoom.
        Uses major/minor line distinction (every 5th line is major).
        
        Args:
            cr: Cairo context to draw on (with rotation + zoom + pan transforms already applied).
        """
        # Delegate to GridRenderer service
        grid_spacing = self.get_grid_spacing()
        
        # RECALCULATE BOUNDS: get_visible_bounds() transforms all 4 viewport corners
        # and computes axis-aligned bounding box (AABB) to cover rotated viewport
        # This ensures grid regenerates correctly for pan, zoom, and rotation
        min_x, min_y, max_x, max_y = self.get_visible_bounds()
        
        render_draw_grid(
            cr=cr,
            grid_style=self.grid_style,
            grid_spacing=grid_spacing,
            zoom=self.zoom,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y
        )
    
    # ==================== State Management ====================
    
    def set_viewport_size(self, width, height):
        """Update viewport size when widget is resized.
        
        Args:
            width: New viewport width in pixels.
            height: New viewport height in pixels.
        """
        # Delegate to ViewportController
        self.viewport_controller.set_viewport_size(width, height)
        
        # Handle initial pan centering (legacy compatibility)
        if not self._initial_pan_set and width > 0 and height > 0:
            # Center the canvas at origin
            self.viewport_controller.pan_to(0, 0)
            self._initial_pan_set = True
        
        self._needs_redraw = True
    
    def set_grid_style(self, style):
        """Set the grid rendering style.
        
        Args:
            style: Grid style ('line', 'dot', or 'cross').
        """
        if style in [GRID_STYLE_LINE, GRID_STYLE_DOT, GRID_STYLE_CROSS]:
            self.grid_style = style
            self._needs_redraw = True
    
    # ==================== Canvas Rotation Methods ====================
    
    def rotate_canvas_90_cw(self):
        """Rotate canvas 90° clockwise."""
        rotation = self.transformation_manager.get_rotation()
        if rotation:
            rotation.rotate_90_cw()
            self.mark_dirty()  # Mark document as having unsaved changes
            self.mark_needs_redraw()  # Trigger canvas redraw with new rotation
    
    def rotate_canvas_90_ccw(self):
        """Rotate canvas 90° counterclockwise."""
        rotation = self.transformation_manager.get_rotation()
        if rotation:
            rotation.rotate_90_ccw()
            self.mark_dirty()  # Mark document as having unsaved changes
            self.mark_needs_redraw()  # Trigger canvas redraw with new rotation
    
    def rotate_canvas_180(self):
        """Rotate canvas 180°."""
        rotation = self.transformation_manager.get_rotation()
        if rotation:
            rotation.rotate_180()
            self.mark_dirty()  # Mark document as having unsaved changes
            self.mark_needs_redraw()  # Trigger canvas redraw with new rotation
    
    def reset_canvas_rotation(self):
        """Reset canvas rotation to 0°."""
        rotation = self.transformation_manager.get_rotation()
        if rotation:
            rotation.reset()
            self.mark_dirty()  # Mark document as having unsaved changes
            self.mark_needs_redraw()  # Trigger canvas redraw with reset rotation
    
    def get_canvas_rotation_angle(self):
        """Get current canvas rotation angle in degrees.
        
        Returns:
            float: Rotation angle in degrees (0-360).
        """
        rotation = self.transformation_manager.get_rotation()
        return rotation.angle_degrees if rotation else 0.0
    
    def is_canvas_rotated(self):
        """Check if canvas is rotated.
        
        Returns:
            bool: True if canvas rotation is not 0°.
        """
        rotation = self.transformation_manager.get_rotation()
        return rotation.is_rotated if rotation else False
    
    # ==================== Pointer and Redraw Management ====================
    
    def set_pointer_position(self, x, y):
        """Update current pointer position for pointer-centered zoom.
        
        Args:
            x: Pointer X coordinate in screen space.
            y: Pointer Y coordinate in screen space.
        """
        # Delegate to ViewportController
        self.viewport_controller.set_pointer_position(x, y)
        # Also update local copy (legacy compatibility)
        self.pointer_x = x
        self.pointer_y = y
    
    def needs_redraw(self):
        """Check if canvas needs redrawing.
        
        Returns:
            bool: True if redraw is needed.
        """
        return self._needs_redraw
    
    def mark_canvas_clean(self):
        """Mark canvas as clean (drawn) - internal rendering state."""
        self._needs_redraw = False
    
    def mark_needs_redraw(self):
        """Mark canvas as needing redraw and trigger widget redraw - internal rendering state."""
        self._needs_redraw = True
        # Trigger widget redraw if callback is set
        if self._redraw_callback:
            self._redraw_callback()
    
    def set_redraw_callback(self, callback):
        """Set callback to trigger widget redraw.
        
        Args:
            callback: Function to call to trigger widget.queue_draw()
        """
        self._redraw_callback = callback
    
    # ==================== Observer Pattern ====================
    
    def register_observer(self, callback):
        """Register an observer to be notified of model changes.
        
        Observers are called with: callback(event_type, obj, old_value=None, new_value=None)
        
        Event types:
            - 'created': New object added (obj=new object)
            - 'deleted': Object removed (obj=deleted object)
            - 'modified': Object properties changed (obj=modified object)
            - 'transformed': Arc type transformed (obj=arc, old_value=old type, new_value=new type)
        
        Args:
            callback: Function to call on model changes
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unregister_observer(self, callback):
        """Unregister an observer.
        
        Args:
            callback: Function to remove from observers
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, event_type, obj, old_value=None, new_value=None):
        """Notify all registered observers of a model change.
        
        Args:
            event_type: Type of event ('created', 'deleted', 'modified', 'transformed')
            obj: The affected object
            old_value: Previous value (for 'transformed' events)
            new_value: New value (for 'transformed' events)
        """
        for callback in self._observers:
            try:
                callback(event_type, obj, old_value=old_value, new_value=new_value)
            except Exception as e:
                import traceback
                traceback.print_exc()
    
    # ==================== Info Methods ====================
    
    def get_zoom_percentage(self):
        """Get zoom level as percentage string.
        
        Returns:
            str: Zoom percentage (e.g., "100%").
        """
        return f"{int(self.zoom * 100)}%"
    
    def get_info(self):
        """Get canvas state information for debugging.
        
        Returns:
            dict: Canvas state information.
        """
        return {
            'zoom': self.zoom,
            'zoom_percent': self.get_zoom_percentage(),
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'viewport': (self.viewport_width, self.viewport_height),
            'grid_spacing': self.get_grid_spacing(),
            'visible_bounds': self.get_visible_bounds(),
        }
    
    # ==================== Document Management ====================
    
    def create_new_document(self, filename="default"):
        """Initialize a new document with default state.
        
        Args:
            filename: Base filename without extension.
            
        Returns:
            dict: Validation result with 'valid' bool and 'errors' list.
        """
        # Reset to initial state
        self.filename = filename
        self.modified = False
        self.created_at = datetime.now()
        self.modified_at = None
        
        # Reset zoom and pan to defaults
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._initial_pan_set = False
        
        # Mark for redraw but keep clean state (new empty document has no unsaved changes)
        self.mark_clean()  # New document is clean (no unsaved changes)
        self.mark_needs_redraw()  # Trigger canvas redraw with reset view
        
        # Validate initial state
        return self.validate_initial_state()
    
    def validate_initial_state(self):
        """Validate the initial state of the document.
        
        Checks:
        - Canvas dimensions are valid (> 0)
        - Zoom is at 100% (1.0)
        - Pan is centered (will be set on first draw)
        - Grid style is valid
        
        Returns:
            dict: {'valid': bool, 'errors': list of error messages}
        """
        errors = []
        
        # Check canvas dimensions
        if self.canvas_width <= 0:
            errors.append(f"Invalid canvas width: {self.canvas_width}")
        if self.canvas_height <= 0:
            errors.append(f"Invalid canvas height: {self.canvas_height}")
        
        # Check zoom is at 100%
        if abs(self.zoom - 1.0) > 0.01:
            errors.append(f"Initial zoom should be 100%, got {self.get_zoom_percentage()}")
        
        # Check zoom is within bounds
        if self.zoom < self.MIN_ZOOM or self.zoom > self.MAX_ZOOM:
            errors.append(f"Zoom out of bounds: {self.zoom} (min: {self.MIN_ZOOM}, max: {self.MAX_ZOOM})")
        
        # Check grid style is valid
        valid_styles = [self.GRID_STYLE_LINE, self.GRID_STYLE_DOT, self.GRID_STYLE_CROSS]
        if self.grid_style not in valid_styles:
            errors.append(f"Invalid grid style: {self.grid_style}")
        
        # Check filename is valid
        if not self.filename or self.filename.strip() == "":
            errors.append("Filename cannot be empty")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_document_state(self):
        """Get the current document state for saving.
        
        Returns:
            dict: Document state including metadata and canvas properties.
        """
        return {
            'filename': self.filename,
            'modified': self.modified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'canvas': {
                'width': self.canvas_width,
                'height': self.canvas_height,
                'zoom': self.zoom,
                'pan_x': self.pan_x,
                'pan_y': self.pan_y,
                'grid_style': self.grid_style,
            },
            'viewport': {
                'width': self.viewport_width,
                'height': self.viewport_height,
            }
        }
    
    def mark_modified(self):
        """Mark document as modified."""
        if not self.modified:
            self.modified = True
            self.modified_at = datetime.now()
            self.mark_dirty()
    
    def set_filename(self, filename):
        """Set the document filename.
        
        Args:
            filename: Base filename without extension.
        """
        if filename != self.filename:
            self.filename = filename
            self.mark_modified()
    
    def is_default_filename(self) -> bool:
        """Check if document has the default filename (unsaved state).
        
        This is a flag that indicates the document is in an unsaved/new state
        and should trigger file chooser dialogs in save operations.
        
        Also returns True for imported documents that haven't been saved yet,
        so they trigger "Save As" behavior on first save.
        
        Returns:
            bool: True if filename is "default" or document is imported (unsaved), False otherwise
        """
        return self.filename == "default" or self._is_imported
    
    def mark_as_imported(self, imported_name: str = None):
        """Mark this document as imported (from KEGG, SBML, etc.).
        
        Imported documents should trigger "Save As" on first save, even if they
        have a descriptive filename.
        
        Args:
            imported_name: Optional descriptive name for the imported document
        """
        self._is_imported = True
        if imported_name and imported_name != "default":
            self.filename = imported_name
    
    def mark_as_saved(self):
        """Mark this document as saved (no longer imported/new).
        
        Call this after a successful save operation to clear the imported flag.
        """
        self._is_imported = False
    
    # ==================== Per-Document File State Management (Phase 1) ====================
    
    def mark_dirty(self):
        """Mark document as having unsaved changes.
        
        This is the new per-document dirty tracking system that replaces
        the global NetObjPersistency dirty state. Each manager owns its
        own dirty flag.
        
        Automatically called when objects are modified, added, or deleted.
        Triggers on_dirty_changed callback to update UI (tab labels).
        """
        if not self._is_dirty:
            self._is_dirty = True
            # Check if callbacks are suppressed during initial setup
            if not getattr(self, '_suppress_callbacks', False):
                if self.on_dirty_changed:
                    self.on_dirty_changed(True)
    
    def mark_clean(self):
        """Mark document as saved (no unsaved changes).
        
        Call this after successful save operation.
        Triggers on_dirty_changed callback to update UI (remove asterisk from tab).
        """
        if self._is_dirty:
            self._is_dirty = False
            # Check if callbacks are suppressed during initial setup
            if not getattr(self, '_suppress_callbacks', False):
                if self.on_dirty_changed:
                    self.on_dirty_changed(False)
    
    def is_dirty(self) -> bool:
        """Check if document has unsaved changes.
        
        Returns:
            bool: True if document has been modified since last save, False otherwise
        """
        return self._is_dirty
    
    def set_filepath(self, filepath: str):
        """Set the full file path for this document.
        
        Updates both the filepath (full path) and filename (base name).
        Used when saving document or loading from file.
        
        Args:
            filepath: Full path to the .shy file (e.g., "/path/to/model.shy")
        """
        import os
        self.filepath = filepath
        if filepath:
            # Extract base filename without extension
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            self.filename = base_name
        else:
            self.filename = "default"
    
    def get_filepath(self) -> str:
        """Get the full file path for this document.
        
        Returns:
            str: Full path to file, or None if document hasn't been saved yet
        """
        return self.filepath
    
    def has_filepath(self) -> bool:
        """Check if document has an associated file path.
        
        Returns:
            bool: True if document has been saved to a file, False if new/unsaved
        """
        return self.filepath is not None and self.filepath != ""
    
    def get_display_name(self) -> str:
        """Get display name for this document.
        
        Returns:
            str: Filename if saved, "Untitled" if new document
        """
        if self.has_filepath():
            import os
            return os.path.basename(self.filepath)
        return "Untitled" if self.filename == "default" else self.filename
    
    # ==================== End Per-Document State Management ====================
    
    def to_document_model(self):
        """Convert canvas manager's Petri net objects to a DocumentModel.
        
        This creates a DocumentModel instance that can be saved/loaded by
        the persistency manager.
        
        Returns:
            DocumentModel: Document model containing all Petri net objects
        """
        from shypn.data.canvas import DocumentModel
        
        
        document = DocumentModel()
        document.places = list(self.places)
        document.transitions = list(self.transitions)
        document.arcs = list(self.arcs)
        
        
        # Sync ID counters
        document._next_place_id = self._next_place_id
        document._next_transition_id = self._next_transition_id
        document._next_arc_id = self._next_arc_id
        
        # Sync view state (zoom, pan, and transformations including rotation)
        document.view_state = {
            "zoom": self.zoom,
            "pan_x": self.pan_x,
            "pan_y": self.pan_y,
            "transformations": self.transformation_manager.to_dict()
        }
        
        return document
    
    # ==================== View State Persistence ====================
    
    def get_view_state(self):
        """Get current canvas view state for persistence.
        
        Returns:
            dict: View state containing pan_x, pan_y, zoom, and transformations (rotation)
        """
        return {
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'zoom': self.zoom,
            'transformations': self.transformation_manager.to_dict()
        }
    
    def set_view_state(self, view_state):
        """Restore canvas view state from saved data.
        
        Args:
            view_state: Dictionary containing pan_x, pan_y, zoom, and transformations
        """
        if view_state:
            self.pan_x = view_state.get('pan_x', 0.0)
            self.pan_y = view_state.get('pan_y', 0.0)
            self.zoom = view_state.get('zoom', 1.0)
            
            # Clamp zoom to valid range
            self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom))
            
            # Clamp pan to infinite canvas bounds
            self.clamp_pan()
            
            # Restore transformations (rotation)
            if 'transformations' in view_state:
                self.transformation_manager.from_dict(view_state['transformations'])
            
            # Mark that we don't need initial centering
            self._initial_pan_set = True
            
            self.mark_dirty()  # Mark document as having unsaved changes
            self.mark_needs_redraw()  # Trigger canvas redraw with restored view
    
    def save_view_state_to_file(self, filepath=None):
        """Save current view state to a JSON file.
        
        Args:
            filepath: Optional custom file path. If None, uses default location.
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if filepath is None:
            # Create .shypn config directory in user's home
            config_dir = os.path.expanduser('~/.shypn')
            os.makedirs(config_dir, exist_ok=True)
            
            # Use filename to create view state file
            filename = self.filename if self.filename else 'default'
            filepath = os.path.join(config_dir, f'{filename}_view.json')
        
        try:
            view_state = self.get_view_state()
            with open(filepath, 'w') as f:
                json.dump(view_state, f, indent=2)
            return True
        except Exception as e:
            return False
    
    def load_view_state_from_file(self, filepath=None):
        """Load view state from a JSON file.
        
        If no view state file exists or loading fails, centers the view on content.
        
        Args:
            filepath: Optional custom file path. If None, uses default location.
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if filepath is None:
            # Look for view state file in config directory
            config_dir = os.path.expanduser('~/.shypn')
            filename = self.filename if self.filename else 'default'
            filepath = os.path.join(config_dir, f'{filename}_view.json')
        
        if not os.path.exists(filepath):
            # No saved view state - center on content as fallback
            self.center_view_on_content()
            return False
        
        try:
            with open(filepath, 'r') as f:
                view_state = json.load(f)
            self.set_view_state(view_state)
            return True
        except Exception as e:
            # Failed to load - center on content as fallback
            self.center_view_on_content()
            return False
