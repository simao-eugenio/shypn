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
import math

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

# Import Petri net object types for isinstance checks
try:
    from shypn.netobjs import Place, Transition, Arc
except ImportError as e:
    print(f'ERROR: Cannot import Petri net objects: {e}', file=sys.stderr)
    sys.exit(1)

# Import zoom palette
try:
    from shypn.helpers.predefined_zoom import create_zoom_palette
except ImportError as e:
    print(f'ERROR: Cannot import zoom palette: {e}', file=sys.stderr)
    sys.exit(1)

# Import edit palettes
try:
    from shypn.helpers.edit_palette_loader import create_edit_palette
    from shypn.helpers.edit_tools_loader import create_edit_tools_palette
except ImportError as e:
    print(f'ERROR: Cannot import edit palettes: {e}', file=sys.stderr)
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
        
        # Dictionary to map drawing areas to their edit palettes
        self.edit_palettes = {}  # {drawing_area: EditPaletteLoader}
        self.edit_tools_palettes = {}  # {drawing_area: EditToolsLoader}
        
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
            overlay_widget = None
            
            # Page is now a GtkOverlay, get the overlay box and scrolled window
            if isinstance(page, Gtk.Overlay):
                overlay_widget = page  # Store the actual GtkOverlay for add_overlay
                # Get the scrolled window (first child)
                scrolled = overlay_widget.get_child()
                if isinstance(scrolled, Gtk.ScrolledWindow):
                    drawing_area = scrolled.get_child()
                    # ScrolledWindow may wrap child in Viewport
                    if hasattr(drawing_area, 'get_child'):
                        drawing_area = drawing_area.get_child()
                    if drawing_area and isinstance(drawing_area, Gtk.DrawingArea):
                        # Get overlay box for adding zoom control
                        overlay_box = self.builder.get_object('canvas_overlay_box_1')
                        self._setup_canvas_manager(drawing_area, overlay_box, overlay_widget)
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
    
    def _setup_canvas_manager(self, drawing_area, overlay_box=None, overlay_widget=None):
        """Setup canvas manager and wire up callbacks for a drawing area.
        
        Args:
            drawing_area: GtkDrawingArea widget to setup.
            overlay_box: Optional GtkBox for overlay widgets (zoom control).
            overlay_widget: Optional GtkOverlay for adding overlays directly.
        """
        
        # Create canvas manager for this drawing area (no filename needed)
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
        self.canvas_managers[drawing_area] = manager
        
        # Detect and set screen DPI
        try:
            screen = drawing_area.get_screen()
            if screen:
                dpi = screen.get_resolution()
                if dpi and dpi > 0:
                    manager.set_screen_dpi(dpi)
                    print(f"[DPI] Detected screen DPI: {dpi}")
                else:
                    print("[DPI] Using default DPI: 96.0")
        except Exception as e:
            print(f"[DPI] Could not detect DPI: {e}, using default 96.0")
        
        # Load saved view state if it exists
        manager.load_view_state_from_file()
        
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
            # Create and add zoom palette
            zoom_palette = create_zoom_palette()
            zoom_widget = zoom_palette.get_widget()
            if zoom_widget:
                overlay_box.pack_start(zoom_widget, False, False, 0)  # GTK3 uses pack_start
                zoom_palette.set_canvas_manager(manager, drawing_area, self.parent_window)
                self.zoom_palettes[drawing_area] = zoom_palette
            
            # Create and add edit palettes (independent overlays, positioned via their own properties)
            if overlay_widget:
                # Create edit tools palette first (so edit palette can reference it)
                edit_tools_palette = create_edit_tools_palette()
                edit_tools_widget = edit_tools_palette.get_widget()
                
                # Create edit palette (main [E] button)
                edit_palette = create_edit_palette()
                edit_widget = edit_palette.get_widget()
                
                # Link the two palettes
                edit_palette.set_tools_palette_loader(edit_tools_palette)
                
                # Add widgets as independent overlays using the GtkOverlay (like legacy code does)
                # Tools palette added first (appears above [E] button when revealed)
                if edit_tools_widget:
                    overlay_widget.add_overlay(edit_tools_widget)
                    self.edit_tools_palettes[drawing_area] = edit_tools_palette
                
                if edit_widget:
                    overlay_widget.add_overlay(edit_widget)
                    self.edit_palettes[drawing_area] = edit_palette
                
                # Connect tool-changed signal to update canvas manager
                edit_tools_palette.connect('tool-changed', self._on_tool_changed, manager, drawing_area)
        
    
    def _on_tool_changed(self, tools_palette, tool_name, manager, drawing_area):
        """Handle tool selection change from edit tools palette.
        
        Args:
            tools_palette: EditToolsLoader instance that emitted the signal.
            tool_name: Name of the selected tool ('place', 'transition', 'arc') or empty string for none.
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        # Update canvas manager with selected tool
        if tool_name:
            manager.set_tool(tool_name)
        else:
            manager.clear_tool()
    
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
        
        # Store arc creation state per drawing area
        if not hasattr(self, '_arc_state'):
            self._arc_state = {}
        self._arc_state[drawing_area] = {
            'source': None,  # Source object for arc creation
            'cursor_pos': (0, 0)  # Last cursor position for preview
        }
        
        # Store double-click tracking per drawing area
        if not hasattr(self, '_click_state'):
            self._click_state = {}
        self._click_state[drawing_area] = {
            'last_click_time': 0.0,
            'last_click_obj': None,
            'double_click_threshold': 0.3,  # 300ms for double-click
            'pending_timeout': None,  # GLib timeout ID for delayed single-click
            'pending_click_data': None  # Store click data while waiting
        }
        
        # Setup context menu
        self._setup_canvas_context_menu(drawing_area, manager)
    
    # ==================== GTK3 Event Handlers ====================
    
    def _on_button_press(self, widget, event, manager):
        """Handle button press events (GTK3)."""
        state = self._drag_state[widget]
        arc_state = self._arc_state[widget]
        
        # Check if arc tool is active (special handling)
        if event.button == 1 and manager.is_tool_active() and manager.get_tool() == 'arc':
            # Arc tool: two-click arc creation
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            clicked_obj = manager.find_object_at_position(world_x, world_y)
            
            if clicked_obj is None:
                # Click on empty space: reset arc source
                if arc_state['source'] is not None:
                    arc_state['source'] = None
                    widget.queue_draw()
                return True
            
            if arc_state['source'] is None:
                # First click: set source
                # Only places and transitions can be arc sources
                if isinstance(clicked_obj, (Place, Transition)):
                    arc_state['source'] = clicked_obj
                    print(f"Arc creation: source {clicked_obj.name} selected")
                    widget.queue_draw()
                return True
            else:
                # Second click: create arc from source to target
                target = clicked_obj
                source = arc_state['source']
                
                if target == source:
                    # Same object: ignore
                    return True
                
                # Try to create arc (bipartite validation happens in Arc.__init__)
                try:
                    arc = manager.add_arc(source, target)
                    print(f"Created {arc.name}: {source.name} → {target.name}")
                    widget.queue_draw()
                except ValueError as e:
                    # Bipartite validation failed
                    print(f"Cannot create arc: {e}")
                finally:
                    # Reset arc source
                    arc_state['source'] = None
                    widget.queue_draw()
                
                return True
        
        # Check if creation tools are active (left-click only)
        # Note: Select tool is handled separately below in selection mode
        if event.button == 1 and manager.is_tool_active():
            tool = manager.get_tool()
            
            # Only handle creation tools (place, transition) here
            # Select tool is handled in selection mode logic below
            if tool in ('place', 'transition'):
                # Tool mode: handle object creation
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                
                if tool == 'place':
                    # Create place at click position
                    place = manager.add_place(world_x, world_y)
                    print(f"Created {place.name} at ({world_x:.1f}, {world_y:.1f})")
                    widget.queue_draw()
                elif tool == 'transition':
                    # Create transition at click position
                    transition = manager.add_transition(world_x, world_y)
                    print(f"Created {transition.name} at ({world_x:.1f}, {world_y:.1f})")
                    widget.queue_draw()
                
                # Don't start drag mode when using creation tools
                return True
        
        # Selection mode: active when no tool OR select tool is active
        # This allows both clicking objects with no tool and explicit select tool
        tool = manager.get_tool() if manager.is_tool_active() else None
        is_selection_mode = (tool is None or tool == 'select')
        
        if event.button == 1 and is_selection_mode:
            # Left-click: toggle selection OR start rectangle selection
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            clicked_obj = manager.find_object_at_position(world_x, world_y)
            
            # Check for Ctrl key (multi-select)
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            
            if clicked_obj is not None:
                # Check for double-click to enter edit mode
                import time
                from gi.repository import GLib
                
                click_state = self._click_state[widget]
                current_time = time.time()
                time_since_last = current_time - click_state['last_click_time']
                is_double_click = (
                    time_since_last < click_state['double_click_threshold'] and
                    click_state['last_click_obj'] == clicked_obj
                )
                
                # ALWAYS cancel any pending single-click first
                # This prevents multiple pending clicks from accumulating
                if click_state['pending_timeout'] is not None:
                    GLib.source_remove(click_state['pending_timeout'])
                    click_state['pending_timeout'] = None
                    click_state['pending_click_data'] = None
                
                # Check if clicking on already-selected object (potential drag start)
                if clicked_obj.selected and not is_double_click:
                    # Start potential drag (will activate after movement threshold)
                    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
                    
                    # IMPORTANT: Set drag state so motion handler can update drag
                    state['active'] = True
                    state['button'] = event.button
                    state['start_x'] = event.x
                    state['start_y'] = event.y
                    state['is_panning'] = False
                    state['is_rect_selecting'] = False
                
                if is_double_click:
                    # Double-click detected: enter EDIT mode (only if already selected)
                    if clicked_obj.selected:
                        manager.selection_manager.enter_edit_mode(clicked_obj, manager=manager)
                        print(f"{clicked_obj.name} entered EDIT mode (transform handles visible)")
                    else:
                        # First click selected, second click enters edit mode - handle immediately
                        manager.selection_manager.toggle_selection(clicked_obj, multi=is_ctrl, manager=manager)
                        manager.selection_manager.enter_edit_mode(clicked_obj, manager=manager)
                        print(f"{clicked_obj.name} selected and entered EDIT mode")
                    
                    click_state['last_click_time'] = 0.0  # Reset to prevent triple-click
                    click_state['last_click_obj'] = None
                    widget.queue_draw()
                    return True
                else:
                    # Potential single-click: delay processing to detect double-click
                    # Store click data
                    click_state['pending_click_data'] = {
                        'obj': clicked_obj,
                        'is_ctrl': is_ctrl,
                        'widget': widget,
                        'manager': manager
                    }
                    
                    # Schedule delayed single-click processing
                    def process_single_click():
                        data = click_state['pending_click_data']
                        if data is None:
                            return False  # Already processed or cancelled
                        
                        obj = data['obj']
                        ctrl = data['is_ctrl']
                        w = data['widget']
                        mgr = data['manager']
                        
                        # Check if drag started (if so, don't process single-click)
                        if mgr.selection_manager.is_dragging():
                            click_state['pending_timeout'] = None
                            click_state['pending_click_data'] = None
                            return False
                        
                        # Check if we entered EDIT mode (via double-click) before this callback fired
                        # If so, don't process the single-click - it's already handled
                        if mgr.selection_manager.is_edit_mode() and mgr.selection_manager.edit_target == obj:
                            # Double-click already handled this, skip single-click processing
                            click_state['pending_timeout'] = None
                            click_state['pending_click_data'] = None
                            return False
                        
                        # Exit edit mode only when selecting a DIFFERENT object
                        if mgr.selection_manager.is_edit_mode():
                            current_edit_target = mgr.selection_manager.edit_target
                            if current_edit_target != obj:
                                mgr.selection_manager.exit_edit_mode()
                                print(f"Exited EDIT mode (selected different object)")
                        
                        mgr.selection_manager.toggle_selection(obj, multi=ctrl, manager=mgr)
                        status = "selected" if obj.selected else "deselected"
                        multi_str = " (multi)" if ctrl else ""
                        print(f"{obj.name} {status}{multi_str} [NORMAL mode]")
                        
                        w.queue_draw()
                        
                        # Clear pending data
                        click_state['pending_timeout'] = None
                        click_state['pending_click_data'] = None
                        return False  # Don't repeat
                    
                    # Wait 300ms to see if double-click comes
                    timeout_ms = int(click_state['double_click_threshold'] * 1000)
                    click_state['pending_timeout'] = GLib.timeout_add(timeout_ms, process_single_click)
                    
                    # Update click tracking
                    click_state['last_click_time'] = current_time
                    click_state['last_click_obj'] = clicked_obj
                    
                    return True
            else:
                # Clicked empty space: start rectangle selection (rubber-band)
                manager.rectangle_selection.start(world_x, world_y)
                
                # Exit EDIT mode when clicking empty space
                if manager.selection_manager.is_edit_mode():
                    manager.selection_manager.exit_edit_mode()
                    print("Exited EDIT mode (clicked empty space)")
                
                # Also start drag state for tracking
                state['active'] = True
                state['button'] = event.button
                state['start_x'] = event.x
                state['start_y'] = event.y
                state['is_panning'] = False
                state['is_rect_selecting'] = True  # Flag for rectangle selection
                
                # Clear selection if not multi-select
                if not is_ctrl:
                    manager.clear_all_selections()
                
                widget.grab_focus()
                return True
        
        # Default behavior: pan mode
        # All buttons can start drag (including right-click for pan)
        state['active'] = True
        state['button'] = event.button
        state['start_x'] = event.x
        state['start_y'] = event.y
        state['start_pan_x'] = manager.pan_x  # Store initial pan offset
        state['start_pan_y'] = manager.pan_y
        state['is_panning'] = False
        state['is_rect_selecting'] = False  # Initialize flag
        
        widget.grab_focus()
        
        # Return True to prevent default handling (especially for right-click)
        return True
    
    def _on_button_release(self, widget, event, manager):
        """Handle button release events (GTK3)."""
        state = self._drag_state[widget]
        
        # End object dragging if active
        if manager.selection_manager.end_drag():
            widget.queue_draw()
        
        # Handle rectangle selection finish
        if state.get('is_rect_selecting', False):
            # Check for Ctrl key (multi-select)
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            
            # Finish rectangle selection and select objects
            bounds = manager.rectangle_selection.finish()
            if bounds:
                count = manager.rectangle_selection.select_objects(manager, multi=is_ctrl)
                multi_str = " (multi)" if is_ctrl else ""
                print(f"Rectangle selection: {count} objects selected{multi_str}")
            
            # Reset state
            state['is_rect_selecting'] = False
            widget.queue_draw()
        
        # Right-click: show context menu ONLY if no panning occurred
        if event.button == 3 and not state['is_panning']:
            # Double-check: only show menu if it was a click (< 5px movement), not a drag
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < 5:
                # Check if clicked on an object
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                clicked_obj = manager.find_object_at_position(world_x, world_y)
                
                if clicked_obj:
                    # Show object-specific context menu
                    self._show_object_context_menu(event.x, event.y, widget, manager, clicked_obj)
                else:
                    # Show canvas context menu
                    self._show_canvas_context_menu(event.x, event.y, widget)
        
        # Reset all drag state
        was_panning = state['is_panning']
        state['active'] = False
        state['button'] = 0
        state['is_panning'] = False  # IMPORTANT: Reset panning flag
        
        # Save view state after panning operation completes
        if was_panning:
            manager.save_view_state_to_file()
        
        # Return True to prevent default handling
        return True
    
    def _on_motion_notify(self, widget, event, manager):
        """Handle motion events (GTK3)."""
        state = self._drag_state[widget]
        arc_state = self._arc_state[widget]
        
        # Update cursor position always (for zoom centering and arc preview)
        manager.set_pointer_position(event.x, event.y)
        world_x, world_y = manager.screen_to_world(event.x, event.y)
        arc_state['cursor_pos'] = (world_x, world_y)
        
        # If arc tool active with source selected, redraw for preview
        if manager.is_tool_active() and manager.get_tool() == 'arc' and arc_state['source'] is not None:
            widget.queue_draw()
        
        # Handle dragging only if button is pressed
        if state['active'] and state['button'] > 0:
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            
            # Start panning if movement detected (5px threshold)
            if not state['is_panning'] and (abs(dx) >= 5 or abs(dy) >= 5):
                state['is_panning'] = True
            
            # Handle rectangle selection drag
            if state.get('is_rect_selecting', False):
                # Update rectangle selection
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                manager.rectangle_selection.update(world_x, world_y)
                widget.queue_draw()
                return True
            
            # Check if dragging objects (via SelectionManager)
            # Only check if NOT doing rectangle selection
            if manager.selection_manager.update_drag(event.x, event.y, manager):
                # Cancel any pending single-click processing
                # This prevents selection change when dragging starts
                click_state = self._click_state.get(widget)
                if click_state and click_state.get('pending_timeout'):
                    from gi.repository import GLib
                    GLib.source_remove(click_state['pending_timeout'])
                    click_state['pending_timeout'] = None
                    click_state['pending_click_data'] = None
                
                widget.queue_draw()
                return True
            
            # Pan with right button (3) or middle button (2) or Shift+left (1)
            is_shift_pressed = event.state & Gdk.ModifierType.SHIFT_MASK
            should_pan = state['button'] in [2, 3] or (state['button'] == 1 and is_shift_pressed)
            
            if should_pan and state['is_panning']:
                # Calculate total delta from start (legacy approach)
                # Pan is set to initial offset + screen delta / zoom
                dx = event.x - state['start_x']
                dy = event.y - state['start_y']
                manager.pan_x = state['start_pan_x'] + dx / manager.zoom
                manager.pan_y = state['start_pan_y'] + dy / manager.zoom
                manager.clamp_pan()
                manager._needs_redraw = True
                widget.queue_draw()
        
        # Return True to prevent default handling
        return True
    
    def _on_scroll_event(self, widget, event, manager):
        """Handle scroll events for zoom (GTK3).
        
        Supports both discrete scroll wheels and smooth scrolling (trackpads).
        Zooms centered at cursor position (pointer-centered zoom).
        """
        direction = event.direction
        factor = None
        
        # Smooth scrolling (trackpad) uses delta_y sign
        if direction == Gdk.ScrollDirection.SMOOTH:
            dy = event.delta_y
            if abs(dy) < 1e-6:
                return False
            # delta_y > 0 = scroll down = zoom out
            # delta_y < 0 = scroll up = zoom in
            factor = (1 / 1.1) if dy > 0 else 1.1
        else:
            # Discrete scroll wheel
            if direction == Gdk.ScrollDirection.UP:
                factor = 1.1  # Zoom in 10%
            elif direction == Gdk.ScrollDirection.DOWN:
                factor = 1 / 1.1  # Zoom out ~9%
        
        if factor is None:
            return False
        
        # Apply pointer-centered zoom
        manager.zoom_at_point(factor, event.x, event.y)
        widget.queue_draw()
        return True
    
    def _on_key_press_event(self, widget, event, manager):
        """Handle key press events (GTK3)."""
        # Escape key: cancel drag OR exit edit mode OR dismiss context menu
        if event.keyval == Gdk.KEY_Escape:
            # First priority: cancel drag if active
            if manager.selection_manager.cancel_drag():
                print("Drag cancelled - positions restored")
                widget.queue_draw()
                return True
            
            # Second priority: exit edit mode if active
            if manager.selection_manager.is_edit_mode():
                manager.selection_manager.exit_edit_mode()
                print("Exited EDIT mode → NORMAL mode")
                widget.queue_draw()
                return True
            
            # Third priority: dismiss context menu
            if hasattr(self, '_canvas_context_menu') and self._canvas_context_menu:
                # GTK3 Menu: use popdown()
                if isinstance(self._canvas_context_menu, Gtk.Menu):
                    self._canvas_context_menu.popdown()
                    return True
        return False
    
    # ==================== Event Handlers (Legacy - will be cleaned up) ====================
    
    def _on_draw(self, drawing_area, cr, width, height, manager):
        """Draw callback for the canvas.
        
        Uses Cairo transformation approach (legacy-compatible):
        - Apply cr.scale() and cr.translate() for automatic coordinate transformation
        - Objects render in world coordinates, Cairo scales them automatically
        - Line widths compensated to maintain constant pixel size
        
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
        
        # Apply pan and zoom transformation (legacy-compatible)
        # This makes all subsequent drawing operations happen in world coordinates
        cr.save()
        cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
        cr.scale(manager.zoom, manager.zoom)
        
        # Draw grid in world space (scales with zoom)
        manager.draw_grid(cr)
        
        # Draw Petri Net objects in world coordinates
        # Objects are rendered in order: arcs (behind), then places, then transitions
        for obj in manager.get_all_objects():
            obj.render(cr, zoom=manager.zoom)  # Pass zoom for line width compensation
        
        # Draw selection layer (selection highlights, bounding box, transform handles)
        manager.editing_transforms.render_selection_layer(cr, manager, manager.zoom)
        
        # Draw rectangle selection (rubber-band) if active
        manager.rectangle_selection.render(cr, manager.zoom)
        
        # Restore device space (for overlays)
        cr.restore()
        
        # Draw arc preview line in device space (overlay)
        if drawing_area in self._arc_state:
            arc_state = self._arc_state[drawing_area]
            if (manager.is_tool_active() and manager.get_tool() == 'arc' and 
                arc_state['source'] is not None):
                self._draw_arc_preview(cr, arc_state, manager)
        
        # Mark as clean after drawing
        manager.mark_clean()
    
    def _draw_arc_preview(self, cr, arc_state, manager):
        """Draw orange preview line for arc creation.
        
        Args:
            cr: Cairo context.
            arc_state: Arc state dictionary with 'source' and 'cursor_pos'.
            manager: ModelCanvasManager instance.
        """
        source = arc_state['source']
        cursor_x, cursor_y = arc_state['cursor_pos']
        
        # Get source position in world space
        src_x, src_y = source.x, source.y
        
        # Calculate direction vector
        dx = cursor_x - src_x
        dy = cursor_y - src_y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < 1:
            return  # Too close, don't draw
        
        # Normalize direction
        ux, uy = dx / dist, dy / dist
        
        # Determine source radius (offset start point)
        if isinstance(source, Place):
            src_radius = source.radius
        elif isinstance(source, Transition):
            # Approximate with max dimension
            w = source.width if source.horizontal else source.height
            h = source.height if source.horizontal else source.width
            src_radius = max(w, h) / 2.0
        else:
            src_radius = 20.0  # Fallback
        
        # Calculate start point (offset by radius)
        start_x = src_x + ux * src_radius
        start_y = src_y + uy * src_radius
        
        # Convert to screen space
        start_sx, start_sy = manager.world_to_screen(start_x, start_y)
        end_sx, end_sy = manager.world_to_screen(cursor_x, cursor_y)
        
        # Draw orange preview line (legacy style)
        cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)  # Orange, semi-transparent
        cr.set_line_width(2.0)
        cr.move_to(start_sx, start_sy)
        cr.line_to(end_sx, end_sy)
        cr.stroke()
        
        # Draw arrowhead at cursor (smaller preview arrowhead)
        arrow_len = 11.0
        arrow_width = 6.0
        angle = math.atan2(dy, dx)
        
        # Calculate arrowhead points
        left_x = end_sx - arrow_len * math.cos(angle) + arrow_width * math.sin(angle)
        left_y = end_sy - arrow_len * math.sin(angle) - arrow_width * math.cos(angle)
        right_x = end_sx - arrow_len * math.cos(angle) - arrow_width * math.sin(angle)
        right_y = end_sy - arrow_len * math.sin(angle) + arrow_width * math.cos(angle)
        
        # Draw filled arrowhead
        cr.move_to(end_sx, end_sy)
        cr.line_to(left_x, left_y)
        cr.line_to(right_x, right_y)
        cr.close_path()
        cr.fill()
    
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
    
    def _show_object_context_menu(self, x, y, drawing_area, manager, obj):
        """Show object-specific context menu.
        
        Args:
            x, y: Position to show menu (widget-relative coordinates)
            drawing_area: GtkDrawingArea widget
            manager: ModelCanvasManager instance
            obj: Selected object (Place, Transition, or Arc)
        """
        from shypn.netobjs import Place, Transition, Arc
        
        # Create context menu
        menu = Gtk.Menu()
        
        # Determine object type for title
        if isinstance(obj, Place):
            obj_type = "Place"
        elif isinstance(obj, Transition):
            obj_type = "Transition"
        elif isinstance(obj, Arc):
            obj_type = "Arc"
        else:
            obj_type = "Object"
        
        # Add title item (disabled)
        title_item = Gtk.MenuItem(label=f"{obj_type}: {obj.name}")
        title_item.set_sensitive(False)
        title_item.show()
        menu.append(title_item)
        
        # Add separator
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        menu.append(separator)
        
        # Add menu items
        menu_items = [
            ("Edit Properties...", lambda: self._on_object_properties(obj, manager, drawing_area)),
            ("Edit Mode (Double-click)", lambda: self._on_object_edit_mode(obj, manager, drawing_area)),
            None,  # Separator
            ("Delete", lambda: self._on_object_delete(obj, manager, drawing_area)),
        ]
        
        # Add arc-specific options
        if isinstance(obj, Arc):
            menu_items.insert(2, ("Edit Weight...", lambda: self._on_arc_edit_weight(obj, manager, drawing_area)))
        
        for item_data in menu_items:
            if item_data is None:
                menu_item = Gtk.SeparatorMenuItem()
            else:
                label, callback = item_data
                menu_item = Gtk.MenuItem(label=label)
                menu_item.connect("activate", lambda w, cb=callback: cb())
            
            menu_item.show()
            menu.append(menu_item)
        
        # Show menu
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
    
    # ==================== Object Context Menu Actions ====================
    
    def _on_object_delete(self, obj, manager, drawing_area):
        """Delete an object from the canvas.
        
        Args:
            obj: Object to delete (Place, Transition, or Arc)
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Place, Transition, Arc
        
        # Remove from appropriate list
        if isinstance(obj, Place):
            if obj in manager.places:
                manager.places.remove(obj)
                print(f"Deleted {obj.name}")
        elif isinstance(obj, Transition):
            if obj in manager.transitions:
                manager.transitions.remove(obj)
                print(f"Deleted {obj.name}")
        elif isinstance(obj, Arc):
            if obj in manager.arcs:
                manager.arcs.remove(obj)
                print(f"Deleted {obj.name}")
        
        # Deselect the object
        if obj.selected:
            manager.selection_manager.deselect(obj)
        
        # Exit EDIT mode if this was the edit target
        if manager.selection_manager.is_edit_mode() and manager.selection_manager.edit_target == obj:
            manager.selection_manager.exit_edit_mode()
        
        manager.mark_dirty()
        drawing_area.queue_draw()
    
    def _on_object_edit_mode(self, obj, manager, drawing_area):
        """Enter EDIT mode for an object.
        
        Args:
            obj: Object to edit
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Select the object if not selected
        if not obj.selected:
            manager.selection_manager.select(obj, multi=False, manager=manager)
        
        # Enter EDIT mode
        manager.selection_manager.enter_edit_mode(obj, manager=manager)
        print(f"{obj.name} entered EDIT mode")
        drawing_area.queue_draw()
    
    def _on_object_properties(self, obj, manager, drawing_area):
        """Open properties dialog for an object.
        
        Args:
            obj: Object to edit properties for
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Place, Transition, Arc
        
        # Create properties dialog
        dialog = Gtk.Dialog(
            title=f"{type(obj).__name__} Properties",
            parent=self.parent_window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_border_width(10)
        
        # Add property fields
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        
        row = 0
        
        # Name (read-only)
        label = Gtk.Label(label="Name:")
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)
        
        name_label = Gtk.Label(label=obj.name)
        name_label.set_halign(Gtk.Align.START)
        grid.attach(name_label, 1, row, 1, 1)
        row += 1
        
        # Label (editable)
        label = Gtk.Label(label="Label:")
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)
        
        label_entry = Gtk.Entry()
        label_entry.set_text(obj.label or "")
        label_entry.set_hexpand(True)
        grid.attach(label_entry, 1, row, 1, 1)
        row += 1
        
        # Type-specific properties
        if isinstance(obj, Place):
            # Initial marking
            label = Gtk.Label(label="Marking:")
            label.set_halign(Gtk.Align.END)
            grid.attach(label, 0, row, 1, 1)
            
            marking_spin = Gtk.SpinButton()
            marking_spin.set_adjustment(Gtk.Adjustment(value=obj.marking, lower=0, upper=999, step_increment=1))
            marking_spin.set_digits(0)
            grid.attach(marking_spin, 1, row, 1, 1)
            row += 1
            
        elif isinstance(obj, Arc):
            # Arc weight
            label = Gtk.Label(label="Weight:")
            label.set_halign(Gtk.Align.END)
            grid.attach(label, 0, row, 1, 1)
            
            weight_spin = Gtk.SpinButton()
            weight_spin.set_adjustment(Gtk.Adjustment(value=obj.weight, lower=1, upper=999, step_increment=1))
            weight_spin.set_digits(0)
            grid.attach(weight_spin, 1, row, 1, 1)
            row += 1
        
        grid.show_all()
        content_area.pack_start(grid, True, True, 0)
        
        # Show dialog and get response
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Update object properties
            new_label = label_entry.get_text()
            if new_label != obj.label:
                obj.label = new_label
                print(f"Updated {obj.name} label: '{new_label}'")
            
            # Update type-specific properties
            if isinstance(obj, Place):
                new_marking = int(marking_spin.get_value())
                if new_marking != obj.marking:
                    obj.set_marking(new_marking)
                    print(f"Updated {obj.name} marking: {new_marking}")
            
            elif isinstance(obj, Arc):
                new_weight = int(weight_spin.get_value())
                if new_weight != obj.weight:
                    obj.set_weight(new_weight)
                    print(f"Updated {obj.name} weight: {new_weight}")
            
            manager.mark_modified()
            drawing_area.queue_draw()
        
        dialog.destroy()
    
    def _on_arc_edit_weight(self, arc, manager, drawing_area):
        """Quick edit arc weight.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Create simple dialog for weight
        dialog = Gtk.Dialog(
            title=f"Edit {arc.name} Weight",
            parent=self.parent_window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_border_width(10)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        label = Gtk.Label(label="Weight:")
        box.pack_start(label, False, False, 0)
        
        weight_spin = Gtk.SpinButton()
        weight_spin.set_adjustment(Gtk.Adjustment(value=arc.weight, lower=1, upper=999, step_increment=1))
        weight_spin.set_digits(0)
        box.pack_start(weight_spin, True, True, 0)
        
        box.show_all()
        content_area.pack_start(box, True, True, 0)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_weight = int(weight_spin.get_value())
            if new_weight != arc.weight:
                arc.set_weight(new_weight)
                print(f"Updated {arc.name} weight: {new_weight}")
                manager.mark_modified()
                drawing_area.queue_draw()
        
        dialog.destroy()


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
