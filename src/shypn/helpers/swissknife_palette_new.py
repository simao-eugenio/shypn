#!/usr/bin/env python3
"""SwissKnifePalette - Refactored Modular Architecture.

Main coordinator class that integrates all modules:
- SwissKnifePaletteUI: Widget construction
- SwissKnifePaletteAnimator: Animation state machine
- SwissKnifePaletteController: Signal coordination
- SubPaletteRegistry: Plugin management
- ParameterPanelManager: Universal parameter panel lifecycle (Phase 3)

This refactored version maintains 100% compatibility with the old API
while providing clean separation of concerns.

PHASE 3: Universal Parameter Panel Architecture
================================================
Parameter panels now slide UP above sub-palettes, maintaining constant
114px main palette height (50px sub-palette + 64px buttons).
"""

from gi.repository import Gtk, Gdk, GObject

from shypn.helpers.swissknife_palette_ui import SwissKnifePaletteUI
from shypn.helpers.swissknife_palette_animator import SwissKnifePaletteAnimator
from shypn.helpers.swissknife_palette_controller import SwissKnifePaletteController
from shypn.helpers.swissknife_palette_registry import SubPaletteRegistry
from shypn.helpers.parameter_panel_manager import ParameterPanelManager


class SwissKnifePalette(GObject.GObject):
    """Unified multi-mode palette for Petri net operations (Refactored).
    
    Provides mode-aware interface with animated sub-palettes.
    Supports both simple tool buttons and complex widget palettes.
    
    Signals:
        category-selected(str): Category button clicked
        tool-activated(str): Tool button clicked  
        sub-palette-shown(str): Sub-palette revealed (after animation)
        sub-palette-hidden(str): Sub-palette hidden (after animation)
        mode-change-requested(str): Mode change requested (edit/simulate)
        simulation-step-executed(float): Simulation step completed (forwarded)
        simulation-reset-executed(): Simulation reset (forwarded)
        simulation-settings-changed(): Simulation settings changed (forwarded)
    """
    
    __gsignals__ = {
        'category-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'tool-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-shown': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-hidden': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'mode-change-requested': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        # Forward simulation palette signals
        'simulation-step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'simulation-reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'simulation-settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        # Drag and drop signals
        'position-changed': (GObject.SignalFlags.RUN_FIRST, None, (float, float)),
        'float-toggled': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }
    
    def __init__(self, mode='edit', model=None, tool_registry=None):
        """Initialize SwissKnifePalette.
        
        Args:
            mode: 'edit' or 'simulate' mode
            model: PetriNetModel instance for widget palettes (required for simulation)
            tool_registry: Optional tool registry for custom tools. If None, uses default.
        """
        super().__init__()
        
        self.mode = mode
        self.model = model
        self.tool_registry = tool_registry or self._create_default_tool_registry()
        
        # Get configuration from tool registry
        self.categories = self.tool_registry.get_categories(mode)
        self.tools = self.tool_registry.get_all_tools()
        
        # Drag state for floating palette
        self.drag_active = False
        self.drag_pending = False  # Button pressed but not yet dragging
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.drag_threshold = 5  # Minimum pixels to move before drag starts
        self.ignore_next_release = False  # Flag to ignore release after double-click
        
        # Create modular components
        self.ui = SwissKnifePaletteUI(self.categories, self.tools)
        self.registry = SubPaletteRegistry(self.ui, self.categories, self.tools)
        
        # Build UI first
        self.ui.build()
        
        # Wrap main container in EventBox for drag functionality
        self._wrap_in_draggable_container()
        
        # Create all sub-palettes
        self.registry.create_all_sub_palettes(model)
        
        # Create layout settings loader (for parameter panel)
        self._create_layout_settings_loader()
        
        # Create animator with sub-palettes
        self.animator = SwissKnifePaletteAnimator(self.registry.get_all_sub_palettes())
        
        # PHASE 3: Create parameter panel manager
        self.parameter_manager = ParameterPanelManager(
            self.ui.main_container,
            self.ui.sub_palette_area
        )
        
        # Register parameter panels from widget palettes
        self._register_parameter_panels()
        
        # Create controller with UI, animator, and parameter manager
        self.controller = SwissKnifePaletteController(
            self.ui, 
            self.animator, 
            mode,
            self.parameter_manager  # Pass parameter manager for auto-hide
        )
        
        # Connect controller signals to forward them
        self._connect_controller_signals()
        
        # Connect tool signals
        self.controller.connect_tool_signals(self.tools)
        
        # Connect simulation signals if available
        self.registry.connect_simulation_signals(self)
        
        # Apply CSS
        self._apply_css()
    
    def _create_default_tool_registry(self):
        """Create default tool registry.
        
        Returns:
            ToolRegistry: Default tool registry with standard tools
        """
        from shypn.ui.swissknife_tool_registry import ToolRegistry
        return ToolRegistry()
    
    def _wrap_in_draggable_container(self):
        """Wrap main container in EventBox for drag and double-click interactions.
        
        NEW APPROACH: No separate controls - use intuitive gestures on palette itself
        - Single-click + drag on empty space → drag palette (when floating)
        - Double-click on empty space → toggle float/attach
        
        This eliminates the need for separate drag handle and button controls.
        """
        # Wrap main container in EventBox to capture mouse events
        self.drag_event_box = Gtk.EventBox()
        self.drag_event_box.add(self.ui.main_container)
        self.drag_event_box.set_above_child(False)
        
        # Enable events for drag and double-click
        self.drag_event_box.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        
        # Connect events
        self.drag_event_box.connect('button-press-event', self._on_button_press)
        self.drag_event_box.connect('button-release-event', self._on_button_release)
        self.drag_event_box.connect('motion-notify-event', self._on_drag_motion)
        
        # State for float/attach
        self.is_floating = False  # Default to attached (bottom-center)
        
        # Change cursor on hover when floating
        self.drag_event_box.connect('enter-notify-event', 
            lambda w, e: w.get_window().set_cursor(Gdk.Cursor.new_from_name(w.get_display(), 'grab')) if self.is_floating else None)
        self.drag_event_box.connect('leave-notify-event', 
            lambda w, e: w.get_window().set_cursor(None) if not self.drag_active else None)
        
        # Set EventBox as the draggable container
        self.draggable_container = self.drag_event_box
    
    def _on_button_press(self, widget, event):
        """Handle button press event - prepare for drag or detect double-click.
        
        IMPROVED: Uses press-and-hold + movement for drag initiation.
        Drag only starts when mouse moves beyond threshold while button is held.
        This prevents conflict with double-click and accidental drags.
        
        Args:
            widget: EventBox widget
            event: Button press event (event.type: BUTTON_PRESS or DOUBLE_BUTTON_PRESS)
        """
        if event.button == 1:  # Left click
            # Check for double-click FIRST (before processing as single click)
            if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
                # Double-click: toggle float/attach
                # Cancel any pending drag from the first click
                self.drag_pending = False
                self.drag_active = False
                
                # Toggle floating state
                self.is_floating = not self.is_floating
                self.emit('float-toggled', self.is_floating)
                
                # Set flag to ignore the upcoming BUTTON_RELEASE
                # (GTK sends BUTTON_RELEASE after DOUBLE_BUTTON_PRESS)
                self.ignore_next_release = True
                
                return True  # Event handled, stop propagation
            
            # Single button press: prepare for potential drag (only when floating)
            elif event.type == Gdk.EventType.BUTTON_PRESS:
                # Only set pending if we're floating AND not ignoring events
                if self.is_floating and not self.ignore_next_release:
                    # Set pending state - drag will start only if mouse moves
                    self.drag_pending = True
                    self.drag_active = False
                    self.drag_start_x = event.x_root
                    self.drag_start_y = event.y_root
                
                # Reset ignore flag for single clicks
                self.ignore_next_release = False
                
                return False  # Allow event to propagate to children (buttons still work)
        
        return False
    
    def _on_button_release(self, widget, event):
        """Handle button release event - end drag or cancel pending drag.
        
        Args:
            widget: EventBox widget
            event: Button release event
        """
        if event.button == 1:
            # Check if we should ignore this release (after double-click)
            if self.ignore_next_release:
                self.ignore_next_release = False
                self.drag_pending = False
                self.drag_active = False
                return True  # Consume the event
            
            # If we were dragging, end it
            if self.drag_active:
                self.drag_active = False
                self.drag_pending = False
                
                # Restore cursor
                if self.is_floating:
                    widget.get_window().set_cursor(Gdk.Cursor.new_from_name(widget.get_display(), 'grab'))
                else:
                    widget.get_window().set_cursor(None)
                return True
            
            # If drag was pending but never activated (quick click), just cancel
            elif self.drag_pending:
                self.drag_pending = False
                return False  # Let click propagate to children
        
        return False
    
    def _on_drag_motion(self, widget, event):
        """Handle drag motion event.
        
        IMPROVED: Drag activates only after mouse moves beyond threshold.
        This prevents accidental drags from quick clicks and makes the
        distinction between click and drag-intent clear.
        
        Behavior:
        - Button pressed but not moved → drag_pending (no visual change)
        - Button pressed + moved > threshold → drag_active (cursor changes, palette moves)
        - This makes drag distinct from double-click
        
        TODO: Canvas transformation awareness
        ─────────────────────────────────────
        Mouse coordinates (event.x_root, event.y_root) are in screen space,
        but when canvas has pan/zoom/rotation applied, the overlay positioning
        needs to compensate. Currently using raw screen deltas.
        
        Options:
        1. Keep palette in screen space (current) - palette doesn't move with canvas
        2. Transform to world space - palette would move/scale with canvas (not desired)
        
        Current approach (1) is correct, but may need adjustment when:
        - Canvas rotation is active (drag deltas need rotation transformation)
        - Multiple monitors with different DPI (rare edge case)
        
        Args:
            widget: EventBox widget
            event: Motion event with screen coordinates
        """
        # Check if button is pressed (pending or active drag)
        if self.drag_pending or self.drag_active:
            # Calculate delta from initial press
            dx_from_start = event.x_root - self.drag_start_x
            dy_from_start = event.y_root - self.drag_start_y
            distance = (dx_from_start**2 + dy_from_start**2)**0.5
            
            # If pending and movement exceeds threshold, activate drag
            if self.drag_pending and distance > self.drag_threshold:
                self.drag_active = True
                self.drag_pending = False
                
                # NOW change cursor to grabbing (user is clearly dragging)
                widget.get_window().set_cursor(Gdk.Cursor.new_from_name(widget.get_display(), 'grabbing'))
            
            # If drag is active, update position
            if self.drag_active:
                # Calculate delta from last position
                # (drag_start gets updated after each move for smooth incremental updates)
                dx = event.x_root - self.drag_start_x
                dy = event.y_root - self.drag_start_y
                
                # Update offsets
                self.drag_offset_x += dx
                self.drag_offset_y += dy
                
                # Update start position for next delta
                self.drag_start_x = event.x_root
                self.drag_start_y = event.y_root
                
                # Update widget position
                self._update_position()
                return True
        
        return False
    
    def _update_position(self):
        """Update palette position based on drag offsets.
        
        Emits position-changed signal with delta values for parent to handle.
        The parent (model_canvas_loader) will update the widget margins.
        
        TODO: Canvas transformation coordination
        ────────────────────────────────────────
        This method emits raw screen-space deltas. The handler in model_canvas_loader
        must be aware of:
        
        1. Overlay coordinate system: GtkOverlay uses widget-relative coordinates
        2. Canvas transformations: Zoom/pan/rotation affect canvas but not overlay
        3. Position bounds: Need to clamp to keep palette visible
        
        Current implementation: Screen-space deltas → margin updates
        This is correct for palettes that should stay in screen space (not move
        with canvas). If we ever want palettes to follow canvas transformations,
        this signal would need to include canvas_manager reference.
        
        Signal: position-changed(dx: float, dy: float)
        Handler: model_canvas_loader._on_swissknife_position_changed()
        """
        # Emit delta, not cumulative (so parent can add to current position)
        # Get the delta since last update
        dx = self.drag_offset_x
        dy = self.drag_offset_y
        
        # Reset offsets after emitting (we work with deltas)
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
        # Emit signal for parent to handle
        # TODO: Consider passing canvas_manager if transformation awareness needed
        self.emit('position-changed', dx, dy)
    
    def _create_layout_settings_loader(self):
        """Create layout settings loader for parameter panel.
        
        Creates an instance of LayoutSettingsLoader to provide parameter
        panel for layout algorithms.
        """
        try:
            from shypn.helpers.layout_settings_loader import LayoutSettingsLoader
            self.layout_settings_loader = LayoutSettingsLoader()
        except Exception as e:
            import traceback
            print(f'Warning: Failed to create layout settings loader: {e}')
            traceback.print_exc()
            self.layout_settings_loader = None
    
    def _register_parameter_panels(self):
        """Register parameter panels from widget palettes.
        
        PHASE 3: Extract parameter panel factories from widget palettes
        and register them with the parameter panel manager.
        """
        # Register simulate category parameter panel (settings)
        simulate_loader = self.registry.get_widget_palette_instance('simulate')
        if simulate_loader and hasattr(simulate_loader, 'create_settings_panel'):
            self.parameter_manager.register_parameter_panel(
                'simulate',
                simulate_loader.create_settings_panel
            )
        
        # Register layout category parameter panel (settings)
        if self.layout_settings_loader and hasattr(self.layout_settings_loader, 'create_settings_panel'):
            self.parameter_manager.register_parameter_panel(
                'layout',
                self.layout_settings_loader.create_settings_panel
            )
    
    def _connect_controller_signals(self):
        """Connect controller signals to forward them."""
        self.controller.connect('category-selected', self._forward_signal, 'category-selected')
        self.controller.connect('tool-activated', self._forward_signal, 'tool-activated')
        self.controller.connect('sub-palette-shown', self._forward_signal, 'sub-palette-shown')
        self.controller.connect('sub-palette-hidden', self._forward_signal, 'sub-palette-hidden')
        self.controller.connect('mode-change-requested', self._forward_signal, 'mode-change-requested')
    
    def _forward_signal(self, controller, *args):
        """Forward controller signal.
        
        Args:
            controller: Controller instance
            *args: Signal arguments (last arg is signal name)
        """
        signal_name = args[-1]
        signal_args = args[:-1]
        self.emit(signal_name, *signal_args)
    
    # Simulation signal handlers (for forwarding)
    
    def _on_simulation_step(self, sim_palette, time):
        """Forward simulation step signal.
        
        Args:
            sim_palette: Simulation palette instance
            time: Current simulation time
        """
        self.emit('simulation-step-executed', time)
    
    def _on_simulation_reset(self, sim_palette):
        """Forward simulation reset signal.
        
        Args:
            sim_palette: Simulation palette instance
        """
        self.emit('simulation-reset-executed')
    
    def _on_simulation_settings_changed(self, sim_palette):
        """Forward simulation settings changed signal.
        
        Args:
            sim_palette: Simulation palette instance
        """
        self.emit('simulation-settings-changed')
    
    def _on_settings_toggle_requested(self, sim_palette):
        """Handle settings toggle request from simulation palette.
        
        PHASE 3: Toggle parameter panel via ParameterPanelManager.
        
        Args:
            sim_palette: Simulation palette instance
        """
        self.parameter_manager.toggle_panel('simulate')
    
    def _apply_css(self):
        """Apply CSS styles to palette."""
        css = b"""
        /* SwissKnifePalette Styles */
        
        .swissknife-container {
            background-color: rgba(40, 50, 60, 0.95);
            border-radius: 8px;
            padding: 0px;
        }
        
        .category-buttons {
            background-color: transparent;
        }
        
        .category-button {
            min-width: 80px;
            min-height: 36px;
            padding: 8px 16px;
            font-weight: bold;
            background-image: none;
            background-color: rgba(60, 70, 80, 0.8);
            border: 1px solid rgba(100, 110, 120, 0.5);
            border-radius: 4px;
            color: #e0e0e0;
        }
        
        .category-button:hover {
            background-color: rgba(80, 90, 100, 0.9);
            border-color: rgba(120, 130, 140, 0.7);
        }
        
        .category-button.active {
            background-color: rgba(100, 110, 120, 1.0);
            border-color: rgba(140, 150, 160, 0.9);
            color: #ffffff;
        }
        
        .sub-palette {
            background-color: rgba(50, 60, 70, 0.9);
            border-radius: 6px;
            padding: 4px;
        }
        """
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    # Public API (maintains compatibility with old interface)
    
    def get_widget(self):
        """Get the main palette widget.
        
        Returns:
            Gtk.Box: Draggable container with palette (includes drag handle)
        """
        return self.draggable_container
    
    def set_mode(self, mode):
        """Set palette mode.
        
        Args:
            mode: 'edit' or 'simulate'
        """
        self.mode = mode
        self.controller.set_mode(mode)
    
    def hide_all_sub_palettes(self):
        """Hide all sub-palettes (for mode switching)."""
        self.controller.force_hide_all()
    
    def get_simulate_palette_loader(self):
        """Get SimulateToolsPaletteLoader instance.
        
        Returns:
            SimulateToolsPaletteLoader instance or None
        """
        return self.registry.get_widget_palette_instance('simulate')


__all__ = ['SwissKnifePalette']
