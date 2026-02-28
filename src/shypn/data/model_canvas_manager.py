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

╔═══════════════════════════════════════════════════════════════════════════╗
║ ARCHITECTURE NOTE: This class is intentionally large (2700+ lines)        ║
║                                                                            ║
║ REASON: SHYPN implements pseudo-MDI where GTK4/Wayland don't support it. ║
║         Viewport, document, grid, and event state MUST stay synchronized  ║
║         to maintain panel switching and focus management.                 ║
║                                                                            ║
║ ⚠️  DO NOT SPLIT: Viewport/document/grid into separate managers          ║
║ ⚠️  DO NOT SPLIT: Event emission from state changes                      ║
║ ⚠️  DO NOT SPLIT: Object lifecycle to separate class                     ║
║                                                                            ║
║ SAFE REFACTORINGS:                                                        ║
║ ✅ Extract pure algorithms (geometry calculations, validations)           ║
║ ✅ Create value objects (ViewportState, RenderContext, etc.)              ║
║ ✅ Extract Wayland parent management to helper class                      ║
║ ✅ Group related methods with section comments                            ║
║                                                                            ║
║ SEE: doc/ADR-002-model-canvas-manager-size.md (when created)              ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
import math
import json
import os
import time
from datetime import datetime
from shypn.events import EventBus
from shypn.core.document_id import doc_id
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
    MIN_ZOOM = 0.05  # 5% minimum (allows viewing very large models)
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
        
        # Reference to the canvas loader (set by loader after creation)
        self._canvas_loader = None
        self._drawing_area = None
        
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
        
        # REMOVED: simulation_settings (moved to controller, session-specific)
        # Simulation parameters like duration, dt, batch mode should NOT be model-dependent
        
        # Document model for storing metadata and settings
        # This provides a persistent model for thermodynamic settings, compound mappings, etc.
        from shypn.data.canvas import DocumentModel
        self._document_model = DocumentModel()
        
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
        
        # Arc geometry service (Phase 6 extraction — pure math + arc mutation)
        from shypn.core.services.arc_geometry_service import ArcGeometryService
        self._arc_geometry = ArcGeometryService(manager=self)
        
        # Ensure all arcs have proper manager references
        self.ensure_arc_references()
    
    # ==================== Property Proxies (Backward Compatibility) ====================
    # These properties delegate to controllers for backward compatibility
    
    @property
    def document(self):
        """Get the document model for this canvas.
        
        This provides access to document-level settings and metadata including:
        - Thermodynamic settings (pH, temperature, presets)
        - Compound mappings (place ID → compound ID)
        - Petri net objects (places, transitions, arcs)
        - Document-level properties and metadata
        
        ModelCanvasManager serves as its own document model via property delegation.
        
        Returns:
            ModelCanvasManager: Self (provides unified access to all document components)
        """
        return self
    
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
        """Get next place ID counter (delegates to IDManager)."""
        return self.document_controller.id_manager._next_place_id
    
    @_next_place_id.setter
    def _next_place_id(self, value):
        """Set next place ID counter (delegates to IDManager)."""
        self.document_controller.id_manager._next_place_id = value
    
    @property
    def _next_transition_id(self):
        """Get next transition ID counter (delegates to IDManager)."""
        return self.document_controller.id_manager._next_transition_id
    
    @_next_transition_id.setter
    def _next_transition_id(self, value):
        """Set next transition ID counter (delegates to IDManager)."""
        self.document_controller.id_manager._next_transition_id = value
    
    @property
    def _next_arc_id(self):
        """Get next arc ID counter (delegates to IDManager)."""
        return self.document_controller.id_manager._next_arc_id
    
    @_next_arc_id.setter
    def _next_arc_id(self, value):
        """Set next arc ID counter (delegates to IDManager)."""
        self.document_controller.id_manager._next_arc_id = value
    
    @property
    def thermodynamic_settings(self):
        """Get thermodynamic settings dictionary (delegates to DocumentModel)."""
        return self._document_model.thermodynamic_settings
    
    @property
    def compound_mappings(self):
        """Get compound mappings dictionary (delegates to DocumentModel)."""
        return self._document_model.compound_mappings
    
    @property
    def metadata(self):
        """Get metadata dictionary (delegates to DocumentModel).
        
        Metadata contains model provenance and import information:
        - name: Model name
        - source/source_type: Import source (KEGG, SBML)
        - source_id/pathway_id: Source identifier
        - organism/source_organism: Organism name
        - imported_date/created: Import/creation timestamp
        - raw_file/original_file: Original file path
        """
        if hasattr(self._document_model, 'metadata'):
            return self._document_model.metadata
        return {}
    
    def update_thermodynamic_settings(self, **kwargs):
        """Update thermodynamic settings (delegates to DocumentModel)."""
        return self._document_model.update_thermodynamic_settings(**kwargs)
    
    def set_thermodynamic_preset(self, preset_id):
        """Apply thermodynamic preset (delegates to DocumentModel)."""
        return self._document_model.set_thermodynamic_preset(preset_id)
    
    def get_thermodynamic_setting(self, key: str, default=None):
        """Get a specific thermodynamic setting value (delegates to DocumentModel)."""
        return self._document_model.get_thermodynamic_setting(key, default)
    
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
    
    # Helper methods for coordinate transformations (PHASE 1 EXTRACTION)
    
    def _calculate_rotation_center(self):
        """Calculate rotation center in world coordinates.
        
        The rotation center is the viewport center transformed to world space.
        
        Returns:
            tuple: (center_world_x, center_world_y)
        """
        center_world_x = self.viewport_width / (2.0 * self.zoom) - self.pan_x
        center_world_y = self.viewport_height / (2.0 * self.zoom) - self.pan_y
        return center_world_x, center_world_y
    
    @staticmethod
    def _apply_rotation_to_point(x, y, center_x, center_y, cos_angle, sin_angle):
        """Apply rotation transformation to a point around a center.
        
        Args:
            x, y: Point coordinates
            center_x, center_y: Rotation center
            cos_angle, sin_angle: Rotation angle (cosine and sine)
            
        Returns:
            tuple: (rotated_x, rotated_y)
        """
        # Translate to origin
        dx = x - center_x
        dy = y - center_y
        
        # Rotate
        rotated_dx = dx * cos_angle - dy * sin_angle
        rotated_dy = dx * sin_angle + dy * cos_angle
        
        # Translate back
        return rotated_dx + center_x, rotated_dy + center_y
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world (model) coordinates.
        
        Applies transformations in order: zoom/pan inverse, then rotation inverse.
        This matches the drawing pipeline: zoom/pan → rotation.
        
        REFACTORED: Now uses extracted helper methods for rotation calculations.
        
        Args:
            screen_x: X coordinate in screen space (pixels).
            screen_y: Y coordinate in screen space (pixels).
            
        Returns:
            tuple: (world_x, world_y) in model coordinate space.
        """
        # Step 1: Apply zoom/pan inverse transformation (screen → pre-rotation space)
        pre_rot_x, pre_rot_y = coord_screen_to_world(screen_x, screen_y, self.zoom, self.pan_x, self.pan_y)
        
        # Step 2: Apply rotation inverse transformation (pre-rotation → world space)
        rotation = self.transformation_manager.get_rotation()
        if rotation and rotation.angle_degrees != 0:
            center_world_x, center_world_y = self._calculate_rotation_center()
            cos_a = math.cos(-rotation.angle_radians)  # Negative for inverse rotation
            sin_a = math.sin(-rotation.angle_radians)
            return self._apply_rotation_to_point(pre_rot_x, pre_rot_y, center_world_x, center_world_y, cos_a, sin_a)
        else:
            return pre_rot_x, pre_rot_y
    
    def world_to_screen(self, world_x, world_y):
        """Convert world (model) coordinates to screen coordinates.
        
        Applies transformations in order: rotation, then zoom/pan.
        This matches the drawing pipeline: zoom/pan → rotation (applied in reverse).
        
        REFACTORED: Now uses extracted helper methods for rotation calculations.
        
        Args:
            world_x: X coordinate in world space.
            world_y: Y coordinate in world space.
            
        Returns:
            tuple: (screen_x, screen_y) in screen coordinate space (pixels).
        """
        # Step 1: Apply rotation transformation (world → pre-screen space)
        rotation = self.transformation_manager.get_rotation()
        if rotation and rotation.angle_degrees != 0:
            center_world_x, center_world_y = self._calculate_rotation_center()
            cos_a = math.cos(rotation.angle_radians)
            sin_a = math.sin(rotation.angle_radians)
            pre_screen_x, pre_screen_y = self._apply_rotation_to_point(
                world_x, world_y, center_world_x, center_world_y, cos_a, sin_a
            )
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
        
        # Emit EventBus event
        if self._drawing_area:
            EventBus.emit('model.place.created', {
                'object': place,
                'object_type': 'place',
                'object_id': place.id,
                'action': 'created',
                'timestamp': time.time(),
                'batch_id': None
            }, document_id=doc_id(self._drawing_area))
        
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
        
        # Emit EventBus event
        if self._drawing_area:
            EventBus.emit('model.transition.created', {
                'object': transition,
                'object_type': 'transition',
                'object_id': transition.id,
                'action': 'created',
                'timestamp': time.time(),
                'batch_id': None
            }, document_id=doc_id(self._drawing_area))
        
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
        
        # Emit EventBus event
        if self._drawing_area:
            EventBus.emit('model.arc.created', {
                'object': arc,
                'object_type': 'arc',
                'object_id': arc.id,
                'action': 'created',
                'timestamp': time.time(),
                'batch_id': None
            }, document_id=doc_id(self._drawing_area))
        
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
        
        # Emit EventBus event
        if self._drawing_area:
            EventBus.emit('model.place.deleted', {
                'object': place,
                'object_type': 'place',
                'object_id': place.id,
                'action': 'deleted',
                'timestamp': time.time(),
                'batch_id': None
            }, document_id=doc_id(self._drawing_area))
    
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
        
        # Emit EventBus event
        if self._drawing_area:
            EventBus.emit('model.transition.deleted', {
                'object': transition,
                'object_type': 'transition',
                'object_id': transition.id,
                'action': 'deleted',
                'timestamp': time.time(),
                'batch_id': None
            }, document_id=doc_id(self._drawing_area))
    
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
        
        # Emit EventBus event
        if self._drawing_area:
            EventBus.emit('model.arc.deleted', {
                'object': arc,
                'object_type': 'arc',
                'object_id': arc.id,
                'action': 'deleted',
                'timestamp': time.time(),
                'batch_id': None
            }, document_id=doc_id(self._drawing_area))
    
    # ==================== Object Loading (Bulk Import/Deserialize) ====================
    
    def _load_modules(self, modules):
        """Load modules into document controller.
        
        Args:
            modules: Dict of Module objects to add
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if modules and hasattr(self, 'document_controller'):
            if not hasattr(self.document_controller, 'modules'):
                self.document_controller.modules = {}
            self.document_controller.modules.update(modules)
            logger.info(f"[LOAD_OBJECTS] Loaded {len(modules)} modules to document_controller")
    
    def _add_objects_with_notification(self, places, transitions, arcs):
        """Add places, transitions, and arcs with observer notification.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
            arcs: List of Arc objects
        """
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
    
    def _validate_and_clean_arcs(self, arcs):
        """Validate arcs and remove corrupted ones, then auto-convert parallel arcs.
        
        Args:
            arcs: List of Arc objects to validate
            
        Returns:
            List of valid arcs (corrupted arcs removed)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Validate and remove corrupted arcs BEFORE auto-conversion
        # Corrupted arcs can have invalid source/target references
        validation = self.validate_arcs()
        if not validation['valid']:
            logger.warning(f"[ARC_VALIDATION] ⚠️ Detected {len(validation['corrupted_arcs'])} corrupted arc(s) after load")
            for error in validation['errors']:
                logger.warning(f"[ARC_VALIDATION]   - {error}")
            removed = self.remove_corrupted_arcs()
            logger.info(f"[ARC_VALIDATION] ✅ Cleaned up {removed} corrupted arc(s)")
            # Filter out removed arcs from the arcs list
            arcs = [arc for arc in arcs if arc in self.arcs]
        
        # Auto-convert loop arcs and parallel arcs to curved
        for arc in arcs:
            self._auto_convert_parallel_arcs_to_curved(arc)
        
        return arcs
    
    def _register_object_ids(self, places, transitions, arcs):
        """Register object IDs with IDManager to avoid collisions.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
            arcs: List of Arc objects
        """
        # Ensure lifecycle scope is set to this canvas before registering
        try:
            if self._canvas_loader and hasattr(self._canvas_loader, 'lifecycle_manager') and self._drawing_area:
                from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
                set_lifecycle_scope_manager(self._canvas_loader.lifecycle_manager.id_manager)
                self._canvas_loader.lifecycle_manager.id_manager.set_scope(f"canvas_{id(self._drawing_area)}")
        except (AttributeError, TypeError, RuntimeError) as e:
            self.logger.debug(f"Failed to set lifecycle ID scope in canvas manager: {e}")
        
        if places:
            for p in self.places:
                self.document_controller.id_manager.register_place_id(p.id)
        
        if transitions:
            for t in self.transitions:
                self.document_controller.id_manager.register_transition_id(t.id)
        
        if arcs:
            for a in self.arcs:
                self.document_controller.id_manager.register_arc_id(a.id)
    
    def _reset_places_to_initial_marking(self, places):
        """Reset all places to their initial marking state.
        
        When loading (File Open, KEGG import, SBML import), start with initial state
        rather than simulation state. Critical for test arcs (catalysts).
        
        Args:
            places: List of Place objects to reset
        """
        for place in places:
            if hasattr(place, 'initial_marking'):
                place.tokens = place.initial_marking
    
    def _trigger_simulation_reset(self):
        """Trigger simulation controller reset after loading objects.
        
        Uses Global Canvas State Lifecycle system for proper initialization.
        Clears stale state from previous model (behavior_cache, transition_states, etc).
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("[LOAD_OBJECTS] Requesting simulation reset via lifecycle_manager")
        
        # Try to use lifecycle manager first (proper architecture)
        if self._canvas_loader and hasattr(self._canvas_loader, 'lifecycle_manager'):
            lifecycle_mgr = self._canvas_loader.lifecycle_manager
            if lifecycle_mgr and self._drawing_area:
                try:
                    logger.info("[LOAD_OBJECTS] Using lifecycle_manager.sync_after_file_load()")
                    lifecycle_mgr.sync_after_file_load(self._drawing_area, file_path=None)
                    logger.info("[LOAD_OBJECTS] ✅ Lifecycle manager sync complete")
                except (AttributeError, TypeError, RuntimeError) as e:
                    logger.warning(f"[LOAD_OBJECTS] Lifecycle manager sync failed: {e}, falling back")
                    logger.info("[LOAD_OBJECTS] Calling _request_simulation_reset_direct() as fallback")
                    self._request_simulation_reset_direct()
                    logger.info("[LOAD_OBJECTS] Fallback reset complete")
            else:
                logger.info("[LOAD_OBJECTS] No lifecycle_manager available, using direct reset")
                self._request_simulation_reset_direct()
        else:
            logger.info("[LOAD_OBJECTS] No canvas_loader reference, using direct reset")
            self._request_simulation_reset_direct()
    
    def _refresh_viability_panel(self):
        """Refresh viability panel observer with updated KB after objects loaded.
        
        The viability panel observer needs to re-scan the KB now that it has data.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if self._canvas_loader and self._drawing_area:
            logger.info("[LOAD_OBJECTS] Refreshing viability panel with populated KB")
            try:
                overlay_mgr = self._canvas_loader.overlay_managers.get(self._drawing_area)
                if overlay_mgr:
                    viability_loader = getattr(overlay_mgr, 'viability_panel_loader', None)
                    if viability_loader:
                        panel = viability_loader.panel
                        panel.refresh_all()
                        logger.info("[LOAD_OBJECTS] ✅ Viability panel refreshed")
                    else:
                        logger.info("[LOAD_OBJECTS] No viability_panel_loader found")
                else:
                    logger.info("[LOAD_OBJECTS] No overlay_manager found")
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.warning(f"[LOAD_OBJECTS] Failed to refresh viability panel: {e}")
    
    def load_objects(self, places=None, transitions=None, arcs=None, modules=None):
        """Load objects into the model in bulk (for import/deserialize operations).
        
        This method ensures all objects are added through proper channels with
        automatic observer notification, providing a UNIFIED PATH for both manual
        creation and import/load operations.
        
        REFACTORED: Now delegates to helper methods for better readability.
        
        Args:
            places: List of Place objects to add (default: None = no places)
            transitions: List of Transition objects to add (default: None = no transitions)
            arcs: List of Arc objects to add (default: None = no arcs)
            modules: Dict of Module objects to add (default: None = no modules)
        
        Example:
            manager.load_objects(
                places=document_model.places,
                transitions=document_model.transitions,
                arcs=document_model.arcs
            )
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[LOAD_OBJECTS] Called with {len(places or [])} places, {len(transitions or [])} transitions, {len(arcs or [])} arcs")
        
        # Normalize input parameters
        places = places or []
        transitions = transitions or []
        arcs = arcs or []
        modules = modules or {}
        
        # Orchestrate loading workflow using extracted helper methods
        self._load_modules(modules)
        self._add_objects_with_notification(places, transitions, arcs)
        arcs = self._validate_and_clean_arcs(arcs)
        self._register_object_ids(places, transitions, arcs)
        self._reset_places_to_initial_marking(places)
        self._trigger_simulation_reset()
        
        # Mark document state
        self.mark_dirty()
        self.mark_needs_redraw()
        
        # Refresh dependent panels
        self._refresh_viability_panel()
    
    def _request_simulation_reset_direct(self):
        """Request simulation controller reset DIRECTLY (not via idle callback).
        
        This is the new approach that ensures the reset completes before
        simulation starts, and step listeners are properly re-registered.
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("[RESET_DIRECT] Starting direct simulation reset")
            
            # Validate stored references
            canvas_loader, drawing_area = self._validate_stored_references(logger)
            if not canvas_loader or not drawing_area:
                return
            
            logger.info("[RESET_DIRECT] Found canvas_loader and drawing_area via stored references")
            
            # Execute reset and initialization
            self._execute_simulation_reset(canvas_loader, drawing_area, logger)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[RESET_DIRECT] ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Helper methods for _request_simulation_reset_direct (PHASE 1 EXTRACTION)
    
    def _validate_stored_references(self, logger):
        """Validate stored canvas_loader and drawing_area references.
        
        Args:
            logger: Logger instance.
            
        Returns:
            tuple: (canvas_loader, drawing_area) or (None, None) if invalid.
        """
        canvas_loader = self._canvas_loader
        drawing_area = self._drawing_area
        
        if not canvas_loader:
            logger.warning("[RESET_DIRECT] ⚠️  No canvas_loader reference stored")
            return None, None
        
        if not drawing_area:
            logger.warning("[RESET_DIRECT] ⚠️  No drawing_area reference stored")
            return None, None
        
        return canvas_loader, drawing_area
    
    def _execute_simulation_reset(self, canvas_loader, drawing_area, logger):
        """Execute simulation reset and initialize transition states.
        
        Args:
            canvas_loader: Canvas loader instance.
            drawing_area: Drawing area instance.
            logger: Logger instance.
        """
        if not hasattr(canvas_loader, '_ensure_simulation_reset'):
            logger.warning("[RESET_DIRECT] ⚠️  _ensure_simulation_reset not found on canvas_loader")
            return
        
        logger.info("[RESET_DIRECT] Calling _ensure_simulation_reset()")
        canvas_loader._ensure_simulation_reset(drawing_area)
        
        # Initialize transition states after reset
        controller = canvas_loader.simulation_controllers.get(drawing_area)
        if controller:
            logger.info(f"[RESET_DIRECT] Initializing transition states for {len(self.transitions)} transitions")
            self._initialize_transition_states(controller)
            logger.info(f"[RESET_DIRECT] ✅ Controller has {len(controller.step_listeners)} step listeners")
        else:
            logger.warning("[RESET_DIRECT] ⚠️  Could not get controller")
        
        logger.info("[RESET_DIRECT] ✅ Simulation controller reset and initialized")
    
    # Helper methods for _request_simulation_reset (PHASE 1 EXTRACTION)
    
    @staticmethod
    def _find_canvas_loader(manager):
        """Find the canvas_loader instance that owns this manager.
        
        Args:
            manager: ModelCanvasManager instance
            
        Returns:
            canvas_loader instance or None
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Import here to avoid circular dependency at module load time
        from shypn.helpers import model_canvas_loader
        
        # Try singleton instance first
        if hasattr(model_canvas_loader, '_instance'):
            logger.info("[IDLE_RESET] Found canvas_loader via _instance")
            return model_canvas_loader._instance
        
        # Fallback: try to find via manager attributes
        for loader_attr in ['canvas_loader', '_canvas_loader']:
            if hasattr(manager, loader_attr):
                canvas_loader = getattr(manager, loader_attr)
                logger.info(f"[IDLE_RESET] Found canvas_loader via {loader_attr}")
                return canvas_loader
        
        logger.warning("[IDLE_RESET] ⚠️  Could not find canvas_loader")
        return None
    
    @staticmethod
    def _find_drawing_area(canvas_loader, manager):
        """Find the drawing_area for this manager.
        
        Args:
            canvas_loader: Canvas loader instance
            manager: ModelCanvasManager instance
            
        Returns:
            drawing_area widget or None
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not hasattr(canvas_loader, 'canvas_managers'):
            logger.warning("[IDLE_RESET] ⚠️  canvas_loader has no canvas_managers dict")
            return None
        
        for da, mgr in canvas_loader.canvas_managers.items():
            if mgr == manager:
                logger.info("[IDLE_RESET] Found matching drawing_area")
                return da
        
        logger.warning("[IDLE_RESET] ⚠️  Could not find drawing_area for this manager")
        return None
    
    @staticmethod
    def _perform_simulation_reset(canvas_loader, drawing_area, manager):
        """Perform the simulation controller reset and transition initialization.
        
        Args:
            canvas_loader: Canvas loader instance
            drawing_area: GTK drawing area widget
            manager: ModelCanvasManager instance
            
        Returns:
            True if successful, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not hasattr(canvas_loader, '_ensure_simulation_reset'):
            logger.warning("[IDLE_RESET] ⚠️  _ensure_simulation_reset not found")
            return False
        
        # Call the reset method (handles controller reset + listener re-registration)
        canvas_loader._ensure_simulation_reset(drawing_area)
        
        # CRITICAL: After reset, initialize transition states for all transitions
        # This ensures source transitions and other transitions are immediately
        # ready to fire without needing a manual "wakeup" action
        controller = canvas_loader.simulation_controllers.get(drawing_area)
        if controller:
            manager._initialize_transition_states(controller)
            logger.info(f"✅ Simulation controller reset and initialized after load_objects()")
            logger.info(f"   Controller has {len(controller.step_listeners)} step listeners")
            return True
        else:
            logger.warning("[IDLE_RESET] ⚠️  Could not get controller after reset")
            return False
    
    def _request_simulation_reset(self):
        """Request simulation controller reset for this canvas.
        
        Called after load_objects() to ensure simulation controller is in clean
        state for the newly loaded model. This is critical for imports (KEGG, SBML)
        that auto-load models into canvas.
        
        Implementation uses GLib.idle_add to:
        1. Avoid circular dependency (manager → canvas_loader → controller → manager)
        2. Ensure reset happens after GTK main loop processes the object additions
        3. Give canvas time to stabilize before resetting controller
        
        REFACTORED: Now delegates to extracted helper methods for better readability.
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("[REQUEST_RESET] _request_simulation_reset() called")
            
            # Setup GLib and schedule idle callback
            import gi
            gi.require_version('GLib', '2.0')
            from gi.repository import GLib
            
            logger.info("[REQUEST_RESET] About to schedule idle callback with GLib.idle_add()")
            
            # Schedule reset on idle using extracted callback
            result = GLib.idle_add(self._create_reset_callback())
            logger.info(f"[REQUEST_RESET] GLib.idle_add() returned: {result}")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[REQUEST_RESET] ❌ Exception in _request_simulation_reset: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_reset_callback(self):
        """Create the idle callback function for simulation reset.
        
        Returns:
            callable: Callback function for GLib.idle_add
        """
        def reset_on_idle():
            """Reset controller on GTK idle (after canvas updates)."""
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info("[IDLE_RESET] Idle callback triggered - starting reset")
                
                # Find canvas_loader and drawing_area
                canvas_loader = self._find_canvas_loader(self)
                if not canvas_loader:
                    logger.warning("[IDLE_RESET] ⚠️  Could not find canvas_loader")
                    return False
                
                drawing_area = self._find_drawing_area(canvas_loader, self)
                if not drawing_area:
                    logger.warning("[IDLE_RESET] ⚠️  Could not find drawing_area")
                    return False
                
                # Perform reset
                success = self._perform_simulation_reset(canvas_loader, drawing_area, self)
                if not success:
                    logger.warning("[IDLE_RESET] ⚠️  Reset failed")
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"❌ Failed to reset simulation after load: {e}")
                import traceback
                traceback.print_exc()
            
            return False  # Don't repeat
        
        return reset_on_idle
    
    def _initialize_transition_states(self, controller):
        """Initialize transition states for all transitions in the model.
        
        Called after simulation controller reset to ensure all transitions
        (especially source transitions) are immediately ready to fire without
        needing a manual "wakeup" action (like drawing on canvas).
        
        Args:
            controller: SimulationController instance to initialize
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            from shypn.engine.simulation.controller import TransitionState
            
            logger.info(f"[INIT_STATES] Initializing transition states for {len(self.transitions)} transitions")
            
            source_count = 0
            for transition in self.transitions:
                # Ensure transition state exists
                if transition.id not in controller.transition_states:
                    controller.transition_states[transition.id] = TransitionState()
                
                behavior = controller._get_behavior(transition)
                is_source = getattr(transition, 'is_source', False)
                
                if is_source:
                    source_count += 1
                    self._enable_source_transition(controller, transition, behavior, logger)
                else:
                    self._check_and_enable_transition(controller, transition, behavior, logger)
            
            logger.info(f"[INIT_STATES] ✅ Complete: {len(controller.transition_states)} transitions, {source_count} sources enabled")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize transition states: {e}")
            import traceback
            traceback.print_exc()
    
    # Helper methods for _initialize_transition_states (PHASE 1 EXTRACTION)
    
    @staticmethod
    def _enable_source_transition(controller, transition, behavior, logger):
        """Enable a source transition (no input arcs).
        
        Args:
            controller: Simulation controller.
            transition: Transition to enable.
            behavior: Transition behavior.
            logger: Logger instance.
        """
        state = controller.transition_states[transition.id]
        state.enablement_time = controller.time
        if hasattr(behavior, 'set_enablement_time'):
            behavior.set_enablement_time(controller.time)
        logger.info(f"[INIT_STATES] ✅ {transition.id}: Source transition enabled at t={controller.time}")
    
    @staticmethod
    def _check_and_enable_transition(controller, transition, behavior, logger):
        """Check and enable non-source transition if inputs are satisfied.
        
        Args:
            controller: Simulation controller.
            transition: Transition to check.
            behavior: Transition behavior.
            logger: Logger instance.
        """
        input_arcs = behavior.get_input_arcs()
        locally_enabled = True
        
        for arc in input_arcs:
            source_place = behavior._get_place(arc.source_id)
            if source_place is None or source_place.tokens < arc.weight:
                locally_enabled = False
                break
        
        if locally_enabled:
            state = controller.transition_states[transition.id]
            state.enablement_time = controller.time
            if hasattr(behavior, 'set_enablement_time'):
                behavior.set_enablement_time(controller.time)
            logger.debug(f"  {transition.id}: Enabled at t=0 (has sufficient tokens)")
        else:
            logger.debug(f"  {transition.id}: Not enabled (insufficient tokens)")
    
    def detect_parallel_arcs(self, arc):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry.detect_parallel_arcs(arc)
    
    def _auto_convert_parallel_arcs_to_curved(self, new_arc):
        """Delegate to ArcGeometryService."""
        self._arc_geometry.auto_convert_parallel_arcs_to_curved(new_arc)
    
    def _validate_arc_references(self, arc):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry.validate_arc_references(arc)
    
    def _convert_loop_arc(self, arc):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._convert_loop_arc(arc)
    
    def _find_opposite_direction_arc(self, arc, parallels):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._find_opposite_direction_arc(arc, parallels)
    
    def _calculate_perpendicular_offset(self, arc1, arc2, offset_distance=50.0):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._calculate_perpendicular_offset(arc1, arc2, offset_distance)
    
    # Helper methods for _calculate_perpendicular_offset (PHASE 1 EXTRACTION)
    
    def _compute_direction_vector(self, arc):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._compute_direction_vector(arc)
    
    def _normalize_vector(self, dx, dy, length):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._normalize_vector(dx, dy, length)
    
    def _compute_perpendicular_vector(self, dx, dy):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._compute_perpendicular_vector(dx, dy)
    
    def _compute_offset_pair(self, arc1, arc2, perp_x, perp_y, offset_distance):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._compute_offset_pair(arc1, arc2, perp_x, perp_y, offset_distance)
    
    def _convert_opposite_direction_pair(self, new_arc, opposite_arc):
        """Delegate to ArcGeometryService."""
        self._arc_geometry._convert_opposite_direction_pair(new_arc, opposite_arc)
    
    def _convert_same_direction_parallels(self, new_arc, parallels):
        """Delegate to ArcGeometryService."""
        self._arc_geometry._convert_same_direction_parallels(new_arc, parallels)
    
    def _replace_arc_in_list(self, old_arc, new_arc):
        """Delegate to ArcGeometryService."""
        self._arc_geometry._replace_arc_in_list(old_arc, new_arc)
    
    # Helper methods for calculate_arc_offset (PHASE 1 EXTRACTION)
    
    def _separate_parallel_arcs(self, arc, parallels):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._separate_parallel_arcs(arc, parallels)
    
    def _calculate_opposite_direction_offset(self, arc, opposite_arc):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._calculate_opposite_direction_offset(arc, opposite_arc)
    
    def _calculate_same_direction_offset(self, arc, all_arcs):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry._calculate_same_direction_offset(arc, all_arcs)
    
    def calculate_arc_offset(self, arc, parallels):
        """Delegate to ArcGeometryService."""
        return self._arc_geometry.calculate_arc_offset(arc, parallels)
    
    def replace_arc(self, old_arc, new_arc):
        """Delegate to ArcGeometryService."""
        self._arc_geometry.replace_arc(old_arc, new_arc)
    
    def ensure_arc_references(self):
        """Delegate to ArcGeometryService (no-op during __init__ before service is created)."""
        if hasattr(self, '_arc_geometry'):
            self._arc_geometry.ensure_arc_references()
    
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

        Delegates rotation-aware zoom math to ViewportController.

        Args:
            factor: Multiplicative zoom factor.
            center_x: X coordinate of zoom center (screen space).
            center_y: Y coordinate of zoom center (screen space).
        """
        # Convert screen focal point to world space before zoom changes anything
        world_x, world_y = self.screen_to_world(center_x, center_y)
        rotation = self.transformation_manager.get_rotation()
        changed = self.viewport_controller.zoom_at_point_rotation_aware(
            factor, center_x, center_y, world_x, world_y, rotation
        )
        if changed:
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
        """Calculate the bounding box of all content (places, transitions, and arcs).

        Delegates to ViewportController which owns the pure-math algorithm.

        Returns:
            tuple: (min_x, min_y, max_x, max_y) or None if no content.
        """
        return self.viewport_controller.get_content_bounds(
            self.places, self.transitions, self.arcs
        )

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
        
        Calculates bounding box, computes zoom level to fit content with padding,
        and centers view on content.
        
        REFACTORED: Now delegates to helper methods for better readability.
        
        Args:
            padding_percent: Percentage of viewport to leave as margin (10% default)
            deferred: If True, defer execution until next draw
            horizontal_offset_percent: Percentage offset (+ = right, - = left)
            vertical_offset_percent: Percentage offset (+ = down, - = up)
            
        Returns:
            bool: True if content was fitted, False if no content or deferred
        """
        # Handle deferred execution
        if deferred:
            return self._defer_fit_to_page(padding_percent, horizontal_offset_percent, vertical_offset_percent)

        bounds = self.get_content_bounds()

        # Handle empty content
        if not bounds:
            return self._handle_empty_content()

        # Delegate zoom + pan + offset maths to ViewportController
        self.viewport_controller.fit_content(
            bounds, padding_percent, horizontal_offset_percent, vertical_offset_percent
        )

        self._finalize_view_state()
        return True
    
    # Helper methods for fit_to_page (PHASE 1 EXTRACTION)
    
    def _defer_fit_to_page(self, padding_percent, horizontal_offset_percent, vertical_offset_percent):
        """Defer fit_to_page execution until next draw.
        
        Args:
            padding_percent: Padding percentage to store.
            horizontal_offset_percent: Horizontal offset to store.
            vertical_offset_percent: Vertical offset to store.
            
        Returns:
            bool: False (deferred)
        """
        self._fit_to_page_pending = True
        self._fit_to_page_padding = padding_percent
        self._fit_to_page_horizontal_offset = horizontal_offset_percent
        self._fit_to_page_vertical_offset = vertical_offset_percent
        return False
    
    def _handle_empty_content(self):
        """Handle fit_to_page when no content exists.

        Returns:
            bool: False (no content).
        """
        self.zoom = 1.0  # delegates to viewport_controller via property
        self.pan_to(0.0, 0.0)
        return False

    def _finalize_view_state(self):
        """Persist view state and request redraw after a fit/zoom operation."""
        self.save_view_state_to_file()
        self._needs_redraw = True
    
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
    
    # Helper methods for initial state validation (PHASE 1 EXTRACTION)
    
    def _validate_canvas_dimensions(self):
        """Validate canvas dimensions are positive.
        
        Returns:
            list: Error messages (empty if valid)
        """
        errors = []
        if self.canvas_width <= 0:
            errors.append(f"Invalid canvas width: {self.canvas_width}")
        if self.canvas_height <= 0:
            errors.append(f"Invalid canvas height: {self.canvas_height}")
        return errors
    
    def _validate_zoom_state(self):
        """Validate zoom is at default 100% and within bounds.
        
        Returns:
            list: Error messages (empty if valid)
        """
        errors = []
        if abs(self.zoom - 1.0) > 0.01:
            errors.append(f"Initial zoom should be 100%, got {self.get_zoom_percentage()}")
        if self.zoom < self.MIN_ZOOM or self.zoom > self.MAX_ZOOM:
            errors.append(f"Zoom out of bounds: {self.zoom} (min: {self.MIN_ZOOM}, max: {self.MAX_ZOOM})")
        return errors
    
    def _validate_grid_and_filename(self):
        """Validate grid style and filename are valid.
        
        Returns:
            list: Error messages (empty if valid)
        """
        errors = []
        valid_styles = [self.GRID_STYLE_LINE, self.GRID_STYLE_DOT, self.GRID_STYLE_CROSS]
        if self.grid_style not in valid_styles:
            errors.append(f"Invalid grid style: {self.grid_style}")
        if not self.filename or self.filename.strip() == "":
            errors.append("Filename cannot be empty")
        return errors
    
    def validate_initial_state(self):
        """Validate the initial state of the document.
        
        Checks canvas dimensions, zoom, grid style, and filename.
        
        REFACTORED: Now delegates to extracted validation helpers.
        
        Returns:
            dict: {'valid': bool, 'errors': list of error messages}
        """
        errors = []
        errors.extend(self._validate_canvas_dimensions())
        errors.extend(self._validate_zoom_state())
        errors.extend(self._validate_grid_and_filename())
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    # Helper methods for arc validation (PHASE 1 EXTRACTION)
    
    @staticmethod
    def _validate_arc_endpoint(arc, endpoint_name, endpoint, arc_label):
        """Validate an arc endpoint (source or target).
        
        Args:
            arc: Arc object being validated
            endpoint_name: 'source' or 'target'
            endpoint: The endpoint object to validate
            arc_label: Human-readable arc label for error messages
            
        Returns:
            tuple: (is_valid, error_message or None)
        """
        if not hasattr(arc, endpoint_name) or endpoint is None:
            return False, f"{arc_label}: {endpoint_name} is None"
        
        if not hasattr(endpoint, 'x') or not hasattr(endpoint, 'y'):
            endpoint_type = type(endpoint).__name__
            return False, f"{arc_label}: {endpoint_name} ({endpoint_type}) has no x, y attributes"
        
        return True, None
    
    def validate_arcs(self):
        """Validate all arcs and detect corrupted references.
        
        Checks that all arcs have valid source and target references
        (Place or Transition objects with x, y attributes).
        
        REFACTORED: Now uses extracted helper for endpoint validation.
        
        Returns:
            dict: {'valid': bool, 'corrupted_arcs': list, 'errors': list}
        """
        corrupted = []
        errors = []
        
        for arc in self.arcs:
            arc_label = f"Arc {arc.id} ({arc.source_id} → {arc.target_id})"
            
            # Validate source endpoint
            source_valid, source_error = self._validate_arc_endpoint(
                arc, 'source', arc.source, arc_label
            )
            if not source_valid:
                errors.append(source_error)
                corrupted.append(arc)
            
            # Validate target endpoint
            target_valid, target_error = self._validate_arc_endpoint(
                arc, 'target', arc.target, arc_label
            )
            if not target_valid:
                errors.append(target_error)
                if arc not in corrupted:
                    corrupted.append(arc)
        
        return {
            'valid': len(corrupted) == 0,
            'corrupted_arcs': corrupted,
            'errors': errors
        }
    
    @staticmethod
    def _format_arc_label(arc):
        """Format arc label for debugging/logging.
        
        Args:
            arc: Arc object
            
        Returns:
            str: Formatted arc label (e.g., "Arc P1→T1 (P1 → T1)")
        """
        arc_label = f"Arc {arc.id}"
        if hasattr(arc, 'source_id'):
            arc_label += f" ({arc.source_id}"
        if hasattr(arc, 'target_id'):
            arc_label += f" → {arc.target_id})"
        else:
            arc_label += " → ?)"
        return arc_label
    
    def _remove_arc_from_list(self, arc):
        """Remove an arc from the arcs list.
        
        Args:
            arc: Arc to remove
            
        Returns:
            bool: True if arc was removed, False if not found
        """
        if arc in self.arcs:
            self.arcs.remove(arc)
            return True
        return False
    
    def remove_corrupted_arcs(self):
        """Remove corrupted arcs from the model.
        
        Identifies and removes any arcs with invalid source/target references.
        This is a safety measure to prevent crashes from corrupted model data.
        
        REFACTORED: Now uses extracted helper methods for arc formatting and removal.
        
        Returns:
            int: Number of corrupted arcs removed
        """
        validation = self.validate_arcs()
        
        if validation['valid']:
            return 0  # No corrupted arcs
        
        corrupted = validation['corrupted_arcs']
        removed_count = 0
        
        for arc in corrupted:
            try:
                arc_label = self._format_arc_label(arc)
                print(f"[ARC_CLEANUP] ⚠️ Removing corrupted arc: {arc_label}")
                
                if self._remove_arc_from_list(arc):
                    removed_count += 1
                    
            except Exception as e:
                print(f"[ARC_CLEANUP] ❌ Error removing arc: {e}")
        
        if removed_count > 0:
            print(f"[ARC_CLEANUP] ✅ Removed {removed_count} corrupted arc(s)")
            self.mark_dirty()
            self.mark_needs_redraw()
        
        return removed_count
    
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
        
        # Sync filepath with document model for settings persistence
        if hasattr(self, '_document_model') and self._document_model:
            self._document_model.filepath = filepath
        
        # Update viewport controller's model filepath for view state persistence
        if hasattr(self, 'viewport_controller'):
            self.viewport_controller.model_filepath = filepath
        
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
    
    # Helper methods for color reset operations (PHASE 1 EXTRACTION)
    
    @staticmethod
    def _should_preserve_transition_color(transition):
        """Check if transition has semantic colors that should be preserved.
        
        Args:
            transition: Transition object to check
            
        Returns:
            bool: True if transition color is semantic (source/sink)
        """
        return transition.is_source or transition.is_sink
    
    @staticmethod
    def _should_preserve_place_color(place):
        """Check if place has semantic colors that should be preserved.
        
        Args:
            place: Place object to check
            
        Returns:
            bool: True if place color is semantic (compartment/signal/regulatory)
        """
        from shypn.utils.color_schema_manager import ColorSchemaManager
        return ColorSchemaManager.is_semantic_place_color(place)
    
    @staticmethod
    def _should_preserve_arc_color(arc):
        """Check if arc has semantic colors that should be preserved.
        
        Args:
            arc: Arc object to check
            
        Returns:
            bool: True if arc color is semantic (boundary species, signal flow)
        """
        from shypn.netobjs.arc import Arc
        # Any non-default color is considered semantic
        return arc.color != Arc.DEFAULT_COLOR
    
    def _reset_transition_colors_to_default(self):
        """Reset transition colors to defaults (preserving semantic colors)."""
        from shypn.netobjs import Transition
        
        for transition in self.transitions:
            if self._should_preserve_transition_color(transition):
                continue
            transition.border_color = Transition.DEFAULT_BORDER_COLOR
            transition.fill_color = Transition.DEFAULT_COLOR
    
    def _reset_place_colors_to_default(self):
        """Reset place colors to defaults (preserving semantic colors)."""
        from shypn.netobjs import Place
        
        for place in self.places:
            if self._should_preserve_place_color(place):
                continue
            place.border_color = Place.DEFAULT_BORDER_COLOR
    
    def _reset_arc_colors_to_default(self):
        """Reset arc colors to defaults (preserving semantic colors)."""
        from shypn.netobjs.arc import Arc
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        for arc in self.arcs:
            if self._should_preserve_arc_color(arc):
                continue
            # Reset to type-specific default
            if isinstance(arc, SignalFlowArc):
                arc.color = SignalFlowArc.DEFAULT_COLOR
            else:
                arc.color = Arc.DEFAULT_COLOR
    
    def _reset_analysis_colors(self):
        """Reset all analysis-related colors to defaults before saving.
        
        When objects are selected in the Analyses panel, they get colored with
        plot colors for visualization. These colors are temporary and should NOT
        be saved to the file.
        
        REFACTORED: Now delegates to helper methods for better testability.
        
        Preserves semantic colors:
        - Source/sink transitions keep their cyan colors
        - Compartment places keep their violet borders
        - Boundary species arcs keep their cyan colors
        """
        # Reset colors using extracted helper methods
        self._reset_transition_colors_to_default()
        self._reset_place_colors_to_default()
        self._reset_arc_colors_to_default()
        
        # Trigger redraw to show the reset colors
        self.mark_needs_redraw()
    
    def _store_and_reset_transition_colors(self):
        """Store and reset transition colors (preserving semantic colors).
        
        Returns:
            list: Original colors (or None for preserved transitions)
        """
        from shypn.netobjs import Transition
        
        original_colors = []
        for transition in self.transitions:
            if self._should_preserve_transition_color(transition):
                original_colors.append(None)
                continue
            original_colors.append((transition.border_color, transition.fill_color))
            transition.border_color = Transition.DEFAULT_BORDER_COLOR
            transition.fill_color = Transition.DEFAULT_COLOR
        
        return original_colors
    
    def _store_and_reset_place_colors(self):
        """Store and reset place colors (preserving semantic colors).
        
        Returns:
            list: Original colors (or None for preserved places)
        """
        from shypn.netobjs import Place
        
        original_colors = []
        for place in self.places:
            if self._should_preserve_place_color(place):
                original_colors.append(None)
                continue
            original_colors.append(place.border_color)
            place.border_color = Place.DEFAULT_BORDER_COLOR
        
        return original_colors
    
    def _store_and_reset_arc_colors(self):
        """Store and reset arc colors (preserving semantic colors).
        
        Returns:
            list: Original colors (or None for preserved arcs)
        """
        from shypn.netobjs.arc import Arc
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        original_colors = []
        for arc in self.arcs:
            # Check if arc has semantic color
            if isinstance(arc, SignalFlowArc):
                if arc.color != SignalFlowArc.DEFAULT_COLOR:
                    original_colors.append(None)
                    continue
                original_colors.append(arc.color)
                arc.color = SignalFlowArc.DEFAULT_COLOR
            else:
                if arc.color != Arc.DEFAULT_COLOR:
                    original_colors.append(None)
                    continue
                original_colors.append(arc.color)
                arc.color = Arc.DEFAULT_COLOR
        
        return original_colors
    
    def _reset_analysis_colors_for_save(self):
        """Temporarily reset analysis colors for save, then restore them.
        
        Returns the original colors so they can be restored after serialization.
        This allows saving with default colors without modifying the live canvas.
        
        REFACTORED: Now delegates to helper methods for better testability.
        
        Returns:
            dict: Original colors for transitions, places, and arcs
        """
        # Store and reset colors using extracted helper methods
        original_colors = {
            'transitions': self._store_and_reset_transition_colors(),
            'places': self._store_and_reset_place_colors(),
            'arcs': self._store_and_reset_arc_colors()
        }
        
        return original_colors
    
    def _restore_analysis_colors(self, original_colors):
        """Restore colors after save.
        
        Args:
            original_colors: Dictionary returned by _reset_analysis_colors_for_save()
        """
        # Restore transition colors
        for i, transition in enumerate(self.transitions):
            if original_colors['transitions'][i] is not None:
                transition.border_color, transition.fill_color = original_colors['transitions'][i]
        
        # Restore place colors
        for i, place in enumerate(self.places):
            if original_colors['places'][i] is not None:
                place.border_color = original_colors['places'][i]
        
        # Restore arc colors
        for i, arc in enumerate(self.arcs):
            if original_colors['arcs'][i] is not None:
                arc.color = original_colors['arcs'][i]
    
    def _populate_document_objects(self, document):
        """Populate DocumentModel with Petri net objects.
        
        Args:
            document: DocumentModel to populate
        """
        document.places = list(self.places)
        document.transitions = list(self.transitions)
        document.arcs = list(self.arcs)
        
        # Copy modules if they exist
        if hasattr(self.document_controller, 'modules') and self.document_controller.modules:
            document.modules = dict(self.document_controller.modules)
    
    def _sync_id_counters(self, document):
        """Sync ID counters from DocumentController to DocumentModel.
        
        Args:
            document: DocumentModel to sync counters to
        """
        place_id, trans_id, arc_id, module_id = self.document_controller.id_manager.get_state()
        document.id_manager.set_state(place_id, trans_id, arc_id, module_id)
    
    def _sync_view_state(self, document):
        """Sync view state (zoom, pan, rotation) to DocumentModel.
        
        Args:
            document: DocumentModel to sync view state to
        """
        document.view_state = {
            "zoom": self.zoom,
            "pan_x": self.pan_x,
            "pan_y": self.pan_y,
            "transformations": self.transformation_manager.to_dict()
        }
    
    def to_document_model(self):
        """Convert canvas manager's Petri net objects to a DocumentModel.
        
        This creates a DocumentModel instance that can be saved/loaded by
        the persistency manager.
        
        REFACTORED: Now delegates to extracted helper methods for document setup.
        
        Returns:
            DocumentModel: Document model containing all Petri net objects
        """
        from shypn.data.canvas import DocumentModel
        
        # Reset analysis colors before serialization
        original_colors = self._reset_analysis_colors_for_save()
        
        # Create and populate document using extracted helpers
        document = DocumentModel()
        self._populate_document_objects(document)
        self._sync_id_counters(document)
        self._sync_view_state(document)
        
        # Restore analysis colors after serialization
        self._restore_analysis_colors(original_colors)
        
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
            
            # CRITICAL: Sync viewport controller state BEFORE clamping
            # The clamp_pan() delegates to viewport_controller.clamp_pan()
            # so viewport_controller must have the correct values first
            self.viewport_controller.pan_x = self.pan_x
            self.viewport_controller.pan_y = self.pan_y
            self.viewport_controller.zoom = self.zoom
            self.viewport_controller._initial_pan_set = True  # Prevent auto-centering
            
            # Clamp pan to infinite canvas bounds
            self.clamp_pan()
            
            # Sync back after clamping (clamp_pan modifies viewport_controller)
            self.pan_x = self.viewport_controller.pan_x
            self.pan_y = self.viewport_controller.pan_y
            
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
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.debug(f"Failed to save view state: {e}")
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
