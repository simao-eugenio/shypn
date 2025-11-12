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
    from gi.repository import Gtk, Gdk, Gio, GLib
    import time
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
    # PHASE 3 COMPLETE: Using new modular architecture with constant height + parameter panels
    from shypn.helpers.swissknife_palette_new import SwissKnifePalette
    from shypn.helpers.swissknife_tool_registry import ToolRegistry
except ImportError as e:
    print(f'ERROR: Cannot import new OOP palettes: {e}', file=sys.stderr)
    sys.exit(1)

# PHASE 4: Import simulation controller for state-based permissions
try:
    from shypn.engine.simulation.controller import SimulationController
    # PHASE 4: Import IDManager lifecycle integration
    from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
except ImportError as e:
    print(f'ERROR: Cannot import SimulationController: {e}', file=sys.stderr)
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
        
        # PHASE 4: Simulation controllers - one per canvas
        # Canvas-centric design: Controllers stored by drawing_area, not palette.
        # This ensures wiring survives SwissPalette refactoring.
        # Access pattern: drawing_area → controller → state_detector, interaction_guard
        self.simulation_controllers = {}
        
        # GLOBAL-SYNC: Canvas lifecycle management
        # Initialize lifecycle system for coordinated component management
        try:
            from shypn.canvas.lifecycle import enable_lifecycle_system
            self.lifecycle_manager, self.lifecycle_adapter = enable_lifecycle_system(self)
            
            # PHASE 4: Connect global IDManager to lifecycle scoping
            # This makes all ID generation canvas-scoped automatically
            if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
                set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
        except Exception as e:
            self.lifecycle_manager = None
            self.lifecycle_adapter = None
        
        self.parent_window = None
        self.persistency = None
        self.right_panel_loader = None
        self.report_panel_loader = None  # PHASE 1-2: For simulation results tables
        self.context_menu_handler = None
        self._clipboard = []  # Clipboard for cut/copy/paste operations
        
        # Knowledge bases for intelligent model repair (Viability Panel)
        # One ModelKnowledgeBase instance per drawing_area
        self.knowledge_bases = {}  # drawing_area -> ModelKnowledgeBase
        
        # Project reference for structured save paths (pathways/, models/, metadata/)
        self.project = None
        
        # Track last pointer position for paste-at-pointer functionality
        self._last_pointer_world_x = 0.0
        self._last_pointer_world_y = 0.0

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
        
        # Override theme's notebook styling - use light, clean colors
        css_provider = Gtk.CssProvider()
        css = b"""
        #canvas_notebook {
            background: white;
        }
        #canvas_notebook > header {
            background: white;
        }
        #canvas_notebook > header > tabs > tab {
            background: white;
        }
        #canvas_notebook > header > tabs > tab:checked {
            background: white;
        }
        #canvas_notebook > stack {
            background: white;
        }
        """
        css_provider.load_from_data(css)
        style_context = self.notebook.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        
        # CRITICAL FIX: Remove default tab from UI file and create fresh one programmatically
        # The UI file contains a pre-baked tab that has timing issues with controller wiring
        # Solution: Delete the UI tab and create a new one using add_document() for consistency
        self.document_count = self.notebook.get_n_pages()
        if self.document_count > 0:
            print(f"\n[DEFAULT_TAB_INIT] ==========================================")
            print(f"[DEFAULT_TAB_INIT] Found {self.document_count} tab(s) from UI file")
            print(f"[DEFAULT_TAB_INIT] Removing UI tab and creating fresh programmatic tab")
            
            # Remove all pages from the UI file
            while self.notebook.get_n_pages() > 0:
                self.notebook.remove_page(0)
            
            print(f"[DEFAULT_TAB_INIT] Removed UI tabs, notebook now has {self.notebook.get_n_pages()} pages")
            print(f"[DEFAULT_TAB_INIT] ==========================================\n")
        
        self.notebook.connect('switch-page', self._on_notebook_page_changed)
        
        # Create fresh default tab using add_document() for consistent initialization
        # This ensures the default tab follows the SAME path as File→New
        print(f"[DEFAULT_TAB_INIT] Creating fresh default tab via add_document()")
        page_index, drawing_area = self.add_document(filename='default')
        print(f"[DEFAULT_TAB_INIT] ✅ Default tab created at index {page_index}")
        
        # Wire data collector for the initial default tab
        # The switch-page signal doesn't fire for the initially displayed page,
        # so we need to manually wire the data collector for tab 0
        if self.notebook.get_n_pages() > 0:
            initial_page = self.notebook.get_nth_page(0)
            self._wire_data_collector_for_page(initial_page)
            
            # ============================================================
            # CRITICAL: Set model and context menu handler for first tab
            # This is normally done in _on_notebook_page_changed, but that signal
            # doesn't fire for the initially displayed tab
            # ============================================================
            if self.right_panel_loader and drawing_area:
                if drawing_area in self.canvas_managers:
                    manager = self.canvas_managers[drawing_area]
                    self.right_panel_loader.set_model(manager)
                    
                    # CRITICAL: Explicitly ensure context menu handler has the correct model
                    # This ensures "Add to Transition Analyses" works from app startup
                    if self.right_panel_loader.context_menu_handler:
                        self.right_panel_loader.context_menu_handler.set_model(manager)
        
        return self.container

    def _wire_data_collector_for_page(self, page):
        """Wire the data collector to the right panel for a given page.
        
        Extracts the drawing_area from the page and wires its data collector.
        
        Args:
            page: Notebook page widget (Gtk.Overlay or Gtk.ScrolledWindow)
        """
        # print(f"\n[WIRE] _wire_data_collector_for_page() called")
        drawing_area = None
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
        
        # print(f"[WIRE]   drawing_area={drawing_area} (id={id(drawing_area) if drawing_area else 'None'})")
        
        if self.right_panel_loader and drawing_area:
            pass
            # Get simulate_tools_palette from SwissKnife registry
            if drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                # print(f"[WIRE]   Found overlay_manager")
                
                # SwissKnifePalette stores SimulateToolsPaletteLoader in widget_palette_instances
                if hasattr(overlay_manager, 'swissknife_palette'):
                    swissknife = overlay_manager.swissknife_palette
                    # print(f"[WIRE]   Found swissknife_palette")
                    
                    # NEW architecture: widget_palette_instances is in swissknife.registry
                    # OLD architecture: widget_palette_instances is directly on swissknife
                    simulate_tools_palette = None
                    
                    if hasattr(swissknife, 'registry') and hasattr(swissknife.registry, 'widget_palette_instances'):
                        pass
                        # print(f"[WIRE]   Using NEW architecture (registry.widget_palette_instances)")
                        simulate_tools_palette = swissknife.registry.widget_palette_instances.get('simulate')
                    elif hasattr(swissknife, 'widget_palette_instances'):
                        pass
                        # print(f"[WIRE]   Using OLD architecture (widget_palette_instances)")
                        simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
                    else:
                        pass
                        # print(f"[WIRE]   ❌ FAIL: No widget_palette_instances found in registry or swissknife")
                    
                    # print(f"[WIRE]   simulate_tools_palette={simulate_tools_palette}")
                    if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
                        data_collector = simulate_tools_palette.data_collector
                        # print(f"[WIRE]   ✅ SUCCESS: Wiring data_collector to right panel")
                        # print(f"[WIRE]      data_collector={data_collector} (id={id(data_collector)})")
                        self.right_panel_loader.set_data_collector(data_collector)
                        return True
                    else:
                        pass
                        # print(f"[WIRE]   ❌ FAIL: No simulate_tools_palette or data_collector found")
                else:
                    pass
                    # print(f"[WIRE]   ❌ FAIL: No swissknife_palette")
            else:
                pass
                # print(f"[WIRE]   ❌ FAIL: drawing_area not in overlay_managers")
        else:
            pass
            # print(f"[WIRE]   ❌ FAIL: No right_panel_loader or drawing_area")
        return False

    def _on_notebook_page_changed(self, notebook, page, page_num):
        """Handle notebook page switch.
        
        Args:
            notebook: GtkNotebook instance.
            page: The new page widget.
            page_num: The index of the new page.
        """
        # print(f"\n[TAB_SWITCH] ==========================================")
        # print(f"[TAB_SWITCH] Page changed to index {page_num}")
        # print(f"[TAB_SWITCH] ==========================================")
        
        # Update active tab styling - remove 'active' class from all tabs, add to current
        for i in range(notebook.get_n_pages()):
            page_widget = notebook.get_nth_page(i)
            tab_widget = notebook.get_tab_label(page_widget)
            if tab_widget and isinstance(tab_widget, Gtk.Box):
                style_context = tab_widget.get_style_context()
                if i == page_num:
                    style_context.add_class('active')
                else:
                    style_context.remove_class('active')
        
        drawing_area = None
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
        
        # print(f"[TAB_SWITCH] Extracted drawing_area: {drawing_area} (id={id(drawing_area) if drawing_area else 'None'})")
        
        # ============================================================
        # GLOBAL-SYNC: Switch canvas context when tab changes
        # ============================================================
        if self.lifecycle_adapter and drawing_area:
            try:
                self.lifecycle_adapter.switch_to_canvas(drawing_area)
            except Exception as e:
                pass  # Failed to switch canvas context
        
        if self.persistency:
            if drawing_area and drawing_area in self.canvas_managers:
                manager = self.canvas_managers[drawing_area]
                filename = manager.filename
                if manager.is_default_filename():
                    self.persistency.set_filepath(None)
                else:
                    pass
        
        # Wire data collector for the switched-to page
        # print(f"[TAB_SWITCH] Calling _wire_data_collector_for_page()...")
        wired = self._wire_data_collector_for_page(page)
        # print(f"[TAB_SWITCH] Wiring result: {wired}")
        
        # ============================================================
        # CRITICAL: Clear global Analyses panel when switching tabs
        # Since there's only ONE Analyses panel shared across ALL canvases,
        # we must clear the selected objects and reset arc colors when switching
        # ============================================================
        if self.right_panel_loader:
            from shypn.netobjs import Transition, Place, Arc
            
            # Clear transition panel selections
            if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                transition_panel = self.right_panel_loader.transition_panel
                
                # Reset arc colors for all transitions with locality
                # We need to check ALL canvases since selections could be from any canvas
                for transition_id, locality_data in list(transition_panel._locality_places.items()):
                    # Find which canvas this transition belongs to
                    for check_drawing_area, check_manager in self.canvas_managers.items():
                        # Find the transition in this canvas
                        transition_obj = None
                        for t in check_manager.transitions:
                            if t.id == transition_id:
                                transition_obj = t
                                break
                        
                        if transition_obj:
                            # Reset colors of arcs from input places to transition
                            for place in locality_data.get('input_places', []):
                                for arc in check_manager.arcs:
                                    if arc.source.id == place.id and arc.target.id == transition_id:
                                        arc.color = Arc.DEFAULT_COLOR
                            
                            # Reset colors of arcs from transition to output places
                            for place in locality_data.get('output_places', []):
                                for arc in check_manager.arcs:
                                    if arc.source.id == transition_id and arc.target.id == place.id:
                                        arc.color = Arc.DEFAULT_COLOR
                            
                            # Trigger redraw for this canvas
                            check_manager.mark_needs_redraw()
                            break
                
                # Reset colors for all selected transitions
                for obj in transition_panel.selected_objects:
                    old_callback = obj.on_changed if hasattr(obj, 'on_changed') else None
                    obj.on_changed = None
                    
                    if isinstance(obj, Transition):
                        obj.border_color = Transition.DEFAULT_BORDER_COLOR
                        obj.fill_color = Transition.DEFAULT_COLOR
                    
                    obj.on_changed = old_callback
                
                # Clear the selections
                transition_panel.selected_objects.clear()
                transition_panel.last_data_length.clear()
                transition_panel._plot_lines.clear()
                transition_panel._locality_places.clear()
                transition_panel._show_empty_state()
                transition_panel._update_objects_list()
            
            # Clear place panel selections
            if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
                place_panel = self.right_panel_loader.place_panel
                # Reset colors for all selected places
                for obj in place_panel.selected_objects:
                    old_callback = obj.on_changed if hasattr(obj, 'on_changed') else None
                    obj.on_changed = None
                    
                    if isinstance(obj, Place):
                        obj.border_color = Place.DEFAULT_BORDER_COLOR
                    
                    obj.on_changed = old_callback
                
                # Clear the selections
                place_panel.selected_objects.clear()
                place_panel.last_data_length.clear()
                place_panel._plot_lines.clear()
                place_panel._show_empty_state()
                place_panel._update_objects_list()
        
        # ============================================================
        # CRITICAL: Update right panel loader model and context menu handler
        # This ensures "Add to Transition Analyses" works consistently
        # ============================================================
        if self.right_panel_loader and drawing_area:
            if drawing_area in self.canvas_managers:
                manager = self.canvas_managers[drawing_area]
                self.right_panel_loader.set_model(manager)
                
                # CRITICAL: Explicitly ensure context menu handler has the correct model
                # This must happen EVERY time we switch tabs to ensure locality detection works
                if self.right_panel_loader.context_menu_handler:
                    self.right_panel_loader.context_menu_handler.set_model(manager)
            
            if self.right_panel_loader.context_menu_handler and (not self.context_menu_handler):
                self.set_context_menu_handler(self.right_panel_loader.context_menu_handler)
        
        # Swap per-document Viability Panel when tab changes
        if drawing_area and hasattr(self, 'viability_panel_container') and self.viability_panel_container:
            if self.viability_panel_container.get_visible():
                # Viability panel is currently shown, swap to this document's panel
                if drawing_area in self.overlay_managers:
                    overlay_manager = self.overlay_managers[drawing_area]
                    if hasattr(overlay_manager, 'viability_panel_loader'):
                        viability_loader = overlay_manager.viability_panel_loader
                        if viability_loader and viability_loader.panel:
                            # Clear container first
                            for child in self.viability_panel_container.get_children():
                                self.viability_panel_container.remove(child)
                            # Add per-document panel
                            if viability_loader.widget.get_parent() != self.viability_panel_container:
                                current_parent = viability_loader.widget.get_parent()
                                if current_parent:
                                    current_parent.remove(viability_loader.widget)
                                self.viability_panel_container.pack_start(viability_loader.widget, True, True, 0)
                            viability_loader.panel.show_all()
                            print(f"[TAB_SWITCH] ✓ Swapped to per-document viability panel for drawing_area {id(drawing_area)}")
        
        # ============================================================
        # CRITICAL: Update Report Panel controller when switching tabs
        # This ensures Dynamic Analyses tables show the correct document's data
        # ============================================================
        if drawing_area and drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            
            # Get the controller for this document
            if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller:
                controller = overlay_manager.simulation_controller
                
                # Update Report Panel's controller reference
                if hasattr(overlay_manager, 'report_panel_loader') and overlay_manager.report_panel_loader:
                    report_panel = overlay_manager.report_panel_loader.panel
                    if report_panel and hasattr(report_panel, 'set_controller'):
                        print(f"[TAB_SWITCH] Updating Report Panel controller for drawing_area {id(drawing_area)}")
                        report_panel.set_controller(controller)
                        print(f"[TAB_SWITCH] ✓ Report Panel now shows data for controller {id(controller)}")

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

    def _create_tab_label(self, filename='default', is_modified=False):
        """Create a tab label with file icon, filename, and close button.
        
        Args:
            filename: Document filename (without extension, or None for default)
            is_modified: Whether document has unsaved changes
            
        Returns:
            tuple: (tab_box, label_widget, close_button) for later updates
        """
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        
        # Apply CSS styling for elevated tab appearance
        css_provider = Gtk.CssProvider()
        css = b"""
        .tab-box {
            padding: 2px 6px;
            border: 1px solid #ccc;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            background: #f5f5f5;
            min-height: 18px;
            margin-top: 0;
            margin-bottom: -1px;
            margin-left: 0;
            margin-right: -1px;
        }
        .tab-box:hover {
            background: #ffffff;
            border-color: #999;
        }
        .tab-box.active {
            background: #ffffff;
            border-color: #aaa;
            border-width: 1px;
            font-weight: bold;
        }
        .tab-box.active label {
            color: white;
        }
        """
        css_provider.load_from_data(css)
        style_context = tab_box.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        style_context.add_class('tab-box')
        
        # File type icon (document icon for Petri nets) - using SMALL_TOOLBAR for compact size
        file_icon = Gtk.Image.new_from_icon_name('text-x-generic', Gtk.IconSize.SMALL_TOOLBAR)
        file_icon.show()
        tab_box.pack_start(file_icon, False, False, 0)
        
        # Use 'default.shy' if no filename provided
        if not filename or filename == 'default':
            filename = 'default.shy'
        elif not filename.endswith('.shy'):
            filename = f"{filename}.shy"
        
        # Filename label - expand to show full name without ellipsis
        display_name = f"{filename}{'*' if is_modified else ''}"
        tab_label = Gtk.Label(label=display_name)
        # Don't truncate - let tab expand to fit full filename
        # tab_label.set_ellipsize(3)  # Removed - show full text
        # tab_label.set_max_width_chars(20)  # Removed - no width limit
        tab_label.set_xalign(0.0)  # Left align
        tab_label.show()
        tab_box.pack_start(tab_label, expand=True, fill=True, padding=0)
        
        # Close button (X) - using MENU size for compact appearance
        close_button = Gtk.Button()
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_focus_on_click(False)
        close_icon = Gtk.Image.new_from_icon_name('window-close-symbolic', Gtk.IconSize.MENU)
        close_button.set_image(close_icon)
        close_button.show()
        tab_box.pack_start(close_button, False, False, 0)
        
        tab_box.show()
        
        return (tab_box, tab_label, close_button)

    def _update_tab_label(self, page_widget, filename='default', is_modified=False):
        """Update tab label for a page with new filename and modification state.
        
        Args:
            page_widget: The page widget (Gtk.Overlay) whose tab to update
            filename: New filename (without extension, or None for default)
            is_modified: Whether document has unsaved changes
        """
        tab_widget = self.notebook.get_tab_label(page_widget)
        if not tab_widget or not isinstance(tab_widget, Gtk.Box):
            return
        
        # Ensure filename is a string (convert if needed)
        filename = str(filename) if filename is not None else 'default'
        
        # Ensure is_modified is a boolean
        is_modified = bool(is_modified)
        
        # Use 'default.shy' if no filename provided
        if not filename or filename == 'default':
            filename = 'default.shy'
        elif not filename.endswith('.shy'):
            filename = f"{filename}.shy"
        
        # Find the label in the tab box (it's the second child after icon)
        children = tab_widget.get_children()
        if len(children) >= 2:
            label = children[1]  # Index 1 is the label (after icon)
            if isinstance(label, Gtk.Label):
                display_name = f"{filename}{'*' if is_modified else ''}"
                label.set_text(display_name)

    def update_current_tab_label(self, filename='default', is_modified=False):
        """Update the current (active) tab's label with new filename.
        
        Public method to be called when a file is opened or saved.
        
        Args:
            filename: New filename (can include or exclude .shy extension)
            is_modified: Whether document has unsaved changes
        """
        current_page = self.notebook.get_current_page()
        if current_page < 0:
            return
        page_widget = self.notebook.get_nth_page(current_page)
        if page_widget:
            self._update_tab_label(page_widget, filename, is_modified)

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
        
        # ============================================================
        # GLOBAL-SYNC: Destroy canvas in lifecycle system
        # ============================================================
        if self.lifecycle_adapter and drawing_area:
            try:
                self.lifecycle_adapter.destroy_canvas(drawing_area)
            except Exception as e:
                pass  # Failed to destroy canvas in lifecycle
        
        if drawing_area and drawing_area in self.canvas_managers:
            del self.canvas_managers[drawing_area]
        if drawing_area and drawing_area in self.simulation_controllers:
            del self.simulation_controllers[drawing_area]
        if drawing_area and drawing_area in self.overlay_managers:
            pass
            # Cleanup overlay manager and all its palettes
            overlay_manager = self.overlay_managers[drawing_area]
            overlay_manager.cleanup_overlays()
            del self.overlay_managers[drawing_area]
        if drawing_area and drawing_area in self.knowledge_bases:
            # Cleanup knowledge base
            del self.knowledge_bases[drawing_area]
            print(f"[KNOWLEDGE_BASE] Cleaned up KB for canvas {id(drawing_area)}")
        if self.notebook.get_n_pages() == 0:
            self.add_document(filename='default')
        return True

    def is_current_tab_empty_default(self):
        """Check if current tab is an empty default tab that can be replaced.
        
        DEPRECATED: This feature has been disabled. Users must manually close default tabs.
        
        Returns:
            bool: Always returns False (auto-replacement disabled)
        """
        # Auto-replacement disabled - users manually close default tab if unwanted
        return False

    def _get_drawing_area_from_page(self, page_widget):
        """Extract drawing area from a notebook page widget.
        
        Args:
            page_widget: Notebook page widget (Gtk.Overlay or Gtk.ScrolledWindow)
            
        Returns:
            Gtk.DrawingArea or None
        """
        if isinstance(page_widget, Gtk.Overlay):
            scrolled = page_widget.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                return scrolled.get_child()
        elif isinstance(page_widget, Gtk.ScrolledWindow):
            return page_widget.get_child()
        return None

    def add_document(self, title=None, filename=None, replace_empty_default=True):
        """Add a new document (tab) to the canvas.
        
        Args:
            title: Optional title for the new document tab (deprecated, use filename).
            filename: Base filename without extension (default: "default").
            replace_empty_default: DEPRECATED - No longer used. Always creates new tab.
            
        Returns:
            tuple: (page_index, drawing_area) for the new document.
        """
        if self.notebook is None:
            raise RuntimeError('Canvas not loaded. Call load() first.')
        
        # Auto-replacement feature has been disabled
        # Users must manually close the default tab if they don't want it
        
        # Create new tab FROM UI TEMPLATE
        # This ensures identical widget hierarchy for all canvases (default, File→New, imports)
        # and eliminates Wayland timing issues by using consistent UI-based instantiation
        self.document_count += 1
        if filename is None:
            if title:
                filename = title
            else:
                filename = f"default{(self.document_count if self.document_count > 1 else '')}"
        
        # Load canvas tab from UI template
        template_path = os.path.join(os.path.dirname(self.ui_path), 'canvas_tab_template.ui')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Canvas tab template not found: {template_path}")
        
        # Create a new builder instance for this canvas (each canvas gets its own widgets)
        tab_builder = Gtk.Builder.new_from_file(template_path)
        overlay = tab_builder.get_object('canvas_overlay_template')
        scrolled = tab_builder.get_object('canvas_scroll_template')
        drawing = tab_builder.get_object('canvas_drawing_template')
        overlay_box = tab_builder.get_object('canvas_overlay_box_template')
        
        if not all([overlay, scrolled, drawing, overlay_box]):
            raise ValueError("Failed to load canvas widgets from template")
        
        # Create tab label with file icon
        tab_filename = filename if filename else 'default'
        tab_box, tab_label, close_button = self._create_tab_label(tab_filename, False)
        close_button.connect('clicked', self._on_tab_close_clicked, overlay)
        tab_box.show_all()
        
        page_index = self.notebook.append_page(overlay, tab_box)
        overlay.show_all()
        
        # WAYLAND FIX: Realize the widget before setup to ensure proper parent window hierarchy
        # On Wayland, dialogs require their parent to be realized (have a GdkWindow/GdkSurface)
        # Default canvas works because it's loaded from UI file and realized when main window shows
        # File→New/Import canvases are created programmatically and need explicit realization
        if not overlay.get_realized():
            overlay.realize()
        
        # Setup canvas manager BEFORE switching tabs
        # This ensures the canvas is fully initialized before receiving focus/events
        self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)
        
        # CRITICAL: Reset simulation to initial state after creating new document
        # Ensures clean slate with no stale cached behaviors
        self._ensure_simulation_reset(drawing)
        
        # Switch to the newly created tab to give it focus (AFTER setup is complete)
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
        
        # Store references back to loader and drawing area for simulation reset
        manager._canvas_loader = self
        manager._drawing_area = drawing_area
        
        # Set redraw callback so manager can trigger widget redraws
        manager.set_redraw_callback(lambda: drawing_area.queue_draw())
        
        # WAYLAND FIX: Set flag to suppress callbacks during initial setup
        # Prevents premature signal firing before canvas state is fully initialized
        manager._suppress_callbacks = True
        
        # PHASE 1: Wire dirty state callback to update tab label with asterisk
        # This enables automatic tab label updates when document is modified
        def on_dirty_changed(is_dirty):
            """Callback when manager's dirty state changes.
            
            Updates the tab label to show/hide asterisk indicator.
            """
            # Skip callback if we're still setting up the canvas
            if getattr(manager, '_suppress_callbacks', False):
                return
            
            try:
                pass
                # Find the page widget for this drawing area
                # Navigation: drawing_area -> GtkScrolledWindow -> GtkOverlay (page widget)
                parent = drawing_area.get_parent()  # Should be GtkScrolledWindow
                if not parent:
                    pass
                    # Widget hierarchy not yet established - this is normal during initial setup
                    # Callback will be triggered again later when changes occur
                    return
                
                page_widget = parent.get_parent()  # Should be GtkOverlay
                if not page_widget:
                    pass
                    # Still setting up widget hierarchy
                    return
                    
                # Verify page_widget is actually in the notebook
                page_num = self.notebook.page_num(page_widget)
                if page_num < 0:
                    pass
                    # Not yet added to notebook
                    return
                
                # Get display name from manager (filename without path)
                display_name = manager.get_display_name()
                # Update tab label using existing method
                self._update_tab_label(page_widget, display_name, is_modified=is_dirty)
            except Exception as e:
                pass
                # Silently ignore errors during widget setup
                # (e.g., if called before widget hierarchy is complete)
                pass
        
        manager.on_dirty_changed = on_dirty_changed
        
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
        
        # Create Knowledge Base for intelligent model repair
        try:
            from shypn.viability.knowledge import ModelKnowledgeBase
            kb = ModelKnowledgeBase(model=None)  # Model will be set when available
            self.knowledge_bases[drawing_area] = kb
            # Make KB accessible from canvas manager
            manager.knowledge_base = kb
            print(f"[KNOWLEDGE_BASE] Created KB for canvas {id(drawing_area)}")
        except Exception as e:
            print(f"[KNOWLEDGE_BASE] ⚠️ Failed to create knowledge base: {e}")

        def on_draw_wrapper(widget, cr):
            allocation = widget.get_allocation()
            self._on_draw(widget, cr, allocation.width, allocation.height, manager)
            return False
        drawing_area.connect('draw', on_draw_wrapper)
        self._setup_event_controllers(drawing_area, manager)
        
        # Trigger initial redraw now that draw handler is connected
        # (create_new_document() called mark_needs_redraw() but handler wasn't connected yet)
        manager.mark_needs_redraw()
        
        # Setup overlay manager to handle all palettes
        print(f"[SETUP_CANVAS] overlay_box={overlay_box is not None}, overlay_widget={overlay_widget is not None}")
        if overlay_box and overlay_widget:
            print(f"[SETUP_CANVAS] ✅ Creating CanvasOverlayManager")
            overlay_manager = CanvasOverlayManager(
                overlay_widget=overlay_widget,
                overlay_box=overlay_box,
                drawing_area=drawing_area,
                canvas_manager=manager
            )
            overlay_manager.setup_overlays(parent_window=self.parent_window)
            
            # Store overlay manager for later access
            self.overlay_managers[drawing_area] = overlay_manager
            print(f"[SETUP_CANVAS] ✅ Stored overlay_manager in self.overlay_managers (id={id(drawing_area)})")
            
            # Connect signals from palettes
            overlay_manager.connect_tool_changed_signal(
                self._on_tool_changed, manager, drawing_area
            )
            overlay_manager.connect_simulation_signals(
                self._on_simulation_step, self._on_simulation_reset, drawing_area
            )
            overlay_manager.connect_edit_button_signal(
                self._on_edit_button_toggled, drawing_area
            )
            
            # Set initial state: Edit mode is default
            # Old [E] and [S] buttons no longer exist - removed, replaced by SwissKnifePalette
            
            # Setup new OOP palette system
            self._setup_edit_palettes(overlay_widget, manager, drawing_area, overlay_manager)
            
            # Canvas setup complete - enable callbacks now that state is properly initialized
            manager._suppress_callbacks = False
        else:
            print(f"[SETUP_CANVAS] ❌ NO overlay_box or overlay_widget - CanvasOverlayManager NOT created!")
            print(f"[SETUP_CANVAS] ❌ This canvas will NOT have TransitionRatePanel or right_panel_loader!")
            # CRITICAL FIX: Even without overlay_box, MUST enable callbacks
            # Otherwise canvas becomes non-interactive
            manager._suppress_callbacks = False

    def _reset_manager_for_load(self, manager, filename):
        """Reset manager state before loading objects from file.
        
        This prepares an existing manager to receive a loaded document,
        resetting all state flags and counters to clean slate.
        
        MUST be called BEFORE load_objects() when reusing a tab for File→Open or Import.
        
        This is the CANONICAL state reset for document loading, ensuring:
        - All state flags are reset
        - Callbacks are enabled
        - Objects are cleared
        - ID counters are reset
        - Canvas interaction states are reset (drag, arc, lasso, etc.)
        - Simulation controllers are reset to initial state
        - Swiss palettes are reset to default tool/mode
        
        Args:
            manager: ModelCanvasManager instance to reset
            filename: Base filename (without extension) for the document
        """
        from datetime import datetime
        
        # Reset document metadata
        manager.filename = filename
        manager.modified = False
        manager.created_at = datetime.now()
        manager.modified_at = None
        
        # Reset view state (will be overridden by saved view_state if exists)
        manager.zoom = 1.0
        manager.pan_x = 0.0
        manager.pan_y = 0.0
        # CRITICAL: Reset initial_pan_set flag in BOTH manager and viewport_controller
        manager._initial_pan_set = False
        manager.viewport_controller._initial_pan_set = False
        
        # CRITICAL: Ensure callbacks are enabled
        # This is the most common cause of "frozen canvas" bugs
        manager._suppress_callbacks = False
        
        # Clear any existing objects
        # (Should be empty when reusing default tab, but be paranoid)
        manager.places.clear()
        manager.transitions.clear()
        manager.arcs.clear()
        
        # Reset ID counters to avoid collisions
        manager.document_controller.id_manager.reset()
        
        # Mark as clean (document will be loaded)
        manager.mark_clean()
        
        # Clear selection
        if hasattr(manager, 'selection_manager'):
            manager.selection_manager.clear_selection()
        
        # Reset tool state
        manager.clear_tool()
        
        # Reset canvas interaction states (CRITICAL for fixing corrupted context menu/drag)
        # These states can get stuck if not properly reset between document loads
        # Find the drawing_area for this manager by looking through self.canvas_managers
        drawing_area = None
        if hasattr(self, 'canvas_managers'):
            for da, mgr in self.canvas_managers.items():
                if mgr == manager:
                    drawing_area = da
                    break
        
        if drawing_area:
            pass
            # Ensure event masks and focus are set (critical for interaction)
            drawing_area.set_events(
                Gdk.EventMask.BUTTON_PRESS_MASK | 
                Gdk.EventMask.BUTTON_RELEASE_MASK | 
                Gdk.EventMask.POINTER_MOTION_MASK | 
                Gdk.EventMask.SCROLL_MASK | 
                Gdk.EventMask.KEY_PRESS_MASK
            )
            drawing_area.set_can_focus(True)
            
            # Reset drag state (prevents stuck panning/dragging)
            if hasattr(self, '_drag_state') and drawing_area in self._drag_state:
                self._drag_state[drawing_area] = {
                    'active': False,
                    'button': 0,
                    'start_x': 0,
                    'start_y': 0,
                    'is_panning': False,
                    'is_rect_selecting': False,
                    'is_transforming': False
                }
            
            # Reset arc creation state (prevents stuck arc drawing)
            if hasattr(self, '_arc_state') and drawing_area in self._arc_state:
                self._arc_state[drawing_area] = {
                    'source': None,
                    'cursor_pos': (0, 0),
                    'target_valid': None,
                    'hovered_target': None,
                    'ignore_next_release': False
                }
            
            # Reset click state (prevents stuck double-click detection)
            if hasattr(self, '_click_state') and drawing_area in self._click_state:
                click_state = self._click_state[drawing_area]
                # Cancel any pending click timeout
                if click_state.get('pending_timeout'):
                    GLib.source_remove(click_state['pending_timeout'])
                self._click_state[drawing_area] = {
                    'last_click_time': 0.0,
                    'last_click_obj': None,
                    'double_click_threshold': 0.3,
                    'pending_timeout': None,
                    'pending_click_data': None
                }
            
            # Reset lasso selection state (prevents stuck lasso mode)
            if hasattr(self, '_lasso_state') and drawing_area in self._lasso_state:
                lasso_state = self._lasso_state[drawing_area]
                # Deactivate any active lasso
                if lasso_state.get('selector'):
                    lasso_state['selector'].cancel()
                self._lasso_state[drawing_area] = {
                    'active': False,
                    'selector': None
                }
            
            # ============================================================
            # NOTE: Simulation controller reset moved to AFTER load_objects()
            # ============================================================
            # The simulation controller should be reset AFTER objects are loaded,
            # not here when the manager is still empty. The reset happens in
            # _ensure_simulation_reset() which is called after load_objects().
            # This ensures the controller sees the full loaded model.
            # print(f"[LOAD] Skipping controller reset here (will reset after objects loaded)")
            
            # ============================================================
            # CRITICAL: Reset Swiss Knife Palette to default state
            # ============================================================
            # The palette maintains tool selection, mode, and visual state.
            # When loading a new model, reset to default state (no active sub-palette).
            if drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                if hasattr(overlay_manager, 'swissknife_palette'):
                    palette = overlay_manager.swissknife_palette
                    # Hide any active sub-palette (returns to default state)
                    # Note: active_sub_palette only exists in old palette, not new refactored one
                    if hasattr(palette, 'active_sub_palette') and palette.active_sub_palette:
                        if hasattr(palette, '_hide_sub_palette') and hasattr(palette, 'active_category'):
                            palette._hide_sub_palette(palette.active_category)
                    # Update palette's model reference to the (reset) manager
                    palette.model = manager
                    # If palette has widget palette instances (like SimulateToolsPaletteLoader),
                    # update their model references too
                    if hasattr(palette, 'widget_palette_instances'):
                        for widget_palette in palette.widget_palette_instances.values():
                            if hasattr(widget_palette, 'model'):
                                widget_palette.model = manager
        
        # Trigger redraw to show canvas is ready for new content
        manager.mark_needs_redraw()
    
    def _ensure_simulation_reset(self, drawing_area):
        """Ensure simulation is reset to initial state for a canvas.
        
        CRITICAL for consistent behavior across all flows:
        This must be called after any operation that creates or modifies a model:
        - File → New
        - File → Open
        - Double-click file in explorer
        - KEGG import
        - SBML import
        - Parameter application (Heuristic/BRENDA/SABIO-RK)
        
        The reset ensures:
        - Behavior cache is cleared (old behaviors don't persist)
        - Places are set to initial marking (clean start)
        - Simulation time is reset to 0.0
        - Enablement states are recalculated
        
        See: CANVAS_STATE_ISSUES_COMPARISON.md for recurring pattern history
        
        Args:
            drawing_area: GtkDrawingArea for the canvas to reset
        """
        if not drawing_area:
            return
        
        try:
            if drawing_area in self.simulation_controllers:
                controller = self.simulation_controllers[drawing_area]
                manager = self.canvas_managers.get(drawing_area)
                # print(f"[RESET] _ensure_simulation_reset called for canvas")
                # print(f"[RESET] Controller ID: {id(controller)}")
                if manager:
                    pass
                    # print(f"[RESET] Manager has {len(manager.places)} places, {len(manager.transitions)} transitions")
                    # CRITICAL: Use reset_for_new_model() instead of reset()
                    # This recreates the model adapter and ensures the controller
                    # references the correct manager with the loaded objects
                    controller.reset_for_new_model(manager)
                    # print(f"[RESET] Full reset complete (model adapter recreated)")
                    
                    # CRITICAL: Update SimulateToolsPaletteLoader's controller reference
                    # The palette has its own simulation controller reference that needs
                    # to be updated when we reset/recreate the controller for a loaded model
                    # print(f"[RESET] Looking for overlay_manager...")
                    overlay_manager = self.overlay_managers.get(drawing_area)
                    if overlay_manager:
                        pass
                        # print(f"[RESET] Found overlay_manager: {type(overlay_manager).__name__}")
                        swissknife = getattr(overlay_manager, 'swissknife_palette', None)
                        # print(f"[RESET] swissknife_palette: {swissknife}")
                        if swissknife:
                            pass
                            # Use registry.get_widget_palette_instance() instead
                            if hasattr(swissknife, 'registry'):
                                pass
                                # print(f"[RESET] Has registry attribute")
                                simulate_tools_palette = swissknife.registry.get_widget_palette_instance('simulate')
                                # print(f"[RESET] simulate_tools_palette: {simulate_tools_palette}")
                                if simulate_tools_palette:
                                    pass
                                    # print(f"[RESET] ✅ Updating SimulateToolsPaletteLoader.simulation reference")
                                    # print(f"[RESET] Old controller ID: {id(simulate_tools_palette.simulation) if simulate_tools_palette.simulation else 'None'}")
                                    
                                    # CRITICAL: Preserve step listeners from old controller
                                    # When we replace the controller reference, we need to re-register
                                    # the step listeners on the new controller, otherwise the UI won't update!
                                    old_controller = simulate_tools_palette.simulation
                                    if old_controller and hasattr(old_controller, 'step_listeners'):
                                        pass
                                        # print(f"[RESET] Old controller had {len(old_controller.step_listeners)} step listeners")
                                    
                                    simulate_tools_palette.simulation = controller
                                    # print(f"[RESET] New controller ID: {id(simulate_tools_palette.simulation)}")
                                    
                                    # Re-register step listeners on new controller
                                    # The palette's _on_simulation_step callback updates progress and triggers redraws
                                    if hasattr(simulate_tools_palette, '_on_simulation_step'):
                                        controller.add_step_listener(simulate_tools_palette._on_simulation_step)
                                        # print(f"[RESET] Re-registered palette step listener")
                                    if hasattr(simulate_tools_palette, 'data_collector'):
                                        controller.add_step_listener(simulate_tools_palette.data_collector.on_simulation_step)
                                        # print(f"[RESET] Re-registered data collector step listener")
                                    
                                    # PHASE 1-2 FIX: Do NOT overwrite controller.data_collector
                                    # The controller has its own DataCollector (for Report Panel)
                                    # The simulate_tools_palette has its own (for real-time plots)
                                    # Both should coexist
                                    # DO NOT OVERWRITE: controller.data_collector = simulate_tools_palette.data_collector
                                    # print(f"[RESET] ✅ Preserved both data collectors (controller + palette)")
                                    
                                    # CRITICAL: Re-apply UI defaults to new controller
                                    # This ensures progress bar works globally after controller reset
                                    # (for File → Open, File → Reset, KEGG/SBML imports, parameter changes)
                                    simulate_tools_palette._apply_ui_defaults_to_settings()
                                    # print(f"[RESET] ✅ Re-applied UI defaults (duration, units) to new controller")
                                    
                                    # PHASE 1-2 FIX: Wire controller to Report Panel for table population
                                    # The Report Panel needs the controller reference to access simulation results
                                    if self.report_panel_loader and hasattr(self.report_panel_loader, 'panel'):
                                        report_panel = self.report_panel_loader.panel
                                        if report_panel and hasattr(report_panel, 'set_controller'):
                                            report_panel.set_controller(controller)
                                            # print(f"[RESET] ✅ Wired controller to Report Panel for simulation tables")
                                        else:
                                            pass
                                            # print(f"[RESET] ⚠️  Report panel not found or no set_controller method")
                                    else:
                                        pass
                                        # print(f"[RESET] ⚠️  report_panel_loader not found in model_canvas_loader")
                                    
                                    # VIABILITY PANEL: Wire simulation complete callback after reset
                                    # After controller reset, re-establish the callback chain for PER-DOCUMENT panel
                                    if drawing_area in self.overlay_managers:
                                        overlay_manager = self.overlay_managers[drawing_area]
                                        if hasattr(overlay_manager, 'viability_panel_loader') and overlay_manager.viability_panel_loader:
                                            try:
                                                viability_panel = overlay_manager.viability_panel_loader.panel
                                                if viability_panel and hasattr(viability_panel, 'on_simulation_complete'):
                                                    existing_callback = getattr(controller, 'on_simulation_complete', None)
                                                    
                                                    def combined_callback():
                                                        if existing_callback and callable(existing_callback):
                                                            existing_callback()
                                                        viability_panel.on_simulation_complete()
                                                    
                                                    controller.on_simulation_complete = combined_callback
                                                    print(f"[RESET] ✅ Re-wired simulation_complete → Per-document ViabilityPanel")
                                            except Exception as e:
                                                print(f"[RESET] ⚠️ Failed to wire viability callback: {e}")
                                else:
                                    pass
                                    # print(f"[RESET] ❌ simulate_tools_palette not found in registry")
                            else:
                                pass
                                # print(f"[RESET] ❌ No registry attribute on swissknife")
                        else:
                            pass
                            # print(f"[RESET] ❌ No swissknife_palette")
                    else:
                        pass
                        # print(f"[RESET] ❌ overlay_manager not found for drawing_area")
                else:
                    pass
                    # Fallback to basic reset if we can't get the manager
                    controller.reset()
                    # print(f"[RESET] Basic reset complete (no manager reference)")
                # print(f"[RESET] Simulation reset for canvas: {drawing_area}")
                if manager:
                    pass
                    # print(f"[RESET] Controller.model has {len(controller.model.places)} places, {len(controller.model.transitions)} transitions")
                    # print(f"[RESET] Controller.transition_states has {len(controller.transition_states)} entries")
                    
                    # CRITICAL LIFECYCLE FIX: Verify all transitions are registered
                    # After import/load, controller.transition_states should have entries for ALL transitions
                    # If missing, simulation won't run until user interaction triggers re-registration
                    missing_count = 0
                    for transition in manager.transitions:
                        if transition.id not in controller.transition_states:
                            missing_count += 1
                            # print(f"[RESET] ⚠️ Missing transition_state for {transition.id} - forcing registration")
                            # Force create state for this transition
                            state = controller._get_or_create_state(transition)
                            # Initialize enablement state for this transition
                            behavior = controller._get_behavior(transition)
                            is_source = getattr(transition, 'is_source', False)
                            if is_source:
                                pass
                                # Source transitions are always enabled
                                state.enablement_time = controller.time
                                if hasattr(behavior, 'set_enablement_time'):
                                    behavior.set_enablement_time(controller.time)
                    
                    if missing_count > 0:
                        pass
                        # print(f"[RESET] ✅ Registered {missing_count} missing transitions")
                    else:
                        pass
                        # print(f"[RESET] ✅ All {len(manager.transitions)} transitions properly registered")
                    
                    # CRITICAL LIFECYCLE FIX #2: Invalidate model adapter caches
                    # After load, the model adapter may have stale arc/place/transition caches
                    # Drawing an arc triggers cache invalidation which "wakes up" the simulation
                    # We must explicitly invalidate here to ensure proper simulation state
                    if hasattr(controller, 'model_adapter') and controller.model_adapter:
                        controller.model_adapter.invalidate_caches()
                        # print(f"[RESET] ✅ Model adapter caches invalidated")
        except Exception as e:
            pass
            # print(f"[RESET] Error resetting simulation: {e}")
            import traceback
            traceback.print_exc()
        

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
        swissknife_widget.set_vexpand(False)
        
        # Add to overlay
        overlay_widget.add_overlay(swissknife_widget)
        
        # Wire SwissKnifePalette signals
        swissknife_palette.connect('tool-activated', self._on_swissknife_tool_activated, canvas_manager, drawing_area)
        swissknife_palette.connect('mode-change-requested', self._on_swissknife_mode_change_requested, canvas_manager, drawing_area)
        swissknife_palette.connect('simulation-step-executed', self._on_simulation_step, drawing_area)
        swissknife_palette.connect('simulation-reset-executed', self._on_simulation_reset, drawing_area)
        swissknife_palette.connect('simulation-settings-changed', self._on_simulation_settings_changed, drawing_area)
        swissknife_palette.connect('float-toggled', self._on_swissknife_float_toggled, swissknife_widget, drawing_area)
        swissknife_palette.connect('position-changed', self._on_swissknife_position_changed, swissknife_widget, drawing_area)
        
        # ============================================================
        # PHASE 4: Create simulation controller for this canvas
        # ============================================================
        # Canvas-centric design: One controller per drawing_area
        # This wiring survives SwissPalette refactoring because:
        #   1. Controller keyed by drawing_area (stable, won't change)
        #   2. Palette can access controller through overlay_manager
        #   3. Signal handlers use get_canvas_controller() accessor
        # 
        # When SwissPalette refactoring happens:
        #   - Controller creation stays here (unchanged)
        #   - Signal handler names may change (easy to find and update)
        #   - Controller access pattern stays the same (drawing_area → controller)
        simulation_controller = SimulationController(canvas_manager)
        # CRITICAL: Store drawing_area reference in controller so Report Panel can find its document
        simulation_controller._drawing_area = drawing_area
        self.simulation_controllers[drawing_area] = simulation_controller
        
        # ============================================================
        # REPORT PANEL INTEGRATION: Wire new controller to Report Panel
        # ============================================================
        # When a new controller is created (File→New, interactive model, etc.),
        # automatically wire it to the Report Panel so simulation data appears
        # print(f"[CONTROLLER_WIRE] Controller created for canvas")
        # print(f"[CONTROLLER_WIRE] Has report_panel_loader: {hasattr(self, 'report_panel_loader')}")
        if hasattr(self, 'report_panel_loader'):
            pass
            # print(f"[CONTROLLER_WIRE] report_panel_loader = {self.report_panel_loader}")
            if self.report_panel_loader and hasattr(self.report_panel_loader, 'panel'):
                pass
                # print(f"[CONTROLLER_WIRE] report_panel_loader.panel = {self.report_panel_loader.panel}")
                
        if hasattr(self, 'report_panel_loader') and self.report_panel_loader:
            try:
                print(f"[CONTROLLER_WIRE] ❌ Using GLOBAL report_panel_loader (WRONG for multi-document!)")
                print(f"[CONTROLLER_WIRE] This should use per-document report_panel_loader instead")
                self.report_panel_loader.panel.set_controller(simulation_controller)
            except Exception as e:
                print(f"[CONTROLLER_WIRE] Failed to wire controller: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[CONTROLLER_WIRE] ⚠️  GLOBAL report_panel_loader not available (expected for multi-doc)")
        
        # ============================================================
        # VIABILITY PANEL INTEGRATION: Wire simulation complete callback
        # ============================================================
        # When simulation completes, notify the PER-DOCUMENT Viability Panel so it can:
        #  1. Extract simulation results (dead transitions, inactive places)
        #  2. Feed data to the ViabilityObserver
        #  3. Trigger rule evaluation
        #  4. Refresh categories with detected issues
        # NOTE: This is now handled in per-document creation above
        # This fallback is for backward compatibility with global singleton
        if hasattr(self, 'viability_panel_loader') and self.viability_panel_loader:
            try:
                viability_panel = self.viability_panel_loader.panel
                if viability_panel and hasattr(viability_panel, 'on_simulation_complete'):
                    # Store existing callback if any
                    existing_callback = getattr(simulation_controller, 'on_simulation_complete', None)
                    
                    # Create combined callback that calls both
                    def combined_callback():
                        if existing_callback and callable(existing_callback):
                            existing_callback()
                        viability_panel.on_simulation_complete()
                    
                    simulation_controller.on_simulation_complete = combined_callback
                    print(f"[CONTROLLER_WIRE] ✅ Wired simulation_complete → GLOBAL ViabilityPanel (fallback)")
                else:
                    print(f"[CONTROLLER_WIRE] ⚠️ Global viability panel or method not available yet")
            except AttributeError as e:
                print(f"[CONTROLLER_WIRE] ⚠️ Global viability panel loader not attached yet: {e}")
            except Exception as e:
                print(f"[CONTROLLER_WIRE] Failed to wire global viability callback: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[CONTROLLER_WIRE] ⚠️ Global viability panel loader not available (using per-document instead)")
        
        # ============================================================
        # GLOBAL-SYNC: Integrate with canvas lifecycle system
        # ============================================================
        # If lifecycle system is enabled, register this canvas with it.
        # This provides coordinated management of all canvas components.
        if self.lifecycle_adapter:
            try:
                pass
                # Register canvas with adapter (maintains legacy dict compatibility)
                self.lifecycle_adapter.register_canvas(
                    drawing_area,
                    canvas_manager,
                    simulation_controller,
                    swissknife_palette
                )
            except Exception as e:
                pass  # Failed to register canvas, continuing with legacy management
        
        # Store reference for mode switching
        if drawing_area not in self.overlay_managers:
            self.overlay_managers[drawing_area] = type('obj', (object,), {})()
        self.overlay_managers[drawing_area].swissknife_palette = swissknife_palette
        # PHASE 4: Also store controller reference for palette access
        self.overlay_managers[drawing_area].simulation_controller = simulation_controller
        
        # MULTI-DOCUMENT: Create per-document report data container
        from shypn.ui.panels.report.document_report_data import DocumentReportData
        self.overlay_managers[drawing_area].report_data = DocumentReportData(drawing_area=drawing_area)
        
        # MULTI-DOCUMENT: Create per-document Report Panel
        # Each document gets its own Report Panel instance to maintain independent state
        print(f"[PER_DOC_REPORT] Checking if report_panel_loader exists for drawing_area {id(drawing_area)}")
        if not hasattr(self.overlay_managers[drawing_area], 'report_panel_loader'):
            print(f"[PER_DOC_REPORT] Creating NEW per-document Report Panel")
            from shypn.helpers.report_panel_loader import ReportPanelLoader
            
            # Pass the ModelCanvasLoader (self) so Report Panel can access get_current_model()
            report_panel_loader = ReportPanelLoader(project=None, model_canvas_loader=self)
            report_panel_loader.load()
            print(f"[PER_DOC_REPORT] ReportPanelLoader created and loaded")
            
            # Wire float/attach callbacks from main app (stored in model_canvas_loader)
            if hasattr(self, 'on_report_float') and hasattr(self, 'on_report_attach'):
                report_panel_loader.on_float_callback = self.on_report_float
                report_panel_loader.on_attach_callback = self.on_report_attach
            
            # Set parent window for Wayland transient relationship
            if hasattr(self, 'main_window') and self.main_window:
                report_panel_loader.parent_window = self.main_window
            
            # DON'T call add_to_stack() - Report panel is manually managed per-document
            # Each tab switch will manually pack_start() the appropriate panel
            
            # Wire controller to this document's Report Panel
            if hasattr(report_panel_loader, 'panel') and report_panel_loader.panel:
                print(f"[CONTROLLER_WIRE] ✅ Wiring controller to PER-DOCUMENT Report Panel (drawing_area {id(drawing_area)})")
                report_panel_loader.panel.set_controller(simulation_controller)
                print(f"[CONTROLLER_WIRE] ✅ Controller set successfully")
                
                # CRITICAL: Set the actual model manager for ModelsCategory
                # Get the model manager for this specific drawing_area
                model_manager = self.overlay_managers[drawing_area].canvas_manager
                if model_manager:
                    report_panel_loader.panel.set_model_canvas(model_manager)
                    print(f"[CONTROLLER_WIRE] ✅ Set model_manager: {len(model_manager.places)} places, {len(model_manager.transitions)} transitions")
                
                # Connect Topology Panel to Report Panel for analysis data
                if hasattr(self, 'topology_panel_loader') and self.topology_panel_loader:
                    if hasattr(self.topology_panel_loader, 'panel') and self.topology_panel_loader.panel:
                        report_panel_loader.panel.set_topology_panel(self.topology_panel_loader.panel)
                        print(f"[CONTROLLER_WIRE] ✅ Connected Topology Panel to Report Panel")
                        
                        # Trigger immediate refresh to show any existing analysis data
                        report_panel_loader.panel.refresh_all()
                        print(f"[CONTROLLER_WIRE] ✅ Refreshed Report Panel to load topology data")
                
                # NOTE: Locality sync callback will be wired later in set_right_panel_loader()
                # when the transition panel is guaranteed to exist
            
            self.overlay_managers[drawing_area].report_panel_loader = report_panel_loader
            # print(f"[MODEL_CANVAS_LOADER] Created per-document Report Panel for drawing_area {id(drawing_area)}")
        
        # ============================================================
        # PER-DOCUMENT VIABILITY PANEL: One instance per model/document
        # ============================================================
        # Each document gets its own Viability Panel instance to maintain independent state
        print(f"[PER_DOC_VIABILITY] Checking if viability_panel_loader exists for drawing_area {id(drawing_area)}")
        if not hasattr(self.overlay_managers[drawing_area], 'viability_panel_loader'):
            print(f"[PER_DOC_VIABILITY] Creating NEW per-document Viability Panel")
            from shypn.helpers.viability_panel_loader import ViabilityPanelLoader
            
            # Create per-document viability panel (panel is created in __init__)
            viability_panel_loader = ViabilityPanelLoader(model=None)
            print(f"[PER_DOC_VIABILITY] ViabilityPanelLoader created")
            
            # Wire model_canvas_loader so viability can access current model
            viability_panel_loader.set_model_canvas_loader(self)
            
            # Set parent window for Wayland transient relationship
            if hasattr(self, 'main_window') and self.main_window:
                viability_panel_loader.parent_window = self.main_window
            
            # Wire controller to this document's Viability Panel
            if hasattr(viability_panel_loader, 'panel') and viability_panel_loader.panel:
                print(f"[CONTROLLER_WIRE] ✅ Wiring simulation callback to PER-DOCUMENT Viability Panel (drawing_area {id(drawing_area)})")
                
                # Get the panel
                viability_panel = viability_panel_loader.panel
                
                # Set the drawing area so the panel knows which document it belongs to
                if hasattr(viability_panel, 'set_drawing_area'):
                    viability_panel.set_drawing_area(drawing_area)
                
                # Set the model canvas loader (not canvas_manager!)
                # The panel needs model_canvas_loader to access get_current_knowledge_base()
                viability_panel.set_model_canvas(self)
                print(f"[CONTROLLER_WIRE] ✅ Set model_canvas_loader for Viability Panel")
                
                # Wire simulation complete callback
                if hasattr(viability_panel, 'on_simulation_complete'):
                    existing_callback = getattr(simulation_controller, 'on_simulation_complete', None)
                    print(f"[CONTROLLER_WIRE] Viability capturing existing callback: {existing_callback}")
                    print(f"[CONTROLLER_WIRE]   Callable: {callable(existing_callback) if existing_callback else False}")
                    
                    # Check if existing callback is already a Viability Panel callback
                    # If so, skip to avoid infinite wrapping
                    is_viability_callback = (
                        existing_callback and 
                        hasattr(existing_callback, '__self__') and 
                        existing_callback.__self__.__class__.__name__ == 'ViabilityPanel'
                    )
                    
                    if is_viability_callback:
                        print(f"[CONTROLLER_WIRE] ⚠️  Existing callback is already a Viability Panel callback, skipping to avoid double-wrap")
                    else:
                        print(f"[CONTROLLER_WIRE] Creating combined callback to preserve Report Panel callback")
                        
                        def combined_callback():
                            print(f"[VIABILITY_COMBINED] Combined callback executing...")
                            if existing_callback and callable(existing_callback):
                                print(f"[VIABILITY_COMBINED] Calling existing callback (Report Panel)...")
                                existing_callback()
                                print(f"[VIABILITY_COMBINED] Existing callback completed")
                            else:
                                print(f"[VIABILITY_COMBINED] No existing callback to call")
                            print(f"[VIABILITY_COMBINED] Calling Viability Panel callback...")
                            viability_panel.on_simulation_complete()
                            print(f"[VIABILITY_COMBINED] Viability Panel callback completed")
                        
                        simulation_controller.on_simulation_complete = combined_callback
                        print(f"[CONTROLLER_WIRE] ✅ Wired simulation_complete → ViabilityPanel")
                
                # Connect Topology Panel to Viability Panel for analysis data
                if hasattr(self, 'topology_panel_loader') and self.topology_panel_loader:
                    if hasattr(self.topology_panel_loader, 'panel') and self.topology_panel_loader.panel:
                        viability_panel.set_topology_panel(self.topology_panel_loader.panel)
                        print(f"[CONTROLLER_WIRE] ✅ Connected Topology Panel to Viability Panel")
            
            self.overlay_managers[drawing_area].viability_panel_loader = viability_panel_loader
            print(f"[PER_DOC_VIABILITY] ✓ Created per-document Viability Panel for drawing_area {id(drawing_area)}")
        
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
        
        # ============================================================
        # WIRE RIGHT PANEL ANALYSES: Set data_collector on initial load
        # ============================================================
        # The data_collector is created by SimulateToolsPaletteLoader
        # and should be wired immediately after palette creation.
        # This ensures the Analyses Panel is functional on first model load,
        # not just after tab switches.
        
        if self.right_panel_loader and drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            if hasattr(overlay_manager, 'swissknife_palette'):
                swissknife = overlay_manager.swissknife_palette
                # Access widget_palette_instances dict directly (not through registry)
                if hasattr(swissknife, 'widget_palette_instances'):
                    simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
                    if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
                        data_collector = simulate_tools_palette.data_collector
                        self.right_panel_loader.set_data_collector(data_collector)
    
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
            pass
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
            pass
            # PHASE 4: Check permission before activating structural tools
            # This uses canvas-centric access pattern that survives SwissPalette refactoring
            controller = self.get_canvas_controller(drawing_area)
            if controller:
                allowed, reason = controller.interaction_guard.check_tool_activation(tool_id)
                if not allowed:
                    self._show_info_message(reason)
                    return  # Don't activate the tool
            
            canvas_manager.set_tool(tool_id)
            drawing_area.queue_draw()
        
        # Selection tools
        elif tool_id == 'select':
            canvas_manager.clear_tool()
            drawing_area.queue_draw()
        
        elif tool_id == 'lasso':
            pass
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
            self._on_layout_auto_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_hierarchical':
            self._on_layout_hierarchical_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_force':
            self._on_layout_force_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_settings':
            pass
            # Toggle layout parameter panel
            palette.parameter_manager.toggle_panel('layout')
    
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
        # TODO: Implement mode switching logic when needed
        # current_mode = self._get_current_mode(drawing_area)
        # if requested_mode != current_mode:
        #     self._switch_canvas_mode(drawing_area, requested_mode)
        pass
    
    def _on_swissknife_float_toggled(self, palette, is_floating, widget, drawing_area):
        """Handle float/attach toggle from SwissKnifePalette.
        
        Repositions the palette between floating (center/variable) and 
        attached (bottom/center) states.
        
        Args:
            palette: SwissKnifePalette instance
            is_floating: True if now floating, False if attached
            widget: The palette widget to reposition
            drawing_area: GtkDrawingArea for canvas reference (unused now)
        """
        if is_floating:
            pass
            # Floating mode: use START alignment for absolute positioning via margins
            # Combined with hexpand/vexpand=False to maintain natural size
            widget.set_halign(Gtk.Align.START)
            widget.set_valign(Gtk.Align.START)
            widget.set_hexpand(False)
            widget.set_vexpand(False)
            
            # DON'T set size_request - let widget maintain its natural size
            # This allows sub-palettes and parameter panels to expand/collapse naturally
            
            # Keep current position (margins stay as they are)
        else:
            pass
            # Attached mode: move to bottom center
            widget.set_halign(Gtk.Align.CENTER)
            widget.set_valign(Gtk.Align.END)
            widget.set_hexpand(False)
            widget.set_vexpand(False)
            
            # Clear size request to allow natural sizing in attached mode
            widget.set_size_request(-1, -1)
            
            # Get overlay widget (viewport container) - this is the actual visible area
            # Navigation: widget (palette) -> overlay (viewport container)
            overlay_widget = widget.get_parent()
            if overlay_widget:
                pass
                # Ensure margin keeps palette visible in viewport
                viewport_height = overlay_widget.get_allocated_height()
                palette_height = widget.get_allocated_height()
                
                # Calculate safe margin (keep at least 10px from bottom)
                min_margin = 20
                max_margin = max(min_margin, viewport_height - palette_height - 10)
                margin = min(min_margin, max_margin)
                
                widget.set_margin_bottom(margin)
            else:
                pass
                # Fallback if parent not available
                widget.set_margin_bottom(20)
            
            widget.set_margin_top(0)
            widget.set_margin_start(0)
            widget.set_margin_end(0)
    
    def _on_swissknife_position_changed(self, palette, dx, dy, widget, drawing_area):
        """Handle position change from SwissKnifePalette drag.
        
        Updates the widget margins to move it by the delta amounts.
        Uses viewport-aware bounds to keep palette mostly visible.
        
        Args:
            palette: SwissKnifePalette instance
            dx: Horizontal delta from drag (screen space)
            dy: Vertical delta from drag (screen space)
            widget: The palette widget to reposition
            drawing_area: GtkDrawingArea for canvas reference (unused now)
        """
        # Get overlay widget (viewport container) - this is the actual visible area
        # Navigation: widget (palette) -> overlay (viewport container)
        overlay_widget = widget.get_parent()
        if not overlay_widget:
            return
        
        # Get viewport dimensions from overlay (actual window size)
        viewport_width = overlay_widget.get_allocated_width()
        viewport_height = overlay_widget.get_allocated_height()
        
        # Get palette dimensions
        palette_width = widget.get_allocated_width()
        palette_height = widget.get_allocated_height()
        
        # Get current margins
        current_left = widget.get_margin_start()
        current_top = widget.get_margin_top()
        
        # Apply delta with viewport-aware bounds
        # Keep at least min_visible pixels of palette on screen
        min_visible = 50  # Minimum pixels that must stay visible
        
        # Calculate bounds
        # Left bound: palette can go left until only min_visible pixels show
        min_left = -palette_width + min_visible
        # Right bound: palette can go right until only min_visible pixels show
        max_left = viewport_width - min_visible
        # Top bound: palette can go up until only min_visible pixels show
        min_top = -palette_height + min_visible
        # Bottom bound: palette can go down until only min_visible pixels show
        max_top = viewport_height - min_visible
        
        # Apply delta and clamp to bounds
        new_left = max(min_left, min(max_left, int(current_left + dx)))
        new_top = max(min_top, min(max_top, int(current_top + dy)))
        
        widget.set_margin_start(new_left)
        widget.set_margin_top(new_top)

    def _on_simulation_step(self, palette, time, drawing_area):
        """Handle simulation step - redraw canvas to show updated token state.
        
        Args:
            palette: SimulateToolsPaletteLoader that emitted the signal
            time: Current simulation time
            drawing_area: GtkDrawingArea widget to redraw
        """
        # Debug: Log redraw requests (only log every 100 steps to avoid spam)
        if not hasattr(self, '_step_count'):
            self._step_count = 0
        self._step_count += 1
        if self._step_count % 100 == 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[CANVAS_REDRAW] Step {self._step_count}, time={time:.3f}, requesting queue_draw()")
        
        drawing_area.queue_draw()

    def _on_simulation_reset(self, palette, drawing_area):
        """Handle simulation reset - blank analysis plots immediately.
        
        IMPORTANT: Force immediate canvas blanking by calling update_plot() directly
        instead of setting needs_update=True. This ensures plots are cleared synchronously
        with the reset action, providing immediate visual feedback to the user.
        
        Args:
            palette: SwissKnifePalette that forwarded the signal
            drawing_area: GtkDrawingArea widget for the canvas
        """
        if self.right_panel_loader:
            pass
            # Place panel - force immediate update
            if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
                panel = self.right_panel_loader.place_panel
                panel.last_data_length.clear()
                # Force immediate canvas blank/update - don't wait for periodic check
                if panel.selected_objects:
                    panel.update_plot()  # Will show empty plot with 0 data
                else:
                    panel._show_empty_state()
            
            # Transition panel - force immediate update
            if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                panel = self.right_panel_loader.transition_panel
                panel.last_data_length.clear()
                # Force immediate canvas blank/update - don't wait for periodic check
                if panel.selected_objects:
                    panel.update_plot()  # Will show empty plot with 0 data
                else:
                    panel._show_empty_state()
            
            # PHASE 1-2 FIX: Reset Dynamic Analyses Panel plots
            # This clears all real-time plots (transitions, places, diagnostics)
            if hasattr(self.right_panel_loader, 'dynamic_analyses_panel') and self.right_panel_loader.dynamic_analyses_panel:
                try:
                    self.right_panel_loader.dynamic_analyses_panel.reset()
                except Exception as e:
                    print(f"Warning: Could not reset dynamic analyses panel: {e}")

    def _on_simulation_settings_changed(self, palette, drawing_area):
        """Handle simulation settings change.
        
        Args:
            palette: SimulateToolsPaletteLoader that emitted the signal
            drawing_area: GtkDrawingArea widget
        """
        # Settings changed - may need to update visualization
        # Currently just redraw the canvas
        drawing_area.queue_draw()

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
            pass
            # PHASE 4: Check permission before activating tools
            # Canvas-centric access ensures this survives SwissPalette refactoring
            controller = self.get_canvas_controller(drawing_area)
            if controller:
                allowed, reason = controller.interaction_guard.check_tool_activation(tool_name)
                if not allowed:
                    self._show_info_message(reason)
                    tools_palette.clear_selection()  # Deselect the tool button
                    return
            
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
        # Grab focus so keyboard shortcuts work
        if not widget.has_focus():
            widget.grab_focus()
        
        state = self._drag_state[widget]
        arc_state = self._arc_state[widget]
        lasso_state = self._lasso_state.get(widget, {})
        
        # Check if lasso mode is active
        if lasso_state.get('active', False) and event.button == 1:
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            # Store Ctrl state at press time for multi-select support
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            lasso_state['is_ctrl'] = is_ctrl
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
                    pass
                    # Show error dialog instead of silent failure
                    # Defensive check for parent window (Wayland compatibility)
                    parent = self.parent_window if self.parent_window else None
                    dialog = Gtk.MessageDialog(
                        transient_for=parent,
                        flags=0,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Cannot Create Arc"
                    )
                    dialog.set_keep_above(True)  # Ensure dialog stays on top
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
                        pass
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
                    pass
                    # Ctrl+Click on selected object → Deselect (remove from multi-selection)
                    if is_ctrl:
                        manager.selection_manager.deselect(clicked_obj)
                        widget.queue_draw()
                        # Record for double-click detection
                        click_state['last_click_time'] = current_time
                        click_state['last_click_obj'] = clicked_obj
                        return True
                    
                    # Already selected (no Ctrl) - start drag immediately
                    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
                    state['active'] = True
                    state['button'] = event.button
                    state['start_x'] = event.x
                    state['start_y'] = event.y
                    state['is_panning'] = False
                    state['is_rect_selecting'] = False
                    # Record for double-click detection
                    click_state['last_click_time'] = current_time
                    click_state['last_click_obj'] = clicked_obj
                elif not is_double_click:
                    pass
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
                    pass
                    # Double-click behavior: enter edit mode
                    # Note: Legacy block that prevented edit mode for parallel arcs has been removed
                    # Users now have full manual control over curved arc transformations
                    
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
                pass
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
            if lasso_state['selector'].is_active and event.button == 1:
                pass
                # Use Ctrl state from button press (not release) for consistent behavior
                is_ctrl = lasso_state.get('is_ctrl', False)
                lasso_state['selector'].finish_lasso(multi=is_ctrl)
                # Deactivate lasso mode completely after selection
                lasso_state['active'] = False
                # Clear stored Ctrl state
                lasso_state['is_ctrl'] = False
                # Force redraw to remove lasso visualization
                widget.queue_draw()
                return True
        
        # End transformation if active
        if state.get('is_transforming', False):
            if manager.editing_transforms.end_transformation():
                pass
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
            pass
            # Record move operation for undo if objects moved
            if move_data and hasattr(manager, 'undo_manager'):
                from shypn.edit.undo_operations import MoveOperation
                manager.undo_manager.push(MoveOperation(move_data))
            
            # Reset drag state immediately to stop further drag processing
            state['active'] = False
            state['button'] = 0
            widget.queue_draw()
            return True
            
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
        
        # Track pointer position for paste-at-pointer functionality
        self._last_pointer_world_x = world_x
        self._last_pointer_world_y = world_y
        
        # Update lasso path if active
        if lasso_state.get('active', False) and lasso_state.get('selector'):
            if lasso_state['selector'].is_active:
                lasso_state['selector'].add_point(world_x, world_y)
                widget.queue_draw()
                return True
        
        # FIX: Update arc preview with target validation
        if manager.is_tool_active() and manager.get_tool() == 'arc' and (arc_state['source'] is not None):
            pass
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
            pass
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
                
                # Use pan() method which handles rotation correctly
                # Reset pan to start position first, then apply delta
                manager.pan_x = state['start_pan_x']
                manager.pan_y = state['start_pan_y']
                manager.pan(dx, dy)
                
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
        
        # Delete key - delete selected objects
        if event.keyval == Gdk.KEY_Delete or event.keyval == Gdk.KEY_KP_Delete:
            selected = manager.selection_manager.get_selected_objects(manager)
            if selected:
                pass
                # TODO: Implement undo support for delete
                # from shypn.edit.undo_operations import DeleteOperation
                # Store delete data for undo
                # delete_data = []
                # for obj in selected:
                #     delete_data.append(manager.serialize_object_for_undo(obj))
                
                # Delete all selected objects
                for obj in selected:
                    self._delete_object(manager, obj)
                
                # Push to undo stack
                # if hasattr(manager, 'undo_manager') and delete_data:
                #     manager.undo_manager.push(DeleteOperation(delete_data, manager))
                
                widget.queue_draw()
                return True
        
        # Cut (Ctrl+X) - check both lowercase and uppercase
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_x or event.keyval == Gdk.KEY_X):
            selected = manager.selection_manager.get_selected_objects(manager)
            if selected:
                self._cut_selection(manager, widget)
                return True
        
        # Copy (Ctrl+C) - check both lowercase and uppercase
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_c or event.keyval == Gdk.KEY_C):
            selected = manager.selection_manager.get_selected_objects(manager)
            if selected:
                self._copy_selection(manager)
                return True
        
        # Paste (Ctrl+V) - check both lowercase and uppercase
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_v or event.keyval == Gdk.KEY_V):
            if hasattr(self, '_clipboard') and self._clipboard:
                pass
                # Paste at last known pointer position
                self._paste_selection(
                    manager, 
                    widget, 
                    self._last_pointer_world_x, 
                    self._last_pointer_world_y
                )
                return True
        
        # Save (Ctrl+S) - check both lowercase and uppercase
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_s or event.keyval == Gdk.KEY_S):
            pass
            # Trigger save for current document
            if hasattr(self, 'file_explorer_panel') and self.file_explorer_panel:
                self.file_explorer_panel.save_current_document()
                return True
        
        # Save As (Ctrl+Shift+S) - check both lowercase and uppercase
        if is_ctrl and is_shift and (event.keyval == Gdk.KEY_s or event.keyval == Gdk.KEY_S):
            pass
            # Trigger save as for current document
            if hasattr(self, 'file_explorer_panel') and self.file_explorer_panel:
                self.file_explorer_panel.save_current_document_as()
                return True
        
        # Open (Ctrl+O) - check both lowercase and uppercase
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_o or event.keyval == Gdk.KEY_O):
            pass
            # Trigger open file dialog (FileChooser, not system file explorer)
            if hasattr(self, 'file_explorer_panel') and self.file_explorer_panel:
                self.file_explorer_panel.open_document()
                return True
        
        # Undo (Ctrl+Z) - check both lowercase and uppercase
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_z or event.keyval == Gdk.KEY_Z):
            pass
            # TODO: Implement undo/redo functionality
            # Undo/redo system not yet implemented
            # For now, just consume the event silently
            return True
        
        # Redo (Ctrl+Shift+Z or Ctrl+Y) - check both lowercase and uppercase
        if (is_ctrl and is_shift and (event.keyval == Gdk.KEY_z or event.keyval == Gdk.KEY_Z)) or \
           (is_ctrl and not is_shift and (event.keyval == Gdk.KEY_y or event.keyval == Gdk.KEY_Y)):
            # TODO: Implement undo/redo functionality
            # Undo/redo system not yet implemented
            # For now, just consume the event silently
            return True
        
        if event.keyval == Gdk.KEY_Escape:
            pass
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
            
            # Cancel drag if active
            if manager.selection_manager.cancel_drag():
                widget.queue_draw()
                return True
            
            # Exit edit mode if active
            if manager.selection_manager.is_edit_mode():
                manager.selection_manager.exit_edit_mode()
                widget.queue_draw()
                return True
            
            # Close context menu if open
            if hasattr(self, '_canvas_context_menu') and self._canvas_context_menu:
                if isinstance(self._canvas_context_menu, Gtk.Menu):
                    self._canvas_context_menu.popdown()
                    return True
            
            # Finally, clear all selections if any exist
            if manager.selection_manager.has_selection():
                manager.clear_all_selections()
                widget.queue_draw()
                return True
        
        return False

    def _on_draw(self, drawing_area, cr, width, height, manager):
        """Draw callback for the canvas.
        
        Uses Cairo transformation approach (legacy-compatible):
            pass
        - Apply cr.scale() and cr.translate() for automatic coordinate transformation
        - Objects render in world coordinates, Cairo scales them automatically
        - Line widths compensated to maintain constant pixel size
        - Grid drawn BEFORE rotation (stays fixed in screen space)
        - Model objects drawn AFTER rotation (rotate with canvas)
        
        Args:
            drawing_area: GtkDrawingArea being drawn.
            cr: Cairo context.
            width: Viewport width in pixels.
            height: Viewport height in pixels.
            manager: ModelCanvasManager instance.
        """
        if manager.viewport_width != width or manager.viewport_height != height:
            manager.set_viewport_size(width, height)
        
        # Execute deferred fit_to_page if pending (after viewport size is known)
        if hasattr(manager, '_fit_to_page_pending') and manager._fit_to_page_pending:
            horizontal_offset = getattr(manager, '_fit_to_page_horizontal_offset', 0)
            vertical_offset = getattr(manager, '_fit_to_page_vertical_offset', 0)
            manager._fit_to_page_pending = False  # Clear flag before execution
            manager.fit_to_page(
                padding_percent=manager._fit_to_page_padding,
                deferred=False,
                horizontal_offset_percent=horizontal_offset,
                vertical_offset_percent=vertical_offset
            )
        
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.paint()
        
        # Apply ALL transformations for infinite rotating canvas
        # Transformation order (Cairo applies in reverse):
        #   Code order: zoom/pan → rotation
        #   Actual order: rotation → zoom/pan (rotation happens first in world space)
        cr.save()
        
        # STEP 1: Apply zoom and pan transformations
        # These establish the viewport position and scale in world space
        cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
        cr.scale(manager.zoom, manager.zoom)
        
        # STEP 2: Apply rotation around viewport center
        # This rotates the entire zoomed/panned coordinate system
        # Rotation center needs to be in world coordinates (account for zoom/pan)
        center_world_x = width / (2.0 * manager.zoom) - manager.pan_x
        center_world_y = height / (2.0 * manager.zoom) - manager.pan_y
        
        rotation = manager.transformation_manager.get_rotation()
        if rotation and rotation.angle_degrees != 0:
            cr.translate(center_world_x, center_world_y)
            cr.rotate(rotation.angle_radians)
            cr.translate(-center_world_x, -center_world_y)
        
        # STEP 3: Draw grid with all transformations applied (infinite canvas effect)
        # Grid bounds are calculated to cover the entire rotated viewport
        manager.draw_grid(cr)
        
        # Render all objects (these will be rotated)
        all_objects = manager.get_all_objects()
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
                pass
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
                pass
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
        manager.mark_canvas_clean()

    def _draw_arc_preview(self, cr, arc_state, manager):
        """Draw orange preview line for arc creation.
        
        Args:
            cr: Cairo context.
            arc_state: Arc state dictionary with 'source' and 'cursor_pos'.
            manager: ModelCanvasManager instance.
        """
        source = arc_state['source']
        cursor_x, cursor_y = arc_state['cursor_pos']
        hovered_target = arc_state.get('hovered_target')
        
        src_x, src_y = (source.x, source.y)
        dx = cursor_x - src_x
        dy = cursor_y - src_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return
        ux, uy = (dx / dist, dy / dist)
        
        # Calculate source boundary point
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
        
        # Calculate end point (cursor or target boundary)
        end_x = cursor_x
        end_y = cursor_y
        
        # Detect parallel arc and calculate offset
        parallel_offset = 0.0
        if hovered_target and hovered_target != source:
            pass
            # Check if this would create a parallel arc
            existing_arcs = [arc for arc in manager.arcs 
                           if (arc.source == source and arc.target == hovered_target) or
                              (arc.source == hovered_target and arc.target == source)]
            
            if existing_arcs:
                pass
                # Calculate offset direction based on arc direction
                # Same direction as existing arc: small offset (±15px)
                # Opposite direction: large offset (±50px)
                existing_arc = existing_arcs[0]
                same_direction = (existing_arc.source == source and existing_arc.target == hovered_target)
                opposite_direction = (existing_arc.source == hovered_target and existing_arc.target == source)
                
                if opposite_direction:
                    pass
                    # Opposite direction: offset to opposite sides
                    parallel_offset = -50.0  # New arc gets negative offset
                elif same_direction:
                    pass
                    # Same direction: both offset to same side (shouldn't happen for new arc, but handle it)
                    parallel_offset = 15.0
            
            # Calculate target boundary point
            # Only for Place/Transition, not Arc (arcs don't have .x/.y attributes)
            if isinstance(hovered_target, (Place, Transition)):
                tgt_x, tgt_y = hovered_target.x, hovered_target.y
                dx_to_target = tgt_x - src_x
                dy_to_target = tgt_y - src_y
                dist_to_target = math.sqrt(dx_to_target * dx_to_target + dy_to_target * dy_to_target)
                
                if dist_to_target > 1e-6:
                    ux_target = dx_to_target / dist_to_target
                    uy_target = dy_to_target / dist_to_target
                    
                    if isinstance(hovered_target, Place):
                        tgt_radius = hovered_target.radius
                    elif isinstance(hovered_target, Transition):
                        w = hovered_target.width if hovered_target.horizontal else hovered_target.height
                        h = hovered_target.height if hovered_target.horizontal else hovered_target.width
                        tgt_radius = max(w, h) / 2.0
                    else:
                        tgt_radius = 20.0
                    
                    end_x = tgt_x - ux_target * tgt_radius
                    end_y = tgt_y - uy_target * tgt_radius
        
        # Apply parallel offset perpendicular to arc direction
        if abs(parallel_offset) > 1e-6:
            pass
            # Calculate perpendicular direction (rotate 90 degrees)
            perp_x = -uy
            perp_y = ux
            
            # Apply offset to both start and end points
            start_x += perp_x * parallel_offset
            start_y += perp_y * parallel_offset
            end_x += perp_x * parallel_offset
            end_y += perp_y * parallel_offset
        
        # Convert to screen coordinates
        start_sx, start_sy = manager.world_to_screen(start_x, start_y)
        end_sx, end_sy = manager.world_to_screen(end_x, end_y)
        
        # Draw the preview line
        cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
        cr.set_line_width(2.0)
        cr.move_to(start_sx, start_sy)
        cr.line_to(end_sx, end_sy)
        cr.stroke()
        
        # Draw arrowhead
        arrow_len = 11.0
        arrow_width = 6.0
        angle = math.atan2(end_y - start_y, end_x - start_x)
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
                pass
                # Use popup_at_pointer() instead of deprecated popup() for Wayland compatibility
                menu.popup_at_pointer(None)

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
            pass
            # For parallel arcs, don't include "Edit Mode" option
            menu_items = [('Edit Properties...', lambda: self._on_object_properties(obj, manager, drawing_area)), None, ('Delete', lambda: self._on_object_delete(obj, manager, drawing_area))]
        else:
            pass
            # For normal objects, include "Edit Mode" option
            menu_items = [('Edit Properties...', lambda: self._on_object_properties(obj, manager, drawing_area)), ('Edit Mode (Double-click)', lambda: self._on_object_edit_mode(obj, manager, drawing_area)), None, ('Delete', lambda: self._on_object_delete(obj, manager, drawing_area))]
        if isinstance(obj, Transition):
            type_submenu_item = Gtk.MenuItem(label='Change Type ►')
            type_submenu = Gtk.Menu()
            current_type = getattr(obj, 'transition_type', 'continuous')
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
            pass
            # Add arc transformation submenu
            from shypn.utils.arc_transform import is_straight, is_curved, is_inhibitor, is_normal
            from shypn.netobjs.place import Place
            from shypn.netobjs.transition import Transition
            from shypn.netobjs.test_arc import TestArc
            from shypn.netobjs.inhibitor_arc import InhibitorArc
            
            transform_submenu_item = Gtk.MenuItem(label='Transform Arc ►')
            transform_submenu = Gtk.Menu()
            
            # Check arc type capabilities
            can_be_inhibitor = isinstance(obj.source, Place) and isinstance(obj.target, Transition)
            can_be_test = isinstance(obj.source, Place) and isinstance(obj.target, Transition)
            is_test = isinstance(obj, TestArc)
            is_inhibitor_arc = isinstance(obj, InhibitorArc)
            is_normal_arc = not is_test and not is_inhibitor_arc
            
            # Curve/Straight transformation options
            if is_curved(obj):
                pass
                # Curved arc can be made straight
                straight_item = Gtk.MenuItem(label='Transform to Straight')
                straight_item.connect('activate', lambda w: self._on_arc_make_straight(obj, manager, drawing_area))
                straight_item.show()
                transform_submenu.append(straight_item)
            elif is_straight(obj):
                pass
                # Straight arc can be made curved
                curved_item = Gtk.MenuItem(label='Transform to Curved')
                curved_item.connect('activate', lambda w: self._on_arc_make_curved(obj, manager, drawing_area))
                curved_item.show()
                transform_submenu.append(curved_item)
            
            # Add separator if we have both curve/straight and type conversion options
            if transform_submenu.get_children():
                separator = Gtk.SeparatorMenuItem()
                separator.show()
                transform_submenu.append(separator)
            
            # Arc Type Conversion Options (Normal ↔ Test ↔ Inhibitor)
            if can_be_test or can_be_inhibitor:
                pass
                # Show checkmark for current type
                type_label = "Arc Type ►"
                type_submenu_item = Gtk.MenuItem(label=type_label)
                type_submenu = Gtk.Menu()
                
                # Normal arc option
                normal_label = "✓ Normal Arc" if is_normal_arc else "   Normal Arc"
                normal_item = Gtk.MenuItem(label=normal_label)
                if not is_normal_arc:
                    normal_item.connect('activate', lambda w: self._on_arc_convert_to_normal(obj, manager, drawing_area))
                else:
                    normal_item.set_sensitive(False)
                normal_item.show()
                type_submenu.append(normal_item)
                
                # Test arc option (catalyst) - only for Place → Transition
                if can_be_test:
                    test_label = "✓ Test Arc (Catalyst)" if is_test else "   Test Arc (Catalyst)"
                    test_item = Gtk.MenuItem(label=test_label)
                    if not is_test:
                        test_item.connect('activate', lambda w: self._on_arc_convert_to_test(obj, manager, drawing_area))
                    else:
                        test_item.set_sensitive(False)
                    test_item.show()
                    type_submenu.append(test_item)
                
                # Inhibitor arc option - only for Place → Transition
                if can_be_inhibitor:
                    inhibitor_label = "✓ Inhibitor Arc" if is_inhibitor_arc else "   Inhibitor Arc"
                    inhibitor_item = Gtk.MenuItem(label=inhibitor_label)
                    if not is_inhibitor_arc:
                        inhibitor_item.connect('activate', lambda w: self._on_arc_convert_to_inhibitor(obj, manager, drawing_area))
                    else:
                        inhibitor_item.set_sensitive(False)
                    inhibitor_item.show()
                    type_submenu.append(inhibitor_item)
                
                type_submenu_item.set_submenu(type_submenu)
                type_submenu_item.show()
                transform_submenu.append(type_submenu_item)
            
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
        
        # Store reference to active menu for cleanup before dialogs
        self._active_context_menu = menu
        
        # Attach menu to drawing_area for proper Wayland parent window handling
        menu.attach_to_widget(drawing_area, None)
        # Use popup_at_pointer() instead of deprecated popup() for Wayland compatibility
        menu.popup_at_pointer(None)

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

    def get_canvas_controller(self, drawing_area=None):
        """Get the simulation controller for a drawing area.
        
        PHASE 4: Canvas-centric controller access.
        This method provides stable access to controllers that survives
        SwissPalette refactoring. Controllers are keyed by drawing_area,
        which is a stable reference that won't change during UI refactoring.
        
        Args:
            drawing_area: GtkDrawingArea. If None, returns controller for current document.
            
        Returns:
            SimulationController: Controller instance with state_detector, 
                                 buffered_settings, and interaction_guard.
                                 Returns None if not found.
        
        Usage:
            controller = self.get_canvas_controller(drawing_area)
            if controller and not controller.interaction_guard.can_activate_tool('place'):
                reason = controller.interaction_guard.get_block_reason('place')
                show_message(reason)
        """
        if drawing_area is None:
            drawing_area = self.get_current_document()
        return self.simulation_controllers.get(drawing_area)

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

    def get_current_model(self):
        """Get the current canvas manager as model for topology analysis.
        
        The ModelCanvasManager IS the model - it has places, transitions, arcs
        attributes that satisfy the TopologyAnalyzer duck-typed interface.
        
        This method is used by the Topology Panel to get the model for analysis.
        
        Returns:
            ModelCanvasManager: The active canvas manager (which is the model),
                               or None if no document is open.
        
        Example:
            # From Topology Panel Controller:
            model = model_canvas_loader.get_current_model()
            if model:
                analyzer = PInvariantAnalyzer(model)
                result = analyzer.analyze()
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            return None
        return self.get_canvas_manager(drawing_area)
    
    def get_current_knowledge_base(self):
        """Get the knowledge base for the currently active document.
        
        The ModelKnowledgeBase aggregates multi-domain knowledge (topology,
        biology, biochemistry, dynamics) to enable intelligent model repair.
        
        Returns:
            ModelKnowledgeBase: The knowledge base for the active document,
                               or None if no document is open or KB not created.
        
        Example:
            # From Viability Panel:
            kb = model_canvas_loader.get_current_knowledge_base()
            if kb:
                dead_transitions = kb.get_dead_transitions()
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            return None
        return self.knowledge_bases.get(drawing_area)
    
    def get_knowledge_base(self, drawing_area):
        """Get the knowledge base for a specific drawing area.
        
        Args:
            drawing_area: The GtkDrawingArea widget
            
        Returns:
            ModelKnowledgeBase: The knowledge base, or None if not found
        """
        return self.knowledge_bases.get(drawing_area)
    
    def reset_current_canvas(self):
        """Reset the current canvas to initial state (File → New equivalent).
        
        Clears all objects, resets simulation, reinitializes palette.
        Preserves the canvas instance and ID scope.
        Uses the lifecycle system when available, falls back to legacy clear otherwise.
        
        Returns:
            bool: True if reset succeeded, False if no canvas or reset failed
            
        Example:
            # From File menu handler:
            if model_canvas_loader.reset_current_canvas():
                print("Canvas reset successfully")
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            pass
            # print("[RESET] No active canvas to reset")
            return False
        
        # PHASE 4: Use lifecycle system if available
        if self.lifecycle_manager:
            try:
                self.lifecycle_manager.reset_canvas(drawing_area)
                # print(f"[RESET] ✓ Canvas reset via lifecycle system")
                # Trigger redraw
                drawing_area.queue_draw()
                return True
            except Exception as e:
                pass
                # print(f"[RESET] ⚠️  Lifecycle reset failed: {e}")
                # print("[RESET] Falling back to legacy reset")
        
        # Legacy fallback: Manual cleanup
        try:
            manager = self.get_canvas_manager(drawing_area)
            if manager:
                pass
                # Clear objects
                manager.places.clear()
                manager.transitions.clear()
                manager.arcs.clear()
                
                # Reset simulation if controller exists
                if drawing_area in self.simulation_controllers:
                    controller = self.simulation_controllers[drawing_area]
                    if hasattr(controller, 'reset'):
                        controller.reset()
                
                # Trigger redraw
                drawing_area.queue_draw()
                # print("[RESET] ✓ Canvas reset via legacy method")
                return True
        except Exception as e:
            pass
            # print(f"[RESET] ✗ Reset failed: {e}")
            return False
        
        return False
    
    def get_current_canvas_info(self):
        """Get information about the current canvas for UI display.
        
        Returns a dictionary with canvas metadata including:
        - canvas_id: Unique canvas identifier
        - scope_name: ID scope name  
        - next_place_id: Next place ID that will be generated
        - next_transition_id: Next transition ID that will be generated
        - next_arc_id: Next arc ID that will be generated
        - element_count: Number of elements in canvas
        
        Returns:
            dict: Canvas information, or None if no active canvas
            
        Example:
            info = model_canvas_loader.get_current_canvas_info()
            if info:
                print(f"Canvas: {info['scope_name']}")
                print(f"Next IDs: P{info['next_place_id']}, T{info['next_transition_id']}")
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            return None
        
        info = {
            'canvas_id': id(drawing_area),
            'scope_name': None,
            'next_place_id': '?',
            'next_transition_id': '?',
            'next_arc_id': '?',
            'element_count': 0
        }
        
        # Get scope information from lifecycle if available
        if self.lifecycle_manager:
            try:
                context = self.lifecycle_manager.get_context(drawing_area)
                if context:
                    info['scope_name'] = context.id_scope
                    
                    # Get next IDs from the ID manager
                    # We can't generate without side effects, so we peek at counters
                    id_mgr = self.lifecycle_manager.id_manager
                    if hasattr(id_mgr, '_scopes') and context.id_scope in id_mgr._scopes:
                        scope_data = id_mgr._scopes[context.id_scope]
                        info['next_place_id'] = scope_data.get('place', 0) + 1
                        info['next_transition_id'] = scope_data.get('transition', 0) + 1
                        info['next_arc_id'] = scope_data.get('arc', 0) + 1
            except Exception as e:
                print(f"[INFO] Could not get lifecycle info: {e}")
        
        # Get element count from canvas manager
        manager = self.get_canvas_manager(drawing_area)
        if manager:
            place_count = len(manager.places) if hasattr(manager, 'places') else 0
            trans_count = len(manager.transitions) if hasattr(manager, 'transitions') else 0
            arc_count = len(manager.arcs) if hasattr(manager, 'arcs') else 0
            info['element_count'] = place_count + trans_count + arc_count
        
        return info


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
        
        # Connect to persistency callbacks to update tab labels
        if hasattr(persistency, 'on_file_saved'):
            original_on_file_saved = persistency.on_file_saved
            def on_file_saved_wrapper(filepath):
                self._on_file_operation_completed(filepath, is_save=True)
                if original_on_file_saved:
                    original_on_file_saved(filepath)
            persistency.on_file_saved = on_file_saved_wrapper
        
        if hasattr(persistency, 'on_file_loaded'):
            original_on_file_loaded = persistency.on_file_loaded
            def on_file_loaded_wrapper(filepath, document):
                self._on_file_operation_completed(filepath, is_save=False)
                if original_on_file_loaded:
                    original_on_file_loaded(filepath, document)
            persistency.on_file_loaded = on_file_loaded_wrapper
        
        if hasattr(persistency, 'on_dirty_changed'):
            original_on_dirty_changed = persistency.on_dirty_changed
            def on_dirty_changed_wrapper(is_dirty):
                self._on_dirty_state_changed(is_dirty)
                if original_on_dirty_changed:
                    original_on_dirty_changed(is_dirty)
            persistency.on_dirty_changed = on_dirty_changed_wrapper
    
    def set_project(self, project):
        """Set the current project for structured save paths.
        
        When a project is open, all saves go to structured directories:
        - Petri net models → project/models/
        - Raw pathway data → project/pathways/
        - Metadata (BRENDA) → project/metadata/
        
        Args:
            project: Project instance or None
        """
        self.project = project

    def _on_file_operation_completed(self, filepath, is_save=True):
        """Handle file save/load completion to update tab label.
        
        Args:
            filepath: Full path to the saved/loaded file
            is_save: True if save operation, False if load operation
        """
        # print(f"\n[FILE_OP] ========================================")
        # print(f"[FILE_OP] File operation: {'SAVE' if is_save else 'LOAD'}")
        # print(f"[FILE_OP] filepath: {filepath}")
        
        if not filepath:
            pass
            # print(f"[FILE_OP] No filepath, returning")
            return
        
        # Extract filename with .shy extension
        filename = os.path.basename(filepath)
        # If filename doesn't have .shy extension, it might be without extension
        if not filename.endswith('.shy'):
            base = os.path.splitext(filename)[0]
            filename = f"{base}.shy"
        
        # print(f"[FILE_OP] Extracted filename: {filename}")
        
        # Get current page
        current_page_num = self.notebook.get_current_page()
        if current_page_num < 0:
            pass
            # print(f"[FILE_OP] No current page, returning")
            return
        
        current_page = self.notebook.get_nth_page(current_page_num)
        # print(f"[FILE_OP] Current page num: {current_page_num}")
        
        # Update tab label with new filename (no asterisk after save/load)
        self._update_tab_label(current_page, filename, is_modified=False)
        # print(f"[FILE_OP] Tab label updated to: {filename}")
        
        # Also update the canvas manager's filename (without extension for internal use)
        drawing_area = self._get_drawing_area_from_page(current_page)
        # print(f"[FILE_OP] drawing_area: {drawing_area} (id={id(drawing_area) if drawing_area else 'None'})")
        
        if drawing_area and drawing_area in self.canvas_managers:
            manager = self.canvas_managers[drawing_area]
            # Store filename without extension in manager
            base_filename = os.path.splitext(filename)[0]
            manager.filename = base_filename
            # print(f"[FILE_OP] Manager filename updated to: {base_filename}")
            
            # If this was a save operation, mark as saved (clears imported flag)
            if is_save:
                manager.mark_as_saved()
                # print(f"[FILE_OP] Manager marked as saved")
        
        # print(f"[FILE_OP] ========================================\n")

    def _on_dirty_state_changed(self, is_dirty):
        """Handle dirty state change to update tab label modification indicator.
        
        Args:
            is_dirty: True if document has unsaved changes
        """
        # Get current page
        current_page_num = self.notebook.get_current_page()
        if current_page_num < 0:
            return
        
        current_page = self.notebook.get_nth_page(current_page_num)
        drawing_area = self._get_drawing_area_from_page(current_page)
        
        if drawing_area and drawing_area in self.canvas_managers:
            manager = self.canvas_managers[drawing_area]
            # Get base filename (without extension) from manager
            base_filename = manager.filename if hasattr(manager, 'filename') else 'default'
            
            # _update_tab_label will add .shy extension automatically
            # Update tab label with modification indicator (asterisk)
            self._update_tab_label(current_page, base_filename, is_modified=is_dirty)

    def _get_drawing_area_from_page(self, page_widget):
        """Extract drawing area from a notebook page widget.
        
        Args:
            page_widget: Page widget (usually Gtk.Overlay)
            
        Returns:
            Gtk.DrawingArea or None
        """
        if isinstance(page_widget, Gtk.Overlay):
            scrolled = page_widget.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
                return drawing_area
        return None

    def set_right_panel_loader(self, right_panel_loader):
        """Set the right panel loader for data collector updates.
        
        This allows the notebook to update the right panel's data collector
        when the user switches between tabs with different simulations.
        
        Args:
            right_panel_loader: RightPanelLoader instance from main application
        """
        print(f"[MODEL_CANVAS_LOADER] set_right_panel_loader() called")
        self.right_panel_loader = right_panel_loader
        if self.notebook and self.notebook.get_n_pages() > 0:
            current_page_num = self.notebook.get_current_page()
            current_page = self.notebook.get_nth_page(current_page_num)
            self._on_notebook_page_changed(self.notebook, current_page, current_page_num)
        
        # Wire locality sync callback for all existing Report panels
        print(f"[MODEL_CANVAS_LOADER] About to call _wire_locality_sync_for_existing_panels()")
        self._wire_locality_sync_for_existing_panels()
        print(f"[MODEL_CANVAS_LOADER] Completed _wire_locality_sync_for_existing_panels()")
    
    def _wire_locality_sync_for_existing_panels(self):
        """Wire transition→report locality sync callbacks for all existing panels.
        
        Called when right_panel_loader is set, to retroactively wire callbacks
        for Report panels that were created before the transition panel existed.
        """
        if not self.right_panel_loader:
            return
        
        if not hasattr(self.right_panel_loader, 'transition_panel') or not self.right_panel_loader.transition_panel:
            print(f"[LOCALITY_WIRE] No transition_panel in right_panel_loader yet")
            return
        
        transition_panel = self.right_panel_loader.transition_panel
        print(f"[LOCALITY_WIRE] Wiring locality sync for {len(self.overlay_managers)} existing documents")
        
        # Create a SINGLE callback that dynamically routes to the current active document's report panel
        # This fixes the issue where the callback was captured for a specific document
        def on_transition_selected(transition, locality):
            """Called when user selects transition in Analyses panel.
            
            Routes the selection to the CURRENTLY ACTIVE document's report panel.
            """
            print(f"[LOCALITY_CALLBACK] Received transition {transition.name if hasattr(transition, 'name') else transition.id}")
            print(f"[LOCALITY_CALLBACK] Locality valid: {locality.is_valid if locality else False}")
            
            # Get the current active drawing area
            current_page_num = self.notebook.get_current_page()
            current_page = self.notebook.get_nth_page(current_page_num)
            
            drawing_area = None
            if isinstance(current_page, Gtk.Overlay):
                scrolled = current_page.get_child()
                if isinstance(scrolled, Gtk.ScrolledWindow):
                    drawing_area = scrolled.get_child()
                    if hasattr(drawing_area, 'get_child'):
                        drawing_area = drawing_area.get_child()
            
            if not drawing_area or drawing_area not in self.overlay_managers:
                print(f"[LOCALITY_CALLBACK] ⚠️ No active drawing area found")
                return
            
            # Get the report panel for the current document
            overlay_manager = self.overlay_managers[drawing_area]
            if not hasattr(overlay_manager, 'report_panel_loader'):
                print(f"[LOCALITY_CALLBACK] ⚠️ No report_panel_loader for active document")
                return
            
            report_panel_loader = overlay_manager.report_panel_loader
            if not report_panel_loader or not hasattr(report_panel_loader, 'panel'):
                print(f"[LOCALITY_CALLBACK] ⚠️ No report panel for active document")
                return
            
            report_panel = report_panel_loader.panel
            print(f"[LOCALITY_CALLBACK] Report panel categories: {len(report_panel.categories)}")
            
            # Find ModelsCategory in Report panel (for "Show Selected Locality")
            from shypn.ui.panels.report.model_structure_category import ModelsCategory
            for category in report_panel.categories:
                print(f"[LOCALITY_CALLBACK] Checking category: {type(category).__name__}")
                if isinstance(category, ModelsCategory):
                    print(f"[LOCALITY_CALLBACK] Found ModelsCategory, calling set_selected_locality()")
                    category.set_selected_locality(transition, locality)
                    print(f"[LOCALITY_CALLBACK] set_selected_locality() completed")
                    break
            else:
                print(f"[LOCALITY_CALLBACK] ⚠️ ModelsCategory not found in report panel!")
            
            # Find DynamicAnalysesCategory in Report panel (for "Reaction Selected" simulation data)
            from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory
            for category in report_panel.categories:
                if isinstance(category, DynamicAnalysesCategory):
                    print(f"[LOCALITY_CALLBACK] Found DynamicAnalysesCategory, calling set_selected_reaction()")
                    category.set_selected_reaction(transition, locality)
                    print(f"[LOCALITY_CALLBACK] set_selected_reaction() completed")
                    break
            else:
                print(f"[LOCALITY_CALLBACK] ⚠️ DynamicAnalysesCategory not found in report panel!")
        
        # Set the single dynamic callback (no loop needed, single global transition panel)
        transition_panel.on_selection_changed_callback = on_transition_selected
        print(f"[LOCALITY_WIRE] ✓ Wired dynamic callback for all documents")
    
    def wire_existing_canvases_to_right_panel(self):
        """Wire data_collector to right_panel for all existing canvases.
        
        This is called after both model_canvas_loader and right_panel_loader are initialized.
        It retroactively wires any canvases that were created before right_panel_loader existed
        (e.g., the startup default canvas).
        
        Simple solution: Just trigger the existing _on_notebook_page_changed() handler
        for the current page, which already has all the wiring logic.
        """
        if not self.right_panel_loader:
            return
        
        # Get the current page and trigger the page changed handler
        # This will execute all the existing wiring logic
        current_page_num = self.notebook.get_current_page()
        current_page = self.notebook.get_nth_page(current_page_num)
        
        # Manually call the page changed handler to wire the startup canvas
        self._on_notebook_page_changed(self.notebook, current_page, current_page_num)
    
    def _wire_viability_callbacks(self):
        """Wire simulation complete callbacks to Viability Panel for all existing controllers.
        
        Called after viability_panel_loader is set, to retroactively wire callbacks
        for controllers that were created before the viability panel existed.
        
        NOTE: This handles GLOBAL viability panel. Per-document panels are wired
        during their creation in _setup_edit_palettes().
        """
        if not hasattr(self, 'viability_panel_loader') or not self.viability_panel_loader:
            print(f"[VIABILITY_WIRE] No global viability_panel_loader - skipping global wiring")
            return
        
        viability_panel = self.viability_panel_loader.panel
        if not viability_panel or not hasattr(viability_panel, 'on_simulation_complete'):
            print(f"[VIABILITY_WIRE] Global viability panel or method not available")
            return
        
        print(f"[VIABILITY_WIRE] Wiring GLOBAL viability callbacks for {len(self.simulation_controllers)} existing controllers")
        
        # Wire callback for each existing controller
        for drawing_area, controller in self.simulation_controllers.items():
            try:
                # Store existing callback if any
                existing_callback = getattr(controller, 'on_simulation_complete', None)
                
                # Create combined callback that calls both
                def make_combined_callback(existing):
                    def combined():
                        if existing and callable(existing):
                            existing()
                        viability_panel.on_simulation_complete()
                    return combined
                
                controller.on_simulation_complete = make_combined_callback(existing_callback)
                print(f"[VIABILITY_WIRE] ✓ Wired GLOBAL callback for drawing_area {id(drawing_area)}")
            except Exception as e:
                print(f"[VIABILITY_WIRE] ⚠️ Failed to wire callback for drawing_area {id(drawing_area)}: {e}")

    def set_context_menu_handler(self, handler):
        """Set the context menu handler for adding analysis menu items.
        
        This allows canvas object context menus to include "Add to Analysis" options.
        
        Args:
            handler: ContextMenuHandler instance
        """
        self.context_menu_handler = handler

    def set_file_explorer_panel(self, file_explorer_panel):
        """Set the file explorer panel for keyboard shortcut integration.
        
        This allows keyboard shortcuts (Ctrl+S, Ctrl+Shift+S) to trigger
        save operations through the file explorer panel.
        
        Args:
            file_explorer_panel: FileExplorerPanel instance from main application
        """
        self.file_explorer_panel = file_explorer_panel

    def _setup_canvas_context_menu(self, drawing_area, manager):
        """Setup context menu for canvas operations using Gtk.Menu.
        
        Args:
            drawing_area: GtkDrawingArea widget.
            manager: ModelCanvasManager instance.
        """
        menu = Gtk.Menu()
        # Attach menu to drawing_area for proper Wayland parent window handling
        menu.attach_to_widget(drawing_area, None)
        menu_items = [
            ('Reset Zoom (100%)', lambda: self._on_reset_zoom_clicked(menu, drawing_area, manager)),
            ('Zoom In', lambda: self._on_zoom_in_clicked(menu, drawing_area, manager)),
            ('Zoom Out', lambda: self._on_zoom_out_clicked(menu, drawing_area, manager)),
            ('Fit to Window', lambda: self._on_fit_to_window_clicked(menu, drawing_area, manager)),
            None,  # Separator
            ('Rotate 90° CW', lambda: self._on_rotate_90_cw_clicked(menu, drawing_area, manager)),
            ('Rotate 90° CCW', lambda: self._on_rotate_90_ccw_clicked(menu, drawing_area, manager)),
            ('Rotate 180°', lambda: self._on_rotate_180_clicked(menu, drawing_area, manager)),
            ('Reset Rotation', lambda: self._on_reset_rotation_clicked(menu, drawing_area, manager)),
            None,  # Separator
            ('Grid: Line Style', lambda: self._on_grid_line_clicked(menu, drawing_area, manager)),
            ('Grid: Dot Style', lambda: self._on_grid_dot_clicked(menu, drawing_area, manager)),
            ('Grid: Cross Style', lambda: self._on_grid_cross_clicked(menu, drawing_area, manager)),
            None,  # Separator
            ('Layout: Auto (Best)', lambda: self._on_layout_auto_clicked(menu, drawing_area, manager)),
            ('Layout: Hierarchical', lambda: self._on_layout_hierarchical_clicked(menu, drawing_area, manager)),
            ('Layout: Force-Directed', lambda: self._on_layout_force_clicked(menu, drawing_area, manager)),
            ('Layout: Solar System (SSCC)', lambda: self._on_layout_solar_system_clicked(menu, drawing_area, manager)),
            ('Layout: Circular', lambda: self._on_layout_circular_clicked(menu, drawing_area, manager)),
            ('Layout: Orthogonal', lambda: self._on_layout_orthogonal_clicked(menu, drawing_area, manager)),
            None,  # Separator
            ('Center View', lambda: self._on_center_view_clicked(menu, drawing_area, manager)),
            ('Clear Canvas', lambda: self._on_clear_canvas_clicked(menu, drawing_area, manager)),
            None,  # Separator
            ('🎯 Create Center Marker', lambda: self._on_create_center_marker_clicked(menu, drawing_area, manager))
        ]
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
        """Zoom in action (pointer-centered)."""
        manager.zoom_in(manager.pointer_x, manager.pointer_y)
        drawing_area.queue_draw()

    def _on_zoom_out_clicked(self, menu, drawing_area, manager):
        """Zoom out action (pointer-centered)."""
        manager.zoom_out(manager.pointer_x, manager.pointer_y)
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
    
    def _on_rotate_90_cw_clicked(self, menu, drawing_area, manager):
        """Rotate canvas 90° clockwise."""
        manager.rotate_canvas_90_cw()
        drawing_area.queue_draw()
    
    def _on_rotate_90_ccw_clicked(self, menu, drawing_area, manager):
        """Rotate canvas 90° counterclockwise."""
        manager.rotate_canvas_90_ccw()
        drawing_area.queue_draw()
    
    def _on_rotate_180_clicked(self, menu, drawing_area, manager):
        """Rotate canvas 180°."""
        manager.rotate_canvas_180()
        drawing_area.queue_draw()
    
    def _on_reset_rotation_clicked(self, menu, drawing_area, manager):
        """Reset canvas rotation to 0°."""
        manager.reset_canvas_rotation()
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

    def _on_create_center_marker_clicked(self, menu, drawing_area, manager):
        """Create a red circle at document center (0, 0) for viewport calibration.
        
        This creates a large red circle at the exact document origin to help
        visualize and calibrate viewport centering.
        """
        manager.create_test_objects()
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
                pass
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
                pass
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
    
    def _on_layout_solar_system_clicked(self, menu, drawing_area, manager):
        """Apply Solar System (SSCC) layout with unified physics."""
        try:
            from shypn.layout.sscc import SolarSystemLayoutEngine
            
            # Check if there are nodes to layout
            if not manager.places and not manager.transitions:
                self._show_layout_message("No objects to layout", drawing_area)
                return
            
            # Create engine with unified physics (all forces active)
            engine = SolarSystemLayoutEngine(
                iterations=1000,
                use_arc_weight=True,
                scc_radius=50.0,
                planet_orbit=300.0,
                satellite_orbit=50.0
            )
            
            # Apply layout
            positions = engine.apply_layout(
                places=list(manager.places),
                transitions=list(manager.transitions),
                arcs=list(manager.arcs)
            )
            
            # Update object positions
            for obj_id, (x, y) in positions.items():
                pass
                # Find object by ID
                obj = None
                for place in manager.places:
                    if place.id == obj_id:
                        obj = place
                        break
                if not obj:
                    for transition in manager.transitions:
                        if transition.id == obj_id:
                            obj = transition
                            break
                
                if obj:
                    obj.x = x
                    obj.y = y
            
            # Get statistics
            stats = engine.get_statistics()
            message = f"Applied Solar System (SSCC) layout\n"
            message += f"Physics: {stats['physics_model']}\n"
            message += f"SCCs found: {stats['num_sccs']}\n"
            message += f"Nodes in SCCs: {stats['num_nodes_in_sccs']}\n"
            message += f"Free places: {stats['num_free_places']}"
            self._show_layout_message(message, drawing_area)
            
            # Redraw
            drawing_area.queue_draw()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_layout_message(f"Solar System layout error: {str(e)}", drawing_area)
    
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
            
            # Calculate current center of objects (to preserve relative position)
            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                center_y = sum(obj.y for obj in all_objs) / len(all_objs)
            else:
                pass
                # Default to canvas center
                center_x = manager.canvas_width / 2
                center_y = manager.canvas_height / 2
            
            # Try to get layout parameters from SBML Import panel (if available)
            layout_params = {}
            try:
                pass
                # Check if sbml_panel is available (set during initialization)
                if hasattr(self, 'sbml_panel') and self.sbml_panel:
                    layout_params = self.sbml_panel.get_layout_parameters_for_algorithm(algorithm)
                    if layout_params:
                        pass  # Use these params
            except Exception as e:
                pass  # If we can't get params from SBML panel, just use defaults
            
            # Create engine and apply layout with parameters
            engine = LayoutEngine(manager)
            result = engine.apply_layout(algorithm, **layout_params)
            
            # The layout algorithms center at (0, 0), so we need to offset
            # back to the original center or canvas center
            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                pass
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
            message = f"Applied {algorithm_name} layout\nMoved {result['nodes_moved']} objects"
            if layout_params:
                message += f"\nParameters: {layout_params}"
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
        # Message displayed - could be wired to status bar in future
        pass

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
        # ============================================================================
        # WAYLAND FIX: Close any open context menu BEFORE opening property dialog
        # This prevents menu/dialog parent conflicts on Wayland
        # ============================================================================
        if hasattr(self, '_active_context_menu') and self._active_context_menu:
            try:
                self._active_context_menu.popdown()
                self._active_context_menu.hide()
                # Give Wayland time to process menu destruction
                from gi.repository import GLib
                # Process ALL pending events to ensure menu is fully closed
                for _ in range(10):  # Process multiple times
                    while GLib.MainContext.default().pending():
                        GLib.MainContext.default().iteration(False)
            except Exception:
                pass
            self._active_context_menu = None
        
        # Give Wayland a moment to fully process menu destruction
        import time
        time.sleep(0.05)  # 50ms delay
        
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
        
        # CRITICAL: Ensure parent_window is valid for Wayland
        if not self.parent_window:
            print(f"[DIALOG] ERROR: parent_window is None! Cannot open dialog.")
            return
        
        # WAYLAND FIX: Ensure the canvas page widget AND drawing area are mapped before opening dialog
        # On Wayland, dialogs require the entire widget hierarchy to be fully visible and mapped
        # Get the page widget (overlay) for this drawing area
        page_widget = None
        for i in range(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(i)
            page_drawing = self._get_drawing_area_from_page(page)
            if page_drawing == drawing_area:
                page_widget = page
                break
        
        # Check if BOTH page widget and drawing area are mapped
        page_mapped = page_widget.get_mapped() if page_widget else False
        drawing_mapped = drawing_area.get_mapped()
        page_realized = page_widget.get_realized() if page_widget else False
        drawing_realized = drawing_area.get_realized()
        
        # CRITICAL: Also check if this page is the CURRENT page in the notebook
        # On Wayland, dialogs can only attach to widgets on the visible/current page
        current_page_num = self.notebook.get_current_page()
        page_num = -1
        if page_widget:
            page_num = self.notebook.page_num(page_widget)
        is_current_page = (page_num == current_page_num)
        
        print(f"  page_widget: {page_widget}")
        print(f"  page_mapped: {page_mapped}, drawing_mapped: {drawing_mapped}")
        print(f"  page_realized: {page_realized}, drawing_realized: {drawing_realized}")
        print(f"  page_num: {page_num}, current_page_num: {current_page_num}, is_current: {is_current_page}")
        
        if not (page_mapped and drawing_mapped and is_current_page):
            print(f"  Reason: page_mapped={page_mapped}, drawing_mapped={drawing_mapped}, is_current={is_current_page}")
            # Use timeout to defer dialog opening until both widgets are mapped
            from gi.repository import GLib
            
            retry_count = [0]  # Use list to allow modification in nested function
            MAX_RETRIES = 20  # 20 retries * 50ms = 1 second max wait
            
            def open_when_mapped():
                retry_count[0] += 1
                page_ready = page_widget.get_mapped() if page_widget else False
                drawing_ready = drawing_area.get_mapped()
                is_current = (self.notebook.page_num(page_widget) == self.notebook.get_current_page()) if page_widget else False
                
                if page_ready and drawing_ready and is_current:
                    pass
                    # Call this function again now that widgets are mapped
                    self._on_object_properties(obj, manager, drawing_area)
                    return False  # Don't repeat
                elif retry_count[0] >= MAX_RETRIES:
                    print(f"[DIALOG] ERROR: Gave up after {MAX_RETRIES} retries")
                    print(f"  Final state: page_ready={page_ready}, drawing_ready={drawing_ready}, is_current={is_current}")
                    return False  # Give up
                else:
                    return True  # Keep checking
            
            # Check every 50ms for up to 1 second
            GLib.timeout_add(50, open_when_mapped)
            return
        
        # Check the drawing area's toplevel for Wayland compatibility
        toplevel = drawing_area.get_toplevel()
        if toplevel and isinstance(toplevel, Gtk.Window):
            pass
        
        dialog_loader = None
        if isinstance(obj, Place):
            dialog_loader = create_place_prop_dialog(obj, parent_window=self.parent_window, persistency_manager=self.persistency, model=manager)
        elif isinstance(obj, Transition):
            data_collector = None
            if drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                
                
                # Get from SwissKnifePalette widget_palette_instances
                # NOTE: New SwissKnifePalette architecture stores widget palettes in registry
                if hasattr(overlay_manager, 'swissknife_palette'):
                    swissknife = overlay_manager.swissknife_palette
                    
                    # Try new architecture (registry.widget_palette_instances)
                    if hasattr(swissknife, 'registry') and hasattr(swissknife.registry, 'widget_palette_instances'):
                        simulate_tools = swissknife.registry.widget_palette_instances.get('simulate')
                        if simulate_tools and hasattr(simulate_tools, 'data_collector'):
                            data_collector = simulate_tools.data_collector
                    # Fallback to old architecture (widget_palette_instances directly)
                    elif hasattr(swissknife, 'widget_palette_instances'):
                        simulate_tools = swissknife.widget_palette_instances.get('simulate')
                        if simulate_tools and hasattr(simulate_tools, 'data_collector'):
                            data_collector = simulate_tools.data_collector
            else:
                pass
                
            dialog_loader = create_transition_prop_dialog(obj, parent_window=self.parent_window, persistency_manager=self.persistency, model=manager, data_collector=data_collector)
        elif isinstance(obj, Arc):
            dialog_loader = create_arc_prop_dialog(obj, parent_window=self.parent_window, persistency_manager=self.persistency, model=manager)
        else:
            return
        if isinstance(obj, Arc):

            pass

        def on_properties_changed(_):
            if isinstance(obj, Arc):
                pass
            drawing_area.queue_draw()
            
            # MANAGER SYNCHRONIZATION FIX: Use canvas-centric controller access
            # This works reliably across ALL canvas creation paths (Default Canvas,
            # File New, File Open, KEGG Import, SBML Import) because controllers are
            # keyed by drawing_area in self.simulation_controllers dict.
            # Previous code used overlay_manager.get_palette('simulate_tools') which
            # was unreliable due to palette structure variations across paths.
            if isinstance(obj, Transition):
                controller = self.get_canvas_controller(drawing_area)
                if controller:
                    pass
                    # Clear behavior cache when transition type/properties change
                    # This forces behavior algorithm recompilation on next simulation step
                    if obj.id in controller.behavior_cache:
                        del controller.behavior_cache[obj.id]
                    
                    # CRITICAL: If transition became a source transition, enable it immediately
                    # This allows simulation to run without needing to press Reset
                    if getattr(obj, 'is_source', False):
                        if obj.id in controller.transition_states:
                            state = controller.transition_states[obj.id]
                            if state.enablement_time is None:
                                state.enablement_time = controller.time
                                print(f"[PROPERTIES_CHANGED] Enabled source transition {obj.id} at t={controller.time}")
                    
                    # Clear historical data so plot shows new rate function immediately
                    if hasattr(controller, 'data_collector') and controller.data_collector:
                        controller.data_collector.clear_transition(obj.id)
                
                # CRITICAL: Notify manager observers so controller gets 'modified' event
                # This ensures the observer pattern properly handles property changes
                manager._notify_observers('modified', obj)
            
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
        
        # Show dialog
        self._show_dialog_safely(dialog_loader, drawing_area, original_tool, manager)
    
    def _show_dialog_safely(self, dialog_loader, drawing_area, original_tool, manager):
        """Show dialog with error handling.
        
        Args:
            dialog_loader: The dialog loader instance
            drawing_area: The canvas drawing area
            original_tool: The original tool before dialog (for restoration)
            manager: The canvas manager
        """
        try:
            pass
            # The dialog_loader already has parent_window set during creation
            # We don't need to set transient_for again - it's already configured
            
            response = dialog_loader.run()
            
            if response == Gtk.ResponseType.OK:
                drawing_area.queue_draw()
                
                # Update simulation controller state after transition type/property changes
                # This ensures newly created or type-switched stochastic/timed transitions
                # are properly scheduled when the simulation starts
                controller = self.get_canvas_controller(drawing_area)
                if controller:
                    controller._update_enablement_states()
        except Exception as e:
            print(f"[ERROR] Dialog run failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            pass
            # CRITICAL: Always destroy dialog to prevent orphaned widgets
            # Orphaned widgets cause Wayland focus issues and app crashes
            dialog_loader.destroy()
        
        # Restore original tool if we switched it
        if original_tool == 'arc':
            manager.set_tool('arc')
        
        # Clear arc creation state again after dialog closes to prevent spurious arc creation
        # This handles the case where mouse release happens after dialog closes
        arc_state = self._arc_state.get(drawing_area)
        if arc_state:
            arc_state['source'] = None
            arc_state['cursor_pos'] = (0, 0)

    def _on_transition_type_change(self, transition, new_type, manager, drawing_area):
        """Handle transition type change from context menu.
        
        Args:
            transition: Transition object
            new_type: New transition type ('immediate', 'timed', 'stochastic', 'continuous')
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Transition
        old_type = getattr(transition, 'transition_type', 'continuous')
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
        dialog.set_keep_above(True)  # Ensure dialog stays on top
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
            pass
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
    
    def _on_arc_convert_to_test(self, arc, manager, drawing_area):
        """Convert arc to test type (catalyst).
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import convert_to_test
        
        try:
            new_arc = convert_to_test(arc)
            manager.replace_arc(arc, new_arc)
            drawing_area.queue_draw()
        except ValueError as e:
            pass
            # Invalid transformation (e.g., Transition → Place)
            self._show_error_dialog(str(e))
            return
    
    def _cut_selection(self, manager, widget):
        """Cut selected objects to clipboard.
        
        Args:
            manager: ModelCanvasManager instance
            widget: GtkDrawingArea widget
        """
        # First copy, then delete
        self._copy_selection(manager)
        
        # Delete selected objects
        selected = manager.selection_manager.get_selected_objects(manager)
        if selected:
            pass
            # TODO: Implement undo support for cut
            # from shypn.edit.undo_operations import DeleteOperation
            # Store delete data for undo
            # delete_data = []
            # for obj in selected:
            #     delete_data.append(manager.serialize_object_for_undo(obj))
            
            # Delete all selected objects
            for obj in selected:
                self._delete_object(manager, obj)
            
            # Push to undo stack
            # if hasattr(manager, 'undo_manager') and delete_data:
            #     manager.undo_manager.push(DeleteOperation(delete_data, manager))
            
            widget.queue_draw()
    
    def _delete_object(self, manager, obj):
        """Delete an object using the appropriate remove method.
        
        Args:
            manager: ModelCanvasManager instance
            obj: Object to delete (Place, Transition, or Arc)
        """
        from shypn.netobjs import Place, Transition, Arc
        
        if isinstance(obj, Place):
            manager.remove_place(obj)
        elif isinstance(obj, Transition):
            manager.remove_transition(obj)
        elif isinstance(obj, Arc):
            manager.remove_arc(obj)
    
    def _copy_selection(self, manager):
        """Copy selected objects to clipboard.
        
        Args:
            manager: ModelCanvasManager instance
        """
        from shypn.netobjs import Place, Transition, Arc
        
        selected = manager.selection_manager.get_selected_objects(manager)
        if not selected:
            return
        
        self._clipboard = []
        
        # Separate places, transitions, and arcs
        places = [obj for obj in selected if isinstance(obj, Place)]
        transitions = [obj for obj in selected if isinstance(obj, Transition)]
        arcs = [obj for obj in selected if isinstance(obj, Arc)]
        
        # Serialize places and transitions
        for place in places:
            self._clipboard.append({
                'type': 'place',
                'name': place.name,
                'x': place.x,
                'y': place.y,
                'radius': place.radius,
                'tokens': place.tokens,
                'capacity': getattr(place, 'capacity', float('inf')),
                'id': id(place)  # Temporary ID for arc reconstruction
            })
        
        for transition in transitions:
            self._clipboard.append({
                'type': 'transition',
                'name': transition.name,
                'x': transition.x,
                'y': transition.y,
                'width': transition.width,
                'height': transition.height,
                'horizontal': transition.horizontal,
                'transition_type': getattr(transition, 'transition_type', 'continuous'),
                'rate': getattr(transition, 'rate', 1.0),
                'delay': getattr(transition, 'delay', 0.0),
                'id': id(transition)  # Temporary ID for arc reconstruction
            })
        
        # Serialize arcs only if both source and target are in selection
        for arc in arcs:
            if arc.source in selected and arc.target in selected:
                arc_data = {
                    'type': 'arc',
                    'source_id': id(arc.source),
                    'target_id': id(arc.target),
                    'weight': arc.weight,
                    'arc_type': getattr(arc, 'arc_type', 'normal')
                }
                
                # Handle curved arcs
                if hasattr(arc, 'is_curved') and arc.is_curved:
                    arc_data['is_curved'] = True
                    arc_data['handle_x'] = arc.handle_x
                    arc_data['handle_y'] = arc.handle_y
                
                self._clipboard.append(arc_data)
    
    def _paste_selection(self, manager, widget, pointer_x=None, pointer_y=None):
        """Paste objects from clipboard at pointer position.
        
        Pastes the clipboard contents centered at the pointer position (or canvas center).
        This provides intuitive paste behavior where objects appear where you want them.
        
        Args:
            manager: ModelCanvasManager instance
            widget: GtkDrawingArea widget
            pointer_x: World X coordinate to paste at (None = use canvas center)
            pointer_y: World Y coordinate to paste at (None = use canvas center)
        """
        from shypn.netobjs import Place, Transition
        
        if not self._clipboard:
            return
        
        # Calculate clipboard bounding box center
        items_with_pos = [item for item in self._clipboard if 'x' in item and 'y' in item]
        if not items_with_pos:
            return
        
        clipboard_min_x = min(item['x'] for item in items_with_pos)
        clipboard_min_y = min(item['y'] for item in items_with_pos)
        clipboard_max_x = max(item['x'] for item in items_with_pos)
        clipboard_max_y = max(item['y'] for item in items_with_pos)
        clipboard_center_x = (clipboard_min_x + clipboard_max_x) / 2
        clipboard_center_y = (clipboard_min_y + clipboard_max_y) / 2
        
        # Get paste position
        if pointer_x is None or pointer_y is None:
            pass
            # Use canvas center if no pointer position provided
            screen_center_x = manager.viewport_width / 2
            screen_center_y = manager.viewport_height / 2
            pointer_x, pointer_y = manager.screen_to_world(screen_center_x, screen_center_y)
        
        # Calculate offset to center clipboard at pointer
        offset_x = pointer_x - clipboard_center_x
        offset_y = pointer_y - clipboard_center_y
        
        # Clear current selection
        manager.clear_all_selections()
        
        # Map old IDs to new objects
        id_map = {}
        
        # Create places and transitions first
        for item in self._clipboard:
            if item['type'] == 'place':
                place = manager.add_place(
                    item['x'] + offset_x,
                    item['y'] + offset_y
                )
                place.tokens = item['tokens']
                place.capacity = item.get('capacity', float('inf'))
                place.radius = item['radius']
                id_map[item['id']] = place
                
                # Select pasted object
                place.selected = True
                manager.selection_manager.select(place, multi=True, manager=manager)
            
            elif item['type'] == 'transition':
                transition = manager.add_transition(
                    item['x'] + offset_x,
                    item['y'] + offset_y
                )
                transition.horizontal = item['horizontal']
                transition.width = item['width']
                transition.height = item['height']
                transition.transition_type = item.get('transition_type', 'continuous')
                transition.rate = item.get('rate', 1.0)
                transition.delay = item.get('delay', 0.0)
                id_map[item['id']] = transition
                
                # Select pasted object
                transition.selected = True
                manager.selection_manager.select(transition, multi=True, manager=manager)
        
        # Create arcs after all nodes exist
        for item in self._clipboard:
            if item['type'] == 'arc':
                source = id_map.get(item['source_id'])
                target = id_map.get(item['target_id'])
                
                if source and target:
                    try:
                        arc = manager.add_arc(source, target)
                        arc.weight = item['weight']
                        
                        # Set arc type
                        if item.get('arc_type') == 'inhibitor':
                            from shypn.utils.arc_transform import convert_to_inhibitor
                            new_arc = convert_to_inhibitor(arc)
                            manager.replace_arc(arc, new_arc)
                            arc = new_arc
                        
                        # Handle curved arcs
                        if item.get('is_curved'):
                            arc.is_curved = True
                            arc.handle_x = item['handle_x'] + offset_x
                            arc.handle_y = item['handle_y'] + offset_y
                    except ValueError:
                        pass
                        # Skip invalid arcs
                        pass
        
        widget.queue_draw()
    
    def _generate_unique_name(self, manager, base_name):
        """Generate a unique name for a pasted object.
        
        Args:
            manager: ModelCanvasManager instance
            base_name: Base name to start from
            
        Returns:
            str: Unique name
        """
        # Extract base name without numeric suffix
        import re
        match = re.match(r'(.+?)(\d+)$', base_name)
        if match:
            prefix = match.group(1)
        else:
            prefix = base_name
        
        # Find all existing names
        existing_names = set()
        for place in manager.places:
            existing_names.add(place.name)
        for transition in manager.transitions:
            existing_names.add(transition.name)
        
        # Generate unique name
        counter = 1
        while True:
            candidate = f"{prefix}{counter}"
            if candidate not in existing_names:
                return candidate
            counter += 1
    
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
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_info_message(self, message):
        """Show an informational message to the user.
        
        Used for permission denials and state-based restrictions.
        
        Args:
            message: Information message to display
        """
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Action Not Allowed"
        )
        dialog.set_keep_above(True)  # Ensure dialog stays on top
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