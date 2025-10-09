"""Canvas Overlay Manager - Concrete implementation for managing canvas overlays.

This module implements the overlay management for Petri net canvas editing.
It creates and manages all palettes and overlay widgets, keeping the main
ModelCanvasLoader focused on canvas lifecycle management.

Design Principles:
- Composition over inheritance: Uses palette loaders rather than inheriting from them
- Single Responsibility: Only manages overlays, not core canvas logic
- Separation of Concerns: Palettes, tools, and modes managed independently
"""
import sys
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print('ERROR: GTK3 not available in canvas_overlay_manager:', e, file=sys.stderr)
    sys.exit(1)

from shypn.canvas.base_overlay_manager import BaseOverlayManager

# Import palette loaders
try:
    from shypn.helpers.predefined_zoom import create_zoom_palette
    from shypn.helpers.edit_palette_loader import create_edit_palette
    from shypn.edit.tools_palette_loader import create_tools_palette
    from shypn.edit.operations_palette_loader import create_operations_palette
    from shypn.helpers.simulate_palette_loader import create_simulate_palette
    from shypn.helpers.simulate_tools_palette_loader import create_simulate_tools_palette
    from ui.palettes.mode.mode_palette_loader import ModePaletteLoader
except ImportError as e:
    print(f'ERROR: Cannot import palette loaders: {e}', file=sys.stderr)
    sys.exit(1)

# Import editing operations classes
try:
    from shypn.edit import (
        EditOperations,
        LassoSelector
    )
except ImportError as e:
    print(f'ERROR: Cannot import editing operations: {e}', file=sys.stderr)
    sys.exit(1)


