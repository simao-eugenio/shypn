"""Model Canvas Loader/Controller.

This module manages the multi-document Petri Net drawing canvas.
The canvas supports multiple tabs (documents), each with a scrollable
drawing area for creating and editing Petri Net models.

Architecture:
    pass
- GtkNotebook: Multi-document tab container
- GtkScrolledWindow: Scrollable viewport for each document
- GtkDrawingArea: Canvas for drawing Petri Net objects (Places, Transitions, Arcs)

Future extensions:
    pass
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
try:
    from shypn.data.model_canvas_manager import ModelCanvasManager
except ImportError as e:
    print(f'ERROR: Cannot import ModelCanvasManager: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.netobjs import Place, Transition, Arc
except ImportError as e:
    print(f'ERROR: Cannot import Petri net objects: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.helpers.predefined_zoom import create_zoom_palette
except ImportError as e:
    print(f'ERROR: Cannot import zoom palette: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.helpers.edit_palette_loader import create_edit_palette
    from shypn.helpers.edit_tools_loader import create_edit_tools_palette
except ImportError as e:
    print(f'ERROR: Cannot import edit palettes: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.helpers.simulate_palette_loader import create_simulate_palette
    from shypn.helpers.simulate_tools_palette_loader import create_simulate_tools_palette
except ImportError as e:
    print(f'ERROR: Cannot import simulation palettes: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from ui.palettes.mode.mode_palette_loader import ModePaletteLoader
except ImportError as e:
    print(f'ERROR: Cannot import mode palette: {e}', file=sys.stderr)
    sys.exit(1)

class ModelCanvasLoader:
    """Loader and controller for the model canvas (multi-document Petri Net editor)."""

    def __init__(self, ui_path=None):
        """Initialize the model canvas loader.
        
        Args:
            ui_path: Optional path to model_canvas.ui. If None, uses default location.
        """
        if ui_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'canvas', 'model_canvas.ui')
        self.ui_path = ui_path
        self.builder = None
        self.container = None
        self.notebook = None
        self.document_count = 0
        self.canvas_managers = {}
        self.zoom_palettes = {}
        self.edit_palettes = {}
        self.edit_tools_palettes = {}
        self.simulate_palettes = {}
        self.simulate_tools_palettes = {}
        self.mode_palettes = {}
        self.parent_window = None
        self.canvas_managers = {}
        self.document_count = 0
        self.persistency = None
        self.right_panel_loader = None
        self.context_menu_handler = None

    def load(self):
        """Load the canvas UI and return the container.
        
        Returns:
            Gtk.Box: The model canvas container with notebook.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If container or notebook not found in UI file.
        """
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'Model canvas UI file not found: {self.ui_path}')
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.container = self.builder.get_object('model_canvas_container')
        self.notebook = self.builder.get_object('canvas_notebook')
        if self.container is None:
            raise ValueError("Object 'model_canvas_container' not found in model_canvas.ui")
        if self.notebook is None:
            raise ValueError("Object 'canvas_notebook' not found in model_canvas.ui")
        self.document_count = self.notebook.get_n_pages()
        if self.document_count > 0:
            page = self.notebook.get_nth_page(0)
            drawing_area = None
            overlay_box = None
            overlay_widget = None
            if isinstance(page, Gtk.Overlay):
                overlay_widget = page
                scrolled = overlay_widget.get_child()
                if isinstance(scrolled, Gtk.ScrolledWindow):
                    drawing_area = scrolled.get_child()
                    if hasattr(drawing_area, 'get_child'):
                        drawing_area = drawing_area.get_child()
                    if drawing_area and isinstance(drawing_area, Gtk.DrawingArea):
                        overlay_box = self.builder.get_object('canvas_overlay_box_1')
                        self._setup_canvas_manager(drawing_area, overlay_box, overlay_widget)
            elif isinstance(page, Gtk.ScrolledWindow):
                drawing_area = page.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
                if drawing_area and isinstance(drawing_area, Gtk.DrawingArea):
                    self._setup_canvas_manager(drawing_area)
            if drawing_area:
                tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                tab_label = Gtk.Label(label='')
                tab_label.set_ellipsize(3)
                tab_box.pack_start(tab_label, True, True, 0)
                close_button = Gtk.Button()
                close_button.set_relief(Gtk.ReliefStyle.NONE)
                close_button.set_focus_on_click(False)
                close_icon = Gtk.Image.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON)
                close_button.set_image(close_icon)
                close_button.connect('clicked', self._on_tab_close_clicked, page)
                tab_box.pack_start(close_button, False, False, 0)
                self.notebook.set_tab_label(page, tab_box)
                tab_box.show_all()
        self.notebook.connect('switch-page', self._on_notebook_page_changed)
        return self.container

    def _on_notebook_page_changed(self, notebook, page, page_num):
        """Handle notebook page switch.
        
        Args:
            notebook: GtkNotebook instance.
            page: The new page widget.
            page_num: The index of the new page.
        """
        drawing_area = None
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
        if self.persistency:
            if drawing_area and drawing_area in self.canvas_managers:
                manager = self.canvas_managers[drawing_area]
                filename = manager.filename
                if manager.is_default_filename():
                    self.persistency.set_filepath(None)
                else:
                    pass
        if self.right_panel_loader and drawing_area:
            if drawing_area in self.simulate_tools_palettes:
                simulate_tools_palette = self.simulate_tools_palettes[drawing_area]
                if hasattr(simulate_tools_palette, 'data_collector'):
                    data_collector = simulate_tools_palette.data_collector
                    self.right_panel_loader.set_data_collector(data_collector)
            if drawing_area in self.canvas_managers:
                manager = self.canvas_managers[drawing_area]
                self.right_panel_loader.set_model(manager)
            if self.right_panel_loader.context_menu_handler and (not self.context_menu_handler):
                self.set_context_menu_handler(self.right_panel_loader.context_menu_handler)

    def _on_tab_close_clicked(self, button, page_widget):
        """Handle tab close button click.
        
        Args:
            button: The close button that was clicked.
            page_widget: The page widget (overlay) to close.
        """
        page_num = self.notebook.page_num(page_widget)
        if page_num == -1:
            return
        self.close_tab(page_num)

    def close_tab(self, page_num):
        """Close a tab after checking for unsaved changes.
        
        Args:
            page_num: Index of the tab to close.
            
        Returns:
            bool: True if tab was closed, False if user cancelled.
        """
        if page_num < 0 or page_num >= self.notebook.get_n_pages():
            return False
        page = self.notebook.get_nth_page(page_num)
        drawing_area = None
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
        if self.persistency and drawing_area:
            manager = self.canvas_managers.get(drawing_area)
            if manager:
                current_page = self.notebook.get_current_page()
                current_widget = self.notebook.get_nth_page(current_page)
                self.notebook.set_current_page(page_num)
                if not self.persistency.check_unsaved_changes():
                    self.notebook.set_current_page(current_page)
                    return False
        self.notebook.remove_page(page_num)
        if drawing_area and drawing_area in self.canvas_managers:
            del self.canvas_managers[drawing_area]
        if drawing_area and drawing_area in self.zoom_palettes:
            del self.zoom_palettes[drawing_area]
        if drawing_area and drawing_area in self.edit_palettes:
            del self.edit_palettes[drawing_area]
        if drawing_area and drawing_area in self.edit_tools_palettes:
            del self.edit_tools_palettes[drawing_area]
        if drawing_area and drawing_area in self.simulate_palettes:
            del self.simulate_palettes[drawing_area]
        if drawing_area and drawing_area in self.simulate_tools_palettes:
            del self.simulate_tools_palettes[drawing_area]
        if self.notebook.get_n_pages() == 0:
            self.add_document(filename='default')
        return True

    def add_document(self, title=None, filename=None):
        """Add a new document (tab) to the canvas.
        
        Args:
            title: Optional title for the new document tab (deprecated, use filename).
            filename: Base filename without extension (default: "default").
            
        Returns:
            tuple: (page_index, drawing_area) for the new document.
        """
        if self.notebook is None:
            raise RuntimeError('Canvas not loaded. Call load() first.')
        self.document_count += 1
        if filename is None:
            if title:
                filename = title
            else:
                filename = f"default{(self.document_count if self.document_count > 1 else '')}"
        overlay = Gtk.Overlay()
        overlay.set_hexpand(True)
        overlay.set_vexpand(True)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        drawing = Gtk.DrawingArea()
        drawing.set_hexpand(True)
        drawing.set_vexpand(True)
        drawing.set_size_request(2000, 2000)
        scrolled.add(drawing)
        overlay.add(scrolled)
        overlay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        overlay_box.set_halign(Gtk.Align.END)
        overlay_box.set_valign(Gtk.Align.END)
        overlay_box.set_margin_end(10)
        overlay_box.set_margin_bottom(10)
        overlay.add_overlay(overlay_box)
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        tab_label = Gtk.Label(label='')
        tab_label.set_ellipsize(3)
        tab_box.pack_start(tab_label, True, True, 0)
        close_button = Gtk.Button()
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_focus_on_click(False)
        close_icon = Gtk.Image.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON)
        close_button.set_image(close_icon)
        close_button.connect('clicked', self._on_tab_close_clicked, overlay)
        tab_box.pack_start(close_button, False, False, 0)
        tab_box.show_all()
        page_index = self.notebook.append_page(overlay, tab_box)
        overlay.show_all()
        self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)
        self.notebook.set_current_page(page_index)
        return (page_index, drawing)

    def _setup_canvas_manager(self, drawing_area, overlay_box=None, overlay_widget=None, filename=None):
        """Setup canvas manager and wire up callbacks for a drawing area.
        
        Args:
            drawing_area: GtkDrawingArea widget to setup.
            overlay_box: Optional GtkBox for overlay widgets (zoom control).
            overlay_widget: Optional GtkOverlay for adding overlays directly.
            filename: Base filename without extension (default: "default").
        """
        if filename is None:
            filename = 'default'
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000, filename=filename)
        self.canvas_managers[drawing_area] = manager
        try:
            screen = drawing_area.get_screen()
            if screen:
                dpi = screen.get_resolution()
                if dpi and dpi > 0:
                    manager.set_screen_dpi(dpi)
        except Exception as e:
            pass
        manager.load_view_state_from_file()
        validation = manager.create_new_document(filename=filename)

        def on_draw_wrapper(widget, cr):
            allocation = widget.get_allocation()
            self._on_draw(widget, cr, allocation.width, allocation.height, manager)
            return False
        drawing_area.connect('draw', on_draw_wrapper)
        self._setup_event_controllers(drawing_area, manager)
        if overlay_box:
            zoom_palette = create_zoom_palette()
            zoom_widget = zoom_palette.get_widget()
            if zoom_widget:
                overlay_box.pack_start(zoom_widget, False, False, 0)
                zoom_palette.set_canvas_manager(manager, drawing_area, self.parent_window)
                self.zoom_palettes[drawing_area] = zoom_palette
            if overlay_widget:
                edit_tools_palette = create_edit_tools_palette()
                edit_tools_widget = edit_tools_palette.get_widget()
                edit_palette = create_edit_palette()
                edit_widget = edit_palette.get_widget()
                edit_palette.set_tools_palette_loader(edit_tools_palette)
                if edit_tools_widget:
                    overlay_widget.add_overlay(edit_tools_widget)
                    self.edit_tools_palettes[drawing_area] = edit_tools_palette
                if edit_widget:
                    overlay_widget.add_overlay(edit_widget)
                    self.edit_palettes[drawing_area] = edit_palette
                edit_tools_palette.connect('tool-changed', self._on_tool_changed, manager, drawing_area)
                simulate_tools_palette = create_simulate_tools_palette(model=manager)
                simulate_tools_widget = simulate_tools_palette.get_widget()
                simulate_tools_palette.connect('step-executed', self._on_simulation_step, drawing_area)
                simulate_tools_palette.connect('reset-executed', self._on_simulation_reset)
                simulate_palette = create_simulate_palette()
                simulate_widget = simulate_palette.get_widget()
                simulate_palette.set_tools_palette_loader(simulate_tools_palette)
                if simulate_tools_widget:
                    overlay_widget.add_overlay(simulate_tools_widget)
                    self.simulate_tools_palettes[drawing_area] = simulate_tools_palette
                if simulate_widget:
                    overlay_widget.add_overlay(simulate_widget)
                    self.simulate_palettes[drawing_area] = simulate_palette
                mode_palette = ModePaletteLoader()
                mode_widget = mode_palette.get_widget()
                if mode_widget:
                    overlay_widget.add_overlay(mode_widget)
                    self.mode_palettes[drawing_area] = mode_palette
                    mode_palette.connect('mode-changed', self._on_mode_changed, drawing_area, edit_palette, edit_tools_palette, simulate_palette, simulate_tools_palette)
                    self._update_palette_visibility(drawing_area, 'edit', edit_palette, edit_tools_palette, simulate_palette, simulate_tools_palette)

    def _on_simulation_step(self, palette, time, drawing_area):
        """Handle simulation step - redraw canvas to show updated token state.
        
        Args:
            palette: SimulateToolsPaletteLoader that emitted the signal
            time: Current simulation time
            drawing_area: GtkDrawingArea widget to redraw
        """
        drawing_area.queue_draw()

    def _on_simulation_reset(self, palette):
        """Handle simulation reset - blank analysis plots and prepare for new data.
        
        Args:
            palette: SimulateToolsPaletteLoader that emitted the signal
        """
        if self.right_panel_loader:
            if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
                panel = self.right_panel_loader.place_panel
                panel.last_data_length.clear()
                if panel.selected_objects:
                    panel.needs_update = True
                else:
                    panel._show_empty_state()
            if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                panel = self.right_panel_loader.transition_panel
                panel.last_data_length.clear()
                if panel.selected_objects:
                    panel.needs_update = True
                else:
                    panel._show_empty_state()

    def _on_mode_changed(self, mode_palette, mode, drawing_area, edit_palette, edit_tools_palette, simulate_palette, simulate_tools_palette):
        """Handle mode change between edit and simulation.
        
        Args:
            mode_palette: ModePaletteLoader that emitted the signal
            mode: New mode ('edit' or 'sim')
            drawing_area: GtkDrawingArea widget
            edit_palette: EditPaletteLoader instance
            edit_tools_palette: EditToolsLoader instance
            simulate_palette: SimulatePaletteLoader instance
            simulate_tools_palette: SimulateToolsPaletteLoader instance
        """
        self._update_palette_visibility(drawing_area, mode, edit_palette, edit_tools_palette, simulate_palette, simulate_tools_palette)

    def _update_palette_visibility(self, drawing_area, mode, edit_palette, edit_tools_palette, simulate_palette, simulate_tools_palette):
        """Update palette visibility based on current mode.
        
        Args:
            drawing_area: GtkDrawingArea widget
            mode: Current mode ('edit' or 'sim')
            edit_palette: EditPaletteLoader instance
            edit_tools_palette: EditToolsLoader instance
            simulate_palette: SimulatePaletteLoader instance
            simulate_tools_palette: SimulateToolsPaletteLoader instance
        """
        if mode == 'edit':
            if edit_palette:
                edit_palette.get_widget().show()
            if edit_tools_palette:
                edit_tools_palette.get_widget().show()
            if simulate_palette:
                simulate_palette.get_widget().hide()
            if simulate_tools_palette:
                simulate_tools_palette.get_widget().hide()
        else:
            if edit_palette:
                edit_palette.get_widget().hide()
            if edit_tools_palette:
                edit_tools_palette.get_widget().hide()
            if simulate_palette:
                simulate_palette.get_widget().show()
            if simulate_tools_palette:
                simulate_tools_palette.get_widget().show()

    def _on_tool_changed(self, tools_palette, tool_name, manager, drawing_area):
        """Handle tool selection change from edit tools palette.
        
        Args:
            tools_palette: EditToolsLoader instance that emitted the signal.
            tool_name: Name of the selected tool ('place', 'transition', 'arc') or empty string for none.
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
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
        drawing_area.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.KEY_PRESS_MASK)
        drawing_area.set_can_focus(True)
        drawing_area.connect('button-press-event', self._on_button_press, manager)
        drawing_area.connect('button-release-event', self._on_button_release, manager)
        drawing_area.connect('motion-notify-event', self._on_motion_notify, manager)
        drawing_area.connect('scroll-event', self._on_scroll_event, manager)
        drawing_area.connect('key-press-event', self._on_key_press_event, manager)
        if not hasattr(self, '_drag_state'):
            self._drag_state = {}
        self._drag_state[drawing_area] = {'active': False, 'button': 0, 'start_x': 0, 'start_y': 0, 'is_panning': False}
        if not hasattr(self, '_arc_state'):
            self._arc_state = {}
        self._arc_state[drawing_area] = {'source': None, 'cursor_pos': (0, 0)}
        if not hasattr(self, '_click_state'):
            self._click_state = {}
        self._click_state[drawing_area] = {'last_click_time': 0.0, 'last_click_obj': None, 'double_click_threshold': 0.3, 'pending_timeout': None, 'pending_click_data': None}
        self._setup_canvas_context_menu(drawing_area, manager)

    def _on_button_press(self, widget, event, manager):
        """Handle button press events (GTK3)."""
        state = self._drag_state[widget]
        arc_state = self._arc_state[widget]
        if event.button == 1 and manager.is_tool_active() and (manager.get_tool() == 'arc'):
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            clicked_obj = manager.find_object_at_position(world_x, world_y)
            if clicked_obj is None:
                if arc_state['source'] is not None:
                    arc_state['source'] = None
                    widget.queue_draw()
                return True
            if arc_state['source'] is None:
                if isinstance(clicked_obj, (Place, Transition)):
                    arc_state['source'] = clicked_obj
                    widget.queue_draw()
                return True
            else:
                target = clicked_obj
                source = arc_state['source']
                if target == source:
                    return True
                try:
                    arc = manager.add_arc(source, target)
                    widget.queue_draw()
                except ValueError as e:
                    pass  # Silently ignore arc creation errors
                finally:
                    arc_state['source'] = None
                    widget.queue_draw()
                return True
        if event.button == 1 and manager.is_tool_active():
            tool = manager.get_tool()
            if tool in ('place', 'transition'):
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                if tool == 'place':
                    place = manager.add_place(world_x, world_y)
                    widget.queue_draw()
                elif tool == 'transition':
                    transition = manager.add_transition(world_x, world_y)
                    widget.queue_draw()
                return True
        tool = manager.get_tool() if manager.is_tool_active() else None
        is_selection_mode = tool is None or tool == 'select'
        if event.button == 1 and is_selection_mode:
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            clicked_obj = manager.find_object_at_position(world_x, world_y)
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            if clicked_obj is not None:
                import time
                from gi.repository import GLib
                click_state = self._click_state[widget]
                current_time = time.time()
                time_since_last = current_time - click_state['last_click_time']
                is_double_click = time_since_last < click_state['double_click_threshold'] and click_state['last_click_obj'] == clicked_obj
                if click_state['pending_timeout'] is not None:
                    GLib.source_remove(click_state['pending_timeout'])
                    click_state['pending_timeout'] = None
                    click_state['pending_click_data'] = None
                if clicked_obj.selected and (not is_double_click):
                    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
                    state['active'] = True
                    state['button'] = event.button
                    state['start_x'] = event.x
                    state['start_y'] = event.y
                    state['is_panning'] = False
                    state['is_rect_selecting'] = False
                if is_double_click:
                    if clicked_obj.selected:
                        manager.selection_manager.enter_edit_mode(clicked_obj, manager=manager)
                    else:
                        manager.selection_manager.toggle_selection(clicked_obj, multi=is_ctrl, manager=manager)
                        manager.selection_manager.enter_edit_mode(clicked_obj, manager=manager)
                    click_state['last_click_time'] = 0.0
                    click_state['last_click_obj'] = None
                    widget.queue_draw()
                    return True
                else:
                    click_state['pending_click_data'] = {'obj': clicked_obj, 'is_ctrl': is_ctrl, 'widget': widget, 'manager': manager}

                    def process_single_click():
                        data = click_state['pending_click_data']
                        if data is None:
                            return False
                        obj = data['obj']
                        ctrl = data['is_ctrl']
                        w = data['widget']
                        mgr = data['manager']
                        if mgr.selection_manager.is_dragging():
                            click_state['pending_timeout'] = None
                            click_state['pending_click_data'] = None
                            return False
                        if mgr.selection_manager.is_edit_mode() and mgr.selection_manager.edit_target == obj:
                            click_state['pending_timeout'] = None
                            click_state['pending_click_data'] = None
                            return False
                        if mgr.selection_manager.is_edit_mode():
                            current_edit_target = mgr.selection_manager.edit_target
                            if current_edit_target != obj:
                                mgr.selection_manager.exit_edit_mode()
                        mgr.selection_manager.toggle_selection(obj, multi=ctrl, manager=mgr)
                        status = 'selected' if obj.selected else 'deselected'
                        multi_str = ' (multi)' if ctrl else ''
                        w.queue_draw()
                        click_state['pending_timeout'] = None
                        click_state['pending_click_data'] = None
                        return False
                    timeout_ms = int(click_state['double_click_threshold'] * 1000)
                    click_state['pending_timeout'] = GLib.timeout_add(timeout_ms, process_single_click)
                    click_state['last_click_time'] = current_time
                    click_state['last_click_obj'] = clicked_obj
                    return True
            else:
                manager.rectangle_selection.start(world_x, world_y)
                if manager.selection_manager.is_edit_mode():
                    manager.selection_manager.exit_edit_mode()
                state['active'] = True
                state['button'] = event.button
                state['start_x'] = event.x
                state['start_y'] = event.y
                state['is_panning'] = False
                state['is_rect_selecting'] = True
                if not is_ctrl:
                    manager.clear_all_selections()
                widget.grab_focus()
                return True
        state['active'] = True
        state['button'] = event.button
        state['start_x'] = event.x
        state['start_y'] = event.y
        state['start_pan_x'] = manager.pan_x
        state['start_pan_y'] = manager.pan_y
        state['is_panning'] = False
        state['is_rect_selecting'] = False
        widget.grab_focus()
        return True

    def _on_button_release(self, widget, event, manager):
        """Handle button release events (GTK3)."""
        state = self._drag_state[widget]
        if manager.selection_manager.end_drag():
            widget.queue_draw()
        if state.get('is_rect_selecting', False):
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            bounds = manager.rectangle_selection.finish()
            if bounds:
                count = manager.rectangle_selection.select_objects(manager, multi=is_ctrl)
                multi_str = ' (multi)' if is_ctrl else ''
            state['is_rect_selecting'] = False
            widget.queue_draw()
        if event.button == 3 and (not state['is_panning']):
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 5:
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                clicked_obj = manager.find_object_at_position(world_x, world_y)
                if clicked_obj:
                    self._show_object_context_menu(event.x, event.y, widget, manager, clicked_obj)
                else:
                    self._show_canvas_context_menu(event.x, event.y, widget)
        was_panning = state['is_panning']
        state['active'] = False
        state['button'] = 0
        state['is_panning'] = False
        if was_panning:
            manager.save_view_state_to_file()
        return True

    def _on_motion_notify(self, widget, event, manager):
        """Handle motion events (GTK3)."""
        state = self._drag_state[widget]
        arc_state = self._arc_state[widget]
        manager.set_pointer_position(event.x, event.y)
        world_x, world_y = manager.screen_to_world(event.x, event.y)
        arc_state['cursor_pos'] = (world_x, world_y)
        if manager.is_tool_active() and manager.get_tool() == 'arc' and (arc_state['source'] is not None):
            widget.queue_draw()
        if state['active'] and state['button'] > 0:
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            if not state['is_panning'] and (abs(dx) >= 5 or abs(dy) >= 5):
                state['is_panning'] = True
            if state.get('is_rect_selecting', False):
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                manager.rectangle_selection.update(world_x, world_y)
                widget.queue_draw()
                return True
            if manager.selection_manager.update_drag(event.x, event.y, manager):
                click_state = self._click_state.get(widget)
                if click_state and click_state.get('pending_timeout'):
                    from gi.repository import GLib
                    GLib.source_remove(click_state['pending_timeout'])
                    click_state['pending_timeout'] = None
                    click_state['pending_click_data'] = None
                widget.queue_draw()
                return True
            is_shift_pressed = event.state & Gdk.ModifierType.SHIFT_MASK
            should_pan = state['button'] in [2, 3] or (state['button'] == 1 and is_shift_pressed)
            if should_pan and state['is_panning']:
                dx = event.x - state['start_x']
                dy = event.y - state['start_y']
                manager.pan_x = state['start_pan_x'] + dx / manager.zoom
                manager.pan_y = state['start_pan_y'] + dy / manager.zoom
                manager.clamp_pan()
                manager._needs_redraw = True
                widget.queue_draw()
        return True

    def _on_scroll_event(self, widget, event, manager):
        """Handle scroll events for zoom (GTK3).
        
        Supports both discrete scroll wheels and smooth scrolling (trackpads).
        Zooms centered at cursor position (pointer-centered zoom).
        """
        direction = event.direction
        factor = None
        if direction == Gdk.ScrollDirection.SMOOTH:
            dy = event.delta_y
            if abs(dy) < 1e-06:
                return False
            factor = 1 / 1.1 if dy > 0 else 1.1
        elif direction == Gdk.ScrollDirection.UP:
            factor = 1.1
        elif direction == Gdk.ScrollDirection.DOWN:
            factor = 1 / 1.1
        if factor is None:
            return False
        manager.zoom_at_point(factor, event.x, event.y)
        manager.save_view_state_to_file()
        widget.queue_draw()
        return True

    def _on_key_press_event(self, widget, event, manager):
        """Handle key press events (GTK3)."""
        if event.keyval == Gdk.KEY_Escape:
            if manager.selection_manager.cancel_drag():
                widget.queue_draw()
                return True
            if manager.selection_manager.is_edit_mode():
                manager.selection_manager.exit_edit_mode()
                widget.queue_draw()
                return True
            if hasattr(self, '_canvas_context_menu') and self._canvas_context_menu:
                if isinstance(self._canvas_context_menu, Gtk.Menu):
                    self._canvas_context_menu.popdown()
                    return True
        return False

    def _on_draw(self, drawing_area, cr, width, height, manager):
        """Draw callback for the canvas.
        
        Uses Cairo transformation approach (legacy-compatible):
            pass
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
        if manager.viewport_width != width or manager.viewport_height != height:
            manager.set_viewport_size(width, height)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.paint()
        cr.save()
        cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
        cr.scale(manager.zoom, manager.zoom)
        manager.draw_grid(cr)
        
        # Render all objects
        all_objects = manager.get_all_objects()
        for obj in all_objects:
            obj.render(cr, zoom=manager.zoom)
        
        manager.editing_transforms.render_selection_layer(cr, manager, manager.zoom)
        manager.rectangle_selection.render(cr, manager.zoom)
        cr.restore()
        if drawing_area in self._arc_state:
            arc_state = self._arc_state[drawing_area]
            if manager.is_tool_active() and manager.get_tool() == 'arc' and (arc_state['source'] is not None):
                self._draw_arc_preview(cr, arc_state, manager)
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
        src_x, src_y = (source.x, source.y)
        dx = cursor_x - src_x
        dy = cursor_y - src_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return
        ux, uy = (dx / dist, dy / dist)
        if isinstance(source, Place):
            src_radius = source.radius
        elif isinstance(source, Transition):
            w = source.width if source.horizontal else source.height
            h = source.height if source.horizontal else source.width
            src_radius = max(w, h) / 2.0
        else:
            src_radius = 20.0
        start_x = src_x + ux * src_radius
        start_y = src_y + uy * src_radius
        start_sx, start_sy = manager.world_to_screen(start_x, start_y)
        end_sx, end_sy = manager.world_to_screen(cursor_x, cursor_y)
        cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
        cr.set_line_width(2.0)
        cr.move_to(start_sx, start_sy)
        cr.line_to(end_sx, end_sy)
        cr.stroke()
        arrow_len = 11.0
        arrow_width = 6.0
        angle = math.atan2(dy, dx)
        left_x = end_sx - arrow_len * math.cos(angle) + arrow_width * math.sin(angle)
        left_y = end_sy - arrow_len * math.sin(angle) - arrow_width * math.cos(angle)
        right_x = end_sx - arrow_len * math.cos(angle) - arrow_width * math.sin(angle)
        right_y = end_sy - arrow_len * math.sin(angle) + arrow_width * math.cos(angle)
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
        if hasattr(self, 'canvas_context_menus'):
            menu = self.canvas_context_menus.get(drawing_area)
            if menu:
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
        menu = Gtk.Menu()
        if isinstance(obj, Place):
            obj_type = 'Place'
        elif isinstance(obj, Transition):
            obj_type = 'Transition'
        elif isinstance(obj, Arc):
            obj_type = 'Arc'
        else:
            obj_type = 'Object'
        title_item = Gtk.MenuItem(label=f'{obj_type}: {obj.name}')
        title_item.set_sensitive(False)
        title_item.show()
        menu.append(title_item)
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        menu.append(separator)
        menu_items = [('Edit Properties...', lambda: self._on_object_properties(obj, manager, drawing_area)), ('Edit Mode (Double-click)', lambda: self._on_object_edit_mode(obj, manager, drawing_area)), None, ('Delete', lambda: self._on_object_delete(obj, manager, drawing_area))]
        if isinstance(obj, Transition):
            type_submenu_item = Gtk.MenuItem(label='Change Type ►')
            type_submenu = Gtk.Menu()
            current_type = getattr(obj, 'transition_type', 'immediate')
            transition_types = [('immediate', 'Immediate (zero delay)'), ('timed', 'Timed (TPN)'), ('stochastic', 'Stochastic (GSPN)'), ('continuous', 'Continuous (SHPN)')]
            for type_value, type_label in transition_types:
                if type_value == current_type:
                    label = f'✓ {type_label}'
                else:
                    label = f'   {type_label}'
                type_item = Gtk.MenuItem(label=label)
                type_item.connect('activate', lambda w, t=type_value: self._on_transition_type_change(obj, t, manager, drawing_area))
                type_item.show()
                type_submenu.append(type_item)
            type_submenu_item.set_submenu(type_submenu)
            type_submenu_item.show()
            menu_items.insert(2, ('__SUBMENU__', type_submenu_item))
        if isinstance(obj, Arc):
            # Add arc transformation submenu
            from shypn.utils.arc_transform import is_straight, is_curved, is_inhibitor, is_normal
            
            transform_submenu_item = Gtk.MenuItem(label='Transform Arc ►')
            transform_submenu = Gtk.Menu()
            
            # Curve/Straight options
            if is_straight(obj):
                curve_item = Gtk.MenuItem(label='Make Curved')
                curve_item.connect('activate', lambda w: self._on_arc_make_curved(obj, manager, drawing_area))
            else:
                curve_item = Gtk.MenuItem(label='Make Straight')
                curve_item.connect('activate', lambda w: self._on_arc_make_straight(obj, manager, drawing_area))
            curve_item.show()
            transform_submenu.append(curve_item)
            
            # Normal/Inhibitor options
            if is_normal(obj):
                inhibitor_item = Gtk.MenuItem(label='Convert to Inhibitor Arc')
                inhibitor_item.connect('activate', lambda w: self._on_arc_convert_to_inhibitor(obj, manager, drawing_area))
            else:
                inhibitor_item = Gtk.MenuItem(label='Convert to Normal Arc')
                inhibitor_item.connect('activate', lambda w: self._on_arc_convert_to_normal(obj, manager, drawing_area))
            inhibitor_item.show()
            transform_submenu.append(inhibitor_item)
            
            transform_submenu_item.set_submenu(transform_submenu)
            transform_submenu_item.show()
            menu_items.insert(2, ('__SUBMENU__', transform_submenu_item))
            
            # Add weight editing option
            menu_items.insert(3, ('Edit Weight...', lambda: self._on_arc_edit_weight(obj, manager, drawing_area)))
        for item_data in menu_items:
            if item_data is None:
                menu_item = Gtk.SeparatorMenuItem()
            elif item_data[0] == '__SUBMENU__':
                menu_item = item_data[1]
            else:
                label, callback = item_data
                menu_item = Gtk.MenuItem(label=label)

                def on_activate(widget, cb):
                    cb()
                menu_item.connect('activate', on_activate, callback)
            menu_item.show()
            menu.append(menu_item)
        if self.context_menu_handler:
            self.context_menu_handler.add_analysis_menu_items(menu, obj)
        menu.popup(None, None, None, None, 3, Gtk.get_current_event_time())

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
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                child = scrolled.get_child()
                if hasattr(child, 'get_child'):
                    child = child.get_child()
                if isinstance(child, Gtk.DrawingArea):
                    return child
        elif isinstance(page, Gtk.ScrolledWindow):
            child = page.get_child()
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

    def set_persistency_manager(self, persistency):
        """Set the persistency manager for file operations integration.
        
        This allows canvas operations (like clear canvas) to properly reset
        the persistency state when creating a new document.
        
        Args:
            persistency: NetObjPersistency instance from main application
        """
        self.persistency = persistency

    def set_right_panel_loader(self, right_panel_loader):
        """Set the right panel loader for data collector updates.
        
        This allows the notebook to update the right panel's data collector
        when the user switches between tabs with different simulations.
        
        Args:
            right_panel_loader: RightPanelLoader instance from main application
        """
        self.right_panel_loader = right_panel_loader
        if self.notebook and self.notebook.get_n_pages() > 0:
            current_page_num = self.notebook.get_current_page()
            current_page = self.notebook.get_nth_page(current_page_num)
            self._on_notebook_page_changed(self.notebook, current_page, current_page_num)

    def set_context_menu_handler(self, handler):
        """Set the context menu handler for adding analysis menu items.
        
        This allows canvas object context menus to include "Add to Analysis" options.
        
        Args:
            handler: ContextMenuHandler instance
        """
        self.context_menu_handler = handler

    def _setup_canvas_context_menu(self, drawing_area, manager):
        """Setup context menu for canvas operations using Gtk.Menu.
        
        Args:
            drawing_area: GtkDrawingArea widget.
            manager: ModelCanvasManager instance.
        """
        menu = Gtk.Menu()
        menu_items = [('Reset Zoom (100%)', lambda: self._on_reset_zoom_clicked(menu, drawing_area, manager)), ('Zoom In', lambda: self._on_zoom_in_clicked(menu, drawing_area, manager)), ('Zoom Out', lambda: self._on_zoom_out_clicked(menu, drawing_area, manager)), ('Fit to Window', lambda: self._on_fit_to_window_clicked(menu, drawing_area, manager)), None, ('Grid: Line Style', lambda: self._on_grid_line_clicked(menu, drawing_area, manager)), ('Grid: Dot Style', lambda: self._on_grid_dot_clicked(menu, drawing_area, manager)), ('Grid: Cross Style', lambda: self._on_grid_cross_clicked(menu, drawing_area, manager)), None, ('Center View', lambda: self._on_center_view_clicked(menu, drawing_area, manager)), ('Clear Canvas', lambda: self._on_clear_canvas_clicked(menu, drawing_area, manager))]
        for item_data in menu_items:
            if item_data is None:
                menu_item = Gtk.SeparatorMenuItem()
            else:
                label, callback = item_data
                menu_item = Gtk.MenuItem(label=label)
                menu_item.connect('activate', lambda w, cb=callback: cb())
            menu_item.show()
            menu.append(menu_item)
        self._canvas_context_menu = menu
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
        zoom_x = manager.viewport_width / manager.canvas_width
        zoom_y = manager.viewport_height / manager.canvas_height
        fit_zoom = min(zoom_x, zoom_y) * 0.95
        manager.set_zoom(fit_zoom, manager.viewport_width / 2, manager.viewport_height / 2)
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
        """Clear the canvas and reset to default state.
        
        This removes all objects and resets the document to "default" filename
        state (unsaved), as if creating a new document. Also resets the
        persistency manager so the next save will prompt for a new filename.
        """
        if self.persistency:
            if not self.persistency.check_unsaved_changes():
                return
            self.persistency.new_document()
        manager.clear_all_objects()
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

    def _on_object_delete(self, obj, manager, drawing_area):
        """Delete an object from the canvas.
        
        Args:
            obj: Object to delete (Place, Transition, or Arc)
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Place, Transition, Arc
        if isinstance(obj, Place):
            if obj in manager.places:
                manager.places.remove(obj)
        elif isinstance(obj, Transition):
            if obj in manager.transitions:
                manager.transitions.remove(obj)
        elif isinstance(obj, Arc):
            if obj in manager.arcs:
                manager.arcs.remove(obj)
        if obj.selected:
            manager.selection_manager.deselect(obj)
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
        if not obj.selected:
            manager.selection_manager.select(obj, multi=False, manager=manager)
        manager.selection_manager.enter_edit_mode(obj, manager=manager)
        drawing_area.queue_draw()

    def _on_object_properties(self, obj, manager, drawing_area):
        """Open properties dialog for an object.
        
        Args:
            obj: Object to edit properties for
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Place, Transition, Arc
        from shypn.helpers.place_prop_dialog_loader import create_place_prop_dialog
        from shypn.helpers.transition_prop_dialog_loader import create_transition_prop_dialog
        from shypn.helpers.arc_prop_dialog_loader import create_arc_prop_dialog
        dialog_loader = None
        if isinstance(obj, Place):
            dialog_loader = create_place_prop_dialog(obj, parent_window=self.parent_window, persistency_manager=self.persistency)
        elif isinstance(obj, Transition):
            data_collector = None
            if drawing_area in self.simulate_tools_palettes:
                simulate_tools = self.simulate_tools_palettes[drawing_area]
                if hasattr(simulate_tools, 'data_collector'):
                    data_collector = simulate_tools.data_collector
            dialog_loader = create_transition_prop_dialog(obj, parent_window=self.parent_window, persistency_manager=self.persistency, model=manager, data_collector=data_collector)
        elif isinstance(obj, Arc):
            dialog_loader = create_arc_prop_dialog(obj, parent_window=self.parent_window, persistency_manager=self.persistency)
        else:
            return
        if isinstance(obj, Arc):

            pass

        def on_properties_changed(_):
            if isinstance(obj, Arc):
                pass
            drawing_area.queue_draw()
            if isinstance(obj, Transition) and drawing_area in self.simulate_tools_palettes:
                simulate_tools = self.simulate_tools_palettes[drawing_area]
                if simulate_tools.simulation:
                    if obj.id in simulate_tools.simulation.behavior_cache:
                        del simulate_tools.simulation.behavior_cache[obj.id]
            if isinstance(obj, (Place, Transition)) and self.right_panel_loader:
                if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
                    if isinstance(obj, Place):
                        if obj in self.right_panel_loader.place_panel.selected_objects:
                            self.right_panel_loader.place_panel.needs_update = True
                if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                    if isinstance(obj, Transition):
                        if obj in self.right_panel_loader.transition_panel.selected_objects:
                            self.right_panel_loader.transition_panel.needs_update = True
        dialog_loader.connect('properties-changed', on_properties_changed)
        response = dialog_loader.run()
        if isinstance(obj, Arc):
            pass
        if response == Gtk.ResponseType.OK:
            drawing_area.queue_draw()

    def _on_transition_type_change(self, transition, new_type, manager, drawing_area):
        """Handle transition type change from context menu.
        
        Args:
            transition: Transition object
            new_type: New transition type ('immediate', 'timed', 'stochastic', 'continuous')
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Transition
        old_type = getattr(transition, 'transition_type', 'immediate')
        if old_type == new_type:
            return
        transition.transition_type = new_type
        if self.persistency:
            self.persistency.mark_dirty()
        if drawing_area in self.simulate_tools_palettes:
            simulate_tools = self.simulate_tools_palettes[drawing_area]
            if simulate_tools.simulation:
                if transition.id in simulate_tools.simulation.behavior_cache:
                    del simulate_tools.simulation.behavior_cache[transition.id]
        if self.right_panel_loader:
            if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                if transition in self.right_panel_loader.transition_panel.selected_objects:
                    self.right_panel_loader.transition_panel.needs_update = True
        drawing_area.queue_draw()

    def _on_arc_edit_weight(self, arc, manager, drawing_area):
        """Quick edit arc weight.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        dialog = Gtk.Dialog(title=f'Edit {arc.name} Weight', parent=self.parent_window, flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_border_width(10)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label = Gtk.Label(label='Weight:')
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
                manager.mark_modified()
                drawing_area.queue_draw()
        dialog.destroy()

    def _on_arc_make_curved(self, arc, manager, drawing_area):
        """Transform arc to curved.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import make_curved
        
        new_arc = make_curved(arc)
        manager.replace_arc(arc, new_arc)
        drawing_area.queue_draw()

    def _on_arc_make_straight(self, arc, manager, drawing_area):
        """Transform arc to straight.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import make_straight
        
        new_arc = make_straight(arc)
        manager.replace_arc(arc, new_arc)
        drawing_area.queue_draw()

    def _on_arc_convert_to_inhibitor(self, arc, manager, drawing_area):
        """Convert arc to inhibitor type.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import convert_to_inhibitor
        
        
        try:
            new_arc = convert_to_inhibitor(arc)
            manager.replace_arc(arc, new_arc)
            drawing_area.queue_draw()
        except ValueError as e:
            # Invalid transformation (e.g., Transition → Place)
            self._show_error_dialog(str(e))
            return

    def _on_arc_convert_to_normal(self, arc, manager, drawing_area):
        """Convert arc to normal type.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import convert_to_normal
        
        new_arc = convert_to_normal(arc)
        manager.replace_arc(arc, new_arc)
        drawing_area.queue_draw()
    
    def _show_error_dialog(self, message):
        """Show an error dialog to the user.
        
        Args:
            message: Error message to display
        """
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Invalid Operation"
        )
        dialog.format_secondary_text(message)
        dialog.run()
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