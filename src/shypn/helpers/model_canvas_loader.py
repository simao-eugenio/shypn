#!/usr/bin/env python3
"""Model Canvas Loader/Controller.

This module manages the multi-document Petri Net drawing canvas.
The canvas supports multiple tabs (documents), each with a scrollable
drawing area for creating and editing Petri Net models.

Architecture:
- GtkNotebook: Multi-document tab container
- GtkScrolledWindow: Scrollable viewport for each document
- GtkDrawingArea: Canvas for drawing Petri Net objects (Places, Transitions, Arcs)

Future extensions:
- Drawing primitives: Place (circle), Transition (rectangle), Arc (arrow)
- Edit operations: select, move, draw, undo, redo
- Model overlay support for floating palettes
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, Gdk, Gio
except Exception as e:
    print('ERROR: GTK3 not available in model_canvas loader:', e, file=sys.stderr)
    sys.exit(1)

# Import canvas manager from data layer
try:
    from shypn.data.model_canvas_manager import ModelCanvasManager
except ImportError as e:
    print(f'ERROR: Cannot import ModelCanvasManager: {e}', file=sys.stderr)
    sys.exit(1)

# Import zoom palette
try:
    from shypn.helpers.predefined_zoom import create_zoom_palette
except ImportError as e:
    print(f'ERROR: Cannot import zoom palette: {e}', file=sys.stderr)
    sys.exit(1)


class ModelCanvasLoader:
    """Loader and controller for the model canvas (multi-document Petri Net editor)."""
    
    def __init__(self, ui_path=None):
        """Initialize the model canvas loader.
        
        Args:
            ui_path: Optional path to model_canvas.ui. If None, uses default location.
        """
        if ui_path is None:
            # Default: ui/canvas/model_canvas.ui
            # This loader file is in: src/shypn/helpers/model_canvas_loader.py
            # UI file is in: ui/canvas/model_canvas.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'canvas', 'model_canvas.ui')
        
        self.ui_path = ui_path
        self.builder = None
        self.container = None
        self.notebook = None
        self.document_count = 0
        
        # Dictionary to map drawing areas to their canvas managers
        self.canvas_managers = {}  # {drawing_area: ModelCanvasManager}
        
        # Dictionary to map drawing areas to their zoom palettes
        self.zoom_palettes = {}  # {drawing_area: PredefinedZoom}
        
        # Parent window reference (for zoom window transient behavior)
        self.parent_window = None
        
                # Internal tracking
        self.canvas_managers = {}  # {drawing_area: ModelCanvasManager}
        self.document_count = 0
    
    def load(self):
        """Load the canvas UI and return the container.
        
        Returns:
            Gtk.Box: The model canvas container with notebook.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If container or notebook not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Model canvas UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract container and notebook
        self.container = self.builder.get_object('model_canvas_container')
        self.notebook = self.builder.get_object('canvas_notebook')
        
        if self.container is None:
            raise ValueError("Object 'model_canvas_container' not found in model_canvas.ui")
        if self.notebook is None:
            raise ValueError("Object 'canvas_notebook' not found in model_canvas.ui")
        
        self.document_count = self.notebook.get_n_pages()
        
        # Setup the initial document's canvas manager and callbacks
        if self.document_count > 0:
            page = self.notebook.get_nth_page(0)
            drawing_area = None
            overlay_box = None
            
            # Page is now a GtkOverlay, get the overlay box and scrolled window
            if isinstance(page, Gtk.Overlay):
                overlay = page
                # Get the scrolled window (first child)
                scrolled = overlay.get_child()
                if isinstance(scrolled, Gtk.ScrolledWindow):
                    drawing_area = scrolled.get_child()
                    # ScrolledWindow may wrap child in Viewport
                    if hasattr(drawing_area, 'get_child'):
                        drawing_area = drawing_area.get_child()
                    if drawing_area and isinstance(drawing_area, Gtk.DrawingArea):
                        # Get overlay box for adding zoom control
                        overlay_box = self.builder.get_object('canvas_overlay_box_1')
                        self._setup_canvas_manager(drawing_area, overlay_box)
            # Fallback for old structure without overlay
            elif isinstance(page, Gtk.ScrolledWindow):
                drawing_area = page.get_child()
                # ScrolledWindow may wrap child in Viewport
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
                if drawing_area and isinstance(drawing_area, Gtk.DrawingArea):
                    self._setup_canvas_manager(drawing_area)
            
            # Set tab label to empty (no filename display)
            if drawing_area:
                # Create simple empty label for tab
                tab_label = Gtk.Label(label="")
                self.notebook.set_tab_label(page, tab_label)
                tab_label.show()
        
        # Connect switch-page signal to update active tab styling
        self.notebook.connect('switch-page', self._on_notebook_page_changed)
        
        return self.container
    
    def _on_notebook_page_changed(self, notebook, page, page_num):
        """Handle notebook page switch.
        
        Args:
            notebook: GtkNotebook instance.
            page: The new page widget.
            page_num: The index of the new page.
        """
        # Simple page change handler - no special styling needed
        pass
    
    def add_document(self, title=None, filename=None):
        """Add a new document (tab) to the canvas.
        
        Args:
            title: Optional title for the new document tab (deprecated, use filename).
            filename: Base filename without extension (default: "default").
            
        Returns:
            tuple: (page_index, drawing_area) for the new document.
        """
        if self.notebook is None:
            raise RuntimeError("Canvas not loaded. Call load() first.")
        
        self.document_count += 1
        
        # Determine filename for the document
        if filename is None:
            if title:
                # Legacy support: use title as filename
                filename = title
            else:
                filename = f"default{self.document_count if self.document_count > 1 else ''}"
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Create drawing area
        drawing = Gtk.DrawingArea()
        drawing.set_hexpand(True)
        drawing.set_vexpand(True)
        # GTK3: Use set_size_request instead of set_content_width/height
        drawing.set_size_request(2000, 2000)
        
        scrolled.add(drawing)  # GTK3 uses add() instead of set_child()
        
        # Create simple empty tab label (no filename display)
        tab_label = Gtk.Label(label="")
        
        # Add page to notebook
        page_index = self.notebook.append_page(scrolled, tab_label)
        self.notebook.set_current_page(page_index)
        
        # Setup canvas manager for the new drawing area
        self._setup_canvas_manager(drawing)
        
        return page_index, drawing
    
    def _setup_canvas_manager(self, drawing_area, overlay_box=None):
        """Setup canvas manager and wire up callbacks for a drawing area.
        
        Args:
            drawing_area: GtkDrawingArea widget to setup.
            overlay_box: Optional GtkBox for overlay widgets (zoom control).
        """
        
        # Create canvas manager for this drawing area (no filename needed)
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
        self.canvas_managers[drawing_area] = manager
        
        # Initialize new document and validate
        validation = manager.create_new_document()
        # Silently ignore validation errors on initialization
        
        # GTK3: Connect 'draw' signal (receives widget and Cairo context)
        def on_draw_wrapper(widget, cr):
            # Get widget's allocated size for viewport dimensions
            allocation = widget.get_allocation()
            self._on_draw(widget, cr, allocation.width, allocation.height, manager)
            return False
        
        drawing_area.connect('draw', on_draw_wrapper)
        
        # Setup event controllers for mouse and scroll
        self._setup_event_controllers(drawing_area, manager)
        
        # Setup zoom palette if overlay box is provided
        if overlay_box:
            zoom_palette = create_zoom_palette()
            zoom_widget = zoom_palette.get_widget()
            if zoom_widget:
                overlay_box.pack_start(zoom_widget, False, False, 0)  # GTK3 uses pack_start
                zoom_palette.set_canvas_manager(manager, drawing_area, self.parent_window)
                self.zoom_palettes[drawing_area] = zoom_palette
        
    
    def _setup_event_controllers(self, drawing_area, manager):
        """Setup mouse and keyboard event controllers.
        
        Args:
            drawing_area: GtkDrawingArea widget.
            manager: ModelCanvasManager instance.
        """
        # GTK3: Enable events we need
        drawing_area.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.SCROLL_MASK |
            Gdk.EventMask.KEY_PRESS_MASK
        )
        
        # Make drawing area focusable for keyboard events
        drawing_area.set_can_focus(True)
        
        # Connect GTK3 signals instead of controllers
        drawing_area.connect('button-press-event', self._on_button_press, manager)
        drawing_area.connect('button-release-event', self._on_button_release, manager)
        drawing_area.connect('motion-notify-event', self._on_motion_notify, manager)
        drawing_area.connect('scroll-event', self._on_scroll_event, manager)
        drawing_area.connect('key-press-event', self._on_key_press_event, manager)
        
        # Store drag state per drawing area
        if not hasattr(self, '_drag_state'):
            self._drag_state = {}
        self._drag_state[drawing_area] = {
            'active': False,
            'button': 0,
            'start_x': 0,
            'start_y': 0,
            'is_panning': False
        }
        
        # Setup context menu
        self._setup_canvas_context_menu(drawing_area, manager)
    
    # ==================== GTK3 Event Handlers ====================
    
    def _on_button_press(self, widget, event, manager):
        """Handle button press events (GTK3)."""
        state = self._drag_state[widget]
        
        # All buttons can start drag (including right-click for pan)
        state['active'] = True
        state['button'] = event.button
        state['start_x'] = event.x
        state['start_y'] = event.y
        state['is_panning'] = False
        
        widget.grab_focus()
        
        # Return True to prevent default handling (especially for right-click)
        return True
    
    def _on_button_release(self, widget, event, manager):
        """Handle button release events (GTK3)."""
        state = self._drag_state[widget]
        
        # Right-click: show context menu ONLY if no panning occurred
        if event.button == 3 and not state['is_panning']:
            # Double-check: only show menu if it was a click (< 5px movement), not a drag
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < 5:
                self._show_canvas_context_menu(event.x, event.y, widget)
        
        # Reset all drag state
        state['active'] = False
        state['button'] = 0
        state['is_panning'] = False  # IMPORTANT: Reset panning flag
        
        # Return True to prevent default handling
        return True
    
    def _on_motion_notify(self, widget, event, manager):
        """Handle motion events (GTK3)."""
        state = self._drag_state[widget]
        
        # Update cursor position always (for zoom centering)
        manager.set_pointer_position(event.x, event.y)
        
        # Handle dragging only if button is pressed
        if state['active'] and state['button'] > 0:
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            
            # Start panning if movement detected (5px threshold)
            if not state['is_panning'] and (abs(dx) >= 5 or abs(dy) >= 5):
                state['is_panning'] = True
            
            # Pan with right button (3) or middle button (2) or Shift+left (1)
            is_shift_pressed = event.state & Gdk.ModifierType.SHIFT_MASK
            should_pan = state['button'] in [2, 3] or (state['button'] == 1 and is_shift_pressed)
            
            if should_pan and state['is_panning']:
                # Pan by the incremental delta
                manager.pan_relative(dx, dy)
                state['start_x'] = event.x
                state['start_y'] = event.y
                widget.queue_draw()
        
        # Return True to prevent default handling
        return True
    
    def _on_scroll_event(self, widget, event, manager):
        """Handle scroll events for zoom (GTK3)."""
        if event.direction == Gdk.ScrollDirection.UP:
            manager.zoom_at_point(1.1, event.x, event.y)
            widget.queue_draw()
        elif event.direction == Gdk.ScrollDirection.DOWN:
            manager.zoom_at_point(0.9, event.x, event.y)
            widget.queue_draw()
        return True
    
    def _on_key_press_event(self, widget, event, manager):
        """Handle key press events (GTK3)."""
        # Escape key to dismiss context menu
        if event.keyval == Gdk.KEY_Escape:
            if hasattr(self, '_canvas_context_menu') and self._canvas_context_menu:
                # GTK3 Menu: use popdown()
                if isinstance(self._canvas_context_menu, Gtk.Menu):
                    self._canvas_context_menu.popdown()
                    return True
        return False
    
    # ==================== Event Handlers (Legacy - will be cleaned up) ====================
    
    def _on_draw(self, drawing_area, cr, width, height, manager):
        """Draw callback for the canvas.
        
        Args:
            drawing_area: GtkDrawingArea being drawn.
            cr: Cairo context.
            width: Viewport width in pixels.
            height: Viewport height in pixels.
            manager: ModelCanvasManager instance.
        """
        # Update viewport size if changed
        if manager.viewport_width != width or manager.viewport_height != height:
            manager.set_viewport_size(width, height)
        
        # Clear background
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White background
        cr.paint()
        
        # Draw grid
        manager.draw_grid(cr)
        
        # TODO: Draw Petri Net objects here (Places, Transitions, Arcs)
        
        # Mark as clean after drawing
        manager.mark_clean()
    
    def _show_canvas_context_menu(self, x, y, drawing_area):
        """Show the canvas context menu at the given position.
        
        Args:
            x, y: Position to show menu (widget-relative coordinates)
            drawing_area: GtkDrawingArea widget
        """
        
        # Get the menu
        if hasattr(self, 'canvas_context_menus'):
            menu = self.canvas_context_menus.get(drawing_area)
            if menu:
                # GTK3: popup menu at pointer position
                # popup(parent_menu_shell, parent_menu_item, func, data, button, activate_time)
                menu.popup(None, None, None, None, 3, Gtk.get_current_event_time())
    
    # ==================== Public API ====================
    
    def get_canvas_manager(self, drawing_area=None):
        """Get the canvas manager for a drawing area.
        
        Args:
            drawing_area: GtkDrawingArea. If None, returns manager for current document.
            
        Returns:
            ModelCanvasManager: Canvas manager instance, or None if not found.
        """
        if drawing_area is None:
            drawing_area = self.get_current_document()
        
        return self.canvas_managers.get(drawing_area)
    
    def get_current_document(self):
        """Get the currently active document's drawing area.
        
        Returns:
            GtkDrawingArea: The active drawing area, or None if no pages.
        """
        if self.notebook is None:
            return None
        
        page_index = self.notebook.get_current_page()
        if page_index == -1:
            return None
        
        page = self.notebook.get_nth_page(page_index)
        if isinstance(page, Gtk.ScrolledWindow):
            child = page.get_child()
            # ScrolledWindow may wrap child in Viewport
            if hasattr(child, 'get_child'):
                child = child.get_child()
            if isinstance(child, Gtk.DrawingArea):
                return child
        return None
    
    def get_notebook(self):
        """Get the notebook widget for direct access.
        
        Returns:
            GtkNotebook: The canvas notebook widget.
        """
        return self.notebook
    
    def set_grid_style(self, style, drawing_area=None):
        """Set the grid style for a drawing area.
        
        Args:
            style: Grid style ('line', 'dot', or 'cross').
            drawing_area: GtkDrawingArea. If None, applies to current document.
        """
        manager = self.get_canvas_manager(drawing_area)
        if manager:
            manager.set_grid_style(style)
            if drawing_area is None:
                drawing_area = self.get_current_document()
            if drawing_area:
                drawing_area.queue_draw()
    
    def cycle_grid_style(self, drawing_area=None):
        """Cycle through grid styles (line -> dot -> cross -> line).
        
        Args:
            drawing_area: GtkDrawingArea. If None, applies to current document.
        """
        manager = self.get_canvas_manager(drawing_area)
        if manager:
            styles = [manager.GRID_STYLE_LINE, manager.GRID_STYLE_DOT, manager.GRID_STYLE_CROSS]
            current_index = styles.index(manager.grid_style)
            next_style = styles[(current_index + 1) % len(styles)]
            self.set_grid_style(next_style, drawing_area)
    
    # ==================== Context Menu ====================
    
    def _setup_canvas_context_menu(self, drawing_area, manager):
        """Setup context menu for canvas operations using Gtk.Menu.
        
        Args:
            drawing_area: GtkDrawingArea widget.
            manager: ModelCanvasManager instance.
        """
        # Create GTK3 Menu (more stable than Window approach)
        menu = Gtk.Menu()
        
        # Add menu items
        menu_items = [
            ("Reset Zoom (100%)", lambda: self._on_reset_zoom_clicked(menu, drawing_area, manager)),
            ("Zoom In", lambda: self._on_zoom_in_clicked(menu, drawing_area, manager)),
            ("Zoom Out", lambda: self._on_zoom_out_clicked(menu, drawing_area, manager)),
            ("Fit to Window", lambda: self._on_fit_to_window_clicked(menu, drawing_area, manager)),
            None,  # Separator
            ("Grid: Line Style", lambda: self._on_grid_line_clicked(menu, drawing_area, manager)),
            ("Grid: Dot Style", lambda: self._on_grid_dot_clicked(menu, drawing_area, manager)),
            ("Grid: Cross Style", lambda: self._on_grid_cross_clicked(menu, drawing_area, manager)),
            None,  # Separator
            ("Center View", lambda: self._on_center_view_clicked(menu, drawing_area, manager)),
            ("Clear Canvas", lambda: self._on_clear_canvas_clicked(menu, drawing_area, manager)),
        ]
        
        for item_data in menu_items:
            if item_data is None:
                # Add separator
                menu_item = Gtk.SeparatorMenuItem()
            else:
                label, callback = item_data
                menu_item = Gtk.MenuItem(label=label)
                menu_item.connect("activate", lambda w, cb=callback: cb())
            
            menu_item.show()
            menu.append(menu_item)
        
        # Store for later use
        self._canvas_context_menu = menu
        
        # Store menu per drawing area
        if not hasattr(self, 'canvas_context_menus'):
            self.canvas_context_menus = {}
        self.canvas_context_menus[drawing_area] = menu
        

    
    def _on_zoom_in_clicked(self, menu, drawing_area, manager):
        """Zoom in action."""
        manager.zoom_in(manager.viewport_width / 2, manager.viewport_height / 2)
        drawing_area.queue_draw()
    
    def _on_zoom_out_clicked(self, menu, drawing_area, manager):
        """Zoom out action."""
        manager.zoom_out(manager.viewport_width / 2, manager.viewport_height / 2)
        drawing_area.queue_draw()
    
    def _on_fit_to_window_clicked(self, menu, drawing_area, manager):
        """Fit canvas to window."""
        # Calculate zoom to fit canvas in viewport
        zoom_x = manager.viewport_width / manager.canvas_width
        zoom_y = manager.viewport_height / manager.canvas_height
        fit_zoom = min(zoom_x, zoom_y) * 0.95  # 95% to add margin
        manager.set_zoom(fit_zoom, manager.viewport_width / 2, manager.viewport_height / 2)
        # Center the canvas
        manager.pan_x = 0
        manager.pan_y = 0
        drawing_area.queue_draw()
    
    def _on_grid_line_clicked(self, menu, drawing_area, manager):
        """Set grid to line style."""
        manager.set_grid_style('line')
        drawing_area.queue_draw()
    
    def _on_grid_dot_clicked(self, menu, drawing_area, manager):
        """Set grid to dot style."""
        manager.set_grid_style('dot')
        drawing_area.queue_draw()
    
    def _on_grid_cross_clicked(self, menu, drawing_area, manager):
        """Set grid to cross style."""
        manager.set_grid_style('cross')
        drawing_area.queue_draw()
    
    def _on_clear_canvas_clicked(self, menu, drawing_area, manager):
        """Clear the canvas."""
        # TODO: Implement canvas clearing when we have objects
        drawing_area.queue_draw()
    
    def _on_reset_zoom_clicked(self, menu, drawing_area, manager):
        """Reset zoom to 100%."""
        manager.set_zoom(1.0, manager.viewport_width / 2, manager.viewport_height / 2)
        drawing_area.queue_draw()
    
    def _on_center_view_clicked(self, menu, drawing_area, manager):
        """Center the view."""
        manager.pan_x = 0
        manager.pan_y = 0
        drawing_area.queue_draw()


def create_model_canvas(ui_path=None):
    """Convenience function to create and load the model canvas loader.
    
    Args:
        ui_path: Optional path to model_canvas.ui.
        
    Returns:
        ModelCanvasLoader: The loaded model canvas loader instance.
        
    Example:
        loader = create_model_canvas()
        container = loader.load()
        # Add to main window workspace
    """
    loader = ModelCanvasLoader(ui_path)
    loader.load()
    return loader
