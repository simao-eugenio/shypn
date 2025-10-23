#!/usr/bin/env python3
"""Right Panel Loader/Controller.

This module is responsible for loading and managing the right Dynamic Analyses panel.
The panel can exist in two states:
  - Detached: standalone floating window
  - Attached: content embedded in main window container (extreme right)
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in right_panel loader:', e, file=sys.stderr)
    sys.exit(1)


class RightPanelLoader:
    """Loader and controller for the right Dynamic Analyses panel (attachable window)."""
    
    def __init__(self, ui_path=None, data_collector=None):
        """Initialize the right panel loader.
        
        Args:
            ui_path: Optional path to right_panel.ui. If None, uses default location.
            data_collector: Optional SimulationDataCollector for plotting panels
        """
        if ui_path is None:
            # Default: ui/panels/right_panel.ui
            # This loader file is in: src/shypn/helpers/right_panel_loader.py
            # UI file is in: ui/panels/right_panel.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'panels', 'right_panel.ui')
        
        self.ui_path = ui_path
        self.data_collector = data_collector
        self.model = None  # ModelCanvasManager for search functionality
        self.builder = None
        self.window = None
        self.content = None
        self.is_hanged = False  # Simple state flag (skeleton pattern)
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
        self.on_float_callback = None  # Callback to notify when panel floats
        self.on_attach_callback = None  # Callback to notify when panel attaches
        
        # Plotting panels (will be instantiated in load())
        self.place_panel = None
        self.transition_panel = None
        self.diagnostics_panel = None  # NEW: Diagnostics panel for runtime metrics
        
        # Context menu handler (will be instantiated after panels are created)
        self.context_menu_handler = None
    
    def load(self):
        """Load the panel UI and return the window.
        
        Returns:
            Gtk.Window: The right panel window.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If window or content not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Right panel UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract window and content
        self.window = self.builder.get_object('right_panel_window')
        self.content = self.builder.get_object('right_panel_content')
        
        if self.window is None:
            raise ValueError("Object 'right_panel_window' not found in right_panel.ui")
        if self.content is None:
            raise ValueError("Object 'right_panel_content' not found in right_panel.ui")
        
        # Get float button and connect callback
        float_button = self.builder.get_object('float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
            self.float_button = float_button
        else:
            self.float_button = None
        
        # Initialize plotting panels if data_collector is available
        if self.data_collector is not None:
            self._setup_plotting_panels()
        
        # WAYLAND FIX: Realize window and set event mask for multi-monitor support
        self.window.realize()
        if self.window.get_window():
            try:
                from gi.repository import Gdk
                self.window.get_window().set_events(
                    self.window.get_window().get_events() | 
                    Gdk.EventMask.STRUCTURE_MASK |
                    Gdk.EventMask.PROPERTY_CHANGE_MASK
                )
            except Exception as e:
                print(f"[RIGHT_PANEL] Could not set window event mask: {e}", file=sys.stderr)
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        return self.window
    
    def _setup_plotting_panels(self):
        """Set up plotting panels in canvas containers.
        
        This method ONLY instantiates panel modules and attaches them to containers.
        All business logic is in the panel modules themselves.
        """
        # Import panel modules
        from shypn.analyses import PlaceRatePanel, TransitionRatePanel
        from shypn.analyses.diagnostics_panel import DiagnosticsPanel
        
        # === Places Panel ===
        places_container = self.builder.get_object('places_canvas_container')
        if places_container:
            # Remove placeholder label if it exists
            for child in places_container.get_children():
                places_container.remove(child)
            
            # Instantiate and add place rate panel with expand=True to fill vertical space
            self.place_panel = PlaceRatePanel(self.data_collector)
            places_container.pack_start(self.place_panel, True, True, 0)
            
            # Register panel to observe model changes (for automatic cleanup of deleted objects)
            if self.model is not None and hasattr(self.place_panel, 'register_with_model'):
                self.place_panel.register_with_model(self.model)
            
        else:
        
            pass
        # === Transitions Panel ===
        transitions_container = self.builder.get_object('transitions_canvas_container')
        if transitions_container:
            # Remove placeholder label if it exists
            for child in transitions_container.get_children():
                transitions_container.remove(child)
            
            # Instantiate and add transition rate panel with expand=True to fill vertical space
            # Pass place_panel reference for locality plotting support
            self.transition_panel = TransitionRatePanel(self.data_collector, place_panel=self.place_panel)
            transitions_container.pack_start(self.transition_panel, True, True, 0)
            
            # Register panel to observe model changes (for automatic cleanup of deleted objects)
            if self.model is not None and hasattr(self.transition_panel, 'register_with_model'):
                self.transition_panel.register_with_model(self.model)
            
        else:
        
            pass
        # === Diagnostics Panel (NEW) ===
        diagnostics_container = self.builder.get_object('diagnostics_content_container')
        diagnostics_selection_label = self.builder.get_object('diagnostics_selection_label')
        diagnostics_placeholder = self.builder.get_object('diagnostics_placeholder')
        
        if diagnostics_container:
            # Instantiate diagnostics panel
            self.diagnostics_panel = DiagnosticsPanel(self.model, self.data_collector)
            self.diagnostics_panel.setup(
                diagnostics_container,
                selection_label=diagnostics_selection_label,
                placeholder_label=diagnostics_placeholder
            )
            
        else:
        
            pass
        # Wire search UI if model is available
        if self.model is not None:
            self._wire_search_ui()
        
        # Create context menu handler now that panels exist
        if self.place_panel and self.transition_panel:
            from shypn.analyses import ContextMenuHandler
            self.context_menu_handler = ContextMenuHandler(
                self.place_panel, 
                self.transition_panel, 
                self.model,
                self.diagnostics_panel  # Pass diagnostics panel
            )
    
    def _wire_search_ui(self):
        """Wire search UI controls to panel search functionality.
        
        This method connects the search widgets from the UI to the panel methods.
        The panels handle all the search logic internally.
        """
        # === Places Search UI ===
        places_entry = self.builder.get_object('places_search_entry')
        places_search_btn = self.builder.get_object('places_search_button')
        places_result_label = self.builder.get_object('places_result_label')
        
        if self.place_panel and all([places_entry, places_search_btn, places_result_label]):
            self.place_panel.wire_search_ui(
                places_entry,
                places_search_btn,
                places_result_label,
                self.model
            )
        else:
        
            pass
        # === Transitions Search UI ===
        transitions_entry = self.builder.get_object('transitions_search_entry')
        transitions_search_btn = self.builder.get_object('transitions_search_button')
        transitions_result_label = self.builder.get_object('transitions_result_label')
        
        if self.transition_panel and all([transitions_entry, transitions_search_btn, transitions_result_label]):
            self.transition_panel.wire_search_ui(
                transitions_entry,
                transitions_search_btn,
                transitions_result_label,
                self.model
            )
        else:
    
            pass
    def set_data_collector(self, data_collector):
        """Set or update the data collector for plotting panels.
        
        This allows setting the data collector after initialization,
        useful when the right panel is created before the simulation controller.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        self.data_collector = data_collector
        
        # If panels don't exist yet, create them
        if self.place_panel is None or self.transition_panel is None:
            if self.builder is not None:  # UI must be loaded first
                self._setup_plotting_panels()
                
                # Create and wire context menu handler after panels are created
                if self.place_panel and self.transition_panel and not self.context_menu_handler:
                    from shypn.analyses import ContextMenuHandler
                    self.context_menu_handler = ContextMenuHandler(
                        self.place_panel, 
                        self.transition_panel, 
                        self.model,
                        self.diagnostics_panel  # Pass diagnostics panel
                    )
                    
                    # Notify parent if needed (for wiring to model_canvas_loader)
                    if hasattr(self, '_on_context_menu_handler_ready'):
                        self._on_context_menu_handler_ready(self.context_menu_handler)
        else:
            # Update existing panels
            self.place_panel.data_collector = data_collector
            self.transition_panel.data_collector = data_collector
        
        # Update diagnostics panel
        if self.diagnostics_panel:
            self.diagnostics_panel.set_data_collector(data_collector)
    
    def set_model(self, model):
        """Set the model for search functionality.
        
        This allows setting the model after initialization,
        useful when the right panel is created before the canvas loader.
        
        Args:
            model: ModelCanvasManager instance for searching places/transitions
        """
        self.model = model
        
        # Update context menu handler's model for locality detection
        if self.context_menu_handler:
            self.context_menu_handler.set_model(model)
        
        # Update diagnostics panel's model
        if self.diagnostics_panel:
            self.diagnostics_panel.set_model(model)
        
        # If panels exist and UI is loaded, wire search functionality
        if self.builder is not None and (self.place_panel or self.transition_panel):
            self._wire_search_ui()
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        # Prevent recursive calls when we update the button state programmatically
        if self._updating_button:
            return
            
        is_active = button.get_active()
        if is_active:
            # Button is now active → detach the panel (float)
            self.detach()
        else:
            # Button is now inactive → attach the panel back
            if self.parent_container:
                self.hang_on(self.parent_container)
    
    def detach(self):
        """Detach from container and restore as independent window (skeleton pattern)."""
        
        if not self.is_hanged:
            return
        
        # Remove from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            # Hide the container after unattaching
            self.parent_container.set_visible(False)
        
        # Hide the stack if this was the active panel
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
        
        # Return content to independent window
        self.window.add(self.content)
        
        # Set transient for main window if available
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state
        if self.float_button and not self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Notify that panel is floating
        if self.on_float_callback:
            self.on_float_callback()
        
        # Show window
        self.window.show_all()
        
    
    def float(self, parent_window=None):
        """Float panel as a separate window (alias for detach for backward compatibility).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        if parent_window:
            self.parent_window = parent_window
        self.detach()
    
    def hang_on(self, container):
        """Hang this panel on a container (attach - skeleton pattern).
        
        Args:
            container: Gtk.Box or other container to embed content into.
        """
        
        if self.is_hanged:
            if not self.content.get_visible():
                self.content.show_all()
            # Make sure container is visible when re-showing
            if not container.get_visible():
                container.set_visible(True)
            return
        
        # Hide independent window
        self.window.hide()
        
        # Remove content from window
        self.window.remove(self.content)
        
        # Hang content on container
        container.pack_start(self.content, True, True, 0)
        self.content.show_all()
        
        # Make container visible (it was hidden when detached)
        container.set_visible(True)
        
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Show the stack if available
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(True)
            if hasattr(self, '_stack_panel_name'):
                self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Notify that panel is attached
        if self.on_attach_callback:
            self.on_attach_callback()
        
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (alias for hang_on for backward compatibility).
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        if parent_window:
            self.parent_window = parent_window
        
        self.hang_on(container)
        
    
    def unattach(self):
        """Unattach panel from container (alias for detach for backward compatibility)."""
        self.detach()
    
    def hide(self):
        """Hide the panel (keep hanged but invisible - skeleton pattern)."""
        
        if self.is_hanged and self.parent_container:
            # Hide content while keeping it hanged
            self.content.set_no_show_all(True)  # Prevent show_all from revealing it
            self.content.hide()
        else:
            # Hide floating window
            self.window.hide()
    
    def show(self):
        """Show the panel (reveal if hanged, show window if floating - skeleton pattern)."""
        
        if self.is_hanged and self.parent_container:
            # Re-enable show_all and show content (reveal)
            self.content.set_no_show_all(False)
            self.content.show_all()
        else:
            # Show floating window
            self.window.show_all()
        
        # WAYLAND FIX: Use idle callback to defer hide operation
        GLib.idle_add(_do_hide)
    
    # ========================================================================
    # PHASE 4: GtkStack Integration Methods
    # New architecture: Panels live in GtkStack, controlled by Master Palette
    # ========================================================================
    
    def add_to_stack(self, stack, container, panel_name='analyses'):
        """Add panel content to a GtkStack container (Phase 4: new architecture).
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('analyses')
        """
        
        if self.window is None:
            self.load()
        
        # Extract content from window
        current_parent = self.content.get_parent()
        if current_parent == self.window:
            self.window.remove(self.content)
        elif current_parent and current_parent != container:
            current_parent.remove(self.content)
        
        # Add content to stack container
        if self.content.get_parent() != container:
            container.add(self.content)
        
        # Mark as hanged in stack mode
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
        # Hide window (not needed in stack mode)
        if self.window:
            self.window.hide()
        
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Re-enable show_all and make content visible
        if self.content:
            self.content.set_no_show_all(False)  # Re-enable show_all
            self.content.show_all()  # Show all child widgets recursively
        
        # Make container visible too
        if self.parent_container:
            self.parent_container.set_visible(True)
        
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)

        


def create_right_panel(ui_path=None, data_collector=None):
    """Convenience function to create and load the right panel loader.
    
    Args:
        ui_path: Optional path to right_panel.ui.
        data_collector: Optional SimulationDataCollector for plotting panels.
        
    Returns:
        RightPanelLoader: The loaded right panel loader instance.
        
    Example:
        # With data collector for plotting
        loader = create_right_panel(data_collector=collector)
        loader.detach(main_window)  # Show as floating
        # or
        loader.attach_to(container)  # Attach to extreme right
    """
    loader = RightPanelLoader(ui_path, data_collector)
    loader.load()
    return loader
