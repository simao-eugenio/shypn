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
    from shypn.canvas import CanvasOverlayManager
except ImportError as e:
    print(f'ERROR: Cannot import CanvasOverlayManager: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.edit.palette_manager import PaletteManager
    from shypn.edit.tools_palette_new import ToolsPalette
    from shypn.edit.operations_palette_new import OperationsPalette
    # SwissKnifePalette - unified palette replacing ToolsPalette + OperationsPalette
    from shypn.helpers.swissknife_palette import SwissKnifePalette
    from shypn.helpers.swissknife_tool_registry import ToolRegistry
except ImportError as e:
    print(f'ERROR: Cannot import new OOP palettes: {e}', file=sys.stderr)
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
        self.overlay_managers = {}  # Replaces individual palette dictionaries
        self.palette_managers = {}  # New OOP palette managers
        self.parent_window = None
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
            # Get simulate_tools_palette from overlay manager
            if drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                simulate_tools_palette = overlay_manager.get_palette('simulate_tools')
                if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
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
        if drawing_area and drawing_area in self.overlay_managers:
            # Cleanup overlay manager and all its palettes
            overlay_manager = self.overlay_managers[drawing_area]
            overlay_manager.cleanup_overlays()
            del self.overlay_managers[drawing_area]
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
        
        # Setup overlay manager to handle all palettes
        if overlay_box and overlay_widget:
            overlay_manager = CanvasOverlayManager(
                overlay_widget=overlay_widget,
                overlay_box=overlay_box,
                drawing_area=drawing_area,
                canvas_manager=manager
            )
            overlay_manager.setup_overlays(parent_window=self.parent_window)
            
            # Store overlay manager for later access
            self.overlay_managers[drawing_area] = overlay_manager
            
            # Connect signals from palettes
            overlay_manager.connect_tool_changed_signal(
                self._on_tool_changed, manager, drawing_area
            )
            overlay_manager.connect_simulation_signals(
                self._on_simulation_step, self._on_simulation_reset, drawing_area
            )
            overlay_manager.connect_mode_changed_signal(
                self._on_mode_changed, drawing_area
            )
            # Old signal removed - mode palette no longer has edit-palettes-toggled
            # overlay_manager.connect_edit_palettes_toggle_signal(
            #     self._on_edit_palettes_toggled, drawing_area
            # )
            overlay_manager.connect_edit_button_signal(
                self._on_edit_button_toggled, drawing_area
            )
            
            # Set initial state: Edit mode is default
            # Old [E] and [S] buttons no longer exist - removed, replaced by SwissKnifePalette
            
            # Setup new OOP palette system
            self._setup_edit_palettes(overlay_widget, manager, drawing_area, overlay_manager)

    def _setup_edit_palettes(self, overlay_widget, canvas_manager, drawing_area, overlay_manager):
        """Setup new OOP palette system with SwissKnifePalette.
        
        SwissKnifePalette replaces the old ToolsPalette + OperationsPalette + [E] button.
        
        Args:
            overlay_widget: GtkOverlay to attach palettes to.
            canvas_manager: ModelCanvasManager instance for this canvas.
            drawing_area: GtkDrawingArea widget.
            overlay_manager: CanvasOverlayManager instance.
        """
        # Old [E] button reference no longer needed - SwissKnifePalette is self-contained
        
        # Create palette manager (kept for backward compatibility with old code)
        palette_manager = PaletteManager(overlay_widget, reference_widget=None)
        self.palette_managers[drawing_area] = palette_manager
        
        # [E] button is at bottom-center: margin_bottom=24, height=36
        # Palettes should be centered horizontally, ~18px above edit palette container
        # Edit palette (refactored with [ ][E][ ] layout):
        #   - margin_bottom: 12px (changed from 24px)
        #   - container width: ~100px (3 buttons @ 28px + spacing + padding + border)
        #   - container height: ~38px (border + padding + button + padding + border)
        #   - halign: center (follows window center automatically)
        #   - top from bottom: 12 + 38 = 50px
        # Palette bottom should be at: 50 + 18 = 68px from bottom
        
        # Virtual palette positioning strategy:
        # Use CENTER alignment instead of FILL with fixed margins
        # This makes palettes follow the window center automatically on resize
        #
        # Tools palette (148px wide):
        #   - halign: CENTER
        #   - margin_end: (194 + 80) = 274px (operations width + gap)
        #   - Effect: Positioned to the left of center by 274px
        #
        # Operations palette (194px wide):
        #   - halign: CENTER
        #   - margin_start: (148 + 80) = 228px (tools width + gap)
        #   - Effect: Positioned to the right of center by 228px
        #
        # Gap between them: 80px (centered on the window)
        # Total virtual palette width: 148 + 80 + 194 = 422px
        # This configuration keeps palettes centered above [E] button on any window size!
        
        # ============================================================
        # SWISSKNIFE PALETTE - Unified Edit/Simulate/Layout palette
        # ============================================================
        # Replaces old ToolsPalette + OperationsPalette
        # Features:
        #   - Edit category: P/T/A/S/L tools
        #   - Simulate category: Widget palette (SimulateToolsPaletteLoader)
        #   - Layout category: Auto/Hier/Force tools
        #   - Sub-palettes reveal upward with 600ms animations
        #   - Dark blue-gray theme matching application style
        
        # Create tool registry
        tool_registry = ToolRegistry()
        
        # Create SwissKnifePalette in edit mode
        # NOTE: canvas_manager IS the model (has places, transitions, arcs attributes)
        swissknife_palette = SwissKnifePalette(
            mode='edit',
            model=canvas_manager,  # canvas_manager itself is the Petri net model
            tool_registry=tool_registry
        )
        
        # Get palette widget and position it
        swissknife_widget = swissknife_palette.get_widget()
        swissknife_widget.set_halign(Gtk.Align.CENTER)
        swissknife_widget.set_valign(Gtk.Align.END)
        swissknife_widget.set_margin_bottom(20)  # 20px from bottom
        swissknife_widget.set_hexpand(False)
        
        # Add to overlay
        overlay_widget.add_overlay(swissknife_widget)
        
        # Wire SwissKnifePalette signals
        swissknife_palette.connect('tool-activated', self._on_swissknife_tool_activated, canvas_manager, drawing_area)
        swissknife_palette.connect('mode-change-requested', self._on_swissknife_mode_change_requested, canvas_manager, drawing_area)
        swissknife_palette.connect('simulation-step-executed', self._on_simulation_step, drawing_area)
        swissknife_palette.connect('simulation-reset-executed', self._on_simulation_reset, drawing_area)
        swissknife_palette.connect('simulation-settings-changed', self._on_simulation_settings_changed, drawing_area)
        
        # Store reference for mode switching
        if drawing_area not in self.overlay_managers:
            self.overlay_managers[drawing_area] = type('obj', (object,), {})()
        self.overlay_managers[drawing_area].swissknife_palette = swissknife_palette
        
        # ============================================================
        # OLD PALETTE CODE - Keeping temporarily for reference
        # ============================================================
        # Create and register tools palette
        tools_palette = ToolsPalette()
        palette_manager.register_palette(
            tools_palette,
            position=(Gtk.Align.CENTER, Gtk.Align.END)  # Changed to CENTER alignment
        )
        # Set margins for positioning relative to center
        tools_revealer = tools_palette.get_widget()
        tools_revealer.set_margin_bottom(68)   # 18px above edit palette (50 + 18)
        tools_revealer.set_margin_end(194 + 80)  # Offset left: operations width + gap
        tools_revealer.set_hexpand(False)      # Don't expand horizontally
        tools_revealer.hide()  # Hide old palette
        
        # Create and register operations palette
        operations_palette = OperationsPalette()
        palette_manager.register_palette(
            operations_palette,
            position=(Gtk.Align.CENTER, Gtk.Align.END)  # Changed to CENTER alignment
        )
        # Set margins for positioning relative to center
        operations_revealer = operations_palette.get_widget()
        operations_revealer.set_margin_bottom(68)  # Same vertical position (50 + 18)
        operations_revealer.set_margin_start(148 + 80)  # Offset right: tools width + gap
        operations_revealer.set_hexpand(False)     # Don't expand horizontally
        operations_revealer.hide()  # Hide old palette
        
        # Wire old palette signals (keeping for backward compatibility during transition)
        tools_palette.connect('tool-selected', self._on_palette_tool_selected, canvas_manager, drawing_area)
        operations_palette.connect('operation-triggered', self._on_palette_operation_triggered, canvas_manager, drawing_area)
        
        # Wire undo/redo button state updates
        if hasattr(canvas_manager, 'undo_manager'):
            def update_undo_redo_buttons(can_undo, can_redo):
                operations_palette.update_undo_redo_state(can_undo, can_redo)
            canvas_manager.undo_manager.set_state_changed_callback(update_undo_redo_buttons)
            # Initialize button states
            initial_undo = canvas_manager.undo_manager.can_undo()
            initial_redo = canvas_manager.undo_manager.can_redo()
            update_undo_redo_buttons(initial_undo, initial_redo)
        
        # Ensure overlay and all children are visible
        overlay_widget.show_all()
        
        # IMPORTANT: hide [S] button AFTER show_all() (which makes everything visible)
        # This must be done after show_all() because show_all() recursively shows all children
        if drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            if overlay_manager.simulate_palette:
                sim_widget = overlay_manager.simulate_palette.get_widget()
                if sim_widget:
                    sim_widget.hide()
        
        # DON'T show palettes initially - they should only appear in edit mode
        # palette_manager.show_all()  # Removed - mode change handler will show them
    
    def _on_palette_tool_selected(self, tools_palette, tool_name, canvas_manager, drawing_area):
        """Handle tool selection from new OOP tools palette.
        
        Args:
            tools_palette: ToolsPalette instance.
            tool_name: Name of selected tool ('place', 'transition', 'arc', 'select').
            canvas_manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        if tool_name == 'select':
            canvas_manager.clear_tool()
        else:
            canvas_manager.set_tool(tool_name)
        drawing_area.queue_draw()
    
    def _on_palette_operation_triggered(self, operations_palette, operation, canvas_manager, drawing_area):
        """Handle operation trigger from new OOP operations palette.
        
        Args:
            operations_palette: OperationsPalette instance.
            operation: Operation name ('select', 'lasso', 'undo', 'redo').
            canvas_manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        if operation == 'select':
            canvas_manager.clear_tool()
            drawing_area.queue_draw()
        elif operation == 'lasso':
            # Import LassoSelector
            from shypn.edit.lasso_selector import LassoSelector
            
            # Get or create lasso state
            if drawing_area not in self._lasso_state:
                self._lasso_state[drawing_area] = {
                    'active': False,
                    'selector': None
                }
            
            lasso_state = self._lasso_state[drawing_area]
            
            # Create LassoSelector instance if needed
            if lasso_state['selector'] is None:
                lasso_state['selector'] = LassoSelector(canvas_manager)
            
            # Activate lasso mode
            lasso_state['active'] = True
            canvas_manager.clear_tool()  # Deactivate other tools
            
            drawing_area.queue_draw()
        elif operation == 'undo':
            if hasattr(canvas_manager, 'undo_manager') and canvas_manager.undo_manager:
                if canvas_manager.undo_manager.undo(canvas_manager):
                    drawing_area.queue_draw()
        elif operation == 'redo':
            if hasattr(canvas_manager, 'undo_manager') and canvas_manager.undo_manager:
                if canvas_manager.undo_manager.redo(canvas_manager):
                    drawing_area.queue_draw()

    # ============================================================
    # SWISSKNIFE PALETTE SIGNAL HANDLERS - Unified handlers
    # ============================================================
    
    def _on_swissknife_tool_activated(self, palette, tool_id, canvas_manager, drawing_area):
        """Handle tool activation from SwissKnifePalette.
        
        Unified handler for all tool types from SwissKnifePalette:
        - Drawing tools: place, transition, arc
        - Selection tools: select, lasso
        - Layout tools: layout_auto, layout_hierarchical, layout_force
        
        This replaces the old _on_palette_tool_selected and _on_palette_operation_triggered handlers.
        
        Args:
            palette: SwissKnifePalette instance
            tool_id: Tool identifier string
            canvas_manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Update tool visual feedback
        if hasattr(palette, 'tool_registry'):
            palette.tool_registry.set_active_tool(tool_id)
        
        # Set cursor based on tool
        window = drawing_area.get_window()
        if window:
            display = drawing_area.get_display()
            cursor = None
            
            if tool_id == 'place':
                cursor = Gdk.Cursor.new_from_name(display, 'crosshair')
            elif tool_id == 'transition':
                cursor = Gdk.Cursor.new_from_name(display, 'crosshair')
            elif tool_id == 'arc':
                cursor = Gdk.Cursor.new_from_name(display, 'cell')
            elif tool_id == 'select':
                cursor = Gdk.Cursor.new_from_name(display, 'default')
            elif tool_id == 'lasso':
                cursor = Gdk.Cursor.new_from_name(display, 'hand1')
            elif tool_id.startswith('layout_'):
                cursor = Gdk.Cursor.new_from_name(display, 'default')
            
            window.set_cursor(cursor)
        
        # Drawing tools (place, transition, arc)
        if tool_id in ('place', 'transition', 'arc'):
            canvas_manager.set_tool(tool_id)
            drawing_area.queue_draw()
        
        # Selection tools
        elif tool_id == 'select':
            canvas_manager.clear_tool()
            drawing_area.queue_draw()
        
        elif tool_id == 'lasso':
            # Lasso selection logic (copied from old _on_palette_operation_triggered)
            from shypn.edit.lasso_selector import LassoSelector
            
            # Get or create lasso state
            if drawing_area not in self._lasso_state:
                self._lasso_state[drawing_area] = {
                    'active': False,
                    'selector': None
                }
            
            lasso_state = self._lasso_state[drawing_area]
            
            # Create LassoSelector instance if needed
            if lasso_state['selector'] is None:
                lasso_state['selector'] = LassoSelector(canvas_manager)
            
            # Activate lasso mode
            lasso_state['active'] = True
            canvas_manager.clear_tool()  # Deactivate other tools
            
            drawing_area.queue_draw()
        
        # Layout tools - call existing layout methods
        elif tool_id == 'layout_auto':
            print(f"[SwissKnife] Auto layout requested")
            self._on_layout_auto_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_hierarchical':
            print(f"[SwissKnife] Hierarchical layout requested")
            self._on_layout_hierarchical_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_force':
            print(f"[SwissKnife] Force-directed layout requested")
            self._on_layout_force_clicked(None, drawing_area, canvas_manager)
        
        else:
            print(f"[SwissKnife] Unknown tool: {tool_id}")
    
    def _on_swissknife_mode_change_requested(self, palette, requested_mode, canvas_manager, drawing_area):
        """Handle mode change request from SwissKnifePalette.
        
        Called when user clicks category buttons that trigger mode changes.
        Currently, Edit/Simulate/Layout are all in 'edit' mode, so this may not
        trigger until modes are separated in future.
        
        Args:
            palette: SwissKnifePalette instance
            requested_mode: 'edit' or 'simulate'
            canvas_manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        print(f"[SwissKnife] Mode change requested: {requested_mode}")
        # TODO: Implement mode switching logic when needed
        # current_mode = self._get_current_mode(drawing_area)
        # if requested_mode != current_mode:
        #     self._switch_canvas_mode(drawing_area, requested_mode)

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

    def _on_simulation_settings_changed(self, palette, drawing_area):
        """Handle simulation settings change.
        
        Args:
            palette: SimulateToolsPaletteLoader that emitted the signal
            drawing_area: GtkDrawingArea widget
        """
        # Settings changed - may need to update visualization
        # Currently just redraw the canvas
        drawing_area.queue_draw()

    def _on_mode_changed(self, mode_palette, mode, drawing_area, *args):
        """Handle mode change between edit and simulation.
        
        Args:
            mode_palette: ModePaletteLoader that emitted the signal
            mode: New mode ('edit' or 'sim')
            drawing_area: GtkDrawingArea widget
            *args: Additional arguments from signal (edit_palette, etc. - ignored)
        """
        # Show/hide [E] and [S] buttons based on mode
        if drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            
            if mode == 'edit':
                # Switching to EDIT mode:
                # 1. Show [E] button, hide [S] button
                if overlay_manager.edit_palette:
                    edit_widget = overlay_manager.edit_palette.get_widget()
                    if edit_widget:
                        edit_widget.show()
                        # Reset [E] button to OFF state (edit tools hidden)
                        if overlay_manager.edit_palette.edit_toggle_button:
                            if overlay_manager.edit_palette.edit_toggle_button.get_active():
                                overlay_manager.edit_palette.edit_toggle_button.set_active(False)
                if overlay_manager.simulate_palette:
                    sim_widget = overlay_manager.simulate_palette.get_widget()
                    if sim_widget:
                        sim_widget.hide()
                        # Reset [S] button to OFF state when hiding it
                        sim_button = overlay_manager.simulate_palette.get_toggle_button()
                        if sim_button and sim_button.get_active():
                            sim_button.set_active(False)
                
                # 2. Hide any open simulation tools palette
                if overlay_manager.simulate_tools_palette:
                    overlay_manager.simulate_tools_palette.hide()  # Use palette's hide() method
                
                # 3. Hide any open edit tools palettes (ensure clean state)
                if drawing_area in self.palette_managers:
                    palette_manager = self.palette_managers[drawing_area]
                    palette_manager.hide_all()
                
                
            elif mode == 'sim':
                # Switching to SIM mode:
                # 1. Hide [E] button, show [S] button
                if overlay_manager.edit_palette:
                    edit_widget = overlay_manager.edit_palette.get_widget()
                    if edit_widget:
                        edit_widget.hide()
                if overlay_manager.simulate_palette:
                    sim_widget = overlay_manager.simulate_palette.get_widget()
                    if sim_widget:
                        sim_widget.show()
                        # Reset [S] button to OFF state (simulation tools hidden)
                        sim_button = overlay_manager.simulate_palette.get_toggle_button()
                        if sim_button and sim_button.get_active():
                            sim_button.set_active(False)
                
                # 2. Hide any open edit palettes
                if drawing_area in self.palette_managers:
                    palette_manager = self.palette_managers[drawing_area]
                    palette_manager.hide_all()
                
    
    def _on_edit_button_toggled(self, edit_palette, show, drawing_area):
        """Handle [E] button toggle for showing/hiding NEW OOP edit palettes.
        
        Args:
            edit_palette: EditPaletteLoader that emitted the signal
            show: True to show palettes, False to hide
            drawing_area: GtkDrawingArea widget
        """
        if drawing_area in self.palette_managers:
            palette_manager = self.palette_managers[drawing_area]
            if show:
                palette_manager.show_all()
            else:
                palette_manager.hide_all()

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
        self._drag_state[drawing_area] = {'active': False, 'button': 0, 'start_x': 0, 'start_y': 0, 'is_panning': False, 'is_rect_selecting': False, 'is_transforming': False}
        if not hasattr(self, '_arc_state'):
            self._arc_state = {}
        self._arc_state[drawing_area] = {'source': None, 'cursor_pos': (0, 0), 'target_valid': None, 'hovered_target': None, 'ignore_next_release': False}
        if not hasattr(self, '_click_state'):
            self._click_state = {}
        self._click_state[drawing_area] = {'last_click_time': 0.0, 'last_click_obj': None, 'double_click_threshold': 0.3, 'pending_timeout': None, 'pending_click_data': None}
        if not hasattr(self, '_lasso_state'):
            self._lasso_state = {}
        self._lasso_state[drawing_area] = {'active': False, 'selector': None}
        self._setup_canvas_context_menu(drawing_area, manager)

    def _on_button_press(self, widget, event, manager):
        """Handle button press events (GTK3)."""
        state = self._drag_state[widget]
        arc_state = self._arc_state[widget]
        lasso_state = self._lasso_state.get(widget, {})
        
        # Check if lasso mode is active
        if lasso_state.get('active', False) and event.button == 1:
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            lasso_state['selector'].start_lasso(world_x, world_y)
            widget.queue_draw()
            return True
        
        # Check if we should ignore this click (after dialog close)
        if arc_state.get('ignore_next_release', False):
            arc_state['ignore_next_release'] = False
            return True  # Consume the event without doing anything
        
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
                    # Show error dialog instead of silent failure
                    dialog = Gtk.MessageDialog(
                        transient_for=self.parent_window,
                        flags=0,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Cannot Create Arc"
                    )
                    dialog.format_secondary_text(str(e))
                    dialog.run()
                    dialog.destroy()
                finally:
                    arc_state['source'] = None
                    arc_state['target_valid'] = None
                    arc_state['hovered_target'] = None
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
            
            # Check if clicking on a transform handle in edit mode
            if manager.selection_manager.is_edit_mode():
                edit_target = manager.selection_manager.get_edit_target()
                if edit_target:
                    handle = manager.editing_transforms.check_handle_at_position(
                        edit_target, world_x, world_y, manager.zoom
                    )
                    
                    if handle:
                        # Start transformation instead of normal drag
                        if manager.editing_transforms.start_transformation(
                            edit_target, handle, world_x, world_y
                        ):
                            state['active'] = True
                            state['button'] = event.button
                            state['start_x'] = event.x
                            state['start_y'] = event.y
                            state['is_panning'] = False
                            state['is_rect_selecting'] = False
                            state['is_transforming'] = True
                            widget.queue_draw()
                            return True
            
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
                    # Already selected - start drag immediately
                    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
                    state['active'] = True
                    state['button'] = event.button
                    state['start_x'] = event.x
                    state['start_y'] = event.y
                    state['is_panning'] = False
                    state['is_rect_selecting'] = False
                elif not is_double_click:
                    # Not selected yet - select immediately and start drag
                    # This makes dragging feel more responsive
                    if not is_ctrl:
                        manager.clear_all_selections()
                    clicked_obj.selected = True
                    manager.selection_manager.select(clicked_obj, multi=is_ctrl, manager=manager)
                    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
                    state['active'] = True
                    state['button'] = event.button
                    state['start_x'] = event.x
                    state['start_y'] = event.y
                    state['is_panning'] = False
                    state['is_rect_selecting'] = False
                    widget.queue_draw()
                    # Record for double-click detection
                    click_state['last_click_time'] = current_time
                    click_state['last_click_obj'] = clicked_obj
                    return True
                if is_double_click:
                    # Check if this is an arc with parallel arcs (legacy parallel arc system)
                    from shypn.netobjs import Arc
                    is_parallel_arc = False
                    if isinstance(clicked_obj, Arc):
                        parallels = manager.detect_parallel_arcs(clicked_obj)
                        is_parallel_arc = len(parallels) > 0
                    
                    # Prevent double-click edit mode for parallel arcs
                    if is_parallel_arc:
                        # Just select the arc, don't enter edit mode
                        if not clicked_obj.selected:
                            manager.selection_manager.toggle_selection(clicked_obj, multi=is_ctrl, manager=manager)
                        click_state['last_click_time'] = 0.0
                        click_state['last_click_obj'] = None
                        widget.queue_draw()
                        return True
                    
                    # Normal double-click behavior for non-parallel objects
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
                # Clicked on empty space
                # If in edit mode, just exit edit mode (keep selection)
                if manager.selection_manager.is_edit_mode():
                    manager.selection_manager.exit_edit_mode()
                    widget.queue_draw()
                    # Don't start rectangle selection if just exiting edit mode
                    return True
                
                # Otherwise, start rectangle selection
                manager.rectangle_selection.start(world_x, world_y)
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
        lasso_state = self._lasso_state.get(widget, {})
        
        # Complete lasso selection if active
        if lasso_state.get('active', False) and lasso_state.get('selector'):
            if lasso_state['selector'].is_active:
                lasso_state['selector'].finish_lasso()
                lasso_state['active'] = False
                widget.queue_draw()
                return True
        
        # End transformation if active
        if state.get('is_transforming', False):
            if manager.editing_transforms.end_transformation():
                # Transformation was committed successfully
                widget.queue_draw()
            state['is_transforming'] = False
            state['active'] = False
            state['button'] = 0
            return True
        
        # Get move data before ending drag (for undo)
        move_data = None
        if manager.selection_manager.is_dragging():
            move_data = manager.selection_manager.get_move_data_for_undo()
        
        # End drag
        if manager.selection_manager.end_drag():
            # Record move operation for undo if objects moved
            if move_data and hasattr(manager, 'undo_manager'):
                from shypn.edit.undo_operations import MoveOperation
                manager.undo_manager.push(MoveOperation(move_data))
            
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
        lasso_state = self._lasso_state.get(widget, {})
        manager.set_pointer_position(event.x, event.y)
        world_x, world_y = manager.screen_to_world(event.x, event.y)
        arc_state['cursor_pos'] = (world_x, world_y)
        
        # Update lasso path if active
        if lasso_state.get('active', False) and lasso_state.get('selector'):
            if lasso_state['selector'].is_active:
                lasso_state['selector'].add_point(world_x, world_y)
                widget.queue_draw()
                return True
        
        # FIX: Update arc preview with target validation
        if manager.is_tool_active() and manager.get_tool() == 'arc' and (arc_state['source'] is not None):
            # Check hovered object for target validation
            hovered = manager.find_object_at_position(world_x, world_y)
            if hovered and hovered != arc_state['source']:
                source = arc_state['source']
                # Valid: Place→Transition or Transition→Place
                is_valid = (isinstance(source, Place) and isinstance(hovered, Transition)) or \
                           (isinstance(source, Transition) and isinstance(hovered, Place))
                arc_state['target_valid'] = is_valid
                arc_state['hovered_target'] = hovered
            else:
                arc_state['target_valid'] = None
                arc_state['hovered_target'] = None
            
            widget.queue_draw()
        if state['active'] and state['button'] > 0:
            # Handle transformation drag
            if state.get('is_transforming', False):
                manager.editing_transforms.update_transformation(world_x, world_y)
                widget.queue_draw()
                return True
            
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            # Reduced threshold for more responsive drag (was 5 pixels)
            if not state['is_panning'] and (abs(dx) >= 2 or abs(dy) >= 2):
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
        # First, let editing operations palette handle its shortcuts
        if widget in self.overlay_managers:
            overlay_manager = self.overlay_managers[widget]
            editing_ops_palette = overlay_manager.get_palette('editing_operations')
            if editing_ops_palette and editing_ops_palette.handle_key_press(event):
                return True
        
        # Check for Ctrl modifier
        is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        is_shift = event.state & Gdk.ModifierType.SHIFT_MASK
        
        # Undo (Ctrl+Z)
        if is_ctrl and not is_shift and event.keyval == Gdk.KEY_z:
            if hasattr(manager, 'undo_manager') and manager.undo_manager:
                if manager.undo_manager.undo(manager):
                    widget.queue_draw()
                return True
        
        # Redo (Ctrl+Shift+Z)
        if is_ctrl and is_shift and event.keyval == Gdk.KEY_z:
            if hasattr(manager, 'undo_manager') and manager.undo_manager:
                if manager.undo_manager.redo(manager):
                    widget.queue_draw()
                return True
        
        if event.keyval == Gdk.KEY_Escape:
            # Cancel lasso if active
            lasso_state = self._lasso_state.get(widget, {})
            if lasso_state.get('active', False) and lasso_state.get('selector'):
                if lasso_state['selector'].is_active:
                    lasso_state['selector'].cancel_lasso()
                    lasso_state['active'] = False
                    widget.queue_draw()
                    return True
            
            # Cancel transformation if active
            if manager.editing_transforms.is_transforming():
                manager.editing_transforms.cancel_transformation()
                widget.queue_draw()
                return True
            
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
        if len(all_objects) > 0 and len(manager.places) > 0:
            for obj in all_objects:
                obj.render(cr, zoom=manager.zoom)
        
        manager.editing_transforms.render_selection_layer(cr, manager, manager.zoom)
        manager.rectangle_selection.render(cr, manager.zoom)
        
        # Render lasso if active
        if drawing_area in self._lasso_state:
            lasso_state = self._lasso_state[drawing_area]
            if lasso_state.get('active', False) and lasso_state.get('selector'):
                lasso_state['selector'].render_lasso(cr, manager.zoom)
        
        # Highlight source object when creating arc
        if drawing_area in self._arc_state:
            arc_state = self._arc_state[drawing_area]
            source = arc_state.get('source')
            
            if source is not None:
                # Green glow for source
                cr.set_source_rgba(0.2, 0.9, 0.2, 0.6)
                cr.set_line_width(4.0 / manager.zoom)
                
                if isinstance(source, Place):
                    cr.arc(source.x, source.y, source.radius + 6, 0, 2 * math.pi)
                    cr.stroke()
                elif isinstance(source, Transition):
                    w = source.width if source.horizontal else source.height
                    h = source.height if source.horizontal else source.width
                    cr.rectangle(source.x - w/2 - 6, source.y - h/2 - 6, w + 12, h + 12)
                    cr.stroke()
            
            # Highlight hovered target with validation color
            hovered = arc_state.get('hovered_target')
            target_valid = arc_state.get('target_valid')
            
            if hovered is not None and target_valid is not None:
                # Green for valid, red for invalid
                if target_valid:
                    cr.set_source_rgba(0.2, 0.9, 0.2, 0.5)
                else:
                    cr.set_source_rgba(0.9, 0.2, 0.2, 0.5)
                
                cr.set_line_width(3.0 / manager.zoom)
                
                if isinstance(hovered, Place):
                    cr.arc(hovered.x, hovered.y, hovered.radius + 4, 0, 2 * math.pi)
                    cr.stroke()
                elif isinstance(hovered, Transition):
                    w = hovered.width if hovered.horizontal else hovered.height
                    h = hovered.height if hovered.horizontal else hovered.width
                    cr.rectangle(hovered.x - w/2 - 4, hovered.y - h/2 - 4, w + 8, h + 8)
                    cr.stroke()
        
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
        
        # Check if this is a parallel arc (for disabling edit mode)
        is_parallel_arc = False
        if isinstance(obj, Arc):
            parallels = manager.detect_parallel_arcs(obj)
            is_parallel_arc = len(parallels) > 0
        
        # Build menu items list
        if is_parallel_arc:
            # For parallel arcs, don't include "Edit Mode" option
            menu_items = [('Edit Properties...', lambda: self._on_object_properties(obj, manager, drawing_area)), None, ('Delete', lambda: self._on_object_delete(obj, manager, drawing_area))]
        else:
            # For normal objects, include "Edit Mode" option
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
            from shypn.netobjs.place import Place
            from shypn.netobjs.transition import Transition
            
            transform_submenu_item = Gtk.MenuItem(label='Transform Arc ►')
            transform_submenu = Gtk.Menu()
            
            # Check if arc can be converted to inhibitor (Place → Transition only)
            can_be_inhibitor = isinstance(obj.source, Place) and isinstance(obj.target, Transition)
            
            # Normal/Inhibitor options only (Curve/Straight options removed)
            if is_normal(obj):
                if can_be_inhibitor:
                    inhibitor_item = Gtk.MenuItem(label='Convert to Inhibitor Arc')
                    inhibitor_item.connect('activate', lambda w: self._on_arc_convert_to_inhibitor(obj, manager, drawing_area))
                    inhibitor_item.show()
                    transform_submenu.append(inhibitor_item)
                # If arc is Transition → Place, don't show inhibitor option at all
            else:
                # Already an inhibitor arc, show option to convert back to normal
                inhibitor_item = Gtk.MenuItem(label='Convert to Normal Arc')
                inhibitor_item.connect('activate', lambda w: self._on_arc_convert_to_normal(obj, manager, drawing_area))
                inhibitor_item.show()
                transform_submenu.append(inhibitor_item)
            
            # Only show Transform submenu if there are options
            if transform_submenu.get_children():
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
        menu_items = [('Reset Zoom (100%)', lambda: self._on_reset_zoom_clicked(menu, drawing_area, manager)), ('Zoom In', lambda: self._on_zoom_in_clicked(menu, drawing_area, manager)), ('Zoom Out', lambda: self._on_zoom_out_clicked(menu, drawing_area, manager)), ('Fit to Window', lambda: self._on_fit_to_window_clicked(menu, drawing_area, manager)), None, ('Grid: Line Style', lambda: self._on_grid_line_clicked(menu, drawing_area, manager)), ('Grid: Dot Style', lambda: self._on_grid_dot_clicked(menu, drawing_area, manager)), ('Grid: Cross Style', lambda: self._on_grid_cross_clicked(menu, drawing_area, manager)), None, ('Layout: Auto (Best)', lambda: self._on_layout_auto_clicked(menu, drawing_area, manager)), ('Layout: Hierarchical', lambda: self._on_layout_hierarchical_clicked(menu, drawing_area, manager)), ('Layout: Force-Directed', lambda: self._on_layout_force_clicked(menu, drawing_area, manager)), ('Layout: Circular', lambda: self._on_layout_circular_clicked(menu, drawing_area, manager)), ('Layout: Orthogonal', lambda: self._on_layout_orthogonal_clicked(menu, drawing_area, manager)), None, ('Center View', lambda: self._on_center_view_clicked(menu, drawing_area, manager)), ('Clear Canvas', lambda: self._on_clear_canvas_clicked(menu, drawing_area, manager))]
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

    def _on_layout_auto_clicked(self, menu, drawing_area, manager):
        """Apply automatic layout (best algorithm for graph topology)."""
        try:
            from shypn.edit.graph_layout import LayoutEngine
            
            # Check if there are nodes to layout
            if not manager.places and not manager.transitions:
                self._show_layout_message("No objects to layout", drawing_area)
                return
            
            # Calculate current center of objects (to preserve relative position)
            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                center_y = sum(obj.y for obj in all_objs) / len(all_objs)
            else:
                # Default to canvas center
                center_x = manager.canvas_width / 2
                center_y = manager.canvas_height / 2
            
            # Create engine and apply layout
            engine = LayoutEngine(manager)
            result = engine.apply_layout('auto')
            
            # The layout algorithms center at (0, 0), so we need to offset
            # back to the original center or canvas center
            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                # Calculate new center after layout
                new_center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                new_center_y = sum(obj.y for obj in all_objs) / len(all_objs)
                
                # Calculate offset needed
                offset_x = center_x - new_center_x
                offset_y = center_y - new_center_y
                
                # Apply offset to all objects
                for obj in all_objs:
                    obj.x += offset_x
                    obj.y += offset_y
            
            # Show result
            message = (f"Applied {result['algorithm']} layout\n"
                      f"Moved {result['nodes_moved']} objects\n"
                      f"Reason: {result['reason']}")
            self._show_layout_message(message, drawing_area)
            
            # Redraw
            drawing_area.queue_draw()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_layout_message(f"Layout error: {str(e)}", drawing_area)
    
    def _on_layout_hierarchical_clicked(self, menu, drawing_area, manager):
        """Apply hierarchical (Sugiyama) layout."""
        self._apply_specific_layout(manager, drawing_area, 'hierarchical', 'Hierarchical (Sugiyama)')
    
    def _on_layout_force_clicked(self, menu, drawing_area, manager):
        """Apply force-directed (Fruchterman-Reingold) layout."""
        self._apply_specific_layout(manager, drawing_area, 'force_directed', 'Force-Directed')
    
    def _on_layout_circular_clicked(self, menu, drawing_area, manager):
        """Apply circular layout."""
        self._apply_specific_layout(manager, drawing_area, 'circular', 'Circular')
    
    def _on_layout_orthogonal_clicked(self, menu, drawing_area, manager):
        """Apply orthogonal (grid-aligned) layout."""
        self._apply_specific_layout(manager, drawing_area, 'orthogonal', 'Orthogonal')
    
    def _apply_specific_layout(self, manager, drawing_area, algorithm, algorithm_name):
        """Apply a specific layout algorithm.
        
        Args:
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
            algorithm: Algorithm name ('hierarchical', 'force_directed', etc.)
            algorithm_name: Human-readable name for messages
        """
        try:
            from shypn.edit.graph_layout import LayoutEngine
            
            # Check if there are nodes to layout
            if not manager.places and not manager.transitions:
                self._show_layout_message("No objects to layout", drawing_area)
                return
            
            print(f"[Layout] Before: {len(manager.places)} places, {len(manager.transitions)} transitions")
            
            # Calculate current center of objects (to preserve relative position)
            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                center_y = sum(obj.y for obj in all_objs) / len(all_objs)
            else:
                # Default to canvas center
                center_x = manager.canvas_width / 2
                center_y = manager.canvas_height / 2
            
            # Create engine and apply layout
            engine = LayoutEngine(manager)
            result = engine.apply_layout(algorithm)
            
            # The layout algorithms center at (0, 0), so we need to offset
            # back to the original center or canvas center
            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                # Calculate new center after layout
                new_center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                new_center_y = sum(obj.y for obj in all_objs) / len(all_objs)
                
                # Calculate offset needed
                offset_x = center_x - new_center_x
                offset_y = center_y - new_center_y
                
                # Apply offset to all objects
                for obj in all_objs:
                    obj.x += offset_x
                    obj.y += offset_y
            
            print(f"[Layout] After: {len(manager.places)} places, {len(manager.transitions)} transitions")
            print(f"[Layout] Result: {result}")
            
            # Show result
            message = f"Applied {algorithm_name} layout\nMoved {result['nodes_moved']} objects"
            self._show_layout_message(message, drawing_area)
            
            # Redraw
            drawing_area.queue_draw()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_layout_message(f"Layout error: {str(e)}", drawing_area)
    
    def _show_layout_message(self, message, drawing_area):
        """Show a temporary message on the status bar or console.
        
        Args:
            message: Message to display
            drawing_area: GtkDrawingArea widget (for future status bar integration)
        """
        # For now, just print to console
        # Later this can be wired to a status bar
        print(f"[Graph Layout] {message}")

    def _on_object_delete(self, obj, manager, drawing_area):
        """Delete an object from the canvas.
        
        Args:
            obj: Object to delete (Place, Transition, or Arc)
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Place, Transition, Arc
        
        # Record operation for undo (capture state before deletion)
        if hasattr(manager, 'undo_manager'):
            from shypn.edit.snapshots import capture_delete_snapshots
            from shypn.edit.undo_operations import DeleteOperation
            snapshots = capture_delete_snapshots(manager, [obj])
            manager.undo_manager.push(DeleteOperation(snapshots))
        
        # Perform deletion
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
        # Clear arc creation state to prevent spurious arc creation
        arc_state = self._arc_state.get(drawing_area)
        if arc_state:
            arc_state['source'] = None
            arc_state['ignore_next_release'] = True  # Ignore any queued mouse events
        
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
        # CRITICAL: Clear ALL arc creation state before opening dialog
        # This prevents spurious arc creation when dialog closes
        arc_state = self._arc_state.get(drawing_area)
        if arc_state:
            arc_state['source'] = None
            arc_state['cursor_pos'] = (0, 0)
            arc_state['ignore_next_release'] = True
        
        # Also temporarily switch tool if arc tool is active
        original_tool = None
        if manager.is_tool_active() and manager.get_tool() == 'arc':
            original_tool = 'arc'
            manager.set_tool('select')  # Force to select mode during dialog
        
        from shypn.netobjs import Place, Transition, Arc
        from shypn.helpers.place_prop_dialog_loader import create_place_prop_dialog
        from shypn.helpers.transition_prop_dialog_loader import create_transition_prop_dialog
        from shypn.helpers.arc_prop_dialog_loader import create_arc_prop_dialog
        dialog_loader = None
        if isinstance(obj, Place):
            dialog_loader = create_place_prop_dialog(obj, parent_window=self.parent_window, persistency_manager=self.persistency)
        elif isinstance(obj, Transition):
            data_collector = None
            if drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                simulate_tools = overlay_manager.get_palette('simulate_tools')
                if simulate_tools and hasattr(simulate_tools, 'data_collector'):
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
            if isinstance(obj, Transition) and drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                simulate_tools = overlay_manager.get_palette('simulate_tools')
                if simulate_tools and simulate_tools.simulation:
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
        
        # Restore original tool if we switched it
        if original_tool == 'arc':
            manager.set_tool('arc')
        
        # Clear arc creation state again after dialog closes to prevent spurious arc creation
        # This handles the case where mouse release happens after dialog closes
        arc_state = self._arc_state.get(drawing_area)
        if arc_state:
            arc_state['source'] = None
            arc_state['cursor_pos'] = (0, 0)
        
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
        if drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            simulate_tools = overlay_manager.get_palette('simulate_tools')
            if simulate_tools and simulate_tools.simulation:
                simulate_tools.simulation.invalidate_behavior_cache(transition.id)
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
        dialog = Gtk.Dialog(title=f'Edit {arc.name} Weight', parent=self.parent_window, modal=True, destroy_with_parent=True)
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