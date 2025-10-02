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
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk
except Exception as e:
    print('ERROR: GTK4 not available in model_canvas loader:', e, file=sys.stderr)
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
        
        # Track pan state for incremental drag updates
        self.pan_last_offset_x = {}  # {drawing_area: last_offset_x}
        self.pan_last_offset_y = {}  # {drawing_area: last_offset_y}
        self.is_panning = {}  # {drawing_area: is_panning_bool}
        
        # Track document filenames for tab labels
        self.document_filenames = {}  # {drawing_area: filename_without_extension}
    
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
            
            # Update initial tab label to editable format [default.shy]
            if drawing_area:
                tab_label = self._create_editable_tab_label("default", drawing_area)
                self.notebook.set_tab_label(page, tab_label)
                self.document_filenames[drawing_area] = "default"
                # Mark initial tab as active
                tab_label.add_css_class("active-tab")
        
        # Connect switch-page signal to update active tab styling
        self.notebook.connect('switch-page', self._on_notebook_page_changed)
        
        print(f"✓ Model canvas loaded from: {os.path.basename(self.ui_path)}")
        print(f"  └─ {self.document_count} document(s) initialized")
        return self.container
    
    def _create_editable_tab_label(self, filename="default", drawing_area=None):
        """Create an editable tab label with format filename.shy.
        
        Args:
            filename: Base filename without extension (default: "default").
            drawing_area: Associated drawing area for tracking.
            
        Returns:
            GtkBox: Tab label widget with editable filename.
        """
        # Apply CSS for seamless tab entry (only once)
        if not hasattr(self, '_tab_css_applied'):
            css_provider = Gtk.CssProvider()
            css = """
            .tab-container {
                padding: 4px 8px;
                background: transparent;
            }
            
            .tab-container:hover {
                background: alpha(currentColor, 0.05);
            }
            
            .tab-container.active-tab {
                background: alpha(currentColor, 0.12);
            }
            
            .tab-filename-entry {
                background: rgba(255, 255, 255, 0.9);
                border: none;
                box-shadow: none;
                padding: 2px 0px 2px 6px;
                margin: 0;
                min-height: 0;
                font-size: 13px;
                min-width: 60px;
                border-radius: 3px 0 0 3px;
            }
            
            .tab-filename-entry.final-name {
                background: transparent;
            }
            
            .tab-filename-entry text {
                text-align: right;
            }
            
            .tab-filename-entry:focus {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 3px 0 0 3px;
            }
            
            .tab-filename-entry selection {
                background-color: rgba(74, 144, 226, 0.3);
                color: inherit;
            }
            
            .tab-extension-label {
                font-size: 13px;
                color: alpha(currentColor, 0.6);
                padding-left: 0;
                padding-right: 4px;
                margin-left: 0;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 0 3px 3px 0;
                padding: 2px 4px 2px 0px;
            }
            """
            css_provider.load_from_string(css)
            Gdk.Display.get_default()
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self._tab_css_applied = True
        
        # Create horizontal box for tab label with border
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        tab_box.add_css_class("tab-container")
        
        # Editable filename entry (without extension)
        filename_entry = Gtk.Entry()
        filename_entry.set_text(filename)
        filename_entry.set_width_chars(len(filename) + 2)
        filename_entry.set_max_width_chars(40)
        filename_entry.set_has_frame(False)
        filename_entry.set_alignment(1.0)  # Right-align text (1.0 = right, 0.0 = left)
        filename_entry.add_css_class("tab-filename-entry")
        
        # Add white background class if it's a default name
        if filename.startswith('default'):
            # Keep white background for default names
            pass
        else:
            # Use transparent background for final/custom names
            filename_entry.add_css_class("final-name")
        
        # Add focus controller to select all text when focused
        focus_controller = Gtk.EventControllerFocus.new()
        
        def on_entry_focus_enter(controller):
            # Select all text in the entry
            filename_entry.select_region(0, -1)
        
        focus_controller.connect('enter', on_entry_focus_enter)
        filename_entry.add_controller(focus_controller)
        
        # Connect signal to update filename when changed
        if drawing_area:
            filename_entry.connect('changed', self._on_filename_changed, drawing_area)
        
        tab_box.append(filename_entry)
        
        # Extension label (.shy - visible but outside entry)
        extension_label = Gtk.Label(label=".shy")
        extension_label.set_selectable(False)
        extension_label.add_css_class("tab-extension-label")
        tab_box.append(extension_label)
        
        # Store filename entry as a Python attribute
        tab_box.filename_entry = filename_entry
        
        return tab_box
    
    def _on_filename_changed(self, entry, drawing_area):
        """Handle filename entry changes.
        
        Args:
            entry: GtkEntry widget for filename (without extension).
            drawing_area: Associated drawing area.
        """
        new_filename = entry.get_text()
        
        # Remove any .shy extension if user typed it
        if new_filename.endswith('.shy'):
            new_filename = new_filename[:-4]
            entry.set_text(new_filename)
        
        # Store updated filename (without extension)
        self.document_filenames[drawing_area] = new_filename
        
        # Update entry width to fit content
        entry.set_width_chars(max(len(new_filename) + 2, 8))
        
        # Update CSS class based on whether it's still a default name
        if new_filename.startswith('default'):
            # Keep white background for default names
            entry.remove_css_class("final-name")
        else:
            # Switch to transparent background for custom names
            if not entry.has_css_class("final-name"):
                entry.add_css_class("final-name")
        
        # Mark document as modified if canvas manager exists
        if drawing_area in self.canvas_managers:
            manager = self.canvas_managers[drawing_area]
            if hasattr(manager, 'mark_modified'):
                manager.mark_modified()
    
    def _on_notebook_page_changed(self, notebook, page, page_num):
        """Handle notebook page switch to update active tab styling.
        
        Args:
            notebook: GtkNotebook instance.
            page: The new page widget.
            page_num: The index of the new page.
        """
        # Remove active-tab class from all tabs
        for i in range(notebook.get_n_pages()):
            tab_widget = notebook.get_tab_label(notebook.get_nth_page(i))
            if tab_widget and hasattr(tab_widget, 'remove_css_class'):
                tab_widget.remove_css_class("active-tab")
        
        # Add active-tab class to the current tab
        current_tab = notebook.get_tab_label(page)
        if current_tab and hasattr(current_tab, 'add_css_class'):
            current_tab.add_css_class("active-tab")
    
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
        drawing.set_content_width(2000)
        drawing.set_content_height(2000)
        
        scrolled.set_child(drawing)
        
        # Create editable tab label [filename.shy]
        tab_label = self._create_editable_tab_label(filename, drawing)
        
        # Store filename
        self.document_filenames[drawing] = filename
        
        # Add page to notebook
        page_index = self.notebook.append_page(scrolled, tab_label)
        self.notebook.set_current_page(page_index)
        
        # Setup canvas manager for the new drawing area
        self._setup_canvas_manager(drawing)
        
        print(f"✓ Added document: [{filename}.shy] (page {page_index})")
        return page_index, drawing
    
    def _setup_canvas_manager(self, drawing_area, overlay_box=None):
        """Setup canvas manager and wire up callbacks for a drawing area.
        
        Args:
            drawing_area: GtkDrawingArea widget to setup.
            overlay_box: Optional GtkBox for overlay widgets (zoom control).
        """
        # Get filename for this drawing area
        filename = self.document_filenames.get(drawing_area, "default")
        
        # Create canvas manager for this drawing area
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000, filename=filename)
        self.canvas_managers[drawing_area] = manager
        
        # Initialize new document and validate
        validation = manager.create_new_document(filename)
        if not validation['valid']:
            print(f"  ⚠ Document validation warnings:")
            for error in validation['errors']:
                print(f"    - {error}")
        
        # Set draw function
        drawing_area.set_draw_func(self._on_draw, manager)
        
        # Setup event controllers for mouse and scroll
        self._setup_event_controllers(drawing_area, manager)
        
        # Setup zoom palette if overlay box is provided
        if overlay_box:
            zoom_palette = create_zoom_palette()
            zoom_widget = zoom_palette.get_widget()
            if zoom_widget:
                overlay_box.append(zoom_widget)
                zoom_palette.set_canvas_manager(manager, drawing_area, self.parent_window)
                self.zoom_palettes[drawing_area] = zoom_palette
                print(f"  ✓ Zoom palette attached to canvas")
        
        print(f"  ✓ Canvas manager attached to drawing area")
    
    def _setup_event_controllers(self, drawing_area, manager):
        """Setup mouse and keyboard event controllers.
        
        Args:
            drawing_area: GtkDrawingArea widget.
            manager: ModelCanvasManager instance.
        """
        # Click controller to hide revealer when clicking on canvas
        click_controller = Gtk.GestureClick.new()
        click_controller.connect('pressed', self._on_canvas_clicked, drawing_area)
        drawing_area.add_controller(click_controller)
        
        # Scroll controller for zoom (mouse wheel)
        scroll_controller = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
        )
        scroll_controller.connect('scroll', self._on_scroll, manager, drawing_area)
        drawing_area.add_controller(scroll_controller)
        
        # Motion controller for pointer tracking and pan
        motion_controller = Gtk.EventControllerMotion.new()
        motion_controller.connect('motion', self._on_motion, manager, drawing_area)
        drawing_area.add_controller(motion_controller)
        
        # Drag gesture for pan (middle button or primary button with ctrl)
        drag_gesture = Gtk.GestureDrag.new()
        drag_gesture.set_button(2)  # Middle mouse button
        drag_gesture.connect('drag-begin', self._on_drag_begin, manager, drawing_area)
        drag_gesture.connect('drag-update', self._on_drag_update, manager, drawing_area)
        drag_gesture.connect('drag-end', self._on_drag_end, manager, drawing_area)
        drawing_area.add_controller(drag_gesture)
        
        # Pan with right mouse button
        drag_gesture_right = Gtk.GestureDrag.new()
        drag_gesture_right.set_button(3)  # Right mouse button
        drag_gesture_right.connect('drag-begin', self._on_drag_begin, manager, drawing_area)
        drag_gesture_right.connect('drag-update', self._on_drag_update, manager, drawing_area)
        drag_gesture_right.connect('drag-end', self._on_drag_end, manager, drawing_area)
        drawing_area.add_controller(drag_gesture_right)
        
        # Also support ctrl+left-drag for pan
        drag_gesture_ctrl = Gtk.GestureDrag.new()
        drag_gesture_ctrl.set_button(1)  # Primary button
        drag_gesture_ctrl.connect('drag-begin', self._on_drag_begin_ctrl, manager, drawing_area)
        drag_gesture_ctrl.connect('drag-update', self._on_drag_update, manager, drawing_area)
        drag_gesture_ctrl.connect('drag-end', self._on_drag_end, manager, drawing_area)
        drawing_area.add_controller(drag_gesture_ctrl)
    
    # ==================== Event Handlers ====================
    
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
    
    def _on_canvas_clicked(self, gesture, n_press, x, y, drawing_area):
        """Handle click events on canvas - hide zoom revealer.
        
        Args:
            gesture: GestureClick controller.
            n_press: Number of presses (1=single, 2=double, etc).
            x: X coordinate of click.
            y: Y coordinate of click.
            drawing_area: GtkDrawingArea widget.
        """
        # Hide zoom revealer when clicking on canvas
        if drawing_area in self.zoom_palettes:
            zoom_palette = self.zoom_palettes[drawing_area]
            if zoom_palette.zoom_revealer:
                zoom_palette.zoom_revealer.set_reveal_child(False)
    
    def _on_scroll(self, controller, dx, dy, manager, drawing_area):
        """Handle scroll events for zooming.
        
        Args:
            controller: EventControllerScroll.
            dx: Horizontal scroll delta (unused).
            dy: Vertical scroll delta (negative = scroll up = zoom in).
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        # Get pointer position for centered zoom
        pointer_x = manager.pointer_x
        pointer_y = manager.pointer_y
        
        # Scroll up (dy < 0) = zoom in, scroll down (dy > 0) = zoom out
        if dy < 0:
            manager.zoom_in(pointer_x, pointer_y)
        else:
            manager.zoom_out(pointer_x, pointer_y)
        
        # Update zoom palette display if available
        if drawing_area in self.zoom_palettes:
            self.zoom_palettes[drawing_area].update_zoom_display()
        
        # Request redraw
        drawing_area.queue_draw()
        
        return True  # Event handled
    
    def _on_motion(self, controller, x, y, manager, drawing_area):
        """Handle motion events for pointer tracking.
        
        Args:
            controller: EventControllerMotion.
            x: Pointer X coordinate.
            y: Pointer Y coordinate.
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        # Update pointer position in manager
        manager.set_pointer_position(x, y)
    
    def _on_drag_begin(self, gesture, start_x, start_y, manager, drawing_area):
        """Handle drag begin for panning (middle button or right button).
        
        Args:
            gesture: GestureDrag.
            start_x: Starting X coordinate.
            start_y: Starting Y coordinate.
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        self.is_panning[drawing_area] = True
        self.pan_last_offset_x[drawing_area] = 0.0
        self.pan_last_offset_y[drawing_area] = 0.0
    
    def _on_drag_begin_ctrl(self, gesture, start_x, start_y, manager, drawing_area):
        """Handle drag begin for panning (ctrl+left button).
        
        Args:
            gesture: GestureDrag.
            start_x: Starting X coordinate.
            start_y: Starting Y coordinate.
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        # Only pan if ctrl is pressed
        state = gesture.get_current_event_state()
        if state & Gdk.ModifierType.CONTROL_MASK:
            self.is_panning[drawing_area] = True
            self.pan_last_offset_x[drawing_area] = 0.0
            self.pan_last_offset_y[drawing_area] = 0.0
    
    def _on_drag_update(self, gesture, offset_x, offset_y, manager, drawing_area):
        """Handle drag update for panning.
        
        Args:
            gesture: GestureDrag.
            offset_x: X offset from drag start (cumulative).
            offset_y: Y offset from drag start (cumulative).
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        if self.is_panning.get(drawing_area, False):
            # Calculate incremental delta since last update
            last_x = self.pan_last_offset_x.get(drawing_area, 0.0)
            last_y = self.pan_last_offset_y.get(drawing_area, 0.0)
            delta_x = offset_x - last_x
            delta_y = offset_y - last_y
            
            # Pan by the incremental delta
            manager.pan(-delta_x, -delta_y)
            
            # Store current offset for next update
            self.pan_last_offset_x[drawing_area] = offset_x
            self.pan_last_offset_y[drawing_area] = offset_y
            
            # Request redraw
            drawing_area.queue_draw()
    
    def _on_drag_end(self, gesture, offset_x, offset_y, manager, drawing_area):
        """Handle drag end for panning.
        
        Args:
            gesture: GestureDrag.
            offset_x: Final X offset from drag start.
            offset_y: Final Y offset from drag start.
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        if self.is_panning.get(drawing_area, False):
            # Final incremental pan update
            last_x = self.pan_last_offset_x.get(drawing_area, 0.0)
            last_y = self.pan_last_offset_y.get(drawing_area, 0.0)
            delta_x = offset_x - last_x
            delta_y = offset_y - last_y
            
            manager.pan(-delta_x, -delta_y)
            drawing_area.queue_draw()
            
        # Clear pan state
        self.is_panning[drawing_area] = False
        self.pan_last_offset_x[drawing_area] = 0.0
        self.pan_last_offset_y[drawing_area] = 0.0
    
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