class CanvasOverlayManager(BaseOverlayManager):
    """Concrete overlay manager for Petri net canvas.
    
    This class manages all overlay widgets for a single canvas:
    - Zoom palette (top-left)
    - Edit palette and tools (left side)
    - Editing operations palette (reveals with [E] button)
    - Simulate palette and tools (left side)
    - Mode palette (switches between edit/simulate)
    
    The manager handles palette visibility based on the current mode
    and coordinates interactions between palettes.
    """
    
    def __init__(self, overlay_widget, overlay_box, drawing_area, canvas_manager):
        """Initialize the canvas overlay manager.
        
        Args:
            overlay_widget: GtkOverlay widget for adding overlay children
            overlay_box: Optional GtkBox for positioning overlays (zoom palette)
            drawing_area: GtkDrawingArea widget
            canvas_manager: ModelCanvasManager instance
        """
        super().__init__(overlay_widget, overlay_box, drawing_area, canvas_manager)
        
        # Palette instances
        self.zoom_palette = None
        self.edit_palette = None
        self.tools_palette = None  # Edit tools palette [P][T][A]
        self.operations_palette = None  # Operations palette [S][L][U][R]
        self.simulate_palette = None
        self.simulate_tools_palette = None
        self.mode_palette = None
        
        # Parent window reference (for floating palettes)
        self.parent_window = None
        
        # Callback handlers
        self.on_tool_changed = None
        self.on_simulation_step = None
        self.on_simulation_reset = None
    
    def setup_overlays(self, parent_window=None):
        """Create and attach all overlay widgets to the canvas.
        
        This method creates all palettes and adds them to the overlay widget.
        It also connects signals and sets up initial visibility.
        
        Args:
            parent_window: Optional parent window for floating palettes
        """
        self.parent_window = parent_window
        
        # Setup zoom palette in overlay_box (top-left corner)
        if self.overlay_box:
            self._setup_zoom_palette()
        
        # Setup all other palettes as overlays
        if self.overlay_widget:
            # NOTE: Edit palettes now handled by SwissKnifePalette in model_canvas_loader
            # Old edit palette ([E] button) no longer needed - replaced by SwissKnifePalette
            # self._setup_edit_palettes()          # OLD - Create tools and operations palettes
            # self._setup_edit_palette()            # OLD - Create [E] button - REPLACED by SwissKnifePalette
            self._setup_simulate_palettes()
            self._setup_mode_palette()
    
    def _setup_zoom_palette(self):
        """Create and add zoom palette to overlay box."""
        self.zoom_palette = create_zoom_palette()
        zoom_widget = self.zoom_palette.get_widget()
        
        if zoom_widget:
            self.overlay_box.pack_start(zoom_widget, False, False, 0)
            self.zoom_palette.set_canvas_manager(
                self.canvas_manager,
                self.drawing_area,
                self.parent_window
            )
            self.register_palette('zoom', self.zoom_palette)
    
    def _setup_edit_palettes(self):
        """Create and add edit tools and operations palettes."""
        # Create EditOperations instance (shared by both palettes)
        edit_operations = EditOperations(self.canvas_manager)
        
        # Create tools palette [P][T][A]
        self.tools_palette = create_tools_palette()
        self.tools_palette.set_edit_operations(edit_operations)
        
        # Add tools revealer to overlay
        tools_revealer = self.tools_palette.revealer
        if tools_revealer:
            self.overlay_widget.add_overlay(tools_revealer)
            self.register_palette('tools', self.tools_palette)
        
        # Create operations palette [S][L][U][R]
        self.operations_palette = create_operations_palette()
        self.operations_palette.set_edit_operations(edit_operations)
        
        # Add operations revealer to overlay
        operations_revealer = self.operations_palette.revealer
        if operations_revealer:
            self.overlay_widget.add_overlay(operations_revealer)
            self.register_palette('operations', self.operations_palette)
    
    def _setup_edit_palette(self):
        """Create and add edit palette ([E] toggle button).
        
        The [E] button will be wired to NEW OOP palettes (ToolsPalette, OperationsPalette)
        by ModelCanvasLoader after palette_manager is created.
        """
        # Create edit palette
        self.edit_palette = create_edit_palette()
        edit_widget = self.edit_palette.get_widget()
        
        # NOTE: OLD palette wiring removed. NEW OOP palettes will be wired by
        # ModelCanvasLoader.connect_edit_button_signal()
        
        # Add to overlay
        if edit_widget:
            self.overlay_widget.add_overlay(edit_widget)
            self.register_palette('edit', self.edit_palette)
            # [E] button starts VISIBLE (edit mode is default) but palettes start hidden
    
    def _setup_simulate_palettes(self):
        """Create and add simulation mode palettes (simulate_tools only).
        
        NOTE: Old [S] button removed - replaced by SwissKnifePalette's Simulate category.
        Only the simulate_tools_palette (simulation controls) is kept, as it's used
        as a widget palette inside SwissKnifePalette.
        """
        # Create simulate tools palette - this will be embedded in SwissKnifePalette
        self.simulate_tools_palette = create_simulate_tools_palette(model=self.canvas_manager)
        simulate_tools_widget = self.simulate_tools_palette.get_widget()
        
        # Connect simulation signals (will be wired by ModelCanvasLoader)
        # self.simulate_tools_palette.connect('step-executed', callback, drawing_area)
        # self.simulate_tools_palette.connect('reset-executed', callback)
        
        # OLD [S] button removed - now part of SwissKnifePalette
        # self.simulate_palette = create_simulate_palette()
        # simulate_widget = self.simulate_palette.get_widget()
        self.simulate_palette = None  # Set to None to indicate it's not used
        
        # Add simulate tools to overlay (used by SwissKnifePalette as widget palette)
        if simulate_tools_widget:
            self.overlay_widget.add_overlay(simulate_tools_widget)
            self.register_palette('simulate_tools', self.simulate_tools_palette)
            # Don't hide the revealer widget - it controls visibility via reveal-child property
            # simulate_tools_widget.hide()  # REMOVED: This prevents revealer from working
            # Instead, ensure revealer starts with reveal-child=False (set in UI file)
            self.simulate_tools_palette.hide()  # Use palette's hide() method which sets reveal-child=False
    
    def _setup_mode_palette(self):
        """Create and add mode palette (edit/simulate mode switcher)."""
        # Create palette loader instance
        self.mode_palette = ModePaletteLoader()
        
        # Load UI file and apply styling (like zoom palette)
        self.mode_palette.load()
        
        # Get the styled container widget
        mode_widget = self.mode_palette.get_widget()
        
        if mode_widget:
            self.overlay_widget.add_overlay(mode_widget)
            self.register_palette('mode', self.mode_palette)
            
            # Connect mode changed signal (will be wired by ModelCanvasLoader)
            # self.mode_palette.connect('mode-changed', callback, ...)
            
            # Set initial visibility to 'edit' mode (hides simulate palettes)
            # NEW OOP edit palettes start hidden and show via mode-changed signal
            self.update_palette_visibility('edit')
    
    def cleanup_overlays(self):
        """Remove and cleanup all overlay widgets.
        
        This method is called when closing a canvas tab to properly
        cleanup resources and remove references.
        """
        # Clear all palette references
        self.zoom_palette = None
        self.edit_palette = None
        self.edit_tools_palette = None
        self.editing_operations_palette = None
        self.editing_operations_palette_loader = None
        self.simulate_palette = None
        self.simulate_tools_palette = None
        self.mode_palette = None
        
        # Clear palette registry
        self._palettes.clear()
    
    def update_palette_visibility(self, mode):
        """Update which palettes are visible based on the current mode.
        
        NOTE: This method now only handles simulate palettes visibility.
        Edit palettes (tools/operations) are handled by the NEW OOP PaletteManager
        system via mode-changed signal in ModelCanvasLoader.
        
        Args:
            mode: Current mode string ('edit' or 'simulate')
        """
        if mode == 'edit':
            # Hide simulate palettes when in edit mode
            if self.simulate_palette:
                widget = self.simulate_palette.get_widget()
                if widget:
                    widget.hide()
            
            if self.simulate_tools_palette:
                widget = self.simulate_tools_palette.get_widget()
                if widget:
                    widget.hide()
        
        elif mode == 'simulate':
            # Show simulate palettes when in simulation mode
            if self.simulate_palette:
                widget = self.simulate_palette.get_widget()
                if widget:
                    widget.show()
            
            if self.simulate_tools_palette:
                widget = self.simulate_tools_palette.get_widget()
                if widget:
                    widget.show()
    
    def get_palette(self, palette_name):
        """Get a specific palette by name.
        
        Args:
            palette_name: Name of the palette to retrieve
            
        Returns:
            The palette instance, or None if not found
        """
        return self._palettes.get(palette_name)
    
    def connect_tool_changed_signal(self, callback, manager, drawing_area):
        """Connect the tool-changed signals from both palettes.
        
        Args:
            callback: Callback function to handle tool changes
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        if self.tools_palette:
            self.tools_palette.connect('tool-changed', callback, manager, drawing_area)
        if self.operations_palette:
            self.operations_palette.connect('tool-changed', callback, manager, drawing_area)
    
    def connect_simulation_signals(self, step_callback, reset_callback, drawing_area):
        """Connect simulation signals from simulate_tools_palette.
        
        Args:
            step_callback: Callback for step-executed signal
            reset_callback: Callback for reset-executed signal
            drawing_area: GtkDrawingArea widget
        """
        if self.simulate_tools_palette:
            self.simulate_tools_palette.connect('step-executed', step_callback, drawing_area)
            self.simulate_tools_palette.connect('reset-executed', reset_callback)
    
    def connect_mode_changed_signal(self, callback, drawing_area):
        """Connect the mode-changed signal from mode_palette.
        
        Args:
            callback: Callback function to handle mode changes
            drawing_area: GtkDrawingArea widget
        """
        if self.mode_palette:
            self.mode_palette.connect('mode-changed', callback, drawing_area, 
                                     self.edit_palette, self.tools_palette,
                                     self.simulate_palette, self.simulate_tools_palette)
    
    def connect_edit_palettes_toggle_signal(self, callback, drawing_area):
        """Connect the edit-palettes-toggled signal from mode_palette.
        
        Args:
            callback: Callback function to handle edit palettes toggle
            drawing_area: GtkDrawingArea widget
        """
        if self.mode_palette:
            self.mode_palette.connect('edit-palettes-toggled', callback, drawing_area)
    
    def connect_edit_button_signal(self, callback, drawing_area):
        """Connect the tools-toggled signal from edit_palette [E] button.
        
        Args:
            callback: Callback function to handle [E] button toggle
            drawing_area: GtkDrawingArea widget
        """
        if self.edit_palette:
            self.edit_palette.connect('tools-toggled', callback, drawing_area)
