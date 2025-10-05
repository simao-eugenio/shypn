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
        self.is_attached = False
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
        self.on_float_callback = None  # Callback to notify when panel floats
        self.on_attach_callback = None  # Callback to notify when panel attaches
        
        # Plotting panels (will be instantiated in load())
        self.place_panel = None
        self.transition_panel = None
        
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
        
        # === Places Panel ===
        places_container = self.builder.get_object('places_canvas_container')
        if places_container:
            # Remove placeholder label if it exists
            for child in places_container.get_children():
                places_container.remove(child)
            
            # Instantiate and add place rate panel with expand=True to fill vertical space
            self.place_panel = PlaceRatePanel(self.data_collector)
            places_container.pack_start(self.place_panel, True, True, 0)
            
            print("[RightPanelLoader] Place rate panel attached to places_canvas_container")
        else:
            print("[RightPanelLoader] Warning: places_canvas_container not found in UI")
        
        # === Transitions Panel ===
        transitions_container = self.builder.get_object('transitions_canvas_container')
        if transitions_container:
            # Remove placeholder label if it exists
            for child in transitions_container.get_children():
                transitions_container.remove(child)
            
            # Instantiate and add transition rate panel with expand=True to fill vertical space
            self.transition_panel = TransitionRatePanel(self.data_collector)
            transitions_container.pack_start(self.transition_panel, True, True, 0)
            
            print("[RightPanelLoader] Transition rate panel attached to transitions_canvas_container")
        else:
            print("[RightPanelLoader] Warning: transitions_canvas_container not found in UI")
        
        # Wire search UI if model is available
        if self.model is not None:
            self._wire_search_ui()
        
        # Create context menu handler now that panels exist
        if self.place_panel and self.transition_panel:
            from shypn.analyses import ContextMenuHandler
            self.context_menu_handler = ContextMenuHandler(self.place_panel, self.transition_panel, self.model)
            print("[RightPanelLoader] Context menu handler created with model support")
    
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
            print("[RightPanelLoader] Places search UI wired")
        else:
            print("[RightPanelLoader] Warning: Could not wire places search UI (missing widgets or panel)")
        
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
            print("[RightPanelLoader] Transitions search UI wired")
        else:
            print("[RightPanelLoader] Warning: Could not wire transitions search UI (missing widgets or panel)")
    
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
                    self.context_menu_handler = ContextMenuHandler(self.place_panel, self.transition_panel, self.model)
                    print("[RightPanelLoader] Context menu handler created with model support")
                    
                    # Notify parent if needed (for wiring to model_canvas_loader)
                    if hasattr(self, '_on_context_menu_handler_ready'):
                        self._on_context_menu_handler_ready(self.context_menu_handler)
        else:
            # Update existing panels
            self.place_panel.data_collector = data_collector
            self.transition_panel.data_collector = data_collector
            print("[RightPanelLoader] Data collector updated for plotting panels")
    
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
            print("[RightPanelLoader] Context menu handler model updated for locality detection")
        
        # If panels exist and UI is loaded, wire search functionality
        if self.builder is not None and (self.place_panel or self.transition_panel):
            self._wire_search_ui()
            print("[RightPanelLoader] Model set and search UI wired")
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        # Prevent recursive calls when we update the button state programmatically
        if self._updating_button:
            return
            
        is_active = button.get_active()
        if is_active:
            # Button is now active -> float the panel
            self.float(self.parent_window)
        else:
            # Button is now inactive -> dock the panel back
            if self.parent_container:
                self.attach_to(self.parent_container, self.parent_window)
    
    def float(self, parent_window=None):
        """Float panel as a separate window (detach if currently attached).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        # If window doesn't exist, load the UI
        if self.window is None:
            self.load()
        
        # If currently attached, unattach first (moves content back to window)
        if self.is_attached:
            self.unattach()
            # Hide the container after unattaching
            if self.parent_container:
                self.parent_container.set_visible(False)
        
        # Set as transient for parent if provided
        if parent_window:
            self.window.set_transient_for(parent_window)
        
        # Update float button state
        if self.float_button and not self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Notify that panel is floating (to collapse paned)
        if self.on_float_callback:
            self.on_float_callback()
        
        # GTK3: use show_all() instead of present() to ensure all widgets are visible
        self.window.show_all()
    
    def detach(self, parent_window=None):
        """Detach panel to show as a floating window.
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        # Detach is now an alias for float
        self.float(parent_window)
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (embed content in extreme right, hide window).
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        
        if self.window is None:
            self.load()
        
        # Store parent window and container for float button callback
        if parent_window:
            self.parent_window = parent_window
        self.parent_container = container
        
        # Extract content from window first
        current_parent = self.content.get_parent()
        if current_parent == self.window:
            self.window.remove(self.content)  # GTK3 uses remove()
        elif current_parent and current_parent != container:
            current_parent.remove(self.content)
        
        # Hide the window but DON'T destroy it - we need it to float again
        if self.window and self.window.get_visible():
            self.window.hide()
        
        # Only add if not already in container
        if self.content.get_parent() != container:
            container.add(self.content)  # GTK3 uses add() instead of append()
        else:
            pass
        
        # Make container visible when panel is attached
        container.set_visible(True)
        
        # Make sure content is visible
        self.content.set_visible(True)
        self.content.show_all()  # Ensure all child widgets are visible
        
        # Update float button state
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        self.is_attached = True
        
        # Notify that panel is attached (to expand paned)
        if self.on_attach_callback:
            self.on_attach_callback()
        
    
    def unattach(self):
        """Unattach panel from container (return content to window)."""
        if not self.is_attached:
            return
        
        
        # Remove from container
        if self.parent_container and self.content.get_parent() == self.parent_container:
            self.parent_container.remove(self.content)
        
        # Return content to window
        self.window.add(self.content)  # GTK3 uses add() instead of set_child()
        
        # Make sure content is visible in window
        self.content.show_all()
        
        self.is_attached = False
        # Don't clear parent_container - we need it to dock back
    
    def hide(self):
        """Hide panel (works for both attached and detached states)."""
        if self.is_attached:
            # When attached, hide both content and container
            self.content.set_visible(False)
            if self.parent_container:
                self.parent_container.set_visible(False)
        elif self.window:
            self.window.set_visible(False)


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
